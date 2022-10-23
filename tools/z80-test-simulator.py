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
from skoolkit.simulator import Simulator, A
from skoolkit.tap2sna import get_tap_blocks, sim_load

class Options:
    start = None
    reg = []
    state = []

class Tracer:
    def __init__(self):
        self.msg = ''
        self.count = 0
        self.failed = False

    def trace(self, simulator, address):
        self.count += 1
        if simulator.pc == 16:
            a = simulator.registers[A]
            if a >= 32:
                self.msg += chr(a)
                sys.stdout.write(self.msg + chr(8) * len(self.msg))
                sys.stdout.flush()
            elif a == 13:
                if self.msg.strip():
                    print(self.msg)
                    if self.msg.endswith(' tests failed.'):
                        self.failed = True
                        return True
                    if self.msg.endswith('all tests passed.'):
                        return True
                else:
                    print()
                self.msg = ''

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
    simulator = Simulator(snapshot)
    tracer = None
    if options.quiet:
        stop = 32850
        print('Running tests')
    else:
        tracer = Tracer()
        simulator.set_tracer(tracer)
        stop = None
    begin = time.time()
    simulator.run(start, stop)
    rt = time.time() - begin
    z80t = simulator.tstates / 3500000
    speed = z80t / rt
    if tracer is None:
        failed = simulator.registers[A]
        if failed:
            print(f'{failed} test(s) failed')
        else:
            print('All tests passed')
    print(f'Z80 execution time: {simulator.tstates} T-states ({z80t:.03f}s)')
    print(f'Simulation time: {rt:.03f}s (x{speed:.02f})')
    if tracer:
        failed = tracer.failed
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
    group.add_argument('-q', '--quiet', action='store_true',
                       help="Don't show test progress.")
    namespace, unknown_args = parser.parse_known_args()
    if unknown_args or namespace.tapfile is None:
        parser.exit(2, parser.format_help())
    sys.exit(run(namespace.tapfile, namespace))
