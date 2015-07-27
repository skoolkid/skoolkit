# -*- coding: utf-8 -*-

# Copyright 2010-2015 Richard Dymond (rjdymond@gmail.com)
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

from skoolkit.z80 import convert_case

class Instruction:
    def __init__(self, address, operation, data):
        self.address = address
        self.operation = operation
        self.bytes = data
        self.referrers = []
        self.entry = None
        self.ctl = None
        self.comment = None

    def add_referrer(self, entry):
        if not self.ctl:
            self.ctl = '*'
        if entry is not self.entry and entry not in self.referrers:
            self.referrers.append(entry)

    def size(self):
        return len(self.bytes)

class Disassembler:
    ops = {}
    after_CB = {}
    after_DD = {}
    after_ED = {}
    after_DDCB = {}

    def __init__(self, snapshot, defb_size=8, defb_mod=1, zfill=False, defm_width=66, asm_hex=False, asm_lower=False):
        self.snapshot = snapshot
        self.defb_size = defb_size
        self.defb_mod = defb_mod
        self.zfill = zfill
        self.defm_width = defm_width
        self.asm_hex = asm_hex
        self.asm_lower = asm_lower
        self.defw_size = 2
        self.byte_formats = {
            'b': '%{:08b}',
            'h': '${:02X}',
            'd': '{}'
        }
        if self.zfill:
            self.byte_formats['d'] = '{:03d}'
        self.word_formats = {
            'b': '%{:016b}',
            'h': '${:04X}',
            'd': '{}'
        }

    def num_str(self, value, num_bytes=0, base=None):
        if base:
            base = base[0]
        if base == 'c' and 32 <= value < 127 and value not in (94, 96):
            if value in (34, 92):
                return r'"\{}"'.format(chr(value))
            return '"{}"'.format(chr(value))
        if base not in self.byte_formats:
            if self.asm_hex:
                base = 'h'
            else:
                base = 'd'
        if num_bytes == 0 and value < 10 and base == 'h':
            return str(value)
        if value > 255 or num_bytes > 1:
            return self.word_formats[base].format(value)
        return self.byte_formats[base].format(value)

    def disassemble(self, start, end=65536, base=None):
        instructions = []
        address = start
        while address < end:
            byte = self.snapshot[address]
            decoder, template = self.ops[byte]
            if template is None:
                operation, length = decoder(self, address, base)
            else:
                operation, length = decoder(self, template, address, base)
            if address + length <= 65536:
                if self.asm_lower:
                    operation = convert_case(operation)
                instructions.append(Instruction(address, operation, self.snapshot[address:address + length]))
            else:
                instructions.append(self.defb_line(address, self.snapshot[address:65536]))
            address += length
        return instructions

    def defb_range(self, start, end, sublengths):
        if sublengths[0][0] or end - start <= self.defb_size:
            return [self.defb_line(start, self.snapshot[start:end], sublengths)]
        instructions = []
        data = []
        aligned = start % self.defb_mod == 0
        ready = False
        for i in range(start, end):
            data.append(self.snapshot[i])
            if not aligned and (i + 1) % self.defb_mod == 0:
                aligned = True
                ready = True
            if len(data) == self.defb_size or ready:
                instructions.append(self.defb_line(i - len(data) + 1, data, sublengths))
                data = []
                ready = False
        if data:
            instructions.append(self.defb_line(i - len(data) + 1, data, sublengths))
        return instructions

    def _defw_items(self, data, sublengths):
        items = []
        i = 0
        for length, base in sublengths:
            for j in range(i, i + length, 2):
                word = data[j] + 256 * data[j + 1]
                items.append(self.num_str(word, 2, base))
            i += length
        return ','.join(items)

    def defw_range(self, start, end, sublengths):
        if sublengths[0][0]:
            step = end - start
        else:
            step = self.defw_size
            sublengths = ((step, sublengths[0][1]),)
        instructions = []
        for address in range(start, end, step):
            data = self.snapshot[address:address + step]
            defw_dir = 'DEFW {}'.format(self._defw_items(data, sublengths))
            if self.asm_lower:
                defw_dir = convert_case(defw_dir)
            instructions.append(Instruction(address, defw_dir, data))
        return instructions

    def defm_range(self, start, end, sublengths):
        if sublengths[0][0]:
            data = self.snapshot[start:end]
            item_str = self.defb_items(data, sublengths, False)
            defm_dir = 'DEFM {}'.format(item_str)
            if self.asm_lower:
                defm_dir = convert_case(defm_dir)
            return [Instruction(start, defm_dir, data)]
        instructions = []
        msg = []
        for i in range(start, end):
            byte = self.snapshot[i]
            if 32 <= byte < 127 and byte not in (94, 96):
                msg.append(byte)
            else:
                if msg:
                    instructions.extend(self.defm_lines(i - len(msg), msg))
                    msg[:] = []
                instructions.append(self.defb_line(i, [byte]))
        if msg:
            instructions.extend(self.defm_lines(i - len(msg) + 1, msg))
        return instructions

    def defs(self, start, end, sublengths):
        size = end - start
        items = [self.num_str(value or size, base=base) for value, base in sublengths]
        defs_dir = 'DEFS {}'.format(','.join(items))
        if self.asm_lower:
            defs_dir = convert_case(defs_dir)
        return Instruction(start, defs_dir, self.snapshot[start:end])

    def ignore(self, start, end):
        return [Instruction(start, '', self.snapshot[start:end])]

    def get_message(self, data):
        message = ''
        for b in data:
            char = chr(b)
            if char in '\\"':
                message += '\\'
            message += char
        return message

    def no_arg(self, template, a, base):
        return template, 1

    def byte_arg(self, template, a, base):
        return template.format(self.num_str(self.snapshot[a + 1], 1, base)), 2

    def word_arg(self, template, a, base):
        return template.format(self.num_str(self.snapshot[a + 1] + 256 * self.snapshot[a + 2], 2, base)), 3

    def jr_arg(self, template, a, base):
        offset = self.snapshot[a + 1]
        if offset < 128:
            address = a + 2 + offset
        else:
            address = a + offset - 254
        if 0 <= address < 65536:
            return template.format(self.num_str(address, 2, base)), 2
        return self.defb(a, 2)

    def rst_arg(self, rst_address, a, base):
        return 'RST {}'.format(self.num_str(rst_address, 1, base)), 1

    def format_byte(self, value, base=None):
        if base not in self.byte_formats:
            if self.asm_hex:
                base = 'h'
            else:
                base = 'd'
        return self.byte_formats[base].format(value)

    def defb_items(self, data, sublengths, defb=True):
        if sublengths[0][0]:
            items = []
            i = 0
            for length, ctl in sublengths:
                if ctl and ctl in 'Bbdh':
                    text = False
                elif ctl == 'T':
                    text = True
                elif ctl:
                    text = defb
                else:
                    text = not defb
                chunk = data[i:i + length]
                if text:
                    items.append('"{0}"'.format(self.get_message(chunk)))
                else:
                    items.append(','.join([(self.format_byte(b, ctl)) for b in chunk]))
                i += length
        else:
            base = sublengths[0][1]
            items = [self.format_byte(b, base) for b in data]
        return ','.join(items)

    def defb_dir(self, data, sublengths=((None, None),)):
        defb_dir = 'DEFB {}'.format(self.defb_items(data, sublengths))
        if self.asm_lower:
            defb_dir = convert_case(defb_dir)
        return defb_dir

    def defb(self, a, length):
        return self.defb_dir(self.snapshot[a:a + length]), length

    def defb4(self, a, base):
        return self.defb(a, 4)

    def index(self, template, a, base):
        return template.format(self.index_offset(a, base)), 2

    def index_arg(self, template, a, base):
        if base:
            arg_base = base[-1]
        else:
            arg_base = None
        return template.format(self.index_offset(a, base), self.num_str(self.snapshot[a + 2], 1, arg_base)), 3

    def index_offset(self, a, base):
        i = self.snapshot[a + 1]
        if i < 128:
            return '+{}'.format(self.num_str(i, 1, base))
        return '-{}'.format(self.num_str(abs(i - 256), 1, base))

    def cb_arg(self, a, base):
        return self.after_CB[self.snapshot[a + 1]], 2

    def ed_arg(self, a, base):
        decoder, template = self.after_ED.get(self.snapshot[a + 1], (None, None))
        if template:
            operation, length = decoder(self, template, a + 1, base)
            return operation, length + 1
        if decoder:
            return decoder(self, a, base)
        return self.defb(a, 2)

    def dd_arg(self, a, base):
        decoder, template = self.after_DD.get(self.snapshot[a + 1], (None, None))
        if template:
            operation, length = decoder(self, template, a + 1, base)
            return operation, length + 1
        if decoder:
            return decoder(self, a, base)
        # The instruction is unchanged by the DD prefix
        return self.defb(a, 1)

    def fd_arg(self, a, base):
        operation, length = self.dd_arg(a, base)
        return operation.replace('IX', 'IY'), length

    def ddcb_arg(self, a, base):
        decoder, template = self.after_DDCB.get(self.snapshot[a + 3], (None, None))
        if template:
            operation = decoder(self, template, a + 1, base)[0]
            return operation, 4
        return self.defb(a, 4)

    def defb_line(self, address, data, sublengths=((None, None),)):
        return Instruction(address, self.defb_dir(data, sublengths), data)

    def defm_line(self, address, data):
        defm_dir = 'DEFM "{}"'.format(self.get_message(data))
        if self.asm_lower:
            defm_dir = convert_case(defm_dir)
        return Instruction(address, defm_dir, data)

    def defm_lines(self, address, data):
        lines = []
        for i in range(0, len(data), self.defm_width):
            lines.append(self.defm_line(address + i, data[i:i + self.defm_width]))
        return lines

    ops[0] = no_arg, 'NOP'
    ops[1] = word_arg, 'LD BC,{0}'
    ops[2] = no_arg, 'LD (BC),A'
    ops[3] = no_arg, 'INC BC'
    ops[4] = no_arg, 'INC B'
    ops[5] = no_arg, 'DEC B'
    ops[6] = byte_arg, 'LD B,{0}'
    ops[7] = no_arg, 'RLCA'
    ops[8] = no_arg, "EX AF,AF'"
    ops[9] = no_arg, 'ADD HL,BC'
    ops[10] = no_arg, 'LD A,(BC)'
    ops[11] = no_arg, 'DEC BC'
    ops[12] = no_arg, 'INC C'
    ops[13] = no_arg, 'DEC C'
    ops[14] = byte_arg, 'LD C,{0}'
    ops[15] = no_arg, 'RRCA'
    ops[16] = jr_arg, 'DJNZ {0}'
    ops[17] = word_arg, 'LD DE,{0}'
    ops[18] = no_arg, 'LD (DE),A'
    ops[19] = no_arg, 'INC DE'
    ops[20] = no_arg, 'INC D'
    ops[21] = no_arg, 'DEC D'
    ops[22] = byte_arg, 'LD D,{0}'
    ops[23] = no_arg, 'RLA'
    ops[24] = jr_arg, 'JR {0}'
    ops[25] = no_arg, 'ADD HL,DE'
    ops[26] = no_arg, 'LD A,(DE)'
    ops[27] = no_arg, 'DEC DE'
    ops[28] = no_arg, 'INC E'
    ops[29] = no_arg, 'DEC E'
    ops[30] = byte_arg, 'LD E,{0}'
    ops[31] = no_arg, 'RRA'
    ops[32] = jr_arg, 'JR NZ,{0}'
    ops[33] = word_arg, 'LD HL,{0}'
    ops[34] = word_arg, 'LD ({0}),HL'
    ops[35] = no_arg, 'INC HL'
    ops[36] = no_arg, 'INC H'
    ops[37] = no_arg, 'DEC H'
    ops[38] = byte_arg, 'LD H,{0}'
    ops[39] = no_arg, 'DAA'
    ops[40] = jr_arg, 'JR Z,{0}'
    ops[41] = no_arg, 'ADD HL,HL'
    ops[42] = word_arg, 'LD HL,({0})'
    ops[43] = no_arg, 'DEC HL'
    ops[44] = no_arg, 'INC L'
    ops[45] = no_arg, 'DEC L'
    ops[46] = byte_arg, 'LD L,{0}'
    ops[47] = no_arg, 'CPL'
    ops[48] = jr_arg, 'JR NC,{0}'
    ops[49] = word_arg, 'LD SP,{0}'
    ops[50] = word_arg, 'LD ({0}),A'
    ops[51] = no_arg, 'INC SP'
    ops[52] = no_arg, 'INC (HL)'
    ops[53] = no_arg, 'DEC (HL)'
    ops[54] = byte_arg, 'LD (HL),{0}'
    ops[55] = no_arg, 'SCF'
    ops[56] = jr_arg, 'JR C,{0}'
    ops[57] = no_arg, 'ADD HL,SP'
    ops[58] = word_arg, 'LD A,({0})'
    ops[59] = no_arg, 'DEC SP'
    ops[60] = no_arg, 'INC A'
    ops[61] = no_arg, 'DEC A'
    ops[62] = byte_arg, 'LD A,{0}'
    ops[63] = no_arg, 'CCF'
    ops[64] = no_arg, 'LD B,B'
    ops[65] = no_arg, 'LD B,C'
    ops[66] = no_arg, 'LD B,D'
    ops[67] = no_arg, 'LD B,E'
    ops[68] = no_arg, 'LD B,H'
    ops[69] = no_arg, 'LD B,L'
    ops[70] = no_arg, 'LD B,(HL)'
    ops[71] = no_arg, 'LD B,A'
    ops[72] = no_arg, 'LD C,B'
    ops[73] = no_arg, 'LD C,C'
    ops[74] = no_arg, 'LD C,D'
    ops[75] = no_arg, 'LD C,E'
    ops[76] = no_arg, 'LD C,H'
    ops[77] = no_arg, 'LD C,L'
    ops[78] = no_arg, 'LD C,(HL)'
    ops[79] = no_arg, 'LD C,A'
    ops[80] = no_arg, 'LD D,B'
    ops[81] = no_arg, 'LD D,C'
    ops[82] = no_arg, 'LD D,D'
    ops[83] = no_arg, 'LD D,E'
    ops[84] = no_arg, 'LD D,H'
    ops[85] = no_arg, 'LD D,L'
    ops[86] = no_arg, 'LD D,(HL)'
    ops[87] = no_arg, 'LD D,A'
    ops[88] = no_arg, 'LD E,B'
    ops[89] = no_arg, 'LD E,C'
    ops[90] = no_arg, 'LD E,D'
    ops[91] = no_arg, 'LD E,E'
    ops[92] = no_arg, 'LD E,H'
    ops[93] = no_arg, 'LD E,L'
    ops[94] = no_arg, 'LD E,(HL)'
    ops[95] = no_arg, 'LD E,A'
    ops[96] = no_arg, 'LD H,B'
    ops[97] = no_arg, 'LD H,C'
    ops[98] = no_arg, 'LD H,D'
    ops[99] = no_arg, 'LD H,E'
    ops[100] = no_arg, 'LD H,H'
    ops[101] = no_arg, 'LD H,L'
    ops[102] = no_arg, 'LD H,(HL)'
    ops[103] = no_arg, 'LD H,A'
    ops[104] = no_arg, 'LD L,B'
    ops[105] = no_arg, 'LD L,C'
    ops[106] = no_arg, 'LD L,D'
    ops[107] = no_arg, 'LD L,E'
    ops[108] = no_arg, 'LD L,H'
    ops[109] = no_arg, 'LD L,L'
    ops[110] = no_arg, 'LD L,(HL)'
    ops[111] = no_arg, 'LD L,A'
    ops[112] = no_arg, 'LD (HL),B'
    ops[113] = no_arg, 'LD (HL),C'
    ops[114] = no_arg, 'LD (HL),D'
    ops[115] = no_arg, 'LD (HL),E'
    ops[116] = no_arg, 'LD (HL),H'
    ops[117] = no_arg, 'LD (HL),L'
    ops[118] = no_arg, 'HALT'
    ops[119] = no_arg, 'LD (HL),A'
    ops[120] = no_arg, 'LD A,B'
    ops[121] = no_arg, 'LD A,C'
    ops[122] = no_arg, 'LD A,D'
    ops[123] = no_arg, 'LD A,E'
    ops[124] = no_arg, 'LD A,H'
    ops[125] = no_arg, 'LD A,L'
    ops[126] = no_arg, 'LD A,(HL)'
    ops[127] = no_arg, 'LD A,A'
    ops[128] = no_arg, 'ADD A,B'
    ops[129] = no_arg, 'ADD A,C'
    ops[130] = no_arg, 'ADD A,D'
    ops[131] = no_arg, 'ADD A,E'
    ops[132] = no_arg, 'ADD A,H'
    ops[133] = no_arg, 'ADD A,L'
    ops[134] = no_arg, 'ADD A,(HL)'
    ops[135] = no_arg, 'ADD A,A'
    ops[136] = no_arg, 'ADC A,B'
    ops[137] = no_arg, 'ADC A,C'
    ops[138] = no_arg, 'ADC A,D'
    ops[139] = no_arg, 'ADC A,E'
    ops[140] = no_arg, 'ADC A,H'
    ops[141] = no_arg, 'ADC A,L'
    ops[142] = no_arg, 'ADC A,(HL)'
    ops[143] = no_arg, 'ADC A,A'
    ops[144] = no_arg, 'SUB B'
    ops[145] = no_arg, 'SUB C'
    ops[146] = no_arg, 'SUB D'
    ops[147] = no_arg, 'SUB E'
    ops[148] = no_arg, 'SUB H'
    ops[149] = no_arg, 'SUB L'
    ops[150] = no_arg, 'SUB (HL)'
    ops[151] = no_arg, 'SUB A'
    ops[152] = no_arg, 'SBC A,B'
    ops[153] = no_arg, 'SBC A,C'
    ops[154] = no_arg, 'SBC A,D'
    ops[155] = no_arg, 'SBC A,E'
    ops[156] = no_arg, 'SBC A,H'
    ops[157] = no_arg, 'SBC A,L'
    ops[158] = no_arg, 'SBC A,(HL)'
    ops[159] = no_arg, 'SBC A,A'
    ops[160] = no_arg, 'AND B'
    ops[161] = no_arg, 'AND C'
    ops[162] = no_arg, 'AND D'
    ops[163] = no_arg, 'AND E'
    ops[164] = no_arg, 'AND H'
    ops[165] = no_arg, 'AND L'
    ops[166] = no_arg, 'AND (HL)'
    ops[167] = no_arg, 'AND A'
    ops[168] = no_arg, 'XOR B'
    ops[169] = no_arg, 'XOR C'
    ops[170] = no_arg, 'XOR D'
    ops[171] = no_arg, 'XOR E'
    ops[172] = no_arg, 'XOR H'
    ops[173] = no_arg, 'XOR L'
    ops[174] = no_arg, 'XOR (HL)'
    ops[175] = no_arg, 'XOR A'
    ops[176] = no_arg, 'OR B'
    ops[177] = no_arg, 'OR C'
    ops[178] = no_arg, 'OR D'
    ops[179] = no_arg, 'OR E'
    ops[180] = no_arg, 'OR H'
    ops[181] = no_arg, 'OR L'
    ops[182] = no_arg, 'OR (HL)'
    ops[183] = no_arg, 'OR A'
    ops[184] = no_arg, 'CP B'
    ops[185] = no_arg, 'CP C'
    ops[186] = no_arg, 'CP D'
    ops[187] = no_arg, 'CP E'
    ops[188] = no_arg, 'CP H'
    ops[189] = no_arg, 'CP L'
    ops[190] = no_arg, 'CP (HL)'
    ops[191] = no_arg, 'CP A'
    ops[192] = no_arg, 'RET NZ'
    ops[193] = no_arg, 'POP BC'
    ops[194] = word_arg, 'JP NZ,{0}'
    ops[195] = word_arg, 'JP {0}'
    ops[196] = word_arg, 'CALL NZ,{0}'
    ops[197] = no_arg, 'PUSH BC'
    ops[198] = byte_arg, 'ADD A,{0}'
    ops[199] = rst_arg, 0
    ops[200] = no_arg, 'RET Z'
    ops[201] = no_arg, 'RET'
    ops[202] = word_arg, 'JP Z,{0}'
    ops[203] = cb_arg, None
    ops[204] = word_arg, 'CALL Z,{0}'
    ops[205] = word_arg, 'CALL {0}'
    ops[206] = byte_arg, 'ADC A,{0}'
    ops[207] = rst_arg, 8
    ops[208] = no_arg, 'RET NC'
    ops[209] = no_arg, 'POP DE'
    ops[210] = word_arg, 'JP NC,{0}'
    ops[211] = byte_arg, 'OUT ({0}),A'
    ops[212] = word_arg, 'CALL NC,{0}'
    ops[213] = no_arg, 'PUSH DE'
    ops[214] = byte_arg, 'SUB {0}'
    ops[215] = rst_arg, 16
    ops[216] = no_arg, 'RET C'
    ops[217] = no_arg, 'EXX'
    ops[218] = word_arg, 'JP C,{0}'
    ops[219] = byte_arg, 'IN A,({0})'
    ops[220] = word_arg, 'CALL C,{0}'
    ops[221] = dd_arg, None
    ops[222] = byte_arg, 'SBC A,{0}'
    ops[223] = rst_arg, 24
    ops[224] = no_arg, 'RET PO'
    ops[225] = no_arg, 'POP HL'
    ops[226] = word_arg, 'JP PO,{0}'
    ops[227] = no_arg, 'EX (SP),HL'
    ops[228] = word_arg, 'CALL PO,{0}'
    ops[229] = no_arg, 'PUSH HL'
    ops[230] = byte_arg, 'AND {0}'
    ops[231] = rst_arg, 32
    ops[232] = no_arg, 'RET PE'
    ops[233] = no_arg, 'JP (HL)'
    ops[234] = word_arg, 'JP PE,{0}'
    ops[235] = no_arg, 'EX DE,HL'
    ops[236] = word_arg, 'CALL PE,{0}'
    ops[237] = ed_arg, None
    ops[238] = byte_arg, 'XOR {0}'
    ops[239] = rst_arg, 40
    ops[240] = no_arg, 'RET P'
    ops[241] = no_arg, 'POP AF'
    ops[242] = word_arg, 'JP P,{0}'
    ops[243] = no_arg, 'DI'
    ops[244] = word_arg, 'CALL P,{0}'
    ops[245] = no_arg, 'PUSH AF'
    ops[246] = byte_arg, 'OR {0}'
    ops[247] = rst_arg, 48
    ops[248] = no_arg, 'RET M'
    ops[249] = no_arg, 'LD SP,HL'
    ops[250] = word_arg, 'JP M,{0}'
    ops[251] = no_arg, 'EI'
    ops[252] = word_arg, 'CALL M,{0}'
    ops[253] = fd_arg, None
    ops[254] = byte_arg, 'CP {0}'
    ops[255] = rst_arg, 56

    after_CB[0] = 'RLC B'
    after_CB[1] = 'RLC C'
    after_CB[2] = 'RLC D'
    after_CB[3] = 'RLC E'
    after_CB[4] = 'RLC H'
    after_CB[5] = 'RLC L'
    after_CB[6] = 'RLC (HL)'
    after_CB[7] = 'RLC A'
    after_CB[8] = 'RRC B'
    after_CB[9] = 'RRC C'
    after_CB[10] = 'RRC D'
    after_CB[11] = 'RRC E'
    after_CB[12] = 'RRC H'
    after_CB[13] = 'RRC L'
    after_CB[14] = 'RRC (HL)'
    after_CB[15] = 'RRC A'
    after_CB[16] = 'RL B'
    after_CB[17] = 'RL C'
    after_CB[18] = 'RL D'
    after_CB[19] = 'RL E'
    after_CB[20] = 'RL H'
    after_CB[21] = 'RL L'
    after_CB[22] = 'RL (HL)'
    after_CB[23] = 'RL A'
    after_CB[24] = 'RR B'
    after_CB[25] = 'RR C'
    after_CB[26] = 'RR D'
    after_CB[27] = 'RR E'
    after_CB[28] = 'RR H'
    after_CB[29] = 'RR L'
    after_CB[30] = 'RR (HL)'
    after_CB[31] = 'RR A'
    after_CB[32] = 'SLA B'
    after_CB[33] = 'SLA C'
    after_CB[34] = 'SLA D'
    after_CB[35] = 'SLA E'
    after_CB[36] = 'SLA H'
    after_CB[37] = 'SLA L'
    after_CB[38] = 'SLA (HL)'
    after_CB[39] = 'SLA A'
    after_CB[40] = 'SRA B'
    after_CB[41] = 'SRA C'
    after_CB[42] = 'SRA D'
    after_CB[43] = 'SRA E'
    after_CB[44] = 'SRA H'
    after_CB[45] = 'SRA L'
    after_CB[46] = 'SRA (HL)'
    after_CB[47] = 'SRA A'
    after_CB[48] = 'SLL B'
    after_CB[49] = 'SLL C'
    after_CB[50] = 'SLL D'
    after_CB[51] = 'SLL E'
    after_CB[52] = 'SLL H'
    after_CB[53] = 'SLL L'
    after_CB[54] = 'SLL (HL)'
    after_CB[55] = 'SLL A'
    after_CB[56] = 'SRL B'
    after_CB[57] = 'SRL C'
    after_CB[58] = 'SRL D'
    after_CB[59] = 'SRL E'
    after_CB[60] = 'SRL H'
    after_CB[61] = 'SRL L'
    after_CB[62] = 'SRL (HL)'
    after_CB[63] = 'SRL A'
    after_CB[64] = 'BIT 0,B'
    after_CB[65] = 'BIT 0,C'
    after_CB[66] = 'BIT 0,D'
    after_CB[67] = 'BIT 0,E'
    after_CB[68] = 'BIT 0,H'
    after_CB[69] = 'BIT 0,L'
    after_CB[70] = 'BIT 0,(HL)'
    after_CB[71] = 'BIT 0,A'
    after_CB[72] = 'BIT 1,B'
    after_CB[73] = 'BIT 1,C'
    after_CB[74] = 'BIT 1,D'
    after_CB[75] = 'BIT 1,E'
    after_CB[76] = 'BIT 1,H'
    after_CB[77] = 'BIT 1,L'
    after_CB[78] = 'BIT 1,(HL)'
    after_CB[79] = 'BIT 1,A'
    after_CB[80] = 'BIT 2,B'
    after_CB[81] = 'BIT 2,C'
    after_CB[82] = 'BIT 2,D'
    after_CB[83] = 'BIT 2,E'
    after_CB[84] = 'BIT 2,H'
    after_CB[85] = 'BIT 2,L'
    after_CB[86] = 'BIT 2,(HL)'
    after_CB[87] = 'BIT 2,A'
    after_CB[88] = 'BIT 3,B'
    after_CB[89] = 'BIT 3,C'
    after_CB[90] = 'BIT 3,D'
    after_CB[91] = 'BIT 3,E'
    after_CB[92] = 'BIT 3,H'
    after_CB[93] = 'BIT 3,L'
    after_CB[94] = 'BIT 3,(HL)'
    after_CB[95] = 'BIT 3,A'
    after_CB[96] = 'BIT 4,B'
    after_CB[97] = 'BIT 4,C'
    after_CB[98] = 'BIT 4,D'
    after_CB[99] = 'BIT 4,E'
    after_CB[100] = 'BIT 4,H'
    after_CB[101] = 'BIT 4,L'
    after_CB[102] = 'BIT 4,(HL)'
    after_CB[103] = 'BIT 4,A'
    after_CB[104] = 'BIT 5,B'
    after_CB[105] = 'BIT 5,C'
    after_CB[106] = 'BIT 5,D'
    after_CB[107] = 'BIT 5,E'
    after_CB[108] = 'BIT 5,H'
    after_CB[109] = 'BIT 5,L'
    after_CB[110] = 'BIT 5,(HL)'
    after_CB[111] = 'BIT 5,A'
    after_CB[112] = 'BIT 6,B'
    after_CB[113] = 'BIT 6,C'
    after_CB[114] = 'BIT 6,D'
    after_CB[115] = 'BIT 6,E'
    after_CB[116] = 'BIT 6,H'
    after_CB[117] = 'BIT 6,L'
    after_CB[118] = 'BIT 6,(HL)'
    after_CB[119] = 'BIT 6,A'
    after_CB[120] = 'BIT 7,B'
    after_CB[121] = 'BIT 7,C'
    after_CB[122] = 'BIT 7,D'
    after_CB[123] = 'BIT 7,E'
    after_CB[124] = 'BIT 7,H'
    after_CB[125] = 'BIT 7,L'
    after_CB[126] = 'BIT 7,(HL)'
    after_CB[127] = 'BIT 7,A'
    after_CB[128] = 'RES 0,B'
    after_CB[129] = 'RES 0,C'
    after_CB[130] = 'RES 0,D'
    after_CB[131] = 'RES 0,E'
    after_CB[132] = 'RES 0,H'
    after_CB[133] = 'RES 0,L'
    after_CB[134] = 'RES 0,(HL)'
    after_CB[135] = 'RES 0,A'
    after_CB[136] = 'RES 1,B'
    after_CB[137] = 'RES 1,C'
    after_CB[138] = 'RES 1,D'
    after_CB[139] = 'RES 1,E'
    after_CB[140] = 'RES 1,H'
    after_CB[141] = 'RES 1,L'
    after_CB[142] = 'RES 1,(HL)'
    after_CB[143] = 'RES 1,A'
    after_CB[144] = 'RES 2,B'
    after_CB[145] = 'RES 2,C'
    after_CB[146] = 'RES 2,D'
    after_CB[147] = 'RES 2,E'
    after_CB[148] = 'RES 2,H'
    after_CB[149] = 'RES 2,L'
    after_CB[150] = 'RES 2,(HL)'
    after_CB[151] = 'RES 2,A'
    after_CB[152] = 'RES 3,B'
    after_CB[153] = 'RES 3,C'
    after_CB[154] = 'RES 3,D'
    after_CB[155] = 'RES 3,E'
    after_CB[156] = 'RES 3,H'
    after_CB[157] = 'RES 3,L'
    after_CB[158] = 'RES 3,(HL)'
    after_CB[159] = 'RES 3,A'
    after_CB[160] = 'RES 4,B'
    after_CB[161] = 'RES 4,C'
    after_CB[162] = 'RES 4,D'
    after_CB[163] = 'RES 4,E'
    after_CB[164] = 'RES 4,H'
    after_CB[165] = 'RES 4,L'
    after_CB[166] = 'RES 4,(HL)'
    after_CB[167] = 'RES 4,A'
    after_CB[168] = 'RES 5,B'
    after_CB[169] = 'RES 5,C'
    after_CB[170] = 'RES 5,D'
    after_CB[171] = 'RES 5,E'
    after_CB[172] = 'RES 5,H'
    after_CB[173] = 'RES 5,L'
    after_CB[174] = 'RES 5,(HL)'
    after_CB[175] = 'RES 5,A'
    after_CB[176] = 'RES 6,B'
    after_CB[177] = 'RES 6,C'
    after_CB[178] = 'RES 6,D'
    after_CB[179] = 'RES 6,E'
    after_CB[180] = 'RES 6,H'
    after_CB[181] = 'RES 6,L'
    after_CB[182] = 'RES 6,(HL)'
    after_CB[183] = 'RES 6,A'
    after_CB[184] = 'RES 7,B'
    after_CB[185] = 'RES 7,C'
    after_CB[186] = 'RES 7,D'
    after_CB[187] = 'RES 7,E'
    after_CB[188] = 'RES 7,H'
    after_CB[189] = 'RES 7,L'
    after_CB[190] = 'RES 7,(HL)'
    after_CB[191] = 'RES 7,A'
    after_CB[192] = 'SET 0,B'
    after_CB[193] = 'SET 0,C'
    after_CB[194] = 'SET 0,D'
    after_CB[195] = 'SET 0,E'
    after_CB[196] = 'SET 0,H'
    after_CB[197] = 'SET 0,L'
    after_CB[198] = 'SET 0,(HL)'
    after_CB[199] = 'SET 0,A'
    after_CB[200] = 'SET 1,B'
    after_CB[201] = 'SET 1,C'
    after_CB[202] = 'SET 1,D'
    after_CB[203] = 'SET 1,E'
    after_CB[204] = 'SET 1,H'
    after_CB[205] = 'SET 1,L'
    after_CB[206] = 'SET 1,(HL)'
    after_CB[207] = 'SET 1,A'
    after_CB[208] = 'SET 2,B'
    after_CB[209] = 'SET 2,C'
    after_CB[210] = 'SET 2,D'
    after_CB[211] = 'SET 2,E'
    after_CB[212] = 'SET 2,H'
    after_CB[213] = 'SET 2,L'
    after_CB[214] = 'SET 2,(HL)'
    after_CB[215] = 'SET 2,A'
    after_CB[216] = 'SET 3,B'
    after_CB[217] = 'SET 3,C'
    after_CB[218] = 'SET 3,D'
    after_CB[219] = 'SET 3,E'
    after_CB[220] = 'SET 3,H'
    after_CB[221] = 'SET 3,L'
    after_CB[222] = 'SET 3,(HL)'
    after_CB[223] = 'SET 3,A'
    after_CB[224] = 'SET 4,B'
    after_CB[225] = 'SET 4,C'
    after_CB[226] = 'SET 4,D'
    after_CB[227] = 'SET 4,E'
    after_CB[228] = 'SET 4,H'
    after_CB[229] = 'SET 4,L'
    after_CB[230] = 'SET 4,(HL)'
    after_CB[231] = 'SET 4,A'
    after_CB[232] = 'SET 5,B'
    after_CB[233] = 'SET 5,C'
    after_CB[234] = 'SET 5,D'
    after_CB[235] = 'SET 5,E'
    after_CB[236] = 'SET 5,H'
    after_CB[237] = 'SET 5,L'
    after_CB[238] = 'SET 5,(HL)'
    after_CB[239] = 'SET 5,A'
    after_CB[240] = 'SET 6,B'
    after_CB[241] = 'SET 6,C'
    after_CB[242] = 'SET 6,D'
    after_CB[243] = 'SET 6,E'
    after_CB[244] = 'SET 6,H'
    after_CB[245] = 'SET 6,L'
    after_CB[246] = 'SET 6,(HL)'
    after_CB[247] = 'SET 6,A'
    after_CB[248] = 'SET 7,B'
    after_CB[249] = 'SET 7,C'
    after_CB[250] = 'SET 7,D'
    after_CB[251] = 'SET 7,E'
    after_CB[252] = 'SET 7,H'
    after_CB[253] = 'SET 7,L'
    after_CB[254] = 'SET 7,(HL)'
    after_CB[255] = 'SET 7,A'

    after_DD[9] = no_arg, 'ADD IX,BC'
    after_DD[25] = no_arg, 'ADD IX,DE'
    after_DD[33] = word_arg, 'LD IX,{0}'
    after_DD[34] = word_arg, 'LD ({0}),IX'
    after_DD[35] = no_arg, 'INC IX'
    after_DD[36] = no_arg, 'INC IXh'
    after_DD[37] = no_arg, 'DEC IXh'
    after_DD[38] = byte_arg, 'LD IXh,{0}'
    after_DD[41] = no_arg, 'ADD IX,IX'
    after_DD[42] = word_arg, 'LD IX,({0})'
    after_DD[43] = no_arg, 'DEC IX'
    after_DD[44] = no_arg, 'INC IXl'
    after_DD[45] = no_arg, 'DEC IXl'
    after_DD[46] = byte_arg, 'LD IXl,{0}'
    after_DD[52] = index, 'INC (IX{0})'
    after_DD[53] = index, 'DEC (IX{0})'
    after_DD[54] = index_arg, 'LD (IX{0}),{1}'
    after_DD[57] = no_arg, 'ADD IX,SP'
    after_DD[68] = no_arg, 'LD B,IXh'
    after_DD[69] = no_arg, 'LD B,IXl'
    after_DD[70] = index, 'LD B,(IX{0})'
    after_DD[76] = no_arg, 'LD C,IXh'
    after_DD[77] = no_arg, 'LD C,IXl'
    after_DD[78] = index, 'LD C,(IX{0})'
    after_DD[84] = no_arg, 'LD D,IXh'
    after_DD[85] = no_arg, 'LD D,IXl'
    after_DD[86] = index, 'LD D,(IX{0})'
    after_DD[92] = no_arg, 'LD E,IXh'
    after_DD[93] = no_arg, 'LD E,IXl'
    after_DD[94] = index, 'LD E,(IX{0})'
    after_DD[96] = no_arg, 'LD IXh,B'
    after_DD[97] = no_arg, 'LD IXh,C'
    after_DD[98] = no_arg, 'LD IXh,D'
    after_DD[99] = no_arg, 'LD IXh,E'
    after_DD[100] = no_arg, 'LD IXh,IXh'
    after_DD[101] = no_arg, 'LD IXh,IXl'
    after_DD[102] = index, 'LD H,(IX{0})'
    after_DD[103] = no_arg, 'LD IXh,A'
    after_DD[104] = no_arg, 'LD IXl,B'
    after_DD[105] = no_arg, 'LD IXl,C'
    after_DD[106] = no_arg, 'LD IXl,D'
    after_DD[107] = no_arg, 'LD IXl,E'
    after_DD[108] = no_arg, 'LD IXl,IXh'
    after_DD[109] = no_arg, 'LD IXl,IXl'
    after_DD[110] = index, 'LD L,(IX{0})'
    after_DD[111] = no_arg, 'LD IXl,A'
    after_DD[112] = index, 'LD (IX{0}),B'
    after_DD[113] = index, 'LD (IX{0}),C'
    after_DD[114] = index, 'LD (IX{0}),D'
    after_DD[115] = index, 'LD (IX{0}),E'
    after_DD[116] = index, 'LD (IX{0}),H'
    after_DD[117] = index, 'LD (IX{0}),L'
    after_DD[119] = index, 'LD (IX{0}),A'
    after_DD[124] = no_arg, 'LD A,IXh'
    after_DD[125] = no_arg, 'LD A,IXl'
    after_DD[126] = index, 'LD A,(IX{0})'
    after_DD[132] = no_arg, 'ADD A,IXh'
    after_DD[133] = no_arg, 'ADD A,IXl'
    after_DD[134] = index, 'ADD A,(IX{0})'
    after_DD[140] = no_arg, 'ADC A,IXh'
    after_DD[141] = no_arg, 'ADC A,IXl'
    after_DD[142] = index, 'ADC A,(IX{0})'
    after_DD[148] = no_arg, 'SUB IXh'
    after_DD[149] = no_arg, 'SUB IXl'
    after_DD[150] = index, 'SUB (IX{0})'
    after_DD[156] = no_arg, 'SBC A,IXh'
    after_DD[157] = no_arg, 'SBC A,IXl'
    after_DD[158] = index, 'SBC A,(IX{0})'
    after_DD[164] = no_arg, 'AND IXh'
    after_DD[165] = no_arg, 'AND IXl'
    after_DD[166] = index, 'AND (IX{0})'
    after_DD[172] = no_arg, 'XOR IXh'
    after_DD[173] = no_arg, 'XOR IXl'
    after_DD[174] = index, 'XOR (IX{0})'
    after_DD[180] = no_arg, 'OR IXh'
    after_DD[181] = no_arg, 'OR IXl'
    after_DD[182] = index, 'OR (IX{0})'
    after_DD[188] = no_arg, 'CP IXh'
    after_DD[189] = no_arg, 'CP IXl'
    after_DD[190] = index, 'CP (IX{0})'
    after_DD[203] = ddcb_arg, None
    after_DD[225] = no_arg, 'POP IX'
    after_DD[227] = no_arg, 'EX (SP),IX'
    after_DD[229] = no_arg, 'PUSH IX'
    after_DD[233] = no_arg, 'JP (IX)'
    after_DD[249] = no_arg, 'LD SP,IX'

    after_ED[64] = no_arg, 'IN B,(C)'
    after_ED[65] = no_arg, 'OUT (C),B'
    after_ED[66] = no_arg, 'SBC HL,BC'
    after_ED[67] = word_arg, 'LD ({0}),BC'
    after_ED[68] = no_arg, 'NEG'
    after_ED[69] = no_arg, 'RETN'
    after_ED[70] = no_arg, 'IM 0'
    after_ED[71] = no_arg, 'LD I,A'
    after_ED[72] = no_arg, 'IN C,(C)'
    after_ED[73] = no_arg, 'OUT (C),C'
    after_ED[74] = no_arg, 'ADC HL,BC'
    after_ED[75] = word_arg, 'LD BC,({0})'
    after_ED[77] = no_arg, 'RETI'
    after_ED[79] = no_arg, 'LD R,A'
    after_ED[80] = no_arg, 'IN D,(C)'
    after_ED[81] = no_arg, 'OUT (C),D'
    after_ED[82] = no_arg, 'SBC HL,DE'
    after_ED[83] = word_arg, 'LD ({0}),DE'
    after_ED[86] = no_arg, 'IM 1'
    after_ED[87] = no_arg, 'LD A,I'
    after_ED[88] = no_arg, 'IN E,(C)'
    after_ED[89] = no_arg, 'OUT (C),E'
    after_ED[90] = no_arg, 'ADC HL,DE'
    after_ED[91] = word_arg, 'LD DE,({0})'
    after_ED[94] = no_arg, 'IM 2'
    after_ED[95] = no_arg, 'LD A,R'
    after_ED[96] = no_arg, 'IN H,(C)'
    after_ED[97] = no_arg, 'OUT (C),H'
    after_ED[98] = no_arg, 'SBC HL,HL'
    # ED63 is 'LD (nn),HL', but if we disassemble to that, it won't assemble
    # back to the same bytes
    after_ED[99] = defb4, None
    after_ED[103] = no_arg, 'RRD'
    after_ED[104] = no_arg, 'IN L,(C)'
    after_ED[105] = no_arg, 'OUT (C),L'
    after_ED[106] = no_arg, 'ADC HL,HL'
    # ED6B is 'LD HL,(nn)', but if we disassemble to that, it won't assemble
    # back to the same bytes
    after_ED[107] = defb4, None
    after_ED[111] = no_arg, 'RLD'
    after_ED[114] = no_arg, 'SBC HL,SP'
    after_ED[115] = word_arg, 'LD ({0}),SP'
    after_ED[120] = no_arg, 'IN A,(C)'
    after_ED[121] = no_arg, 'OUT (C),A'
    after_ED[122] = no_arg, 'ADC HL,SP'
    after_ED[123] = word_arg, 'LD SP,({0})'
    after_ED[160] = no_arg, 'LDI'
    after_ED[161] = no_arg, 'CPI'
    after_ED[162] = no_arg, 'INI'
    after_ED[163] = no_arg, 'OUTI'
    after_ED[168] = no_arg, 'LDD'
    after_ED[169] = no_arg, 'CPD'
    after_ED[170] = no_arg, 'IND'
    after_ED[171] = no_arg, 'OUTD'
    after_ED[176] = no_arg, 'LDIR'
    after_ED[177] = no_arg, 'CPIR'
    after_ED[178] = no_arg, 'INIR'
    after_ED[179] = no_arg, 'OTIR'
    after_ED[184] = no_arg, 'LDDR'
    after_ED[185] = no_arg, 'CPDR'
    after_ED[186] = no_arg, 'INDR'
    after_ED[187] = no_arg, 'OTDR'

    after_DDCB[6] = index, 'RLC (IX{0})'
    after_DDCB[14] = index, 'RRC (IX{0})'
    after_DDCB[22] = index, 'RL (IX{0})'
    after_DDCB[30] = index, 'RR (IX{0})'
    after_DDCB[38] = index, 'SLA (IX{0})'
    after_DDCB[46] = index, 'SRA (IX{0})'
    after_DDCB[54] = index, 'SLL (IX{0})'
    after_DDCB[62] = index, 'SRL (IX{0})'
    after_DDCB[70] = index, 'BIT 0,(IX{0})'
    after_DDCB[78] = index, 'BIT 1,(IX{0})'
    after_DDCB[86] = index, 'BIT 2,(IX{0})'
    after_DDCB[94] = index, 'BIT 3,(IX{0})'
    after_DDCB[102] = index, 'BIT 4,(IX{0})'
    after_DDCB[110] = index, 'BIT 5,(IX{0})'
    after_DDCB[118] = index, 'BIT 6,(IX{0})'
    after_DDCB[126] = index, 'BIT 7,(IX{0})'
    after_DDCB[134] = index, 'RES 0,(IX{0})'
    after_DDCB[142] = index, 'RES 1,(IX{0})'
    after_DDCB[150] = index, 'RES 2,(IX{0})'
    after_DDCB[158] = index, 'RES 3,(IX{0})'
    after_DDCB[166] = index, 'RES 4,(IX{0})'
    after_DDCB[174] = index, 'RES 5,(IX{0})'
    after_DDCB[182] = index, 'RES 6,(IX{0})'
    after_DDCB[190] = index, 'RES 7,(IX{0})'
    after_DDCB[198] = index, 'SET 0,(IX{0})'
    after_DDCB[206] = index, 'SET 1,(IX{0})'
    after_DDCB[214] = index, 'SET 2,(IX{0})'
    after_DDCB[222] = index, 'SET 3,(IX{0})'
    after_DDCB[230] = index, 'SET 4,(IX{0})'
    after_DDCB[238] = index, 'SET 5,(IX{0})'
    after_DDCB[246] = index, 'SET 6,(IX{0})'
    after_DDCB[254] = index, 'SET 7,(IX{0})'
