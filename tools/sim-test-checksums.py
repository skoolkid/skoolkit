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
from sim_test_tracers import *

def generate(name, tclass, args, opcodes):
    start = 32768
    snapshot = [0] * 65536
    snapshot[start:start + len(opcodes)] = opcodes
    simulator = Simulator(snapshot)
    tracer = tclass(start, *args)
    simulator.set_tracer(tracer)
    simulator.run(start)
    print(f"{name} = '{tracer.checksum}'")

SUITES = {
    'ALO': (
        'Arithmetic/logic operations on the accumulator',
        ('ADD_A_r', AFRTracer, ('B',), (0x80,)),
        ('ADD_A_A', AFTracer,  (),     (0x87,)),
        ('ADC_A_r', AFRTracer, ('B',), (0x88,)),
        ('ADC_A_A', AFTracer,  (),     (0x8F,)),
        ('SUB_r',   AFRTracer, ('B',), (0x90,)),
        ('SUB_A',   AFTracer,  (),     (0x97,)),
        ('SBC_A_r', AFRTracer, ('B',), (0x98,)),
        ('SBC_A_A', AFTracer,  (),     (0x9F,)),
        ('AND_r',   AFRTracer, ('B',), (0xA0,)),
        ('AND_A',   AFTracer,  (),     (0xA7,)),
        ('XOR_r',   AFRTracer, ('B',), (0xA8,)),
        ('XOR_A',   AFTracer,  (),     (0xAF,)),
        ('OR_r',    AFRTracer, ('B',), (0xB0,)),
        ('OR_A',    AFTracer,  (),     (0xB7,)),
        ('CP_r',    AFRTracer, ('B',), (0xB8,)),
        ('CP_A',    AFTracer,  (),     (0xBF,)),
    ),
    'DAA': (
        'DAA instruction',
        ('DAA', DAATracer, (), (0x27,)),
    ),
    'CF': (
        'SCF/CCF instructions',
        ('SCF', FTracer, (), (0x37,)),
        ('CCF', FTracer, (), (0x3F,)),
    ),
    'CPL': (
        'CPL instruction',
        ('CPL', AFTracer, (0xFF,), (0x2F,)),
    ),
    'NEG': (
        'NEG instruction',
        ('NEG', AFTracer, (0xFF,), (0xED, 0x44)),
    ),
}

def run(suites):
    for suite in suites:
        for name, tclass, args, opcodes in SUITES[suite][1:]:
            generate(name, tclass, args, opcodes)

if __name__ == '__main__':
    width = max(len(k) for k in SUITES.keys())
    tests = '\n  '.join(f'{k:<{width}} - {v[0]}' for k, v in SUITES.items())
    parser = argparse.ArgumentParser(
        usage='{} SUITE [SUITE...]'.format(os.path.basename(sys.argv[0])),
        description="Generate Simulator test checksums. SUITE may be one of the following:\n\n"
                    "  ALL - All test suites\n  " + tests,
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
