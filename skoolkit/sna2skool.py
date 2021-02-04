# Copyright 2009-2015, 2017-2021 Richard Dymond (rjdymond@gmail.com)
#
# This file is part of SkoolKit.
#
# SkoolKit is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# SkoolKit is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# SkoolKit. If not, see <http://www.gnu.org/licenses/>.

import argparse
import glob
import os.path

from skoolkit import info, integer, VERSION
from skoolkit.config import get_config, show_config, update_options
from skoolkit.ctlparser import CtlParser
from skoolkit.snapshot import make_snapshot
from skoolkit.snaskool import SkoolWriter

def get_ctl_parser(ctls, infile, start, end, def_start, def_end):
    if infile[-4:].lower() in ('.bin', '.sna', '.szx', '.z80'):
        prefix = infile[:-4]
    else:
        prefix = infile
    if not ctls:
        ctls.extend(sorted(glob.glob(prefix + '*.ctl')))
    ctlfiles = []
    if ctls and '0' not in ctls:
        # Use control file(s)
        for ctl in ctls:
            if os.path.isdir(ctl):
                ctlfiles.extend(sorted(glob.glob(os.path.join(ctl, '*.ctl'))))
            else:
                ctlfiles.append(ctl)
    if ctlfiles:
        if len(ctlfiles) > 1:
            suffix = 's'
        else:
            suffix = ''
        info('Using control file{}: {}'.format(suffix, ', '.join(ctlfiles)))
        ctl_parser = CtlParser()
        ctl_parser.parse_ctls(ctlfiles, start, end)
    else:
        ctl_parser = CtlParser({def_start: 'c', def_end: 'i'})
    return ctl_parser

def run(infile, options, config):
    snapshot, start, end = make_snapshot(infile, options.org, options.start, options.end, options.page)
    if options.start is None:
        options.start = 0
    ctl_parser = get_ctl_parser(options.ctls, infile, options.start, options.end, start, end)
    writer = SkoolWriter(snapshot, ctl_parser, options, config)
    writer.write_skool(config['ListRefs'], config['Text'])

def main(args):
    config = get_config('sna2skool')
    parser = argparse.ArgumentParser(
        usage='sna2skool.py [options] FILE',
        description="Convert a binary (raw memory) file or a SNA, SZX or Z80 snapshot into a skool file. "
                    "FILE may be a regular file, or '-' for standard input.",
        add_help=False
    )
    parser.add_argument('snafile', help=argparse.SUPPRESS, nargs='?')
    group = parser.add_argument_group('Options')
    group.add_argument('-c', '--ctl', dest='ctls', metavar='PATH', action='append', default=[],
                       help="Specify a control file to use, or a directory from which to read control files. "
                            "PATH may be '-' for standard input, or '0' to use no control file. "
                            "This option may be used multiple times.")
    group.add_argument('-e', '--end', dest='end', metavar='ADDR', type=integer, default=65536,
                       help='Stop disassembling at this address (default=65536).')
    group.add_argument('-H', '--hex', dest='base', action='store_const', const=16, default=config['Base'],
                       help='Write hexadecimal addresses and operands in the disassembly.')
    group.add_argument('-I', '--ini', dest='params', metavar='p=v', action='append', default=[],
                       help="Set the value of the configuration parameter 'p' to 'v'. This option may be used multiple times.")
    group.add_argument('-l', '--lower', dest='case', action='store_const', const=1, default=config['Case'],
                       help='Write the disassembly in lower case.')
    group.add_argument('-o', '--org', dest='org', metavar='ADDR', type=integer,
                       help='Specify the origin address of a binary (.bin) file (default: 65536 - length).')
    group.add_argument('-p', '--page', dest='page', metavar='PAGE', type=int, choices=list(range(8)),
                       help='Specify the page (0-7) of a 128K snapshot to map to 49152-65535.')
    group.add_argument('--show-config', dest='show_config', action='store_true',
                       help="Show configuration parameter values.")
    group.add_argument('-s', '--start', dest='start', metavar='ADDR', type=integer,
                       help='Start disassembling at this address.')
    group.add_argument('-V', '--version', action='version', version='SkoolKit {}'.format(VERSION),
                       help='Show SkoolKit version number and exit.')
    group.add_argument('-w', '--line-width', dest='line_width', metavar='W', type=int, default=config['LineWidth'],
                       help='Set the maximum line width of the skool file (default: {}).'.format(config['LineWidth']))

    namespace, unknown_args = parser.parse_known_args(args)
    if namespace.show_config:
        show_config('sna2skool', config)
    if unknown_args or namespace.snafile is None:
        parser.exit(2, parser.format_help())
    update_options('sna2skool', namespace, namespace.params, config)
    run(namespace.snafile, namespace, config)
