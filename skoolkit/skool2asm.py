# Copyright 2008-2019 Richard Dymond (rjdymond@gmail.com)
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
import os.path
import time

from skoolkit import (info, get_class, integer, show_package_dir, VERSION,
                      BASE_10, BASE_16, CASE_LOWER, CASE_UPPER)
from skoolkit.config import get_config, show_config, update_options
from skoolkit.refparser import RefParser
from skoolkit.skoolasm import AsmWriter, TEMPLATES
from skoolkit.skoolparser import SkoolParser

def clock(quiet, prefix, operation, *args, **kwargs):
    go = time.time()
    result = operation(*args, **kwargs)
    stop = time.time()
    if not quiet:
        info('{} ({:0.2f}s)'.format(prefix, stop - go))
    return result

def run(skoolfile, options):
    # Read custom ASM templates
    t_parser = RefParser()
    if options.templates:
        t_parser.parse(options.templates, '#')
    templates = {t: t_parser.get_section(t, trim=False) for t in TEMPLATES if t_parser.has_section(t)}

    # Create the parser
    if skoolfile == '-':
        fname = 'stdin'
    else:
        fname = skoolfile
    asm_mode = options.asm_mode + 4 * int(options.force)
    parser = clock(options.quiet, 'Parsed {}'.format(fname), SkoolParser, skoolfile,
                   options.case, options.base, asm_mode, options.warn, options.fix_mode,
                   False, options.create_labels, True, options.start, options.end, options.variables)

    # Write the ASM file
    cls_name = options.writer or parser.asm_writer_class
    if cls_name:
        asm_writer_class = get_class(cls_name, os.path.dirname(skoolfile))
        if not options.quiet:
            info('Using ASM writer {0}'.format(cls_name))
    else:
        asm_writer_class = AsmWriter
    properties = dict(parser.properties)
    for spec in options.properties:
        name, sep, value = spec.partition('=')
        if sep:
            properties[name] = value
    if not options.warn:
        properties['warnings'] = '0'
    asm_writer = asm_writer_class(parser, properties, templates)
    clock(options.quiet, 'Wrote ASM to stdout', asm_writer.write)

def main(args):
    config = get_config('skool2asm')
    def_properties = ['{}={}'.format(k[4:], v) for k, v in config.items() if k.startswith('Set-')]

    parser = argparse.ArgumentParser(
        usage='skool2asm.py [options] FILE',
        description="Convert a skool file into an ASM file and write it to standard output. "
                    "FILE may\nbe a regular file, or '-' for standard input.",
        formatter_class=argparse.RawTextHelpFormatter,
        add_help=False
    )
    parser.add_argument('skoolfile', help=argparse.SUPPRESS, nargs='?')
    group = parser.add_argument_group('Options')
    group.add_argument('-c', '--create-labels', dest='create_labels', action='store_const', const=1, default=config['CreateLabels'],
                       help="Create default labels for unlabelled instructions.")
    group.add_argument('-D', '--decimal', dest='base', action='store_const', const=BASE_10, default=config['Base'],
                       help="Write the disassembly in decimal.")
    group.add_argument('-E', '--end', dest='end', metavar='ADDR', type=integer, default=65536,
                       help="Stop converting at this address.")
    group.add_argument('-f', '--fixes', dest='fix_mode', metavar='N', type=int, choices=range(4), default=0,
                       help="Apply fixes:\n"
                            "  N=0: None (default)\n"
                            "  N=1: @ofix only\n"
                            "  N=2: @ofix and @bfix\n"
                            "  N=3: @ofix, @bfix and @rfix (implies -r)")
    group.add_argument('-F', '--force', dest='force', action='store_true',
                       help="Force conversion, ignoring @start and @end directives.")
    group.add_argument('-H', '--hex', dest='base', action='store_const', const=BASE_16, default=config['Base'],
                       help="Write the disassembly in hexadecimal.")
    group.add_argument('-I', '--ini', dest='params', metavar='p=v', action='append', default=[],
                       help="Set the value of the configuration parameter 'p' to\n'v'. This option may be used multiple times.")
    group.add_argument('-l', '--lower', dest='case', action='store_const', const=CASE_LOWER, default=config['Case'],
                       help="Write the disassembly in lower case.")
    group.add_argument('-p', '--package-dir', dest='package_dir', action='store_true',
                       help="Show path to skoolkit package directory and exit.")
    group.add_argument('-P', '--set', dest='properties', metavar='p=v', action='append', default=def_properties,
                       help="Set the value of ASM writer property 'p' to 'v'. This\noption may be used multiple times.")
    group.add_argument('-q', '--quiet', dest='quiet', action='store_const', const=1, default=config['Quiet'],
                       help="Be quiet.")
    group.add_argument('-r', '--rsub', dest='asm_mode', action='store_const', const=3, default=1,
                       help="Apply safe substitutions (@ssub) and relocatability\nsubstitutions (@rsub) (implies '-f 1').")
    group.add_argument('--show-config', dest='show_config', action='store_true',
                       help="Show configuration parameter values.")
    group.add_argument('-s', '--ssub', dest='asm_mode', action='store_const', const=2, default=1,
                       help="Apply safe substitutions (@ssub).")
    group.add_argument('-S', '--start', dest='start', metavar='ADDR', type=integer, default=0,
                       help="Start converting at this address.")
    group.add_argument('-u', '--upper', dest='case', action='store_const', const=CASE_UPPER, default=config['Case'],
                       help="Write the disassembly in upper case.")
    group.add_argument('--var', dest='variables', metavar='name=value', action='append', default=[],
                       help="Define a variable that can be used by @if, #IF and #MAP.\nThis option may be used multiple times.")
    group.add_argument('-V', '--version', action='version', version='SkoolKit {}'.format(VERSION),
                       help='Show SkoolKit version number and exit.')
    group.add_argument('-w', '--no-warnings', dest='warn', action='store_const', const=0, default=config['Warnings'],
                       help="Suppress warnings.")
    group.add_argument('-W', '--writer', dest='writer', metavar='CLASS',
                       help="Specify the ASM writer class to use.")

    namespace, unknown_args = parser.parse_known_args(args)
    if namespace.show_config:
        show_config('skool2asm', config)
    if namespace.package_dir:
        show_package_dir()
    if unknown_args or namespace.skoolfile is None:
        parser.exit(2, parser.format_help())
    update_options('skool2asm', namespace, namespace.params, config)
    namespace.properties += [p[4:] for p in namespace.params if p.startswith('Set-')]
    if namespace.fix_mode == 3:
        namespace.asm_mode = 3
    elif namespace.asm_mode == 3:
        namespace.fix_mode = max(namespace.fix_mode, 1)
    run(namespace.skoolfile, namespace)
