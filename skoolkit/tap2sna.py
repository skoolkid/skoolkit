# -*- coding: utf-8 -*-

# Copyright 2013, 2015 Richard Dymond (rjdymond@gmail.com)
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
import argparse
import textwrap
import tempfile
import zipfile
try:
    from urllib2 import urlopen
    from urlparse import urlparse
except ImportError:                    # pragma: no cover
    from urllib.request import urlopen # pragma: no cover
    from urllib.parse import urlparse  # pragma: no cover

from skoolkit import SkoolKitError, get_int_param, get_word, get_word3, get_dword, open_file, write_line, VERSION
from skoolkit.snapshot import set_z80_registers, set_z80_state, make_z80_ram_block, Z80_REGISTERS

class SkoolKitArgumentParser(argparse.ArgumentParser):
    def convert_arg_line_to_args(self, arg_line):
        for arg in arg_line.split():
            if arg in (';', '#'):
                break
            yield arg

class TapeError(Exception):
    pass

def _get_z80(ram, options):
    z80 = [0] * 86
    z80[30] = 54 # Indicate a v3 Z80 snapshot
    set_z80_registers(z80, 'i=63', 'iy=23610')
    set_z80_registers(z80, *options.reg)
    set_z80_state(z80, 'iff=1', 'im=1')
    set_z80_state(z80, *options.state)
    for bank, data in ((5, ram[:16384]), (1, ram[16384:32768]), (2, ram[32768:49152])):
        z80 += make_z80_ram_block(data, bank + 3)
    return z80

def _write_z80(ram, options, fname):
    parent_dir = os.path.dirname(fname)
    if parent_dir and not os.path.isdir(parent_dir):
        os.makedirs(parent_dir)
    write_line('Writing {0}'.format(fname))
    with open(fname, 'wb') as f:
        f.write(bytearray(_get_z80(ram, options)))

def _get_int_params(param_str, num, leave=()):
    params = []
    for index, n in enumerate(param_str.split(',')):
        if index in leave:
            params.append(n)
        elif n:
            params.append(get_int_param(n))
        else:
            params.append(None)
    params += [None] * (num - len(params))
    return params[:num]

def _load_block(snapshot, block, start, length=None, step=None, offset=None, inc=None, index=1):
    if length is None:
        data = block[index:-1]
    else:
        data = block[index:index + length]
    if step is None:
        step = 1
    if offset is None:
        offset = 0
    if inc is None:
        inc = 0
    i = start
    for b in data:
        snapshot[(i + offset) & 65535] = b
        i += step
        if i > 65535:
            i += inc
        i &= 65535
    return len(data)

def _load(snapshot, counters, blocks, param_str):
    block_num, start, length, step, offset, inc = _get_int_params(param_str, 6, (0,))
    default_index = 1
    load_last = False
    if block_num.startswith('+'):
        block_num = block_num[1:]
        default_index = 0
    if block_num.endswith('+'):
        block_num = block_num[:-1]
        load_last = True
    block_num = get_int_param(block_num)
    index = counters.setdefault(block_num, default_index)
    try:
        block = blocks[block_num - 1]
    except IndexError:
        raise TapeError("Block {} not found".format(block_num))
    if length is None and load_last:
        length = len(block) - index
    length = _load_block(snapshot, block, start, length, step, offset, inc, index)
    counters[block_num] += length

def move(snapshot, param_str):
    src, length, dest = _get_int_params(param_str, 3)
    snapshot[dest:dest + length] = snapshot[src:src + length]

def poke(snapshot, param_str):
    addr, val = param_str.split(',', 1)
    if val.startswith('^'):
        value = get_int_param(val[1:])
        poke_f = lambda b: b ^ value
    elif val.startswith('+'):
        value = get_int_param(val[1:])
        poke_f = lambda b: (b + value) & 255
    else:
        value = get_int_param(val)
        poke_f = lambda b: value
    step = 1
    if '-' in addr:
        addr1, addr2 = addr.split('-', 1)
        addr1 = get_int_param(addr1)
        if '-' in addr2:
            addr2, step = [get_int_param(i) for i in addr2.split('-', 1)]
        else:
            addr2 = get_int_param(addr2)
    else:
        addr1 = get_int_param(addr)
        addr2 = addr1
    addr2 += 1
    for a in range(addr1, addr2, step):
        snapshot[a] = poke_f(snapshot[a])

def _get_ram(blocks, options):
    snapshot = [0] * 65536

    operations = []
    standard_load = True
    for spec in options.ram_ops:
        op_type, param_str = spec.split('=', 1)
        if op_type in ('load', 'move', 'poke'):
            operations.append((op_type, param_str))
            if op_type == 'load':
                standard_load = False
        else:
            raise SkoolKitError("Invalid operation: {}".format(spec))

    if standard_load:
        start = None
        for block_num, block in enumerate(blocks, 1):
            if block:
                if block[0] == 0:
                    # Header
                    block_type = block[1]
                    if block_type == 3:
                        # Bytes
                        start = block[14] + 256 * block[15]
                    elif block_type == 0:
                        # Program
                        start = 23755
                    else:
                        raise TapeError('Unknown block type ({}) in header block {}'.format(block_type, block_num))
                elif start is not None:
                    # Data
                    _load_block(snapshot, block, start)
                    start = None

    counters = {}
    for op_type, param_str in operations:
        try:
            if op_type == 'load':
                _load(snapshot, counters, blocks, param_str)
            elif op_type == 'move':
                move(snapshot, param_str)
            elif op_type == 'poke':
                poke(snapshot, param_str)
        except ValueError:
            raise SkoolKitError("Cannot parse integer: {}={}".format(op_type, param_str))

    return snapshot[16384:]

def _get_tzx_block(data, i):
    # http://www.worldofspectrum.org/TZXformat.html
    block_id = data[i]
    tape_data = None
    i += 1
    if block_id == 16:
        # Standard speed data block
        length = get_word(data, i + 2)
        tape_data = data[i + 4:i + 4 + length]
        i += 4 + length
    elif block_id == 17:
        # Turbo speed data block
        length = get_word3(data, i + 15)
        tape_data = data[i + 18:i + 18 + length]
        i += 18 + length
    elif block_id == 18:
        # Pure tone
        i += 4
    elif block_id == 19:
        # Sequence of pulses of various lengths
        i += 2 * data[i] + 1
    elif block_id == 20:
        # Pure data block
        length = get_word3(data, i + 7)
        tape_data = data[i + 10:i + 10 + length]
        i += 10 + length
    elif block_id == 21:
        # Direct recording block
        i += get_word3(data, i + 5) + 8
    elif block_id == 24:
        # CSW recording block
        i += get_dword(data, i) + 4
    elif block_id == 25:
        # Generalized data block
        i += get_dword(data, i) + 4
    elif block_id == 32:
        # Pause (silence) or 'Stop the tape' command
        i += 2
    elif block_id == 33:
        # Group start
        i += data[i] + 1
    elif block_id == 34:
        # Group end
        pass
    elif block_id == 35:
        # Jump to block
        i += 2
    elif block_id == 36:
        # Loop start
        i += 2
    elif block_id == 37:
        # Loop end
        pass
    elif block_id == 38:
        # Call sequence
        i += get_word(data, i) * 2 + 2
    elif block_id == 39:
        # Return from sequence
        pass
    elif block_id == 40:
        # Select block
        i += get_word(data, i) + 2
    elif block_id == 42:
        # Stop the tape if in 48K mode
        i += 4
    elif block_id == 43:
        # Set signal level
        i += 5
    elif block_id == 48:
        # Text description
        i += data[i] + 1
    elif block_id == 49:
        # Message block
        i += data[i + 1] + 2
    elif block_id == 50:
        # Archive info
        i += get_word(data, i) + 2
    elif block_id == 51:
        # Hardware type
        i += data[i] * 3 + 1
    elif block_id == 53:
        # Custom info block
        i += get_dword(data, i + 16) + 20
    elif block_id == 90:
        # "Glue" block
        i += 9
    else:
        raise TapeError('Unknown TZX block ID: 0x{:X}'.format(block_id))
    return i, tape_data

def _get_tzx_blocks(data):
    signature = ''.join(chr(b) for b in data[:7])
    if signature != 'ZXTape!':
        raise TapeError("Not a TZX file")
    i = 10
    blocks = []
    while i < len(data):
        i, tape_data = _get_tzx_block(data, i)
        blocks.append(tape_data)
    return blocks

def _get_tap_blocks(tap):
    blocks = []
    i = 0
    while i < len(tap):
        block_len = tap[i] + 256 * tap[i + 1]
        i += 2
        blocks.append(tap[i:i + block_len])
        i += block_len
    return blocks

def _get_tape_blocks(tape_type, tape):
    if tape_type.lower() == 'tzx':
        return _get_tzx_blocks(tape)
    return _get_tap_blocks(tape)

def _get_tape(urlstring, member=None):
    url = urlparse(urlstring)
    if url.scheme:
        write_line('Downloading {0}'.format(urlstring))
        u = urlopen(urlstring, timeout=30)
        f = tempfile.NamedTemporaryFile(prefix='tap2sna-')
        while 1:
            data = bytearray(u.read(4096))
            if data:
                f.write(data)
            else:
                break
    elif url.path:
        f = open_file(url.path, 'rb')

    if urlstring.lower().endswith('.zip'):
        z = zipfile.ZipFile(f)
        if member is None:
            for name in z.namelist():
                if name.lower().endswith(('.tap', '.tzx')):
                    member = name
                    break
            else:
                raise TapeError('No TAP or TZX file found')
        write_line('Extracting {0}'.format(member))
        tape = z.open(member)
        data = bytearray(tape.read())
        tape_type = member[-3:]
    else:
        tape_type = urlstring[-3:]
        f.seek(0)
        data = bytearray(f.read())

    f.close()
    return tape_type, data

def _print_ram_help():
    sys.stdout.write("""
Usage: --ram load=block,start[,length,step,offset,inc]
       --ram move=src,size,dest
       --ram poke=a[-b[-c]],v

Load data from a tape block, move a block of bytes from one location to
another, or POKE a single address or range of addresses with a given value.

--ram load=[+]block[+],start[,length,step,offset,inc]

  By default, tap2sna.py loads bytes from every data block on the tape, using
  the start address given in the corresponding header. For tapes that contain
  headerless data blocks, headers with incorrect start addresses, or irrelevant
  blocks, '--ram load' can be used to load bytes from specific blocks at the
  appropriate addresses.

  block  - the tape block number (the first block is 1, the next is 2, etc.);
           attach a '+' prefix to load the first byte of the block (usually the
           flag byte), and a '+' suffix to load the last byte (usually the
           parity byte)
  start  - the destination address at which to start loading
  length - the number of bytes to load (optional; default is the number of
           bytes remaining in the block)
  step   - this number is added to the destination address after each byte is
           loaded (optional; default=1)
  offset - this number is added to the destination address before a byte is
           loaded, and subtracted after the byte is loaded (optional;
           default=0)
  inc    - after 'step' is added to the destination address, this number is
           added too if the result is greater than 65535 (optional; default=0)

  A single tape block can be loaded in two or more stages; for example:

  --ram load=2,32768,2048  # Load the first 2K at 32768
  --ram load=2,49152       # Load the remainder at 49152

--ram move=src,size,dest

  Move a block of bytes from one location to another.

  src  - the address of the first byte in the block
  size - the number of bytes in the block
  dest - the destination address

  For example:

  --ram move=32512,256,32768  # Move 32512-32767 to 32768-33023

--ram poke=a[-b[-c]],[^+]v

  Do POKE N,v for N in {a, a+c, a+2c..., b}.

  a - the first address to POKE
  b - the last address to POKE (optional; default=a)
  c - step (optional; default=1)
  v - the value to POKE; prefix the value with '^' to perform an XOR operation,
      or '+' to perform an ADD operation

  For example:

  --ram poke=24576,16        # POKE 24576,16
  --ram poke=30000-30002,^85 # Perform 'XOR 85' on addresses 30000-30002
  --ram poke=40000-40004-2,1 # POKE 40000,1: POKE 40002,1: POKE 40004,1
""".lstrip())

def _print_reg_help():
    reg_names = ', '.join(sorted(Z80_REGISTERS.keys()))
    sys.stdout.write("""
Usage: --reg name=value

Set the value of a register or register pair. For example:

  --reg hl=32768
  --reg b=17

To set the value of an alternate (shadow) register, use the '^' prefix:

  --reg ^hl=10072

Recognised register names are:

  {}
""".format('\n  '.join(textwrap.wrap(reg_names, 70))).lstrip())

def _print_state_help():
    sys.stdout.write("""
Usage: --state name=value

Set a hardware state attribute. Recognised names and their default values are:

  border - border colour (default=0)
  iff    - interrupt flip-flop: 0=disabled, 1=enabled (default=1)
  im     - interrupt mode (default=1)
""".lstrip())

def _make_z80(url, namespace, z80):
    tape_type, tape = _get_tape(url)
    tape_blocks = _get_tape_blocks(tape_type, tape)
    ram = _get_ram(tape_blocks, namespace)
    _write_z80(ram, namespace, z80)

def main(args):
    parser = SkoolKitArgumentParser(
        usage='\n  tap2sna.py [options] INPUT snapshot.z80\n  tap2sna.py @FILE',
        description="Convert a TAP or TZX file (which may be inside a zip archive) into a Z80 snapshot. "
                    "INPUT may be the full URL to a remote zip archive or TAP/TZX file, or the path to a local file. "
                    "Arguments may be read from FILE instead of (or as well as) being given on the command line.",
        fromfile_prefix_chars='@',
        add_help=False
    )
    parser.add_argument('args', help=argparse.SUPPRESS, nargs='*')
    group = parser.add_argument_group('Options')
    group.add_argument('-d', '--output-dir', dest='output_dir', metavar='DIR',
                       help="Write the snapshot file in this directory.")
    group.add_argument('-f', '--force', action='store_true',
                       help="Overwrite an existing snapshot.")
    group.add_argument('--ram', dest='ram_ops', metavar='OPERATION', action='append', default=[],
                       help="Perform a load, move or poke operation on the memory snapshot being built. "
                            "Do '--ram help' for more information. This option may be used multiple times.")
    group.add_argument('--reg', dest='reg', metavar='name=value', action='append', default=[],
                       help="Set the value of a register. Do '--reg help' for more information. "
                            "This option may be used multiple times.")
    group.add_argument('--state', dest='state', metavar='name=value', action='append', default=[],
                       help="Set a hardware state attribute. Do '--state help' for more information. "
                            "This option may be used multiple times.")
    group.add_argument('-V', '--version', action='version', version='SkoolKit {}'.format(VERSION),
                       help='Show SkoolKit version number and exit.')
    namespace, unknown_args = parser.parse_known_args(args)
    if 'help' in namespace.ram_ops:
        _print_ram_help()
        return
    if 'help' in namespace.reg:
        _print_reg_help()
        return
    if 'help' in namespace.state:
        _print_state_help()
        return
    if unknown_args or len(namespace.args) != 2:
        parser.exit(2, parser.format_help())
    url, z80 = namespace.args
    if namespace.output_dir:
        z80 = os.path.join(namespace.output_dir, z80)
    if namespace.force or not os.path.isfile(z80):
        try:
            _make_z80(url, namespace, z80)
        except Exception as e:
            raise SkoolKitError("Error while getting snapshot {0}: {1}".format(os.path.basename(z80), e.args[0]))
    else:
        write_line('{0}: file already exists; use -f to overwrite'.format(z80))
