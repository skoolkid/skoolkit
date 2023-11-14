# Copyright 2009-2013, 2015-2023 Richard Dymond (rjdymond@gmail.com)
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

import textwrap
import zlib

from skoolkit import SkoolKitError, get_dword, get_int_param, parse_int, read_bin_file
from skoolkit.components import get_snapshot_reader, get_value

FRAME_DURATIONS = (69888, 70908)

# https://worldofspectrum.net/faq/reference/z80format.htm
Z80_REGISTERS = {
    'a': 0,
    'f': 1,
    'bc': 2,
    'c': 2,
    'b': 3,
    'hl': 4,
    'l': 4,
    'h': 5,
    'sp': 8,
    'i': 10,
    'r': 11,
    'de': 13,
    'e': 13,
    'd': 14,
    '^bc': 15,
    '^c': 15,
    '^b': 16,
    '^de': 17,
    '^e': 17,
    '^d': 18,
    '^hl': 19,
    '^l': 19,
    '^h': 20,
    '^a': 21,
    '^f': 22,
    'iy': 23,
    'ix': 25,
    'pc': 32
}

# https://spectaculator.com/docs/zx-state/z80regs.shtml
SZX_REGISTERS = {
    'a': 1,
    'f': 0,
    'bc': 2,
    'c': 2,
    'b': 3,
    'de': 4,
    'e': 4,
    'd': 5,
    'hl': 6,
    'l': 6,
    'h': 7,
    '^a': 9,
    '^f': 8,
    '^bc': 10,
    '^c': 10,
    '^b': 11,
    '^de': 12,
    '^e': 12,
    '^d': 13,
    '^hl': 14,
    '^l': 14,
    '^h': 15,
    'ix': 16,
    'iy': 18,
    'sp': 20,
    'pc': 22,
    'i': 24,
    'r': 25
}

class Memory:
    def __init__(self, snapshot=None, banks=None, page=None):
        if banks:
            self.banks = banks
            self.memory = [[0] * 0x4000, self.banks[5], self.banks[2], self.banks[page]]
        elif len(snapshot) == 0x20000:
            self.banks = [snapshot[a:a + 0x4000] for a in range(0, 0x20000, 0x4000)]
            self.memory = [[0] * 0x4000, self.banks[5], self.banks[2], self.banks[page]]
        else:
            self.banks = None
            self.memory = [[0] * 0x4000, snapshot[0x4000:0x8000], snapshot[0x8000:0xC000], snapshot[0xC000:]]

    def __getitem__(self, index):
        if isinstance(index, int):
            return self.memory[index // 0x4000][index % 0x4000]
        return [self.memory[a // 0x4000][a % 0x4000] for a in range(index.start, min(index.stop, 0x10000))]

    def __setitem__(self, index, value):
        if isinstance(index, int):
            self.memory[index // 0x4000][index % 0x4000] = value
        else:
            for a, b in zip(range(index.start, index.stop), value):
                self.memory[a // 0x4000][a % 0x4000] = b

    def contents(self):
        if self.banks:
            return self.banks
        return self.memory[1] + self.memory[2] + self.memory[3]

class SZX:
    def __init__(self, szxfile):
        self.blocks = {}
        banks = [None] * 8
        data = bytearray(read_bin_file(szxfile))
        if len(data) < 8 or data[:4] != b'ZXST':
            raise SnapshotError(f'{szxfile}: invalid SZX file')
        self.header = data[:8]
        page = 0
        i = 8
        while i + 8 <= len(data):
            block_id = data[i:i + 4]
            block_len = get_dword(data, i + 4)
            if i + 8 + block_len <= len(data):
                if block_id == b'RAMP':
                    bank = data[i + 10] % 8
                    ram = data[i + 11:i + 8 + block_len]
                    if data[i + 8] % 2:
                        ram = zlib.decompress(ram)
                    banks[bank] = list(ram)
                else:
                    if block_id == b'SPCR':
                        page = data[i + 9] % 8
                    self.blocks[bytes(block_id)] = data[i + 8:i + 8 + block_len]
            i += 8 + block_len
        self.memory = Memory(banks=banks, page=page)

    def __getitem__(self, index):
        return self.memory.__getitem__(index)

    def __setitem__(self, index, value):
        self.memory.__setitem__(index, value)

    def set_registers_and_state(self, registers, state):
        _add_zxstspecregs(None, state, self.blocks.get(b'SPCR'))
        _add_zxstz80regs(None, registers, state, self.blocks.get(b'Z80R'))
        if any(spec.startswith(('ay[', 'fffd=')) for spec in state):
            _add_zxstayblock(None, state, self.blocks.setdefault(b'AY\x00\x00', bytearray([0] * 18)))
        if any(spec.startswith('issue2=') for spec in state):
            _add_zxstkeyboard(None, state, self.blocks.setdefault(b'KEYB', bytearray([0] * 5)))

    def write(self, szxfile):
        with open(szxfile, 'wb') as f:
            f.write(self.header)
            for block_id, block_data in self.blocks.items():
                f.write(block_id)
                size = len(block_data)
                f.write(bytes((size % 256, (size >> 8) % 256, (size >> 16) % 256, (size >> 24) % 256)))
                f.write(block_data)
            for bank, data in enumerate(self.memory.banks):
                if data:
                    f.write(_get_zxstrampage(bank, data))

# Component API
def can_read(fname):
    """
    Return whether this snapshot reader can read the file `fname`.
    """
    return fname[-4:].lower() in ('.sna', '.z80', '.szx')

# Component API
def get_snapshot(fname, page=None):
    """
    Read a snapshot file and produce a list of byte values. For a 48K snapshot,
    or a 128K snapshot with a page number (0-7) specified, the list contains
    65536 (64K) elements: a blank 16K ROM followed by 48K RAM. For a 128K
    snapshot with `page` equal to -1, the list contains 131072 (128K) elements:
    RAM banks 0-7 (16K each) in order.

    :param fname: The snapshot filename.
    :param page: The page number (0-7) to map to addresses 49152-65535
                 (C000-FFFF), or -1 to return all RAM banks. This is relevant
                 only when reading a 128K snapshot file.
    :return: A list of byte values.
    """
    if not can_read(fname):
        raise SnapshotError("{}: Unknown file type".format(fname))
    data = read_bin_file(fname)
    ext = fname[-4:].lower()
    if ext == '.sna':
        ram = _read_sna(data, page)
    elif ext == '.z80':
        ram = _read_z80(data, page)
    elif ext == '.szx':
        ram = _read_szx(data, page)
    if len(ram) == 49152:
        return [0] * 16384 + list(ram)
    if len(ram) == 131072:
        return list(ram)
    raise SnapshotError(f'RAM size is {len(ram)}')

def make_snapshot(fname, org, start=None, end=65536, page=None):
    snapshot_reader = get_snapshot_reader()
    if snapshot_reader.can_read(fname):
        if start is None:
            start = parse_int(get_value('DefaultDisassemblyStartAddress'), 16384)
        return snapshot_reader.get_snapshot(fname, page), start, end
    if start is None:
        start = 0
    ram = read_bin_file(fname, 65536)
    if org is None:
        org = 65536 - len(ram)
    mem = [0] * 65536
    mem[org:org + len(ram)] = ram
    return mem, max(org, start), min(end, org + len(ram))

def write_snapshot(fname, ram, registers, state):
    snapshot_type = fname[-4:].lower()
    if snapshot_type == '.z80':
        _write_z80v3(fname, ram, registers, state)
    elif snapshot_type == '.szx':
        _write_szx(fname, ram, registers, state)
    else:
        raise SnapshotError(f'{fname}: Unsupported snapshot type')

def set_z80_registers(z80, *specs):
    for spec in specs:
        reg, sep, val = spec.lower().partition('=')
        if sep:
            if reg.startswith('^'):
                size = len(reg) - 1
            else:
                size = len(reg)
            if reg == 'pc' and z80[6:8] != [0, 0]:
                offset = 6
            else:
                offset = Z80_REGISTERS.get(reg, -1)
            if offset >= 0:
                try:
                    value = get_int_param(val, True)
                except ValueError:
                    raise SkoolKitError("Cannot parse register value: {}".format(spec))
                lsb, msb = value % 256, (value & 65535) // 256
                if size == 1:
                    z80[offset] = lsb
                elif size == 2:
                    z80[offset:offset + 2] = [lsb, msb]
                if reg == 'r':
                    if lsb & 128:
                        z80[12] |= 1
                    else:
                        z80[12] &= 254
            else:
                raise SkoolKitError('Invalid register: {}'.format(spec))

def print_reg_help(short_option=None):
    options = ['--reg name=value']
    if short_option:
        options.insert(0, '-{} name=value'.format(short_option))
    reg_names = ', '.join(sorted(Z80_REGISTERS))
    print("""
Usage: {}

Set the value of a register or register pair. For example:

  --reg hl=32768
  --reg b=17

To set the value of an alternate (shadow) register, use the '^' prefix:

  --reg ^hl=10072

Recognised register names are:

  {}
""".format(', '.join(options), '\n  '.join(textwrap.wrap(reg_names, 70))).strip())

def set_z80_state(z80, *specs):
    for spec in specs:
        name, sep, val = spec.lower().partition('=')
        try:
            if name == 'iff':
                z80[27] = z80[28] = get_int_param(val) & 255
            elif name == 'im':
                z80[29] &= 252 # Clear bits 0 and 1
                z80[29] |= get_int_param(val) & 3
            elif name == 'issue2':
                z80[29] &= 251 # Clear bit 2
                z80[29] |= (get_int_param(val) & 1) * 4
            elif name == 'border':
                z80[12] &= 241 # Clear bits 1-3
                z80[12] |= (get_int_param(val) & 7) * 2 # Border colour
            elif name == 'tstates':
                frame_duration = FRAME_DURATIONS[z80[34] > 3]
                qframe_duration = frame_duration // 4
                t = frame_duration - 1 - (get_int_param(val) % frame_duration)
                t1, t2 = t % qframe_duration, t // qframe_duration
                z80[55:58] = (t1 % 256, t1 // 256, (2 - t2) % 4)
            elif name == '7ffd':
                z80[35] = get_int_param(val) & 255
            elif name == 'fffd':
                z80[38] = get_int_param(val) & 255
            elif name.startswith('ay[') and name.endswith(']'):
                r = get_int_param(name[3:-1]) & 15
                z80[39 + r] = get_int_param(val) & 255
        except ValueError:
            raise SkoolKitError("Cannot parse integer: {}".format(spec))

def print_state_help(short_option=None, show_defaults=True):
    options = ['--state name=value']
    if short_option:
        options.insert(0, '-{} name=value'.format(short_option))
    opts = ', '.join(options)
    if show_defaults:
        infix = 'and their default values '
        border = issue2 = ' (default=0)'
        iff = im = ' (default=1)'
        tstates = ' (default=34943)'
    else:
        infix = border = issue2 = iff = im = tstates = ''
    attributes = [
        ('7ffd', 'last OUT to port 0x7ffd (128K only)'),
        ('ay[N]', 'contents of AY register N (N=0-15; 128K only)'),
        ('border', f'border colour{border}'),
        ('fe', 'last OUT to port 0xfe (SZX only)'),
        ('fffd', 'last OUT to port 0xfffd (128K only)'),
        ('iff', f'interrupt flip-flop: 0=disabled, 1=enabled{iff}'),
        ('im', f'interrupt mode{im}'),
        ('issue2', f'issue 2 emulation: 0=disabled, 1=enabled{issue2}'),
        ('tstates', f'T-states elapsed since start of frame{tstates}')
    ]
    attrs = '\n'.join(f'  {a:<7} - {d}' for a, d in sorted(attributes))
    print(f'Usage: {opts}\n\nSet a hardware state attribute. Recognised names {infix}are:\n\n{attrs}')

def make_z80_ram_block(data, page):
    block = []
    prev_b = None
    count = 0
    for b in data:
        if b == prev_b or prev_b is None:
            prev_b = b
            if count < 255:
                count += 1
                continue
        if count > 4 or (count > 1 and prev_b == 237):
            block.extend((237, 237, count, prev_b))
        elif prev_b == 237:
            block.extend((237, b))
            prev_b = None
            count = 0
            continue
        else:
            block.extend((prev_b,) * count)
        prev_b = b
        count = 1
    if count > 4 or (count > 1 and prev_b == 237):
        block.extend((237, 237, count, prev_b))
    else:
        block.extend((prev_b,) * count)
    length = len(block)
    return [length % 256, length // 256, page] + block

def make_z80v3_ram_blocks(ram):
    blocks = []
    if len(ram) == 8:
        for n, bank in enumerate(ram, 3):
            blocks.extend(make_z80_ram_block(bank, n))
    else:
        for bank, data in ((5, ram[:0x4000]), (1, ram[0x4000:0x8000]), (2, ram[0x8000:0xC000])):
            blocks.extend(make_z80_ram_block(data, bank + 3))
    return blocks

def _write_z80v3(fname, ram, registers, state):
    z80 = [0] * 86
    z80[30] = 54 # Indicate a v3 Z80 snapshot
    if len(ram) == 8:
        z80[34] = 4 # 128K
    set_z80_registers(z80, 'i=63', 'iy=23610', *registers)
    set_z80_state(z80, 'iff=1', 'im=1', *state)
    with open(fname, 'wb') as f:
        f.write(bytes(z80 + make_z80v3_ram_blocks(ram)))

def _add_zxstspecregs(szx, state, spcr=None):
    if spcr:
        values = spcr
    else:
        values = [0] * 8
    for spec in state:
        name, sep, val = spec.lower().partition('=')
        try:
            if name == 'border':
                values[0] = get_int_param(val) % 8
            elif name == '7ffd':
                values[1] = get_int_param(val) % 256
            elif name == 'fe':
                values[3] = get_int_param(val) % 256
        except ValueError:
            raise SkoolKitError(f'Cannot parse integer: {spec}')
    if szx:
        szx.extend((83, 80, 67, 82)) # SPCR
        szx.extend((8, 0, 0, 0))     # Block size
        szx.extend(values)

def _add_zxstkeyboard(szx, state, keyb=None):
    if keyb:
        values = keyb
    else:
        values = [0] * 5
    for spec in state:
        name, sep, val = spec.lower().partition('=')
        try:
            if name == 'issue2':
                values[0] = get_int_param(val) % 2
        except ValueError:
            raise SkoolKitError(f'Cannot parse integer: {spec}')
    if szx:
        szx.extend(b'KEYB')
        szx.extend((5, 0, 0, 0)) # Block size
        szx.extend(values)

def _add_zxstayblock(szx, state, ay=None):
    if ay:
        values = ay
    else:
        values = [0] * 18
    for spec in state:
        name, sep, val = spec.lower().partition('=')
        try:
            if name == 'fffd':
                values[1] = get_int_param(val) % 256
            elif name.startswith('ay[') and name.endswith(']'):
                r = get_int_param(name[3:-1]) % 16
                values[2 + r] = get_int_param(val) % 256
        except ValueError:
            raise SkoolKitError(f'Cannot parse integer: {spec}')
    if szx:
        szx.extend(b'AY\x00\x00')
        szx.extend((18, 0, 0, 0)) # Block size
        szx.extend(values)

def _add_zxstz80regs(szx, registers, state, z80r=None):
    if z80r:
        values = z80r
    else:
        values = [0] * 26
        values.extend((
            1,              # IFF1
            1,              # IFF2
            1,              # IM
            127, 136, 0, 0, # dwCyclesStart=34943
            0, 0, 0, 0
        ))

    for spec in registers:
        reg, sep, val = spec.lower().partition('=')
        if sep:
            if reg.startswith('^'):
                size = len(reg) - 1
            else:
                size = len(reg)
            offset = SZX_REGISTERS.get(reg)
            if offset is None:
                raise SkoolKitError(f'Invalid register: {spec}')
            try:
                value = get_int_param(val, True)
            except ValueError:
                raise SkoolKitError(f'Cannot parse register value: {spec}')
            values[offset] = value % 256
            if size == 2:
                values[offset + 1] = (value // 256) % 256

    for spec in state:
        name, sep, val = spec.lower().partition('=')
        try:
            if name == 'iff':
                values[26] = values[27] = get_int_param(val) & 255
            elif name == 'im':
                values[28] = get_int_param(val) & 3
            elif name == 'tstates':
                tstates = get_int_param(val)
                values[29:32] = (tstates % 256, (tstates // 256) % 256, (tstates // 65536) % 256)
        except ValueError:
            raise SkoolKitError(f'Cannot parse integer: {spec}')

    if szx:
        szx.extend(b'Z80R')
        szx.extend((37, 0, 0, 0)) # Block size
        szx.extend(values)

def _get_zxstrampage(page, data):
    ram = zlib.compress(bytes(data), 9)
    size = len(ram) + 3
    ramp = bytearray(b'RAMP')
    ramp.extend((size % 256, size // 256, 0, 0)) # Block size
    ramp.extend((1, 0, page))
    ramp.extend(ram)
    return ramp

def _write_szx(fname, ram, registers, state):
    szx = [90, 88, 83, 84] # ZXST
    szx.extend((1, 4)) # Version 1.4
    if len(ram) == 8:
        szx.append(2) # 128K
    else:
        szx.append(1) # 48K
    szx.append(0) # Flags

    _add_zxstspecregs(szx, state)
    _add_zxstz80regs(szx, registers, state)
    if len(ram) == 8:
        _add_zxstayblock(szx, state)
        rampages = [_get_zxstrampage(n, bank) for n, bank in enumerate(ram)]
    else:
        _add_zxstkeyboard(szx, state)
        rampages = (
            _get_zxstrampage(0, ram[32768:]),
            _get_zxstrampage(2, ram[16384:32768]),
            _get_zxstrampage(5, ram[:16384])
        )
    for bank in rampages:
        szx.extend(bank)

    with open(fname, 'wb') as f:
        f.write(bytes(szx))

def move(snapshot, param_str):
    params = param_str.split(',', 2)
    if len(params) < 3:
        raise SkoolKitError("Not enough arguments in move spec (expected 3): {}".format(param_str))
    try:
        src, length, dest = [get_int_param(p, True) for p in params]
    except ValueError:
        raise SkoolKitError('Invalid integer in move spec: {}'.format(param_str))
    snapshot[dest:dest + length] = snapshot[src:src + length]

def poke(snapshot, param_str):
    try:
        addr, val = param_str.split(',', 1)
    except ValueError:
        raise SkoolKitError("Value missing in poke spec: {}".format(param_str))
    try:
        if val.startswith('^'):
            value = get_int_param(val[1:], True)
            poke_f = lambda b: b ^ value
        elif val.startswith('+'):
            value = get_int_param(val[1:], True)
            poke_f = lambda b: (b + value) & 255
        else:
            value = get_int_param(val, True)
            poke_f = lambda b: value
    except ValueError:
        raise SkoolKitError('Invalid value in poke spec: {}'.format(param_str))
    try:
        values = [get_int_param(i, True) for i in addr.split('-', 2)]
    except ValueError:
        raise SkoolKitError('Invalid address range in poke spec: {}'.format(param_str))
    addr1, addr2, step = values + [values[0], 1][len(values) - 1:]
    for a in range(addr1, addr2 + 1, step):
        snapshot[a] = poke_f(snapshot[a])

def _read_sna(data, page=None):
    if len(data) <= 49179 or page is None:
        return data[27:49179]
    paged_bank = data[49181] & 7
    pages = {5: data[27:16411], 2: data[16411:32795], paged_bank: data[32795:49179]}
    offset = 49183
    for i in range(8):
        if i not in pages:
            pages[i] = data[offset:offset + 16384]
            offset += 16384
    if page >= 0:
        return pages[5] + pages[2] + pages[page]
    return pages[0] + pages[1] + pages[2] + pages[3] + pages[4] + pages[5] + pages[6] + pages[7]

def _read_z80(data, page=None):
    if sum(data[6:8]) > 0:
        version = 1
    else:
        version = 2
    if version == 1:
        header_size = 30
    else:
        header_size = 32 + data[30]
    header = data[:header_size]
    if version == 1:
        if header[12] & 32:
            return _decompress_block(data[header_size:-4])
        return data[header_size:]
    machine_id = data[34]
    extension = ()
    if (version == 2 and machine_id < 2) or (version == 3 and machine_id in (0, 1, 3)):
        if data[37] & 128:
            banks = (5,) # 16K
            extension = [0] * 32768
        else:
            banks = (5, 1, 2) # 48K
    else:
        if page is None:
            banks = (5, 2, data[35] & 7)
        elif page < 0:
            banks = (0, 1, 2, 3, 4, 5, 6, 7)
        else:
            banks = (5, 2, page)
    return _decompress(data[header_size:], banks, extension)

def _read_szx(data, page=None):
    extension = ()
    machine_id = data[6]
    if machine_id == 0:
        banks = (5,) # 16K
        extension = [0] * 32768
    elif machine_id == 1:
        banks = (5, 2, 0) # 48K
    else:
        if page is None:
            specregs = _get_zxstblock(data, 8, 'SPCR')[1]
            if specregs is None:
                raise SnapshotError("SPECREGS (SPCR) block not found")
            banks = (5, 2, specregs[1] & 7)
        elif page < 0:
            banks = (0, 1, 2, 3, 4, 5, 6, 7)
        else:
            banks = (5, 2, page)
    pages = {}
    for bank in banks:
        pages[bank] = None
    i = 8
    while 1:
        i, rampage = _get_zxstblock(data, i, 'RAMP')
        if rampage is None:
            break
        page = rampage[2]
        if page in pages:
            ram = rampage[3:]
            if rampage[0] & 1:
                try:
                    ram = zlib.decompress(ram)
                except zlib.error as e:
                    raise SnapshotError("Error while decompressing page {0}: {1}".format(page, e.args[0]))
            if len(ram) != 16384:
                raise SnapshotError("Page {0} is {1} bytes (should be 16384)".format(page, len(ram)))
            pages[page] = ram
    return _concatenate_pages(pages, banks, extension)

def _get_zxstblock(data, index, block_id):
    block = None
    while index < len(data) and block is None:
        size = data[index + 4] + 256 * data[index + 5] + 65536 * data[index + 6] + 16777216 * data[index + 7]
        dw_id = ''.join([chr(b) for b in data[index:index + 4]])
        if dw_id == block_id:
            block = data[index + 8:index + 8 + size]
        index += 8 + size
    return index, block

def _concatenate_pages(pages, banks, extension):
    ram = []
    for bank in banks:
        if pages[bank] is None:
            raise SnapshotError("Page {0} not found".format(bank))
        ram.extend(pages[bank])
    ram.extend(extension)
    return ram

def _decompress(ramz, banks, extension):
    pages = {}
    for bank in banks:
        pages[bank] = None
    j = 0
    while j < len(ramz):
        length = ramz[j] + 256 * ramz[j + 1]
        page = ramz[j + 2] - 3
        if length == 65535:
            if page in pages:
                pages[page] = ramz[j + 3:j + 16387]
            j += 16387
        else:
            if page in pages:
                pages[page] = _decompress_block(ramz[j + 3:j + 3 + length])
            j += 3 + length
    return _concatenate_pages(pages, banks, extension)

def _decompress_block(ramz):
    block = []
    i = 0
    while i < len(ramz):
        b = ramz[i]
        i += 1
        if b == 237 and i < len(ramz):
            c = ramz[i]
            i += 1
            if c == 237:
                length, byte = ramz[i], ramz[i + 1]
                if length == 0:
                    raise SnapshotError("Found ED ED 00 {0:02X}".format(byte))
                block += [byte] * length
                i += 2
            else:
                block += [b, c]
        else:
            block.append(b)
    return block

# API (SnapshotReader)
class SnapshotError(SkoolKitError):
    """Raised when an error occurs while reading a snapshot file."""
