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
    sys.stderr.write(f'SKOOLKIT_HOME={SKOOLKIT_HOME}; directory not found\n')
    sys.exit(1)
sys.path.insert(0, SKOOLKIT_HOME)

from skoolkit import ROM48, tap2sna, CSimulator, CCMIOSimulator, read_bin_file
from skoolkit.cmiosimulator import CMIOSimulator
from skoolkit.simulator import Simulator
from skoolkit.simutils import PC, T

START = 0x8057
STOP = 0x8067

# Ignore tests that require MEMPTR emulation
IGNORE_TESTS = ('BIT n,(HL)', 'CB (00-FF) 5+3 ROM', 'CB (00-FF) 5+3 RAM')

class Tracer:
    def __init__(self):
        self.failed = 0
        self.count = 0
        self.msg = ''
        self.skip = False

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

    def rst16_cb(self, a):
        if a >= 32:
            self.msg += chr(a)
        elif a == 13:
            if self.msg.strip():
                if self.msg.startswith(IGNORE_TESTS):
                    self.skip = True
                else:
                    if not ('expected' in self.msg and self.skip):
                        print(self.msg)
                    if self.msg.endswith(' failed'):
                        self.failed += 1
                        self.count += 1
                    elif self.msg.endswith(' passed'):
                        self.count += 1
                    self.skip = False
            else:
                print()
            self.msg = ''

def write_snapshot(fname, ram, registers, state):
    global snapshot
    snapshot = [0] * 65536
    rom = read_bin_file(ROM48)
    snapshot[:len(rom)] = rom
    snapshot[0x4000:] = ram
    snapshot[0x5C8C] = 0xFF # Inhibit 'scroll?' prompt
    snapshot[0x80DA] = 0xC9 # Disable CLS routine (which enables 'scroll?')

def load_tap(tapfile):
    global snapshot
    tap2sna.write_snapshot = write_snapshot
    tap2sna.main([tapfile])
    return START, snapshot

def run(tapfile, options):
    if options.csim and CSimulator is None:
        sys.stderr.write('ERROR: CSimulator is not available\n')
        sys.exit(1)
    if options.ccmio and CCMIOSimulator is None:
        sys.stderr.write('ERROR: CCMIOSimulator is not available\n')
        sys.exit(1)
    start, snapshot = load_tap(tapfile)
    print()
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
    if failed:
        msg = f'{failed}/{tracer.count} tests failed.'
    else:
        msg = 'All tests passed.'
    print(f'\n{msg}\n')
    z80t = simulator.registers[T] / 3500000
    speed = z80t / rt
    print(f'Z80 execution time: {simulator.registers[T]} T-states ({z80t:.03f}s)')
    print(f'Simulation time: {rt:.03f}s (x{speed:.02f})')
    return 1 if failed else 0

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        usage='{} [options] FILE'.format(os.path.basename(sys.argv[0])),
        description="Run Mark Woodmass's Z80 flags tests on a SkoolKit Simulator instance. "
                    "FILE must be a TAP file that loads the tests.",
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
    namespace, unknown_args = parser.parse_known_args()
    if unknown_args or namespace.tapfile is None:
        parser.exit(2, parser.format_help())
    sys.exit(run(namespace.tapfile, namespace))
