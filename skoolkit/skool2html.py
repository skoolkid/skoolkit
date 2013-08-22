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

import os
from os.path import isfile, isdir, basename, dirname
import posixpath
import shutil
import time
import argparse

from . import PACKAGE_DIR, VERSION, show_package_dir, write, write_line, get_class, SkoolKitError
from .image import ImageWriter
from .skoolhtml import join, FileInfo
from .skoolparser import SkoolParser, CASE_UPPER, CASE_LOWER, BASE_10, BASE_16
from .refparser import RefParser

verbose = True
show_timings = False

SEARCH_DIRS = (
    '',
    'resources',
    os.path.expanduser('~/.skoolkit'),
    '/usr/share/skoolkit',
    os.path.join(PACKAGE_DIR, 'resources')
)
CONFIG = 'Config'

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

def find(fname, search_dir=None):
    if fname is None:
        return
    if search_dir:
        search_dirs = [search_dir]
    else:
        search_dirs = []
    search_dirs.extend(SEARCH_DIRS)
    for f in [join(d, fname) for d in search_dirs]:
        if isfile(f):
            return f

def add_lines(ref_parser, config_specs, section=None):
    for config_spec in config_specs:
        section_name, sep, line = config_spec.partition('/')
        if not sep:
            raise SkoolKitError("Malformed SectionName/Line spec: {0}".format(config_spec))
        if section is None or section_name == section:
            ref_parser.add_line(section_name, line)

def get_config(ref_parser, config_specs):
    add_lines(ref_parser, config_specs, CONFIG)
    return ref_parser.get_dictionary(CONFIG)

def get_colours(colour_specs):
    colours = {}
    for k, v in colour_specs.items():
        if v.startswith('#'):
            hex_rgb = v[1:7]
            if len(hex_rgb) == 3:
                hex_rgb = '{0}{0}{1}{1}{2}{2}'.format(*hex_rgb)
            else:
                hex_rgb = '0' * (6 - len(hex_rgb)) + hex_rgb
            values = [hex_rgb[i:i + 2] for i in range(0, 5, 2)]
            base = 16
        else:
            values = v.split(',')[:3]
            values.extend(['0'] * (3 - len(values)))
            base = 10
        try:
            colours[k] = tuple([int(n, base) for n in values])
        except ValueError:
            raise SkoolKitError("Invalid colour spec: {}={}".format(k, v))
    return colours

def copy_resources(search_dir, root_dir, fnames, dest, themes=None, suffix=None, indent=0):
    if fnames:
        actual_files = []
        for fname in fnames.split(';'):
            files = []
            f = find(fname, search_dir)
            if f:
                files.append(f)
            else:
                raise SkoolKitError('{0}: file not found'.format(fname))
            if themes and fname.endswith(suffix):
                for theme in themes:
                    f = find('{0}-{1}{2}'.format(fname[:-len(suffix)], theme, suffix), search_dir)
                    if f:
                        files.append(f)
            for f in files:
                base_f = basename(f)
                actual_files.append(base_f)
                html_f = posixpath.normpath(join(root_dir, dest, base_f))
                if not isfile(html_f) or os.stat(f).st_mtime > os.stat(html_f).st_mtime:
                    notify('{}Copying {} to {}'.format(indent * ' ', f, html_f))
                    shutil.copy2(f, html_f)
        return ';'.join(actual_files)

def get_prefix(fname):
    if '.' in fname:
        return fname.rsplit('.', 1)[0]
    return fname

def process_file(infile, topdir, files, case, base, pages, config_specs, new_images, css_theme, create_labels, asm_labels):
    reffile = skoolfile = None
    if infile.endswith('.ref'):
        reffile = infile
    else:
        skoolfile = infile

    ref_parser = RefParser()
    reffile_f = find(reffile)
    config = {}
    search_dir = None

    prefix = None
    if reffile:
        if reffile_f is None:
            raise SkoolKitError('{0}: file not found'.format(reffile))
        search_dir = dirname(reffile_f)
        ref_parser.parse(reffile_f)
        config = get_config(ref_parser, config_specs)
        prefix = get_prefix(basename(reffile))
        skoolfile = config.get('SkoolFile', '{0}.skool'.format(prefix))

    if skoolfile == '-':
        skoolfile_f = skoolfile
    else:
        skoolfile_f = find(skoolfile, search_dir)
    if skoolfile_f is None:
        raise SkoolKitError('{0}: file not found'.format(skoolfile))

    if prefix is None:
        if skoolfile_f == '-':
            prefix = 'program'
        else:
            prefix = get_prefix(basename(skoolfile_f))

    if reffile is None and skoolfile != '-':
        search_dir = dirname(skoolfile_f)
        reffile_f = find('{0}.ref'.format(prefix), search_dir)
        if reffile_f:
            ref_parser.parse(reffile_f)
            config = get_config(ref_parser, config_specs)
            search_dir = dirname(reffile_f)

    reffiles = [posixpath.join(search_dir, f) for f in os.listdir(search_dir or '.') if f.startswith(prefix) and f.endswith('.ref')]
    reffiles = [f for f in reffiles if isfile(f)]
    if reffile_f in reffiles:
        reffiles.remove(reffile_f)
    reffiles.sort()
    for oreffile_f in reffiles:
        ref_parser.parse(oreffile_f)
    if reffile_f:
        reffiles.insert(0, reffile_f)
    add_lines(ref_parser, config_specs)

    notify('Using skool file: {0}'.format(skoolfile_f))
    if reffiles:
        if len(reffiles) > 1:
            suffix = 's'
        else:
            suffix = ''
        notify('Using ref file{0}: {1}'.format(suffix, ', '.join(reffiles)))
    else:
        notify('Found no ref file for {0}'.format(skoolfile_f))

    html_writer_class = get_class(config.get('HtmlWriterClass', 'skoolkit.skoolhtml.HtmlWriter'))
    game_dir = config.get('GameDir', prefix)

    # Parse the skool file and initialise the writer
    if skoolfile_f == '-':
        fname = 'standard input'
    else:
        fname = skoolfile_f
    skool_parser = clock(SkoolParser, 'Parsing {0}'.format(fname), skoolfile_f, case=case, base=base, html=True, create_labels=create_labels, asm_labels=asm_labels)
    file_info = FileInfo(topdir, game_dir, new_images)
    colours = get_colours(ref_parser.get_dictionary('Colours'))
    iw_options = ref_parser.get_dictionary('ImageWriter')
    image_writer = ImageWriter(colours, iw_options)
    html_writer = html_writer_class(skool_parser, ref_parser, file_info, image_writer, case)

    # Check that the specified pages exist
    all_page_ids = html_writer.get_page_ids()
    for page_id in pages:
        if page_id not in all_page_ids:
            raise SkoolKitError('Invalid page ID: {0}'.format(page_id))
    pages = pages or all_page_ids

    write_disassembly(html_writer, files, search_dir, pages, css_theme)

def write_disassembly(html_writer, files, search_dir, pages, css_theme):
    game_dir = html_writer.file_info.game_dir
    paths = html_writer.paths
    game_vars = html_writer.game_vars

    # Create the disassembly subdirectory if necessary
    odir = html_writer.file_info.odir
    if not isdir(odir):
        notify('Creating directory {0}'.format(odir))
        os.makedirs(odir)

    # Copy CSS and font files if necessary
    html_writer.set_style_sheet(copy_resources(search_dir, odir, game_vars.get('StyleSheet'), paths.get('StyleSheetPath', ''), css_theme, '.css'))
    copy_resources(search_dir, odir, game_vars.get('Font'), paths.get('FontPath', ''))

    # Write disassembly files
    if 'd' in files:
        clock(html_writer.write_asm_entries, '  Writing disassembly files in {0}'.format(join(game_dir, html_writer.code_path)))

    # Write the memory map files
    if 'm' in files:
        for map_name in html_writer.memory_map_names:
            map_details = html_writer.memory_maps[map_name]
            if html_writer.should_write_map(map_details):
                map_path = html_writer.get_map_path(map_details)
                clock(html_writer.write_map, '  Writing {0}'.format(join(game_dir, map_path)), map_details)

    # Write pages defined in the ref file
    if 'P' in files:
        for page_id in pages:
            page_details = html_writer.pages[page_id]
            copy_resources(search_dir, odir, page_details.get('JavaScript'), paths.get('JavaScriptPath', ''), indent=2)
            clock(html_writer.write_page, '  Writing {0}'.format(join(game_dir, paths[page_id])), page_id)

    # Write other files
    if 'G' in files and html_writer.has_gbuffer():
        clock(html_writer.write_gbuffer, '  Writing {0}'.format(join(game_dir, paths['GameStatusBuffer'])))
    if 'g' in files and html_writer.graphics:
        clock(html_writer.write_graphics, '  Writing {0}'.format(join(game_dir, paths['Graphics'])))
    if 'B' in files and html_writer.graphic_glitches:
        clock(html_writer.write_graphic_glitches, '  Writing {0}'.format(join(game_dir, paths['GraphicGlitches'])))
    if 'c' in files and html_writer.changelog:
        clock(html_writer.write_changelog, '  Writing {0}'.format(join(game_dir, paths['Changelog'])))
    if 'b' in files and html_writer.bugs:
        clock(html_writer.write_bugs, '  Writing {0}'.format(join(game_dir, paths['Bugs'])))
    if 't' in files and html_writer.facts:
        clock(html_writer.write_facts, '  Writing {0}'.format(join(game_dir, paths['Facts'])))
    if 'y' in files and html_writer.glossary:
        clock(html_writer.write_glossary, '  Writing {0}'.format(join(game_dir, paths['Glossary'])))
    if 'p' in files and html_writer.pokes:
        clock(html_writer.write_pokes, '  Writing {0}'.format(join(game_dir, paths['Pokes'])))
    if 'o' in files:
        mode = html_writer.parser.mode
        for code_id, code in html_writer.other_code:
            skoolfile = find(code['Source'], search_dir)
            skool2_parser = clock(html_writer.parser.clone, '  Parsing {0}'.format(skoolfile), skoolfile)
            html_writer2 = html_writer.clone(skool2_parser, code_id)
            map_path = code['Index']
            asm_path = code['Path']
            map_details = {
                'Path': map_path,
                'AsmPath': asm_path,
                'Title': code['Title']
            }
            clock(html_writer2.write_map, '    Writing {0}'.format(join(game_dir, map_path)), map_details)
            clock(html_writer2.write_entries, '    Writing disassembly files in {0}'.format(join(game_dir, asm_path)), asm_path, map_path, code['Header'])

    # Write index.html
    if 'i' in files:
        clock(html_writer.write_index, '  Writing {0}'.format(join(game_dir, paths['GameIndex'])))

def run(files, options):
    if options.output_dir in (None, '.'):
        topdir = ''
    else:
        pdir, bdir = os.path.split(options.output_dir)
        if not bdir:
            pdir, bdir = os.path.split(pdir)
        topdir = join(pdir, bdir)
        if not isdir(topdir):
            # Create the top-level directory
            notify('Creating directory {0}'.format(topdir))
            os.makedirs(topdir)

    for infile in files:
        process_file(infile, topdir, options.files, options.case, options.base, options.pages, options.config_specs, options.new_images, options.themes, options.create_labels, options.asm_labels)

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
    group.add_argument('-l', '--lower', dest='case', action='store_const', const=CASE_LOWER,
                       help="Write the disassembly in lower case")
    group.add_argument('-o', '--rebuild-images', dest='new_images', action='store_true',
                       help="Overwrite existing image files")
    group.add_argument('-p', '--package-dir', dest='package_dir', action='store_true',
                       help="Show path to skoolkit package directory and exit")
    group.add_argument('-P', '--pages', dest='pages', metavar='PAGES',
                       help="Write only these custom pages (when '-w P' is\n"
                            "specified); PAGES should be a comma-separated list of\n"
                            "IDs of pages defined in [Page:*] sections in the ref\n"
                            "file(s)")
    group.add_argument('-q', '--quiet', dest='verbose', action='store_false',
                       help="Be quiet")
    group.add_argument('-t', '--time', dest='show_timings', action='store_true',
                       help="Show timings")
    group.add_argument('-T', '--theme', dest='themes', metavar='THEME', action='append',
                       help="Use this CSS theme; this option may be used multiple\ntimes")
    group.add_argument('-u', '--upper', dest='case', action='store_const', const=CASE_UPPER,
                       help="Write the disassembly in upper case")
    group.add_argument('-V', '--version', action='version',
                       version='SkoolKit {}'.format(VERSION),
                       help='Show SkoolKit version number and exit')
    group.add_argument('-w', '--write', dest='files', metavar='X', default='BbcdGgimoPpty',
                       help="Write only these files, where X is one or more of:\n"
                            "  B = Graphic glitches    m = Memory maps\n"
                            "  b = Bugs                o = Other code\n"
                            "  c = Changelog           P = Custom pages\n"
                            "  d = Disassembly files   p = Pokes\n"
                            "  G = Game status buffer  t = Trivia\n"
                            "  g = Graphics            y = Glossary\n"
                            "  i = Disassembly index")

    start = time.time()
    namespace, unknown_args = parser.parse_known_args(args)
    if namespace.package_dir:
        show_package_dir()
    if unknown_args or not namespace.infiles:
        parser.exit(2, parser.format_help())
    verbose, show_timings = namespace.verbose, namespace.show_timings
    namespace.config_specs = namespace.config_specs or []
    if namespace.pages:
        namespace.pages = namespace.pages.split(',')
    else:
        namespace.pages = []
    run(namespace.infiles, namespace)
    if show_timings:
        notify('Done ({0:0.2f}s)'.format(time.time() - start))
