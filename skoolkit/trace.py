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
from skoolkit.snapshot import make_snapshot, poke, print_reg_help, write_z80v3
from skoolkit.simulator import (Simulator, A, F, B, C, D, E, H, L, IXh, IXl, IYh, IYl,
                                SP, I, R, xA, xF, xB, xC, xD, xE, xH, xL, PC, T, FRAME_DURATION)
from skoolkit.snapinfo import parse_snapshot
from skoolkit.traceutils import disassemble

TRACE1H = "${address:04X} {data:<8} {i}"
TRACE1D = "{address:05} {data:<8} {i}"
TRACE2H = """
${address:04X} {data:<8} {i:<15}  A={A:02X} F={F:08b} BC={BC:04X} DE={DE:04X} HL={HL:04X} IX={IX:04X} IY={IY:04X} IR={IR:04X}
                                A'={^A:02X} F'={^F:08b} BC'={BC':04X} DE'={DE':04X} HL'={HL':04X} SP={SP:04X}
""".strip()
TRACE2D = """
{address:05} {data:<8} {i:<15}  A={A:<3} F={F:08b} BC={BC:<5} DE={DE:<5} HL={HL:<5} IX={IX:<5} IY={IY:<5} I={I:<3} R={R:<3}
                                A'={^A:<3} F'={^F:08b} BC'={BC':<5} DE'={DE':<5} HL'={HL':<5} SP={SP:<5}
""".strip()

class Tracer:
    def __init__(self, border):
        self.operations = 0
        self.border = border
        self.spkr = None
        self.out_times = []

    def run(self, simulator, start, stop, verbose, max_operations, max_tstates, decimal, interrupts):
        opcodes = simulator.opcodes
        memory = simulator.memory
        registers = simulator.registers
        pc = registers[PC] = start
        operations = 0
        tstates = 0
        accept_int = False

        if decimal:
            p = b = w = ''
            if verbose > 1:
                fmt = TRACE2D
            else:
                fmt = TRACE1D
        else:
            p, b, w = '$', '02X', '04X'
            if verbose > 1:
                fmt = TRACE2H
            else:
                fmt = TRACE1H
        if verbose:
            instruction, size = disassemble(memory, pc, p, b, w)
            values = {
                'address': pc,
                'data': ''.join(f'{memory[a % 65536]:02X}' for a in range(pc, pc + size)),
                'i': instruction
            }

        while True:
            t0 = tstates
            opcodes[memory[pc]]()
            tstates = registers[25]

            if interrupts and simulator.iff:
                if tstates // FRAME_DURATION > t0 // FRAME_DURATION:
                    accept_int = True
                if accept_int:
                    accept_int = simulator.accept_interrupt(registers, memory, pc)

            pc = registers[24]

            if verbose:
                values.update({
                    "A": registers[A],
                    "F": registers[F],
                    "BC": registers[C] + 256 * registers[B],
                    "DE": registers[E] + 256 * registers[D],
                    "HL": registers[L] + 256 * registers[H],
                    "IX": registers[IXl] + 256 * registers[IXh],
                    "IY": registers[IYl] + 256 * registers[IYh],
                    "I": registers[I],
                    "R": registers[R],
                    "IR": registers[R] + 256 * registers[I],
                    "SP": registers[SP],
                    "^A": registers[xA],
                    "^F": registers[xF],
                    "BC'": registers[xC] + 256 * registers[xB],
                    "DE'": registers[xE] + 256 * registers[xD],
                    "HL'": registers[xL] + 256 * registers[xH]
                })
                print(fmt.format(**values))
                instruction, size = disassemble(memory, pc, p, b, w)
                values['address'] = pc
                values['data'] = ''.join(f'{memory[a % 65536]:02X}' for a in range(pc, pc + size))
                values['i'] = instruction

            operations += 1

            if operations >= max_operations > 0:
                print(f'Stopped at {p}{pc:{w}}: {operations} operations')
                break
            if registers[T] >= max_tstates > 0:
                print(f'Stopped at {p}{pc:{w}}: {registers[T]} T-states')
                break
            if pc == stop:
                print(f'Stopped at {p}{pc:{w}}')
                break

        self.operations = operations

    def write_port(self, registers, port, value):
        if port % 2 == 0:
            self.border = value % 8
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

def run(snafile, options):
    if snafile == '.':
        memory = [0] * 65536
        reg = None
        org = 0
    else:
        memory, org = make_snapshot(snafile, options.org)[0:2]
        reg = parse_snapshot(snafile)[1]
        if snafile.lower()[-4:] == '.sna':
            reg.sp = (reg.sp + 2) % 65536
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
    else:
        rom = read_bin_file(ROM48)
    memory[:len(rom)] = rom
    for spec in options.pokes:
        poke(memory, spec)
    if reg:
        im = reg.im
        iff = reg.iff2
        border = reg.border
        tstates = reg.tstates
    else:
        im = 1
        iff = 1
        border = 7
        tstates = 0
    state = {'im': im, 'iff': iff, 'tstates': tstates}
    fast = options.verbose == 0 and not options.interrupts
    config = {'fast_djnz': fast, 'fast_ldir': fast}
    simulator = Simulator(memory, get_registers(reg, options.reg), state, config)
    tracer = Tracer(border)
    simulator.set_tracer(tracer)
    begin = time.time()
    tracer.run(simulator, start, options.stop, options.verbose,
               options.max_operations, options.max_tstates, options.decimal,
               options.interrupts)
    rt = time.time() - begin
    if options.stats:
        z80t = simulator.registers[T] - tstates
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
        ram = simulator.memory[16384:]
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
        state = (
            f'border={tracer.border}',
            f'iff={simulator.iff}',
            f'im={simulator.imode}',
            f'tstates={r[T]}'
        )
        write_z80v3(options.dump, ram, registers, state)
        print(f'Z80 snapshot dumped to {options.dump}')

def main(args):
    parser = argparse.ArgumentParser(
        usage='trace.py [options] FILE',
        description="Trace Z80 machine code execution. "
                    "FILE may be a binary (raw memory) file, a SNA, SZX or Z80 snapshot, or '.' for no snapshot.",
        add_help=False
    )
    parser.add_argument('snafile', help=argparse.SUPPRESS, nargs='?')
    group = parser.add_argument_group('Options')
    group.add_argument('--audio', action='store_true',
                       help="Show audio delays.")
    group.add_argument('-D', '--decimal', action='store_true',
                       help="Show decimal values in verbose mode.")
    group.add_argument('--depth', type=int, default=2,
                       help='Simplify audio delays to this depth (default: 2).')
    group.add_argument('--dump', metavar='FILE',
                       help='Dump a Z80 snapshot to this file after execution.')
    group.add_argument('-i', '--interrupts', action='store_true',
                       help='Execute interrupt routines.')
    group.add_argument('--max-operations', metavar='MAX', type=int, default=0,
                       help='Maximum number of instructions to execute.')
    group.add_argument('--max-tstates', metavar='MAX', type=int, default=0,
                       help='Maximum number of T-states to run for.')
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
                       help='Patch in a ROM at address 0 from this file. '
                            'By default the 48K ZX Spectrum ROM is used.')
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
    if 'help' in namespace.reg:
        print_reg_help()
        return
    if unknown_args or namespace.snafile is None:
        parser.exit(2, parser.format_help())
    run(namespace.snafile, namespace)
