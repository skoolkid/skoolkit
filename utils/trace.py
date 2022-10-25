#!/usr/bin/env python3

import argparse
from collections import namedtuple
import os
import sys
import time

SKOOLKIT_HOME = os.environ.get('SKOOLKIT_HOME')
if not SKOOLKIT_HOME:
    sys.stderr.write('SKOOLKIT_HOME is not set; aborting\n')
    sys.exit(1)
if not os.path.isdir(SKOOLKIT_HOME):
    sys.stderr.write('SKOOLKIT_HOME={}; directory not found\n'.format(SKOOLKIT_HOME))
    sys.exit(1)
sys.path.insert(0, SKOOLKIT_HOME)

from skoolkit import ROM48, SkoolKitError, get_int_param, integer, read_bin_file
from skoolkit.snapshot import make_snapshot, poke, print_reg_help
from skoolkit.simulator import (Simulator, A, F, B, C, D, E, H, L, IXh, IXl, IYh, IYl,
                                SP, I, R, xA, xF, xB, xC, xD, xE, xH, xL)

from disassembler import Disassembler

TRACE1 = "${address:04X} {data:<8} {i}"
TRACE2 = """
${address:04X} {data:<8} {i:<15}  A={A:02X} F={F:08b} BC={BC:04X} DE={DE:04X} HL={HL:04X} IX={IX:04X} IY={IY:04X} IR={IR:04X}
                                A'={^A:02X} F'={^F:08b} BC'={BC':04X} DE'={DE':04X} HL'={HL':04X} SP={SP:04X}
""".strip()

class Tracer:
    def __init__(self, memory, start, verbose, end=-1, max_operations=0, max_tstates=0):
        self.verbose = verbose
        self.end = end
        self.max_operations = max_operations
        self.max_tstates = max_tstates
        self.operations = 0
        self.spkr = None
        self.out_times = []
        if self.verbose:
            self.address = start
            self.disassembler = Disassembler()
            self.instruction, size = self.disassembler.disassemble(memory, start)
            self.data = ''.join(f'{memory[a % 65536]:02X}' for a in range(start, start + size))

    def trace(self, simulator, address):
        if self.verbose:
            if self.verbose > 1:
                fmt = TRACE2
            else:
                fmt = TRACE1
            sim_registers = simulator.registers
            registers = {
                "A": sim_registers[A],
                "F": sim_registers[F],
                "BC": sim_registers[C] + 256 * sim_registers[B],
                "DE": sim_registers[E] + 256 * sim_registers[D],
                "HL": sim_registers[L] + 256 * sim_registers[H],
                "IX": sim_registers[IXl] + 256 * sim_registers[IXh],
                "IY": sim_registers[IYl] + 256 * sim_registers[IYh],
                "IR": sim_registers[R] + 256 * sim_registers[I],
                "SP": sim_registers[SP],
                "^A": sim_registers[xA],
                "^F": sim_registers[xF],
                "BC'": sim_registers[xC] + 256 * sim_registers[xB],
                "DE'": sim_registers[xE] + 256 * sim_registers[xD],
                "HL'": sim_registers[xL] + 256 * sim_registers[xH],
            }
            print(fmt.format(address=self.address, data=self.data, i=self.instruction, **registers))
            memory, address = simulator.memory, simulator.pc
            self.instruction, size = self.disassembler.disassemble(memory, address)
            self.data = ''.join(f'{memory[a % 65536]:02X}' for a in range(address, address + size))
            self.address = address

        self.operations += 1

        addr = f'${simulator.pc:04X}'
        if self.operations >= self.max_operations > 0:
            print(f'Stopped at {addr}: {self.operations} operations')
            return True
        if simulator.tstates >= self.max_tstates > 0:
            print(f'Stopped at {addr}: {simulator.tstates} T-states')
            return True
        if simulator.pc == self.end:
            print(f'Stopped at {addr}')
            return True
        if simulator.ppcount < 0 and self.max_operations <= 0 and self.max_tstates <= 0 and self.end < 0:
            print(f'Stopped at {addr}: PUSH-POP count is {simulator.ppcount}')
            return True

    def write_port(self, simulator, port, value):
        if port & 0xFF == 0xFE and self.spkr is None or self.spkr != value & 0x10:
            self.spkr = value & 0x10
            self.out_times.append(simulator.tstates)

def get_registers(specs):
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

def run(snafile, start, options):
    memory, start = make_snapshot(snafile, options.org, start)[0:2]
    if options.rom:
        rom = read_bin_file(options.rom)
    else:
        rom = read_bin_file(ROM48)
    memory[:len(rom)] = rom
    for spec in options.pokes:
        poke(memory, spec)
    config = {'fast_djnz': options.audio, 'fast_ldir': True}
    simulator = Simulator(memory, get_registers(options.reg), config=config)
    tracer = Tracer(memory, start, options.verbose, options.end, options.max_operations, options.max_tstates)
    simulator.set_tracer(tracer)
    begin = time.time()
    simulator.run(start)
    rt = time.time() - begin
    if options.stats:
        z80t = simulator.tstates / 3500000
        speed = z80t / rt
        print(f'Z80 execution time: {simulator.tstates} T-states ({z80t:.03f}s)')
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
        with open(options.dump, 'wb') as f:
            f.write(bytearray(simulator.memory[16384:]))
        print(f'Snapshot dumped to {options.dump}')

def main(args):
    parser = argparse.ArgumentParser(
        usage='trace.py [options] FILE START',
        description="Trace Z80 machine code execution. "
                    "FILE may be a binary (raw memory) file, or a SNA, SZX or Z80 snapshot.",
        add_help=False
    )
    parser.add_argument('snafile', help=argparse.SUPPRESS, nargs='?')
    parser.add_argument('start', type=integer, help=argparse.SUPPRESS, nargs='?')
    group = parser.add_argument_group('Options')
    group.add_argument('--audio', action='store_true',
                       help="Show audio delays.")
    group.add_argument('--depth', type=int, default=2,
                       help='Simplify audio delays to this depth (default: 2).')
    group.add_argument('--dump', metavar='FILE',
                       help='Dump snapshot to this file after execution.')
    group.add_argument('-e', '--end', metavar='ADDR', type=integer, default=-1,
                       help='End execution at this address.')
    group.add_argument('--max-operations', metavar='MAX', type=int, default=0,
                       help='Maximum number of instructions to execute.')
    group.add_argument('--max-tstates', metavar='MAX', type=int, default=0,
                       help='Maximum number of T-states to run for.')
    group.add_argument('-o', '--org', dest='org', metavar='ADDR', type=integer,
                       help='Specify the origin address of a binary (.bin) file (default: 65536 - length).')
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
    group.add_argument('--stats', action='store_true',
                       help="Show stats after execution.")
    group.add_argument('-v', '--verbose', action='count', default=0,
                       help="Show executed instructions. Repeat this option to show register values too.")
    namespace, unknown_args = parser.parse_known_args(args)
    if 'help' in namespace.reg:
        print_reg_help()
        sys.exit(0)
    if unknown_args or namespace.start is None:
        parser.exit(2, parser.format_help())
    run(namespace.snafile, namespace.start, namespace)

if __name__ == '__main__':
    main(sys.argv[1:])
