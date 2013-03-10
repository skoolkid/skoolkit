# -*- coding: utf-8 -*-

# Copyright 2008-2013 Richard Dymond (rjdymond@gmail.com)
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

import time

from . import info, get_class, parse_int_arg, UsageError
from .skoolparser import SkoolParser, CASE_LOWER, CASE_UPPER, BASE_10, BASE_16
from .skoolasm import AsmWriter

quiet = False

DEF_INSTR_WIDTH = 23

TAB = 'tab'
CRLF = 'crlf'
INSTRUCTION_WIDTH = 'instruction-width'

USAGE = """skool2asm.py [options] FILE

  Convert a skool file into an ASM file, written to standard output. FILE may
  be a regular file, or '-' for standard input.

Options:
  -q    Be quiet
  -w    Suppress warnings
  -d    Use CR+LF to end lines
  -t    Use tab to indent instructions (default indentation is 2 spaces)
  -l    Write disassembly in lower case
  -u    Write disassembly in upper case
  -D    Write disassembly in decimal
  -H    Write disassembly in hexadecimal
  -i N  Set instruction field width to N (default={0})
  -f N  Apply fixes:
          N=0: None (default)
          N=1: @ofix only
          N=2: @ofix and @bfix
          N=3: @ofix, @bfix and @rfix (implies -r)
  -c    Create default labels for unlabelled instructions
  -s    Use safe substitutions (@ssub)
  -r    Use relocatability substitutions too (@rsub) (implies '-f 1')""".format(DEF_INSTR_WIDTH)

def notify(notice):
    if not quiet:
        info(notice)

def clock(prefix, operation, *args, **kwargs):
    go = time.time()
    result = operation(*args, **kwargs)
    stop = time.time()
    notify('{0} ({1:0.2f}s)'.format(prefix, stop - go))
    return result

def parse_args(args):
    be_quiet = False
    properties = {}
    case = None
    base = None
    asm_mode = 1
    fix_mode = 0
    warn = True
    create_labels = False
    files = []
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == '-q':
            be_quiet = True
        elif arg == '-w':
            warn = False
        elif arg == '-d':
            properties[CRLF] = '1'
        elif arg == '-l':
            case = CASE_LOWER
        elif arg == '-u':
            case = CASE_UPPER
        elif arg == '-D':
            base = BASE_10
        elif arg == '-H':
            base = BASE_16
        elif arg == '-i':
            properties[INSTRUCTION_WIDTH] = parse_int_arg(args[i + 1], arg, 'Instruction field width')
            i += 1
        elif arg == '-f':
            fix_mode = parse_int_arg(args[i + 1], arg, 'Fix mode')
            i += 1
        elif arg == '-r':
            asm_mode = 3
        elif arg == '-s':
            asm_mode = 2
        elif arg == '-t':
            properties[TAB] = '1'
        elif arg == '-c':
            create_labels = True
        elif len(arg) > 1 and arg[0] == '-':
            raise UsageError(USAGE)
        else:
            files.append(arg)
        i += 1

    if len(files) != 1:
        raise UsageError(USAGE)
    parser_mode = (case, base, asm_mode, warn, fix_mode, create_labels)
    writer_mode = (case == CASE_LOWER, warn)
    return files[0], properties, parser_mode, writer_mode, be_quiet

def run(skoolfile, properties, parser_mode, writer_mode):
    # Create the parser
    case, base, asm_mode, warn, fix_mode, create_labels = parser_mode
    parser = clock('Parsed {0}'.format(skoolfile), SkoolParser, skoolfile, case=case, base=base, asm_mode=asm_mode, warnings=warn, fix_mode=fix_mode, create_labels=create_labels)

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
    cls_name = parser.asm_writer_class
    if cls_name:
        asm_writer_class = get_class(cls_name)
        notify('Using ASM writer {0}'.format(cls_name))
    else:
        asm_writer_class = AsmWriter
    skool_writer = asm_writer_class(parser, crlf, tab, writer_properties, lower, instr_width, show_warnings)
    clock('Wrote ASM to stdout', skool_writer.write)

def main(args):
    global quiet
    skoolfile, properties, parser_mode, writer_mode, quiet = parse_args(args)
    run(skoolfile, properties, parser_mode, writer_mode)
