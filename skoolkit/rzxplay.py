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

from skoolkit import VERSION, SkoolKitError, get_dword, get_word, read_bin_file, write
from skoolkit.pagingtracer import PagingTracer
from skoolkit.simulator import Simulator, R1
from skoolkit.snapshot import Snapshot, Z80, write_snapshot
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
    def __init__(self, tstates, frames):
        self.tstates = tstates
        self.frames = frames

class Frame:
    def __init__(self, fetch_counter, port_readings):
        self.fetch_counter = fetch_counter
        self.port_readings = port_readings

class RZXTracer(PagingTracer):
    def __init__(self, context, input_rec):
        self.context = context
        self.set_input_rec(input_rec)
        self.simulator = context.simulator
        self.simulator.registers[25] = input_rec.tstates
        self.simulator.opcodes[0x76] = partial(self.halt, self.simulator.registers)
        self.border = context.snapshot.border
        self.out7ffd = context.snapshot.out7ffd
        self.outfffd = context.snapshot.outfffd
        self.ay = list(context.snapshot.ay)
        self.outfe = context.snapshot.outfe

    def set_input_rec(self, input_rec):
        self.frames = input_rec.frames
        self.frame_index = -1
        self.readings = None

    def next_frame(self):
        if self.readings:
            raise SkoolKitError(f'{len(self.readings)} port reading(s) left for frame {self.context.frame_count}')
        self.frame_index += 1
        if self.frame_index < len(self.frames):
            frame = self.frames[self.frame_index]
            self.readings = frame.port_readings
            return frame.fetch_counter

    def read_port(self, registers, port):
        if self.readings:
            return self.readings.pop(0)
        raise SkoolKitError(f'Port readings exhausted for frame {self.context.frame_count}')

    def halt(self, registers):
        # HALT
        registers[25] += 4 # T-states
        registers[15] = R1[registers[15]] # R

class RZXContext:
    def __init__(self, screen=None, p_rectangles=None, c_rectangles=None, clock=None):
        self.screen = screen
        self.p_rectangles = p_rectangles
        self.c_rectangles = c_rectangles
        self.clock = clock
        self.tracefile = None
        self.snapshot = None
        self.simulator = None
        self.total_frames = 0
        self.frame_count = 0
        self.stop = False

def as_dword(num):
    return (num % 256, (num >> 8) % 256, (num >> 16) % 256, (num >> 24) % 256)

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

    ram, registers, state = context.simulator.state()
    z80 = Z80(ram=ram)
    z80.set_registers_and_state(registers, state)
    z80_data = z80.data()
    z80_data_z = zlib.compress(z80_data, 9)
    s_len = len(z80_data)
    b_len = 17 + len(z80_data_z)
    rzx_data.extend((
        0x30,             # Block ID (Snapshot)
        *as_dword(b_len), # Block length
        2, 0, 0, 0,       # Flags
        122, 56, 48, 0,   # z80
        *as_dword(s_len)  # Uncompressed snapshot length
    ))
    rzx_data.extend(z80_data_z)

    tracer = context.simulator.tracer
    frames = tracer.frames[tracer.frame_index + 1:]
    nf = len(frames)
    io_frames = bytearray()
    for frame in frames:
        fc = frame.fetch_counter
        ic = len(frame.port_readings)
        io_frames.extend((fc % 256, fc // 256, ic % 256, ic // 256))
        io_frames.extend(frame.port_readings)
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
            if flags & 1:
                raise SkoolKitError('Missing snapshot (external file)')
            ext = ''.join(chr(b) for b in data[i + 9:i + 13] if b)
            sdata = data[i + 17:i + block_len]
            if flags & 2:
                sdata = zlib.decompress(sdata)
            contents.append(RZXBlock(data[i:i + block_len], Snapshot.get(sdata, ext)))
        elif block_id == 0x80:
            # Input recording
            num_frames = get_dword(data, i + 5)
            tstates = get_dword(data, i + 10)
            flags = get_dword(data, i + 14)
            frames = []
            contents.append(RZXBlock(data[i:i + block_len], InputRecording(tstates, frames)))
            frames_data = data[i + 18:i + block_len]
            if flags & 2:
                frames_data = zlib.decompress(frames_data)
            j = 0
            port_readings = []
            for k in range(num_frames):
                fetch_counter = get_word(frames_data, j)
                in_counter = get_word(frames_data, j + 2)
                if in_counter == 65535:
                    port_readings = port_readings[:]
                    j += 4
                else:
                    port_readings = list(frames_data[j + 4:j + 4 + in_counter])
                    j += 4 + in_counter
                frames.append(Frame(fetch_counter, port_readings))
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
    if snapshot.type == 'Z80':
        header = snapshot.header
        if len(header) == 30:
            # Version 1
            return
        if header[37] & 128:
            return 'Unsupported machine type'
        machine_id = header[34]
        if len(header) == 55:
            # Version 2
            if machine_id not in (0, 3):
                return 'Unsupported machine type'
        # Version 3
        elif machine_id not in (0, 4):
            return 'Unsupported machine type'
    elif snapshot.type == 'SZX':
        supported_blocks = {'AY', 'CRTR', 'KEYB', 'JOY', 'RAMP', 'SPCR', 'TAPE', 'Z80R'}
        unsupported_blocks = set(b[0] for b in snapshot.tail) - supported_blocks
        if unsupported_blocks:
            return 'Unsupported block(s) ({}) in SZX snapshot'.format(', '.join(unsupported_blocks))
        machine_id = snapshot.header[6]
        if machine_id > 2:
            return 'Unsupported machine type'

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
    if context.snapshot is None:
        return
    if context.simulator:
        simulator = context.simulator
        tracer = simulator.tracer
        tracer.set_input_rec(block)
    else:
        simulator = Simulator.from_snapshot(context.snapshot)
        context.simulator = simulator
        tracer = RZXTracer(context, block)
        simulator.set_tracer(tracer)
    opcodes = simulator.opcodes
    memory = simulator.memory
    registers = simulator.registers
    frame_duration = simulator.frame_duration
    total_frames = context.total_frames
    fnwidth = len(str(total_frames))
    prev_scr = [None] * 6912
    show_progress = not options.quiet
    fps = options.fps
    stop = options.stop
    tracefile = context.tracefile
    frame_count = context.frame_count
    screen = context.screen
    if screen: # pragma: no cover
        p_rectangles = context.p_rectangles
        c_rectangles = context.c_rectangles
        clock = context.clock
    run = True
    while run:
        fetch_counter = tracer.next_frame()
        if fetch_counter is None:
            break
        while fetch_counter > 0:
            pc = registers[24]
            r0 = registers[15]
            ld_r_a = memory[pc] == 0xED and memory[(pc + 1) % 65536] == 0x4F
            if tracefile:
                i = disassemble(memory, pc)[0]
                tracefile.write(f'F:{frame_count:0{fnwidth}} T:{registers[25]:05} C:{fetch_counter:05} I:{len(tracer.readings):05} ${pc:04X} {i}\n')
            opcodes[memory[pc]]()
            if ld_r_a:
                fetch_counter -= 2
            else:
                fetch_counter -= 2 - ((registers[15] ^ r0) % 2)
        if screen: # pragma: no cover
            draw(screen, memory, frames, p_rectangles, c_rectangles, prev_scr)
            pygame.display.update()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
            if fps > 0:
                clock.tick(fps)
            prev_scr = memory[16384:23296]
        registers[25] = 0
        if simulator.iff:
            if memory[pc] == 0x76:
                # Advance PC if the CPU was halted
                registers[24] = (registers[24] + 1) % 65536
            # Always accept an interrupt at a frame boundary, even if the
            # instruction just executed would normally block it
            simulator.accept_interrupt(registers, memory, 0)
        frame_count += 1
        if show_progress:
            p = (frame_count / total_frames) * 100
            write(f'[{p:5.1f}%]\x08\x08\x08\x08\x08\x08\x08\x08')
        if frame_count == stop:
            context.stop = True
            break
    context.frame_count = frame_count

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
    if options.trace:
        context.tracefile = open(options.trace, 'w')
    rzx_blocks = parse_rzx(infile)
    while rzx_blocks and isinstance(rzx_blocks[-1].obj, Snapshot):
        rzx_blocks.pop()
    for block in rzx_blocks:
        if isinstance(block.obj, InputRecording):
            context.total_frames += len(block.obj.frames)
    while rzx_blocks:
        process_block(rzx_blocks.pop(0).obj, options, context)
        if context.stop:
            break
    if context.tracefile:
        context.tracefile.close()
    if options.dump:
        ext = options.dump.lower().rpartition('.')[2]
        if ext in ('szx', 'z80'):
            ram, registers, state = context.simulator.state()
            write_snapshot(options.dump, ram, registers, state)
        elif ext == 'rzx':
            write_rzx(options.dump, context, rzx_blocks)
        else:
            raise SkoolKitError(f'Unknown file type: {ext}')
        print(f'Wrote {options.dump}')

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
    group.add_argument('--force', action='store_true',
                       help="Force playback when unsupported hardware is detected.")
    group.add_argument('--fps', type=int, default=50,
                       help="Run at this many frames per second (default: 50). "
                            "0 means maximum speed.")
    group.add_argument('--no-screen', dest='screen', action='store_false',
                       help="Run without a screen.")
    group.add_argument('--quiet', action='store_true',
                       help="Don't print progress percentage.")
    group.add_argument('--scale', metavar='SCALE', type=int, default=2, choices=(1, 2, 3, 4),
                       help="Scale display up by this factor (1-4; default: 2).")
    group.add_argument('--stop', metavar='FRAMES', type=int,
                       help="Stop after playing this many frames.")
    group.add_argument('--trace', metavar='FILE',
                       help="Log executed instructions to a file.")
    group.add_argument('-V', '--version', action='version', version='SkoolKit {}'.format(VERSION),
                       help='Show SkoolKit version number and exit.')
    namespace, unknown_args = parser.parse_known_args(args)
    if unknown_args or namespace.infile is None:
        parser.exit(2, parser.format_help())
    run(namespace.infile, namespace)
