# Copyright 2024 Richard Dymond (rjdymond@gmail.com)
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
REGISTERS = ('#REGb', '#REGc', '#REGd', '#REGe', '#REGh', '#REGl', '(#REGhl)', '#REGa')
BITS = tuple(tuple(b for b in range(8) if (n >> b) % 2) for n in range(256))

ZF, SF, PF, CF = 0b01000000, 0b10000000, 0b00000100, 0b00000001
NA, SIGN, ZERO, COMPARE, PARITY, PARITY_REG, OFLOW, OFLOW_INC, OFLOW_DEC, IFF2, BLOCK, NEGATE = range(12)

FLAGS = {
    SF: ({
        NA: 'the sign flag is not set (positive)',
        SIGN: '{}<' + BYTE.format(128),
    }, {
        NA: 'the sign flag is set (negative)',
        SIGN: '{}>=' + BYTE.format(128),
    }),
    ZF: ({
        NA: 'the zero flag is not set',
        ZERO: '{}>0',
        COMPARE: '#REGa<>{}',
    }, {
        NA: 'the zero flag is set',
        ZERO: '{}=0',
        COMPARE: '#REGa={}',
    }),
    PF: ({
        NA: 'the parity/overflow flag is not set (parity odd)',
        PARITY: 'the parity flag is not set',
        PARITY_REG: 'the parity of {} is odd',
        OFLOW: 'there was no overflow',
        OFLOW_INC: '{}<>' + BYTE.format(128),
        OFLOW_DEC: '{}<>' + BYTE.format(127),
        IFF2: 'interrupts are disabled',
        BLOCK: '#REGbc=0',
    }, {
        NA: 'the parity/overflow flag is set (parity even)',
        PARITY: 'the parity flag is set',
        PARITY_REG: 'the parity of {} is even',
        OFLOW: 'there was overflow',
        OFLOW_INC: '{}=' + BYTE.format(128),
        OFLOW_DEC: '{}=' + BYTE.format(127),
        IFF2: 'interrupts are enabled',
        BLOCK: '#REGbc>0',
    }),
    CF: ({
        NA: 'the carry flag is not set',
        COMPARE: '#REGa>={}',
        NEGATE: '#REGa=0',
    }, {
        NA: 'the carry flag is set',
        COMPARE: '#REGa<{}',
        NEGATE: '#REGa>0',
    })
}

DEFAULT_FLAGS = {SF: SIGN, ZF: ZERO, PF: PARITY, CF: NA}
CP_FLAGS = {SF: NA, ZF: COMPARE, PF: OFLOW, CF: COMPARE}
PARITY_FLAGS = {SF: SIGN, ZF: ZERO, PF: PARITY_REG, CF: NA}
OFLOW_FLAGS = {SF: SIGN, ZF: ZERO, PF: OFLOW, CF: NA}
OFLOW_INC_FLAGS = {SF: SIGN, ZF: ZERO, PF: OFLOW_INC, CF: NA}
OFLOW_DEC_FLAGS = {SF: SIGN, ZF: ZERO, PF: OFLOW_DEC, CF: NA}
IFF2_FLAGS = {SF: SIGN, ZF: ZERO, PF: IFF2, CF: NA}
NEGATE_FLAGS = {SF: SIGN, ZF: ZERO, PF: PARITY_REG, CF: NEGATE}
LDBLOCK_FLAGS = {SF: NA, ZF: NA, PF: BLOCK, CF: NA}
CPBLOCK_FLAGS = {SF: NA, ZF: COMPARE, PF: BLOCK, CF: NA}

ADD = '{0}={0}+{1}'
ADD_A = '#REGa=#REGa+{}'
ADC = '{0}={0}+carry+{1}'
ADC_A = '#REGa=#REGa+carry+{}'
AND = '#REGa=#REGa&{}'
BIT = 'Set the zero flag if bit {} of {} is 0'
CP = 'Set the zero flag if #REGa={0}, or the carry flag if #REGa<{0}'
DEC = '{0}={0}-1'
EX_SP = 'Exchange the last item on the stack with {}'
IM = 'Set interrupt mode {}'
IN = '{}=IN {}'
INC = '{0}={0}+1'
JP_rr = 'Jump to #REG{}'
LD = '{}={}'
LD_mm_rr = 'POKE {0},#REG{1}; POKE {0},#REG{2}'
LD_rr_mm = '#REG{1}=PEEK {0}; #REG{2}=PEEK {0}'
NEG = '#REGa=#N(256,2,,1)($)-#REGa'
NOP = 'Do nothing'
OR = '#REGa=#REGa|{}'
OUT = 'OUT {},{}'
POP = 'Pop last item from stack into #REG{}'
PUSH = 'Push #REG{} onto the stack'
RES = 'Reset bit {} of {}'
RETI = 'Return from maskable interrupt'
RETN = 'Return from non-maskable interrupt'
RL = 'Rotate {} left through the carry flag'
RLC = 'Rotate {} left circular (copying bit 7 into bit 0 and into the carry flag)'
RR = 'Rotate {} right through the carry flag'
RRC = 'Rotate {} right circular (copying bit 0 into bit 7 and into the carry flag)'
RST = 'CALL #R{}'
SBC = '{0}={0}-carry-{1}'
SBC_A = '#REGa=#REGa-carry-{}'
SET = 'Set bit {} of {}'
SLA = 'Shift {} left (copying bit 7 into the carry flag, and resetting bit 0)'
SLL = 'Shift {} left (copying bit 7 into the carry flag, and setting bit 0)'
SRA = 'Shift {} right (copying bit 0 into the carry flag, and leaving bit 7 unchanged)'
SRL = 'Shift {} right (copying bit 0 into the carry flag, and resetting bit 7)'
SUB = '#REGa=#REGa-{}'
XOR = '#REGa=#REGa^{}'

class CommentGenerator:
    def __init__(self):
        self.ctx = None
        self.reg = None

        self.ops = {
            0x00: (None, NOP, None),
            0x01: (self.word_arg, LD.format('#REGbc', WORD), None),
            0x02: (None, 'POKE #REGbc,#REGa', None),
            0x03: (None, INC.format('#REGbc'), None),
            0x07: (None, RLC.format('#REGa'), None),
            0x08: (None, "Exchange #REGaf and #REGaf'", None),
            0x09: (None, ADD.format('#REGhl', '#REGbc'), None),
            0x0A: (None, '#REGa=PEEK #REGbc', None),
            0x0B: (None, DEC.format('#REGbc'), None),
            0x0F: (None, RRC.format('#REGa'), None),
            0x10: (self.jr_arg, 'Decrement #REGb and jump to #R{} if #REGb>0', None),
            0x11: (self.word_arg, LD.format('#REGde', WORD), None),
            0x12: (None, 'POKE #REGde,#REGa', None),
            0x13: (None, INC.format('#REGde'), None),
            0x17: (None, RL.format('#REGa'), None),
            0x18: (self.jr_arg, 'Jump to #R{}', None),
            0x19: (None, ADD.format('#REGhl', '#REGde'), None),
            0x1A: (None, '#REGa=PEEK #REGde', None),
            0x1B: (None, DEC.format('#REGde'), None),
            0x1F: (None, RR.format('#REGa'), None),
            0x20: (self.jr_cc, (ZF, 0), None),
            0x21: (self.word_arg, LD.format('#REGhl', WORD), None),
            0x22: (self.addr_arg, LD_mm_rr.format(WORD, 'l', 'h'), None),
            0x23: (None, INC.format('#REGhl'), None),
            0x27: (None, 'Decimal adjust #REGa', ('#REGa', PARITY_FLAGS)),
            0x28: (self.jr_cc, (ZF, 1), None),
            0x29: (None, ADD.format('#REGhl', '#REGhl'), None),
            0x2A: (self.addr_arg, LD_rr_mm.format(WORD, 'l', 'h'), None),
            0x2B: (None, DEC.format('#REGhl'), None),
            0x2F: (None, '#REGa=#N($FF,2,,1)($)-#REGa', None),
            0x30: (self.jr_cc, (CF, 0), None),
            0x31: (self.word_arg, LD.format('#REGsp', WORD), None),
            0x32: (self.word_arg, f'POKE {WORD},#REGa', None),
            0x33: (None, INC.format('#REGsp'), None),
            0x37: (None, 'Set the carry flag', None),
            0x38: (self.jr_cc, (CF, 1), None),
            0x39: (None, ADD.format('#REGhl', '#REGsp'), None),
            0x3A: (self.word_arg, f'#REGa=PEEK {WORD}', None),
            0x3B: (None, DEC.format('#REGsp'), None),
            0x3F: (None, 'Complement the carry flag', None),
            0x76: (None, 'Wait for the next interrupt', None),
            0x97: (None, '#REGa=0', ('#REGa', OFLOW_FLAGS)),
            0x9F: (None, '#REGa=#N($FF,2,,1)($) if carry flag is set, 0 otherwise', ('#REGa', OFLOW_FLAGS)),
            0xA7: (None, 'Clear the carry flag and set the zero flag if #REGa=0', ('#REGa', PARITY_FLAGS)),
            0xAF: (None, '#REGa=0', ('#REGa', PARITY_FLAGS)),
            0xB7: (None, 'Clear the carry flag and set the zero flag if #REGa=0', ('#REGa', PARITY_FLAGS)),
            0xBF: (None, 'Clear the carry flag and set the zero flag', None),
            0xC0: (self.ret_cc, (ZF, 0), None),
            0xC1: (None, POP.format('bc'), None),
            0xC2: (self.jp_cc, (ZF, 0), None),
            0xC3: (self.word_arg, 'Jump to #R{}', None),
            0xC4: (self.call_cc, (ZF, 0), None),
            0xC5: (None, PUSH.format('bc'), None),
            0xC6: (self.byte_arg, ADD_A.format(BYTE), ('#REGa', OFLOW_FLAGS)),
            0xC8: (self.ret_cc, (ZF, 1), None),
            0xC9: (None, 'Return', None),
            0xCA: (self.jp_cc, (ZF, 1), None),
            0xCB: (self.cb_arg, None, None),
            0xCC: (self.call_cc, (ZF, 1), None),
            0xCD: (self.word_arg, 'CALL #R{}', None),
            0xCE: (self.byte_arg, ADC_A.format(BYTE), ('#REGa', OFLOW_FLAGS)),
            0xD0: (self.ret_cc, (CF, 0), None),
            0xD1: (None, POP.format('de'), None),
            0xD2: (self.jp_cc, (CF, 0), None),
            0xD3: (self.byte_arg, OUT.format(BYTE, '#REGa'), None),
            0xD4: (self.call_cc, (CF, 0), None),
            0xD5: (None, PUSH.format('de'), None),
            0xD6: (self.byte_arg, SUB.format(BYTE), ('#REGa', OFLOW_FLAGS)),
            0xD8: (self.ret_cc, (CF, 1), None),
            0xD9: (None, "Exchange #REGbc, #REGde and #REGhl with #REGbc', #REGde' and #REGhl'", None),
            0xDA: (self.jp_cc, (CF, 1), None),
            0xDB: (self.byte_arg, IN.format('#REGa', f'(#N(256,,,1)($)*#REGa+{BYTE})'), None),
            0xDC: (self.call_cc, (CF, 1), None),
            0xDD: (self.dd_arg, None, None),
            0xDE: (self.byte_arg, SBC_A.format(BYTE), ('#REGa', OFLOW_FLAGS)),
            0xE0: (self.ret_cc, (PF, 0), None),
            0xE1: (None, POP.format('hl'), None),
            0xE2: (self.jp_cc, (PF, 0), None),
            0xE3: (None, EX_SP.format('#REGhl'), None),
            0xE4: (self.call_cc, (PF, 0), None),
            0xE5: (None, PUSH.format('hl'), None),
            0xE6: (self.and_n, None, ('#REGa', PARITY_FLAGS)),
            0xE8: (self.ret_cc, (PF, 1), None),
            0xE9: (None, JP_rr.format('hl'), None),
            0xEA: (self.jp_cc, (PF, 1), None),
            0xEB: (None, 'Exchange #REGde and #REGhl', None),
            0xEC: (self.call_cc, (PF, 1), None),
            0xED: (self.ed_arg, None, None),
            0xEE: (self.xor_n, None, ('#REGa', PARITY_FLAGS)),
            0xF0: (self.ret_cc, (SF, 0), None),
            0xF1: (None, POP.format('af'), None),
            0xF2: (self.jp_cc, (SF, 0), None),
            0xF3: (None, 'Disable interrupts', None),
            0xF4: (self.call_cc, (SF, 0), None),
            0xF5: (None, PUSH.format('af'), None),
            0xF6: (self.or_n, None, ('#REGa', PARITY_FLAGS)),
            0xF8: (self.ret_cc, (SF, 1), None),
            0xF9: (None, LD.format('#REGsp', '#REGhl'), None),
            0xFA: (self.jp_cc, (SF, 1), None),
            0xFB: (None, 'Enable interrupts', None),
            0xFC: (self.call_cc, (SF, 1), None),
            0xFD: (self.fd_arg, None, None),
            0xFE: (self.byte_arg, CP.format(BYTE), (BYTE.format('{1}'), CP_FLAGS))
        }

        self.after_DD = {
            0x09: (None, ADD.format('#REGix', '#REGbc'), None),
            0x19: (None, ADD.format('#REGix', '#REGde'), None),
            0x21: (self.word_arg, LD.format('#REGix', WORD), None),
            0x22: (self.addr_arg, LD_mm_rr.format(WORD, 'ixl', 'ixh'), None),
            0x23: (None, INC.format('#REGix'), None),
            0x24: (None, INC.format('#REGixh'), ('#REGixh', OFLOW_INC_FLAGS)),
            0x25: (None, DEC.format('#REGixh'), ('#REGixh', OFLOW_DEC_FLAGS)),
            0x26: (self.byte_arg, LD.format('#REGixh', BYTE), None),
            0x29: (None, ADD.format('#REGix', '#REGix'), None),
            0x2A: (self.addr_arg, LD_rr_mm.format(WORD, 'ixl', 'ixh'), None),
            0x2B: (None, DEC.format('#REGix'), None),
            0x2C: (None, INC.format('#REGixl'), ('#REGixl', OFLOW_INC_FLAGS)),
            0x2D: (None, DEC.format('#REGixl'), ('#REGixl', OFLOW_DEC_FLAGS)),
            0x2E: (self.byte_arg, LD.format('#REGixl', BYTE), None),
            0x34: (self.index, 'POKE {ixd},(PEEK {ixd})+1', ('(PEEK {ixd})', OFLOW_INC_FLAGS)),
            0x35: (self.index, 'POKE {ixd},(PEEK {ixd})-1', ('(PEEK {ixd})', OFLOW_DEC_FLAGS)),
            0x36: (self.index_arg, 'POKE {},{}', None),
            0x39: (None, ADD.format('#REGix', '#REGsp'), None),
            0x44: (None, LD.format('#REGb', '#REGixh'), None),
            0x45: (None, LD.format('#REGb', '#REGixl'), None),
            0x46: (self.index, '#REGb=PEEK {ixd}', None),
            0x4C: (None, LD.format('#REGc', '#REGixh'), None),
            0x4D: (None, LD.format('#REGc', '#REGixl'), None),
            0x4E: (self.index, '#REGc=PEEK {ixd}', None),
            0x54: (None, LD.format('#REGd', '#REGixh'), None),
            0x55: (None, LD.format('#REGd', '#REGixl'), None),
            0x56: (self.index, '#REGd=PEEK {ixd}', None),
            0x5C: (None, LD.format('#REGe', '#REGixh'), None),
            0x5D: (None, LD.format('#REGe', '#REGixl'), None),
            0x5E: (self.index, '#REGe=PEEK {ixd}', None),
            0x60: (None, LD.format('#REGixh', '#REGb'), None),
            0x61: (None, LD.format('#REGixh', '#REGc'), None),
            0x62: (None, LD.format('#REGixh', '#REGd'), None),
            0x63: (None, LD.format('#REGixh', '#REGe'), None),
            0x64: (None, NOP, None),
            0x65: (None, LD.format('#REGixh', '#REGixl'), None),
            0x66: (self.index, '#REGh=PEEK {ixd}', None),
            0x67: (None, LD.format('#REGixh', '#REGa'), None),
            0x68: (None, LD.format('#REGixl', '#REGb'), None),
            0x69: (None, LD.format('#REGixl', '#REGc'), None),
            0x6A: (None, LD.format('#REGixl', '#REGd'), None),
            0x6B: (None, LD.format('#REGixl', '#REGe'), None),
            0x6C: (None, LD.format('#REGixl', '#REGixh'), None),
            0x6D: (None, NOP, None),
            0x6E: (self.index, '#REGl=PEEK {ixd}', None),
            0x6F: (None, LD.format('#REGixl', '#REGa'), None),
            0x7C: (None, LD.format('#REGa', '#REGixh'), None),
            0x7D: (None, LD.format('#REGa', '#REGixl'), None),
            0x7E: (self.index, '#REGa=PEEK {ixd}', None),
            0x84: (None, ADD_A.format('#REGixh'), ('#REGa', OFLOW_FLAGS)),
            0x85: (None, ADD_A.format('#REGixl'), ('#REGa', OFLOW_FLAGS)),
            0x86: (self.index, ADD_A.format('PEEK {ixd}'), ('#REGa', OFLOW_FLAGS)),
            0x8C: (None, ADC_A.format('#REGixh'), ('#REGa', OFLOW_FLAGS)),
            0x8D: (None, ADC_A.format('#REGixl'), ('#REGa', OFLOW_FLAGS)),
            0x8E: (self.index, ADC_A.format('PEEK {ixd}'), ('#REGa', OFLOW_FLAGS)),
            0x94: (None, SUB.format('#REGixh'), ('#REGa', OFLOW_FLAGS)),
            0x95: (None, SUB.format('#REGixl'), ('#REGa', OFLOW_FLAGS)),
            0x96: (self.index, SUB.format('PEEK {ixd}'), ('#REGa', OFLOW_FLAGS)),
            0x9C: (None, SBC_A.format('#REGixh'), ('#REGa', OFLOW_FLAGS)),
            0x9D: (None, SBC_A.format('#REGixl'), ('#REGa', OFLOW_FLAGS)),
            0x9E: (self.index, SBC_A.format('PEEK {ixd}'), ('#REGa', OFLOW_FLAGS)),
            0xA4: (None, AND.format('#REGixh'), ('#REGa', PARITY_FLAGS)),
            0xA5: (None, AND.format('#REGixl'), ('#REGa', PARITY_FLAGS)),
            0xA6: (self.index, AND.format('PEEK {ixd}'), ('#REGa', PARITY_FLAGS)),
            0xAC: (None, XOR.format('#REGixh'), ('#REGa', PARITY_FLAGS)),
            0xAD: (None, XOR.format('#REGixl'), ('#REGa', PARITY_FLAGS)),
            0xAE: (self.index, XOR.format('PEEK {ixd}'), ('#REGa', PARITY_FLAGS)),
            0xB4: (None, OR.format('#REGixh'), ('#REGa', PARITY_FLAGS)),
            0xB5: (None, OR.format('#REGixl'), ('#REGa', PARITY_FLAGS)),
            0xB6: (self.index, OR.format('PEEK {ixd}'), ('#REGa', PARITY_FLAGS)),
            0xBC: (None, CP.format('#REGixh'), ('#REGixh', CP_FLAGS)),
            0xBD: (None, CP.format('#REGixl'), ('#REGixl', CP_FLAGS)),
            0xBE: (self.index, CP.format('PEEK {ixd}'), ('PEEK {ixd}', CP_FLAGS)),
            0xCB: (self.ddcb_arg, None, None),
            0xE1: (None, POP.format('ix'), None),
            0xE3: (None, EX_SP.format('#REGix'), None),
            0xE5: (None, PUSH.format('ix'), None),
            0xE9: (None, JP_rr.format('ix'), None),
            0xF9: (None, LD.format('#REGsp', '#REGix'), None)
        }

        self.after_ED = {
            0x42: (None, SBC.format('#REGhl', '#REGbc'), ('#REGhl', OFLOW_FLAGS)),
            0x43: (self.addr_arg, LD_mm_rr.format(WORD, 'c', 'b'), None),
            0x47: (None, LD.format('#REGi', '#REGa'), None),
            0x4A: (None, ADC.format('#REGhl', '#REGbc'), ('#REGhl', OFLOW_FLAGS)),
            0x4B: (self.addr_arg, LD_rr_mm.format(WORD, 'c', 'b'), None),
            0x4F: (None, LD.format('#REGr', '#REGa'), None),
            0x52: (None, SBC.format('#REGhl', '#REGde'), ('#REGhl', OFLOW_FLAGS)),
            0x53: (self.addr_arg, LD_mm_rr.format(WORD, 'e', 'd'), None),
            0x57: (None, LD.format('#REGa', '#REGi'), ('#REGa', IFF2_FLAGS)),
            0x5A: (None, ADC.format('#REGhl', '#REGde'), ('#REGhl', OFLOW_FLAGS)),
            0x5B: (self.addr_arg, LD_rr_mm.format(WORD, 'e', 'd'), None),
            0x5F: (None, LD.format('#REGa', '#REGr'), ('#REGa', IFF2_FLAGS)),
            0x62: (None, '#REGhl=#N($FFFF,4,,1)($) if carry flag is set, 0 otherwise', ('#REGhl', OFLOW_FLAGS)),
            0x63: (self.addr_arg, LD_mm_rr.format(WORD, 'l', 'h'), None),
            0x67: (None, 'Rotate the low nibble of #REGa and all of (#REGhl) right 4 bits', ('#REGa', PARITY_FLAGS)),
            0x6A: (None, ADC.format('#REGhl', '#REGhl'), ('#REGhl', OFLOW_FLAGS)),
            0x6B: (self.addr_arg, LD_rr_mm.format(WORD, 'l', 'h'), None),
            0x6F: (None, 'Rotate the low nibble of #REGa and all of (#REGhl) left 4 bits', ('#REGa', PARITY_FLAGS)),
            0x70: (None, 'Read from port #REGbc and set flags accordingly', None),
            0x71: (None, OUT.format('#REGbc', 0), None),
            0x72: (None, SBC.format('#REGhl', '#REGsp'), ('#REGhl', OFLOW_FLAGS)),
            0x73: (self.addr_arg, LD_mm_rr.format(WORD, 'sp-lo', 'sp-hi'), None),
            0x7A: (None, ADC.format('#REGhl', '#REGsp'), ('#REGhl', OFLOW_FLAGS)),
            0x7B: (self.addr_arg, f'#REGsp=PEEK {WORD}+#N(256,2,,1)($)*PEEK {WORD}', None),
            0xA0: (None, 'POKE #REGde,PEEK #REGhl; #REGhl=#REGhl+1; #REGde=#REGde+1; #REGbc=#REGbc-1', ('', LDBLOCK_FLAGS)),
            0xA1: (None, 'Compare #REGa with PEEK #REGhl; #REGhl=#REGhl+1; #REGbc=#REGbc-1', ('PEEK #REGhl', CPBLOCK_FLAGS)),
            0xA2: (None, 'POKE #REGhl,IN #REGbc; #REGhl=#REGhl+1; #REGb=#REGb-1', ('#REGb', DEFAULT_FLAGS)),
            0xA3: (None, '#REGb=#REGb-1; OUT #REGbc,PEEK #REGhl; #REGhl=#REGhl+1', ('#REGb', DEFAULT_FLAGS)),
            0xA8: (None, 'POKE #REGde,PEEK #REGhl; #REGhl=#REGhl-1; #REGde=#REGde-1; #REGbc=#REGbc-1', ('', LDBLOCK_FLAGS)),
            0xA9: (None, 'Compare #REGa with PEEK #REGhl; #REGhl=#REGhl-1; #REGbc=#REGbc-1', ('PEEK #REGhl', CPBLOCK_FLAGS)),
            0xAA: (None, 'POKE #REGhl,IN #REGbc; #REGhl=#REGhl-1; #REGb=#REGb-1', ('#REGb', DEFAULT_FLAGS)),
            0xAB: (None, '#REGb=#REGb-1; OUT #REGbc,PEEK #REGhl; #REGhl=#REGhl-1', ('#REGb', DEFAULT_FLAGS)),
            0xB0: (None, 'POKE #REGde,PEEK #REGhl; #REGhl=#REGhl+1; #REGde=#REGde+1; #REGbc=#REGbc-1; repeat until #REGbc=0', None),
            0xB1: (None, 'Compare #REGa with PEEK #REGhl; #REGhl=#REGhl+1; #REGbc=#REGbc-1; repeat until #REGbc=0 or #REGa=PEEK #REGhl', None),
            0xB2: (None, 'POKE #REGhl,IN #REGbc; #REGhl=#REGhl+1; #REGb=#REGb-1; repeat until #REGb=0', None),
            0xB3: (None, '#REGb=#REGb-1; OUT #REGbc,PEEK #REGhl; #REGhl=#REGhl+1; repeat until #REGb=0', None),
            0xB8: (None, 'POKE #REGde,PEEK #REGhl; #REGhl=#REGhl-1; #REGde=#REGde-1; #REGbc=#REGbc-1; repeat until #REGbc=0', None),
            0xB9: (None, 'Compare #REGa with PEEK #REGhl; #REGhl=#REGhl-1; #REGbc=#REGbc-1; repeat until #REGbc=0 or #REGa=PEEK #REGhl', None),
            0xBA: (None, 'POKE #REGhl,IN #REGbc; #REGhl=#REGhl-1; #REGb=#REGb-1; repeat until #REGb=0', None),
            0xBB: (None, '#REGb=#REGb-1; OUT #REGbc,PEEK #REGhl; #REGhl=#REGhl-1; repeat until #REGb=0', None)
        }

        self.after_CB = {}
        self.after_DDCB = {}

        for i, r in enumerate(REGISTERS):
            if i == 6:
                self.ops[0x04 + 8 * i] = (None, 'POKE #REGhl,(PEEK #REGhl)+1', ('(PEEK #REGhl)', OFLOW_INC_FLAGS))
                self.ops[0x05 + 8 * i] = (None, 'POKE #REGhl,(PEEK #REGhl)-1', ('(PEEK #REGhl)', OFLOW_DEC_FLAGS))
                self.ops[0x06 + 8 * i] = (self.byte_arg, f'POKE #REGhl,{BYTE}', None)
                alo_r = 'PEEK #REGhl'
            else:
                self.ops[0x04 + 8 * i] = (None, INC.format(r), (r, OFLOW_INC_FLAGS))
                self.ops[0x05 + 8 * i] = (None, DEC.format(r), (r, OFLOW_DEC_FLAGS))
                self.ops[0x06 + 8 * i] = (self.byte_arg, LD.format(r, BYTE), None)
                alo_r = r
            for j, r2 in enumerate(REGISTERS):
                if i == j:
                    if i != 6:
                        self.ops[0x40 + 8 * i + j] = (None, NOP, None)
                elif i == 6:
                    self.ops[0x40 + 8 * i + j] = (None, f'POKE #REGhl,{r2}', None)
                elif j == 6:
                    self.ops[0x40 + 8 * i + j] = (None, f'{r}=PEEK #REGhl', None)
                else:
                    self.ops[0x40 + 8 * i + j] = (None, LD.format(r, r2), None)
            self.ops[0x80 + i] = (None, ADD_A.format(alo_r), ('#REGa', OFLOW_FLAGS))
            self.ops[0x88 + i] = (None, ADC_A.format(alo_r), ('#REGa', OFLOW_FLAGS))
            if i < 7:
                self.ops[0x90 + i] = (None, SUB.format(alo_r), ('#REGa', OFLOW_FLAGS))
                self.ops[0x98 + i] = (None, SBC_A.format(alo_r), ('#REGa', OFLOW_FLAGS))
                self.ops[0xA0 + i] = (None, AND.format(alo_r), ('#REGa', PARITY_FLAGS))
                self.ops[0xA8 + i] = (None, XOR.format(alo_r), ('#REGa', PARITY_FLAGS))
                self.ops[0xB0 + i] = (None, OR.format(alo_r), ('#REGa', PARITY_FLAGS))
                if i == 6:
                    self.ops[0xB8 + i] = (None, CP.format(alo_r), ('PEEK #REGhl', CP_FLAGS))
                else:
                    self.ops[0xB8 + i] = (None, CP.format(alo_r), (r, CP_FLAGS))
            self.ops[0xC7 + 8 * i] = (None, RST.format(8 * i), None)
            if i != 6:
                self.after_DD[0x70 + i] = (self.index, f'POKE {{ixd}},{r}', None)
                self.after_ED[0x40 + 8 * i] = (None, IN.format(r, '#REGbc'), (r, PARITY_FLAGS))
                self.after_ED[0x41 + 8 * i] = (None, OUT.format('#REGbc', r), None)
            self.after_ED[0x44 + 8 * i] = (None, NEG, ('#REGa', NEGATE_FLAGS))
            self.after_ED[0x45 + 8 * i] = (None, (RETN, RETI)[i == 1], None)
            self.after_ED[0x46 + 8 * i] = (None, IM.format((0, 0, 1, 2)[i % 4]), None)
            for b, comment in enumerate((RLC, RRC, RL, RR, SLA, SRA, SLL, SRL)):
                self.after_CB[0x40 + 8 * b + i] = (BIT.format(b, r), None)
                self.after_CB[0x80 + 8 * b + i] = (RES.format(b, r), None)
                self.after_CB[0xC0 + 8 * b + i] = (SET.format(b, r), None)
                self.after_DDCB[0x40 + 8 * b + i] = (self.index, BIT.format(b, '{ixd}'), None)
                if i == 6:
                    self.after_CB[0x00 + 8 * b + i] = (comment.format(r), ('(PEEK #REGhl)', PARITY_FLAGS))
                    self.after_DDCB[0x00 + 8 * b + i] = (self.index, comment.format('{ixd}'), ('(PEEK {ixd})', PARITY_FLAGS))
                    self.after_DDCB[0x80 + 8 * b + i] = (self.index, RES.format(b, '{ixd}'), None)
                    self.after_DDCB[0xC0 + 8 * b + i] = (self.index, SET.format(b, '{ixd}'), None)
                else:
                    self.after_CB[0x00 + 8 * b + i] = (comment.format(r), (r, PARITY_FLAGS))
                    self.after_DDCB[0x00 + 8 * b + i] = (self.index, comment.format('{ixd}') + f' and copy the result to {r}', (r, PARITY_FLAGS))
                    self.after_DDCB[0x80 + 8 * b + i] = (self.index, RES.format(b, '{ixd}') + f' and copy the result to {r}', None)
                    self.after_DDCB[0xC0 + 8 * b + i] = (self.index, SET.format(b, '{ixd}') + f' and copy the result to {r}', None)

    # Component API
    def get_comment(self, address, values):
        """Generate an instruction comment.

        :param address: The address of the instruction.
        :param values: The instruction's byte values.
        :return: A comment for the instruction.
        """
        decoder, template, fctx = self.ops[values[0]]
        if decoder is None:
            rv = template
        elif template is None:
            rv = decoder(address, values)
        elif isinstance(template, str):
            rv = decoder(template, address, values)
        else:
            rv = decoder(*template, address, values)
        if isinstance(rv, str):
            comment = rv
        else:
            comment, fctx = rv
        if fctx:
            self.reg, self.ctx = fctx[0].format(*values), fctx[1]
        else:
            self.reg, self.ctx = None, None
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
            return f'#REGa={BYTE}'.format(0)
        if len(bits) == 1:
            return f'Keep only bit {bits[0]} of #REGa'
        if len(bits) < 5:
            bits_str = ', '.join(str(b) for b in bits[:-1]) + f' and {bits[-1]}'
            return f'Keep only bits {bits_str} of #REGa'
        nbits = [b for b in range(8) if b not in bits]
        if len(nbits) == 0:
            return 'Set the zero flag if #REGa=0, and reset the carry flag'
        if len(nbits) == 1:
            return f'Reset bit {nbits[0]} of #REGa'
        nbits_str = ', '.join(str(b) for b in nbits[:-1]) + f' and {nbits[-1]}'
        return f'Reset bits {nbits_str} of #REGa'

    def or_n(self, address, values):
        bits = BITS[values[1]]
        if len(bits) == 0:
            return 'Set the zero flag if #REGa=0, and reset the carry flag'
        if len(bits) == 1:
            return f'Set bit {bits[0]} of #REGa'
        if len(bits) < 8:
            bits_str = ', '.join(str(b) for b in bits[:-1]) + f' and {bits[-1]}'
            return f'Set bits {bits_str} of #REGa'
        return f'#REGa={BYTE}'.format(255)

    def xor_n(self, address, values):
        bits = BITS[values[1]]
        if len(bits) == 0:
            return 'Set the zero flag if #REGa=0, and reset the carry flag'
        if len(bits) == 1:
            return f'Flip bit {bits[0]} of #REGa'
        if len(bits) < 8:
            bits_str = ', '.join(str(b) for b in bits[:-1]) + f' and {bits[-1]}'
            return f'Flip bits {bits_str} of #REGa'
        return 'Flip every bit of #REGa'

    def addr_arg(self, template, address, values):
        if values[0] in PREFIXES:
            addr = values[2] + 256 * values[3]
        else:
            addr = values[1] + 256 * values[2]
        return template.format(addr, (addr + 1) % 65536)

    def jr_arg(self, template, address, values):
        if values[1] < 128:
            addr = address + 2 + values[1]
        else:
            addr = address + values[1] - 254
        return template.format(addr % 65536)

    def index(self, template, address, values):
        return template.format(ixd=self.index_offset(address, values))

    def index_arg(self, template, address, values):
        return template.format(self.index_offset(address, values), values[3])

    def index_offset(self, address, values):
        if values[2] < 128:
            return f'(#REGix+#N({values[2]},2,,1)($))'
        return f'(#REGix-#N({256 - values[2]},2,,1)($))'

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
            addr = address + 2 + values[1]
        else:
            addr = address + values[1] - 254
        if self.ctx:
            cond = FLAGS[flag][value][self.ctx[flag]].format(self.reg)
            return f'Jump to #R{addr % 65536} if {cond}'
        return f'Jump to #R{addr % 65536} if {FLAGS[flag][value][NA]}'

    def ret_cc(self, flag, value, address, values):
        if self.ctx:
            cond = FLAGS[flag][value][self.ctx[flag]].format(self.reg)
            return f'Return if {cond}'
        return f'Return if {FLAGS[flag][value][NA]}'
