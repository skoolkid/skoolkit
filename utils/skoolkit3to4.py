#!/usr/bin/env python
import sys
import argparse
from collections import OrderedDict

CSS_SELECTORS = (
    ('div.box1', 'div.box-1'),
    ('div.box2', 'div.box-2'),
    ('div.boxTitle', 'div.box-title'),
    ('div.changelog1', 'div.changelog-1'),
    ('div.changelog2', 'div.changelog-2'),
    ('div.changelogDesc', 'div.changelog-desc'),
    ('div.changelogTitle', 'div.changelog-title'),
    ('div.gbufDesc', 'div.map-entry-title-11'),
    ('div.headerText', 'div.section-header'),
    ('div.mapIntro', 'div.map-intro'),
    ('table.dataDisassembly', 'table.disassembly'),
    ('table.gbuffer', 'table.map'),
    ('table.input', 'table.input-1'),
    ('table.output', 'table.output-1'),
    ('table.prevNext', 'table.asm-navigation'),
    ('td.address', 'td.address-1'),
    ('td.asmLabel', 'td.asm-label-1'),
    ('td.comment', 'td.comment-11'),
    ('td.dataComment', 'td.comment-11'),
    ('td.dataDesc', 'td.map-b-desc, td.map-w-desc'),
    ('td.data', 'td.map-b, td.map-w'),
    ('td.gbufAddress', 'td.map-b, td.map-c, td.map-g, td.map-s, td.map-t, td.map-u, td.map-w'),
    ('td.gbufferDesc', 'td.map-g-desc'),
    ('td.gbuffer', 'td.map-g'),
    ('td.gbufLength', 'td.map-length-1'),
    ('td.headerText', 'td.page-header'),
    ('td.label', 'td.address-2'),
    ('td.mapByte', 'td.map-byte-1'),
    ('td.mapPage', 'td.map-page-1'),
    ('td.messageDesc', 'td.map-t-desc'),
    ('td.message', 'td.map-t'),
    ('td.routineComment', 'td.routine-comment'),
    ('td.routineDesc', 'td.map-c-desc'),
    ('td.routine', 'td.map-c'),
    ('td.transparentComment', 'td.comment-10'),
    ('td.transparentDataComment', 'td.comment-10'),
    ('td.unusedDesc', 'td.map-s-desc, td.map-u-desc'),
    ('td.unused', 'td.map-s, td.map-u'),
    ('ul.indexList', 'ul.index-list'),
    ('ul.linkList', 'ul.contents'),
    ('body.bugs', 'body.Bugs'),
    ('body.changelog', 'body.Changelog'),
    ('body.disassembly', 'body.Asm-b, body.Asm-c, body.Asm-g, body.Asm-s, body.Asm-t, body.Asm-u, body.Asm-w'),
    ('body.facts', 'body.Facts'),
    ('body.gbuffer', 'body.GameStatusBuffer'),
    ('body.glossary', 'body.Glossary'),
    ('body.main', 'body.GameIndex'),
    ('body.map', 'body.DataMap, body.MemoryMap, body.MessagesMap, body.RoutinesMap, body.UnusedMap'),
    ('body.pokes', 'body.Pokes'),
    ('div.gbufDetails', 'div.map-entry-desc-1'),
    ('td.gbufDesc', 'td.map-b-desc, td.map-c-desc, td.map-g-desc, td.map-s-desc, td.map-t-desc, td.map-u-desc, td.map-w-desc'),
    ('td.headerLogo', 'td.logo'),
    ('td.registerContents', 'td.register-desc')
)

def write(text):
    sys.stdout.write(text)

def info(text):
    sys.stderr.write(text + '\n')

def add_line(sections, section_name, line, default=None, index=0):
    sections.setdefault(section_name, default or []).insert(index, line)

def convert_skool(skoolfile_f):
    z_count = 0
    for line in skoolfile_f:
        if line.startswith('z'):
            write('s' + line[1:])
            z_count += 1
        else:
            write(line)
    if z_count:
        info("Converted {} 'z' directives to 's'".format(z_count))
    else:
        info("No changes")

def convert_ref(reffile_f):
    preamble = []
    sections = OrderedDict()
    section = []
    section_name = None
    for line in reffile_f:
        s_line = line.rstrip()
        if line.startswith('[') and s_line.endswith(']'):
            if section_name:
                sections[section_name] = section
            else:
                preamble = section
            section_name = s_line[1:-1]
            section = []
        else:
            section.append(s_line)
    if section_name:
        sections[section_name] = section
    else:
        preamble = section

    # [Info]
    if 'Info' in sections:
        if 'Game' in sections:
            game_section = sections['Game']
            index = 0
            if game_section:
                index = len(game_section) - 1
                while index >= 0:
                    if game_section[index]:
                        index += 1
                        break
                    index -= 1
            index = max(index, 0)
            for line in sections['Info']:
                if line:
                    game_section.insert(index, line)
                    index += 1
        else:
            sections['Game'] = sections['Info']
        del sections['Info']

    # [Graphics]
    if 'Graphics' in sections:
        sections['PageContent:Graphics'] = sections['Graphics']
        if not ('Paths' in sections and any([line.startswith('Graphics=') for line in sections['Paths']])):
            add_line(sections, 'Paths', 'Graphics=graphics/graphics.html')
        index_section = 'Index:Graphics:Graphics'
        if not (index_section in sections and any([line == 'Graphics' for line in sections[index_section]])):
            add_line(sections, index_section, 'Graphics', ['GraphicGlitches'])
        del sections['Graphics']

    # [Page:*]
    empty_page_sections = []
    for section_name, lines in sections.items():
        if section_name.startswith('Page:'):
            page_id = section_name[5:]
            new_lines = []
            for line in lines:
                if line.startswith('Link='):
                    add_line(sections, 'Links', '{}={}'.format(page_id, line[5:]))
                elif line.startswith('Path='):
                    add_line(sections, 'Paths', '{}={}'.format(page_id, line[5:]))
                elif line.startswith('Title='):
                    add_line(sections, 'Titles', '{}={}'.format(page_id, line[6:]))
                elif line and not line.startswith('BodyClass='):
                    new_lines.append(line)
            if new_lines:
                lines[:] = new_lines
            else:
                empty_page_sections.append(section_name)
    for section_name in empty_page_sections:
        del sections[section_name]

    # [OtherCode:*]
    for section_name, lines in sections.items():
        if section_name.startswith('OtherCode:'):
            code_id = section_name[10:]
            index_page_id = '{}-Index'.format(code_id)
            new_lines = []
            for line in lines:
                if line.startswith('Link='):
                    add_line(sections, 'Links', '{}={}'.format(index_page_id, line[5:]))
                elif line.startswith('Index='):
                    add_line(sections, 'Paths', '{}={}'.format(index_page_id, line[6:]))
                elif line.startswith('Path='):
                    add_line(sections, 'Paths', '{}-CodePath={}'.format(code_id, line[5:]))
                elif line.startswith('Title='):
                    title = line[6:]
                    add_line(sections, 'PageHeaders', '{}={}'.format(index_page_id, title))
                    add_line(sections, 'Titles', '{}={}'.format(index_page_id, title))
                elif line.startswith('Header='):
                    header = line[7:]
                    index = 0
                    for ctl in 'bcgstuw':
                        add_line(sections, 'PageHeaders', '{}-Asm-{}={}'.format(code_id, ctl, header), index=index)
                        index += 1
                elif line and not line.startswith('IndexPageId='):
                    new_lines.append(line)
            lines[:] = new_lines

    write('\n'.join(preamble) + '\n')
    for section_name, lines in sections.items():
        write('[{}]\n'.format(section_name))
        write('\n'.join(lines).rstrip())
        write('\n\n')

def convert_ctl(ctlfile_f):
    z_count = Z_count = 0
    for line in ctlfile_f:
        if line.startswith('z'):
            write('s' + line[1:])
            z_count += 1
        elif line.startswith('Z'):
            write('S' + line[1:])
            Z_count += 1
        else:
            write(line)
    if z_count:
        info("Converted {} 'z' directives to 's'".format(z_count))
    if Z_count:
        info("Converted {} 'Z' directives to 'S'".format(Z_count))
    if z_count == Z_count == 0:
        info("No changes")

def convert_sft(sftfile_f):
    z_count = Z_count = 0
    for line in sftfile_f:
        o_line = line
        if o_line.startswith('z'):
            o_line = 's' + o_line[1:]
            z_count += 1
        if len(o_line) > 1 and o_line[1] == 'Z':
            o_line = o_line[0] + 'S' + o_line[2:]
            Z_count += 1
        write(o_line)
    if z_count:
        info("Converted {} 'z' directives to 's'".format(z_count))
    if Z_count:
        info("Converted {} 'Z' directives to 'S'".format(Z_count))
    if z_count == Z_count == 0:
        info("No changes")

def convert_css(cssfile_f):
    css = cssfile_f.read()
    for old, new in CSS_SELECTORS:
        css = css.replace(old, new)
    write(css)

def main(args):
    parser = argparse.ArgumentParser(
        usage='skoolkit3to4.py FILE',
        description="Convert a skool, ref, ctl, sft or css file from SkoolKit 3 format to SkoolKit 4 format and print it on standard output.",
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
        elif infile_l.endswith('.ctl'):
            convert_ctl(f)
        elif infile_l.endswith('.sft'):
            convert_sft(f)
        elif infile_l.endswith('.css'):
            convert_css(f)
        else:
            convert_skool(f)

if __name__ == '__main__':
    main(sys.argv[1:])
