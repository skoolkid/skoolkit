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

import array

from skoolkit import ROM48, read_bin_file
from skoolkit.pagingtracer import Memory

FRAME_DURATIONS = (69888, 70908)

INT_ACTIVE = (32, 36)

A = 0
F = 1
B = 2
C = 3
D = 4
E = 5
H = 6
L = 7
IXh = 8
IXl = 9
IYh = 10
IYl = 11
SP = 12
SP2 = 13
I = 14
R = 15
xA = 16
xF = 17
xB = 18
xC = 19
xD = 20
xE = 21
xH = 22
xL = 23
PC = 24
T = 25
IFF = 26
IM = 27
HALT = 28

REGISTERS = {
    'A': A,
    'F': F,
    'B': B,
    'C': C,
    'D': D,
    'E': E,
    'H': H,
    'L': L,
    'IXh': IXh,
    'IXl': IXl,
    'IYh': IYh,
    'IYl': IYl,
    'SP': SP,
    'I': I,
    'R': R,
    '^A': xA,
    '^F': xF,
    '^B': xB,
    '^C': xC,
    '^D': xD,
    '^E': xE,
    '^H': xH,
    '^L': xL,
    'PC': PC,
    'T': T
}

def from_snapshot(cls, snapshot, registers=None, state=None, config=None, rom_file=None):
    ram = snapshot.ram(-1)
    if len(ram) == 0x20000:
        banks = [ram[a:a + 0x4000] for a in range(0, 0x20000, 0x4000)]
        s_memory = Memory(banks, snapshot.out7ffd, snapshot.machine)
    else:
        s_memory = [0] * 16384 + ram
        rom = read_bin_file(rom_file or ROM48)
        s_memory[:len(rom)] = rom
    s_registers = {
        'A': snapshot.a,
        'F': snapshot.f,
        'BC': snapshot.bc,
        'DE': snapshot.de,
        'HL': snapshot.hl,
        'IX': snapshot.ix,
        'IY': snapshot.iy,
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
    if registers:
        s_registers.update(registers)
    s_state = {
        'im': snapshot.im,
        'iff': snapshot.iff1,
        'tstates': snapshot.tstates
    }
    if state:
        s_state.update(state)
    s_config = {
        'frame_duration': FRAME_DURATIONS[len(ram) == 0x20000],
        'int_active': INT_ACTIVE[len(ram) == 0x20000]
    }
    if config:
        s_config.update(config)
    return cls(s_memory, s_registers, s_state, s_config)

def get_state(simulator, tstates=True):
    registers = [
        f'A={simulator.registers[A]}',
        f'F={simulator.registers[F]}',
        f'BC={simulator.registers[C] + 256 * simulator.registers[B]}',
        f'DE={simulator.registers[E] + 256 * simulator.registers[D]}',
        f'HL={simulator.registers[L] + 256 * simulator.registers[H]}',
        f'IX={simulator.registers[IXl] + 256 * simulator.registers[IXh]}',
        f'IY={simulator.registers[IYl] + 256 * simulator.registers[IYh]}',
        f'SP={simulator.registers[SP]}',
        f'I={simulator.registers[I]}',
        f'R={simulator.registers[R]}',
        f'^A={simulator.registers[xA]}',
        f'^F={simulator.registers[xF]}',
        f'^BC={simulator.registers[xC] + 256 * simulator.registers[xB]}',
        f'^DE={simulator.registers[xE] + 256 * simulator.registers[xD]}',
        f'^HL={simulator.registers[xL] + 256 * simulator.registers[xH]}',
        f'PC={simulator.registers[PC]}'
    ]
    state = [
        f'border={simulator.tracer.border}',
        f'fe={simulator.tracer.outfe}',
        f'iff={simulator.registers[IFF]}',
        f'im={simulator.registers[IM]}'
    ]
    if tstates:
        state.append(f'tstates={simulator.registers[T]}')
    if isinstance(simulator.memory, Memory):
        ram = simulator.memory.banks
        state.extend(f'ay[{n}]={v}' for n, v in enumerate(simulator.tracer.ay))
        state.extend((f'7ffd={simulator.memory.o7ffd}', f'fffd={simulator.tracer.outfffd}'))
        machine = simulator.memory.machine
    else:
        ram = simulator.memory[0x4000:]
        machine = '48K'
    return ram, registers, state, machine

def get_registers(config, state, as_array=True):
    registers = [0] * 29
    if as_array: # pragma: no cover
        registers = array.array('Q', registers)
    registers[IYh] = 92
    registers[IYl] = 58
    registers[SP] = 23552
    registers[I] = 63
    if config:
        for reg, value in config.items():
            if reg in REGISTERS:
                registers[REGISTERS[reg]] = value
            elif reg in ('IX', 'IY'):
                rh = REGISTERS[reg + 'h']
                registers[rh] = value // 256
                registers[rh + 1] = value % 256
            elif reg.startswith('^'):
                rh = REGISTERS[reg[:2]]
                registers[rh] = value // 256
                registers[rh + 1] = value % 256
            elif len(reg) == 2:
                rh = REGISTERS[reg[0]]
                registers[rh] = value // 256
                registers[rh + 1] = value % 256
    if state is None:
        state = {}
    registers[IM] = state.get('im', 1)
    registers[IFF] = state.get('iff', 0)
    registers[HALT] = state.get('halted', 0)
    registers[T] = state.get('tstates', 0)
    return registers
