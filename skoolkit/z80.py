# -*- coding: utf-8 -*-

# Copyright 2015 Richard Dymond (rjdymond@gmail.com)
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

from functools import partial

from skoolkit import get_int_param, parse_int
from skoolkit.textutils import split_unquoted

REG = ('B', 'C', 'D', 'E', 'H', 'L', '(HL)', 'A')
REG_PAIRS = ('BC', 'DE', 'HL', 'SP')
INDEX_REG = ('IXH', 'IXL', 'IYH', 'IYL')
INDEX_REG_PAIRS = ('IX', 'IY')

def _parse_num(num, brackets):
    if brackets:
        if num.startswith("(") and num.endswith(")"):
            return get_int_param(num[1:-1])
        raise ValueError
    return get_int_param(num)

def _parse_byte(num, limit=256, brackets=False):
    value = _parse_num(num, brackets)
    if 0 <= value < limit:
        return value
    raise ValueError

def _parse_word(num, brackets=False):
    value = _parse_num(num, brackets)
    if 0 <= value < 65536:
        return value
    raise ValueError

def _parse_offset(op):
    if op.startswith(('(IX+', '(IX-', '(IY+', '(IY-')) and op.endswith(')'):
        offset = _parse_byte(op[4:-1])
        if op[3] == '-':
            return 256 - offset
        return offset
    raise ValueError

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

def _arithmetic_a(base_code, address, op):
    if op.startswith('(I'):
        return (_index_code(op), base_code + 6, _parse_offset(op))
    if op in INDEX_REG:
        return (_index_code(op), base_code + 4 + (_index_reg_index(op) % 2))
    try:
        return (base_code + _reg_index(op),)
    except ValueError:
        return (base_code + 70, _parse_byte(op))

def _assemble_adc(address, op1, op2):
    if op1 == 'A':
        return _arithmetic_a(136, address, op2)
    if op1 == 'HL':
        return (237, 74 + 16 * _reg_pair_index(op2))

def _assemble_add(address, op1, op2):
    if op1 == 'A':
        return _arithmetic_a(128, address, op2)
    if op1 == 'HL':
        return (9 + 16 * _reg_pair_index(op2),)
    if op1 in INDEX_REG_PAIRS:
        if op1 == op2:
            return (_index_code(op1), 41)
        if op2 != 'HL':
            return (_index_code(op1), 9 + 16 * _reg_pair_index(op2))

def _bit_res_set(base_code, address, op1, op2):
    bit_offset = base_code + 8 * _parse_byte(op1, 8)
    if op2.startswith('(I'):
        return (_index_code(op2), 203, _parse_offset(op2), bit_offset + 6)
    return (203, bit_offset + _reg_index(op2))

def _assemble_call(address, op1, op2=None):
    if op2 is None:
        addr = _parse_word(op1)
        return (205, addr % 256, addr // 256)
    addr = _parse_word(op2)
    return (196 + 8 * _condition_index(op1), addr % 256, addr // 256)

def _inc_dec(base_code8, base_code16, address, op):
    if len(op) == 2:
        try:
            return (base_code16 + 16 * _reg_pair_index(op),)
        except ValueError:
            return (_index_code(op), base_code16 + 32)
    if op.startswith('(I'):
        return (_index_code(op), base_code8 + 48, _parse_offset(op))
    if op in INDEX_REG:
        return (_index_code(op), base_code8 + 32 + 8 * (_index_reg_index(op) % 2))
    return (base_code8 + 8 * _reg_index(op),)

def _address_offset(address, op):
    offset = _parse_word(op) - address
    if offset >= 65410:
        offset -= 65536
    elif offset <= -65407:
        offset += 65536
    if -126 <= offset < 130:
        return (offset - 2) & 255
    raise ValueError

def _assemble_djnz(address, op):
    return (16, _address_offset(address, op))

def _assemble_ex(address, op1, op2):
    if op1 == 'AF' and op2 == "AF'":
        return (8,)
    if op1 == 'DE' and op2 == 'HL':
        return (235,)
    if op1 == '(SP)':
        if op2 == 'HL':
            return (227,)
        if op2 in INDEX_REG_PAIRS:
            return (_index_code(op2), 227)

def _assemble_im(address, op):
    return (237, 70 + (0, 16, 24)[_parse_byte(op, 3)])

def _assemble_in(address, op1, op2):
    if op2 == '(C)' and op1 != '(HL)':
        return (237, 64 + 8 * _reg_index(op1))
    if op1 == 'A':
        return (219, _parse_byte(op2, brackets=True))

def _assemble_jp(address, op1, op2=None):
    if op2 is None:
        if op1 == '(HL)':
            return (233,)
        if op1 == '(IX)':
            return (221, 233)
        if op1 == '(IY)':
            return (253, 233)
        addr = _parse_word(op1)
        return (195, addr % 256, addr // 256)
    addr = _parse_word(op2)
    return (194 + 8 * _condition_index(op1), addr % 256, addr // 256)

def _assemble_jr(address, op1, op2=None):
    if op2 is None:
        return (24, _address_offset(address, op1))
    return (32 + 8 * _condition_index(op1), _address_offset(address, op2))

def _assemble_ld(address, op1, op2):
    if op1 in REG:
        op1_index = _reg_index(op1)
        if op2 in REG and not (op1 == op2 == '(HL)'):
            # LD r,r'; LD r,(HL)
            return (64 + 8 * op1_index + _reg_index(op2),)
        if op2.startswith('(I') and  op1 != '(HL)':
            # LD r,(I{X,Y}+d)
            return (_index_code(op2), 70 + 8 * op1_index, _parse_offset(op2))
        if op2 in INDEX_REG and op1 not in ('H', 'L', '(HL)'):
            # LD r,I{X,Y}{h,l}
            return (_index_code(op2), 68 + 8 * op1_index + (_index_reg_index(op2) % 2))
        if op1 == 'A':
            if op2.startswith('('):
                try:
                    # LD A,(nn)
                    addr = _parse_word(op2, True)
                    return (58, addr % 256, addr // 256)
                except ValueError:
                    # LD A,(BC); LD A,(DE)
                    return (10 + 16 * ('(BC)', '(DE)').index(op2),)
            try:
                # LD A,n
                return (62, _parse_byte(op2))
            except ValueError:
                # LD A,I; LD A,R
                return (237, 87 + 8 * ('I', 'R').index(op2))
        # LD r,n (r != A)
        return (6 + 8 * _reg_index(op1), _parse_byte(op2))

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
        return (_index_code(op1), 38 + 8 * (index1 % 2), _parse_byte(op2))

    if op1.startswith('(I'):
        offset = _parse_offset(op1)
        if op2 in REG and op2 != '(HL)':
            # LD (I{X,Y}+d),r
            return (_index_code(op1), 112 + _reg_index(op2), offset)
        # LD (I{X,Y}+d),n
        return (_index_code(op1), 54, offset, _parse_byte(op2))

    if op1 in REG_PAIRS:
        op1_index = _reg_pair_index(op1)
        if op2.startswith('('):
            addr = _parse_word(op2, True)
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
        addr = _parse_word(op2)
        return (1 + 16 * op1_index, addr % 256, addr // 256)

    if op1 in INDEX_REG_PAIRS:
        if op2.startswith('('):
            addr = _parse_word(op2, True)
            # LD I{X,Y},(nn)
            return (_index_code(op1), 42, addr % 256, addr // 256)
        # LD I{X,Y},nn
        addr = _parse_word(op2)
        return (_index_code(op1), 33, addr % 256, addr // 256)

    if op1.startswith('('):
        if op2 == 'A':
            try:
                # LD (nn),A
                addr = _parse_word(op1, True)
                return (50, addr % 256, addr // 256)
            except ValueError:
                # LD (BC),A; LD (DE),A
                return (2 + 16 * ('(BC)', '(DE)').index(op1),)
        addr = _parse_word(op1, True)
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

def _assemble_out(address, op1, op2):
    if op1 == '(C)' and op2 != '(HL)':
        return (237, 65 + 8 * _reg_index(op2))
    if op2 == 'A':
        return (211, _parse_byte(op1, brackets=True))

def _pop_push(base_code, address, op):
    if op in INDEX_REG_PAIRS:
        return (_index_code(op), base_code + 32)
    return (base_code + 16 * ('BC', 'DE', 'HL', 'AF').index(op),)

def _assemble_ret(address, op1=None):
    if op1 is None:
        return (201,)
    return (192 + 8 * _condition_index(op1),)

def _rotate_and_shift(base_code, address, op):
    if op.startswith('(I'):
        return (_index_code(op), 203, _parse_offset(op), base_code + 6)
    return (203, base_code + _reg_index(op))

def _assemble_rst(address, op):
    num = _parse_byte(op, 57)
    if num % 8 == 0:
        return (199 + num,)

def _assemble_sbc(address, op1, op2):
    if op1 == 'A':
        return _arithmetic_a(152, address, op2)
    if op1 == 'HL':
        return (237, 66 + 16 * _reg_pair_index(op2))

MNEMONICS = {
    'ADC': _assemble_adc,
    'ADD': _assemble_add,
    'AND': partial(_arithmetic_a, 160),
    'BIT': partial(_bit_res_set, 64),
    'CALL': _assemble_call,
    'CCF': (63,),
    'CP': partial(_arithmetic_a, 184),
    'CPD': (237, 169),
    'CPDR': (237, 185),
    'CPI': (237, 161),
    'CPIR': (237, 177),
    'CPL': (47,),
    'DAA': (39,),
    'DEC': partial(_inc_dec, 5, 11),
    'DI': (243,),
    'DJNZ': _assemble_djnz,
    'EI': (251,),
    'EX': _assemble_ex,
    'EXX': (217,),
    'HALT': (118,),
    'IM': _assemble_im,
    'IN': _assemble_in,
    'INC': partial(_inc_dec, 4, 3),
    'IND': (237, 170),
    'INDR': (237, 186),
    'INI': (237, 162),
    'INIR': (237, 178),
    'JP': _assemble_jp,
    'JR': _assemble_jr,
    'LD': _assemble_ld,
    'LDD': (237, 168),
    'LDDR': (237, 184),
    'LDI': (237, 160),
    'LDIR': (237, 176),
    'NEG': (237, 68),
    'NOP': (0,),
    'OR': partial(_arithmetic_a, 176),
    'OTDR': (237, 187),
    'OTIR': (237, 179),
    'OUT': _assemble_out,
    'OUTD': (237, 171),
    'OUTI': (237, 163),
    'POP': partial(_pop_push, 193),
    'PUSH': partial(_pop_push, 197),
    'RES': partial(_bit_res_set, 128),
    'RET': _assemble_ret,
    'RETI': (237, 77),
    'RETN': (237, 69),
    'RL': partial(_rotate_and_shift, 16),
    'RLA': (23,),
    'RLC': partial(_rotate_and_shift, 0),
    'RLCA': (7,),
    'RLD': (237, 111),
    'RR': partial(_rotate_and_shift, 24),
    'RRA': (31,),
    'RRC': partial(_rotate_and_shift, 8),
    'RRCA': (15,),
    'RRD': (237, 103),
    'RST': _assemble_rst,
    'SBC': _assemble_sbc,
    'SCF': (55,),
    'SET': partial(_bit_res_set, 192),
    'SLA': partial(_rotate_and_shift, 32),
    'SLL': partial(_rotate_and_shift, 48),
    'SRA': partial(_rotate_and_shift, 40),
    'SRL': partial(_rotate_and_shift, 56),
    'SUB': partial(_arithmetic_a, 144),
    'XOR': partial(_arithmetic_a, 168)
}

def _item_value(item, limit=256):
    value = parse_int(item, 0)
    if 0 <= value < limit:
        return value
    return 0

def _assemble_defb(items):
    data = []
    for item in items:
        if item.startswith('"'):
            i = 1
            while i < len(item) - 1:
                if item[i] == '\\':
                    i += 1
                data.append(ord(item[i]))
                i += 1
        else:
            data.append(_item_value(item))
    return tuple(data)

def _assemble_defs(items):
    if items:
        span = _item_value(items[0], 65536)
        if len(items) > 1:
            value = _item_value(items[1])
        else:
            value = 0
        return (value,) * span

def _assemble_defw(items):
    data = []
    for arg in [_item_value(v, 65536) for v in items]:
        data.extend((arg % 256, arg // 256))
    return tuple(data)

def convert_case(operation, lower=True, trim=False):
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

def _assemble(operation, address):
    if operation.upper().startswith(('DEFB ', 'DEFM ', 'DEFS ', 'DEFW ')):
        parts = split_operation(operation)
        directive, items = parts[0].upper(), parts[1:]
        if directive in ('DEFB', 'DEFM'):
            return _assemble_defb(items)
        if directive == 'DEFS':
            return _assemble_defs(items)
        if directive == 'DEFW':
            return _assemble_defw(items)

    parts = split_operation(operation, True)
    try:
        a = MNEMONICS[parts[0]]
        if isinstance(a, tuple):
            if len(parts) == 1:
                return a
            return
        return a(address, *parts[1:])
    except:
        return

def split_operation(operation, tidy=False, strip=True):
    if tidy:
        operation = convert_case(operation, False, True)
    elements = operation.split(None, 1)
    if len(elements) < 2:
        return elements
    elements[1:] = split_unquoted(elements[1], ',')
    if strip:
        return [e.strip() for e in elements]
    return elements

def get_size(operation, address):
    return len(assemble(operation, address))

def assemble(operation, address=None):
    return _assemble(operation, address) or ()
