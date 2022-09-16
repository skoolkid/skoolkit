#!/usr/bin/env python3

import argparse
import hashlib
import os
import sys

SKOOLKIT_HOME = os.environ.get('SKOOLKIT_HOME')
if not SKOOLKIT_HOME:
    sys.stderr.write('SKOOLKIT_HOME is not set; aborting\n')
    sys.exit(1)
if not os.path.isdir(SKOOLKIT_HOME):
    sys.stderr.write('SKOOLKIT_HOME={}; directory not found\n'.format(SKOOLKIT_HOME))
    sys.exit(1)
sys.path.insert(0, f'{SKOOLKIT_HOME}')

from skoolkit.simulator import Simulator

class AFRTracer:
    def __init__(self, start, reg):
        self.start = start
        self.reg = reg
        self.count = 0x1FFFF
        self.data = bytearray()
        self.checksum = None

    def trace(self, simulator, instruction):
        if instruction.time > 0:
            self.data.extend((simulator.registers['A'], simulator.registers['F']))
        if self.count < 0:
            self.checksum = hashlib.md5(self.data).hexdigest()
            return True
        simulator.registers['F'] = self.count >> 16
        simulator.registers['A'] = (self.count >> 8) & 0xFF
        simulator.registers[self.reg] = self.count & 0xFF
        simulator.registers['PC'] = self.start
        self.count -= 1

class AFTracer:
    def __init__(self, start):
        self.start = start
        self.count = 0x1FF
        self.data = bytearray()
        self.checksum = None

    def trace(self, simulator, instruction):
        if instruction.time > 0:
            self.data.extend((simulator.registers['A'], simulator.registers['F']))
        if self.count < 0:
            self.checksum = hashlib.md5(self.data).hexdigest()
            return True
        simulator.registers['F'] = self.count >> 8
        simulator.registers['A'] = self.count & 0xFF
        simulator.registers['PC'] = self.start
        self.count -= 1

def generate(name, reg, *opcodes):
    start = 32768
    snapshot = [0] * 65536
    snapshot[start:start + len(opcodes)] = opcodes
    simulator = Simulator(snapshot)
    if reg:
        tracer = AFRTracer(start, reg)
    else:
        tracer = AFTracer(start)
    simulator.set_tracer(tracer)
    simulator.run(start)
    print(f"{name} = '{tracer.checksum}'")

SUITES = {
    'ALO': (
        ('ADD_A_r', 'B', (0x80,)),
        ('ADD_A_A', '', (0x87,)),
        ('ADC_A_r', 'B', (0x88,)),
        ('ADC_A_A', '', (0x8F,)),
        ('SUB_r', 'B', (0x90,)),
        ('SUB_A', '', (0x97,)),
        ('SBC_A_r', 'B', (0x98,)),
        ('SBC_A_A', '', (0x9F,)),
        ('AND_r', 'B', (0xA0,)),
        ('AND_A', '', (0xA7,)),
        ('XOR_r', 'B', (0xA8,)),
        ('XOR_A', '', (0xAF,)),
        ('OR_r', 'B', (0xB0,)),
        ('OR_A', '', (0xB7,)),
        ('CP_r', 'B', (0xB8,)),
        ('CP_A', '', (0xBF,)),
    )
}

def run(suites):
    for suite in suites:
        for name, reg, opcodes in SUITES[suite]:
            generate(name, reg, *opcodes)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        usage='{} SUITE [SUITE...]'.format(os.path.basename(sys.argv[0])),
        description="Generate Simulator test checksums. SUITE may be one of the following:\n\n"
                    "  ALL - All test suites\n"
                    "  ALO - Arithmetic/logic operations on the accumulator\n",
        formatter_class=argparse.RawTextHelpFormatter,
        add_help=False
    )
    parser.add_argument('suites', help=argparse.SUPPRESS, nargs='*')
    namespace, unknown_args = parser.parse_known_args()
    if unknown_args or not namespace.suites or (any(s != 'ALL' and s not in SUITES for s in namespace.suites)):
        parser.exit(2, parser.format_help())
    if any(s == 'ALL' for s in namespace.suites):
        namespace.suites = SUITES.keys()
    run(namespace.suites)
