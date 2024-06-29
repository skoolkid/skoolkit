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

from skoolkit import ROM48, tap2sna, CCMIOSimulator, read_bin_file
from skoolkit.cmiosimulator import CMIOSimulator
from skoolkit.simutils import PC, T

class Tracer:
    def __init__(self):
        self.msg = ''
        self.press_enter = 60
        self.passed = 0
        self.failed = 0

    def run(self, simulator):
        registers = simulator.registers
        if hasattr(simulator, 'opcodes'):
            opcodes = simulator.opcodes
            memory = simulator.memory
            pc = registers[PC]
            while True:
                opcodes[memory[pc]]()
                if registers[26] and registers[25] % 69888 < 32:
                    simulator.accept_interrupt(registers, memory, pc)
                pc = registers[24]
                if pc == 0x15F2:
                    if self.print_cb(registers[0]):
                        break
        else:
            while True:
                simulator.run(interrupts=True)
                if registers[24] == 0x15F2:
                    if self.print_cb(registers[0]):
                        break

    def read_port(self, registers, port):
        if self.press_enter > 0 and port == 0xBFFE:
            self.press_enter -= 1
            return 0xFE # Press ENTER
        return 0xFF

    def print_cb(self, a):
        if a >= 32:
            self.msg += chr(a)
        elif a == 13:
            if self.msg.strip():
                if self.msg == 'ZXSPECTRUMZXSPECTRUMZXSPECTRUMZX':
                    # Tests 36+ test floating bus emulation, so quit now
                    return True
                print(self.msg)
                if self.msg.endswith('Pass'):
                    self.passed += 1
                elif self.msg.endswith('Fail'):
                    self.failed += 1
            else:
                print()
            self.msg = ''
        return False

def write_snapshot(fname, ram, registers, state):
    global snapshot, reg
    snapshot = [0] * 65536
    rom = read_bin_file(ROM48)
    snapshot[:len(rom)] = rom
    snapshot[0x4000:] = ram
    reg = {}
    for spec in registers:
        s = spec.split('=', 1)
        reg[s[0]] = int(s[1])

def load_tap(tapfile):
    global snapshot, reg
    tap2sna.write_snapshot = write_snapshot
    tap2sna.main(('--start', '7997', tapfile))
    return snapshot, reg

def run(tapfile, options):
    if options.cmio:
        simulator_cls = CMIOSimulator
    else:
        if CCMIOSimulator is None:
            sys.stderr.write('ERROR: CCMIOSimulator is not available\n')
            sys.exit(1)
        simulator_cls = CCMIOSimulator
    snapshot, registers = load_tap(tapfile)
    simulator = simulator_cls(snapshot, registers, {'iff': 1})
    tracer = Tracer()
    simulator.set_tracer(tracer)
    begin = time.time()
    tracer.run(simulator)
    rt = time.time() - begin
    z80t = simulator.registers[T] / 3500000
    speed = z80t / rt
    print(f'\n{tracer.passed} tests passed\n{tracer.failed} tests failed\n')
    print(f'Z80 execution time: {simulator.registers[T]} T-states ({z80t:.03f}s)')
    print(f'Simulation time: {rt:.03f}s (x{speed:.02f})')
    return 1 if tracer.failed else 0

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        usage='{} [options] FILE'.format(os.path.basename(sys.argv[0])),
        description="Run 'ZX Spectrum Timing Tests 48K' on a SkoolKit CMIOSimulator instance. "
                    "FILE must be a TAP file that loads the tests.",
        add_help=False
    )
    parser.add_argument('tapfile', help=argparse.SUPPRESS, nargs='?')
    group = parser.add_argument_group('Options')
    group.add_argument('--ccmio', action='store_true',
                       help="Run tests with CCMIOSimulator (this is the default).")
    group.add_argument('--cmio', action='store_true',
                       help="Run tests with CMIOSimulator.")
    namespace, unknown_args = parser.parse_known_args()
    if unknown_args or namespace.tapfile is None:
        parser.exit(2, parser.format_help())
    sys.exit(run(namespace.tapfile, namespace))
