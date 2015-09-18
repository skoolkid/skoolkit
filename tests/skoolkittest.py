# -*- coding: utf-8 -*-
import sys
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
import os
from os.path import abspath, dirname
from shutil import rmtree
import glob
import tempfile
import zlib
from unittest import TestCase

SKOOLKIT_HOME = abspath(dirname(dirname(__file__)))
sys.path.insert(0, SKOOLKIT_HOME)
from skoolkit import bin2tap, skool2asm, skool2bin, skool2ctl, skool2html, skool2sft, sna2skool, tap2sna, tapinfo

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
    header.extend((0, 0))
    header.append(get_parity(header))
    return header

def create_data_block(data):
    parity = 0
    for b in data:
        parity ^= b
    return [255] + data + [get_parity(data)]

def create_tap_data_block(data):
    data_block = create_data_block(data)
    length = len(data_block)
    return [length % 256, length // 256] + data_block

def create_tap_header_block(title='', start=0, length=0, data_type=3):
    return [19, 0] + create_header_block(title, start, length, data_type)

def create_tzx_data_block(data):
    block = [16] # Block ID
    block.extend((0, 0)) # Pause duration
    data_block = create_data_block(data)
    length = len(data_block)
    block.extend((length % 256, length // 256))
    block.extend(data_block)
    return block

def create_tzx_header_block(title='', start=0, data_type=3):
    block = [16] # Block ID
    block.extend((0, 0)) # Pause duration
    data_block = create_header_block(title, start, data_type=data_type)
    length = len(data_block)
    block.extend((length % 256, length // 256))
    block.extend(data_block)
    return block

class Stream:
    def __init__(self):
        self.buffer = StringIO()

    def write(self, text):
        self.buffer.write(text)

    def writelines(self, lines):
        self.buffer.writelines(lines)

    def flush(self):
        return

    def getvalue(self):
        return self.buffer.getvalue()

    def clear(self):
        self.buffer.seek(0)
        self.buffer.truncate()

class SkoolKitTestCase(TestCase):
    def setUp(self):
        self.maxDiff = None
        self.stdin = sys.stdin
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        sys.stdout = self.out = Stream()
        sys.stderr = self.err = Stream()
        self.tempfiles = []
        self.tempdirs = []

    def tearDown(self):
        self.remove_files()
        sys.stdin.close()
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

    def write_stdin(self, contents):
        sys.stdin = open(self.write_text_file(contents), 'r')

    def _get_z80_ram_block(self, data, compress, page=None):
        if compress:
            block = []
            prev_b = None
            count = 0
            for b in data + [-1]:
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
        else:
            block = data
        if page is not None:
            length = len(block) if compress else 65535
            return [length % 256, length // 256, page] + block
        if compress:
            return block + [0, 237, 237, 0]
        return block

    def write_z80(self, ram, version=3, compress=False, machine_id=0, modify=False, out_7ffd=0, pages={}):
        model = 1
        if version == 1:
            header = [0] * 30
            header[6] = 255 # Set PC > 0 to indicate a v1 Z80 snapshot
            if compress:
                header[12] |= 32 # Signal that the RAM data block is compressed
            z80 = header + self._get_z80_ram_block(ram, compress)
        else:
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
            z80 = header
            for bank, data in banks.items():
                z80 += self._get_z80_ram_block(data, compress, bank + 3)
        return model, self.write_bin_file(z80, suffix='.z80')

    def _get_szx_header(self, machine_id=1, ch7ffd=0, specregs=True):
        header = [90, 88, 83, 84] # ZXST
        header.extend((1, 4)) # Version 1.4
        header.append(machine_id) # 0=16K, 1=48K, 2+=128K
        header.append(0) # Flags
        if specregs:
            header.extend((83, 80, 67, 82)) # SPCR
            header.extend((8, 0, 0, 0)) # Size
            header.append(0) # Border
            header.append(ch7ffd) # Last OUT to port $7FFD
            header.extend((0, 0, 0, 0, 0, 0))
        return header

    def _get_zxstrampage(self, page, compress, data):
        if compress:
            # PY: No need to convert to bytes and bytearray in Python 3
            ram = bytearray(zlib.compress(bytes(bytearray(data)), 9))
        else:
            ram = data
        ramp = [82, 65, 77, 80] # RAMP
        size = len(ram) + 3
        ramp.extend((size % 256, size // 256, 0, 0))
        ramp.extend((1 if compress else 0, 0))
        ramp.append(page)
        ramp.extend(ram)
        return ramp

    def write_szx(self, exp_ram, compress=True, machine_id=1, ch7ffd=0, pages={}):
        szx = self._get_szx_header(machine_id, ch7ffd)
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
        for rampage in rampages.values():
            szx.extend(rampage)
        return self.write_bin_file(szx, suffix='.szx')

    def to_lines(self, text, strip_cr):
        # Use rstrip() to remove '\r' characters (useful on Windows)
        if strip_cr:
            lines = [line.rstrip() for line in text.split('\n')]
        else:
            lines = text.split('\n')
        if lines[-1] == '':
            lines.pop()
        return lines

    def _run_skoolkit_command(self, cmd, args, out_lines, err_lines, strip_cr, catch_exit):
        self.clear_streams()
        if catch_exit is None:
            cmd(args.split())
        else:
            with self.assertRaises(SystemExit) as cm:
                cmd(args.split())
            self.assertEqual(cm.exception.args[0], catch_exit)
        out = self.to_lines(self.out.getvalue(), strip_cr) if out_lines else self.out.getvalue()
        err = self.to_lines(self.err.getvalue(), strip_cr) if err_lines else self.err.getvalue()
        return out, err

    def run_bin2tap(self, args='', out_lines=True, err_lines=False, strip_cr=True, catch_exit=None):
        return self._run_skoolkit_command(bin2tap.main, args, out_lines, err_lines, strip_cr, catch_exit)

    def run_skool2asm(self, args='', out_lines=True, err_lines=False, strip_cr=True, catch_exit=None):
        return self._run_skoolkit_command(skool2asm.main, args, out_lines, err_lines, strip_cr, catch_exit)

    def run_skool2bin(self, args='', out_lines=True, err_lines=False, strip_cr=True, catch_exit=None):
        return self._run_skoolkit_command(skool2bin.main, args, out_lines, err_lines, strip_cr, catch_exit)

    def run_skool2ctl(self, args='', out_lines=True, err_lines=False, strip_cr=True, catch_exit=None):
        return self._run_skoolkit_command(skool2ctl.main, args, out_lines, err_lines, strip_cr, catch_exit)

    def run_skool2html(self, args='', out_lines=True, err_lines=False, strip_cr=True, catch_exit=None):
        return self._run_skoolkit_command(skool2html.main, args, out_lines, err_lines, strip_cr, catch_exit)

    def run_skool2sft(self, args='', out_lines=True, err_lines=False, strip_cr=True, catch_exit=None):
        return self._run_skoolkit_command(skool2sft.main, args, out_lines, err_lines, strip_cr, catch_exit)

    def run_sna2skool(self, args='', out_lines=True, err_lines=False, strip_cr=True, catch_exit=None):
        return self._run_skoolkit_command(sna2skool.main, args, out_lines, err_lines, strip_cr, catch_exit)

    def run_tap2sna(self, args='', out_lines=True, err_lines=False, strip_cr=True, catch_exit=None):
        return self._run_skoolkit_command(tap2sna.main, args, out_lines, err_lines, strip_cr, catch_exit)

    def run_tapinfo(self, args='', out_lines=True, err_lines=False, strip_cr=True, catch_exit=None):
        return self._run_skoolkit_command(tapinfo.main, args, out_lines, err_lines, strip_cr, catch_exit)
