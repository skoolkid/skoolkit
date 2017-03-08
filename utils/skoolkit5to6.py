#!/usr/bin/env python3
import sys
import argparse
import re

DESCRIPTION = """
Convert a ref file or CSS file from SkoolKit 5 format to SkoolKit 6 format and
print it on standard output. Specifically:

* reactivate [PageContent:*] sections
* rename and update [Template:changelog_entry] sections
* rename and update [Template:changelog_item_list] sections
* update {div,ul}.changelog* CSS selectors
"""

CSS_SELECTORS = (
    ('(div|ul).changelog', r'\1.list-entry'),
    ('div.changelog-(1|2|desc|title)', r'div.list-entry-\1'),
    ('ul.changelog([1-9][0-9]*)', r'ul.list-entry\1'),
)

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
            return index, section
    return -1, None

def _update_template(sections, old_name, new_name, old_field, new_field):
    template = _get_section(sections, 'Template:' + old_name)[1]
    if template:
        template[0] = 'Template:' + new_name
        lines = template[1]
        for i in range(len(lines)):
            lines[i] = lines[i].replace(old_field, new_field).replace('changelog', 'list-entry')

def convert_ref(reffile_f):
    preamble, sections = _parse_ref(reffile_f)

    # Reactivate [PageContent:*] sections
    new_page_sections = []
    for section in sections:
        if section[0].startswith('PageContent:'):
            page_section_name = 'Page:' + section[0][12:]
            index, page_section = _get_section(sections, page_section_name)
            page_content_param = 'PageContent=#INCLUDE({})'.format(section[0])
            if page_section is None:
                new_page_sections.append((page_section_name, [page_content_param]))
            else:
                lines = page_section[1]
                index = len(lines)
                while index and not lines[index - 1]:
                    index -= 1
                lines.insert(index, page_content_param)
    for section in new_page_sections:
        index = _get_section(sections, 'PageContent:' + section[0][5:])[0]
        sections.insert(index, section)

    # [Template:changelog_entry]
    _update_template(sections, 'changelog_entry', 'list_entry', '{t_changelog_item_list}', '{t_list_items}')

    # [Template:changelog_item_list]
    _update_template(sections, 'changelog_item_list', 'list_items', '{m_changelog_item}', '{m_list_item}')

    # Print ref file
    if preamble:
        print('\n'.join(preamble))
    for section_name, lines in sections:
        print('[{}]'.format(section_name))
        print('\n'.join(lines).rstrip() + '\n')

def convert_css(cssfile_f):
    css = cssfile_f.read()
    for old, new in CSS_SELECTORS:
        css = re.sub(old + '(?= |,|$)', new, css)
    print(css.rstrip())

def main(args):
    parser = argparse.ArgumentParser(
        usage='skoolkit5to6.py FILE',
        description=DESCRIPTION,
        formatter_class=argparse.RawTextHelpFormatter,
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
        elif infile_l.endswith('.css'):
            convert_css(f)
        else:
            print('Input file must be a ref file or css file', file=sys.stderr)

if __name__ == '__main__':
    main(sys.argv[1:])
