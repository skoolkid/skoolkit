# Copyright 2013, 2015-2018, 2020, 2021 Richard Dymond (rjdymond@gmail.com)
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
import tempfile
import zipfile
from urllib.request import Request, urlopen
from urllib.parse import urlparse

from skoolkit import (SkoolKitError, get_dword, get_int_param, get_word,
                      get_word3, integer, open_file, write_line, VERSION)
from skoolkit.snapshot import move, poke, print_reg_help, print_state_help, write_z80v3

SYSVARS = (
    255, 0, 0, 0,         # 23552 - KSTATE0
    255, 0, 0, 0,         # 23556 - KSTATE4
    0,                    # 23560 - LAST-K
    35,                   # 23561 - REPDEL
    5,                    # 23562 - REPPER
    0, 0,                 # 23563 - DEFADD
    0,                    # 23565 - K-DATA
    0, 0,                 # 23566 - TVDATA
    1, 0,                 # 23568 - STRMS - stream 253 (keyboard)
    6, 0,                 # 23570 - STRMS - stream 254 (screen)
    11, 0,                # 23572 - STRMS - stream 255 (work space)
    1, 0,                 # 23574 - STRMS - stream 0 (keyboard)
    1, 0,                 # 23576 - STRMS - stream 1 (keyboard)
    6, 0,                 # 23578 - STRMS - stream 2 (screen)
    16, 0,                # 23580 - STRMS - stream 3 (printer)
    0, 0,                 # 23582 - STRMS - stream 4
    0, 0,                 # 23584 - STRMS - stream 5
    0, 0,                 # 23586 - STRMS - stream 6
    0, 0,                 # 23588 - STRMS - stream 7
    0, 0,                 # 23590 - STRMS - stream 8
    0, 0,                 # 23592 - STRMS - stream 9
    0, 0,                 # 23594 - STRMS - stream 10
    0, 0,                 # 23596 - STRMS - stream 11
    0, 0,                 # 23598 - STRMS - stream 12
    0, 0,                 # 23600 - STRMS - stream 13
    0, 0,                 # 23602 - STRMS - stream 14
    0, 0,                 # 23604 - STRMS - stream 15
    0, 60,                # 23606 - CHARS
    64,                   # 23608 - RASP
    0,                    # 23609 - PIP
    0,                    # 23610 - ERR-NR
    0,                    # 23611 - FLAGS
    33,                   # 23612 - TV-FLAG
    84, 255,              # 23613 - ERR-SP
    0, 0,                 # 23615 - LIST-SP
    0,                    # 23617 - MODE
    0, 0,                 # 23618 - NEWPPC
    0,                    # 23620 - NSPPC
    0, 0,                 # 23621 - PPC
    0,                    # 23623 - SUBPPC
    56,                   # 23624 - BORDCR
    0, 0,                 # 23625 - E-PPC
    203, 92,              # 23627 - VARS
    0, 0,                 # 23629 - DEST
    182, 92,              # 23631 - CHANS
    182, 92,              # 23633 - CURCHL
    203, 92,              # 23635 - PROG
    0, 0,                 # 23637 - NXTLIN
    202, 92,              # 23639 - DATADD
    204, 92,              # 23641 - E-LINE
    0, 0,                 # 23643 - K-CUR
    0, 0,                 # 23645 - CH-ADD
    0, 0,                 # 23647 - X-PTR
    206, 92,              # 23649 - WORKSP
    206, 92,              # 23651 - STKBOT
    206, 92,              # 23653 - STKEND
    0,                    # 23655 - BREG
    0, 0,                 # 23656 - MEM
    16,                   # 23658 - FLAGS2
    2,                    # 23659 - DF-SZ
    0, 0,                 # 23660 - S-TOP
    0, 0,                 # 23662 - OLDPPC
    0,                    # 23664 - OSPCC
    0,                    # 23665 - FLAGX
    0, 0,                 # 23666 - STRLEN
    0, 0,                 # 23668 - T-ADDR
    0, 0,                 # 23670 - SEED
    0, 0, 0,              # 23672 - FRAMES
    88, 255,              # 23675 - UDG
    0, 0,                 # 23677 - COORDS
    33,                   # 23679 - P-POSN
    0, 91,                # 23680 - PR-CC
    5, 23,                # 23682 - ECHO-E
    0, 64,                # 23684 - DF-CC
    252, 80,              # 23686 - DF-CCL
    33, 24,               # 23688 - S-POSN
    5, 23,                # 23690 - SPOSN-L
    1,                    # 23692 - SCR-CT
    56,                   # 23693 - ATTR-P
    0,                    # 23694 - MASK-P
    56,                   # 23695 - ATTR-T
    0,                    # 23696 - MASK-T
    0,                    # 23697 - P-FLAG
    0, 0, 0, 0, 0,        # 23698 - mem-0
    0, 0, 0, 0, 0,        # 23703 - mem-1
    0, 0, 0, 0, 0,        # 23708 - mem-2
    0, 0, 0, 0, 0,        # 23713 - mem-3
    0, 0, 0, 0, 0,        # 23718 - mem-4
    0, 0, 0, 0, 0,        # 23723 - mem-5
    0, 0,                 # 23728 = NMIADD
    87, 255,              # 23730 - RAMTOP
    255, 255,             # 23732 - P-RAMT
    244, 9, 168, 16, 75,  # 23734 - CHINFO - keyboard
    244, 9, 196, 21, 83,  # 23739 - CHINFO - screen
    129, 15, 196, 21, 82, # 23744 - CHINFO - work space
    244, 9, 196, 21, 80,  # 23749 - CHINFO - printer
    128                   # 23754 - CHINFO - end marker
)

class SkoolKitArgumentParser(argparse.ArgumentParser):
    def convert_arg_line_to_args(self, arg_line):
        for arg in arg_line.split():
            if arg in (';', '#'):
                break
            yield arg

class TapeError(Exception):
    pass

def _write_z80(ram, options, fname):
    parent_dir = os.path.dirname(fname)
    if parent_dir and not os.path.isdir(parent_dir):
        os.makedirs(parent_dir)
    write_line('Writing {0}'.format(fname))
    write_z80v3(fname, ram, options.reg, options.state)

def _get_load_params(param_str):
    params = []
    for index, n in enumerate(param_str.split(',')):
        if index == 0:
            params.append(n)
        elif n:
            params.append(get_int_param(n, True))
        else:
            params.append(None)
    params += [None] * (6 - len(params))
    return params[:6]

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
    try:
        block_num, start, length, step, offset, inc = _get_load_params(param_str)
    except ValueError:
        raise SkoolKitError('Invalid integer in load spec: {}'.format(param_str))
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

def _get_ram(blocks, options):
    snapshot = [0] * 65536

    operations = []
    standard_load = True
    for spec in options.ram_ops:
        op_type, sep, param_str = spec.partition('=')
        if op_type in ('load', 'move', 'poke', 'sysvars'):
            operations.append((op_type, param_str))
            if op_type == 'load':
                standard_load = False
        else:
            raise SkoolKitError("Invalid operation: {}".format(spec))

    if standard_load:
        start = None
        for block_num, block in enumerate(blocks, 1):
            if block:
                if block[0] == 0 and len(block) >= 19:
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
                elif block[0] == 255 and start is not None:
                    # Data
                    _load_block(snapshot, block, start)
                    start = None

    counters = {}
    for op_type, param_str in operations:
        if op_type == 'load':
            _load(snapshot, counters, blocks, param_str)
        elif op_type == 'move':
            move(snapshot, param_str)
        elif op_type == 'poke':
            poke(snapshot, param_str)
        elif op_type == 'sysvars':
            snapshot[23552:23755] = SYSVARS

    return snapshot[16384:]

def _get_tzx_block(data, i):
    # https://worldofspectrum.net/features/TZXformat.html
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

def _get_tape(urlstring, user_agent, member=None):
    url = urlparse(urlstring)
    if url.scheme:
        write_line('Downloading {0}'.format(urlstring))
        r = Request(urlstring, headers={'User-Agent': user_agent})
        u = urlopen(r, timeout=30)
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
                f.close()
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
       --ram poke=a[-b[-c]],[^+]v
       --ram sysvars

Load data from a tape block, move a block of bytes from one location to
another, POKE a single address or range of addresses with a given value, or
initialise the system variables.

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
  --ram load=2,0xC000      # Load the remainder at 49152

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

--ram sysvars

  Intialise the system variables at 23552-23754 (5C00-5CCA) with values
  suitable for a 48K ZX Spectrum.
""".lstrip())

def make_z80(url, options, z80):
    tape_type, tape = _get_tape(url, options.user_agent)
    tape_blocks = _get_tape_blocks(tape_type, tape)
    ram = _get_ram(tape_blocks, options)
    _write_z80(ram, options, z80)

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
    group.add_argument('-p', '--stack', dest='stack', metavar='STACK', type=integer,
                       help="Set the stack pointer.")
    group.add_argument('--ram', dest='ram_ops', metavar='OPERATION', action='append', default=[],
                       help="Perform a load, move or poke operation or initialise the system variables in the memory snapshot being built. "
                            "Do '--ram help' for more information. This option may be used multiple times.")
    group.add_argument('--reg', dest='reg', metavar='name=value', action='append', default=[],
                       help="Set the value of a register. Do '--reg help' for more information. "
                            "This option may be used multiple times.")
    group.add_argument('-s', '--start', dest='start', metavar='START', type=integer,
                       help="Set the start address to JP to.")
    group.add_argument('--state', dest='state', metavar='name=value', action='append', default=[],
                       help="Set a hardware state attribute. Do '--state help' for more information. "
                            "This option may be used multiple times.")
    group.add_argument('-u', '--user-agent', dest='user_agent', metavar='AGENT', default='',
                       help="Set the User-Agent header.")
    group.add_argument('-V', '--version', action='version', version='SkoolKit {}'.format(VERSION),
                       help='Show SkoolKit version number and exit.')
    namespace, unknown_args = parser.parse_known_args(args)
    if 'help' in namespace.ram_ops:
        _print_ram_help()
        return
    if 'help' in namespace.reg:
        print_reg_help()
        return
    if 'help' in namespace.state:
        print_state_help()
        return
    if unknown_args or len(namespace.args) != 2:
        parser.exit(2, parser.format_help())
    url, z80 = namespace.args
    if namespace.output_dir:
        z80 = os.path.join(namespace.output_dir, z80)
    if namespace.stack is not None:
        namespace.reg.append('sp={}'.format(namespace.stack))
    if namespace.start is not None:
        namespace.reg.append('pc={}'.format(namespace.start))
    if namespace.force or not os.path.isfile(z80):
        try:
            make_z80(url, namespace, z80)
        except Exception as e:
            raise SkoolKitError("Error while getting snapshot {}: {}".format(os.path.basename(z80), e.args[0] if e.args else e))
    else:
        write_line('{0}: file already exists; use -f to overwrite'.format(z80))
