# Copyright 2010-2015, 2017-2019, 2021, 2024
# Richard Dymond (rjdymond@gmail.com)
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

from skoolkit.components import get_component
from skoolkit.ctlparser import DEFAULT_BASE

VARIANT = 1

class OperandFormatter:
    """Initialise the operand formatter.

    :param config: Configuration object with the following attributes:

                   * `asm_hex` - if `True`, default base is hexadecimal
                   * `asm_lower` - if `True`, format operands in lower case
    """
    # Component API
    def __init__(self, config):
        self.byte_formats = {
            'b': '%{:08b}',
            'd': '{}',
            'h': '${:02X}',
            'm': '-{}',
            DEFAULT_BASE: '{}'
        }
        self.word_formats = {
            'b': '%{:016b}',
            'd': '{}',
            'h': '${:04X}',
            'm': '-{}',
            DEFAULT_BASE: '{}'
        }
        if config.asm_lower:
            self.byte_formats['h'] = '${:02x}'
            self.word_formats['h'] = '${:04x}'
        if config.asm_hex:
            self.byte_formats['m'] = '-' + self.byte_formats['h']
            self.word_formats['m'] = '-' + self.word_formats['h']
            self.byte_formats[DEFAULT_BASE] = self.byte_formats['h']
            self.word_formats[DEFAULT_BASE] = self.word_formats['h']

    # Component API
    def format_byte(self, value, base):
        """Format a byte value.

        :param value: The byte value.
        :param base: The desired base ('b', 'c', 'd', 'h', 'm' or 'n').
        :return: The formatted byte value.
        """
        return self._num_str(value, 1, base)

    # Component API
    def format_word(self, value, base):
        """Format a word (2-byte) value.

        :param value: The word value.
        :param base: The desired base ('b', 'c', 'd', 'h', 'm' or 'n').
        :return: The formatted word value.
        """
        return self._num_str(value, 2, base)

    # Component API
    def is_char(self, value):
        """Return whether a byte value can be formatted as a character.

        :param value: The byte value.
        """
        return 32 <= value < 127 and value not in (94, 96)

    def _num_str(self, value, num_bytes, base):
        if base == 'c':
            if self.is_char(value & 127):
                if value & 128:
                    suffix = '+' + self._num_str(128, 1, DEFAULT_BASE)
                else:
                    suffix = ''
                if value & 127 in (34, 92):
                    return r'"\{}"'.format(chr(value & 127)) + suffix
                return '"{}"'.format(chr(value & 127)) + suffix
            base = DEFAULT_BASE
        if base == 'm':
            if num_bytes == 1:
                value = 256 - value
            else:
                value = 65536 - value
        if value > 255 or num_bytes > 1:
            return self.word_formats[base].format(value)
        return self.byte_formats[base].format(value)

class Disassembler:
    """Initialise the disassembler.

    :param snapshot: The snapshot (list of 65536 byte values) to disassemble.
    :param config: Configuration object with the following attributes:

                   * `asm_hex` - if `True`, produce a hexadecimal disassembly
                   * `asm_lower` - if `True`, produce a lower case disassembly
                   * `defb_size` - default maximum number of bytes in a DEFB
                     statement
                   * `defm_size` - default maximum number of characters in a
                     DEFM statement
                   * `defw_size` - default maximum number of words in a DEFW
                     statement
                   * `imaker` - callable that returns an instruction object
                   * `opcodes` - comma-separated list of values specifying
                     additional opcode sequences to disassemble
                   * `wrap` - if `True`, disassemble an instruction that wraps
                     around the 64K boundary
    """
    # Component API
    def __init__(self, snapshot, config):
        self.snapshot = snapshot
        self.defb_size = config.defb_size
        self.defm_size = config.defm_size
        self.defw_size = config.defw_size
        self.imaker = config.imaker
        self.wrap = config.wrap
        self.op_formatter = get_component('OperandFormatter', config)
        self.defb = 'DEFB '
        self.defm = 'DEFM '
        self.defs = 'DEFS '
        self.defw = 'DEFW '
        self.create_opcodes()
        opcodes = [e.strip() for e in config.opcodes.upper().split(',')]
        if 'ALL' in opcodes:
            opcodes = 'ED63,ED6B,ED70,ED71,IM,NEG,RETN,XYCB'.split(',')
        for opcode in opcodes:
            if opcode == 'ED63':
                self.after_ED[0x63] = (self.word_arg, 'LD ({}),HL', VARIANT)
            elif opcode == 'ED6B':
                self.after_ED[0x6B] = (self.word_arg, 'LD HL,({})', VARIANT)
            elif opcode == 'ED70':
                self.after_ED[0x70] = (self.no_arg, 'IN F,(C)', 0)
            elif opcode == 'ED71':
                self.after_ED[0x71] = (self.no_arg, 'OUT (C),0', 0)
            elif opcode == 'IM':
                self.after_ED[0x4E] = (self.no_arg, 'IM 0', VARIANT)
                self.after_ED[0x66] = (self.no_arg, 'IM 0', VARIANT)
                self.after_ED[0x6E] = (self.no_arg, 'IM 0', VARIANT)
                self.after_ED[0x76] = (self.no_arg, 'IM 1', VARIANT)
                self.after_ED[0x7E] = (self.no_arg, 'IM 2', VARIANT)
            elif opcode == 'NEG':
                for i in range(0x4C, 0x7D, 8):
                    self.after_ED[i] = (self.no_arg, 'NEG', VARIANT)
            elif opcode == 'RETN':
                for i in range(0x55, 0x7E, 8):
                    self.after_ED[i] = (self.no_arg, 'RETN', VARIANT)
            elif opcode == 'XYCB':
                for b, op in enumerate(('RLC', 'RRC', 'RL', 'RR', 'SLA', 'SRA', 'SLL', 'SRL')):
                    for i, r in enumerate(('B', 'C', 'D', 'E', 'H', 'L', '', 'A')):
                        if r:
                            self.after_DDCB[0x00 + 8 * b + i] = (self.index, f'{op} (IX{{}}),{r}', 0)
                            self.after_DDCB[0x40 + 8 * b + i] = (self.index, f'BIT {b},(IX{{}})', VARIANT)
                            self.after_DDCB[0x80 + 8 * b + i] = (self.index, f'RES {b},(IX{{}}),{r}', 0)
                            self.after_DDCB[0xC0 + 8 * b + i] = (self.index, f'SET {b},(IX{{}}),{r}', 0)
        if config.asm_lower:
            self.defb = self.defb.lower()
            self.defm = self.defm.lower()
            self.defs = self.defs.lower()
            self.defw = self.defw.lower()
            self.ops = {k: (v[0], v[1].lower()) for k, v in self.ops.items()}
            self.after_CB = {k: v.lower() for k, v in self.after_CB.items()}
            self.after_DD = {k: (v[0], v[1].lower()) for k, v in self.after_DD.items()}
            self.after_ED = {k: (v[0], v[1].lower(), v[2]) for k, v in self.after_ED.items()}
            self.after_DDCB = {k: (v[0], v[1].lower(), v[2]) for k, v in self.after_DDCB.items()}

    # Component API
    def disassemble(self, start, end, base):
        """Disassemble an address range.

        :param start: The start address.
        :param end: The end address.
        :param base: Base indicator ('b', 'c', 'd', 'h', 'm' or 'n'). For
                     instructions with two numeric operands (e.g.
                     'LD (IX+d),n'), the indicator may consist of two letters,
                     one for each operand (e.g. 'dh').
        :return: A list of instruction objects created by *imaker*.
        """
        instructions = []
        address = start
        while address < end:
            flags = 0
            decoder, template = self.ops[self.snapshot[address]]
            if template == '':
                operation, length, flags = decoder(address, base)
            else:
                operation, length = decoder(template, address, base)
            if address + length <= 65536:
                instruction = self.imaker(address, operation, self.snapshot[address:address + length])
            elif self.wrap:
                instruction = self.imaker(address, operation, self.snapshot[address:65536] + self.snapshot[:(address + length) & 65535])
            else:
                instruction = self._defb_line(address, self.snapshot[address:65536])
            instruction.variant = flags & VARIANT
            instructions.append(instruction)
            address += length
        return instructions

    def _defb_line(self, address, data, sublengths=((0, DEFAULT_BASE),), defm=False):
        return self.imaker(address, self.defb_dir(data, sublengths, defm), data)

    def _defb_lines(self, start, end, sublengths, defm=False):
        if defm:
            max_size = self.defm_size
        else:
            max_size = self.defb_size
        if sublengths[0][0] or end - start <= max_size:
            return [self._defb_line(start, self.snapshot[start:end], sublengths, defm)]
        instructions = []
        data = []
        for i in range(start, end):
            data.append(self.snapshot[i])
            if len(data) == max_size:
                instructions.append(self._defb_line(i - len(data) + 1, data, sublengths, defm))
                data = []
        if data:
            instructions.append(self._defb_line(i - len(data) + 1, data, sublengths, defm))
        return instructions

    # Component API
    def defb_range(self, start, end, sublengths):
        """Produce a sequence of DEFB statements for an address range.

        :param start: The start address.
        :param end: The end address.
        :param sublengths: Sequence of sublength identifiers.
        :return: A list of instruction objects created by *imaker*.
        """
        return self._defb_lines(start, end, sublengths)

    # Component API
    def defm_range(self, start, end, sublengths):
        """Produce a sequence of DEFM statements for an address range.

        :param start: The start address.
        :param end: The end address.
        :param sublengths: Sequence of sublength identifiers.
        :return: A list of instruction objects created by *imaker*.
        """
        return self._defb_lines(start, end, sublengths, True)

    def _defw_lines(self, start, end, sublengths):
        data = self.snapshot[start:end]
        items = []
        i = 0
        instructions = []
        for length, base in sublengths:
            for j in range(i, min(i + length, len(data)), 2):
                if j == len(data) - 1:
                    instructions.append(self._defb_line(start + j, data[j:], ((1, base),)))
                    data = data[:j]
                else:
                    items.append(self.op_formatter.format_word(data[j] + 256 * data[j + 1], base))
            i += length
        if items:
            instructions.insert(0, self.imaker(start, self.defw + ','.join(items), data))
        return instructions

    # Component API
    def defw_range(self, start, end, sublengths):
        """Produce a sequence of DEFW statements for an address range.

        :param start: The start address.
        :param end: The end address.
        :param sublengths: Sequence of sublength identifiers.
        :return: A list of instruction objects created by *imaker*.
        """
        if sublengths[0][0]:
            return self._defw_lines(start, end, sublengths)
        instructions = []
        size, base = self.defw_size * 2, sublengths[0][1]
        for address in range(start, end, size):
            if address + size > end:
                size = end - address
                if size % 2:
                    size += 1
            instructions.extend(self._defw_lines(address, address + size, ((size, base),)))
        return instructions

    # Component API
    def defs_range(self, start, end, sublengths):
        """Produce a sequence of DEFS statements for an address range.

        :param start: The start address.
        :param end: The end address.
        :param sublengths: Sequence of sublength identifiers.
        :return: A list of instruction objects created by *imaker*.
        """
        data = self.snapshot[start:end]
        values = set(data)
        if len(values) > 1:
            return self.defb_range(start, end, ((0, DEFAULT_BASE),))
        value = values.pop()
        size, base = sublengths[0]
        items = [self.op_formatter.format_byte(size or end - start, base)]
        if len(sublengths) > 1:
            items.append(self.op_formatter.format_byte(value, sublengths[1][1]))
        elif value:
            items.append(self.op_formatter.format_byte(value, DEFAULT_BASE))
        defs_dir = self.defs + ','.join(items)
        return [self.imaker(start, defs_dir, data)]

    def get_message(self, data):
        items = []
        for b in data:
            if self.op_formatter.is_char(b):
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
                items.append(self.op_formatter.format_byte(b, DEFAULT_BASE))
        if items[-1].startswith('"'):
            items[-1] += '"'
        return ','.join(items)

    def no_arg(self, template, a, base):
        return template, 1

    def byte_arg(self, template, a, base):
        return template.format(self.op_formatter.format_byte(self.snapshot[(a + 1) & 65535], base)), 2

    def word_arg(self, template, a, base):
        return template.format(self.op_formatter.format_word(self.snapshot[(a + 1) & 65535] + 256 * self.snapshot[(a + 2) & 65535], base)), 3

    def jr_arg(self, template, a, base):
        offset = self.snapshot[(a + 1) & 65535]
        if offset < 128:
            address = a + 2 + offset
        else:
            address = a + offset - 254
        if 0 <= address < 65536:
            return template.format(self.op_formatter.format_word(address, base)), 2
        return self._defb(a, 2)

    def rst_arg(self, template, a, base):
        return template[:4] + self.op_formatter.format_byte(int(template[4:]), base), 1

    def defb_items(self, data, sublengths):
        items = []
        i = 0
        for size, base in sublengths:
            if not size:
                size = len(data)
            if base == 'c' and size > 1:
                items.append(self.get_message(data[i:i + size]))
            else:
                items.append(','.join(self.op_formatter.format_byte(b, base) for b in data[i:i + size]))
            i += size
        return ','.join(items)

    def defb_dir(self, data, sublengths=((0, DEFAULT_BASE),), defm=False):
        if defm:
            directive = self.defm
        else:
            directive = self.defb
        return directive + self.defb_items(data, sublengths)

    def _defb(self, a, length):
        data = self.snapshot[a:a + length]
        return self.defb_dir(data), len(data)

    def defb4(self, a, base):
        return self._defb(a, 4)

    def index(self, template, a, base):
        return template.format(self.index_offset(a, base)), 2

    def index_arg(self, template, a, base):
        return template.format(self.index_offset(a, base[0]), self.op_formatter.format_byte(self.snapshot[(a + 2) & 65535], base[-1])), 3

    def index_offset(self, a, base):
        i = self.snapshot[(a + 1) & 65535]
        if i < 128:
            return '+{}'.format(self.op_formatter.format_byte(i, base))
        return '-{}'.format(self.op_formatter.format_byte(abs(i - 256), base))

    def cb_arg(self, a, base):
        return self.after_CB[self.snapshot[(a + 1) & 65535]], 2, 0

    def ed_arg(self, a, base):
        decoder, template, flags = self.after_ED.get(self.snapshot[(a + 1) & 65535], (None, None, None))
        if template:
            operation, length = decoder(template, a + 1, base)
            return operation, length + 1, flags
        if decoder:
            return decoder(a, base) + (flags,)
        return self._defb(a, 2) + (0,)

    def dd_arg(self, a, base):
        decoder, template = self.after_DD.get(self.snapshot[(a + 1) & 65535], (None, None))
        if template:
            operation, length = decoder(template, a + 1, base)
            return operation, length + 1, 0
        if decoder:
            return decoder(a, base)
        # The instruction is unchanged by the DD prefix
        return self._defb(a, 1) + (0,)

    def fd_arg(self, a, base):
        operation, length, flags = self.dd_arg(a, base)
        return operation.replace('IX', 'IY').replace('ix', 'iy'), length, flags

    def ddcb_arg(self, a, base):
        decoder, template, flags = self.after_DDCB.get(self.snapshot[(a + 3) & 65535], (None, None, None))
        if template:
            operation = decoder(template, a + 1, base)[0]
            return operation, 4, flags
        return self._defb(a, 4) + (0,)

    def create_opcodes(self):
        self.ops = {
            0x00: (self.no_arg, 'NOP'),
            0x01: (self.word_arg, 'LD BC,{}'),
            0x02: (self.no_arg, 'LD (BC),A'),
            0x03: (self.no_arg, 'INC BC'),
            0x04: (self.no_arg, 'INC B'),
            0x05: (self.no_arg, 'DEC B'),
            0x06: (self.byte_arg, 'LD B,{}'),
            0x07: (self.no_arg, 'RLCA'),
            0x08: (self.no_arg, "EX AF,AF'"),
            0x09: (self.no_arg, 'ADD HL,BC'),
            0x0A: (self.no_arg, 'LD A,(BC)'),
            0x0B: (self.no_arg, 'DEC BC'),
            0x0C: (self.no_arg, 'INC C'),
            0x0D: (self.no_arg, 'DEC C'),
            0x0E: (self.byte_arg, 'LD C,{}'),
            0x0F: (self.no_arg, 'RRCA'),
            0x10: (self.jr_arg, 'DJNZ {}'),
            0x11: (self.word_arg, 'LD DE,{}'),
            0x12: (self.no_arg, 'LD (DE),A'),
            0x13: (self.no_arg, 'INC DE'),
            0x14: (self.no_arg, 'INC D'),
            0x15: (self.no_arg, 'DEC D'),
            0x16: (self.byte_arg, 'LD D,{}'),
            0x17: (self.no_arg, 'RLA'),
            0x18: (self.jr_arg, 'JR {}'),
            0x19: (self.no_arg, 'ADD HL,DE'),
            0x1A: (self.no_arg, 'LD A,(DE)'),
            0x1B: (self.no_arg, 'DEC DE'),
            0x1C: (self.no_arg, 'INC E'),
            0x1D: (self.no_arg, 'DEC E'),
            0x1E: (self.byte_arg, 'LD E,{}'),
            0x1F: (self.no_arg, 'RRA'),
            0x20: (self.jr_arg, 'JR NZ,{}'),
            0x21: (self.word_arg, 'LD HL,{}'),
            0x22: (self.word_arg, 'LD ({}),HL'),
            0x23: (self.no_arg, 'INC HL'),
            0x24: (self.no_arg, 'INC H'),
            0x25: (self.no_arg, 'DEC H'),
            0x26: (self.byte_arg, 'LD H,{}'),
            0x27: (self.no_arg, 'DAA'),
            0x28: (self.jr_arg, 'JR Z,{}'),
            0x29: (self.no_arg, 'ADD HL,HL'),
            0x2A: (self.word_arg, 'LD HL,({})'),
            0x2B: (self.no_arg, 'DEC HL'),
            0x2C: (self.no_arg, 'INC L'),
            0x2D: (self.no_arg, 'DEC L'),
            0x2E: (self.byte_arg, 'LD L,{}'),
            0x2F: (self.no_arg, 'CPL'),
            0x30: (self.jr_arg, 'JR NC,{}'),
            0x31: (self.word_arg, 'LD SP,{}'),
            0x32: (self.word_arg, 'LD ({}),A'),
            0x33: (self.no_arg, 'INC SP'),
            0x34: (self.no_arg, 'INC (HL)'),
            0x35: (self.no_arg, 'DEC (HL)'),
            0x36: (self.byte_arg, 'LD (HL),{}'),
            0x37: (self.no_arg, 'SCF'),
            0x38: (self.jr_arg, 'JR C,{}'),
            0x39: (self.no_arg, 'ADD HL,SP'),
            0x3A: (self.word_arg, 'LD A,({})'),
            0x3B: (self.no_arg, 'DEC SP'),
            0x3C: (self.no_arg, 'INC A'),
            0x3D: (self.no_arg, 'DEC A'),
            0x3E: (self.byte_arg, 'LD A,{}'),
            0x3F: (self.no_arg, 'CCF'),
            0x40: (self.no_arg, 'LD B,B'),
            0x41: (self.no_arg, 'LD B,C'),
            0x42: (self.no_arg, 'LD B,D'),
            0x43: (self.no_arg, 'LD B,E'),
            0x44: (self.no_arg, 'LD B,H'),
            0x45: (self.no_arg, 'LD B,L'),
            0x46: (self.no_arg, 'LD B,(HL)'),
            0x47: (self.no_arg, 'LD B,A'),
            0x48: (self.no_arg, 'LD C,B'),
            0x49: (self.no_arg, 'LD C,C'),
            0x4A: (self.no_arg, 'LD C,D'),
            0x4B: (self.no_arg, 'LD C,E'),
            0x4C: (self.no_arg, 'LD C,H'),
            0x4D: (self.no_arg, 'LD C,L'),
            0x4E: (self.no_arg, 'LD C,(HL)'),
            0x4F: (self.no_arg, 'LD C,A'),
            0x50: (self.no_arg, 'LD D,B'),
            0x51: (self.no_arg, 'LD D,C'),
            0x52: (self.no_arg, 'LD D,D'),
            0x53: (self.no_arg, 'LD D,E'),
            0x54: (self.no_arg, 'LD D,H'),
            0x55: (self.no_arg, 'LD D,L'),
            0x56: (self.no_arg, 'LD D,(HL)'),
            0x57: (self.no_arg, 'LD D,A'),
            0x58: (self.no_arg, 'LD E,B'),
            0x59: (self.no_arg, 'LD E,C'),
            0x5A: (self.no_arg, 'LD E,D'),
            0x5B: (self.no_arg, 'LD E,E'),
            0x5C: (self.no_arg, 'LD E,H'),
            0x5D: (self.no_arg, 'LD E,L'),
            0x5E: (self.no_arg, 'LD E,(HL)'),
            0x5F: (self.no_arg, 'LD E,A'),
            0x60: (self.no_arg, 'LD H,B'),
            0x61: (self.no_arg, 'LD H,C'),
            0x62: (self.no_arg, 'LD H,D'),
            0x63: (self.no_arg, 'LD H,E'),
            0x64: (self.no_arg, 'LD H,H'),
            0x65: (self.no_arg, 'LD H,L'),
            0x66: (self.no_arg, 'LD H,(HL)'),
            0x67: (self.no_arg, 'LD H,A'),
            0x68: (self.no_arg, 'LD L,B'),
            0x69: (self.no_arg, 'LD L,C'),
            0x6A: (self.no_arg, 'LD L,D'),
            0x6B: (self.no_arg, 'LD L,E'),
            0x6C: (self.no_arg, 'LD L,H'),
            0x6D: (self.no_arg, 'LD L,L'),
            0x6E: (self.no_arg, 'LD L,(HL)'),
            0x6F: (self.no_arg, 'LD L,A'),
            0x70: (self.no_arg, 'LD (HL),B'),
            0x71: (self.no_arg, 'LD (HL),C'),
            0x72: (self.no_arg, 'LD (HL),D'),
            0x73: (self.no_arg, 'LD (HL),E'),
            0x74: (self.no_arg, 'LD (HL),H'),
            0x75: (self.no_arg, 'LD (HL),L'),
            0x76: (self.no_arg, 'HALT'),
            0x77: (self.no_arg, 'LD (HL),A'),
            0x78: (self.no_arg, 'LD A,B'),
            0x79: (self.no_arg, 'LD A,C'),
            0x7A: (self.no_arg, 'LD A,D'),
            0x7B: (self.no_arg, 'LD A,E'),
            0x7C: (self.no_arg, 'LD A,H'),
            0x7D: (self.no_arg, 'LD A,L'),
            0x7E: (self.no_arg, 'LD A,(HL)'),
            0x7F: (self.no_arg, 'LD A,A'),
            0x80: (self.no_arg, 'ADD A,B'),
            0x81: (self.no_arg, 'ADD A,C'),
            0x82: (self.no_arg, 'ADD A,D'),
            0x83: (self.no_arg, 'ADD A,E'),
            0x84: (self.no_arg, 'ADD A,H'),
            0x85: (self.no_arg, 'ADD A,L'),
            0x86: (self.no_arg, 'ADD A,(HL)'),
            0x87: (self.no_arg, 'ADD A,A'),
            0x88: (self.no_arg, 'ADC A,B'),
            0x89: (self.no_arg, 'ADC A,C'),
            0x8A: (self.no_arg, 'ADC A,D'),
            0x8B: (self.no_arg, 'ADC A,E'),
            0x8C: (self.no_arg, 'ADC A,H'),
            0x8D: (self.no_arg, 'ADC A,L'),
            0x8E: (self.no_arg, 'ADC A,(HL)'),
            0x8F: (self.no_arg, 'ADC A,A'),
            0x90: (self.no_arg, 'SUB B'),
            0x91: (self.no_arg, 'SUB C'),
            0x92: (self.no_arg, 'SUB D'),
            0x93: (self.no_arg, 'SUB E'),
            0x94: (self.no_arg, 'SUB H'),
            0x95: (self.no_arg, 'SUB L'),
            0x96: (self.no_arg, 'SUB (HL)'),
            0x97: (self.no_arg, 'SUB A'),
            0x98: (self.no_arg, 'SBC A,B'),
            0x99: (self.no_arg, 'SBC A,C'),
            0x9A: (self.no_arg, 'SBC A,D'),
            0x9B: (self.no_arg, 'SBC A,E'),
            0x9C: (self.no_arg, 'SBC A,H'),
            0x9D: (self.no_arg, 'SBC A,L'),
            0x9E: (self.no_arg, 'SBC A,(HL)'),
            0x9F: (self.no_arg, 'SBC A,A'),
            0xA0: (self.no_arg, 'AND B'),
            0xA1: (self.no_arg, 'AND C'),
            0xA2: (self.no_arg, 'AND D'),
            0xA3: (self.no_arg, 'AND E'),
            0xA4: (self.no_arg, 'AND H'),
            0xA5: (self.no_arg, 'AND L'),
            0xA6: (self.no_arg, 'AND (HL)'),
            0xA7: (self.no_arg, 'AND A'),
            0xA8: (self.no_arg, 'XOR B'),
            0xA9: (self.no_arg, 'XOR C'),
            0xAA: (self.no_arg, 'XOR D'),
            0xAB: (self.no_arg, 'XOR E'),
            0xAC: (self.no_arg, 'XOR H'),
            0xAD: (self.no_arg, 'XOR L'),
            0xAE: (self.no_arg, 'XOR (HL)'),
            0xAF: (self.no_arg, 'XOR A'),
            0xB0: (self.no_arg, 'OR B'),
            0xB1: (self.no_arg, 'OR C'),
            0xB2: (self.no_arg, 'OR D'),
            0xB3: (self.no_arg, 'OR E'),
            0xB4: (self.no_arg, 'OR H'),
            0xB5: (self.no_arg, 'OR L'),
            0xB6: (self.no_arg, 'OR (HL)'),
            0xB7: (self.no_arg, 'OR A'),
            0xB8: (self.no_arg, 'CP B'),
            0xB9: (self.no_arg, 'CP C'),
            0xBA: (self.no_arg, 'CP D'),
            0xBB: (self.no_arg, 'CP E'),
            0xBC: (self.no_arg, 'CP H'),
            0xBD: (self.no_arg, 'CP L'),
            0xBE: (self.no_arg, 'CP (HL)'),
            0xBF: (self.no_arg, 'CP A'),
            0xC0: (self.no_arg, 'RET NZ'),
            0xC1: (self.no_arg, 'POP BC'),
            0xC2: (self.word_arg, 'JP NZ,{}'),
            0xC3: (self.word_arg, 'JP {}'),
            0xC4: (self.word_arg, 'CALL NZ,{}'),
            0xC5: (self.no_arg, 'PUSH BC'),
            0xC6: (self.byte_arg, 'ADD A,{}'),
            0xC7: (self.rst_arg, 'RST 0'),
            0xC8: (self.no_arg, 'RET Z'),
            0xC9: (self.no_arg, 'RET'),
            0xCA: (self.word_arg, 'JP Z,{}'),
            0xCB: (self.cb_arg, ''),
            0xCC: (self.word_arg, 'CALL Z,{}'),
            0xCD: (self.word_arg, 'CALL {}'),
            0xCE: (self.byte_arg, 'ADC A,{}'),
            0xCF: (self.rst_arg, 'RST 8'),
            0xD0: (self.no_arg, 'RET NC'),
            0xD1: (self.no_arg, 'POP DE'),
            0xD2: (self.word_arg, 'JP NC,{}'),
            0xD3: (self.byte_arg, 'OUT ({}),A'),
            0xD4: (self.word_arg, 'CALL NC,{}'),
            0xD5: (self.no_arg, 'PUSH DE'),
            0xD6: (self.byte_arg, 'SUB {}'),
            0xD7: (self.rst_arg, 'RST 16'),
            0xD8: (self.no_arg, 'RET C'),
            0xD9: (self.no_arg, 'EXX'),
            0xDA: (self.word_arg, 'JP C,{}'),
            0xDB: (self.byte_arg, 'IN A,({})'),
            0xDC: (self.word_arg, 'CALL C,{}'),
            0xDD: (self.dd_arg, ''),
            0xDE: (self.byte_arg, 'SBC A,{}'),
            0xDF: (self.rst_arg, 'RST 24'),
            0xE0: (self.no_arg, 'RET PO'),
            0xE1: (self.no_arg, 'POP HL'),
            0xE2: (self.word_arg, 'JP PO,{}'),
            0xE3: (self.no_arg, 'EX (SP),HL'),
            0xE4: (self.word_arg, 'CALL PO,{}'),
            0xE5: (self.no_arg, 'PUSH HL'),
            0xE6: (self.byte_arg, 'AND {}'),
            0xE7: (self.rst_arg, 'RST 32'),
            0xE8: (self.no_arg, 'RET PE'),
            0xE9: (self.no_arg, 'JP (HL)'),
            0xEA: (self.word_arg, 'JP PE,{}'),
            0xEB: (self.no_arg, 'EX DE,HL'),
            0xEC: (self.word_arg, 'CALL PE,{}'),
            0xED: (self.ed_arg, ''),
            0xEE: (self.byte_arg, 'XOR {}'),
            0xEF: (self.rst_arg, 'RST 40'),
            0xF0: (self.no_arg, 'RET P'),
            0xF1: (self.no_arg, 'POP AF'),
            0xF2: (self.word_arg, 'JP P,{}'),
            0xF3: (self.no_arg, 'DI'),
            0xF4: (self.word_arg, 'CALL P,{}'),
            0xF5: (self.no_arg, 'PUSH AF'),
            0xF6: (self.byte_arg, 'OR {}'),
            0xF7: (self.rst_arg, 'RST 48'),
            0xF8: (self.no_arg, 'RET M'),
            0xF9: (self.no_arg, 'LD SP,HL'),
            0xFA: (self.word_arg, 'JP M,{}'),
            0xFB: (self.no_arg, 'EI'),
            0xFC: (self.word_arg, 'CALL M,{}'),
            0xFD: (self.fd_arg, ''),
            0xFE: (self.byte_arg, 'CP {}'),
            0xFF: (self.rst_arg, 'RST 56')
        }

        self.after_CB = {
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

        self.after_DD = {
            0x09: (self.no_arg, 'ADD IX,BC'),
            0x19: (self.no_arg, 'ADD IX,DE'),
            0x21: (self.word_arg, 'LD IX,{}'),
            0x22: (self.word_arg, 'LD ({}),IX'),
            0x23: (self.no_arg, 'INC IX'),
            0x24: (self.no_arg, 'INC IXh'),
            0x25: (self.no_arg, 'DEC IXh'),
            0x26: (self.byte_arg, 'LD IXh,{}'),
            0x29: (self.no_arg, 'ADD IX,IX'),
            0x2A: (self.word_arg, 'LD IX,({})'),
            0x2B: (self.no_arg, 'DEC IX'),
            0x2C: (self.no_arg, 'INC IXl'),
            0x2D: (self.no_arg, 'DEC IXl'),
            0x2E: (self.byte_arg, 'LD IXl,{}'),
            0x34: (self.index, 'INC (IX{})'),
            0x35: (self.index, 'DEC (IX{})'),
            0x36: (self.index_arg, 'LD (IX{}),{}'),
            0x39: (self.no_arg, 'ADD IX,SP'),
            0x44: (self.no_arg, 'LD B,IXh'),
            0x45: (self.no_arg, 'LD B,IXl'),
            0x46: (self.index, 'LD B,(IX{})'),
            0x4C: (self.no_arg, 'LD C,IXh'),
            0x4D: (self.no_arg, 'LD C,IXl'),
            0x4E: (self.index, 'LD C,(IX{})'),
            0x54: (self.no_arg, 'LD D,IXh'),
            0x55: (self.no_arg, 'LD D,IXl'),
            0x56: (self.index, 'LD D,(IX{})'),
            0x5C: (self.no_arg, 'LD E,IXh'),
            0x5D: (self.no_arg, 'LD E,IXl'),
            0x5E: (self.index, 'LD E,(IX{})'),
            0x60: (self.no_arg, 'LD IXh,B'),
            0x61: (self.no_arg, 'LD IXh,C'),
            0x62: (self.no_arg, 'LD IXh,D'),
            0x63: (self.no_arg, 'LD IXh,E'),
            0x64: (self.no_arg, 'LD IXh,IXh'),
            0x65: (self.no_arg, 'LD IXh,IXl'),
            0x66: (self.index, 'LD H,(IX{})'),
            0x67: (self.no_arg, 'LD IXh,A'),
            0x68: (self.no_arg, 'LD IXl,B'),
            0x69: (self.no_arg, 'LD IXl,C'),
            0x6A: (self.no_arg, 'LD IXl,D'),
            0x6B: (self.no_arg, 'LD IXl,E'),
            0x6C: (self.no_arg, 'LD IXl,IXh'),
            0x6D: (self.no_arg, 'LD IXl,IXl'),
            0x6E: (self.index, 'LD L,(IX{})'),
            0x6F: (self.no_arg, 'LD IXl,A'),
            0x70: (self.index, 'LD (IX{}),B'),
            0x71: (self.index, 'LD (IX{}),C'),
            0x72: (self.index, 'LD (IX{}),D'),
            0x73: (self.index, 'LD (IX{}),E'),
            0x74: (self.index, 'LD (IX{}),H'),
            0x75: (self.index, 'LD (IX{}),L'),
            0x77: (self.index, 'LD (IX{}),A'),
            0x7C: (self.no_arg, 'LD A,IXh'),
            0x7D: (self.no_arg, 'LD A,IXl'),
            0x7E: (self.index, 'LD A,(IX{})'),
            0x84: (self.no_arg, 'ADD A,IXh'),
            0x85: (self.no_arg, 'ADD A,IXl'),
            0x86: (self.index, 'ADD A,(IX{})'),
            0x8C: (self.no_arg, 'ADC A,IXh'),
            0x8D: (self.no_arg, 'ADC A,IXl'),
            0x8E: (self.index, 'ADC A,(IX{})'),
            0x94: (self.no_arg, 'SUB IXh'),
            0x95: (self.no_arg, 'SUB IXl'),
            0x96: (self.index, 'SUB (IX{})'),
            0x9C: (self.no_arg, 'SBC A,IXh'),
            0x9D: (self.no_arg, 'SBC A,IXl'),
            0x9E: (self.index, 'SBC A,(IX{})'),
            0xA4: (self.no_arg, 'AND IXh'),
            0xA5: (self.no_arg, 'AND IXl'),
            0xA6: (self.index, 'AND (IX{})'),
            0xAC: (self.no_arg, 'XOR IXh'),
            0xAD: (self.no_arg, 'XOR IXl'),
            0xAE: (self.index, 'XOR (IX{})'),
            0xB4: (self.no_arg, 'OR IXh'),
            0xB5: (self.no_arg, 'OR IXl'),
            0xB6: (self.index, 'OR (IX{})'),
            0xBC: (self.no_arg, 'CP IXh'),
            0xBD: (self.no_arg, 'CP IXl'),
            0xBE: (self.index, 'CP (IX{})'),
            0xCB: (self.ddcb_arg, ''),
            0xE1: (self.no_arg, 'POP IX'),
            0xE3: (self.no_arg, 'EX (SP),IX'),
            0xE5: (self.no_arg, 'PUSH IX'),
            0xE9: (self.no_arg, 'JP (IX)'),
            0xF9: (self.no_arg, 'LD SP,IX')
        }

        self.after_ED = {
            0x40: (self.no_arg, 'IN B,(C)', 0),
            0x41: (self.no_arg, 'OUT (C),B', 0),
            0x42: (self.no_arg, 'SBC HL,BC', 0),
            0x43: (self.word_arg, 'LD ({}),BC', 0),
            0x44: (self.no_arg, 'NEG', 0),
            0x45: (self.no_arg, 'RETN', 0),
            0x46: (self.no_arg, 'IM 0', 0),
            0x47: (self.no_arg, 'LD I,A', 0),
            0x48: (self.no_arg, 'IN C,(C)', 0),
            0x49: (self.no_arg, 'OUT (C),C', 0),
            0x4A: (self.no_arg, 'ADC HL,BC', 0),
            0x4B: (self.word_arg, 'LD BC,({})', 0),
            0x4D: (self.no_arg, 'RETI', 0),
            0x4F: (self.no_arg, 'LD R,A', 0),
            0x50: (self.no_arg, 'IN D,(C)', 0),
            0x51: (self.no_arg, 'OUT (C),D', 0),
            0x52: (self.no_arg, 'SBC HL,DE', 0),
            0x53: (self.word_arg, 'LD ({}),DE', 0),
            0x56: (self.no_arg, 'IM 1', 0),
            0x57: (self.no_arg, 'LD A,I', 0),
            0x58: (self.no_arg, 'IN E,(C)', 0),
            0x59: (self.no_arg, 'OUT (C),E', 0),
            0x5A: (self.no_arg, 'ADC HL,DE', 0),
            0x5B: (self.word_arg, 'LD DE,({})', 0),
            0x5E: (self.no_arg, 'IM 2', 0),
            0x5F: (self.no_arg, 'LD A,R', 0),
            0x60: (self.no_arg, 'IN H,(C)', 0),
            0x61: (self.no_arg, 'OUT (C),H', 0),
            0x62: (self.no_arg, 'SBC HL,HL', 0),
            # ED63 is 'LD (nn),HL', but if we disassemble to that, it won't
            # assemble back to the same bytes
            0x63: (self.defb4, '', 0),
            0x67: (self.no_arg, 'RRD', 0),
            0x68: (self.no_arg, 'IN L,(C)', 0),
            0x69: (self.no_arg, 'OUT (C),L', 0),
            0x6A: (self.no_arg, 'ADC HL,HL', 0),
            # ED6B is 'LD HL,(nn)', but if we disassemble to that, it won't
            # assemble back to the same bytes
            0x6B: (self.defb4, '', 0),
            0x6F: (self.no_arg, 'RLD', 0),
            0x72: (self.no_arg, 'SBC HL,SP', 0),
            0x73: (self.word_arg, 'LD ({}),SP', 0),
            0x78: (self.no_arg, 'IN A,(C)', 0),
            0x79: (self.no_arg, 'OUT (C),A', 0),
            0x7A: (self.no_arg, 'ADC HL,SP', 0),
            0x7B: (self.word_arg, 'LD SP,({})', 0),
            0xA0: (self.no_arg, 'LDI', 0),
            0xA1: (self.no_arg, 'CPI', 0),
            0xA2: (self.no_arg, 'INI', 0),
            0xA3: (self.no_arg, 'OUTI', 0),
            0xA8: (self.no_arg, 'LDD', 0),
            0xA9: (self.no_arg, 'CPD', 0),
            0xAA: (self.no_arg, 'IND', 0),
            0xAB: (self.no_arg, 'OUTD', 0),
            0xB0: (self.no_arg, 'LDIR', 0),
            0xB1: (self.no_arg, 'CPIR', 0),
            0xB2: (self.no_arg, 'INIR', 0),
            0xB3: (self.no_arg, 'OTIR', 0),
            0xB8: (self.no_arg, 'LDDR', 0),
            0xB9: (self.no_arg, 'CPDR', 0),
            0xBA: (self.no_arg, 'INDR', 0),
            0xBB: (self.no_arg, 'OTDR', 0)
        }

        self.after_DDCB = {
            0x06: (self.index, 'RLC (IX{})', 0),
            0x0E: (self.index, 'RRC (IX{})', 0),
            0x16: (self.index, 'RL (IX{})', 0),
            0x1E: (self.index, 'RR (IX{})', 0),
            0x26: (self.index, 'SLA (IX{})', 0),
            0x2E: (self.index, 'SRA (IX{})', 0),
            0x36: (self.index, 'SLL (IX{})', 0),
            0x3E: (self.index, 'SRL (IX{})', 0),
            0x46: (self.index, 'BIT 0,(IX{})', 0),
            0x4E: (self.index, 'BIT 1,(IX{})', 0),
            0x56: (self.index, 'BIT 2,(IX{})', 0),
            0x5E: (self.index, 'BIT 3,(IX{})', 0),
            0x66: (self.index, 'BIT 4,(IX{})', 0),
            0x6E: (self.index, 'BIT 5,(IX{})', 0),
            0x76: (self.index, 'BIT 6,(IX{})', 0),
            0x7E: (self.index, 'BIT 7,(IX{})', 0),
            0x86: (self.index, 'RES 0,(IX{})', 0),
            0x8E: (self.index, 'RES 1,(IX{})', 0),
            0x96: (self.index, 'RES 2,(IX{})', 0),
            0x9E: (self.index, 'RES 3,(IX{})', 0),
            0xA6: (self.index, 'RES 4,(IX{})', 0),
            0xAE: (self.index, 'RES 5,(IX{})', 0),
            0xB6: (self.index, 'RES 6,(IX{})', 0),
            0xBE: (self.index, 'RES 7,(IX{})', 0),
            0xC6: (self.index, 'SET 0,(IX{})', 0),
            0xCE: (self.index, 'SET 1,(IX{})', 0),
            0xD6: (self.index, 'SET 2,(IX{})', 0),
            0xDE: (self.index, 'SET 3,(IX{})', 0),
            0xE6: (self.index, 'SET 4,(IX{})', 0),
            0xEE: (self.index, 'SET 5,(IX{})', 0),
            0xF6: (self.index, 'SET 6,(IX{})', 0),
            0xFE: (self.index, 'SET 7,(IX{})', 0)
        }
