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
from skoolkit.pagingtracer import Memory
from skoolkit.simutils import PC, T

class Tracer:
    def __init__(self):
        self.failed = 0
        self.msg = ''
        self.prev_x = -1

    def run(self, simulator):
        memory = simulator.memory
        registers = simulator.registers
        c = not hasattr(simulator, 'opcodes')
        if not c:
            opcodes = simulator.opcodes
            frame_duration = simulator.frame_duration
            int_active = simulator.int_active
        pc = registers[PC]

        while True:
            if c:
                simulator.run(interrupts=True)
            else:
                opcodes[memory[pc]]()
                if registers[26] and registers[25] % frame_duration < int_active:
                    simulator.accept_interrupt(registers, memory, pc)
            pc = registers[24]
            if pc == 0xA66C:
                self.print_a(registers[0], memory[0xA667] % 32)
            elif pc == 0x808B:
                break

    def print_a(self, a, x):
        if x <= self.prev_x:
            msg = self.msg.rstrip()
            if msg:
                print(msg)
                if msg.startswith('Failed'):
                    self.failed = int(msg[7:9])
            self.msg = ' ' * x
        elif x > self.prev_x + 1:
            self.msg += ' ' * (x - self.prev_x - 1)
        self.msg += chr(a)
        self.prev_x = x

def write_snapshot(fname, ram, registers, state):
    global pc, snapshot
    if len(ram) == 8:
        # 128K
        for spec in state:
            if spec.startswith('7ffd='):
                out7ffd = int(spec[5:])
                break
        snapshot = Memory(ram, out7ffd)
    else:
        # 48K
        snapshot = [0] * 65536
        rom = read_bin_file(ROM48)
        snapshot[:len(rom)] = rom
        snapshot[0x4000:] = ram
    for r in registers:
        if r.startswith('PC='):
            pc = int(r[3:])
            break

def load_tape(tapefile, is128k):
    global pc, snapshot
    tap2sna.write_snapshot = write_snapshot
    machine = '128' if is128k else '48'
    tap2sna.main(('--start', '32770', '-c', f'machine={machine}', tapefile))
    return pc, snapshot

def run(tapefile, options):
    c = options.ccmio
    if c and CCMIOSimulator is None:
        sys.stderr.write('ERROR: CCMIOSimulator is not available\n')
        sys.exit(1)
    start, snapshot = load_tape(tapefile, options.m128)
    simulator_cls = CCMIOSimulator if c else CMIOSimulator
    simulator = simulator_cls(snapshot, {'PC': start})
    tracer = Tracer()
    simulator.set_tracer(tracer)
    begin = time.time()
    tracer.run(simulator)
    rt = time.time() - begin
    z80t = simulator.registers[T] / 3500000
    speed = z80t / rt
    print(f'Z80 execution time: {simulator.registers[T]} T-states ({z80t:.03f}s)')
    print(f'Simulation time: {rt:.03f}s (x{speed:.02f})')
    return 1 if tracer.failed else 0

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        usage='{} [options] FILE'.format(os.path.basename(sys.argv[0])),
        description="Run Michael Sapach's MEMPTR tests on a SkoolKit (C)CMIOSimulator instance. "
                    "FILE must be a tape file that loads the tests (e.g. cpd-test1250429.tzx).",
        add_help=False
    )
    parser.add_argument('tapefile', help=argparse.SUPPRESS, nargs='?')
    group = parser.add_argument_group('Options')
    group.add_argument('--128', dest='m128', action='store_true',
                       help="Run tests on a 128K machine.")
    group.add_argument('--ccmio', action='store_true',
                       help="Run tests with CCMIOSimulator.")
    group.add_argument('--cmio', action='store_true',
                       help="Run tests with CMIOSimulator (this is the default).")
    namespace, unknown_args = parser.parse_known_args()
    if unknown_args or namespace.tapefile is None:
        parser.exit(2, parser.format_help())
    sys.exit(run(namespace.tapefile, namespace))
