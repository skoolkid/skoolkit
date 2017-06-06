# Copyright 2017 Richard Dymond (rjdymond@gmail.com)
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

from os.path import expanduser

from skoolkit import find_file
from skoolkit.refparser import RefParser

COMMANDS = {
    'sna2skool': {
        'CtlHex': 0,
        'DefbMod': 1,
        'DefbSize': 8,
        'DefbZfill': 0,
        'DefmSize': 66,
        'Erefs': 0,
        'LineWidth': 79,
        'LowerCase': 0,
        'SkoolHex': 0,
        'Text': 0,
        'EntryPointRef': 'This entry point is used by the routine at {ref}.',
        'EntryPointRefs': 'This entry point is used by the routines at {refs} and {ref}.',
        'Ref': 'Used by the routine at {ref}.',
        'Refs': 'Used by the routines at {refs} and {ref}.',
        'Title-b': 'Data block at {address}',
        'Title-c': 'Routine at {address}',
        'Title-g': 'Game status buffer entry at {address}',
        'Title-i': 'Ignored',
        'Title-s': 'Unused',
        'Title-t': 'Message at {address}',
        'Title-u': 'Unused',
        'Title-w': 'Data block at {address}'
    },
    'skool2html': {
        'AsmLabels': 0,
        'AsmOnePage': 0,
        'Base': 0,
        'Case': 0,
        'CreateLabels': 0,
        'JoinCss': '',
        'OutputDir': '.',
        'Quiet': 0,
        'RebuildImages': 0,
        'Search': '',
        'Theme': '',
        'Time': 0
    },
    'skool2asm': {
        'Base': 0,
        'Case': 0,
        'CreateLabels': 0,
        'Quiet': 0,
        'Warnings': 1
    }
}

def get_config(name):
    config = COMMANDS.get(name, {}).copy()
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
            else:
                config[k] = v
    return config
