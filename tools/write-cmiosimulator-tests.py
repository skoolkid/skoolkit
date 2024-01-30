#!/usr/bin/env python3
import argparse
import os
from string import Template
import sys

REG8 = 'ABCDEHL'
REG8XY = ('IXh', 'IXl', 'IYh', 'IYl')
CONDITIONS = ('NZ', 'Z', 'NC', 'C', 'PO', 'PE', 'P', 'M')
SRO = ('RLC', 'RRC', 'RL', 'RR', 'SLA', 'SRA', 'SRL', 'SLL')
ALO_A = ('AND ', 'CP ', 'OR ', 'SUB ', 'XOR ', 'ADC A,', 'ADD A,', 'SBC A,')

ADDRESSES = {
    1: (16384, 32768),               # rr
    2: (16383, 16384, 32767, 32768), # rr, rr+1
    3: (16385, 16386, 32769, 32770), # sp-1, sp-2
}

GROUPS = (
    (
        'pc:4',
        (
            'NOP',
            *[f'LD {r1},{r2}' for r1 in REG8 for r2 in REG8],
            *[f'{op}{r}' for op in ALO_A for r in REG8],
            *[f'{op} {r}' for op in ('INC', 'DEC') for r in REG8],
            'EXX', "EX AF,AF'", 'EX DE,HL',
            'DAA', 'CPL', 'CCF', 'SCF', 'RLA', 'RRA', 'RLCA', 'RRCA',
            'JP (HL)', 'DI', 'EI', 'HALT'
        ),
        [{}]
    ),

    (
        'pc:4,pc+1:4',
        (
            'JP (IX)', 'JP (IY)',
            *[f'{op} {r}' for op in SRO for r in REG8],
            *[f'{op} {b},{r}' for op in ('BIT', 'SET', 'RES') for b in range(8) for r in REG8],
            'NEG', 'IM 0', 'IM 1', 'IM 2',
            *[f'{op}{r}' for op in ALO_A for r in REG8XY],
            *[f'{op} {r}' for op in ('INC', 'DEC') for r in REG8XY],
        ),
        [{}]
    ),

    (
        'pc:4,pc+1:4,ir:1',
        ('LD A,I', 'LD A,R', 'LD I,A', 'LD R,A'),
        [{'IR': ir} for ir in ADDRESSES[1]]
    ),

    (
        'pc:4,ir:1,ir:1',
        (
            'LD SP,HL',
            *[f'{op} {rr}' for op in ('INC', 'DEC') for rr in ('BC', 'DE', 'HL', 'SP')]
        ),
        [{'IR': ir} for ir in ADDRESSES[1]]
    ),

    (
        'pc:4,pc+1:4,ir:1,ir:1',
        ('LD SP,IX', 'LD SP,IY', 'INC IX', 'INC IY', 'DEC IX', 'DEC IY'),
        [{'IR': ir} for ir in ADDRESSES[1]]
    ),

    (
        'pc:4,ir:1,ir:1,ir:1,ir:1,ir:1,ir:1,ir:1',
        ('ADD HL,BC', 'ADD HL,DE', 'ADD HL,HL', 'ADD HL,SP'),
        [{'IR': ir} for ir in ADDRESSES[1]]
    ),

    (
        'pc:4,pc+1:4,ir:1,ir:1,ir:1,ir:1,ir:1,ir:1,ir:1',
        (
            'ADD IX,IX', 'ADD IY,IY',
            *[f'ADD {rr1},{rr2}' for rr1 in ('IX', 'IY') for rr2 in ('BC', 'DE', 'SP')],
            *[f'{op} HL,{rr}' for op in ('ADC', 'SBC') for rr in ('BC', 'DE', 'SP')]
        ),
        [{'IR': ir} for ir in ADDRESSES[1]]
    ),

    (
        'pc:4,pc+1:3',
        (
            *[f'LD {r},0' for r in REG8],
            *[f'{op}0' for op in ALO_A],
        ),
        [{}]
    ),

    (
        'pc:4,pc+1:4,pc+2:3',
        [f'LD {r},0' for r in REG8XY],
        [{}]
    ),

    *[
        (
            f'pc:4,{rr}:3',
            (f'LD A,({rr.upper()})', f'LD ({rr.upper()}),A'),
            [{rr.upper(): rv} for rv in ADDRESSES[1]]
        ) for rr in ('bc', 'de')
    ],

    (
        'pc:4,hl:3',
        (
            *[f'LD {r},(HL)' for r in REG8],
            *[f'LD (HL),{r}' for r in REG8],
            *[f'{op}(HL)' for op in ALO_A],
        ),
        [{'HL': hl} for hl in ADDRESSES[1]]
    ),

    *[
        (
            f'pc:4,pc+1:4,pc+2:3,pc+2:1,pc+2:1,pc+2:1,pc+2:1,pc+2:1,{rr}:3',
            (
                *[f'LD {r},({rr.upper()}+0)' for r in REG8],
                *[f'LD ({rr.upper()}+0),{r}' for r in REG8],
                *[f'{op}({rr.upper()}+0)' for op in ALO_A],
            ),
            [{rr.upper(): rv} for rv in ADDRESSES[1]]
        ) for rr in ('ix', 'iy')
    ],

    (
        'pc:4,pc+1:4,hl:3,hl:1',
        [f'BIT {b},(HL)' for b in range(8)],
        [{'HL': hl} for hl in ADDRESSES[1]]
    ),

    *[
        (
            f'pc:4,pc+1:4,pc+2:3,pc+3:3,pc+3:1,pc+3:1,{rr}:3,{rr}:1',
            [f'BIT {b},({rr.upper()}+0)' for b in range(8)],
            [{rr.upper(): rv} for rv in ADDRESSES[1]]
        ) for rr in ('ix', 'iy')
    ],

    (
        'pc:4,pc+1:3,pc+2:3',
        (
            'JP 0',
            *[f'JP {c},0' for c in CONDITIONS],
            *[f'LD {rr},0' for rr in ('BC', 'DE', 'HL', 'SP')]
        ),
        [{}]
    ),

    (
        'pc:4,pc+1:4,pc+2:3,pc+3:3',
        ('LD IX,0', 'LD IY,0'),
        [{}]
    ),

    (
        'pc:4,pc+1:3,hl:3',
        ['LD (HL),0'],
        [{'HL': hl} for hl in ADDRESSES[1]]
    ),

    *[
        (
            f'pc:4,pc+1:4,pc+2:3,pc+3:3,pc+3:1,pc+3:1,{rr}:3',
            [f'LD ({rr.upper()}+0),0'],
            [{rr.upper(): rv} for rv in ADDRESSES[1]]
        ) for rr in ('ix', 'iy')
    ],

    *[
        (
            f'pc:4,pc+1:3,pc+2:3,{addr:04x}:3',
            (f'LD A,(${addr:04X})', f'LD (${addr:04X}),A'),
            [{}]
        ) for addr in ADDRESSES[1]
    ],

    *[
        (
            f'pc:4,pc+1:3,pc+2:3,{addr:04x}:3,{addr+1:04x}:3',
            (f'LD HL,(${addr:04X})', f'LD (${addr:04X}),HL'),
            [{}]
        ) for addr in ADDRESSES[2]
    ],

    *[
        (
            f'pc:4,pc+1:4,pc+2:3,pc+3:3,{addr:04x}:3,{addr+1:04x}:3',
            (
                f'LD BC,(${addr:04X})', f'LD (${addr:04X}),BC',
                f'LD DE,(${addr:04X})', f'LD (${addr:04X}),DE',
                f'LD SP,(${addr:04X})', f'LD (${addr:04X}),SP',
                f'DEFW $6BED,${addr:04X}', # LD HL,(addr)
                f'DEFW $63ED,${addr:04X}', # LD (addr),HL
                f'LD IX,(${addr:04X})', f'LD (${addr:04X}),IX',
                f'LD IY,(${addr:04X})', f'LD (${addr:04X}),IY',
            ),
            [{}]
        ) for addr in ADDRESSES[2]
    ],

    (
        'pc:4,hl:3,hl:1,hl:3',
        ('INC (HL)', 'DEC (HL)'),
        [{'HL': hl} for hl in ADDRESSES[1]]
    ),

    (
        'pc:4,pc+1:4,hl:3,hl:1,hl:3',
        (
            *[f'SET {b},(HL)' for b in range(8)],
            *[f'RES {b},(HL)' for b in range(8)],
            *[f'{op} (HL)' for op in SRO]
        ),
        [{'HL': hl} for hl in ADDRESSES[1]]
    ),

    *[
        (
            f'pc:4,pc+1:4,pc+2:3,pc+2:1,pc+2:1,pc+2:1,pc+2:1,pc+2:1,{rr}:3,{rr}:1,{rr}:3',
            (f'INC ({rr.upper()}+0)', f'DEC ({rr.upper()}+0)'),
            [{rr.upper(): rv} for rv in ADDRESSES[1]]
        ) for rr in ('ix', 'iy')
    ],

    *[
        (
            f'pc:4,pc+1:4,pc+2:3,pc+3:3,pc+3:1,pc+3:1,{rr}:3,{rr}:1,{rr}:3',
            (
                *[f'SET {b},({rr.upper()}+0)' for b in range(8)],
                *[f'RES {b},({rr.upper()}+0)' for b in range(8)],
                *[f'{op} ({rr.upper()}+0)' for op in SRO]
            ),
            [{rr.upper(): rv} for rv in ADDRESSES[1]]
        ) for rr in ('ix', 'iy')
    ],

    (
        'pc:4,sp:3,sp+1:3',
        ('POP BC', 'POP DE', 'POP HL', 'POP AF', 'RET'),
        [{'SP': sp} for sp in ADDRESSES[2]]
    ),

    (
        'pc:4,pc+1:4,sp:3,sp+1:3',
        ('POP IX', 'POP IY', 'RETI', 'RETN'),
        [{'SP': sp} for sp in ADDRESSES[2]]
    ),

    # Return not made
    (
        'pc:4,ir:1',
        ('RET Z', 'RET C', 'RET PE', 'RET M'),
        [{'F': 0, 'IR': ir} for ir in ADDRESSES[1]]
    ),

    # Return not made
    (
        'pc:4,ir:1',
        ('RET NZ', 'RET NC', 'RET PO', 'RET P'),
        [{'F': 0xFF, 'IR': ir} for ir in ADDRESSES[1]]
    ),

    # Return made
    (
        'pc:4,ir:1,sp:3,sp+1:3',
        ('RET Z', 'RET C', 'RET PE', 'RET M'),
        [{'F': 0xFF, 'IR': ir, 'SP': sp} for ir in ADDRESSES[1] for sp in ADDRESSES[2]]
    ),

    # Return made
    (
        'pc:4,ir:1,sp:3,sp+1:3',
        ('RET NZ', 'RET NC', 'RET PO', 'RET P'),
        [{'F': 0x00, 'IR': ir, 'SP': sp} for ir in ADDRESSES[1] for sp in ADDRESSES[2]]
    ),

    (
        'pc:4,ir:1,sp-1:3,sp-2:3',
        (
            'PUSH BC', 'PUSH DE', 'PUSH HL', 'PUSH AF',
            *[f'RST {n}' for n in range(0, 64, 8)]
        ),
        [{'IR': ir, 'SP': sp} for ir in ADDRESSES[1] for sp in ADDRESSES[3]]
    ),

    (
        'pc:4,pc+1:4,ir:1,sp-1:3,sp-2:3',
        ('PUSH IX', 'PUSH IY'),
        [{'IR': ir, 'SP': sp} for ir in ADDRESSES[1] for sp in ADDRESSES[3]]
    ),

    # CALL not made
    (
        'pc:4,pc+1:3,pc+2:3',
        ('CALL Z,0', 'CALL C,0', 'CALL PE,0', 'CALL M,0'),
        [{'F': 0}]
    ),

    # CALL not made
    (
        'pc:4,pc+1:3,pc+2:3',
        ('CALL NZ,0', 'CALL NC,0', 'CALL PO,0', 'CALL P,0'),
        [{'F': 0xFF}]
    ),

    # CALL made
    (
        'pc:4,pc+1:3,pc+2:3,pc+2:1,sp-1:3,sp-2:3',
        ('CALL Z,0', 'CALL C,0', 'CALL PE,0', 'CALL M,0'),
        [{'F': 0xFF, 'SP': sp} for sp in ADDRESSES[3]]
    ),

    # CALL made
    (
        'pc:4,pc+1:3,pc+2:3,pc+2:1,sp-1:3,sp-2:3',
        ('CALL 0', 'CALL NZ,0', 'CALL NC,0', 'CALL PO,0', 'CALL P,0'),
        [{'F': 0, 'SP': sp} for sp in ADDRESSES[3]]
    ),

    # JR not made
    (
        'pc:4,pc+1:3',
        ('JR C,0', 'JR Z,0'),
        [{'F': 0}]
    ),

    # JR not made
    (
        'pc:4,pc+1:3',
        ('JR NC,0', 'JR NZ,0'),
        [{'F': 0xFF}]
    ),

    # DJNZ not made
    (
        'pc:4,ir:1,pc+1:3',
        ['DJNZ 0'],
        [{'BC': 0x0100, 'IR': ir} for ir in ADDRESSES[1]]
    ),

    # JR made
    (
        'pc:4,pc+1:3,pc+1:1,pc+1:1,pc+1:1,pc+1:1,pc+1:1',
        ('JR C,0', 'JR Z,0'),
        [{'F': 0xFF}]
    ),

    # JR made
    (
        'pc:4,pc+1:3,pc+1:1,pc+1:1,pc+1:1,pc+1:1,pc+1:1',
        ('JR NC,0', 'JR NZ,0'),
        [{'F': 0}]
    ),

    # DJNZ made
    (
        'pc:4,ir:1,pc+1:3,pc+1:1,pc+1:1,pc+1:1,pc+1:1,pc+1:1',
        ['DJNZ 0'],
        [{'BC': 0x0200, 'IR': ir} for ir in ADDRESSES[1]]
    ),

    (
        'pc:4,pc+1:4,hl:3,hl:1,hl:1,hl:1,hl:1,hl:3',
        ('RLD', 'RRD'),
        [{'HL': hl} for hl in ADDRESSES[1]]
    ),

    (
        'pc:4,sp:3,sp+1:3,sp+1:1,sp+1:3,sp:3,sp:1,sp:1',
        ['EX (SP),HL'],
        [{'SP': sp} for sp in ADDRESSES[2]]
    ),

    (
        'pc:4,pc+1:4,sp:3,sp+1:3,sp+1:1,sp+1:3,sp:3,sp:1,sp:1',
        ('EX (SP),IX', 'EX (SP),IY'),
        [{'SP': sp} for sp in ADDRESSES[2]]
    ),

    # LDI/LDIR/LDD/LDDR with BC == 1
    (
        'pc:4,pc+1:4,hl:3,de:3,de:1,de:1',
        ('LDI', 'LDIR', 'LDD', 'LDDR'),
        [{'BC': 1, 'DE': de, 'HL': hl} for de in ADDRESSES[1] for hl in ADDRESSES[1]],
    ),

    # LDIR/LDDR with BC != 1
    (
        'pc:4,pc+1:4,hl:3,de:3,de:1,de:1,de:1,de:1,de:1,de:1,de:1',
        ('LDIR', 'LDDR'),
        [{'BC': 2, 'DE': de, 'HL': hl} for de in ADDRESSES[1] for hl in ADDRESSES[1]]
    ),

    # CPI/CPIR/CPD/CPDR with BC == 1
    (
        'pc:4,pc+1:4,hl:3,hl:1,hl:1,hl:1,hl:1,hl:1',
        ('CPI', 'CPIR', 'CPD', 'CPDR'),
        [{'BC': 1, 'HL': hl} for hl in ADDRESSES[1]]
    ),

    # CPIR/CPDR with BC != 1 and A != (HL)
    (
        'pc:4,pc+1:4,hl:3,hl:1,hl:1,hl:1,hl:1,hl:1,hl:1,hl:1,hl:1,hl:1,hl:1',
        ('CPIR', 'CPDR'),
        [{'A': 1, 'BC': 2, 'HL': hl} for hl in ADDRESSES[1]]
    ),

    *[
        (
            'pc:4,pc+1:3,io:4',
            (f'IN A,(${lsb:02X})', f'OUT (${lsb:02X}),A'),
            [{'A': msb} for msb in (0x40, 0x80)]
        ) for lsb in (0xFE, 0xFF)
    ],

    (
        'pc:4,pc+1:4,io:4',
        (
            *[f'IN {r},(C)' for r in REG8],
            *[f'OUT (C),{r}' for r in REG8]
        ),
        [{'BC': bc} for bc in (0x40FE, 0x40FF, 0x80FE, 0x80FF)]
    ),

    # INI/INIR/IND/INDR with B == 1
    (
        'pc:4,pc+1:4,ir:1,io:4,hl:3',
        ('INI', 'INIR', 'IND', 'INDR'),
        [{'BC': 256 + c, 'IR': ir, 'HL': hl} for c in (0xFE, 0xFF) for ir in ADDRESSES[1] for hl in ADDRESSES[1]]
    ),

    # INIR/INDR with B != 1
    (
        'pc:4,pc+1:4,ir:1,io:4,hl:3,hl:1,hl:1,hl:1,hl:1,hl:1',
        ('INIR', 'INDR'),
        [{'BC': bc, 'IR': ir, 'HL': hl} for bc in (0x40FE, 0x40FF, 0x80FE, 0x80FF) for ir in ADDRESSES[1] for hl in ADDRESSES[1]]
    ),

    # OUTI/OTIR/OUTD/OTDR with B == 1
    (
        'pc:4,pc+1:4,ir:1,hl:3,io:4',
        ('OUTI', 'OTIR', 'OUTD', 'OTDR'),
        [{'BC': 256 + c, 'IR': ir, 'HL': hl} for c in (0xFE, 0xFF) for ir in ADDRESSES[1] for hl in ADDRESSES[1]]
    ),

    # OTIR/OTDR with B != 1
    (
        'pc:4,pc+1:4,ir:1,hl:3,io:4,bc:1,bc:1,bc:1,bc:1,bc:1',
        ('OTIR', 'OTDR'),
        [{'BC': bc, 'IR': ir, 'HL': hl} for bc in (0x40FE, 0x40FF, 0x80FE, 0x80FF) for ir in ADDRESSES[1] for hl in ADDRESSES[1]]
    ),
)

TEMPLATE = r"""
#!/usr/bin/env python3
import os
import sys
import unittest

SKOOLKIT_HOME = os.environ.get('SKOOLKIT_HOME')
if not SKOOLKIT_HOME:
    sys.stderr.write('SKOOLKIT_HOME is not set; aborting\n')
    sys.exit(1)
if not os.path.isdir(SKOOLKIT_HOME):
    sys.stderr.write(f'SKOOLKIT_HOME={SKOOLKIT_HOME}; directory not found\n')
    sys.exit(1)
sys.path.insert(0, SKOOLKIT_HOME)

from skoolkit.cmiosimulator import CMIOSimulator
from skoolkit.pagingtracer import Memory
from skoolkit.z80 import Assembler

GROUPS = $groups

DELAYS_48K = [0] * 69888
for row in range(64, 256):
    for i in range(16):
        t = row * 224 - 1 + i * 8
        DELAYS_48K[t:t + 6] = (6, 5, 4, 3, 2, 1)

DELAYS_128K = [0] * 70908
for row in range(63, 255):
    for i in range(16):
        t = row * 228 - 3 + i * 8
        DELAYS_128K[t:t + 6] = (6, 5, 4, 3, 2, 1)

REGISTERS = {
    'BC': 2,
    'DE': 4,
    'HL': 6,
    'IX': 8,
    'IY': 10,
    'IR': 14
}

ADDRESSES = {
    1: (0x4000, 0x8000),
    2: (0x3FFF, 0x4000, 0x7FFF, 0x8000),
    3: (0x3FFE, 0x3FFF, 0x4000, 0x7FFE, 0x7FFF, 0x8000),
    4: (0x3FFD, 0x3FFE, 0x3FFF, 0x4000, 0x7FFD, 0x7FFE, 0x7FFF, 0x8000)
}

RVALUES = {
    'pc': lambda kw: kw['PC'],
    'pc+1': lambda kw: kw['PC'] + 1,
    'pc+2': lambda kw: kw['PC'] + 2,
    'pc+3': lambda kw: kw['PC'] + 3,
    'sp-2': lambda kw: kw['SP'] - 2,
    'sp-1': lambda kw: kw['SP'] - 1,
    'sp': lambda kw: kw['SP'],
    'sp+1': lambda kw: kw['SP'] + 1,
    'bc': lambda kw: kw['BC'],
    'de': lambda kw: kw['DE'],
    'hl': lambda kw: kw['HL'],
    'ix': lambda kw: kw['IX'],
    'iy': lambda kw: kw['IY'],
    'ir': lambda kw: kw['IR'],
}

def contend_48k(t, timings):
    delay = 0
    if 14312 < t % 69888 < 57245:
        for address, tstates in timings:
            if 0x4000 <= address % 65536 < 0x8000:
                delay += DELAYS_48K[t % 69888]
                t += DELAYS_48K[t % 69888]
            t += tstates
    return delay

def contend_128k(t, timings):
    delay = 0
    if 14338 < t % 70908 < 58035:
        for address, tstates in timings:
            if 0x4000 <= address % 65536 < 0x8000:
                delay += DELAYS_128K[t % 70908]
                t += DELAYS_128K[t % 70908]
            t += tstates
    return delay

def io_contention(port):
    if port % 2:
        # Low bit set
        if 0x4000 <= port < 0x8000:
            return ((0x4000, 1), (0x4000, 1), (0x4000, 1), (0x4000, 1))
        return ((0, 4),)
    # Low bit reset (ULA port)
    if 0x4000 <= port < 0x8000:
        return ((0x4000, 1), (0x4000, 3))
    return ((0, 1), (0x4000, 3))

def calculate_contention(cycles, **kwargs):
    timings = []
    addr_chars = set('0123456789abcdef')
    for spec in cycles:
        r, t = spec.split(':')
        if r in RVALUES:
            rv = RVALUES[r](kwargs)
        elif set(r) < addr_chars:
            rv = int(r, 16)
        elif r == 'io':
            timings.extend(io_contention(kwargs['port']))
        else:
            raise ValueError(f"Unrecognised spec: '{spec}'")
        if r != 'io':
            timings.append((rv, int(t)))
    return timings

def get_times(contend_f, cycles, addr, assembler, assembled, ops, size, registers, t_ranges, t0, period):
    t1 = t0 + period
    tmax = t0 + 191 * period
    d = {}
    times = None
    for op in ops:
        if op in assembled:
            data = assembled[op]
        else:
            data = assembled[op] = assembler.assemble(op, 0)
            if len(data) != size:
                raise ValueError(f'"{op}" is {len(data)} bytes, expected {size}')
        if times:
            continue
        if 'io:4' in cycles:
            if data[0] in (0xD3, 0xDB):
                # IN A,(n) / OUT (n),A
                port = data[1] + 256 * registers['A']
            else:
                port = registers['BC']
            contention = calculate_contention(cycles, PC=addr, port=port, **registers)
        else:
            contention = calculate_contention(cycles, PC=addr, **registers)
        times = {}
        for t_range in t_ranges:
            times[t_range[0]] = []
            for t in t_range:
                if t1 <= t < tmax:
                    delay = d[t % period]
                else:
                    delay = contend_f(t, contention)
                    d[t % period] = delay
                times[t_range[0]].append(delay)
    return times

class CMIOSimulatorTest(unittest.TestCase):
    def _run(self, cs, registers, addr, op, data, t, duration, exp_delay, page=-1):
        if page >= 0:
            cs.memory.out7ffd(page)
        for i, b in enumerate(data):
            cs.memory[(addr + i) % 65536] = b
        for r, v in registers.items():
            if r == 'SP':
                cs.registers[12] = v
            elif r == 'F':
                cs.registers[1] = v
            elif r == 'A':
                cs.registers[0] = v
            else:
                cs.registers[REGISTERS[r]] = v // 256
                cs.registers[REGISTERS[r] + 1] = v % 256
        cs.registers[25] = t
        cs.run(addr)
        self.assertEqual(cs.registers[25] - t - duration, exp_delay, f"Failed for '{op}' {data} at {addr} (T={t}, page={page}, registers={registers})")

    def _test_contention_128k(self, cs, registers, addr, cycles, op, data, t, duration, exp_delay):
        if 'io:4' in cycles and registers.get('BC', 0) // 256 != 1:
            reg = registers.copy()
            if data[0] in (0xD3, 0xDB):
                # IN A,(n) / OUT (n),A
                contended_port = 0x40 <= reg['A'] < 0x80
                reg['A'] = 0xC0
            else:
                contended_port = 0x4000 <= reg['BC'] < 0x8000
                reg['BC'] = 0xC000 + reg['BC'] % 256
            pages = (1, 3, 5, 7) if contended_port else (0, 2, 4, 6)
            for page in pages:
                self._run(cs, reg, addr, op, data, t, duration, exp_delay, page)
        elif addr < 0x8000:
            for page in (1, 3, 5, 7):
                self._run(cs, registers, addr + 0x8000, op, data, t, duration, exp_delay, page)
        else:
            for page in (0, 2, 4, 6):
                self._run(cs, registers, 0xC000, op, data, t, duration, exp_delay, page)

    def _test_contention(self, machine, group):
        assembler = Assembler()
        assembled = {}
        cspec, ops, inputs = group
        cycles = cspec.split(',')
        duration = sum(int(c.split(':')[1]) for c in cycles)
        size = len(set(c.split(':')[0] for c in cycles if c.startswith('pc')))
        if machine == '48K':
            cs = CMIOSimulator([0] * 65536)
            contend_f = contend_48k
            ct0 = 14335
            period = 224
            frame_duration = 69888
        else:
            cs = CMIOSimulator(Memory())
            cs.memory.roms = [[0] * 16384, [0] * 16384]
            cs.memory.out7ffd(0)
            contend_f = contend_128k
            ct0 = 14361
            period = 228
            frame_duration = 70908
        t_ranges = $t_ranges
        for registers in inputs:
            delays = {}
            for addr in ADDRESSES[size]:
                delays[addr] = get_times(contend_f, cycles, addr, assembler, assembled, ops, size, registers, t_ranges, ct0, period)
            for op in ops:
                data = assembled[op]
                for addr, timings in delays.items():
                    for t0, times in timings.items():
                        for t, exp_delay in enumerate(times, t0):
                            self._run(cs, registers, addr, op, data, t, duration, exp_delay)
                            if machine == '128K':
                                self._test_contention_128k(cs, registers, addr, cycles, op, data, t, duration, exp_delay)

$tests

if __name__ == '__main__':
    import nose2
    sys.argv.extend(('--plugin=nose2.plugins.mp', '-N', '0'))
    nose2.main()
""".strip()

def get_ops_lines(ops, indent, max_len):
    lines = []
    line = indent
    i = 0
    while i < len(ops):
        if line == indent:
            line += f'"{ops[i]}",'
            i += 1
            continue
        suffix = f' "{ops[i]}",'
        if len(line) + len(suffix) < max_len:
            line += suffix
            i += 1
            continue
        lines.append(line)
        line = indent + suffix[1:]
        i += 1
    if line:
        lines.append(line)
    if len(ops) > 1:
        # Remove terminal comma
        lines[-1] = lines[-1][:-1]
    return lines

def print_tests(outfile, options):
    ops_line_max_len = 120

    groups = ['(']
    tnames = []
    test_names = []
    for i, (name, ops, reg_sets) in enumerate(GROUPS):
        tname = name.replace(',', '_').replace(':', '').replace('+1', 'n').replace('+2', 'nn').replace('+3', 'nnn').replace('-1', 'p').replace('-2', 'pp')
        count = tnames.count(tname)
        if count:
            test_names.append(f'{tname}_{count + 1}')
        else:
            test_names.append(tname)
        tnames.append(tname)

        if i:
            groups.append('')
        groups.append('    (')
        groups.append(f"        '{name}',")

        # Operations
        sorted_ops = sorted(ops)
        ops_lines = get_ops_lines(sorted_ops, '', ops_line_max_len - 3)
        if len(ops_lines) == 1:
            groups.append(f'        ({ops_lines[0]}),')
        else:
            ops_lines = get_ops_lines(sorted_ops, ''.ljust(12), ops_line_max_len)
            groups.append('        (')
            for line in ops_lines:
                groups.append(line)
            groups.append('        ),')

        # Registers
        groups.append('        (')
        for registers in reg_sets:
            rvals = ', '.join([f"'{r}': 0x{v:0{len(r) * 2}X}" for r, v in registers.items()])
            groups.append(f'            {{{rvals}}},')
        groups.append('        )')

        groups.append('    ),')
    groups.append(')')
    groups = '\n'.join(groups)

    if options.vfast:
        t_ranges = '[[ct0]]'
    elif options.fast:
        t_ranges = '(list(range(ct0 - duration, ct0 + period)), list(range(ct0 + 191 * period, ct0 + 192 * period + 1)))'
    elif options.medium:
        t_ranges = '[list(range(ct0 - period, ct0 + 193 * period))]'
    else:
        t_ranges = '[list(range(frame_duration))]'

    tests = []
    for index, tname in enumerate(test_names):
        tests.append(f"""
    def test_{tname}_48k(self):
        self._test_contention('48K', GROUPS[{index}])

    def test_{tname}_128k(self):
        self._test_contention('128K', GROUPS[{index}])
""".rstrip())
    tests = '\n'.join(tests)

    with open(outfile, 'w') as f:
        f.write(Template(TEMPLATE).substitute(groups=groups, t_ranges=t_ranges, tests=tests))
    os.chmod(outfile, 0o755)
    if options.verbose:
        print(f'Now run ./{outfile}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        usage='%(prog)s [options] [OUTFILE]',
        description="Write tests for CMIOSimulator.",
        add_help=False
    )
    parser.add_argument('outfile', help=argparse.SUPPRESS, nargs='?')
    group = parser.add_argument_group('Options')
    group.add_argument('--vfast', action='store_true',
                       help="Test only one contended T-state.")
    group.add_argument('--fast', action='store_true',
                       help="Test a small subset of contended T-states.")
    group.add_argument('--medium', action='store_true',
                       help="Test all contended T-states.")
    group.add_argument('--slow', action='store_true',
                       help="Test all T-states. (This is the default.)")
    group.add_argument('--quiet', dest='verbose', action='store_false',
                       help="Be quiet.")
    namespace, unknown_args = parser.parse_known_args()
    if unknown_args:
        parser.exit(2, parser.format_help())
    outfile = namespace.outfile or 'slow_test_cmiosimulator.py'
    print_tests(outfile, namespace)
