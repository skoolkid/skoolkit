# -*- coding: utf-8 -*-

# Copyright 2009-2015 Richard Dymond (rjdymond@gmail.com)
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

import sys
import os

from . import warn, write_line, wrap, parse_int, get_address_format, open_file, read_bin_file, SkoolKitError
from .skoolparser import get_address, TABLE_MARKER, TABLE_END_MARKER, LIST_MARKER, LIST_END_MARKER
from .skoolasm import UDGTABLE_MARKER
from .skoolctl import (AD_START, AD_WRITER, AD_ORG, AD_END, AD_SET, AD_IGNOREUA,
                       TITLE, DESCRIPTION, REGISTERS, MID_BLOCK, INSTRUCTION, END)
from .disassembler import Disassembler
from .ctlparser import CtlParser

OP_WIDTH = 13
MIN_COMMENT_WIDTH = 10
MIN_INSTRUCTION_COMMENT_WIDTH = 10

REFS_PREFIX = 'Used by the '
EREFS_PREFIX = 'This entry point is used by the '

# The maximum number of distinct bytes that can be in a data block (as a
# fraction of the block length)
UNIQUE_BYTES_MAX = 0.3

# The minimum allowed length of a text block
MIN_LENGTH = 3
# The minimum number of distinct characters that must be in a text block (as a
# fraction of the block length)
UNIQUE_CHARS_MIN = 0.25
# The maximum number of punctuation characters that can be in a text block (as
# a fraction of the block length)
PUNC_CHARS_MAX = 0.2
# The characters allowed in a text block
CHARS = ' ,.abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
# The punctuation characters allowed in a text block
PUNC_CHARS = ',.'
# If two text blocks are separated by no more than this number of bytes, they
# will be joined
TEXT_GAP_MAX = 8

class CodeMapError(SkoolKitError):
    pass

def _get_code_blocks(snapshot, start, fname):
    if os.path.isdir(fname):
        raise SkoolKitError('{0} is a directory'.format(fname))
    try:
        size = os.path.getsize(fname)
    except OSError as e:
        if e.errno == 2:
            raise SkoolKitError('{0}: file not found'.format(fname))
        raise # pragma: no cover

    if size == 8192:
        # Assume this is a Z80 map file
        sys.stderr.write('Reading {0}'.format(fname))
        sys.stderr.flush()
        addresses = []
        data = read_bin_file(fname)
        address = start & 65528
        for b in data[start // 8:]:
            for i in range(8):
                if b & 1 and address >= start:
                    addresses.append(address)
                b >>= 1
                address += 1
    else:
        sys.stderr.write('Reading {0}: '.format(fname))
        sys.stderr.flush()
        with open_file(fname) as f:
            addresses = _get_addresses(f, fname, size, start)
    sys.stderr.write('\n')

    code_blocks = []
    disassembler = Disassembler(snapshot)
    for address in addresses:
        size = disassembler.disassemble(address, address + 1)[0].size()
        if code_blocks and address <= sum(code_blocks[-1]):
            if address == sum(code_blocks[-1]):
                code_blocks[-1][1] += size
        else:
            code_blocks.append([address, size])

    return code_blocks

def _get_addresses(f, fname, size, start):
    addresses = set()
    base = 16
    i = 1
    rewind = True
    ignore_prefixes = ()

    s_line = ''
    while 1:
        line = f.readline()
        if not line:
            break
        i += 1
        s_line = line.strip()
        if s_line:
            break

    if s_line.startswith('0x'):
        # Fuse profile
        address_f = lambda s_line: s_line[2:6]
    elif s_line.startswith('PC = '):
        # Spud log
        address_f = lambda s_line: s_line[5:9]
    elif s_line.startswith('PC:'):
        # SpecEmu log
        address_f = lambda s_line: s_line[:4]
        ignore_prefixes = ('PC:', 'IX:', 'HL:', 'DE:', 'BC:', 'AF:')
        rewind = False
    elif s_line.endswith('decimal'):
        # Zero log
        if s_line.endswith('in decimal'):
            base = 10
        address_f = lambda s_line: s_line[:s_line.find('\t')]
        rewind = False
    else:
        raise CodeMapError('{0}: Unrecognised format'.format(fname))

    if rewind:
        f.seek(0)
        i = 1

    while 1:
        line = f.readline()
        if not line:
            break
        progress_msg = '{0}%'.format((100 * f.tell()) // size)
        sys.stderr.write(progress_msg + chr(8) * len(progress_msg))
        sys.stderr.flush()
        s_line = line.strip()
        if s_line:
            address_str = address_f(s_line)
            address = None
            if address_str:
                try:
                    address = int(address_str, base)
                except ValueError:
                    if not (ignore_prefixes and s_line.startswith(ignore_prefixes)):
                        raise CodeMapError('{0}, line {1}: Cannot parse address: {2}'.format(fname, i, s_line))
                if address is not None:
                    if address < 0 or address > 65535:
                        raise CodeMapError('{0}, line {1}: Address out of range: {2}'.format(fname, i, s_line))
                    if address >= start:
                        addresses.add(address)
        i += 1

    addresses = list(addresses)
    addresses.sort()

    return addresses

def _is_terminal_instruction(instruction):
    data = instruction.bytes
    if data[0] == 201:
        # RET
        return True
    if len(data) == 2 and data[0] == 237 and data[1] in (69, 77, 85, 93, 101, 109, 117, 125):
        # RETN/RETI
        return True
    if data[0] == 233:
        # JP (HL)
        return True
    if len(data) == 2 and data[0] in (221, 253) and data[1] == 233:
        # JP (IX)/JP (IY)
        return True
    if len(data) == 2 and data[0] == 24 and data[1] > 0:
        # JR d (d != 0)
        return True
    if len(data) == 3 and data[0] == 195:
        # JP nn
        return True
    return False

def _find_terminal_instruction(disassembler, ctls, start, end=65536, ctl=None):
    address = start
    while address < end:
        instruction = disassembler.disassemble(address, address + 1)[0]
        address = instruction.address + instruction.size()
        if ctl is None:
            for a in range(instruction.address, address):
                if a in ctls:
                    next_ctl = ctls[a]
                    del ctls[a]
            if ctls.get(address) == 'c':
                break
        if _is_terminal_instruction(instruction):
            if address < 65536 and address not in ctls:
                ctls[address] = ctl or next_ctl
            break
    return address

def _generate_ctls_with_code_map(snapshot, start, code_map):
    # (1) Use the code map to create an initial set of 'c' ctls, and mark all
    #     unexecuted blocks as 'U' (unknown)
    # (2) Where a 'c' block doesn't end with a RET/JP/JR, extend it up to the
    #     next RET/JP/JR in the following 'U' blocks, or up to the next 'c'
    #     block
    # (3) Mark entry points in 'U' blocks that are CALLed or JPed to from 'c'
    #     blocks with 'c'
    # (4) Split 'c' blocks on RET/JP/JR
    # (5) Scan the disassembly for pairs of adjacent blocks where the start
    #     address of the second block is JRed or JPed to from the first block,
    #     and join such pairs
    # (6) Examine the remaining 'U' blocks for text
    # (7) Mark data blocks of all zeroes with 's'

    # (1) Mark all executed blocks as 'c' and unexecuted blocks as 'U'
    # (unknown)
    ctls = {start: 'U'}
    for address, length in _get_code_blocks(snapshot, start, code_map):
        ctls[address] = 'c'
        if address + length < 65536:
            ctls[address + length] = 'U'

    # (2) Where a 'c' block doesn't end with a RET/JP/JR, extend it up to the
    # next RET/JP/JR in the following 'U' blocks, or up to the next 'c' block
    disassembler = Disassembler(snapshot)
    while 1:
        done = True
        for ctl, start, end in _get_blocks(ctls):
            if ctl == 'c':
                if _is_terminal_instruction(disassembler.disassemble(start, end)[-1]):
                    continue
                if _find_terminal_instruction(disassembler, ctls, end) < 65536:
                    done = False
                    break
        if done:
            break

    # (3) Mark entry points in 'U' blocks that are CALLed or JPed to from 'c'
    # blocks with 'c'
    ctl_parser = CtlParser()
    ctl_parser.ctls = ctls
    disassembly = Disassembly(snapshot, ctl_parser)
    while 1:
        disassembly.build(True)
        done = True
        for entry in disassembly.entries:
            if entry.ctl == 'U':
                for instruction in entry.instructions:
                    for referrer in instruction.referrers:
                        if ctls[referrer.address] == 'c':
                            ctls[instruction.address] = 'c'
                            if entry.next:
                                end = entry.next.address
                            else:
                                end = 65536
                            _find_terminal_instruction(disassembler, ctls, instruction.address, end, entry.ctl)
                            disassembly.remove_entry(entry.address)
                            done = False
                            break
                    if not done:
                        break
                if not done:
                    break
        if done:
            break

    # (4) Split 'c' blocks on RET/JP/JR
    for ctl, address, end in _get_blocks(ctls):
        if ctl == 'c':
            next_address = _find_terminal_instruction(disassembler, ctls, address, end, 'c')
            if next_address < end:
                disassembly.remove_entry(address)
                while next_address < end:
                    next_address = _find_terminal_instruction(disassembler, ctls, next_address, end, 'c')

    # (5) Scan the disassembly for pairs of adjacent blocks where the start
    # address of the second block is JRed or JPed to from the first block, and
    # join such pairs
    while 1:
        disassembly.build()
        done = True
        for entry in disassembly.entries[:-1]:
            if entry.ctl == 'c':
                for instruction in entry.instructions:
                    operation = instruction.operation
                    if operation[:2] in ('JR', 'JP') and operation[-5:] == str(entry.next.address):
                        del ctls[entry.next.address]
                        disassembly.remove_entry(entry.address)
                        disassembly.remove_entry(entry.next.address)
                        done = False
                        break
        if done:
            break

    # (6) Examine the 'U' blocks for text/data
    for ctl, start, end in _get_blocks(ctls):
        if ctl == 'U':
            ctls[start] = 'b'
            for t_start, t_end in _get_text_blocks(snapshot, start, end):
                ctls[t_start] = 't'
                if t_end < end:
                    ctls[t_end] = 'b'

    # (7) Mark data blocks of all zeroes with 's'
    for ctl, start, end in _get_blocks(ctls):
        if ctl == 'b':
            z_end = start
            while z_end < end and snapshot[z_end] == 0:
                z_end += 1
            if z_end > start:
                ctls[start] = 's'
                if z_end < end:
                    ctls[z_end] = 'b'

    return ctls

def _generate_ctls_without_code_map(snapshot, start):
    ctls = {}
    ctls[start] = 'c'

    # Look for potential 'RET', 'JR d' and 'JP nn' instructions and assume that
    # they end a block (after which another block follows); note that we don't
    # bother examining the byte at 65535 because no block can follow it
    for address in range(start, 65535):
        b = snapshot[address]
        if b == 201:
            ctls[address + 1] = 'c'
        elif b == 195 and address < 65533:
            ctls[address + 3] = 'c'
        elif b == 24 and address < 65534:
            ctls[address + 2] = 'c'

    ctl_parser = CtlParser()
    ctl_parser.ctls = ctls
    disassembly = Disassembly(snapshot, ctl_parser)

    # Scan the disassembly for pairs of adjacent blocks that overlap, and join
    # such pairs
    while True:
        done = True
        for entry in disassembly.entries[:-1]:
            if entry.bad_blocks:
                del ctls[entry.next.address]
                disassembly.remove_entry(entry.address)
                disassembly.remove_entry(entry.next.address)
                done = False
        if done:
            break
        disassembly.build()

    # Scan the disassembly for blocks that don't end in a 'RET', 'JP nn' or
    # 'JR d' instruction, and join them to the next block
    changed = False
    for entry in disassembly.entries[:-1]:
        last_instr = entry.instructions[-1].operation
        if last_instr != 'RET' and not (last_instr[:2] in ('JP', 'JR') and last_instr[3:].isdigit()):
            del ctls[entry.next.address]
            disassembly.remove_entry(entry.address)
            disassembly.remove_entry(entry.next.address)
            changed = True
    if changed:
        disassembly.build()

    # Scan the disassembly for pairs of adjacent blocks where the start address
    # of the second block is JRed or JPed to from the first block, and join
    # such pairs
    while True:
        done = True
        for entry in disassembly.entries[:-1]:
            for instruction in entry.instructions:
                operation = instruction.operation
                if operation[:2] in ('JR', 'JP') and operation[-5:] == str(entry.next.address):
                    del ctls[entry.next.address]
                    disassembly.remove_entry(entry.address)
                    disassembly.remove_entry(entry.next.address)
                    done = False
                    break
        if done:
            break
        disassembly.build()

    # Mark any NOP sequences at the beginning of a block as a separate zero
    # block
    for entry in disassembly.entries:
        if entry.instructions[0].operation != 'NOP':
            continue
        for instruction in entry.instructions[1:]:
            if instruction.operation != 'NOP':
                break
        ctls[entry.address] = 's'
        if entry.instructions[-1].operation != 'NOP':
            ctls[instruction.address] = 'c'

    # See which blocks marked as code look like text or data
    _analyse_blocks(disassembly)

    return ctls

def write_ctl(ctlfile, ctls, ctl_hex):
    # Write a control file
    addr_fmt = get_address_format(ctl_hex)
    with open(ctlfile, 'w') as f:
        for address in sorted(ctls.keys()):
            f.write('{0} {1}\n'.format(ctls[address], addr_fmt.format(address)))

def _check_for_data(snapshot, start, end):
    size = end - start
    if size > 3:
        count = 1
        prev_b = snapshot[start]
        for a in range(start + 1, end):
            b = snapshot[a]
            if b == prev_b:
                count += 1
                if count > 3:
                    return True
            else:
                count = 1
                prev_b = b
    if size > 9:
        d = len(set(snapshot[start:end]))
        return d < size * UNIQUE_BYTES_MAX

def _check_text(t_blocks, t_start, t_end, letters, punc):
    length = t_end - t_start
    if length >= MIN_LENGTH and len(set(letters)) >= length * UNIQUE_CHARS_MIN and len(punc) <= length * PUNC_CHARS_MAX:
        t_block = [t_start, t_end]
        if t_blocks:
            prev_t_block = t_blocks[-1]
            if prev_t_block[1] + TEXT_GAP_MAX >= t_start:
                # If the previous t-block is close to this one, merge them
                prev_t_block[1] = t_end
            else:
                t_blocks.append(t_block)
        else:
            t_blocks.append(t_block)

def _get_text_blocks(snapshot, start, end):
    t_blocks = []
    if end - start >= MIN_LENGTH:
        letters = []
        punc = []
        t_start = None
        for address in range(start, end):
            char = chr(snapshot[address])
            if char in CHARS:
                if char in PUNC_CHARS:
                    punc.append(char)
                else:
                    letters.append(char)
                if t_start is None:
                    t_start = address
            else:
                if t_start:
                    _check_text(t_blocks, t_start, address, letters, punc)
                letters[:] = []
                punc[:] = []
                t_start = None
        if t_start:
            _check_text(t_blocks, t_start, end, letters, punc)
    return t_blocks

def _get_blocks(ctls):
    # Determine the block start and end addresses
    blocks = [[ctls[address], address, None] for address in sorted(ctls.keys())]
    for i, block in enumerate(blocks[1:]):
        blocks[i][2] = block[1]
    blocks[-1][2] = 65536
    return blocks

def _analyse_blocks(disassembly):
    snapshot = disassembly.disassembler.snapshot
    ctls = disassembly.ctl_parser.ctls

    # See which blocks marked as code look like text or data
    while 1:
        done = True
        for ctl, start, end in _get_blocks(ctls):
            if ctl == 'c':
                text_blocks = _get_text_blocks(snapshot, start, end)
                if text_blocks:
                    for t_start, t_end in text_blocks:
                        ctls[t_start] = 't'
                        ctls[t_end] = 'c'
                    disassembly.remove_entry(start)
                    done = False
                elif _check_for_data(snapshot, start, end):
                    ctls[start] = 'b'
                    disassembly.remove_entry(start)
                else:
                    # This block is unidentified (it doesn't look like text or
                    # data); mark it with an 'X' so that we don't examine it
                    # again
                    ctls[start] = 'X'
        if done:
            break

    # Relabel the unidentified blocks as code
    for address, ctl in ctls.items():
        if ctl == 'X':
            ctls[address] = 'c'

    # Scan the disassembly for pairs of adjacent blocks that overlap, and mark
    # the first block in each pair as data; also mark code blocks that have no
    # terminal instruction as data
    disassembly.build()
    for entry in disassembly.entries[:-1]:
        if entry.bad_blocks or (entry.ctl == 'c' and not _is_terminal_instruction(entry.instructions[-1])):
            ctls[entry.address] = 'b'

    # Mark any NOP sequences at the beginning of a code block as a separate
    # zero block
    for ctl, start, end in _get_blocks(ctls):
        if ctl == 'c':
            z_end = start
            while z_end < end and snapshot[z_end] == 0:
                z_end += 1
            if z_end > start:
                ctls[start] = 's'
                if z_end < end:
                    ctls[z_end] = 'c'

def generate_ctls(snapshot, start, code_map):
    if code_map:
        ctls = _generate_ctls_with_code_map(snapshot, start, code_map)
    else:
        ctls = _generate_ctls_without_code_map(snapshot, start)

    # Join any adjacent data and zero blocks
    blocks = _get_blocks(ctls)
    prev_block = blocks[0]
    for block in blocks[1:]:
        if prev_block[0] in 'bs' and block[0] in 'bs':
            ctls[prev_block[1]] = 'b'
            del ctls[block[1]]
        else:
            prev_block = block

    return ctls

class Entry:
    def __init__(self, title, description, ctl, blocks, registers, end_comment, asm_directives):
        self.title = title
        self.ctl = ctl
        self.blocks = blocks
        self.instructions = []
        for block in blocks:
            for instruction in block.instructions:
                instruction.entry = self
                self.instructions.append(instruction)
        first_instruction = self.instructions[0]
        first_instruction.ctl = ctl
        self.registers = registers
        self.end_comment = end_comment
        self.start = None
        self.writer = None
        self.org = None
        self.end = None
        self.properties = []
        for directive, value in asm_directives:
            if directive == AD_START:
                self.start = True
            elif directive == AD_WRITER:
                self.writer = value
            elif directive == AD_ORG:
                self.org = value
            elif directive == AD_END:
                self.end = True
            elif directive.startswith(AD_SET):
                self.properties.append((directive[len(AD_SET):], value))
        self.address = first_instruction.address
        self.description = description
        self.next = None
        self.bad_blocks = []
        for block in self.blocks:
            last_instruction = block.instructions[-1]
            if last_instruction.address + last_instruction.size() > block.end:
                self.bad_blocks.append(block)

    def width(self):
        return max([len(i.operation) for i in self.instructions])

class Disassembly:
    def __init__(self, snapshot, ctl_parser, final=False, defb_size=8, defb_mod=1, zfill=False, defm_width=66, asm_hex=False, asm_lower=False):
        self.disassembler = Disassembler(snapshot, defb_size, defb_mod, zfill, defm_width, asm_hex, asm_lower)
        self.ctl_parser = ctl_parser
        if asm_hex:
            if asm_lower:
                self.address_fmt = '{0:04x}'
            else:
                self.address_fmt = '{0:04X}'
        else:
            self.address_fmt = '{0}'
        self.entry_map = {}
        self.build(final)

    def build(self, final=False):
        self.instructions = {}
        self.entries = []
        self._create_entries()
        self.org = self.entries[0].address
        if final:
            self._calculate_references()

    def _create_entries(self):
        for block in self.ctl_parser.get_blocks():
            if block.start in self.entry_map:
                entry = self.entry_map[block.start]
                self.entries.append(entry)
                for instruction in entry.instructions:
                    self.instructions[instruction.address] = instruction
                continue
            title = self.ctl_parser.get_block_title(block.start)
            if block.ctl == 'c':
                title = title or 'Routine at {0}'.format(self.address_str(block.start))
            elif block.ctl in 'bw':
                title = title or 'Data block at {0}'.format(self.address_str(block.start))
            elif block.ctl == 't':
                title = title or 'Message at {0}'.format(self.address_str(block.start))
            elif block.ctl == 'g':
                title = title or 'Game status buffer entry at {0}'.format(self.address_str(block.start))
            elif block.ctl in 'us':
                title = title or 'Unused'
            for sub_block in block.blocks:
                if sub_block.ctl in 'cBT':
                    instructions = self.disassembler.disassemble(sub_block.start, sub_block.end)
                elif sub_block.ctl in 'bgstuw':
                    address = sub_block.start
                    lengths = list(self.ctl_parser.get_lengths(address))
                    one_line = True
                    if not lengths:
                        lengths = [(None, None)]
                    instructions = []
                    while address < sub_block.end:
                        if lengths:
                            length, sublengths = lengths.pop(0)
                        if length is None:
                            one_line = False
                            length = sub_block.end - sub_block.start
                        end = min((address + length, sub_block.end))
                        if sub_block.ctl == 't':
                            instructions += self.disassembler.defm_range(address, end, one_line, sublengths)
                        elif sub_block.ctl == 'w':
                            instructions += self.disassembler.defw_range(address, end, one_line, sublengths)
                        elif sub_block.ctl == 's':
                            instructions.append(self.disassembler.defs(address, end, sublengths))
                        else:
                            instructions += self.disassembler.defb_range(address, end, one_line, sublengths)
                        address += length
                else:
                    instructions = self.disassembler.ignore(sub_block.start, sub_block.end)
                sub_block.header = self.ctl_parser.get_mid_block_comment(sub_block.start)
                sub_block.comment = self.ctl_parser.get_instruction_comment(sub_block.start)
                sub_block.instructions = instructions
                for instruction in instructions:
                    self.instructions[instruction.address] = instruction
                    instruction.asm_directives = self.ctl_parser.get_instruction_asm_directives(instruction.address)

            sub_blocks = []
            i = 0
            while i < len(block.blocks):
                sub_block = block.blocks[i]
                i += 1
                sub_blocks.append(sub_block)
                end, comment = self.ctl_parser.get_multiline_comment(sub_block.start)
                if comment is not None:
                    sub_block.comment = comment
                    while i < len(block.blocks) and (end is None or block.blocks[i].start <= end):
                        sub_block.instructions += block.blocks[i].instructions
                        sub_block.end = block.end
                        i += 1

            description = self.ctl_parser.get_description(block.start)
            registers = self.ctl_parser.get_registers(block.start)
            end_comment = self.ctl_parser.get_end_comment(block.start)
            asm_directives = self.ctl_parser.get_entry_asm_directives(block.start)
            entry = Entry(title, description, block.ctl, sub_blocks, registers, end_comment, asm_directives)
            self.entry_map[entry.address] = entry
            self.entries.append(entry)
        for i, entry in enumerate(self.entries[1:]):
            self.entries[i].next = entry

    def remove_entry(self, address):
        if address in self.entry_map:
            del self.entry_map[address]

    def _calculate_references(self):
        for entry in self.entries:
            for instruction in entry.instructions:
                instruction.referrers = []
        for entry in self.entries:
            if entry.ctl == 'c':
                for instruction in entry.instructions:
                    operation = instruction.operation
                    if operation.upper().startswith(('DJ', 'JR', 'JP', 'CA', 'RS')):
                        addr_str = get_address(operation)
                        if addr_str:
                            callee = self.instructions.get(parse_int(addr_str))
                            if callee:
                                callee.add_referrer(entry)

    def address_str(self, address):
        return self.address_fmt.format(address)

class SkoolWriter:
    def __init__(self, snapshot, ctl_parser, options):
        self.ctl_parser = ctl_parser
        self.comment_width = max(options.line_width - 2, MIN_COMMENT_WIDTH)
        self.disassembly = Disassembly(snapshot, ctl_parser, True, options.defb_size, options.defb_mod, options.zfill,
                                       options.defm_width, options.asm_hex, options.asm_lower)
        self.address_fmt = get_address_format(options.asm_hex, options.asm_lower)
        self.asm_hex = options.asm_hex

    def address_str(self, address, pad=True):
        if self.asm_hex or pad:
            return self.address_fmt.format(address)
        return str(address)

    def write_skool(self, write_refs, text):
        if not self.ctl_parser.contains_entry_asm_directive(AD_START):
            self.write_asm_directive(AD_START)
            if not self.ctl_parser.contains_entry_asm_directive(AD_ORG):
                self.write_asm_directive(AD_ORG, self.address_str(self.disassembly.org, False))
        for entry_index, entry in enumerate(self.disassembly.entries):
            if entry_index:
                write_line('')
            self._write_entry(entry, write_refs, text)

    def _write_entry(self, entry, write_refs, show_text):
        if entry.start:
            self.write_asm_directive(AD_START)
        if entry.writer:
            self.write_asm_directive(AD_WRITER, entry.writer)
        for name, value in entry.properties:
            self.write_asm_directive('{}{}'.format(AD_SET, name), value)
        if entry.org is not None:
            self.write_asm_directive(AD_ORG, entry.org)
        if self.ctl_parser.has_ignoreua_directive(entry.address, TITLE):
            self.write_asm_directive(AD_IGNOREUA)

        if entry.ctl == 'i':
            end = entry.blocks[0].end
            if end < 65536:
                if entry.title:
                    self.write_comment(entry.title)
                write_line('{}{}'.format(entry.ctl, self.address_str(entry.blocks[0].start)))
            return

        for block in entry.bad_blocks:
            warn('Code block at {} overlaps the following block at {}'.format(self.address_str(block.start, False), self.address_str(block.end, False)))

        self.write_comment(entry.title)
        wrote_desc = self._write_entry_description(entry, write_refs)
        if entry.registers:
            if not wrote_desc:
                self._write_empty_paragraph()
                wrote_desc = True
            self._write_registers(entry)

        self._write_body(entry, wrote_desc, write_refs, show_text)

        if self.ctl_parser.has_ignoreua_directive(entry.address, END):
            self.write_asm_directive(AD_IGNOREUA)
        self.write_paragraphs(entry.end_comment)
        if entry.end:
            self.write_asm_directive(AD_END)

    def _write_entry_description(self, entry, write_refs):
        wrote_desc = False
        ignoreua_d = self.ctl_parser.has_ignoreua_directive(entry.address, DESCRIPTION)
        if entry.ctl == 'c' and write_refs > -1:
            referrers = entry.instructions[0].referrers
            if referrers and (write_refs == 1 or not entry.description):
                self.write_comment('')
                if ignoreua_d:
                    self.write_asm_directive(AD_IGNOREUA)
                self.write_referrers(REFS_PREFIX, referrers)
                wrote_desc = True
        if entry.description:
            if wrote_desc:
                self._write_paragraph_separator()
            else:
                self.write_comment('')
                if ignoreua_d:
                    self.write_asm_directive(AD_IGNOREUA)
            self.write_paragraphs(entry.description)
            wrote_desc = True
        return wrote_desc

    def _write_registers(self, entry):
        self.write_comment('')
        if self.ctl_parser.has_ignoreua_directive(entry.address, REGISTERS):
            self.write_asm_directive(AD_IGNOREUA)
        max_indent = max([reg.find(':') for reg, desc in entry.registers])
        for reg, desc in entry.registers:
            reg = reg.rjust(max_indent + len(reg) - reg.find(':'))
            if desc:
                desc_indent = len(reg) + 1
                desc_lines = wrap(desc, max(self.comment_width - desc_indent, MIN_COMMENT_WIDTH))
                write_line('; {} {}'.format(reg, desc_lines[0]))
                desc_prefix = '.'.ljust(desc_indent)
                for line in desc_lines[1:]:
                    write_line('; {}{}'.format(desc_prefix, line))
            else:
                write_line('; {}'.format(reg))

    def _write_body(self, entry, wrote_desc, write_refs, show_text):
        op_width = max((OP_WIDTH, entry.width()))
        line_width = op_width + 8
        first_block = True
        for block in entry.blocks:
            ignoreua_m = self.ctl_parser.has_ignoreua_directive(block.start, MID_BLOCK)
            begun_header = False
            if not first_block and entry.ctl == 'c' and write_refs > -1:
                referrers = block.instructions[0].referrers
                if referrers and (write_refs == 1 or not block.header):
                    if ignoreua_m:
                        self.write_asm_directive(AD_IGNOREUA)
                    self.write_referrers(EREFS_PREFIX, referrers)
                    begun_header = True
            if block.header:
                if first_block:
                    if not wrote_desc:
                        self._write_empty_paragraph()
                    if not entry.registers:
                        self._write_empty_paragraph()
                    self.write_comment('')
                if begun_header:
                    self._write_paragraph_separator()
                elif ignoreua_m:
                    self.write_asm_directive(AD_IGNOREUA)
                self.write_paragraphs(block.header)
            rowspan = len(block.instructions)
            multi_line = rowspan > 1 and block.comment
            if multi_line:
                if not block.comment.replace('.', ''):
                    block.comment = block.comment[1:]
                block.comment = '{{{}}}'.format(block.comment)
            comment_lines = wrap(block.comment, max(self.comment_width - line_width, MIN_INSTRUCTION_COMMENT_WIDTH))
            if multi_line and len(comment_lines) < rowspan:
                comment_lines[-1] = comment_lines[-1][:-1]
                comment_lines.extend([''] * (rowspan - len(comment_lines) - 1))
                comment_lines.append('}')
            self._write_instructions(entry, block, op_width, comment_lines, write_refs, show_text)
            indent = ' ' * line_width
            for j in range(len(block.instructions), len(comment_lines)):
                write_line('{}; {}'.format(indent, comment_lines[j]))
            first_block = False

    def _write_instructions(self, entry, block, op_width, comment_lines, write_refs, show_text):
        index = 0
        for instruction in block.instructions:
            ctl = instruction.ctl or ' '
            address = instruction.address
            operation = instruction.operation
            if block.comment:
                comment = comment_lines[index]
            elif show_text and entry.ctl != 't':
                comment = self.to_ascii(instruction.bytes)
            else:
                comment = ''
            if index > 0 and entry.ctl == 'c' and ctl == '*' and write_refs > -1:
                self.write_referrers(EREFS_PREFIX, instruction.referrers)
            for directive, value in instruction.asm_directives:
                self.write_asm_directive(directive, value)
            if self.ctl_parser.has_ignoreua_directive(instruction.address, INSTRUCTION):
                self.write_asm_directive(AD_IGNOREUA)
            if entry.ctl == 'c' or comment:
                write_line(('{}{} {} ; {}'.format(ctl, self.address_str(address), operation.ljust(op_width), comment)).rstrip())
            else:
                write_line(('{}{} {}'.format(ctl, self.address_str(address), operation)).rstrip())
            index += 1

    def write_comment(self, text):
        if text:
            for line in self.wrap(text):
                write_line('; {0}'.format(line))
        else:
            write_line(';')

    def _write_empty_paragraph(self):
        self.write_comment('')
        self.write_comment('.')

    def _write_paragraph_separator(self):
        self.write_comment('.')

    def write_paragraphs(self, paragraphs):
        if paragraphs:
            for p in paragraphs[:-1]:
                self.write_comment(p)
                self._write_paragraph_separator()
            self.write_comment(paragraphs[-1])

    def write_referrers(self, prefix, referrers):
        if referrers:
            if len(referrers) == 1:
                infix = 'routine at '
            else:
                infix = 'routines at {} and '.format(', '.join('#R{}'.format(self.address_str(r.address, False)) for r in referrers[:-1]))
            suffix = '#R{}'.format(self.address_str(referrers[-1].address, False))
            self.write_comment('{0}{1}{2}.'.format(prefix, infix, suffix))

    def write_asm_directive(self, directive, value=None):
        if value is None:
            suffix = ''
        else:
            suffix = '={0}'.format(value)
        write_line('@{}{}'.format(directive, suffix))

    def to_ascii(self, data):
        chars = ['[']
        for b in data:
            if 32 <= b < 127:
                chars.append(chr(b))
            else:
                chars.append('.')
        chars.append(']')
        return ''.join(chars)

    def wrap(self, text):
        lines = []
        for line in self.parse_blocks(text):
            lines.extend(wrap(line, self.comment_width))
        return lines

    def parse_block(self, text, start):
        indexes = []
        index = text.index(' ', start)
        indexes.append(index)
        index += 1

        # Parse the table rows or list items
        while True:
            start = text.find('{ ', index)
            if start < 0:
                break
            end = text.index(' }', start)
            index = end + 2
            indexes.append(index)

        indexes.append(len(text))
        return indexes

    def parse_blocks(self, text):
        markers = ((TABLE_MARKER, TABLE_END_MARKER), (UDGTABLE_MARKER, TABLE_END_MARKER), (LIST_MARKER, LIST_END_MARKER))
        indexes = []

        # Find table/list markers and row/item definitions
        index = 0
        while True:
            starts = [text.find(marker[0], index) for marker in markers]
            for i, start in enumerate(starts):
                if start >= 0:
                    if start > 0:
                        indexes.append(start - 1)
                    marker, end_marker = markers[i]
                    try:
                        end = text.index(end_marker, start) + len(end_marker)
                    except ValueError:
                        raise SkoolKitError("No end marker found: {}...".format(text[start:start + len(marker) + 15]))
                    indexes.extend(self.parse_block(text[:end], start + len(marker)))
                    break
            else:
                break
            index = indexes[-1] + 1

        # Insert newlines
        end = len(text)
        if end not in indexes:
            indexes.append(end)
        indexes.sort()
        lines = []
        start = 0
        for end in indexes:
            lines.append(text[start:end])
            start = end + 1
        return lines
