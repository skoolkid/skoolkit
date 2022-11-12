# Copyright 2022 Richard Dymond (rjdymond@gmail.com)
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

def disassemble(memory, address, prefix='$', byte_fmt='02X', word_fmt='04X'):
    opcode = memory[address]
    func, operation, size = OPCODES[opcode]
    if func:
        return func(memory, address, operation, size, prefix, byte_fmt, word_fmt)
    if opcode == 0xCB:
        func, operation, size = AFTER_CB[memory[(address + 1) % 65536]]
    elif opcode == 0xED:
        func, operation, size = AFTER_ED[memory[(address + 1) % 65536]]
    elif opcode == 0xDD:
        func, operation, size = AFTER_DD[memory[(address + 1) % 65536]]
        if func is None:
            func, operation, size = AFTER_DDCB[memory[(address + 3) % 65536]]
    else:
        func, operation, size = AFTER_FD[memory[(address + 1) % 65536]]
        if func is None:
            func, operation, size = AFTER_FDCB[memory[(address + 3) % 65536]]
    return func(memory, address, operation, size, prefix, byte_fmt, word_fmt)

def operation(memory, address, operation, size, p, b, w):
    return operation, size

def byte(memory, address, operation, size, p, b, w):
    n = memory[(address + size - 1) % 65536]
    return operation.format(p=p, n=n, b=b), size

def word(memory, address, operation, size, p, b, w):
    n = memory[(address + size - 2) % 65536] + 256 * memory[(address + size - 1) % 65536]
    return operation.format(p=p, n=n, w=w), size

def jump_offset(memory, address, operation, size, p, b, w):
    offset = memory[(address + 1) % 65536]
    if offset < 128:
        n = (address + 2 + offset) % 65536
    else:
        n = (address - 254 + offset) % 65536
    return operation.format(p=p, n=n, w=w), 2

def offset(memory, address, operation, size, p, b, w):
    d = memory[(address + 2) % 65536]
    if d < 128:
        return operation.format(s='+', p=p, d=d, b=b), size
    return operation.format(s='-', p=p, d=256-d, b=b), size

def offset_byte(memory, address, operation, size, p, b, w):
    d = memory[(address + 2) % 65536]
    n = memory[(address + 3) % 65536]
    if d < 128:
        return operation.format(s='+', p=p, d=d, n=n, b=b), 4
    return operation.format(s='-', p=p, d=256-d, n=n, b=b), 4

def rst(memory, address, operation, size, p, b, w):
    n = memory[address] - 0xC7
    return operation.format(p=p, n=n, b=b), 1

def defb(memory, address, operation, size, p, b, w):
    if size == 1:
        return f'DEFB {p}{memory[address]:{b}}', 1
    return f'DEFB {p}{memory[address]:{b}},{p}{memory[(address + 1) % 65536]:{b}}', 2

OPCODES = (
    (operation, "NOP", 1),                               # 00
    (word, "LD BC,{p}{n:{w}}", 3),                       # 01
    (operation, "LD (BC),A", 1),                         # 02
    (operation, "INC BC", 1),                            # 03
    (operation, "INC B", 1),                             # 04
    (operation, "DEC B", 1),                             # 05
    (byte, "LD B,{p}{n:{b}}", 2),                        # 06
    (operation, "RLCA", 1),                              # 07
    (operation, "EX AF,AF'", 1),                         # 08
    (operation, "ADD HL,BC", 1),                         # 09
    (operation, "LD A,(BC)", 1),                         # 0A
    (operation, "DEC BC", 1),                            # 0B
    (operation, "INC C", 1),                             # 0C
    (operation, "DEC C", 1),                             # 0D
    (byte, "LD C,{p}{n:{b}}", 2),                        # 0E
    (operation, "RRCA", 1),                              # 0F
    (jump_offset, "DJNZ {p}{n:{w}}", 2),                 # 10
    (word, "LD DE,{p}{n:{w}}", 3),                       # 11
    (operation, "LD (DE),A", 1),                         # 12
    (operation, "INC DE", 1),                            # 13
    (operation, "INC D", 1),                             # 14
    (operation, "DEC D", 1),                             # 15
    (byte, "LD D,{p}{n:{b}}", 2),                        # 16
    (operation, "RLA", 1),                               # 17
    (jump_offset, "JR {p}{n:{w}}", 2),                   # 18
    (operation, "ADD HL,DE", 1),                         # 19
    (operation, "LD A,(DE)", 1),                         # 1A
    (operation, "DEC DE", 1),                            # 1B
    (operation, "INC E", 1),                             # 1C
    (operation, "DEC E", 1),                             # 1D
    (byte, "LD E,{p}{n:{b}}", 2),                        # 1E
    (operation, "RRA", 1),                               # 1F
    (jump_offset, "JR NZ,{p}{n:{w}}", 2),                # 20
    (word, "LD HL,{p}{n:{w}}", 3),                       # 21
    (word, "LD ({p}{n:{w}}),HL", 3),                     # 22
    (operation, "INC HL", 1),                            # 23
    (operation, "INC H", 1),                             # 24
    (operation, "DEC H", 1),                             # 25
    (byte, "LD H,{p}{n:{b}}", 2),                        # 26
    (operation, "DAA", 1),                               # 27
    (jump_offset, "JR Z,{p}{n:{w}}", 2),                 # 28
    (operation, "ADD HL,HL", 1),                         # 29
    (word, "LD HL,({p}{n:{w}})", 3),                     # 2A
    (operation, "DEC HL", 1),                            # 2B
    (operation, "INC L", 1),                             # 2C
    (operation, "DEC L", 1),                             # 2D
    (byte, "LD L,{p}{n:{b}}", 2),                        # 2E
    (operation, "CPL", 1),                               # 2F
    (jump_offset, "JR NC,{p}{n:{w}}", 2),                # 30
    (word, "LD SP,{p}{n:{w}}", 3),                       # 31
    (word, "LD ({p}{n:{w}}),A", 3),                      # 32
    (operation, "INC SP", 1),                            # 33
    (operation, "INC (HL)", 1),                          # 34
    (operation, "DEC (HL)", 1),                          # 35
    (byte, "LD (HL),{p}{n:{b}}", 2),                     # 36
    (operation, "SCF", 1),                               # 37
    (jump_offset, "JR C,{p}{n:{w}}", 2),                 # 38
    (operation, "ADD HL,SP", 1),                         # 39
    (word, "LD A,({p}{n:{w}})", 3),                      # 3A
    (operation, "DEC SP", 1),                            # 3B
    (operation, "INC A", 1),                             # 3C
    (operation, "DEC A", 1),                             # 3D
    (byte, "LD A,{p}{n:{b}}", 2),                        # 3E
    (operation, "CCF", 1),                               # 3F
    (operation, "LD B,B", 1),                            # 40
    (operation, "LD B,C", 1),                            # 41
    (operation, "LD B,D", 1),                            # 42
    (operation, "LD B,E", 1),                            # 43
    (operation, "LD B,H", 1),                            # 44
    (operation, "LD B,L", 1),                            # 45
    (operation, "LD B,(HL)", 1),                         # 46
    (operation, "LD B,A", 1),                            # 47
    (operation, "LD C,B", 1),                            # 48
    (operation, "LD C,C", 1),                            # 49
    (operation, "LD C,D", 1),                            # 4A
    (operation, "LD C,E", 1),                            # 4B
    (operation, "LD C,H", 1),                            # 4C
    (operation, "LD C,L", 1),                            # 4D
    (operation, "LD C,(HL)", 1),                         # 4E
    (operation, "LD C,A", 1),                            # 4F
    (operation, "LD D,B", 1),                            # 50
    (operation, "LD D,C", 1),                            # 51
    (operation, "LD D,D", 1),                            # 52
    (operation, "LD D,E", 1),                            # 53
    (operation, "LD D,H", 1),                            # 54
    (operation, "LD D,L", 1),                            # 55
    (operation, "LD D,(HL)", 1),                         # 56
    (operation, "LD D,A", 1),                            # 57
    (operation, "LD E,B", 1),                            # 58
    (operation, "LD E,C", 1),                            # 59
    (operation, "LD E,D", 1),                            # 5A
    (operation, "LD E,E", 1),                            # 5B
    (operation, "LD E,H", 1),                            # 5C
    (operation, "LD E,L", 1),                            # 5D
    (operation, "LD E,(HL)", 1),                         # 5E
    (operation, "LD E,A", 1),                            # 5F
    (operation, "LD H,B", 1),                            # 60
    (operation, "LD H,C", 1),                            # 61
    (operation, "LD H,D", 1),                            # 62
    (operation, "LD H,E", 1),                            # 63
    (operation, "LD H,H", 1),                            # 64
    (operation, "LD H,L", 1),                            # 65
    (operation, "LD H,(HL)", 1),                         # 66
    (operation, "LD H,A", 1),                            # 67
    (operation, "LD L,B", 1),                            # 68
    (operation, "LD L,C", 1),                            # 69
    (operation, "LD L,D", 1),                            # 6A
    (operation, "LD L,E", 1),                            # 6B
    (operation, "LD L,H", 1),                            # 6C
    (operation, "LD L,L", 1),                            # 6D
    (operation, "LD L,(HL)", 1),                         # 6E
    (operation, "LD L,A", 1),                            # 6F
    (operation, "LD (HL),B", 1),                         # 70
    (operation, "LD (HL),C", 1),                         # 71
    (operation, "LD (HL),D", 1),                         # 72
    (operation, "LD (HL),E", 1),                         # 73
    (operation, "LD (HL),H", 1),                         # 74
    (operation, "LD (HL),L", 1),                         # 75
    (operation, "HALT", 1),                              # 76
    (operation, "LD (HL),A", 1),                         # 77
    (operation, "LD A,B", 1),                            # 78
    (operation, "LD A,C", 1),                            # 79
    (operation, "LD A,D", 1),                            # 7A
    (operation, "LD A,E", 1),                            # 7B
    (operation, "LD A,H", 1),                            # 7C
    (operation, "LD A,L", 1),                            # 7D
    (operation, "LD A,(HL)", 1),                         # 7E
    (operation, "LD A,A", 1),                            # 7F
    (operation, "ADD A,B", 1),                           # 80
    (operation, "ADD A,C", 1),                           # 81
    (operation, "ADD A,D", 1),                           # 82
    (operation, "ADD A,E", 1),                           # 83
    (operation, "ADD A,H", 1),                           # 84
    (operation, "ADD A,L", 1),                           # 85
    (operation, "ADD A,(HL)", 1),                        # 86
    (operation, "ADD A,A", 1),                           # 87
    (operation, "ADC A,B", 1),                           # 88
    (operation, "ADC A,C", 1),                           # 89
    (operation, "ADC A,D", 1),                           # 8A
    (operation, "ADC A,E", 1),                           # 8B
    (operation, "ADC A,H", 1),                           # 8C
    (operation, "ADC A,L", 1),                           # 8D
    (operation, "ADC A,(HL)", 1),                        # 8E
    (operation, "ADC A,A", 1),                           # 8F
    (operation, "SUB B", 1),                             # 90
    (operation, "SUB C", 1),                             # 91
    (operation, "SUB D", 1),                             # 92
    (operation, "SUB E", 1),                             # 93
    (operation, "SUB H", 1),                             # 94
    (operation, "SUB L", 1),                             # 95
    (operation, "SUB (HL)", 1),                          # 96
    (operation, "SUB A", 1),                             # 97
    (operation, "SBC A,B", 1),                           # 98
    (operation, "SBC A,C", 1),                           # 99
    (operation, "SBC A,D", 1),                           # 9A
    (operation, "SBC A,E", 1),                           # 9B
    (operation, "SBC A,H", 1),                           # 9C
    (operation, "SBC A,L", 1),                           # 9D
    (operation, "SBC A,(HL)", 1),                        # 9E
    (operation, "SBC A,A", 1),                           # 9F
    (operation, "AND B", 1),                             # A0
    (operation, "AND C", 1),                             # A1
    (operation, "AND D", 1),                             # A2
    (operation, "AND E", 1),                             # A3
    (operation, "AND H", 1),                             # A4
    (operation, "AND L", 1),                             # A5
    (operation, "AND (HL)", 1),                          # A6
    (operation, "AND A", 1),                             # A7
    (operation, "XOR B", 1),                             # A8
    (operation, "XOR C", 1),                             # A9
    (operation, "XOR D", 1),                             # AA
    (operation, "XOR E", 1),                             # AB
    (operation, "XOR H", 1),                             # AC
    (operation, "XOR L", 1),                             # AD
    (operation, "XOR (HL)", 1),                          # AE
    (operation, "XOR A", 1),                             # AF
    (operation, "OR B", 1),                              # B0
    (operation, "OR C", 1),                              # B1
    (operation, "OR D", 1),                              # B2
    (operation, "OR E", 1),                              # B3
    (operation, "OR H", 1),                              # B4
    (operation, "OR L", 1),                              # B5
    (operation, "OR (HL)", 1),                           # B6
    (operation, "OR A", 1),                              # B7
    (operation, "CP B", 1),                              # B8
    (operation, "CP C", 1),                              # B9
    (operation, "CP D", 1),                              # BA
    (operation, "CP E", 1),                              # BB
    (operation, "CP H", 1),                              # BC
    (operation, "CP L", 1),                              # BD
    (operation, "CP (HL)", 1),                           # BE
    (operation, "CP A", 1),                              # BF
    (operation, "RET NZ", 1),                            # C0
    (operation, "POP BC", 1),                            # C1
    (word, "JP NZ,{p}{n:{w}}", 3),                       # C2
    (word, "JP {p}{n:{w}}", 3),                          # C3
    (word, "CALL NZ,{p}{n:{w}}", 3),                     # C4
    (operation, "PUSH BC", 1),                           # C5
    (byte, "ADD A,{p}{n:{b}}", 2),                       # C6
    (rst, "RST {p}{n:{b}}", 1),                          # C7
    (operation, "RET Z", 1),                             # C8
    (operation, "RET", 1),                               # C9
    (word, "JP Z,{p}{n:{w}}", 3),                        # CA
    (None, "", 0),                                       # CB
    (word, "CALL Z,{p}{n:{w}}", 3),                      # CC
    (word, "CALL {p}{n:{w}}", 3),                        # CD
    (byte, "ADC A,{p}{n:{b}}", 2),                       # CE
    (rst, "RST {p}{n:{b}}", 1),                          # CF
    (operation, "RET NC", 1),                            # D0
    (operation, "POP DE", 1),                            # D1
    (word, "JP NC,{p}{n:{w}}", 3),                       # D2
    (byte, "OUT ({p}{n:{b}}),A", 2),                     # D3
    (word, "CALL NC,{p}{n:{w}}", 3),                     # D4
    (operation, "PUSH DE", 1),                           # D5
    (byte, "SUB {p}{n:{b}}", 2),                         # D6
    (rst, "RST {p}{n:{b}}", 1),                          # D7
    (operation, "RET C", 1),                             # D8
    (operation, "EXX", 1),                               # D9
    (word, "JP C,{p}{n:{w}}", 3),                        # DA
    (byte, "IN A,({p}{n:{b}})", 2),                      # DB
    (word, "CALL C,{p}{n:{w}}", 3),                      # DC
    (None, "", 0),                                       # DD
    (byte, "SBC A,{p}{n:{b}}", 2),                       # DE
    (rst, "RST {p}{n:{b}}", 1),                          # DF
    (operation, "RET PO", 1),                            # E0
    (operation, "POP HL", 1),                            # E1
    (word, "JP PO,{p}{n:{w}}", 3),                       # E2
    (operation, "EX (SP),HL", 1),                        # E3
    (word, "CALL PO,{p}{n:{w}}", 3),                     # E4
    (operation, "PUSH HL", 1),                           # E5
    (byte, "AND {p}{n:{b}}", 2),                         # E6
    (rst, "RST {p}{n:{b}}", 1),                          # E7
    (operation, "RET PE", 1),                            # E8
    (operation, "JP (HL)", 1),                           # E9
    (word, "JP PE,{p}{n:{w}}", 3),                       # EA
    (operation, "EX DE,HL", 1),                          # EB
    (word, "CALL PE,{p}{n:{w}}", 3),                     # EC
    (None, "", 0),                                       # ED
    (byte, "XOR {p}{n:{b}}", 2),                         # EE
    (rst, "RST {p}{n:{b}}", 1),                          # EF
    (operation, "RET P", 1),                             # F0
    (operation, "POP AF", 1),                            # F1
    (word, "JP P,{p}{n:{w}}", 3),                        # F2
    (operation, "DI", 1),                                # F3
    (word, "CALL P,{p}{n:{w}}", 3),                      # F4
    (operation, "PUSH AF", 1),                           # F5
    (byte, "OR {p}{n:{b}}", 2),                          # F6
    (rst, "RST {p}{n:{b}}", 1),                          # F7
    (operation, "RET M", 1),                             # F8
    (operation, "LD SP,HL", 1),                          # F9
    (word, "JP M,{p}{n:{w}}", 3),                        # FA
    (operation, "EI", 1),                                # FB
    (word, "CALL M,{p}{n:{w}}", 3),                      # FC
    (None, "", 0),                                       # FD
    (byte, "CP {p}{n:{b}}", 2),                          # FE
    (rst, "RST {p}{n:{b}}", 1),                          # FF
)

AFTER_CB = (
    (operation, "RLC B", 2),                             # CB00
    (operation, "RLC C", 2),                             # CB01
    (operation, "RLC D", 2),                             # CB02
    (operation, "RLC E", 2),                             # CB03
    (operation, "RLC H", 2),                             # CB04
    (operation, "RLC L", 2),                             # CB05
    (operation, "RLC (HL)", 2),                          # CB06
    (operation, "RLC A", 2),                             # CB07
    (operation, "RRC B", 2),                             # CB08
    (operation, "RRC C", 2),                             # CB09
    (operation, "RRC D", 2),                             # CB0A
    (operation, "RRC E", 2),                             # CB0B
    (operation, "RRC H", 2),                             # CB0C
    (operation, "RRC L", 2),                             # CB0D
    (operation, "RRC (HL)", 2),                          # CB0E
    (operation, "RRC A", 2),                             # CB0F
    (operation, "RL B", 2),                              # CB10
    (operation, "RL C", 2),                              # CB11
    (operation, "RL D", 2),                              # CB12
    (operation, "RL E", 2),                              # CB13
    (operation, "RL H", 2),                              # CB14
    (operation, "RL L", 2),                              # CB15
    (operation, "RL (HL)", 2),                           # CB16
    (operation, "RL A", 2),                              # CB17
    (operation, "RR B", 2),                              # CB18
    (operation, "RR C", 2),                              # CB19
    (operation, "RR D", 2),                              # CB1A
    (operation, "RR E", 2),                              # CB1B
    (operation, "RR H", 2),                              # CB1C
    (operation, "RR L", 2),                              # CB1D
    (operation, "RR (HL)", 2),                           # CB1E
    (operation, "RR A", 2),                              # CB1F
    (operation, "SLA B", 2),                             # CB20
    (operation, "SLA C", 2),                             # CB21
    (operation, "SLA D", 2),                             # CB22
    (operation, "SLA E", 2),                             # CB23
    (operation, "SLA H", 2),                             # CB24
    (operation, "SLA L", 2),                             # CB25
    (operation, "SLA (HL)", 2),                          # CB26
    (operation, "SLA A", 2),                             # CB27
    (operation, "SRA B", 2),                             # CB28
    (operation, "SRA C", 2),                             # CB29
    (operation, "SRA D", 2),                             # CB2A
    (operation, "SRA E", 2),                             # CB2B
    (operation, "SRA H", 2),                             # CB2C
    (operation, "SRA L", 2),                             # CB2D
    (operation, "SRA (HL)", 2),                          # CB2E
    (operation, "SRA A", 2),                             # CB2F
    (operation, "SLL B", 2),                             # CB30
    (operation, "SLL C", 2),                             # CB31
    (operation, "SLL D", 2),                             # CB32
    (operation, "SLL E", 2),                             # CB33
    (operation, "SLL H", 2),                             # CB34
    (operation, "SLL L", 2),                             # CB35
    (operation, "SLL (HL)", 2),                          # CB36
    (operation, "SLL A", 2),                             # CB37
    (operation, "SRL B", 2),                             # CB38
    (operation, "SRL C", 2),                             # CB39
    (operation, "SRL D", 2),                             # CB3A
    (operation, "SRL E", 2),                             # CB3B
    (operation, "SRL H", 2),                             # CB3C
    (operation, "SRL L", 2),                             # CB3D
    (operation, "SRL (HL)", 2),                          # CB3E
    (operation, "SRL A", 2),                             # CB3F
    (operation, "BIT 0,B", 2),                           # CB40
    (operation, "BIT 0,C", 2),                           # CB41
    (operation, "BIT 0,D", 2),                           # CB42
    (operation, "BIT 0,E", 2),                           # CB43
    (operation, "BIT 0,H", 2),                           # CB44
    (operation, "BIT 0,L", 2),                           # CB45
    (operation, "BIT 0,(HL)", 2),                        # CB46
    (operation, "BIT 0,A", 2),                           # CB47
    (operation, "BIT 1,B", 2),                           # CB48
    (operation, "BIT 1,C", 2),                           # CB49
    (operation, "BIT 1,D", 2),                           # CB4A
    (operation, "BIT 1,E", 2),                           # CB4B
    (operation, "BIT 1,H", 2),                           # CB4C
    (operation, "BIT 1,L", 2),                           # CB4D
    (operation, "BIT 1,(HL)", 2),                        # CB4E
    (operation, "BIT 1,A", 2),                           # CB4F
    (operation, "BIT 2,B", 2),                           # CB50
    (operation, "BIT 2,C", 2),                           # CB51
    (operation, "BIT 2,D", 2),                           # CB52
    (operation, "BIT 2,E", 2),                           # CB53
    (operation, "BIT 2,H", 2),                           # CB54
    (operation, "BIT 2,L", 2),                           # CB55
    (operation, "BIT 2,(HL)", 2),                        # CB56
    (operation, "BIT 2,A", 2),                           # CB57
    (operation, "BIT 3,B", 2),                           # CB58
    (operation, "BIT 3,C", 2),                           # CB59
    (operation, "BIT 3,D", 2),                           # CB5A
    (operation, "BIT 3,E", 2),                           # CB5B
    (operation, "BIT 3,H", 2),                           # CB5C
    (operation, "BIT 3,L", 2),                           # CB5D
    (operation, "BIT 3,(HL)", 2),                        # CB5E
    (operation, "BIT 3,A", 2),                           # CB5F
    (operation, "BIT 4,B", 2),                           # CB60
    (operation, "BIT 4,C", 2),                           # CB61
    (operation, "BIT 4,D", 2),                           # CB62
    (operation, "BIT 4,E", 2),                           # CB63
    (operation, "BIT 4,H", 2),                           # CB64
    (operation, "BIT 4,L", 2),                           # CB65
    (operation, "BIT 4,(HL)", 2),                        # CB66
    (operation, "BIT 4,A", 2),                           # CB67
    (operation, "BIT 5,B", 2),                           # CB68
    (operation, "BIT 5,C", 2),                           # CB69
    (operation, "BIT 5,D", 2),                           # CB6A
    (operation, "BIT 5,E", 2),                           # CB6B
    (operation, "BIT 5,H", 2),                           # CB6C
    (operation, "BIT 5,L", 2),                           # CB6D
    (operation, "BIT 5,(HL)", 2),                        # CB6E
    (operation, "BIT 5,A", 2),                           # CB6F
    (operation, "BIT 6,B", 2),                           # CB70
    (operation, "BIT 6,C", 2),                           # CB71
    (operation, "BIT 6,D", 2),                           # CB72
    (operation, "BIT 6,E", 2),                           # CB73
    (operation, "BIT 6,H", 2),                           # CB74
    (operation, "BIT 6,L", 2),                           # CB75
    (operation, "BIT 6,(HL)", 2),                        # CB76
    (operation, "BIT 6,A", 2),                           # CB77
    (operation, "BIT 7,B", 2),                           # CB78
    (operation, "BIT 7,C", 2),                           # CB79
    (operation, "BIT 7,D", 2),                           # CB7A
    (operation, "BIT 7,E", 2),                           # CB7B
    (operation, "BIT 7,H", 2),                           # CB7C
    (operation, "BIT 7,L", 2),                           # CB7D
    (operation, "BIT 7,(HL)", 2),                        # CB7E
    (operation, "BIT 7,A", 2),                           # CB7F
    (operation, "RES 0,B", 2),                           # CB80
    (operation, "RES 0,C", 2),                           # CB81
    (operation, "RES 0,D", 2),                           # CB82
    (operation, "RES 0,E", 2),                           # CB83
    (operation, "RES 0,H", 2),                           # CB84
    (operation, "RES 0,L", 2),                           # CB85
    (operation, "RES 0,(HL)", 2),                        # CB86
    (operation, "RES 0,A", 2),                           # CB87
    (operation, "RES 1,B", 2),                           # CB88
    (operation, "RES 1,C", 2),                           # CB89
    (operation, "RES 1,D", 2),                           # CB8A
    (operation, "RES 1,E", 2),                           # CB8B
    (operation, "RES 1,H", 2),                           # CB8C
    (operation, "RES 1,L", 2),                           # CB8D
    (operation, "RES 1,(HL)", 2),                        # CB8E
    (operation, "RES 1,A", 2),                           # CB8F
    (operation, "RES 2,B", 2),                           # CB90
    (operation, "RES 2,C", 2),                           # CB91
    (operation, "RES 2,D", 2),                           # CB92
    (operation, "RES 2,E", 2),                           # CB93
    (operation, "RES 2,H", 2),                           # CB94
    (operation, "RES 2,L", 2),                           # CB95
    (operation, "RES 2,(HL)", 2),                        # CB96
    (operation, "RES 2,A", 2),                           # CB97
    (operation, "RES 3,B", 2),                           # CB98
    (operation, "RES 3,C", 2),                           # CB99
    (operation, "RES 3,D", 2),                           # CB9A
    (operation, "RES 3,E", 2),                           # CB9B
    (operation, "RES 3,H", 2),                           # CB9C
    (operation, "RES 3,L", 2),                           # CB9D
    (operation, "RES 3,(HL)", 2),                        # CB9E
    (operation, "RES 3,A", 2),                           # CB9F
    (operation, "RES 4,B", 2),                           # CBA0
    (operation, "RES 4,C", 2),                           # CBA1
    (operation, "RES 4,D", 2),                           # CBA2
    (operation, "RES 4,E", 2),                           # CBA3
    (operation, "RES 4,H", 2),                           # CBA4
    (operation, "RES 4,L", 2),                           # CBA5
    (operation, "RES 4,(HL)", 2),                        # CBA6
    (operation, "RES 4,A", 2),                           # CBA7
    (operation, "RES 5,B", 2),                           # CBA8
    (operation, "RES 5,C", 2),                           # CBA9
    (operation, "RES 5,D", 2),                           # CBAA
    (operation, "RES 5,E", 2),                           # CBAB
    (operation, "RES 5,H", 2),                           # CBAC
    (operation, "RES 5,L", 2),                           # CBAD
    (operation, "RES 5,(HL)", 2),                        # CBAE
    (operation, "RES 5,A", 2),                           # CBAF
    (operation, "RES 6,B", 2),                           # CBB0
    (operation, "RES 6,C", 2),                           # CBB1
    (operation, "RES 6,D", 2),                           # CBB2
    (operation, "RES 6,E", 2),                           # CBB3
    (operation, "RES 6,H", 2),                           # CBB4
    (operation, "RES 6,L", 2),                           # CBB5
    (operation, "RES 6,(HL)", 2),                        # CBB6
    (operation, "RES 6,A", 2),                           # CBB7
    (operation, "RES 7,B", 2),                           # CBB8
    (operation, "RES 7,C", 2),                           # CBB9
    (operation, "RES 7,D", 2),                           # CBBA
    (operation, "RES 7,E", 2),                           # CBBB
    (operation, "RES 7,H", 2),                           # CBBC
    (operation, "RES 7,L", 2),                           # CBBD
    (operation, "RES 7,(HL)", 2),                        # CBBE
    (operation, "RES 7,A", 2),                           # CBBF
    (operation, "SET 0,B", 2),                           # CBC0
    (operation, "SET 0,C", 2),                           # CBC1
    (operation, "SET 0,D", 2),                           # CBC2
    (operation, "SET 0,E", 2),                           # CBC3
    (operation, "SET 0,H", 2),                           # CBC4
    (operation, "SET 0,L", 2),                           # CBC5
    (operation, "SET 0,(HL)", 2),                        # CBC6
    (operation, "SET 0,A", 2),                           # CBC7
    (operation, "SET 1,B", 2),                           # CBC8
    (operation, "SET 1,C", 2),                           # CBC9
    (operation, "SET 1,D", 2),                           # CBCA
    (operation, "SET 1,E", 2),                           # CBCB
    (operation, "SET 1,H", 2),                           # CBCC
    (operation, "SET 1,L", 2),                           # CBCD
    (operation, "SET 1,(HL)", 2),                        # CBCE
    (operation, "SET 1,A", 2),                           # CBCF
    (operation, "SET 2,B", 2),                           # CBD0
    (operation, "SET 2,C", 2),                           # CBD1
    (operation, "SET 2,D", 2),                           # CBD2
    (operation, "SET 2,E", 2),                           # CBD3
    (operation, "SET 2,H", 2),                           # CBD4
    (operation, "SET 2,L", 2),                           # CBD5
    (operation, "SET 2,(HL)", 2),                        # CBD6
    (operation, "SET 2,A", 2),                           # CBD7
    (operation, "SET 3,B", 2),                           # CBD8
    (operation, "SET 3,C", 2),                           # CBD9
    (operation, "SET 3,D", 2),                           # CBDA
    (operation, "SET 3,E", 2),                           # CBDB
    (operation, "SET 3,H", 2),                           # CBDC
    (operation, "SET 3,L", 2),                           # CBDD
    (operation, "SET 3,(HL)", 2),                        # CBDE
    (operation, "SET 3,A", 2),                           # CBDF
    (operation, "SET 4,B", 2),                           # CBE0
    (operation, "SET 4,C", 2),                           # CBE1
    (operation, "SET 4,D", 2),                           # CBE2
    (operation, "SET 4,E", 2),                           # CBE3
    (operation, "SET 4,H", 2),                           # CBE4
    (operation, "SET 4,L", 2),                           # CBE5
    (operation, "SET 4,(HL)", 2),                        # CBE6
    (operation, "SET 4,A", 2),                           # CBE7
    (operation, "SET 5,B", 2),                           # CBE8
    (operation, "SET 5,C", 2),                           # CBE9
    (operation, "SET 5,D", 2),                           # CBEA
    (operation, "SET 5,E", 2),                           # CBEB
    (operation, "SET 5,H", 2),                           # CBEC
    (operation, "SET 5,L", 2),                           # CBED
    (operation, "SET 5,(HL)", 2),                        # CBEE
    (operation, "SET 5,A", 2),                           # CBEF
    (operation, "SET 6,B", 2),                           # CBF0
    (operation, "SET 6,C", 2),                           # CBF1
    (operation, "SET 6,D", 2),                           # CBF2
    (operation, "SET 6,E", 2),                           # CBF3
    (operation, "SET 6,H", 2),                           # CBF4
    (operation, "SET 6,L", 2),                           # CBF5
    (operation, "SET 6,(HL)", 2),                        # CBF6
    (operation, "SET 6,A", 2),                           # CBF7
    (operation, "SET 7,B", 2),                           # CBF8
    (operation, "SET 7,C", 2),                           # CBF9
    (operation, "SET 7,D", 2),                           # CBFA
    (operation, "SET 7,E", 2),                           # CBFB
    (operation, "SET 7,H", 2),                           # CBFC
    (operation, "SET 7,L", 2),                           # CBFD
    (operation, "SET 7,(HL)", 2),                        # CBFE
    (operation, "SET 7,A", 2),                           # CBFF
)

AFTER_DD = (
    (defb, "", 1),                                       # DD00
    (defb, "", 1),                                       # DD01
    (defb, "", 1),                                       # DD02
    (defb, "", 1),                                       # DD03
    (defb, "", 1),                                       # DD04
    (defb, "", 1),                                       # DD05
    (defb, "", 1),                                       # DD06
    (defb, "", 1),                                       # DD07
    (defb, "", 1),                                       # DD08
    (operation, "ADD IX,BC", 2),                         # DD09
    (defb, "", 1),                                       # DD0A
    (defb, "", 1),                                       # DD0B
    (defb, "", 1),                                       # DD0C
    (defb, "", 1),                                       # DD0D
    (defb, "", 1),                                       # DD0E
    (defb, "", 1),                                       # DD0F
    (defb, "", 1),                                       # DD10
    (defb, "", 1),                                       # DD11
    (defb, "", 1),                                       # DD12
    (defb, "", 1),                                       # DD13
    (defb, "", 1),                                       # DD14
    (defb, "", 1),                                       # DD15
    (defb, "", 1),                                       # DD16
    (defb, "", 1),                                       # DD17
    (defb, "", 1),                                       # DD18
    (operation, "ADD IX,DE", 2),                         # DD19
    (defb, "", 1),                                       # DD1A
    (defb, "", 1),                                       # DD1B
    (defb, "", 1),                                       # DD1C
    (defb, "", 1),                                       # DD1D
    (defb, "", 1),                                       # DD1E
    (defb, "", 1),                                       # DD1F
    (defb, "", 1),                                       # DD20
    (word, "LD IX,{p}{n:{w}}", 4),                       # DD21
    (word, "LD ({p}{n:{w}}),IX", 4),                     # DD22
    (operation, "INC IX", 2),                            # DD23
    (operation, "INC IXh", 2),                           # DD24
    (operation, "DEC IXh", 2),                           # DD25
    (byte, "LD IXh,{p}{n:{b}}", 3),                      # DD26
    (defb, "", 1),                                       # DD27
    (defb, "", 1),                                       # DD28
    (operation, "ADD IX,IX", 2),                         # DD29
    (word, "LD IX,({p}{n:{w}})", 4),                     # DD2A
    (operation, "DEC IX", 2),                            # DD2B
    (operation, "INC IXl", 2),                           # DD2C
    (operation, "DEC IXl", 2),                           # DD2D
    (byte, "LD IXl,{p}{n:{b}}", 3),                      # DD2E
    (defb, "", 1),                                       # DD2F
    (defb, "", 1),                                       # DD30
    (defb, "", 1),                                       # DD31
    (defb, "", 1),                                       # DD32
    (defb, "", 1),                                       # DD33
    (offset, "INC (IX{s}{p}{d:{b}})", 3),                # DD34
    (offset, "DEC (IX{s}{p}{d:{b}})", 3),                # DD35
    (offset_byte, "LD (IX{s}{p}{d:{b}}),{p}{n:{b}}", 4), # DD36
    (defb, "", 1),                                       # DD37
    (defb, "", 1),                                       # DD38
    (operation, "ADD IX,SP", 2),                         # DD39
    (defb, "", 1),                                       # DD3A
    (defb, "", 1),                                       # DD3B
    (defb, "", 1),                                       # DD3C
    (defb, "", 1),                                       # DD3D
    (defb, "", 1),                                       # DD3E
    (defb, "", 1),                                       # DD3F
    (defb, "", 1),                                       # DD40
    (defb, "", 1),                                       # DD41
    (defb, "", 1),                                       # DD42
    (defb, "", 1),                                       # DD43
    (operation, "LD B,IXh", 2),                          # DD44
    (operation, "LD B,IXl", 2),                          # DD45
    (offset, "LD B,(IX{s}{p}{d:{b}})", 3),               # DD46
    (defb, "", 1),                                       # DD47
    (defb, "", 1),                                       # DD48
    (defb, "", 1),                                       # DD49
    (defb, "", 1),                                       # DD4A
    (defb, "", 1),                                       # DD4B
    (operation, "LD C,IXh", 2),                          # DD4C
    (operation, "LD C,IXl", 2),                          # DD4D
    (offset, "LD C,(IX{s}{p}{d:{b}})", 3),               # DD4E
    (defb, "", 1),                                       # DD4F
    (defb, "", 1),                                       # DD50
    (defb, "", 1),                                       # DD51
    (defb, "", 1),                                       # DD52
    (defb, "", 1),                                       # DD53
    (operation, "LD D,IXh", 2),                          # DD54
    (operation, "LD D,IXl", 2),                          # DD55
    (offset, "LD D,(IX{s}{p}{d:{b}})", 3),               # DD56
    (defb, "", 1),                                       # DD57
    (defb, "", 1),                                       # DD58
    (defb, "", 1),                                       # DD59
    (defb, "", 1),                                       # DD5A
    (defb, "", 1),                                       # DD5B
    (operation, "LD E,IXh", 2),                          # DD5C
    (operation, "LD E,IXl", 2),                          # DD5D
    (offset, "LD E,(IX{s}{p}{d:{b}})", 3),               # DD5E
    (defb, "", 1),                                       # DD5F
    (operation, "LD IXh,B", 2),                          # DD60
    (operation, "LD IXh,C", 2),                          # DD61
    (operation, "LD IXh,D", 2),                          # DD62
    (operation, "LD IXh,E", 2),                          # DD63
    (operation, "LD IXh,IXh", 2),                        # DD64
    (operation, "LD IXh,IXl", 2),                        # DD65
    (offset, "LD H,(IX{s}{p}{d:{b}})", 3),               # DD66
    (operation, "LD IXh,A", 2),                          # DD67
    (operation, "LD IXl,B", 2),                          # DD68
    (operation, "LD IXl,C", 2),                          # DD69
    (operation, "LD IXl,D", 2),                          # DD6A
    (operation, "LD IXl,E", 2),                          # DD6B
    (operation, "LD IXl,IXh", 2),                        # DD6C
    (operation, "LD IXl,IXl", 2),                        # DD6D
    (offset, "LD L,(IX{s}{p}{d:{b}})", 3),               # DD6E
    (operation, "LD IXl,A", 2),                          # DD6F
    (offset, "LD (IX{s}{p}{d:{b}}),B", 3),               # DD70
    (offset, "LD (IX{s}{p}{d:{b}}),C", 3),               # DD71
    (offset, "LD (IX{s}{p}{d:{b}}),D", 3),               # DD72
    (offset, "LD (IX{s}{p}{d:{b}}),E", 3),               # DD73
    (offset, "LD (IX{s}{p}{d:{b}}),H", 3),               # DD74
    (offset, "LD (IX{s}{p}{d:{b}}),L", 3),               # DD75
    (defb, "", 1),                                       # DD76
    (offset, "LD (IX{s}{p}{d:{b}}),A", 3),               # DD77
    (defb, "", 1),                                       # DD78
    (defb, "", 1),                                       # DD79
    (defb, "", 1),                                       # DD7A
    (defb, "", 1),                                       # DD7B
    (operation, "LD A,IXh", 2),                          # DD7C
    (operation, "LD A,IXl", 2),                          # DD7D
    (offset, "LD A,(IX{s}{p}{d:{b}})", 3),               # DD7E
    (defb, "", 1),                                       # DD7F
    (defb, "", 1),                                       # DD80
    (defb, "", 1),                                       # DD81
    (defb, "", 1),                                       # DD82
    (defb, "", 1),                                       # DD83
    (operation, "ADD A,IXh", 2),                         # DD84
    (operation, "ADD A,IXl", 2),                         # DD85
    (offset, "ADD A,(IX{s}{p}{d:{b}})", 3),              # DD86
    (defb, "", 1),                                       # DD87
    (defb, "", 1),                                       # DD88
    (defb, "", 1),                                       # DD89
    (defb, "", 1),                                       # DD8A
    (defb, "", 1),                                       # DD8B
    (operation, "ADC A,IXh", 2),                         # DD8C
    (operation, "ADC A,IXl", 2),                         # DD8D
    (offset, "ADC A,(IX{s}{p}{d:{b}})", 3),              # DD8E
    (defb, "", 1),                                       # DD8F
    (defb, "", 1),                                       # DD90
    (defb, "", 1),                                       # DD91
    (defb, "", 1),                                       # DD92
    (defb, "", 1),                                       # DD93
    (operation, "SUB IXh", 2),                           # DD94
    (operation, "SUB IXl", 2),                           # DD95
    (offset, "SUB (IX{s}{p}{d:{b}})", 3),                # DD96
    (defb, "", 1),                                       # DD97
    (defb, "", 1),                                       # DD98
    (defb, "", 1),                                       # DD99
    (defb, "", 1),                                       # DD9A
    (defb, "", 1),                                       # DD9B
    (operation, "SBC A,IXh", 2),                         # DD9C
    (operation, "SBC A,IXl", 2),                         # DD9D
    (offset, "SBC A,(IX{s}{p}{d:{b}})", 3),              # DD9E
    (defb, "", 1),                                       # DD9F
    (defb, "", 1),                                       # DDA0
    (defb, "", 1),                                       # DDA1
    (defb, "", 1),                                       # DDA2
    (defb, "", 1),                                       # DDA3
    (operation, "AND IXh", 2),                           # DDA4
    (operation, "AND IXl", 2),                           # DDA5
    (offset, "AND (IX{s}{p}{d:{b}})", 3),                # DDA6
    (defb, "", 1),                                       # DDA7
    (defb, "", 1),                                       # DDA8
    (defb, "", 1),                                       # DDA9
    (defb, "", 1),                                       # DDAA
    (defb, "", 1),                                       # DDAB
    (operation, "XOR IXh", 2),                           # DDAC
    (operation, "XOR IXl", 2),                           # DDAD
    (offset, "XOR (IX{s}{p}{d:{b}})", 3),                # DDAE
    (defb, "", 1),                                       # DDAF
    (defb, "", 1),                                       # DDB0
    (defb, "", 1),                                       # DDB1
    (defb, "", 1),                                       # DDB2
    (defb, "", 1),                                       # DDB3
    (operation, "OR IXh", 2),                            # DDB4
    (operation, "OR IXl", 2),                            # DDB5
    (offset, "OR (IX{s}{p}{d:{b}})", 3),                 # DDB6
    (defb, "", 1),                                       # DDB7
    (defb, "", 1),                                       # DDB8
    (defb, "", 1),                                       # DDB9
    (defb, "", 1),                                       # DDBA
    (defb, "", 1),                                       # DDBB
    (operation, "CP IXh", 2),                            # DDBC
    (operation, "CP IXl", 2),                            # DDBD
    (offset, "CP (IX{s}{p}{d:{b}})", 3),                 # DDBE
    (defb, "", 1),                                       # DDBF
    (defb, "", 1),                                       # DDC0
    (defb, "", 1),                                       # DDC1
    (defb, "", 1),                                       # DDC2
    (defb, "", 1),                                       # DDC3
    (defb, "", 1),                                       # DDC4
    (defb, "", 1),                                       # DDC5
    (defb, "", 1),                                       # DDC6
    (defb, "", 1),                                       # DDC7
    (defb, "", 1),                                       # DDC8
    (defb, "", 1),                                       # DDC9
    (defb, "", 1),                                       # DDCA
    (None, "", 0),                                       # DDCB
    (defb, "", 1),                                       # DDCC
    (defb, "", 1),                                       # DDCD
    (defb, "", 1),                                       # DDCE
    (defb, "", 1),                                       # DDCF
    (defb, "", 1),                                       # DDD0
    (defb, "", 1),                                       # DDD1
    (defb, "", 1),                                       # DDD2
    (defb, "", 1),                                       # DDD3
    (defb, "", 1),                                       # DDD4
    (defb, "", 1),                                       # DDD5
    (defb, "", 1),                                       # DDD6
    (defb, "", 1),                                       # DDD7
    (defb, "", 1),                                       # DDD8
    (defb, "", 1),                                       # DDD9
    (defb, "", 1),                                       # DDDA
    (defb, "", 1),                                       # DDDB
    (defb, "", 1),                                       # DDDC
    (defb, "", 1),                                       # DDDD
    (defb, "", 1),                                       # DDDE
    (defb, "", 1),                                       # DDDF
    (defb, "", 1),                                       # DDE0
    (operation, "POP IX", 2),                            # DDE1
    (defb, "", 1),                                       # DDE2
    (operation, "EX (SP),IX", 2),                        # DDE3
    (defb, "", 1),                                       # DDE4
    (operation, "PUSH IX", 2),                           # DDE5
    (defb, "", 1),                                       # DDE6
    (defb, "", 1),                                       # DDE7
    (defb, "", 1),                                       # DDE8
    (operation, "JP (IX)", 2),                           # DDE9
    (defb, "", 1),                                       # DDEA
    (defb, "", 1),                                       # DDEB
    (defb, "", 1),                                       # DDEC
    (defb, "", 1),                                       # DDED
    (defb, "", 1),                                       # DDEE
    (defb, "", 1),                                       # DDEF
    (defb, "", 1),                                       # DDF0
    (defb, "", 1),                                       # DDF1
    (defb, "", 1),                                       # DDF2
    (defb, "", 1),                                       # DDF3
    (defb, "", 1),                                       # DDF4
    (defb, "", 1),                                       # DDF5
    (defb, "", 1),                                       # DDF6
    (defb, "", 1),                                       # DDF7
    (defb, "", 1),                                       # DDF8
    (operation, "LD SP,IX", 2),                          # DDF9
    (defb, "", 1),                                       # DDFA
    (defb, "", 1),                                       # DDFB
    (defb, "", 1),                                       # DDFC
    (defb, "", 1),                                       # DDFD
    (defb, "", 1),                                       # DDFE
    (defb, "", 1),                                       # DDFF
)

AFTER_ED = (
    (defb, "", 2),                                       # ED00
    (defb, "", 2),                                       # ED01
    (defb, "", 2),                                       # ED02
    (defb, "", 2),                                       # ED03
    (defb, "", 2),                                       # ED04
    (defb, "", 2),                                       # ED05
    (defb, "", 2),                                       # ED06
    (defb, "", 2),                                       # ED07
    (defb, "", 2),                                       # ED08
    (defb, "", 2),                                       # ED09
    (defb, "", 2),                                       # ED0A
    (defb, "", 2),                                       # ED0B
    (defb, "", 2),                                       # ED0C
    (defb, "", 2),                                       # ED0D
    (defb, "", 2),                                       # ED0E
    (defb, "", 2),                                       # ED0F
    (defb, "", 2),                                       # ED10
    (defb, "", 2),                                       # ED11
    (defb, "", 2),                                       # ED12
    (defb, "", 2),                                       # ED13
    (defb, "", 2),                                       # ED14
    (defb, "", 2),                                       # ED15
    (defb, "", 2),                                       # ED16
    (defb, "", 2),                                       # ED17
    (defb, "", 2),                                       # ED18
    (defb, "", 2),                                       # ED19
    (defb, "", 2),                                       # ED1A
    (defb, "", 2),                                       # ED1B
    (defb, "", 2),                                       # ED1C
    (defb, "", 2),                                       # ED1D
    (defb, "", 2),                                       # ED1E
    (defb, "", 2),                                       # ED1F
    (defb, "", 2),                                       # ED20
    (defb, "", 2),                                       # ED21
    (defb, "", 2),                                       # ED22
    (defb, "", 2),                                       # ED23
    (defb, "", 2),                                       # ED24
    (defb, "", 2),                                       # ED25
    (defb, "", 2),                                       # ED26
    (defb, "", 2),                                       # ED27
    (defb, "", 2),                                       # ED28
    (defb, "", 2),                                       # ED29
    (defb, "", 2),                                       # ED2A
    (defb, "", 2),                                       # ED2B
    (defb, "", 2),                                       # ED2C
    (defb, "", 2),                                       # ED2D
    (defb, "", 2),                                       # ED2E
    (defb, "", 2),                                       # ED2F
    (defb, "", 2),                                       # ED30
    (defb, "", 2),                                       # ED31
    (defb, "", 2),                                       # ED32
    (defb, "", 2),                                       # ED33
    (defb, "", 2),                                       # ED34
    (defb, "", 2),                                       # ED35
    (defb, "", 2),                                       # ED36
    (defb, "", 2),                                       # ED37
    (defb, "", 2),                                       # ED38
    (defb, "", 2),                                       # ED39
    (defb, "", 2),                                       # ED3A
    (defb, "", 2),                                       # ED3B
    (defb, "", 2),                                       # ED3C
    (defb, "", 2),                                       # ED3D
    (defb, "", 2),                                       # ED3E
    (defb, "", 2),                                       # ED3F
    (operation, "IN B,(C)", 2),                          # ED40
    (operation, "OUT (C),B", 2),                         # ED41
    (operation, "SBC HL,BC", 2),                         # ED42
    (word, "LD ({p}{n:{w}}),BC", 4),                     # ED43
    (operation, "NEG", 2),                               # ED44
    (operation, "RETN", 2),                              # ED45
    (operation, "IM 0", 2),                              # ED46
    (operation, "LD I,A", 2),                            # ED47
    (operation, "IN C,(C)", 2),                          # ED48
    (operation, "OUT (C),C", 2),                         # ED49
    (operation, "ADC HL,BC", 2),                         # ED4A
    (word, "LD BC,({p}{n:{w}})", 4),                     # ED4B
    (operation, "NEG", 2),                               # ED4C
    (operation, "RETI", 2),                              # ED4D
    (operation, "IM 0", 2),                              # ED4E
    (operation, "LD R,A", 2),                            # ED4F
    (operation, "IN D,(C)", 2),                          # ED50
    (operation, "OUT (C),D", 2),                         # ED51
    (operation, "SBC HL,DE", 2),                         # ED52
    (word, "LD ({p}{n:{w}}),DE", 4),                     # ED53
    (operation, "NEG", 2),                               # ED54
    (operation, "RETN", 2),                              # ED55
    (operation, "IM 1", 2),                              # ED56
    (operation, "LD A,I", 2),                            # ED57
    (operation, "IN E,(C)", 2),                          # ED58
    (operation, "OUT (C),E", 2),                         # ED59
    (operation, "ADC HL,DE", 2),                         # ED5A
    (word, "LD DE,({p}{n:{w}})", 4),                     # ED5B
    (operation, "NEG", 2),                               # ED5C
    (operation, "RETN", 2),                              # ED5D
    (operation, "IM 2", 2),                              # ED5E
    (operation, "LD A,R", 2),                            # ED5F
    (operation, "IN H,(C)", 2),                          # ED60
    (operation, "OUT (C),H", 2),                         # ED61
    (operation, "SBC HL,HL", 2),                         # ED62
    (word, "LD ({p}{n:{w}}),HL", 4),                     # ED63
    (operation, "NEG", 2),                               # ED64
    (operation, "RETN", 2),                              # ED65
    (operation, "IM 0", 2),                              # ED66
    (operation, "RRD", 2),                               # ED67
    (operation, "IN L,(C)", 2),                          # ED68
    (operation, "OUT (C),L", 2),                         # ED69
    (operation, "ADC HL,HL", 2),                         # ED6A
    (word, "LD HL,({p}{n:{w}})", 4),                     # ED6B
    (operation, "NEG", 2),                               # ED6C
    (operation, "RETN", 2),                              # ED6D
    (operation, "IM 0", 2),                              # ED6E
    (operation, "RLD", 2),                               # ED6F
    (operation, "IN F,(C)", 2),                          # ED70
    (operation, "OUT (C),0", 2),                         # ED71
    (operation, "SBC HL,SP", 2),                         # ED72
    (word, "LD ({p}{n:{w}}),SP", 4),                     # ED73
    (operation, "NEG", 2),                               # ED74
    (operation, "RETN", 2),                              # ED75
    (operation, "IM 1", 2),                              # ED76
    (defb, "", 2),                                       # ED77
    (operation, "IN A,(C)", 2),                          # ED78
    (operation, "OUT (C),A", 2),                         # ED79
    (operation, "ADC HL,SP", 2),                         # ED7A
    (word, "LD SP,({p}{n:{w}})", 4),                     # ED7B
    (operation, "NEG", 2),                               # ED7C
    (operation, "RETN", 2),                              # ED7D
    (operation, "IM 2", 2),                              # ED7E
    (defb, "", 2),                                       # ED7F
    (defb, "", 2),                                       # ED80
    (defb, "", 2),                                       # ED81
    (defb, "", 2),                                       # ED82
    (defb, "", 2),                                       # ED83
    (defb, "", 2),                                       # ED84
    (defb, "", 2),                                       # ED85
    (defb, "", 2),                                       # ED86
    (defb, "", 2),                                       # ED87
    (defb, "", 2),                                       # ED88
    (defb, "", 2),                                       # ED89
    (defb, "", 2),                                       # ED8A
    (defb, "", 2),                                       # ED8B
    (defb, "", 2),                                       # ED8C
    (defb, "", 2),                                       # ED8D
    (defb, "", 2),                                       # ED8E
    (defb, "", 2),                                       # ED8F
    (defb, "", 2),                                       # ED90
    (defb, "", 2),                                       # ED91
    (defb, "", 2),                                       # ED92
    (defb, "", 2),                                       # ED93
    (defb, "", 2),                                       # ED94
    (defb, "", 2),                                       # ED95
    (defb, "", 2),                                       # ED96
    (defb, "", 2),                                       # ED97
    (defb, "", 2),                                       # ED98
    (defb, "", 2),                                       # ED99
    (defb, "", 2),                                       # ED9A
    (defb, "", 2),                                       # ED9B
    (defb, "", 2),                                       # ED9C
    (defb, "", 2),                                       # ED9D
    (defb, "", 2),                                       # ED9E
    (defb, "", 2),                                       # ED9F
    (operation, "LDI", 2),                               # EDA0
    (operation, "CPI", 2),                               # EDA1
    (operation, "INI", 2),                               # EDA2
    (operation, "OUTI", 2),                              # EDA3
    (defb, "", 2),                                       # EDA4
    (defb, "", 2),                                       # EDA5
    (defb, "", 2),                                       # EDA6
    (defb, "", 2),                                       # EDA7
    (operation, "LDD", 2),                               # EDA8
    (operation, "CPD", 2),                               # EDA9
    (operation, "IND", 2),                               # EDAA
    (operation, "OUTD", 2),                              # EDAB
    (defb, "", 2),                                       # EDAC
    (defb, "", 2),                                       # EDAD
    (defb, "", 2),                                       # EDAE
    (defb, "", 2),                                       # EDAF
    (operation, "LDIR", 2),                              # EDB0
    (operation, "CPIR", 2),                              # EDB1
    (operation, "INIR", 2),                              # EDB2
    (operation, "OTIR", 2),                              # EDB3
    (defb, "", 2),                                       # EDB4
    (defb, "", 2),                                       # EDB5
    (defb, "", 2),                                       # EDB6
    (defb, "", 2),                                       # EDB7
    (operation, "LDDR", 2),                              # EDB8
    (operation, "CPDR", 2),                              # EDB9
    (operation, "INDR", 2),                              # EDBA
    (operation, "OTDR", 2),                              # EDBB
    (defb, "", 2),                                       # EDBC
    (defb, "", 2),                                       # EDBD
    (defb, "", 2),                                       # EDBE
    (defb, "", 2),                                       # EDBF
    (defb, "", 2),                                       # EDC0
    (defb, "", 2),                                       # EDC1
    (defb, "", 2),                                       # EDC2
    (defb, "", 2),                                       # EDC3
    (defb, "", 2),                                       # EDC4
    (defb, "", 2),                                       # EDC5
    (defb, "", 2),                                       # EDC6
    (defb, "", 2),                                       # EDC7
    (defb, "", 2),                                       # EDC8
    (defb, "", 2),                                       # EDC9
    (defb, "", 2),                                       # EDCA
    (defb, "", 2),                                       # EDCB
    (defb, "", 2),                                       # EDCC
    (defb, "", 2),                                       # EDCD
    (defb, "", 2),                                       # EDCE
    (defb, "", 2),                                       # EDCF
    (defb, "", 2),                                       # EDD0
    (defb, "", 2),                                       # EDD1
    (defb, "", 2),                                       # EDD2
    (defb, "", 2),                                       # EDD3
    (defb, "", 2),                                       # EDD4
    (defb, "", 2),                                       # EDD5
    (defb, "", 2),                                       # EDD6
    (defb, "", 2),                                       # EDD7
    (defb, "", 2),                                       # EDD8
    (defb, "", 2),                                       # EDD9
    (defb, "", 2),                                       # EDDA
    (defb, "", 2),                                       # EDDB
    (defb, "", 2),                                       # EDDC
    (defb, "", 2),                                       # EDDD
    (defb, "", 2),                                       # EDDE
    (defb, "", 2),                                       # EDDF
    (defb, "", 2),                                       # EDE0
    (defb, "", 2),                                       # EDE1
    (defb, "", 2),                                       # EDE2
    (defb, "", 2),                                       # EDE3
    (defb, "", 2),                                       # EDE4
    (defb, "", 2),                                       # EDE5
    (defb, "", 2),                                       # EDE6
    (defb, "", 2),                                       # EDE7
    (defb, "", 2),                                       # EDE8
    (defb, "", 2),                                       # EDE9
    (defb, "", 2),                                       # EDEA
    (defb, "", 2),                                       # EDEB
    (defb, "", 2),                                       # EDEC
    (defb, "", 2),                                       # EDED
    (defb, "", 2),                                       # EDEE
    (defb, "", 2),                                       # EDEF
    (defb, "", 2),                                       # EDF0
    (defb, "", 2),                                       # EDF1
    (defb, "", 2),                                       # EDF2
    (defb, "", 2),                                       # EDF3
    (defb, "", 2),                                       # EDF4
    (defb, "", 2),                                       # EDF5
    (defb, "", 2),                                       # EDF6
    (defb, "", 2),                                       # EDF7
    (defb, "", 2),                                       # EDF8
    (defb, "", 2),                                       # EDF9
    (defb, "", 2),                                       # EDFA
    (defb, "", 2),                                       # EDFB
    (defb, "", 2),                                       # EDFC
    (defb, "", 2),                                       # EDFD
    (defb, "", 2),                                       # EDFE
    (defb, "", 2),                                       # EDFF
)

AFTER_FD = (
    (defb, "", 1),                                       # FD00
    (defb, "", 1),                                       # FD01
    (defb, "", 1),                                       # FD02
    (defb, "", 1),                                       # FD03
    (defb, "", 1),                                       # FD04
    (defb, "", 1),                                       # FD05
    (defb, "", 1),                                       # FD06
    (defb, "", 1),                                       # FD07
    (defb, "", 1),                                       # FD08
    (operation, "ADD IY,BC", 2),                         # FD09
    (defb, "", 1),                                       # FD0A
    (defb, "", 1),                                       # FD0B
    (defb, "", 1),                                       # FD0C
    (defb, "", 1),                                       # FD0D
    (defb, "", 1),                                       # FD0E
    (defb, "", 1),                                       # FD0F
    (defb, "", 1),                                       # FD10
    (defb, "", 1),                                       # FD11
    (defb, "", 1),                                       # FD12
    (defb, "", 1),                                       # FD13
    (defb, "", 1),                                       # FD14
    (defb, "", 1),                                       # FD15
    (defb, "", 1),                                       # FD16
    (defb, "", 1),                                       # FD17
    (defb, "", 1),                                       # FD18
    (operation, "ADD IY,DE", 2),                         # FD19
    (defb, "", 1),                                       # FD1A
    (defb, "", 1),                                       # FD1B
    (defb, "", 1),                                       # FD1C
    (defb, "", 1),                                       # FD1D
    (defb, "", 1),                                       # FD1E
    (defb, "", 1),                                       # FD1F
    (defb, "", 1),                                       # FD20
    (word, "LD IY,{p}{n:{w}}", 4),                       # FD21
    (word, "LD ({p}{n:{w}}),IY", 4),                     # FD22
    (operation, "INC IY", 2),                            # FD23
    (operation, "INC IYh", 2),                           # FD24
    (operation, "DEC IYh", 2),                           # FD25
    (byte, "LD IYh,{p}{n:{b}}", 3),                      # FD26
    (defb, "", 1),                                       # FD27
    (defb, "", 1),                                       # FD28
    (operation, "ADD IY,IY", 2),                         # FD29
    (word, "LD IY,({p}{n:{w}})", 4),                     # FD2A
    (operation, "DEC IY", 2),                            # FD2B
    (operation, "INC IYl", 2),                           # FD2C
    (operation, "DEC IYl", 2),                           # FD2D
    (byte, "LD IYl,{p}{n:{b}}", 3),                      # FD2E
    (defb, "", 1),                                       # FD2F
    (defb, "", 1),                                       # FD30
    (defb, "", 1),                                       # FD31
    (defb, "", 1),                                       # FD32
    (defb, "", 1),                                       # FD33
    (offset, "INC (IY{s}{p}{d:{b}})", 3),                # FD34
    (offset, "DEC (IY{s}{p}{d:{b}})", 3),                # FD35
    (offset_byte, "LD (IY{s}{p}{d:{b}}),{p}{n:{b}}", 4), # FD36
    (defb, "", 1),                                       # FD37
    (defb, "", 1),                                       # FD38
    (operation, "ADD IY,SP", 2),                         # FD39
    (defb, "", 1),                                       # FD3A
    (defb, "", 1),                                       # FD3B
    (defb, "", 1),                                       # FD3C
    (defb, "", 1),                                       # FD3D
    (defb, "", 1),                                       # FD3E
    (defb, "", 1),                                       # FD3F
    (defb, "", 1),                                       # FD40
    (defb, "", 1),                                       # FD41
    (defb, "", 1),                                       # FD42
    (defb, "", 1),                                       # FD43
    (operation, "LD B,IYh", 2),                          # FD44
    (operation, "LD B,IYl", 2),                          # FD45
    (offset, "LD B,(IY{s}{p}{d:{b}})", 3),               # FD46
    (defb, "", 1),                                       # FD47
    (defb, "", 1),                                       # FD48
    (defb, "", 1),                                       # FD49
    (defb, "", 1),                                       # FD4A
    (defb, "", 1),                                       # FD4B
    (operation, "LD C,IYh", 2),                          # FD4C
    (operation, "LD C,IYl", 2),                          # FD4D
    (offset, "LD C,(IY{s}{p}{d:{b}})", 3),               # FD4E
    (defb, "", 1),                                       # FD4F
    (defb, "", 1),                                       # FD50
    (defb, "", 1),                                       # FD51
    (defb, "", 1),                                       # FD52
    (defb, "", 1),                                       # FD53
    (operation, "LD D,IYh", 2),                          # FD54
    (operation, "LD D,IYl", 2),                          # FD55
    (offset, "LD D,(IY{s}{p}{d:{b}})", 3),               # FD56
    (defb, "", 1),                                       # FD57
    (defb, "", 1),                                       # FD58
    (defb, "", 1),                                       # FD59
    (defb, "", 1),                                       # FD5A
    (defb, "", 1),                                       # FD5B
    (operation, "LD E,IYh", 2),                          # FD5C
    (operation, "LD E,IYl", 2),                          # FD5D
    (offset, "LD E,(IY{s}{p}{d:{b}})", 3),               # FD5E
    (defb, "", 1),                                       # FD5F
    (operation, "LD IYh,B", 2),                          # FD60
    (operation, "LD IYh,C", 2),                          # FD61
    (operation, "LD IYh,D", 2),                          # FD62
    (operation, "LD IYh,E", 2),                          # FD63
    (operation, "LD IYh,IYh", 2),                        # FD64
    (operation, "LD IYh,IYl", 2),                        # FD65
    (offset, "LD H,(IY{s}{p}{d:{b}})", 3),               # FD66
    (operation, "LD IYh,A", 2),                          # FD67
    (operation, "LD IYl,B", 2),                          # FD68
    (operation, "LD IYl,C", 2),                          # FD69
    (operation, "LD IYl,D", 2),                          # FD6A
    (operation, "LD IYl,E", 2),                          # FD6B
    (operation, "LD IYl,IYh", 2),                        # FD6C
    (operation, "LD IYl,IYl", 2),                        # FD6D
    (offset, "LD L,(IY{s}{p}{d:{b}})", 3),               # FD6E
    (operation, "LD IYl,A", 2),                          # FD6F
    (offset, "LD (IY{s}{p}{d:{b}}),B", 3),               # FD70
    (offset, "LD (IY{s}{p}{d:{b}}),C", 3),               # FD71
    (offset, "LD (IY{s}{p}{d:{b}}),D", 3),               # FD72
    (offset, "LD (IY{s}{p}{d:{b}}),E", 3),               # FD73
    (offset, "LD (IY{s}{p}{d:{b}}),H", 3),               # FD74
    (offset, "LD (IY{s}{p}{d:{b}}),L", 3),               # FD75
    (defb, "", 1),                                       # FD76
    (offset, "LD (IY{s}{p}{d:{b}}),A", 3),               # FD77
    (defb, "", 1),                                       # FD78
    (defb, "", 1),                                       # FD79
    (defb, "", 1),                                       # FD7A
    (defb, "", 1),                                       # FD7B
    (operation, "LD A,IYh", 2),                          # FD7C
    (operation, "LD A,IYl", 2),                          # FD7D
    (offset, "LD A,(IY{s}{p}{d:{b}})", 3),               # FD7E
    (defb, "", 1),                                       # FD7F
    (defb, "", 1),                                       # FD80
    (defb, "", 1),                                       # FD81
    (defb, "", 1),                                       # FD82
    (defb, "", 1),                                       # FD83
    (operation, "ADD A,IYh", 2),                         # FD84
    (operation, "ADD A,IYl", 2),                         # FD85
    (offset, "ADD A,(IY{s}{p}{d:{b}})", 3),              # FD86
    (defb, "", 1),                                       # FD87
    (defb, "", 1),                                       # FD88
    (defb, "", 1),                                       # FD89
    (defb, "", 1),                                       # FD8A
    (defb, "", 1),                                       # FD8B
    (operation, "ADC A,IYh", 2),                         # FD8C
    (operation, "ADC A,IYl", 2),                         # FD8D
    (offset, "ADC A,(IY{s}{p}{d:{b}})", 3),              # FD8E
    (defb, "", 1),                                       # FD8F
    (defb, "", 1),                                       # FD90
    (defb, "", 1),                                       # FD91
    (defb, "", 1),                                       # FD92
    (defb, "", 1),                                       # FD93
    (operation, "SUB IYh", 2),                           # FD94
    (operation, "SUB IYl", 2),                           # FD95
    (offset, "SUB (IY{s}{p}{d:{b}})", 3),                # FD96
    (defb, "", 1),                                       # FD97
    (defb, "", 1),                                       # FD98
    (defb, "", 1),                                       # FD99
    (defb, "", 1),                                       # FD9A
    (defb, "", 1),                                       # FD9B
    (operation, "SBC A,IYh", 2),                         # FD9C
    (operation, "SBC A,IYl", 2),                         # FD9D
    (offset, "SBC A,(IY{s}{p}{d:{b}})", 3),              # FD9E
    (defb, "", 1),                                       # FD9F
    (defb, "", 1),                                       # FDA0
    (defb, "", 1),                                       # FDA1
    (defb, "", 1),                                       # FDA2
    (defb, "", 1),                                       # FDA3
    (operation, "AND IYh", 2),                           # FDA4
    (operation, "AND IYl", 2),                           # FDA5
    (offset, "AND (IY{s}{p}{d:{b}})", 3),                # FDA6
    (defb, "", 1),                                       # FDA7
    (defb, "", 1),                                       # FDA8
    (defb, "", 1),                                       # FDA9
    (defb, "", 1),                                       # FDAA
    (defb, "", 1),                                       # FDAB
    (operation, "XOR IYh", 2),                           # FDAC
    (operation, "XOR IYl", 2),                           # FDAD
    (offset, "XOR (IY{s}{p}{d:{b}})", 3),                # FDAE
    (defb, "", 1),                                       # FDAF
    (defb, "", 1),                                       # FDB0
    (defb, "", 1),                                       # FDB1
    (defb, "", 1),                                       # FDB2
    (defb, "", 1),                                       # FDB3
    (operation, "OR IYh", 2),                            # FDB4
    (operation, "OR IYl", 2),                            # FDB5
    (offset, "OR (IY{s}{p}{d:{b}})", 3),                 # FDB6
    (defb, "", 1),                                       # FDB7
    (defb, "", 1),                                       # FDB8
    (defb, "", 1),                                       # FDB9
    (defb, "", 1),                                       # FDBA
    (defb, "", 1),                                       # FDBB
    (operation, "CP IYh", 2),                            # FDBC
    (operation, "CP IYl", 2),                            # FDBD
    (offset, "CP (IY{s}{p}{d:{b}})", 3),                 # FDBE
    (defb, "", 1),                                       # FDBF
    (defb, "", 1),                                       # FDC0
    (defb, "", 1),                                       # FDC1
    (defb, "", 1),                                       # FDC2
    (defb, "", 1),                                       # FDC3
    (defb, "", 1),                                       # FDC4
    (defb, "", 1),                                       # FDC5
    (defb, "", 1),                                       # FDC6
    (defb, "", 1),                                       # FDC7
    (defb, "", 1),                                       # FDC8
    (defb, "", 1),                                       # FDC9
    (defb, "", 1),                                       # FDCA
    (None, "", 0),                                       # FDCB
    (defb, "", 1),                                       # FDCC
    (defb, "", 1),                                       # FDCD
    (defb, "", 1),                                       # FDCE
    (defb, "", 1),                                       # FDCF
    (defb, "", 1),                                       # FDD0
    (defb, "", 1),                                       # FDD1
    (defb, "", 1),                                       # FDD2
    (defb, "", 1),                                       # FDD3
    (defb, "", 1),                                       # FDD4
    (defb, "", 1),                                       # FDD5
    (defb, "", 1),                                       # FDD6
    (defb, "", 1),                                       # FDD7
    (defb, "", 1),                                       # FDD8
    (defb, "", 1),                                       # FDD9
    (defb, "", 1),                                       # FDDA
    (defb, "", 1),                                       # FDDB
    (defb, "", 1),                                       # FDDC
    (defb, "", 1),                                       # FDDD
    (defb, "", 1),                                       # FDDE
    (defb, "", 1),                                       # FDDF
    (defb, "", 1),                                       # FDE0
    (operation, "POP IY", 2),                            # FDE1
    (defb, "", 1),                                       # FDE2
    (operation, "EX (SP),IY", 2),                        # FDE3
    (defb, "", 1),                                       # FDE4
    (operation, "PUSH IY", 2),                           # FDE5
    (defb, "", 1),                                       # FDE6
    (defb, "", 1),                                       # FDE7
    (defb, "", 1),                                       # FDE8
    (operation, "JP (IY)", 2),                           # FDE9
    (defb, "", 1),                                       # FDEA
    (defb, "", 1),                                       # FDEB
    (defb, "", 1),                                       # FDEC
    (defb, "", 1),                                       # FDED
    (defb, "", 1),                                       # FDEE
    (defb, "", 1),                                       # FDEF
    (defb, "", 1),                                       # FDF0
    (defb, "", 1),                                       # FDF1
    (defb, "", 1),                                       # FDF2
    (defb, "", 1),                                       # FDF3
    (defb, "", 1),                                       # FDF4
    (defb, "", 1),                                       # FDF5
    (defb, "", 1),                                       # FDF6
    (defb, "", 1),                                       # FDF7
    (defb, "", 1),                                       # FDF8
    (operation, "LD SP,IY", 2),                          # FDF9
    (defb, "", 1),                                       # FDFA
    (defb, "", 1),                                       # FDFB
    (defb, "", 1),                                       # FDFC
    (defb, "", 1),                                       # FDFD
    (defb, "", 1),                                       # FDFE
    (defb, "", 1),                                       # FDFF
)

AFTER_DDCB = (
    (offset, "RLC (IX{s}{p}{d:{b}}),B", 4),              # DDCB..00
    (offset, "RLC (IX{s}{p}{d:{b}}),C", 4),              # DDCB..01
    (offset, "RLC (IX{s}{p}{d:{b}}),D", 4),              # DDCB..02
    (offset, "RLC (IX{s}{p}{d:{b}}),E", 4),              # DDCB..03
    (offset, "RLC (IX{s}{p}{d:{b}}),H", 4),              # DDCB..04
    (offset, "RLC (IX{s}{p}{d:{b}}),L", 4),              # DDCB..05
    (offset, "RLC (IX{s}{p}{d:{b}})", 4),                # DDCB..06
    (offset, "RLC (IX{s}{p}{d:{b}}),A", 4),              # DDCB..07
    (offset, "RRC (IX{s}{p}{d:{b}}),B", 4),              # DDCB..08
    (offset, "RRC (IX{s}{p}{d:{b}}),C", 4),              # DDCB..09
    (offset, "RRC (IX{s}{p}{d:{b}}),D", 4),              # DDCB..0A
    (offset, "RRC (IX{s}{p}{d:{b}}),E", 4),              # DDCB..0B
    (offset, "RRC (IX{s}{p}{d:{b}}),H", 4),              # DDCB..0C
    (offset, "RRC (IX{s}{p}{d:{b}}),L", 4),              # DDCB..0D
    (offset, "RRC (IX{s}{p}{d:{b}})", 4),                # DDCB..0E
    (offset, "RRC (IX{s}{p}{d:{b}}),A", 4),              # DDCB..0F
    (offset, "RL (IX{s}{p}{d:{b}}),B", 4),               # DDCB..10
    (offset, "RL (IX{s}{p}{d:{b}}),C", 4),               # DDCB..11
    (offset, "RL (IX{s}{p}{d:{b}}),D", 4),               # DDCB..12
    (offset, "RL (IX{s}{p}{d:{b}}),E", 4),               # DDCB..13
    (offset, "RL (IX{s}{p}{d:{b}}),H", 4),               # DDCB..14
    (offset, "RL (IX{s}{p}{d:{b}}),L", 4),               # DDCB..15
    (offset, "RL (IX{s}{p}{d:{b}})", 4),                 # DDCB..16
    (offset, "RL (IX{s}{p}{d:{b}}),A", 4),               # DDCB..17
    (offset, "RR (IX{s}{p}{d:{b}}),B", 4),               # DDCB..18
    (offset, "RR (IX{s}{p}{d:{b}}),C", 4),               # DDCB..19
    (offset, "RR (IX{s}{p}{d:{b}}),D", 4),               # DDCB..1A
    (offset, "RR (IX{s}{p}{d:{b}}),E", 4),               # DDCB..1B
    (offset, "RR (IX{s}{p}{d:{b}}),H", 4),               # DDCB..1C
    (offset, "RR (IX{s}{p}{d:{b}}),L", 4),               # DDCB..1D
    (offset, "RR (IX{s}{p}{d:{b}})", 4),                 # DDCB..1E
    (offset, "RR (IX{s}{p}{d:{b}}),A", 4),               # DDCB..1F
    (offset, "SLA (IX{s}{p}{d:{b}}),B", 4),              # DDCB..20
    (offset, "SLA (IX{s}{p}{d:{b}}),C", 4),              # DDCB..21
    (offset, "SLA (IX{s}{p}{d:{b}}),D", 4),              # DDCB..22
    (offset, "SLA (IX{s}{p}{d:{b}}),E", 4),              # DDCB..23
    (offset, "SLA (IX{s}{p}{d:{b}}),H", 4),              # DDCB..24
    (offset, "SLA (IX{s}{p}{d:{b}}),L", 4),              # DDCB..25
    (offset, "SLA (IX{s}{p}{d:{b}})", 4),                # DDCB..26
    (offset, "SLA (IX{s}{p}{d:{b}}),A", 4),              # DDCB..27
    (offset, "SRA (IX{s}{p}{d:{b}}),B", 4),              # DDCB..28
    (offset, "SRA (IX{s}{p}{d:{b}}),C", 4),              # DDCB..29
    (offset, "SRA (IX{s}{p}{d:{b}}),D", 4),              # DDCB..2A
    (offset, "SRA (IX{s}{p}{d:{b}}),E", 4),              # DDCB..2B
    (offset, "SRA (IX{s}{p}{d:{b}}),H", 4),              # DDCB..2C
    (offset, "SRA (IX{s}{p}{d:{b}}),L", 4),              # DDCB..2D
    (offset, "SRA (IX{s}{p}{d:{b}})", 4),                # DDCB..2E
    (offset, "SRA (IX{s}{p}{d:{b}}),A", 4),              # DDCB..2F
    (offset, "SLL (IX{s}{p}{d:{b}}),B", 4),              # DDCB..30
    (offset, "SLL (IX{s}{p}{d:{b}}),C", 4),              # DDCB..31
    (offset, "SLL (IX{s}{p}{d:{b}}),D", 4),              # DDCB..32
    (offset, "SLL (IX{s}{p}{d:{b}}),E", 4),              # DDCB..33
    (offset, "SLL (IX{s}{p}{d:{b}}),H", 4),              # DDCB..34
    (offset, "SLL (IX{s}{p}{d:{b}}),L", 4),              # DDCB..35
    (offset, "SLL (IX{s}{p}{d:{b}})", 4),                # DDCB..36
    (offset, "SLL (IX{s}{p}{d:{b}}),A", 4),              # DDCB..37
    (offset, "SRL (IX{s}{p}{d:{b}}),B", 4),              # DDCB..38
    (offset, "SRL (IX{s}{p}{d:{b}}),C", 4),              # DDCB..39
    (offset, "SRL (IX{s}{p}{d:{b}}),D", 4),              # DDCB..3A
    (offset, "SRL (IX{s}{p}{d:{b}}),E", 4),              # DDCB..3B
    (offset, "SRL (IX{s}{p}{d:{b}}),H", 4),              # DDCB..3C
    (offset, "SRL (IX{s}{p}{d:{b}}),L", 4),              # DDCB..3D
    (offset, "SRL (IX{s}{p}{d:{b}})", 4),                # DDCB..3E
    (offset, "SRL (IX{s}{p}{d:{b}}),A", 4),              # DDCB..3F
    (offset, "BIT 0,(IX{s}{p}{d:{b}})", 4),              # DDCB..40
    (offset, "BIT 0,(IX{s}{p}{d:{b}})", 4),              # DDCB..41
    (offset, "BIT 0,(IX{s}{p}{d:{b}})", 4),              # DDCB..42
    (offset, "BIT 0,(IX{s}{p}{d:{b}})", 4),              # DDCB..43
    (offset, "BIT 0,(IX{s}{p}{d:{b}})", 4),              # DDCB..44
    (offset, "BIT 0,(IX{s}{p}{d:{b}})", 4),              # DDCB..45
    (offset, "BIT 0,(IX{s}{p}{d:{b}})", 4),              # DDCB..46
    (offset, "BIT 0,(IX{s}{p}{d:{b}})", 4),              # DDCB..47
    (offset, "BIT 1,(IX{s}{p}{d:{b}})", 4),              # DDCB..48
    (offset, "BIT 1,(IX{s}{p}{d:{b}})", 4),              # DDCB..49
    (offset, "BIT 1,(IX{s}{p}{d:{b}})", 4),              # DDCB..4A
    (offset, "BIT 1,(IX{s}{p}{d:{b}})", 4),              # DDCB..4B
    (offset, "BIT 1,(IX{s}{p}{d:{b}})", 4),              # DDCB..4C
    (offset, "BIT 1,(IX{s}{p}{d:{b}})", 4),              # DDCB..4D
    (offset, "BIT 1,(IX{s}{p}{d:{b}})", 4),              # DDCB..4E
    (offset, "BIT 1,(IX{s}{p}{d:{b}})", 4),              # DDCB..4F
    (offset, "BIT 2,(IX{s}{p}{d:{b}})", 4),              # DDCB..50
    (offset, "BIT 2,(IX{s}{p}{d:{b}})", 4),              # DDCB..51
    (offset, "BIT 2,(IX{s}{p}{d:{b}})", 4),              # DDCB..52
    (offset, "BIT 2,(IX{s}{p}{d:{b}})", 4),              # DDCB..53
    (offset, "BIT 2,(IX{s}{p}{d:{b}})", 4),              # DDCB..54
    (offset, "BIT 2,(IX{s}{p}{d:{b}})", 4),              # DDCB..55
    (offset, "BIT 2,(IX{s}{p}{d:{b}})", 4),              # DDCB..56
    (offset, "BIT 2,(IX{s}{p}{d:{b}})", 4),              # DDCB..57
    (offset, "BIT 3,(IX{s}{p}{d:{b}})", 4),              # DDCB..58
    (offset, "BIT 3,(IX{s}{p}{d:{b}})", 4),              # DDCB..59
    (offset, "BIT 3,(IX{s}{p}{d:{b}})", 4),              # DDCB..5A
    (offset, "BIT 3,(IX{s}{p}{d:{b}})", 4),              # DDCB..5B
    (offset, "BIT 3,(IX{s}{p}{d:{b}})", 4),              # DDCB..5C
    (offset, "BIT 3,(IX{s}{p}{d:{b}})", 4),              # DDCB..5D
    (offset, "BIT 3,(IX{s}{p}{d:{b}})", 4),              # DDCB..5E
    (offset, "BIT 3,(IX{s}{p}{d:{b}})", 4),              # DDCB..5F
    (offset, "BIT 4,(IX{s}{p}{d:{b}})", 4),              # DDCB..60
    (offset, "BIT 4,(IX{s}{p}{d:{b}})", 4),              # DDCB..61
    (offset, "BIT 4,(IX{s}{p}{d:{b}})", 4),              # DDCB..62
    (offset, "BIT 4,(IX{s}{p}{d:{b}})", 4),              # DDCB..63
    (offset, "BIT 4,(IX{s}{p}{d:{b}})", 4),              # DDCB..64
    (offset, "BIT 4,(IX{s}{p}{d:{b}})", 4),              # DDCB..65
    (offset, "BIT 4,(IX{s}{p}{d:{b}})", 4),              # DDCB..66
    (offset, "BIT 4,(IX{s}{p}{d:{b}})", 4),              # DDCB..67
    (offset, "BIT 5,(IX{s}{p}{d:{b}})", 4),              # DDCB..68
    (offset, "BIT 5,(IX{s}{p}{d:{b}})", 4),              # DDCB..69
    (offset, "BIT 5,(IX{s}{p}{d:{b}})", 4),              # DDCB..6A
    (offset, "BIT 5,(IX{s}{p}{d:{b}})", 4),              # DDCB..6B
    (offset, "BIT 5,(IX{s}{p}{d:{b}})", 4),              # DDCB..6C
    (offset, "BIT 5,(IX{s}{p}{d:{b}})", 4),              # DDCB..6D
    (offset, "BIT 5,(IX{s}{p}{d:{b}})", 4),              # DDCB..6E
    (offset, "BIT 5,(IX{s}{p}{d:{b}})", 4),              # DDCB..6F
    (offset, "BIT 6,(IX{s}{p}{d:{b}})", 4),              # DDCB..70
    (offset, "BIT 6,(IX{s}{p}{d:{b}})", 4),              # DDCB..71
    (offset, "BIT 6,(IX{s}{p}{d:{b}})", 4),              # DDCB..72
    (offset, "BIT 6,(IX{s}{p}{d:{b}})", 4),              # DDCB..73
    (offset, "BIT 6,(IX{s}{p}{d:{b}})", 4),              # DDCB..74
    (offset, "BIT 6,(IX{s}{p}{d:{b}})", 4),              # DDCB..75
    (offset, "BIT 6,(IX{s}{p}{d:{b}})", 4),              # DDCB..76
    (offset, "BIT 6,(IX{s}{p}{d:{b}})", 4),              # DDCB..77
    (offset, "BIT 7,(IX{s}{p}{d:{b}})", 4),              # DDCB..78
    (offset, "BIT 7,(IX{s}{p}{d:{b}})", 4),              # DDCB..79
    (offset, "BIT 7,(IX{s}{p}{d:{b}})", 4),              # DDCB..7A
    (offset, "BIT 7,(IX{s}{p}{d:{b}})", 4),              # DDCB..7B
    (offset, "BIT 7,(IX{s}{p}{d:{b}})", 4),              # DDCB..7C
    (offset, "BIT 7,(IX{s}{p}{d:{b}})", 4),              # DDCB..7D
    (offset, "BIT 7,(IX{s}{p}{d:{b}})", 4),              # DDCB..7E
    (offset, "BIT 7,(IX{s}{p}{d:{b}})", 4),              # DDCB..7F
    (offset, "RES 0,(IX{s}{p}{d:{b}}),B", 4),            # DDCB..80
    (offset, "RES 0,(IX{s}{p}{d:{b}}),C", 4),            # DDCB..81
    (offset, "RES 0,(IX{s}{p}{d:{b}}),D", 4),            # DDCB..82
    (offset, "RES 0,(IX{s}{p}{d:{b}}),E", 4),            # DDCB..83
    (offset, "RES 0,(IX{s}{p}{d:{b}}),H", 4),            # DDCB..84
    (offset, "RES 0,(IX{s}{p}{d:{b}}),L", 4),            # DDCB..85
    (offset, "RES 0,(IX{s}{p}{d:{b}})", 4),              # DDCB..86
    (offset, "RES 0,(IX{s}{p}{d:{b}}),A", 4),            # DDCB..87
    (offset, "RES 1,(IX{s}{p}{d:{b}}),B", 4),            # DDCB..88
    (offset, "RES 1,(IX{s}{p}{d:{b}}),C", 4),            # DDCB..89
    (offset, "RES 1,(IX{s}{p}{d:{b}}),D", 4),            # DDCB..8A
    (offset, "RES 1,(IX{s}{p}{d:{b}}),E", 4),            # DDCB..8B
    (offset, "RES 1,(IX{s}{p}{d:{b}}),H", 4),            # DDCB..8C
    (offset, "RES 1,(IX{s}{p}{d:{b}}),L", 4),            # DDCB..8D
    (offset, "RES 1,(IX{s}{p}{d:{b}})", 4),              # DDCB..8E
    (offset, "RES 1,(IX{s}{p}{d:{b}}),A", 4),            # DDCB..8F
    (offset, "RES 2,(IX{s}{p}{d:{b}}),B", 4),            # DDCB..90
    (offset, "RES 2,(IX{s}{p}{d:{b}}),C", 4),            # DDCB..91
    (offset, "RES 2,(IX{s}{p}{d:{b}}),D", 4),            # DDCB..92
    (offset, "RES 2,(IX{s}{p}{d:{b}}),E", 4),            # DDCB..93
    (offset, "RES 2,(IX{s}{p}{d:{b}}),H", 4),            # DDCB..94
    (offset, "RES 2,(IX{s}{p}{d:{b}}),L", 4),            # DDCB..95
    (offset, "RES 2,(IX{s}{p}{d:{b}})", 4),              # DDCB..96
    (offset, "RES 2,(IX{s}{p}{d:{b}}),A", 4),            # DDCB..97
    (offset, "RES 3,(IX{s}{p}{d:{b}}),B", 4),            # DDCB..98
    (offset, "RES 3,(IX{s}{p}{d:{b}}),C", 4),            # DDCB..99
    (offset, "RES 3,(IX{s}{p}{d:{b}}),D", 4),            # DDCB..9A
    (offset, "RES 3,(IX{s}{p}{d:{b}}),E", 4),            # DDCB..9B
    (offset, "RES 3,(IX{s}{p}{d:{b}}),H", 4),            # DDCB..9C
    (offset, "RES 3,(IX{s}{p}{d:{b}}),L", 4),            # DDCB..9D
    (offset, "RES 3,(IX{s}{p}{d:{b}})", 4),              # DDCB..9E
    (offset, "RES 3,(IX{s}{p}{d:{b}}),A", 4),            # DDCB..9F
    (offset, "RES 4,(IX{s}{p}{d:{b}}),B", 4),            # DDCB..A0
    (offset, "RES 4,(IX{s}{p}{d:{b}}),C", 4),            # DDCB..A1
    (offset, "RES 4,(IX{s}{p}{d:{b}}),D", 4),            # DDCB..A2
    (offset, "RES 4,(IX{s}{p}{d:{b}}),E", 4),            # DDCB..A3
    (offset, "RES 4,(IX{s}{p}{d:{b}}),H", 4),            # DDCB..A4
    (offset, "RES 4,(IX{s}{p}{d:{b}}),L", 4),            # DDCB..A5
    (offset, "RES 4,(IX{s}{p}{d:{b}})", 4),              # DDCB..A6
    (offset, "RES 4,(IX{s}{p}{d:{b}}),A", 4),            # DDCB..A7
    (offset, "RES 5,(IX{s}{p}{d:{b}}),B", 4),            # DDCB..A8
    (offset, "RES 5,(IX{s}{p}{d:{b}}),C", 4),            # DDCB..A9
    (offset, "RES 5,(IX{s}{p}{d:{b}}),D", 4),            # DDCB..AA
    (offset, "RES 5,(IX{s}{p}{d:{b}}),E", 4),            # DDCB..AB
    (offset, "RES 5,(IX{s}{p}{d:{b}}),H", 4),            # DDCB..AC
    (offset, "RES 5,(IX{s}{p}{d:{b}}),L", 4),            # DDCB..AD
    (offset, "RES 5,(IX{s}{p}{d:{b}})", 4),              # DDCB..AE
    (offset, "RES 5,(IX{s}{p}{d:{b}}),A", 4),            # DDCB..AF
    (offset, "RES 6,(IX{s}{p}{d:{b}}),B", 4),            # DDCB..B0
    (offset, "RES 6,(IX{s}{p}{d:{b}}),C", 4),            # DDCB..B1
    (offset, "RES 6,(IX{s}{p}{d:{b}}),D", 4),            # DDCB..B2
    (offset, "RES 6,(IX{s}{p}{d:{b}}),E", 4),            # DDCB..B3
    (offset, "RES 6,(IX{s}{p}{d:{b}}),H", 4),            # DDCB..B4
    (offset, "RES 6,(IX{s}{p}{d:{b}}),L", 4),            # DDCB..B5
    (offset, "RES 6,(IX{s}{p}{d:{b}})", 4),              # DDCB..B6
    (offset, "RES 6,(IX{s}{p}{d:{b}}),A", 4),            # DDCB..B7
    (offset, "RES 7,(IX{s}{p}{d:{b}}),B", 4),            # DDCB..B8
    (offset, "RES 7,(IX{s}{p}{d:{b}}),C", 4),            # DDCB..B9
    (offset, "RES 7,(IX{s}{p}{d:{b}}),D", 4),            # DDCB..BA
    (offset, "RES 7,(IX{s}{p}{d:{b}}),E", 4),            # DDCB..BB
    (offset, "RES 7,(IX{s}{p}{d:{b}}),H", 4),            # DDCB..BC
    (offset, "RES 7,(IX{s}{p}{d:{b}}),L", 4),            # DDCB..BD
    (offset, "RES 7,(IX{s}{p}{d:{b}})", 4),              # DDCB..BE
    (offset, "RES 7,(IX{s}{p}{d:{b}}),A", 4),            # DDCB..BF
    (offset, "SET 0,(IX{s}{p}{d:{b}}),B", 4),            # DDCB..C0
    (offset, "SET 0,(IX{s}{p}{d:{b}}),C", 4),            # DDCB..C1
    (offset, "SET 0,(IX{s}{p}{d:{b}}),D", 4),            # DDCB..C2
    (offset, "SET 0,(IX{s}{p}{d:{b}}),E", 4),            # DDCB..C3
    (offset, "SET 0,(IX{s}{p}{d:{b}}),H", 4),            # DDCB..C4
    (offset, "SET 0,(IX{s}{p}{d:{b}}),L", 4),            # DDCB..C5
    (offset, "SET 0,(IX{s}{p}{d:{b}})", 4),              # DDCB..C6
    (offset, "SET 0,(IX{s}{p}{d:{b}}),A", 4),            # DDCB..C7
    (offset, "SET 1,(IX{s}{p}{d:{b}}),B", 4),            # DDCB..C8
    (offset, "SET 1,(IX{s}{p}{d:{b}}),C", 4),            # DDCB..C9
    (offset, "SET 1,(IX{s}{p}{d:{b}}),D", 4),            # DDCB..CA
    (offset, "SET 1,(IX{s}{p}{d:{b}}),E", 4),            # DDCB..CB
    (offset, "SET 1,(IX{s}{p}{d:{b}}),H", 4),            # DDCB..CC
    (offset, "SET 1,(IX{s}{p}{d:{b}}),L", 4),            # DDCB..CD
    (offset, "SET 1,(IX{s}{p}{d:{b}})", 4),              # DDCB..CE
    (offset, "SET 1,(IX{s}{p}{d:{b}}),A", 4),            # DDCB..CF
    (offset, "SET 2,(IX{s}{p}{d:{b}}),B", 4),            # DDCB..D0
    (offset, "SET 2,(IX{s}{p}{d:{b}}),C", 4),            # DDCB..D1
    (offset, "SET 2,(IX{s}{p}{d:{b}}),D", 4),            # DDCB..D2
    (offset, "SET 2,(IX{s}{p}{d:{b}}),E", 4),            # DDCB..D3
    (offset, "SET 2,(IX{s}{p}{d:{b}}),H", 4),            # DDCB..D4
    (offset, "SET 2,(IX{s}{p}{d:{b}}),L", 4),            # DDCB..D5
    (offset, "SET 2,(IX{s}{p}{d:{b}})", 4),              # DDCB..D6
    (offset, "SET 2,(IX{s}{p}{d:{b}}),A", 4),            # DDCB..D7
    (offset, "SET 3,(IX{s}{p}{d:{b}}),B", 4),            # DDCB..D8
    (offset, "SET 3,(IX{s}{p}{d:{b}}),C", 4),            # DDCB..D9
    (offset, "SET 3,(IX{s}{p}{d:{b}}),D", 4),            # DDCB..DA
    (offset, "SET 3,(IX{s}{p}{d:{b}}),E", 4),            # DDCB..DB
    (offset, "SET 3,(IX{s}{p}{d:{b}}),H", 4),            # DDCB..DC
    (offset, "SET 3,(IX{s}{p}{d:{b}}),L", 4),            # DDCB..DD
    (offset, "SET 3,(IX{s}{p}{d:{b}})", 4),              # DDCB..DE
    (offset, "SET 3,(IX{s}{p}{d:{b}}),A", 4),            # DDCB..DF
    (offset, "SET 4,(IX{s}{p}{d:{b}}),B", 4),            # DDCB..E0
    (offset, "SET 4,(IX{s}{p}{d:{b}}),C", 4),            # DDCB..E1
    (offset, "SET 4,(IX{s}{p}{d:{b}}),D", 4),            # DDCB..E2
    (offset, "SET 4,(IX{s}{p}{d:{b}}),E", 4),            # DDCB..E3
    (offset, "SET 4,(IX{s}{p}{d:{b}}),H", 4),            # DDCB..E4
    (offset, "SET 4,(IX{s}{p}{d:{b}}),L", 4),            # DDCB..E5
    (offset, "SET 4,(IX{s}{p}{d:{b}})", 4),              # DDCB..E6
    (offset, "SET 4,(IX{s}{p}{d:{b}}),A", 4),            # DDCB..E7
    (offset, "SET 5,(IX{s}{p}{d:{b}}),B", 4),            # DDCB..E8
    (offset, "SET 5,(IX{s}{p}{d:{b}}),C", 4),            # DDCB..E9
    (offset, "SET 5,(IX{s}{p}{d:{b}}),D", 4),            # DDCB..EA
    (offset, "SET 5,(IX{s}{p}{d:{b}}),E", 4),            # DDCB..EB
    (offset, "SET 5,(IX{s}{p}{d:{b}}),H", 4),            # DDCB..EC
    (offset, "SET 5,(IX{s}{p}{d:{b}}),L", 4),            # DDCB..ED
    (offset, "SET 5,(IX{s}{p}{d:{b}})", 4),              # DDCB..EE
    (offset, "SET 5,(IX{s}{p}{d:{b}}),A", 4),            # DDCB..EF
    (offset, "SET 6,(IX{s}{p}{d:{b}}),B", 4),            # DDCB..F0
    (offset, "SET 6,(IX{s}{p}{d:{b}}),C", 4),            # DDCB..F1
    (offset, "SET 6,(IX{s}{p}{d:{b}}),D", 4),            # DDCB..F2
    (offset, "SET 6,(IX{s}{p}{d:{b}}),E", 4),            # DDCB..F3
    (offset, "SET 6,(IX{s}{p}{d:{b}}),H", 4),            # DDCB..F4
    (offset, "SET 6,(IX{s}{p}{d:{b}}),L", 4),            # DDCB..F5
    (offset, "SET 6,(IX{s}{p}{d:{b}})", 4),              # DDCB..F6
    (offset, "SET 6,(IX{s}{p}{d:{b}}),A", 4),            # DDCB..F7
    (offset, "SET 7,(IX{s}{p}{d:{b}}),B", 4),            # DDCB..F8
    (offset, "SET 7,(IX{s}{p}{d:{b}}),C", 4),            # DDCB..F9
    (offset, "SET 7,(IX{s}{p}{d:{b}}),D", 4),            # DDCB..FA
    (offset, "SET 7,(IX{s}{p}{d:{b}}),E", 4),            # DDCB..FB
    (offset, "SET 7,(IX{s}{p}{d:{b}}),H", 4),            # DDCB..FC
    (offset, "SET 7,(IX{s}{p}{d:{b}}),L", 4),            # DDCB..FD
    (offset, "SET 7,(IX{s}{p}{d:{b}})", 4),              # DDCB..FE
    (offset, "SET 7,(IX{s}{p}{d:{b}}),A", 4),            # DDCB..FF
)

AFTER_FDCB = (
    (offset, "RLC (IY{s}{p}{d:{b}}),B", 4),              # FDCB..00
    (offset, "RLC (IY{s}{p}{d:{b}}),C", 4),              # FDCB..01
    (offset, "RLC (IY{s}{p}{d:{b}}),D", 4),              # FDCB..02
    (offset, "RLC (IY{s}{p}{d:{b}}),E", 4),              # FDCB..03
    (offset, "RLC (IY{s}{p}{d:{b}}),H", 4),              # FDCB..04
    (offset, "RLC (IY{s}{p}{d:{b}}),L", 4),              # FDCB..05
    (offset, "RLC (IY{s}{p}{d:{b}})", 4),                # FDCB..06
    (offset, "RLC (IY{s}{p}{d:{b}}),A", 4),              # FDCB..07
    (offset, "RRC (IY{s}{p}{d:{b}}),B", 4),              # FDCB..08
    (offset, "RRC (IY{s}{p}{d:{b}}),C", 4),              # FDCB..09
    (offset, "RRC (IY{s}{p}{d:{b}}),D", 4),              # FDCB..0A
    (offset, "RRC (IY{s}{p}{d:{b}}),E", 4),              # FDCB..0B
    (offset, "RRC (IY{s}{p}{d:{b}}),H", 4),              # FDCB..0C
    (offset, "RRC (IY{s}{p}{d:{b}}),L", 4),              # FDCB..0D
    (offset, "RRC (IY{s}{p}{d:{b}})", 4),                # FDCB..0E
    (offset, "RRC (IY{s}{p}{d:{b}}),A", 4),              # FDCB..0F
    (offset, "RL (IY{s}{p}{d:{b}}),B", 4),               # FDCB..10
    (offset, "RL (IY{s}{p}{d:{b}}),C", 4),               # FDCB..11
    (offset, "RL (IY{s}{p}{d:{b}}),D", 4),               # FDCB..12
    (offset, "RL (IY{s}{p}{d:{b}}),E", 4),               # FDCB..13
    (offset, "RL (IY{s}{p}{d:{b}}),H", 4),               # FDCB..14
    (offset, "RL (IY{s}{p}{d:{b}}),L", 4),               # FDCB..15
    (offset, "RL (IY{s}{p}{d:{b}})", 4),                 # FDCB..16
    (offset, "RL (IY{s}{p}{d:{b}}),A", 4),               # FDCB..17
    (offset, "RR (IY{s}{p}{d:{b}}),B", 4),               # FDCB..18
    (offset, "RR (IY{s}{p}{d:{b}}),C", 4),               # FDCB..19
    (offset, "RR (IY{s}{p}{d:{b}}),D", 4),               # FDCB..1A
    (offset, "RR (IY{s}{p}{d:{b}}),E", 4),               # FDCB..1B
    (offset, "RR (IY{s}{p}{d:{b}}),H", 4),               # FDCB..1C
    (offset, "RR (IY{s}{p}{d:{b}}),L", 4),               # FDCB..1D
    (offset, "RR (IY{s}{p}{d:{b}})", 4),                 # FDCB..1E
    (offset, "RR (IY{s}{p}{d:{b}}),A", 4),               # FDCB..1F
    (offset, "SLA (IY{s}{p}{d:{b}}),B", 4),              # FDCB..20
    (offset, "SLA (IY{s}{p}{d:{b}}),C", 4),              # FDCB..21
    (offset, "SLA (IY{s}{p}{d:{b}}),D", 4),              # FDCB..22
    (offset, "SLA (IY{s}{p}{d:{b}}),E", 4),              # FDCB..23
    (offset, "SLA (IY{s}{p}{d:{b}}),H", 4),              # FDCB..24
    (offset, "SLA (IY{s}{p}{d:{b}}),L", 4),              # FDCB..25
    (offset, "SLA (IY{s}{p}{d:{b}})", 4),                # FDCB..26
    (offset, "SLA (IY{s}{p}{d:{b}}),A", 4),              # FDCB..27
    (offset, "SRA (IY{s}{p}{d:{b}}),B", 4),              # FDCB..28
    (offset, "SRA (IY{s}{p}{d:{b}}),C", 4),              # FDCB..29
    (offset, "SRA (IY{s}{p}{d:{b}}),D", 4),              # FDCB..2A
    (offset, "SRA (IY{s}{p}{d:{b}}),E", 4),              # FDCB..2B
    (offset, "SRA (IY{s}{p}{d:{b}}),H", 4),              # FDCB..2C
    (offset, "SRA (IY{s}{p}{d:{b}}),L", 4),              # FDCB..2D
    (offset, "SRA (IY{s}{p}{d:{b}})", 4),                # FDCB..2E
    (offset, "SRA (IY{s}{p}{d:{b}}),A", 4),              # FDCB..2F
    (offset, "SLL (IY{s}{p}{d:{b}}),B", 4),              # FDCB..30
    (offset, "SLL (IY{s}{p}{d:{b}}),C", 4),              # FDCB..31
    (offset, "SLL (IY{s}{p}{d:{b}}),D", 4),              # FDCB..32
    (offset, "SLL (IY{s}{p}{d:{b}}),E", 4),              # FDCB..33
    (offset, "SLL (IY{s}{p}{d:{b}}),H", 4),              # FDCB..34
    (offset, "SLL (IY{s}{p}{d:{b}}),L", 4),              # FDCB..35
    (offset, "SLL (IY{s}{p}{d:{b}})", 4),                # FDCB..36
    (offset, "SLL (IY{s}{p}{d:{b}}),A", 4),              # FDCB..37
    (offset, "SRL (IY{s}{p}{d:{b}}),B", 4),              # FDCB..38
    (offset, "SRL (IY{s}{p}{d:{b}}),C", 4),              # FDCB..39
    (offset, "SRL (IY{s}{p}{d:{b}}),D", 4),              # FDCB..3A
    (offset, "SRL (IY{s}{p}{d:{b}}),E", 4),              # FDCB..3B
    (offset, "SRL (IY{s}{p}{d:{b}}),H", 4),              # FDCB..3C
    (offset, "SRL (IY{s}{p}{d:{b}}),L", 4),              # FDCB..3D
    (offset, "SRL (IY{s}{p}{d:{b}})", 4),                # FDCB..3E
    (offset, "SRL (IY{s}{p}{d:{b}}),A", 4),              # FDCB..3F
    (offset, "BIT 0,(IY{s}{p}{d:{b}})", 4),              # FDCB..40
    (offset, "BIT 0,(IY{s}{p}{d:{b}})", 4),              # FDCB..41
    (offset, "BIT 0,(IY{s}{p}{d:{b}})", 4),              # FDCB..42
    (offset, "BIT 0,(IY{s}{p}{d:{b}})", 4),              # FDCB..43
    (offset, "BIT 0,(IY{s}{p}{d:{b}})", 4),              # FDCB..44
    (offset, "BIT 0,(IY{s}{p}{d:{b}})", 4),              # FDCB..45
    (offset, "BIT 0,(IY{s}{p}{d:{b}})", 4),              # FDCB..46
    (offset, "BIT 0,(IY{s}{p}{d:{b}})", 4),              # FDCB..47
    (offset, "BIT 1,(IY{s}{p}{d:{b}})", 4),              # FDCB..48
    (offset, "BIT 1,(IY{s}{p}{d:{b}})", 4),              # FDCB..49
    (offset, "BIT 1,(IY{s}{p}{d:{b}})", 4),              # FDCB..4A
    (offset, "BIT 1,(IY{s}{p}{d:{b}})", 4),              # FDCB..4B
    (offset, "BIT 1,(IY{s}{p}{d:{b}})", 4),              # FDCB..4C
    (offset, "BIT 1,(IY{s}{p}{d:{b}})", 4),              # FDCB..4D
    (offset, "BIT 1,(IY{s}{p}{d:{b}})", 4),              # FDCB..4E
    (offset, "BIT 1,(IY{s}{p}{d:{b}})", 4),              # FDCB..4F
    (offset, "BIT 2,(IY{s}{p}{d:{b}})", 4),              # FDCB..50
    (offset, "BIT 2,(IY{s}{p}{d:{b}})", 4),              # FDCB..51
    (offset, "BIT 2,(IY{s}{p}{d:{b}})", 4),              # FDCB..52
    (offset, "BIT 2,(IY{s}{p}{d:{b}})", 4),              # FDCB..53
    (offset, "BIT 2,(IY{s}{p}{d:{b}})", 4),              # FDCB..54
    (offset, "BIT 2,(IY{s}{p}{d:{b}})", 4),              # FDCB..55
    (offset, "BIT 2,(IY{s}{p}{d:{b}})", 4),              # FDCB..56
    (offset, "BIT 2,(IY{s}{p}{d:{b}})", 4),              # FDCB..57
    (offset, "BIT 3,(IY{s}{p}{d:{b}})", 4),              # FDCB..58
    (offset, "BIT 3,(IY{s}{p}{d:{b}})", 4),              # FDCB..59
    (offset, "BIT 3,(IY{s}{p}{d:{b}})", 4),              # FDCB..5A
    (offset, "BIT 3,(IY{s}{p}{d:{b}})", 4),              # FDCB..5B
    (offset, "BIT 3,(IY{s}{p}{d:{b}})", 4),              # FDCB..5C
    (offset, "BIT 3,(IY{s}{p}{d:{b}})", 4),              # FDCB..5D
    (offset, "BIT 3,(IY{s}{p}{d:{b}})", 4),              # FDCB..5E
    (offset, "BIT 3,(IY{s}{p}{d:{b}})", 4),              # FDCB..5F
    (offset, "BIT 4,(IY{s}{p}{d:{b}})", 4),              # FDCB..60
    (offset, "BIT 4,(IY{s}{p}{d:{b}})", 4),              # FDCB..61
    (offset, "BIT 4,(IY{s}{p}{d:{b}})", 4),              # FDCB..62
    (offset, "BIT 4,(IY{s}{p}{d:{b}})", 4),              # FDCB..63
    (offset, "BIT 4,(IY{s}{p}{d:{b}})", 4),              # FDCB..64
    (offset, "BIT 4,(IY{s}{p}{d:{b}})", 4),              # FDCB..65
    (offset, "BIT 4,(IY{s}{p}{d:{b}})", 4),              # FDCB..66
    (offset, "BIT 4,(IY{s}{p}{d:{b}})", 4),              # FDCB..67
    (offset, "BIT 5,(IY{s}{p}{d:{b}})", 4),              # FDCB..68
    (offset, "BIT 5,(IY{s}{p}{d:{b}})", 4),              # FDCB..69
    (offset, "BIT 5,(IY{s}{p}{d:{b}})", 4),              # FDCB..6A
    (offset, "BIT 5,(IY{s}{p}{d:{b}})", 4),              # FDCB..6B
    (offset, "BIT 5,(IY{s}{p}{d:{b}})", 4),              # FDCB..6C
    (offset, "BIT 5,(IY{s}{p}{d:{b}})", 4),              # FDCB..6D
    (offset, "BIT 5,(IY{s}{p}{d:{b}})", 4),              # FDCB..6E
    (offset, "BIT 5,(IY{s}{p}{d:{b}})", 4),              # FDCB..6F
    (offset, "BIT 6,(IY{s}{p}{d:{b}})", 4),              # FDCB..70
    (offset, "BIT 6,(IY{s}{p}{d:{b}})", 4),              # FDCB..71
    (offset, "BIT 6,(IY{s}{p}{d:{b}})", 4),              # FDCB..72
    (offset, "BIT 6,(IY{s}{p}{d:{b}})", 4),              # FDCB..73
    (offset, "BIT 6,(IY{s}{p}{d:{b}})", 4),              # FDCB..74
    (offset, "BIT 6,(IY{s}{p}{d:{b}})", 4),              # FDCB..75
    (offset, "BIT 6,(IY{s}{p}{d:{b}})", 4),              # FDCB..76
    (offset, "BIT 6,(IY{s}{p}{d:{b}})", 4),              # FDCB..77
    (offset, "BIT 7,(IY{s}{p}{d:{b}})", 4),              # FDCB..78
    (offset, "BIT 7,(IY{s}{p}{d:{b}})", 4),              # FDCB..79
    (offset, "BIT 7,(IY{s}{p}{d:{b}})", 4),              # FDCB..7A
    (offset, "BIT 7,(IY{s}{p}{d:{b}})", 4),              # FDCB..7B
    (offset, "BIT 7,(IY{s}{p}{d:{b}})", 4),              # FDCB..7C
    (offset, "BIT 7,(IY{s}{p}{d:{b}})", 4),              # FDCB..7D
    (offset, "BIT 7,(IY{s}{p}{d:{b}})", 4),              # FDCB..7E
    (offset, "BIT 7,(IY{s}{p}{d:{b}})", 4),              # FDCB..7F
    (offset, "RES 0,(IY{s}{p}{d:{b}}),B", 4),            # FDCB..80
    (offset, "RES 0,(IY{s}{p}{d:{b}}),C", 4),            # FDCB..81
    (offset, "RES 0,(IY{s}{p}{d:{b}}),D", 4),            # FDCB..82
    (offset, "RES 0,(IY{s}{p}{d:{b}}),E", 4),            # FDCB..83
    (offset, "RES 0,(IY{s}{p}{d:{b}}),H", 4),            # FDCB..84
    (offset, "RES 0,(IY{s}{p}{d:{b}}),L", 4),            # FDCB..85
    (offset, "RES 0,(IY{s}{p}{d:{b}})", 4),              # FDCB..86
    (offset, "RES 0,(IY{s}{p}{d:{b}}),A", 4),            # FDCB..87
    (offset, "RES 1,(IY{s}{p}{d:{b}}),B", 4),            # FDCB..88
    (offset, "RES 1,(IY{s}{p}{d:{b}}),C", 4),            # FDCB..89
    (offset, "RES 1,(IY{s}{p}{d:{b}}),D", 4),            # FDCB..8A
    (offset, "RES 1,(IY{s}{p}{d:{b}}),E", 4),            # FDCB..8B
    (offset, "RES 1,(IY{s}{p}{d:{b}}),H", 4),            # FDCB..8C
    (offset, "RES 1,(IY{s}{p}{d:{b}}),L", 4),            # FDCB..8D
    (offset, "RES 1,(IY{s}{p}{d:{b}})", 4),              # FDCB..8E
    (offset, "RES 1,(IY{s}{p}{d:{b}}),A", 4),            # FDCB..8F
    (offset, "RES 2,(IY{s}{p}{d:{b}}),B", 4),            # FDCB..90
    (offset, "RES 2,(IY{s}{p}{d:{b}}),C", 4),            # FDCB..91
    (offset, "RES 2,(IY{s}{p}{d:{b}}),D", 4),            # FDCB..92
    (offset, "RES 2,(IY{s}{p}{d:{b}}),E", 4),            # FDCB..93
    (offset, "RES 2,(IY{s}{p}{d:{b}}),H", 4),            # FDCB..94
    (offset, "RES 2,(IY{s}{p}{d:{b}}),L", 4),            # FDCB..95
    (offset, "RES 2,(IY{s}{p}{d:{b}})", 4),              # FDCB..96
    (offset, "RES 2,(IY{s}{p}{d:{b}}),A", 4),            # FDCB..97
    (offset, "RES 3,(IY{s}{p}{d:{b}}),B", 4),            # FDCB..98
    (offset, "RES 3,(IY{s}{p}{d:{b}}),C", 4),            # FDCB..99
    (offset, "RES 3,(IY{s}{p}{d:{b}}),D", 4),            # FDCB..9A
    (offset, "RES 3,(IY{s}{p}{d:{b}}),E", 4),            # FDCB..9B
    (offset, "RES 3,(IY{s}{p}{d:{b}}),H", 4),            # FDCB..9C
    (offset, "RES 3,(IY{s}{p}{d:{b}}),L", 4),            # FDCB..9D
    (offset, "RES 3,(IY{s}{p}{d:{b}})", 4),              # FDCB..9E
    (offset, "RES 3,(IY{s}{p}{d:{b}}),A", 4),            # FDCB..9F
    (offset, "RES 4,(IY{s}{p}{d:{b}}),B", 4),            # FDCB..A0
    (offset, "RES 4,(IY{s}{p}{d:{b}}),C", 4),            # FDCB..A1
    (offset, "RES 4,(IY{s}{p}{d:{b}}),D", 4),            # FDCB..A2
    (offset, "RES 4,(IY{s}{p}{d:{b}}),E", 4),            # FDCB..A3
    (offset, "RES 4,(IY{s}{p}{d:{b}}),H", 4),            # FDCB..A4
    (offset, "RES 4,(IY{s}{p}{d:{b}}),L", 4),            # FDCB..A5
    (offset, "RES 4,(IY{s}{p}{d:{b}})", 4),              # FDCB..A6
    (offset, "RES 4,(IY{s}{p}{d:{b}}),A", 4),            # FDCB..A7
    (offset, "RES 5,(IY{s}{p}{d:{b}}),B", 4),            # FDCB..A8
    (offset, "RES 5,(IY{s}{p}{d:{b}}),C", 4),            # FDCB..A9
    (offset, "RES 5,(IY{s}{p}{d:{b}}),D", 4),            # FDCB..AA
    (offset, "RES 5,(IY{s}{p}{d:{b}}),E", 4),            # FDCB..AB
    (offset, "RES 5,(IY{s}{p}{d:{b}}),H", 4),            # FDCB..AC
    (offset, "RES 5,(IY{s}{p}{d:{b}}),L", 4),            # FDCB..AD
    (offset, "RES 5,(IY{s}{p}{d:{b}})", 4),              # FDCB..AE
    (offset, "RES 5,(IY{s}{p}{d:{b}}),A", 4),            # FDCB..AF
    (offset, "RES 6,(IY{s}{p}{d:{b}}),B", 4),            # FDCB..B0
    (offset, "RES 6,(IY{s}{p}{d:{b}}),C", 4),            # FDCB..B1
    (offset, "RES 6,(IY{s}{p}{d:{b}}),D", 4),            # FDCB..B2
    (offset, "RES 6,(IY{s}{p}{d:{b}}),E", 4),            # FDCB..B3
    (offset, "RES 6,(IY{s}{p}{d:{b}}),H", 4),            # FDCB..B4
    (offset, "RES 6,(IY{s}{p}{d:{b}}),L", 4),            # FDCB..B5
    (offset, "RES 6,(IY{s}{p}{d:{b}})", 4),              # FDCB..B6
    (offset, "RES 6,(IY{s}{p}{d:{b}}),A", 4),            # FDCB..B7
    (offset, "RES 7,(IY{s}{p}{d:{b}}),B", 4),            # FDCB..B8
    (offset, "RES 7,(IY{s}{p}{d:{b}}),C", 4),            # FDCB..B9
    (offset, "RES 7,(IY{s}{p}{d:{b}}),D", 4),            # FDCB..BA
    (offset, "RES 7,(IY{s}{p}{d:{b}}),E", 4),            # FDCB..BB
    (offset, "RES 7,(IY{s}{p}{d:{b}}),H", 4),            # FDCB..BC
    (offset, "RES 7,(IY{s}{p}{d:{b}}),L", 4),            # FDCB..BD
    (offset, "RES 7,(IY{s}{p}{d:{b}})", 4),              # FDCB..BE
    (offset, "RES 7,(IY{s}{p}{d:{b}}),A", 4),            # FDCB..BF
    (offset, "SET 0,(IY{s}{p}{d:{b}}),B", 4),            # FDCB..C0
    (offset, "SET 0,(IY{s}{p}{d:{b}}),C", 4),            # FDCB..C1
    (offset, "SET 0,(IY{s}{p}{d:{b}}),D", 4),            # FDCB..C2
    (offset, "SET 0,(IY{s}{p}{d:{b}}),E", 4),            # FDCB..C3
    (offset, "SET 0,(IY{s}{p}{d:{b}}),H", 4),            # FDCB..C4
    (offset, "SET 0,(IY{s}{p}{d:{b}}),L", 4),            # FDCB..C5
    (offset, "SET 0,(IY{s}{p}{d:{b}})", 4),              # FDCB..C6
    (offset, "SET 0,(IY{s}{p}{d:{b}}),A", 4),            # FDCB..C7
    (offset, "SET 1,(IY{s}{p}{d:{b}}),B", 4),            # FDCB..C8
    (offset, "SET 1,(IY{s}{p}{d:{b}}),C", 4),            # FDCB..C9
    (offset, "SET 1,(IY{s}{p}{d:{b}}),D", 4),            # FDCB..CA
    (offset, "SET 1,(IY{s}{p}{d:{b}}),E", 4),            # FDCB..CB
    (offset, "SET 1,(IY{s}{p}{d:{b}}),H", 4),            # FDCB..CC
    (offset, "SET 1,(IY{s}{p}{d:{b}}),L", 4),            # FDCB..CD
    (offset, "SET 1,(IY{s}{p}{d:{b}})", 4),              # FDCB..CE
    (offset, "SET 1,(IY{s}{p}{d:{b}}),A", 4),            # FDCB..CF
    (offset, "SET 2,(IY{s}{p}{d:{b}}),B", 4),            # FDCB..D0
    (offset, "SET 2,(IY{s}{p}{d:{b}}),C", 4),            # FDCB..D1
    (offset, "SET 2,(IY{s}{p}{d:{b}}),D", 4),            # FDCB..D2
    (offset, "SET 2,(IY{s}{p}{d:{b}}),E", 4),            # FDCB..D3
    (offset, "SET 2,(IY{s}{p}{d:{b}}),H", 4),            # FDCB..D4
    (offset, "SET 2,(IY{s}{p}{d:{b}}),L", 4),            # FDCB..D5
    (offset, "SET 2,(IY{s}{p}{d:{b}})", 4),              # FDCB..D6
    (offset, "SET 2,(IY{s}{p}{d:{b}}),A", 4),            # FDCB..D7
    (offset, "SET 3,(IY{s}{p}{d:{b}}),B", 4),            # FDCB..D8
    (offset, "SET 3,(IY{s}{p}{d:{b}}),C", 4),            # FDCB..D9
    (offset, "SET 3,(IY{s}{p}{d:{b}}),D", 4),            # FDCB..DA
    (offset, "SET 3,(IY{s}{p}{d:{b}}),E", 4),            # FDCB..DB
    (offset, "SET 3,(IY{s}{p}{d:{b}}),H", 4),            # FDCB..DC
    (offset, "SET 3,(IY{s}{p}{d:{b}}),L", 4),            # FDCB..DD
    (offset, "SET 3,(IY{s}{p}{d:{b}})", 4),              # FDCB..DE
    (offset, "SET 3,(IY{s}{p}{d:{b}}),A", 4),            # FDCB..DF
    (offset, "SET 4,(IY{s}{p}{d:{b}}),B", 4),            # FDCB..E0
    (offset, "SET 4,(IY{s}{p}{d:{b}}),C", 4),            # FDCB..E1
    (offset, "SET 4,(IY{s}{p}{d:{b}}),D", 4),            # FDCB..E2
    (offset, "SET 4,(IY{s}{p}{d:{b}}),E", 4),            # FDCB..E3
    (offset, "SET 4,(IY{s}{p}{d:{b}}),H", 4),            # FDCB..E4
    (offset, "SET 4,(IY{s}{p}{d:{b}}),L", 4),            # FDCB..E5
    (offset, "SET 4,(IY{s}{p}{d:{b}})", 4),              # FDCB..E6
    (offset, "SET 4,(IY{s}{p}{d:{b}}),A", 4),            # FDCB..E7
    (offset, "SET 5,(IY{s}{p}{d:{b}}),B", 4),            # FDCB..E8
    (offset, "SET 5,(IY{s}{p}{d:{b}}),C", 4),            # FDCB..E9
    (offset, "SET 5,(IY{s}{p}{d:{b}}),D", 4),            # FDCB..EA
    (offset, "SET 5,(IY{s}{p}{d:{b}}),E", 4),            # FDCB..EB
    (offset, "SET 5,(IY{s}{p}{d:{b}}),H", 4),            # FDCB..EC
    (offset, "SET 5,(IY{s}{p}{d:{b}}),L", 4),            # FDCB..ED
    (offset, "SET 5,(IY{s}{p}{d:{b}})", 4),              # FDCB..EE
    (offset, "SET 5,(IY{s}{p}{d:{b}}),A", 4),            # FDCB..EF
    (offset, "SET 6,(IY{s}{p}{d:{b}}),B", 4),            # FDCB..F0
    (offset, "SET 6,(IY{s}{p}{d:{b}}),C", 4),            # FDCB..F1
    (offset, "SET 6,(IY{s}{p}{d:{b}}),D", 4),            # FDCB..F2
    (offset, "SET 6,(IY{s}{p}{d:{b}}),E", 4),            # FDCB..F3
    (offset, "SET 6,(IY{s}{p}{d:{b}}),H", 4),            # FDCB..F4
    (offset, "SET 6,(IY{s}{p}{d:{b}}),L", 4),            # FDCB..F5
    (offset, "SET 6,(IY{s}{p}{d:{b}})", 4),              # FDCB..F6
    (offset, "SET 6,(IY{s}{p}{d:{b}}),A", 4),            # FDCB..F7
    (offset, "SET 7,(IY{s}{p}{d:{b}}),B", 4),            # FDCB..F8
    (offset, "SET 7,(IY{s}{p}{d:{b}}),C", 4),            # FDCB..F9
    (offset, "SET 7,(IY{s}{p}{d:{b}}),D", 4),            # FDCB..FA
    (offset, "SET 7,(IY{s}{p}{d:{b}}),E", 4),            # FDCB..FB
    (offset, "SET 7,(IY{s}{p}{d:{b}}),H", 4),            # FDCB..FC
    (offset, "SET 7,(IY{s}{p}{d:{b}}),L", 4),            # FDCB..FD
    (offset, "SET 7,(IY{s}{p}{d:{b}})", 4),              # FDCB..FE
    (offset, "SET 7,(IY{s}{p}{d:{b}}),A", 4),            # FDCB..FF
)
