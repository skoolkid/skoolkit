#!/usr/bin/env python3
import sys
import argparse

DESCRIPTION = """
Convert a ref file, skool file or skool file template from SkoolKit 6 format to
SkoolKit 7 format and print it on standard output.
"""

def _parse_ref(reffile_f):
    preamble = []
    sections = []
    section = []
    section_name = None
    for line in reffile_f:
        s_line = line.rstrip()
        if line.startswith('[') and not line.startswith('[[') and s_line.endswith(']'):
            if section_name:
                sections.append([section_name, section])
            else:
                preamble = section
            section_name = s_line[1:-1]
            section = []
        else:
            section.append(s_line)
    if section_name:
        sections.append([section_name, section])
    else:
        preamble = section
    return preamble, sections

def _get_section(sections, name):
    for index, section in enumerate(sections):
        if name == section[0]:
            return index, section[1]
    return -1, None

def convert_ref(reffile_f):
    preamble, sections = _parse_ref(reffile_f)

    # GameStatusBufferIncludes
    gsb_includes = None
    index, game_section = _get_section(sections, 'Game')
    prefix = 'GameStatusBufferIncludes='
    if game_section:
        for line in game_section:
            if line.startswith(prefix):
                gsb_includes = line[len(prefix):]
        sections[index][1] = [line for line in game_section if not line.startswith(prefix)]
    mmgsb_section = False
    for section_name, lines in sections:
        if section_name.startswith('MemoryMap:'):
            if section_name[10:] == 'GameStatusBuffer':
                mmgsb_section = True
                entry_types = 'G'
            else:
                entry_types = ''
            for i, line in enumerate(lines):
                if line.startswith('EntryTypes='):
                    entry_types = line[11:]
                    lines[i] = 'EntryTypes=' + entry_types.replace('G', '')
            if 'G' in entry_types and gsb_includes:
                includes = False
                for i, line in enumerate(lines):
                    if line.startswith('Includes='):
                        includes = True
                        lines[i] = '{},{}'.format(line, gsb_includes)
                if not includes:
                    index = len(lines)
                    while index and not lines[index - 1]:
                        index -= 1
                    lines.insert(index, 'Includes=' + gsb_includes)
    if not mmgsb_section and gsb_includes:
        sections.append(['MemoryMap:GameStatusBuffer', ['Includes=' + gsb_includes]])

    # Print ref file
    if preamble:
        print('\n'.join(preamble))
    for section_name, lines in sections:
        print('[{}]'.format(section_name))
        print('\n'.join(lines).rstrip() + '\n')

def _add_remote(directives, lines):
    if lines:
        directives.append('@remote={}:{}'.format(lines[0][1], ','.join([r[0] for r in lines])))
        lines[:] = []

def convert_skool(skoolfile_f):
    directives = []
    remotes = []
    blocks = []
    lines = []
    entry_ctl = ''
    for line in skoolfile_f:
        if line.startswith((';', '@')):
            lines.append(line)
            continue
        s_line = line.strip()
        if not s_line:
            if entry_ctl not in ('d', 'r'):
                blocks.append((entry_ctl, lines))
                blocks.append(('', [line]))
            lines = []
            entry_ctl = ''
            _add_remote(directives, remotes)
            continue
        if s_line[0] == ';':
            lines.append(line)
            continue
        lines.append(line)
        ctl = line[0]
        addr = line[1:6]
        operation = line[6:].partition(';')[0].strip()
        suffix = line[6:].strip()
        if ctl in 'bcdgirstuw':
            entry_ctl = entry_ctl or ctl
        if entry_ctl == 'd':
            op_l = operation[:4].lower()
            if op_l in ('defb', 'defs', 'defw'):
                directives.append('@{}={}:{}'.format(op_l, addr, suffix[4:].lstrip()))
        elif entry_ctl == 'r':
            remotes.append((addr, operation))
    blocks.append((entry_ctl, lines))
    _add_remote(directives, remotes)

    for ctl, lines in blocks:
        if ctl and directives:
            while directives:
                print(directives.pop(0))
        for line in lines:
            sys.stdout.write(line)

def main(args):
    parser = argparse.ArgumentParser(
        usage='skoolkit6to7.py FILE',
        description=DESCRIPTION,
        add_help=False
    )
    parser.add_argument('infile', help=argparse.SUPPRESS, nargs='?')
    namespace, unknown_args = parser.parse_known_args(args)
    infile = namespace.infile
    if unknown_args or infile is None:
        parser.exit(2, parser.format_help())
    infile_l = infile.lower()
    with open(infile) as f:
        if infile_l.endswith('.ref'):
            convert_ref(f)
        elif infile_l.endswith(('.ctl', '.css')):
            print('Input file must be a ref file, skool file or skool file template', file=sys.stderr)
        else:
            convert_skool(f)

if __name__ == '__main__':
    main(sys.argv[1:])
