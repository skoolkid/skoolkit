# Copyright 2008-2018 Richard Dymond (rjdymond@gmail.com)
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

import glob
import sys
import os
from os.path import isfile, isdir, basename, dirname
import shutil
import time
import argparse
from io import StringIO

from skoolkit import (defaults, SkoolKitError, find_file, show_package_dir,
                      write, write_line, get_class, normpath, PACKAGE_DIR,
                      VERSION, BASE_10, BASE_16, CASE_UPPER, CASE_LOWER)
from skoolkit.config import get_config, show_config, update_options
from skoolkit.refparser import RefParser
from skoolkit.skoolhtml import FileInfo
from skoolkit.skoolparser import SkoolParser

SEARCH_DIRS = (
    '',
    'resources',
    os.path.expanduser('~/.skoolkit'),
    os.path.join(PACKAGE_DIR, 'resources')
)

SEARCH_DIRS_MSG = """
skool2html.py searches the following directories for CSS files, JavaScript
files, font files, and files listed in the [Resources] section of the ref file:

""".lstrip()

def show_search_dirs():
    write(SEARCH_DIRS_MSG)
    prefix = '- '
    write_line(prefix + 'The directory that contains the skool file named on the command line')
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

def _get_search_dirs(extra_search_dirs, first_search_dir=None):
    if first_search_dir:
        search_dirs = [first_search_dir]
    else:
        search_dirs = []
    search_dirs.extend(SEARCH_DIRS)
    search_dirs.extend(extra_search_dirs)
    return search_dirs

def find(fname, extra_search_dirs, first_search_dir=None):
    return find_file(fname, _get_search_dirs(extra_search_dirs, first_search_dir))

def add_lines(ref_parser, config_specs, section=None):
    for config_spec in config_specs:
        section_name, sep, line = config_spec.partition('/')
        if not sep:
            raise SkoolKitError("Malformed SectionName/Line spec: {0}".format(config_spec))
        if section is None or section_name == section:
            ref_parser.add_line(section_name, line)

def copy_resource(fname, root_dir, dest_dir):
    base_f = basename(fname)
    dest_f = normpath(root_dir, dest_dir, base_f)
    if not isfile(dest_f) or os.stat(fname).st_mtime > os.stat(dest_f).st_mtime:
        fname_n = normpath(fname)
        dest_d = dirname(dest_f)
        if isfile(dest_d):
            raise SkoolKitError("Cannot copy {0} to {1}: {1} is not a directory".format(fname_n, normpath(dest_dir)))
        if not isdir(dest_d):
            os.makedirs(dest_d)
        notify('Copying {} to {}'.format(fname_n, normpath(dest_dir, base_f)))
        shutil.copy2(fname, dest_f)

def copy_resources(search_dir, extra_search_dirs, root_dir, fnames, dest_dir, themes=(), suffix=None, single_css=None):
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
                notify('Appending {} to {}'.format(normpath(f), dest_css))
                with open(f) as src:
                    for line in src:
                        css.write(line)
                css.write('\n')
        return single_css

    for f in files:
        copy_resource(f, root_dir, dest_dir)
    return ';'.join([basename(f) for f in files])

def parse_ref_files(reffiles, ref_parser, fnames, search_dir=''):
    for f in fnames:
        if f:
            ref_f = normpath(search_dir, f)
            if not isfile(os.path.join(search_dir, f)):
                raise SkoolKitError('{}: file not found'.format(ref_f))
            if ref_f not in reffiles:
                reffiles.append(ref_f)
                ref_parser.parse(ref_f)

def run(infiles, options):
    ref_search_dir = module_path = ''
    skoolfile = infiles[0]
    if skoolfile == '-':
        fname = 'skool file from standard input'
        prefix = 'program'
    elif isfile(skoolfile):
        fname = normpath(skoolfile)
        ref_search_dir = module_path = dirname(skoolfile)
        prefix = basename(skoolfile).rsplit('.', 1)[0]
    else:
        raise SkoolKitError('{}: file not found'.format(normpath(skoolfile)))

    reffiles = sorted(normpath(f) for f in glob.glob(os.path.join(ref_search_dir, prefix + '*.ref')))
    main_ref = normpath(ref_search_dir, prefix + '.ref')
    if main_ref in reffiles:
        reffiles.remove(main_ref)
        reffiles.insert(0, main_ref)
    ref_parser = RefParser()
    ref_parser.parse(StringIO(defaults.get_section('Config')))
    config = ref_parser.get_dictionary('Config')
    for oreffile_f in reffiles:
        ref_parser.parse(oreffile_f)
    add_lines(ref_parser, options.config_specs, 'Config')
    config.update(ref_parser.get_dictionary('Config'))
    parse_ref_files(reffiles, ref_parser, config.get('RefFiles', '').split(';'), ref_search_dir)
    parse_ref_files(reffiles, ref_parser, infiles[1:])
    add_lines(ref_parser, options.config_specs)

    if reffiles:
        if len(reffiles) > 1:
            suffix = 's'
        else:
            suffix = ''
        notify('Using ref file{0}: {1}'.format(suffix, ', '.join(reffiles)))
    elif skoolfile != '-':
        notify('Found no ref file for ' + normpath(skoolfile))

    html_writer_class = get_class(config['HtmlWriterClass'], module_path)
    game_dir = config.get('GameDir', prefix)

    # Parse the skool file and initialise the writer
    skool_parser = clock(SkoolParser, 'Parsing {}'.format(fname), skoolfile, case=options.case, base=options.base,
                         html=True, create_labels=options.create_labels, asm_labels=options.asm_labels,
                         variables=options.variables)
    if options.output_dir == '.':
        topdir = ''
    else:
        topdir = normpath(options.output_dir)
    file_info = FileInfo(topdir, game_dir, options.new_images)
    html_writer = html_writer_class(skool_parser, ref_parser, file_info)

    # Check that the specified pages exist
    all_page_ids = html_writer.get_page_ids()
    for page_id in options.pages:
        if page_id not in all_page_ids:
            raise SkoolKitError('Invalid page ID: {0}'.format(page_id))
    pages = options.pages or all_page_ids

    write_disassembly(html_writer, options.files, ref_search_dir, options.search, pages, options.themes, options.single_css)

def write_disassembly(html_writer, files, search_dir, extra_search_dirs, pages, css_themes, single_css):
    paths = html_writer.paths
    game_vars = html_writer.game_vars

    # Create the disassembly subdirectory if necessary
    odir = html_writer.file_info.odir
    if not isdir(odir):
        os.makedirs(odir)
    notify('Output directory: ' + odir)

    # Copy CSS, JavaScript and font files if necessary
    html_writer.set_style_sheet(copy_resources(search_dir, extra_search_dirs, odir, game_vars.get('StyleSheet'), paths.get('StyleSheetPath', ''), css_themes, '.css', single_css))
    js_path = paths.get('JavaScriptPath', '')
    copy_resources(search_dir, extra_search_dirs, odir, game_vars.get('JavaScript'), js_path)
    copy_resources(search_dir, extra_search_dirs, odir, game_vars.get('Font'), paths.get('FontPath', ''))

    # Copy resources named in the [Resources] section
    resources = html_writer.ref_parser.get_dictionary('Resources')
    search_dirs = _get_search_dirs(extra_search_dirs, search_dir)
    for f, dest_dir in resources.items():
        fnames = []
        for d in search_dirs:
            fnames.extend(glob.glob(os.path.join(d, f)))
        if not fnames:
            raise SkoolKitError('Cannot copy resource "{}": file not found'.format(normpath(f)))
        for fname in fnames:
            copy_resource(fname, odir, dest_dir)

    # Write disassembly files
    if 'd' in files:
        if html_writer.asm_single_page_template:
            message = 'Writing ' + normpath(paths['AsmSinglePage'])
        else:
            message = 'Writing disassembly files in ' + normpath(html_writer.code_path)
        clock(html_writer.write_asm_entries, message)

    # Write the memory map files
    if 'm' in files:
        for map_name in html_writer.main_memory_maps:
            clock(html_writer.write_map, 'Writing ' + normpath(paths[map_name]), map_name)

    # Write pages defined by [Page:*] sections
    if 'P' in files:
        for page_id in pages:
            page_details = html_writer.pages[page_id]
            copy_resources(search_dir, extra_search_dirs, odir, page_details.get('JavaScript'), js_path)
            clock(html_writer.write_page, 'Writing ' + normpath(paths[page_id]), page_id)

    # Write other code files
    if 'o' in files:
        for code_id, code in html_writer.other_code:
            skoolfile = find(code['Source'], extra_search_dirs, search_dir)
            if not skoolfile:
                raise SkoolKitError('{}: file not found'.format(normpath(code['Source'])))
            skool2_parser = clock(html_writer.parser.clone, 'Parsing ' + normpath(skoolfile), skoolfile)
            html_writer2 = html_writer.clone(skool2_parser, code_id)
            map_name = code['IndexPageId']
            map_path = paths[map_name]
            asm_path = paths[code['CodePathId']]
            clock(html_writer2.write_map, 'Writing ' + normpath(map_path), map_name)
            if html_writer.asm_single_page_template:
                message = 'Writing ' + normpath(paths[code['AsmSinglePageId']])
            else:
                message = 'Writing disassembly files in ' + normpath(asm_path)
            clock(html_writer2.write_entries, message, asm_path, map_path)

    # Write index.html
    if 'i' in files:
        clock(html_writer.write_index, 'Writing ' + normpath(paths['GameIndex']))

def main(args):
    global verbose, show_timings

    config = get_config('skool2html')

    parser = argparse.ArgumentParser(
        usage='skool2html.py [options] SKOOLFILE [REFFILE...]',
        description="Convert a skool file and ref files to HTML. SKOOLFILE may be a regular file, or\n"
                    "'-' for standard input.",
        formatter_class=argparse.RawTextHelpFormatter,
        add_help=False
    )
    parser.add_argument('infiles', help=argparse.SUPPRESS, nargs='*')
    group = parser.add_argument_group('Options')
    group.add_argument('-1', '--asm-one-page', dest='asm_one_page', action='store_const', const=1, default=config['AsmOnePage'],
                       help="Write all routines and data blocks to a single page.")
    group.add_argument('-a', '--asm-labels', dest='asm_labels', action='store_const', const=1, default=config['AsmLabels'],
                       help="Use ASM labels.")
    group.add_argument('-c', '--config', dest='config_specs', metavar='S/L', action='append', default=[],
                       help="Add the line 'L' to the ref file section 'S'. This\n"
                            "option may be used multiple times.")
    group.add_argument('-C', '--create-labels', dest='create_labels', action='store_const', const=1, default=config['CreateLabels'],
                       help="Create default labels for unlabelled instructions.")
    group.add_argument('-d', '--output-dir', dest='output_dir', metavar='DIR', default=config['OutputDir'],
                       help="Write files in this directory (default is '.').")
    group.add_argument('-D', '--decimal', dest='base', action='store_const', const=BASE_10, default=config['Base'],
                       help="Write the disassembly in decimal.")
    group.add_argument('-H', '--hex', dest='base', action='store_const', const=BASE_16, default=config['Base'],
                       help="Write the disassembly in hexadecimal.")
    group.add_argument('-I', '--ini', dest='params', metavar='p=v', action='append', default=[],
                       help="Set the value of the configuration parameter 'p' to\n'v'. This option may be used multiple times.")
    group.add_argument('-j', '--join-css', dest='single_css', metavar='NAME', default=config['JoinCss'],
                       help="Concatenate CSS files into a single file with this name.")
    group.add_argument('-l', '--lower', dest='case', action='store_const', const=CASE_LOWER, default=config['Case'],
                       help="Write the disassembly in lower case.")
    group.add_argument('-o', '--rebuild-images', dest='new_images', action='store_const', const=1, default=config['RebuildImages'],
                       help="Overwrite existing image files.")
    group.add_argument('-p', '--package-dir', dest='package_dir', action='store_true',
                       help="Show path to skoolkit package directory and exit.")
    group.add_argument('-P', '--pages', dest='pages', metavar='PAGES',
                       help="Write only these pages (when using '--write P').\n"
                            "PAGES is a comma-separated list of page IDs.")
    group.add_argument('-q', '--quiet', dest='quiet', action='store_const', const=1, default=config['Quiet'],
                       help="Be quiet.")
    group.add_argument('-r', '--ref-sections', dest='ref_sections', metavar='PREFIX',
                       help="Show default ref file sections whose names start with\n"
                            "PREFIX and exit.")
    group.add_argument('-R', '--ref-file', dest='ref_file', action='store_true',
                       help="Show the entire default ref file and exit.")
    group.add_argument('-s', '--search-dirs', dest='search_dirs', action='store_true',
                       help="Show the locations skool2html.py searches for resources.")
    group.add_argument('-S', '--search', dest='search', metavar='DIR', action='append', default=config['Search'],
                       help="Add this directory to the resource search path. This\n"
                            "option may be used multiple times.")
    group.add_argument('--show-config', dest='show_config', action='store_true',
                       help="Show configuration parameter values.")
    group.add_argument('-t', '--time', dest='show_timings', action='store_const', const=1, default=config['Time'],
                       help="Show timings.")
    group.add_argument('-T', '--theme', dest='themes', metavar='THEME', action='append', default=config['Theme'],
                       help="Use this CSS theme. This option may be used multiple\ntimes.")
    group.add_argument('-u', '--upper', dest='case', action='store_const', const=CASE_UPPER, default=config['Case'],
                       help="Write the disassembly in upper case.")
    group.add_argument('--var', dest='variables', metavar='name=value', action='append', default=[],
                       help="Define a variable that can be used by @if, #IF and #MAP.\nThis option may be used multiple times.")
    group.add_argument('-V', '--version', action='version',
                       version='SkoolKit {}'.format(VERSION),
                       help='Show SkoolKit version number and exit.')
    group.add_argument('-w', '--write', dest='files', metavar='X', default='dimoP',
                       help="Write only these files, where X is one or more of:\n"
                            "  d = Disassembly files   o = Other code\n"
                            "  i = Disassembly index   P = Other pages\n"
                            "  m = Memory maps\n")
    group.add_argument('-W', '--writer', dest='writer', metavar='CLASS',
                       help="Specify the HTML writer class to use; shorthand for\n"
                            "'--config Config/HtmlWriterClass=CLASS'.")

    start = time.time()
    namespace, unknown_args = parser.parse_known_args(args)
    if namespace.show_config:
        show_config('skool2html', config)
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
    update_options('skool2html', namespace, namespace.params)
    verbose, show_timings = not namespace.quiet, namespace.show_timings
    if namespace.asm_one_page:
        namespace.config_specs.append('Game/AsmSinglePageTemplate=AsmAllInOne')
    if namespace.writer:
        namespace.config_specs.append('Config/HtmlWriterClass={}'.format(namespace.writer))
    if namespace.pages:
        namespace.pages = namespace.pages.split(',')
    else:
        namespace.pages = []
    run(namespace.infiles, namespace)
    if show_timings:
        notify('Done ({0:0.2f}s)'.format(time.time() - start))
