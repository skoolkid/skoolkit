# -*- coding: utf-8 -*-

# Copyright 2008-2015 Richard Dymond (rjdymond@gmail.com)
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

import sys
import os
from os.path import isfile, isdir, basename, dirname
import shutil
import time
import argparse
try:
    from StringIO import StringIO
except ImportError:         # pragma: no cover
    from io import StringIO # pragma: no cover

from skoolkit import defaults, SkoolKitError, show_package_dir, write, write_line, get_class, normpath, PACKAGE_DIR, VERSION
from skoolkit.refparser import RefParser
from skoolkit.skoolhtml import FileInfo
from skoolkit.skoolparser import SkoolParser, CASE_UPPER, CASE_LOWER, BASE_10, BASE_16

SEARCH_DIRS = (
    '',
    'resources',
    os.path.expanduser('~/.skoolkit'),
    os.path.join(PACKAGE_DIR, 'resources')
)

SEARCH_DIRS_MSG = """
skool2html.py searches the following directories for skool files, ref files,
CSS files, JavaScript files, font files, and files listed in the [Resources]
section of the ref file:

""".lstrip()

def show_search_dirs():
    write(SEARCH_DIRS_MSG)
    prefix = '- '
    write_line(prefix + 'The directory that contains the skool or ref file named on the command line')
    for search_dir in SEARCH_DIRS:
        if not search_dir:
            search_dir = 'The current working directory'
        elif not os.path.split(search_dir)[0]:
            search_dir = os.path.join('.', search_dir)
        else:
            search_dir = os.path.normpath(search_dir)
        write_line(prefix + search_dir)
    write_line(prefix + 'Any other directories specified by the -S/--search option')
    sys.exit(0)

def show_ref_file():
    write(defaults.REF_FILE)
    sys.exit(0)

def show_ref_sections(prefix):
    write(defaults.get_sections(prefix))
    sys.exit(0)

def notify(notice):
    if verbose:
        write_line(notice)

def clock(operation, prefix, *args, **kwargs):
    if verbose:
        if show_timings:
            write('{0} '.format(prefix))
            go = time.time()
        else:
            write_line(prefix)
    result = operation(*args, **kwargs)
    if verbose and show_timings:
        notify('({0:0.2f}s)'.format(time.time() - go))
    return result

def find(fname, extra_search_dirs, first_search_dir=None):
    if first_search_dir:
        search_dirs = [first_search_dir]
    else:
        search_dirs = []
    search_dirs.extend(SEARCH_DIRS)
    if extra_search_dirs:
        search_dirs.extend(extra_search_dirs)
    for f in [os.path.join(d, fname) for d in search_dirs]:
        if isfile(f):
            return f

def add_lines(ref_parser, config_specs, section=None):
    for config_spec in config_specs:
        section_name, sep, line = config_spec.partition('/')
        if not sep:
            raise SkoolKitError("Malformed SectionName/Line spec: {0}".format(config_spec))
        if section is None or section_name == section:
            ref_parser.add_line(section_name, line)

def copy_resource(fname, root_dir, dest_dir, indent=0):
    base_f = basename(fname)
    dest_f = normpath(root_dir, dest_dir, base_f)
    if not isfile(dest_f) or os.stat(fname).st_mtime > os.stat(dest_f).st_mtime:
        fname_n = normpath(fname)
        dest_d = dirname(dest_f)
        if isfile(dest_d):
            raise SkoolKitError("Cannot copy {0} to {1}: {1} is not a directory".format(fname_n, normpath(dest_dir)))
        elif not isdir(dest_d):
            os.makedirs(dest_d)
        notify('{}Copying {} to {}'.format(indent * ' ', fname_n, dest_f))
        shutil.copy2(fname, dest_f)

def copy_resources(search_dir, extra_search_dirs, root_dir, fnames, dest_dir, themes=(), suffix=None, single_css=None, indent=0):
    if not fnames:
        return

    files = []

    for fname in fnames.split(';'):
        f = find(fname, extra_search_dirs, search_dir)
        if f:
            files.append(f)
        else:
            raise SkoolKitError('{}: file not found'.format(normpath(fname)))
        if themes and fname.endswith(suffix):
            for theme in themes:
                f = find('{}-{}{}'.format(fname[:-len(suffix)], theme, suffix), extra_search_dirs, search_dir)
                if f:
                    files.append(f)

    for theme in themes:
        f = find('{}{}'.format(theme, suffix), extra_search_dirs, search_dir)
        if f:
            files.append(f)

    if single_css:
        dest_css = normpath(root_dir, dest_dir, single_css)
        if isdir(dest_css):
            raise SkoolKitError("Cannot write CSS file '{}': {} already exists and is a directory".format(normpath(single_css), dest_css))
        with open(dest_css, 'w') as css:
            for f in files:
                notify('{}Appending {} to {}'.format(indent * ' ', normpath(f), dest_css))
                with open(f) as src:
                    for line in src:
                        css.write(line)
                css.write('\n')
        return single_css

    for f in files:
        copy_resource(f, root_dir, dest_dir, indent)
    return ';'.join([basename(f) for f in files])

def get_prefix(fname):
    if '.' in fname:
        return fname.rsplit('.', 1)[0]
    return fname

def process_file(infile, topdir, options):
    extra_search_dirs = options.search
    case = options.case
    pages = options.pages
    stdin = False

    skoolfile_f = reffile_f = None
    ref_search_dir = ''
    if infile.endswith('.ref'):
        reffile_f = find(infile, extra_search_dirs)
        if reffile_f:
            ref_search_dir = dirname(reffile_f)
            prefix = get_prefix(basename(reffile_f))
    elif infile == '-':
        stdin = True
        skoolfile_f = infile
        prefix = 'program'
    else:
        skoolfile_f = find(infile, extra_search_dirs)
        if skoolfile_f:
            ref_search_dir = dirname(skoolfile_f)
            prefix = get_prefix(basename(skoolfile_f))
            reffile_f = find('{}.ref'.format(prefix), extra_search_dirs, ref_search_dir)
            if reffile_f:
                ref_search_dir = dirname(reffile_f)
    if skoolfile_f is reffile_f is None:
        raise SkoolKitError('{}: file not found'.format(normpath(infile)))

    reffiles = []
    if reffile_f:
        reffiles.append(normpath(reffile_f))
    base_ref = prefix + '.ref'
    for f in sorted(os.listdir(ref_search_dir or '.')):
        if isfile(os.path.join(ref_search_dir, f)) and f.endswith('.ref') and f.startswith(prefix) and f != base_ref:
            reffiles.append(normpath(ref_search_dir, f))
    ref_parser = RefParser()
    ref_parser.parse(StringIO(defaults.get_section('Config')))
    config = ref_parser.get_dictionary('Config')
    for oreffile_f in reffiles:
        ref_parser.parse(oreffile_f)
    add_lines(ref_parser, options.config_specs, 'Config')
    config.update(ref_parser.get_dictionary('Config'))
    extra_reffiles = config.get('RefFiles')
    if extra_reffiles:
        for f in extra_reffiles.split(';'):
            if isfile(os.path.join(ref_search_dir, f)):
                ref_f = normpath(ref_search_dir, f)
                if ref_f not in reffiles:
                    reffiles.append(ref_f)
                    ref_parser.parse(ref_f)
    add_lines(ref_parser, options.config_specs)

    if skoolfile_f is None:
        skoolfile = config.get('SkoolFile', '{}.skool'.format(prefix))
        skoolfile_f = find(skoolfile, extra_search_dirs, ref_search_dir)
        if skoolfile_f is None:
            raise SkoolKitError('{}: file not found'.format(normpath(skoolfile)))

    skoolfile_n = normpath(skoolfile_f)
    if not stdin:
        notify('Using skool file: {}'.format(skoolfile_n))
    if reffiles:
        if len(reffiles) > 1:
            suffix = 's'
        else:
            suffix = ''
        notify('Using ref file{0}: {1}'.format(suffix, ', '.join(reffiles)))
    elif not stdin:
        notify('Found no ref file for {}'.format(skoolfile_n))

    html_writer_class = get_class(config['HtmlWriterClass'])
    game_dir = config.get('GameDir', prefix)

    # Parse the skool file and initialise the writer
    if stdin:
        fname = 'skool file from standard input'
    else:
        fname = skoolfile_f
    skool_parser = clock(SkoolParser, 'Parsing {}'.format(fname), skoolfile_f, case=case, base=options.base, html=True, create_labels=options.create_labels, asm_labels=options.asm_labels)
    file_info = FileInfo(topdir, game_dir, options.new_images)
    html_writer = html_writer_class(skool_parser, ref_parser, file_info, case)

    # Check that the specified pages exist
    all_page_ids = html_writer.get_page_ids()
    for page_id in pages:
        if page_id not in all_page_ids:
            raise SkoolKitError('Invalid page ID: {0}'.format(page_id))
    pages = pages or all_page_ids

    write_disassembly(html_writer, options.files, ref_search_dir, extra_search_dirs, pages, options.themes, options.single_css)

def write_disassembly(html_writer, files, search_dir, extra_search_dirs, pages, css_themes, single_css):
    game_dir = html_writer.file_info.game_dir
    paths = html_writer.paths
    game_vars = html_writer.game_vars

    # Create the disassembly subdirectory if necessary
    odir = html_writer.file_info.odir
    if not isdir(odir):
        notify('Creating directory {0}'.format(odir))
        os.makedirs(odir)

    # Copy CSS, JavaScript and font files if necessary
    html_writer.set_style_sheet(copy_resources(search_dir, extra_search_dirs, odir, game_vars.get('StyleSheet'), paths.get('StyleSheetPath', ''), css_themes, '.css', single_css))
    js_path = paths.get('JavaScriptPath', '')
    copy_resources(search_dir, extra_search_dirs, odir, game_vars.get('JavaScript'), js_path)
    copy_resources(search_dir, extra_search_dirs, odir, game_vars.get('Font'), paths.get('FontPath', ''))

    # Copy resources named in the [Resources] section
    resources = html_writer.ref_parser.get_dictionary('Resources')
    for f, dest_dir in resources.items():
        fname = find(f, extra_search_dirs, search_dir)
        if not fname:
            raise SkoolKitError('Cannot copy resource "{}": file not found'.format(normpath(f)))
        copy_resource(fname, odir, dest_dir)

    # Write disassembly files
    if 'd' in files:
        clock(html_writer.write_asm_entries, '  Writing disassembly files in {}'.format(normpath(game_dir, html_writer.code_path)))

    # Write the memory map files
    if 'm' in files:
        for map_name in html_writer.main_memory_maps:
            clock(html_writer.write_map, '  Writing {}'.format(normpath(game_dir, paths[map_name])), map_name)

    # Write pages defined in the ref file
    if 'P' in files:
        for page_id in pages:
            page_details = html_writer.pages[page_id]
            copy_resources(search_dir, extra_search_dirs, odir, page_details.get('JavaScript'), js_path, indent=2)
            clock(html_writer.write_page, '  Writing {}'.format(normpath(game_dir, paths[page_id])), page_id)

    # Write other files
    if 'B' in files and html_writer.graphic_glitches:
        clock(html_writer.write_graphic_glitches, '  Writing {}'.format(normpath(game_dir, paths['GraphicGlitches'])))
    if 'c' in files and html_writer.changelog:
        clock(html_writer.write_changelog, '  Writing {}'.format(normpath(game_dir, paths['Changelog'])))
    if 'b' in files and html_writer.bugs:
        clock(html_writer.write_bugs, '  Writing {}'.format(normpath(game_dir, paths['Bugs'])))
    if 't' in files and html_writer.facts:
        clock(html_writer.write_facts, '  Writing {}'.format(normpath(game_dir, paths['Facts'])))
    if 'y' in files and html_writer.glossary:
        clock(html_writer.write_glossary, '  Writing {}'.format(normpath(game_dir, paths['Glossary'])))
    if 'p' in files and html_writer.pokes:
        clock(html_writer.write_pokes, '  Writing {}'.format(normpath(game_dir, paths['Pokes'])))
    if 'o' in files:
        for code_id, code in html_writer.other_code:
            skoolfile = find(code['Source'], extra_search_dirs, search_dir)
            if not skoolfile:
                raise SkoolKitError('{}: file not found'.format(normpath(code['Source'])))
            skool2_parser = clock(html_writer.parser.clone, '  Parsing {0}'.format(skoolfile), skoolfile)
            html_writer2 = html_writer.clone(skool2_parser, code_id)
            map_name = code['IndexPageId']
            map_path = paths[map_name]
            asm_path = paths[code['CodePathId']]
            clock(html_writer2.write_map, '    Writing {}'.format(normpath(game_dir, map_path)), map_name)
            clock(html_writer2.write_entries, '    Writing disassembly files in {}'.format(normpath(game_dir, asm_path)), asm_path, map_path)

    # Write index.html
    if 'i' in files:
        clock(html_writer.write_index, '  Writing {}'.format(normpath(game_dir, paths['GameIndex'])))

def run(files, options):
    if options.output_dir in (None, '.'):
        topdir = ''
    else:
        topdir = normpath(options.output_dir)
    for infile in files:
        process_file(infile, topdir, options)

def main(args):
    global verbose, show_timings

    parser = argparse.ArgumentParser(
        usage='skool2html.py [options] FILE [FILE...]',
        description="Convert skool files and ref files to HTML. FILE may be a regular file, or '-'\n"
                    "for standard input.",
        formatter_class=argparse.RawTextHelpFormatter,
        add_help=False
    )
    parser.add_argument('infiles', help=argparse.SUPPRESS, nargs='*')
    group = parser.add_argument_group('Options')
    group.add_argument('-a', '--asm-labels', dest='asm_labels', action='store_true',
                       help="Use ASM labels")
    group.add_argument('-c', '--config', dest='config_specs', metavar='S/L', action='append',
                       help="Add the line 'L' to the ref file section 'S'; this\n"
                            "option may be used multiple times")
    group.add_argument('-C', '--create-labels', dest='create_labels', action='store_true',
                       help="Create default labels for unlabelled instructions")
    group.add_argument('-d', '--output-dir', dest='output_dir', metavar='DIR',
                       help="Write files in this directory (default is '.')")
    group.add_argument('-D', '--decimal', dest='base', action='store_const', const=BASE_10,
                       help="Write the disassembly in decimal")
    group.add_argument('-H', '--hex', dest='base', action='store_const', const=BASE_16,
                       help="Write the disassembly in hexadecimal")
    group.add_argument('-j', '--join-css', dest='single_css', metavar='NAME',
                       help="Concatenate CSS files into a single file with this name")
    group.add_argument('-l', '--lower', dest='case', action='store_const', const=CASE_LOWER,
                       help="Write the disassembly in lower case")
    group.add_argument('-o', '--rebuild-images', dest='new_images', action='store_true',
                       help="Overwrite existing image files")
    group.add_argument('-p', '--package-dir', dest='package_dir', action='store_true',
                       help="Show path to skoolkit package directory and exit")
    group.add_argument('-P', '--pages', dest='pages', metavar='PAGES',
                       help="Write only these custom pages (when using '--write P');\n"
                            "PAGES is a comma-separated list of page IDs")
    group.add_argument('-q', '--quiet', dest='verbose', action='store_false',
                       help="Be quiet")
    group.add_argument('-r', '--ref-sections', dest='ref_sections', metavar='PREFIX',
                       help="Show default ref file sections whose names start with\n"
                            "PREFIX and exit")
    group.add_argument('-R', '--ref-file', dest='ref_file', action='store_true',
                       help="Show the entire default ref file and exit")
    group.add_argument('-s', '--search-dirs', dest='search_dirs', action='store_true',
                       help="Show the locations skool2html.py searches for resources")
    group.add_argument('-S', '--search', dest='search', metavar='DIR', action='append',
                       help="Add this directory to the resource search path; this\n"
                            "option may be used multiple times")
    group.add_argument('-t', '--time', dest='show_timings', action='store_true',
                       help="Show timings")
    group.add_argument('-T', '--theme', dest='themes', metavar='THEME', action='append', default=[],
                       help="Use this CSS theme; this option may be used multiple\ntimes")
    group.add_argument('-u', '--upper', dest='case', action='store_const', const=CASE_UPPER,
                       help="Write the disassembly in upper case")
    group.add_argument('-V', '--version', action='version',
                       version='SkoolKit {}'.format(VERSION),
                       help='Show SkoolKit version number and exit')
    group.add_argument('-w', '--write', dest='files', metavar='X', default='BbcdGgimoPpty',
                       help="Write only these files, where X is one or more of:\n"
                            "  B = Graphic glitches    o = Other code\n"
                            "  b = Bugs                P = Custom pages\n"
                            "  c = Changelog           p = Pokes\n"
                            "  d = Disassembly files   t = Trivia\n"
                            "  i = Disassembly index   y = Glossary\n"
                            "  m = Memory maps\n")
    group.add_argument('-W', '--writer', dest='writer', metavar='CLASS',
                       help="Specify the HTML writer class to use; shorthand for\n"
                            "'--config Config/HtmlWriterClass=CLASS'")

    start = time.time()
    namespace, unknown_args = parser.parse_known_args(args)
    if namespace.package_dir:
        show_package_dir()
    if namespace.search_dirs:
        show_search_dirs()
    if namespace.ref_file:
        show_ref_file()
    if namespace.ref_sections is not None:
        show_ref_sections(namespace.ref_sections)
    if unknown_args or not namespace.infiles:
        parser.exit(2, parser.format_help())
    verbose, show_timings = namespace.verbose, namespace.show_timings
    namespace.config_specs = namespace.config_specs or []
    if namespace.writer:
        namespace.config_specs.append('Config/HtmlWriterClass={}'.format(namespace.writer))
    if namespace.pages:
        namespace.pages = namespace.pages.split(',')
    else:
        namespace.pages = []
    run(namespace.infiles, namespace)
    if show_timings:
        notify('Done ({0:0.2f}s)'.format(time.time() - start))
