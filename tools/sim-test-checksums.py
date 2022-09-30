#!/usr/bin/env python3

import argparse
import os
import sys

SKOOLKIT_HOME = os.environ.get('SKOOLKIT_HOME')
if not SKOOLKIT_HOME:
    sys.stderr.write('SKOOLKIT_HOME is not set; aborting\n')
    sys.exit(1)
if not os.path.isdir(SKOOLKIT_HOME):
    sys.stderr.write('SKOOLKIT_HOME={}; directory not found\n'.format(SKOOLKIT_HOME))
    sys.exit(1)
sys.path.insert(0, f'{SKOOLKIT_HOME}/tests')
sys.path.insert(0, f'{SKOOLKIT_HOME}')

from skoolkit.simulator import Simulator
from sim_test_tracers import *

def generate(name, tclass, args, opcodes):
    start = 32768
    snapshot = [0] * 65536
    snapshot[start:start + len(opcodes)] = opcodes
    simulator = Simulator(snapshot)
    tracer = tclass(start, *args)
    simulator.add_tracer(tracer)
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
    'RA1': (
        'RLCA/RRCA/RLA/RRA instructions',
        ('RLCA', AFTracer, (0xFFFF,), (0x07,)),
        ('RRCA', AFTracer, (0xFFFF,), (0x0F,)),
        ('RLA',  AFTracer, (0xFFFF,), (0x17,)),
        ('RRA',  AFTracer, (0xFFFF,), (0x1F,)),
    ),
    'SRO': (
        'Shift/rotate instructions',
        ('RLC_r', FRTracer, ('B',), (0xCB, 0x00)),
        ('RRC_r', FRTracer, ('B',), (0xCB, 0x08)),
        ('RL_r',  FRTracer, ('B',), (0xCB, 0x10)),
        ('RR_r',  FRTracer, ('B',), (0xCB, 0x18)),
        ('SLA_r', FRTracer, ('B',), (0xCB, 0x20)),
        ('SRA_r', FRTracer, ('B',), (0xCB, 0x28)),
        ('SLL_r', FRTracer, ('B',), (0xCB, 0x30)),
        ('SRL_r', FRTracer, ('B',), (0xCB, 0x38)),
    ),
    'INC': (
        'INC/DEC instructions',
        ('INC_r', FRTracer, ('B',), (0x04,)),
        ('DEC_r', FRTracer, ('B',), (0x05,)),
    ),
    'AHL': (
        '16-bit ADD/ADC/SBC instructions',
        ('ADD_HL_rr', HLRRFTracer, ('HL', 'BC'), (0x09,)),
        ('ADC_HL_rr', HLRRFTracer, ('HL', 'BC'), (0xED, 0x4A,)),
        ('SBC_HL_rr', HLRRFTracer, ('HL', 'BC'), (0xED, 0x42,)),
        ('ADD_HL_HL', HLFTracer, ('HL',), (0x29,)),
        ('ADC_HL_HL', HLFTracer, ('HL',), (0xED, 0x6A,)),
        ('SBC_HL_HL', HLFTracer, ('HL',), (0xED, 0x62,)),
    ),
    'BLK': (
        'Block LD/CP/IN/OUT instructions',
        ('LDI',  BlockTracer, (), (0xED, 0xA0)),
        ('LDD',  BlockTracer, (), (0xED, 0xA8)),
        ('CPI',  BlockTracer, (), (0xED, 0xA1)),
        ('CPD',  BlockTracer, (), (0xED, 0xA9)),
        ('INI',  BlockTracer, (), (0xED, 0xA2)),
        ('IND',  BlockTracer, (), (0xED, 0xAA)),
        ('OUTI', BlockTracer, (), (0xED, 0xA3)),
        ('OUTD', BlockTracer, (), (0xED, 0xAB)),
    ),
    'BIT': (
        'BIT n,[r,xy] instructions',
        ('BIT_n_r', BitTracer, ('B',), (0xCB, 0x40)),
        ('BIT_n_xy', BitTracer, ('(IX+d)',), (0xDD, 0xCB, 0x00, 0x46)),
    ),
    'RRD': (
        'RRD/RLD instructions',
        ('RRD', RRDRLDTracer, (), (0xED, 0x67)),
        ('RLD', RRDRLDTracer, (), (0xED, 0x6F)),
    ),
    'INR': (
        'IN r,(C) instructions',
        ('IN_r_C', InTracer, ('A',), (0xED, 0x78)),
        ('IN_F_C', InTracer, ('F',), (0xED, 0x70)),
    ),
    'AIR': (
        'LD A,I/R instructions',
        ('LD_A_I', AIRTracer, ('I',), (0xED, 0x57)),
        ('LD_A_R', AIRTracer, ('R',), (0xED, 0x5F)),
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
