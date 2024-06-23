import sys
from importlib import invalidate_caches
from io import BytesIO, StringIO
import os
from os.path import abspath, dirname
from shutil import rmtree
import glob
import tempfile
from textwrap import dedent
import zlib
from unittest import TestCase

SKOOLKIT_HOME = abspath(dirname(dirname(__file__)))
sys.path.insert(0, SKOOLKIT_HOME)
from skoolkit import (bin2sna, bin2tap, rzxinfo, rzxplay, sna2img, skool2asm,
                      skool2bin, skool2ctl, skool2html, sna2ctl, sna2skool,
                      snapinfo, snapmod, tap2sna, tapinfo, trace)

Z80_REGISTERS = {
    'a': 0, 'f': 1, 'bc': 2, 'c': 2, 'b': 3, 'hl': 4, 'l': 4, 'h': 5,
    'sp': 8, 'i': 10, 'r': 11, 'de': 13, 'e': 13, 'd': 14, '^bc': 15,
    '^c': 15, '^b': 16, '^de': 17, '^e': 17, '^d': 18, '^hl': 19,
    '^l': 19, '^h': 20, '^a': 21, '^f': 22, 'iy': 23, 'ix': 25,
    'pc': 32
}

def as_dword(num):
    return (num % 256, (num >> 8) % 256, (num >> 16) % 256, (num >> 24) % 256)

def as_word(num):
    return (num % 256, (num >> 8) % 256)

def as_words(values):
    data = []
    for v in values:
        data.extend(as_word(v))
    return data

def get_parity(data):
    parity = 0
    for b in data:
        parity ^= b
    return parity

def create_header_block(title='', start=0, length=0, data_type=3):
    header = [0, data_type]
    header.extend([ord(c) for c in title[:10].ljust(10)])
    header.extend((length % 256, length // 256))
    header.extend((start % 256, start // 256))
    if data_type == 0:
        header.extend((length % 256, length // 256))
    else:
        header.extend((0, 0))
    header.append(get_parity(header))
    return header

def create_data_block(data):
    data_block = [255] + data
    data_block.append(get_parity(data_block))
    return data_block

def create_tap_data_block(data):
    data_block = create_data_block(data)
    length = len(data_block)
    return [length % 256, length // 256] + data_block

def create_tap_header_block(title='', start=0, length=0, data_type=3):
    return [19, 0] + create_header_block(title, start, length, data_type)

def create_tzx_data_block(data, pause=0):
    block = [16] # Block ID
    block.extend((pause % 256, pause // 256))
    data_block = create_data_block(data)
    length = len(data_block)
    block.extend((length % 256, length // 256))
    block.extend(data_block)
    return block

def create_tzx_header_block(title='', start=0, length=0, data_type=3, pause=0):
    block = [16] # Block ID
    block.extend((pause % 256, pause // 256))
    data_block = create_header_block(title, start, length, data_type)
    length = len(data_block)
    block.extend((length % 256, length // 256))
    block.extend(data_block)
    return block

def create_tzx_turbo_data_block(data, zero=855, one=1710, used_bits=8):
    block = [
        0x11,                    # Block ID
        120, 8,                  # Length of PILOT pulse (2168)
        155, 2,                  # Length of first SYNC pulse (667)
        223, 2,                  # Length of second SYNC pulse (735)
        zero % 256, zero // 256, # Length of ZERO bit pulse
        one % 256, one // 256,   # Length of ONE bit pulse
        151, 12,                 # Length of PILOT tone (3223)
        used_bits,               # Used bits in the last byte
        0, 0,                    # Pause after this block (0)
    ]
    data_block = create_data_block(data)
    block.extend((len(data_block) % 256, len(data_block) // 256, 0))
    block.extend(data_block)
    return block

def create_tzx_pure_data_block(data, zero=855, one=1710, used_bits=8):
    return [
        0x14,                    # Block ID
        zero % 256, zero // 256, # Length of 0-bit pulse
        one % 256, one // 256,   # Length of 1-bit pulse
        used_bits,               # Used bits in the last byte
        0, 0,                    # Pause after this block (0)
        len(data), 0, 0,         # Data length
        *data,                   # Data
    ]

class Stream:
    def __init__(self, binary=False):
        self._buffer = BytesIO() if binary else StringIO()
        self.buffer = self
        self.name = ''

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return

    def write(self, text):
        self._buffer.write(text)

    def flush(self):
        return

    def getvalue(self):
        return self._buffer.getvalue()

    def tell(self):
        return self._buffer.tell()

    def clear(self):
        self._buffer.seek(0)
        self._buffer.truncate()

    def close(self):
        return

class StdIn:
    def __init__(self, data):
        self.data = data
        self.buffer = self

    def __iter__(self):
        for line in self.data.split('\n'):
            yield line

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return

    def read(self, *args):
        return self.data

    def close(self):
        return

class SZX:
    def __init__(self, szxfile):
        self.blocks = {}
        self.banks = [None] * 8
        with open(szxfile, 'rb') as f:
            data = f.read()
        self.header = data[:8]
        i = 8
        while i + 8 <= len(data):
            block_id = data[i:i + 4]
            block_len = data[i + 4] + 256 * data[i + 5] + 65536 * data[i + 6] + 16777216 * data[i + 7]
            if block_len > 0x8000:
                raise ValueError(f"SZX block length too large: {block_len}")
            if i + 8 + block_len <= len(data):
                if block_id == b'RAMP':
                    bank = data[i + 10] % 8
                    ram = data[i + 11:i + 8 + block_len]
                    if data[i + 8] % 2:
                        ram = zlib.decompress(ram)
                    self.banks[bank] = list(ram)
                else:
                    self.blocks[block_id] = data[i + 8:i + 8 + block_len]
            i += 8 + block_len

    def compare(self, other):
        block_diffs = {}
        for block_id, block in self.blocks.items():
            other_block = other.blocks.get(block_id)
            if block != other_block:
                block_diffs[block_id] = block
        ram_diffs = {}
        for i, (bank, other_bank) in enumerate(zip(self.banks, other.banks)):
            if bank != other_bank:
                ram_diffs[i] = bank
        return block_diffs, ram_diffs

class Z80:
    def __init__(self, z80file):
        with open(z80file, 'rb') as f:
            data = list(f.read())
        if sum(data[6:8]) > 0:
            # Version 1
            self.header = data[:30]
            if data[12] & 32:
                self.ram = self._decompress_block(data[30:-4])
            else:
                self.ram = data[30:]
        else:
            banks = [None] * 8
            i = 32 + data[30]
            self.header = data[:i]
            while i < len(data):
                length = data[i] + 256 * data[i + 1]
                bank = data[i + 2] - 3
                if length == 65535:
                    length = 16384
                    banks[bank] = data[i + 3:i + 3 + length]
                else:
                    banks[bank] = self._decompress_block(data[i + 3:i + 3 + length])
                i += 3 + length
            if (i == 55 and data[34] > 2) or (i > 55 and data[34] > 3):
                self.ram = banks[0] + banks[1] + banks[2] + banks[3] + banks[4] + banks[5] + banks[6] + banks[7]
            else:
                self.ram = banks[5] + banks[1] + banks[2]

    def _decompress_block(self, data):
        block = []
        i = 0
        while i < len(data):
            b = data[i]
            i += 1
            if b == 237 and i < len(data):
                c = data[i]
                i += 1
                if c == 237:
                    length, byte = data[i], data[i + 1]
                    if length == 0:
                        raise ValueError(f'Found ED ED 00 {byte:02X}')
                    block += [byte] * length
                    i += 2
                else:
                    block += [b, c]
            else:
                block.append(b)
        return block

class RZX:
    def __init__(self, major=0, minor=13):
        self.major = major
        self.minor = minor
        self.creator = ()
        self.security = ()
        self.signature = ()
        self.snapshots = []

    def set_creator(self, creator_id='Nobody', major=1, minor=0, custom_data=()):
        b_len = 29 + len(custom_data)
        creator_b = [ord(c) for c in creator_id[:20]]
        creator_b += [0] * (20 - len(creator_b))
        self.creator = [
            0x10,             # Block ID
            *as_dword(b_len), # Block length
            *creator_b,       # Creator ID
            major % 256, major // 256,
            minor % 256, minor // 256,
            *custom_data
        ]

    def set_security(self, key_id=0, week_code=0):
        self.security = [
            0x20,                # Block ID
            13, 0, 0, 0,         # Block length
            *as_dword(key_id),
            *as_dword(week_code)
        ]

    def set_signature(self, r=(), s=()):
        b_len = 5 + len(r) + len(s)
        self.signature = [
            0x21,            # Block ID
            *as_dword(b_len) # Block length
        ]
        self.signature.extend(r)
        self.signature.extend(s)

    def add_snapshot(self, data=None, ext=None, frames=None, flags=0, tstates=0, io_flags=2):
        if data:
            ext_b = [ord(c) for c in ext[:4]]
            ext_b += [0] * (4 - len(ext_b))
            s_len = len(data)
            if flags & 2:
                s_data = zlib.compress(bytes(data), 9)
            else:
                s_data = data
            b_len = 17 + len(s_data)
            s_block = [
                0x30,             # Block ID
                *as_dword(b_len), # Block length
                *as_dword(flags), # Flags
                *ext_b,
                *as_dword(s_len)  # Uncompressed snapshot length
            ]
            s_block.extend(s_data)
        else:
            s_block = ()

        if frames is None:
            frames = [(1, 1, [0])]
        if frames:
            io_frames = []
            for nf, (fc, ic, readings) in enumerate(frames, 1):
                io_frames.extend((fc % 256, fc // 256, ic % 256, ic // 256))
                io_frames.extend(readings)
            if io_flags & 2:
                io_frames = zlib.compress(bytes(io_frames), 9)
            b_len = 18 + len(io_frames)
            io_block = [
                0x80,               # Block ID
                *as_dword(b_len),   # Block length
                *as_dword(nf),      # Number of frames
                0,                  # Reserved
                *as_dword(tstates), # Initial T-states
                *as_dword(io_flags) # Flags
            ]
            io_block.extend(io_frames)
        else:
            io_block = ()

        self.snapshots.append((s_block, io_block))

    def data(self):
        data = [
            82, 90, 88, 33, # RZX!
            self.major,
            self.minor,
            0, 0, 0, 0      # Flags
        ]
        data.extend(self.creator)
        data.extend(self.security)
        data.extend(self.signature)
        for snapshot, input_recording in self.snapshots:
            data.extend(snapshot)
            data.extend(input_recording)
        return data

class PZX:
    def __init__(self, major=1, minor=0, info=(), null=True):
        info_bytes = []
        for key, value in info:
            if key:
                info_bytes.extend(ord(c) for c in key)
                info_bytes.append(0)
            info_bytes.extend(ord(c) for c in value)
            info_bytes.append(0)
        if info_bytes and info_bytes[-1] == 0 and not null:
            info_bytes.pop()
        length = 2 + len(info_bytes)
        self.data = [
            80, 90, 88, 84,    # PZXT
            *as_dword(length), # Block length
            major, minor,      # Version
            *info_bytes        # Tape info
        ]

    def _encode_pulses(self, count, duration):
        if count == 1 and duration < 0x8000:
            return as_word(duration)
        if duration < 0x8000:
            return (*as_word(0x8000 + count), *as_word(duration))
        return (*as_word(0x8000 + count), *as_word(0x8000 + (duration >> 16)), *as_word(duration % 65536))

    def add_puls(self, standard=1, pulses=(), pulse_counts=()):
        pulse_data = []
        if pulses:
            count = 1
            prev_p = pulses[0]
            for p in list(pulses[1:]) + [None]:
                if p == prev_p:
                    count += 1
                else:
                    while count > 0:
                        pulse_data.extend(self._encode_pulses(min(count, 0x7FFF), prev_p))
                        count -= 0x7FFF
                    count = 1
                prev_p = p
        elif pulse_counts:
            for count, duration in pulse_counts:
                pulse_data.extend(self._encode_pulses(count, duration))
        else:
            pulse_data.extend(self._encode_pulses(3223 + 4840 * (standard > 1), 2168))
            pulse_data.extend(self._encode_pulses(1, 667))
            pulse_data.extend(self._encode_pulses(1, 735))
        length = len(pulse_data)
        self.data.extend((
            80, 85, 76, 83,    # PULS
            *as_dword(length), # Block length
            *pulse_data        # Pulses
        ))

    def add_data(self, data, s0=(855, 855), s1=(1710, 1710), tail=945, used_bits=0, polarity=1):
        length = 8 + 2 * (len(s0) + len(s1)) + len(data)
        bits = 8 * len(data)
        if used_bits:
            bits += used_bits - 8
        bits += polarity * 0x80000000
        self.data.extend((
            68, 65, 84, 65,    # DATA
            *as_dword(length), # Block length
            *as_dword(bits),   # Polarity and bit count
            *as_word(tail),    # Tail pulse
            len(s0),           # p0
            len(s1),           # p1
            *as_words(s0),     # s0
            *as_words(s1),     # s1
            *data              # Data
        ))

    def add_paus(self, duration=3500000, polarity=0):
        value = polarity * 0x80000000 + (duration % 0x80000000)
        self.data.extend((
            80, 65, 85, 83,   # PAUS
            *as_dword(4),     # Block length
            *as_dword(value)  # Duration
        ))

    def add_brws(self, text):
        text_bytes = [ord(c) for c in text]
        length = len(text)
        self.data.extend((
            66, 82, 87, 83,    # BRWS
            *as_dword(length), # Block length
            *text_bytes        # Text
        ))

    def add_stop(self, always=True):
        flags = int(not always)
        self.data.extend((
            83, 84, 79, 80, # STOP
            *as_dword(2),   # Block length
            *as_word(flags) # Flags
        ))

    def add_block(self, name, data):
        block = [32, 32, 32, 32, *as_dword(len(data)), *data]
        block[:len(name)] = [ord(c) for c in name[:4]]
        self.data.extend(block)

class SkoolKitTestCase(TestCase):
    stdout_binary = False

    def setUp(self):
        self.longMessage = True
        self.maxDiff = None
        self.stdin = sys.stdin
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        sys.stdout = self.out = Stream(self.stdout_binary)
        sys.stderr = self.err = Stream()
        self.tempfiles = []
        self.tempdirs = []
        self.cwd = os.getcwd()
        os.chdir(self.make_directory())

    def tearDown(self):
        os.chdir(self.cwd)
        self.remove_files()
        sys.stdin = self.stdin
        sys.stdout = self.stdout
        sys.stderr = self.stderr

    def remove_files(self):
        for f in self.tempfiles:
            if os.path.isfile(f):
                os.remove(f)
                if f.endswith('.py'):
                    pyc_pattern = os.path.join(dirname(f), '__pycache__', '{0}*.pyc'.format(f[:-3]))
                    for pyc in [f + 'c'] + glob.glob(pyc_pattern):
                        if os.path.isfile(pyc):
                            os.remove(pyc)
        self.tempfiles = []
        for d in self.tempdirs:
            if os.path.isdir(d):
                rmtree(d, True)
        self.tempdirs = []

    def clear_streams(self):
        self.out.clear()
        self.err.clear()

    def make_directory(self, path=None):
        if path is None:
            tempdir = tempfile.mkdtemp(dir='')
            self.tempdirs.append(os.path.abspath(tempdir))
            return os.path.relpath(tempdir)
        if path and not os.path.isdir(path):
            parent = path
            while 1:
                parent = dirname(parent)
                if os.path.abspath(parent) in self.tempdirs:
                    os.makedirs(path)
                    return
                if parent in ('', os.path.sep):
                    break
            self.fail("Tried to create a directory in a non-temporary directory")

    def _write_file(self, contents, path, suffix, text):
        mode = 'wt' if text else 'wb'
        if path is None:
            fd, path = tempfile.mkstemp(suffix=suffix, dir='', text=text)
            path = os.path.basename(path.replace(os.path.sep, '/'))
            f = os.fdopen(fd, mode)
        else:
            self.make_directory(dirname(path))
            f = open(path, mode)
        self.tempfiles.append(path)
        f.write(contents)
        f.close()
        return path

    def write_text_file(self, contents='', path=None, suffix=''):
        return self._write_file(contents, path, suffix, True)

    def write_bin_file(self, data=(), path=None, suffix=''):
        return self._write_file(bytearray(data), path, suffix, False)

    def write_component_config(self, key, value, contents):
        module_name = self.write_text_file(dedent(contents), suffix='.py')[:-3]
        ini = "[skoolkit]\n{}=:{}".format(key, value.replace('*', module_name))
        self.write_text_file(ini, 'skoolkit.ini')
        invalidate_caches()

    def write_stdin(self, contents):
        sys.stdin = StdIn(contents)

    def write_rzx_file(self, rzx):
        return self.write_bin_file(rzx.data(), suffix='.rzx')

    def _get_z80_ram_block(self, data, compress, page=None):
        if compress:
            block = []
            prev_b = None
            count = 0
            for b in data:
                if b == prev_b or prev_b is None:
                    prev_b = b
                    if count < 255:
                        count += 1
                        continue
                if count > 4 or (prev_b == 237 and count > 1):
                    block += [237, 237, count, prev_b]
                elif prev_b == 237:
                    block += [237, b]
                    prev_b = None
                    count = 0
                    continue
                else:
                    block += [prev_b] * count
                prev_b = b
                count = 1
            if count > 4 or (count > 1 and prev_b == 237):
                block.extend((237, 237, count, prev_b))
            else:
                block.extend((prev_b,) * count)
        else:
            block = data
        if page is not None:
            length = len(block) if compress else 65535
            return [length % 256, length // 256, page] + block
        if compress:
            return block + [0, 237, 237, 0]
        return block

    def _set_z80_registers(self, header, version, registers):
        header[0] = registers.get('A', 0)
        header[1] = registers.get('F', 0)
        header[2] = registers.get('C', 0)
        header[3] = registers.get('B', 0)
        header[4] = registers.get('L', 0)
        header[5] = registers.get('H', 0)
        pc = registers.get('PC', 0)
        if version == 1:
            header[6] = pc % 256
            header[7] = pc // 256
        else:
            header[32] = pc % 256
            header[33] = pc // 256
            if version == 3:
                frame_duration = 69888 if header[34] < 4 else 70908
                qframe_duration = frame_duration // 4
                t = frame_duration - 1 - (registers.get('tstates', 0) % frame_duration)
                t1, t2 = t % qframe_duration, t // qframe_duration
                header[55:58] = (t1 % 256, t1 // 256, (2 - t2) % 4)
        sp = registers.get('SP', 0)
        header[8] = sp % 256
        header[9] = sp // 256
        header[10] = registers.get('I', 0)
        r = registers.get('R', 0)
        header[11] = r % 0x80
        header[12] = (header[12] & 0xFE) | (r // 0x80)
        header[13] = registers.get('E', 0)
        header[14] = registers.get('D', 0)
        header[15] = registers.get('^C', 0)
        header[16] = registers.get('^B', 0)
        header[17] = registers.get('^E', 0)
        header[18] = registers.get('^D', 0)
        header[19] = registers.get('^L', 0)
        header[20] = registers.get('^H', 0)
        header[21] = registers.get('^A', 0)
        header[22] = registers.get('^F', 0)
        header[23] = registers.get('IXl', 0)
        header[24] = registers.get('IXh', 0)
        header[25] = registers.get('IYl', 0)
        header[26] = registers.get('IYh', 0)
        header[27] = registers.get('iff1', 0)
        header[28] = registers.get('iff2', 0)
        header[29] = (header[29] & 0xFC) | registers.get('im', 0)

    def write_z80(self, ram, version=3, compress=False, machine_id=0, modify=False, out_7ffd=0, pages={}, header=None, registers=None, ay=None, ret_data=False):
        model = 1
        if version == 1:
            if header is None:
                header = [0] * 30
                header[6] = 255 # Set PC > 0 to indicate a v1 Z80 snapshot
                if compress:
                    header[12] |= 32 # Signal that the RAM data block is compressed
            if registers:
                self._set_z80_registers(header, version, registers)
            z80 = header + self._get_z80_ram_block(ram, compress)
        else:
            if header is None:
                if version == 2:
                    header = [0] * 55
                    header[30] = 23 # Indicate a v2 Z80 snapshot
                else:
                    header = [0] * 86
                    header[30] = 54 # Indicate a v3 Z80 snapshot
                header[34] = machine_id
                header[35] = out_7ffd
                header[37] = 128 if modify else 0
            else:
                machine_id = header[34]
            banks = {5: ram[:16384]}
            if (version == 2 and machine_id < 2) or (version == 3 and machine_id in (0, 1, 3)):
                # 16K/48K
                model = 0 if modify else 1
                banks[1] = ram[16384:32768]
                banks[2] = ram[32768:49152]
            else:
                # 128K
                model = 2
                banks[2] = ram[16384:32768]
                banks[out_7ffd & 7] = ram[32768:49152]
                banks.update(pages)
                for bank in set(range(8)) - set(banks.keys()):
                    banks[bank] = [0] * 16384
                if ay:
                    header[38:38 + len(ay)] = ay
            z80 = header[:]
            if registers:
                self._set_z80_registers(z80, version, registers)
            for bank in sorted(banks):
                z80 += self._get_z80_ram_block(banks[bank], compress, bank + 3)
        if ret_data:
            return model, z80
        return model, self.write_bin_file(z80, suffix='.z80')

    def write_z80_file(self, header, ram, version=3, compress=False, machine_id=0, modify=False, out7ffd=0, pages={}, registers=None, ay=None, ret_data=False):
        return self.write_z80(ram, version, compress, machine_id, modify, out7ffd, pages, header, registers, ay, ret_data)[1]

    def _get_szx_header(self, machine_id=1, ch7ffd=0, specregs=True, border=0):
        header = [90, 88, 83, 84] # ZXST
        header.extend((1, 4)) # Version 1.4
        header.append(machine_id) # 0=16K, 1=48K, 2+=128K
        header.append(0) # Flags
        if specregs:
            header.extend((83, 80, 67, 82)) # SPCR
            header.extend((8, 0, 0, 0)) # Size
            header.append(border) # BORDER
            header.append(ch7ffd) # Last OUT to port $7FFD
            header.extend((0, 0, 0, 0, 0, 0))
        return header

    def _get_zxstz80regs(self, registers):
        z80r = [90, 56, 48, 82] # Z80R
        z80r.extend((37, 0, 0, 0)) # Size
        z80r.extend(registers)
        z80r.extend([0] * (37 - len(registers)))
        return z80r

    def _get_zxstrampage(self, page, compress, data):
        if compress:
            ram = zlib.compress(bytearray(data), 9)
        else:
            ram = data
        ramp = [82, 65, 77, 80] # RAMP
        size = len(ram) + 3
        ramp.extend((size % 256, size // 256, 0, 0))
        ramp.extend((1 if compress else 0, 0))
        ramp.append(page)
        ramp.extend(ram)
        return ramp

    def write_szx(self, ram, compress=True, machine_id=1, ch7ffd=0, pages={}, registers=(), border=0, keyb=False, issue2=0, ay=None, blocks=(), ret_data=False):
        szx = self._get_szx_header(machine_id, ch7ffd, border=border)
        if keyb:
            szx.extend((75, 69, 89, 66)) # KEYB
            szx.extend((5, 0, 0, 0)) # Size
            szx.extend((issue2, 0, 0, 0)) # dwFlags
            szx.append(0) # chKeyboardJoystick
        if ay:
            szx.extend((65, 89, 0, 0))       # AY
            szx.extend((18, 0, 0, 0))        # Size
            szx.append(0)                    # chFlags
            szx.append(ay[0])                # chCurrentRegister
            szx.extend(ay[1:])               # chAyRegs
            szx.extend([0] * (17 - len(ay))) # Remaining chAyRegs
        if registers:
            szx.extend(self._get_zxstz80regs(registers))
        rampages = {5: self._get_zxstrampage(5, compress, ram[:16384])}
        if machine_id >= 1:
            # 48K and 128K
            rampages[2] = self._get_zxstrampage(2, compress, ram[16384:32768])
            if machine_id == 1:
                # 48K
                rampages[0] = self._get_zxstrampage(0, compress, ram[32768:])
            else:
                # 128K
                rampages[ch7ffd & 7] = self._get_zxstrampage(ch7ffd & 7, compress, ram[32768:])
                for bank, data in pages.items():
                    rampages[bank] = self._get_zxstrampage(bank, compress, data)
                for bank in set(range(8)) - set(rampages):
                    rampages[bank] = self._get_zxstrampage(bank, compress, [0] * 16384)
        for block in blocks:
            szx.extend(block)
        for bank in sorted(rampages):
            szx.extend(rampages[bank])
        if ret_data:
            return szx
        return self.write_bin_file(szx, suffix='.szx')

    def _run_skoolkit_command(self, cmd, args, catch_exit):
        self.clear_streams()
        if isinstance(args, str):
            args = args.split()
        if catch_exit is None:
            cmd(args)
        else:
            with self.assertRaises(SystemExit) as cm:
                cmd(args)
            self.assertEqual(cm.exception.args[0], catch_exit)
        return self.out.getvalue(), self.err.getvalue()

    def run_bin2sna(self, args='', catch_exit=None):
        return self._run_skoolkit_command(bin2sna.main, args, catch_exit)

    def run_bin2tap(self, args='', catch_exit=None):
        return self._run_skoolkit_command(bin2tap.main, args, catch_exit)

    def run_rzxinfo(self, args='', catch_exit=None):
        return self._run_skoolkit_command(rzxinfo.main, args, catch_exit)

    def run_rzxplay(self, args='', catch_exit=None):
        return self._run_skoolkit_command(rzxplay.main, args, catch_exit)

    def run_sna2img(self, args='', catch_exit=None):
        return self._run_skoolkit_command(sna2img.main, args, catch_exit)

    def run_skool2asm(self, args='', catch_exit=None):
        return self._run_skoolkit_command(skool2asm.main, args, catch_exit)

    def run_skool2bin(self, args='', catch_exit=None):
        return self._run_skoolkit_command(skool2bin.main, args, catch_exit)

    def run_skool2ctl(self, args='', catch_exit=None):
        return self._run_skoolkit_command(skool2ctl.main, args, catch_exit)

    def run_skool2html(self, args='', catch_exit=None):
        return self._run_skoolkit_command(skool2html.main, args, catch_exit)

    def run_sna2ctl(self, args='', catch_exit=None):
        return self._run_skoolkit_command(sna2ctl.main, args, catch_exit)

    def run_sna2skool(self, args='', catch_exit=None):
        return self._run_skoolkit_command(sna2skool.main, args, catch_exit)

    def run_snapinfo(self, args='', catch_exit=None):
        return self._run_skoolkit_command(snapinfo.main, args, catch_exit)

    def run_snapmod(self, args='', catch_exit=None):
        return self._run_skoolkit_command(snapmod.main, args, catch_exit)

    def run_tap2sna(self, args='', catch_exit=None):
        return self._run_skoolkit_command(tap2sna.main, args, catch_exit)

    def run_tapinfo(self, args='', catch_exit=None):
        return self._run_skoolkit_command(tapinfo.main, args, catch_exit)

    def run_trace(self, args='', catch_exit=None):
        return self._run_skoolkit_command(trace.main, args, catch_exit)
