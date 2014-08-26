# -*- coding: utf-8 -*-

# Copyright 2008-2014 Richard Dymond (rjdymond@gmail.com)
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
import time

from . import info, get_class, VERSION, show_package_dir
from .skoolparser import SkoolParser, CASE_LOWER, CASE_UPPER, BASE_10, BASE_16
from .skoolasm import AsmWriter

quiet = False

DEF_INSTR_WIDTH = 23

TAB = 'tab'
CRLF = 'crlf'
INSTRUCTION_WIDTH = 'instruction-width'

def notify(notice):
    if not quiet:
        info(notice)

def clock(prefix, operation, *args, **kwargs):
    go = time.time()
    result = operation(*args, **kwargs)
    stop = time.time()
    notify('{0} ({1:0.2f}s)'.format(prefix, stop - go))
    return result

def run(skoolfile, options, parser_mode, writer_mode):
    global quiet
    quiet = options.quiet

    # Create the parser
    case, base, asm_mode, warn, fix_mode, create_labels = parser_mode
    if skoolfile == '-':
        fname = 'stdin'
    else:
        fname = skoolfile
    parser = clock('Parsed {}'.format(fname), SkoolParser, skoolfile, case=case, base=base, asm_mode=asm_mode, warnings=warn, fix_mode=fix_mode, create_labels=create_labels)

    properties = {}
    if options.crlf:
        properties[CRLF] = '1'
    if options.inst_width is not None:
        properties[INSTRUCTION_WIDTH] = options.inst_width
    if options.tabs:
        properties[TAB] = '1'
    writer_properties = {}
    writer_properties.update(parser.properties)
    writer_properties.update(properties)
    crlf = writer_properties.get(CRLF, '0') != '0'
    tab = writer_properties.get(TAB, '0') != '0'
    lower, show_warnings = writer_mode
    if show_warnings:
        show_warnings = writer_properties.get('warnings', '1') != '0'
    try:
        instr_width = int(writer_properties.get(INSTRUCTION_WIDTH, DEF_INSTR_WIDTH))
    except ValueError:
        instr_width = DEF_INSTR_WIDTH

    # Write the ASM file
    cls_name = options.writer or parser.asm_writer_class
    if cls_name:
        asm_writer_class = get_class(cls_name)
        notify('Using ASM writer {0}'.format(cls_name))
    else:
        asm_writer_class = AsmWriter
    skool_writer = asm_writer_class(parser, crlf, tab, writer_properties, lower, instr_width, show_warnings)
    clock('Wrote ASM to stdout', skool_writer.write)

def main(args):
    parser = argparse.ArgumentParser(
        usage='skool2asm.py [options] file',
        description="Convert a skool file into an ASM file, written to standard output. "
                    "FILE may be\na regular file, or '-' for standard input.",
        formatter_class=argparse.RawTextHelpFormatter,
        add_help=False
    )
    parser.add_argument('skoolfile', help=argparse.SUPPRESS, nargs='?')
    group = parser.add_argument_group('Options')
    group.add_argument('-c', '--create-labels', dest='create_labels', action='store_true',
                       help="Create default labels for unlabelled instructions")
    group.add_argument('-d', '--crlf', dest='crlf', action='store_true',
                       help="Use CR+LF to end lines")
    group.add_argument('-D', '--decimal', dest='base', action='store_const', const=BASE_10,
                       help="Write the disassembly in decimal")
    group.add_argument('-f', '--fixes', dest='fix_mode', metavar='N', type=int, choices=range(4), default=0,
                       help="Apply fixes:\n"
                            "  N=0: None (default)\n"
                            "  N=1: @ofix only\n"
                            "  N=2: @ofix and @bfix\n"
                            "  N=3: @ofix, @bfix and @rfix (implies -r)")
    group.add_argument('-H', '--hex', dest='base', action='store_const', const=BASE_16,
                       help="Write the disassembly in hexadecimal")
    group.add_argument('-i', '--inst-width', dest='inst_width', metavar='N', type=int,
                       help="Set instruction field width (default={})".format(DEF_INSTR_WIDTH))
    group.add_argument('-l', '--lower', dest='case', action='store_const', const=CASE_LOWER,
                       help="Write the disassembly in lower case")
    group.add_argument('-p', '--package-dir', dest='package_dir', action='store_true',
                       help="Show path to skoolkit package directory and exit")
    group.add_argument('-q', '--quiet', dest='quiet', action='store_true',
                       help="Be quiet")
    group.add_argument('-r', '--rsub', dest='asm_mode', action='store_const', const=3, default=1,
                       help="Use relocatability substitutions too (@rsub) (implies\n'-f 1')")
    group.add_argument('-s', '--ssub', dest='asm_mode', action='store_const', const=2, default=1,
                       help="Use safe substitutions (@ssub)")
    group.add_argument('-t', '--tabs', dest='tabs', action='store_true',
                       help="Use tab to indent instructions (default indentation is\n2 spaces)")
    group.add_argument('-u', '--upper', dest='case', action='store_const', const=CASE_UPPER,
                       help="Write the disassembly in upper case")
    group.add_argument('-V', '--version', action='version', version='SkoolKit {}'.format(VERSION),
                       help='Show SkoolKit version number and exit')
    group.add_argument('-w', '--no-warnings', dest='warn', action='store_false',
                       help="Suppress warnings")
    group.add_argument('-W', '--writer', dest='writer', metavar='CLASS',
                       help="Specify the ASM writer class to use")

    namespace, unknown_args = parser.parse_known_args(args)
    if namespace.package_dir:
        show_package_dir()
    if unknown_args or namespace.skoolfile is None:
        parser.exit(2, parser.format_help())
    parser_mode = (namespace.case, namespace.base, namespace.asm_mode, namespace.warn, namespace.fix_mode, namespace.create_labels)
    writer_mode = (namespace.case == CASE_LOWER, namespace.warn)
    run(namespace.skoolfile, namespace, parser_mode, writer_mode)
