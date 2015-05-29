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

from skoolkit import SkoolKitError, SkoolParsingError, open_file, info, warn, error, get_int_param
from skoolkit.skoolparser import parse_asm_block_directive, find_comment
from skoolkit.skoolsft import VALID_CTLS, VERBATIM_BLOCKS
from skoolkit.z80 import assemble

class BinWriter:
    def __init__(self, skoolfile):
        self.snapshot = [0] * 65536
        self.base_address = len(self.snapshot)
        self.end_address = 0
        self.stack = []
        self.verbatim = False
        self._parse_skool(skoolfile)

    def _parse_skool(self, skoolfile):
        entry_ctl = None
        f = open_file(skoolfile)
        for line in f:
            if line.startswith(';'):
                comment = line[1:].strip()
                if comment.startswith('@'):
                    self._parse_asm_directive(comment[1:])
                continue
            if line.startswith('@'):
                self._parse_asm_directive(line[1:].rstrip())
                continue
            if self.verbatim:
                # This line is inside a '+' block
                continue
            s_line = line.strip()
            if not s_line:
                # This line is blank
                entry_ctl = None
                continue
            # Check whether we're in a verbatim block
            if entry_ctl is None and line.startswith(VERBATIM_BLOCKS):
                entry_ctl = line[0]
            if entry_ctl in VERBATIM_BLOCKS:
                continue
            if s_line.startswith(';'):
                # This line is a continuation of an instruction comment
                continue
            if line[0] in VALID_CTLS:
                # This line contains an instruction
                self._parse_instruction(line)
        f.close()

    def _parse_instruction(self, line):
        try:
            address = get_int_param(line[1:6])
        except ValueError:
            raise SkoolParsingError("Invalid address ({}):\n{}".format(line[1:6], line.rstrip()))
        comment_index = find_comment(line)
        if comment_index > 0:
            end = comment_index
        else:
            end = len(line)
        operation = line[7:end].strip()
        data = assemble(operation, address)
        if data:
            end_address = address + len(data)
            self.snapshot[address:end_address] = data
            self.base_address = min(self.base_address, address)
            self.end_address = max(self.end_address, end_address)
        else:
            warn("Failed to assemble:\n {} {}".format(address, operation))

    def _parse_asm_directive(self, directive):
        if parse_asm_block_directive(directive, self.stack):
            self.verbatim = False
            for p, i in self.stack:
                if i != '-':
                    self.verbatim = True
                    break

    def write(self, binfile, origin, end):
        if origin is None:
            base_address = self.base_address
        else:
            base_address = origin
        if end is None:
            end_address = self.end_address
        else:
            end_address = end
        data = self.snapshot[base_address:end_address]
        with open(binfile, 'wb') as f:
            f.write(bytearray(data))
        info("Wrote {}: origin={}, end={}, size={}".format(binfile, base_address, end_address, len(data)))

def run(skoolfile, binfile, options):
    binwriter = BinWriter(skoolfile)
    binwriter.write(binfile, options.origin, options.end)

def main(args):
    parser = argparse.ArgumentParser(
        usage='{} [options] file.skool [file.bin]'.format(os.path.basename(sys.argv[0])),
        description="Convert a skool file into a binary (raw memory) file. "
                    "'file.skool' may be a regular file, or '-' for standard input. "
                    "If 'file.bin' is not given, it defaults to the name of the input file with '.skool' replaced by '.bin'.",
        add_help=False
    )
    parser.add_argument('skoolfile', help=argparse.SUPPRESS, nargs='?')
    parser.add_argument('binfile', help=argparse.SUPPRESS, nargs='?')
    group = parser.add_argument_group('Options')
    group.add_argument('-e', dest='end', metavar='ADDR', type=int,
                       help='Use this end address (default is the end address of the skool file)')
    group.add_argument('-o', dest='origin', metavar='ADDR', type=int,
                       help='Use this origin address (default is the base address of the skool file)')
    namespace, unknown_args = parser.parse_known_args(args)
    skoolfile = namespace.skoolfile
    if unknown_args or skoolfile is None:
        parser.exit(2, parser.format_help())

    binfile = namespace.binfile
    if binfile is None:
        if skoolfile.lower().endswith('.skool'):
            binfile = skoolfile[:-6] + '.bin'
        else:
            binfile = skoolfile + '.bin'
    run(skoolfile, binfile, namespace)

###############################################################################
# Begin
###############################################################################
try:
    main(sys.argv[1:])
except SkoolKitError as e:
    error(e.args[0])
