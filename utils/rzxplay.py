#!/usr/bin/env python3
import argparse
import contextlib
from functools import partial
import io
import os
import sys
import tempfile
import zlib

with contextlib.redirect_stdout(io.StringIO()) as pygame_io:
    try:
        import pygame
    except ImportError:
        pygame = None

SKOOLKIT_HOME = os.environ.get('SKOOLKIT_HOME')
if not SKOOLKIT_HOME:
    sys.stderr.write('SKOOLKIT_HOME is not set; aborting\n')
    sys.exit(1)
if not os.path.isdir(SKOOLKIT_HOME):
    sys.stderr.write(f'SKOOLKIT_HOME={SKOOLKIT_HOME}; directory not found\n')
    sys.exit(1)
sys.path.insert(0, SKOOLKIT_HOME)

from skoolkit import ROM48, error, get_dword, get_word, read_bin_file, write
from skoolkit.pagingtracer import Memory
from skoolkit.snapshot import Snapshot, FRAME_DURATIONS
from skoolkit.simulator import Simulator, INT_ACTIVE, R1
from skoolkit.traceutils import disassemble

if pygame:
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

class InputRecording:
    def __init__(self, tstates, frames):
        self.tstates = tstates
        self.frames = frames

class Frame:
    def __init__(self, fetch_counter, port_readings):
        self.fetch_counter = fetch_counter
        self.port_readings = port_readings

class RZXTracer:
    def __init__(self, simulator, frames, tstates):
        self.simulator = simulator
        self.frames = frames
        self.frame_index = -1
        self.readings = None
        simulator.registers[25] = tstates
        simulator.opcodes[0x76] = partial(self.halt, simulator.registers)

    def next_frame(self):
        if self.readings:
            error(f'{len(self.readings)} port reading(s) left for frame {self.frame_index}')
        self.frame_index += 1
        if self.frame_index < len(self.frames):
            frame = self.frames[self.frame_index]
            self.readings = frame.port_readings
            return frame.fetch_counter

    def read_port(self, registers, port):
        if self.readings:
            return self.readings.pop(0)
        error(f'ERROR: Port readings exhausted for frame {self.frame_index}')

    def halt(self, registers):
        # HALT
        registers[25] += 4 # T-states
        registers[15] = R1[registers[15]] # R

class RZXTracer128(RZXTracer):
    def __init__(self, simulator, frames, tstates, out7ffd):
        super().__init__(simulator, frames, tstates)
        self.out7ffd = out7ffd

    def write_port(self, registers, port, value):
        if port & 0x8002 == 0 and self.out7ffd & 32 == 0:
            self.simulator.memory.out7ffd(value)
            self.out7ffd = value

def parse_rzx(rzxfile):
    with open(rzxfile, 'rb') as f:
        data = f.read()
    if data[:4] != b'RZX!' or len(data) < 10:
        error('Not an RZX file')
    i = 10
    contents = []
    while i < len(data):
        block_id = data[i]
        block_len = get_dword(data, i + 1)
        if block_id == 0x30:
            # Snapshot
            flags = data[i + 5]
            ext = ''.join(chr(b) for b in data[i + 9:i + 13] if b)
            sdata = data[i + 17:i + block_len]
            if flags & 2:
                sdata = zlib.decompress(sdata)
            with tempfile.NamedTemporaryFile(suffix=f'.{ext}') as f:
                f.write(sdata)
                snapshot = Snapshot.get(f.name)
            contents.append([snapshot, None])
        elif block_id == 0x80:
            # Input recording
            num_frames = get_dword(data, i + 5)
            tstates = get_dword(data, i + 10)
            flags = get_dword(data, i + 14)
            frames = []
            if contents[-1][1] is None:
                contents[-1][1] = InputRecording(tstates, frames)
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

def draw(screen, memory, frame, pixel_rects, cell_rects, prev_scr):
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

def get_registers(snapshot):
    return {
        'A': snapshot.a,
        'F': snapshot.f,
        'BC': snapshot.bc,
        'DE': snapshot.de,
        'HL': snapshot.hl,
        'IXh': snapshot.ix // 256,
        'IXl': snapshot.ix % 256,
        'IYh': snapshot.iy // 256,
        'IYl': snapshot.iy % 256,
        'SP': snapshot.sp,
        'I': snapshot.i,
        'R': snapshot.r,
        '^A': snapshot.a2,
        '^F': snapshot.f2,
        '^BC': snapshot.bc2,
        '^DE': snapshot.de2,
        '^HL': snapshot.hl2,
        'PC': snapshot.pc
    }

def get_simulator(snapshot, options):
    memory = snapshot.ram(-1)
    if len(memory) == 0x20000:
        banks = [memory[a:a + 0x4000] for a in range(0, 0x20000, 0x4000)]
        memory = Memory(banks, snapshot.out7ffd)
    else:
        memory = list(read_bin_file(ROM48)) + memory
    state = {'im': snapshot.im, 'iff': snapshot.iff1, 'tstates': snapshot.tstates}
    registers = get_registers(snapshot)
    config = {}
    if len(memory) == 0x20000:
        config['frame_duration'] = FRAME_DURATIONS[1]
        config['int_active'] = INT_ACTIVE[1]
    return Simulator(memory, registers, state, config)

def supported(snapshot):
    if snapshot is None:
        return False
    if snapshot.type == 'Z80':
        header = snapshot.header
        if len(header) == 30:
            # Version 1
            return True
        machine_id = header[34]
        if len(header) == 55:
            # Version 2
            return machine_id in (0, 3)
        # Version 3
        return machine_id in (0, 4, 12)
    elif snapshot.type == 'SZX':
        machine_id = snapshot.header[6]
        return machine_id < 4
    return True

def run(infile, options):
    if options.screen and pygame:
        print(pygame_io.getvalue())
        pygame.init()
        scale = options.scale
        pygame.display.set_mode((256 * scale, 192 * scale))
        pygame.display.set_caption(os.path.basename(infile))
        p_rectangles = [[pygame.Rect(px * scale, py * scale, scale, scale) for py in range(192)] for px in range(256)]
        c_rectangles = [[pygame.Rect(px * scale, py * scale, 8 * scale, 8 * scale) for py in range(0, 192, 8)] for px in range(0, 256, 8)]
        screen = pygame.display.get_surface()
        clock = pygame.time.Clock()
    else:
        screen = None
    snapshot, input_rec = parse_rzx(infile)[0]
    if not supported(snapshot):
        error('Snapshot or machine type not supported')
    simulator = get_simulator(snapshot, options)
    if len(simulator.memory) == 0x20000:
        tracer = RZXTracer128(simulator, input_rec.frames, input_rec.tstates, snapshot.out7ffd)
    else:
        tracer = RZXTracer(simulator, input_rec.frames, input_rec.tstates)
    simulator.set_tracer(tracer)
    opcodes = simulator.opcodes
    memory = simulator.memory
    registers = simulator.registers
    frame_duration = simulator.frame_duration
    if options.trace:
        tracefile = open(options.trace, 'w')
    else:
        tracefile = None
    frames = -1
    num_frames = len(input_rec.frames)
    prev_scr = [None] * 6912
    run = True
    while run:
        fetch_counter = tracer.next_frame()
        if fetch_counter is None:
            break
        frames += 1
        if not options.quiet:
            p = (frames / num_frames) * 100
            msg = f'[{p:0.1f}%]'
            write(msg + chr(8) * len(msg))
        while fetch_counter > 0:
            pc = registers[24]
            r0 = registers[15]
            ld_r_a = memory[pc] == 0xED and memory[(pc + 1) % 65536] == 0x4F
            if tracefile:
                i = disassemble(memory, pc)[0]
                tracefile.write(f'F:{frames:05} T:{registers[25] % frame_duration:05} C:{fetch_counter:05} I:{len(tracer.readings):05} ${pc:04X} {i}\n')
            opcodes[memory[pc]]()
            if ld_r_a:
                fetch_counter -= 2
            else:
                fetch_counter -= 2 - ((registers[15] ^ r0) % 2)
        if screen:
            draw(screen, memory, frames, p_rectangles, c_rectangles, prev_scr)
            pygame.display.update()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
            clock.tick(options.fps)
            prev_scr = memory[16384:23296]
        if simulator.iff:
            if memory[pc] == 0x76:
                # Advance PC if the CPU was halted
                registers[24] = (registers[24] + 1) % 65536
            simulator.accept_interrupt(registers, memory, pc)
    if tracefile:
        tracefile.close()

parser = argparse.ArgumentParser(
    usage='%(prog)s [options] FILE',
    description="Play an RZX file.",
    add_help=False
)
parser.add_argument('infile', help=argparse.SUPPRESS, nargs='?')
group = parser.add_argument_group('Options')
group.add_argument('--trace', metavar='FILE',
                   help="Log executed instructions to a file.")
group.add_argument('--fps', type=int, default=50,
                   help="Run at this many frames per second.")
group.add_argument('--no-screen', dest='screen', action='store_false',
                   help="Run without a screen.")
group.add_argument('--scale', metavar='SCALE', type=int, default=2, choices=(1, 2, 3, 4),
                   help="Scale display up by this factor (1-4; default: 2).")
group.add_argument('--quiet', action='store_true',
                   help="Don't print progress percentage.")
namespace, unknown_args = parser.parse_known_args()
if unknown_args or namespace.infile is None:
    parser.exit(2, parser.format_help())
run(namespace.infile, namespace)