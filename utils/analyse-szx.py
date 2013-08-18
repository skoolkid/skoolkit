#!/usr/bin/env python
import sys
import argparse

MACHINES = {
    0: '16K ZX Spectrum',
    1: '48K ZX Spectrum',
    2: 'ZX Spectrum 128',
    3: 'ZX Spectrum +2',
    4: 'ZX Spectrum +2A/+2B',
    5: 'ZX Spectrum +3',
    6: 'ZX Spectrum +3e'
}

def get_block_id(data, index):
    return ''.join([chr(b) for b in data[index:index+ 4]])

def get_dword(data, index):
    return data[index] + 256 * data[index + 1] + 65536 * data[index + 2] + 16777216 * data[index + 3]

def get_word(data, index):
    return data[index] + 256 * data[index + 1]

def to_binary(b):
    binstr = ["1" if b & 2 ** (n - 1) else "0" for n in range(8, 0, -1)]
    return ''.join(binstr)

def print_ramp(block, variables):
    lines = []
    flags = get_word(block, 0)
    compressed = 'compressed' if flags & 1 else 'uncompressed'
    page = block[2]
    ram = block[3:]
    lines.append("Page: {}".format(page))
    machine_id = variables['chMachineId']
    addresses = ''
    if page == 5:
        addresses = '16384-32767'
    elif page == 2:
        addresses = '32768-49151'
    elif machine_id > 1 and page == variables['ch7ffd'] & 7:
        addresses = '49152-65535'
    if addresses:
        addresses += ' - '
    lines.append("RAM: {}{} bytes, {}".format(addresses, len(ram), compressed))
    return lines

def print_spcr(block, variables):
    lines = []
    lines.append('Border: {}'.format(block[0]))
    ch7ffd = block[1]
    variables['ch7ffd'] = ch7ffd
    bank = ch7ffd & 7
    lines.append('Port $7FFD: {} (bank {} paged into 49152-65535)'.format(ch7ffd, bank))
    return lines

def print_z80r(block, variables):
    lines = []
    width = 11
    flags = "SZ5H3PNC"
    lines.append('PC={}'.format(get_word(block, 22)))
    lines.append('SP={}'.format(get_word(block, 20)))
    lines.append('I={}'.format(block[23]))
    lines.append('R={}'.format(block[24]))
    lines.append("{} A'={}".format('A={}'.format(block[9]).ljust(width), block[1]))
    lines.append("  {}    {}".format(flags.ljust(width - 2), flags))
    lines.append("{} F'={}".format('F={}'.format(to_binary(block[8])).ljust(width), to_binary(block[0])))
    lines.append("{} B'={}".format('B={}'.format(block[11]).ljust(width), block[3]))
    lines.append("{} C'={}".format('C={}'.format(block[10]).ljust(width), block[2]))
    lines.append("{} D'={}".format('D={}'.format(block[13]).ljust(width), block[5]))
    lines.append("{} E'={}".format('E={}'.format(block[12]).ljust(width), block[4]))
    lines.append("{} H'={}".format('H={}'.format(block[15]).ljust(width), block[7]))
    lines.append("{} L'={}".format('L={}'.format(block[14]).ljust(width), block[6]))
    lines.append('IX={}'.format(get_word(block, 16)))
    lines.append('IY={}'.format(get_word(block, 18)))
    return lines

BLOCK_PRINTERS = {
    'RAMP': print_ramp,
    'SPCR': print_spcr,
    'Z80R': print_z80r
}

def analyse(szx):
    print('Version: {}.{}'.format(szx[4], szx[5]))
    machine_id = szx[6]
    print('Machine: {}'.format(MACHINES.get(machine_id, 'Unknown')))
    variables = {'chMachineId': machine_id}

    i = 8
    while i < len(szx):
        block_id = get_block_id(szx, i)
        block_size = get_dword(szx, i + 4)
        i += 8
        print('{}: {} bytes'.format(block_id, block_size))
        printer = BLOCK_PRINTERS.get(block_id)
        if printer:
            for line in printer(szx[i:i + block_size], variables):
                print("  " + line)
        i += block_size

###############################################################################
# Begin
###############################################################################
parser = argparse.ArgumentParser(
    usage="analyse-szx.py FILE.szx",
    description="Analyse an SZX snapshot.",
    add_help=False
)
parser.add_argument('szxfile', help=argparse.SUPPRESS, nargs='?')
namespace, unknown_args = parser.parse_known_args()
if unknown_args or namespace.szxfile is None:
    parser.exit(2, parser.format_help())

with open(namespace.szxfile, 'rb') as f:
    szx = bytearray(f.read())

magic = get_block_id(szx, 0)
if magic != 'ZXST':
    sys.stderr.write("{} is not an SZX file\n".format(namespace.szxfile))
    sys.exit(1)

analyse(szx)
