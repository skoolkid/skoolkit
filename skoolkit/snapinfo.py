# Copyright 2013-2017, 2019-2024 Richard Dymond (rjdymond@gmail.com)
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

import argparse

from skoolkit import SkoolKitError, get_dword, get_int_param, get_word, integer, VERSION
from skoolkit.basic import BasicLister, VariableLister, get_char
from skoolkit.config import get_config, show_config, update_options
from skoolkit.opcodes import END, decode
from skoolkit.snapshot import Snapshot, make_snapshot
from skoolkit.sna2skool import get_ctl_parser
from skoolkit.snaskool import Disassembly

class Registers:
    def __init__(self, snapshot):
        for r in (
                'a', 'f', 'bc', 'de', 'hl', 'a2', 'f2', 'bc2', 'de2', 'hl2',
                'ix', 'iy', 'sp', 'i', 'r', 'pc', 'border', 'iff1', 'iff2',
                'im', 'tstates', 'out7ffd', 'outfffd', 'ay', 'outfe'
        ):
            setattr(self, r, getattr(snapshot, r))
        self.reg_map = {
            'b': 'bc', 'c': 'bc', 'b2': 'bc2', 'c2': 'bc2',
            'd': 'de', 'e': 'de', 'd2': 'de2', 'e2': 'de2',
            'h': 'hl', 'l': 'hl', 'h2': 'hl2', 'l2': 'hl2'
        }

    def get_lines(self):
        lines = []
        sep = ' ' * 4
        for row in (
            ('pc', 'sp'), ('ix', 'iy'), ('i', 'r'),
            ('b', 'b2'), ('c', 'c2'), ('bc', 'bc2'),
            ('d', 'd2'), ('e', 'e2'), ('de', 'de2'),
            ('h', 'h2'), ('l', 'l2'), ('hl', 'hl2'),
            ('a', 'a2')
        ):
            lines.append(self._reg(sep, *row))
        lines.append("  {0}    {1}   {0}".format("SZ5H3PNC", sep))
        lines.append("F {:08b}    {}F' {:08b}".format(self.f, sep, self.f2))
        return lines

    def _reg(self, sep, *registers):
        strings = []
        for reg in registers:
            name = reg.upper().replace('2', "'")
            size = len(name) - 1 if name.endswith("'") else len(name)
            value = self._get_value(reg)
            strings.append("{0:<3} {1:>5} {2:<{3}}{1:0{4}X}".format(name, value, "", (2 - size) * 2, size * 2))
        return sep.join(strings)

    def _get_value(self, register):
        try:
            return getattr(self, register)
        except AttributeError:
            reg_pair = self.reg_map[register]
            word = getattr(self, reg_pair)
            if register[0] == reg_pair[0]:
                return word // 256
            return word % 256

###############################################################################

# https://worldofspectrum.net/features/faq/reference/z80format.htm
# https://worldofspectrum.net/features/faq/reference/128kreference.htm

BLOCK_ADDRESSES_48K = {
    4: '32768-49151 8000-BFFF',
    5: '49152-65535 C000-FFFF',
    8: '16384-32767 4000-7FFF'
}

BLOCK_ADDRESSES_128K = {
    5: '32768-49151 8000-BFFF',
    8: '16384-32767 4000-7FFF'
}

V2_MACHINES = {
    0: ('48K Spectrum', '16K Spectrum'),
    1: ('48K Spectrum + IF1', '16K Spectrum + IF1'),
    2: ('SamRam', 'SamRam'),
    3: ('128K Spectrum', 'Spectrum +2'),
    4: ('128K Spectrum + IF1', 'Spectrum +2 + IF1')
}

V3_MACHINES = {
    0: ('48K Spectrum', '16K Spectrum'),
    1: ('48K Spectrum + IF1', '16K Spectrum + IF1'),
    2: ('SamRam', 'SamRam'),
    3: ('48K Spectrum + MGT', '16K Spectrum + MGT'),
    4: ('128K Spectrum', 'Spectrum +2'),
    5: ('128K Spectrum + IF1', 'Spectrum +2 + IF1'),
    6: ('128K Spectrum + MGT', 'Spectrum +2 + MGT'),
}

MACHINES = {
    7: ('Spectrum +3', 'Spectrum +2A'),
    8: ('Spectrum +3', 'Spectrum +2A'),
    9: ('Pentagon (128K)', 'Pentagon (128K)'),
    10: ('Scorpion (256K)', 'Scorpion (256K)'),
    11: ('Didaktik+Kompakt', 'Didaktik+Kompakt'),
    12: ('Spectrum +2', 'Spectrum +2'),
    13: ('Spectrum +2A', 'Spectrum +2A'),
    14: ('TC2048', 'TC2048'),
    15: ('TC2068', 'TC2068'),
    128: ('TS2068', 'TS2068'),
}

def get_z80_machine_type(header):
    version = _get_z80_version(header)
    if version == 1:
        return '48K Spectrum'
    if version == 2:
        machine_dict = V2_MACHINES
    else:
        machine_dict = V3_MACHINES
    machine_id = header[34]
    index = header[37] // 128
    machine_spec = machine_dict.get(machine_id, MACHINES.get(machine_id, ('Unknown', 'Unknown')))
    return machine_spec[index]

def _get_z80_version(header):
    if len(header) == 30:
        return 1
    if len(header) == 55:
        return 2
    return 3

def _analyse_z80(header, reg, ram_blocks):
    # Print version, machine, interrupt status, border, port $7FFD
    version = _get_z80_version(header)
    print('Version: {}'.format(version))
    is128 = (version == 2 and header[34] > 1) or (version == 3 and header[34] not in (0, 1, 3))
    if is128:
        block_dict = BLOCK_ADDRESSES_128K
    else:
        block_dict = BLOCK_ADDRESSES_48K
    print('Machine: {}'.format(get_z80_machine_type(header)))
    print('Interrupts: {}abled'.format('en' if reg.iff1 else 'dis'))
    print('Interrupt mode: {}'.format(reg.im))
    print('Issue 2 emulation: {}abled'.format('en' if header[29] & 4 else 'dis'))
    if version == 3:
        print(f'T-states: {reg.tstates}')
    print(f'Border: {reg.border}')
    if is128:
        print(f'Port $FFFD: {reg.outfffd}')
        bank = reg.out7ffd % 8
        print('Port $7FFD: {} - bank {} (block {}) paged into 49152-65535 C000-FFFF'.format(reg.out7ffd, bank, bank + 3))

    # Print register contents
    print('Registers:')
    for line in reg.get_lines():
        print('  ' + line)

    # Print RAM block info
    if version == 1:
        block_len = len(ram_blocks)
        prefix = '' if header[12] & 32 else 'un'
        print('48K RAM block (16384-65535 4000-FFFF): {} bytes ({}compressed)'.format(block_len, prefix))
    else:
        i = 0
        while i < len(ram_blocks):
            block_len = get_word(ram_blocks, i)
            page_num = ram_blocks[i + 2]
            addr_range = block_dict.get(page_num)
            if addr_range is None and page_num - 3 == bank:
                addr_range = '49152-65535 C000-FFFF'
            if addr_range:
                addr_range = ' ({})'.format(addr_range)
            else:
                addr_range = ''
            i += 3
            if block_len == 65535:
                block_len = 16384
                prefix = 'un'
            else:
                prefix = ''
            print('RAM block {}{}: {} bytes ({}compressed)'.format(page_num, addr_range, block_len, prefix))
            i += block_len

###############################################################################

# https://www.spectaculator.com/docs/zx-state/intro.shtml

SZX_MACHINES = {
    0: '16K ZX Spectrum',
    1: '48K ZX Spectrum',
    2: 'ZX Spectrum 128',
    3: 'ZX Spectrum +2',
    4: 'ZX Spectrum +2A/+2B',
    5: 'ZX Spectrum +3',
    6: 'ZX Spectrum +3e',
    7: 'Pentagon 128',
    8: 'Timex Sinclair TC2048',
    9: 'Timex Sinclair TC2068',
    10: 'Scorpion ZS-256',
    11: 'ZX Spectrum SE',
    12: 'Timex Sinclair TS2068',
    13: 'Pentagon 512',
    14: 'Pentagon 1024',
    15: '48K ZX Spectrum (NTSC)',
    16: 'ZX Spectrum 128Ke'
}

def get_szx_machine_type(header):
    return SZX_MACHINES.get(header[6], 'Unknown')

def _print_ay(block, reg):
    return [f'Current AY register: {reg.outfffd}']

def _print_keyb(block, reg):
    issue2 = get_dword(block, 0) & 1
    return ['Issue 2 emulation: {}abled'.format('en' if issue2 else 'dis')]

def _print_ramp(block, reg):
    flags = get_word(block, 0)
    compressed = 'compressed' if flags & 1 else 'uncompressed'
    page = block[2]
    ram = block[3:]
    addresses = ''
    if page == 5:
        addresses = '16384-32767 4000-7FFF'
    elif page == 2:
        addresses = '32768-49151 8000-BFFF'
    elif reg.machine_id > 1 and page == reg.out7ffd & 7:
        addresses = '49152-65535 C000-FFFF'
    if addresses:
        addresses += ': '
    return (
        f'Page: {page}',
        f'RAM: {addresses}{len(ram)} bytes, {compressed}'
    )

def _print_spcr(block, reg):
    lines = [f'Border: {reg.border}']
    if reg.machine_id > 1:
        lines.append(f'Port $7FFD: {reg.out7ffd} (bank {reg.out7ffd % 8} paged into 49152-65535 C000-FFFF)')
    return lines

def _print_z80r(block, reg):
    lines = [
        'Interrupts: {}abled'.format('en' if reg.iff1 else 'dis'),
        f'Interrupt mode: {reg.im}',
        f'T-states: {reg.tstates}'
    ]
    return lines + reg.get_lines()

SZX_BLOCK_PRINTERS = {
    'AY': _print_ay,
    'KEYB': _print_keyb,
    'RAMP': _print_ramp,
    'SPCR': _print_spcr,
    'Z80R': _print_z80r
}

def _analyse_szx(header, reg, blocks):
    print('Version: {}.{}'.format(header[4], header[5]))
    print('Machine: {}'.format(get_szx_machine_type(header)))
    reg.machine_id = header[6]

    for block_id, block in blocks:
        print('{}: {} bytes'.format(block_id, len(block)))
        printer = SZX_BLOCK_PRINTERS.get(block_id)
        if printer:
            for line in printer(block, reg):
                print("  " + line)

###############################################################################

# https://worldofspectrum.net/features/faq/reference/formats.htm#SNA

def _print_ram_banks(sna):
    bank = sna[49154] & 7
    print('RAM bank 5 (16384 bytes: 16384-32767 4000-7FFF)')
    print('RAM bank 2 (16384 bytes: 32768-49151 8000-BFFF)')
    print('RAM bank {} (16384 bytes: 49152-65535 C000-FFFF)'.format(bank))
    for b in sorted({0, 1, 3, 4, 6, 7} - {bank}):
        print('RAM bank {} (16384 bytes)'.format(b))

def _analyse_sna(reg, ram):
    is128 = len(ram) > 49152
    print('RAM: {}K'.format(128 if is128 else 48))
    print('Interrupts: {}abled'.format('en' if reg.iff1 else 'dis'))
    print('Interrupt mode: {}'.format(reg.im))
    print('Border: {}'.format(reg.border))

    print('Registers:')
    for line in reg.get_lines():
        print('  ' + line)

    if is128:
        _print_ram_banks(ram)

###############################################################################

def _get_address_ranges(specs, step=1):
    addr_ranges = []
    for addr_range in specs:
        try:
            values = [get_int_param(i, True) for i in addr_range.split('-', 2)]
        except ValueError:
            raise SkoolKitError('Invalid address range: {}'.format(addr_range))
        addr_ranges.append(values + [values[0], step][len(values) - 1:])
    return addr_ranges

def _call_graph(snapshot, ctlfiles, prefix, start, end, config):
    disassembly = Disassembly(snapshot, get_ctl_parser(ctlfiles, prefix, start, end, start, end), self_refs=True)
    entries = {e.address: (e, set(), set(), set(), {}) for e in disassembly.entries if e.ctl == 'c'}
    for entry, children, parents, main_refs, props in entries.values():
        props.update({'address': entry.address, 'label': entry.instructions[0].label or ''})
        for instruction in entry.instructions:
            for ref_addr in instruction.referrers:
                if ref_addr in entries:
                    if ref_addr != entry.address:
                        parents.add(ref_addr)
                        entries[ref_addr][1].add(entry.address)
                    if entry.address == instruction.address:
                        main_refs.add(ref_addr)
        addr, size, mc, op_id, op = next(decode(snapshot, entry.instructions[-1].address, 65536))
        if op_id != END:
            next_entry_addr = addr + size
            if next_entry_addr in entries:
                children.add(next_entry_addr)
                entries[next_entry_addr][2].add(entry.address)
                entries[next_entry_addr][3].add(entry.address)

    for desc, addresses in (
            ('Unconnected', {e.address for e, c, p, m, n in entries.values() if not (c or p)}),
            ('Orphans', {e.address for e, c, p, m, n in entries.values() if c and not p}),
            ('First instruction not used', {e.address for e, c, p, m, n in entries.values() if p and not m})
    ):
        node_ids = [config['NodeId'].format(**entries[addr][4]) for addr in sorted(addresses)]
        if not node_ids:
            node_ids.append('None')
        print('// {}: {}'.format(desc, ', '.join(node_ids)))
    print('digraph {')
    if config['GraphAttributes']:
        print('graph [{}]'.format(config['GraphAttributes']))
    if config['NodeAttributes']:
        print('node [{}]'.format(config['NodeAttributes']))
    if config['EdgeAttributes']:
        print('edge [{}]'.format(config['EdgeAttributes']))
    for entry, children, parents, main_refs, props in entries.values():
        node_id = config['NodeId'].format(**props)
        print('{} [label={}]'.format(node_id, config['NodeLabel'].format(**props)))
        if children:
            ref_ids = [config['NodeId'].format(address=a, label=entries[a][0].instructions[0].label or '') for a in children]
            print('{} -> {{{}}}'.format(node_id, ' '.join(ref_ids)))
    print('}')

def _find(snapshot, byte_seq, base_addr):
    steps = '1'
    if '-' in byte_seq:
        byte_seq, steps = byte_seq.split('-', 1)
    try:
        byte_values = [get_int_param(i, True) for i in byte_seq.split(',')]
    except ValueError:
        raise SkoolKitError('Invalid byte sequence: {}'.format(byte_seq))
    try:
        if '-' in steps:
            limits = [get_int_param(n, True) for n in steps.split('-', 1)]
            steps = range(limits[0], limits[1] + 1)
        else:
            steps = [get_int_param(steps, True)]
    except ValueError:
        raise SkoolKitError('Invalid distance: {}'.format(steps))
    for step in steps:
        offset = step * len(byte_values)
        if len(snapshot) == 0x20000:
            for bank in range(8):
                i = bank * 16384
                for a in range(16385 - offset):
                    if snapshot[i + a:i + a + offset:step] == byte_values:
                        print("{0}:{1:05}-{2:05}-{3} {0}:{1:04X}-{2:04X}-{3:X}: {4}".format(bank, a, a + offset - step, step, byte_seq))
        else:
            for a in range(base_addr, 65537 - offset):
                if snapshot[a:a + offset:step] == byte_values:
                    print("{0}-{1}-{2} {0:04X}-{1:04X}-{2:X}: {3}".format(a, a + offset - step, step, byte_seq))

def _find_tile(snapshot, coords, df_base):
    steps = '1'
    if '-' in coords:
        coords, steps = coords.split('-', 1)
    try:
        x, y = [get_int_param(i) for i in coords.split(',', 1)]
        if not 0 <= x < 32 or not 0 <= y < 24:
            raise ValueError
    except ValueError:
        raise SkoolKitError('Invalid tile coordinates: {}'.format(coords))
    df_addr = df_base + 2048 * (y // 8) + 32 * (y % 8) + x
    byte_seq = snapshot[df_addr:df_addr + 2048:256]
    for b in byte_seq:
        print('|{:08b}|'.format(b).replace('0', ' ').replace('1', '*'))
    _find(snapshot, '{}-{}'.format(','.join([str(b) for b in byte_seq]), steps), 23296)

def _find_text(snapshot, text, base_addr):
    size = len(text)
    byte_values = [ord(c) for c in text]
    if len(snapshot) == 0x20000:
        for bank in range(8):
            i = bank * 16384
            for a in range(16385 - size):
                if snapshot[i + a:i + a + size] == byte_values:
                    print("{0}:{1:05}-{2:05} {0}:{1:04X}-{2:04X}: {3}".format(bank, a, a + size - 1, text))
    else:
        for a in range(base_addr, 65536 - size + 1):
            if snapshot[a:a + size] == byte_values:
                print("{0}-{1} {0:04X}-{1:04X}: {2}".format(a, a + size - 1, text))

def _peek(snapshot, specs, fmt):
    for addr1, addr2, step in _get_address_ranges(specs):
        for a in range(addr1, addr2 + 1, step):
            value = snapshot[a]
            char = get_char(value, '', 'UDG-{}', True)
            print(fmt.format(address=a, value=value, char=char))

def _word(snapshot, specs, fmt):
    for addr1, addr2, step in _get_address_ranges(specs, 2):
        for a in range(addr1, addr2 + 1, step):
            value = snapshot[a] + 256 * snapshot[a + 1]
            print(fmt.format(address=a, value=value))

def run(infile, options, config):
    if any((options.find, options.tile, options.text, options.call_graph, options.peek,
            options.word, options.basic, options.variables)):
        if (options.find or options.text or options.tile) and options.page is None:
            options.page = -1
        snapshot, start, end = make_snapshot(infile, options.org, page=options.page)
        if options.find:
            _find(snapshot, options.find, start)
        elif options.tile:
            if len(snapshot) == 0x20000:
                out7ffd = Snapshot.get(infile).out7ffd
                df_base = (5 + (out7ffd & 8) // 4) * 16384
            else:
                df_base = 16384
            _find_tile(snapshot, options.tile, df_base)
        elif options.text:
            _find_text(snapshot, options.text, start)
        elif options.call_graph:
            _call_graph(snapshot, options.ctlfiles, infile, start, end, config)
        elif options.peek:
            _peek(snapshot, options.peek, config['Peek'])
        elif options.word:
            _word(snapshot, options.word, config['Word'])
        else:
            if options.basic:
                print(BasicLister().list_basic(snapshot))
            if options.variables:
                print(VariableLister().list_variables(snapshot))
    else:
        snapshot = Snapshot.get(infile)
        if snapshot:
            registers = Registers(snapshot)
            if snapshot.type == 'SNA':
                _analyse_sna(registers, snapshot.tail)
            elif snapshot.type == 'Z80':
                _analyse_z80(snapshot.header, registers, snapshot.tail)
            elif snapshot.type == 'SZX':
                _analyse_szx(snapshot.header, registers, snapshot.tail)

def main(args):
    config = get_config('snapinfo')
    parser = argparse.ArgumentParser(
        usage='snapinfo.py [options] file',
        description="Analyse a binary (raw memory) file or a SNA, SZX or Z80 snapshot.",
        add_help=False
    )
    parser.add_argument('infile', help=argparse.SUPPRESS, nargs='?')
    group = parser.add_argument_group('Options')
    group.add_argument('-b', '--basic', action='store_true',
                       help='List the BASIC program.')
    group.add_argument('-c', '--ctl', dest='ctlfiles', metavar='PATH', action='append', default=[],
                       help="When generating a call graph, specify a control file to use, or a directory from which to read control files. "
                            "PATH may be '-' for standard input. This option may be used multiple times.")
    group.add_argument('-f', '--find', metavar='A[,B...[-M[-N]]]',
                       help='Search for the byte sequence A,B... with distance ranging from M to N (default=1) between bytes.')
    group.add_argument('-g', '--call-graph', action='store_true',
                       help='Generate a call graph in DOT format.')
    group.add_argument('-I', '--ini', dest='params', metavar='p=v', action='append', default=[],
                       help="Set the value of the configuration parameter 'p' to 'v'. This option may be used multiple times.")
    group.add_argument('-o', '--org', dest='org', metavar='ADDR', type=integer,
                       help='Specify the origin address of a binary (raw memory) file (default: 65536 - length).')
    group.add_argument('-p', '--peek', metavar='A[-B[-C]]', action='append',
                       help='Show the contents of addresses A TO B STEP C. This option may be used multiple times.')
    group.add_argument('-P', '--page', dest='page', metavar='PAGE', type=int, choices=list(range(8)),
                       help='Specify the page (0-7) of a 128K snapshot to map to 49152-65535.')
    group.add_argument('--show-config', dest='show_config', action='store_true',
                       help="Show configuration parameter values.")
    group.add_argument('-t', '--find-text', dest='text', metavar='TEXT',
                       help='Search for a text string.')
    group.add_argument('-T', '--find-tile', dest='tile', metavar='X,Y[-M[-N]]',
                       help='Search for the graphic data of the tile at (X,Y) with distance ranging from M to N (default=1) between bytes.')
    group.add_argument('-v', '--variables', action='store_true',
                       help='List variables.')
    group.add_argument('-V', '--version', action='version', version='SkoolKit {}'.format(VERSION),
                       help='Show SkoolKit version number and exit.')
    group.add_argument('-w', '--word', metavar='A[-B[-C]]', action='append',
                       help='Show the words at addresses A TO B STEP C. This option may be used multiple times.')
    namespace, unknown_args = parser.parse_known_args(args)
    if namespace.show_config:
        show_config('snapinfo', config)
    if unknown_args or namespace.infile is None:
        parser.exit(2, parser.format_help())
    update_options('snapinfo', namespace, namespace.params, config)
    run(namespace.infile, namespace, config)
