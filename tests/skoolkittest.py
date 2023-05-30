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
from skoolkit import (bin2sna, bin2tap, sna2img, skool2asm, skool2bin,
                      skool2ctl, skool2html, sna2ctl, sna2skool, snapinfo,
                      snapmod, tap2sna, tapinfo, trace)

Z80_REGISTERS = {
    'a': 0, 'f': 1, 'bc': 2, 'c': 2, 'b': 3, 'hl': 4, 'l': 4, 'h': 5,
    'sp': 8, 'i': 10, 'r': 11, 'de': 13, 'e': 13, 'd': 14, '^bc': 15,
    '^c': 15, '^b': 16, '^de': 17, '^e': 17, '^d': 18, '^hl': 19,
    '^l': 19, '^h': 20, '^a': 21, '^f': 22, 'iy': 23, 'ix': 25,
    'pc': 32
}

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

    def tearDown(self):
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
            self.tempdirs.append(tempdir)
            return tempdir
        if path and not os.path.isdir(path):
            parent = path
            while 1:
                parent = dirname(parent)
                if parent in self.tempdirs:
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
                t = 69887 - (registers.get('tstates', 0) % 69888)
                t1, t2 = t % 17472, t // 17472
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

    def write_z80(self, ram, version=3, compress=False, machine_id=0, modify=False, out_7ffd=0, pages={}, header=None, registers=None):
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
            z80 = header[:]
            if registers:
                self._set_z80_registers(z80, version, registers)
            for bank in sorted(banks):
                z80 += self._get_z80_ram_block(banks[bank], compress, bank + 3)
        return model, self.write_bin_file(z80, suffix='.z80')

    def write_z80_file(self, header, ram, version=3, compress=False, machine_id=0, pages={}, registers=None):
        return self.write_z80(ram, version, compress, machine_id, pages=pages, header=header, registers=registers)[1]

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

    def write_szx(self, exp_ram, compress=True, machine_id=1, ch7ffd=0, pages={}, registers=None, border=0, keyb=False, issue2=0):
        szx = self._get_szx_header(machine_id, ch7ffd, border=border)
        if keyb:
            szx.extend((75, 69, 89, 66)) # KEYB
            szx.extend((5, 0, 0, 0)) # Size
            szx.extend((issue2, 0, 0, 0)) # dwFlags
            szx.append(0) # chKeyboardJoystick
        if registers:
            szx.extend(self._get_zxstz80regs(registers))
        rampages = {5: self._get_zxstrampage(5, compress, exp_ram[:16384])}
        if machine_id >= 1:
            # 48K and 128K
            rampages[2] = self._get_zxstrampage(2, compress, exp_ram[16384:32768])
            if machine_id == 1:
                # 48K
                rampages[0] = self._get_zxstrampage(0, compress, exp_ram[32768:])
            else:
                # 128K
                rampages[ch7ffd & 7] = self._get_zxstrampage(ch7ffd & 7, compress, exp_ram[32768:])
                for bank, data in pages.items():
                    rampages[bank] = self._get_zxstrampage(bank, compress, data)
                for bank in set(range(8)) - set(rampages):
                    rampages[bank] = self._get_zxstrampage(bank, compress, [0] * 16384)
        for bank in sorted(rampages):
            szx.extend(rampages[bank])
        return self.write_bin_file(szx, suffix='.szx')

    def _run_skoolkit_command(self, cmd, args, catch_exit):
        self.clear_streams()
        if catch_exit is None:
            cmd(args.split())
        else:
            with self.assertRaises(SystemExit) as cm:
                cmd(args.split())
            self.assertEqual(cm.exception.args[0], catch_exit)
        return self.out.getvalue(), self.err.getvalue()

    def run_bin2sna(self, args='', catch_exit=None):
        return self._run_skoolkit_command(bin2sna.main, args, catch_exit)

    def run_bin2tap(self, args='', catch_exit=None):
        return self._run_skoolkit_command(bin2tap.main, args, catch_exit)

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
