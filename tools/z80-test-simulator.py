#!/usr/bin/env python3

import argparse
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

from skoolkit import integer, read_bin_file
from skoolkit.snapshot import make_snapshot
from skoolkit.simulator import Simulator

class Tracer:
    def __init__(self, verbose, max_operations, end):
        self.verbose = verbose
        self.max_operations = max_operations
        self.end = end
        self.msg = ''
        self.count = 0

    def trace(self, simulator, instruction):
        if self.verbose:
            print(f'{instruction.time:>9}  ${instruction.address:04X} {instruction.operation:<15}')
        self.count += 1
        if self.count >= self.max_operations > 0:
            print(f'Stopped at {simulator.pc} after {self.count} operations')
            return True
        if simulator.pc == self.end:
            return True
        if simulator.pc == 16:
            a = simulator.registers['A']
            if a >= 32:
                self.msg += chr(a)
                sys.stdout.write(self.msg + chr(8) * len(self.msg))
                sys.stdout.flush()
            elif a == 13:
                if self.msg.strip():
                    print(f'{self.msg} ({self.count} operations)')
                else:
                    print()
                self.msg = ''

def run(romfile, snafile, options):
    snapshot, start = make_snapshot(snafile, None, options.start)[0:2]
    snapshot[23692] = 255 # Inhibit 'scroll?' prompt
    rom = read_bin_file(romfile, 16384)
    snapshot[:len(rom)] = rom
    if options.test:
        addr = 32768
        while snapshot[addr:addr + 6] != [1, 0, 0, 33, 122, 136]:
            addr += 1
        snapshot[addr + 1] = options.test
        test_addr = 34938 + options.test * 2
        snapshot[addr + 4:addr + 6] = (test_addr % 256, test_addr // 256)
    simulator = Simulator(snapshot)
    tracer = Tracer(options.verbose, options.max_operations, options.end)
    simulator.add_tracer(tracer)
    begin = time.time()
    simulator.run(start)
    rt = time.time() - begin
    z80t = simulator.tstates / 3500000
    speed = z80t / rt
    print(f'Z80 execution time: {simulator.tstates} T-states ({z80t:.03f}s)')
    print(f'Instructions executed: {tracer.count}')
    print(f'Simulation time: {rt:.03f}s (x{speed:.02f})')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        usage='{} [options] rom.bin FILE'.format(os.path.basename(sys.argv[0])),
        description="Run RAXOFT Z80 tests on a SkoolKit Simulator instance. "
                    "FILE must be a snapshot that contains the tests.",
        add_help=False
    )
    parser.add_argument('romfile', help=argparse.SUPPRESS, nargs='?')
    parser.add_argument('z80file', help=argparse.SUPPRESS, nargs='?')
    group = parser.add_argument_group('Options')
    group.add_argument('--max-operations', metavar='MAX', type=int, default=0,
                       help='Maximum number of instructions to execute.')
    group.add_argument('-e', '--end', metavar='ADDR', type=integer, default=32912,
                       help='End execution at this address (default: 32912).')
    group.add_argument('-s', '--start', metavar='ADDR', type=integer, default=32768,
                       help='Start execution at this address (default: 32768).')
    group.add_argument('-t', '--test', metavar='TEST', type=int, default=0,
                       help='Start at this test (default: 0).')
    group.add_argument('-v', '--verbose', action='count', default=0,
                       help="Show executed instructions.")
    namespace, unknown_args = parser.parse_known_args()
    if unknown_args or namespace.z80file is None:
        parser.exit(2, parser.format_help())
    run(namespace.romfile, namespace.z80file, namespace)
