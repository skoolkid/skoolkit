#!/usr/bin/env python
import sys
import argparse

def write(text):
    sys.stdout.write(text)

def info(text):
    sys.stderr.write(text + '\n')

def _convert_ctl_asm_directive(line):
    asm_fields = line[3:].rstrip().split(':', 1)
    if len(asm_fields) < 2:
        write(line)
        return 0
    directive = asm_fields[0]
    asm_fields[1] = asm_fields[1].split('=', 1)
    addr_str = asm_fields[1][0]
    if directive == 'ignoreua':
        comment_type = 'i'
        if ':' in addr_str:
            addr_str, comment_type = addr_str.split(':', 1)
        write('@ {} {}:{}\n'.format(addr_str, directive, comment_type))
    elif len(asm_fields[1]) == 2:
        write('@ {} {}={}\n'.format(addr_str, directive, asm_fields[1][1]))
    else:
        write('@ {} {}\n'.format(addr_str, directive))
    return 1

def convert_skool(skoolfile_f):
    count = 0
    for line in skoolfile_f:
        if line.startswith('; @'):
            write(line[2:])
            count += 1
        else:
            write(line)
    if count:
        info("Converted {} ASM directive(s)".format(count))
    else:
        info("No changes")

def convert_ctl(ctlfile_f):
    asm_dir_count = 0
    for line in ctlfile_f:
        if line.startswith('; @'):
            asm_dir_count += _convert_ctl_asm_directive(line)
        else:
            write(line)
    if asm_dir_count:
        info("Converted {} ASM directive(s)".format(asm_dir_count))
    else:
        info("No changes")

def convert_sft(sftfile_f):
    convert_skool(sftfile_f)

def main(args):
    parser = argparse.ArgumentParser(
        usage='skoolkit4to5.py FILE',
        description="Convert a skool, ctl or sft file from SkoolKit 4 format to SkoolKit 5 format and print it on standard output.",
        add_help=False
    )
    parser.add_argument('infile', help=argparse.SUPPRESS, nargs='?')
    namespace, unknown_args = parser.parse_known_args(args)
    infile = namespace.infile
    if unknown_args or infile is None:
        parser.exit(2, parser.format_help())
    infile_l = infile.lower()
    with open(infile) as f:
        if infile_l.endswith('.ctl'):
            convert_ctl(f)
        elif infile_l.endswith('.sft'):
            convert_sft(f)
        else:
            convert_skool(f)

if __name__ == '__main__':
    main(sys.argv[1:])
