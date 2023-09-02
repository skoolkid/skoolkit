# Copyright 2022, 2023 Richard Dymond (rjdymond@gmail.com)
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
import time

from skoolkit import ROM48, VERSION, SkoolKitError, get_int_param, integer, read_bin_file
from skoolkit.config import get_config, show_config, update_options
from skoolkit.pagingtracer import Memory, PagingTracer
from skoolkit.snapshot import make_snapshot, poke, print_reg_help, write_snapshot
from skoolkit.simulator import (Simulator, A, F, B, C, D, E, H, L, IXh, IXl, IYh, IYl,
                                SP, SP2, I, R, xA, xF, xB, xC, xD, xE, xH, xL, PC, T)
from skoolkit.snapinfo import parse_snapshot
from skoolkit.traceutils import disassemble

REGISTERS = {
    'a': (A, SP2),
    'f': (F, SP2),
    'bc': (C, B),
    'b': (B, SP2),
    'c': (C, SP2),
    'de': (E, D),
    'd': (D, SP2),
    'e': (E, SP2),
    'hl': (L, H),
    'h': (H, SP2),
    'l': (L, SP2),
    'ix': (IXl, IXh),
    'ixh': (IXh, SP2),
    'ixl': (IXl, SP2),
    'iy': (IYl, IYh),
    'iyh': (IYh, SP2),
    'iyl': (IYl, SP2),
    'sp': (SP, SP2),
    'i': (I, SP2),
    'r': (R, SP2),
    '^a': (xA, SP2),
    '^f': (xF, SP2),
    '^bc': (xC, xB),
    '^b': (xB, SP2),
    '^c': (xC, SP2),
    '^de': (xE, xD),
    '^d': (xD, SP2),
    '^e': (xE, SP2),
    '^hl': (xL, xH),
    '^h': (xH, SP2),
    '^l': (xL, SP2)
}

class Registers:
    def __init__(self, registers):
        self.registers = registers

    def __getitem__(self, key):
        lo, hi = REGISTERS[key]
        return self.registers[lo] + 256 * self.registers[hi]

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
        opcodes = simulator.opcodes
        memory = simulator.memory
        registers = simulator.registers
        frame_duration = simulator.frame_duration
        pc = registers[PC] = start
        operations = 0
        tstates = registers[25]
        accept_int = False
        r = Registers(registers)

        while True:
            t0 = tstates
            if trace_line:
                i = disassemble(memory, pc, prefix, byte_fmt, word_fmt)[0]
                opcodes[memory[pc]]()
                print(trace_line.format(pc=pc, i=i, r=r, t=t0))
            else:
                opcodes[memory[pc]]()
            tstates = registers[25]

            if interrupts and simulator.iff:
                if tstates // frame_duration > t0 // frame_duration:
                    accept_int = True
                if accept_int:
                    accept_int = simulator.accept_interrupt(registers, memory, pc)

            pc = registers[24]
            operations += 1

            if operations >= max_operations > 0:
                print(f'Stopped at {prefix}{pc:{word_fmt}}: {operations} operations')
                break
            if tstates >= max_tstates > 0:
                print(f'Stopped at {prefix}{pc:{word_fmt}}: {tstates} T-states')
                break
            if pc == stop:
                print(f'Stopped at {prefix}{pc:{word_fmt}}')
                break

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

def get_registers(sna_reg, specs):
    if sna_reg:
        registers = {
            'A': sna_reg.a,
            'F': sna_reg.f,
            'BC': sna_reg.bc,
            'DE': sna_reg.de,
            'HL': sna_reg.hl,
            'IXh': sna_reg.ix // 256,
            'IXl': sna_reg.ix % 256,
            'IYh': sna_reg.iy // 256,
            'IYl': sna_reg.iy % 256,
            'SP': sna_reg.sp,
            'I': sna_reg.i,
            'R': sna_reg.r,
            '^A': sna_reg.a2,
            '^F': sna_reg.f2,
            '^BC': sna_reg.bc2,
            '^DE': sna_reg.de2,
            '^HL': sna_reg.hl2
        }
    else:
        registers = {}
    for spec in specs:
        reg, sep, val = spec.upper().partition('=')
        if sep:
            try:
                registers[reg] = get_int_param(val, True)
            except ValueError:
                raise SkoolKitError("Cannot parse register value: {}".format(spec))
    return registers

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
    if snafile in ('48', '128'):
        if snafile == '48':
            memory = [0] * 0x10000
        else:
            memory = [0] * 0x20000
        reg = None
        org = 0
    else:
        memory, org = make_snapshot(snafile, options.org, page=-1)[:2]
        reg = parse_snapshot(snafile)[1]
        if snafile.lower()[-4:] == '.sna':
            reg.sp = (reg.sp + 2) % 65536
    if reg:
        state = {'im': reg.im, 'iff': reg.iff2, 'tstates': reg.tstates}
        border = reg.border
        out7ffd = reg.out7ffd
        outfffd = reg.outfffd
        ay = list(reg.ay)
        outfe = reg.outfe
    else:
        state = {'im': 1, 'iff': 1, 'tstates': 0}
        border = 7
        out7ffd = 0
        outfffd = 0
        ay = [0] * 16
        outfe = 0
    start = options.start
    if start is None:
        if reg:
            start = reg.pc
        elif options.org is not None:
            start = options.org
        else:
            start = org
    if options.rom:
        rom = read_bin_file(options.rom)
        memory[:len(rom)] = rom
    elif len(memory) == 65536:
        memory[:0x4000] = read_bin_file(ROM48)
    else:
        banks = [memory[a:a + 0x4000] for a in range(0, 0x20000, 0x4000)]
        memory = Memory(banks, out7ffd)
    for spec in options.pokes:
        poke(memory, spec)
    fast = options.verbose == 0 and not options.interrupts
    sim_config = {'fast_djnz': fast, 'fast_ldir': fast}
    simulator = Simulator(memory, get_registers(reg, options.reg), state, sim_config)
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
    tracer.run(start, options.stop, options.max_operations, options.max_tstates,
               options.interrupts, trace_line, prefix, byte_fmt, word_fmt)
    rt = time.time() - begin
    if options.stats:
        z80t = simulator.registers[T] - state['tstates']
        z80s = z80t / 3500000
        speed = z80s / (rt or 0.001) # Avoid division by zero
        print(f'Z80 execution time: {z80t} T-states ({z80s:.03f}s)')
        print(f'Instructions executed: {tracer.operations}')
        print(f'Simulation time: {rt:.03f}s (x{speed:.02f})')
    if options.audio:
        delays = []
        for i, t in enumerate(tracer.out_times[1:]):
            delays.append(t - tracer.out_times[i])
        duration = sum(delays)
        print('Sound duration: {} T-states ({:.03f}s)'.format(duration, duration / 3500000))
        print('Delays: {}'.format(simplify(delays, options.depth)))
    if options.dump:
        state = []
        if isinstance(memory, Memory):
            ram = memory.banks
            state.extend(f'ay[{n}]={v}' for n, v in enumerate(tracer.ay))
            state.extend((f'7ffd={tracer.out7ffd}', f'fffd={tracer.outfffd}'))
        else:
            ram = memory[0x4000:]
        r = simulator.registers
        registers = (
            f'a={r[A]}',
            f'f={r[F]}',
            f'bc={r[C] + 256 * r[B]}',
            f'de={r[E] + 256 * r[D]}',
            f'hl={r[L] + 256 * r[H]}',
            f'ix={r[IXl] + 256 * r[IXh]}',
            f'iy={r[IYl] + 256 * r[IYh]}',
            f'sp={r[SP]}',
            f'i={r[I]}',
            f'r={r[R]}',
            f'^a={r[xA]}',
            f'^f={r[xF]}',
            f'^bc={r[xC] + 256 * r[xB]}',
            f'^de={r[xE] + 256 * r[xD]}',
            f'^hl={r[xL] + 256 * r[xH]}',
            f'pc={r[PC]}'
        )
        state.extend((
            f'border={tracer.border}',
            f'fe={tracer.outfe}',
            f'iff={simulator.iff}',
            f'im={simulator.imode}',
            f'tstates={r[T]}'
        ))
        write_snapshot(options.dump, ram, registers, state)
        print(f'Wrote {options.dump}')

def main(args):
    config = get_config('trace')
    parser = argparse.ArgumentParser(
        usage='trace.py [options] FILE [OUTFILE]',
        description="Trace Z80 machine code execution. "
                    "FILE may be a binary (raw memory) file, a SNA, SZX or Z80 snapshot, or '48' or '128' for no snapshot. "
                    "If 'OUTFILE' is given, an SZX or Z80 snapshot is written after execution has completed.",
        add_help=False
    )
    parser.add_argument('snafile', help=argparse.SUPPRESS, nargs='?')
    parser.add_argument('dump', help=argparse.SUPPRESS, nargs='?')
    group = parser.add_argument_group('Options')
    group.add_argument('--audio', action='store_true',
                       help="Show audio delays.")
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
    group.add_argument('-p', '--poke', dest='pokes', metavar='a[-b[-c]],[^+]v', action='append', default=[],
                       help="POKE N,v for N in {a, a+c, a+2c..., b}. "
                            "Prefix 'v' with '^' to perform an XOR operation, or '+' to perform an ADD operation. "
                            "This option may be used multiple times.")
    group.add_argument('-r', '--reg', metavar='name=value', action='append', default=[],
                       help="Set the value of a register. Do '--reg help' for more information. "
                            "This option may be used multiple times.")
    group.add_argument('--rom', metavar='FILE',
                       help='Patch in a ROM at address 0 from this file.')
    group.add_argument('--show-config', dest='show_config', action='store_true',
                       help="Show configuration parameter values.")
    group.add_argument('-s', '--start', metavar='ADDR', type=integer,
                       help='Start execution at this address.')
    group.add_argument('-S', '--stop', metavar='ADDR', type=integer,
                       help='Stop execution at this address.')
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
    if unknown_args or namespace.snafile is None:
        parser.exit(2, parser.format_help())
    update_options('trace', namespace, namespace.params, config)
    run(namespace.snafile, namespace, config)
