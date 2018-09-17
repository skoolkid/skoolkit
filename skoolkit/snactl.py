# Copyright 2009-2018 Richard Dymond (rjdymond@gmail.com)
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

from skoolkit import SkoolKitError, open_file, read_bin_file, write_line, get_address_format
from skoolkit.ctlparser import CtlParser
from skoolkit.disassembler import Disassembler
from skoolkit.skoolctl import AD_ORG, AD_START
from skoolkit.snaskool import Disassembly

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

def _get_code_blocks(snapshot, start, end, fname):
    if os.path.isdir(fname):
        raise SkoolKitError('{0} is a directory'.format(fname))
    try:
        size = os.path.getsize(fname)
    except OSError as e:
        if e.errno == 2:
            raise SkoolKitError('{0}: file not found'.format(fname))
        raise SkoolKitError('Failed to get size of {}: {}'.format(fname, e.strerror))

    if size == 8192:
        # Assume this is a Z80 map file
        sys.stderr.write('Reading {0}'.format(fname))
        sys.stderr.flush()
        addresses = []
        data = read_bin_file(fname)
        address = start & 65528
        for b in data[start // 8:end // 8 + 1]:
            for i in range(8):
                if b & 1 and start <= address < end:
                    addresses.append(address)
                b >>= 1
                address += 1
    elif size == 65536:
        # Assume this is a SpecEmu map file
        sys.stderr.write('Reading {}'.format(fname))
        sys.stderr.flush()
        addresses = []
        data = read_bin_file(fname)
        for address in range(start, end):
            if data[address] & 1:
                addresses.append(address)
    else:
        sys.stderr.write('Reading {0}: '.format(fname))
        sys.stderr.flush()
        with open_file(fname) as f:
            addresses = _get_addresses(f, fname, size, start, end)
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

def _get_addresses(f, fname, size, start, end):
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
                    if start <= address < end:
                        addresses.add(address)
        i += 1

    return sorted(addresses)

def _is_terminal_instruction(instruction):
    data = instruction.bytes
    if data[0] in (195, 201, 233):
        # JP nn / RET / JP (HL)
        return True
    if len(data) == 2:
        if data[0] == 237 and data[1] in (69, 77, 85, 93, 101, 109, 117, 125):
            # RETN/RETI
            return True
        if data[0] in (221, 253) and data[1] == 233:
            # JP (IX)/JP (IY)
            return True
        if data[0] == 24 and data[1] > 0:
            # JR d (d != 0)
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

def _generate_ctls_with_code_map(snapshot, start, end, code_map):
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
    ctls = {start: 'U', end: 'i'}
    for address, length in _get_code_blocks(snapshot, start, end, code_map):
        ctls[address] = 'c'
        if address + length < end:
            ctls[address + length] = 'U'

    # (2) Where a 'c' block doesn't end with a RET/JP/JR, extend it up to the
    # next RET/JP/JR in the following 'U' blocks, or up to the next 'c' block
    disassembler = Disassembler(snapshot)
    while 1:
        done = True
        for ctl, b_start, b_end in _get_blocks(ctls):
            if ctl == 'c':
                if _is_terminal_instruction(disassembler.disassemble(b_start, b_end)[-1]):
                    continue
                if _find_terminal_instruction(disassembler, ctls, b_end, end) < end:
                    done = False
                    break
        if done:
            break

    # (3) Mark entry points in 'U' blocks that are CALLed or JPed to from 'c'
    # blocks with 'c'
    ctl_parser = CtlParser(ctls)
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
                                e_end = entry.next.address
                            else:
                                e_end = 65536
                            _find_terminal_instruction(disassembler, ctls, instruction.address, e_end, entry.ctl)
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
    for ctl, b_address, b_end in _get_blocks(ctls):
        if ctl == 'c':
            next_address = _find_terminal_instruction(disassembler, ctls, b_address, b_end, 'c')
            if next_address < b_end:
                disassembly.remove_entry(b_address)
                while next_address < b_end:
                    next_address = _find_terminal_instruction(disassembler, ctls, next_address, b_end, 'c')

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
    for ctl, b_start, b_end in _get_blocks(ctls):
        if ctl == 'U':
            ctls[b_start] = 'b'
            for t_start, t_end in _get_text_blocks(snapshot, b_start, b_end):
                ctls[t_start] = 't'
                if t_end < b_end:
                    ctls[t_end] = 'b'

    # (7) Mark data blocks of all zeroes with 's'
    for ctl, b_start, b_end in _get_blocks(ctls):
        if ctl == 'b' and sum(snapshot[b_start:b_end]) == 0:
            ctls[b_start] = 's'

    return ctls

def _generate_ctls_without_code_map(snapshot, start, end):
    ctls = {start: 'c', end: 'i'}

    # Look for potential 'RET', 'JR d' and 'JP nn' instructions and assume that
    # they end a block (after which another block follows); note that we don't
    # bother examining the final byte because no block can follow it
    for address in range(start, end - 1):
        b = snapshot[address]
        if b == 201:
            ctls[address + 1] = 'c'
        elif b == 195 and address < end - 3:
            ctls[address + 3] = 'c'
        elif b == 24 and address < end - 2:
            ctls[address + 2] = 'c'

    ctl_parser = CtlParser(ctls)
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
            next_address = entry.next.address
            if next_address < end:
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

    # Mark a NOP sequence at the beginning of a block as a separate zero block
    for entry in disassembly.entries:
        ctls[entry.address] = 's'
        for instruction in entry.instructions:
            if instruction.operation != 'NOP':
                ctls[instruction.address] = 'c'
                break

    # See which blocks marked as code look like text or data
    _analyse_blocks(disassembly, ctls)

    return ctls

def write_ctl(ctls, ctl_hex):
    addr_fmt = get_address_format(ctl_hex, ctl_hex == 1)
    start = addr_fmt.format(min(ctls))
    write_line('@ {} {}'.format(start, AD_START))
    write_line('@ {} {}'.format(start, AD_ORG))
    for address in [a for a in sorted(ctls) if a < 65536]:
        write_line('{} {}'.format(ctls[address], addr_fmt.format(address)))

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
    blocks = [[ctls[address], address, None] for address in sorted(ctls)]
    for i, block in enumerate(blocks[1:]):
        blocks[i][2] = block[1]
    blocks.pop()
    return blocks

def _analyse_blocks(disassembly, ctls):
    snapshot = disassembly.disassembler.snapshot

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
    for entry in disassembly.entries:
        if entry.bad_blocks or (ctls[entry.address] == 'c' and not _is_terminal_instruction(entry.instructions[-1])):
            ctls[entry.address] = 'b'

    # Mark a NOP sequence at the beginning of a code block as a zero block
    for ctl, start, end in _get_blocks(ctls):
        if ctl == 'c':
            ctls[start] = 's'
            for address in range(start, end):
                if snapshot[address]:
                    ctls[address] = 'c'
                    break

def generate_ctls(snapshot, start, end, code_map):
    if code_map:
        ctls = _generate_ctls_with_code_map(snapshot, start, end, code_map)
    else:
        ctls = _generate_ctls_without_code_map(snapshot, start, end)

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
