# Copyright 2010-2015, 2017, 2018 Richard Dymond (rjdymond@gmail.com)
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

from skoolkit import is_char
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

    def num_str(self, value, num_bytes=1, base=None):
        if base:
            base = base[0]
        if base == 'c' and is_char(value & 127):
            if value & 128:
                suffix = '+' + self.num_str(128)
            else:
                suffix = ''
            if value & 127 in (34, 92):
                return r'"\{}"'.format(chr(value & 127)) + suffix
            return '"{}"'.format(chr(value & 127)) + suffix
        sign = ''
        if base == 'm':
            sign = '-'
            if num_bytes == 1:
                value = 256 - value
            else:
                value = 65536 - value
        if base not in self.byte_formats:
            if self.asm_hex:
                base = 'h'
            else:
                base = 'd'
        if value > 255 or num_bytes > 1:
            return sign + self.word_formats[base].format(value)
        return sign + self.byte_formats[base].format(value)

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
            if is_char(byte):
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
        data = self.snapshot[start:end]
        values = set(data)
        if len(values) > 1:
            return self.defb_range(start, end, ((end - start, None),))
        value = values.pop()
        size, base = sublengths[0]
        items = [self.num_str(size or end - start, base=base)]
        if len(sublengths) > 1:
            items.append(self.num_str(value, base=sublengths[1][1]))
        elif value:
            items.append(self.num_str(value))
        defs_dir = 'DEFS {}'.format(','.join(items))
        if self.asm_lower:
            defs_dir = convert_case(defs_dir)
        return [Instruction(start, defs_dir, data)]

    def ignore(self, start, end):
        return [Instruction(start, '', self.snapshot[start:end])]

    def get_message(self, data):
        items = []
        for b in data:
            if is_char(b):
                char = chr(b)
                if char in '\\"':
                    char = '\\' + char
                if items and items[-1].startswith('"'):
                    items[-1] += char
                else:
                    items.append('"' + char)
            else:
                if items and items[-1].startswith('"'):
                    items[-1] += '"'
                items.append(self.num_str(b))
        if items[-1].startswith('"'):
            items[-1] += '"'
        return ','.join(items)

    def no_arg(self, template, a, base):
        return template, 1

    def byte_arg(self, template, a, base):
        return template.format(self.num_str(self.snapshot[(a + 1) & 65535], 1, base)), 2

    def word_arg(self, template, a, base):
        return template.format(self.num_str(self.snapshot[(a + 1) & 65535] + 256 * self.snapshot[(a + 2) & 65535], 2, base)), 3

    def jr_arg(self, template, a, base):
        offset = self.snapshot[(a + 1) & 65535]
        if offset < 128:
            address = a + 2 + offset
        else:
            address = a + offset - 254
        if 0 <= address < 65536:
            return template.format(self.num_str(address, 2, base)), 2
        return self.defb(a, 2)

    def rst_arg(self, rst_address, a, base):
        return 'RST {}'.format(self.num_str(rst_address, 1, base)), 1

    def defb_items(self, data, sublengths, defb=True):
        if sublengths[0][0]:
            items = []
            i = 0
            for length, ctl in sublengths:
                if ctl and ctl in 'Bbdhmn':
                    text = False
                elif ctl == 'T':
                    text = True
                elif ctl:
                    text = defb
                else:
                    text = not defb
                chunk = data[i:i + length]
                if text:
                    if length == 1:
                        items.append(self.num_str(chunk[0], base='c'))
                    else:
                        items.append(self.get_message(chunk))
                else:
                    items.append(','.join(self.num_str(b, 1, ctl) for b in chunk))
                i += length
        else:
            base = sublengths[0][1]
            items = [self.num_str(b, 1, base) for b in data]
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
        return template.format(self.index_offset(a, base), self.num_str(self.snapshot[(a + 2) & 65535], 1, arg_base)), 3

    def index_offset(self, a, base):
        i = self.snapshot[(a + 1) & 65535]
        if i < 128:
            return '+{}'.format(self.num_str(i, 1, base))
        return '-{}'.format(self.num_str(abs(i - 256), 1, base))

    def cb_arg(self, a, base):
        return self.after_CB[self.snapshot[(a + 1) & 65535]], 2

    def ed_arg(self, a, base):
        decoder, template = self.after_ED.get(self.snapshot[(a + 1) & 65535], (None, None))
        if template:
            operation, length = decoder(self, template, a + 1, base)
            return operation, length + 1
        if decoder:
            return decoder(self, a, base)
        return self.defb(a, 2)

    def dd_arg(self, a, base):
        decoder, template = self.after_DD.get(self.snapshot[(a + 1) & 65535], (None, None))
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
        decoder, template = self.after_DDCB.get(self.snapshot[(a + 3) & 65535], (None, None))
        if template:
            operation = decoder(self, template, a + 1, base)[0]
            return operation, 4
        return self.defb(a, 4)

    def defb_line(self, address, data, sublengths=((None, None),)):
        return Instruction(address, self.defb_dir(data, sublengths), data)

    def defm_line(self, address, data):
        defm_dir = 'DEFM {}'.format(self.get_message(data))
        if self.asm_lower:
            defm_dir = convert_case(defm_dir)
        return Instruction(address, defm_dir, data)

    def defm_lines(self, address, data):
        lines = []
        for i in range(0, len(data), self.defm_width):
            lines.append(self.defm_line(address + i, data[i:i + self.defm_width]))
        return lines

    ops = {
        0x00: (no_arg, 'NOP'),
        0x01: (word_arg, 'LD BC,{}'),
        0x02: (no_arg, 'LD (BC),A'),
        0x03: (no_arg, 'INC BC'),
        0x04: (no_arg, 'INC B'),
        0x05: (no_arg, 'DEC B'),
        0x06: (byte_arg, 'LD B,{}'),
        0x07: (no_arg, 'RLCA'),
        0x08: (no_arg, "EX AF,AF'"),
        0x09: (no_arg, 'ADD HL,BC'),
        0x0A: (no_arg, 'LD A,(BC)'),
        0x0B: (no_arg, 'DEC BC'),
        0x0C: (no_arg, 'INC C'),
        0x0D: (no_arg, 'DEC C'),
        0x0E: (byte_arg, 'LD C,{}'),
        0x0F: (no_arg, 'RRCA'),
        0x10: (jr_arg, 'DJNZ {}'),
        0x11: (word_arg, 'LD DE,{}'),
        0x12: (no_arg, 'LD (DE),A'),
        0x13: (no_arg, 'INC DE'),
        0x14: (no_arg, 'INC D'),
        0x15: (no_arg, 'DEC D'),
        0x16: (byte_arg, 'LD D,{}'),
        0x17: (no_arg, 'RLA'),
        0x18: (jr_arg, 'JR {}'),
        0x19: (no_arg, 'ADD HL,DE'),
        0x1A: (no_arg, 'LD A,(DE)'),
        0x1B: (no_arg, 'DEC DE'),
        0x1C: (no_arg, 'INC E'),
        0x1D: (no_arg, 'DEC E'),
        0x1E: (byte_arg, 'LD E,{}'),
        0x1F: (no_arg, 'RRA'),
        0x20: (jr_arg, 'JR NZ,{}'),
        0x21: (word_arg, 'LD HL,{}'),
        0x22: (word_arg, 'LD ({}),HL'),
        0x23: (no_arg, 'INC HL'),
        0x24: (no_arg, 'INC H'),
        0x25: (no_arg, 'DEC H'),
        0x26: (byte_arg, 'LD H,{}'),
        0x27: (no_arg, 'DAA'),
        0x28: (jr_arg, 'JR Z,{}'),
        0x29: (no_arg, 'ADD HL,HL'),
        0x2A: (word_arg, 'LD HL,({})'),
        0x2B: (no_arg, 'DEC HL'),
        0x2C: (no_arg, 'INC L'),
        0x2D: (no_arg, 'DEC L'),
        0x2E: (byte_arg, 'LD L,{}'),
        0x2F: (no_arg, 'CPL'),
        0x30: (jr_arg, 'JR NC,{}'),
        0x31: (word_arg, 'LD SP,{}'),
        0x32: (word_arg, 'LD ({}),A'),
        0x33: (no_arg, 'INC SP'),
        0x34: (no_arg, 'INC (HL)'),
        0x35: (no_arg, 'DEC (HL)'),
        0x36: (byte_arg, 'LD (HL),{}'),
        0x37: (no_arg, 'SCF'),
        0x38: (jr_arg, 'JR C,{}'),
        0x39: (no_arg, 'ADD HL,SP'),
        0x3A: (word_arg, 'LD A,({})'),
        0x3B: (no_arg, 'DEC SP'),
        0x3C: (no_arg, 'INC A'),
        0x3D: (no_arg, 'DEC A'),
        0x3E: (byte_arg, 'LD A,{}'),
        0x3F: (no_arg, 'CCF'),
        0x40: (no_arg, 'LD B,B'),
        0x41: (no_arg, 'LD B,C'),
        0x42: (no_arg, 'LD B,D'),
        0x43: (no_arg, 'LD B,E'),
        0x44: (no_arg, 'LD B,H'),
        0x45: (no_arg, 'LD B,L'),
        0x46: (no_arg, 'LD B,(HL)'),
        0x47: (no_arg, 'LD B,A'),
        0x48: (no_arg, 'LD C,B'),
        0x49: (no_arg, 'LD C,C'),
        0x4A: (no_arg, 'LD C,D'),
        0x4B: (no_arg, 'LD C,E'),
        0x4C: (no_arg, 'LD C,H'),
        0x4D: (no_arg, 'LD C,L'),
        0x4E: (no_arg, 'LD C,(HL)'),
        0x4F: (no_arg, 'LD C,A'),
        0x50: (no_arg, 'LD D,B'),
        0x51: (no_arg, 'LD D,C'),
        0x52: (no_arg, 'LD D,D'),
        0x53: (no_arg, 'LD D,E'),
        0x54: (no_arg, 'LD D,H'),
        0x55: (no_arg, 'LD D,L'),
        0x56: (no_arg, 'LD D,(HL)'),
        0x57: (no_arg, 'LD D,A'),
        0x58: (no_arg, 'LD E,B'),
        0x59: (no_arg, 'LD E,C'),
        0x5A: (no_arg, 'LD E,D'),
        0x5B: (no_arg, 'LD E,E'),
        0x5C: (no_arg, 'LD E,H'),
        0x5D: (no_arg, 'LD E,L'),
        0x5E: (no_arg, 'LD E,(HL)'),
        0x5F: (no_arg, 'LD E,A'),
        0x60: (no_arg, 'LD H,B'),
        0x61: (no_arg, 'LD H,C'),
        0x62: (no_arg, 'LD H,D'),
        0x63: (no_arg, 'LD H,E'),
        0x64: (no_arg, 'LD H,H'),
        0x65: (no_arg, 'LD H,L'),
        0x66: (no_arg, 'LD H,(HL)'),
        0x67: (no_arg, 'LD H,A'),
        0x68: (no_arg, 'LD L,B'),
        0x69: (no_arg, 'LD L,C'),
        0x6A: (no_arg, 'LD L,D'),
        0x6B: (no_arg, 'LD L,E'),
        0x6C: (no_arg, 'LD L,H'),
        0x6D: (no_arg, 'LD L,L'),
        0x6E: (no_arg, 'LD L,(HL)'),
        0x6F: (no_arg, 'LD L,A'),
        0x70: (no_arg, 'LD (HL),B'),
        0x71: (no_arg, 'LD (HL),C'),
        0x72: (no_arg, 'LD (HL),D'),
        0x73: (no_arg, 'LD (HL),E'),
        0x74: (no_arg, 'LD (HL),H'),
        0x75: (no_arg, 'LD (HL),L'),
        0x76: (no_arg, 'HALT'),
        0x77: (no_arg, 'LD (HL),A'),
        0x78: (no_arg, 'LD A,B'),
        0x79: (no_arg, 'LD A,C'),
        0x7A: (no_arg, 'LD A,D'),
        0x7B: (no_arg, 'LD A,E'),
        0x7C: (no_arg, 'LD A,H'),
        0x7D: (no_arg, 'LD A,L'),
        0x7E: (no_arg, 'LD A,(HL)'),
        0x7F: (no_arg, 'LD A,A'),
        0x80: (no_arg, 'ADD A,B'),
        0x81: (no_arg, 'ADD A,C'),
        0x82: (no_arg, 'ADD A,D'),
        0x83: (no_arg, 'ADD A,E'),
        0x84: (no_arg, 'ADD A,H'),
        0x85: (no_arg, 'ADD A,L'),
        0x86: (no_arg, 'ADD A,(HL)'),
        0x87: (no_arg, 'ADD A,A'),
        0x88: (no_arg, 'ADC A,B'),
        0x89: (no_arg, 'ADC A,C'),
        0x8A: (no_arg, 'ADC A,D'),
        0x8B: (no_arg, 'ADC A,E'),
        0x8C: (no_arg, 'ADC A,H'),
        0x8D: (no_arg, 'ADC A,L'),
        0x8E: (no_arg, 'ADC A,(HL)'),
        0x8F: (no_arg, 'ADC A,A'),
        0x90: (no_arg, 'SUB B'),
        0x91: (no_arg, 'SUB C'),
        0x92: (no_arg, 'SUB D'),
        0x93: (no_arg, 'SUB E'),
        0x94: (no_arg, 'SUB H'),
        0x95: (no_arg, 'SUB L'),
        0x96: (no_arg, 'SUB (HL)'),
        0x97: (no_arg, 'SUB A'),
        0x98: (no_arg, 'SBC A,B'),
        0x99: (no_arg, 'SBC A,C'),
        0x9A: (no_arg, 'SBC A,D'),
        0x9B: (no_arg, 'SBC A,E'),
        0x9C: (no_arg, 'SBC A,H'),
        0x9D: (no_arg, 'SBC A,L'),
        0x9E: (no_arg, 'SBC A,(HL)'),
        0x9F: (no_arg, 'SBC A,A'),
        0xA0: (no_arg, 'AND B'),
        0xA1: (no_arg, 'AND C'),
        0xA2: (no_arg, 'AND D'),
        0xA3: (no_arg, 'AND E'),
        0xA4: (no_arg, 'AND H'),
        0xA5: (no_arg, 'AND L'),
        0xA6: (no_arg, 'AND (HL)'),
        0xA7: (no_arg, 'AND A'),
        0xA8: (no_arg, 'XOR B'),
        0xA9: (no_arg, 'XOR C'),
        0xAA: (no_arg, 'XOR D'),
        0xAB: (no_arg, 'XOR E'),
        0xAC: (no_arg, 'XOR H'),
        0xAD: (no_arg, 'XOR L'),
        0xAE: (no_arg, 'XOR (HL)'),
        0xAF: (no_arg, 'XOR A'),
        0xB0: (no_arg, 'OR B'),
        0xB1: (no_arg, 'OR C'),
        0xB2: (no_arg, 'OR D'),
        0xB3: (no_arg, 'OR E'),
        0xB4: (no_arg, 'OR H'),
        0xB5: (no_arg, 'OR L'),
        0xB6: (no_arg, 'OR (HL)'),
        0xB7: (no_arg, 'OR A'),
        0xB8: (no_arg, 'CP B'),
        0xB9: (no_arg, 'CP C'),
        0xBA: (no_arg, 'CP D'),
        0xBB: (no_arg, 'CP E'),
        0xBC: (no_arg, 'CP H'),
        0xBD: (no_arg, 'CP L'),
        0xBE: (no_arg, 'CP (HL)'),
        0xBF: (no_arg, 'CP A'),
        0xC0: (no_arg, 'RET NZ'),
        0xC1: (no_arg, 'POP BC'),
        0xC2: (word_arg, 'JP NZ,{}'),
        0xC3: (word_arg, 'JP {}'),
        0xC4: (word_arg, 'CALL NZ,{}'),
        0xC5: (no_arg, 'PUSH BC'),
        0xC6: (byte_arg, 'ADD A,{}'),
        0xC7: (rst_arg, 0),
        0xC8: (no_arg, 'RET Z'),
        0xC9: (no_arg, 'RET'),
        0xCA: (word_arg, 'JP Z,{}'),
        0xCB: (cb_arg, None),
        0xCC: (word_arg, 'CALL Z,{}'),
        0xCD: (word_arg, 'CALL {}'),
        0xCE: (byte_arg, 'ADC A,{}'),
        0xCF: (rst_arg, 8),
        0xD0: (no_arg, 'RET NC'),
        0xD1: (no_arg, 'POP DE'),
        0xD2: (word_arg, 'JP NC,{}'),
        0xD3: (byte_arg, 'OUT ({}),A'),
        0xD4: (word_arg, 'CALL NC,{}'),
        0xD5: (no_arg, 'PUSH DE'),
        0xD6: (byte_arg, 'SUB {}'),
        0xD7: (rst_arg, 16),
        0xD8: (no_arg, 'RET C'),
        0xD9: (no_arg, 'EXX'),
        0xDA: (word_arg, 'JP C,{}'),
        0xDB: (byte_arg, 'IN A,({})'),
        0xDC: (word_arg, 'CALL C,{}'),
        0xDD: (dd_arg, None),
        0xDE: (byte_arg, 'SBC A,{}'),
        0xDF: (rst_arg, 24),
        0xE0: (no_arg, 'RET PO'),
        0xE1: (no_arg, 'POP HL'),
        0xE2: (word_arg, 'JP PO,{}'),
        0xE3: (no_arg, 'EX (SP),HL'),
        0xE4: (word_arg, 'CALL PO,{}'),
        0xE5: (no_arg, 'PUSH HL'),
        0xE6: (byte_arg, 'AND {}'),
        0xE7: (rst_arg, 32),
        0xE8: (no_arg, 'RET PE'),
        0xE9: (no_arg, 'JP (HL)'),
        0xEA: (word_arg, 'JP PE,{}'),
        0xEB: (no_arg, 'EX DE,HL'),
        0xEC: (word_arg, 'CALL PE,{}'),
        0xED: (ed_arg, None),
        0xEE: (byte_arg, 'XOR {}'),
        0xEF: (rst_arg, 40),
        0xF0: (no_arg, 'RET P'),
        0xF1: (no_arg, 'POP AF'),
        0xF2: (word_arg, 'JP P,{}'),
        0xF3: (no_arg, 'DI'),
        0xF4: (word_arg, 'CALL P,{}'),
        0xF5: (no_arg, 'PUSH AF'),
        0xF6: (byte_arg, 'OR {}'),
        0xF7: (rst_arg, 48),
        0xF8: (no_arg, 'RET M'),
        0xF9: (no_arg, 'LD SP,HL'),
        0xFA: (word_arg, 'JP M,{}'),
        0xFB: (no_arg, 'EI'),
        0xFC: (word_arg, 'CALL M,{}'),
        0xFD: (fd_arg, None),
        0xFE: (byte_arg, 'CP {}'),
        0xFF: (rst_arg, 56)
    }

    after_CB = {
        0x00: 'RLC B',
        0x01: 'RLC C',
        0x02: 'RLC D',
        0x03: 'RLC E',
        0x04: 'RLC H',
        0x05: 'RLC L',
        0x06: 'RLC (HL)',
        0x07: 'RLC A',
        0x08: 'RRC B',
        0x09: 'RRC C',
        0x0A: 'RRC D',
        0x0B: 'RRC E',
        0x0C: 'RRC H',
        0x0D: 'RRC L',
        0x0E: 'RRC (HL)',
        0x0F: 'RRC A',
        0x10: 'RL B',
        0x11: 'RL C',
        0x12: 'RL D',
        0x13: 'RL E',
        0x14: 'RL H',
        0x15: 'RL L',
        0x16: 'RL (HL)',
        0x17: 'RL A',
        0x18: 'RR B',
        0x19: 'RR C',
        0x1A: 'RR D',
        0x1B: 'RR E',
        0x1C: 'RR H',
        0x1D: 'RR L',
        0x1E: 'RR (HL)',
        0x1F: 'RR A',
        0x20: 'SLA B',
        0x21: 'SLA C',
        0x22: 'SLA D',
        0x23: 'SLA E',
        0x24: 'SLA H',
        0x25: 'SLA L',
        0x26: 'SLA (HL)',
        0x27: 'SLA A',
        0x28: 'SRA B',
        0x29: 'SRA C',
        0x2A: 'SRA D',
        0x2B: 'SRA E',
        0x2C: 'SRA H',
        0x2D: 'SRA L',
        0x2E: 'SRA (HL)',
        0x2F: 'SRA A',
        0x30: 'SLL B',
        0x31: 'SLL C',
        0x32: 'SLL D',
        0x33: 'SLL E',
        0x34: 'SLL H',
        0x35: 'SLL L',
        0x36: 'SLL (HL)',
        0x37: 'SLL A',
        0x38: 'SRL B',
        0x39: 'SRL C',
        0x3A: 'SRL D',
        0x3B: 'SRL E',
        0x3C: 'SRL H',
        0x3D: 'SRL L',
        0x3E: 'SRL (HL)',
        0x3F: 'SRL A',
        0x40: 'BIT 0,B',
        0x41: 'BIT 0,C',
        0x42: 'BIT 0,D',
        0x43: 'BIT 0,E',
        0x44: 'BIT 0,H',
        0x45: 'BIT 0,L',
        0x46: 'BIT 0,(HL)',
        0x47: 'BIT 0,A',
        0x48: 'BIT 1,B',
        0x49: 'BIT 1,C',
        0x4A: 'BIT 1,D',
        0x4B: 'BIT 1,E',
        0x4C: 'BIT 1,H',
        0x4D: 'BIT 1,L',
        0x4E: 'BIT 1,(HL)',
        0x4F: 'BIT 1,A',
        0x50: 'BIT 2,B',
        0x51: 'BIT 2,C',
        0x52: 'BIT 2,D',
        0x53: 'BIT 2,E',
        0x54: 'BIT 2,H',
        0x55: 'BIT 2,L',
        0x56: 'BIT 2,(HL)',
        0x57: 'BIT 2,A',
        0x58: 'BIT 3,B',
        0x59: 'BIT 3,C',
        0x5A: 'BIT 3,D',
        0x5B: 'BIT 3,E',
        0x5C: 'BIT 3,H',
        0x5D: 'BIT 3,L',
        0x5E: 'BIT 3,(HL)',
        0x5F: 'BIT 3,A',
        0x60: 'BIT 4,B',
        0x61: 'BIT 4,C',
        0x62: 'BIT 4,D',
        0x63: 'BIT 4,E',
        0x64: 'BIT 4,H',
        0x65: 'BIT 4,L',
        0x66: 'BIT 4,(HL)',
        0x67: 'BIT 4,A',
        0x68: 'BIT 5,B',
        0x69: 'BIT 5,C',
        0x6A: 'BIT 5,D',
        0x6B: 'BIT 5,E',
        0x6C: 'BIT 5,H',
        0x6D: 'BIT 5,L',
        0x6E: 'BIT 5,(HL)',
        0x6F: 'BIT 5,A',
        0x70: 'BIT 6,B',
        0x71: 'BIT 6,C',
        0x72: 'BIT 6,D',
        0x73: 'BIT 6,E',
        0x74: 'BIT 6,H',
        0x75: 'BIT 6,L',
        0x76: 'BIT 6,(HL)',
        0x77: 'BIT 6,A',
        0x78: 'BIT 7,B',
        0x79: 'BIT 7,C',
        0x7A: 'BIT 7,D',
        0x7B: 'BIT 7,E',
        0x7C: 'BIT 7,H',
        0x7D: 'BIT 7,L',
        0x7E: 'BIT 7,(HL)',
        0x7F: 'BIT 7,A',
        0x80: 'RES 0,B',
        0x81: 'RES 0,C',
        0x82: 'RES 0,D',
        0x83: 'RES 0,E',
        0x84: 'RES 0,H',
        0x85: 'RES 0,L',
        0x86: 'RES 0,(HL)',
        0x87: 'RES 0,A',
        0x88: 'RES 1,B',
        0x89: 'RES 1,C',
        0x8A: 'RES 1,D',
        0x8B: 'RES 1,E',
        0x8C: 'RES 1,H',
        0x8D: 'RES 1,L',
        0x8E: 'RES 1,(HL)',
        0x8F: 'RES 1,A',
        0x90: 'RES 2,B',
        0x91: 'RES 2,C',
        0x92: 'RES 2,D',
        0x93: 'RES 2,E',
        0x94: 'RES 2,H',
        0x95: 'RES 2,L',
        0x96: 'RES 2,(HL)',
        0x97: 'RES 2,A',
        0x98: 'RES 3,B',
        0x99: 'RES 3,C',
        0x9A: 'RES 3,D',
        0x9B: 'RES 3,E',
        0x9C: 'RES 3,H',
        0x9D: 'RES 3,L',
        0x9E: 'RES 3,(HL)',
        0x9F: 'RES 3,A',
        0xA0: 'RES 4,B',
        0xA1: 'RES 4,C',
        0xA2: 'RES 4,D',
        0xA3: 'RES 4,E',
        0xA4: 'RES 4,H',
        0xA5: 'RES 4,L',
        0xA6: 'RES 4,(HL)',
        0xA7: 'RES 4,A',
        0xA8: 'RES 5,B',
        0xA9: 'RES 5,C',
        0xAA: 'RES 5,D',
        0xAB: 'RES 5,E',
        0xAC: 'RES 5,H',
        0xAD: 'RES 5,L',
        0xAE: 'RES 5,(HL)',
        0xAF: 'RES 5,A',
        0xB0: 'RES 6,B',
        0xB1: 'RES 6,C',
        0xB2: 'RES 6,D',
        0xB3: 'RES 6,E',
        0xB4: 'RES 6,H',
        0xB5: 'RES 6,L',
        0xB6: 'RES 6,(HL)',
        0xB7: 'RES 6,A',
        0xB8: 'RES 7,B',
        0xB9: 'RES 7,C',
        0xBA: 'RES 7,D',
        0xBB: 'RES 7,E',
        0xBC: 'RES 7,H',
        0xBD: 'RES 7,L',
        0xBE: 'RES 7,(HL)',
        0xBF: 'RES 7,A',
        0xC0: 'SET 0,B',
        0xC1: 'SET 0,C',
        0xC2: 'SET 0,D',
        0xC3: 'SET 0,E',
        0xC4: 'SET 0,H',
        0xC5: 'SET 0,L',
        0xC6: 'SET 0,(HL)',
        0xC7: 'SET 0,A',
        0xC8: 'SET 1,B',
        0xC9: 'SET 1,C',
        0xCA: 'SET 1,D',
        0xCB: 'SET 1,E',
        0xCC: 'SET 1,H',
        0xCD: 'SET 1,L',
        0xCE: 'SET 1,(HL)',
        0xCF: 'SET 1,A',
        0xD0: 'SET 2,B',
        0xD1: 'SET 2,C',
        0xD2: 'SET 2,D',
        0xD3: 'SET 2,E',
        0xD4: 'SET 2,H',
        0xD5: 'SET 2,L',
        0xD6: 'SET 2,(HL)',
        0xD7: 'SET 2,A',
        0xD8: 'SET 3,B',
        0xD9: 'SET 3,C',
        0xDA: 'SET 3,D',
        0xDB: 'SET 3,E',
        0xDC: 'SET 3,H',
        0xDD: 'SET 3,L',
        0xDE: 'SET 3,(HL)',
        0xDF: 'SET 3,A',
        0xE0: 'SET 4,B',
        0xE1: 'SET 4,C',
        0xE2: 'SET 4,D',
        0xE3: 'SET 4,E',
        0xE4: 'SET 4,H',
        0xE5: 'SET 4,L',
        0xE6: 'SET 4,(HL)',
        0xE7: 'SET 4,A',
        0xE8: 'SET 5,B',
        0xE9: 'SET 5,C',
        0xEA: 'SET 5,D',
        0xEB: 'SET 5,E',
        0xEC: 'SET 5,H',
        0xED: 'SET 5,L',
        0xEE: 'SET 5,(HL)',
        0xEF: 'SET 5,A',
        0xF0: 'SET 6,B',
        0xF1: 'SET 6,C',
        0xF2: 'SET 6,D',
        0xF3: 'SET 6,E',
        0xF4: 'SET 6,H',
        0xF5: 'SET 6,L',
        0xF6: 'SET 6,(HL)',
        0xF7: 'SET 6,A',
        0xF8: 'SET 7,B',
        0xF9: 'SET 7,C',
        0xFA: 'SET 7,D',
        0xFB: 'SET 7,E',
        0xFC: 'SET 7,H',
        0xFD: 'SET 7,L',
        0xFE: 'SET 7,(HL)',
        0xFF: 'SET 7,A'
    }

    after_DD = {
        0x09: (no_arg, 'ADD IX,BC'),
        0x19: (no_arg, 'ADD IX,DE'),
        0x21: (word_arg, 'LD IX,{}'),
        0x22: (word_arg, 'LD ({}),IX'),
        0x23: (no_arg, 'INC IX'),
        0x24: (no_arg, 'INC IXh'),
        0x25: (no_arg, 'DEC IXh'),
        0x26: (byte_arg, 'LD IXh,{}'),
        0x29: (no_arg, 'ADD IX,IX'),
        0x2A: (word_arg, 'LD IX,({})'),
        0x2B: (no_arg, 'DEC IX'),
        0x2C: (no_arg, 'INC IXl'),
        0x2D: (no_arg, 'DEC IXl'),
        0x2E: (byte_arg, 'LD IXl,{}'),
        0x34: (index, 'INC (IX{})'),
        0x35: (index, 'DEC (IX{})'),
        0x36: (index_arg, 'LD (IX{}),{}'),
        0x39: (no_arg, 'ADD IX,SP'),
        0x44: (no_arg, 'LD B,IXh'),
        0x45: (no_arg, 'LD B,IXl'),
        0x46: (index, 'LD B,(IX{})'),
        0x4C: (no_arg, 'LD C,IXh'),
        0x4D: (no_arg, 'LD C,IXl'),
        0x4E: (index, 'LD C,(IX{})'),
        0x54: (no_arg, 'LD D,IXh'),
        0x55: (no_arg, 'LD D,IXl'),
        0x56: (index, 'LD D,(IX{})'),
        0x5C: (no_arg, 'LD E,IXh'),
        0x5D: (no_arg, 'LD E,IXl'),
        0x5E: (index, 'LD E,(IX{})'),
        0x60: (no_arg, 'LD IXh,B'),
        0x61: (no_arg, 'LD IXh,C'),
        0x62: (no_arg, 'LD IXh,D'),
        0x63: (no_arg, 'LD IXh,E'),
        0x64: (no_arg, 'LD IXh,IXh'),
        0x65: (no_arg, 'LD IXh,IXl'),
        0x66: (index, 'LD H,(IX{})'),
        0x67: (no_arg, 'LD IXh,A'),
        0x68: (no_arg, 'LD IXl,B'),
        0x69: (no_arg, 'LD IXl,C'),
        0x6A: (no_arg, 'LD IXl,D'),
        0x6B: (no_arg, 'LD IXl,E'),
        0x6C: (no_arg, 'LD IXl,IXh'),
        0x6D: (no_arg, 'LD IXl,IXl'),
        0x6E: (index, 'LD L,(IX{})'),
        0x6F: (no_arg, 'LD IXl,A'),
        0x70: (index, 'LD (IX{}),B'),
        0x71: (index, 'LD (IX{}),C'),
        0x72: (index, 'LD (IX{}),D'),
        0x73: (index, 'LD (IX{}),E'),
        0x74: (index, 'LD (IX{}),H'),
        0x75: (index, 'LD (IX{}),L'),
        0x77: (index, 'LD (IX{}),A'),
        0x7C: (no_arg, 'LD A,IXh'),
        0x7D: (no_arg, 'LD A,IXl'),
        0x7E: (index, 'LD A,(IX{})'),
        0x84: (no_arg, 'ADD A,IXh'),
        0x85: (no_arg, 'ADD A,IXl'),
        0x86: (index, 'ADD A,(IX{})'),
        0x8C: (no_arg, 'ADC A,IXh'),
        0x8D: (no_arg, 'ADC A,IXl'),
        0x8E: (index, 'ADC A,(IX{})'),
        0x94: (no_arg, 'SUB IXh'),
        0x95: (no_arg, 'SUB IXl'),
        0x96: (index, 'SUB (IX{})'),
        0x9C: (no_arg, 'SBC A,IXh'),
        0x9D: (no_arg, 'SBC A,IXl'),
        0x9E: (index, 'SBC A,(IX{})'),
        0xA4: (no_arg, 'AND IXh'),
        0xA5: (no_arg, 'AND IXl'),
        0xA6: (index, 'AND (IX{})'),
        0xAC: (no_arg, 'XOR IXh'),
        0xAD: (no_arg, 'XOR IXl'),
        0xAE: (index, 'XOR (IX{})'),
        0xB4: (no_arg, 'OR IXh'),
        0xB5: (no_arg, 'OR IXl'),
        0xB6: (index, 'OR (IX{})'),
        0xBC: (no_arg, 'CP IXh'),
        0xBD: (no_arg, 'CP IXl'),
        0xBE: (index, 'CP (IX{})'),
        0xCB: (ddcb_arg, None),
        0xE1: (no_arg, 'POP IX'),
        0xE3: (no_arg, 'EX (SP),IX'),
        0xE5: (no_arg, 'PUSH IX'),
        0xE9: (no_arg, 'JP (IX)'),
        0xF9: (no_arg, 'LD SP,IX')
    }

    after_ED = {
        0x40: (no_arg, 'IN B,(C)'),
        0x41: (no_arg, 'OUT (C),B'),
        0x42: (no_arg, 'SBC HL,BC'),
        0x43: (word_arg, 'LD ({}),BC'),
        0x44: (no_arg, 'NEG'),
        0x45: (no_arg, 'RETN'),
        0x46: (no_arg, 'IM 0'),
        0x47: (no_arg, 'LD I,A'),
        0x48: (no_arg, 'IN C,(C)'),
        0x49: (no_arg, 'OUT (C),C'),
        0x4A: (no_arg, 'ADC HL,BC'),
        0x4B: (word_arg, 'LD BC,({})'),
        0x4D: (no_arg, 'RETI'),
        0x4F: (no_arg, 'LD R,A'),
        0x50: (no_arg, 'IN D,(C)'),
        0x51: (no_arg, 'OUT (C),D'),
        0x52: (no_arg, 'SBC HL,DE'),
        0x53: (word_arg, 'LD ({}),DE'),
        0x56: (no_arg, 'IM 1'),
        0x57: (no_arg, 'LD A,I'),
        0x58: (no_arg, 'IN E,(C)'),
        0x59: (no_arg, 'OUT (C),E'),
        0x5A: (no_arg, 'ADC HL,DE'),
        0x5B: (word_arg, 'LD DE,({})'),
        0x5E: (no_arg, 'IM 2'),
        0x5F: (no_arg, 'LD A,R'),
        0x60: (no_arg, 'IN H,(C)'),
        0x61: (no_arg, 'OUT (C),H'),
        0x62: (no_arg, 'SBC HL,HL'),
        # ED63 is 'LD (nn),HL', but if we disassemble to that, it won't
        # assemble back to the same bytes
        0x63: (defb4, None),
        0x67: (no_arg, 'RRD'),
        0x68: (no_arg, 'IN L,(C)'),
        0x69: (no_arg, 'OUT (C),L'),
        0x6A: (no_arg, 'ADC HL,HL'),
        # ED6B is 'LD HL,(nn)', but if we disassemble to that, it won't
        # assemble back to the same bytes
        0x6B: (defb4, None),
        0x6F: (no_arg, 'RLD'),
        0x72: (no_arg, 'SBC HL,SP'),
        0x73: (word_arg, 'LD ({}),SP'),
        0x78: (no_arg, 'IN A,(C)'),
        0x79: (no_arg, 'OUT (C),A'),
        0x7A: (no_arg, 'ADC HL,SP'),
        0x7B: (word_arg, 'LD SP,({})'),
        0xA0: (no_arg, 'LDI'),
        0xA1: (no_arg, 'CPI'),
        0xA2: (no_arg, 'INI'),
        0xA3: (no_arg, 'OUTI'),
        0xA8: (no_arg, 'LDD'),
        0xA9: (no_arg, 'CPD'),
        0xAA: (no_arg, 'IND'),
        0xAB: (no_arg, 'OUTD'),
        0xB0: (no_arg, 'LDIR'),
        0xB1: (no_arg, 'CPIR'),
        0xB2: (no_arg, 'INIR'),
        0xB3: (no_arg, 'OTIR'),
        0xB8: (no_arg, 'LDDR'),
        0xB9: (no_arg, 'CPDR'),
        0xBA: (no_arg, 'INDR'),
        0xBB: (no_arg, 'OTDR')
    }

    after_DDCB = {
        0x06: (index, 'RLC (IX{})'),
        0x0E: (index, 'RRC (IX{})'),
        0x16: (index, 'RL (IX{})'),
        0x1E: (index, 'RR (IX{})'),
        0x26: (index, 'SLA (IX{})'),
        0x2E: (index, 'SRA (IX{})'),
        0x36: (index, 'SLL (IX{})'),
        0x3E: (index, 'SRL (IX{})'),
        0x46: (index, 'BIT 0,(IX{})'),
        0x4E: (index, 'BIT 1,(IX{})'),
        0x56: (index, 'BIT 2,(IX{})'),
        0x5E: (index, 'BIT 3,(IX{})'),
        0x66: (index, 'BIT 4,(IX{})'),
        0x6E: (index, 'BIT 5,(IX{})'),
        0x76: (index, 'BIT 6,(IX{})'),
        0x7E: (index, 'BIT 7,(IX{})'),
        0x86: (index, 'RES 0,(IX{})'),
        0x8E: (index, 'RES 1,(IX{})'),
        0x96: (index, 'RES 2,(IX{})'),
        0x9E: (index, 'RES 3,(IX{})'),
        0xA6: (index, 'RES 4,(IX{})'),
        0xAE: (index, 'RES 5,(IX{})'),
        0xB6: (index, 'RES 6,(IX{})'),
        0xBE: (index, 'RES 7,(IX{})'),
        0xC6: (index, 'SET 0,(IX{})'),
        0xCE: (index, 'SET 1,(IX{})'),
        0xD6: (index, 'SET 2,(IX{})'),
        0xDE: (index, 'SET 3,(IX{})'),
        0xE6: (index, 'SET 4,(IX{})'),
        0xEE: (index, 'SET 5,(IX{})'),
        0xF6: (index, 'SET 6,(IX{})'),
        0xFE: (index, 'SET 7,(IX{})')
    }
