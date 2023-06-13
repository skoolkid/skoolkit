# Copyright 2013, 2015-2018, 2020-2023 Richard Dymond (rjdymond@gmail.com)
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
import hashlib
import tempfile
import zipfile
from urllib.request import Request, urlopen
from urllib.parse import urlparse

from skoolkit import (SkoolKitError, get_dword, get_int_param, get_object,
                      get_word, get_word3, integer, open_file, parse_int,
                      read_bin_file, warn, write_line, ROM48, VERSION)
from skoolkit.config import get_config, show_config, update_options
from skoolkit.loadsample import ACCELERATORS
from skoolkit.loadtracer import LoadTracer, get_edges
from skoolkit.simulator import (Simulator, A, F, B, C, D, E, H, L, IXh, IXl, IYh, IYl,
                                SP, I, R, xA, xF, xB, xC, xD, xE, xH, xL, PC)
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
    0, 0,                 # 23728 - NMIADD
    87, 255,              # 23730 - RAMTOP
    255, 255,             # 23732 - P-RAMT
    244, 9, 168, 16, 75,  # 23734 - CHINFO - keyboard
    244, 9, 196, 21, 83,  # 23739 - CHINFO - screen
    129, 15, 196, 21, 82, # 23744 - CHINFO - work space
    244, 9, 196, 21, 80,  # 23749 - CHINFO - printer
    128                   # 23754 - CHINFO - end marker
)

SIM_LOAD_PATCH = {
    0x5C04: 0x050D, # KSTATE4 0/1
    0x5C06: 0x0D23, # KSTATE4 2/3
    0x5C08: 0x0D,   # LAST-K
    0x5C3A: 0xFF,   # ERR-NR
    0x5C3B: 0x0C,   # FLAGS
    0x5C3C: 0x01,   # TV-FLAG
    0x5C47: 0x01,   # SUBPPC
    0x5C5B: 0x5CCF, # K-CUR
    0x5C5D: 0x5CCD, # CH-ADD
    0x5C61: 0x5CD1, # WORKSP
    0x5C63: 0x5CD1, # STKBOT
    0x5C65: 0x5CD1, # STKEND
    0x5C68: 0x5C92, # MEM
    0x5C74: 0x1AE1, # T-ADDR
    0x5C82: 0x19,   # ECHO-E
    0x5C86: 0xE0,   # DF-CCL
    0x5C8A: 0x21,   # S-POSNL
    0x5CCB: 0x80,   # First byte of program area
    0x5CCC: 0xEF,   # LOAD
    0x5CCD: 0x2222, # ""
    0x5CCF: 0x0D,   # ENTER
    0x5CD0: 0x80,   # End of program area
    0xFF18: 0x0DF3, # Stack...
    0xFF1A: 0x0BCE,
    0xFF1C: 0x50E3,
    0xFF1E: 0x0BCE,
    0xFF20: 0x50E4,
    0xFF22: 0x171D,
    0xFF24: 0x0ADC,
    0xFF26: 0x0BCE,
    0xFF28: 0x50E7,
    0xFF2A: 0x171A,
    0xFF2C: 0x0ADC,
    0xFF2E: 0x18D7,
    0xFF30: 0x0038,
    0xFF32: 0x0038,
    0xFF34: 0x190D,
    0xFF36: 0x5CCF,
    0xFF38: 0x0306,
    0xFF3A: 0x5C07,
    0xFF3C: 0x004D,
    0xFF3E: 0x33B1,
    0xFF40: 0x5C92,
    0xFF42: 0x0005,
    0xFF44: 0x32C8,
    0xFF46: 0x3429,
    0xFF48: 0x369B,
    0xFF4A: 0x001F,
    0xFF4C: 0x1B6D,
    0xFF4E: 0x1CDB,
    0xFF50: 0x1B52, # Address of SCAN-LOOP
    0xFF52: 0x1B76, # Address of STMT-RET
    0xFF54: 0x12B7, # Address of entry point in 'MAIN EXECUTION' loop at 0x12A2
    0xFF56: 0x3E00  # RAMTOP marker
}

SIM_LOAD_CODE_PATCH = {
    0x5C5B: 0x5CD0, # K-CUR
    0x5C61: 0x5CD2, # WORKSP
    0x5C63: 0x5CD2, # STKBOT
    0x5C65: 0x5CD2, # STKEND
    0x5C82: 0x14,   # ECHO-E
    0x5CCF: 0xAF,   # CODE
    0x5CD0: 0x0D,   # ENTER
    0x5CD1: 0x80,   # End of program area
    0xFF1C: 0x50EA, # Stack...
    0xFF20: 0x50EB,
    0xFF22: 0x1716,
    0xFF28: 0x50EC,
    0xFF2A: 0x1715,
    0xFF30: 0x000A,
    0xFF36: 0x5CD0
}

class SkoolKitArgumentParser(argparse.ArgumentParser):
    def convert_arg_line_to_args(self, arg_line):
        args = []
        arg = ''
        q = None
        for c in arg_line:
            if c == q:
                args.append(arg)
                arg = ''
                q = None
            elif c in '\'"' and q is None:
                q = c
            elif c.isspace() and q is None:
                if arg:
                    args.append(arg)
                    arg = ''
            elif c in ';#' and q is None:
                break
            else:
                arg += c
        if arg:
            args.append(arg)
        return args

class TapeError(Exception):
    pass

class TapeBlockTimings:
    def __init__(self, pilot_len=0, pilot=0, sync=(), zero=0, one=0, pause=0, used_bits=8):
        self.pilot_len = pilot_len
        self.pilot = pilot
        self.sync = sync
        self.zero = zero
        self.one = one
        self.pause = pause
        self.used_bits = used_bits

def get_tape_block_timings(first_byte, pause=3500000):
    if first_byte == 0:
        # Header block
        return TapeBlockTimings(8063, 2168, (667, 735), 855, 1710, pause)
    # Data block
    return TapeBlockTimings(3223, 2168, (667, 735), 855, 1710, pause)

def _write_z80(ram, options, fname):
    parent_dir = os.path.dirname(fname)
    if parent_dir and not os.path.isdir(parent_dir):
        os.makedirs(parent_dir)
    write_line('Writing {0}'.format(fname))
    write_z80v3(fname, ram, options.reg, options.state)

def _ram_operations(snapshot, ram_ops, blocks=None):
    counters = {}
    for spec in ram_ops:
        op_type, sep, param_str = spec.partition('=')
        if op_type == 'call':
            _call(snapshot, param_str)
        elif op_type == 'load':
            if blocks:
                _load(snapshot, counters, blocks, param_str)
        elif op_type == 'move':
            move(snapshot, param_str)
        elif op_type == 'poke':
            poke(snapshot, param_str)
        elif op_type == 'sysvars':
            snapshot[23552:23755] = SYSVARS
        else:
            raise SkoolKitError(f'Invalid operation: {spec}')

def _set_sim_load_config(options):
    options.accelerate_dec_a = 1
    options.accelerator = 'auto'
    options.contended_in = False
    options.fast_load = True
    options.finish_tape = False
    options.first_edge = -2168
    options.pause = True
    options.timeout = 900
    options.trace = None
    for spec in options.sim_load_config:
        name, sep, value = spec.lower().partition('=')
        if sep:
            if name == 'accelerate-dec-a': # pragma: no cover
                options.accelerate_dec_a = parse_int(value, options.accelerate_dec_a)
            elif name == 'accelerator':
                options.accelerator = value
            elif name == 'contended-in': # pragma: no cover
                options.contended_in = parse_int(value, options.contended_in)
            elif name == 'fast-load': # pragma: no cover
                options.fast_load = parse_int(value, options.fast_load)
            elif name == 'finish-tape': # pragma: no cover
                options.finish_tape = parse_int(value, options.finish_tape)
            elif name == 'first-edge': # pragma: no cover
                options.first_edge = parse_int(value, options.first_edge)
            elif name == 'pause': # pragma: no cover
                options.pause = parse_int(value, options.pause)
            elif name == 'timeout': # pragma: no cover
                options.timeout = parse_int(value, options.timeout)
            elif name == 'trace':
                options.trace = value
            else:
                raise SkoolKitError(f'Invalid sim-load configuration parameter: {name}')

def sim_load(blocks, options, config):
    _set_sim_load_config(options)
    if options.tape_analysis:
        get_edges(blocks, options.first_edge, True)
        sys.exit(0)
    list_accelerators = options.accelerator == 'list'
    accelerators = set()
    if options.accelerator == 'auto' or list_accelerators:
        accelerators.update(ACCELERATORS.values())
    elif options.accelerator and options.accelerator != 'none':
        for name in options.accelerator.split(','):
            if name in ACCELERATORS:
                accelerators.add(ACCELERATORS[name]) # pragma: no cover
            else:
                raise SkoolKitError(f'Unrecognised accelerator: {name}')
    snapshot = [0] * 65536
    rom = read_bin_file(ROM48, 16384)
    snapshot[:len(rom)] = rom
    snapshot[0x5800:0x5B00] = [56] * 768 # PAPER 7: INK 0
    snapshot[0x5C00:0x5C00 + len(SYSVARS)] = SYSVARS
    for a, b in SIM_LOAD_PATCH.items():
        snapshot[a] = b % 256
        if b > 0xFF:
            snapshot[a + 1] = b // 256
    block1_data = blocks[0][1]
    if len(block1_data) >= 19 and tuple(block1_data[0:2]) == (0, 3):
        for a, b in SIM_LOAD_CODE_PATCH.items():
            snapshot[a] = b % 256
            if b > 0xFF:
                snapshot[a + 1] = b // 256
    snapshot[0xFF58:] = snapshot[0x3E08:0x3EB0] # UDGs
    simulator = Simulator(snapshot, {'SP': 0xFF50})
    if options.contended_in: # pragma: no cover
        in_min_addr = 0x4000
    else:
        in_min_addr = 0x8000
    tracer = LoadTracer(simulator, blocks, accelerators, options.pause, options.first_edge,
                        options.finish_tape, in_min_addr, options.accelerate_dec_a, list_accelerators)
    simulator.set_tracer(tracer, False, False)
    op_fmt = config['TraceOperand']
    prefix, byte_fmt, word_fmt = (op_fmt + ',' * (2 - op_fmt.count(','))).split(',')[:3]
    try:
        # Begin execution at 0x0605 (SAVE-ETC)
        tracer.run(0x0605, options.start, options.fast_load, options.timeout * 3500000,
                   options.trace, config['TraceLine'] + '\n', prefix, byte_fmt, word_fmt)
        _ram_operations(snapshot, options.ram_ops)
    except KeyboardInterrupt: # pragma: no cover
        write_line(f'Simulation stopped (interrupted): PC={simulator.registers[PC]}')
    if list_accelerators: # pragma: no cover
        accelerators = '; '.join(f'{k}: {v}' for k, v in tracer.accelerators.items()) or 'none'
        write_line(f'Accelerators: {accelerators}; misses: {tracer.inc_b_misses}/{tracer.dec_b_misses}')
    sim_registers = simulator.registers
    registers = {
        'A': sim_registers[A],
        'F': sim_registers[F],
        'B': sim_registers[B],
        'C': sim_registers[C],
        'D': sim_registers[D],
        'E': sim_registers[E],
        'H': sim_registers[H],
        'L': sim_registers[L],
        'IX': sim_registers[IXl] + 256 * sim_registers[IXh],
        'IY': sim_registers[IYl] + 256 * sim_registers[IYh],
        'I': sim_registers[I],
        'R': sim_registers[R],
        'SP': sim_registers[SP],
        '^A': sim_registers[xA],
        '^F': sim_registers[xF],
        '^B': sim_registers[xB],
        '^C': sim_registers[xC],
        '^D': sim_registers[xD],
        '^E': sim_registers[xE],
        '^H': sim_registers[xH],
        '^L': sim_registers[xL],
        'PC': sim_registers[PC]
    }
    options.reg = [f'{r}={v}' for r, v in registers.items()] + options.reg
    state = [f'im={simulator.imode}', f'iff={simulator.iff}', f'border={tracer.border}']
    options.state = state + options.state
    return simulator.memory[0x4000:]

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

def _call(snapshot, param_str):
    try:
        get_object(param_str)(snapshot)
    except TypeError as e:
        raise SkoolKitError(e.args[0])

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
    standard_load = True
    for spec in options.ram_ops:
        if spec.partition('=')[0] == 'load':
            standard_load = False
            break

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
                elif block[0] == 255:
                    if start is None:
                        warn(f'Ignoring headerless block {block_num}')
                    else:
                        # Data
                        _load_block(snapshot, block, start)
                        start = None

    _ram_operations(snapshot, options.ram_ops, blocks)
    return snapshot[16384:]

def _get_tzx_block(data, i, sim):
    # https://worldofspectrum.net/features/TZXformat.html
    block_id = data[i]
    tape_data = None
    timings = None
    i += 1
    if block_id == 16:
        # Standard speed data block
        pause = get_word(data, i) * 3500
        length = get_word(data, i + 2)
        tape_data = data[i + 4:i + 4 + length]
        if tape_data:
            timings = get_tape_block_timings(tape_data[0], pause)
        i += 4 + length
    elif block_id == 17:
        # Turbo speed data block
        length = get_word3(data, i + 15)
        tape_data = data[i + 18:i + 18 + length]
        pilot = get_word(data, i)
        sync1 = get_word(data, i + 2)
        sync2 = get_word(data, i + 4)
        zero = get_word(data, i + 6)
        one = get_word(data, i + 8)
        pilot_len = get_word(data, i + 10)
        used_bits = data[i + 12]
        pause = get_word(data, i + 13) * 3500
        timings = TapeBlockTimings(pilot_len, pilot, (sync1, sync2), zero, one, pause, used_bits)
        i += 18 + length
    elif block_id == 18:
        # Pure tone
        if sim: # pragma: no cover
            tape_data = []
            pilot = get_word(data, i)
            pilot_len = get_word(data, i + 2)
            timings = TapeBlockTimings(pilot_len, pilot)
        i += 4
    elif block_id == 19:
        # Sequence of pulses of various lengths
        length = 2 * data[i]
        if sim: # pragma: no cover
            tape_data = []
            pulses = [get_word(data, j) for j in range(i + 1, i + 1 + length, 2)]
            timings = TapeBlockTimings(sync=pulses)
        i += length + 1
    elif block_id == 20:
        # Pure data block
        length = get_word3(data, i + 7)
        tape_data = data[i + 10:i + 10 + length]
        if sim: # pragma: no cover
            zero = get_word(data, i)
            one = get_word(data, i + 2)
            used_bits = data[i + 4]
            pause = get_word(data, i + 5) * 3500
            timings = TapeBlockTimings(zero=zero, one=one, pause=pause, used_bits=used_bits)
        i += 10 + length
    elif block_id == 21:
        # Direct recording block
        if sim:
            raise TapeError("TZX Direct Recording (0x15) not supported")
        i += get_word3(data, i + 5) + 8
    elif block_id == 24:
        # CSW recording block
        if sim:
            raise TapeError("TZX CSW Recording (0x18) not supported")
        i += get_dword(data, i) + 4
    elif block_id == 25:
        # Generalized data block
        if sim:
            raise TapeError("TZX Generalized Data Block (0x19) not supported")
        i += get_dword(data, i) + 4
    elif block_id == 32:
        # Pause (silence) or 'Stop the tape' command
        if sim: # pragma: no cover
            pause = get_word(data, i) * 3500
            timings = TapeBlockTimings(pause=pause)
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
    return i, block_id, timings, tape_data

def _get_tzx_blocks(data, sim, start, stop):
    signature = ''.join(chr(b) for b in data[:7])
    if signature != 'ZXTape!':
        raise TapeError("Not a TZX file")
    i = 10
    blocks = []
    block_num = 1
    loop = None
    while i < len(data):
        if block_num >= stop > 0:
            break
        i, block_id, timings, tape_data = _get_tzx_block(data, i, sim)
        if block_num >= start:
            if sim: # pragma: no cover
                if block_id == 0x20:
                    if stop == 0 and timings.pause == 0:
                        break
                elif block_id == 0x24:
                    loop = []
                    repetitions = get_word(data, i - 2)
                elif block_id == 0x2A and stop == 0:
                    # Stop the tape if in 48K mode
                    break
            if loop is None:
                blocks.append((timings, tape_data))
            else: # pragma: no cover
                loop.append((timings, tape_data))
            if block_id == 0x25 and loop is not None: # pragma: no cover
                blocks.extend(loop * repetitions)
                loop = None
        block_num += 1
    return blocks

def get_tap_blocks(tap, start=1, stop=0):
    blocks = []
    block_num = 1
    i = 0
    while i + 1 < len(tap):
        if block_num >= stop > 0:
            break # pragma: no cover (tested but missed by coverage)
        block_len = tap[i] + 256 * tap[i + 1]
        i += 2
        if block_num >= start:
            data = tap[i:i + block_len]
            if data:
                timings = get_tape_block_timings(data[0])
                blocks.append((timings, data))
        i += block_len
        block_num += 1
    return blocks

def _get_tape_blocks(tape_type, tape, sim, start, stop):
    if tape_type.lower() == 'tzx':
        return _get_tzx_blocks(tape, sim, start, stop)
    return get_tap_blocks(tape, start, stop)

def _get_tape(urlstring, user_agent, member):
    url = urlparse(urlstring)
    if url.scheme:
        write_line('Downloading {0}'.format(urlstring))
        r = Request(urlstring, headers={'User-Agent': user_agent})
        u = urlopen(r, timeout=30)
        f = tempfile.NamedTemporaryFile(prefix='tap2sna-')
        while 1:
            data = bytearray(u.read(4096))
            if not data:
                break
            f.write(data)
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
        try:
            tape = z.open(member)
        except KeyError:
            raise TapeError(f'No file named "{member}" in the archive')
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
Usage: --ram call=[/path/to/moduledir:]module.function
       --ram load=[+]block[+],start[,length,step,offset,inc]
       --ram move=src,size,dest
       --ram poke=a[-b[-c]],[^+]v
       --ram sysvars

Load data from a tape block, move a block of bytes from one location to
another, POKE a single address or range of addresses with a given value,
initialise the system variables, or call a Python function to modify the memory
snapshot in an arbitrary way.

--ram call=[/path/to/moduledir:]module.function

  Call a Python function to modify the memory snapshot. The function is called
  with the memory snapshot (a list of 65536 byte values) as the sole positional
  argument. The function must modify the snapshot in place. The path to the
  module's location may be omitted if the module is already in the module
  search path.

  For example:

  --ram call=:ram.modify # Call modify(snapshot) in ./ram.py

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

  Initialise the system variables at 23552-23754 (5C00-5CCA) with values
  suitable for a 48K ZX Spectrum.
""".lstrip())

def _print_sim_load_config_help():
    width = max(len(n) for n in ACCELERATORS) + 2
    names = [n.ljust(width) for n in sorted(ACCELERATORS)]
    num_cols = 3
    names += [''] * (-len(names) % num_cols)
    cl = len(names) // num_cols
    columns = [names[i:i + cl] for i in range(0, len(names), cl)]
    accelerators = '\n  '.join(''.join(n) for n in zip(*columns))
    print(f"""
Usage: --sim-load-config accelerate-dec-a=0/1/2
       --sim-load-config accelerator=NAME
       --sim-load-config contended-in=0/1
       --sim-load-config fast-load=0/1
       --sim-load-config finish-tape=0/1
       --sim-load-config first-edge=N
       --sim-load-config pause=0/1
       --sim-load-config timeout=N
       --sim-load-config trace=FILE

Configure various properties of a simulated LOAD.

--sim-load-config accelerate-dec-a=0/1/2

  Specify whether to accelerate 'DEC A: JR NZ,$-1' loops (1, the default), or
  'DEC A: JP NZ,$-1' loops (2), or neither (0).

--sim-load-config accelerator=auto/none/list/NAME[,NAME...]

  Use one or more specific accelerators to speed up the simulation of the
  tape-sampling loops in a loading routine, disable acceleration entirely, or
  list the accelerators used during a simulated LOAD. (By default, appropriate
  accelerators are automatically selected, if available.) Recognised
  accelerator names are:

  {accelerators}

--sim-load-config contended-in=0/1

  By default, 'IN A,($FE)' instructions in RAM are ignored (i.e. are not
  interpreted as reading the tape) unless they are at address $8000 or above.
  Set contended-in=1 to enable 'IN A,($FE)' instructions in the address range
  $4000-$7FFF to read the tape as well.

--sim-load-config fast-load=0/1

  By default, whenever the Spectrum ROM's load routine is called, a shortcut is
  taken by "fast loading" the next block on the tape. This significantly
  reduces the load time for many tapes, but can also cause some loaders to
  fail. Set fast-load=0 to disable fast loading.

--sim-load-config finish-tape=0/1

  By default, the simulated LOAD stops as soon as the program counter hits the
  address specified by the '--start' option (if any), regardless of whether the
  tape has finished running. Set finish-tape=1 to ensure that the end of the
  tape is reached before stopping the simulation at the given start address.

--sim-load-config first-edge=N

  Set the time (in T-states) from the start of the tape at which to place the
  leading edge of the first pulse (default: -2168). The default value places
  the trailing edge of the first pulse at time 0, but some loaders (e.g.
  polarity-sensitive loaders) require first-edge=0.

--sim-load-config pause=0/1

  By default, the tape is paused between blocks, and resumed whenever port 254
  is read. While this can help with tapes that require (but do not actually
  contain) long pauses between blocks, it can cause some loaders to fail. Set
  pause=0 to disable this behaviour and run the tape continuously.

--sim-load-config timeout=N

  Set the timeout to N seconds (default: 900). A simulated LOAD still in
  progress after this period of Z80 CPU time will automatically abort.

--sim-load-config trace=FILE

  Log to FILE all instructions executed during the simulated LOAD.
""".strip())

def make_z80(url, options, z80, config):
    tape_type, tape = _get_tape(url, options.user_agent, options.tape_name)
    if options.tape_sum:
        md5sum = hashlib.md5(tape).hexdigest()
        if md5sum != options.tape_sum:
            raise TapeError(f'Checksum mismatch: Expected {options.tape_sum}, actually {md5sum}')
    tape_blocks = _get_tape_blocks(tape_type, tape, options.sim_load, options.tape_start, options.tape_stop)
    if options.sim_load:
        blocks = [b for b in tape_blocks if b[0]]
        ram = sim_load(blocks, options, config)
    else:
        blocks = [b[1] for b in tape_blocks]
        ram = _get_ram(blocks, options)
    _write_z80(ram, options, z80)

def main(args):
    config = get_config('tap2sna')
    parser = SkoolKitArgumentParser(
        usage='\n  tap2sna.py [options] INPUT snapshot.z80\n  tap2sna.py --tape-analysis [options] INPUT\n  tap2sna.py @FILE [args]',
        description="Convert a TAP or TZX file (which may be inside a zip archive) into a Z80 snapshot. "
                    "INPUT may be the full URL to a remote zip archive or TAP/TZX file, or the path to a local file. "
                    "Arguments may be read from FILE instead of (or as well as) being given on the command line.",
        fromfile_prefix_chars='@',
        add_help=False
    )
    parser.add_argument('args', help=argparse.SUPPRESS, nargs='*')
    group = parser.add_argument_group('Options')
    group.add_argument('-c', '--sim-load-config', metavar='name=value', action='append', default=[],
                       help="Set the value of a --sim-load configuration parameter. "
                            "Do '-c help' for more information. This option may be used multiple times.")
    group.add_argument('-d', '--output-dir', dest='output_dir', metavar='DIR',
                       help="Write the snapshot file in this directory.")
    group.add_argument('-f', '--force', action='store_true',
                       help="Overwrite an existing snapshot.")
    group.add_argument('-I', '--ini', dest='params', metavar='p=v', action='append', default=[],
                       help="Set the value of the configuration parameter 'p' to 'v'. This option may be used multiple times.")
    group.add_argument('-p', '--stack', dest='stack', metavar='STACK', type=integer,
                       help="Set the stack pointer.")
    group.add_argument('--ram', dest='ram_ops', metavar='OPERATION', action='append', default=[],
                       help="Perform a load operation or otherwise modify the memory snapshot being built. "
                            "Do '--ram help' for more information. This option may be used multiple times.")
    group.add_argument('--reg', dest='reg', metavar='name=value', action='append', default=[],
                       help="Set the value of a register. Do '--reg help' for more information. "
                            "This option may be used multiple times.")
    group.add_argument('--show-config', dest='show_config', action='store_true',
                       help="Show configuration parameter values.")
    group.add_argument('-s', '--start', dest='start', metavar='START', type=integer,
                       help="Set the start address to JP to.")
    group.add_argument('--sim-load', action='store_true',
                       help='Simulate a 48K ZX Spectrum running LOAD "".')
    group.add_argument('--state', dest='state', metavar='name=value', action='append', default=[],
                       help="Set a hardware state attribute. Do '--state help' for more information. "
                            "This option may be used multiple times.")
    group.add_argument('--tape-analysis', action='store_true',
                       help="Show an analysis of the tape's tones, pulse sequences and data blocks.")
    group.add_argument('--tape-name', metavar='NAME',
                       help="Specify the name of a TAP/TZX file in a zip archive.")
    group.add_argument('--tape-start', metavar='BLOCK', type=int, default=1,
                       help="Start the tape at this block number.")
    group.add_argument('--tape-stop', metavar='BLOCK', type=int, default=0,
                       help="Stop the tape at this block number.")
    group.add_argument('--tape-sum', metavar='MD5SUM',
                       help="Specify the MD5 checksum of the TAP/TZX file.")
    group.add_argument('-u', '--user-agent', dest='user_agent', metavar='AGENT', default='',
                       help="Set the User-Agent header.")
    group.add_argument('-V', '--version', action='version', version='SkoolKit {}'.format(VERSION),
                       help='Show SkoolKit version number and exit.')
    namespace, unknown_args = parser.parse_known_args(args)
    if namespace.show_config:
        show_config('tap2sna', config)
    if 'help' in namespace.sim_load_config:
        _print_sim_load_config_help()
        return
    if 'help' in namespace.ram_ops:
        _print_ram_help()
        return
    if 'help' in namespace.reg:
        print_reg_help()
        return
    if 'help' in namespace.state:
        print_state_help()
        return
    if namespace.tape_analysis:
        if unknown_args or len(namespace.args) != 1:
            parser.exit(2, parser.format_help())
        namespace.args.append(None)
        namespace.sim_load = True
    if unknown_args or len(namespace.args) != 2:
        parser.exit(2, parser.format_help())
    url, z80 = namespace.args
    if namespace.output_dir:
        z80 = os.path.join(namespace.output_dir, z80)
    if namespace.stack is not None:
        namespace.reg.append('sp={}'.format(namespace.stack))
    if namespace.start is not None:
        namespace.reg.append('pc={}'.format(namespace.start))
    if z80 is None or namespace.force or not os.path.isfile(z80):
        update_options('tap2sna', namespace, namespace.params, config)
        try:
            make_z80(url, namespace, z80, config)
        except Exception as e:
            raise SkoolKitError("Error while getting snapshot {}: {}".format(os.path.basename(z80), e.args[0] if e.args else e))
    else:
        write_line('{0}: file already exists; use -f to overwrite'.format(z80))
