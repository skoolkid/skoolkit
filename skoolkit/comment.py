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

ADD = '{}+={}'
ADD_A = '#REGa+={}'
ADC = '{}+=carry+{}'
ADC_A = '#REGa+=carry+{}'
AND = '#REGa&={}'
BIT = 'Set the zero flag if bit {} of {} is 0'
CALL_cc = 'CALL #R{{}} if the {}'
CP = 'Set the zero flag if #REGa={0}, or the carry flag if #REGa<{0}'
DEC = '{}-=1'
EX_SP = 'Exchange the last item on the stack with {}'
IM = 'Set interrupt mode {}'
IN_C = 'Read from port #REGbc into {}'
INC = '{}+=1'
JP_cc = 'Jump to #R{{}} if the {}'
JP_rr = 'Jump to #REG{}'
JR_cc = 'Jump to #R{{}} if the {}'
LD = '{}={}'
LD_mm_rr = 'POKE {0},#REG{1}; POKE {0},#REG{2}'
LD_rr_mm = '#REG{1}=PEEK {0}; #REG{2}=PEEK {0}'
NEG = '#REGa=#N(256,2,,1)($)-#REGa'
NOP = 'Do nothing'
OR = '#REGa|={}'
OUT_C = 'Output {} to port #REGbc'
POP = 'Pop last item from stack into #REG{}'
PUSH = 'Push #REG{} onto the stack'
RES = 'Reset bit {} of {}'
RET_cc = 'Return if the {}'
RETI = 'Return from maskable interrupt'
RETN = 'Return from non-maskable interrupt'
RL = 'Rotate {} left through the carry flag'
RLC = 'Rotate {} left circular (copying bit 7 into bit 0 and into the carry flag)'
RR = 'Rotate {} right through the carry flag'
RRC = 'Rotate {} right circular (copying bit 0 into bit 7 and into the carry flag)'
RST = 'CALL #R{}'
SBC = '{}-=carry+{}'
SBC_A = '#REGa-=carry+{}'
SET = 'Set bit {} of {}'
SLA = 'Shift {} left (copying bit 7 into the carry flag, and resetting bit 0)'
SLL = 'Shift {} left (copying bit 7 into the carry flag, and setting bit 0)'
SRA = 'Shift {} right (copying bit 0 into the carry flag, and leaving bit 7 unchanged)'
SRL = 'Shift {} right (copying bit 0 into the carry flag, and resetting bit 7)'
SUB = '#REGa-={}'
XOR = '#REGa^={}'

class CommentGenerator:
    def __init__(self):
        self.ops = {
            0x00: (None, NOP),
            0x01: (self.word_arg, LD.format('#REGbc', WORD)),
            0x02: (None, 'POKE #REGbc,#REGa'),
            0x03: (None, INC.format('#REGbc')),
            0x07: (None, RLC.format('#REGa')),
            0x08: (None, "Exchange #REGaf and #REGaf'"),
            0x09: (None, ADD.format('#REGhl', '#REGbc')),
            0x0A: (None, '#REGa=PEEK #REGbc'),
            0x0B: (None, DEC.format('#REGbc')),
            0x0F: (None, RRC.format('#REGa')),
            0x10: (self.jr_arg, 'Decrement #REGb and jump to #R{} if #REGb>0'),
            0x11: (self.word_arg, LD.format('#REGde', WORD)),
            0x12: (None, 'POKE #REGde,#REGa'),
            0x13: (None, INC.format('#REGde')),
            0x17: (None, RL.format('#REGa')),
            0x18: (self.jr_arg, 'Jump to #R{}'),
            0x19: (None, ADD.format('#REGhl', '#REGde')),
            0x1A: (None, '#REGa=PEEK #REGde'),
            0x1B: (None, DEC.format('#REGde')),
            0x1F: (None, RR.format('#REGa')),
            0x20: (self.jr_arg, JR_cc.format('zero flag is not set')),
            0x21: (self.word_arg, LD.format('#REGhl', WORD)),
            0x22: (self.addr_arg, LD_mm_rr.format(WORD, 'l', 'h')),
            0x23: (None, INC.format('#REGhl')),
            0x27: (None, 'Decimal adjust #REGa'),
            0x28: (self.jr_arg, JR_cc.format('zero flag is set')),
            0x29: (None, ADD.format('#REGhl', '#REGhl')),
            0x2A: (self.addr_arg, LD_rr_mm.format(WORD, 'l', 'h')),
            0x2B: (None, DEC.format('#REGhl')),
            0x2F: (None, '#REGa=#N($FF,2,,1)($)-#REGa'),
            0x30: (self.jr_arg, JR_cc.format('carry flag is not set')),
            0x31: (self.word_arg, LD.format('#REGsp', WORD)),
            0x32: (self.word_arg, f'POKE {WORD},#REGa'),
            0x33: (None, INC.format('#REGsp')),
            0x37: (None, 'Set the carry flag'),
            0x38: (self.jr_arg, JR_cc.format('carry flag is set')),
            0x39: (None, ADD.format('#REGhl', '#REGsp')),
            0x3A: (self.word_arg, f'#REGa=PEEK {WORD}'),
            0x3B: (None, DEC.format('#REGsp')),
            0x3F: (None, 'Complement the carry flag'),
            0x76: (None, 'Wait for the next interrupt'),
            0x97: (None, '#REGa=0'),
            0x9F: (None, '#REGa=#N($FF,2,,1)($) if carry flag is set, 0 otherwise'),
            0xA7: (None, 'Clear the carry flag and set the zero flag if #REGa=0'),
            0xAF: (None, '#REGa=0'),
            0xB7: (None, 'Clear the carry flag and set the zero flag if #REGa=0'),
            0xBF: (None, 'Clear the carry flag and set the zero flag'),
            0xC0: (None, RET_cc.format('zero flag is not set')),
            0xC1: (None, POP.format('bc')),
            0xC2: (self.word_arg, JP_cc.format('zero flag is not set')),
            0xC3: (self.word_arg, 'Jump to #R{}'),
            0xC4: (self.word_arg, CALL_cc.format('zero flag is not set')),
            0xC5: (None, PUSH.format('bc')),
            0xC6: (self.byte_arg, ADD_A.format(BYTE)),
            0xC8: (None, RET_cc.format('zero flag is set')),
            0xC9: (None, 'Return'),
            0xCA: (self.word_arg, JP_cc.format('zero flag is set')),
            0xCB: (self.cb_arg, None),
            0xCC: (self.word_arg, CALL_cc.format('zero flag is set')),
            0xCD: (self.word_arg, 'CALL #R{}'),
            0xCE: (self.byte_arg, ADC_A.format(BYTE)),
            0xD0: (None, RET_cc.format('carry flag is not set')),
            0xD1: (None, POP.format('de')),
            0xD2: (self.word_arg, JP_cc.format('carry flag is not set')),
            0xD3: (self.byte_arg, f'Output #REGa to port {BYTE}'),
            0xD4: (self.word_arg, CALL_cc.format('carry flag is not set')),
            0xD5: (None, PUSH.format('de')),
            0xD6: (self.byte_arg, SUB.format(BYTE)),
            0xD8: (None, RET_cc.format('carry flag is set')),
            0xD9: (None, "Exchange #REGbc, #REGde and #REGhl with #REGbc', #REGde' and #REGhl'"),
            0xDA: (self.word_arg, JP_cc.format('carry flag is set')),
            0xDB: (self.byte_arg, f'Read from port {BYTE} into #REGa'),
            0xDC: (self.word_arg, CALL_cc.format('carry flag is set')),
            0xDD: (self.dd_arg, None),
            0xDE: (self.byte_arg, SBC_A.format(BYTE)),
            0xE0: (None, RET_cc.format('parity/overflow flag is not set (parity odd)')),
            0xE1: (None, POP.format('hl')),
            0xE2: (self.word_arg, JP_cc.format('parity/overflow flag is not set (parity odd)')),
            0xE3: (None, EX_SP.format('#REGhl')),
            0xE4: (self.word_arg, CALL_cc.format('parity/overflow flag is not set (parity odd)')),
            0xE5: (None, PUSH.format('hl')),
            0xE6: (self.and_n, None),
            0xE8: (None, RET_cc.format('parity/overflow flag is set (parity even)')),
            0xE9: (None, JP_rr.format('hl')),
            0xEA: (self.word_arg, JP_cc.format('parity/overflow flag is set (parity even)')),
            0xEB: (None, 'Exchange #REGde and #REGhl'),
            0xEC: (self.word_arg, CALL_cc.format('parity/overflow flag is set (parity even)')),
            0xED: (self.ed_arg, None),
            0xEE: (self.xor_n, None),
            0xF0: (None, RET_cc.format('sign flag is not set (positive)')),
            0xF1: (None, POP.format('af')),
            0xF2: (self.word_arg, JP_cc.format('sign flag is not set (positive)')),
            0xF3: (None, 'Disable interrupts'),
            0xF4: (self.word_arg, CALL_cc.format('sign flag is not set (positive)')),
            0xF5: (None, PUSH.format('af')),
            0xF6: (self.or_n, None),
            0xF8: (None, RET_cc.format('sign flag is set (negative)')),
            0xF9: (None, LD.format('#REGsp', '#REGhl')),
            0xFA: (self.word_arg, JP_cc.format('sign flag is set (negative)')),
            0xFB: (None, 'Enable interrupts'),
            0xFC: (self.word_arg, CALL_cc.format('sign flag is set (negative)')),
            0xFD: (self.fd_arg, None),
            0xFE: (self.byte_arg, CP.format(BYTE))
        }

        self.after_DD = {
            0x09: (None, ADD.format('#REGix', '#REGbc')),
            0x19: (None, ADD.format('#REGix', '#REGde')),
            0x21: (self.word_arg, LD.format('#REGix', WORD)),
            0x22: (self.addr_arg, LD_mm_rr.format(WORD, 'ixl', 'ixh')),
            0x23: (None, INC.format('#REGix')),
            0x24: (None, INC.format('#REGixh')),
            0x25: (None, DEC.format('#REGixh')),
            0x26: (self.byte_arg, LD.format('#REGixh', BYTE)),
            0x29: (None, ADD.format('#REGix', '#REGix')),
            0x2A: (self.addr_arg, LD_rr_mm.format(WORD, 'ixl', 'ixh')),
            0x2B: (None, DEC.format('#REGix')),
            0x2C: (None, INC.format('#REGixl')),
            0x2D: (None, DEC.format('#REGixl')),
            0x2E: (self.byte_arg, LD.format('#REGixl', BYTE)),
            0x34: (self.index, 'POKE {ixd},(PEEK {ixd})+1'),
            0x35: (self.index, 'POKE {ixd},(PEEK {ixd})-1'),
            0x36: (self.index_arg, 'POKE {},{}'),
            0x39: (None, ADD.format('#REGix', '#REGsp')),
            0x44: (None, LD.format('#REGb', '#REGixh')),
            0x45: (None, LD.format('#REGb', '#REGixl')),
            0x46: (self.index, '#REGb=PEEK {ixd}'),
            0x4C: (None, LD.format('#REGc', '#REGixh')),
            0x4D: (None, LD.format('#REGc', '#REGixl')),
            0x4E: (self.index, '#REGc=PEEK {ixd}'),
            0x54: (None, LD.format('#REGd', '#REGixh')),
            0x55: (None, LD.format('#REGd', '#REGixl')),
            0x56: (self.index, '#REGd=PEEK {ixd}'),
            0x5C: (None, LD.format('#REGe', '#REGixh')),
            0x5D: (None, LD.format('#REGe', '#REGixl')),
            0x5E: (self.index, '#REGe=PEEK {ixd}'),
            0x60: (None, LD.format('#REGixh', '#REGb')),
            0x61: (None, LD.format('#REGixh', '#REGc')),
            0x62: (None, LD.format('#REGixh', '#REGd')),
            0x63: (None, LD.format('#REGixh', '#REGe')),
            0x64: (None, NOP),
            0x65: (None, LD.format('#REGixh', '#REGixl')),
            0x66: (self.index, '#REGh=PEEK {ixd}'),
            0x67: (None, LD.format('#REGixh', '#REGa')),
            0x68: (None, LD.format('#REGixl', '#REGb')),
            0x69: (None, LD.format('#REGixl', '#REGc')),
            0x6A: (None, LD.format('#REGixl', '#REGd')),
            0x6B: (None, LD.format('#REGixl', '#REGe')),
            0x6C: (None, LD.format('#REGixl', '#REGixh')),
            0x6D: (None, NOP),
            0x6E: (self.index, '#REGl=PEEK {ixd}'),
            0x6F: (None, LD.format('#REGixl', '#REGa')),
            0x7C: (None, LD.format('#REGa', '#REGixh')),
            0x7D: (None, LD.format('#REGa', '#REGixl')),
            0x7E: (self.index, '#REGa=PEEK {ixd}'),
            0x84: (None, ADD_A.format('#REGixh')),
            0x85: (None, ADD_A.format('#REGixl')),
            0x86: (self.index, ADD_A.format('PEEK {ixd}')),
            0x8C: (None, ADC_A.format('#REGixh')),
            0x8D: (None, ADC_A.format('#REGixl')),
            0x8E: (self.index, ADC_A.format('PEEK {ixd}')),
            0x94: (None, SUB.format('#REGixh')),
            0x95: (None, SUB.format('#REGixl')),
            0x96: (self.index, SUB.format('PEEK {ixd}')),
            0x9C: (None, SBC_A.format('#REGixh')),
            0x9D: (None, SBC_A.format('#REGixl')),
            0x9E: (self.index, SBC_A.format('PEEK {ixd}')),
            0xA4: (None, AND.format('#REGixh')),
            0xA5: (None, AND.format('#REGixl')),
            0xA6: (self.index, AND.format('PEEK {ixd}')),
            0xAC: (None, XOR.format('#REGixh')),
            0xAD: (None, XOR.format('#REGixl')),
            0xAE: (self.index, XOR.format('PEEK {ixd}')),
            0xB4: (None, OR.format('#REGixh')),
            0xB5: (None, OR.format('#REGixl')),
            0xB6: (self.index, OR.format('PEEK {ixd}')),
            0xBC: (None, CP.format('#REGixh')),
            0xBD: (None, CP.format('#REGixl')),
            0xBE: (self.index, CP.format('PEEK {ixd}')),
            0xCB: (self.ddcb_arg, None),
            0xE1: (None, POP.format('ix')),
            0xE3: (None, EX_SP.format('#REGix')),
            0xE5: (None, PUSH.format('ix')),
            0xE9: (None, JP_rr.format('ix')),
            0xF9: (None, LD.format('#REGsp', '#REGix'))
        }

        self.after_ED = {
            0x42: (None, SBC.format('#REGhl', '#REGbc')),
            0x43: (self.addr_arg, LD_mm_rr.format(WORD, 'c', 'b')),
            0x47: (None, LD.format('#REGi', '#REGa')),
            0x4A: (None, ADC.format('#REGhl', '#REGbc')),
            0x4B: (self.addr_arg, LD_rr_mm.format(WORD, 'c', 'b')),
            0x4F: (None, LD.format('#REGr', '#REGa')),
            0x52: (None, SBC.format('#REGhl', '#REGde')),
            0x53: (self.addr_arg, LD_mm_rr.format(WORD, 'e', 'd')),
            0x57: (None, LD.format('#REGa', '#REGi')),
            0x5A: (None, ADC.format('#REGhl', '#REGde')),
            0x5B: (self.addr_arg, LD_rr_mm.format(WORD, 'e', 'd')),
            0x5F: (None, LD.format('#REGa', '#REGr')),
            0x62: (None, '#REGhl=#N($FFFF,4,,1)($) if carry flag is set, 0 otherwise'),
            0x63: (self.addr_arg, LD_mm_rr.format(WORD, 'l', 'h')),
            0x67: (None, 'Rotate the low nibble of #REGa and all of (#REGhl) right 4 bits'),
            0x6A: (None, ADC.format('#REGhl', '#REGhl')),
            0x6B: (self.addr_arg, LD_rr_mm.format(WORD, 'l', 'h')),
            0x6F: (None, 'Rotate the low nibble of #REGa and all of (#REGhl) left 4 bits'),
            0x70: (None, 'Read from port #REGbc and set flags accordingly'),
            0x71: (None, OUT_C.format(0)),
            0x72: (None, SBC.format('#REGhl', '#REGsp')),
            0x73: (self.addr_arg, LD_mm_rr.format(WORD, 'sp-lo', 'sp-hi')),
            0x7A: (None, ADC.format('#REGhl', '#REGsp')),
            0x7B: (self.addr_arg, f'#REGsp=PEEK {WORD}+#N(256,2,,1)($)*PEEK {WORD}'),
            0xA0: (None, 'POKE #REGde,PEEK #REGhl; #REGhl+=1; #REGde+=1; #REGbc-=1'),
            0xA1: (None, 'Compare #REGa with PEEK #REGhl; #REGhl+=1; #REGbc-=1'),
            0xA2: (None, 'POKE #REGhl,IN #REGbc; #REGhl+=1; #REGb-=1'),
            0xA3: (None, '#REGb-=1; OUT #REGbc,PEEK #REGhl; #REGhl+=1'),
            0xA8: (None, 'POKE #REGde,PEEK #REGhl; #REGhl-=1; #REGde-=1; #REGbc-=1'),
            0xA9: (None, 'Compare #REGa with PEEK #REGhl; #REGhl-=1; #REGbc-=1'),
            0xAA: (None, 'POKE #REGhl,IN #REGbc; #REGhl-=1; #REGb-=1'),
            0xAB: (None, '#REGb-=1; OUT #REGbc,PEEK #REGhl; #REGhl-=1'),
            0xB0: (None, 'POKE #REGde,PEEK #REGhl; #REGhl+=1; #REGde+=1; #REGbc-=1; repeat until #REGbc=0'),
            0xB1: (None, 'Compare #REGa with PEEK #REGhl; #REGhl+=1; #REGbc-=1; repeat until #REGbc=0 or #REGa=PEEK #REGhl'),
            0xB2: (None, 'POKE #REGhl,IN #REGbc; #REGhl+=1; #REGb-=1; repeat until #REGb=0'),
            0xB3: (None, '#REGb-=1; OUT #REGbc,PEEK #REGhl; #REGhl+=1; repeat until #REGb=0'),
            0xB8: (None, 'POKE #REGde,PEEK #REGhl; #REGhl-=1; #REGde-=1; #REGbc-=1; repeat until #REGbc=0'),
            0xB9: (None, 'Compare #REGa with PEEK #REGhl; #REGhl-=1; #REGbc-=1; repeat until #REGbc=0 or #REGa=PEEK #REGhl'),
            0xBA: (None, 'POKE #REGhl,IN #REGbc; #REGhl-=1; #REGb-=1; repeat until #REGb=0'),
            0xBB: (None, '#REGb-=1; OUT #REGbc,PEEK #REGhl; #REGhl-=1; repeat until #REGb=0')
        }

        self.after_CB = {}
        self.after_DDCB = {}

        for i, r in enumerate(REGISTERS):
            if i == 6:
                self.ops[0x04 + 8 * i] = (None, 'POKE #REGhl,(PEEK #REGhl)+1')
                self.ops[0x05 + 8 * i] = (None, 'POKE #REGhl,(PEEK #REGhl)-1')
                self.ops[0x06 + 8 * i] = (self.byte_arg, f'POKE #REGhl,{BYTE}')
                alo_r = 'PEEK #REGhl'
            else:
                self.ops[0x04 + 8 * i] = (None, INC.format(r))
                self.ops[0x05 + 8 * i] = (None, DEC.format(r))
                self.ops[0x06 + 8 * i] = (self.byte_arg, LD.format(r, BYTE))
                alo_r = r
            for j, r2 in enumerate(REGISTERS):
                if i == j:
                    if i != 6:
                        self.ops[0x40 + 8 * i + j] = (None, NOP)
                elif i == 6:
                    self.ops[0x40 + 8 * i + j] = (None, f'POKE #REGhl,{r2}')
                elif j == 6:
                    self.ops[0x40 + 8 * i + j] = (None, f'{r}=PEEK #REGhl')
                else:
                    self.ops[0x40 + 8 * i + j] = (None, LD.format(r, r2))
            self.ops[0x80 + i] = (None, ADD_A.format(alo_r))
            self.ops[0x88 + i] = (None, ADC_A.format(alo_r))
            if i < 7:
                self.ops[0x90 + i] = (None, SUB.format(alo_r))
                self.ops[0x98 + i] = (None, SBC_A.format(alo_r))
                self.ops[0xA0 + i] = (None, AND.format(alo_r))
                self.ops[0xA8 + i] = (None, XOR.format(alo_r))
                self.ops[0xB0 + i] = (None, OR.format(alo_r))
                self.ops[0xB8 + i] = (None, CP.format(alo_r))
            self.ops[0xC7 + 8 * i] = (None, RST.format(8 * i))
            if i != 6:
                self.after_DD[0x70 + i] = (self.index, f'POKE {{ixd}},{r}')
                self.after_ED[0x40 + 8 * i] = (None, IN_C.format(r))
                self.after_ED[0x41 + 8 * i] = (None, OUT_C.format(r))
            self.after_ED[0x44 + 8 * i] = (None, NEG)
            self.after_ED[0x45 + 8 * i] = (None, (RETN, RETI)[i == 1])
            self.after_ED[0x46 + 8 * i] = (None, IM.format((0, 0, 1, 2)[i % 4]))
            for b, comment in enumerate((RLC, RRC, RL, RR, SLA, SRA, SLL, SRL)):
                self.after_CB[0x00 + 8 * b + i] = comment.format(r)
                self.after_CB[0x40 + 8 * b + i] = BIT.format(b, r)
                self.after_CB[0x80 + 8 * b + i] = RES.format(b, r)
                self.after_CB[0xC0 + 8 * b + i] = SET.format(b, r)
                self.after_DDCB[0x40 + 8 * b + i] = (self.index, BIT.format(b, '{ixd}'))
                if i == 6:
                    self.after_DDCB[0x00 + 8 * b + i] = (self.index, comment.format('{ixd}'))
                    self.after_DDCB[0x80 + 8 * b + i] = (self.index, RES.format(b, '{ixd}'))
                    self.after_DDCB[0xC0 + 8 * b + i] = (self.index, SET.format(b, '{ixd}'))
                else:
                    self.after_DDCB[0x00 + 8 * b + i] = (self.index, comment.format('{ixd}') + f' and copy the result to {r}')
                    self.after_DDCB[0x80 + 8 * b + i] = (self.index, RES.format(b, '{ixd}') + f' and copy the result to {r}')
                    self.after_DDCB[0xC0 + 8 * b + i] = (self.index, SET.format(b, '{ixd}') + f' and copy the result to {r}')

    # Component API
    def get_comment(self, address, values):
        """Generate an instruction comment.

        :param address: The address of the instruction.
        :param values: The instruction's byte values.
        :return: A comment for the instruction.
        """
        decoder, template = self.ops[values[0]]
        if decoder is None:
            return template
        if template is None:
            return decoder(address, values)
        return decoder(template, address, values)

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
        decoder, template = self.after_ED.get(values[1], (None, ''))
        if decoder:
            return decoder(template, address, values)
        return template

    def dd_arg(self, address, values):
        decoder, template = self.after_DD.get(values[1], (None, ''))
        if decoder:
            return decoder(template, address, values)
        return template

    def fd_arg(self, address, values):
        return self.dd_arg(address, values).replace('ix', 'iy')

    def ddcb_arg(self, template, address, values):
        decoder, template = self.after_DDCB.get(values[3], (None, None))
        return decoder(template, address, values)
