#!/usr/bin/env python
import sys
import os
import argparse

# Use the current development version of SkoolKit
SKOOLKIT_HOME = os.environ.get('SKOOLKIT_HOME')
if not SKOOLKIT_HOME:
    sys.stderr.write('SKOOLKIT_HOME is not set; aborting\n')
    sys.exit(1)
if not os.path.isdir(SKOOLKIT_HOME):
    sys.stderr.write('SKOOLKIT_HOME={0}; directory not found\n'.format(SKOOLKIT_HOME))
    sys.exit(1)
sys.path.insert(0, SKOOLKIT_HOME)

from skoolkit.snapshot import get_snapshot

# http://www.worldofspectrum.org/faq/reference/z80format.htm
# http://www.worldofspectrum.org/faq/reference/128kreference.htm

BLOCK_ADDRESSES_48K = {
    4: '32768-49151',
    5: '49152-65535',
    8: '16384-32767'
}

BLOCK_ADDRESSES_128K = {
    5: '32768-49151',
    8: '16384-32767'
}

V2_MACHINES = {
    0: ('48K Spectrum', '16K Spectrum', True),
    1: ('48K Spectrum + IF1', '16K Spectrum + IF1', True),
    2: ('SamRam', 'SamRam', False),
    3: ('128K Spectrum', 'Spectrum +2', False),
    4: ('128K Spectrum + IF1', 'Spectrum +2 + IF1', False)
}

V3_MACHINES = {
    0: ('48K Spectrum', '16K Spectrum', True),
    1: ('48K Spectrum + IF1', '16K Spectrum + IF1', True),
    2: ('SamRam', 'SamRam', False),
    3: ('48K Spectrum + MGT', '16K Spectrum + MGT', True),
    4: ('128K Spectrum', 'Spectrum +2', False),
    5: ('128K Spectrum + IF1', 'Spectrum +2 + IF1', False),
    6: ('128K Spectrum + MGT' 'Spectrum +2 + MGT', False),
}

MACHINES = {
    7: ('Spectrum +3', 'Spectrum +2A', False),
    8: ('Spectrum +3', 'Spectrum +2A', False),
    9: ('Pentagon (128K)', 'Pentagon (128K)', False),
    10: ('Scorpion (256K)', 'Scorpion (256K)', False),
    11: ('Didaktik+Kompakt', 'Didaktik+Kompakt', False),
    12: ('Spectrum +2', 'Spectrum +2', False),
    13: ('Spectrum +2A', 'Spectrum +2A', False),
    14: ('TC2048', 'TC2048', False),
    15: ('TC2068', 'TC2068', False),
    128: ('TS2068', 'TS2068', False),
}

def get_word(data, index):
    return data[index] + 256 * data[index + 1]

def to_binary(b):
    binstr = ["1" if b & 2 ** (n - 1) else "0" for n in range(8, 0, -1)]
    return ''.join(binstr)

def analyse(z80file):
    # Read the Z80 file
    with open(z80file, 'rb') as f:
        data = bytearray(f.read())

    # Extract header and RAM block(s)
    if get_word(data, 6) > 0:
        version = 1
        header = data[:30]
        ram_blocks = data[30:]
    else:
        header_len = 32 + get_word(data, 30)
        header = data[:header_len]
        ram_blocks = data[header_len:]
        version = 2 if header_len == 55 else 3

    # Print file name, version, machine, interrupt status, border, port $7FFD
    print('Z80 file: {0}'.format(z80file))
    print('Version: {0}'.format(version))
    bank = None
    if version == 1:
        machine = '48K Spectrum'
        block_dict = BLOCK_ADDRESSES_48K
    else:
        machine_dict = V2_MACHINES if version == 2 else V3_MACHINES
        machine_id = header[34]
        index = header[37] // 128
        machine_spec = machine_dict.get(machine_id, MACHINES.get(machine_id, ('Unknown', 'Unknown')))
        machine = machine_spec[index]
        if machine_spec[2]:
            block_dict = BLOCK_ADDRESSES_48K
        else:
            block_dict = BLOCK_ADDRESSES_128K
            bank = header[35] & 7
    print('Machine: {0}'.format(machine))
    print('Interrupts: {0}abled'.format('en' if header[27] else 'dis'))
    print('Border: {0}'.format((header[12] // 2) & 7))
    if bank is not None:
        print('Port $7FFD: {0} - bank {1} (block {2}) paged into 49152-65535'.format(header[35], bank, bank + 3))

    # Print register contents
    width = 11
    flags = "SZ5H3PNC"
    print('Registers:')
    if version == 1:
        print('  PC={0}'.format(get_word(header, 6)))
    else:
        print('  PC={0}'.format(get_word(header, 32)))
    print('  SP={0}'.format(get_word(header, 8)))
    print('  I={0}'.format(header[10]))
    print('  R={0}'.format(header[11]))
    print("  {0} A'={1}".format('A={0}'.format(header[0]).ljust(width), header[21]))
    print("    {0}    {1}".format(flags.ljust(width - 2), flags))
    print("  {0} F'={1}".format('F={0}'.format(to_binary(header[1])).ljust(width), to_binary(header[22])))
    print("  {0} B'={1}".format('B={0}'.format(header[3]).ljust(width), header[16]))
    print("  {0} C'={1}".format('C={0}'.format(header[2]).ljust(width), header[15]))
    print("  {0} D'={1}".format('D={0}'.format(header[14]).ljust(width), header[18]))
    print("  {0} E'={1}".format('E={0}'.format(header[13]).ljust(width), header[17]))
    print("  {0} H'={1}".format('H={0}'.format(header[5]).ljust(width), header[20]))
    print("  {0} L'={1}".format('L={0}'.format(header[4]).ljust(width), header[19]))
    print('  IX={0}'.format(get_word(header, 25)))
    print('  IY={0}'.format(get_word(header, 23)))

    # Print RAM block info
    if version == 1:
        block_len = len(ram_blocks)
        prefix = '' if header[12] & 32 else 'un'
        print('48K RAM block (16384-65535): {0} bytes ({1}compressed)'.format(block_len, prefix))
    else:
        i = 0
        while i < len(ram_blocks):
            block_len = get_word(ram_blocks, i)
            page_num = ram_blocks[i + 2]
            addr_range = block_dict.get(page_num)
            if addr_range is None:
                if page_num == bank + 3:
                    addr_range = '49152-65535'
            if addr_range:
                addr_range = ' ({0})'.format(addr_range)
            else:
                addr_range = ''
            i += 3
            if block_len == 65535:
                block_len = 16384
                prefix = 'un'
            else:
                prefix = ''
            print('RAM block {0}{1}: {2} bytes ({3}compressed)'.format(page_num, addr_range, block_len, prefix))
            i += block_len

###############################################################################
# Begin
###############################################################################
parser = argparse.ArgumentParser(
    usage='analyse-z80.py [options] file.z80',
    description="Analyse a Z80 snapshot.",
    add_help=False
)
parser.add_argument('z80file', help=argparse.SUPPRESS, nargs='?')
group = parser.add_argument_group('Options')
group.add_argument('--peek', metavar='ADDR', type=int,
                   help='Show the contents of an address')
namespace, unknown_args = parser.parse_known_args()
if unknown_args or namespace.z80file is None:
    parser.exit(2, parser.format_help())
z80file = namespace.z80file

if namespace.peek is not None:
    address = namespace.peek & 65535
    snapshot = get_snapshot(z80file)
    print('{}: {}'.format(address, snapshot[address]))
else:
    analyse(z80file)
