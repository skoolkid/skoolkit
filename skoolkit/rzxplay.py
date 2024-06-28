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
import contextlib
from functools import partial
import io
import os
import re
import zlib

with contextlib.redirect_stdout(io.StringIO()) as pygame_io:
    try:
        import pygame
    except ImportError: # pragma: no cover
        pygame = None

from skoolkit import (VERSION, SkoolKitError, CSimulator, as_dword, get_dword,
                      get_word, parse_int, read_bin_file, warn, write)
from skoolkit.pagingtracer import PagingTracer
from skoolkit.simulator import Simulator
from skoolkit.simutils import from_snapshot, get_state
from skoolkit.snapshot import Snapshot, write_snapshot
from skoolkit.traceutils import disassemble

if pygame: # pragma: no cover
    COLOURS = (
        pygame.Color(0x00, 0x00, 0x00), # Black
        pygame.Color(0x00, 0x00, 0xc5), # Blue
        pygame.Color(0xc5, 0x00, 0x00), # Red
        pygame.Color(0xc5, 0x00, 0xc5), # Magenta
        pygame.Color(0x00, 0xc6, 0x00), # Green
        pygame.Color(0x00, 0xc6, 0xc5), # Cyan
        pygame.Color(0xc5, 0xc6, 0x00), # Yellow
        pygame.Color(0xcd, 0xc6, 0xcd), # White
        pygame.Color(0x00, 0x00, 0x00), # Bright black
        pygame.Color(0x00, 0x00, 0xff), # Bright blue
        pygame.Color(0xff, 0x00, 0x00), # Bright red
        pygame.Color(0xff, 0x00, 0xff), # Bright magenta
        pygame.Color(0x00, 0xff, 0x00), # Bright green
        pygame.Color(0x00, 0xff, 0xff), # Bright cyan
        pygame.Color(0xff, 0xff, 0x00), # Bright yellow
        pygame.Color(0xff, 0xff, 0xff), # Bright white
    )

CELLS = tuple((x, y, 2048 * (y // 8) + 32 * (y % 8) + x, 6144 + 32 * y + x) for x in range(32) for y in range(24))

class RZXBlock:
    def __init__(self, data, obj):
        self.data = data
        self.obj = obj

class InputRecording:
    def __init__(self, tstates, frames, data):
        self.tstates = tstates
        self.frames = frames
        self.data = data

class Frame:
    def __init__(self, fetch_counter, start, end):
        self.fetch_counter = fetch_counter
        self.start = start
        self.end = end

class RZXTracer(PagingTracer):
    def __init__(self, context, input_rec):
        self.context = context
        self.set_input_rec(input_rec)
        self.simulator = context.simulator
        self.simulator.registers[25] = input_rec.tstates
        self.border = context.snapshot.border
        self.out7ffd = context.snapshot.out7ffd
        self.outfffd = context.snapshot.outfffd
        self.ay = list(context.snapshot.ay)
        self.outfe = context.snapshot.outfe

    def set_input_rec(self, input_rec):
        self.frames = input_rec.frames
        self.data = input_rec.data
        self.frame_index = -1
        self.index = 0
        self.end = 0

    def next_frame(self):
        if self.end > self.index:
            raise SkoolKitError(f'{self.end - self.index} port reading(s) left for frame {self.context.frame_count}')
        self.frame_index += 1
        if self.frame_index > 0:
            self.context.frame_count += 1
        while self.frame_index < len(self.frames):
            frame = self.frames[self.frame_index]
            if frame.fetch_counter > 0:
                self.index = frame.start
                self.end = frame.end
                return frame.fetch_counter
            self.frame_index += 1
            self.context.frame_count += 1
        return -1

    def read_port(self, registers, port):
        if self.index < self.end:
            self.index += 1
            return self.data[self.index - 1]
        raise SkoolKitError(f'Port readings exhausted for frame {self.context.frame_count}')

class RZXContext:
    def __init__(self, screen=None, p_rectangles=None, c_rectangles=None, clock=None):
        self.screen = screen
        self.p_rectangles = p_rectangles
        self.c_rectangles = c_rectangles
        self.clock = clock
        self.exec_map = None
        self.tracefile = None
        self.snapshot = None
        self.simulator = None
        self.total_frames = 0
        self.frame_count = 0
        self.stop = False

def write_rzx(fname, context, rzx_blocks):
    creator_b = (83, 107, 111, 111, 108, 75, 105, 116, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    major, minor = re.match('([0-9]+).([0-9]+)', VERSION).groups()
    rzx_data = bytearray((
        82, 90, 88, 33,   # RZX!
        0, 13,            # Version 0.13
        0, 0, 0, 0,       # Flags
        0x10,             # Block ID (Creator)
        29, 0, 0, 0,      # Block length
        *creator_b,       # Creator ID (SkoolKit)
        int(major), 0,
        int(minor), 0
    ))

    ram, registers, state = get_state(context.simulator)[:3]
    snapshot = context.snapshot
    snapshot.set_ram(ram)
    snapshot.set_registers_and_state(registers, state)
    snapshot_data = snapshot.data()
    snapshot_data_z = zlib.compress(snapshot_data, 9)
    snapshot_ext = [ord(c) for c in snapshot.type.lower()] + [0]
    s_len = len(snapshot_data)
    b_len = 17 + len(snapshot_data_z)
    rzx_data.extend((
        0x30,             # Block ID (Snapshot)
        *as_dword(b_len), # Block length
        2, 0, 0, 0,       # Flags
        *snapshot_ext,    # z80/szx
        *as_dword(s_len)  # Uncompressed snapshot length
    ))
    rzx_data.extend(snapshot_data_z)

    tracer = context.simulator.tracer
    frames = tracer.frames[tracer.frame_index:]
    nf = len(frames)
    io_frames = bytearray()
    for frame in frames:
        fc = frame.fetch_counter
        port_readings = tracer.data[frame.start:frame.end]
        ic = len(port_readings)
        io_frames.extend((fc % 256, fc // 256, ic % 256, ic // 256))
        io_frames.extend(port_readings)
    io_frames = zlib.compress(io_frames, 9)
    b_len = 18 + len(io_frames)
    rzx_data.extend((
        0x80,             # Block ID (Input recording)
        *as_dword(b_len), # Block length
        *as_dword(nf),    # Number of frames
        0,                # Reserved
        0, 0, 0, 0,       # Initial T-states
        2, 0, 0, 0        # Flags
    ))
    rzx_data.extend(io_frames)

    for rzx_block in rzx_blocks:
        rzx_data.extend(rzx_block.data)

    with open(fname, 'wb') as f:
        f.write(rzx_data)

def parse_rzx(rzxfile):
    data = read_bin_file(rzxfile)
    if data[:4] != b'RZX!' or len(data) < 10:
        raise SkoolKitError('Not an RZX file')
    i = 10
    contents = []
    while i < len(data):
        block_id = data[i]
        block_len = get_dword(data, i + 1)
        if block_id == 0x30:
            # Snapshot
            flags = data[i + 5]
            if flags & 1 == 0:
                ext = ''.join(chr(b) for b in data[i + 9:i + 13] if b)
                sdata = data[i + 17:i + block_len]
                if flags & 2:
                    try:
                        sdata = zlib.decompress(sdata)
                    except zlib.error as e:
                        raise SkoolKitError(f'Failed to decompress snapshot: {e.args[0]}')
                contents.append(RZXBlock(data[i:i + block_len], Snapshot.get(sdata, ext)))
        elif block_id == 0x80:
            # Input recording
            num_frames = get_dword(data, i + 5)
            tstates = get_dword(data, i + 10)
            flags = get_dword(data, i + 14)
            frames = []
            frames_data = data[i + 18:i + block_len]
            if flags & 2:
                try:
                    frames_data = zlib.decompress(frames_data)
                except zlib.error as e:
                    raise SkoolKitError(f'Failed to decompress input recording block: {e.args[0]}')
            contents.append(RZXBlock(data[i:i + block_len], InputRecording(tstates, frames, frames_data)))
            j = 0
            start = end = 0
            for k in range(num_frames):
                fetch_counter = get_word(frames_data, j)
                in_counter = get_word(frames_data, j + 2)
                if in_counter == 65535:
                    j += 4
                else:
                    start = j + 4
                    end = j = start + in_counter
                frames.append(Frame(fetch_counter, start, end))
        i += block_len
    return contents

def draw(screen, memory, frame, pixel_rects, cell_rects, prev_scr): # pragma: no cover
    current_scr = memory[16384:23296]
    flash_change = (frame % 16) == 0
    flash_switch = (frame // 16) % 2

    for (x, y, df_addr, af_addr) in CELLS:
        update = False
        attr = current_scr[af_addr]
        for a in range(df_addr, df_addr + 2048, 256):
            if current_scr[a] != prev_scr[a]:
                update = True
                break
        else:
            update = attr != prev_scr[af_addr] or (flash_change and attr & 0x80)
        if update:
            bright = (attr & 64) // 8
            ink = COLOURS[bright + (attr % 8)]
            paper = COLOURS[bright + ((attr // 8) % 8)]
            if attr & 0x80 and flash_switch:
                ink, paper = paper, ink
            py = 8 * y
            screen.fill(paper, cell_rects[x][y])
            for addr in range(df_addr, df_addr + 2048, 256):
                b = current_scr[addr]
                px = 8 * x
                while b % 256:
                    if b & 0x80:
                        screen.fill(ink, pixel_rects[px][py])
                    b *= 2
                    px += 1
                py += 1

def check_supported(snapshot, options):
    if options.force:
        return
    if snapshot.machine is None:
        return 'Unsupported machine type'
    if snapshot.type == 'Z80':
        header = snapshot.header
        if len(header) == 55 and header[34] not in (0, 3):
            # Version 2
            warn('Unsupported hardware (IF1)')
        elif len(header) > 55 and header[34] not in (0, 4, 12):
            # Version 3
            warn('Unsupported hardware (IF1 or MGT)')
    elif snapshot.type == 'SZX':
        supported_blocks = {'AY', 'CRTR', 'KEYB', 'JOY', 'RAMP', 'SPCR', 'TAPE', 'Z80R'}
        unsupported_blocks = set(b[0] for b in snapshot.tail) - supported_blocks
        if unsupported_blocks:
            warn('Unsupported block(s) ({}) in SZX snapshot'.format(', '.join(sorted(unsupported_blocks))))

def trace_exec(tracefile, context, fetch_counter, pc):
    i = disassemble(context.simulator.memory, pc)[0]
    readings_left = context.simulator.tracer.end - context.simulator.tracer.index
    tracefile.write(f'F:{context.frame_count:0{context.fnwidth}} C:{fetch_counter:05} I:{readings_left:05} ${pc:04X} {i}\n')

def process_block(block, options, context):
    if block is None:
        raise SkoolKitError('Unsupported snapshot type')
    if isinstance(block, Snapshot):
        error_msg = check_supported(block, options)
        if error_msg:
            raise SkoolKitError(error_msg)
        context.snapshot = block
        context.simulator = None
        return
    if context.simulator:
        simulator = context.simulator
        tracer = simulator.tracer
        tracer.set_input_rec(block)
    else:
        # Set 'int_active' to 0 to prevent 'HALT' and 'LD A,I/R' from ever
        # behaving as if an interrupt is to be accepted
        config = {'int_active': 0}
        if options.python:
            simulator_cls = Simulator
        else:
            simulator_cls = CSimulator or Simulator
        simulator = from_snapshot(simulator_cls, context.snapshot, config=config)
        context.simulator = simulator
        tracer = RZXTracer(context, block)
        simulator.set_tracer(tracer)
    opcodes = simulator.opcodes if hasattr(simulator, 'opcodes') else None
    memory = simulator.memory
    registers = simulator.registers
    total_frames = context.total_frames
    context.fnwidth = len(str(total_frames)) - 1
    prev_scr = [None] * 6912
    show_progress = not options.quiet
    fps = options.fps
    stop = options.stop or total_frames
    flags = parse_int(options.flags, 0)
    flags_ldair = flags & 1
    flags_ei = flags & 2
    exec_map = context.exec_map
    tracefile = context.tracefile
    if tracefile:
        trace = partial(trace_exec, tracefile, context)
    else:
        trace = None
    screen = context.screen
    if screen: # pragma: no cover
        p_rectangles = context.p_rectangles
        c_rectangles = context.c_rectangles
        clock = context.clock
    fetch_counter = tracer.next_frame()
    run = True
    csimulator = hasattr(simulator, 'exec_frame')
    while run:
        if fetch_counter < 0:
            break
        if csimulator: # pragma: no cover
            pc = simulator.exec_frame(fetch_counter, exec_map, trace)
        else:
            while fetch_counter > 0:
                pc = registers[24]
                r0 = registers[15]
                ld_r_a = memory[pc] == 0xED and memory[(pc + 1) % 65536] == 0x4F
                if tracefile:
                    trace_exec(tracefile, context, fetch_counter, pc)
                if exec_map is not None:
                    exec_map.add(pc)
                opcodes[memory[pc]]()
                if ld_r_a:
                    fetch_counter -= 2
                else:
                    fetch_counter -= 2 - ((registers[15] ^ r0) % 2)
        if screen: # pragma: no cover
            draw(screen, memory, context.frame_count, p_rectangles, c_rectangles, prev_scr)
            pygame.display.update()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
            if fps > 0:
                clock.tick(fps)
            prev_scr = memory[16384:23296]
        registers[25] = 0
        fetch_counter = tracer.next_frame()
        if registers[26]:
            if memory[pc] == 0x76:
                # Advance PC if the CPU was halted
                registers[24] = (registers[24] + 1) % 65536
                simulator.accept_interrupt(registers, memory, 0)
            elif flags_ldair and memory[pc] == 0xED and memory[(pc + 1) % 65536] in (0x57, 0x5F):
                # If bit 0 of the playback flags is set and the last
                # instruction was 'LD A,I' or 'LD A,R', reset bit 2 of F
                registers[1] &= 0b11111011
                simulator.accept_interrupt(registers, memory, 0)
            elif flags_ei:
                # If bit 1 of the playback flags is set, accept an interrupt at
                # a frame boundary unless the last instruction was EI and the
                # next frame is short
                if memory[pc] != 0xFB or fetch_counter > 2:
                    simulator.accept_interrupt(registers, memory, 0)
            else:
                simulator.accept_interrupt(registers, memory, 0)
        if show_progress:
            p = (context.frame_count / total_frames) * 100
            write(f'[{p:5.1f}%]\x08\x08\x08\x08\x08\x08\x08\x08')
        if context.frame_count >= stop:
            context.stop = True
            break

def run(infile, options):
    if options.screen and pygame: # pragma: no cover
        print(pygame_io.getvalue())
        pygame.init()
        scale = options.scale
        pygame.display.set_mode((256 * scale, 192 * scale))
        pygame.display.set_caption(os.path.basename(infile))
        p_rectangles = [[pygame.Rect(px * scale, py * scale, scale, scale) for py in range(192)] for px in range(256)]
        c_rectangles = [[pygame.Rect(px * scale, py * scale, 8 * scale, 8 * scale) for py in range(0, 192, 8)] for px in range(0, 256, 8)]
        screen = pygame.display.get_surface()
        clock = pygame.time.Clock()
        context = RZXContext(screen, p_rectangles, c_rectangles, clock)
    else:
        context = RZXContext()
    if options.map:
        context.exec_map = set()
        if os.path.isfile(options.map):
            with open(options.map) as f:
                for line in f:
                    if re.match(r'\$[0-9A-F]{4}', line):
                        context.exec_map.add(int(line[1:5], 16))
    if options.trace:
        context.tracefile = open(options.trace, 'w')
    rzx_blocks = parse_rzx(infile)
    if options.snapshot:
        rzx_blocks.insert(0, RZXBlock(None, Snapshot.get(options.snapshot)))
    while rzx_blocks and isinstance(rzx_blocks[-1].obj, Snapshot):
        rzx_blocks.pop()
    if rzx_blocks and isinstance(rzx_blocks[0].obj, InputRecording):
        raise SkoolKitError('Missing snapshot')
    for block in rzx_blocks:
        if isinstance(block.obj, InputRecording):
            context.total_frames += len(block.obj.frames)
    if options.stop and options.stop > 0:
        context.total_frames = min(options.stop, context.total_frames)
    while rzx_blocks:
        process_block(rzx_blocks.pop(0).obj, options, context)
        if context.stop:
            break
    if options.map:
        with open(options.map, 'w') as f:
            for addr in sorted(context.exec_map):
                f.write(f'${addr:04X}\n')
    if context.tracefile:
        context.tracefile.close()
    if options.dump:
        ext = options.dump.lower().rpartition('.')[2]
        if ext in ('szx', 'z80'):
            ram, registers, state, machine = get_state(context.simulator)
            write_snapshot(options.dump, ram, registers, state, machine)
        elif ext == 'rzx':
            write_rzx(options.dump, context, rzx_blocks)
        else:
            raise SkoolKitError(f'Unknown file type: {ext}')
        print(f'Wrote {options.dump}')

def print_flags_help():
    print("""
Usage: --flags FLAGS

Set flags that control the playback of RZX frames when interrupts are enabled.
FLAGS is the sum of the following values, chosen according to the desired
outcome:

  1 - When the last instruction in a frame is either 'LD A,I' or 'LD A,R',
      reset bit 2 of the flags register. This is the expected behaviour of a
      real Z80, but some RZX files fail when this flag is set.

  2 - When the last instruction in a frame is 'EI', and the next frame is a
      short one (i.e. has a fetch count of 1 or 2), block the interrupt in the
      next frame. By default, and according to RZX convention, rzxplay.py
      accepts an interrupt at the start of every frame except the first,
      regardless of whether the instruction just executed would normally block
      it. However, some RZX files contain a short frame immediately after an
      'EI' to indicate that the interrupt should in fact be blocked, and
      therefore require this flag to be set to play back correctly.

""".strip())

def main(args):
    parser = argparse.ArgumentParser(
        usage='rzxplay.py [options] FILE [OUTFILE]',
        description="Play an RZX file. "
                    "If 'OUTFILE' is given, an SZX or Z80 snapshot or an RZX file is written after playback has completed.",
        add_help=False
    )
    parser.add_argument('infile', help=argparse.SUPPRESS, nargs='?')
    parser.add_argument('dump', help=argparse.SUPPRESS, nargs='?')
    group = parser.add_argument_group('Options')
    group.add_argument('--flags', default='0',
                       help="Set playback flags. Do '--flags help' for more information.")
    group.add_argument('--force', action='store_true',
                       help="Force playback when unsupported hardware is detected.")
    group.add_argument('--fps', type=int, default=50,
                       help="Run at this many frames per second (default: 50). "
                            "0 means maximum speed.")
    group.add_argument('--map', metavar='FILE',
                       help="Log addresses of executed instructions to a file.")
    group.add_argument('--no-screen', dest='screen', action='store_false',
                       help="Run without a screen.")
    group.add_argument('--python', action='store_true',
                       help="Use the pure Python Z80 simulator.")
    group.add_argument('--quiet', action='store_true',
                       help="Don't print progress percentage.")
    group.add_argument('--scale', metavar='SCALE', type=int, default=2, choices=(1, 2, 3, 4),
                       help="Scale display up by this factor (1-4; default: 2).")
    group.add_argument('--snapshot', metavar='FILE',
                       help="Specify an external snapshot file to start with.")
    group.add_argument('--stop', metavar='FRAMES', type=int,
                       help="Stop after playing this many frames.")
    group.add_argument('--trace', metavar='FILE',
                       help="Log executed instructions to a file.")
    group.add_argument('-V', '--version', action='version', version='SkoolKit {}'.format(VERSION),
                       help='Show SkoolKit version number and exit.')
    namespace, unknown_args = parser.parse_known_args(args)
    if namespace.flags == 'help':
        print_flags_help()
        return
    if unknown_args or namespace.infile is None:
        parser.exit(2, parser.format_help())
    run(namespace.infile, namespace)
