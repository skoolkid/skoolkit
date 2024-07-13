# Copyright 2022-2024 Richard Dymond (rjdymond@gmail.com)
#
# This file is part of SkoolKit.
#
# SkoolKit is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# SkoolKit is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# SkoolKit. If not, see <http://www.gnu.org/licenses/>.

import argparse
import textwrap
import time

from skoolkit import (ROM48, VERSION, SkoolKitError, CSimulator,
                      CCMIOSimulator, get_int_param, integer, read_bin_file)
from skoolkit.audio import CLOCK_SPEED, AudioWriter
from skoolkit.cmiosimulator import CMIOSimulator
from skoolkit.config import get_config, show_config, update_options
from skoolkit.pagingtracer import Memory, PagingTracer
from skoolkit.simulator import Simulator
from skoolkit.simutils import PC, T, from_snapshot, get_state
from skoolkit.snapshot import (Snapshot, make_snapshot, poke, print_reg_help,
                               print_state_help, write_snapshot)
from skoolkit.traceutils import Registers, disassemble, get_trace_line

class Tracer(PagingTracer):
    def __init__(self, simulator, border, out7ffd, outfffd, ay, outfe):
        self.simulator = simulator
        self.border = border
        self.out7ffd = out7ffd
        self.outfffd = outfffd
        self.ay = ay
        self.outfe = outfe
        self.operations = 0
        self.spkr = None
        self.out_times = []

    def run(self, start, stop, max_operations, max_tstates, interrupts, trace_line, prefix, byte_fmt, word_fmt):
        simulator = self.simulator
        memory = simulator.memory
        registers = simulator.registers
        start_time = registers[T]
        if max_tstates > 0:
            max_time = start_time + max_tstates
        else:
            max_time = 0
        if trace_line:
            r = Registers(registers)

        if hasattr(simulator, 'trace'): # pragma: no cover
            if trace_line:
                df = lambda pc: disassemble(memory, pc, prefix, byte_fmt, word_fmt)[0]
                tf = lambda pc, i, t0: print(trace_line.format(pc=pc, i=i, r=r, t=t0, m=memory))
            else:
                df = tf = None
            stop_cond, operations = simulator.trace(start, stop, max_operations, max_time, interrupts, df, tf)
        else:
            opcodes = simulator.opcodes
            frame_duration = simulator.frame_duration
            int_active = simulator.int_active
            pc = registers[PC] = start
            operations = 0
            tstates = registers[25]
            while True:
                t0 = tstates
                if trace_line:
                    i = disassemble(memory, pc, prefix, byte_fmt, word_fmt)[0]
                    opcodes[memory[pc]]()
                    print(trace_line.format(pc=pc, i=i, r=r, t=t0, m=memory))
                else:
                    opcodes[memory[pc]]()
                tstates = registers[25]

                if interrupts and registers[26] and tstates % frame_duration < int_active:
                    simulator.accept_interrupt(registers, memory, pc)
                    tstates = registers[25]

                pc = registers[24]
                operations += 1

                if operations >= max_operations > 0:
                    stop_cond = 1
                    break
                if tstates >= max_time > 0:
                    stop_cond = 2
                    break
                if pc == stop:
                    stop_cond = 3
                    break

        if stop_cond == 1:
            print(f'Stopped at {prefix}{registers[PC]:{word_fmt}}: {operations} operations')
        elif stop_cond == 2:
            print(f'Stopped at {prefix}{registers[PC]:{word_fmt}}: {registers[T] - start_time} T-states')
        elif stop_cond == 3:
            print(f'Stopped at {prefix}{registers[PC]:{word_fmt}}')
        self.operations = operations

    def read_port(self, registers, port):
        if port == 0xFFFD:
            return self.ay[self.outfffd % 16]
        return 0xFF

    def write_port(self, registers, port, value):
        super().write_port(registers, port, value)
        if port % 2 == 0:
            if self.spkr != value & 0x10:
                self.spkr = value & 0x10
                self.out_times.append(registers[T])

    def get_delays(self):
        return [t1 - t0 for t0, t1 in zip(self.out_times, self.out_times[1:])]

def rle(s, length):
    s2 = []
    count = 1
    i = 0
    while i < len(s):
        while s[i:i + length] == s[i + length:i + length + length]:
            count += 1
            i += length
        if count > 1:
            s2.append('[{}]*{}'.format(', '.join(s[i:i + length]), count))
            i += length
            count = 1
        else:
            s2.append(s[i])
            i += 1
    return s2

def simplify(delays, depth):
    s0 = [str(d) for d in delays]
    if s0 and depth > 0:
        length = 1
        while length <= depth:
            s1 = rle(s0, length)
            if length > 1:
                while 1:
                    s0 = s1
                    s1 = rle(s1, length)
                    if s1 == s0:
                        break
            s0 = s1
            length += 1
    return ', '.join(s0)

def run(snafile, options, config):
    snapshot = None
    org = 0
    if snafile == '48':
        memory = [0] * 0x10000
    elif snafile == '128':
        memory = [0] * 0x20000
        machine = '128K'
    elif snafile == '+2':
        memory = [0] * 0x20000
        machine = '+2'
    else:
        snapshot = Snapshot.get(snafile)
        if snapshot:
            if snapshot.type == 'SNA' and len(snapshot.tail) == 0xC000:
                snapshot.sp = (snapshot.sp + 2) % 65536
        else:
            memory, org = make_snapshot(snafile, options.org)[:2]
    if options.cmio:
        if options.python:
            simulator_cls = CMIOSimulator
        else:
            simulator_cls = CCMIOSimulator or CMIOSimulator
    elif options.python:
        simulator_cls = Simulator
    else:
        simulator_cls = CSimulator or Simulator
    registers = {}
    for spec in options.reg:
        reg, sep, val = spec.partition('=')
        if sep:
            try:
                registers[reg.upper()] = get_int_param(val, True)
            except ValueError:
                raise SkoolKitError("Cannot parse register value: {}".format(spec))
    state = {'ay': [None] * 16}
    for spec in options.state:
        attr, sep, val = spec.partition('=')
        if sep:
            try:
                if attr.startswith('ay[') and attr.endswith(']'):
                    state['ay'][get_int_param(attr[3:-1]) % 16] = get_int_param(val)
                else:
                    state[attr] = get_int_param(val)
            except ValueError:
                raise SkoolKitError(f'Cannot parse integer: {spec}')
    fast = options.verbose == 0 and options.max_operations == 0 and options.max_tstates == 0
    sim_config = {'fast_djnz': fast, 'fast_ldir': fast}
    if snapshot:
        border = state.get('border', snapshot.border)
        out7ffd = state.get('7ffd', snapshot.out7ffd)
        outfffd = state.get('fffd', snapshot.outfffd)
        ay = list(snapshot.ay)
        outfe = state.get('fe', snapshot.outfe)
        simulator = from_snapshot(simulator_cls, snapshot, registers, state, sim_config, options.rom)
        memory = simulator.memory
        if len(memory) == 0x20000:
            memory.out7ffd(out7ffd)
    else:
        border = state.get('border', 7)
        out7ffd = state.get('7ffd', 0)
        outfffd = state.get('fffd', 0)
        ay = [0] * 16
        outfe = state.get('fe', 0)
        if len(memory) == 65536:
            rom = read_bin_file(options.rom or ROM48)
            memory[:len(rom)] = rom
        else:
            banks = [memory[a:a + 0x4000] for a in range(0, 0x20000, 0x4000)]
            memory = Memory(banks, out7ffd, machine)
        state.setdefault('iff', 1)
        simulator = simulator_cls(memory, registers, state, sim_config)
    for r, v in enumerate(state['ay']):
        if v is not None:
            ay[r] = v
    t0 = simulator.registers[T]
    start = options.start
    if start is None:
        if snapshot:
            start = snapshot.pc
        elif options.org is not None:
            start = options.org
        else:
            start = org
    for spec in options.pokes:
        poke(simulator.memory, spec)
    tracer = Tracer(simulator, border, out7ffd, outfffd, ay, outfe)
    simulator.set_tracer(tracer)
    if options.verbose:
        s = (('', '2'), ('Decimal', 'Decimal2'))[options.decimal][min(options.verbose - 1, 1)]
        trace_line = config['TraceLine' + s].replace(r'\n', '\n')
    else:
        trace_line = None
    trace_operand = config['TraceOperand' + ('', 'Decimal')[options.decimal]]
    prefix, byte_fmt, word_fmt = (trace_operand + ',' * (2 - trace_operand.count(','))).split(',')[:3]
    begin = time.time()
    if trace_line:
        orig_trace_line, trace_line = trace_line, get_trace_line(trace_line)
        try:
            trace_line.format(pc=0, i='.', r=Registers(simulator.registers), t=0, m=simulator.memory)
        except Exception as e:
            raise SkoolKitError(f"Invalid format string: '{orig_trace_line}'")
    tracer.run(start, options.stop, options.max_operations, options.max_tstates,
               options.interrupts, trace_line, prefix, byte_fmt, word_fmt)
    rt = time.time() - begin
    if len(simulator.memory) == 65536:
        cpu_freq = 3500000
    else:
        cpu_freq = 3546900
    if options.stats:
        z80t = simulator.registers[T] - t0
        z80s = z80t / cpu_freq
        speed = z80s / (rt or 0.001) # Avoid division by zero
        print(f'Z80 execution time: {z80t} T-states ({z80s:.3f}s)')
        print(f'Instructions executed: {tracer.operations}')
        print(f'Simulation time: {rt:.3f}s (x{speed:.2f})')
    if options.audio:
        delays = tracer.get_delays()
        z80t = sum(delays)
        z80s = z80t / cpu_freq
        print(f'Sound duration: {z80t} T-states ({z80s:.3f}s)')
        lines = textwrap.wrap(simplify(delays, options.depth), 78)
        print('Delays:\n {}'.format('\n '.join(lines)))
    if options.dump:
        if options.dump.lower().endswith('.wav'):
            delays = tracer.get_delays()
            if delays:
                audio_writer = AudioWriter({CLOCK_SPEED: cpu_freq})
                with open(options.dump, 'wb') as f:
                    audio_writer.write_audio(f, delays, ma_filter=True)
            else:
                raise SkoolKitError('No audio detected')
        else:
            ram, registers, state, machine = get_state(simulator)
            write_snapshot(options.dump, ram, registers, state, machine)
        print(f'Wrote {options.dump}')

def main(args):
    config = get_config('trace')
    parser = argparse.ArgumentParser(
        usage='trace.py [options] FILE [OUTFILE]',
        description="Trace Z80 machine code execution. "
                    "FILE may be a binary (raw memory) file, a SNA, SZX or Z80 snapshot, or '48', '128' or '+2' for no snapshot. "
                    "If 'OUTFILE' is given, an SZX/Z80 snapshot or WAV file is written after execution has completed.",
        add_help=False
    )
    parser.add_argument('snafile', help=argparse.SUPPRESS, nargs='?')
    parser.add_argument('dump', help=argparse.SUPPRESS, nargs='?')
    group = parser.add_argument_group('Options')
    group.add_argument('--audio', action='store_true',
                       help="Show audio delays.")
    group.add_argument('-c', '--cmio', action='store_true',
                       help="Simulate memory and I/O contention.")
    group.add_argument('-D', '--decimal', action='store_true',
                       help="Show decimal values in verbose mode.")
    group.add_argument('--depth', type=int, default=2,
                       help='Simplify audio delays to this depth (default: 2).')
    group.add_argument('-I', '--ini', dest='params', metavar='p=v', action='append', default=[],
                       help="Set the value of the configuration parameter 'p' to 'v'. This option may be used multiple times.")
    group.add_argument('-m', '--max-operations', metavar='MAX', type=int, default=0,
                       help='Maximum number of instructions to execute.')
    group.add_argument('-M', '--max-tstates', metavar='MAX', type=int, default=0,
                       help='Maximum number of T-states to run for.')
    group.add_argument('-n', '--no-interrupts', dest='interrupts', action='store_false',
                       help="Don't execute interrupt routines.")
    group.add_argument('-o', '--org', metavar='ADDR', type=integer,
                       help='Specify the origin address of a binary (raw memory) file (default: 65536 - length).')
    group.add_argument('-p', '--poke', dest='pokes', metavar='[p:]a[-b[-c]],[^+]v', action='append', default=[],
                       help="POKE N,v in RAM bank p for N in {a, a+c, a+2c..., b} before execution begins. "
                            "Prefix 'v' with '^' to perform an XOR operation, or '+' to perform an ADD operation. "
                            "This option may be used multiple times.")
    group.add_argument('--python', action='store_true',
                       help="Use the pure Python Z80 simulator.")
    group.add_argument('-r', '--reg', metavar='name=value', action='append', default=[],
                       help="Set the value of a register before execution begins. Do '--reg help' for more information. "
                            "This option may be used multiple times.")
    group.add_argument('--rom', metavar='FILE',
                       help='Patch in a ROM at address 0 from this file.')
    group.add_argument('--show-config', dest='show_config', action='store_true',
                       help="Show configuration parameter values.")
    group.add_argument('-s', '--start', metavar='ADDR', type=integer,
                       help='Start execution at this address.')
    group.add_argument('-S', '--stop', metavar='ADDR', type=integer,
                       help='Stop execution at this address.')
    group.add_argument('--state', dest='state', metavar='name=value', action='append', default=[],
                       help="Set a hardware state attribute before execution begins. Do '--state help' for more information. "
                            "This option may be used multiple times.")
    group.add_argument('--stats', action='store_true',
                       help="Show stats after execution.")
    group.add_argument('-v', '--verbose', action='count', default=0,
                       help="Show executed instructions. Repeat this option to show register values too.")
    group.add_argument('-V', '--version', action='version', version='SkoolKit {}'.format(VERSION),
                       help='Show SkoolKit version number and exit.')
    namespace, unknown_args = parser.parse_known_args(args)
    if namespace.show_config:
        show_config('trace', config)
    if 'help' in namespace.reg:
        print_reg_help()
        return
    if 'help' in namespace.state:
        print_state_help(show_defaults=False, omit=['issue2'])
        return
    if unknown_args or namespace.snafile is None:
        parser.exit(2, parser.format_help())
    update_options('trace', namespace, namespace.params, config)
    run(namespace.snafile, namespace, config)
