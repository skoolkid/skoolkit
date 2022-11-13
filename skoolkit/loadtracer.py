# Copyright 2022 Richard Dymond (rjdymond@gmail.com)
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

from skoolkit import SkoolKitError, write, write_line
from skoolkit.basic import TextReader
from skoolkit.simulator import A, F, D, E, H, L, IXh, IXl, PC, T, R1

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

SIM_TIMEOUT = 10 * 60 * 3500000 # 10 minutes of Z80 CPU time

def get_edges(blocks):
    # Return a list of elements of the form
    #   [edges, data]
    # where each one corresponds to a block on the tape and
    # - 'edges' is a list of integers, each of which can be interpreted as the
    #   timestamp (in T-states) of an 'edge' in the tape block
    # - 'data' is a list of the byte values in the tape block (used for fast
    #   loading where possible)

    tape_blocks = [[[], []]]
    tstates = -1

    for i, (timings, data) in enumerate(blocks):
        edges = tape_blocks[-1][0]

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
            for b in data:
                for j in range(8):
                    if b & 0x80:
                        duration = timings.one
                    else:
                        duration = timings.zero
                    for k in range(2):
                        tstates += duration
                        edges.append(tstates)
                    b *= 2
            tape_blocks[-1][1][:] = data
            if i < len(blocks) - 1:
                tape_blocks.append([[], []])

    return tape_blocks

class LoadTracer:
    def __init__(self, blocks):
        self.blocks = get_edges(blocks)
        self.block_index = -1
        self.next_block()
        self.end_of_tape = 0
        self.tape_end_time = 0
        self.custom_loader = False
        self.border = 7
        self.text = TextReader()

    def run(self, simulator, start, stop):
        opcodes = simulator.opcodes
        memory = simulator.memory
        registers = simulator.registers
        opcodes[0x3D] = partial(self.dec_a, registers, memory)
        registers[24] = start
        pc = start
        progress = 0
        tape_length = self.blocks[-1][0][-1] // 1000

        while True:
            opcodes[memory[pc]]()
            pc = registers[24]
            tstates = registers[25]

            if self.tape_running and tstates > self.next_edge: # pragma: no cover
                index = self.index
                max_index = self.max_index
                edges = self.edges
                while index < max_index and edges[index + 1] < tstates:
                    index += 1
                self.index = index
                if index == max_index:
                    if tstates - edges[index] > 3500:
                        # Move to the next block on the tape if the final edge
                        # of the current block hasn't been read in over 1ms
                        self.next_block(tstates)
                else:
                    self.next_edge = edges[index + 1]
                    p = edges[index] // tape_length
                    if p > progress:
                        msg = f'[{p/10:0.1f}%]'
                        write(msg + chr(8) * len(msg))
                        progress = p

            if pc == stop:
                write_line(f'Simulation stopped (PC at start address): PC={pc}')
                break

            if pc == 0x0556:
                self.fast_load(simulator)
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

    def read_port(self, registers, port):
        if port % 256 == 0xFE:
            pc = registers[24]
            if pc > 0x7FFF or 0x0562 <= pc <= 0x05F1: # pragma: no cover
                self.custom_loader = True
                index = self.index
                if not self.tape_running:
                    self.tape_running = True
                    registers[T] = self.edges[0]
                    length = len(self.blocks[self.block_index][1])
                    write_line(f'Data ({length} bytes)\n')
                elif index == self.max_index:
                    self.next_block(registers[T])
                if index % 2:
                    return 255
        return 191

    def write_port(self, registers, port, value):
        if port % 2 == 0:
            self.border = value % 8

    def next_block(self, tstates=None):
        self.block_index += 1
        if self.block_index >= len(self.blocks):
            self.end_of_tape += 1
            if self.end_of_tape == 1:
                write_line('Tape finished')
                self.tape_end_time = tstates
        else:
            self.edges = self.blocks[self.block_index][0]
            self.next_edge = self.edges[0]
            self.index = 0
            self.max_index = len(self.edges) - 1
        self.tape_running = False

    def fast_load(self, simulator):
        if self.block_index < len(self.blocks):
            block = self.blocks[self.block_index][1]
        else:
            raise SkoolKitError("Failed to fast load block: unexpected end of tape")
        registers = simulator.registers
        memory = simulator.memory
        ix = registers[IXl] + 256 * registers[IXh] # Start address
        de = registers[E] + 256 * registers[D] # Block length
        a = registers[A]
        data_len = len(block) - 2

        # Preload the machine stack with 0x053F (as done at 0x055E)
        registers[H], registers[L] = 0x05, 0x3F # SA-LD-RET
        simulator.push(registers, memory, R1, 11, 1, H, L)

        if a == block[0]:
            skipped = ''
        else:
            skipped = ' [skipped]\n'
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
            write_line(f'Fast loading data block: {ix},{de}\n')

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
        self.next_block(registers[T])
