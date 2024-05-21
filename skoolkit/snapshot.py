# Copyright 2009-2013, 2015-2024 Richard Dymond (rjdymond@gmail.com)
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

from skoolkit import SkoolKitError, get_dword, get_word, get_int_param, parse_int, read_bin_file
from skoolkit.components import get_snapshot_reader, get_value
from skoolkit.simutils import FRAME_DURATIONS

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
            if isinstance(banks, dict):
                self.banks = [banks.get(i) for i in range(max(8, max(banks)))]
            else:
                self.banks = banks
            if page is None:
                # Z80 48K
                self.memory = [[0] * 0x4000, self.banks[5], self.banks[1], self.banks[2]]
            else:
                self.memory = [[0] * 0x4000, self.banks[5], self.banks[2], self.banks[page]]
        elif len(snapshot) == 0x20000:
            self.banks = [snapshot[a:a + 0x4000] for a in range(0, 0x20000, 0x4000)]
            self.memory = [[0] * 0x4000, self.banks[5], self.banks[2], self.banks[page]]
        else:
            self.banks = [None] * 8
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
        if all(self.banks):
            return self.banks
        return self.memory[1] + self.memory[2] + self.memory[3]

    def ram(self, page):
        if not all(self.banks) or page is None:
            if self.memory[2]:
                return self.memory[1] + self.memory[2] + self.memory[3]
            return self.memory[1] + [0] * 32768
        if page >= 0:
            return self.banks[5] + self.banks[2] + self.banks[page]
        return self.banks[0] + self.banks[1] + self.banks[2] + self.banks[3] + self.banks[4] + self.banks[5] + self.banks[6] + self.banks[7]

class Snapshot:
    def __init__(self):
        self.type = None
        self.a = 0
        self.f = 0
        self.bc = 0
        self.de = 0
        self.hl = 0
        self.a2 = 0
        self.f2 = 0
        self.bc2 = 0
        self.de2 = 0
        self.hl2 = 0
        self.ix = 0
        self.iy = 0
        self.sp = 0
        self.i = 0
        self.r = 0
        self.pc = 0
        self.border = 0
        self.iff1 = 0
        self.iff2 = 0
        self.im = 0
        self.tstates = 0
        self.out7ffd = 0
        self.outfffd = 0
        self.ay = (0,) * 16
        self.outfe = 0
        self.machine = None

    @classmethod
    def get(cls, sfile, ext=None):
        if ext is None:
            ext = sfile.rpartition('.')[2]
            data = read_bin_file(sfile)
        else:
            data = sfile
        if ext.lower() == 'sna':
            return SNA(data)
        if ext.lower() == 'szx':
            return SZX(data)
        if ext.lower() == 'z80':
            return Z80(data)

    def ram(self, page=None):
        return self.memory.ram(page)

    def move(self, specs):
        for spec in specs:
            move(self.memory, spec)

    def poke(self, specs):
        for spec in specs:
            poke(self.memory, spec)

class SNA(Snapshot):
    def __init__(self, sna_data):
        super().__init__()
        self.type = 'SNA'
        data = list(sna_data)
        self.header = data[:27]
        self.tail = data[27:]
        if len(self.tail) not in (49152, 131076, 147460):
            raise SnapshotError('Invalid SNA file')
        self.i = self.header[0]
        self.hl2 = get_word(self.header, 1)
        self.de2 = get_word(self.header, 3)
        self.bc2 = get_word(self.header, 5)
        self.f2 = self.header[7]
        self.a2 = self.header[8]
        self.hl = get_word(self.header, 9)
        self.de = get_word(self.header, 11)
        self.bc = get_word(self.header, 13)
        self.iy = get_word(self.header, 15)
        self.ix = get_word(self.header, 17)
        self.r = self.header[20]
        self.f = self.header[21]
        self.a = self.header[22]
        self.sp = get_word(self.header, 23)
        self.border = self.header[26] % 8
        self.iff1 = (self.header[19] & 4) // 4
        self.iff2 = self.iff1
        self.im = self.header[25]
        banks = [None] * 8
        if len(self.tail) == 49152:
            if self.sp >= 16384:
                self.pc = get_word(self.tail, self.sp - 16384)
            page = 0
            self.machine = '48K'
        else:
            self.pc = get_word(self.tail, 49152)
            self.out7ffd = self.tail[49154]
            page = self.out7ffd % 8
            offset = 49156
            for i in sorted(set(range(8)) - {5, 2, page}):
                banks[i] = self.tail[offset:offset + 16384]
                offset += 16384
            self.machine = '128K'
        banks[5] = self.tail[:0x4000]
        banks[2] = self.tail[0x4000:0x8000]
        banks[page] = self.tail[0x8000:0xC000]
        self.memory = Memory(banks=banks, page=page)

class SZX(Snapshot):
    def __init__(self, szx_data=None, ram=None, machine='48K'):
        super().__init__()
        self.type = 'SZX'
        if szx_data:
            self._read(szx_data)
        else:
            self.header = bytearray(b'ZXST\x01\x04\x01\x00')
            self.blocks = {}
            if len(ram) == 8:
                # 128K
                if machine == '+2':
                    self.header[6] = 3 # +2
                else:
                    self.header[6] = 2 # 128K
                self.blocks[b'AY\x00\x00'] = bytearray([0] * 18)
            else:
                # 48K
                self.blocks[b'KEYB'] = bytearray([0] * 5)
            self.set_ram(ram)

    def _read(self, szx_data):
        self.tail = []
        self.blocks = {}
        banks = {}
        data = bytearray(szx_data)
        if len(data) < 8 or data[:4] != b'ZXST':
            raise SnapshotError('Invalid SZX file')
        self.header = data[:8]
        machine_id = self.header[6]
        if machine_id < 2:
            self.machine = '48K'
        elif machine_id == 2:
            self.machine = '128K'
        elif machine_id == 3:
            self.machine = '+2'
        page = 0
        i = 8
        while i + 8 <= len(data):
            block_id = bytes(data[i:i + 4])
            block_len = get_dword(data, i + 4)
            if i + 8 + block_len <= len(data):
                block_id_str = ''.join(chr(b) for b in block_id if b)
                block = data[i + 8:i + 8 + block_len]
                self.tail.append((block_id_str, block))
                if block_id == b'RAMP':
                    bank = data[i + 10] % 8
                    ram = data[i + 11:i + 8 + block_len]
                    if data[i + 8] % 2:
                        try:
                            ram = zlib.decompress(ram)
                        except zlib.error as e:
                            raise SnapshotError(f'Error while decompressing page {bank}: {e.args[0]}')
                    if len(ram) != 16384:
                        raise SnapshotError(f'Page {bank} is {len(ram)} bytes (should be 16384)')
                    banks[bank] = list(ram)
                else:
                    self.blocks[block_id] = block
                    if block_id == b'Z80R':
                        self.f = block[0]
                        self.a = block[1]
                        self.bc = get_word(block, 2)
                        self.de = get_word(block, 4)
                        self.hl = get_word(block, 6)
                        self.f2 = block[8]
                        self.a2 = block[9]
                        self.bc2 = get_word(block, 10)
                        self.de2 = get_word(block, 12)
                        self.hl2 = get_word(block, 14)
                        self.ix = get_word(block, 16)
                        self.iy = get_word(block, 18)
                        self.sp = get_word(block, 20)
                        self.pc = get_word(block, 22)
                        self.i = block[24]
                        self.r = block[25]
                        self.iff1 = block[26]
                        self.iff2 = block[27]
                        self.im = block[28]
                        self.tstates = get_dword(block, 29)
                    elif block_id == b'SPCR':
                        self.border = block[0] % 8
                        self.out7ffd = block[1]
                        self.outfe = block[3]
                    elif block_id == b'AY\x00\x00':
                        self.outfffd = block[1]
                        self.ay = tuple(block[2:18])
            i += 8 + block_len
        if self.header[6] > 1 and b'SPCR' not in self.blocks:
            raise SnapshotError("SPECREGS (SPCR) block not found")
        self.memory = Memory(banks=banks, page=self.out7ffd % 8)

    def _add_zxstspecregs(self, state):
        spcr = self.blocks.setdefault(b'SPCR', bytearray([0] * 8))
        for spec in state:
            name, sep, val = spec.lower().partition('=')
            try:
                if name == 'border':
                    spcr[0] = get_int_param(val) % 8
                elif name == '7ffd':
                    spcr[1] = get_int_param(val) % 256
                elif name == 'fe':
                    spcr[3] = get_int_param(val) % 256
            except ValueError:
                raise SkoolKitError(f'Cannot parse integer: {spec}')

    def _add_zxstz80regs(self, registers, state):
        z80r = self.blocks.setdefault(b'Z80R', bytearray([0] * 37))
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
                z80r[offset] = value % 256
                if size == 2:
                    z80r[offset + 1] = (value // 256) % 256
        for spec in state:
            name, sep, val = spec.lower().partition('=')
            try:
                if name == 'iff':
                    z80r[26] = z80r[27] = get_int_param(val) & 255
                elif name == 'im':
                    z80r[28] = get_int_param(val) & 3
                elif name == 'tstates':
                    tstates = get_int_param(val)
                    z80r[29:32] = (tstates % 256, (tstates // 256) % 256, (tstates // 65536) % 256)
            except ValueError:
                raise SkoolKitError(f'Cannot parse integer: {spec}')

    def _add_zxstayblock(self, state):
        ay = self.blocks.setdefault(b'AY\x00\x00', bytearray([0] * 18))
        for spec in state:
            name, sep, val = spec.lower().partition('=')
            try:
                if name == 'fffd':
                    ay[1] = get_int_param(val) % 256
                elif name.startswith('ay[') and name.endswith(']'):
                    r = get_int_param(name[3:-1]) % 16
                    ay[2 + r] = get_int_param(val) % 256
            except ValueError:
                raise SkoolKitError(f'Cannot parse integer: {spec}')

    def _add_zxstkeyboard(self, state):
        keyb = self.blocks.setdefault(b'KEYB', bytearray([0] * 5))
        for spec in state:
            name, sep, val = spec.lower().partition('=')
            try:
                if name == 'issue2':
                    keyb[0] = get_int_param(val) % 2
            except ValueError:
                raise SkoolKitError(f'Cannot parse integer: {spec}')

    def _get_zxstrampage(self, page, data):
        ram = zlib.compress(bytes(data), 9)
        size = len(ram) + 3
        ramp = bytearray(b'RAMP')
        ramp.extend((size % 256, size // 256, 0, 0)) # Block size
        ramp.extend((1, 0, page))
        ramp.extend(ram)
        return ramp

    def set_ram(self, ram):
        if len(ram) == 8:
            # 128K
            banks = ram
        else:
            # 48K
            banks = [None] * 8
            banks[5] = ram[0x0000:0x4000]
            banks[2] = ram[0x4000:0x8000]
            banks[0] = ram[0x8000:0xC000]
        self.memory = Memory(banks=banks)

    def set_registers_and_state(self, registers, state):
        self._add_zxstspecregs(state)
        self._add_zxstz80regs(registers, state)
        if any(spec.startswith(('ay[', 'fffd=')) for spec in state):
            self._add_zxstayblock(state)
        if any(spec.startswith('issue2=') for spec in state) and self.header[6] < 2:
            self._add_zxstkeyboard(state)

    def data(self):
        szx = bytearray()
        szx.extend(self.header)
        for block_id, block_data in self.blocks.items():
            szx.extend(block_id)
            size = len(block_data)
            szx.extend((size % 256, (size >> 8) % 256, (size >> 16) % 256, (size >> 24) % 256))
            szx.extend(block_data)
        for bank, data in enumerate(self.memory.banks):
            if data:
                szx.extend(self._get_zxstrampage(bank, data))
        return szx

    def write(self, szxfile):
        with open(szxfile, 'wb') as f:
            f.write(self.data())

class Z80(Snapshot):
    def __init__(self, z80_data=None, ram=(0,) * 49152, machine='48K'):
        super().__init__()
        self.type = 'Z80'
        if z80_data:
            self._read(z80_data)
        else:
            self.header = [0] * 86
            self.header[30] = 54 # Version 3
            if len(ram) == 8:
                # 128K
                self.header[34] = 4
                if machine == '+2':
                    self.header[37] |= 0x80 # +2
            self.set_ram(ram)

    def _read(self, z80_data):
        banks = {}
        data = list(z80_data)
        if sum(data[6:8]) > 0:
            # Version 1
            page = 0
            self.header = data[:30]
            self.pc = get_word(self.header, 6)
            if data[12] & 32:
                ram = self._decompress(data[30:-4])
            else:
                ram = data[30:]
            if len(ram) != 49152:
                raise SnapshotError(f'RAM is {len(ram)} bytes (should be 49152)')
            banks[5] = ram[0x0000:0x4000]
            banks[2] = ram[0x4000:0x8000]
            banks[0] = ram[0x8000:0xC000]
            self.machine = '48K'
        else:
            page = None
            i = 32 + data[30]
            self.header = data[:i]
            self.pc = get_word(self.header, 32)
            self.out7ffd = self.header[35]
            self.outfffd = self.header[38]
            self.ay = tuple(self.header[39:55])
            machine_id = (self.header[34], self.header[37] // 128)
            if i > 55:
                # Version 3
                frame_duration = FRAME_DURATIONS[self.header[34] > 3]
                qframe_duration = frame_duration // 4
                t1 = (self.header[55] + 256 * self.header[56]) % qframe_duration
                t2 = (2 - self.header[57]) % 4
                self.tstates = frame_duration - 1 - t2 * qframe_duration - t1
                m48_ids = (0, 1, 3)
                m128_ids = (4, 5, 6, 12)
            else:
                # Version 2
                m48_ids = (0, 1)
                m128_ids = (3, 4, 12)
            if machine_id[0] in m48_ids:
                self.machine = '48K'
            elif machine_id[0] in m128_ids:
                if machine_id[0] == 12 or machine_id[1] == 1:
                    self.machine = '+2'
                else:
                    self.machine = '128K'
            if (i == 55 and machine_id[0] > 2) or (i > 55 and machine_id[0] > 3):
                page = data[35] % 8 # 128K
            while i < len(data):
                length = data[i] + 256 * data[i + 1]
                bank = data[i + 2] - 3
                if length == 65535:
                    length = 16384
                    banks[bank] = data[i + 3:i + 3 + length]
                else:
                    banks[bank] = self._decompress(data[i + 3:i + 3 + length])
                if len(banks[bank]) != 16384:
                    raise SnapshotError(f'Page {bank} is {len(banks[bank])} bytes (should be 16384)')
                i += 3 + length
        self.a = self.header[0]
        self.f = self.header[1]
        self.bc = get_word(self.header, 2)
        self.hl = get_word(self.header, 4)
        self.sp = get_word(self.header, 8)
        self.i = self.header[10]
        self.r = 128 * (self.header[12] % 2) + (self.header[11] % 128)
        self.de = get_word(self.header, 13)
        self.bc2 = get_word(self.header, 15)
        self.de2 = get_word(self.header, 17)
        self.hl2 = get_word(self.header, 19)
        self.a2 = self.header[21]
        self.f2 = self.header[22]
        self.iy = get_word(self.header, 23)
        self.ix = get_word(self.header, 25)
        self.border = (self.header[12] // 2) % 8
        self.iff1 = self.header[27]
        self.iff2 = self.header[28]
        self.im = self.header[29] % 4
        self.tail = data[len(self.header):]
        self.memory = Memory(banks=banks, page=page)

    def _decompress(self, ramz):
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

    def _set_registers(self, specs):
        for spec in specs:
            reg, sep, val = spec.lower().partition('=')
            if sep:
                if reg.startswith('^'):
                    size = len(reg) - 1
                else:
                    size = len(reg)
                if reg == 'pc' and sum(self.header[6:8]) > 0:
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
                        self.header[offset] = lsb
                    elif size == 2:
                        self.header[offset:offset + 2] = [lsb, msb]
                    if reg == 'r':
                        if lsb & 128:
                            self.header[12] |= 1
                        else:
                            self.header[12] &= 254
                else:
                    raise SkoolKitError('Invalid register: {}'.format(spec))

    def _set_state(self, specs):
        for spec in specs:
            name, sep, val = spec.lower().partition('=')
            try:
                if name == 'iff':
                    self.header[27] = self.header[28] = get_int_param(val) & 255
                elif name == 'im':
                    self.header[29] &= 252 # Clear bits 0 and 1
                    self.header[29] |= get_int_param(val) & 3
                elif name == 'issue2':
                    self.header[29] &= 251 # Clear bit 2
                    self.header[29] |= (get_int_param(val) & 1) * 4
                elif name == 'border':
                    self.header[12] &= 241 # Clear bits 1-3
                    self.header[12] |= (get_int_param(val) & 7) * 2 # Border colour
                elif name == 'tstates':
                    if len(self.header) > 58:
                        frame_duration = FRAME_DURATIONS[self.header[34] > 3]
                        qframe_duration = frame_duration // 4
                        t = frame_duration - 1 - (get_int_param(val) % frame_duration)
                        t1, t2 = t % qframe_duration, t // qframe_duration
                        self.header[55:58] = (t1 % 256, t1 // 256, (2 - t2) % 4)
                elif name == '7ffd':
                    if len(self.header) > 35:
                        self.header[35] = get_int_param(val) & 255
                elif name == 'fffd':
                    if len(self.header) > 38:
                        self.header[38] = get_int_param(val) & 255
                elif name.startswith('ay[') and name.endswith(']'):
                    if len(self.header) > 54:
                        r = get_int_param(name[3:-1]) & 15
                        self.header[39 + r] = get_int_param(val) & 255
            except ValueError:
                raise SkoolKitError("Cannot parse integer: {}".format(spec))

    def _make_z80_ram_block(self, data, page=None):
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
        if page is None:
            return bytes(block + [0, 237, 237, 0])
        length = len(block)
        return bytes([length % 256, length // 256, page] + block)

    def set_ram(self, ram):
        if len(ram) == 8:
            # 128K
            banks = ram
        else:
            # 48K
            banks = [None] * 8
            banks[5] = ram[0x0000:0x4000]
            if len(self.header) == 30:
                # Version 1
                banks[2] = ram[0x4000:0x8000]
                banks[0] = ram[0x8000:0xC000]
            else:
                banks[1] = ram[0x4000:0x8000]
                banks[2] = ram[0x8000:0xC000]
        self.memory = Memory(banks=banks)

    def set_registers_and_state(self, registers, state):
        self._set_registers(registers)
        self._set_state(state)

    def data(self):
        z80 = bytearray()
        if len(self.header) == 30:
            # Version 1
            self.header[12] |= 32 # RAM is compressed
            z80.extend(self.header)
            ram = self.memory.banks[5] + self.memory.banks[2] + self.memory.banks[0]
            z80.extend(self._make_z80_ram_block(ram))
        else:
            z80.extend(self.header)
            for bank, data in enumerate(self.memory.banks, 3):
                if data:
                    z80.extend(self._make_z80_ram_block(data, bank))
        return z80

    def write(self, z80file):
        with open(z80file, 'wb') as f:
            f.write(self.data())

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
    ram = Snapshot.get(fname).ram(page)
    if len(ram) == 49152:
        return [0] * 16384 + list(ram)
    return list(ram)

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

def write_snapshot(fname, ram, registers, state, machine='48K'):
    snapshot_type = fname[-4:].lower()
    if snapshot_type == '.z80':
        snapshot = Z80(ram=ram, machine=machine)
        registers = ('i=63', 'iy=23610', *registers)
    elif snapshot_type == '.szx':
        snapshot = SZX(ram=ram, machine=machine)
    else:
        raise SnapshotError(f'{fname}: Unsupported snapshot type')
    snapshot.set_registers_and_state(registers, ('iff=1', 'im=1', 'tstates=34943', *state))
    snapshot.write(fname)

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

def print_state_help(short_option=None, show_defaults=True, omit=()):
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
    all_attrs = (
        ('7ffd', 'last OUT to port 0x7ffd (128K only)'),
        ('ay[N]', 'contents of AY register N (N=0-15; 128K only)'),
        ('border', f'border colour{border}'),
        ('fe', 'last OUT to port 0xfe (SZX only)'),
        ('fffd', 'last OUT to port 0xfffd (128K only)'),
        ('iff', f'interrupt flip-flop: 0=disabled, 1=enabled{iff}'),
        ('im', f'interrupt mode{im}'),
        ('issue2', f'issue 2 emulation: 0=disabled, 1=enabled{issue2}'),
        ('tstates', f'T-states elapsed since start of frame{tstates}')
    )
    attributes = [attr for attr in all_attrs if attr[0] not in omit]
    attrs = '\n'.join(f'  {a:<7} - {d}' for a, d in sorted(attributes))
    print(f'Usage: {opts}\n\nSet a hardware state attribute. Recognised names {infix}are:\n\n{attrs}')

def _get_page(param, desc, spec, default=None):
    if ':' in param:
        page, v = param.split(':', 1)
        try:
            return get_int_param(page), v
        except ValueError:
            raise SkoolKitError(f'Invalid page number in {desc} spec: {spec}')
    return default, param

def move(snapshot, param_str):
    try:
        src, length, dest = param_str.split(',', 2)
    except ValueError:
        raise SkoolKitError(f'Not enough arguments in move spec (expected 3): {param_str}')
    src_page, src = _get_page(src, 'move', param_str)
    dest_page, dest = _get_page(dest, 'move', param_str, src_page)
    try:
        src, length, dest = [get_int_param(p, True) for p in (src, length, dest)]
    except ValueError:
        raise SkoolKitError('Invalid integer in move spec: {}'.format(param_str))
    if src_page is None:
        snapshot[dest:dest + length] = snapshot[src:src + length]
    elif hasattr(snapshot, 'banks'):
        src_bank = snapshot.banks[src_page % 8]
        dest_bank = snapshot.banks[dest_page % 8]
        if src_bank and dest_bank:
            s = src % 0x4000
            d = dest % 0x4000
            dest_bank[d:d + length] = src_bank[s:s + length]

def poke(snapshot, param_str):
    try:
        addr, val = param_str.split(',', 1)
    except ValueError:
        raise SkoolKitError("Value missing in poke spec: {}".format(param_str))
    page, addr = _get_page(addr, 'poke', param_str)
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
    if page is None:
        for a in range(addr1, addr2 + 1, step):
            snapshot[a] = poke_f(snapshot[a])
    elif hasattr(snapshot, 'banks'):
        bank = snapshot.banks[page % 8]
        if bank:
            for a in range(addr1, addr2 + 1, step):
                bank[a % 0x4000] = poke_f(bank[a % 0x4000])

# API (SnapshotReader)
class SnapshotError(SkoolKitError):
    """Raised when an error occurs while reading a snapshot file."""
