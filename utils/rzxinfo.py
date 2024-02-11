#!/usr/bin/env python3
import argparse
import os
import sys
import tempfile
import zlib

SKOOLKIT_HOME = os.environ.get('SKOOLKIT_HOME')
if not SKOOLKIT_HOME:
    sys.stderr.write('SKOOLKIT_HOME is not set; aborting\n')
    sys.exit(1)
if not os.path.isdir(SKOOLKIT_HOME):
    sys.stderr.write(f'SKOOLKIT_HOME={SKOOLKIT_HOME}; directory not found\n')
    sys.exit(1)
sys.path.insert(0, SKOOLKIT_HOME)

from skoolkit import error, get_dword, get_word
from skoolkit.snapshot import Snapshot
from skoolkit.snapinfo import get_szx_machine_type, get_z80_machine_type

def _get_str(data, i):
    s = ''
    while data[i]:
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
            creator_id = _get_str(data, i + 5)
            vmajor = get_word(data, i + 25)
            vminor = get_word(data, i + 27)
            print(f'  ID: {creator_id} {vmajor}.{vminor}')
        elif block_id == 0x20:
            print('Security information')
        elif block_id == 0x21:
            print('Security signature')
        elif block_id == 0x30:
            print('Snapshot:')
            flags = data[i + 5]
            ext = _get_str(data, i + 9)
            length = get_dword(data, i + 13)
            print(f'  Filename extension: {ext}')
            print(f'  Size: {length} bytes')
            sdata = data[i + 17:i + block_len]
            if flags & 1:
                ext_sname = ''.join(chr(b) for b in sdata[4:])
                print(f'  External snapshot: {ext_sname}')
            else:
                if flags & 2:
                    sdata = zlib.decompress(sdata)
                with tempfile.NamedTemporaryFile(suffix=f'.{ext}') as f:
                    f.write(sdata)
                    snap = Snapshot.get(f.name)
                    machine = 'Unknown'
                    if snap:
                        if snap.type == 'SNA':
                            if len(snap.ram(-1)) == 0x20000:
                                machine = '128K Spectrum'
                            else:
                                machine = '48K Spectrum'
                        elif snap.type == 'SZX':
                            machine = get_szx_machine_type(snap.header)
                        elif snap.type == 'Z80':
                            machine = get_z80_machine_type(snap.header)
                print(f'  Machine: {machine}')
                print(f'  Start address: {snap.pc}')
        elif block_id == 0x80:
            print('Input recording')
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
                    frames = zlib.decompress(frames)
                j = 0
                pr_str = '?'
                suffix = ''
                for k in range(num_frames):
                    fetch_counter = get_word(frames, j)
                    in_counter = get_word(frames, j + 2)
                    print(f'  Frame {k}:')
                    print(f'    Fetch counter: {fetch_counter}')
                    print(f'    IN counter: {in_counter}')
                    if in_counter == 65535:
                        print(f'    Port readings: {pr_str}{suffix}')
                        j += 4
                    else:
                        port_readings = list(frames[j + 4:j + 4 + in_counter])
                        pr_str = ', '.join(str(b) for b in port_readings[:10])
                        suffix = '...' if len(port_readings) > 10 else ''
                        print(f'    Port readings: {pr_str}{suffix}')
                        j += 4 + in_counter
        else:
            print(f'Unknown block ID: 0x{block_id:02X}')
        i += block_len

def run(infile, options):
    with open(infile, 'rb') as f:
        data = f.read()
    if data[:4] != b'RZX!' or len(data) < 10:
        error('Not an RZX file')
    _show_blocks(data, options)

parser = argparse.ArgumentParser(
    usage='%(prog)s [options] FILE',
    description="Show the blocks in an RZX file.",
    add_help=False
)
parser.add_argument('infile', help=argparse.SUPPRESS, nargs='?')
group = parser.add_argument_group('Options')
group.add_argument('--frames', action='store_true',
                   help="Show the contents of every frame.")
namespace, unknown_args = parser.parse_known_args()
if unknown_args or namespace.infile is None:
    parser.exit(2, parser.format_help())
run(namespace.infile, namespace)
