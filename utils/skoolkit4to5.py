#!/usr/bin/env python
import sys
import argparse

def write(text):
    sys.stdout.write(text)

def info(text):
    sys.stderr.write(text + '\n')

def convert_skool(skoolfile_f):
    count = 0
    for line in skoolfile_f:
        if line.startswith('; @'):
            write(line[2:])
            count += 1
        else:
            write(line)
    if count:
        info("Converted {} ASM directives".format(count))
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
            raise NotImplementedError
        elif infile_l.endswith('.sft'):
            convert_sft(f)
        else:
            convert_skool(f)

if __name__ == '__main__':
    main(sys.argv[1:])
