# Copyright 2017-2019 Richard Dymond (rjdymond@gmail.com)
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
from os.path import expanduser

from skoolkit import find_file
from skoolkit.refparser import RefParser

COMMANDS = {
    'sna2ctl' : {
        'Dictionary': ('', ''),
        'Hex': (0, 'ctl_hex'),
        'TextChars': ('0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ !"$%&\'()*+,-./:;<=>?[]', ''),
        'TextMinLengthCode': (12, ''),
        'TextMinLengthData': (3, '')
    },
    'sna2skool': {
        'Base': (10, 'base'),
        'Case': (2, 'case'),
        'CommentWidthMin': (10, ''),
        'DefbMod': (1, ''),
        'DefbSize': (8, ''),
        'DefbZfill': (0, ''),
        'DefmSize': (66, ''),
        'InstructionWidth': (13, ''),
        'LineWidth': (79, 'line_width'),
        'ListRefs': (1, ''),
        'Text': (0, ''),
        'EntryPointRef': ('This entry point is used by the routine at {ref}.', ''),
        'EntryPointRefs': ('This entry point is used by the routines at {refs} and {ref}.', ''),
        'Ref': ('Used by the routine at {ref}.', ''),
        'Refs': ('Used by the routines at {refs} and {ref}.', ''),
        'Semicolons': ('c', ''),
        'Title-b': ('Data block at {address}', ''),
        'Title-c': ('Routine at {address}', ''),
        'Title-g': ('Game status buffer entry at {address}', ''),
        'Title-i': ('Ignored', ''),
        'Title-s': ('Unused', ''),
        'Title-t': ('Message at {address}', ''),
        'Title-u': ('Unused', ''),
        'Title-w': ('Data block at {address}', '')
    },
    'skool2ctl': {
        'Hex': (0, 'write_hex'),
        'KeepLines': (0, 'keep_lines'),
        'PreserveBase': (0, 'preserve_base')
    },
    'skool2html': {
        'AsmLabels': (0, 'asm_labels'),
        'AsmOnePage': (0, 'asm_one_page'),
        'Base': (0, 'base'),
        'Case': (0, 'case'),
        'CreateLabels': (0, 'create_labels'),
        'JoinCss': ('', 'single_css'),
        'OutputDir': ('.', 'output_dir'),
        'Quiet': (0, 'quiet'),
        'RebuildImages': (0, 'new_images'),
        'Search': ((), 'search'),
        'Theme': ((), 'themes'),
        'Time': (0, 'show_timings')
    },
    'skool2asm': {
        'Base': (0, 'base'),
        'Case': (0, 'case'),
        'CreateLabels': (0, 'create_labels'),
        'Quiet': (0, 'quiet'),
        'Templates': ('', 'templates'),
        'Warnings': (1, 'warn')
    }
}

def get_config(name):
    config = {}
    for k, v in COMMANDS.get(name, {}).items():
        if isinstance(v[0], tuple):
            config[k] = []
        else:
            config[k] = v[0]
    skoolkit_ini = find_file('skoolkit.ini', ('', expanduser('~/.skoolkit')))
    if skoolkit_ini:
        ref_parser = RefParser()
        ref_parser.parse(skoolkit_ini)
        for k, v in ref_parser.get_dictionary(name).items():
            if isinstance(config.get(k), int):
                try:
                    config[k] = int(v)
                except ValueError:
                    pass
            elif isinstance(config.get(k), list):
                config[k] = [s for s in v.split(',') if s]
            else:
                config[k] = v
    return config

def update_options(name, options, specs, config=None):
    def_config = COMMANDS.get(name, {})
    for spec in specs:
        param, sep, value = spec.partition('=')
        if sep and param in def_config:
            def_value, attr_name = def_config[param]
            try:
                if isinstance(def_value, int):
                    value = int(value)
                elif isinstance(def_value, tuple):
                    value = [s for s in value.split(',') if s]
                if attr_name:
                    setattr(options, attr_name, value)
                if config:
                    config[param] = value
            except ValueError:
                pass
    if config:
        for param, (def_value, attr_name) in def_config.items():
            if attr_name and not hasattr(options, attr_name):
                setattr(options, attr_name, config[param])

def show_config(section_name, config):
    print('[{}]'.format(section_name))
    for name in sorted(config):
        value = config[name]
        if isinstance(value, list):
            value = ','.join(value)
        print('{}={}'.format(name, value))
    sys.exit(0)
