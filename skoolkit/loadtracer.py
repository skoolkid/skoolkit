# Copyright 2022-2024 Richard Dymond (rjdymond@gmail.com)
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

import array
from collections import defaultdict
from functools import partial

from skoolkit import SkoolKitError, write, write_line
from skoolkit.basic import TextReader
from skoolkit.pagingtracer import PagingTracer
from skoolkit.simulator import R1
from skoolkit.simutils import A, D, E, F, H, L, IXh, IXl, R, SP, PC, T, IFF
from skoolkit.traceutils import Registers, disassemble, get_trace_line

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

class DataBlock:
    def __init__(self, data, start, end, fast_load=True):
        self.data = data
        self.start = start
        self.end = end
        self.fast_load = fast_load

    def adjust(self, max_index):
        self.start = min(self.start, max_index)
        self.end = min(self.end, max_index)

def _check_polarity(timings, polarity, edges, tstates, analysis):
    if timings.polarity is not None:
        ear = (len(edges) - 1) % 2
        if ear != timings.polarity ^ (polarity % 2):
            if analysis:
                analysis.append(f'{tstates:>10}  {ear:>3}  Polarity adjustment ({ear}->{ear ^ 1})')
            edges.append(tstates)

def get_edges(blocks, first_edge, polarity, analyse=False):
    edges = [first_edge]
    if polarity % 2:
        edges.append(first_edge)
    data_blocks = []
    tstates = first_edge
    tail = first_edge - 1
    if analyse:
        analysis = ['T-states    EAR  Description']
    else:
        analysis = ()

    for i, block in enumerate(blocks):
        timings = block.timings
        data = block.data

        # Pulses
        if timings.pulses:
            _check_polarity(timings, polarity, edges, tstates, analysis)
            for count, duration in timings.pulses:
                if analyse:
                    ear = (len(edges) - 1) % 2
                    if count == 1:
                        analysis.append(f'{tstates:>10}  {ear:>3}  Pulse ({duration} T-states)')
                    else:
                        analysis.append(f'{tstates:>10}  {ear:>3}  Tone ({count} x {duration} T-states)')
                for n in range(count):
                    tstates += duration
                    edges.append(tstates)

        # Data
        if data:
            _check_polarity(timings, polarity, edges, tstates, analysis)
            if analyse:
                if timings.used_bits < 8:
                    bits = f' + {timings.used_bits} bits'
                    data_len = len(data) - 1
                else:
                    bits = ''
                    data_len = len(data)
                ear = (len(edges) - 1) % 2
                zero = ','.join(str(d) for d in timings.zero)
                one = ','.join(str(d) for d in timings.one)
                analysis.append(f'{tstates:>10}  {ear:>3}  Data ({data_len} bytes{bits}; {zero}/{one} T-states)')
            start = len(edges) - 1
            for k, b in enumerate(data, 1):
                if k < len(data):
                    num_bits = 8
                else:
                    num_bits = timings.used_bits
                for j in range(num_bits):
                    if b & 0x80:
                        durations = timings.one
                    else:
                        durations = timings.zero
                    for d in durations:
                        tstates += d
                        edges.append(tstates)
                    b *= 2

            # Tail pulse
            if timings.tail:
                if analyse:
                    ear = (len(edges) - 1) % 2
                    analysis.append(f'{tstates:>10}  {ear:>3}  Tail pulse ({timings.tail} T-states)')
                tstates += timings.tail
                tail = tstates
                edges.append(tstates)

            if 0 in timings.zero or 0 in timings.one:
                # This is sample data as opposed to byte values, so ensure it's
                # not fast-loaded
                data_blocks.append(DataBlock(data, len(edges) - 1, len(edges) - 1, False))
            else:
                data_blocks.append(DataBlock(data, start, len(edges) - 1))
        elif timings.data or (i == len(blocks) - 1 and timings.pulses):
            # If this block contains a Direct Recording, or is the last block
            # on the tape and contains pulses but no data, add a data block to
            # ensure that the pulses are read
            data_blocks.append(DataBlock((), len(edges) - 1, len(edges) - 1, False))

        # Pause
        if i + 1 < len(blocks) and timings.pause:
            _check_polarity(timings, polarity, edges, tstates, analysis)
            if analyse:
                ear = (len(edges) - 1) % 2
                analysis.append(f'{tstates:>10}  {ear:>3}  Pause ({timings.pause} T-states)')
            tstates += timings.pause

    if edges[-1] == tail:
        edges.pop()
        if analysis:
            analysis.pop()
        if data_blocks:
            data_blocks[-1].adjust(len(edges) - 1)

    for line in analysis:
        print(line)

    return edges, data_blocks

class LoadTracer(PagingTracer):
    def __init__(self, simulator, blocks, accelerators, pause, first_edge, polarity,
                 in_min_addr, accel_dec_a, list_accelerators, border, out7ffd, outfffd, ay, outfe):
        self.acc_usage = defaultdict(int)
        self.inc_b_misses = 0
        self.dec_b_misses = 0
        self.dec_a_jr_hits = 0
        self.dec_a_jp_hits = 0
        self.dec_a_misses = 0
        self.simulator = simulator
        self.edges, self.blocks = get_edges(blocks, first_edge, polarity)
        self.pause = pause
        self.in_min_addr = in_min_addr
        self.announce_data = True
        self.accelerators = accelerators
        if hasattr(simulator, 'opcodes'):
            opcodes = simulator.opcodes
            memory = simulator.memory
            registers = simulator.registers
            if list_accelerators and accel_dec_a:
                opcodes[0x3D] = partial(self.dec_a_list, registers, memory)
            elif accel_dec_a == 1:
                opcodes[0x3D] = partial(self.dec_a_jr, registers, memory)
            elif accel_dec_a == 2:
                opcodes[0x3D] = partial(self.dec_a_jp, registers, memory)
            if accelerators:
                inc_b_acc = []
                dec_b_acc = []
                for accelerator in accelerators:
                    if accelerator.opcode == 0x04:
                        inc_b_acc.append(accelerator)
                    else:
                        dec_b_acc.append(accelerator)
                if list_accelerators:
                    opcodes[0x04] = partial(self.list_accelerators, registers, memory, inc_b_acc, self.inc_b_auto, 0x04)
                    opcodes[0x05] = partial(self.list_accelerators, registers, memory, dec_b_acc, self.dec_b_auto, 0x05)
                else:
                    if len(inc_b_acc) == 1:
                        accelerator = inc_b_acc[0]
                        if None in accelerator.code:
                            opcodes[0x04] = partial(self.inc_b_none, registers, memory, accelerator)
                        else:
                            opcodes[0x04] = partial(self.inc_b, registers, memory, accelerator)
                    elif inc_b_acc:
                        opcodes[0x04] = partial(self.inc_b_auto, registers, memory, inc_b_acc)
                    if len(dec_b_acc) == 1:
                        opcodes[0x05] = partial(self.dec_b, registers, memory, dec_b_acc[0])
                    elif dec_b_acc:
                        opcodes[0x05] = partial(self.dec_b_auto, registers, memory, dec_b_acc)
        self.block_index = 0
        self.block_data_index = self.blocks[0].start
        self.max_index = len(self.edges) - 1
        self.border = border
        if len(simulator.memory) == 65536:
            self.out7ffd = 0x10 # Signal: 48K ROM always
        else: # pragma: no cover
            self.out7ffd = out7ffd # 128K ROM 0/1
        self.outfffd = outfffd
        self.ay = ay
        self.outfe = outfe
        self.text = TextReader()
        self.state = [
            0,                  # state[0]: next edge (timestamp)
            0,                  # state[1]: edge index
            0,                  # state[2]: end of tape reached
            self.blocks[0].end, # state[3]: index of final edge in current block
            0,                  # state[4]: tape running
            accel_dec_a,        # state[5]
            list_accelerators,  # state[6]
            0,                  # state[7]: custom loader detected
            0,                  # state[8]: tape end time
        ]
        if hasattr(simulator, 'load'): # pragma: no cover
            self.edges = array.array('Q', self.edges)
            self.state = array.array('Q', self.state)
        self.read_port = partial(self._read_port, self.state)

    def run(self, stop, fast_load, finish_tape, timeout, tracefile, trace_line, prefix, byte_fmt, word_fmt):
        simulator = self.simulator
        memory = simulator.memory
        registers = simulator.registers
        if tracefile:
            trace_line = get_trace_line(trace_line)
            r = Registers(registers)
            m = memory

        if hasattr(simulator, 'load'): # pragma: no cover
            if tracefile:
                df = lambda pc: disassemble(memory, pc, prefix, byte_fmt, word_fmt)[0]
                tf = lambda pc, i, t0: tracefile.write(trace_line.format(pc=pc, i=i, r=r, t=t0, m=m))
            else:
                df = tf = None
            ppf = lambda p: write(f'[{p/10:5.1f}%]\x08\x08\x08\x08\x08\x08\x08\x08')
            stop_cond = simulator.load(stop, fast_load, finish_tape, timeout, ppf, df, tf)
            pc = registers[24]
        else:
            opcodes = simulator.opcodes
            frame_duration = simulator.frame_duration
            int_active = simulator.int_active
            pc = registers[24]
            progress = 0
            edges = self.edges
            tape_length = edges[-1] // 1000
            max_index = self.max_index
            tstates = registers[25]
            state = self.state
            while True:
                t0 = tstates
                if tracefile:
                    i = disassemble(memory, pc, prefix, byte_fmt, word_fmt)[0]
                    opcodes[memory[pc]]()
                    tracefile.write(trace_line.format(pc=pc, i=i, r=r, t=t0, m=m))
                else:
                    opcodes[memory[pc]]()
                tstates = registers[25]

                if registers[26] and tstates % frame_duration < int_active:
                    simulator.accept_interrupt(registers, memory, pc)
                    tstates = registers[25]

                if state[4] and tstates >= state[0]:
                    index = state[1]
                    while index < max_index and edges[index + 1] < tstates:
                        index += 1
                    state[1] = index
                    if index == max_index:
                        # Allow 1ms for the final edge on the tape to be read
                        if tstates - edges[index] > 3500:
                            self.stop_tape(tstates) # pragma: no cover
                    elif index > state[3]:
                        # Pause tape between blocks
                        self.next_block(tstates) # pragma: no cover
                    else:
                        state[0] = edges[index + 1]
                        if index < state[3]:
                            p = edges[index] // tape_length
                            if p > progress:
                                write(f'[{p/10:5.1f}%]\x08\x08\x08\x08\x08\x08\x08\x08')
                                progress = p

                pc = registers[24]

                if pc == stop and (state[2] or not finish_tape):
                    stop_cond = 0
                    break

                if pc == 0x0556 and self.out7ffd & 0x10 and fast_load and self.fast_load(simulator):
                    state[1] = state[3]
                    if state[1] == max_index:
                        # Final block, so stop the tape
                        self.stop_tape(tstates)
                    else:
                        # Otherwise continue to play the tape until this block's
                        # 'pause' period (if any) has elapsed
                        state[4] = 1 # Signal: tape is running
                        registers[25] = state[0] = edges[state[1]]
                    pc = registers[24]
                else:
                    if state[2] and stop is None:
                        # The tape has ended and no stop address is set
                        if state[7]:
                            # Custom loader was detected
                            stop_cond = 1
                            break
                        if pc > 0x3FFF:
                            # PC in RAM
                            stop_cond = 2
                            break
                        if tstates - self.state[8] > 3500000: # pragma: no cover
                            # Tape ended 1 second ago
                            stop_cond = 3
                            break
                    if tstates > timeout: # pragma: no cover
                        stop_cond = 4
                        break

        if stop_cond == 0:
            write_line(f'Simulation stopped (PC at start address): PC={pc}')
        elif stop_cond == 1:
            write_line(f'Simulation stopped (end of tape): PC={pc}')
        elif stop_cond == 2:
            write_line(f'Simulation stopped (PC in RAM): PC={pc}')
        elif stop_cond == 3: # pragma: no cover
            write_line(f'Simulation stopped (tape ended 1 second ago): PC={pc}')
        elif stop_cond == 4: # pragma: no cover
            write_line(f'Simulation stopped (timed out): PC={pc}')

    def dec_a_jr(self, registers, memory):
        # Speed up any
        #   LD_DELAY: DEC A
        #             JR NZ,LD_DELAY
        # loop, which is common in tape loading routines
        a = registers[0]
        pcn = (registers[24] + 1) % 65536
        if registers[26] == 0 and a and memory[pcn] == 0x20 and memory[(pcn + 1) % 65536] == 0xFD:
            registers[0] = 0
            registers[1] = 0x42 + (registers[1] % 2)
            r = registers[15]
            registers[15] = (r & 0x80) + ((r + a * 2) % 128)
            registers[25] += 16 * a - 5
            registers[24] = (pcn + 2) % 65536
        else:
            registers[0], registers[1] = DEC[registers[1] % 2][a]
            registers[15] = R1[registers[15]]
            registers[25] += 4
            registers[24] = pcn % 65536

    def dec_a_jp(self, registers, memory):
        # Speed up any
        #   LD_DELAY: DEC A
        #             JP NZ,LD_DELAY
        # loop, which is used in a few tape loading routines
        a = registers[0]
        pc = registers[24]
        if registers[26] == 0 and a and memory[(pc + 1) % 65536] == 0xC2 and memory[(pc + 2) % 65536] == pc % 256 and memory[(pc + 3) % 65536] == pc // 256:
            registers[0] = 0
            registers[1] = 0x42 + (registers[1] % 2)
            r = registers[15]
            registers[15] = (r & 0x80) + ((r + a * 2) % 128)
            registers[25] += 14 * a
            registers[24] = (pc + 4) % 65536
        else:
            registers[0], registers[1] = DEC[registers[1] % 2][a]
            registers[15] = R1[registers[15]]
            registers[25] += 4
            registers[24] = (pc + 1) % 65536

    def dec_a_list(self, registers, memory):
        # Speed up any 'DEC A: JR/JP NZ,$-1' loop, and also count hits and
        # misses
        pc = registers[24]
        if registers[26] == 0:
            if memory[(pc + 1) % 65536] == 0x20 and memory[(pc + 2) % 65536] == 0xFD:
                self.dec_a_jr_hits += 1
                self.dec_a_jr(registers, memory)
                return
            if memory[(pc + 1) % 65536] == 0xC2 and memory[(pc + 2) % 65536] == pc % 256 and memory[(pc + 3) % 65536] == pc // 256:
                self.dec_a_jp_hits += 1
                self.dec_a_jp(registers, memory)
                return
        self.dec_a_misses += 1
        registers[0], registers[1] = DEC[registers[1] % 2][registers[0]]
        registers[15] = R1[registers[15]]
        registers[25] += 4
        registers[24] = (pc + 1) % 65536

    def dec_b(self, registers, memory, acc):
        # Speed up the tape-sampling loop with a loader-specific accelerator
        b = registers[2]
        loops = 0
        pcn = registers[24] + 1
        if self.state[4] and registers[26] == 0 and memory[pcn - acc.c0:pcn + acc.c1] == acc.code:
            if registers[3] & acc.ear_mask == ((self.state[1] - acc.polarity) % 2) * acc.ear_mask:
                delta = self.state[0] - registers[25] - acc.in_time
                if delta > 0:
                    loops = min(delta // acc.loop_time + 1, (b - 1) % 256)
                    if loops:
                        # The carry flag is cleared on each loop iteration
                        registers[1] &= 0xFE
        registers[2], registers[1] = DEC[registers[1] % 2][(b - loops) % 256]
        r = registers[15]
        registers[15] = (r & 0x80) + ((r + acc.loop_r_inc * loops + 1) % 0x80)
        registers[25] += acc.loop_time * loops + 4
        registers[24] = pcn % 65536

    def dec_b_auto(self, registers, memory, accelerators):
        # Speed up the tape-sampling loop with an automatically selected
        # loader-specific accelerator
        b = registers[2]
        pcn = registers[24] + 1
        if self.state[4] and registers[26] == 0:
            loops = 0
            for i, acc in enumerate(accelerators):
                if memory[pcn - acc.c0:pcn + acc.c1] == acc.code:
                    if registers[3] & acc.ear_mask == ((self.state[1] - acc.polarity) % 2) * acc.ear_mask:
                        delta = self.state[0] - registers[25] - acc.in_time
                        if delta > 0:
                            loops = min(delta // acc.loop_time + 1, (b - 1) % 256)
                            if loops:
                                # The carry flag is cleared on each loop iteration
                                registers[1] &= 0xFE
                    if i:
                        # Move the selected accelerator to the beginning of the
                        # list so that it can be found quicker next time
                        accelerators.remove(acc)
                        accelerators.insert(0, acc)
                    registers[2], registers[1] = DEC[registers[1] % 2][(b - loops) % 256]
                    r = registers[15]
                    registers[15] = (r & 0x80) + ((r + acc.loop_r_inc * loops + 1) % 0x80)
                    registers[25] += acc.loop_time * loops + 4
                    registers[24] = pcn % 65536
                    return
        registers[2], registers[1] = DEC[registers[1] % 2][b]
        registers[15] = R1[registers[15]]
        registers[25] += 4
        registers[24] = pcn % 65536

    def inc_b(self, registers, memory, acc):
        # Speed up the tape-sampling loop with a loader-specific accelerator
        b = registers[2]
        loops = 0
        pcn = registers[24] + 1
        if self.state[4] and registers[26] == 0 and memory[pcn - acc.c0:pcn + acc.c1] == acc.code:
            if registers[3] & acc.ear_mask == ((self.state[1] - acc.polarity) % 2) * acc.ear_mask:
                delta = self.state[0] - registers[25] - acc.in_time
                if delta > 0:
                    loops = min(delta // acc.loop_time + 1, 255 - b)
                    if loops:
                        # The carry flag is cleared on each loop iteration
                        registers[1] &= 0xFE
        registers[2], registers[1] = INC[registers[1] % 2][b + loops]
        r = registers[15]
        registers[15] = (r & 0x80) + ((r + acc.loop_r_inc * loops + 1) % 0x80)
        registers[25] += acc.loop_time * loops + 4
        registers[24] = pcn % 65536

    def inc_b_none(self, registers, memory, acc):
        # Speed up the tape-sampling loop with a loader-specific accelerator
        b = registers[2]
        loops = 0
        pcn = registers[24] + 1
        if self.state[4] and registers[26] == 0 and all(x == y or y is None for x, y in zip(memory[pcn - acc.c0:pcn + acc.c1], acc.code)):
            if registers[3] & acc.ear_mask == ((self.state[1] - acc.polarity) % 2) * acc.ear_mask:
                delta = self.state[0] - registers[25] - acc.in_time
                if delta > 0:
                    loops = min(delta // acc.loop_time + 1, 255 - b)
                    if loops:
                        # The carry flag is cleared on each loop iteration
                        registers[1] &= 0xFE
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
        if self.state[4] and registers[26] == 0:
            loops = 0
            for i, acc in enumerate(accelerators):
                if all(x == y or y is None for x, y in zip(memory[pcn - acc.c0:pcn + acc.c1], acc.code)):
                    if registers[3] & acc.ear_mask == ((self.state[1] - acc.polarity) % 2) * acc.ear_mask:
                        delta = self.state[0] - registers[25] - acc.in_time
                        if delta > 0:
                            loops = min(delta // acc.loop_time + 1, 255 - b)
                            if loops:
                                # The carry flag is cleared on each loop iteration
                                registers[1] &= 0xFE
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

    def list_accelerators(self, registers, memory, accelerators, auto_method, opcode):
        # Speed up the tape-sampling loop with an automatically selected
        # loader-specific accelerator, and also count hits and misses
        pcn = registers[24] + 1
        if self.state[4] and registers[26] == 0:
            for i, acc in enumerate(accelerators):
                if all(x == y or y is None for x, y in zip(memory[pcn - acc.c0:pcn + acc.c1], acc.code)):
                    self.acc_usage[acc.name] += 1
                    if i:
                        # Move the selected accelerator to the beginning of the
                        # list so that it can be found quicker by auto_method()
                        accelerators.remove(acc)
                        accelerators.insert(0, acc)
                    auto_method(registers, memory, accelerators)
                    return
        if opcode == 0x04:
            self.inc_b_misses += 1
        else:
            self.dec_b_misses += 1
        auto_method(registers, memory, ())

    def _read_port(self, state, registers, port):
        if port % 256 == 0xFE:
            pc = registers[24]
            if pc >= self.in_min_addr or (0x0562 <= pc <= 0x05F1 and self.out7ffd & 0x10):
                state[7] = 1 # Signal: custom loader detected
                index = state[1]
                if self.announce_data and not state[2]:
                    self.announce_data = False
                    state[4] = 1 # Signal: tape is running
                    registers[T] = self.edges[index]
                    length = len(self.blocks[self.block_index].data)
                    if length:
                        write_line(f'Data ({length} bytes)')
                elif index == self.max_index:
                    # Final edge, so stop the tape
                    self.stop_tape(registers[T])
                if index % 2 == 0:
                    return 191
        elif port == 0xFFFD: # pragma: no cover
            ay_reg = self.outfffd % 16
            if ay_reg == 14 and registers[24] == 0x08B2:
                # Avoid an infinite loop at 0x08AF in the 128K ROM:
                #   $08AF CALL $05D6  ; Check for BREAK.
                #   $08B2 IN A,(C)    ; Read AY register 14 (BC=$FFFD).
                #   $08B4 AND $40     ; Ready to send data?
                #   $08B6 JR NZ,$08AF ; Jump back if not (bit 6 set).
                return 0
            return self.ay[ay_reg]
        return 255

    def next_block(self, tstates):
        self.block_index += 1
        if self.block_index >= len(self.blocks):
            self.stop_tape(tstates) # pragma: no cover
        else:
            self.state[1] = self.state[3] + 1
            self.state[0] = self.edges[self.state[1]]
            self.block_data_index = self.blocks[self.block_index].start
            self.state[3] = self.blocks[self.block_index].end
            self.state[4] = int(not self.pause) # Pause tape unless configured not to
            self.announce_data = True

    def stop_tape(self, tstates):
        self.block_index = len(self.blocks)
        self.state[2] += 1 # Signal: end of tape reached
        if self.state[2] == 1:
            write_line('Tape finished')
            self.state[8] = tstates # Set tape end time
        self.state[4] = 0 # Signal: tape is not running

    def fast_load(self, simulator):
        registers = simulator.registers
        while self.block_data_index <= self.state[1] < self.max_index:
            self.next_block(registers[T])
        if self.block_index < len(self.blocks):
            data_block = self.blocks[self.block_index]
        else:
            raise SkoolKitError("Failed to fast load block: unexpected end of tape")
        if not data_block.fast_load:
            return False # pragma: no cover

        memory = simulator.memory
        ix = registers[IXl] + 256 * registers[IXh] # Start address
        de = registers[E] + 256 * registers[D] # Block length
        a = registers[A]
        block = data_block.data
        data_len = len(block) - 2

        # Exchange AF register pairs (as done at 0x0557), disable interrupts
        # (as done at 0x0559), and preload the machine stack with 0x053F (as
        # done at 0x055E)
        registers[0:2], registers[16:18] = registers[16:18], registers[0:2]
        registers[IFF] = 0
        registers[H], registers[L] = 0x05, 0x3F # SA-LD-RET
        sp = (registers[SP] - 2) % 65536
        registers[SP] = sp
        if sp > 0x3FFF:
            memory[sp] = registers[L]
        sp = (sp + 1) % 65536
        if sp > 0x3FFF:
            memory[sp] = registers[H]
        registers[R] = R1[registers[R]]
        registers[T] += 11

        if a == block[0]:
            skipped = ''
        else:
            skipped = ' [skipped]'
        if block[0] == 0 and data_len >= 17 and block[1] <= 3:
            name = self.text.get_text(block[2:12])
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
            registers[F] = 0x00 # Reset ZF, reset CF: flag byte mismatch
            registers[H] = 0
        else:
            addr = ix
            if de <= data_len:
                length = de
                ix += de
                de = 0
                check_parity = True
            else:
                length = data_len + 1
                ix += data_len + 1
                de -= data_len + 1
                check_parity = False
                registers[F] = 0x40 # Set ZF, reset CF: edge detection failed
            i = 1
            parity = block[0]
            while length:
                if addr > 0x3FFF:
                    memory[addr] = block[i]
                parity ^= block[i]
                addr = (addr + 1) % 65536
                i += 1
                length -= 1
            if check_parity:
                a = parity ^ block[i]
                registers[A] = a
                registers[F] = (a == 1) * 0x40 + (a == 0)
            registers[IXh] = (ix >> 8) & 0xFF
            registers[IXl] = ix & 0xFF
            registers[D] = (de >> 8) & 0xFF
            registers[E] = de & 0xFF

        registers[PC] = 0x05E2
        self.announce_data = False
        return True
