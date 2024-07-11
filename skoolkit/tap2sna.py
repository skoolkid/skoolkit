# Copyright 2013, 2015-2018, 2020-2024 Richard Dymond (rjdymond@gmail.com)
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

from skoolkit import (SkoolKitError, CSimulator, CCMIOSimulator, get_int_param,
                      get_object, get_word, integer, open_file, parse_int,
                      read_bin_file, write_line, ROM48, VERSION)
from skoolkit.cmiosimulator import CMIOSimulator
from skoolkit.config import get_config, show_config, update_options
from skoolkit.kbtracer import KeyboardTracer
from skoolkit.loadsample import ACCELERATORS
from skoolkit.loadtracer import LoadTracer, get_edges
from skoolkit.pagingtracer import Memory
from skoolkit.simulator import Simulator
from skoolkit.simutils import FRAME_DURATIONS, INT_ACTIVE, PC, T, get_state
from skoolkit.snapshot import move, poke, print_reg_help, print_state_help, write_snapshot
from skoolkit.tape import parse_pzx, parse_tap, parse_tzx

SUPPORTED_TAPES = ('.pzx', '.tap', '.tzx')

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

SIM_LOAD_CONFIG_HELP = """
Usage: --sim-load-config accelerate-dec-a=0/1/2
       --sim-load-config accelerator=NAME
       --sim-load-config cmio=0/1
       --sim-load-config fast-load=0/1
       --sim-load-config finish-tape=0/1
       --sim-load-config first-edge=N
       --sim-load-config in-flags=FLAGS
       --sim-load-config load=KEYS
       --sim-load-config machine=48/128
       --sim-load-config pause=0/1
       --sim-load-config polarity=0/1
       --sim-load-config python=0/1
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

--sim-load-config cmio=0/1

  By default, memory contention and I/O contention delays are not simulated.
  This improves performance and does not affect most loaders. Set cmio=1 to
  enable simulation of memory and I/O contention delays. Note that when cmio=1,
  all acceleration is disabled.

--sim-load-config fast-load=0/1

  By default, whenever the Spectrum ROM's load routine is called, a shortcut is
  taken by "fast loading" (also known as "flash loading") the next block on the
  tape. This significantly reduces the load time for many tapes, but can also
  cause some loaders to fail. Set fast-load=0 to disable fast loading.

--sim-load-config finish-tape=0/1

  By default, the simulated LOAD stops as soon as the program counter hits the
  address specified by the '--start' option (if any), regardless of whether the
  tape has finished running. Set finish-tape=1 to ensure that the end of the
  tape is reached before stopping the simulation at the given start address.

--sim-load-config first-edge=N

  Set the time (in T-states) from the start of the tape at which to place the
  leading edge of the first pulse (default: 0).

--sim-load-config in-flags=FLAGS

  Specify how to handle 'IN' instructions. FLAGS is the sum of the following
  values, chosen according to the desired behaviour:

    1 - interpret 'IN A,($FE)' instructions in the address range $4000-$7FFF as
        reading the tape (by default they are ignored)
    2 - ignore 'IN' instructions in the address range $4000-$FFFF (i.e. in RAM)
        that read port $FE
    4 - yield a simulated port reading when executing an 'IN r,(C)' instruction
        (by default such an instruction always yields the value $FF)

--sim-load-config load=KEYS

  By default, the simulated LOAD begins by executing either 'LOAD ""' or
  'LOAD ""CODE' (depending on whether the tape begins with a Bytes block). If
  an alternative command line is required to load the tape, it can be specified
  by this parameter. KEYS is a space-separated list of 'words' (a 'word' being
  a sequence of any characters other than space), each of which is broken down
  into a sequence of one or more keypresses. If a word contains the '+' symbol,
  the tokens it separates are converted into keypresses made simultaneously. If
  a word matches a BASIC token, the corresponding sequence of keypresses to
  produce that token are substituted. Otherwise, each character in the word is
  converted individually into the appropriate keypresses.

  The following special tokens are also recognised:

    CS         - CAPS SHIFT
    SS         - SYMBOL SHIFT
    SPACE      - SPACE
    ENTER      - ENTER
    DOWN       - Cursor down (CS+6)
    GOTO       - GO TO (g)
    GOSUB      - GO SUB (h)
    DEFFN      - DEF FN (CS+SS SS+1)
    OPEN#      - OPEN # (CS+SS SS+4)
    CLOSE#     - CLOSE # (CS+SS SS+5)
    PC=address - Stop the keyboard input simulation at this address

  The 'PC=address' token, if present, must appear last. The default address is
  either 0x0605 (when a 48K Spectrum is being simulated) or 0x13BE (on a 128K
  Spectrum). The simulated LOAD begins at this address.

  ENTER is automatically appended to the command line if not already present.

--sim-load-config machine=48/128

  By default, tap2sna.py simulates a 48K Spectrum. Set machine=128 to simulate
  a 128K Spectrum.

--sim-load-config pause=0/1

  By default, the tape is paused between blocks, and resumed whenever port 254
  is read. While this can help with tapes that require (but do not actually
  contain) long pauses between blocks, it can cause some loaders to fail. Set
  pause=0 to disable this behaviour and run the tape continuously.

--sim-load-config polarity=0/1

  By default, the first pulse on the tape produces an EAR bit reading of 0
  (polarity=0), and subsequent pulses give readings that alternate between 1
  and 0. This works for most loaders, but some require polarity=1.

--sim-load-config python=0/1

  By default, tap2sna.py will use the C version of the Z80 simulator if it's
  available. Set python=1 to force usage of the pure Python Z80 simulator.

--sim-load-config timeout=N

  Set the timeout to N seconds (default: 900). A simulated LOAD still in
  progress after this period of Z80 CPU time will automatically abort.

--sim-load-config trace=FILE

  Log to FILE all instructions executed during the simulated LOAD.
""".strip()

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

def _write_snapshot(ram, options, fname):
    parent_dir = os.path.dirname(fname)
    if parent_dir and not os.path.isdir(parent_dir):
        os.makedirs(parent_dir)
    write_line('Writing {0}'.format(fname))
    write_snapshot(fname, ram, options.reg, options.state)

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
    options.cmio = False
    options.fast_load = True
    options.finish_tape = False
    options.first_edge = 0
    options.in_flags = 0
    options.load = None
    options.machine = '48'
    options.pause = True
    options.polarity = 0
    options.python = 0
    options.timeout = 900
    options.trace = None
    for spec in options.sim_load_config:
        name, sep, value = spec.partition('=')
        if sep:
            if name == 'accelerate-dec-a':
                options.accelerate_dec_a = parse_int(value, options.accelerate_dec_a)
            elif name == 'accelerator':
                options.accelerator = value
            elif name == 'cmio':
                options.cmio = parse_int(value, options.cmio)
            elif name == 'fast-load':
                options.fast_load = parse_int(value, options.fast_load)
            elif name == 'finish-tape':
                options.finish_tape = parse_int(value, options.finish_tape)
            elif name == 'first-edge':
                options.first_edge = parse_int(value, options.first_edge)
            elif name == 'in-flags':
                options.in_flags = parse_int(value, options.in_flags)
            elif name == 'load':
                options.load = value
            elif name == 'machine':
                options.machine = value
            elif name == 'pause':
                options.pause = parse_int(value, options.pause)
            elif name == 'polarity':
                options.polarity = parse_int(value, options.polarity)
            elif name == 'python':
                options.python = parse_int(value, options.python)
            elif name == 'timeout':
                options.timeout = parse_int(value, options.timeout)
            elif name == 'trace':
                options.trace = value
            else:
                raise SkoolKitError(f'Invalid sim-load configuration parameter: {name}')

def sim_load(blocks, options, config):
    if options.tape_analysis:
        get_edges(blocks, options.first_edge, options.polarity, True)
        sys.exit(0)

    list_accelerators = int(options.accelerator == 'list')
    accelerators = set()
    if options.accelerator == 'auto' or list_accelerators:
        accelerators.update(ACCELERATORS.values())
    elif options.accelerator and options.accelerator != 'none':
        for name in options.accelerator.split(','):
            if name in ACCELERATORS:
                accelerators.add(ACCELERATORS[name])
            else:
                raise SkoolKitError(f'Unrecognised accelerator: {name}')

    interrupted = False
    fast = not options.trace
    sim_cfg = {'fast_djnz': fast, 'fast_ldir': fast}
    if options.machine == '128':
        if not options.load:
            options.load = 'ENTER'
        registers = {'PC': 0x00EA, '^HL': 0xFFFF, 'R': 0x38}
        state = {'tstates': 3453395}
        sim_cfg['frame_duration'] = FRAME_DURATIONS[1]
        sim_cfg['int_active'] = INT_ACTIVE[1]
        memory = Memory()
        stop = 0x13BE
        kb_delay = 13
    else:
        registers = {'PC': 0x1200, 'HL': 0xFFFF, 'R': 0x22}
        state = {'tstates': 5701854}
        memory = [0] * 65536
        memory[:0x4000] = read_bin_file(ROM48, 16384)
        stop = 0x0605 # SAVE-ETC
        kb_delay = 4

    if options.trace:
        tracefile = open_file(options.trace, 'w')
        trace_line = config['TraceLine'] + '\n'
        op_fmt = config['TraceOperand']
        prefix, byte_fmt, word_fmt = (op_fmt + ',' * (2 - op_fmt.count(','))).split(',')[:3]
    else:
        tracefile = trace_line = prefix = byte_fmt = word_fmt = None

    timeout = options.timeout * 3500000

    if options.cmio:
        if options.python:
            simulator_cls = CMIOSimulator
        else:
            simulator_cls = CCMIOSimulator or CMIOSimulator
        accelerators.clear()
        options.accelerate_dec_a = 0
    elif options.python:
        simulator_cls = Simulator
    else:
        simulator_cls = CSimulator or Simulator

    if options.load:
        load = options.load.split()
        if load[-1].startswith('PC='):
            pc = load.pop()
            try:
                stop = get_int_param(pc[3:], True)
            except ValueError:
                raise SkoolKitError(f"Invalid integer in 'load' parameter: {pc}")
        if not load or load[-1] != 'ENTER':
            load.append('ENTER')
        simulator = simulator_cls(memory, registers, state, sim_cfg)
        tracer = KeyboardTracer(simulator, load, kb_delay)
        simulator.set_tracer(tracer)
        try:
            tracer.run(stop, timeout, tracefile, trace_line, prefix, byte_fmt, word_fmt)
            border = tracer.border
            out7ffd = tracer.out7ffd
            outfffd = tracer.outfffd
            ay = tracer.ay
            outfe = tracer.outfe
            timeout -= simulator.registers[T]
        except KeyboardInterrupt:
            write_line(f'Simulation stopped (interrupted): PC={simulator.registers[PC]}')
            interrupted = True
    else:
        memory[0x5800:0x5B00] = [56] * 768 # PAPER 7: INK 0
        memory[0x5C00:0x5C00 + len(SYSVARS)] = SYSVARS
        for a, b in SIM_LOAD_PATCH.items():
            memory[a] = b % 256
            if b > 0xFF:
                memory[a + 1] = b // 256
        is_code = False
        for block in blocks:
            if block.block_id == 0x15:
                break
            if block.data:
                if len(block.data) >= 19 and tuple(block.data[0:2]) == (0, 3):
                    is_code = True
                break
        if is_code:
            for a, b in SIM_LOAD_CODE_PATCH.items():
                memory[a] = b % 256
                if b > 0xFF:
                    memory[a + 1] = b // 256
        memory[0xFF58:] = memory[0x3E08:0x3EB0] # UDGs
        simulator = simulator_cls(memory, {'PC': 0x0605, 'SP': 0xFF50}, config=sim_cfg)
        border = 7
        out7ffd = 0
        outfffd = 0
        ay = [0] * 16
        outfe = 0

    if timeout <= 0:
        write_line(f'Simulation stopped (timed out): PC={simulator.registers[PC]}')
    elif not interrupted:
        if options.in_flags & 1:
            in_min_addr = 0x4000
        elif options.in_flags & 2:
            in_min_addr = 0x10000
        else:
            in_min_addr = 0x8000
        tracer = LoadTracer(simulator, blocks, accelerators, options.pause, options.first_edge,
                            options.polarity, in_min_addr, options.accelerate_dec_a,
                            list_accelerators, border, out7ffd, outfffd, ay, outfe)
        simulator.set_tracer(tracer, options.in_flags & 4, False)
        try:
            tracer.run(options.start, options.fast_load, options.finish_tape, timeout, tracefile, trace_line, prefix, byte_fmt, word_fmt)
            _ram_operations(simulator.memory, options.ram_ops)
        except KeyboardInterrupt:
            write_line(f'Simulation stopped (interrupted): PC={simulator.registers[PC]}')
        if list_accelerators:
            accelerators = '; '.join(f'{k}: {v}' for k, v in sorted(tracer.acc_usage.items())) or 'none'
            tsl_misses = f'{tracer.inc_b_misses}/{tracer.dec_b_misses}'
            dec_a_stats = f'{tracer.dec_a_jr_hits}/{tracer.dec_a_jp_hits}/{tracer.dec_a_misses}'
            write_line(f'Accelerators: {accelerators}; misses: {tsl_misses}; dec-a: {dec_a_stats}')

    if tracefile:
        tracefile.close()

    ram, registers, state = get_state(simulator, False)[:3]
    options.reg = registers + options.reg
    options.state = state + options.state
    return ram

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
    _ram_operations(snapshot, options.ram_ops, blocks)
    return snapshot[16384:]

def _get_tzx_blocks(data, sim, start, stop, is48):
    tape = parse_tzx(data, start, stop, False, sim)
    blocks = []
    loop = None
    for block in tape.blocks:
        if block.timings and block.timings.error:
            raise TapeError(block.timings.error)
        if sim:
            if block.block_id == 0x20:
                if stop == 0 and block.timings.pause == 0:
                    break
            elif block.block_id == 0x24:
                loop = []
                repetitions = get_word(block.block_data, 0)
            elif block.block_id == 0x2A and stop == 0 and is48:
                # Stop the tape if in 48K mode
                break
        if loop is None:
            blocks.append(block)
        else:
            loop.append(block)
        if block.block_id == 0x25 and loop is not None:
            blocks.extend(loop * repetitions)
            loop = None
    return blocks

def _get_pzx_blocks(data, sim, start, stop, is48):
    tape = parse_pzx(data, start, stop)
    blocks = []
    for block in tape.blocks:
        if sim:
            if block.block_id == 'STOP':
                mode = block.block_data[0]
                if mode != 1 or is48:
                    break
        blocks.append(block)
    return blocks

def _get_tape_blocks(tape_type, tape, sim, start, stop, is48):
    if tape_type.lower() == 'pzx':
        return _get_pzx_blocks(tape, sim, start, stop, is48)
    if tape_type.lower() == 'tzx':
        return _get_tzx_blocks(tape, sim, start, stop, is48)
    tap = parse_tap(tape, start, stop)
    return [block for block in tap.blocks if block.data]

def _get_tape(urlstring, user_agent, member):
    url = urlparse(urlstring)
    if url.scheme:
        write_line(f'Downloading {urlstring}')
        r = Request(urlstring, headers={'User-Agent': user_agent})
        f = tempfile.NamedTemporaryFile(prefix='tap2sna-')
        with urlopen(r, timeout=30) as u:
            while 1:
                data = u.read(4096)
                if not data:
                    break
                f.write(data)
        f.seek(0)
    else:
        f = open_file(urlstring, 'rb')

    if urlstring.lower().endswith('.zip'):
        z = zipfile.ZipFile(f)
        if member is None:
            for name in z.namelist():
                if name.lower().endswith(SUPPORTED_TAPES):
                    member = name
                    break
            else:
                f.close()
                raise TapeError('No PZX, TAP or TZX file found')
        write_line(f'Extracting {member}')
        try:
            tape = z.open(member)
        except KeyError:
            raise TapeError(f'No file named "{member}" in the archive')
        data = tape.read()
    else:
        member = os.path.basename(urlstring)
        data = f.read()

    f.close()
    tape_type = member[-3:]
    return member, tape_type, data

def _print_ram_help():
    sys.stdout.write("""
Usage: --ram call=[/path/to/moduledir:]module.function
       --ram load=[+]block[+],start[,length,step,offset,inc]
       --ram move=[s:]src,size,[d:]dest
       --ram poke=[p:]a[-b[-c]],[^+]v
       --ram sysvars

Load data from a tape block, copy a block of bytes from one location to
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

--ram move=[s:]src,size,[d:]dest

  Copy a block of bytes from one location to another.

  s    - the source RAM bank (0-7; 128K only)
  src  - the address of the first byte in the block
  size - the number of bytes in the block
  d    - the destination RAM bank (0-7; 128K only)
  dest - the destination address

  For example:

  --ram move=32512,256,32768  # Copy 32512-32767 to 32768-33023
  --ram move=3:0,8,4:0        # Copy the first 8 bytes of bank 3 to bank 4

--ram poke=[p:]a[-b[-c]],[^+]v

  Do POKE N,v in RAM bank p for N in {a, a+c, a+2c..., b}.

  p - the RAM bank to POKE (0-7; 128K only)
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

def _print_sim_load_config_help(param):
    width = max(len(n) for n in ACCELERATORS) + 2
    names = [n.ljust(width) for n in sorted(ACCELERATORS)]
    num_cols = 3
    names += [''] * (-len(names) % num_cols)
    cl = len(names) // num_cols
    columns = [names[i:i + cl] for i in range(0, len(names), cl)]
    accelerators = '\n  '.join(''.join(n) for n in zip(*columns))
    help_text = SIM_LOAD_CONFIG_HELP.format(accelerators=accelerators)
    if param:
        params = {}
        name = None
        for line in help_text.split('\n'):
            if line.startswith('--sim-load-config '):
                name = line[18:].split('=', 1)[0]
                params[name] = [line]
            elif name == param:
                params[name].append(line)
        if param in params:
            help_text = '\n'.join(params[param]).rstrip()
    print(help_text)

def make_snapshot(url, options, outfile, config):
    tape_name, tape_type, tape = _get_tape(url, options.user_agent, options.tape_name)
    if options.tape_sum:
        md5sum = hashlib.md5(tape).hexdigest()
        if md5sum != options.tape_sum:
            raise TapeError(f'Checksum mismatch: Expected {options.tape_sum}, actually {md5sum}')
    if options.sim_load:
        _set_sim_load_config(options)
        is48 = options.machine == '48'
    else:
        is48 = True
    tape_blocks = _get_tape_blocks(tape_type, tape, options.sim_load, options.tape_start, options.tape_stop, is48)
    if options.sim_load:
        blocks = [block for block in tape_blocks if block.timings]
        if not blocks:
            raise TapeError('Tape is empty')
        ram = sim_load(blocks, options, config)
    else:
        blocks = [block.data for block in tape_blocks]
        ram = _get_ram(blocks, options)
    if outfile is None:
        if tape_name.lower().endswith(SUPPORTED_TAPES):
            tape_name = tape_name[:-4]
        fmt = config['DefaultSnapshotFormat']
        outfile = f'{tape_name}.{fmt}'
    if options.output_dir:
        outfile = os.path.join(options.output_dir, outfile)
    _write_snapshot(ram, options, outfile)

def main(args):
    config = get_config('tap2sna')
    parser = SkoolKitArgumentParser(
        usage='\n  tap2sna.py [options] INPUT [OUTFILE]\n  tap2sna.py @FILE [args]',
        description="Convert a PZX, TAP or TZX file (which may be inside a zip archive) into an SZX or Z80 snapshot. "
                    "INPUT may be the full URL to a remote zip archive or tape file, or the path to a local file. "
                    "Arguments may be read from FILE instead of (or as well as) being given on the command line.",
        fromfile_prefix_chars='@',
        add_help=False
    )
    parser.add_argument('url', help=argparse.SUPPRESS, nargs='?')
    parser.add_argument('outfile', help=argparse.SUPPRESS, nargs='?')
    group = parser.add_argument_group('Options')
    group.add_argument('-c', '--sim-load-config', metavar='name=value', action='append', default=[],
                       help="Set the value of a simulated LOAD configuration parameter. "
                            "Do '-c help' for more information, or '-c help-name' for help on a specific parameter. "
                            "This option may be used multiple times.")
    group.add_argument('-d', '--output-dir', dest='output_dir', metavar='DIR',
                       help="Write the snapshot file in this directory.")
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
    group.add_argument('--state', dest='state', metavar='name=value', action='append', default=[],
                       help="Set a hardware state attribute. Do '--state help' for more information. "
                            "This option may be used multiple times.")
    group.add_argument('--tape-analysis', action='store_true',
                       help="Show an analysis of the tape's tones, pulse sequences and data blocks.")
    group.add_argument('--tape-name', metavar='NAME',
                       help="Specify the name of a tape file in a zip archive.")
    group.add_argument('--tape-start', metavar='BLOCK', type=int, default=1,
                       help="Start the tape at this block number.")
    group.add_argument('--tape-stop', metavar='BLOCK', type=int, default=0,
                       help="Stop the tape at this block number.")
    group.add_argument('--tape-sum', metavar='MD5SUM',
                       help="Specify the MD5 checksum of the tape file.")
    group.add_argument('-u', '--user-agent', dest='user_agent', metavar='AGENT', default='',
                       help="Set the User-Agent header.")
    group.add_argument('-V', '--version', action='version', version='SkoolKit {}'.format(VERSION),
                       help='Show SkoolKit version number and exit.')
    namespace, unknown_args = parser.parse_known_intermixed_args(args)
    if namespace.show_config:
        show_config('tap2sna', config)
    for param in namespace.sim_load_config:
        if param.startswith('help'):
            _print_sim_load_config_help(param[5:])
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
    if unknown_args or namespace.url is None:
        parser.exit(2, parser.format_help())
    if namespace.stack is not None:
        namespace.reg.append('sp={}'.format(namespace.stack))
    namespace.sim_load = not any(s.startswith('load=') for s in namespace.ram_ops)
    if not namespace.sim_load and namespace.start is not None:
        namespace.reg.append('pc={}'.format(namespace.start))
    update_options('tap2sna', namespace, namespace.params, config)
    if namespace.outfile is None:
        for arg in args:
            if arg.startswith('@') and arg.lower().endswith('.t2s') and os.path.isfile(arg[1:]):
                namespace.outfile = os.path.basename(arg[1:-3]) + config['DefaultSnapshotFormat']
                break
    try:
        make_snapshot(namespace.url, namespace, namespace.outfile, config)
    except Exception as e:
        raise SkoolKitError("Error while converting {}: {}".format(os.path.basename(namespace.url), e.args[0] if e.args else e))
