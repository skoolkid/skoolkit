# Copyright 2018, 2019 Richard Dymond (rjdymond@gmail.com)
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

from skoolkit import find_file, info, integer, open_file, VERSION
from skoolkit.config import get_config, show_config, update_options
from skoolkit.snactl import generate_ctls, write_ctl
from skoolkit.snapshot import make_snapshot

END = 65536

def run(snafile, options, config):
    dict_fname = config['Dictionary']
    if dict_fname:
        if find_file(dict_fname):
            info("Using dictionary file: {}".format(dict_fname))
            words = set()
            with open_file(config['Dictionary']) as f:
                for line in f:
                    word = line.strip().lower()
                    if word:
                        words.add(word)
            if words:
                config['words'] = words
        else:
            info("Dictionary file '{}' not found".format(dict_fname))
    snapshot, start, end = make_snapshot(snafile, options.org, options.start, options.end, options.page)
    ctls = generate_ctls(snapshot, start, end, config, options.code_map)
    write_ctl(ctls, options.ctl_hex)

def main(args):
    config = get_config('sna2ctl')
    parser = argparse.ArgumentParser(
        usage='sna2ctl.py [options] FILE',
        description="Generate a control file for a binary (raw memory) file or a SNA, SZX or Z80 snapshot. "
                    "FILE may be a regular file, or '-' for standard input.",
        add_help=False
    )
    parser.add_argument('snafile', help=argparse.SUPPRESS, nargs='?')
    group = parser.add_argument_group('Options')
    group.add_argument('-e', '--end', dest='end', metavar='ADDR', type=integer, default=END,
                       help='Stop at this address (default={}).'.format(END))
    group.add_argument('-h', '--hex', dest='ctl_hex', action='store_const', const=2, default=config['Hex'],
                       help='Write upper case hexadecimal addresses.')
    group.add_argument('-I', '--ini', dest='params', metavar='p=v', action='append', default=[],
                       help="Set the value of the configuration parameter 'p' to 'v'. This option may be used multiple times.")
    group.add_argument('-l', '--hex-lower', dest='ctl_hex', action='store_const', const=1, default=config['Hex'],
                       help='Write lower case hexadecimal addresses.')
    group.add_argument('-m', '--map', dest='code_map', metavar='FILE',
                       help='Use FILE as a code execution map.')
    group.add_argument('-o', '--org', dest='org', metavar='ADDR', type=integer,
                       help='Specify the origin address of a binary file (default: 65536 - length).')
    group.add_argument('-p', '--page', dest='page', metavar='PAGE', type=int, choices=list(range(8)),
                       help='Specify the page (0-7) of a 128K snapshot to map to 49152-65535.')
    group.add_argument('--show-config', dest='show_config', action='store_true',
                       help="Show configuration parameter values.")
    group.add_argument('-s', '--start', dest='start', metavar='ADDR', type=integer, default=0,
                       help='Start at this address (default=16384).')
    group.add_argument('-V', '--version', action='version', version='SkoolKit {}'.format(VERSION),
                       help='Show SkoolKit version number and exit.')

    namespace, unknown_args = parser.parse_known_args(args)
    if namespace.show_config:
        show_config('sna2ctl', config)
    if unknown_args or namespace.snafile is None:
        parser.exit(2, parser.format_help())
    update_options('sna2ctl', namespace, namespace.params, config)
    run(namespace.snafile, namespace, config)
