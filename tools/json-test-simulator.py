#!/usr/bin/env python3
import argparse
import json
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

from skoolkit import CSimulator, CCMIOSimulator
from skoolkit.cmiosimulator import CMIOSimulator
from skoolkit.simulator import Simulator
from skoolkit.simutils import (A, F, B, C, D, E, H, L, IXh, IXl, IYh, IYl, SP,
                               I, R, xA, xF, xB, xC, xD, xE, xH, xL, PC, T,
                               IFF, IM)
from skoolkit.traceutils import disassemble

REGISTERS = {
    "a": A,
    "b": B,
    "c": C,
    "d": D,
    "e": E,
    "f": F,
    "h": H,
    "l": L,
    "i": I,
    "r": R,
    "af_": (xA, xF),
    "bc_": (xB, xC),
    "de_": (xD, xE),
    "hl_": (xH, xL),
    "ix": (IXh, IXl),
    "iy": (IYh, IYl),
    "pc": PC,
    "sp": SP,
    "iff1": IFF,
    "im": IM,
}

class Tracer:
    def __init__(self):
        self.ports_r = {}
        self.ports_w = {}

    def read_port(self, registers, port):
        if port in self.ports_r:
            return self.ports_r[port]
        return 0xFF

    def write_port(self, registers, port, value):
        self.ports_w[port] = value

def init_simulator(simulator, tracer, initial, ports):
    registers = simulator.registers
    memory = simulator.memory
    tracer.ports_r.clear()
    tracer.ports_w.clear()
    for k, v in initial.items():
        r = REGISTERS.get(k)
        if r is not None:
            if isinstance(r, int):
                registers[r] = v
            else:
                registers[r[0]] = v // 256
                registers[r[1]] = v % 256
        elif k == 'ram':
            for a, b in v:
                memory[a] = b
    for port, value, mode in ports:
        if mode == 'r':
            tracer.ports_r[port] = value

def check_simulator(simulator, tracer, final, ports, instruction):
    registers = simulator.registers
    memory = simulator.memory
    errors = []
    for k, exp_v in final.items():
        r = REGISTERS.get(k)
        if r is not None:
            if isinstance(r, int):
                v = registers[r]
            else:
                v = registers[r[0]] * 256 + registers[r[1]]
            if r == F:
                if instruction in ('CCF', 'SCF'):
                    exp_v = (exp_v & 0xD7) | (registers[A] & 0x28)
                elif instruction in ('LD A,I', 'LD A,R'):
                    exp_v = (exp_v & 0xFB) + registers[IFF] * 0x04
                elif instruction.startswith('BIT ') and instruction.endswith(',(HL)'):
                    at_hl = memory[registers[L] + 256 * registers[H]]
                    exp_v = (exp_v & 0xD7) | (at_hl & 0x28)
            elif r == IFF:
                if instruction in ('RETI', 'RETN'):
                    exp_v = registers[IFF]
            elif r == PC:
                if instruction == 'HALT':
                    exp_v = registers[PC]
            if v != exp_v:
                if r == F:
                    errors.append(f'{k}={v:08b} (expected {exp_v:08b})')
                else:
                    errors.append(f'{k}={v} (expected {exp_v})')
        elif k == 'ram':
            for a, exp_b in exp_v:
                if a > 0x3FFF:
                    b = memory[a]
                    if b != exp_b:
                        errors.append(f'({a})={b} (expected {exp_b})')
    for port, exp_v, mode in ports:
        if mode == 'w':
            v = tracer.ports_w.get(port)
            if v != exp_v:
                errors.append(f'port {port} has value {v} (expected {exp_v})')
    return errors

def get_exp_changes(initial, final, options):
    exp_changes = []
    for k, v in initial.items():
        if k in REGISTERS or k in ('ram', 'iff2'):
            fv = final[k]
            if options.verbose > 1 or fv != v:
                if k == 'f':
                    exp_changes.append(f'{k}: {v:08b} -> {fv:08b}')
                else:
                    exp_changes.append(f'{k}: {v} -> {fv}')
    return exp_changes

def run_tests(simulator, jsonfiles, options):
    registers = simulator.registers
    memory = simulator.memory
    tracer = Tracer()
    simulator.set_tracer(tracer)
    failed = []
    count = 0
    for jsonfile in jsonfiles:
        with open(jsonfile) as f:
            tests = json.load(f)
        for test in tests:
            name = test['name']
            if options.test_name is None or name == options.test_name:
                ports = test.get('ports', [])
                init_simulator(simulator, tracer, test['initial'], ports)
                pc = registers[PC]
                instructions = [disassemble(memory, pc, '', '', '')[0]]
                registers[T] = 10000
                simulator.run()
                if instructions[0] in ('DEFB 221', 'DEFB 253'):
                    # Advance beyond invalid 0xDD/0xFD prefix
                    instructions.append(disassemble(memory, registers[PC], '', '', '')[0])
                    simulator.run()
                errors = check_simulator(simulator, tracer, test['final'], ports, instructions[-1])
                i = ': '.join(instructions)
                if errors:
                    print(f'[FAIL] {name} ({i})')
                    exp_changes = get_exp_changes(test['initial'], test['final'], options)
                    failed.append((jsonfile, name, f'{pc:05} {i}', errors, exp_changes))
                elif options.verbose:
                    print(f'[ OK ] {name} ({i})')
                count += 1
    return failed, count

def run(jsonfiles, options):
    if options.csim and CSimulator is None:
        sys.stderr.write('ERROR: CSimulator is not available\n')
        sys.exit(1)
    if options.ccmio and CCMIOSimulator is None:
        sys.stderr.write('ERROR: CCMIOSimulator is not available\n')
        sys.exit(1)
    c = options.csim or options.ccmio
    if c:
        simulator_cls = CCMIOSimulator if options.ccmio else CSimulator
    else:
        simulator_cls = CMIOSimulator if options.cmio else Simulator
    simulator = simulator_cls([0] * 65536)
    begin = time.time()
    failed, count = run_tests(simulator, jsonfiles, options)
    rt = time.time() - begin
    z80t = simulator.registers[T] / 3500000
    speed = z80t / rt
    if failed:
        if options.verbose:
            for jsonfile, name, instruction, errors, exp_changes in failed:
                print(f'{jsonfile}: {name}')
                print
                for line in exp_changes:
                    print(f'  {line}')
                print(f'  instruction: {instruction}')
                for error in errors:
                    print(f'  {error}')
                print()
        print(f'{len(failed)}/{count} test(s) failed')
    else:
        if count:
            if options.verbose:
                print()
            print(f'{count} test(s) passed')
        else:
            print('No tests run')
    print(f'\nRun time: {rt:.03f}s')
    return len(failed) > 0

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        usage='{} [options] FILE [FILE...]'.format(os.path.basename(sys.argv[0])),
        description="Run the tests in the specified JSON file(s). "
                    "The format of each JSON file should be the same as that used by the repository at https://github.com/SingleStepTests/z80.",
        add_help=False
    )
    parser.add_argument('jsonfiles', help=argparse.SUPPRESS, nargs='*')
    group = parser.add_argument_group('Options')
    group.add_argument('--ccmio', action='store_true',
                       help="Run tests with CCMIOSimulator.")
    group.add_argument('--cmio', action='store_true',
                       help="Run tests with CMIOSimulator.")
    group.add_argument('--csim', action='store_true',
                       help="Run tests with CSimulator.")
    group.add_argument('--sim', action='store_true',
                       help="Run tests with Simulator (this is the default).")
    group.add_argument('-t', dest='test_name', metavar='NAME',
                       help="Run only the test with this name.")
    group.add_argument('-v', dest='verbose', action='count', default=0,
                       help="Show details for each test. Do -vv for even more details.")
    namespace, unknown_args = parser.parse_known_args()
    if unknown_args or not namespace.jsonfiles:
        parser.exit(2, parser.format_help())
    sys.exit(run(namespace.jsonfiles, namespace))
