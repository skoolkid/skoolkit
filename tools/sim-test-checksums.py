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

def generate(name, tclass, args):
    simulator = Simulator([0] * 65536)
    tracer = tclass(*args)
    simulator.set_tracer(tracer)
    tracer.run(simulator)
    return tracer.checksum

def run(suites):
    for suite in suites:
        print(f"class {suite}Test(SimulatorTest):")
        for name, tclass, args in SUITES[suite][1:]:
            checksum = generate(name, tclass, args)
            targs = ', '.join(str(a) for a in args)
            print(f"    def test_{name.lower()}(self):")
            print(f"        self._verify({tclass.__name__}({targs}), '{checksum}')\n")

if __name__ == '__main__':
    width = max(len(k) for k in SUITES.keys())
    tests = '\n  '.join(f'{k:<{width}} - {v[0]}' for k, v in SUITES.items())
    parser = argparse.ArgumentParser(
        usage='{} SUITE [SUITE...]'.format(os.path.basename(sys.argv[0])),
        description="Generate Simulator test methods. SUITE may be one of the following:\n\n"
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
