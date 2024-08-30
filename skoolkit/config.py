# Copyright 2017-2024 Richard Dymond (rjdymond@gmail.com)
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
    'skoolkit': {
        'Assembler': 'skoolkit.z80.Assembler',
        'ControlDirectiveComposer': 'skoolkit.skoolctl.ControlDirectiveComposer',
        'ControlFileGenerator': 'skoolkit.snactl',
        'DefaultDisassemblyStartAddress': '16384',
        'Disassembler': 'skoolkit.disassembler.Disassembler',
        'HtmlTemplateFormatter': 'skoolkit.skoolhtml.TemplateFormatter',
        'ImageWriter': 'skoolkit.image.ImageWriter',
        'InstructionUtility': 'skoolkit.skoolparser.InstructionUtility',
        'OperandEvaluator': 'skoolkit.z80',
        'OperandFormatter': 'skoolkit.disassembler.OperandFormatter',
        'SnapshotReader': 'skoolkit.snapshot',
        'SnapshotReferenceCalculator': 'skoolkit.snaskool',
        'SnapshotReferenceOperations': 'DJ,JR,JP,CA,RS'
    },
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
        'DefbSize': (8, ''),
        'DefmSize': (65, ''),
        'DefwSize': (1, ''),
        'InstructionWidth': (13, ''),
        'LineWidth': (79, 'line_width'),
        'ListRefs': (1, ''),
        'Text': (0, ''),
        'EntryPointRef': ('This entry point is used by the routine at {ref}.', ''),
        'EntryPointRefs': ('This entry point is used by the routines at {refs} and {ref}.', ''),
        'Opcodes': ('', ''),
        'Ref': ('Used by the routine at {ref}.', ''),
        'RefFormat': ('#R{address}', ''),
        'Refs': ('Used by the routines at {refs} and {ref}.', ''),
        'Semicolons': ('c', ''),
        'Timings': (0, ''),
        'Title-b': ('Data block at {address}', ''),
        'Title-c': ('Routine at {address}', ''),
        'Title-g': ('Game status buffer entry at {address}', ''),
        'Title-i': ('Ignored', ''),
        'Title-s': ('Unused', ''),
        'Title-t': ('Message at {address}', ''),
        'Title-u': ('Unused', ''),
        'Title-w': ('Data block at {address}', ''),
        'Wrap': (0, '')
    },
    'snapinfo': {
        'EdgeAttributes': ('', ''),
        'GraphAttributes': ('', ''),
        'NodeAttributes': ('shape=record', ''),
        'NodeId': ('{address}', ''),
        'NodeLabel': (r'"{address} {address:04X}\n{label}"', ''),
        'Peek': ('{address:>5} {address:04X}: {value:>3}  {value:02X}  {value:08b}  {char}', ''),
        'Word': ('{address:>5} {address:04X}: {value:>5}  {value:04X}', '')
    },
    'skool2bin': {
        'Banks': (0, 'banks'),
        'Data': (0, 'data'),
        'PadLeft': (65536, ''),
        'PadRight': (0, ''),
        'Verbose': (0, 'verbose'),
        'Warnings': (1, 'warn')
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
        'EntryLabel': ('L{address}', ''),
        'EntryPointLabel': ('{main}_{index}', ''),
        'JoinCss': ('', 'single_css'),
        'OutputDir': ('.', 'output_dir'),
        'Quiet': (0, 'quiet'),
        'RebuildAudio': (0, 'new_audio'),
        'RebuildImages': (0, 'new_images'),
        'Search': ((), 'search'),
        'Theme': ((), 'themes'),
        'Time': (0, 'show_timings')
    },
    'skool2asm': {
        'Address': ('', ''),
        'Base': (0, 'base'),
        'Case': (0, 'case'),
        'CreateLabels': (0, 'create_labels'),
        'EntryLabel': ('L{address}', ''),
        'EntryPointLabel': ('{main}_{index}', ''),
        'Quiet': (0, 'quiet'),
        'Templates': ('', ''),
        'Warnings': (1, 'warn')
    },
    'tap2sna': {
        'DefaultSnapshotFormat': ('z80', ''),
        'TraceLine': ('${pc:04X} {i}', ''),
        'TraceOperand': ('$,02X,04X', '')
    },
    'trace': {
        'PNGScale': (2, ''),
        'ScreenFps': (50, ''),
        'ScreenScale': (2, ''),
        'TraceLine': ("${pc:04X} {i}", ''),
        'TraceLine2': (
            "${pc:04X} {i:<15}  "
            "A={r[a]:02X}  F={r[f]:08b}  BC={r[bc]:04X}  DE={r[de]:04X}  HL={r[hl]:04X}  IX={r[ix]:04X} IY={r[iy]:04X}\\n                       "
            "A'={r[^a]:02X} F'={r[^f]:08b} BC'={r[^bc]:04X} DE'={r[^de]:04X} HL'={r[^hl]:04X} SP={r[sp]:04X} IR={r[i]:02X}{r[r]:02X}",
            ''
        ),
        'TraceLineDecimal': ("{pc:05} {i}", ''),
        'TraceLineDecimal2': (
            "{pc:05} {i:<15}  "
            "A={r[a]:<3}  F={r[f]:08b}  BC={r[bc]:<5}  DE={r[de]:<5}  HL={r[hl]:<5}  IX={r[ix]:<5} IY={r[iy]:<5}\\n                       "
            "A'={r[^a]:<3} F'={r[^f]:08b} BC'={r[^bc]:<5} DE'={r[^de]:<5} HL'={r[^hl]:<5} SP={r[sp]:<5} I={r[i]:<3} R={r[r]:<3}",
            ''
        ),
        'TraceOperand': ('$,02X,04X', ''),
        'TraceOperandDecimal': (',,', '')
    }
}

def get_config(name):
    config = {}
    for k, v in COMMANDS.get(name, {}).items():
        if isinstance(v, tuple):
            if isinstance(v[0], tuple):
                config[k] = []
            else:
                config[k] = v[0]
        else:
            config[k] = v
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

def update_options(name, options, specs, config):
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
                config[param] = value
            except ValueError:
                pass

def show_config(section_name, config):
    print('[{}]'.format(section_name))
    for name in sorted(config):
        value = config[name]
        if isinstance(value, list):
            value = ','.join(value)
        print('{}={}'.format(name, value))
    sys.exit(0)
