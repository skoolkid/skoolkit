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

from skoolkit import ROM48, integer, read_bin_file
from skoolkit.simulator import Simulator, A, PC, T
from skoolkit.tap2sna import get_tap_blocks, sim_load

class Options:
    start = None
    ram_ops = ()
    reg = []
    state = []
    accelerator = None
    fast_load = True

class Tracer:
    def __init__(self):
        self.count = 0
        self.failed = False

    def run(self, simulator):
        opcodes = simulator.opcodes
        memory = simulator.memory
        registers = simulator.registers
        pc = registers[PC]
        count = 0
        msg = ''

        while True:
            opcodes[memory[pc]]()
            pc = registers[24]
            count += 1
            if pc == 16:
                a = registers[0]
                if a >= 32:
                    msg += chr(a)
                elif a == 13:
                    if msg.strip():
                        print(msg)
                        if msg.endswith(' tests failed.'):
                            self.failed = True
                            self.count = count
                            break
                        if msg.endswith('all tests passed.'):
                            self.count = count
                            break
                    else:
                        print()
                    msg = ''

def load_tap(tapfile):
    tap_blocks = get_tap_blocks(read_bin_file(tapfile))
    options = Options()
    snapshot = [0] * 16384 + sim_load(tap_blocks, options)
    rom = read_bin_file(ROM48)
    snapshot[:len(rom)] = rom
    for r in options.reg:
        if r.startswith('PC='):
            return int(r[3:]), snapshot

def run(tapfile, options):
    start, snapshot = load_tap(tapfile)
    print()
    snapshot[23692] = 255 # Inhibit 'scroll?' prompt
    if options.test:
        addr = 32768
        while snapshot[addr:addr + 6] != [1, 0, 0, 33, 122, 136]:
            addr += 1
        snapshot[addr + 1] = options.test
        test_addr = 34938 + options.test * 2
        snapshot[addr + 4:addr + 6] = (test_addr % 256, test_addr // 256)
    if options.stop > 0:
        test_addr = 34938 + options.stop * 2
        snapshot[test_addr:test_addr + 2] = (0, 0)
    simulator = Simulator(snapshot, {'PC': start})
    if options.quiet:
        tracer = None
        print('Running tests')
        begin = time.time()
        simulator.run(stop=32850)
    else:
        tracer = Tracer()
        begin = time.time()
        tracer.run(simulator)
    rt = time.time() - begin
    if tracer:
        failed = tracer.failed
    else:
        failed = simulator.registers[A]
        if failed:
            print(f'{failed} test(s) failed')
        else:
            print('All tests passed')
    z80t = simulator.registers[T] / 3500000
    speed = z80t / rt
    print(f'Z80 execution time: {simulator.registers[T]} T-states ({z80t:.03f}s)')
    print(f'Simulation time: {rt:.03f}s (x{speed:.02f})')
    return 1 if failed else 0

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        usage='{} [options] FILE'.format(os.path.basename(sys.argv[0])),
        description="Run RAXOFT Z80 tests (v1.2) on a SkoolKit Simulator instance. "
                    "FILE must be a TAP file that loads the tests (e.g. z80doc.tap).",
        add_help=False
    )
    parser.add_argument('tapfile', help=argparse.SUPPRESS, nargs='?')
    group = parser.add_argument_group('Options')
    group.add_argument('-t', '--test', metavar='TEST', type=int, default=0,
                       help='Start at this test (default: 0).')
    group.add_argument('-T', '--stop', metavar='TEST', type=int, default=0,
                       help='Stop at this test.')
    group.add_argument('-q', '--quiet', action='store_true',
                       help="Don't show test progress.")
    namespace, unknown_args = parser.parse_known_args()
    if unknown_args or namespace.tapfile is None:
        parser.exit(2, parser.format_help())
    sys.exit(run(namespace.tapfile, namespace))
