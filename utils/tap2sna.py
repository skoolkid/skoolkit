#!/usr/bin/env python
import sys
import os
import argparse
import zipfile
from io import BytesIO
try:
    from urllib2 import urlopen
except ImportError:
    from urllib.request import urlopen

SKOOLKIT_HOME = os.environ.get('SKOOLKIT_HOME')
if not SKOOLKIT_HOME:
    sys.stderr.write('SKOOLKIT_HOME is not set; aborting\n')
    sys.exit(1)
if not os.path.isdir(SKOOLKIT_HOME):
    sys.stderr.write('SKOOLKIT_HOME={0}: directory not found\n'.format(SKOOLKIT_HOME))
    sys.exit(1)

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
    if parent_dir and not os.path.isdir(parent_dir):
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

def get_tap(url, member=None):
    sys.stdout.write('Downloading {0}\n'.format(url))
    u = urlopen(url, timeout=30)
    data = u.read()

    z = zipfile.ZipFile(BytesIO(data))
    if member is None:
        for name in z.namelist():
            if name.lower().endswith('.tap'):
                member = name
                break
        else:
            raise TapError('No TAP file found')
    sys.stdout.write('Extracting {0}\n'.format(member))
    tap = z.open(member)
    return bytearray(tap.read())

def main(args):
    parser = argparse.ArgumentParser(
        usage='tap2sna.py [options] ZIPURL FILE.z80',
        description="Convert a TAP file into a Z80 snapshot. ZIPURL should be "
                    "the full URL to a zip archive that contains the TAP file.",
        add_help=False
    )
    parser.add_argument('args', help=argparse.SUPPRESS, nargs='*')
    group = parser.add_argument_group('Options')
    group.add_argument('-f', '--force', action='store_true',
                       help="Overwrite an existing snapshot")
    group.add_argument('-s', '--start', dest='start', type=int, default=0,
                       help="Specify the start address")
    namespace, unknown_args = parser.parse_known_args(args)
    if unknown_args or len(namespace.args) != 2:
        parser.exit(2, parser.format_help())
    url, z80 = namespace.args
    if namespace.force or not os.path.isfile(z80):
        try:
            tap = get_tap(url)
            ram = get_ram(tap)
            write_z80(ram, namespace.start, z80)
        except Exception as e:
            sys.stderr.write("Error while getting snapshot {0}: {1}\n".format(os.path.basename(z80), e.args[0]))
            sys.exit(1)
    else:
        sys.stdout.write('{0}: file already exists; use -f to overwrite\n'.format(z80))
        sys.exit(0)

if __name__ == '__main__':
    main(sys.argv[1:])
