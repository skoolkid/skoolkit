#!/usr/bin/env python
import sys
import os
import argparse

SKOOLKIT_HOME = os.environ.get('SKOOLKIT_HOME')
if SKOOLKIT_HOME:
    if not os.path.isdir(SKOOLKIT_HOME):
        sys.stderr.write('SKOOLKIT_HOME={}: directory not found\n'.format(SKOOLKIT_HOME))
        sys.exit(1)
    sys.path.insert(0, SKOOLKIT_HOME)
else:
    try:
        import skoolkit
    except ImportError:
        sys.stderr.write('Error: SKOOLKIT_HOME is not set, and SkoolKit is not installed\n')
        sys.exit(1)

from skoolkit.tap2sna import move, poke
from skoolkit.snapshot import get_snapshot, make_z80_ram_block

def get_word(data, index):
    return data[index] + 256 * data[index + 1]

def read_z80(z80file):
    with open(z80file, 'rb') as f:
        data = bytearray(f.read())
    if get_word(data, 6) > 0:
        header = data[:30]
    else:
        header_len = 32 + get_word(data, 30)
        header = data[:header_len]
    return list(header), get_snapshot(z80file)

def write_z80(header, snapshot, fname):
    if len(header) == 30:
        if header[12] & 32:
            ram = make_z80_ram_block(snapshot[16384:], 0)[3:] + [0, 237, 237, 0]
        else:
            ram = snapshot[16384:]
    else:
        ram = []
        for bank, data in ((5, snapshot[16384:32768]), (1, snapshot[32768:49152]), (2, snapshot[49152:])):
            ram += make_z80_ram_block(data, bank + 3)
    with open(fname, 'wb') as f:
        f.write(bytearray(header + ram))

def run(infile, options, outfile):
    header, snapshot = read_z80(infile)
    for spec in options.moves:
        move(snapshot, spec)
    for spec in options.pokes:
        poke(snapshot, spec)
    write_z80(header, snapshot, namespace.outfile)

###############################################################################
# Begin
###############################################################################
parser = argparse.ArgumentParser(
    usage='snapmod.py [options] in.z80 out.z80',
    description="Modify a 48K Z80 snapshot.",
    add_help=False
)
parser.add_argument('infile', help=argparse.SUPPRESS, nargs='?')
parser.add_argument('outfile', help=argparse.SUPPRESS, nargs='?')
group = parser.add_argument_group('Options')
group.add_argument('-m', dest='moves', metavar='src,size,dest', action='append', default=[],
                   help='Move a block of bytes of the given size from src to dest (this option may be used multiple times)')
group.add_argument('-p', dest='pokes', metavar='a[-b[-c]],v', action='append', default=[],
                   help='POKE N,v for N in {a, a+c, a+2c..., b} (this option may be used multiple times)')
namespace, unknown_args = parser.parse_known_args()
if unknown_args or None in (namespace.infile, namespace.outfile):
    parser.exit(2, parser.format_help())
if namespace.infile[-4:].lower() != '.z80':
    sys.stderr.write('Error: unrecognised input snapshot type\n')
    sys.exit(1)

run(namespace.infile, namespace, namespace.outfile)
