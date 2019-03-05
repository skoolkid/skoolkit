# Copyright 2009-2019 Richard Dymond (rjdymond@gmail.com)
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
from skoolkit.opcodes import END, decode
from skoolkit.skoolctl import AD_ORG, AD_START
from skoolkit.snaskool import Disassembly

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
    for address in addresses:
        size = next(decode(snapshot, address, address + 1))[1]
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

def _find_terminal_instruction(snapshot, ctls, start, end, ctl=None):
    address = start
    while address < end:
        i_addr, size, max_count, op_id = next(decode(snapshot, address, address + 1))[:4]
        address += size
        if ctl is None:
            for a in range(i_addr, address):
                if a in ctls:
                    next_ctl = ctls[a]
                    del ctls[a]
            if ctls.get(address) == 'c':
                break
        if op_id == END:
            if address < 65536 and address not in ctls:
                ctls[address] = ctl or next_ctl
            break
    return address

def _get_blocks(ctls):
    # Determine the block start and end addresses
    blocks = [[ctls[address], address, None] for address in sorted(ctls)]
    for i, block in enumerate(blocks[1:]):
        blocks[i][2] = block[1]
    blocks.pop()
    return blocks

def _generate_ctls_with_code_map(snapshot, start, end, config, code_map):
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
    while 1:
        done = True
        for ctl, b_start, b_end in _get_blocks(ctls):
            if ctl == 'c':
                last_op_id = list(decode(snapshot, b_start, b_end))[-1][3]
                if last_op_id == END:
                    continue
                if _find_terminal_instruction(snapshot, ctls, b_end, end) < end:
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
                            _find_terminal_instruction(snapshot, ctls, instruction.address, e_end, entry.ctl)
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
            next_address = _find_terminal_instruction(snapshot, ctls, b_address, b_end, 'c')
            if next_address < b_end:
                disassembly.remove_entry(b_address)
                while next_address < b_end:
                    next_address = _find_terminal_instruction(snapshot, ctls, next_address, b_end, 'c')

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
            for t_start, t_end in _get_text_blocks(snapshot, b_start, b_end, config):
                ctls[t_start] = 't'
                if t_end < b_end:
                    ctls[t_end] = 'b'

    # (7) Mark data blocks of all zeroes with 's'
    for ctl, b_start, b_end in _get_blocks(ctls):
        if ctl == 'b' and sum(snapshot[b_start:b_end]) == 0:
            ctls[b_start] = 's'

    return ctls

def _check_text(t_blocks, t_start, t_end, text, min_length, config):
    if len(text) >= min_length:
        words = config.get('words')
        if words:
            t_lower = text.lower()
            for word in words:
                if word in t_lower:
                    break
            else:
                return
        t_blocks.append((t_start, t_end))

def _get_text_blocks(snapshot, start, end, config, data=True):
    if data:
        min_length = config['TextMinLengthData']
    else:
        min_length = config['TextMinLengthCode']
    t_blocks = []
    if end - start >= min_length:
        text = ''
        for address in range(start, end):
            char = chr(snapshot[address])
            if char in config['TextChars']:
                if not text:
                    t_start = address
                text += char
            elif text:
                _check_text(t_blocks, t_start, address, text, min_length, config)
                text = ''
        if text:
            _check_text(t_blocks, t_start, end, text, min_length, config)
    return t_blocks

def _catch_data(ctls, ctl_addr, count, max_count, addr, op, op_bytes):
    if count >= max_count > 0:
        # A 2-instruction sequence ending with 'LD H,(HL)' or 'LD L,(HL)' is OK
        if not (count == 2 and op_bytes[0] in (0x66, 0x6E)):
            if not ctls or ctls[-1][1] != 'b':
                ctls.append((ctl_addr, 'b'))
            return addr
    return ctl_addr

def _generate_ctls_without_code_map(snapshot, start, end, config):
    ctls = []
    ctl_addr = start
    prev_max_count, prev_op_id, prev_op, prev_op_bytes = 0, None, None, ()
    count = 1
    for addr, size, max_count, op_id, operation in decode(snapshot, start, end):
        op_bytes = snapshot[addr:addr + size]
        if op_id == END:
            # Catch data-like sequences that precede a terminal instruction
            ctl_addr = _catch_data(ctls, ctl_addr, count, prev_max_count, addr, prev_op, prev_op_bytes)
            ctls.append((ctl_addr, 'c'))
            ctl_addr = addr + size
            prev_max_count, prev_op_id, prev_op, prev_op_bytes = 0, None, None, ()
            count = 1
            continue
        if op_id == prev_op_id:
            count += 1
        elif prev_op:
            ctl_addr = _catch_data(ctls, ctl_addr, count, prev_max_count, addr, prev_op, prev_op_bytes)
            count = 1
        prev_max_count, prev_op_id, prev_op, prev_op_bytes = max_count, op_id, operation, op_bytes

    if not ctls or ctls[-1][0] != ctl_addr:
        ctls.append((ctl_addr, 'b'))
    ctls.append((end, 'i'))

    ctls = dict(ctls)

    # Mark a NOP sequence at the beginning of a code block as a zero block,
    # and mark a data block of all zeroes as a zero block
    edges = sorted(ctls)
    for i in range(len(edges) - 1):
        start, end = edges[i], edges[i + 1]
        if ctls[start] == 'c':
            ctls[start] = 's'
            for address in range(start, end):
                if snapshot[address]:
                    ctls[address] = 'c'
                    break
        elif set(snapshot[start:end]) == {0}:
            ctls[start] = 's'

    # Join any adjacent data and zero blocks
    ctls_s = sorted(ctls.items())
    prev_addr, prev_ctl = ctls_s[0]
    for addr, ctl in ctls_s[1:]:
        if ctl in 'bs' and prev_ctl in 'bs':
            ctls[prev_addr] = 'b'
            del ctls[addr]
        else:
            prev_addr, prev_ctl = addr, ctl

    # Look for text
    edges = sorted(ctls)
    for i in range(len(edges) - 1):
        start, end = edges[i], edges[i + 1]
        if ctls[start] == 'b':
            for t_start, t_end in _get_text_blocks(snapshot, start, end, config):
                ctls[t_start] = 't'
                if t_end < end:
                    ctls[t_end] = 'b'
        elif ctls[start] == 'c':
            text_blocks = _get_text_blocks(snapshot, start, end, config, False)
            if text_blocks:
                ctls[start] = 'b'
                for t_start, t_end in text_blocks:
                    ctls[t_start] = 't'
                    if t_end < end:
                        ctls[t_end] = 'b'
                if t_end < end:
                    ctls[t_end] = 'c'

    return ctls

def write_ctl(ctls, ctl_hex):
    addr_fmt = get_address_format(ctl_hex, ctl_hex == 1)
    start = addr_fmt.format(min(ctls))
    write_line('@ {} {}'.format(start, AD_START))
    write_line('@ {} {}'.format(start, AD_ORG))
    for address in [a for a in sorted(ctls) if a < 65536]:
        write_line('{} {}'.format(ctls[address], addr_fmt.format(address)))

def generate_ctls(snapshot, start, end, config, code_map):
    if code_map:
        return _generate_ctls_with_code_map(snapshot, start, end, config, code_map)
    return _generate_ctls_without_code_map(snapshot, start, end, config)
