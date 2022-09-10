# Copyright 2015, 2017-2019, 2021, 2022 Richard Dymond (rjdymond@gmail.com)
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

import re
from functools import partial

from skoolkit import get_int_param
from skoolkit.components import get_operand_evaluator
from skoolkit.textutils import split_unquoted, split_quoted

REG = ('B', 'C', 'D', 'E', 'H', 'L', '(HL)', 'A')
REG_PAIRS = ('BC', 'DE', 'HL', 'SP')
INDEX_REG = ('IXH', 'IXL', 'IYH', 'IYL')
INDEX_REG_PAIRS = ('IX', 'IY')
OPERAND_AE_CHARS = frozenset('+-*/%0123456789()')

TIMINGS = {
    0x00: 4,        # NOP
    0x01: 10,       # LD BC,nn
    0x02: 7,        # LD (BC),A
    0x03: 6,        # INC BC
    0x04: 4,        # INC B
    0x05: 4,        # DEC B
    0x06: 7,        # LD B,n
    0x07: 4,        # RLCA
    0x08: 4,        # EX AF,AF'
    0x09: 11,       # ADD HL,BC
    0x0A: 7,        # LD A,(BC)
    0x0B: 6,        # DEC BC
    0x0C: 4,        # INC C
    0x0D: 4,        # DEC C
    0x0E: 7,        # LD C,n
    0x0F: 4,        # RRCA
    0x10: (13, 8),  # DJNZ nn
    0x11: 10,       # LD DE,nn
    0x12: 7,        # LD (DE),A
    0x13: 6,        # INC DE
    0x14: 4,        # INC D
    0x15: 4,        # DEC D
    0x16: 7,        # LD D,n
    0x17: 4,        # RLA
    0x18: 12,       # JR nn
    0x19: 11,       # ADD HL,DE
    0x1A: 7,        # LD A,(DE)
    0x1B: 6,        # DEC DE
    0x1C: 4,        # INC E
    0x1D: 4,        # DEC E
    0x1E: 7,        # LD E,n
    0x1F: 4,        # RRA
    0x20: (12, 7),  # JR NZ,nn
    0x21: 10,       # LD HL,nn
    0x22: 16,       # LD (nn),HL
    0x23: 6,        # INC HL
    0x24: 4,        # INC H
    0x25: 4,        # DEC H
    0x26: 7,        # LD H,n
    0x27: 4,        # DAA
    0x28: (12, 7),  # JR Z,nn
    0x29: 11,       # ADD HL,HL
    0x2A: 16,       # LD HL,(nn)
    0x2B: 6,        # DEC HL
    0x2C: 4,        # INC L
    0x2D: 4,        # DEC L
    0x2E: 7,        # LD L,n
    0x2F: 4,        # CPL
    0x30: (12, 7),  # JR NC,nn
    0x31: 10,       # LD SP,nn
    0x32: 13,       # LD (nn),A
    0x33: 6,        # INC SP
    0x34: 11,       # INC (HL)
    0x35: 11,       # DEC (HL)
    0x36: 10,       # LD (HL),r
    0x37: 4,        # SCF
    0x38: (12, 7),  # JR C,nn
    0x39: 11,       # ADD HL,SP
    0x3A: 13,       # LD A,(nn)
    0x3B: 6,        # DEC SP
    0x3C: 4,        # INC A
    0x3D: 4,        # DEC A
    0x3E: 7,        # LD A,n
    0x3F: 4,        # CCF
    0x40: 4,        # LD B,B
    0x41: 4,        # LD B,C
    0x42: 4,        # LD B,D
    0x43: 4,        # LD B,E
    0x44: 4,        # LD B,H
    0x45: 4,        # LD B,L
    0x46: 7,        # LD B,(HL)
    0x47: 4,        # LD B,A
    0x48: 4,        # LD C,B
    0x49: 4,        # LD C,C
    0x4A: 4,        # LD C,D
    0x4B: 4,        # LD C,E
    0x4C: 4,        # LD C,H
    0x4D: 4,        # LD C,L
    0x4E: 7,        # LD C,(HL)
    0x4F: 4,        # LD C,A
    0x50: 4,        # LD D,B
    0x51: 4,        # LD D,C
    0x52: 4,        # LD D,D
    0x53: 4,        # LD D,E
    0x54: 4,        # LD D,H
    0x55: 4,        # LD D,L
    0x56: 7,        # LD D,(HL)
    0x57: 4,        # LD D,A
    0x58: 4,        # LD E,B
    0x59: 4,        # LD E,C
    0x5A: 4,        # LD E,D
    0x5B: 4,        # LD E,E
    0x5C: 4,        # LD E,H
    0x5D: 4,        # LD E,L
    0x5E: 7,        # LD E,(HL)
    0x5F: 4,        # LD E,A
    0x60: 4,        # LD H,B
    0x61: 4,        # LD H,C
    0x62: 4,        # LD H,D
    0x63: 4,        # LD H,E
    0x64: 4,        # LD H,H
    0x65: 4,        # LD H,L
    0x66: 7,        # LD H,(HL)
    0x67: 4,        # LD H,A
    0x68: 4,        # LD L,B
    0x69: 4,        # LD L,C
    0x6A: 4,        # LD L,D
    0x6B: 4,        # LD L,E
    0x6C: 4,        # LD L,H
    0x6D: 4,        # LD L,L
    0x6E: 7,        # LD L,(HL)
    0x6F: 4,        # LD L,A
    0x70: 7,        # LD (HL),B
    0x71: 7,        # LD (HL),C
    0x72: 7,        # LD (HL),D
    0x73: 7,        # LD (HL),E
    0x74: 7,        # LD (HL),H
    0x75: 7,        # LD (HL),L
    0x76: 4,        # HALT
    0x77: 7,        # LD (HL),A
    0x78: 4,        # LD A,B
    0x79: 4,        # LD A,C
    0x7A: 4,        # LD A,D
    0x7B: 4,        # LD A,E
    0x7C: 4,        # LD A,H
    0x7D: 4,        # LD A,L
    0x7E: 7,        # LD A,(HL)
    0x7F: 4,        # LD A,A
    0x80: 4,        # ADD A,B
    0x81: 4,        # ADD A,C
    0x82: 4,        # ADD A,D
    0x83: 4,        # ADD A,E
    0x84: 4,        # ADD A,H
    0x85: 4,        # ADD A,L
    0x86: 7,        # ADD A,(HL)
    0x87: 4,        # ADD A,A
    0x88: 4,        # ADC A,B
    0x89: 4,        # ADC A,C
    0x8A: 4,        # ADC A,D
    0x8B: 4,        # ADC A,E
    0x8C: 4,        # ADC A,H
    0x8D: 4,        # ADC A,L
    0x8E: 7,        # ADC A,(HL)
    0x8F: 4,        # ADC A,A
    0x90: 4,        # SUB B
    0x91: 4,        # SUB C
    0x92: 4,        # SUB D
    0x93: 4,        # SUB E
    0x94: 4,        # SUB H
    0x95: 4,        # SUB L
    0x96: 7,        # SUB (HL)
    0x97: 4,        # SUB A
    0x98: 4,        # SBC A,B
    0x99: 4,        # SBC A,C
    0x9A: 4,        # SBC A,D
    0x9B: 4,        # SBC A,E
    0x9C: 4,        # SBC A,H
    0x9D: 4,        # SBC A,L
    0x9E: 7,        # SBC A,(HL)
    0x9F: 4,        # SBC A,A
    0xA0: 4,        # AND B
    0xA1: 4,        # AND C
    0xA2: 4,        # AND D
    0xA3: 4,        # AND E
    0xA4: 4,        # AND H
    0xA5: 4,        # AND L
    0xA6: 7,        # AND (HL)
    0xA7: 4,        # AND A
    0xA8: 4,        # XOR B
    0xA9: 4,        # XOR C
    0xAA: 4,        # XOR D
    0xAB: 4,        # XOR E
    0xAC: 4,        # XOR H
    0xAD: 4,        # XOR L
    0xAE: 7,        # XOR (HL)
    0xAF: 4,        # XOR A
    0xB0: 4,        # OR B
    0xB1: 4,        # OR C
    0xB2: 4,        # OR D
    0xB3: 4,        # OR E
    0xB4: 4,        # OR H
    0xB5: 4,        # OR L
    0xB6: 7,        # OR (HL)
    0xB7: 4,        # OR A
    0xB8: 4,        # CP B
    0xB9: 4,        # CP C
    0xBA: 4,        # CP D
    0xBB: 4,        # CP E
    0xBC: 4,        # CP H
    0xBD: 4,        # CP L
    0xBE: 7,        # CP (HL)
    0xBF: 4,        # CP A
    0xC0: (11, 5),  # RET NZ
    0xC1: 10,       # POP BC
    0xC2: 10,       # JP NZ,nn
    0xC3: 10,       # JP nn
    0xC4: (17, 10), # CALL NZ,nn
    0xC5: 11,       # PUSH BC
    0xC6: 7,        # ADD A,n
    0xC7: 11,       # RST 0
    0xC8: (11, 5),  # RET Z
    0xC9: 10,       # RET
    0xCA: 10,       # JP Z,nn
    0xCC: (17, 10), # CALL Z,nn
    0xCD: 17,       # CALL nn
    0xCE: 7,        # ADC A,n
    0xCF: 11,       # RST 8
    0xD0: (11, 5),  # RET NC
    0xD1: 10,       # POP DE
    0xD2: 10,       # JP NC,nn
    0xD3: 11,       # OUT (n),A
    0xD4: (17, 10), # CALL NC,nn
    0xD5: 11,       # PUSH DE
    0xD6: 7,        # SUB n
    0xD7: 11,       # RST 16
    0xD8: (11, 5),  # RET C
    0xD9: 4,        # EXX
    0xDA: 10,       # JP C,nn
    0xDB: 11,       # IN A,(n)
    0xDC: (17, 10), # CALL C,nn
    0xDE: 7,        # SBC A,n
    0xDF: 11,       # RST 24
    0xE0: (11, 5),  # RET PO
    0xE1: 10,       # POP HL
    0xE2: 10,       # JP PO,nn
    0xE3: 19,       # EX (SP),HL
    0xE4: (17, 10), # CALL PO,nn
    0xE5: 11,       # PUSH HL
    0xE6: 7,        # AND n
    0xE7: 11,       # RST 32
    0xE8: (11, 5),  # RET PE
    0xE9: 4,        # JP (HL)
    0xEA: 10,       # JP PE,nn
    0xEB: 4,        # EX DE,HL
    0xEC: (17, 10), # CALL PE,nn
    0xEE: 7,        # XOR n
    0xEF: 11,       # RST 40
    0xF0: (11, 5),  # RET P
    0xF1: 10,       # POP AF
    0xF2: 10,       # JP P,nn
    0xF3: 4,        # DI
    0xF4: (17, 10), # CALL P,nn
    0xF5: 11,       # PUSH AF
    0xF6: 7,        # OR n
    0xF7: 11,       # RST 48
    0xF8: (11, 5),  # RET M
    0xF9: 6,        # LD SP,HL
    0xFA: 10,       # JP M,nn
    0xFB: 4,        # EI
    0xFC: (17, 10), # CALL M,nn
    0xFE: 7,        # CP n
    0xFF: 11        # RST 56
}

AFTER_CB_TIMINGS = {
    0x00: 8,  # RLC B
    0x01: 8,  # RLC C
    0x02: 8,  # RLC D
    0x03: 8,  # RLC E
    0x04: 8,  # RLC H
    0x05: 8,  # RLC L
    0x06: 15, # RLC (HL)
    0x07: 8,  # RLC A
    0x08: 8,  # RRC B
    0x09: 8,  # RRC C
    0x0A: 8,  # RRC D
    0x0B: 8,  # RRC E
    0x0C: 8,  # RRC H
    0x0D: 8,  # RRC L
    0x0E: 15, # RRC (HL)
    0x0F: 8,  # RRC A
    0x10: 8,  # RL B
    0x11: 8,  # RL C
    0x12: 8,  # RL D
    0x13: 8,  # RL E
    0x14: 8,  # RL H
    0x15: 8,  # RL L
    0x16: 15, # RL (HL)
    0x17: 8,  # RL A
    0x18: 8,  # RR B
    0x19: 8,  # RR C
    0x1A: 8,  # RR D
    0x1B: 8,  # RR E
    0x1C: 8,  # RR H
    0x1D: 8,  # RR L
    0x1E: 15, # RR (HL)
    0x1F: 8,  # RR A
    0x20: 8,  # SLA B
    0x21: 8,  # SLA C
    0x22: 8,  # SLA D
    0x23: 8,  # SLA E
    0x24: 8,  # SLA H
    0x25: 8,  # SLA L
    0x26: 15, # SLA (HL)
    0x27: 8,  # SLA A
    0x28: 8,  # SRA B
    0x29: 8,  # SRA C
    0x2A: 8,  # SRA D
    0x2B: 8,  # SRA E
    0x2C: 8,  # SRA H
    0x2D: 8,  # SRA L
    0x2E: 15, # SRA (HL)
    0x2F: 8,  # SRA A
    0x30: 8,  # SLL B
    0x31: 8,  # SLL C
    0x32: 8,  # SLL D
    0x33: 8,  # SLL E
    0x34: 8,  # SLL H
    0x35: 8,  # SLL L
    0x36: 15, # SLL (HL)
    0x37: 8,  # SLL A
    0x38: 8,  # SRL B
    0x39: 8,  # SRL C
    0x3A: 8,  # SRL D
    0x3B: 8,  # SRL E
    0x3C: 8,  # SRL H
    0x3D: 8,  # SRL L
    0x3E: 15, # SRL (HL)
    0x3F: 8,  # SRL A
    0x40: 8,  # BIT 0,B
    0x41: 8,  # BIT 0,C
    0x42: 8,  # BIT 0,D
    0x43: 8,  # BIT 0,E
    0x44: 8,  # BIT 0,H
    0x45: 8,  # BIT 0,L
    0x46: 12, # BIT 0,(HL)
    0x47: 8,  # BIT 0,A
    0x48: 8,  # BIT 1,B
    0x49: 8,  # BIT 1,C
    0x4A: 8,  # BIT 1,D
    0x4B: 8,  # BIT 1,E
    0x4C: 8,  # BIT 1,H
    0x4D: 8,  # BIT 1,L
    0x4E: 12, # BIT 1,(HL)
    0x4F: 8,  # BIT 1,A
    0x50: 8,  # BIT 2,B
    0x51: 8,  # BIT 2,C
    0x52: 8,  # BIT 2,D
    0x53: 8,  # BIT 2,E
    0x54: 8,  # BIT 2,H
    0x55: 8,  # BIT 2,L
    0x56: 12, # BIT 2,(HL)
    0x57: 8,  # BIT 2,A
    0x58: 8,  # BIT 3,B
    0x59: 8,  # BIT 3,C
    0x5A: 8,  # BIT 3,D
    0x5B: 8,  # BIT 3,E
    0x5C: 8,  # BIT 3,H
    0x5D: 8,  # BIT 3,L
    0x5E: 12, # BIT 3,(HL)
    0x5F: 8,  # BIT 3,A
    0x60: 8,  # BIT 4,B
    0x61: 8,  # BIT 4,C
    0x62: 8,  # BIT 4,D
    0x63: 8,  # BIT 4,E
    0x64: 8,  # BIT 4,H
    0x65: 8,  # BIT 4,L
    0x66: 12, # BIT 4,(HL)
    0x67: 8,  # BIT 4,A
    0x68: 8,  # BIT 5,B
    0x69: 8,  # BIT 5,C
    0x6A: 8,  # BIT 5,D
    0x6B: 8,  # BIT 5,E
    0x6C: 8,  # BIT 5,H
    0x6D: 8,  # BIT 5,L
    0x6E: 12, # BIT 5,(HL)
    0x6F: 8,  # BIT 5,A
    0x70: 8,  # BIT 6,B
    0x71: 8,  # BIT 6,C
    0x72: 8,  # BIT 6,D
    0x73: 8,  # BIT 6,E
    0x74: 8,  # BIT 6,H
    0x75: 8,  # BIT 6,L
    0x76: 12, # BIT 6,(HL)
    0x77: 8,  # BIT 6,A
    0x78: 8,  # BIT 7,B
    0x79: 8,  # BIT 7,C
    0x7A: 8,  # BIT 7,D
    0x7B: 8,  # BIT 7,E
    0x7C: 8,  # BIT 7,H
    0x7D: 8,  # BIT 7,L
    0x7E: 12, # BIT 7,(HL)
    0x7F: 8,  # BIT 7,A
    0x80: 8,  # RES 0,B
    0x81: 8,  # RES 0,C
    0x82: 8,  # RES 0,D
    0x83: 8,  # RES 0,E
    0x84: 8,  # RES 0,H
    0x85: 8,  # RES 0,L
    0x86: 15, # RES 0,(HL)
    0x87: 8,  # RES 0,A
    0x88: 8,  # RES 1,B
    0x89: 8,  # RES 1,C
    0x8A: 8,  # RES 1,D
    0x8B: 8,  # RES 1,E
    0x8C: 8,  # RES 1,H
    0x8D: 8,  # RES 1,L
    0x8E: 15, # RES 1,(HL)
    0x8F: 8,  # RES 1,A
    0x90: 8,  # RES 2,B
    0x91: 8,  # RES 2,C
    0x92: 8,  # RES 2,D
    0x93: 8,  # RES 2,E
    0x94: 8,  # RES 2,H
    0x95: 8,  # RES 2,L
    0x96: 15, # RES 2,(HL)
    0x97: 8,  # RES 2,A
    0x98: 8,  # RES 3,B
    0x99: 8,  # RES 3,C
    0x9A: 8,  # RES 3,D
    0x9B: 8,  # RES 3,E
    0x9C: 8,  # RES 3,H
    0x9D: 8,  # RES 3,L
    0x9E: 15, # RES 3,(HL)
    0x9F: 8,  # RES 3,A
    0xA0: 8,  # RES 4,B
    0xA1: 8,  # RES 4,C
    0xA2: 8,  # RES 4,D
    0xA3: 8,  # RES 4,E
    0xA4: 8,  # RES 4,H
    0xA5: 8,  # RES 4,L
    0xA6: 15, # RES 4,(HL)
    0xA7: 8,  # RES 4,A
    0xA8: 8,  # RES 5,B
    0xA9: 8,  # RES 5,C
    0xAA: 8,  # RES 5,D
    0xAB: 8,  # RES 5,E
    0xAC: 8,  # RES 5,H
    0xAD: 8,  # RES 5,L
    0xAE: 15, # RES 5,(HL)
    0xAF: 8,  # RES 5,A
    0xB0: 8,  # RES 6,B
    0xB1: 8,  # RES 6,C
    0xB2: 8,  # RES 6,D
    0xB3: 8,  # RES 6,E
    0xB4: 8,  # RES 6,H
    0xB5: 8,  # RES 6,L
    0xB6: 15, # RES 6,(HL)
    0xB7: 8,  # RES 6,A
    0xB8: 8,  # RES 7,B
    0xB9: 8,  # RES 7,C
    0xBA: 8,  # RES 7,D
    0xBB: 8,  # RES 7,E
    0xBC: 8,  # RES 7,H
    0xBD: 8,  # RES 7,L
    0xBE: 15, # RES 7,(HL)
    0xBF: 8,  # RES 7,A
    0xC0: 8,  # SET 0,B
    0xC1: 8,  # SET 0,C
    0xC2: 8,  # SET 0,D
    0xC3: 8,  # SET 0,E
    0xC4: 8,  # SET 0,H
    0xC5: 8,  # SET 0,L
    0xC6: 15, # SET 0,(HL)
    0xC7: 8,  # SET 0,A
    0xC8: 8,  # SET 1,B
    0xC9: 8,  # SET 1,C
    0xCA: 8,  # SET 1,D
    0xCB: 8,  # SET 1,E
    0xCC: 8,  # SET 1,H
    0xCD: 8,  # SET 1,L
    0xCE: 15, # SET 1,(HL)
    0xCF: 8,  # SET 1,A
    0xD0: 8,  # SET 2,B
    0xD1: 8,  # SET 2,C
    0xD2: 8,  # SET 2,D
    0xD3: 8,  # SET 2,E
    0xD4: 8,  # SET 2,H
    0xD5: 8,  # SET 2,L
    0xD6: 15, # SET 2,(HL)
    0xD7: 8,  # SET 2,A
    0xD8: 8,  # SET 3,B
    0xD9: 8,  # SET 3,C
    0xDA: 8,  # SET 3,D
    0xDB: 8,  # SET 3,E
    0xDC: 8,  # SET 3,H
    0xDD: 8,  # SET 3,L
    0xDE: 15, # SET 3,(HL)
    0xDF: 8,  # SET 3,A
    0xE0: 8,  # SET 4,B
    0xE1: 8,  # SET 4,C
    0xE2: 8,  # SET 4,D
    0xE3: 8,  # SET 4,E
    0xE4: 8,  # SET 4,H
    0xE5: 8,  # SET 4,L
    0xE6: 15, # SET 4,(HL)
    0xE7: 8,  # SET 4,A
    0xE8: 8,  # SET 5,B
    0xE9: 8,  # SET 5,C
    0xEA: 8,  # SET 5,D
    0xEB: 8,  # SET 5,E
    0xEC: 8,  # SET 5,H
    0xED: 8,  # SET 5,L
    0xEE: 15, # SET 5,(HL)
    0xEF: 8,  # SET 5,A
    0xF0: 8,  # SET 6,B
    0xF1: 8,  # SET 6,C
    0xF2: 8,  # SET 6,D
    0xF3: 8,  # SET 6,E
    0xF4: 8,  # SET 6,H
    0xF5: 8,  # SET 6,L
    0xF6: 15, # SET 6,(HL)
    0xF7: 8,  # SET 6,A
    0xF8: 8,  # SET 7,B
    0xF9: 8,  # SET 7,C
    0xFA: 8,  # SET 7,D
    0xFB: 8,  # SET 7,E
    0xFC: 8,  # SET 7,H
    0xFD: 8,  # SET 7,L
    0xFE: 15, # SET 7,(HL)
    0xFF: 8   # SET 7,A
}

AFTER_DD_TIMINGS = {
    0x09: 15, # ADD IX,BC
    0x19: 15, # ADD IX,DE
    0x21: 14, # LD IX,nn
    0x22: 20, # LD (nn),IX
    0x23: 10, # INC IX
    0x24: 8,  # INC IXh
    0x25: 8,  # DEC IXh
    0x26: 11, # LD IXh,n
    0x29: 15, # ADD IX,IX
    0x2A: 20, # LD IX,(nn)
    0x2B: 10, # DEC IX
    0x2C: 8,  # INC IXl
    0x2D: 8,  # DEC IXl
    0x2E: 11, # LD IXl,n
    0x34: 23, # INC (IX+d)
    0x35: 23, # DEC (IX+d)
    0x36: 19, # LD (IX+d),n
    0x39: 15, # ADD IX,SP
    0x44: 8,  # LD B,IXh
    0x45: 8,  # LD B,IXl
    0x46: 19, # LD B,(IX+d)
    0x4C: 8,  # LD C,IXh
    0x4D: 8,  # LD C,IXl
    0x4E: 19, # LD C,(IX+d)
    0x54: 8,  # LD D,IXh
    0x55: 8,  # LD D,IXl
    0x56: 19, # LD D,(IX+d)
    0x5C: 8,  # LD E,IXh
    0x5D: 8,  # LD E,IXl
    0x5E: 19, # LD E,(IX+d)
    0x60: 8,  # LD IXh,B
    0x61: 8,  # LD IXh,C
    0x62: 8,  # LD IXh,D
    0x63: 8,  # LD IXh,E
    0x64: 8,  # LD IXh,IXh
    0x65: 8,  # LD IXh,IXl
    0x66: 19, # LD H,(IX+d)
    0x67: 8,  # LD IXh,A
    0x68: 8,  # LD IXl,B
    0x69: 8,  # LD IXl,C
    0x6A: 8,  # LD IXl,D
    0x6B: 8,  # LD IXl,E
    0x6C: 8,  # LD IXl,IXh
    0x6D: 8,  # LD IXl,IXl
    0x6E: 19, # LD L,(IX+d)
    0x6F: 8,  # LD IXl,A
    0x70: 19, # LD (IX+d),B
    0x71: 19, # LD (IX+d),C
    0x72: 19, # LD (IX+d),D
    0x73: 19, # LD (IX+d),E
    0x74: 19, # LD (IX+d),H
    0x75: 19, # LD (IX+d),L
    0x77: 19, # LD (IX+d),A
    0x7C: 8,  # LD A,IXh
    0x7D: 8,  # LD A,IXl
    0x7E: 19, # LD A,(IX+d)
    0x84: 8,  # ADD A,IXh
    0x85: 8,  # ADD A,IXl
    0x86: 19, # ADD A,(IX+d)
    0x8C: 8,  # ADC A,IXh
    0x8D: 8,  # ADC A,IXl
    0x8E: 19, # ADC A,(IX+d)
    0x94: 8,  # SUB IXh
    0x95: 8,  # SUB IXl
    0x96: 19, # SUB (IX+d)
    0x9C: 8,  # SBC A,IXh
    0x9D: 8,  # SBC A,IXl
    0x9E: 19, # SBC A,(IX+d)
    0xA4: 8,  # AND IXh
    0xA5: 8,  # AND IXl
    0xA6: 19, # AND (IX+d)
    0xAC: 8,  # XOR IXh
    0xAD: 8,  # XOR IXl
    0xAE: 19, # XOR (IX+d)
    0xB4: 8,  # OR IXh
    0xB5: 8,  # OR IXl
    0xB6: 19, # OR (IX+d)
    0xBC: 8,  # CP IXh
    0xBD: 8,  # CP IXl
    0xBE: 19, # CP (IX+d)
    0xE1: 14, # POP IX
    0xE3: 23, # EX (SP),IX
    0xE5: 15, # PUSH IX
    0xE9: 8,  # JP (IX)
    0xF9: 10  # LD SP,IX
}

AFTER_ED_TIMINGS = {
    0x40: 12,       # IN B,(C)
    0x41: 12,       # OUT (C),B
    0x42: 15,       # SBC HL,BC
    0x43: 20,       # LD (nn),BC
    0x44: 8,        # NEG
    0x45: 14,       # RETN
    0x46: 8,        # IM 0
    0x47: 9,        # LD I,A
    0x48: 12,       # IN C,(C)
    0x49: 12,       # OUT (C),C
    0x4A: 15,       # ADC HL,BC
    0x4B: 20,       # LD BC,(nn)
    0x4D: 14,       # RETI
    0x4F: 9,        # LD R,A
    0x50: 12,       # IN D,(C)
    0x51: 12,       # OUT (C),D
    0x52: 15,       # SBC HL,DE
    0x53: 20,       # LD (nn),DE
    0x56: 8,        # IM 1
    0x57: 9,        # LD A,I
    0x58: 12,       # IN E,(C)
    0x59: 12,       # OUT (C),E
    0x5A: 15,       # ADC HL,DE
    0x5B: 20,       # LD DE,(nn)
    0x5E: 8,        # IM 2
    0x5F: 9,        # LD A,R
    0x60: 12,       # IN H,(C)
    0x61: 12,       # OUT (C),H
    0x62: 15,       # SBC HL,HL
    0x67: 18,       # RRD
    0x68: 12,       # IN L,(C)
    0x69: 12,       # OUT (C),L
    0x6A: 15,       # ADC HL,HL
    0x6F: 18,       # RLD
    0x72: 15,       # SBC HL,SP
    0x73: 20,       # LD (nn),SP
    0x78: 12,       # IN A,(C)
    0x79: 12,       # OUT (C),A
    0x7A: 15,       # ADC HL,SP
    0x7B: 20,       # LD SP,(nn)
    0xA0: 16,       # LDI
    0xA1: 16,       # CPI
    0xA2: 16,       # INI
    0xA3: 16,       # OUTI
    0xA8: 16,       # LDD
    0xA9: 16,       # CPD
    0xAA: 16,       # IND
    0xAB: 16,       # OUTD
    0xB0: (21, 16), # LDIR
    0xB1: (21, 16), # CPIR
    0xB2: (21, 16), # INIR
    0xB3: (21, 16), # OTIR
    0xB8: (21, 16), # LDDR
    0xB9: (21, 16), # CPDR
    0xBA: (21, 16), # INDR
    0xBB: (21, 16)  # OTDR
}

AFTER_DDCB_TIMINGS = {
    0x06: 23, # RLC (IX+d)
    0x0E: 23, # RRC (IX+d)
    0x16: 23, # RL (IX+d)
    0x1E: 23, # RR (IX+d)
    0x26: 23, # SLA (IX+d)
    0x2E: 23, # SRA (IX+d)
    0x36: 23, # SLL (IX+d)
    0x3E: 23, # SRL (IX+d)
    0x46: 20, # BIT 0,(IX+d)
    0x4E: 20, # BIT 1,(IX+d)
    0x56: 20, # BIT 2,(IX+d)
    0x5E: 20, # BIT 3,(IX+d)
    0x66: 20, # BIT 4,(IX+d)
    0x6E: 20, # BIT 5,(IX+d)
    0x76: 20, # BIT 6,(IX+d)
    0x7E: 20, # BIT 7,(IX+d)
    0x86: 23, # RES 0,(IX+d)
    0x8E: 23, # RES 1,(IX+d)
    0x96: 23, # RES 2,(IX+d)
    0x9E: 23, # RES 3,(IX+d)
    0xA6: 23, # RES 4,(IX+d)
    0xAE: 23, # RES 5,(IX+d)
    0xB6: 23, # RES 6,(IX+d)
    0xBE: 23, # RES 7,(IX+d)
    0xC6: 23, # SET 0,(IX+d)
    0xCE: 23, # SET 1,(IX+d)
    0xD6: 23, # SET 2,(IX+d)
    0xDE: 23, # SET 3,(IX+d)
    0xE6: 23, # SET 4,(IX+d)
    0xEE: 23, # SET 5,(IX+d)
    0xF6: 23, # SET 6,(IX+d)
    0xFE: 23  # SET 7,(IX+d)
}

def _convert_chars(text):
    s = ''
    for p in split_quoted(text):
        if p.startswith('"') and p.endswith('"'):
            if p.startswith('"\\'):
                s += str(ord(p[2:-1]))
            else:
                s += str(ord(p[1:-1]))
        else:
            s += p
    return s

def _convert_nums(text):
    elements = re.split('(\$[0-9A-Fa-f]+|%[01]+|\d+)', re.sub('\s+', '', text))
    for i in range(1, len(elements), 2):
        q = elements[i]
        if q.startswith('$'):
            elements[i] = str(int(q[1:], 16))
        elif q.startswith('%'):
            p = elements[i - 1]
            if i == 1 or (p and p[-1] != ')'):
                elements[i] = str(int(q[1:], 2))
        elif q.startswith('0'):
            elements[i] = str(int(q))
    return ''.join(elements)

def get_timing(instruction):
    if not instruction.operation.upper().startswith('DEF') and instruction.bytes:
        opcode = instruction.bytes[0]
        if opcode == 0xCB:
            return AFTER_CB_TIMINGS[instruction.bytes[1]]
        if opcode == 0xED:
            return AFTER_ED_TIMINGS[instruction.bytes[1]]
        if opcode in (0xDD, 0xFD):
            opcode2 = instruction.bytes[1]
            if opcode2 == 0xCB:
                return AFTER_DDCB_TIMINGS[instruction.bytes[3]]
            return AFTER_DD_TIMINGS[opcode2]
        return TIMINGS[opcode]

# Component API
def eval_int(text):
    """Evaluate an integer operand.

    :param text: The operand.
    :return: The integer value.
    :raises: `ValueError` if the operand is not a valid integer.
    """
    try:
        return get_int_param(text)
    except ValueError:
        pass
    try:
        s = _convert_nums(_convert_chars(text))
        if set(s) <= OPERAND_AE_CHARS:
            return int(eval(s.replace('/', '//')))
    except (ValueError, TypeError):
        pass
    raise ValueError

# Component API
def eval_string(text):
    """Evaluate a string operand.

    :param text: The operand, including enclosing quotes.
    :return: A list of byte values.
    :raises: `ValueError` if the operand is not a valid string.
    """
    if text.startswith('"') and text.endswith('"'):
        data = []
        i = 1
        while i < len(text) - 1:
            if text[i] == '"':
                raise ValueError
            if text[i] == '\\':
                i += 1
            data.append(ord(text[i]))
            i += 1
        return data
    raise ValueError

# Component API
def split_operands(text):
    """Split a comma-separated list of operands.

    :param text: The operands.
    :return: A list of individual operands.
    """
    return [e.strip() for e in split_unquoted(text, ',')]

def _index_code(op):
    if op.startswith('('):
        reg = op[1:3]
    else:
        reg = op[:2]
    return 221 + 32 * INDEX_REG_PAIRS.index(reg)

def _reg_index(reg):
    return REG.index(reg)

def _reg_pair_index(reg_pair):
    return REG_PAIRS.index(reg_pair)

def _index_reg_index(index_reg):
    return INDEX_REG.index(index_reg)

def _condition_index(condition):
    return ('NZ', 'Z', 'NC', 'C', 'PO', 'PE', 'P', 'M').index(condition)

class Assembler:
    def __init__(self):
        self.op_evaluator = get_operand_evaluator()
        self.mnemonics = {
            'ADC': self._assemble_adc,
            'ADD': self._assemble_add,
            'AND': partial(self._arithmetic_a, 160),
            'BIT': partial(self._bit_res_set, 64),
            'CALL': self._assemble_call,
            'CCF': (63,),
            'CP': partial(self._arithmetic_a, 184),
            'CPD': (237, 169),
            'CPDR': (237, 185),
            'CPI': (237, 161),
            'CPIR': (237, 177),
            'CPL': (47,),
            'DAA': (39,),
            'DEC': partial(self._inc_dec, 5, 11),
            'DI': (243,),
            'DJNZ': self._assemble_djnz,
            'EI': (251,),
            'EX': self._assemble_ex,
            'EXX': (217,),
            'HALT': (118,),
            'IM': self._assemble_im,
            'IN': self._assemble_in,
            'INC': partial(self._inc_dec, 4, 3),
            'IND': (237, 170),
            'INDR': (237, 186),
            'INI': (237, 162),
            'INIR': (237, 178),
            'JP': self._assemble_jp,
            'JR': self._assemble_jr,
            'LD': self._assemble_ld,
            'LDD': (237, 168),
            'LDDR': (237, 184),
            'LDI': (237, 160),
            'LDIR': (237, 176),
            'NEG': (237, 68),
            'NOP': (0,),
            'OR': partial(self._arithmetic_a, 176),
            'OTDR': (237, 187),
            'OTIR': (237, 179),
            'OUT': self._assemble_out,
            'OUTD': (237, 171),
            'OUTI': (237, 163),
            'POP': partial(self._pop_push, 193),
            'PUSH': partial(self._pop_push, 197),
            'RES': partial(self._bit_res_set, 128),
            'RET': self._assemble_ret,
            'RETI': (237, 77),
            'RETN': (237, 69),
            'RL': partial(self._rotate_and_shift, 16),
            'RLA': (23,),
            'RLC': partial(self._rotate_and_shift, 0),
            'RLCA': (7,),
            'RLD': (237, 111),
            'RR': partial(self._rotate_and_shift, 24),
            'RRA': (31,),
            'RRC': partial(self._rotate_and_shift, 8),
            'RRCA': (15,),
            'RRD': (237, 103),
            'RST': self._assemble_rst,
            'SBC': self._assemble_sbc,
            'SCF': (55,),
            'SET': partial(self._bit_res_set, 192),
            'SLA': partial(self._rotate_and_shift, 32),
            'SLL': partial(self._rotate_and_shift, 48),
            'SRA': partial(self._rotate_and_shift, 40),
            'SRL': partial(self._rotate_and_shift, 56),
            'SUB': partial(self._arithmetic_a, 144),
            'XOR': partial(self._arithmetic_a, 168)
        }

    def _parse_expr(self, text, limit, brackets, non_neg, default):
        try:
            in_brackets = text.startswith("(") and text.endswith(")")
            if not brackets or in_brackets:
                if in_brackets:
                    text = text[1:-1]
                value = self.op_evaluator.eval_int(text)
                if not (abs(value) >= limit or (non_neg and value < 0)):
                    return value % limit
            raise ValueError
        except ValueError:
            if default is None:
                raise
            return default

    def parse_byte(self, text, limit=256, brackets=False, non_neg=False, default=None):
        return self._parse_expr(text, limit, brackets, non_neg, default)

    def parse_word(self, text, brackets=False, default=None):
        return self._parse_expr(text, 65536, brackets, False, default)

    def _parse_offset(self, op):
        if op.startswith(('(IX+', '(IX-', '(IY+', '(IY-')) and op.endswith(')'):
            offset = self.parse_byte(op[4:-1])
            if op[3] == '-':
                return 256 - offset
            return offset
        raise ValueError

    def _arithmetic_a(self, base_code, address, op):
        if op.startswith('(I'):
            return (_index_code(op), base_code + 6, self._parse_offset(op))
        if op in INDEX_REG:
            return (_index_code(op), base_code + 4 + (_index_reg_index(op) % 2))
        try:
            return (base_code + _reg_index(op),)
        except ValueError:
            return (base_code + 70, self.parse_byte(op))

    def _assemble_adc(self, address, op1, op2):
        if op1 == 'A':
            return self._arithmetic_a(136, address, op2)
        if op1 == 'HL':
            return (237, 74 + 16 * _reg_pair_index(op2))

    def _assemble_add(self, address, op1, op2):
        if op1 == 'A':
            return self._arithmetic_a(128, address, op2)
        if op1 == 'HL':
            return (9 + 16 * _reg_pair_index(op2),)
        if op1 in INDEX_REG_PAIRS:
            if op1 == op2:
                return (_index_code(op1), 41)
            if op2 != 'HL':
                return (_index_code(op1), 9 + 16 * _reg_pair_index(op2))

    def _bit_res_set(self, base_code, address, op1, op2):
        bit_offset = base_code + 8 * self.parse_byte(op1, 8, non_neg=True)
        if op2.startswith('(I'):
            return (_index_code(op2), 203, self._parse_offset(op2), bit_offset + 6)
        return (203, bit_offset + _reg_index(op2))

    def _assemble_call(self, address, op1, op2=None):
        if op2 is None:
            addr = self.parse_word(op1)
            return (205, addr % 256, addr // 256)
        addr = self.parse_word(op2)
        return (196 + 8 * _condition_index(op1), addr % 256, addr // 256)

    def _inc_dec(self, base_code8, base_code16, address, op):
        if len(op) == 2:
            try:
                return (base_code16 + 16 * _reg_pair_index(op),)
            except ValueError:
                return (_index_code(op), base_code16 + 32)
        if op.startswith('(I'):
            return (_index_code(op), base_code8 + 48, self._parse_offset(op))
        if op in INDEX_REG:
            return (_index_code(op), base_code8 + 32 + 8 * (_index_reg_index(op) % 2))
        return (base_code8 + 8 * _reg_index(op),)

    def _address_offset(self, address, op):
        offset = self.parse_word(op) - address
        if offset >= 65410:
            offset -= 65536
        elif offset <= -65407:
            offset += 65536
        if -126 <= offset < 130:
            return (offset - 2) & 255
        raise ValueError

    def _assemble_djnz(self, address, op):
        return (16, self._address_offset(address, op))

    def _assemble_ex(self, address, op1, op2):
        if op1 == 'AF' and op2 == "AF'":
            return (8,)
        if op1 == 'DE' and op2 == 'HL':
            return (235,)
        if op1 == '(SP)':
            if op2 == 'HL':
                return (227,)
            if op2 in INDEX_REG_PAIRS:
                return (_index_code(op2), 227)

    def _assemble_im(self, address, op):
        return (237, 70 + (0, 16, 24)[self.parse_byte(op, 3, non_neg=True)])

    def _assemble_in(self, address, op1, op2):
        if op2 == '(C)' and op1 != '(HL)':
            return (237, 64 + 8 * _reg_index(op1))
        if op1 == 'A':
            return (219, self.parse_byte(op2, brackets=True, non_neg=True))

    def _assemble_jp(self, address, op1, op2=None):
        if op2 is None:
            if op1 == '(HL)':
                return (233,)
            if op1 == '(IX)':
                return (221, 233)
            if op1 == '(IY)':
                return (253, 233)
            addr = self.parse_word(op1)
            return (195, addr % 256, addr // 256)
        addr = self.parse_word(op2)
        return (194 + 8 * _condition_index(op1), addr % 256, addr // 256)

    def _assemble_jr(self, address, op1, op2=None):
        if op2 is None:
            return (24, self._address_offset(address, op1))
        return (32 + 8 * _condition_index(op1), self._address_offset(address, op2))

    def _assemble_ld(self, address, op1, op2):
        if op1 in REG:
            op1_index = _reg_index(op1)
            if op2 in REG and not op1 == op2 == '(HL)':
                # LD r,r'; LD r,(HL)
                return (64 + 8 * op1_index + _reg_index(op2),)
            if op2.startswith('(I') and  op1 != '(HL)':
                # LD r,(I{X,Y}+d)
                return (_index_code(op2), 70 + 8 * op1_index, self._parse_offset(op2))
            if op2 in INDEX_REG and op1 not in ('H', 'L', '(HL)'):
                # LD r,I{X,Y}{h,l}
                return (_index_code(op2), 68 + 8 * op1_index + (_index_reg_index(op2) % 2))
            if op1 == 'A':
                if op2.startswith('('):
                    try:
                        # LD A,(nn)
                        addr = self.parse_word(op2, True)
                        return (58, addr % 256, addr // 256)
                    except ValueError:
                        # LD A,(BC); LD A,(DE)
                        return (10 + 16 * ('(BC)', '(DE)').index(op2),)
                try:
                    # LD A,n
                    return (62, self.parse_byte(op2))
                except ValueError:
                    # LD A,I; LD A,R
                    return (237, 87 + 8 * ('I', 'R').index(op2))
            # LD r,n (r != A)
            return (6 + 8 * _reg_index(op1), self.parse_byte(op2))

        if op1 in INDEX_REG:
            index1 = _index_reg_index(op1)
            if op2 in INDEX_REG and op1[1] == op2[1]:
                # LD IX{h,l},IX{h,l}; LD IY{h,l},IY{h,l}
                index2 = _index_reg_index(op2)
                return (_index_code(op1), 100 + 8 * (index1 % 2) + (index2 % 2))
            if op2 in ('A', 'B', 'C', 'D', 'E'):
                # LD I{X,Y}{h,l},r
                return (_index_code(op1), 96 + 8 * (index1 % 2) + _reg_index(op2))
            # LD I{X,Y}{h,l},n
            return (_index_code(op1), 38 + 8 * (index1 % 2), self.parse_byte(op2))

        if op1.startswith('(I'):
            offset = self._parse_offset(op1)
            if op2 in REG and op2 != '(HL)':
                # LD (I{X,Y}+d),r
                return (_index_code(op1), 112 + _reg_index(op2), offset)
            # LD (I{X,Y}+d),n
            return (_index_code(op1), 54, offset, self.parse_byte(op2))

        if op1 in REG_PAIRS:
            op1_index = _reg_pair_index(op1)
            if op2.startswith('('):
                addr = self.parse_word(op2, True)
                lsb, msb = addr % 256, addr // 256
                if op1 == 'HL':
                    # LD HL,(nn)
                    return (42, lsb, msb)
                # LD BC|DE|SP,(nn)
                return (237, 75 + 16 * op1_index, lsb, msb)
            if op1 == 'SP' and op2 in ('HL', 'IX', 'IY'):
                if op2 == 'HL':
                    # LD SP,HL
                    return (249,)
                # LD SP,I{X,Y}
                return (_index_code(op2), 249)
            # LD BC|DE|HL|SP,nn
            addr = self.parse_word(op2)
            return (1 + 16 * op1_index, addr % 256, addr // 256)

        if op1 in INDEX_REG_PAIRS:
            if op2.startswith('('):
                addr = self.parse_word(op2, True)
                # LD I{X,Y},(nn)
                return (_index_code(op1), 42, addr % 256, addr // 256)
            # LD I{X,Y},nn
            addr = self.parse_word(op2)
            return (_index_code(op1), 33, addr % 256, addr // 256)

        if op1.startswith('('):
            if op2 == 'A':
                try:
                    # LD (nn),A
                    addr = self.parse_word(op1, True)
                    return (50, addr % 256, addr // 256)
                except ValueError:
                    # LD (BC),A; LD (DE),A
                    return (2 + 16 * ('(BC)', '(DE)').index(op1),)
            addr = self.parse_word(op1, True)
            lsb, msb = addr % 256, addr // 256
            if op2 == 'HL':
                # LD (nn),HL
                return (34, lsb, msb)
            if op2 in INDEX_REG_PAIRS:
                # LD (nn),I{X,Y}
                return (_index_code(op2), 34, lsb, msb)
            # LD (nn),BC|DE|SP
            return (237, 67 + 16 * _reg_pair_index(op2), lsb, msb)

        if op2 == 'A':
            # LD I,A; LD R,A
            return (237, 71 + 8 * ('I', 'R').index(op1))

    def _assemble_out(self, address, op1, op2):
        if op1 == '(C)' and op2 != '(HL)':
            return (237, 65 + 8 * _reg_index(op2))
        if op2 == 'A':
            return (211, self.parse_byte(op1, brackets=True, non_neg=True))

    def _pop_push(self, base_code, address, op):
        if op in INDEX_REG_PAIRS:
            return (_index_code(op), base_code + 32)
        return (base_code + 16 * ('BC', 'DE', 'HL', 'AF').index(op),)

    def _assemble_ret(self, address, op1=None):
        if op1 is None:
            return (201,)
        return (192 + 8 * _condition_index(op1),)

    def _rotate_and_shift(self, base_code, address, op):
        if op.startswith('(I'):
            return (_index_code(op), 203, self._parse_offset(op), base_code + 6)
        return (203, base_code + _reg_index(op))

    def _assemble_rst(self, address, op):
        num = self.parse_byte(op, 57, non_neg=True)
        if num % 8 == 0:
            return (199 + num,)

    def _assemble_sbc(self, address, op1, op2):
        if op1 == 'A':
            return self._arithmetic_a(152, address, op2)
        if op1 == 'HL':
            return (237, 66 + 16 * _reg_pair_index(op2))

    def _assemble_defb(self, items):
        data = []
        for item in items:
            try:
                data.extend(self.op_evaluator.eval_string(item))
            except ValueError:
                data.append(self.parse_byte(item, default=0))
        return tuple(data)

    def _assemble_defs(self, items):
        if items:
            span = self.parse_word(items[0], default=0)
            if len(items) > 1:
                value = self.parse_byte(items[1], default=0)
            else:
                value = 0
            return (value,) * span

    def _assemble_defw(self, items):
        data = []
        for arg in [self.parse_word(v, default=0) for v in items]:
            data.extend((arg % 256, arg // 256))
        return tuple(data)

    def convert_case(self, operation, lower=True, trim=False):
        i = 0
        converted = ''
        convert = True
        leave_spaces = True
        while i < len(operation):
            c = operation[i]
            if c == '"':
                convert = not convert
            elif c == '\\' and not convert:
                converted += operation[i:i + 2]
                i += 2
                continue
            if convert:
                if c.isspace():
                    if not trim or leave_spaces:
                        converted += ' '
                        leave_spaces = False
                elif lower:
                    converted += c.lower()
                else:
                    converted += c.upper()
            else:
                converted += c
            i += 1
        return converted

    def _assemble(self, operation, address):
        if operation.upper().startswith(('DEFB ', 'DEFM ', 'DEFS ', 'DEFW ')):
            directive = operation.upper()[:4]
            items = self.op_evaluator.split_operands(operation[5:].strip())
            if directive in ('DEFB', 'DEFM'):
                return self._assemble_defb(items)
            if directive == 'DEFS':
                return self._assemble_defs(items)
            if directive == 'DEFW':
                return self._assemble_defw(items)

        parts = self.split_operation(operation, True)
        a = self.mnemonics[parts[0]]
        if isinstance(a, tuple):
            if len(parts) == 1:
                return a
            return
        return a(address, *parts[1:])

    def split_operation(self, operation, tidy=False):
        if tidy:
            operation = self.convert_case(operation, False, True)
        elements = operation.split(None, 1)
        if len(elements) > 1:
            elements[1:] = self.op_evaluator.split_operands(elements[1])
        return elements

    # Component API
    def get_size(self, operation, address):
        """Compute the size (in bytes) of an assembly language instruction or
        DEFB/DEFM/DEFS/DEFW statement.

        :param operation: The operation (e.g. 'XOR A').
        :param address: The instruction address.
        :return: The instruction size, or 0 if the instruction cannot be assembled.
        """
        return len(self.assemble(operation, address))

    # Component API
    def assemble(self, operation, address):
        """Convert an assembly language instruction or DEFB/DEFM/DEFS/DEFW
        statement into a sequence of byte values.

        :param operation: The operation to convert (e.g. 'XOR A').
        :param address: The instruction address.
        :return: A sequence of byte values (empty if the instruction cannot be
                 assembled).
        """
        try:
            return self._assemble(operation, address) or ()
        except:
            return ()
