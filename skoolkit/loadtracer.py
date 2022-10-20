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

from skoolkit import write, write_line
from skoolkit.basic import TextReader
from skoolkit.simulator import (A, F, D, E, H, L, IXh, IXl, SP)

SILENCE = 0
PILOT = 1
SYNC = 2
DATA = 3
STOP = 4

SIM_TIMEOUT = 10 * 60 * 3500000 # 10 minutes of Z80 CPU time

def get_ear_samples(blocks):
    samples = []
    tstates = -1
    sample = 0xFF # EAR off (bit 6 set), no keys pressed
    ear = 0x40

    for i, (timings, data) in enumerate(blocks):
        # Pilot tone
        for n in range(timings.pilot_len):
            sample ^= ear
            if tstates < 0:
                tstates = 0
            else:
                tstates += timings.pilot
            samples.append((tstates, sample, PILOT, i))

        # Sync pulses
        for s in timings.sync:
            sample ^= ear
            tstates += s
            samples.append((tstates, sample, SYNC, i))

        # Data
        for b in data:
            for j in range(8):
                if b & 0x80:
                    duration = timings.one
                else:
                    duration = timings.zero
                for k in range(2):
                    sample ^= ear
                    tstates += duration
                    samples.append((tstates, sample, DATA, i))
                b <<= 1

        # Pause
        if i + 1 < len(blocks) and timings.pause:
            r = samples.pop()
            samples.append((r[0], r[1], SILENCE, i + 1))
            tstates += timings.pause

    ts, sample, stype, bnum = samples[-1]
    samples.append((ts + 3500, sample, STOP, bnum))

    return samples

class LoadTracer:
    def __init__(self, blocks, stop):
        self.blocks = [b[1] for b in blocks]
        self.samples = get_ear_samples(blocks)
        self.index = 0
        self.max_index = len(self.samples) - 1
        self.stop = stop
        self.tape_started = None
        self.progress = 0
        self.tape_length = self.samples[-1][0] // 1000
        self.end_of_tape = 0
        self.tape_end_time = 0
        self.pulse_type = None
        self.custom_loader = False
        self.border = 7
        self.text = TextReader()

    def trace(self, simulator, address):
        if self.tape_started is not None:
            index = self.index
            samples = self.samples
            offset = simulator.tstates - self.tape_started
            block_num = samples[index][3]
            while index < self.max_index and samples[index + 1][0] < offset:
                index += 1 # pragma: no cover
            sample = samples[index]
            if sample[3] > block_num:
                # Pause tape between blocks
                self.tape_started = None # pragma: no cover
            else:
                if index == self.max_index:
                    self.end_of_tape += 1
                    if self.end_of_tape == 1:
                        write_line('Tape finished')
                        self.tape_end_time = simulator.tstates
                if self.custom_loader: # pragma: no cover
                    progress = sample[0] // self.tape_length
                    if progress > self.progress:
                        msg = f'[{progress/10:0.1f}%]'
                        write(msg + chr(8) * len(msg))
                        self.progress = progress
            self.index = index

        if simulator.pc == self.stop:
            write_line(f'Simulation stopped (PC at start address): PC={simulator.pc}')
            return True

        if simulator.pc == 0x0556:
            return self.fast_load(simulator)

        if self.end_of_tape and self.stop is None:
            if self.custom_loader: # pragma: no cover
                write_line(f'Simulation stopped (end of tape): PC={simulator.pc}')
                return True
            if simulator.pc > 0x3FFF:
                write_line(f'Simulation stopped (PC in RAM): PC={simulator.pc}')
                return True
            if simulator.tstates - self.tape_end_time > 3500000: # pragma: no cover
                write_line(f'Simulation stopped (tape ended 1 second ago): PC={simulator.pc}')
                return True

        if simulator.tstates > SIM_TIMEOUT: # pragma: no cover
            write_line(f'Simulation stopped (timed out): PC={simulator.pc}')
            return True

    def read_port(self, simulator, port):
        if port & 0xFF == 0xFE:
            read_tape = False
            if simulator.pc > 0x7FFF: # pragma: no cover
                self.custom_loader = True
                read_tape = True
            elif 0x0562 <= simulator.pc <= 0x05F1:
                read_tape = True # pragma: no cover

            if read_tape: # pragma: no cover
                if self.tape_started is None:
                    self.tape_started = simulator.tstates - self.samples[self.index][0]

                if self.index == self.max_index - 1:
                    ts, sample, stype, bnum = self.samples.pop()
                    self.samples.append((self.samples[-1][0], sample, STOP, bnum))

                pulse_type = self.samples[self.index][2]
                if pulse_type != self.pulse_type:
                    if pulse_type == PILOT:
                        write_line('Pilot tone')
                    elif pulse_type == SYNC:
                        write_line('Sync pulses')
                    elif pulse_type == DATA:
                        length = len(self.blocks[self.samples[self.index][3]])
                        write_line(f'Data ({length} bytes)\n')
                    self.pulse_type = pulse_type

                return self.samples[self.index][1]

    def write_port(self, simulator, port, value):
        if port & 0x01 == 0:
            self.border = value & 0x07

    def fast_load(self, simulator):
        block = self.blocks[self.samples[self.index][3]]
        registers = simulator.registers
        ix = registers[IXl] + 256 * registers[IXh] # Start address
        de = registers[E] + 256 * registers[D] # Block length
        a = registers[A]
        data_len = len(block) - 2

        # Preload the machine stack with 0x053F (as done at 0x055E)
        registers[H], registers[L] = 0x05, 0x3F # SA-LD-RET
        simulator.push(H)

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
                simulator.snapshot[ix:ix + de] = block[1:1 + de]
                registers[F] = 0x01 # Set carry flag: success
                ix += de
                de = 0
            else:
                simulator.snapshot[ix:ix + data_len + 1] = block[1:]
                registers[F] = 0x00 # Reset carry flag: error
                ix += data_len + 1
                de -= data_len + 1
            registers[IXh] = (ix >> 8) & 0xFF
            registers[IXl] = ix & 0xFF
            registers[D] = (de >> 8) & 0xFF
            registers[E] = de & 0xFF

        simulator.pc = 0x05E2

        block_num = self.samples[self.index][3]
        while self.index < self.max_index and self.samples[self.index][3] == block_num:
            self.index += 1
        if self.samples[self.index][3] > block_num:
            # Pause tape between blocks
            self.tape_started = None
        else:
            self.tape_started = simulator.tstates - self.samples[self.index][0]
        self.pulse_type = DATA
