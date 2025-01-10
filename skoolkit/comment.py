# Copyright 2024, 2025 Richard Dymond (rjdymond@gmail.com)
#
# This file is part of SkoolKit.
#
# SkoolKit is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# SkoolKit is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# SkoolKit. If not, see <http://www.gnu.org/licenses/>.

BYTE = '#N({0},2,,1)($)'
WORD = '#N({},4,,1)($)'
PREFIXES = (0xDD, 0xED, 0xFD)
BITS = tuple(tuple(b for b in range(8) if (n >> b) % 2) for n in range(256))

A, B, C, D, E, H, L, AF, BC, DE, HL, IX, IXh, IXl, SP, SPh, SPl, I, R = (
    f'#REG{r}' for r in (
        'a', 'b', 'c', 'd', 'e', 'h', 'l',
        'af', 'bc', 'de', 'hl', 'ix', 'ixh', 'ixl',
        'sp', 'sp-hi', 'sp-lo', 'i', 'r'
    )
)

ZF, SF, PF, CF = 0b01000000, 0b10000000, 0b00000100, 0b00000001
(NA, SIGN, ZERO, COMPARE, PARITY, PARITY_REG, OFLOW, OFLOW_INC, OFLOW_DEC,
 IFF2, BLOCK, NEGATE, BIT_TEST, BIT_7_TEST) = range(14)

FLAGS = {
    SF: ({
        NA: 'the sign flag is not set (positive)',
        SIGN: '{}<' + BYTE.format(128),
        BIT_7_TEST: '{} is reset',
    }, {
        NA: 'the sign flag is set (negative)',
        SIGN: '{}>=' + BYTE.format(128),
        BIT_7_TEST: '{} is set',
    }),
    ZF: ({
        NA: 'the zero flag is not set',
        ZERO: '{}>0',
        COMPARE: f'{A}<>{{}}',
        BIT_TEST: '{} is set',
    }, {
        NA: 'the zero flag is set',
        ZERO: '{}=0',
        COMPARE: f'{A}={{}}',
        BIT_TEST: '{} is reset',
    }),
    PF: ({
        NA: 'the parity/overflow flag is not set (parity odd)',
        PARITY: 'the parity flag is not set',
        PARITY_REG: 'the parity of {} is odd',
        OFLOW: 'there was no overflow',
        OFLOW_INC: '{}<>' + BYTE.format(128),
        OFLOW_DEC: '{}<>' + BYTE.format(127),
        IFF2: 'interrupts are disabled',
        BLOCK: f'{BC}=0',
        BIT_TEST: '{} is set',
    }, {
        NA: 'the parity/overflow flag is set (parity even)',
        PARITY: 'the parity flag is set',
        PARITY_REG: 'the parity of {} is even',
        OFLOW: 'there was overflow',
        OFLOW_INC: '{}=' + BYTE.format(128),
        OFLOW_DEC: '{}=' + BYTE.format(127),
        IFF2: 'interrupts are enabled',
        BLOCK: f'{BC}>0',
        BIT_TEST: '{} is reset',
    }),
    CF: ({
        NA: 'the carry flag is not set',
        COMPARE: f'{A}>={{}}',
        NEGATE: f'{A}=0',
    }, {
        NA: 'the carry flag is set',
        COMPARE: f'{A}<{{}}',
        NEGATE: f'{A}>0',
    })
}

DEFAULT_FLAGS = {SF: SIGN, ZF: ZERO, PF: PARITY, CF: NA}
CP_FLAGS = {SF: NA, ZF: COMPARE, PF: OFLOW, CF: COMPARE}
CP0_FLAGS = {SF: NA, ZF: COMPARE, PF: OFLOW, CF: NA}
PARITY_FLAGS = {SF: SIGN, ZF: ZERO, PF: PARITY_REG, CF: NA}
OFLOW_FLAGS = {SF: SIGN, ZF: ZERO, PF: OFLOW, CF: NA}
OFLOW_INC_FLAGS = {SF: SIGN, ZF: ZERO, PF: OFLOW_INC, CF: NA}
OFLOW_DEC_FLAGS = {SF: SIGN, ZF: ZERO, PF: OFLOW_DEC, CF: NA}
IFF2_FLAGS = {SF: SIGN, ZF: ZERO, PF: IFF2, CF: NA}
NEGATE_FLAGS = {SF: SIGN, ZF: ZERO, PF: PARITY_REG, CF: NEGATE}
LDBLOCK_FLAGS = {SF: NA, ZF: NA, PF: BLOCK, CF: NA}
CPBLOCK_FLAGS = {SF: NA, ZF: COMPARE, PF: BLOCK, CF: NA}
BIT_TEST_FLAGS = {SF: NA, ZF: BIT_TEST, PF: BIT_TEST, CF: NA}
BIT_7_TEST_FLAGS = {SF: BIT_7_TEST, ZF: BIT_TEST, PF: BIT_TEST, CF: NA}

ADD = '{0}={0}+{1}'
ADC = '{0}={0}+carry+{1}'
AND = f'{A}={A}&{{}}'
BIT = 'Set the zero flag if bit {} of {} is 0'
CP = f'Set the zero flag if {A}={{0}}, or the carry flag if {A}<{{0}}'
DEC = '{0}={0}-1'
EX_SP = 'Exchange the last item on the stack with {}'
IM = 'Set interrupt mode {}'
IN = '{}=IN {}'
INC = '{0}={0}+1'
JP_rr = 'Jump to {}'
LD = '{}={}'
LD_mm_rr = 'POKE {0},{1}; POKE {0},{2}'
LD_rr_mm = '{1}=PEEK {0}; {2}=PEEK {0}'
NEG = f'{A}=#N(256,2,,1)($)-{A}'
NOP = 'Do nothing'
OR = f'{A}={A}|{{}}'
OUT = 'OUT {},{}'
POP = 'Pop last item from stack into {}'
PUSH = 'Push {} onto the stack'
RES = 'Reset bit {} of {}'
RETI = 'Return from maskable interrupt'
RETN = 'Return from non-maskable interrupt'
RL = 'Rotate {} left through the carry flag'
RLC = 'Rotate {} left circular (copying bit 7 into bit 0 and into the carry flag)'
RR = 'Rotate {} right through the carry flag'
RRC = 'Rotate {} right circular (copying bit 0 into bit 7 and into the carry flag)'
RST = 'CALL #R{}'
SBC = '{0}={0}-carry-{1}'
SET = 'Set bit {} of {}'
SLA = 'Shift {} left (copying bit 7 into the carry flag, and resetting bit 0)'
SLL = 'Shift {} left (copying bit 7 into the carry flag, and setting bit 0)'
SRA = 'Shift {} right (copying bit 0 into the carry flag, and leaving bit 7 unchanged)'
SRL = 'Shift {} right (copying bit 0 into the carry flag, and resetting bit 7)'
SUB = f'{A}={A}-{{}}'
XOR = f'{A}={A}^{{}}'

class CommentGenerator:
    def __init__(self):
        self.exp_addr = None
        self.ctx = None
        self.reg = None

        self.ops = {
            0x00: (None, NOP, None),
            0x01: (self.word_arg, LD.format(BC, WORD), None),
            0x02: (None, f'POKE {BC},{A}', None),
            0x03: (None, INC.format(BC), None),
            0x07: (None, RLC.format(A), None),
            0x08: (None, f"Exchange {AF} and {AF}'", None),
            0x09: (None, ADD.format(HL, BC), None),
            0x0A: (None, f'{A}=PEEK {BC}', None),
            0x0B: (None, DEC.format(BC), None),
            0x0F: (None, RRC.format(A), None),
            0x10: (self.jr_arg, f'Decrement {B} and jump to #R{{}} if {B}>0', None),
            0x11: (self.word_arg, LD.format(DE, WORD), None),
            0x12: (None, f'POKE {DE},{A}', None),
            0x13: (None, INC.format(DE), None),
            0x17: (None, RL.format(A), None),
            0x18: (self.jr_arg, 'Jump to #R{}', None),
            0x19: (None, ADD.format(HL, DE), None),
            0x1A: (None, f'{A}=PEEK {DE}', None),
            0x1B: (None, DEC.format(DE), None),
            0x1F: (None, RR.format(A), None),
            0x20: (self.jr_cc, (ZF, 0), None),
            0x21: (self.word_arg, LD.format(HL, WORD), None),
            0x22: (self.addr_arg, LD_mm_rr.format(WORD, L, H), None),
            0x23: (None, INC.format(HL), None),
            0x27: (None, f'Decimal adjust {A}', (A, PARITY_FLAGS)),
            0x28: (self.jr_cc, (ZF, 1), None),
            0x29: (None, ADD.format(HL, HL), None),
            0x2A: (self.addr_arg, LD_rr_mm.format(WORD, L, H), None),
            0x2B: (None, DEC.format(HL), None),
            0x2F: (None, f'{A}={BYTE}-{A}'.format('$FF'), None),
            0x30: (self.jr_cc, (CF, 0), None),
            0x31: (self.word_arg, LD.format(SP, WORD), None),
            0x32: (self.word_arg, f'POKE {WORD},{A}', None),
            0x33: (None, INC.format(SP), None),
            0x37: (None, 'Set the carry flag', None),
            0x38: (self.jr_cc, (CF, 1), None),
            0x39: (None, ADD.format(HL, SP), None),
            0x3A: (self.word_arg, f'{A}=PEEK {WORD}', None),
            0x3B: (None, DEC.format(SP), None),
            0x3F: (None, 'Complement the carry flag', None),
            0x76: (None, 'Wait for the next interrupt', None),
            0x97: (None, f'{A}=0', (A, OFLOW_FLAGS)),
            0x9F: (None, f'{A}={BYTE} if carry flag is set, 0 otherwise'.format('$FF'), (A, OFLOW_FLAGS)),
            0xA7: (None, f'Clear the carry flag and set the zero flag if {A}=0', (A, PARITY_FLAGS)),
            0xAF: (None, f'{A}=0', (A, PARITY_FLAGS)),
            0xB7: (None, f'Clear the carry flag and set the zero flag if {A}=0', (A, PARITY_FLAGS)),
            0xBF: (None, 'Clear the carry flag and set the zero flag', None),
            0xC0: (self.ret_cc, (ZF, 0), None),
            0xC1: (None, POP.format(BC), None),
            0xC2: (self.jp_cc, (ZF, 0), None),
            0xC3: (self.word_arg, 'Jump to #R{}', None),
            0xC4: (self.call_cc, (ZF, 0), None),
            0xC5: (None, PUSH.format(BC), None),
            0xC6: (self.byte_arg, ADD.format(A, BYTE), (A, OFLOW_FLAGS)),
            0xC8: (self.ret_cc, (ZF, 1), None),
            0xC9: (None, 'Return', None),
            0xCA: (self.jp_cc, (ZF, 1), None),
            0xCB: (self.cb_arg, None, None),
            0xCC: (self.call_cc, (ZF, 1), None),
            0xCD: (self.word_arg, 'CALL #R{}', None),
            0xCE: (self.byte_arg, ADC.format(A, BYTE), (A, OFLOW_FLAGS)),
            0xD0: (self.ret_cc, (CF, 0), None),
            0xD1: (None, POP.format(DE), None),
            0xD2: (self.jp_cc, (CF, 0), None),
            0xD3: (self.byte_arg, OUT.format(BYTE, A), None),
            0xD4: (self.call_cc, (CF, 0), None),
            0xD5: (None, PUSH.format(DE), None),
            0xD6: (self.byte_arg, SUB.format(BYTE), (A, OFLOW_FLAGS)),
            0xD8: (self.ret_cc, (CF, 1), None),
            0xD9: (None, f"Exchange {BC}, {DE} and {HL} with {BC}', {DE}' and {HL}'", None),
            0xDA: (self.jp_cc, (CF, 1), None),
            0xDB: (self.byte_arg, IN.format(A, f'(#N(256,,,1)($)*{A}+{BYTE})'), None),
            0xDC: (self.call_cc, (CF, 1), None),
            0xDD: (self.dd_arg, None, None),
            0xDE: (self.byte_arg, SBC.format(A, BYTE), (A, OFLOW_FLAGS)),
            0xE0: (self.ret_cc, (PF, 0), None),
            0xE1: (None, POP.format(HL), None),
            0xE2: (self.jp_cc, (PF, 0), None),
            0xE3: (None, EX_SP.format(HL), None),
            0xE4: (self.call_cc, (PF, 0), None),
            0xE5: (None, PUSH.format(HL), None),
            0xE6: (self.and_n, None, (A, PARITY_FLAGS)),
            0xE8: (self.ret_cc, (PF, 1), None),
            0xE9: (None, JP_rr.format(HL), None),
            0xEA: (self.jp_cc, (PF, 1), None),
            0xEB: (None, f'Exchange {DE} and {HL}', None),
            0xEC: (self.call_cc, (PF, 1), None),
            0xED: (self.ed_arg, None, None),
            0xEE: (self.xor_n, None, (A, PARITY_FLAGS)),
            0xF0: (self.ret_cc, (SF, 0), None),
            0xF1: (None, POP.format(AF), None),
            0xF2: (self.jp_cc, (SF, 0), None),
            0xF3: (None, 'Disable interrupts', None),
            0xF4: (self.call_cc, (SF, 0), None),
            0xF5: (None, PUSH.format(AF), None),
            0xF6: (self.or_n, None, (A, PARITY_FLAGS)),
            0xF8: (self.ret_cc, (SF, 1), None),
            0xF9: (None, LD.format(SP, HL), None),
            0xFA: (self.jp_cc, (SF, 1), None),
            0xFB: (None, 'Enable interrupts', None),
            0xFC: (self.call_cc, (SF, 1), None),
            0xFD: (self.fd_arg, None, None),
            0xFE: (self.cp_n, None, None)
        }

        self.after_DD = {
            0x09: (None, ADD.format(IX, BC), None),
            0x19: (None, ADD.format(IX, DE), None),
            0x21: (self.word_arg, LD.format(IX, WORD), None),
            0x22: (self.addr_arg, LD_mm_rr.format(WORD, IXl, IXh), None),
            0x23: (None, INC.format(IX), None),
            0x24: (None, INC.format(IXh), (IXh, OFLOW_INC_FLAGS)),
            0x25: (None, DEC.format(IXh), (IXh, OFLOW_DEC_FLAGS)),
            0x26: (self.byte_arg, LD.format(IXh, BYTE), None),
            0x29: (None, ADD.format(IX, IX), None),
            0x2A: (self.addr_arg, LD_rr_mm.format(WORD, IXl, IXh), None),
            0x2B: (None, DEC.format(IX), None),
            0x2C: (None, INC.format(IXl), (IXl, OFLOW_INC_FLAGS)),
            0x2D: (None, DEC.format(IXl), (IXl, OFLOW_DEC_FLAGS)),
            0x2E: (self.byte_arg, LD.format(IXl, BYTE), None),
            0x34: (self.index, 'POKE {ixd},(PEEK {ixd})+1', ('(PEEK {ixd})', OFLOW_INC_FLAGS)),
            0x35: (self.index, 'POKE {ixd},(PEEK {ixd})-1', ('(PEEK {ixd})', OFLOW_DEC_FLAGS)),
            0x36: (self.index_arg, 'POKE {},{}', None),
            0x39: (None, ADD.format(IX, SP), None),
            0x44: (None, LD.format(B, IXh), None),
            0x45: (None, LD.format(B, IXl), None),
            0x46: (self.index, f'{B}=PEEK {{ixd}}', None),
            0x4C: (None, LD.format(C, IXh), None),
            0x4D: (None, LD.format(C, IXl), None),
            0x4E: (self.index, f'{C}=PEEK {{ixd}}', None),
            0x54: (None, LD.format(D, IXh), None),
            0x55: (None, LD.format(D, IXl), None),
            0x56: (self.index, f'{D}=PEEK {{ixd}}', None),
            0x5C: (None, LD.format(E, IXh), None),
            0x5D: (None, LD.format(E, IXl), None),
            0x5E: (self.index, f'{E}=PEEK {{ixd}}', None),
            0x60: (None, LD.format(IXh, B), None),
            0x61: (None, LD.format(IXh, C), None),
            0x62: (None, LD.format(IXh, D), None),
            0x63: (None, LD.format(IXh, E), None),
            0x64: (None, NOP, None),
            0x65: (None, LD.format(IXh, IXl), None),
            0x66: (self.index, f'{H}=PEEK {{ixd}}', None),
            0x67: (None, LD.format(IXh, A), None),
            0x68: (None, LD.format(IXl, B), None),
            0x69: (None, LD.format(IXl, C), None),
            0x6A: (None, LD.format(IXl, D), None),
            0x6B: (None, LD.format(IXl, E), None),
            0x6C: (None, LD.format(IXl, IXh), None),
            0x6D: (None, NOP, None),
            0x6E: (self.index, f'{L}=PEEK {{ixd}}', None),
            0x6F: (None, LD.format(IXl, A), None),
            0x7C: (None, LD.format(A, IXh), None),
            0x7D: (None, LD.format(A, IXl), None),
            0x7E: (self.index, f'{A}=PEEK {{ixd}}', None),
            0x84: (None, ADD.format(A, IXh), (A, OFLOW_FLAGS)),
            0x85: (None, ADD.format(A, IXl), (A, OFLOW_FLAGS)),
            0x86: (self.index, ADD.format(A, 'PEEK {ixd}'), (A, OFLOW_FLAGS)),
            0x8C: (None, ADC.format(A, IXh), (A, OFLOW_FLAGS)),
            0x8D: (None, ADC.format(A, IXl), (A, OFLOW_FLAGS)),
            0x8E: (self.index, ADC.format(A, 'PEEK {ixd}'), (A, OFLOW_FLAGS)),
            0x94: (None, SUB.format(IXh), (A, OFLOW_FLAGS)),
            0x95: (None, SUB.format(IXl), (A, OFLOW_FLAGS)),
            0x96: (self.index, SUB.format('PEEK {ixd}'), (A, OFLOW_FLAGS)),
            0x9C: (None, SBC.format(A, IXh), (A, OFLOW_FLAGS)),
            0x9D: (None, SBC.format(A, IXl), (A, OFLOW_FLAGS)),
            0x9E: (self.index, SBC.format(A, 'PEEK {ixd}'), (A, OFLOW_FLAGS)),
            0xA4: (None, AND.format(IXh), (A, PARITY_FLAGS)),
            0xA5: (None, AND.format(IXl), (A, PARITY_FLAGS)),
            0xA6: (self.index, AND.format('PEEK {ixd}'), (A, PARITY_FLAGS)),
            0xAC: (None, XOR.format(IXh), (A, PARITY_FLAGS)),
            0xAD: (None, XOR.format(IXl), (A, PARITY_FLAGS)),
            0xAE: (self.index, XOR.format('PEEK {ixd}'), (A, PARITY_FLAGS)),
            0xB4: (None, OR.format(IXh), (A, PARITY_FLAGS)),
            0xB5: (None, OR.format(IXl), (A, PARITY_FLAGS)),
            0xB6: (self.index, OR.format('PEEK {ixd}'), (A, PARITY_FLAGS)),
            0xBC: (None, CP.format(IXh), (IXh, CP_FLAGS)),
            0xBD: (None, CP.format(IXl), (IXl, CP_FLAGS)),
            0xBE: (self.index, CP.format('PEEK {ixd}'), ('PEEK {ixd}', CP_FLAGS)),
            0xCB: (self.ddcb_arg, None, None),
            0xE1: (None, POP.format(IX), None),
            0xE3: (None, EX_SP.format(IX), None),
            0xE5: (None, PUSH.format(IX), None),
            0xE9: (None, JP_rr.format(IX), None),
            0xF9: (None, LD.format(SP, IX), None)
        }

        self.after_ED = {
            0x42: (None, SBC.format(HL, BC), (HL, OFLOW_FLAGS)),
            0x43: (self.addr_arg, LD_mm_rr.format(WORD, C, B), None),
            0x47: (None, LD.format(I, A), None),
            0x4A: (None, ADC.format(HL, BC), (HL, OFLOW_FLAGS)),
            0x4B: (self.addr_arg, LD_rr_mm.format(WORD, C, B), None),
            0x4F: (None, LD.format(R, A), None),
            0x52: (None, SBC.format(HL, DE), (HL, OFLOW_FLAGS)),
            0x53: (self.addr_arg, LD_mm_rr.format(WORD, E, D), None),
            0x57: (None, LD.format(A, I), (A, IFF2_FLAGS)),
            0x5A: (None, ADC.format(HL, DE), (HL, OFLOW_FLAGS)),
            0x5B: (self.addr_arg, LD_rr_mm.format(WORD, E, D), None),
            0x5F: (None, LD.format(A, R), (A, IFF2_FLAGS)),
            0x62: (None, f'{HL}={WORD} if carry flag is set, 0 otherwise'.format('$FFFF'), (HL, OFLOW_FLAGS)),
            0x63: (self.addr_arg, LD_mm_rr.format(WORD, L, H), None),
            0x67: (None, f'Rotate the low nibble of {A} and all of ({HL}) right 4 bits', (A, PARITY_FLAGS)),
            0x6A: (None, ADC.format(HL, HL), (HL, OFLOW_FLAGS)),
            0x6B: (self.addr_arg, LD_rr_mm.format(WORD, L, H), None),
            0x6F: (None, f'Rotate the low nibble of {A} and all of ({HL}) left 4 bits', (A, PARITY_FLAGS)),
            0x70: (None, f'Read from port {BC} and set flags accordingly', None),
            0x71: (None, OUT.format(BC, 0), None),
            0x72: (None, SBC.format(HL, SP), (HL, OFLOW_FLAGS)),
            0x73: (self.addr_arg, LD_mm_rr.format(WORD, SPl, SPh), None),
            0x7A: (None, ADC.format(HL, SP), (HL, OFLOW_FLAGS)),
            0x7B: (self.addr_arg, f'{SP}=PEEK {WORD}+#N(256,2,,1)($)*PEEK {WORD}', None),
            0xA0: (None, f'POKE {DE},PEEK {HL}; {HL}={HL}+1; {DE}={DE}+1; {BC}={BC}-1', ('', LDBLOCK_FLAGS)),
            0xA1: (None, f'Compare {A} with PEEK {HL}; {HL}={HL}+1; {BC}={BC}-1', (f'PEEK {HL}', CPBLOCK_FLAGS)),
            0xA2: (None, f'POKE {HL},IN {BC}; {HL}={HL}+1; {B}={B}-1', (B, DEFAULT_FLAGS)),
            0xA3: (None, f'{B}={B}-1; OUT {BC},PEEK {HL}; {HL}={HL}+1', (B, DEFAULT_FLAGS)),
            0xA8: (None, f'POKE {DE},PEEK {HL}; {HL}={HL}-1; {DE}={DE}-1; {BC}={BC}-1', ('', LDBLOCK_FLAGS)),
            0xA9: (None, f'Compare {A} with PEEK {HL}; {HL}={HL}-1; {BC}={BC}-1', (f'PEEK {HL}', CPBLOCK_FLAGS)),
            0xAA: (None, f'POKE {HL},IN {BC}; {HL}={HL}-1; {B}={B}-1', (B, DEFAULT_FLAGS)),
            0xAB: (None, f'{B}={B}-1; OUT {BC},PEEK {HL}; {HL}={HL}-1', (B, DEFAULT_FLAGS)),
            0xB0: (None, f'POKE {DE},PEEK {HL}; {HL}={HL}+1; {DE}={DE}+1; {BC}={BC}-1; repeat until {BC}=0', None),
            0xB1: (None, f'Compare {A} with PEEK {HL}; {HL}={HL}+1; {BC}={BC}-1; repeat until {BC}=0 or {A}=PEEK {HL}', (f'PEEK {HL}', CPBLOCK_FLAGS)),
            0xB2: (None, f'POKE {HL},IN {BC}; {HL}={HL}+1; {B}={B}-1; repeat until {B}=0', None),
            0xB3: (None, f'{B}={B}-1; OUT {BC},PEEK {HL}; {HL}={HL}+1; repeat until {B}=0', None),
            0xB8: (None, f'POKE {DE},PEEK {HL}; {HL}={HL}-1; {DE}={DE}-1; {BC}={BC}-1; repeat until {BC}=0', None),
            0xB9: (None, f'Compare {A} with PEEK {HL}; {HL}={HL}-1; {BC}={BC}-1; repeat until {BC}=0 or {A}=PEEK {HL}', (f'PEEK {HL}', CPBLOCK_FLAGS)),
            0xBA: (None, f'POKE {HL},IN {BC}; {HL}={HL}-1; {B}={B}-1; repeat until {B}=0', None),
            0xBB: (None, f'{B}={B}-1; OUT {BC},PEEK {HL}; {HL}={HL}-1; repeat until {B}=0', None)
        }

        self.after_CB = {}
        self.after_DDCB = {}

        for i, r in enumerate((B, C, D, E, H, L, f'({HL})', A)):
            if i == 6:
                self.ops[0x04 + 8 * i] = (None, f'POKE {HL},(PEEK {HL})+1', (f'(PEEK {HL})', OFLOW_INC_FLAGS))
                self.ops[0x05 + 8 * i] = (None, f'POKE {HL},(PEEK {HL})-1', (f'(PEEK {HL})', OFLOW_DEC_FLAGS))
                self.ops[0x06 + 8 * i] = (self.byte_arg, f'POKE {HL},{BYTE}', None)
                alo_r = f'PEEK {HL}'
            else:
                self.ops[0x04 + 8 * i] = (None, INC.format(r), (r, OFLOW_INC_FLAGS))
                self.ops[0x05 + 8 * i] = (None, DEC.format(r), (r, OFLOW_DEC_FLAGS))
                self.ops[0x06 + 8 * i] = (self.byte_arg, LD.format(r, BYTE), None)
                alo_r = r
            for j, r2 in enumerate((B, C, D, E, H, L, '', A)):
                if i == j:
                    if i != 6:
                        self.ops[0x40 + 8 * i + j] = (None, NOP, None)
                elif i == 6:
                    self.ops[0x40 + 8 * i + j] = (None, f'POKE {HL},{r2}', None)
                elif j == 6:
                    self.ops[0x40 + 8 * i + j] = (None, f'{r}=PEEK {HL}', None)
                else:
                    self.ops[0x40 + 8 * i + j] = (None, LD.format(r, r2), None)
            self.ops[0x80 + i] = (None, ADD.format(A, alo_r), (A, OFLOW_FLAGS))
            self.ops[0x88 + i] = (None, ADC.format(A, alo_r), (A, OFLOW_FLAGS))
            if i < 7:
                self.ops[0x90 + i] = (None, SUB.format(alo_r), (A, OFLOW_FLAGS))
                self.ops[0x98 + i] = (None, SBC.format(A, alo_r), (A, OFLOW_FLAGS))
                self.ops[0xA0 + i] = (None, AND.format(alo_r), (A, PARITY_FLAGS))
                self.ops[0xA8 + i] = (None, XOR.format(alo_r), (A, PARITY_FLAGS))
                self.ops[0xB0 + i] = (None, OR.format(alo_r), (A, PARITY_FLAGS))
                if i == 6:
                    self.ops[0xB8 + i] = (None, CP.format(alo_r), (f'PEEK {HL}', CP_FLAGS))
                else:
                    self.ops[0xB8 + i] = (None, CP.format(alo_r), (r, CP_FLAGS))
            self.ops[0xC7 + 8 * i] = (None, RST.format(8 * i), None)
            if i != 6:
                self.after_DD[0x70 + i] = (self.index, f'POKE {{ixd}},{r}', None)
                self.after_ED[0x40 + 8 * i] = (None, IN.format(r, BC), (r, PARITY_FLAGS))
                self.after_ED[0x41 + 8 * i] = (None, OUT.format(BC, r), None)
            self.after_ED[0x44 + 8 * i] = (None, NEG, (A, NEGATE_FLAGS))
            self.after_ED[0x45 + 8 * i] = (None, (RETN, RETI)[i == 1], None)
            self.after_ED[0x46 + 8 * i] = (None, IM.format((0, 0, 1, 2)[i % 4]), None)
            for b, comment in enumerate((RLC, RRC, RL, RR, SLA, SRA, SLL, SRL)):
                bit_test_flags = BIT_7_TEST_FLAGS if b == 7 else BIT_TEST_FLAGS
                self.after_CB[0x80 + 8 * b + i] = (RES.format(b, r), None)
                self.after_CB[0xC0 + 8 * b + i] = (SET.format(b, r), None)
                self.after_DDCB[0x40 + 8 * b + i] = (self.index, BIT.format(b, '{ixd}'), (f'bit {b} of PEEK {{ixd}}', bit_test_flags))
                if i == 6:
                    self.after_CB[0x00 + 8 * b + i] = (comment.format(r), (f'(PEEK {HL})', PARITY_FLAGS))
                    self.after_CB[0x40 + 8 * b + i] = (BIT.format(b, r), (f'bit {b} of PEEK {HL}', bit_test_flags))
                    self.after_DDCB[0x00 + 8 * b + i] = (self.index, comment.format('{ixd}'), ('(PEEK {ixd})', PARITY_FLAGS))
                    self.after_DDCB[0x80 + 8 * b + i] = (self.index, RES.format(b, '{ixd}'), None)
                    self.after_DDCB[0xC0 + 8 * b + i] = (self.index, SET.format(b, '{ixd}'), None)
                else:
                    self.after_CB[0x00 + 8 * b + i] = (comment.format(r), (r, PARITY_FLAGS))
                    self.after_CB[0x40 + 8 * b + i] = (BIT.format(b, r), (f'bit {b} of {r}', bit_test_flags))
                    self.after_DDCB[0x00 + 8 * b + i] = (self.index, comment.format('{ixd}') + f' and copy the result to {r}', (r, PARITY_FLAGS))
                    self.after_DDCB[0x80 + 8 * b + i] = (self.index, RES.format(b, '{ixd}') + f' and copy the result to {r}', None)
                    self.after_DDCB[0xC0 + 8 * b + i] = (self.index, SET.format(b, '{ixd}') + f' and copy the result to {r}', None)

    # Component API
    def get_comment(self, instruction):
        """Return an instruction comment. The *instruction* object has the
        following attributes:

        * *address* - the address of the instruction
        * *bytes* - the byte values of the instruction
        """
        if instruction.address != self.exp_addr:
            self.ctx = None
        decoder, template, fctx = self.ops[instruction.bytes[0]]
        if decoder is None:
            rv = template
        elif template is None:
            rv = decoder(instruction.address, instruction.bytes)
        elif isinstance(template, str):
            rv = decoder(template, instruction.address, instruction.bytes)
        else:
            rv = decoder(*template, instruction.address, instruction.bytes)
        if isinstance(rv, str):
            comment = rv
        else:
            comment, fctx = rv
        if fctx:
            self.reg, self.ctx = fctx[0].format(*instruction.bytes), fctx[1]
        else:
            self.ctx = None
        self.exp_addr = (instruction.address + len(instruction.bytes)) % 65536
        return comment

    def byte_arg(self, template, address, values):
        if values[0] in PREFIXES:
            return template.format(values[2])
        return template.format(values[1])

    def word_arg(self, template, address, values):
        if values[0] in PREFIXES:
            return template.format(values[2] + 256 * values[3])
        return template.format(values[1] + 256 * values[2])

    def and_n(self, address, values):
        bits = BITS[values[1]]
        if len(bits) == 0:
            return f'{A}=0'
        if len(bits) == 1:
            return f'Keep only bit {bits[0]} of {A}'
        if len(bits) < 5:
            bits_str = ', '.join(str(b) for b in bits[:-1]) + f' and {bits[-1]}'
            return f'Keep only bits {bits_str} of {A}'
        nbits = [b for b in range(8) if b not in bits]
        if len(nbits) == 0:
            return f'Set the zero flag if {A}=0, and reset the carry flag'
        if len(nbits) == 1:
            return f'Reset bit {nbits[0]} of {A}'
        nbits_str = ', '.join(str(b) for b in nbits[:-1]) + f' and {nbits[-1]}'
        return f'Reset bits {nbits_str} of {A}'

    def or_n(self, address, values):
        bits = BITS[values[1]]
        if len(bits) == 0:
            return f'Set the zero flag if {A}=0, and reset the carry flag'
        if len(bits) == 1:
            return f'Set bit {bits[0]} of {A}'
        if len(bits) < 8:
            bits_str = ', '.join(str(b) for b in bits[:-1]) + f' and {bits[-1]}'
            return f'Set bits {bits_str} of {A}'
        return f'{A}={BYTE}'.format(255)

    def xor_n(self, address, values):
        bits = BITS[values[1]]
        if len(bits) == 0:
            return f'Set the zero flag if {A}=0, and reset the carry flag'
        if len(bits) == 1:
            return f'Flip bit {bits[0]} of {A}'
        if len(bits) < 8:
            bits_str = ', '.join(str(b) for b in bits[:-1]) + f' and {bits[-1]}'
            return f'Flip bits {bits_str} of {A}'
        return f'Flip every bit of {A}'

    def cp_n(self, address, values):
        n = BYTE.format(values[1])
        if values[1]:
            return CP.format(n), (n, CP_FLAGS)
        return f'Set the zero flag if {A}=0, and reset the carry flag', (n, CP0_FLAGS)

    def addr_arg(self, template, address, values):
        if values[0] in PREFIXES:
            addr = values[2] + 256 * values[3]
        else:
            addr = values[1] + 256 * values[2]
        return template.format(addr, (addr + 1) % 65536)

    def jr_arg(self, template, address, values):
        if values[1] < 128:
            return template.format((address + 2 + values[1]) % 65536)
        return template.format((address + values[1] - 254) % 65536)

    def index(self, template, address, values):
        return template.format(ixd=self.index_offset(address, values))

    def index_arg(self, template, address, values):
        return template.format(self.index_offset(address, values), values[3])

    def index_offset(self, address, values):
        if values[2] < 128:
            return f'({IX}+{BYTE})'.format(values[2])
        return f'({IX}-{BYTE})'.format(256 - values[2])

    def cb_arg(self, address, values):
        return self.after_CB[values[1]]

    def ed_arg(self, address, values):
        decoder, template, fctx = self.after_ED.get(values[1], (None, '', None))
        if decoder:
            return decoder(template, address, values), fctx
        return template, fctx

    def dd_arg(self, address, values):
        decoder, template, fctx = self.after_DD.get(values[1], (None, '', None))
        if decoder:
            rv = decoder(template, address, values)
            if isinstance(rv, str):
                comment = rv
            else:
                comment, fctx = rv
        else:
            comment = template
        if fctx and 'ixd' in fctx[0]:
            fctx = (self.index(fctx[0], address, values), fctx[1])
        return comment, fctx

    def fd_arg(self, address, values):
        comment, fctx = self.dd_arg(address, values)
        if fctx:
            fctx = (fctx[0].replace('ix', 'iy'), fctx[1])
        return comment.replace('ix', 'iy'), fctx

    def ddcb_arg(self, template, address, values):
        decoder, template, fctx = self.after_DDCB.get(values[3], (None, None, None))
        return decoder(template, address, values), fctx

    def call_cc(self, flag, value, address, values):
        addr = values[1] + 256 * values[2]
        if self.ctx:
            cond = FLAGS[flag][value][self.ctx[flag]].format(self.reg)
            return f'CALL #R{addr} if {cond}'
        return f'CALL #R{addr} if {FLAGS[flag][value][NA]}'

    def jp_cc(self, flag, value, address, values):
        addr = values[1] + 256 * values[2]
        if self.ctx:
            cond = FLAGS[flag][value][self.ctx[flag]].format(self.reg)
            return f'Jump to #R{addr} if {cond}'
        return f'Jump to #R{addr} if {FLAGS[flag][value][NA]}'

    def jr_cc(self, flag, value, address, values):
        if values[1] < 128:
            addr = (address + 2 + values[1]) % 65536
        else:
            addr = (address + values[1] - 254) % 65536
        if self.ctx:
            cond = FLAGS[flag][value][self.ctx[flag]].format(self.reg)
            return f'Jump to #R{addr} if {cond}'
        return f'Jump to #R{addr} if {FLAGS[flag][value][NA]}'

    def ret_cc(self, flag, value, address, values):
        if self.ctx:
            cond = FLAGS[flag][value][self.ctx[flag]].format(self.reg)
            return f'Return if {cond}'
        return f'Return if {FLAGS[flag][value][NA]}'
