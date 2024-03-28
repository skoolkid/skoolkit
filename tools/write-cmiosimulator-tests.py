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
    1: (0x4000, 0x8000, 0xC000),                                         # rr
    2: (0x3FFF, 0x4000, 0x7FFF, 0x8000, 0xBFFF, 0xC000, 0xFFFF),         # rr, rr+1
    3: (0x0000, 0x0001, 0x4001, 0x4002, 0x8001, 0x8002, 0xC001, 0xC002), # sp-1, sp-2
}

PORTS = (0x40FE, 0x40FF, 0x80FE, 0x80FF, 0xC0FE, 0xC0FF)
BC_OTIR_OTDR = (0x41FE, 0x41FF, 0x81FE, 0x81FF, 0xC1FE, 0xC1FF)
PORTS_MSB = (0x40, 0x80, 0xC0)
PORTS_LSB = (0xFE, 0xFF)

GROUPS = (
    (
        'pc4',
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
        'pc4_pcn4',
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
        'ld_a_ir',
        'pc:4,pc+1:4,ir:1',
        ('LD A,I', 'LD A,R', 'LD I,A', 'LD R,A'),
        [{'IR': ir} for ir in ADDRESSES[1]]
    ),

    (
        'ld_sp_hl_inc_dec_rr',
        'pc:4,ir:1,ir:1',
        (
            'LD SP,HL',
            *[f'{op} {rr}' for op in ('INC', 'DEC') for rr in ('BC', 'DE', 'HL', 'SP')]
        ),
        [{'IR': ir} for ir in ADDRESSES[1]]
    ),

    (
        'ld_sp_xy_inc_dec_xy',
        'pc:4,pc+1:4,ir:1,ir:1',
        ('LD SP,IX', 'LD SP,IY', 'INC IX', 'INC IY', 'DEC IX', 'DEC IY'),
        [{'IR': ir} for ir in ADDRESSES[1]]
    ),

    (
        'add_hl_rr',
        'pc:4,ir:1,ir:1,ir:1,ir:1,ir:1,ir:1,ir:1',
        ('ADD HL,BC', 'ADD HL,DE', 'ADD HL,HL', 'ADD HL,SP'),
        [{'IR': ir} for ir in ADDRESSES[1]]
    ),

    (
        'add_xy_rr_adc_sbc_hl_rr',
        'pc:4,pc+1:4,ir:1,ir:1,ir:1,ir:1,ir:1,ir:1,ir:1',
        (
            *[f'ADD {rr1},{rr2}' for rr1 in ('IX', 'IY') for rr2 in ('BC', 'DE', rr1, 'SP')],
            *[f'{op} HL,{rr}' for op in ('ADC', 'SBC') for rr in ('BC', 'DE', 'HL', 'SP')]
        ),
        [{'IR': ir} for ir in ADDRESSES[1]]
    ),

    (
        'ld_r_n_alo_a_n',
        'pc:4,pc+1:3',
        (
            *[f'LD {r},0' for r in REG8],
            *[f'{op}0' for op in ALO_A],
        ),
        [{}]
    ),

    (
        'ld_xy_n',
        'pc:4,pc+1:4,pc+2:3',
        [f'LD {r},0' for r in REG8XY],
        [{}]
    ),

    *[
        (
            f'ld_a_{rr}',
            f'pc:4,{rr}:3',
            (f'LD A,({rr.upper()})', f'LD ({rr.upper()}),A'),
            [{rr.upper(): rv} for rv in ADDRESSES[1]]
        ) for rr in ('bc', 'de')
    ],

    (
        'ld_r_hl_alo_a_hl',
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
            f'ld_r_{rr}_d_alo_a_{rr}_d',
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
        'bit_n_hl',
        'pc:4,pc+1:4,hl:3,hl:1',
        [f'BIT {b},(HL)' for b in range(8)],
        [{'HL': hl} for hl in ADDRESSES[1]]
    ),

    *[
        (
            f'bit_n_{rr}_d',
            f'pc:4,pc+1:4,pc+2:3,pc+3:3,pc+3:1,pc+3:1,{rr}:3,{rr}:1',
            [f'BIT {b},({rr.upper()}+0)' for b in range(8)],
            [{rr.upper(): rv} for rv in ADDRESSES[1]]
        ) for rr in ('ix', 'iy')
    ],

    (
        'jp_nn_ld_rr_nn',
        'pc:4,pc+1:3,pc+2:3',
        (
            'JP 0',
            *[f'JP {c},0' for c in CONDITIONS],
            *[f'LD {rr},0' for rr in ('BC', 'DE', 'HL', 'SP')]
        ),
        [{}]
    ),

    (
        'ld_xy_nn',
        'pc:4,pc+1:4,pc+2:3,pc+3:3',
        ('LD IX,0', 'LD IY,0'),
        [{}]
    ),

    (
        'ld_hl_n',
        'pc:4,pc+1:3,hl:3',
        ['LD (HL),0'],
        [{'HL': hl} for hl in ADDRESSES[1]]
    ),

    *[
        (
            f'ld_{rr}_d_n',
            f'pc:4,pc+1:4,pc+2:3,pc+3:3,pc+3:1,pc+3:1,{rr}:3',
            [f'LD ({rr.upper()}+0),0'],
            [{rr.upper(): rv} for rv in ADDRESSES[1]]
        ) for rr in ('ix', 'iy')
    ],

    *[
        (
            f'ld_a_{addr:04x}',
            f'pc:4,pc+1:3,pc+2:3,{addr:04x}:3',
            (f'LD A,(${addr:04X})', f'LD (${addr:04X}),A'),
            [{}]
        ) for addr in ADDRESSES[1]
    ],

    *[
        (
            f'ld_hl_{addr:04x}',
            f'pc:4,pc+1:3,pc+2:3,{addr:04x}:3,{addr+1:04x}:3',
            (f'LD HL,(${addr:04X})', f'LD (${addr:04X}),HL'),
            [{}]
        ) for addr in ADDRESSES[2]
    ],

    *[
        (
            f'ld_rr_{addr:04x}',
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
        'inc_dec_hl',
        'pc:4,hl:3,hl:1,hl:3',
        ('INC (HL)', 'DEC (HL)'),
        [{'HL': hl} for hl in ADDRESSES[1]]
    ),

    (
        'set_res_sro_hl',
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
            f'inc_dec_{rr}_d',
            f'pc:4,pc+1:4,pc+2:3,pc+2:1,pc+2:1,pc+2:1,pc+2:1,pc+2:1,{rr}:3,{rr}:1,{rr}:3',
            (f'INC ({rr.upper()}+0)', f'DEC ({rr.upper()}+0)'),
            [{rr.upper(): rv} for rv in ADDRESSES[1]]
        ) for rr in ('ix', 'iy')
    ],

    *[
        (
            f'set_res_sro_{rr}_d',
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
        'pop_rr_ret',
        'pc:4,sp:3,sp+1:3',
        ('POP BC', 'POP DE', 'POP HL', 'POP AF', 'RET'),
        [{'SP': sp} for sp in ADDRESSES[2]]
    ),

    (
        'pop_xy_reti_retn',
        'pc:4,pc+1:4,sp:3,sp+1:3',
        ('POP IX', 'POP IY', 'RETI', 'RETN'),
        [{'SP': sp} for sp in ADDRESSES[2]]
    ),

    # RET Z/C/PE/M - return not made
    (
        'ret_z_c_pe_m_not_made',
        'pc:4,ir:1',
        ('RET Z', 'RET C', 'RET PE', 'RET M'),
        [{'F': 0, 'IR': ir} for ir in ADDRESSES[1]]
    ),

    # RET NZ/NC/PO/P - return not made
    (
        'ret_nz_nc_po_p_not_made',
        'pc:4,ir:1',
        ('RET NZ', 'RET NC', 'RET PO', 'RET P'),
        [{'F': 0xFF, 'IR': ir} for ir in ADDRESSES[1]]
    ),

    # RET Z/C/PE/M - return made
    (
        'ret_z_c_pe_m_made',
        'pc:4,ir:1,sp:3,sp+1:3',
        ('RET Z', 'RET C', 'RET PE', 'RET M'),
        [{'F': 0xFF, 'IR': ir, 'SP': sp} for ir in ADDRESSES[1] for sp in ADDRESSES[2]]
    ),

    # RET NZ/NC/PO/P - return made
    (
        'ret_nz_nc_po_p_made',
        'pc:4,ir:1,sp:3,sp+1:3',
        ('RET NZ', 'RET NC', 'RET PO', 'RET P'),
        [{'F': 0x00, 'IR': ir, 'SP': sp} for ir in ADDRESSES[1] for sp in ADDRESSES[2]]
    ),

    (
        'push_rr_rst',
        'pc:4,ir:1,sp-1:3,sp-2:3',
        (
            'PUSH BC', 'PUSH DE', 'PUSH HL', 'PUSH AF',
            *[f'RST {n}' for n in range(0, 64, 8)]
        ),
        [{'IR': ir, 'SP': sp} for ir in ADDRESSES[1] for sp in ADDRESSES[3]]
    ),

    (
        'push_xy',
        'pc:4,pc+1:4,ir:1,sp-1:3,sp-2:3',
        ('PUSH IX', 'PUSH IY'),
        [{'IR': ir, 'SP': sp} for ir in ADDRESSES[1] for sp in ADDRESSES[3]]
    ),

    # CALL
    (
        'call',
        'pc:4,pc+1:3,pc+2:3,pc+2:1,sp-1:3,sp-2:3',
        ['CALL 0'],
        [{'SP': sp} for sp in ADDRESSES[3]]
    ),

    # CALL Z/C/PE/M not made
    (
        'call_z_c_pe_m_not_made',
        'pc:4,pc+1:3,pc+2:3',
        ('CALL Z,0', 'CALL C,0', 'CALL PE,0', 'CALL M,0'),
        [{'F': 0}]
    ),

    # CALL NZ/NC/PO/P not made
    (
        'call_nz_nc_po_p_not_made',
        'pc:4,pc+1:3,pc+2:3',
        ('CALL NZ,0', 'CALL NC,0', 'CALL PO,0', 'CALL P,0'),
        [{'F': 0xFF}]
    ),

    # CALL Z/C/PE/M made
    (
        'call_z_c_pe_m_made',
        'pc:4,pc+1:3,pc+2:3,pc+2:1,sp-1:3,sp-2:3',
        ('CALL Z,0', 'CALL C,0', 'CALL PE,0', 'CALL M,0'),
        [{'F': 0xFF, 'SP': sp} for sp in ADDRESSES[3]]
    ),

    # CALL NZ/NC/PO/P made
    (
        'call_nz_nc_po_p_made',
        'pc:4,pc+1:3,pc+2:3,pc+2:1,sp-1:3,sp-2:3',
        ('CALL 0', 'CALL NZ,0', 'CALL NC,0', 'CALL PO,0', 'CALL P,0'),
        [{'F': 0, 'SP': sp} for sp in ADDRESSES[3]]
    ),

    # JR C/Z not made
    (
        'jr_c_z_no_jump',
        'pc:4,pc+1:3',
        ('JR C,0', 'JR Z,0'),
        [{'F': 0}]
    ),

    # JR NC/NZ not made
    (
        'jr_nc_nz_no_jump',
        'pc:4,pc+1:3',
        ('JR NC,0', 'JR NZ,0'),
        [{'F': 0xFF}]
    ),

    # DJNZ not made
    (
        'djnz_no_jump',
        'pc:4,ir:1,pc+1:3',
        ['DJNZ 0'],
        [{'BC': 0x0100, 'IR': ir} for ir in ADDRESSES[1]]
    ),

    # JR C/Z made
    (
        'jr_c_z_jump_made',
        'pc:4,pc+1:3,pc+1:1,pc+1:1,pc+1:1,pc+1:1,pc+1:1',
        ('JR C,0', 'JR Z,0'),
        [{'F': 0xFF}]
    ),

    # JR NC/NZ made
    (
        'jr_nc_nz_jump_made',
        'pc:4,pc+1:3,pc+1:1,pc+1:1,pc+1:1,pc+1:1,pc+1:1',
        ('JR NC,0', 'JR NZ,0'),
        [{'F': 0}]
    ),

    # JR
    (
        'jr',
        'pc:4,pc+1:3,pc+1:1,pc+1:1,pc+1:1,pc+1:1,pc+1:1',
        ['JR 0'],
        [{}]
    ),

    # DJNZ made
    (
        'djnz_jump_made',
        'pc:4,ir:1,pc+1:3,pc+1:1,pc+1:1,pc+1:1,pc+1:1,pc+1:1',
        ['DJNZ 0'],
        [{'BC': 0x0200, 'IR': ir} for ir in ADDRESSES[1]]
    ),

    (
        'rld_rrd',
        'pc:4,pc+1:4,hl:3,hl:1,hl:1,hl:1,hl:1,hl:3',
        ('RLD', 'RRD'),
        [{'HL': hl} for hl in ADDRESSES[1]]
    ),

    (
        'ex_sp_hl',
        'pc:4,sp:3,sp+1:3,sp+1:1,sp+1:3,sp:3,sp:1,sp:1',
        ['EX (SP),HL'],
        [{'SP': sp} for sp in ADDRESSES[2]]
    ),

    (
        'ex_sp_xy',
        'pc:4,pc+1:4,sp:3,sp+1:3,sp+1:1,sp+1:3,sp:3,sp:1,sp:1',
        ('EX (SP),IX', 'EX (SP),IY'),
        [{'SP': sp} for sp in ADDRESSES[2]]
    ),

    # LDI/LDIR/LDD/LDDR with BC == 1
    (
        'ldi_ldd_ldir_lddr_no_repeat',
        'pc:4,pc+1:4,hl:3,de:3,de:1,de:1',
        ('LDI', 'LDIR', 'LDD', 'LDDR'),
        [{'BC': 1, 'DE': de, 'HL': hl} for de in ADDRESSES[1] for hl in ADDRESSES[1]],
    ),

    # LDIR/LDDR with BC != 1
    (
        'ldir_lddr_repeat',
        'pc:4,pc+1:4,hl:3,de:3,de:1,de:1,de:1,de:1,de:1,de:1,de:1',
        ('LDIR', 'LDDR'),
        [{'BC': 2, 'DE': de, 'HL': hl} for de in ADDRESSES[1] for hl in ADDRESSES[1]]
    ),

    # CPI/CPIR/CPD/CPDR with BC == 1
    (
        'cpi_cpd_cpir_cpdr_no_repeat',
        'pc:4,pc+1:4,hl:3,hl:1,hl:1,hl:1,hl:1,hl:1',
        ('CPI', 'CPIR', 'CPD', 'CPDR'),
        [{'BC': 1, 'HL': hl} for hl in ADDRESSES[1]]
    ),

    # CPIR/CPDR with BC != 1 and A != (HL)
    (
        'cpir_cpdr_repeat',
        'pc:4,pc+1:4,hl:3,hl:1,hl:1,hl:1,hl:1,hl:1,hl:1,hl:1,hl:1,hl:1,hl:1',
        ('CPIR', 'CPDR'),
        [{'A': 1, 'BC': 2, 'HL': hl} for hl in ADDRESSES[1]]
    ),

    *[
        (
            f'in_out_a_{lsb:02x}',
            'pc:4,pc+1:3,io:4',
            (f'IN A,(${lsb:02X})', f'OUT (${lsb:02X}),A'),
            [{'A': msb} for msb in PORTS_MSB]
        ) for lsb in (0xFE, 0xFF)
    ],

    (
        'in_out_c',
        'pc:4,pc+1:4,io:4',
        (
            *[f'IN {r},(C)' for r in REG8],
            *[f'OUT (C),{r}' for r in REG8]
        ),
        [{'BC': bc} for bc in PORTS]
    ),

    # INI/INIR/IND/INDR with B == 1
    (
        'ini_ind_inir_indr_no_repeat',
        'pc:4,pc+1:4,ir:1,io:4,hl:3',
        ('INI', 'INIR', 'IND', 'INDR'),
        [{'BC': 256 + c, 'IR': ir, 'HL': hl} for c in PORTS_LSB for ir in ADDRESSES[1] for hl in ADDRESSES[1]]
    ),

    # INIR/INDR with B != 1
    (
        'inir_indr_repeat',
        'pc:4,pc+1:4,ir:1,io:4,hl:3,hl:1,hl:1,hl:1,hl:1,hl:1',
        ('INIR', 'INDR'),
        [{'BC': bc, 'IR': ir, 'HL': hl} for bc in PORTS for ir in ADDRESSES[1] for hl in ADDRESSES[1]]
    ),

    # OUTI/OTIR/OUTD/OTDR with B == 1
    (
        'outi_outd_otir_otdr_no_repeat',
        'pc:4,pc+1:4,ir:1,hl:3,io:4',
        ('OUTI', 'OTIR', 'OUTD', 'OTDR'),
        [{'BC': 256 + c, 'IR': ir, 'HL': hl} for c in PORTS_LSB for ir in ADDRESSES[1] for hl in ADDRESSES[1]]
    ),

    # OTIR/OTDR with B != 1
    (
        'otir_otdr_repeat',
        'pc:4,pc+1:4,ir:1,hl:3,io:4,bc:1,bc:1,bc:1,bc:1,bc:1',
        ('OTIR', 'OTDR'),
        [{'BC': bc, 'IR': ir, 'HL': hl} for bc in BC_OTIR_OTDR for ir in ADDRESSES[1] for hl in ADDRESSES[1]]
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

if $ccmio:
    from skoolkit.ccmiosimulator import CCMIOSimulator

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
    1: (0x4000, 0x8000, 0xC000),
    2: (0x3FFF, 0x4000, 0x7FFF, 0x8000, 0xBFFF, 0xC000, 0xFFFF),
    3: (0x3FFE, 0x3FFF, 0x4000, 0x7FFE, 0x7FFF, 0x8000, 0xBFFE, 0xBFFF, 0xC000, 0xFFFE, 0xFFFF),
    4: (0x3FFD, 0x3FFE, 0x3FFF, 0x4000, 0x7FFD, 0x7FFE, 0x7FFF, 0x8000, 0xBFFD, 0xBFFE, 0xBFFF, 0xC000, 0xFFFD, 0xFFFE, 0xFFFF)
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

def contend_48k(t, timings, page):
    delay = 0
    if 14312 < t % 69888 < 57245:
        for address, tstates in timings:
            if 0x4000 <= address % 65536 < 0x8000:
                delay += DELAYS_48K[t % 69888]
                t += DELAYS_48K[t % 69888]
            t += tstates
    return delay

def contend_128k(t, timings, page):
    delay = 0
    if 14338 < t % 70908 < 58035:
        for address, tstates in timings:
            if 0x4000 <= address % 65536 < 0x8000 or (page % 2 and 0xC000 <= address % 65536):
                delay += DELAYS_128K[t % 70908]
                t += DELAYS_128K[t % 70908]
            t += tstates
    return delay

def io_contention(port, page):
    if port % 2:
        # Low bit set
        if 0x4000 <= port < 0x8000 or (page % 2 and port >= 0xC000):
            return ((0x4000, 1), (0x4000, 1), (0x4000, 1), (0x4000, 1))
        return ((0, 4),)
    # Low bit reset (ULA port)
    if 0x4000 <= port < 0x8000 or (page % 2 and port >= 0xC000):
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
            timings.extend(io_contention(kwargs['port'], kwargs['page']))
        else:
            raise ValueError(f"Unrecognised spec: '{spec}'")
        if r != 'io':
            timings.append((rv, int(t)))
    return timings

def get_times(contend_f, cycles, duration, addr, assembler, assembled, ops, size, registers, t_ranges, t0, period, page=0):
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
            elif data[0] == 0xED and data[1] in (0xA3, 0xAB, 0xB3, 0xBB):
                # OUTI / OUTD / OTIR / OTDR
                port = (registers['BC'] - 256) % 65536
            else:
                port = registers['BC']
            contention = calculate_contention(cycles, PC=addr, port=port, page=page, **registers)
        else:
            contention = calculate_contention(cycles, PC=addr, **registers)
        times = {}
        for t_range in t_ranges:
            times[t_range[0]] = []
            for t in t_range:
                if t1 <= t < tmax:
                    delay = d[t % period]
                else:
                    delay = contend_f(t, contention, page)
                    d[t % period] = delay
                times[t_range[0]].append(duration + delay)
    return times

if $ccmio:
    CS48 = CCMIOSimulator([0] * 65536)
    CS128 = CCMIOSimulator(Memory())
else:
    CS48 = CMIOSimulator([0] * 65536)
    CS128 = CMIOSimulator(Memory())
CS48_MEMORY = CS48.memory
CS48_REGISTERS = CS48.registers
CS128_MEMORY = CS128.memory
CS128_MEMORY.roms[0][:] = [0] * 16384
CS128_MEMORY.roms[1][:] = [0] * 16384
CS128_MEMORY.memory[1][0x2000:0x2007] = (
    0x3E, 0x00,       # 6000 LD A,00
    0x01, 0xFD, 0x7F, # 6002 LD BC,7FFD
    0xED, 0x79,       # 6005 OUT (C),A
)
CS128_REGISTERS = CS128.registers

class CMIOSimulatorTest(unittest.TestCase):
    def _test_contention(self, machine, cspec, ops, regvals):
        assembler = Assembler()
        assembled = {}
        cycles = cspec.split(',')
        duration = sum(int(c.split(':')[1]) for c in cycles)
        size = len(set(c.split(':')[0] for c in cycles if c.startswith('pc')))
        if machine == '48K':
            cs = CS48
            memory = CS48_MEMORY
            registers = CS48_REGISTERS
            ct0 = 14335
            period = 224
            frame_duration = 69888
        else:
            cs = CS128
            memory = CS128_MEMORY
            registers = CS128_REGISTERS
            ct0 = 14361
            period = 228
            frame_duration = 70908
        t_ranges = $t_ranges
        cs_registers = []
        for r, v in regvals.items():
            if r == 'SP':
                cs_registers.append((12, v))
            elif r == 'F':
                cs_registers.append((1, v))
            elif r == 'A':
                cs_registers.append((0, v))
            else:
                cs_registers.extend(((REGISTERS[r], v // 256), (REGISTERS[r] + 1, v % 256)))
        op_times = {}
        for addr in ADDRESSES[size]:
            if machine == '48K':
                op_times[(addr, -1)] = get_times(contend_48k, cycles, duration, addr, assembler, assembled, ops, size, regvals, t_ranges, ct0, period)
            else:
                op_times[(addr, 0)] = get_times(contend_128k, cycles, duration, addr, assembler, assembled, ops, size, regvals, t_ranges, ct0, period, 0)
                op_times[(addr, 1)] = get_times(contend_128k, cycles, duration, addr, assembler, assembled, ops, size, regvals, t_ranges, ct0, period, 1)
                for page in range(2, 8):
                    op_times[(addr, page)] = op_times[(addr, page % 2)]
        for op in ops:
            data = assembled[op]
            for (addr, page), timings in op_times.items():
                if page >= 0:
                    memory.out7ffd(page)
                    if $ccmio:
                        memory[0x6001] = page
                        cs.run(0x6000, 0x6007)
                for t0, times in timings.items():
                    t = t0
                    for exp_timing in times:
                        a = addr
                        for b in data:
                            memory[a % 65536] = b
                            a += 1
                        for r, v in cs_registers:
                            registers[r] = v
                        registers[25] = t
                        cs.run(addr)
                        if registers[25] - t != exp_timing:
                            self.fail(f"Failed for '$${addr:04X} {op}' (T={t}, page={page}, registers={regvals}): expected {exp_timing} T-states, was {registers[25] - t}")
                        t += 1
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
    for i, (name, cspec, ops, reg_sets) in enumerate(GROUPS):
        if i:
            groups.append('')
        groups.append('    (')
        groups.append(f"        '{cspec}',")

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
        t_ranges = '(list(range(ct0 - duration, ct0 + 8)), list(range(ct0 + 191 * period + 120, ct0 + 191 * period + 129)))'
    elif options.medium:
        t_ranges = '(list(range(ct0 - duration, ct0 + period)), list(range(ct0 + 191 * period, ct0 + 192 * period + 1)))'
    elif options.slow:
        t_ranges = '[list(range(ct0 - period, ct0 + 193 * period))]'
    else:
        t_ranges = '[list(range(frame_duration))]'

    tests = []
    names = set()
    for i, (name, cspec, ops, reg_sets) in enumerate(GROUPS):
        if name in names:
            print(f'ERROR: Duplicate test name: {name}', file=sys.stderr)
            sys.exit(1)
        names.add(name)
        for j in range(len(reg_sets)):
            tests.append(f"""
    def test_{name}_{j:02}_48k(self):
        self._test_contention('48K', GROUPS[{i}][0], GROUPS[{i}][1], GROUPS[{i}][2][{j}])

    def test_{name}_{j:02}_128k(self):
        self._test_contention('128K', GROUPS[{i}][0], GROUPS[{i}][1], GROUPS[{i}][2][{j}])
""".rstrip())
    tests = '\n'.join(tests)

    with open(outfile, 'w') as f:
        f.write(Template(TEMPLATE).substitute(groups=groups, t_ranges=t_ranges, tests=tests, ccmio=options.ccmio))
    os.chmod(outfile, 0o755)
    if options.verbose:
        print(f'Now run ./{outfile}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        usage='%(prog)s [options] [OUTFILE]',
        description="Write tests for CMIOSimulator or CCMIOSimulator.",
        add_help=False
    )
    parser.add_argument('outfile', help=argparse.SUPPRESS, nargs='?')
    group = parser.add_argument_group('Options')
    group.add_argument('--ccmio', action='store_true',
                       help="Write tests for CCMIOSimulator.")
    group.add_argument('--vfast', action='store_true',
                       help="Test only one contended T-state.")
    group.add_argument('--fast', action='store_true',
                       help="Test a small subset of contended T-states.")
    group.add_argument('--medium', action='store_true',
                       help="Test a larger subset of contended T-states.")
    group.add_argument('--slow', action='store_true',
                       help="Test all contended T-states.")
    group.add_argument('--vslow', action='store_true',
                       help="Test all T-states. (This is the default.)")
    group.add_argument('--quiet', dest='verbose', action='store_false',
                       help="Be quiet.")
    namespace, unknown_args = parser.parse_known_args()
    if unknown_args:
        parser.exit(2, parser.format_help())
    def_outfile = 'slow_test_{}cmiosimulator.py'.format('c' if namespace.ccmio else '')
    outfile = namespace.outfile or def_outfile
    print_tests(outfile, namespace)
