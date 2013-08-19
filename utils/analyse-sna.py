#!/usr/bin/env python
import argparse

def get_word(data, index):
    return data[index] + 256 * data[index + 1]

def to_binary(b):
    binstr = ["1" if b & 2 ** (n - 1) else "0" for n in range(8, 0, -1)]
    return ''.join(binstr)

def analyse(sna):
    print('Border: {}'.format(sna[26] & 7))
    width = 11
    flags = "SZ5H3PNC"
    lines = []
    sp = get_word(sna, 23)
    lines.append('PC=(SP)={}'.format(get_word(sna, sp - 16357)))
    lines.append('SP={}'.format(sp))
    lines.append('I={}'.format(sna[0]))
    lines.append('R={}'.format(sna[20]))
    lines.append("{} A'={}".format('A={}'.format(sna[22]).ljust(width), sna[8]))
    lines.append("  {}    {}".format(flags.ljust(width - 2), flags))
    lines.append("{} F'={}".format('F={}'.format(to_binary(sna[21])).ljust(width), to_binary(sna[7])))
    lines.append("{} B'={}".format('B={}'.format(sna[14]).ljust(width), sna[6]))
    lines.append("{} C'={}".format('C={}'.format(sna[13]).ljust(width), sna[5]))
    lines.append("{} D'={}".format('D={}'.format(sna[12]).ljust(width), sna[4]))
    lines.append("{} E'={}".format('E={}'.format(sna[11]).ljust(width), sna[3]))
    lines.append("{} H'={}".format('H={}'.format(sna[10]).ljust(width), sna[2]))
    lines.append("{} L'={}".format('L={}'.format(sna[9]).ljust(width), sna[1]))
    lines.append('IX={}'.format(get_word(sna, 17)))
    lines.append('IY={}'.format(get_word(sna, 15)))
    print('Registers:')
    for line in lines:
        print('  ' + line)

###############################################################################
# Begin
###############################################################################
parser = argparse.ArgumentParser(
    usage="analyse-sna.py FILE.sna",
    description="Analyse an SNA snapshot.",
    add_help=False
)
parser.add_argument('snafile', help=argparse.SUPPRESS, nargs='?')
namespace, unknown_args = parser.parse_known_args()
if unknown_args or namespace.snafile is None:
    parser.exit(2, parser.format_help())

with open(namespace.snafile, 'rb') as f:
    sna = bytearray(f.read(49179))

analyse(sna)
