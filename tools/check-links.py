#!/usr/bin/env python3

import sys
import os
import argparse

SKOOLKIT_HOME = os.environ.get('SKOOLKIT_HOME')
if not SKOOLKIT_HOME:
    sys.stderr.write('SKOOLKIT_HOME is not set; aborting\n')
    sys.exit(1)
SKOOLKIT_TESTS = '{}/tests'.format(SKOOLKIT_HOME)
if not os.path.isdir(SKOOLKIT_TESTS):
    sys.stderr.write('{}: directory not found\n'.format(SKOOLKIT_TESTS))
    sys.exit(1)
sys.path.insert(0, SKOOLKIT_TESTS)

from disassemblytest import check_links

def run(root_dir, options):
    all_files, orphans, missing_files, missing_anchors = check_links(root_dir)

    if options.counts:
        html = img = css = js = 0
        other_files = []
        for fname in all_files:
            if fname.endswith('.html'):
                html += 1
            elif fname.endswith(('.png', '.gif')):
                img += 1
            elif fname.endswith('.css'):
                css += 1
            elif fname.endswith('.js'):
                js += 1
            else:
                other_files.append(fname)
        print('HTML files: {}'.format(html))
        print('Image files: {}'.format(img))
        print('CSS files: {}'.format(css))
        print('JavaScript files: {}'.format(js))
        print('Other files: {}'.format(len(other_files)))
        for fname in other_files:
            print('  {}'.format(fname))

    if options.links:
        for fname in all_files:
            if fname.endswith('.html'):
                links = all_files[fname][1]
                if links:
                    print('{}:'.format(fname))
                    for link_dest in links:
                        print('  -> {}'.format(link_dest))

    print('Orphaned files: {}'.format(len(orphans)))
    for fname in orphans:
        print('  {}'.format(fname))

    print('Links to non-existent files: {}'.format(len(missing_files)))
    for fname, link_dest in missing_files:
        print('  {} -> {}'.format(fname, link_dest))

    print('Links to non-existent anchors: {}'.format(len(missing_anchors)))
    for fname, link_dest in missing_anchors:
        print('  {} -> {}'.format(fname, link_dest))

    return 1 if orphans or missing_files or missing_anchors else 0

###############################################################################
# Begin
###############################################################################
parser = argparse.ArgumentParser(
    usage='check-links.py [options] ROOTDIR',
    description="Check links (to both files and anchors) in all HTML files under ROOTDIR.",
    add_help=False
)
parser.add_argument('root_dir', help=argparse.SUPPRESS, nargs='?')
group = parser.add_argument_group('Options')
group.add_argument('-c', dest='counts', action='store_true',
                   help='Show file counts')
group.add_argument('-s', dest='links', action='store_true',
                   help='Show links')
namespace, unknown_args = parser.parse_known_args()
if unknown_args or namespace.root_dir is None:
    parser.exit(2, parser.format_help())
sys.exit(run(namespace.root_dir, namespace))
