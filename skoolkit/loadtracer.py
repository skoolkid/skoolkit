# Copyright 2022, 2023 Richard Dymond (rjdymond@gmail.com)
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

from functools import partial

from skoolkit import SkoolKitError, open_file, write, write_line
from skoolkit.basic import TextReader
from skoolkit.simulator import A, F, D, E, H, L, IXh, IXl, PC, T, R1, FRAME_DURATION
from skoolkit.traceutils import disassemble

DEC = tuple(tuple((
        v % 256,
        (v & 0xA8)                 # S.5.3...
        + (v == 0) * 0x40          # .Z......
        + (v % 16 == 0x0F) * 0x10  # ...H....
        + (v == 0x7F) * 0x04       # .....P..
        + 0x02                     # ......N.
        + c                        # .......C
    ) for v in range(-1, 255)
    ) for c in (0, 1)
)

INC = tuple(tuple((
        v % 256,
        (v & 0xA8)                 # S.5.3.N.
        + (v == 256) * 0x40        # .Z......
        + (v % 16 == 0x00) * 0x10  # ...H....
        + (v == 0x80) * 0x04       # .....P..
        + c                        # .......C
    ) for v in range(1, 257)
    ) for c in (0, 1)
)

SIM_TIMEOUT = 10 * 60 * 3500000 # 10 minutes of Z80 CPU time

def get_edges(blocks):
    edges = []
    indexes = []
    data_blocks = []
    tstates = -1

    for i, (timings, data) in enumerate(blocks):
        # Pilot tone
        for n in range(timings.pilot_len):
            if tstates < 0:
                tstates = 0
            else:
                tstates += timings.pilot
            edges.append(tstates)

        # Sync pulses
        for s in timings.sync:
            tstates += s
            edges.append(tstates)

        # Data
        if data:
            start = len(edges) - 1
            for k, b in enumerate(data, 1):
                if k < len(data):
                    num_bits = 8
                else:
                    num_bits = timings.used_bits
                for j in range(num_bits):
                    if b & 0x80:
                        duration = timings.one
                    else:
                        duration = timings.zero
                    for k in range(2):
                        tstates += duration
                        edges.append(tstates)
                    b *= 2
            indexes.append((start, len(edges) - 1))
            data_blocks.append(data)

        # Pause
        if i + 1 < len(blocks) and timings.pause:
            tstates += timings.pause

    return edges, indexes, data_blocks

class LoadTracer:
    def __init__(self, simulator, blocks, accelerator, pause, polarity):
        self.simulator = simulator
        self.edges, self.indexes, self.blocks = get_edges(blocks)
        self.accelerator = accelerator
        self.pause = pause
        self.ear = (191 + 64 * polarity, 255 - 64 * polarity)
        self.announce_data = True
        opcodes = simulator.opcodes
        memory = simulator.memory
        registers = simulator.registers
        if accelerator:
            opcodes[0x3D] = partial(self.dec_a, registers, memory)
            if isinstance(accelerator, set):
                inc_b_acc = []
                for acc in accelerator:
                    if acc and acc.opcode == 0x05:
                        # There is exactly one accelerator that uses 'DEC B'
                        opcodes[0x05] = partial(self.dec_b, registers, memory, acc, len(acc.code))
                    elif acc:
                        inc_b_acc.append(acc)
                opcodes[0x04] = partial(self.inc_b_auto, registers, memory, inc_b_acc)
            else: # pragma: no cover
                if accelerator.opcode == 0x05:
                    method = self.dec_b
                elif None in accelerator.code:
                    method = self.inc_b_none
                else:
                    method = self.inc_b
                opcodes[accelerator.opcode] = partial(method, registers, memory, accelerator, len(accelerator.code))
        self.next_edge = 0
        self.block_index = 0
        self.block_data_index, self.block_max_index = self.indexes[0]
        self.index = 0
        self.max_index = len(self.edges) - 1
        self.tape_running = False
        self.end_of_tape = 0
        self.tape_end_time = 0
        self.custom_loader = False
        self.border = 7
        self.text = TextReader()

    def run(self, start, stop, fast_load, trace):
        simulator = self.simulator
        opcodes = simulator.opcodes
        memory = simulator.memory
        registers = simulator.registers
        registers[24] = start
        pc = start
        progress = 0
        edges = self.edges
        tape_length = edges[-1] // 1000
        max_index = self.max_index
        tstates = 0
        accept_int = False
        if trace:
            tracefile = open_file(trace, 'w')

        while True:
            if trace:
                i = disassemble(memory, pc)[0]
                tracefile.write(f'${pc:04X} {i}\n')

            t0 = tstates
            opcodes[memory[pc]]()
            tstates = registers[25]

            if simulator.iff:
                if tstates // FRAME_DURATION > t0 // FRAME_DURATION:
                    accept_int = True
                if accept_int:
                    accept_int = simulator.accept_interrupt(registers, memory, pc)

            if self.tape_running and tstates > self.next_edge: # pragma: no cover
                index = self.index
                while index < max_index and edges[index + 1] < tstates:
                    index += 1
                self.index = index
                if index == max_index:
                    # Allow 1ms for the final edge on the tape to be read
                    if tstates - edges[index] > 3500:
                        self.stop_tape(tstates)
                elif index > self.block_max_index:
                    # Pause tape between blocks
                    self.next_block(tstates)
                else:
                    self.next_edge = edges[index + 1]
                    if index < self.block_max_index:
                        p = edges[index] // tape_length
                        if p > progress:
                            msg = f'[{p/10:0.1f}%]'
                            write(msg + chr(8) * len(msg))
                            progress = p

            pc = registers[24]

            if pc == stop:
                write_line(f'Simulation stopped (PC at start address): PC={pc}')
                break

            if pc == 0x0556 and fast_load:
                self.fast_load(simulator)
                self.index = self.block_max_index
                if self.index == max_index:
                    # Final block, so stop the tape
                    self.stop_tape(tstates)
                else:
                    # Otherwise continue to play the tape until this block's
                    # 'pause' period (if any) has elapsed
                    self.tape_running = True
                    registers[25] = self.next_edge = edges[self.index]
                pc = registers[24]
            else:
                if self.end_of_tape and stop is None:
                    if self.custom_loader: # pragma: no cover
                        write_line(f'Simulation stopped (end of tape): PC={pc}')
                        break
                    if pc > 0x3FFF:
                        write_line(f'Simulation stopped (PC in RAM): PC={pc}')
                        break
                    if tstates - self.tape_end_time > 3500000: # pragma: no cover
                        write_line(f'Simulation stopped (tape ended 1 second ago): PC={pc}')
                        break
                if tstates > SIM_TIMEOUT: # pragma: no cover
                    write_line(f'Simulation stopped (timed out): PC={pc}')
                    break

        if trace:
            tracefile.close()

    def dec_a(self, registers, memory):
        # Speed up any
        #   LD_DELAY: DEC A
        #             JR NZ,LD_DELAY
        # loop, which is common in tape loading routines
        a = registers[0]
        pcn = registers[24] + 1
        if a and memory[pcn:pcn + 2] == [0x20, 0xFD]: # pragma: no cover
            registers[0] = 0
            registers[1] = 0x42 + (registers[1] % 2)
            r = registers[15]
            registers[15] = (r & 0x80) + ((r + a * 2) % 128)
            registers[25] += 16 * a - 5
            registers[24] = (pcn + 2) % 65536
        else:
            registers[:2] = DEC[registers[1] % 2][a]
            registers[15] = R1[registers[15]]
            registers[25] += 4
            registers[24] = pcn % 65536

    def dec_b(self, registers, memory, acc, code_len): # pragma: no cover
        # Speed up the tape-sampling loop with a loader-specific accelerator
        b = registers[2]
        loops = 0
        pcn = registers[24] + 1
        if self.tape_running and memory[pcn:pcn + code_len] == acc.code:
            if registers[3] & acc.ear_mask == (self.index % 2) * acc.ear_mask:
                delta = self.next_edge - registers[25] - acc.in_time
                if delta >= 0:
                    loops = min(delta // acc.loop_time + 1, (b - 1) % 256)
        registers[2], registers[1] = DEC[registers[1] % 2][(b - loops) % 256]
        r = registers[15]
        registers[15] = (r & 0x80) + ((r + acc.loop_r_inc * loops + 1) % 0x80)
        registers[25] += acc.loop_time * loops + 4
        registers[24] = pcn % 65536

    def inc_b(self, registers, memory, acc, code_len): # pragma: no cover
        # Speed up the tape-sampling loop with a loader-specific accelerator
        b = registers[2]
        loops = 0
        pcn = registers[24] + 1
        if self.tape_running and memory[pcn:pcn + code_len] == acc.code:
            if registers[3] & acc.ear_mask == (self.index % 2) * acc.ear_mask:
                delta = self.next_edge - registers[25] - acc.in_time
                if delta >= 0:
                    loops = min(delta // acc.loop_time + 1, 255 - b)
        registers[2], registers[1] = INC[registers[1] % 2][b + loops]
        r = registers[15]
        registers[15] = (r & 0x80) + ((r + acc.loop_r_inc * loops + 1) % 0x80)
        registers[25] += acc.loop_time * loops + 4
        registers[24] = pcn % 65536

    def inc_b_none(self, registers, memory, acc, code_len): # pragma: no cover
        # Speed up the tape-sampling loop with a loader-specific accelerator
        b = registers[2]
        loops = 0
        pcn = registers[24] + 1
        if self.tape_running and all(x == y or y is None for x, y in zip(memory[pcn:pcn + code_len], acc.code)):
            if registers[3] & acc.ear_mask == (self.index % 2) * acc.ear_mask:
                delta = self.next_edge - registers[25] - acc.in_time
                if delta >= 0:
                    loops = min(delta // acc.loop_time + 1, 255 - b)
        registers[2], registers[1] = INC[registers[1] % 2][b + loops]
        r = registers[15]
        registers[15] = (r & 0x80) + ((r + acc.loop_r_inc * loops + 1) % 0x80)
        registers[25] += acc.loop_time * loops + 4
        registers[24] = pcn % 65536

    def inc_b_auto(self, registers, memory, accelerators):
        # Speed up the tape-sampling loop with an automatically selected
        # loader-specific accelerator
        b = registers[2]
        pcn = registers[24] + 1
        if self.tape_running:
            loops = 0
            for i, acc in enumerate(accelerators):
                if all(x == y or y is None for x, y in zip(memory[pcn:pcn + len(acc.code)], acc.code)): # pragma: no cover
                    if registers[3] & acc.ear_mask == (self.index % 2) * acc.ear_mask:
                        delta = self.next_edge - registers[25] - acc.in_time
                        if delta >= 0:
                            loops = min(delta // acc.loop_time + 1, 255 - b)
                    if i:
                        # Move the selected accelerator to the beginning of the
                        # list so that it can be found quicker next time
                        accelerators.remove(acc)
                        accelerators.insert(0, acc)
                    registers[2], registers[1] = INC[registers[1] % 2][b + loops]
                    r = registers[15]
                    registers[15] = (r & 0x80) + ((r + acc.loop_r_inc * loops + 1) % 0x80)
                    registers[25] += acc.loop_time * loops + 4
                    registers[24] = pcn % 65536
                    return
        registers[2], registers[1] = INC[registers[1] % 2][b]
        registers[15] = R1[registers[15]]
        registers[25] += 4
        registers[24] = pcn % 65536

    def read_port(self, registers, port):
        if port % 256 == 0xFE:
            pc = registers[24]
            if pc > 0x7FFF or 0x0562 <= pc <= 0x05F1: # pragma: no cover
                self.custom_loader = True
                index = self.index
                if self.announce_data and not self.end_of_tape:
                    self.announce_data = False
                    self.tape_running = True
                    registers[T] = self.edges[index]
                    length = len(self.blocks[self.block_index])
                    if length:
                        write_line(f'Data ({length} bytes)')
                elif index == self.max_index:
                    # Final edge, so stop the tape
                    self.stop_tape(registers[T])
                return self.ear[index % 2]
        return 191

    def write_port(self, registers, port, value):
        if port % 2 == 0:
            self.border = value % 8

    def next_block(self, tstates):
        self.block_index += 1
        if self.block_index >= len(self.blocks):
            self.stop_tape(tstates) # pragma: no cover
        else:
            self.index = self.block_max_index + 1
            self.next_edge = self.edges[self.index]
            self.block_data_index, self.block_max_index = self.indexes[self.block_index]
            self.tape_running = not self.pause
            self.announce_data = True

    def stop_tape(self, tstates):
        self.block_index = len(self.blocks)
        self.end_of_tape += 1
        if self.end_of_tape == 1:
            write_line('Tape finished')
            self.tape_end_time = tstates
        self.tape_running = False

    def fast_load(self, simulator):
        registers = simulator.registers
        while self.block_data_index <= self.index < self.max_index:
            self.next_block(registers[T])
        if self.block_index < len(self.blocks):
            block = self.blocks[self.block_index]
        else:
            raise SkoolKitError("Failed to fast load block: unexpected end of tape")
        memory = simulator.memory
        ix = registers[IXl] + 256 * registers[IXh] # Start address
        de = registers[E] + 256 * registers[D] # Block length
        a = registers[A]
        data_len = len(block) - 2

        # Disable interrupts (as done at 0x0559), and preload the machine stack
        # with 0x053F (as done at 0x055E)
        simulator.iff = 0
        registers[H], registers[L] = 0x05, 0x3F # SA-LD-RET
        simulator.push(registers, memory, R1, 11, 1, H, L)

        if a == block[0]:
            skipped = ''
        else:
            skipped = ' [skipped]'
        if block[0] == 0 and data_len >= 17 and block[1] <= 3:
            name = ''.join(self.text.get_chars(b) for b in block[2:12])
            if block[1] == 3:
                write_line(f'Bytes: {name}{skipped}')
            elif block[1] == 2:
                write_line(f'Character array: {name}{skipped}')
            elif block[1] == 1:
                write_line(f'Number array: {name}{skipped}')
            elif block[1] == 0:
                write_line(f'Program: {name}{skipped}')
        elif skipped:
            write_line(f'Data block ({data_len} bytes){skipped}')
        else:
            write_line(f'Fast loading data block: {ix},{de}')

        if skipped:
            registers[F] = 0x00 # Reset carry flag: error
        else:
            if de <= data_len:
                memory[ix:ix + de] = block[1:1 + de]
                registers[F] = 0x01 # Set carry flag: success
                ix += de
                de = 0
            else:
                memory[ix:ix + data_len + 1] = block[1:]
                registers[F] = 0x00 # Reset carry flag: error
                ix += data_len + 1
                de -= data_len + 1
            registers[IXh] = (ix >> 8) & 0xFF
            registers[IXl] = ix & 0xFF
            registers[D] = (de >> 8) & 0xFF
            registers[E] = de & 0xFF

        registers[PC] = 0x05E2
        self.announce_data = False
