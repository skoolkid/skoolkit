#!/usr/bin/env python
import sys
import os
import zipfile
try:
    from urllib2 import urlopen
    from StringIO import StringIO as StreamIO
except ImportError:
    from urllib.request import urlopen
    from io import BytesIO as StreamIO

SKOOLKIT_HOME = os.environ.get('SKOOLKIT_HOME')
if not SKOOLKIT_HOME:
    sys.stderr.write('SKOOLKIT_HOME is not set; aborting\n')
    sys.exit(1)
if not os.path.isdir(SKOOLKIT_HOME):
    sys.stderr.write('SKOOLKIT_HOME={0}: directory not found\n'.format(SKOOLKIT_HOME))
    sys.exit(1)

SNAPSHOTS_DIR = os.path.join(SKOOLKIT_HOME, 'snapshots')
MM_Z80 = os.path.join(SNAPSHOTS_DIR, 'manic_miner.z80')
JSW_Z80 = os.path.join(SNAPSHOTS_DIR, 'jet_set_willy.z80')

class TapError(Exception):
    pass

def get_z80_ram_block(data, page):
    block = []
    prev_b = data[0]
    count = 1
    for b in data[1:] + [-1]:
        if b == prev_b:
            if count < 255:
                count += 1
                continue
        if count > 4 or (prev_b == 237 and count > 1):
            block += [237, 237, count, prev_b]
        else:
            block += [prev_b] * count
        prev_b = b
        count = 1
    length = len(block)
    return [length % 256, length // 256, page] + block

def get_z80(ram, start):
    z80 = [0] * 86
    z80[30] = 54 # Indicate a v3 Z80 snapshot
    z80[32:34] = [start % 256, start // 256]
    banks = {5: ram[:16384]}
    banks[1] = ram[16384:32768]
    banks[2] = ram[32768:49152]
    for bank, data in banks.items():
        z80 += get_z80_ram_block(data, bank + 3)
    return z80

def write_z80(ram, start, fname):
    parent_dir = os.path.dirname(fname)
    if not os.path.isdir(parent_dir):
        os.makedirs(parent_dir)
    sys.stdout.write('Writing {0}\n'.format(fname))
    with open(fname, 'wb') as f:
        f.write(bytearray(get_z80(ram, start)))

def get_ram(tap):
    ram = [0] * 49152
    i = 0
    while i < len(tap):
        block_len = tap[i] + 256 * tap[i + 1]
        if tap[i + 2] == 0:
            # Header
            block_type = tap[i + 3]
            if block_type == 3:
                # Bytes
                start = tap[i + 16] + 256 * tap[i + 17]
            elif block_type == 0:
                # Program
                start = 23755
            else:
                raise TapError('Unknown block type ({0}) in header at {1}'.format(block_type, i))
        else:
            # Data
            data = tap[i + 3:i + 1 + block_len]
            ram[start - 16384:start - 16384 + len(data)] = data
        i += block_len + 2
    return ram

def get_tap(url, member):
    sys.stdout.write('Downloading {0}\n'.format(url))
    u = urlopen(url, timeout=30)
    data = u.read()

    sys.stdout.write('Extracting {0}\n'.format(member))
    z = zipfile.ZipFile(StreamIO(data))
    tap = z.open(member)
    return bytearray(tap.read())

def get_mm(fname):
    url = 'ftp://ftp.worldofspectrum.org/pub/sinclair/games/m/ManicMiner.tap.zip'
    tap = get_tap(url, 'MANIC.TAP')
    ram = get_ram(tap)
    write_z80(ram, 33792, fname)

def get_jsw(fname):
    url = 'ftp://ftp.worldofspectrum.org/pub/sinclair/games/j/JetSetWilly(original).tap.zip'
    tap = get_tap(url, 'JETSET.TAP')
    ram = get_ram(tap)
    write_z80(ram, 33792, fname)

###############################################################################
# Begin
###############################################################################
for snapshot, f in ((MM_Z80, get_mm), (JSW_Z80, get_jsw)):
    if os.path.isfile(snapshot):
        sys.stdout.write('{0}: file already exists\n'.format(snapshot))
    else:
        try:
            f(snapshot)
        except Exception as e:
            sys.stderr.write("Error while getting snapshot {0}: {1}\n".format(os.path.basename(snapshot), e.args[0]))
