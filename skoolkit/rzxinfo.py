# Copyright 2024 Richard Dymond (rjdymond@gmail.com)
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
import os
import zlib

from skoolkit import VERSION, SkoolKitError, get_dword, get_word, read_bin_file
from skoolkit.snapinfo import get_szx_machine_type, get_z80_machine_type
from skoolkit.snapshot import Snapshot

def _get_str(data, i, max_len):
    s = ''
    while len(s) < max_len and data[i]:
        s += chr(data[i])
        i += 1
    return s

def _show_blocks(data, options):
    vmajor, vminor = data[4:6]
    print(f'Version: {vmajor}.{vminor}')
    flags = get_dword(data, 6)
    print('Signed: {}'.format('Yes' if flags % 1 else 'No'))
    i = 10
    while i < len(data):
        block_id = data[i]
        block_len = get_dword(data, i + 1)
        if block_id == 0x10:
            print('Creator information:')
            creator_id = _get_str(data, i + 5, 20)
            vmajor = get_word(data, i + 25)
            vminor = get_word(data, i + 27)
            vcanonical = '.'.join(str(data[i + d]) for d in (26, 25, 28, 27))
            print(f'  ID: {creator_id} {vmajor}.{vminor} ({vcanonical})')
        elif block_id == 0x20:
            print('Security information')
        elif block_id == 0x21:
            print('Security signature')
        elif block_id == 0x30:
            print('Snapshot:')
            flags = data[i + 5]
            ext = _get_str(data, i + 9, 4)
            length = get_dword(data, i + 13)
            print(f'  Filename extension: {ext}')
            sdata = data[i + 17:i + block_len]
            if flags & 1:
                ext_sname = _get_str(sdata, 4, len(sdata) - 4)
                print(f'  External snapshot: {ext_sname}')
            else:
                print(f'  Size: {length} bytes')
                if flags & 2:
                    try:
                        sdata = zlib.decompress(sdata)
                    except zlib.error as e:
                        raise SkoolKitError(f'Failed to decompress snapshot: {e.args[0]}')
                snap = Snapshot.get(sdata, ext)
                if snap:
                    if snap.type == 'SNA':
                        if len(snap.tail) > 0xC000:
                            machine = '128K Spectrum'
                        else:
                            machine = '48K Spectrum'
                    elif snap.type == 'SZX':
                        machine = get_szx_machine_type(snap.header)
                    elif snap.type == 'Z80':
                        machine = get_z80_machine_type(snap.header)
                    start_addr = snap.pc
                else:
                    machine = 'Unknown'
                    start_addr = 'Unknown'
                print(f'  Machine: {machine}')
                print(f'  Start address: {start_addr}')
        elif block_id == 0x80:
            print('Input recording:')
            num_frames = get_dword(data, i + 5)
            h = num_frames // 180000
            m = (num_frames % 180000) // 3000
            s = (num_frames % 3000) // 50
            print(f'  Number of frames: {num_frames} ({h}h{m:02}m{s:02}s)')
            tstates = get_dword(data, i + 10)
            print(f'  T-states: {tstates}')
            flags = get_dword(data, i + 14)
            encrypted = flags % 1
            print('  Encrypted: {}'.format('Yes' if encrypted else 'No'))
            if options.frames and not encrypted:
                frames = data[i + 18:i + block_len]
                if flags & 2:
                    try:
                        frames = zlib.decompress(frames)
                    except zlib.error as e:
                        raise SkoolKitError(f'Failed to decompress input recording block: {e.args[0]}')
                j = 0
                pr_str = ''
                port_readings = ()
                suffix = ''
                for k in range(num_frames):
                    fetch_counter = get_word(frames, j)
                    in_counter = get_word(frames, j + 2)
                    print(f'  Frame {k}:')
                    print(f'    Fetch counter: {fetch_counter}')
                    if in_counter == 65535:
                        print(f'    IN counter: {in_counter} ({len(port_readings)})')
                        if pr_str:
                            print(f'    Port readings: {pr_str}{suffix}')
                        j += 4
                    else:
                        print(f'    IN counter: {in_counter}')
                        port_readings = list(frames[j + 4:j + 4 + in_counter])
                        pr_str = ', '.join(str(b) for b in port_readings[:10])
                        suffix = '...' if len(port_readings) > 10 else ''
                        if port_readings:
                            print(f'    Port readings: {pr_str}{suffix}')
                        j += 4 + in_counter
        else:
            print(f'Unknown block ID: 0x{block_id:02X}')
        i += block_len

def _extract_snapshots(data, prefix):
    i = 10
    s_count = 0
    while i < len(data):
        block_id = data[i]
        block_len = get_dword(data, i + 1)
        if block_id == 0x30:
            flags = data[i + 5]
            if flags & 1 == 0:
                ext = _get_str(data, i + 9, 4).lower()
                sdata = data[i + 17:i + block_len]
                if flags & 2:
                    try:
                        sdata = zlib.decompress(sdata)
                    except zlib.error as e:
                        raise SkoolKitError(f'Failed to decompress snapshot: {e.args[0]}')
                s_count += 1
                sfname = f'{prefix}.{s_count:03}.{ext}'
                with open(sfname, 'wb') as f:
                    f.write(sdata)
                print(f'Extracted {sfname}')
        i += block_len
    if s_count == 0:
        print('No snapshots found')

def run(infile, options):
    data = read_bin_file(infile)
    if data[:4] != b'RZX!' or len(data) < 10:
        raise SkoolKitError('Not an RZX file')
    if options.extract:
        _extract_snapshots(data, os.path.basename(infile))
    else:
        _show_blocks(data, options)

def main(args):
    parser = argparse.ArgumentParser(
        usage='rzxinfo.py [options] FILE',
        description="Show the blocks in or extract the snapshots from an RZX file.",
        add_help=False
    )
    parser.add_argument('infile', help=argparse.SUPPRESS, nargs='?')
    group = parser.add_argument_group('Options')
    group.add_argument('--extract', action='store_true',
                       help="Extract snapshots.")
    group.add_argument('--frames', action='store_true',
                       help="Show the contents of every frame.")
    group.add_argument('-V', '--version', action='version', version='SkoolKit {}'.format(VERSION),
                       help='Show SkoolKit version number and exit.')
    namespace, unknown_args = parser.parse_known_args(args)
    if unknown_args or namespace.infile is None:
        parser.exit(2, parser.format_help())
    run(namespace.infile, namespace)
