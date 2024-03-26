#!/usr/bin/env python3

import argparse
import array
from collections import defaultdict
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

from skoolkit import ROM48, CSimulator, CCMIOSimulator, integer, read_bin_file
from skoolkit.cmiosimulator import CMIOSimulator
from skoolkit.simulator import Simulator
from skoolkit.simutils import PC, T
from skoolkit.tap2sna import get_tap_blocks, sim_load

STOP = 0x8094

class Options:
    start = None
    ram_ops = ()
    reg = []
    state = []
    tape_analysis = False
    accelerator = None
    machine = None
    load = None
    cmio = 0
    in_flags = 0
    pause = 1
    first_edge = 0
    polarity = 0
    finish_tape = 0
    accelerate_dec_a = 1
    fast_load = 1
    timeout = 60
    trace = None

class Tracer:
    def __init__(self):
        self.failed = False
        self.msg = ''

    def run(self, simulator):
        opcodes = simulator.opcodes
        memory = simulator.memory
        registers = simulator.registers
        pc = registers[PC]

        while True:
            opcodes[memory[pc]]()
            pc = registers[24]
            if pc == 16:
                self.rst16_cb(registers[0])
            elif pc == STOP:
                break

    def read_port(self, registers, port):
        if port % 256 == 0xFE:
            return 0xBF
        return 0xFF

    def rst16_cb(self, a):
        if a >= 32:
            self.msg += chr(a)
        elif a == 13:
            if self.msg.strip():
                print(self.msg)
                if self.msg.endswith(' tests failed.'):
                    self.failed = True
            else:
                print()
            self.msg = ''

def load_tap(tapfile):
    tap_blocks = get_tap_blocks(read_bin_file(tapfile))
    options = Options()
    snapshot = [0] * 65536
    rom = read_bin_file(ROM48)
    snapshot[:len(rom)] = rom
    snapshot[0x4000:] = sim_load(tap_blocks, options, defaultdict(str))
    for r in options.reg:
        if r.startswith('PC='):
            return int(r[3:]), snapshot

def run(tapfile, options):
    if options.csim and CSimulator is None:
        sys.stderr.write('ERROR: CSimulator is not available\n')
        sys.exit(1)
    if options.ccmio and CCMIOSimulator is None:
        sys.stderr.write('ERROR: CCMIOSimulator is not available\n')
        sys.exit(1)
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
    c = options.csim or options.ccmio
    if c:
        simulator_cls = CCMIOSimulator if options.ccmio else CSimulator
    else:
        simulator_cls = CMIOSimulator if options.cmio else Simulator
    simulator = simulator_cls(snapshot, {'PC': start})
    tracer = Tracer()
    simulator.set_tracer(tracer)
    begin = time.time()
    if c:
        simulator.exec_with_cb(STOP, tracer.rst16_cb)
    else:
        tracer.run(simulator)
    rt = time.time() - begin
    failed = tracer.failed
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
    group.add_argument('--ccmio', action='store_true',
                       help="Run tests with CCMIOSimulator.")
    group.add_argument('--cmio', action='store_true',
                       help="Run tests with CMIOSimulator.")
    group.add_argument('--csim', action='store_true',
                       help="Run tests with CSimulator.")
    group.add_argument('--sim', action='store_true',
                       help="Run tests with Simulator (this is the default).")
    group.add_argument('-t', '--test', metavar='TEST', type=int, default=0,
                       help='Start at this test (default: 0).')
    group.add_argument('-T', '--stop', metavar='TEST', type=int, default=0,
                       help='Stop at this test.')
    namespace, unknown_args = parser.parse_known_args()
    if unknown_args or namespace.tapfile is None:
        parser.exit(2, parser.format_help())
    sys.exit(run(namespace.tapfile, namespace))
