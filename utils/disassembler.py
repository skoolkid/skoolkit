def disassemble(memory, address):
    opcode = memory[address]
    func, operation, size = OPCODES[opcode]
    if func:
        return func(memory, address, operation, size)
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
    return func(memory, address, operation, size)

def operation(memory, address, operation, size):
    return operation, size

def byte(memory, address, operation, size):
    value = memory[(address + size - 1) % 65536]
    return operation.format(f'${value:02X}'), size

def word(memory, address, operation, size):
    value = memory[(address + size - 2) % 65536] + 256 * memory[(address + size - 1) % 65536]
    return operation.format(f'${value:04X}'), size

def jump_offset(memory, address, operation, size):
    offset = memory[(address + 1) % 65536]
    if offset < 128:
        jump_addr = address + 2 + offset
    else:
        jump_addr = address - 254 + offset
    return operation.format(f'${jump_addr:04X}'), 2

def offset(memory, address, operation, size):
    offset = memory[(address + 2) % 65536]
    if offset < 128:
        return operation.format(f'+${offset:02X}'), size
    return operation.format(f'-${256-offset:02X}'), size

def offset_byte(memory, address, operation, size):
    offset = memory[(address + 2) % 65536]
    value = memory[(address + 3) % 65536]
    if offset < 128:
        return operation.format(f'+${offset:02X}', f'${value:02X}'), 4
    return operation.format(f'-${256-offset:02X}', f'${value:02X}'), 4

def rst(memory, address, operation, size):
    addr = (memory[address] - 0xC7) // 8
    return operation.format(f'${addr:02X}'), 1

def defb(memory, address, operation, size):
    if size == 1:
        return f'DEFB ${memory[address]:02X}', 1
    return f'DEFB ${memory[address]:02X},${memory[(address + 1) % 65536]:02X}', 2

OPCODES = (
    (operation, "NOP", 1),            # 0x00
    (word, "LD BC,{}", 3),            # 0x01
    (operation, "LD (BC),A", 1),      # 0x02
    (operation, "INC BC", 1),         # 0x03
    (operation, "INC B", 1),          # 0x04
    (operation, "DEC B", 1),          # 0x05
    (byte, "LD B,{}", 2),             # 0x06
    (operation, "RLCA", 1),           # 0x07
    (operation, "EX AF,AF'", 1),      # 0x08
    (operation, "ADD HL,BC", 1),      # 0x09
    (operation, "LD A,(BC)", 1),      # 0x0A
    (operation, "DEC BC", 1),         # 0x0B
    (operation, "INC C", 1),          # 0x0C
    (operation, "DEC C", 1),          # 0x0D
    (byte, "LD C,{}", 2),             # 0x0E
    (operation, "RRCA", 1),           # 0x0F
    (jump_offset, "DJNZ {}", 2),      # 0x10
    (word, "LD DE,{}", 3),            # 0x11
    (operation, "LD (DE),A", 1),      # 0x12
    (operation, "INC DE", 1),         # 0x13
    (operation, "INC D", 1),          # 0x14
    (operation, "DEC D", 1),          # 0x15
    (byte, "LD D,{}", 2),             # 0x16
    (operation, "RLA", 1),            # 0x17
    (jump_offset, "JR {}", 2),        # 0x18
    (operation, "ADD HL,DE", 1),      # 0x19
    (operation, "LD A,(DE)", 1),      # 0x1A
    (operation, "DEC DE", 1),         # 0x1B
    (operation, "INC E", 1),          # 0x1C
    (operation, "DEC E", 1),          # 0x1D
    (byte, "LD E,{}", 2),             # 0x1E
    (operation, "RRA", 1),            # 0x1F
    (jump_offset, "JR NZ,{}", 2),     # 0x20
    (word, "LD HL,{}", 3),            # 0x21
    (word, "LD ({}),HL", 3),          # 0x22
    (operation, "INC HL", 1),         # 0x23
    (operation, "INC H", 1),          # 0x24
    (operation, "DEC H", 1),          # 0x25
    (byte, "LD H,{}", 2),             # 0x26
    (operation, "DAA", 1),            # 0x27
    (jump_offset, "JR Z,{}", 2),      # 0x28
    (operation, "ADD HL,HL", 1),      # 0x29
    (word, "LD HL,({})", 3),          # 0x2A
    (operation, "DEC HL", 1),         # 0x2B
    (operation, "INC L", 1),          # 0x2C
    (operation, "DEC L", 1),          # 0x2D
    (byte, "LD L,{}", 2),             # 0x2E
    (operation, "CPL", 1),            # 0x2F
    (jump_offset, "JR NC,{}", 2),     # 0x30
    (word, "LD SP,{}", 3),            # 0x31
    (word, "LD ({}),A", 3),           # 0x32
    (operation, "INC SP", 1),         # 0x33
    (operation, "INC (HL)", 1),       # 0x34
    (operation, "DEC (HL)", 1),       # 0x35
    (byte, "LD (HL),{}", 2),          # 0x36
    (operation, "SCF", 1),            # 0x37
    (jump_offset, "JR C,{}", 2),      # 0x38
    (operation, "ADD HL,SP", 1),      # 0x39
    (word, "LD A,({})", 3),           # 0x3A
    (operation, "DEC SP", 1),         # 0x3B
    (operation, "INC A", 1),          # 0x3C
    (operation, "DEC A", 1),          # 0x3D
    (byte, "LD A,{}", 2),             # 0x3E
    (operation, "CCF", 1),            # 0x3F
    (operation, "LD B,B", 1),         # 0x40
    (operation, "LD B,C", 1),         # 0x41
    (operation, "LD B,D", 1),         # 0x42
    (operation, "LD B,E", 1),         # 0x43
    (operation, "LD B,H", 1),         # 0x44
    (operation, "LD B,L", 1),         # 0x45
    (operation, "LD B,(HL)", 1),      # 0x46
    (operation, "LD B,A", 1),         # 0x47
    (operation, "LD C,B", 1),         # 0x48
    (operation, "LD C,C", 1),         # 0x49
    (operation, "LD C,D", 1),         # 0x4A
    (operation, "LD C,E", 1),         # 0x4B
    (operation, "LD C,H", 1),         # 0x4C
    (operation, "LD C,L", 1),         # 0x4D
    (operation, "LD C,(HL)", 1),      # 0x4E
    (operation, "LD C,A", 1),         # 0x4F
    (operation, "LD D,B", 1),         # 0x50
    (operation, "LD D,C", 1),         # 0x51
    (operation, "LD D,D", 1),         # 0x52
    (operation, "LD D,E", 1),         # 0x53
    (operation, "LD D,H", 1),         # 0x54
    (operation, "LD D,L", 1),         # 0x55
    (operation, "LD D,(HL)", 1),      # 0x56
    (operation, "LD D,A", 1),         # 0x57
    (operation, "LD E,B", 1),         # 0x58
    (operation, "LD E,C", 1),         # 0x59
    (operation, "LD E,D", 1),         # 0x5A
    (operation, "LD E,E", 1),         # 0x5B
    (operation, "LD E,H", 1),         # 0x5C
    (operation, "LD E,L", 1),         # 0x5D
    (operation, "LD E,(HL)", 1),      # 0x5E
    (operation, "LD E,A", 1),         # 0x5F
    (operation, "LD H,B", 1),         # 0x60
    (operation, "LD H,C", 1),         # 0x61
    (operation, "LD H,D", 1),         # 0x62
    (operation, "LD H,E", 1),         # 0x63
    (operation, "LD H,H", 1),         # 0x64
    (operation, "LD H,L", 1),         # 0x65
    (operation, "LD H,(HL)", 1),      # 0x66
    (operation, "LD H,A", 1),         # 0x67
    (operation, "LD L,B", 1),         # 0x68
    (operation, "LD L,C", 1),         # 0x69
    (operation, "LD L,D", 1),         # 0x6A
    (operation, "LD L,E", 1),         # 0x6B
    (operation, "LD L,H", 1),         # 0x6C
    (operation, "LD L,L", 1),         # 0x6D
    (operation, "LD L,(HL)", 1),      # 0x6E
    (operation, "LD L,A", 1),         # 0x6F
    (operation, "LD (HL),B", 1),      # 0x70
    (operation, "LD (HL),C", 1),      # 0x71
    (operation, "LD (HL),D", 1),      # 0x72
    (operation, "LD (HL),E", 1),      # 0x73
    (operation, "LD (HL),H", 1),      # 0x74
    (operation, "LD (HL),L", 1),      # 0x75
    (operation, "HALT", 1),           # 0x76
    (operation, "LD (HL),A", 1),      # 0x77
    (operation, "LD A,B", 1),         # 0x78
    (operation, "LD A,C", 1),         # 0x79
    (operation, "LD A,D", 1),         # 0x7A
    (operation, "LD A,E", 1),         # 0x7B
    (operation, "LD A,H", 1),         # 0x7C
    (operation, "LD A,L", 1),         # 0x7D
    (operation, "LD A,(HL)", 1),      # 0x7E
    (operation, "LD A,A", 1),         # 0x7F
    (operation, "ADD A,B", 1),        # 0x80
    (operation, "ADD A,C", 1),        # 0x81
    (operation, "ADD A,D", 1),        # 0x82
    (operation, "ADD A,E", 1),        # 0x83
    (operation, "ADD A,H", 1),        # 0x84
    (operation, "ADD A,L", 1),        # 0x85
    (operation, "ADD A,(HL)", 1),     # 0x86
    (operation, "ADD A,A", 1),        # 0x87
    (operation, "ADC A,B", 1),        # 0x88
    (operation, "ADC A,C", 1),        # 0x89
    (operation, "ADC A,D", 1),        # 0x8A
    (operation, "ADC A,E", 1),        # 0x8B
    (operation, "ADC A,H", 1),        # 0x8C
    (operation, "ADC A,L", 1),        # 0x8D
    (operation, "ADC A,(HL)", 1),     # 0x8E
    (operation, "ADC A,A", 1),        # 0x8F
    (operation, "SUB B", 1),          # 0x90
    (operation, "SUB C", 1),          # 0x91
    (operation, "SUB D", 1),          # 0x92
    (operation, "SUB E", 1),          # 0x93
    (operation, "SUB H", 1),          # 0x94
    (operation, "SUB L", 1),          # 0x95
    (operation, "SUB (HL)", 1),       # 0x96
    (operation, "SUB A", 1),          # 0x97
    (operation, "SBC A,B", 1),        # 0x98
    (operation, "SBC A,C", 1),        # 0x99
    (operation, "SBC A,D", 1),        # 0x9A
    (operation, "SBC A,E", 1),        # 0x9B
    (operation, "SBC A,H", 1),        # 0x9C
    (operation, "SBC A,L", 1),        # 0x9D
    (operation, "SBC A,(HL)", 1),     # 0x9E
    (operation, "SBC A,A", 1),        # 0x9F
    (operation, "AND B", 1),          # 0xA0
    (operation, "AND C", 1),          # 0xA1
    (operation, "AND D", 1),          # 0xA2
    (operation, "AND E", 1),          # 0xA3
    (operation, "AND H", 1),          # 0xA4
    (operation, "AND L", 1),          # 0xA5
    (operation, "AND (HL)", 1),       # 0xA6
    (operation, "AND A", 1),          # 0xA7
    (operation, "XOR B", 1),          # 0xA8
    (operation, "XOR C", 1),          # 0xA9
    (operation, "XOR D", 1),          # 0xAA
    (operation, "XOR E", 1),          # 0xAB
    (operation, "XOR H", 1),          # 0xAC
    (operation, "XOR L", 1),          # 0xAD
    (operation, "XOR (HL)", 1),       # 0xAE
    (operation, "XOR A", 1),          # 0xAF
    (operation, "OR B", 1),           # 0xB0
    (operation, "OR C", 1),           # 0xB1
    (operation, "OR D", 1),           # 0xB2
    (operation, "OR E", 1),           # 0xB3
    (operation, "OR H", 1),           # 0xB4
    (operation, "OR L", 1),           # 0xB5
    (operation, "OR (HL)", 1),        # 0xB6
    (operation, "OR A", 1),           # 0xB7
    (operation, "CP B", 1),           # 0xB8
    (operation, "CP C", 1),           # 0xB9
    (operation, "CP D", 1),           # 0xBA
    (operation, "CP E", 1),           # 0xBB
    (operation, "CP H", 1),           # 0xBC
    (operation, "CP L", 1),           # 0xBD
    (operation, "CP (HL)", 1),        # 0xBE
    (operation, "CP A", 1),           # 0xBF
    (operation, "RET NZ", 1),         # 0xC0
    (operation, "POP BC", 1),         # 0xC1
    (word, "JP NZ,{}", 3),            # 0xC2
    (word, "JP {}", 3),               # 0xC3
    (word, "CALL NZ,{}", 3),          # 0xC4
    (operation, "PUSH BC", 1),        # 0xC5
    (byte, "ADD A,{}", 2),            # 0xC6
    (rst, "RST {}", 1),               # 0xC7
    (operation, "RET Z", 1),          # 0xC8
    (operation, "RET", 1),            # 0xC9
    (word, "JP Z,{}", 3),             # 0xCA
    (None, "", 0),                    # 0xCB
    (word, "CALL Z,{}", 3),           # 0xCC
    (word, "CALL {}", 3),             # 0xCD
    (byte, "ADC A,{}", 2),            # 0xCE
    (rst, "RST {}", 1),               # 0xCF
    (operation, "RET NC", 1),         # 0xD0
    (operation, "POP DE", 1),         # 0xD1
    (word, "JP NC,{}", 3),            # 0xD2
    (byte, "OUT ({}),A", 2),          # 0xD3
    (word, "CALL NC,{}", 3),          # 0xD4
    (operation, "PUSH DE", 1),        # 0xD5
    (byte, "SUB {}", 2),              # 0xD6
    (rst, "RST {}", 1),               # 0xD7
    (operation, "RET C", 1),          # 0xD8
    (operation, "EXX", 1),            # 0xD9
    (word, "JP C,{}", 3),             # 0xDA
    (byte, "IN A,({})", 2),           # 0xDB
    (word, "CALL C,{}", 3),           # 0xDC
    (None, "", 0),                    # 0xDD
    (byte, "SBC A,{}", 2),            # 0xDE
    (rst, "RST {}", 1),               # 0xDF
    (operation, "RET PO", 1),         # 0xE0
    (operation, "POP HL", 1),         # 0xE1
    (word, "JP PO,{}", 3),            # 0xE2
    (operation, "EX (SP),HL", 1),     # 0xE3
    (word, "CALL PO,{}", 3),          # 0xE4
    (operation, "PUSH HL", 1),        # 0xE5
    (byte, "AND {}", 2),              # 0xE6
    (rst, "RST {}", 1),               # 0xE7
    (operation, "RET PE", 1),         # 0xE8
    (operation, "JP (HL)", 1),        # 0xE9
    (word, "JP PE,{}", 3),            # 0xEA
    (operation, "EX DE,HL", 1),       # 0xEB
    (word, "CALL PE,{}", 3),          # 0xEC
    (None, "", 0),                    # 0xED
    (byte, "XOR {}", 2),              # 0xEE
    (rst, "RST {}", 1),               # 0xEF
    (operation, "RET P", 1),          # 0xF0
    (operation, "POP AF", 1),         # 0xF1
    (word, "JP P,{}", 3),             # 0xF2
    (operation, "DI", 1),             # 0xF3
    (word, "CALL P,{}", 3),           # 0xF4
    (operation, "PUSH AF", 1),        # 0xF5
    (byte, "OR {}", 2),               # 0xF6
    (rst, "RST {}", 1),               # 0xF7
    (operation, "RET M", 1),          # 0xF8
    (operation, "LD SP,HL", 1),       # 0xF9
    (word, "JP M,{}", 3),             # 0xFA
    (operation, "EI", 1),             # 0xFB
    (word, "CALL M,{}", 3),           # 0xFC
    (None, "", 0),                    # 0xFD
    (byte, "CP {}", 2),               # 0xFE
    (rst, "RST {}", 1),               # 0xFF
)

AFTER_CB = (
    (operation, "RLC B", 2),          # 0x00
    (operation, "RLC C", 2),          # 0x01
    (operation, "RLC D", 2),          # 0x02
    (operation, "RLC E", 2),          # 0x03
    (operation, "RLC H", 2),          # 0x04
    (operation, "RLC L", 2),          # 0x05
    (operation, "RLC (HL)", 2),       # 0x06
    (operation, "RLC A", 2),          # 0x07
    (operation, "RRC B", 2),          # 0x08
    (operation, "RRC C", 2),          # 0x09
    (operation, "RRC D", 2),          # 0x0A
    (operation, "RRC E", 2),          # 0x0B
    (operation, "RRC H", 2),          # 0x0C
    (operation, "RRC L", 2),          # 0x0D
    (operation, "RRC (HL)", 2),       # 0x0E
    (operation, "RRC A", 2),          # 0x0F
    (operation, "RL B", 2),           # 0x10
    (operation, "RL C", 2),           # 0x11
    (operation, "RL D", 2),           # 0x12
    (operation, "RL E", 2),           # 0x13
    (operation, "RL H", 2),           # 0x14
    (operation, "RL L", 2),           # 0x15
    (operation, "RL (HL)", 2),        # 0x16
    (operation, "RL A", 2),           # 0x17
    (operation, "RR B", 2),           # 0x18
    (operation, "RR C", 2),           # 0x19
    (operation, "RR D", 2),           # 0x1A
    (operation, "RR E", 2),           # 0x1B
    (operation, "RR H", 2),           # 0x1C
    (operation, "RR L", 2),           # 0x1D
    (operation, "RR (HL)", 2),        # 0x1E
    (operation, "RR A", 2),           # 0x1F
    (operation, "SLA B", 2),          # 0x20
    (operation, "SLA C", 2),          # 0x21
    (operation, "SLA D", 2),          # 0x22
    (operation, "SLA E", 2),          # 0x23
    (operation, "SLA H", 2),          # 0x24
    (operation, "SLA L", 2),          # 0x25
    (operation, "SLA (HL)", 2),       # 0x26
    (operation, "SLA A", 2),          # 0x27
    (operation, "SRA B", 2),          # 0x28
    (operation, "SRA C", 2),          # 0x29
    (operation, "SRA D", 2),          # 0x2A
    (operation, "SRA E", 2),          # 0x2B
    (operation, "SRA H", 2),          # 0x2C
    (operation, "SRA L", 2),          # 0x2D
    (operation, "SRA (HL)", 2),       # 0x2E
    (operation, "SRA A", 2),          # 0x2F
    (operation, "SLL B", 2),          # 0x30
    (operation, "SLL C", 2),          # 0x31
    (operation, "SLL D", 2),          # 0x32
    (operation, "SLL E", 2),          # 0x33
    (operation, "SLL H", 2),          # 0x34
    (operation, "SLL L", 2),          # 0x35
    (operation, "SLL (HL)", 2),       # 0x36
    (operation, "SLL A", 2),          # 0x37
    (operation, "SRL B", 2),          # 0x38
    (operation, "SRL C", 2),          # 0x39
    (operation, "SRL D", 2),          # 0x3A
    (operation, "SRL E", 2),          # 0x3B
    (operation, "SRL H", 2),          # 0x3C
    (operation, "SRL L", 2),          # 0x3D
    (operation, "SRL (HL)", 2),       # 0x3E
    (operation, "SRL A", 2),          # 0x3F
    (operation, "BIT 0,B", 2),        # 0x40
    (operation, "BIT 0,C", 2),        # 0x41
    (operation, "BIT 0,D", 2),        # 0x42
    (operation, "BIT 0,E", 2),        # 0x43
    (operation, "BIT 0,H", 2),        # 0x44
    (operation, "BIT 0,L", 2),        # 0x45
    (operation, "BIT 0,(HL)", 2),     # 0x46
    (operation, "BIT 0,A", 2),        # 0x47
    (operation, "BIT 1,B", 2),        # 0x48
    (operation, "BIT 1,C", 2),        # 0x49
    (operation, "BIT 1,D", 2),        # 0x4A
    (operation, "BIT 1,E", 2),        # 0x4B
    (operation, "BIT 1,H", 2),        # 0x4C
    (operation, "BIT 1,L", 2),        # 0x4D
    (operation, "BIT 1,(HL)", 2),     # 0x4E
    (operation, "BIT 1,A", 2),        # 0x4F
    (operation, "BIT 2,B", 2),        # 0x50
    (operation, "BIT 2,C", 2),        # 0x51
    (operation, "BIT 2,D", 2),        # 0x52
    (operation, "BIT 2,E", 2),        # 0x53
    (operation, "BIT 2,H", 2),        # 0x54
    (operation, "BIT 2,L", 2),        # 0x55
    (operation, "BIT 2,(HL)", 2),     # 0x56
    (operation, "BIT 2,A", 2),        # 0x57
    (operation, "BIT 3,B", 2),        # 0x58
    (operation, "BIT 3,C", 2),        # 0x59
    (operation, "BIT 3,D", 2),        # 0x5A
    (operation, "BIT 3,E", 2),        # 0x5B
    (operation, "BIT 3,H", 2),        # 0x5C
    (operation, "BIT 3,L", 2),        # 0x5D
    (operation, "BIT 3,(HL)", 2),     # 0x5E
    (operation, "BIT 3,A", 2),        # 0x5F
    (operation, "BIT 4,B", 2),        # 0x60
    (operation, "BIT 4,C", 2),        # 0x61
    (operation, "BIT 4,D", 2),        # 0x62
    (operation, "BIT 4,E", 2),        # 0x63
    (operation, "BIT 4,H", 2),        # 0x64
    (operation, "BIT 4,L", 2),        # 0x65
    (operation, "BIT 4,(HL)", 2),     # 0x66
    (operation, "BIT 4,A", 2),        # 0x67
    (operation, "BIT 5,B", 2),        # 0x68
    (operation, "BIT 5,C", 2),        # 0x69
    (operation, "BIT 5,D", 2),        # 0x6A
    (operation, "BIT 5,E", 2),        # 0x6B
    (operation, "BIT 5,H", 2),        # 0x6C
    (operation, "BIT 5,L", 2),        # 0x6D
    (operation, "BIT 5,(HL)", 2),     # 0x6E
    (operation, "BIT 5,A", 2),        # 0x6F
    (operation, "BIT 6,B", 2),        # 0x70
    (operation, "BIT 6,C", 2),        # 0x71
    (operation, "BIT 6,D", 2),        # 0x72
    (operation, "BIT 6,E", 2),        # 0x73
    (operation, "BIT 6,H", 2),        # 0x74
    (operation, "BIT 6,L", 2),        # 0x75
    (operation, "BIT 6,(HL)", 2),     # 0x76
    (operation, "BIT 6,A", 2),        # 0x77
    (operation, "BIT 7,B", 2),        # 0x78
    (operation, "BIT 7,C", 2),        # 0x79
    (operation, "BIT 7,D", 2),        # 0x7A
    (operation, "BIT 7,E", 2),        # 0x7B
    (operation, "BIT 7,H", 2),        # 0x7C
    (operation, "BIT 7,L", 2),        # 0x7D
    (operation, "BIT 7,(HL)", 2),     # 0x7E
    (operation, "BIT 7,A", 2),        # 0x7F
    (operation, "RES 0,B", 2),        # 0x80
    (operation, "RES 0,C", 2),        # 0x81
    (operation, "RES 0,D", 2),        # 0x82
    (operation, "RES 0,E", 2),        # 0x83
    (operation, "RES 0,H", 2),        # 0x84
    (operation, "RES 0,L", 2),        # 0x85
    (operation, "RES 0,(HL)", 2),     # 0x86
    (operation, "RES 0,A", 2),        # 0x87
    (operation, "RES 1,B", 2),        # 0x88
    (operation, "RES 1,C", 2),        # 0x89
    (operation, "RES 1,D", 2),        # 0x8A
    (operation, "RES 1,E", 2),        # 0x8B
    (operation, "RES 1,H", 2),        # 0x8C
    (operation, "RES 1,L", 2),        # 0x8D
    (operation, "RES 1,(HL)", 2),     # 0x8E
    (operation, "RES 1,A", 2),        # 0x8F
    (operation, "RES 2,B", 2),        # 0x90
    (operation, "RES 2,C", 2),        # 0x91
    (operation, "RES 2,D", 2),        # 0x92
    (operation, "RES 2,E", 2),        # 0x93
    (operation, "RES 2,H", 2),        # 0x94
    (operation, "RES 2,L", 2),        # 0x95
    (operation, "RES 2,(HL)", 2),     # 0x96
    (operation, "RES 2,A", 2),        # 0x97
    (operation, "RES 3,B", 2),        # 0x98
    (operation, "RES 3,C", 2),        # 0x99
    (operation, "RES 3,D", 2),        # 0x9A
    (operation, "RES 3,E", 2),        # 0x9B
    (operation, "RES 3,H", 2),        # 0x9C
    (operation, "RES 3,L", 2),        # 0x9D
    (operation, "RES 3,(HL)", 2),     # 0x9E
    (operation, "RES 3,A", 2),        # 0x9F
    (operation, "RES 4,B", 2),        # 0xA0
    (operation, "RES 4,C", 2),        # 0xA1
    (operation, "RES 4,D", 2),        # 0xA2
    (operation, "RES 4,E", 2),        # 0xA3
    (operation, "RES 4,H", 2),        # 0xA4
    (operation, "RES 4,L", 2),        # 0xA5
    (operation, "RES 4,(HL)", 2),     # 0xA6
    (operation, "RES 4,A", 2),        # 0xA7
    (operation, "RES 5,B", 2),        # 0xA8
    (operation, "RES 5,C", 2),        # 0xA9
    (operation, "RES 5,D", 2),        # 0xAA
    (operation, "RES 5,E", 2),        # 0xAB
    (operation, "RES 5,H", 2),        # 0xAC
    (operation, "RES 5,L", 2),        # 0xAD
    (operation, "RES 5,(HL)", 2),     # 0xAE
    (operation, "RES 5,A", 2),        # 0xAF
    (operation, "RES 6,B", 2),        # 0xB0
    (operation, "RES 6,C", 2),        # 0xB1
    (operation, "RES 6,D", 2),        # 0xB2
    (operation, "RES 6,E", 2),        # 0xB3
    (operation, "RES 6,H", 2),        # 0xB4
    (operation, "RES 6,L", 2),        # 0xB5
    (operation, "RES 6,(HL)", 2),     # 0xB6
    (operation, "RES 6,A", 2),        # 0xB7
    (operation, "RES 7,B", 2),        # 0xB8
    (operation, "RES 7,C", 2),        # 0xB9
    (operation, "RES 7,D", 2),        # 0xBA
    (operation, "RES 7,E", 2),        # 0xBB
    (operation, "RES 7,H", 2),        # 0xBC
    (operation, "RES 7,L", 2),        # 0xBD
    (operation, "RES 7,(HL)", 2),     # 0xBE
    (operation, "RES 7,A", 2),        # 0xBF
    (operation, "SET 0,B", 2),        # 0xC0
    (operation, "SET 0,C", 2),        # 0xC1
    (operation, "SET 0,D", 2),        # 0xC2
    (operation, "SET 0,E", 2),        # 0xC3
    (operation, "SET 0,H", 2),        # 0xC4
    (operation, "SET 0,L", 2),        # 0xC5
    (operation, "SET 0,(HL)", 2),     # 0xC6
    (operation, "SET 0,A", 2),        # 0xC7
    (operation, "SET 1,B", 2),        # 0xC8
    (operation, "SET 1,C", 2),        # 0xC9
    (operation, "SET 1,D", 2),        # 0xCA
    (operation, "SET 1,E", 2),        # 0xCB
    (operation, "SET 1,H", 2),        # 0xCC
    (operation, "SET 1,L", 2),        # 0xCD
    (operation, "SET 1,(HL)", 2),     # 0xCE
    (operation, "SET 1,A", 2),        # 0xCF
    (operation, "SET 2,B", 2),        # 0xD0
    (operation, "SET 2,C", 2),        # 0xD1
    (operation, "SET 2,D", 2),        # 0xD2
    (operation, "SET 2,E", 2),        # 0xD3
    (operation, "SET 2,H", 2),        # 0xD4
    (operation, "SET 2,L", 2),        # 0xD5
    (operation, "SET 2,(HL)", 2),     # 0xD6
    (operation, "SET 2,A", 2),        # 0xD7
    (operation, "SET 3,B", 2),        # 0xD8
    (operation, "SET 3,C", 2),        # 0xD9
    (operation, "SET 3,D", 2),        # 0xDA
    (operation, "SET 3,E", 2),        # 0xDB
    (operation, "SET 3,H", 2),        # 0xDC
    (operation, "SET 3,L", 2),        # 0xDD
    (operation, "SET 3,(HL)", 2),     # 0xDE
    (operation, "SET 3,A", 2),        # 0xDF
    (operation, "SET 4,B", 2),        # 0xE0
    (operation, "SET 4,C", 2),        # 0xE1
    (operation, "SET 4,D", 2),        # 0xE2
    (operation, "SET 4,E", 2),        # 0xE3
    (operation, "SET 4,H", 2),        # 0xE4
    (operation, "SET 4,L", 2),        # 0xE5
    (operation, "SET 4,(HL)", 2),     # 0xE6
    (operation, "SET 4,A", 2),        # 0xE7
    (operation, "SET 5,B", 2),        # 0xE8
    (operation, "SET 5,C", 2),        # 0xE9
    (operation, "SET 5,D", 2),        # 0xEA
    (operation, "SET 5,E", 2),        # 0xEB
    (operation, "SET 5,H", 2),        # 0xEC
    (operation, "SET 5,L", 2),        # 0xED
    (operation, "SET 5,(HL)", 2),     # 0xEE
    (operation, "SET 5,A", 2),        # 0xEF
    (operation, "SET 6,B", 2),        # 0xF0
    (operation, "SET 6,C", 2),        # 0xF1
    (operation, "SET 6,D", 2),        # 0xF2
    (operation, "SET 6,E", 2),        # 0xF3
    (operation, "SET 6,H", 2),        # 0xF4
    (operation, "SET 6,L", 2),        # 0xF5
    (operation, "SET 6,(HL)", 2),     # 0xF6
    (operation, "SET 6,A", 2),        # 0xF7
    (operation, "SET 7,B", 2),        # 0xF8
    (operation, "SET 7,C", 2),        # 0xF9
    (operation, "SET 7,D", 2),        # 0xFA
    (operation, "SET 7,E", 2),        # 0xFB
    (operation, "SET 7,H", 2),        # 0xFC
    (operation, "SET 7,L", 2),        # 0xFD
    (operation, "SET 7,(HL)", 2),     # 0xFE
    (operation, "SET 7,A", 2),        # 0xFF
)

AFTER_DD = (
    (defb, "", 1),                    # 0x00
    (defb, "", 1),                    # 0x01
    (defb, "", 1),                    # 0x02
    (defb, "", 1),                    # 0x03
    (defb, "", 1),                    # 0x04
    (defb, "", 1),                    # 0x05
    (defb, "", 1),                    # 0x06
    (defb, "", 1),                    # 0x07
    (defb, "", 1),                    # 0x08
    (operation, "ADD IX,BC", 2),      # 0x09
    (defb, "", 1),                    # 0x0A
    (defb, "", 1),                    # 0x0B
    (defb, "", 1),                    # 0x0C
    (defb, "", 1),                    # 0x0D
    (defb, "", 1),                    # 0x0E
    (defb, "", 1),                    # 0x0F
    (defb, "", 1),                    # 0x10
    (defb, "", 1),                    # 0x11
    (defb, "", 1),                    # 0x12
    (defb, "", 1),                    # 0x13
    (defb, "", 1),                    # 0x14
    (defb, "", 1),                    # 0x15
    (defb, "", 1),                    # 0x16
    (defb, "", 1),                    # 0x17
    (defb, "", 1),                    # 0x18
    (operation, "ADD IX,DE", 2),      # 0x19
    (defb, "", 1),                    # 0x1A
    (defb, "", 1),                    # 0x1B
    (defb, "", 1),                    # 0x1C
    (defb, "", 1),                    # 0x1D
    (defb, "", 1),                    # 0x1E
    (defb, "", 1),                    # 0x1F
    (defb, "", 1),                    # 0x20
    (word, "LD IX,{}", 4),            # 0x21
    (word, "LD ({}),IX", 4),          # 0x22
    (operation, "INC IX", 2),         # 0x23
    (operation, "INC IXh", 2),        # 0x24
    (operation, "DEC IXh", 2),        # 0x25
    (byte, "LD IXh,{}", 3),           # 0x26
    (defb, "", 1),                    # 0x27
    (defb, "", 1),                    # 0x28
    (operation, "ADD IX,IX", 2),      # 0x29
    (word, "LD IX,({})", 4),          # 0x2A
    (operation, "DEC IX", 2),         # 0x2B
    (operation, "INC IXl", 2),        # 0x2C
    (operation, "DEC IXl", 2),        # 0x2D
    (byte, "LD IXl,{}", 3),           # 0x2E
    (defb, "", 1),                    # 0x2F
    (defb, "", 1),                    # 0x30
    (defb, "", 1),                    # 0x31
    (defb, "", 1),                    # 0x32
    (defb, "", 1),                    # 0x33
    (offset, "INC (IX{})", 3),        # 0x34
    (offset, "DEC (IX{})", 3),        # 0x35
    (offset_byte, "LD (IX{}),{}", 4), # 0x36
    (defb, "", 1),                    # 0x37
    (defb, "", 1),                    # 0x38
    (operation, "ADD IX,SP", 2),      # 0x39
    (defb, "", 1),                    # 0x3A
    (defb, "", 1),                    # 0x3B
    (defb, "", 1),                    # 0x3C
    (defb, "", 1),                    # 0x3D
    (defb, "", 1),                    # 0x3E
    (defb, "", 1),                    # 0x3F
    (defb, "", 1),                    # 0x40
    (defb, "", 1),                    # 0x41
    (defb, "", 1),                    # 0x42
    (defb, "", 1),                    # 0x43
    (operation, "LD B,IXh", 2),       # 0x44
    (operation, "LD B,IXl", 2),       # 0x45
    (offset, "LD B,(IX{})", 3),       # 0x46
    (defb, "", 1),                    # 0x47
    (defb, "", 1),                    # 0x48
    (defb, "", 1),                    # 0x49
    (defb, "", 1),                    # 0x4A
    (defb, "", 1),                    # 0x4B
    (operation, "LD C,IXh", 2),       # 0x4C
    (operation, "LD C,IXl", 2),       # 0x4D
    (offset, "LD C,(IX{})", 3),       # 0x4E
    (defb, "", 1),                    # 0x4F
    (defb, "", 1),                    # 0x50
    (defb, "", 1),                    # 0x51
    (defb, "", 1),                    # 0x52
    (defb, "", 1),                    # 0x53
    (operation, "LD D,IXh", 2),       # 0x54
    (operation, "LD D,IXl", 2),       # 0x55
    (offset, "LD D,(IX{})", 3),       # 0x56
    (defb, "", 1),                    # 0x57
    (defb, "", 1),                    # 0x58
    (defb, "", 1),                    # 0x59
    (defb, "", 1),                    # 0x5A
    (defb, "", 1),                    # 0x5B
    (operation, "LD E,IXh", 2),       # 0x5C
    (operation, "LD E,IXl", 2),       # 0x5D
    (offset, "LD E,(IX{})", 3),       # 0x5E
    (defb, "", 1),                    # 0x5F
    (operation, "LD IXh,B", 2),       # 0x60
    (operation, "LD IXh,C", 2),       # 0x61
    (operation, "LD IXh,D", 2),       # 0x62
    (operation, "LD IXh,E", 2),       # 0x63
    (operation, "LD IXh,IXh", 2),     # 0x64
    (operation, "LD IXh,IXl", 2),     # 0x65
    (offset, "LD H,(IX{})", 3),       # 0x66
    (operation, "LD IXh,A", 2),       # 0x67
    (operation, "LD IXl,B", 2),       # 0x68
    (operation, "LD IXl,C", 2),       # 0x69
    (operation, "LD IXl,D", 2),       # 0x6A
    (operation, "LD IXl,E", 2),       # 0x6B
    (operation, "LD IXl,IXh", 2),     # 0x6C
    (operation, "LD IXl,IXl", 2),     # 0x6D
    (offset, "LD L,(IX{})", 3),       # 0x6E
    (operation, "LD IXl,A", 2),       # 0x6F
    (offset, "LD (IX{}),B", 3),       # 0x70
    (offset, "LD (IX{}),C", 3),       # 0x71
    (offset, "LD (IX{}),D", 3),       # 0x72
    (offset, "LD (IX{}),E", 3),       # 0x73
    (offset, "LD (IX{}),H", 3),       # 0x74
    (offset, "LD (IX{}),L", 3),       # 0x75
    (defb, "", 1),                    # 0x76
    (offset, "LD (IX{}),A", 3),       # 0x77
    (defb, "", 1),                    # 0x78
    (defb, "", 1),                    # 0x79
    (defb, "", 1),                    # 0x7A
    (defb, "", 1),                    # 0x7B
    (operation, "LD A,IXh", 2),       # 0x7C
    (operation, "LD A,IXl", 2),       # 0x7D
    (offset, "LD A,(IX{})", 3),       # 0x7E
    (defb, "", 1),                    # 0x7F
    (defb, "", 1),                    # 0x80
    (defb, "", 1),                    # 0x81
    (defb, "", 1),                    # 0x82
    (defb, "", 1),                    # 0x83
    (operation, "ADD A,IXh", 2),      # 0x84
    (operation, "ADD A,IXl", 2),      # 0x85
    (offset, "ADD A,(IX{})", 3),      # 0x86
    (defb, "", 1),                    # 0x87
    (defb, "", 1),                    # 0x88
    (defb, "", 1),                    # 0x89
    (defb, "", 1),                    # 0x8A
    (defb, "", 1),                    # 0x8B
    (operation, "ADC A,IXh", 2),      # 0x8C
    (operation, "ADC A,IXl", 2),      # 0x8D
    (offset, "ADC A,(IX{})", 3),      # 0x8E
    (defb, "", 1),                    # 0x8F
    (defb, "", 1),                    # 0x90
    (defb, "", 1),                    # 0x91
    (defb, "", 1),                    # 0x92
    (defb, "", 1),                    # 0x93
    (operation, "SUB IXh", 2),        # 0x94
    (operation, "SUB IXl", 2),        # 0x95
    (offset, "SUB (IX{})", 3),        # 0x96
    (defb, "", 1),                    # 0x97
    (defb, "", 1),                    # 0x98
    (defb, "", 1),                    # 0x99
    (defb, "", 1),                    # 0x9A
    (defb, "", 1),                    # 0x9B
    (operation, "SBC A,IXh", 2),      # 0x9C
    (operation, "SBC A,IXl", 2),      # 0x9D
    (offset, "SBC A,(IX{})", 3),      # 0x9E
    (defb, "", 1),                    # 0x9F
    (defb, "", 1),                    # 0xA0
    (defb, "", 1),                    # 0xA1
    (defb, "", 1),                    # 0xA2
    (defb, "", 1),                    # 0xA3
    (operation, "AND IXh", 2),        # 0xA4
    (operation, "AND IXl", 2),        # 0xA5
    (offset, "AND (IX{})", 3),        # 0xA6
    (defb, "", 1),                    # 0xA7
    (defb, "", 1),                    # 0xA8
    (defb, "", 1),                    # 0xA9
    (defb, "", 1),                    # 0xAA
    (defb, "", 1),                    # 0xAB
    (operation, "XOR IXh", 2),        # 0xAC
    (operation, "XOR IXl", 2),        # 0xAD
    (offset, "XOR (IX{})", 3),        # 0xAE
    (defb, "", 1),                    # 0xAF
    (defb, "", 1),                    # 0xB0
    (defb, "", 1),                    # 0xB1
    (defb, "", 1),                    # 0xB2
    (defb, "", 1),                    # 0xB3
    (operation, "OR IXh", 2),         # 0xB4
    (operation, "OR IXl", 2),         # 0xB5
    (offset, "OR (IX{})", 3),         # 0xB6
    (defb, "", 1),                    # 0xB7
    (defb, "", 1),                    # 0xB8
    (defb, "", 1),                    # 0xB9
    (defb, "", 1),                    # 0xBA
    (defb, "", 1),                    # 0xBB
    (operation, "CP IXh", 2),         # 0xBC
    (operation, "CP IXl", 2),         # 0xBD
    (offset, "CP (IX{})", 3),         # 0xBE
    (defb, "", 1),                    # 0xBF
    (defb, "", 1),                    # 0xC0
    (defb, "", 1),                    # 0xC1
    (defb, "", 1),                    # 0xC2
    (defb, "", 1),                    # 0xC3
    (defb, "", 1),                    # 0xC4
    (defb, "", 1),                    # 0xC5
    (defb, "", 1),                    # 0xC6
    (defb, "", 1),                    # 0xC7
    (defb, "", 1),                    # 0xC8
    (defb, "", 1),                    # 0xC9
    (defb, "", 1),                    # 0xCA
    (None, "", 0),                    # 0xCB
    (defb, "", 1),                    # 0xCC
    (defb, "", 1),                    # 0xCD
    (defb, "", 1),                    # 0xCE
    (defb, "", 1),                    # 0xCF
    (defb, "", 1),                    # 0xD0
    (defb, "", 1),                    # 0xD1
    (defb, "", 1),                    # 0xD2
    (defb, "", 1),                    # 0xD3
    (defb, "", 1),                    # 0xD4
    (defb, "", 1),                    # 0xD5
    (defb, "", 1),                    # 0xD6
    (defb, "", 1),                    # 0xD7
    (defb, "", 1),                    # 0xD8
    (defb, "", 1),                    # 0xD9
    (defb, "", 1),                    # 0xDA
    (defb, "", 1),                    # 0xDB
    (defb, "", 1),                    # 0xDC
    (defb, "", 1),                    # 0xDD
    (defb, "", 1),                    # 0xDE
    (defb, "", 1),                    # 0xDF
    (defb, "", 1),                    # 0xE0
    (operation, "POP IX", 2),         # 0xE1
    (defb, "", 1),                    # 0xE2
    (operation, "EX (SP),IX", 2),     # 0xE3
    (defb, "", 1),                    # 0xE4
    (operation, "PUSH IX", 2),        # 0xE5
    (defb, "", 1),                    # 0xE6
    (defb, "", 1),                    # 0xE7
    (defb, "", 1),                    # 0xE8
    (operation, "JP (IX)", 2),        # 0xE9
    (defb, "", 1),                    # 0xEA
    (defb, "", 1),                    # 0xEB
    (defb, "", 1),                    # 0xEC
    (defb, "", 1),                    # 0xED
    (defb, "", 1),                    # 0xEE
    (defb, "", 1),                    # 0xEF
    (defb, "", 1),                    # 0xF0
    (defb, "", 1),                    # 0xF1
    (defb, "", 1),                    # 0xF2
    (defb, "", 1),                    # 0xF3
    (defb, "", 1),                    # 0xF4
    (defb, "", 1),                    # 0xF5
    (defb, "", 1),                    # 0xF6
    (defb, "", 1),                    # 0xF7
    (defb, "", 1),                    # 0xF8
    (operation, "LD SP,IX", 2),       # 0xF9
    (defb, "", 1),                    # 0xFA
    (defb, "", 1),                    # 0xFB
    (defb, "", 1),                    # 0xFC
    (defb, "", 1),                    # 0xFD
    (defb, "", 1),                    # 0xFE
    (defb, "", 1),                    # 0xFF
)

AFTER_ED = (
    (defb, "", 2),                    # 0x00
    (defb, "", 2),                    # 0x01
    (defb, "", 2),                    # 0x02
    (defb, "", 2),                    # 0x03
    (defb, "", 2),                    # 0x04
    (defb, "", 2),                    # 0x05
    (defb, "", 2),                    # 0x06
    (defb, "", 2),                    # 0x07
    (defb, "", 2),                    # 0x08
    (defb, "", 2),                    # 0x09
    (defb, "", 2),                    # 0x0A
    (defb, "", 2),                    # 0x0B
    (defb, "", 2),                    # 0x0C
    (defb, "", 2),                    # 0x0D
    (defb, "", 2),                    # 0x0E
    (defb, "", 2),                    # 0x0F
    (defb, "", 2),                    # 0x10
    (defb, "", 2),                    # 0x11
    (defb, "", 2),                    # 0x12
    (defb, "", 2),                    # 0x13
    (defb, "", 2),                    # 0x14
    (defb, "", 2),                    # 0x15
    (defb, "", 2),                    # 0x16
    (defb, "", 2),                    # 0x17
    (defb, "", 2),                    # 0x18
    (defb, "", 2),                    # 0x19
    (defb, "", 2),                    # 0x1A
    (defb, "", 2),                    # 0x1B
    (defb, "", 2),                    # 0x1C
    (defb, "", 2),                    # 0x1D
    (defb, "", 2),                    # 0x1E
    (defb, "", 2),                    # 0x1F
    (defb, "", 2),                    # 0x20
    (defb, "", 2),                    # 0x21
    (defb, "", 2),                    # 0x22
    (defb, "", 2),                    # 0x23
    (defb, "", 2),                    # 0x24
    (defb, "", 2),                    # 0x25
    (defb, "", 2),                    # 0x26
    (defb, "", 2),                    # 0x27
    (defb, "", 2),                    # 0x28
    (defb, "", 2),                    # 0x29
    (defb, "", 2),                    # 0x2A
    (defb, "", 2),                    # 0x2B
    (defb, "", 2),                    # 0x2C
    (defb, "", 2),                    # 0x2D
    (defb, "", 2),                    # 0x2E
    (defb, "", 2),                    # 0x2F
    (defb, "", 2),                    # 0x30
    (defb, "", 2),                    # 0x31
    (defb, "", 2),                    # 0x32
    (defb, "", 2),                    # 0x33
    (defb, "", 2),                    # 0x34
    (defb, "", 2),                    # 0x35
    (defb, "", 2),                    # 0x36
    (defb, "", 2),                    # 0x37
    (defb, "", 2),                    # 0x38
    (defb, "", 2),                    # 0x39
    (defb, "", 2),                    # 0x3A
    (defb, "", 2),                    # 0x3B
    (defb, "", 2),                    # 0x3C
    (defb, "", 2),                    # 0x3D
    (defb, "", 2),                    # 0x3E
    (defb, "", 2),                    # 0x3F
    (operation, "IN B,(C)", 2),       # 0x40
    (operation, "OUT (C),B", 2),      # 0x41
    (operation, "SBC HL,BC", 2),      # 0x42
    (word, "LD ({}),BC", 4),          # 0x43
    (operation, "NEG", 2),            # 0x44
    (operation, "RETN", 2),           # 0x45
    (operation, "IM 0", 2),           # 0x46
    (operation, "LD I,A", 2),         # 0x47
    (operation, "IN C,(C)", 2),       # 0x48
    (operation, "OUT (C),C", 2),      # 0x49
    (operation, "ADC HL,BC", 2),      # 0x4A
    (word, "LD BC,({})", 4),          # 0x4B
    (operation, "NEG", 2),            # 0x4C
    (operation, "RETI", 2),           # 0x4D
    (operation, "IM 0", 2),           # 0x4E
    (operation, "LD R,A", 2),         # 0x4F
    (operation, "IN D,(C)", 2),       # 0x50
    (operation, "OUT (C),D", 2),      # 0x51
    (operation, "SBC HL,DE", 2),      # 0x52
    (word, "LD ({}),DE", 4),          # 0x53
    (operation, "NEG", 2),            # 0x54
    (operation, "RETN", 2),           # 0x55
    (operation, "IM 1", 2),           # 0x56
    (operation, "LD A,I", 2),         # 0x57
    (operation, "IN E,(C)", 2),       # 0x58
    (operation, "OUT (C),E", 2),      # 0x59
    (operation, "ADC HL,DE", 2),      # 0x5A
    (word, "LD DE,({})", 4),          # 0x5B
    (operation, "NEG", 2),            # 0x5C
    (operation, "RETN", 2),           # 0x5D
    (operation, "IM 2", 2),           # 0x5E
    (operation, "LD A,R", 2),         # 0x5F
    (operation, "IN H,(C)", 2),       # 0x60
    (operation, "OUT (C),H", 2),      # 0x61
    (operation, "SBC HL,HL", 2),      # 0x62
    (word, "LD ({}),HL", 4),          # 0x63
    (operation, "NEG", 2),            # 0x64
    (operation, "RETN", 2),           # 0x65
    (operation, "IM 0", 2),           # 0x66
    (operation, "RRD", 2),            # 0x67
    (operation, "IN L,(C)", 2),       # 0x68
    (operation, "OUT (C),L", 2),      # 0x69
    (operation, "ADC HL,HL", 2),      # 0x6A
    (word, "LD HL,({})", 4),          # 0x6B
    (operation, "NEG", 2),            # 0x6C
    (operation, "RETN", 2),           # 0x6D
    (operation, "IM 0", 2),           # 0x6E
    (operation, "RLD", 2),            # 0x6F
    (operation, "IN F,(C)", 2),       # 0x70
    (operation, "OUT (C),0", 2),      # 0x71
    (operation, "SBC HL,SP", 2),      # 0x72
    (word, "LD ({}),SP", 4),          # 0x73
    (operation, "NEG", 2),            # 0x74
    (operation, "RETN", 2),           # 0x75
    (operation, "IM 1", 2),           # 0x76
    (defb, "", 2),                    # 0x77
    (operation, "IN A,(C)", 2),       # 0x78
    (operation, "OUT (C),A", 2),      # 0x79
    (operation, "ADC HL,SP", 2),      # 0x7A
    (word, "LD SP,({})", 4),          # 0x7B
    (operation, "NEG", 2),            # 0x7C
    (operation, "RETN", 2),           # 0x7D
    (operation, "IM 2", 2),           # 0x7E
    (defb, "", 2),                    # 0x7F
    (defb, "", 2),                    # 0x80
    (defb, "", 2),                    # 0x81
    (defb, "", 2),                    # 0x82
    (defb, "", 2),                    # 0x83
    (defb, "", 2),                    # 0x84
    (defb, "", 2),                    # 0x85
    (defb, "", 2),                    # 0x86
    (defb, "", 2),                    # 0x87
    (defb, "", 2),                    # 0x88
    (defb, "", 2),                    # 0x89
    (defb, "", 2),                    # 0x8A
    (defb, "", 2),                    # 0x8B
    (defb, "", 2),                    # 0x8C
    (defb, "", 2),                    # 0x8D
    (defb, "", 2),                    # 0x8E
    (defb, "", 2),                    # 0x8F
    (defb, "", 2),                    # 0x90
    (defb, "", 2),                    # 0x91
    (defb, "", 2),                    # 0x92
    (defb, "", 2),                    # 0x93
    (defb, "", 2),                    # 0x94
    (defb, "", 2),                    # 0x95
    (defb, "", 2),                    # 0x96
    (defb, "", 2),                    # 0x97
    (defb, "", 2),                    # 0x98
    (defb, "", 2),                    # 0x99
    (defb, "", 2),                    # 0x9A
    (defb, "", 2),                    # 0x9B
    (defb, "", 2),                    # 0x9C
    (defb, "", 2),                    # 0x9D
    (defb, "", 2),                    # 0x9E
    (defb, "", 2),                    # 0x9F
    (operation, "LDI", 2),            # 0xA0
    (operation, "CPI", 2),            # 0xA1
    (operation, "INI", 2),            # 0xA2
    (operation, "OUTI", 2),           # 0xA3
    (defb, "", 2),                    # 0xA4
    (defb, "", 2),                    # 0xA5
    (defb, "", 2),                    # 0xA6
    (defb, "", 2),                    # 0xA7
    (operation, "LDD", 2),            # 0xA8
    (operation, "CPD", 2),            # 0xA9
    (operation, "IND", 2),            # 0xAA
    (operation, "OUTD", 2),           # 0xAB
    (defb, "", 2),                    # 0xAC
    (defb, "", 2),                    # 0xAD
    (defb, "", 2),                    # 0xAE
    (defb, "", 2),                    # 0xAF
    (operation, "LDIR", 2),           # 0xB0
    (operation, "CPIR", 2),           # 0xB1
    (operation, "INIR", 2),           # 0xB2
    (operation, "OTIR", 2),           # 0xB3
    (defb, "", 2),                    # 0xB4
    (defb, "", 2),                    # 0xB5
    (defb, "", 2),                    # 0xB6
    (defb, "", 2),                    # 0xB7
    (operation, "LDDR", 2),           # 0xB8
    (operation, "CPDR", 2),           # 0xB9
    (operation, "INDR", 2),           # 0xBA
    (operation, "OTDR", 2),           # 0xBB
    (defb, "", 2),                    # 0xBC
    (defb, "", 2),                    # 0xBD
    (defb, "", 2),                    # 0xBE
    (defb, "", 2),                    # 0xBF
    (defb, "", 2),                    # 0xC0
    (defb, "", 2),                    # 0xC1
    (defb, "", 2),                    # 0xC2
    (defb, "", 2),                    # 0xC3
    (defb, "", 2),                    # 0xC4
    (defb, "", 2),                    # 0xC5
    (defb, "", 2),                    # 0xC6
    (defb, "", 2),                    # 0xC7
    (defb, "", 2),                    # 0xC8
    (defb, "", 2),                    # 0xC9
    (defb, "", 2),                    # 0xCA
    (defb, "", 2),                    # 0xCB
    (defb, "", 2),                    # 0xCC
    (defb, "", 2),                    # 0xCD
    (defb, "", 2),                    # 0xCE
    (defb, "", 2),                    # 0xCF
    (defb, "", 2),                    # 0xD0
    (defb, "", 2),                    # 0xD1
    (defb, "", 2),                    # 0xD2
    (defb, "", 2),                    # 0xD3
    (defb, "", 2),                    # 0xD4
    (defb, "", 2),                    # 0xD5
    (defb, "", 2),                    # 0xD6
    (defb, "", 2),                    # 0xD7
    (defb, "", 2),                    # 0xD8
    (defb, "", 2),                    # 0xD9
    (defb, "", 2),                    # 0xDA
    (defb, "", 2),                    # 0xDB
    (defb, "", 2),                    # 0xDC
    (defb, "", 2),                    # 0xDD
    (defb, "", 2),                    # 0xDE
    (defb, "", 2),                    # 0xDF
    (defb, "", 2),                    # 0xE0
    (defb, "", 2),                    # 0xE1
    (defb, "", 2),                    # 0xE2
    (defb, "", 2),                    # 0xE3
    (defb, "", 2),                    # 0xE4
    (defb, "", 2),                    # 0xE5
    (defb, "", 2),                    # 0xE6
    (defb, "", 2),                    # 0xE7
    (defb, "", 2),                    # 0xE8
    (defb, "", 2),                    # 0xE9
    (defb, "", 2),                    # 0xEA
    (defb, "", 2),                    # 0xEB
    (defb, "", 2),                    # 0xEC
    (defb, "", 2),                    # 0xED
    (defb, "", 2),                    # 0xEE
    (defb, "", 2),                    # 0xEF
    (defb, "", 2),                    # 0xF0
    (defb, "", 2),                    # 0xF1
    (defb, "", 2),                    # 0xF2
    (defb, "", 2),                    # 0xF3
    (defb, "", 2),                    # 0xF4
    (defb, "", 2),                    # 0xF5
    (defb, "", 2),                    # 0xF6
    (defb, "", 2),                    # 0xF7
    (defb, "", 2),                    # 0xF8
    (defb, "", 2),                    # 0xF9
    (defb, "", 2),                    # 0xFA
    (defb, "", 2),                    # 0xFB
    (defb, "", 2),                    # 0xFC
    (defb, "", 2),                    # 0xFD
    (defb, "", 2),                    # 0xFE
    (defb, "", 2),                    # 0xFF
)

AFTER_FD = (
    (defb, "", 1),                    # 0x00
    (defb, "", 1),                    # 0x01
    (defb, "", 1),                    # 0x02
    (defb, "", 1),                    # 0x03
    (defb, "", 1),                    # 0x04
    (defb, "", 1),                    # 0x05
    (defb, "", 1),                    # 0x06
    (defb, "", 1),                    # 0x07
    (defb, "", 1),                    # 0x08
    (operation, "ADD IY,BC", 2),      # 0x09
    (defb, "", 1),                    # 0x0A
    (defb, "", 1),                    # 0x0B
    (defb, "", 1),                    # 0x0C
    (defb, "", 1),                    # 0x0D
    (defb, "", 1),                    # 0x0E
    (defb, "", 1),                    # 0x0F
    (defb, "", 1),                    # 0x10
    (defb, "", 1),                    # 0x11
    (defb, "", 1),                    # 0x12
    (defb, "", 1),                    # 0x13
    (defb, "", 1),                    # 0x14
    (defb, "", 1),                    # 0x15
    (defb, "", 1),                    # 0x16
    (defb, "", 1),                    # 0x17
    (defb, "", 1),                    # 0x18
    (operation, "ADD IY,DE", 2),      # 0x19
    (defb, "", 1),                    # 0x1A
    (defb, "", 1),                    # 0x1B
    (defb, "", 1),                    # 0x1C
    (defb, "", 1),                    # 0x1D
    (defb, "", 1),                    # 0x1E
    (defb, "", 1),                    # 0x1F
    (defb, "", 1),                    # 0x20
    (word, "LD IY,{}", 4),            # 0x21
    (word, "LD ({}),IY", 4),          # 0x22
    (operation, "INC IY", 2),         # 0x23
    (operation, "INC IYh", 2),        # 0x24
    (operation, "DEC IYh", 2),        # 0x25
    (byte, "LD IYh,{}", 3),           # 0x26
    (defb, "", 1),                    # 0x27
    (defb, "", 1),                    # 0x28
    (operation, "ADD IY,IY", 2),      # 0x29
    (word, "LD IY,({})", 4),          # 0x2A
    (operation, "DEC IY", 2),         # 0x2B
    (operation, "INC IYl", 2),        # 0x2C
    (operation, "DEC IYl", 2),        # 0x2D
    (byte, "LD IYl,{}", 3),           # 0x2E
    (defb, "", 1),                    # 0x2F
    (defb, "", 1),                    # 0x30
    (defb, "", 1),                    # 0x31
    (defb, "", 1),                    # 0x32
    (defb, "", 1),                    # 0x33
    (offset, "INC (IY{})", 3),        # 0x34
    (offset, "DEC (IY{})", 3),        # 0x35
    (offset_byte, "LD (IY{}),{}", 4), # 0x36
    (defb, "", 1),                    # 0x37
    (defb, "", 1),                    # 0x38
    (operation, "ADD IY,SP", 2),      # 0x39
    (defb, "", 1),                    # 0x3A
    (defb, "", 1),                    # 0x3B
    (defb, "", 1),                    # 0x3C
    (defb, "", 1),                    # 0x3D
    (defb, "", 1),                    # 0x3E
    (defb, "", 1),                    # 0x3F
    (defb, "", 1),                    # 0x40
    (defb, "", 1),                    # 0x41
    (defb, "", 1),                    # 0x42
    (defb, "", 1),                    # 0x43
    (operation, "LD B,IYh", 2),       # 0x44
    (operation, "LD B,IYl", 2),       # 0x45
    (offset, "LD B,(IY{})", 3),       # 0x46
    (defb, "", 1),                    # 0x47
    (defb, "", 1),                    # 0x48
    (defb, "", 1),                    # 0x49
    (defb, "", 1),                    # 0x4A
    (defb, "", 1),                    # 0x4B
    (operation, "LD C,IYh", 2),       # 0x4C
    (operation, "LD C,IYl", 2),       # 0x4D
    (offset, "LD C,(IY{})", 3),       # 0x4E
    (defb, "", 1),                    # 0x4F
    (defb, "", 1),                    # 0x50
    (defb, "", 1),                    # 0x51
    (defb, "", 1),                    # 0x52
    (defb, "", 1),                    # 0x53
    (operation, "LD D,IYh", 2),       # 0x54
    (operation, "LD D,IYl", 2),       # 0x55
    (offset, "LD D,(IY{})", 3),       # 0x56
    (defb, "", 1),                    # 0x57
    (defb, "", 1),                    # 0x58
    (defb, "", 1),                    # 0x59
    (defb, "", 1),                    # 0x5A
    (defb, "", 1),                    # 0x5B
    (operation, "LD E,IYh", 2),       # 0x5C
    (operation, "LD E,IYl", 2),       # 0x5D
    (offset, "LD E,(IY{})", 3),       # 0x5E
    (defb, "", 1),                    # 0x5F
    (operation, "LD IYh,B", 2),       # 0x60
    (operation, "LD IYh,C", 2),       # 0x61
    (operation, "LD IYh,D", 2),       # 0x62
    (operation, "LD IYh,E", 2),       # 0x63
    (operation, "LD IYh,IYh", 2),     # 0x64
    (operation, "LD IYh,IYl", 2),     # 0x65
    (offset, "LD H,(IY{})", 3),       # 0x66
    (operation, "LD IYh,A", 2),       # 0x67
    (operation, "LD IYl,B", 2),       # 0x68
    (operation, "LD IYl,C", 2),       # 0x69
    (operation, "LD IYl,D", 2),       # 0x6A
    (operation, "LD IYl,E", 2),       # 0x6B
    (operation, "LD IYl,IYh", 2),     # 0x6C
    (operation, "LD IYl,IYl", 2),     # 0x6D
    (offset, "LD L,(IY{})", 3),       # 0x6E
    (operation, "LD IYl,A", 2),       # 0x6F
    (offset, "LD (IY{}),B", 3),       # 0x70
    (offset, "LD (IY{}),C", 3),       # 0x71
    (offset, "LD (IY{}),D", 3),       # 0x72
    (offset, "LD (IY{}),E", 3),       # 0x73
    (offset, "LD (IY{}),H", 3),       # 0x74
    (offset, "LD (IY{}),L", 3),       # 0x75
    (defb, "", 1),                    # 0x76
    (offset, "LD (IY{}),A", 3),       # 0x77
    (defb, "", 1),                    # 0x78
    (defb, "", 1),                    # 0x79
    (defb, "", 1),                    # 0x7A
    (defb, "", 1),                    # 0x7B
    (operation, "LD A,IYh", 2),       # 0x7C
    (operation, "LD A,IYl", 2),       # 0x7D
    (offset, "LD A,(IY{})", 3),       # 0x7E
    (defb, "", 1),                    # 0x7F
    (defb, "", 1),                    # 0x80
    (defb, "", 1),                    # 0x81
    (defb, "", 1),                    # 0x82
    (defb, "", 1),                    # 0x83
    (operation, "ADD A,IYh", 2),      # 0x84
    (operation, "ADD A,IYl", 2),      # 0x85
    (offset, "ADD A,(IY{})", 3),      # 0x86
    (defb, "", 1),                    # 0x87
    (defb, "", 1),                    # 0x88
    (defb, "", 1),                    # 0x89
    (defb, "", 1),                    # 0x8A
    (defb, "", 1),                    # 0x8B
    (operation, "ADC A,IYh", 2),      # 0x8C
    (operation, "ADC A,IYl", 2),      # 0x8D
    (offset, "ADC A,(IY{})", 3),      # 0x8E
    (defb, "", 1),                    # 0x8F
    (defb, "", 1),                    # 0x90
    (defb, "", 1),                    # 0x91
    (defb, "", 1),                    # 0x92
    (defb, "", 1),                    # 0x93
    (operation, "SUB IYh", 2),        # 0x94
    (operation, "SUB IYl", 2),        # 0x95
    (offset, "SUB (IY{})", 3),        # 0x96
    (defb, "", 1),                    # 0x97
    (defb, "", 1),                    # 0x98
    (defb, "", 1),                    # 0x99
    (defb, "", 1),                    # 0x9A
    (defb, "", 1),                    # 0x9B
    (operation, "SBC A,IYh", 2),      # 0x9C
    (operation, "SBC A,IYl", 2),      # 0x9D
    (offset, "SBC A,(IY{})", 3),      # 0x9E
    (defb, "", 1),                    # 0x9F
    (defb, "", 1),                    # 0xA0
    (defb, "", 1),                    # 0xA1
    (defb, "", 1),                    # 0xA2
    (defb, "", 1),                    # 0xA3
    (operation, "AND IYh", 2),        # 0xA4
    (operation, "AND IYl", 2),        # 0xA5
    (offset, "AND (IY{})", 3),        # 0xA6
    (defb, "", 1),                    # 0xA7
    (defb, "", 1),                    # 0xA8
    (defb, "", 1),                    # 0xA9
    (defb, "", 1),                    # 0xAA
    (defb, "", 1),                    # 0xAB
    (operation, "XOR IYh", 2),        # 0xAC
    (operation, "XOR IYl", 2),        # 0xAD
    (offset, "XOR (IY{})", 3),        # 0xAE
    (defb, "", 1),                    # 0xAF
    (defb, "", 1),                    # 0xB0
    (defb, "", 1),                    # 0xB1
    (defb, "", 1),                    # 0xB2
    (defb, "", 1),                    # 0xB3
    (operation, "OR IYh", 2),         # 0xB4
    (operation, "OR IYl", 2),         # 0xB5
    (offset, "OR (IY{})", 3),         # 0xB6
    (defb, "", 1),                    # 0xB7
    (defb, "", 1),                    # 0xB8
    (defb, "", 1),                    # 0xB9
    (defb, "", 1),                    # 0xBA
    (defb, "", 1),                    # 0xBB
    (operation, "CP IYh", 2),         # 0xBC
    (operation, "CP IYl", 2),         # 0xBD
    (offset, "CP (IY{})", 3),         # 0xBE
    (defb, "", 1),                    # 0xBF
    (defb, "", 1),                    # 0xC0
    (defb, "", 1),                    # 0xC1
    (defb, "", 1),                    # 0xC2
    (defb, "", 1),                    # 0xC3
    (defb, "", 1),                    # 0xC4
    (defb, "", 1),                    # 0xC5
    (defb, "", 1),                    # 0xC6
    (defb, "", 1),                    # 0xC7
    (defb, "", 1),                    # 0xC8
    (defb, "", 1),                    # 0xC9
    (defb, "", 1),                    # 0xCA
    (None, "", 0),                    # 0xCB
    (defb, "", 1),                    # 0xCC
    (defb, "", 1),                    # 0xCD
    (defb, "", 1),                    # 0xCE
    (defb, "", 1),                    # 0xCF
    (defb, "", 1),                    # 0xD0
    (defb, "", 1),                    # 0xD1
    (defb, "", 1),                    # 0xD2
    (defb, "", 1),                    # 0xD3
    (defb, "", 1),                    # 0xD4
    (defb, "", 1),                    # 0xD5
    (defb, "", 1),                    # 0xD6
    (defb, "", 1),                    # 0xD7
    (defb, "", 1),                    # 0xD8
    (defb, "", 1),                    # 0xD9
    (defb, "", 1),                    # 0xDA
    (defb, "", 1),                    # 0xDB
    (defb, "", 1),                    # 0xDC
    (defb, "", 1),                    # 0xDD
    (defb, "", 1),                    # 0xDE
    (defb, "", 1),                    # 0xDF
    (defb, "", 1),                    # 0xE0
    (operation, "POP IY", 2),         # 0xE1
    (defb, "", 1),                    # 0xE2
    (operation, "EX (SP),IY", 2),     # 0xE3
    (defb, "", 1),                    # 0xE4
    (operation, "PUSH IY", 2),        # 0xE5
    (defb, "", 1),                    # 0xE6
    (defb, "", 1),                    # 0xE7
    (defb, "", 1),                    # 0xE8
    (operation, "JP (IY)", 2),        # 0xE9
    (defb, "", 1),                    # 0xEA
    (defb, "", 1),                    # 0xEB
    (defb, "", 1),                    # 0xEC
    (defb, "", 1),                    # 0xED
    (defb, "", 1),                    # 0xEE
    (defb, "", 1),                    # 0xEF
    (defb, "", 1),                    # 0xF0
    (defb, "", 1),                    # 0xF1
    (defb, "", 1),                    # 0xF2
    (defb, "", 1),                    # 0xF3
    (defb, "", 1),                    # 0xF4
    (defb, "", 1),                    # 0xF5
    (defb, "", 1),                    # 0xF6
    (defb, "", 1),                    # 0xF7
    (defb, "", 1),                    # 0xF8
    (operation, "LD SP,IY", 2),       # 0xF9
    (defb, "", 1),                    # 0xFA
    (defb, "", 1),                    # 0xFB
    (defb, "", 1),                    # 0xFC
    (defb, "", 1),                    # 0xFD
    (defb, "", 1),                    # 0xFE
    (defb, "", 1),                    # 0xFF
)

AFTER_DDCB = (
    (offset, "RLC (IX{}),B", 4),      # 0x00
    (offset, "RLC (IX{}),C", 4),      # 0x01
    (offset, "RLC (IX{}),D", 4),      # 0x02
    (offset, "RLC (IX{}),E", 4),      # 0x03
    (offset, "RLC (IX{}),H", 4),      # 0x04
    (offset, "RLC (IX{}),L", 4),      # 0x05
    (offset, "RLC (IX{})", 4),        # 0x06
    (offset, "RLC (IX{}),A", 4),      # 0x07
    (offset, "RRC (IX{}),B", 4),      # 0x08
    (offset, "RRC (IX{}),C", 4),      # 0x09
    (offset, "RRC (IX{}),D", 4),      # 0x0A
    (offset, "RRC (IX{}),E", 4),      # 0x0B
    (offset, "RRC (IX{}),H", 4),      # 0x0C
    (offset, "RRC (IX{}),L", 4),      # 0x0D
    (offset, "RRC (IX{})", 4),        # 0x0E
    (offset, "RRC (IX{}),A", 4),      # 0x0F
    (offset, "RL (IX{}),B", 4),       # 0x10
    (offset, "RL (IX{}),C", 4),       # 0x11
    (offset, "RL (IX{}),D", 4),       # 0x12
    (offset, "RL (IX{}),E", 4),       # 0x13
    (offset, "RL (IX{}),H", 4),       # 0x14
    (offset, "RL (IX{}),L", 4),       # 0x15
    (offset, "RL (IX{})", 4),         # 0x16
    (offset, "RL (IX{}),A", 4),       # 0x17
    (offset, "RR (IX{}),B", 4),       # 0x18
    (offset, "RR (IX{}),C", 4),       # 0x19
    (offset, "RR (IX{}),D", 4),       # 0x1A
    (offset, "RR (IX{}),E", 4),       # 0x1B
    (offset, "RR (IX{}),H", 4),       # 0x1C
    (offset, "RR (IX{}),L", 4),       # 0x1D
    (offset, "RR (IX{})", 4),         # 0x1E
    (offset, "RR (IX{}),A", 4),       # 0x1F
    (offset, "SLA (IX{}),B", 4),      # 0x20
    (offset, "SLA (IX{}),C", 4),      # 0x21
    (offset, "SLA (IX{}),D", 4),      # 0x22
    (offset, "SLA (IX{}),E", 4),      # 0x23
    (offset, "SLA (IX{}),H", 4),      # 0x24
    (offset, "SLA (IX{}),L", 4),      # 0x25
    (offset, "SLA (IX{})", 4),        # 0x26
    (offset, "SLA (IX{}),A", 4),      # 0x27
    (offset, "SRA (IX{}),B", 4),      # 0x28
    (offset, "SRA (IX{}),C", 4),      # 0x29
    (offset, "SRA (IX{}),D", 4),      # 0x2A
    (offset, "SRA (IX{}),E", 4),      # 0x2B
    (offset, "SRA (IX{}),H", 4),      # 0x2C
    (offset, "SRA (IX{}),L", 4),      # 0x2D
    (offset, "SRA (IX{})", 4),        # 0x2E
    (offset, "SRA (IX{}),A", 4),      # 0x2F
    (offset, "SLL (IX{}),B", 4),      # 0x30
    (offset, "SLL (IX{}),C", 4),      # 0x31
    (offset, "SLL (IX{}),D", 4),      # 0x32
    (offset, "SLL (IX{}),E", 4),      # 0x33
    (offset, "SLL (IX{}),H", 4),      # 0x34
    (offset, "SLL (IX{}),L", 4),      # 0x35
    (offset, "SLL (IX{})", 4),        # 0x36
    (offset, "SLL (IX{}),A", 4),      # 0x37
    (offset, "SRL (IX{}),B", 4),      # 0x38
    (offset, "SRL (IX{}),C", 4),      # 0x39
    (offset, "SRL (IX{}),D", 4),      # 0x3A
    (offset, "SRL (IX{}),E", 4),      # 0x3B
    (offset, "SRL (IX{}),H", 4),      # 0x3C
    (offset, "SRL (IX{}),L", 4),      # 0x3D
    (offset, "SRL (IX{})", 4),        # 0x3E
    (offset, "SRL (IX{}),A", 4),      # 0x3F
    (offset, "BIT 0,(IX{})", 4),      # 0x40
    (offset, "BIT 0,(IX{})", 4),      # 0x41
    (offset, "BIT 0,(IX{})", 4),      # 0x42
    (offset, "BIT 0,(IX{})", 4),      # 0x43
    (offset, "BIT 0,(IX{})", 4),      # 0x44
    (offset, "BIT 0,(IX{})", 4),      # 0x45
    (offset, "BIT 0,(IX{})", 4),      # 0x46
    (offset, "BIT 0,(IX{})", 4),      # 0x47
    (offset, "BIT 1,(IX{})", 4),      # 0x48
    (offset, "BIT 1,(IX{})", 4),      # 0x49
    (offset, "BIT 1,(IX{})", 4),      # 0x4A
    (offset, "BIT 1,(IX{})", 4),      # 0x4B
    (offset, "BIT 1,(IX{})", 4),      # 0x4C
    (offset, "BIT 1,(IX{})", 4),      # 0x4D
    (offset, "BIT 1,(IX{})", 4),      # 0x4E
    (offset, "BIT 1,(IX{})", 4),      # 0x4F
    (offset, "BIT 2,(IX{})", 4),      # 0x50
    (offset, "BIT 2,(IX{})", 4),      # 0x51
    (offset, "BIT 2,(IX{})", 4),      # 0x52
    (offset, "BIT 2,(IX{})", 4),      # 0x53
    (offset, "BIT 2,(IX{})", 4),      # 0x54
    (offset, "BIT 2,(IX{})", 4),      # 0x55
    (offset, "BIT 2,(IX{})", 4),      # 0x56
    (offset, "BIT 2,(IX{})", 4),      # 0x57
    (offset, "BIT 3,(IX{})", 4),      # 0x58
    (offset, "BIT 3,(IX{})", 4),      # 0x59
    (offset, "BIT 3,(IX{})", 4),      # 0x5A
    (offset, "BIT 3,(IX{})", 4),      # 0x5B
    (offset, "BIT 3,(IX{})", 4),      # 0x5C
    (offset, "BIT 3,(IX{})", 4),      # 0x5D
    (offset, "BIT 3,(IX{})", 4),      # 0x5E
    (offset, "BIT 3,(IX{})", 4),      # 0x5F
    (offset, "BIT 4,(IX{})", 4),      # 0x60
    (offset, "BIT 4,(IX{})", 4),      # 0x61
    (offset, "BIT 4,(IX{})", 4),      # 0x62
    (offset, "BIT 4,(IX{})", 4),      # 0x63
    (offset, "BIT 4,(IX{})", 4),      # 0x64
    (offset, "BIT 4,(IX{})", 4),      # 0x65
    (offset, "BIT 4,(IX{})", 4),      # 0x66
    (offset, "BIT 4,(IX{})", 4),      # 0x67
    (offset, "BIT 5,(IX{})", 4),      # 0x68
    (offset, "BIT 5,(IX{})", 4),      # 0x69
    (offset, "BIT 5,(IX{})", 4),      # 0x6A
    (offset, "BIT 5,(IX{})", 4),      # 0x6B
    (offset, "BIT 5,(IX{})", 4),      # 0x6C
    (offset, "BIT 5,(IX{})", 4),      # 0x6D
    (offset, "BIT 5,(IX{})", 4),      # 0x6E
    (offset, "BIT 5,(IX{})", 4),      # 0x6F
    (offset, "BIT 6,(IX{})", 4),      # 0x70
    (offset, "BIT 6,(IX{})", 4),      # 0x71
    (offset, "BIT 6,(IX{})", 4),      # 0x72
    (offset, "BIT 6,(IX{})", 4),      # 0x73
    (offset, "BIT 6,(IX{})", 4),      # 0x74
    (offset, "BIT 6,(IX{})", 4),      # 0x75
    (offset, "BIT 6,(IX{})", 4),      # 0x76
    (offset, "BIT 6,(IX{})", 4),      # 0x77
    (offset, "BIT 7,(IX{})", 4),      # 0x78
    (offset, "BIT 7,(IX{})", 4),      # 0x79
    (offset, "BIT 7,(IX{})", 4),      # 0x7A
    (offset, "BIT 7,(IX{})", 4),      # 0x7B
    (offset, "BIT 7,(IX{})", 4),      # 0x7C
    (offset, "BIT 7,(IX{})", 4),      # 0x7D
    (offset, "BIT 7,(IX{})", 4),      # 0x7E
    (offset, "BIT 7,(IX{})", 4),      # 0x7F
    (offset, "RES 0,(IX{}),B", 4),    # 0x80
    (offset, "RES 0,(IX{}),C", 4),    # 0x81
    (offset, "RES 0,(IX{}),D", 4),    # 0x82
    (offset, "RES 0,(IX{}),E", 4),    # 0x83
    (offset, "RES 0,(IX{}),H", 4),    # 0x84
    (offset, "RES 0,(IX{}),L", 4),    # 0x85
    (offset, "RES 0,(IX{})", 4),      # 0x86
    (offset, "RES 0,(IX{}),A", 4),    # 0x87
    (offset, "RES 1,(IX{}),B", 4),    # 0x88
    (offset, "RES 1,(IX{}),C", 4),    # 0x89
    (offset, "RES 1,(IX{}),D", 4),    # 0x8A
    (offset, "RES 1,(IX{}),E", 4),    # 0x8B
    (offset, "RES 1,(IX{}),H", 4),    # 0x8C
    (offset, "RES 1,(IX{}),L", 4),    # 0x8D
    (offset, "RES 1,(IX{})", 4),      # 0x8E
    (offset, "RES 1,(IX{}),A", 4),    # 0x8F
    (offset, "RES 2,(IX{}),B", 4),    # 0x90
    (offset, "RES 2,(IX{}),C", 4),    # 0x91
    (offset, "RES 2,(IX{}),D", 4),    # 0x92
    (offset, "RES 2,(IX{}),E", 4),    # 0x93
    (offset, "RES 2,(IX{}),H", 4),    # 0x94
    (offset, "RES 2,(IX{}),L", 4),    # 0x95
    (offset, "RES 2,(IX{})", 4),      # 0x96
    (offset, "RES 2,(IX{}),A", 4),    # 0x97
    (offset, "RES 3,(IX{}),B", 4),    # 0x98
    (offset, "RES 3,(IX{}),C", 4),    # 0x99
    (offset, "RES 3,(IX{}),D", 4),    # 0x9A
    (offset, "RES 3,(IX{}),E", 4),    # 0x9B
    (offset, "RES 3,(IX{}),H", 4),    # 0x9C
    (offset, "RES 3,(IX{}),L", 4),    # 0x9D
    (offset, "RES 3,(IX{})", 4),      # 0x9E
    (offset, "RES 3,(IX{}),A", 4),    # 0x9F
    (offset, "RES 4,(IX{}),B", 4),    # 0xA0
    (offset, "RES 4,(IX{}),C", 4),    # 0xA1
    (offset, "RES 4,(IX{}),D", 4),    # 0xA2
    (offset, "RES 4,(IX{}),E", 4),    # 0xA3
    (offset, "RES 4,(IX{}),H", 4),    # 0xA4
    (offset, "RES 4,(IX{}),L", 4),    # 0xA5
    (offset, "RES 4,(IX{})", 4),      # 0xA6
    (offset, "RES 4,(IX{}),A", 4),    # 0xA7
    (offset, "RES 5,(IX{}),B", 4),    # 0xA8
    (offset, "RES 5,(IX{}),C", 4),    # 0xA9
    (offset, "RES 5,(IX{}),D", 4),    # 0xAA
    (offset, "RES 5,(IX{}),E", 4),    # 0xAB
    (offset, "RES 5,(IX{}),H", 4),    # 0xAC
    (offset, "RES 5,(IX{}),L", 4),    # 0xAD
    (offset, "RES 5,(IX{})", 4),      # 0xAE
    (offset, "RES 5,(IX{}),A", 4),    # 0xAF
    (offset, "RES 6,(IX{}),B", 4),    # 0xB0
    (offset, "RES 6,(IX{}),C", 4),    # 0xB1
    (offset, "RES 6,(IX{}),D", 4),    # 0xB2
    (offset, "RES 6,(IX{}),E", 4),    # 0xB3
    (offset, "RES 6,(IX{}),H", 4),    # 0xB4
    (offset, "RES 6,(IX{}),L", 4),    # 0xB5
    (offset, "RES 6,(IX{})", 4),      # 0xB6
    (offset, "RES 6,(IX{}),A", 4),    # 0xB7
    (offset, "RES 7,(IX{}),B", 4),    # 0xB8
    (offset, "RES 7,(IX{}),C", 4),    # 0xB9
    (offset, "RES 7,(IX{}),D", 4),    # 0xBA
    (offset, "RES 7,(IX{}),E", 4),    # 0xBB
    (offset, "RES 7,(IX{}),H", 4),    # 0xBC
    (offset, "RES 7,(IX{}),L", 4),    # 0xBD
    (offset, "RES 7,(IX{})", 4),      # 0xBE
    (offset, "RES 7,(IX{}),A", 4),    # 0xBF
    (offset, "SET 0,(IX{}),B", 4),    # 0xC0
    (offset, "SET 0,(IX{}),C", 4),    # 0xC1
    (offset, "SET 0,(IX{}),D", 4),    # 0xC2
    (offset, "SET 0,(IX{}),E", 4),    # 0xC3
    (offset, "SET 0,(IX{}),H", 4),    # 0xC4
    (offset, "SET 0,(IX{}),L", 4),    # 0xC5
    (offset, "SET 0,(IX{})", 4),      # 0xC6
    (offset, "SET 0,(IX{}),A", 4),    # 0xC7
    (offset, "SET 1,(IX{}),B", 4),    # 0xC8
    (offset, "SET 1,(IX{}),C", 4),    # 0xC9
    (offset, "SET 1,(IX{}),D", 4),    # 0xCA
    (offset, "SET 1,(IX{}),E", 4),    # 0xCB
    (offset, "SET 1,(IX{}),H", 4),    # 0xCC
    (offset, "SET 1,(IX{}),L", 4),    # 0xCD
    (offset, "SET 1,(IX{})", 4),      # 0xCE
    (offset, "SET 1,(IX{}),A", 4),    # 0xCF
    (offset, "SET 2,(IX{}),B", 4),    # 0xD0
    (offset, "SET 2,(IX{}),C", 4),    # 0xD1
    (offset, "SET 2,(IX{}),D", 4),    # 0xD2
    (offset, "SET 2,(IX{}),E", 4),    # 0xD3
    (offset, "SET 2,(IX{}),H", 4),    # 0xD4
    (offset, "SET 2,(IX{}),L", 4),    # 0xD5
    (offset, "SET 2,(IX{})", 4),      # 0xD6
    (offset, "SET 2,(IX{}),A", 4),    # 0xD7
    (offset, "SET 3,(IX{}),B", 4),    # 0xD8
    (offset, "SET 3,(IX{}),C", 4),    # 0xD9
    (offset, "SET 3,(IX{}),D", 4),    # 0xDA
    (offset, "SET 3,(IX{}),E", 4),    # 0xDB
    (offset, "SET 3,(IX{}),H", 4),    # 0xDC
    (offset, "SET 3,(IX{}),L", 4),    # 0xDD
    (offset, "SET 3,(IX{})", 4),      # 0xDE
    (offset, "SET 3,(IX{}),A", 4),    # 0xDF
    (offset, "SET 4,(IX{}),B", 4),    # 0xE0
    (offset, "SET 4,(IX{}),C", 4),    # 0xE1
    (offset, "SET 4,(IX{}),D", 4),    # 0xE2
    (offset, "SET 4,(IX{}),E", 4),    # 0xE3
    (offset, "SET 4,(IX{}),H", 4),    # 0xE4
    (offset, "SET 4,(IX{}),L", 4),    # 0xE5
    (offset, "SET 4,(IX{})", 4),      # 0xE6
    (offset, "SET 4,(IX{}),A", 4),    # 0xE7
    (offset, "SET 5,(IX{}),B", 4),    # 0xE8
    (offset, "SET 5,(IX{}),C", 4),    # 0xE9
    (offset, "SET 5,(IX{}),D", 4),    # 0xEA
    (offset, "SET 5,(IX{}),E", 4),    # 0xEB
    (offset, "SET 5,(IX{}),H", 4),    # 0xEC
    (offset, "SET 5,(IX{}),L", 4),    # 0xED
    (offset, "SET 5,(IX{})", 4),      # 0xEE
    (offset, "SET 5,(IX{}),A", 4),    # 0xEF
    (offset, "SET 6,(IX{}),B", 4),    # 0xF0
    (offset, "SET 6,(IX{}),C", 4),    # 0xF1
    (offset, "SET 6,(IX{}),D", 4),    # 0xF2
    (offset, "SET 6,(IX{}),E", 4),    # 0xF3
    (offset, "SET 6,(IX{}),H", 4),    # 0xF4
    (offset, "SET 6,(IX{}),L", 4),    # 0xF5
    (offset, "SET 6,(IX{})", 4),      # 0xF6
    (offset, "SET 6,(IX{}),A", 4),    # 0xF7
    (offset, "SET 7,(IX{}),B", 4),    # 0xF8
    (offset, "SET 7,(IX{}),C", 4),    # 0xF9
    (offset, "SET 7,(IX{}),D", 4),    # 0xFA
    (offset, "SET 7,(IX{}),E", 4),    # 0xFB
    (offset, "SET 7,(IX{}),H", 4),    # 0xFC
    (offset, "SET 7,(IX{}),L", 4),    # 0xFD
    (offset, "SET 7,(IX{})", 4),      # 0xFE
    (offset, "SET 7,(IX{}),A", 4),    # 0xFF
)

AFTER_FDCB = (
    (offset, "RLC (IY{}),B", 4),      # 0x00
    (offset, "RLC (IY{}),C", 4),      # 0x01
    (offset, "RLC (IY{}),D", 4),      # 0x02
    (offset, "RLC (IY{}),E", 4),      # 0x03
    (offset, "RLC (IY{}),H", 4),      # 0x04
    (offset, "RLC (IY{}),L", 4),      # 0x05
    (offset, "RLC (IY{})", 4),        # 0x06
    (offset, "RLC (IY{}),A", 4),      # 0x07
    (offset, "RRC (IY{}),B", 4),      # 0x08
    (offset, "RRC (IY{}),C", 4),      # 0x09
    (offset, "RRC (IY{}),D", 4),      # 0x0A
    (offset, "RRC (IY{}),E", 4),      # 0x0B
    (offset, "RRC (IY{}),H", 4),      # 0x0C
    (offset, "RRC (IY{}),L", 4),      # 0x0D
    (offset, "RRC (IY{})", 4),        # 0x0E
    (offset, "RRC (IY{}),A", 4),      # 0x0F
    (offset, "RL (IY{}),B", 4),       # 0x10
    (offset, "RL (IY{}),C", 4),       # 0x11
    (offset, "RL (IY{}),D", 4),       # 0x12
    (offset, "RL (IY{}),E", 4),       # 0x13
    (offset, "RL (IY{}),H", 4),       # 0x14
    (offset, "RL (IY{}),L", 4),       # 0x15
    (offset, "RL (IY{})", 4),         # 0x16
    (offset, "RL (IY{}),A", 4),       # 0x17
    (offset, "RR (IY{}),B", 4),       # 0x18
    (offset, "RR (IY{}),C", 4),       # 0x19
    (offset, "RR (IY{}),D", 4),       # 0x1A
    (offset, "RR (IY{}),E", 4),       # 0x1B
    (offset, "RR (IY{}),H", 4),       # 0x1C
    (offset, "RR (IY{}),L", 4),       # 0x1D
    (offset, "RR (IY{})", 4),         # 0x1E
    (offset, "RR (IY{}),A", 4),       # 0x1F
    (offset, "SLA (IY{}),B", 4),      # 0x20
    (offset, "SLA (IY{}),C", 4),      # 0x21
    (offset, "SLA (IY{}),D", 4),      # 0x22
    (offset, "SLA (IY{}),E", 4),      # 0x23
    (offset, "SLA (IY{}),H", 4),      # 0x24
    (offset, "SLA (IY{}),L", 4),      # 0x25
    (offset, "SLA (IY{})", 4),        # 0x26
    (offset, "SLA (IY{}),A", 4),      # 0x27
    (offset, "SRA (IY{}),B", 4),      # 0x28
    (offset, "SRA (IY{}),C", 4),      # 0x29
    (offset, "SRA (IY{}),D", 4),      # 0x2A
    (offset, "SRA (IY{}),E", 4),      # 0x2B
    (offset, "SRA (IY{}),H", 4),      # 0x2C
    (offset, "SRA (IY{}),L", 4),      # 0x2D
    (offset, "SRA (IY{})", 4),        # 0x2E
    (offset, "SRA (IY{}),A", 4),      # 0x2F
    (offset, "SLL (IY{}),B", 4),      # 0x30
    (offset, "SLL (IY{}),C", 4),      # 0x31
    (offset, "SLL (IY{}),D", 4),      # 0x32
    (offset, "SLL (IY{}),E", 4),      # 0x33
    (offset, "SLL (IY{}),H", 4),      # 0x34
    (offset, "SLL (IY{}),L", 4),      # 0x35
    (offset, "SLL (IY{})", 4),        # 0x36
    (offset, "SLL (IY{}),A", 4),      # 0x37
    (offset, "SRL (IY{}),B", 4),      # 0x38
    (offset, "SRL (IY{}),C", 4),      # 0x39
    (offset, "SRL (IY{}),D", 4),      # 0x3A
    (offset, "SRL (IY{}),E", 4),      # 0x3B
    (offset, "SRL (IY{}),H", 4),      # 0x3C
    (offset, "SRL (IY{}),L", 4),      # 0x3D
    (offset, "SRL (IY{})", 4),        # 0x3E
    (offset, "SRL (IY{}),A", 4),      # 0x3F
    (offset, "BIT 0,(IY{})", 4),      # 0x40
    (offset, "BIT 0,(IY{})", 4),      # 0x41
    (offset, "BIT 0,(IY{})", 4),      # 0x42
    (offset, "BIT 0,(IY{})", 4),      # 0x43
    (offset, "BIT 0,(IY{})", 4),      # 0x44
    (offset, "BIT 0,(IY{})", 4),      # 0x45
    (offset, "BIT 0,(IY{})", 4),      # 0x46
    (offset, "BIT 0,(IY{})", 4),      # 0x47
    (offset, "BIT 1,(IY{})", 4),      # 0x48
    (offset, "BIT 1,(IY{})", 4),      # 0x49
    (offset, "BIT 1,(IY{})", 4),      # 0x4A
    (offset, "BIT 1,(IY{})", 4),      # 0x4B
    (offset, "BIT 1,(IY{})", 4),      # 0x4C
    (offset, "BIT 1,(IY{})", 4),      # 0x4D
    (offset, "BIT 1,(IY{})", 4),      # 0x4E
    (offset, "BIT 1,(IY{})", 4),      # 0x4F
    (offset, "BIT 2,(IY{})", 4),      # 0x50
    (offset, "BIT 2,(IY{})", 4),      # 0x51
    (offset, "BIT 2,(IY{})", 4),      # 0x52
    (offset, "BIT 2,(IY{})", 4),      # 0x53
    (offset, "BIT 2,(IY{})", 4),      # 0x54
    (offset, "BIT 2,(IY{})", 4),      # 0x55
    (offset, "BIT 2,(IY{})", 4),      # 0x56
    (offset, "BIT 2,(IY{})", 4),      # 0x57
    (offset, "BIT 3,(IY{})", 4),      # 0x58
    (offset, "BIT 3,(IY{})", 4),      # 0x59
    (offset, "BIT 3,(IY{})", 4),      # 0x5A
    (offset, "BIT 3,(IY{})", 4),      # 0x5B
    (offset, "BIT 3,(IY{})", 4),      # 0x5C
    (offset, "BIT 3,(IY{})", 4),      # 0x5D
    (offset, "BIT 3,(IY{})", 4),      # 0x5E
    (offset, "BIT 3,(IY{})", 4),      # 0x5F
    (offset, "BIT 4,(IY{})", 4),      # 0x60
    (offset, "BIT 4,(IY{})", 4),      # 0x61
    (offset, "BIT 4,(IY{})", 4),      # 0x62
    (offset, "BIT 4,(IY{})", 4),      # 0x63
    (offset, "BIT 4,(IY{})", 4),      # 0x64
    (offset, "BIT 4,(IY{})", 4),      # 0x65
    (offset, "BIT 4,(IY{})", 4),      # 0x66
    (offset, "BIT 4,(IY{})", 4),      # 0x67
    (offset, "BIT 5,(IY{})", 4),      # 0x68
    (offset, "BIT 5,(IY{})", 4),      # 0x69
    (offset, "BIT 5,(IY{})", 4),      # 0x6A
    (offset, "BIT 5,(IY{})", 4),      # 0x6B
    (offset, "BIT 5,(IY{})", 4),      # 0x6C
    (offset, "BIT 5,(IY{})", 4),      # 0x6D
    (offset, "BIT 5,(IY{})", 4),      # 0x6E
    (offset, "BIT 5,(IY{})", 4),      # 0x6F
    (offset, "BIT 6,(IY{})", 4),      # 0x70
    (offset, "BIT 6,(IY{})", 4),      # 0x71
    (offset, "BIT 6,(IY{})", 4),      # 0x72
    (offset, "BIT 6,(IY{})", 4),      # 0x73
    (offset, "BIT 6,(IY{})", 4),      # 0x74
    (offset, "BIT 6,(IY{})", 4),      # 0x75
    (offset, "BIT 6,(IY{})", 4),      # 0x76
    (offset, "BIT 6,(IY{})", 4),      # 0x77
    (offset, "BIT 7,(IY{})", 4),      # 0x78
    (offset, "BIT 7,(IY{})", 4),      # 0x79
    (offset, "BIT 7,(IY{})", 4),      # 0x7A
    (offset, "BIT 7,(IY{})", 4),      # 0x7B
    (offset, "BIT 7,(IY{})", 4),      # 0x7C
    (offset, "BIT 7,(IY{})", 4),      # 0x7D
    (offset, "BIT 7,(IY{})", 4),      # 0x7E
    (offset, "BIT 7,(IY{})", 4),      # 0x7F
    (offset, "RES 0,(IY{}),B", 4),    # 0x80
    (offset, "RES 0,(IY{}),C", 4),    # 0x81
    (offset, "RES 0,(IY{}),D", 4),    # 0x82
    (offset, "RES 0,(IY{}),E", 4),    # 0x83
    (offset, "RES 0,(IY{}),H", 4),    # 0x84
    (offset, "RES 0,(IY{}),L", 4),    # 0x85
    (offset, "RES 0,(IY{})", 4),      # 0x86
    (offset, "RES 0,(IY{}),A", 4),    # 0x87
    (offset, "RES 1,(IY{}),B", 4),    # 0x88
    (offset, "RES 1,(IY{}),C", 4),    # 0x89
    (offset, "RES 1,(IY{}),D", 4),    # 0x8A
    (offset, "RES 1,(IY{}),E", 4),    # 0x8B
    (offset, "RES 1,(IY{}),H", 4),    # 0x8C
    (offset, "RES 1,(IY{}),L", 4),    # 0x8D
    (offset, "RES 1,(IY{})", 4),      # 0x8E
    (offset, "RES 1,(IY{}),A", 4),    # 0x8F
    (offset, "RES 2,(IY{}),B", 4),    # 0x90
    (offset, "RES 2,(IY{}),C", 4),    # 0x91
    (offset, "RES 2,(IY{}),D", 4),    # 0x92
    (offset, "RES 2,(IY{}),E", 4),    # 0x93
    (offset, "RES 2,(IY{}),H", 4),    # 0x94
    (offset, "RES 2,(IY{}),L", 4),    # 0x95
    (offset, "RES 2,(IY{})", 4),      # 0x96
    (offset, "RES 2,(IY{}),A", 4),    # 0x97
    (offset, "RES 3,(IY{}),B", 4),    # 0x98
    (offset, "RES 3,(IY{}),C", 4),    # 0x99
    (offset, "RES 3,(IY{}),D", 4),    # 0x9A
    (offset, "RES 3,(IY{}),E", 4),    # 0x9B
    (offset, "RES 3,(IY{}),H", 4),    # 0x9C
    (offset, "RES 3,(IY{}),L", 4),    # 0x9D
    (offset, "RES 3,(IY{})", 4),      # 0x9E
    (offset, "RES 3,(IY{}),A", 4),    # 0x9F
    (offset, "RES 4,(IY{}),B", 4),    # 0xA0
    (offset, "RES 4,(IY{}),C", 4),    # 0xA1
    (offset, "RES 4,(IY{}),D", 4),    # 0xA2
    (offset, "RES 4,(IY{}),E", 4),    # 0xA3
    (offset, "RES 4,(IY{}),H", 4),    # 0xA4
    (offset, "RES 4,(IY{}),L", 4),    # 0xA5
    (offset, "RES 4,(IY{})", 4),      # 0xA6
    (offset, "RES 4,(IY{}),A", 4),    # 0xA7
    (offset, "RES 5,(IY{}),B", 4),    # 0xA8
    (offset, "RES 5,(IY{}),C", 4),    # 0xA9
    (offset, "RES 5,(IY{}),D", 4),    # 0xAA
    (offset, "RES 5,(IY{}),E", 4),    # 0xAB
    (offset, "RES 5,(IY{}),H", 4),    # 0xAC
    (offset, "RES 5,(IY{}),L", 4),    # 0xAD
    (offset, "RES 5,(IY{})", 4),      # 0xAE
    (offset, "RES 5,(IY{}),A", 4),    # 0xAF
    (offset, "RES 6,(IY{}),B", 4),    # 0xB0
    (offset, "RES 6,(IY{}),C", 4),    # 0xB1
    (offset, "RES 6,(IY{}),D", 4),    # 0xB2
    (offset, "RES 6,(IY{}),E", 4),    # 0xB3
    (offset, "RES 6,(IY{}),H", 4),    # 0xB4
    (offset, "RES 6,(IY{}),L", 4),    # 0xB5
    (offset, "RES 6,(IY{})", 4),      # 0xB6
    (offset, "RES 6,(IY{}),A", 4),    # 0xB7
    (offset, "RES 7,(IY{}),B", 4),    # 0xB8
    (offset, "RES 7,(IY{}),C", 4),    # 0xB9
    (offset, "RES 7,(IY{}),D", 4),    # 0xBA
    (offset, "RES 7,(IY{}),E", 4),    # 0xBB
    (offset, "RES 7,(IY{}),H", 4),    # 0xBC
    (offset, "RES 7,(IY{}),L", 4),    # 0xBD
    (offset, "RES 7,(IY{})", 4),      # 0xBE
    (offset, "RES 7,(IY{}),A", 4),    # 0xBF
    (offset, "SET 0,(IY{}),B", 4),    # 0xC0
    (offset, "SET 0,(IY{}),C", 4),    # 0xC1
    (offset, "SET 0,(IY{}),D", 4),    # 0xC2
    (offset, "SET 0,(IY{}),E", 4),    # 0xC3
    (offset, "SET 0,(IY{}),H", 4),    # 0xC4
    (offset, "SET 0,(IY{}),L", 4),    # 0xC5
    (offset, "SET 0,(IY{})", 4),      # 0xC6
    (offset, "SET 0,(IY{}),A", 4),    # 0xC7
    (offset, "SET 1,(IY{}),B", 4),    # 0xC8
    (offset, "SET 1,(IY{}),C", 4),    # 0xC9
    (offset, "SET 1,(IY{}),D", 4),    # 0xCA
    (offset, "SET 1,(IY{}),E", 4),    # 0xCB
    (offset, "SET 1,(IY{}),H", 4),    # 0xCC
    (offset, "SET 1,(IY{}),L", 4),    # 0xCD
    (offset, "SET 1,(IY{})", 4),      # 0xCE
    (offset, "SET 1,(IY{}),A", 4),    # 0xCF
    (offset, "SET 2,(IY{}),B", 4),    # 0xD0
    (offset, "SET 2,(IY{}),C", 4),    # 0xD1
    (offset, "SET 2,(IY{}),D", 4),    # 0xD2
    (offset, "SET 2,(IY{}),E", 4),    # 0xD3
    (offset, "SET 2,(IY{}),H", 4),    # 0xD4
    (offset, "SET 2,(IY{}),L", 4),    # 0xD5
    (offset, "SET 2,(IY{})", 4),      # 0xD6
    (offset, "SET 2,(IY{}),A", 4),    # 0xD7
    (offset, "SET 3,(IY{}),B", 4),    # 0xD8
    (offset, "SET 3,(IY{}),C", 4),    # 0xD9
    (offset, "SET 3,(IY{}),D", 4),    # 0xDA
    (offset, "SET 3,(IY{}),E", 4),    # 0xDB
    (offset, "SET 3,(IY{}),H", 4),    # 0xDC
    (offset, "SET 3,(IY{}),L", 4),    # 0xDD
    (offset, "SET 3,(IY{})", 4),      # 0xDE
    (offset, "SET 3,(IY{}),A", 4),    # 0xDF
    (offset, "SET 4,(IY{}),B", 4),    # 0xE0
    (offset, "SET 4,(IY{}),C", 4),    # 0xE1
    (offset, "SET 4,(IY{}),D", 4),    # 0xE2
    (offset, "SET 4,(IY{}),E", 4),    # 0xE3
    (offset, "SET 4,(IY{}),H", 4),    # 0xE4
    (offset, "SET 4,(IY{}),L", 4),    # 0xE5
    (offset, "SET 4,(IY{})", 4),      # 0xE6
    (offset, "SET 4,(IY{}),A", 4),    # 0xE7
    (offset, "SET 5,(IY{}),B", 4),    # 0xE8
    (offset, "SET 5,(IY{}),C", 4),    # 0xE9
    (offset, "SET 5,(IY{}),D", 4),    # 0xEA
    (offset, "SET 5,(IY{}),E", 4),    # 0xEB
    (offset, "SET 5,(IY{}),H", 4),    # 0xEC
    (offset, "SET 5,(IY{}),L", 4),    # 0xED
    (offset, "SET 5,(IY{})", 4),      # 0xEE
    (offset, "SET 5,(IY{}),A", 4),    # 0xEF
    (offset, "SET 6,(IY{}),B", 4),    # 0xF0
    (offset, "SET 6,(IY{}),C", 4),    # 0xF1
    (offset, "SET 6,(IY{}),D", 4),    # 0xF2
    (offset, "SET 6,(IY{}),E", 4),    # 0xF3
    (offset, "SET 6,(IY{}),H", 4),    # 0xF4
    (offset, "SET 6,(IY{}),L", 4),    # 0xF5
    (offset, "SET 6,(IY{})", 4),      # 0xF6
    (offset, "SET 6,(IY{}),A", 4),    # 0xF7
    (offset, "SET 7,(IY{}),B", 4),    # 0xF8
    (offset, "SET 7,(IY{}),C", 4),    # 0xF9
    (offset, "SET 7,(IY{}),D", 4),    # 0xFA
    (offset, "SET 7,(IY{}),E", 4),    # 0xFB
    (offset, "SET 7,(IY{}),H", 4),    # 0xFC
    (offset, "SET 7,(IY{}),L", 4),    # 0xFD
    (offset, "SET 7,(IY{})", 4),      # 0xFE
    (offset, "SET 7,(IY{}),A", 4),    # 0xFF
)

