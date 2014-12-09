#!/usr/bin/env python
import sys
import os

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

def parse_args(args):
    show_counts = False
    show_links = False
    p_args = []
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == '-c':
            show_counts = True
        elif arg == '-s':
            show_links = True
        elif arg.startswith('-'):
            usage()
        else:
            p_args.append(arg)
        i += 1
    if len(p_args) != 1:
        usage()
    return show_counts, show_links, p_args[0]

def usage():
    sys.stderr.write("""Usage: {} [options] ROOTDIR

  Checks links (to both files and anchors) in all HTML files under ROOTDIR.

Available options:
  -c  Show file counts
  -s  Show links
""".format(os.path.basename(sys.argv[0])))
    sys.exit(1)

show_counts, show_links, root_dir = parse_args(sys.argv[1:])
all_files, orphans, missing_files, missing_anchors = check_links(root_dir)

if show_counts:
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

if show_links:
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
