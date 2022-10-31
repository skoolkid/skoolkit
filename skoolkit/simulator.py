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

PARITY = (
    4, 0, 0, 4, 0, 4, 4, 0, 0, 4, 4, 0, 4, 0, 0, 4,
    0, 4, 4, 0, 4, 0, 0, 4, 4, 0, 0, 4, 0, 4, 4, 0,
    0, 4, 4, 0, 4, 0, 0, 4, 4, 0, 0, 4, 0, 4, 4, 0,
    4, 0, 0, 4, 0, 4, 4, 0, 0, 4, 4, 0, 4, 0, 0, 4,
    0, 4, 4, 0, 4, 0, 0, 4, 4, 0, 0, 4, 0, 4, 4, 0,
    4, 0, 0, 4, 0, 4, 4, 0, 0, 4, 4, 0, 4, 0, 0, 4,
    4, 0, 0, 4, 0, 4, 4, 0, 0, 4, 4, 0, 4, 0, 0, 4,
    0, 4, 4, 0, 4, 0, 0, 4, 4, 0, 0, 4, 0, 4, 4, 0,
    0, 4, 4, 0, 4, 0, 0, 4, 4, 0, 0, 4, 0, 4, 4, 0,
    4, 0, 0, 4, 0, 4, 4, 0, 0, 4, 4, 0, 4, 0, 0, 4,
    4, 0, 0, 4, 0, 4, 4, 0, 0, 4, 4, 0, 4, 0, 0, 4,
    0, 4, 4, 0, 4, 0, 0, 4, 4, 0, 0, 4, 0, 4, 4, 0,
    4, 0, 0, 4, 0, 4, 4, 0, 0, 4, 4, 0, 4, 0, 0, 4,
    0, 4, 4, 0, 4, 0, 0, 4, 4, 0, 0, 4, 0, 4, 4, 0,
    0, 4, 4, 0, 4, 0, 0, 4, 4, 0, 0, 4, 0, 4, 4, 0,
    4, 0, 0, 4, 0, 4, 4, 0, 0, 4, 4, 0, 4, 0, 0, 4
)

SZ53P = (
    0x44, 0x00, 0x00, 0x04, 0x00, 0x04, 0x04, 0x00, 0x08, 0x0C, 0x0C, 0x08, 0x0C, 0x08, 0x08, 0x0C,
    0x00, 0x04, 0x04, 0x00, 0x04, 0x00, 0x00, 0x04, 0x0C, 0x08, 0x08, 0x0C, 0x08, 0x0C, 0x0C, 0x08,
    0x20, 0x24, 0x24, 0x20, 0x24, 0x20, 0x20, 0x24, 0x2C, 0x28, 0x28, 0x2C, 0x28, 0x2C, 0x2C, 0x28,
    0x24, 0x20, 0x20, 0x24, 0x20, 0x24, 0x24, 0x20, 0x28, 0x2C, 0x2C, 0x28, 0x2C, 0x28, 0x28, 0x2C,
    0x00, 0x04, 0x04, 0x00, 0x04, 0x00, 0x00, 0x04, 0x0C, 0x08, 0x08, 0x0C, 0x08, 0x0C, 0x0C, 0x08,
    0x04, 0x00, 0x00, 0x04, 0x00, 0x04, 0x04, 0x00, 0x08, 0x0C, 0x0C, 0x08, 0x0C, 0x08, 0x08, 0x0C,
    0x24, 0x20, 0x20, 0x24, 0x20, 0x24, 0x24, 0x20, 0x28, 0x2C, 0x2C, 0x28, 0x2C, 0x28, 0x28, 0x2C,
    0x20, 0x24, 0x24, 0x20, 0x24, 0x20, 0x20, 0x24, 0x2C, 0x28, 0x28, 0x2C, 0x28, 0x2C, 0x2C, 0x28,
    0x80, 0x84, 0x84, 0x80, 0x84, 0x80, 0x80, 0x84, 0x8C, 0x88, 0x88, 0x8C, 0x88, 0x8C, 0x8C, 0x88,
    0x84, 0x80, 0x80, 0x84, 0x80, 0x84, 0x84, 0x80, 0x88, 0x8C, 0x8C, 0x88, 0x8C, 0x88, 0x88, 0x8C,
    0xA4, 0xA0, 0xA0, 0xA4, 0xA0, 0xA4, 0xA4, 0xA0, 0xA8, 0xAC, 0xAC, 0xA8, 0xAC, 0xA8, 0xA8, 0xAC,
    0xA0, 0xA4, 0xA4, 0xA0, 0xA4, 0xA0, 0xA0, 0xA4, 0xAC, 0xA8, 0xA8, 0xAC, 0xA8, 0xAC, 0xAC, 0xA8,
    0x84, 0x80, 0x80, 0x84, 0x80, 0x84, 0x84, 0x80, 0x88, 0x8C, 0x8C, 0x88, 0x8C, 0x88, 0x88, 0x8C,
    0x80, 0x84, 0x84, 0x80, 0x84, 0x80, 0x80, 0x84, 0x8C, 0x88, 0x88, 0x8C, 0x88, 0x8C, 0x8C, 0x88,
    0xA0, 0xA4, 0xA4, 0xA0, 0xA4, 0xA0, 0xA0, 0xA4, 0xAC, 0xA8, 0xA8, 0xAC, 0xA8, 0xAC, 0xAC, 0xA8,
    0xA4, 0xA0, 0xA0, 0xA4, 0xA0, 0xA4, 0xA4, 0xA0, 0xA8, 0xAC, 0xAC, 0xA8, 0xAC, 0xA8, 0xA8, 0xAC
)

AND_R = tuple(f + 0x10 for f in SZ53P)

DEC_R = (
    0x42, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x0A, 0x0A, 0x0A, 0x0A, 0x0A, 0x0A, 0x0A, 0x1A,
    0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x0A, 0x0A, 0x0A, 0x0A, 0x0A, 0x0A, 0x0A, 0x1A,
    0x22, 0x22, 0x22, 0x22, 0x22, 0x22, 0x22, 0x22, 0x2A, 0x2A, 0x2A, 0x2A, 0x2A, 0x2A, 0x2A, 0x3A,
    0x22, 0x22, 0x22, 0x22, 0x22, 0x22, 0x22, 0x22, 0x2A, 0x2A, 0x2A, 0x2A, 0x2A, 0x2A, 0x2A, 0x3A,
    0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x0A, 0x0A, 0x0A, 0x0A, 0x0A, 0x0A, 0x0A, 0x1A,
    0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x0A, 0x0A, 0x0A, 0x0A, 0x0A, 0x0A, 0x0A, 0x1A,
    0x22, 0x22, 0x22, 0x22, 0x22, 0x22, 0x22, 0x22, 0x2A, 0x2A, 0x2A, 0x2A, 0x2A, 0x2A, 0x2A, 0x3A,
    0x22, 0x22, 0x22, 0x22, 0x22, 0x22, 0x22, 0x22, 0x2A, 0x2A, 0x2A, 0x2A, 0x2A, 0x2A, 0x2A, 0x3E,
    0x82, 0x82, 0x82, 0x82, 0x82, 0x82, 0x82, 0x82, 0x8A, 0x8A, 0x8A, 0x8A, 0x8A, 0x8A, 0x8A, 0x9A,
    0x82, 0x82, 0x82, 0x82, 0x82, 0x82, 0x82, 0x82, 0x8A, 0x8A, 0x8A, 0x8A, 0x8A, 0x8A, 0x8A, 0x9A,
    0xA2, 0xA2, 0xA2, 0xA2, 0xA2, 0xA2, 0xA2, 0xA2, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xBA,
    0xA2, 0xA2, 0xA2, 0xA2, 0xA2, 0xA2, 0xA2, 0xA2, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xBA,
    0x82, 0x82, 0x82, 0x82, 0x82, 0x82, 0x82, 0x82, 0x8A, 0x8A, 0x8A, 0x8A, 0x8A, 0x8A, 0x8A, 0x9A,
    0x82, 0x82, 0x82, 0x82, 0x82, 0x82, 0x82, 0x82, 0x8A, 0x8A, 0x8A, 0x8A, 0x8A, 0x8A, 0x8A, 0x9A,
    0xA2, 0xA2, 0xA2, 0xA2, 0xA2, 0xA2, 0xA2, 0xA2, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xBA,
    0xA2, 0xA2, 0xA2, 0xA2, 0xA2, 0xA2, 0xA2, 0xA2, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xBA
)

INC_R = (
    0x50, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08,
    0x10, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08,
    0x30, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x28, 0x28, 0x28, 0x28, 0x28, 0x28, 0x28, 0x28,
    0x30, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x28, 0x28, 0x28, 0x28, 0x28, 0x28, 0x28, 0x28,
    0x10, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08,
    0x10, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08,
    0x30, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x28, 0x28, 0x28, 0x28, 0x28, 0x28, 0x28, 0x28,
    0x30, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x28, 0x28, 0x28, 0x28, 0x28, 0x28, 0x28, 0x28,
    0x94, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x88, 0x88, 0x88, 0x88, 0x88, 0x88, 0x88, 0x88,
    0x90, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x88, 0x88, 0x88, 0x88, 0x88, 0x88, 0x88, 0x88,
    0xB0, 0xA0, 0xA0, 0xA0, 0xA0, 0xA0, 0xA0, 0xA0, 0xA8, 0xA8, 0xA8, 0xA8, 0xA8, 0xA8, 0xA8, 0xA8,
    0xB0, 0xA0, 0xA0, 0xA0, 0xA0, 0xA0, 0xA0, 0xA0, 0xA8, 0xA8, 0xA8, 0xA8, 0xA8, 0xA8, 0xA8, 0xA8,
    0x90, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x88, 0x88, 0x88, 0x88, 0x88, 0x88, 0x88, 0x88,
    0x90, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x88, 0x88, 0x88, 0x88, 0x88, 0x88, 0x88, 0x88,
    0xB0, 0xA0, 0xA0, 0xA0, 0xA0, 0xA0, 0xA0, 0xA0, 0xA8, 0xA8, 0xA8, 0xA8, 0xA8, 0xA8, 0xA8, 0xA8,
    0xB0, 0xA0, 0xA0, 0xA0, 0xA0, 0xA0, 0xA0, 0xA0, 0xA8, 0xA8, 0xA8, 0xA8, 0xA8, 0xA8, 0xA8, 0xA8
)

NEG = (
    0x42, 0xBB, 0xBB, 0xBB, 0xBB, 0xBB, 0xBB, 0xBB, 0xBB, 0xB3, 0xB3, 0xB3, 0xB3, 0xB3, 0xB3, 0xB3,
    0xA3, 0xBB, 0xBB, 0xBB, 0xBB, 0xBB, 0xBB, 0xBB, 0xBB, 0xB3, 0xB3, 0xB3, 0xB3, 0xB3, 0xB3, 0xB3,
    0xA3, 0x9B, 0x9B, 0x9B, 0x9B, 0x9B, 0x9B, 0x9B, 0x9B, 0x93, 0x93, 0x93, 0x93, 0x93, 0x93, 0x93,
    0x83, 0x9B, 0x9B, 0x9B, 0x9B, 0x9B, 0x9B, 0x9B, 0x9B, 0x93, 0x93, 0x93, 0x93, 0x93, 0x93, 0x93,
    0x83, 0xBB, 0xBB, 0xBB, 0xBB, 0xBB, 0xBB, 0xBB, 0xBB, 0xB3, 0xB3, 0xB3, 0xB3, 0xB3, 0xB3, 0xB3,
    0xA3, 0xBB, 0xBB, 0xBB, 0xBB, 0xBB, 0xBB, 0xBB, 0xBB, 0xB3, 0xB3, 0xB3, 0xB3, 0xB3, 0xB3, 0xB3,
    0xA3, 0x9B, 0x9B, 0x9B, 0x9B, 0x9B, 0x9B, 0x9B, 0x9B, 0x93, 0x93, 0x93, 0x93, 0x93, 0x93, 0x93,
    0x83, 0x9B, 0x9B, 0x9B, 0x9B, 0x9B, 0x9B, 0x9B, 0x9B, 0x93, 0x93, 0x93, 0x93, 0x93, 0x93, 0x93,
    0x87, 0x3B, 0x3B, 0x3B, 0x3B, 0x3B, 0x3B, 0x3B, 0x3B, 0x33, 0x33, 0x33, 0x33, 0x33, 0x33, 0x33,
    0x23, 0x3B, 0x3B, 0x3B, 0x3B, 0x3B, 0x3B, 0x3B, 0x3B, 0x33, 0x33, 0x33, 0x33, 0x33, 0x33, 0x33,
    0x23, 0x1B, 0x1B, 0x1B, 0x1B, 0x1B, 0x1B, 0x1B, 0x1B, 0x13, 0x13, 0x13, 0x13, 0x13, 0x13, 0x13,
    0x03, 0x1B, 0x1B, 0x1B, 0x1B, 0x1B, 0x1B, 0x1B, 0x1B, 0x13, 0x13, 0x13, 0x13, 0x13, 0x13, 0x13,
    0x03, 0x3B, 0x3B, 0x3B, 0x3B, 0x3B, 0x3B, 0x3B, 0x3B, 0x33, 0x33, 0x33, 0x33, 0x33, 0x33, 0x33,
    0x23, 0x3B, 0x3B, 0x3B, 0x3B, 0x3B, 0x3B, 0x3B, 0x3B, 0x33, 0x33, 0x33, 0x33, 0x33, 0x33, 0x33,
    0x23, 0x1B, 0x1B, 0x1B, 0x1B, 0x1B, 0x1B, 0x1B, 0x1B, 0x13, 0x13, 0x13, 0x13, 0x13, 0x13, 0x13,
    0x03, 0x1B, 0x1B, 0x1B, 0x1B, 0x1B, 0x1B, 0x1B, 0x1B, 0x13, 0x13, 0x13, 0x13, 0x13, 0x13, 0x13
)

R_INC1 = tuple((r & 0x80) + ((r + 1) % 128) for r in range(256))

R_INC2 = tuple((r & 0x80) + ((r + 2) % 128) for r in range(256))

JR_OFFSETS = tuple(j + 2 if j < 128 else j - 254 for j in range(256))

RR = (
    tuple(r // 2 for r in range(256)),
    tuple(128 + r // 2 for r in range(256))
)

RL = (
    tuple((r * 2) % 256 for r in range(256)),
    tuple((r * 2) % 256 + 1 for r in range(256))
)

RRC = tuple(((r * 128) % 256) + r // 2 for r in range(256))

RLC = tuple(r // 128 + ((r * 2) % 256) for r in range(256))

SLA = tuple((r * 2) % 256 for r in range(256))

SRA = tuple((r & 0x80) + r // 2 for r in range(256))

SLL = tuple((r * 2) % 256 + 1 for r in range(256))

SRL = tuple(r // 2 for r in range(256))

FRAME_DURATION = 69888

CONFIG = {
    'fast_djnz': False,
    'fast_ldir': False,
}

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
Bd = 26
Dd = 28
Hd = 30
Xd = 32
Yd = 33
N = 34

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

class Simulator:
    def __init__(self, memory, registers=None, state=None, config=None):
        self.memory = memory
        self.registers = [
            0,     # A
            0,     # F
            0,     # B
            0,     # C
            0,     # D
            0,     # E
            0,     # H
            0,     # L
            0,     # IXh
            0,     # IXl
            92,    # IYh
            58,    # IYl
            23552, # SP
            0,     # Unused
            63,    # I
            0,     # R
            0,     # xA
            0,     # xF
            0,     # xB
            0,     # xC
            0,     # xD
            0,     # xE
            0,     # xH
            0,     # xL
            0,     # PC
            0      # T (T-states)
        ]
        if registers:
            self.set_registers(registers)
        if state is None:
            state = {}
        self.ppcount = state.get('ppcount', 0)
        self.imode = state.get('im', 1)
        self.iff2 = state.get('iff', 0)
        self.registers[25] = state.get('tstates', 0)
        cfg = CONFIG.copy()
        if config:
            cfg.update(config)
        self.create_opcodes()
        if cfg['fast_djnz']:
            self.opcodes[0x10] = partial(self.djnz_fast, self.registers, self.memory)
        if cfg['fast_ldir']:
            self.after_ED[0xB0] = partial(self.ldir_fast, self.registers, self.memory, 1)
            self.after_ED[0xB8] = partial(self.ldir_fast, self.registers, self.memory, -1)
        self.itracer = None
        self.in_tracer = None
        self.out_tracer = None
        self.peek_tracer = None
        self.poke_tracer = None

    def set_tracer(self, tracer):
        if hasattr(tracer, 'trace'):
            self.itracer = partial(tracer.trace, self)
        else:
            self.itracer = None
        if hasattr(tracer, 'read_port'):
            self.in_tracer = partial(tracer.read_port, self)
        else:
            self.in_tracer = None
        if hasattr(tracer, 'write_port'):
            self.out_tracer = partial(tracer.write_port, self)
        else:
            self.out_tracer = None
        if hasattr(tracer, 'read_memory'):
            self.peek_tracer = partial(tracer.read_memory, self)
        else:
            self.peek_tracer = None
        if hasattr(tracer, 'write_memory'):
            self.poke_tracer = partial(tracer.write_memory, self)
        else:
            self.poke_tracer = None

    def run(self, start=None, stop=None):
        opcodes = self.opcodes
        after_CB = self.after_CB
        after_DD = self.after_DD
        after_DDCB = self.after_DDCB
        after_ED = self.after_ED
        after_FD = self.after_FD
        after_FDCB = self.after_FDCB
        memory = self.memory
        registers = self.registers
        itracer = self.itracer
        if start is None:
            pc = registers[24]
        else:
            registers[24] = start
            pc = start
        running = True
        while running:
            opcode = memory[pc]
            method = opcodes[opcode]
            if method:
                r_inc = R_INC1
                method()
            elif opcode == 0xCB:
                r_inc = R_INC2
                after_CB[memory[(pc + 1) % 65536]]()
            elif opcode == 0xED:
                r_inc = R_INC2
                after_ED[memory[(pc + 1) % 65536]]()
            elif opcode == 0xDD:
                r_inc = R_INC2
                method = after_DD[memory[(pc + 1) % 65536]]
                if method:
                    method()
                else:
                    after_DDCB[memory[(pc + 3) % 65536]]()
            else:
                r_inc = R_INC2
                method = after_FD[memory[(pc + 1) % 65536]]
                if method:
                    method()
                else:
                    after_FDCB[memory[(pc + 3) % 65536]]()
            registers[15] = r_inc[registers[15]]
            if itracer:
                running = registers[24] != stop
                if itracer(pc):
                    running = False
            elif stop is None:
                running = False
            else:
                running = registers[24] != stop
            pc = registers[24]

    def set_registers(self, registers):
        for reg, value in registers.items():
            if reg in REGISTERS:
                self.registers[REGISTERS[reg]] = value
            elif reg in ('IX', 'IY'):
                rh = REGISTERS[reg + 'h']
                self.registers[rh] = value // 256
                self.registers[rh + 1] = value % 256
            elif reg.startswith('^'):
                rh = REGISTERS[reg[:2]]
                self.registers[rh] = value // 256
                self.registers[rh + 1] = value % 256
            elif len(reg) == 2:
                rh = REGISTERS[reg[0]]
                self.registers[rh] = value // 256
                self.registers[rh + 1] = value % 256

    def index(self, registers, memory, reg):
        offset = memory[(registers[24] + 2) % 65536]
        if offset >= 128:
            offset -= 256
        if reg == 32:
            return (registers[9] + 256 * registers[8] + offset) % 65536
        return (registers[11] + 256 * registers[10] + offset) % 65536

    def get_operand_value(self, registers, memory, size, reg):
        if reg < 16:
            return registers[reg]
        if reg < 32:
            return self.peek(memory, registers[reg - 23] + 256 * registers[reg - 24])
        if reg == 34:
            return memory[(registers[24] + size - 1) % 65536]
        return self.peek(memory, self.index(registers, memory, reg))

    def set_operand_value(self, registers, memory, reg, value):
        if reg < 16:
            registers[reg] = value
        elif reg < 32:
            self.poke(memory, registers[reg - 23] + 256 * registers[reg - 24], value)
        else:
            self.poke(memory, self.index(registers, memory, reg), value)

    def peek(self, memory, address, count=1):
        if self.peek_tracer:
            self.peek_tracer(address, count)
        if count == 1:
            return memory[address]
        return memory[address], memory[(address + 1) % 65536]

    def poke(self, memory, address, *values):
        if self.poke_tracer:
            self.poke_tracer(address, values)
        if address > 0x3FFF:
            memory[address] = values[0]
        if len(values) > 1:
            address = (address + 1) % 65536
            if address > 0x3FFF:
                memory[address] = values[1]

    def adc_a(self, registers, memory, timing, size, reg):
        value = self.get_operand_value(registers, memory, size, reg)
        old_a = registers[0]
        addend = value + (registers[1] % 2)
        a = old_a + addend
        if a < 0 or a > 255:
            a %= 256
            f = (a & 0xA8) + 0x01 # S.5.3..C
        else:
            f = a & 0xA8          # S.5.3..C
        if a == 0:
            f += 0x40 # .Z......
        if (reg == 0 and old_a % 16 == 0x0F) or ((old_a % 16) + (addend % 16)) & 0x10:
            f += 0x10 # ...H....
        if (old_a ^ value) & 0x80 == 0 and (a ^ old_a) & 0x80:
            # Augend and addend signs are the same - overflow if their sign
            # differs from the sign of the result
            registers[1] = f + 0x04
        else:
            registers[1] = f
        registers[0] = a

        registers[25] += timing
        registers[24] = (registers[24] + size) % 65536

    def adc_hl(self, registers, reg):
        if reg == 12:
            rr = registers[12]
        else:
            rr = registers[reg + 1] + 256 * registers[reg]
        hl = registers[7] + 256 * registers[6]
        rr_c = rr + registers[1] % 2
        result = hl + rr_c

        if result < 0 or result > 0xFFFF:
            result %= 65536
            f = 0x01 # .......C
        else:
            f = 0
        if ((hl % 4096) + (rr_c % 4096)) & 0x1000:
            f += 0x10 # ...H....
        if result & 0x8000:
            f += 0x80 # S.......
        elif result == 0:
            f += 0x40 # .Z......
        if (hl ^ rr) & 0x8000 == 0 and (result ^ hl) & 0x8000:
            # Augend and addend signs are the same - overflow if their sign
            # differs from the sign of the result
            f += 0x04 # .....P..

        h = result // 256
        registers[1] = f + (h & 0x28)
        registers[7] = result % 256
        registers[6] = h

        registers[25] += 15
        registers[24] = (registers[24] + 2) % 65536

    def add_a(self, registers, memory, timing, size, reg):
        addend = self.get_operand_value(registers, memory, size, reg)
        old_a = registers[0]
        a = old_a + addend
        if a < 0 or a > 255:
            a %= 256
            f = (a & 0xA8) + 0x01 # S.5.3..C
        else:
            f = a & 0xA8          # S.5.3..C
        if a == 0:
            f += 0x40 # .Z......
        if ((old_a % 16) + (addend % 16)) & 0x10:
            f += 0x10 # ...H....
        if (old_a ^ addend) & 0x80 == 0 and (a ^ old_a) & 0x80:
            # Augend and addend signs are the same - overflow if their sign
            # differs from the sign of the result
            registers[1] = f + 0x04
        else:
            registers[1] = f
        registers[0] = a

        registers[25] += timing
        registers[24] = (registers[24] + size) % 65536

    def add16(self, registers, timing, size, augend, reg):
        if reg == 12:
            addend_v = registers[12]
        else:
            addend_v = registers[reg + 1] + 256 * registers[reg]
        augend_v = registers[augend + 1] + 256 * registers[augend]
        result = augend_v + addend_v

        if result < 0 or result > 0xFFFF:
            result %= 65536
            f = (registers[1] & 0xC4) + 0x01 # SZ...P.C
        else:
            f = registers[1] & 0xC4 # SZ...P..
        if ((augend_v % 4096) + (addend_v % 4096)) & 0x1000:
            f += 0x10 # ...H....

        result_hi = result // 256
        registers[1] = f + (result_hi & 0x28)
        registers[augend + 1] = result % 256
        registers[augend] = result_hi

        registers[25] += timing
        registers[24] = (registers[24] + size) % 65536

    def and_n(self, registers, memory):
        pcn = registers[24] + 1
        a = registers[0] & memory[pcn % 65536]
        registers[0] = a
        registers[1] = AND_R[a]
        registers[25] += 7
        registers[24] = (pcn + 1) % 65536

    def and_r(self, registers, r):
        a = registers[0] & registers[r]
        registers[0] = a
        registers[1] = AND_R[a]
        registers[25] += 4
        registers[24] = (registers[24] + 1) % 65536

    def anda(self, registers, memory, timing, size, reg):
        a = registers[0] & self.get_operand_value(registers, memory, size, reg)
        registers[0] = a
        registers[1] = AND_R[a]
        registers[25] += timing
        registers[24] = (registers[24] + size) % 65536

    def bit(self, registers, memory, timing, size, mask, reg):
        value = self.get_operand_value(registers, memory, size, reg)
        f = 0x10 + (registers[1] % 2) # ...H..NC
        if value & mask == 0:
            f += 0x44 # .Z...P..
        elif mask == 128:
            f += 0x80 # S.......
        if reg >= 32:
            offset = memory[(registers[24] + 2) % 65536]
            if reg == 32:
                value = (registers[9] + 256 * registers[8] + offset) // 256
            else:
                value = (registers[11] + 256 * registers[10] + offset) // 256
        registers[1] = f + (value & 0x28)
        registers[25] += timing
        registers[24] = (registers[24] + size) % 65536

    def call(self, registers, memory, c_and, c_val):
        if c_and and registers[1] & c_and == c_val:
            registers[25] += 10
            registers[24] = (registers[24] + 3) % 65536
        else:
            pc = registers[24]
            ret_addr = (pc + 3) % 65536
            self._push(registers, memory, ret_addr % 256, ret_addr // 256)
            registers[25] += 17
            registers[24] = memory[(pc + 1) % 65536] + 256 * memory[(pc + 2) % 65536]

    def cf(self, registers, flip):
        f = registers[1] & 0xC4 # SZ...PN.
        if flip and registers[1] % 2:
            registers[1] = f + (registers[0] & 0x28) + 0x10
        else:
            registers[1] = f + (registers[0] & 0x28) + 0x01
        registers[25] += 4
        registers[24] = (registers[24] + 1) % 65536

    def cp(self, registers, memory, timing, size, reg=N):
        value = self.get_operand_value(registers, memory, size, reg)
        a = registers[0]
        result = (a - value) % 256
        f = (result & 0x80) + (value & 0x28) + 0x02 # S.5.3.N.
        if result == 0:
            f += 0x40 # .Z......
        elif ((a % 16) - (value % 16)) & 0x10:
            f += 0x10 # ...H....
        if ((a ^ ~value) ^ 0x80) & 0x80 and (result ^ a) & 0x80:
            # Operand signs are the same - overflow if their sign differs from
            # the sign of the result
            f += 0x04 # .....P..
        if a < value:
            registers[1] = f + 0x01
        else:
            registers[1] = f
        registers[25] += timing
        registers[24] = (registers[24] + size) % 65536

    def cpi(self, registers, memory, inc, repeat):
        # CPI, CPD, CPIR, CPDR
        hl = registers[7] + 256 * registers[6]
        bc = registers[3] + 256 * registers[2]
        a = registers[0]

        value = self.peek(memory, hl)
        result = (a - value) % 256
        hf = ((a % 16) - (value % 16)) & 0x10
        n = a - value - hf // 16
        f = (result & 0x80) + hf + 0x02 + (registers[1] % 2) # S..H..NC
        if result == 0:
            f += 0x40 # .Z......
        if n & 0x02:
            f += 0x20 # ..5.....
        if n & 0x08:
            f += 0x08 # ....3...

        hl = (hl + inc) % 65536
        bc = (bc - 1) % 65536
        registers[7] = hl % 256
        registers[6] = hl // 256
        registers[3] = bc % 256
        registers[2] = bc // 256
        if bc:
            registers[1] = f + 0x04
        else:
            registers[1] = f

        if repeat and result and bc:
            registers[25] += 21
        else:
            registers[25] += 16
            registers[24] = (registers[24] + 2) % 65536

    def cpl(self, registers):
        a = registers[0] ^ 255
        registers[0] = a
        registers[1] = (registers[1] & 0xC5) + (a & 0x28) + 0x12
        registers[25] += 4
        registers[24] = (registers[24] + 1) % 65536

    def daa(self, registers):
        a = registers[0]
        old_f = registers[1]
        hf = old_f & 0x10
        nf = old_f & 0x02
        t = 0
        f = nf

        if hf or a % 16 > 0x09:
            t += 1
        if old_f % 2 or a > 0x99:
            t += 2
            f += 0x01 # .......C

        if (nf and hf and a % 16 < 6) or (nf == 0 and a % 16 >= 0x0A):
            f += 0x10 # ...H....

        if t == 1:
            if nf:
                a = (a + 0xFA) % 256
            else:
                a = (a + 0x06) % 256
        elif t == 2:
            if nf:
                a = (a + 0xA0) % 256
            else:
                a = (a + 0x60) % 256
        elif t == 3:
            if nf:
                a = (a + 0x9A) % 256
            else:
                a = (a + 0x66) % 256

        registers[0] = a
        registers[1] = f + SZ53P[a]

        registers[25] += 4
        registers[24] = (registers[24] + 1) % 65536

    def dec_r(self, registers, reg):
        value = (registers[reg] - 1) % 256
        registers[1] = (registers[1] % 2) + DEC_R[value]
        registers[reg] = value
        registers[25] += 4
        registers[24] = (registers[24] + 1) % 65536

    def di_ei(self, registers, iff2):
        self.iff2 = iff2
        registers[25] += 4
        registers[24] = (registers[24] + 1) % 65536

    def djnz(self, registers, memory):
        b = (registers[2] - 1) % 256
        registers[2] = b
        if b:
            registers[25] += 13
            pc = registers[24]
            registers[24] = (pc + JR_OFFSETS[memory[(pc + 1) % 65536]]) % 65536
        else:
            registers[25] += 8
            registers[24] = (registers[24] + 2) % 65536

    def djnz_fast(self, registers, memory):
        if memory[(registers[24] + 1) % 65536] == 0xFE:
            b = (registers[2] - 1) % 256
            registers[2] = 0
            r = registers[15]
            registers[15] = (r & 0x80) + ((r + b) % 128)
            registers[25] += b * 13 + 8
            registers[24] = (registers[24] + 2) % 65536
        else:
            self.djnz(registers, memory)

    def ex_af(self, registers):
        registers[0], registers[16] = registers[16], registers[0]
        registers[1], registers[17] = registers[17], registers[1]
        registers[25] += 4
        registers[24] = (registers[24] + 1) % 65536

    def ex_de_hl(self, registers):
        registers[4], registers[6] = registers[6], registers[4]
        registers[5], registers[7] = registers[7], registers[5]
        registers[25] += 4
        registers[24] = (registers[24] + 1) % 65536

    def ex_sp(self, registers, memory, reg):
        sp = registers[12]
        sp1, sp2 = self.peek(memory, sp, 2)
        self.poke(memory, sp, registers[reg + 1], registers[reg])
        registers[reg + 1] = sp1
        registers[reg] = sp2
        if reg == 6:
            registers[25] += 19
            registers[24] = (registers[24] + 1) % 65536
        else:
            registers[25] += 23
            registers[24] = (registers[24] + 2) % 65536

    def exx(self, registers):
        registers[2], registers[18] = registers[18], registers[2]
        registers[3], registers[19] = registers[19], registers[3]
        registers[4], registers[20] = registers[20], registers[4]
        registers[5], registers[21] = registers[21], registers[5]
        registers[6], registers[22] = registers[22], registers[6]
        registers[7], registers[23] = registers[23], registers[7]
        registers[25] += 4
        registers[24] = (registers[24] + 1) % 65536

    def halt(self, registers):
        if self.iff2:
            t = registers[25]
            if (t + 4) % FRAME_DURATION < t % FRAME_DURATION:
                registers[24] = (registers[24] + 1) % 65536
        registers[25] += 4

    def im(self, registers, mode):
        self.imode = mode
        registers[25] += 8
        registers[24] = (registers[24] + 2) % 65536

    def _in(self, port):
        if self.in_tracer:
            reading = self.in_tracer(port)
            if reading is None:
                return 191
            return reading
        return 191

    def in_a(self, registers, memory):
        pcn = registers[24] + 1
        registers[0] = self._in(memory[pcn % 65536] + 256 * registers[0])
        registers[25] += 11
        registers[24] = (pcn + 1) % 65536

    def in_c(self, registers, reg):
        value = self._in(registers[3] + 256 * registers[2])
        if reg != F:
            registers[reg] = value
        registers[1] = SZ53P[value] + (registers[1] % 2)
        registers[25] += 12
        registers[24] = (registers[24] + 2) % 65536

    def inc_r(self, registers, reg):
        value = (registers[reg] + 1) % 256
        registers[1] = (registers[1] % 2) + INC_R[value]
        registers[reg] = value
        registers[25] += 4
        registers[24] = (registers[24] + 1) % 65536

    def inc_dec8(self, registers, memory, timing, size, inc, reg):
        value = (self.get_operand_value(registers, memory, size, reg) + inc) % 256
        if inc < 0:
            registers[1] = (registers[1] % 2) + DEC_R[value]
        else:
            registers[1] = (registers[1] % 2) + INC_R[value]
        self.set_operand_value(registers, memory, reg, value)
        registers[25] += timing
        registers[24] = (registers[24] + size) % 65536

    def inc_dec16(self, registers, inc, reg):
        if reg == 12:
            registers[12] = (registers[12] + inc) % 65536
            registers[25] += 6
            registers[24] = (registers[24] + 1) % 65536
        else:
            value = (registers[reg + 1] + 256 * registers[reg] + inc) % 65536
            registers[reg] = value // 256
            registers[reg + 1] = value % 256
            if reg < 8:
                registers[25] += 6
                registers[24] = (registers[24] + 1) % 65536
            else:
                registers[25] += 10
                registers[24] = (registers[24] + 2) % 65536

    def ini(self, registers, memory, inc, repeat):
        # INI, IND, INIR, INDR
        hl = registers[7] + 256 * registers[6]
        b = registers[2]
        c = registers[3]
        a = registers[0]

        value = self._in(c + 256 * b)
        self.poke(memory, hl, value)
        b = (b - 1) % 256
        j = value + ((c + inc) % 256)
        f = (b & 0xA8) + PARITY[(j % 8) ^ b] # S.5.3P..
        if value & 0x80:
            f += 0x02  # ......N.
        if j > 255:
            f += 0x11 # ...H...C
        if b == 0:
            registers[1] = f + 0x40 # .Z......
        else:
            registers[1] = f

        hl = (hl + inc) % 65536
        registers[7] = hl % 256
        registers[6] = hl // 256
        registers[2] = b

        if repeat and b:
            registers[25] += 21
        else:
            registers[24] = (registers[24] + 2) % 65536
            registers[25] += 16

    def jp(self, registers, memory, c_and, c_val):
        if c_and:
            registers[25] += 10
            if registers[1] & c_and == c_val:
                registers[24] = (registers[24] + 3) % 65536
            else:
                registers[24] = memory[(registers[24] + 1) % 65536] + 256 * memory[(registers[24] + 2) % 65536]
        elif c_val == 0:
            registers[25] += 10
            registers[24] = memory[(registers[24] + 1) % 65536] + 256 * memory[(registers[24] + 2) % 65536]
        elif c_val == 6:
            registers[25] += 4
            registers[24] = registers[7] + 256 * registers[6]
        else:
            registers[25] += 8
            registers[24] = registers[c_val + 1] + 256 * registers[c_val]

    def jr(self, registers, memory, c_and, c_val):
        if registers[1] & c_and == c_val:
            registers[25] += 12
            pc = registers[24]
            registers[24] = (pc + JR_OFFSETS[memory[(pc + 1) % 65536]]) % 65536
        else:
            registers[25] += 7
            registers[24] = (registers[24] + 2) % 65536

    def ld_r_n(self, registers, memory, r):
        pcn = registers[24] + 1
        registers[r] = memory[pcn % 65536]
        registers[25] += 7
        registers[24] = (pcn + 1) % 65536

    def ld_r_r(self, registers, r1, r2):
        registers[r1] = registers[r2]
        registers[25] += 4
        registers[24] = (registers[24] + 1) % 65536

    def ld8(self, registers, memory, timing, size, reg, reg2=N):
        self.set_operand_value(registers, memory, reg, self.get_operand_value(registers, memory, size, reg2))
        if reg2 in (14, 15):
            # LD A,I and LD A,R
            a = registers[0]
            if a == 0:
                f = 0x40 + (registers[1] % 2) # .Z.....C
            else:
                f = (a & 0xA8) + (registers[1] % 2) # S.5H3.NC
            if self.iff2:
                registers[1] = f + 0x04
            else:
                registers[1] = f
        registers[25] += timing
        registers[24] = (registers[24] + size) % 65536

    def ld16(self, registers, memory, reg):
        pcn = registers[24] + 1
        if reg < 8:
            registers[reg + 1] = memory[pcn % 65536]
            registers[reg] = memory[(pcn + 1) % 65536]
            registers[25] += 10
            registers[24] = (pcn + 2) % 65536
        elif reg == 12:
            registers[12] = memory[pcn % 65536] + 256 * memory[(pcn + 1) % 65536]
            registers[25] += 10
            registers[24] = (pcn + 2) % 65536
        else:
            registers[reg + 1] = memory[(pcn + 1) % 65536]
            registers[reg] = memory[(pcn + 2) % 65536]
            registers[25] += 14
            registers[24] = (pcn + 3) % 65536

    def ld16addr(self, registers, memory, timing, size, reg, poke):
        end = registers[24] + size
        addr = memory[(end - 2) % 65536] + 256 * memory[(end - 1) % 65536]
        if poke:
            if reg == 12:
                self.poke(memory, addr, registers[12] % 256, registers[12] // 256)
            else:
                self.poke(memory, addr, registers[reg + 1], registers[reg])
        elif reg == 12:
            sp1, sp2 = self.peek(memory, addr, 2)
            registers[12] = sp1 + 256 * sp2
        else:
            registers[reg + 1], registers[reg] = self.peek(memory, addr, 2)
        registers[25] += timing
        registers[24] = end % 65536

    def ldann(self, registers, memory, poke):
        pcn = registers[24] + 1
        if poke:
            self.poke(memory, memory[pcn % 65536] + 256 * memory[(pcn + 1) % 65536], registers[0])
        else:
            registers[0] = self.peek(memory, memory[pcn % 65536] + 256 * memory[(pcn + 1) % 65536])
        registers[25] += 13
        registers[24] = (pcn + 2) % 65536

    def ldi(self, registers, memory, inc, repeat):
        # LDI, LDD, LDIR, LDDR
        hl = registers[7] + 256 * registers[6]
        de = registers[5] + 256 * registers[4]
        bc = registers[3] + 256 * registers[2]

        at_hl = self.peek(memory, hl)
        self.poke(memory, de, at_hl)
        n = registers[0] + at_hl
        f = (registers[1] & 0xC1) + (n & 0x08) # SZ.H3.NC
        if n & 0x02:
            f += 0x20 # ..5.....

        hl = (hl + inc) % 65536
        de = (de + inc) % 65536
        bc = (bc - 1) % 65536
        registers[7] = hl % 256
        registers[6] = hl // 256
        registers[5] = de % 256
        registers[4] = de // 256
        registers[3] = bc % 256
        registers[2] = bc // 256
        if bc:
            registers[1] = f + 0x04 # .....P..
        else:
            registers[1] = f

        if repeat and bc:
            registers[25] += 21
        else:
            registers[25] += 16
            registers[24] = (registers[24] + 2) % 65536

    def ldir_fast(self, registers, memory, inc):
        de = registers[5] + 256 * registers[4]
        bc = registers[3] + 256 * registers[2]
        hl = registers[7] + 256 * registers[6]
        count = 0
        repeat = True
        while repeat:
            self.poke(memory, de, self.peek(memory, hl))
            bc = (bc - 1) % 65536
            if bc == 0 or registers[24] <= de <= registers[24] + 1:
                repeat = False
            de = (de + inc) % 65536
            hl = (hl + inc) % 65536
            count += 1
        registers[3], registers[2] = bc % 256, bc // 256
        registers[5], registers[4] = de % 256, de // 256
        registers[7], registers[6] = hl % 256, hl // 256
        r = registers[15]
        registers[15] = (r & 0x80) + ((r + 2 * (count - 1)) % 128)
        n = registers[0] + memory[(hl - inc) % 65536]
        f = (registers[1] & 0xC1) + (n & 0x08) # SZ.H3.NC
        if bc:
            f += 0x04 # .....P..
        else:
            registers[24] = (registers[24] + 2) % 65536
        if n & 0x02:
            registers[1] = f + 0x20
        else:
            registers[1] = f
        registers[25] += 21 * count - 5

    def ldsprr(self, registers, reg):
        registers[12] = registers[reg + 1] + 256 * registers[reg]
        if reg == 6:
            registers[25] += 6
            registers[24] = (registers[24] + 1) % 65536
        else:
            registers[25] += 10
            registers[24] = (registers[24] + 2) % 65536

    def neg(self, registers):
        a = registers[0]
        registers[0] = (256 - a) % 256
        registers[1] = NEG[a]
        registers[25] += 8
        registers[24] = (registers[24] + 2) % 65536

    def nop(self, registers):
        registers[25] += 4
        registers[24] = (registers[24] + 1) % 65536

    def nop_dd_fd(self, registers):
        registers[25] += 4
        registers[24] = (registers[24] + 1) % 65536

        # Compensate for adding 2 to R in run()
        r = registers[15]
        registers[15] = (r & 128) + ((r - 1) % 128)

    def nop_ed(self, registers):
        registers[25] += 8
        registers[24] = (registers[24] + 2) % 65536

    def or_n(self, registers, memory):
        pcn = registers[24] + 1
        a = registers[0] | memory[pcn % 65536]
        registers[0] = a
        registers[1] = SZ53P[a]
        registers[25] += 7
        registers[24] = (pcn + 1) % 65536

    def or_r(self, registers, r):
        a = registers[0] | registers[r]
        registers[0] = a
        registers[1] = SZ53P[a]
        registers[25] += 4
        registers[24] = (registers[24] + 1) % 65536

    def ora(self, registers, memory, timing, size, reg=N):
        a = registers[0] | self.get_operand_value(registers, memory, size, reg)
        registers[0] = a
        registers[1] = SZ53P[a]
        registers[25] += timing
        registers[24] = (registers[24] + size) % 65536

    def _out(self, port, value):
        if self.out_tracer:
            self.out_tracer(port, value)

    def outa(self, registers, memory):
        a = registers[0]
        pcn = registers[24] + 1
        self._out(memory[pcn % 65536] + 256 * a, a)
        registers[25] += 11
        registers[24] = (pcn + 1) % 65536

    def outc(self, registers, reg):
        if reg >= 0:
            self._out(registers[3] + 256 * registers[2], registers[reg])
        else:
            self._out(registers[3] + 256 * registers[2], 0)
        registers[25] += 12
        registers[24] = (registers[24] + 2) % 65536

    def outi(self, registers, memory, inc, repeat):
        # OUTI, OUTD, OTIR, OTDR
        hl = registers[7] + 256 * registers[6]
        b = (registers[2] - 1) % 256

        outval = self.peek(memory, hl)
        self._out(registers[3] + 256 * b, outval)
        hl = (hl + inc) % 65536
        k = (hl % 256) + outval
        f = (b & 0xA8) + PARITY[(k % 8) ^ b] # S.5.3P..
        if b == 0:
            f += 0x40 # .Z......
        if k > 255:
            f += 0x11 # ...H...C

        registers[7] = hl % 256
        registers[6] = hl // 256
        registers[2] = b
        if outval & 0x80:
            registers[1] = f + 0x02 # ......N.
        else:
            registers[1] = f

        if repeat and b:
            registers[25] += 21
        else:
            registers[25] += 16
            registers[24] = (registers[24] + 2) % 65536

    def _pop(self, registers, memory):
        sp = registers[12]
        registers[12] = (sp + 2) % 65536
        self.ppcount -= 1
        return self.peek(memory, sp, 2)

    def pop(self, registers, memory, reg):
        registers[reg + 1], registers[reg] = self._pop(registers, memory)
        if reg < 8:
            registers[25] += 10
            registers[24] = (registers[24] + 1) % 65536
        else:
            registers[25] += 14
            registers[24] = (registers[24] + 2) % 65536

    def _push(self, registers, memory, lsb, msb):
        sp = (registers[12] - 2) % 65536
        self.poke(memory, sp, lsb, msb)
        self.ppcount += 1
        registers[12] = sp

    def push(self, registers, memory, reg):
        self._push(registers, memory, registers[reg + 1], registers[reg])
        if reg < 8:
            registers[25] += 11
            registers[24] = (registers[24] + 1) % 65536
        else:
            registers[25] += 15
            registers[24] = (registers[24] + 2) % 65536

    def ret(self, registers, memory, c_and, c_val):
        if c_and:
            if registers[1] & c_and == c_val:
                registers[25] += 5
                registers[24] = (registers[24] + 1) % 65536
            else:
                registers[25] += 11
                lsb, msb = self._pop(registers, memory)
                registers[24] = lsb + 256 * msb
        else:
            registers[25] += 10
            lsb, msb = self._pop(registers, memory)
            registers[24] = lsb + 256 * msb

    def reti(self, registers, memory):
        registers[25] += 14
        lsb, msb = self._pop(registers, memory)
        registers[24] = lsb + 256 * msb

    def res_set(self, registers, memory, timing, size, bit, reg, bitval, dest=-1):
        if bitval:
            value = self.get_operand_value(registers, memory, size, reg) | bit
        else:
            value = self.get_operand_value(registers, memory, size, reg) & bit
        self.set_operand_value(registers, memory, reg, value)
        if dest >= 0:
            registers[dest] = value
        registers[25] += timing
        registers[24] = (registers[24] + size) % 65536

    def rld(self, registers, memory):
        hl = registers[7] + 256 * registers[6]
        a = registers[0]
        at_hl = self.peek(memory, hl)
        self.poke(memory, hl, ((at_hl * 16) % 256) + (a % 16))
        a_out = registers[0] = (a & 240) + ((at_hl // 16) % 16)
        registers[1] = SZ53P[a_out] + (registers[1] % 2)
        registers[25] += 18
        registers[24] = (registers[24] + 2) % 65536

    def rrd(self, registers, memory):
        hl = registers[7] + 256 * registers[6]
        a = registers[0]
        at_hl = self.peek(memory, hl)
        self.poke(memory, hl, ((a * 16) % 256) + (at_hl // 16))
        a_out = registers[0] = (a & 240) + (at_hl % 16)
        registers[1] = SZ53P[a_out] + (registers[1] % 2)
        registers[25] += 18
        registers[24] = (registers[24] + 2) % 65536

    def rotate_a(self, registers, cbit, rotate, circular=0):
        a = registers[0]
        old_f = registers[1]
        if circular:
            value = rotate[a]
        else:
            value = rotate[old_f % 2][a]
        registers[0] = value
        if a & cbit:
            registers[1] = (old_f & 0xC4) + (value & 0x28) + 0x01
        else:
            registers[1] = (old_f & 0xC4) + (value & 0x28)
        registers[25] += 4
        registers[24] = (registers[24] + 1) % 65536

    def rotate_r(self, registers, cbit, rotate, reg, circular=0):
        r = registers[reg]
        if circular:
            value = rotate[r]
        else:
            value = rotate[registers[1] % 2][r]
        registers[reg] = value
        if r & cbit:
            registers[1] = SZ53P[value] + 0x01
        else:
            registers[1] = SZ53P[value]
        registers[25] += 8
        registers[24] = (registers[24] + 2) % 65536

    def rotate(self, registers, memory, timing, size, cbit, rotate, reg, circular=0, dest=-1):
        r = self.get_operand_value(registers, memory, size, reg)
        if circular:
            value = rotate[r]
        else:
            value = rotate[registers[1] % 2][r]
        self.set_operand_value(registers, memory, reg, value)
        if dest >= 0:
            registers[dest] = value
        if r & cbit:
            registers[1] = SZ53P[value] + 0x01
        else:
            registers[1] = SZ53P[value]
        registers[25] += timing
        registers[24] = (registers[24] + size) % 65536

    def rst(self, registers, memory, addr):
        ret_addr = (registers[24] + 1) % 65536
        self._push(registers, memory, ret_addr % 256, ret_addr // 256)
        registers[25] += 11
        registers[24] = addr

    def sbc_a(self, registers, memory, timing, size, reg):
        value = self.get_operand_value(registers, memory, size, reg)
        old_c = registers[1] % 2
        old_a = registers[0]
        subtrahend = value + old_c
        a = old_a - subtrahend
        if a < 0 or a > 255:
            a %= 256
            f = (a & 0xA8) + 0x01 # S.5.3..C
        else:
            f = a & 0xA8          # S.5.3..C
        if a == 0:
            f += 0x40 # .Z......
        if reg == 0 and old_a % 16 == 0x0F:
            f += old_c * 16 # ...H....
        elif ((old_a % 16) - (subtrahend % 16)) & 0x10:
            f += 0x10       # ...H....
        f += 0x02 # ......N.
        if (old_a ^ value) & 0x80 and (a ^ old_a) & 0x80:
            # Minuend and operand signs are different - overflow if the
            # minuend's sign differs from the sign of the result
            registers[1] = f + 0x04
        else:
            registers[1] = f
        registers[0] = a

        registers[25] += timing
        registers[24] = (registers[24] + size) % 65536

    def sbc_hl(self, registers, reg):
        if reg == 12:
            rr = registers[12]
        else:
            rr = registers[reg + 1] + 256 * registers[reg]
        hl = registers[7] + 256 * registers[6]
        rr_c = rr + (registers[1] % 2)
        result = hl - rr_c

        if result < 0 or result > 0xFFFF:
            result %= 65536
            f = 0x03 # ......NC
        else:
            f = 0x02 # ......N.
        if ((hl % 4096) - (rr_c % 4096)) & 0x1000:
            f += 0x10 # ...H....
        if result & 0x8000:
            f += 0x80 # S.......
        elif result == 0:
            f += 0x40 # .Z......
        if (hl ^ rr) & 0x8000 and (hl ^ result) & 0x8000:
            # Minuend and subtrahend signs are different - overflow if the
            # minuend's sign differs from the sign of the result
            f += 0x04 # .....P..

        h = result // 256
        registers[1] = f + (h & 0x28)
        registers[7] = result % 256
        registers[6] = h

        registers[25] += 15
        registers[24] = (registers[24] + 2) % 65536

    def shift(self, registers, memory, timing, size, shift, cbit, reg, dest=-1):
        r = self.get_operand_value(registers, memory, size, reg)
        value = shift[r]
        self.set_operand_value(registers, memory, reg, value)
        if dest >= 0:
            registers[dest] = value
        if r & cbit:
            registers[1] = SZ53P[value] + 0x01
        else:
            registers[1] = SZ53P[value]
        registers[25] += timing
        registers[24] = (registers[24] + size) % 65536

    def sub(self, registers, memory, timing, size, reg):
        subtrahend = self.get_operand_value(registers, memory, size, reg)
        old_a = registers[0]
        a = old_a - subtrahend
        if a < 0 or a > 255:
            a %= 256
            f = (a & 0xA8) + 0x01 # S.5.3..C
        else:
            f = a & 0xA8          # S.5.3..C
        if a == 0:
            f += 0x40 # .Z......
        if ((old_a % 16) - (subtrahend % 16)) & 0x10:
            f += 0x10       # ...H....
        f += 0x02 # ......N.
        if (old_a ^ subtrahend) & 0x80 and (a ^ old_a) & 0x80:
            # Minuend and subtrahend signs are different - overflow if the
            # minuend's sign differs from the sign of the result
            registers[1] = f + 0x04
        else:
            registers[1] = f
        registers[0] = a

        registers[25] += timing
        registers[24] = (registers[24] + size) % 65536

    def xor_n(self, registers, memory):
        pcn = registers[24] + 1
        a = registers[0] ^ memory[pcn % 65536]
        registers[0] = a
        registers[1] = SZ53P[a]
        registers[25] += 7
        registers[24] = (pcn + 1) % 65536

    def xor_r(self, registers, r):
        a = registers[0] ^ registers[r]
        registers[0] = a
        registers[1] = SZ53P[a]
        registers[25] += 4
        registers[24] = (registers[24] + 1) % 65536

    def xor(self, registers, memory, timing, size, reg=N):
        a = registers[0] ^ self.get_operand_value(registers, memory, size, reg)
        registers[0] = a
        registers[1] = SZ53P[a]
        registers[25] += timing
        registers[24] = (registers[24] + size) % 65536

    def create_opcodes(self):
        r = self.registers
        m = self.memory

        self.opcodes = [
            partial(self.nop, r),                                  # 0x00 NOP
            partial(self.ld16, r, m, B),                           # 0x01 LD BC,nn
            partial(self.ld8, r, m, 7, 1, Bd, A),                  # 0x02 LD (BC),A
            partial(self.inc_dec16, r, 1, B),                      # 0x03 INC BC
            partial(self.inc_r, r, B),                             # 0x04 INC B
            partial(self.dec_r, r, B),                             # 0x05 DEC B
            partial(self.ld_r_n, r, m, B),                         # 0x06 LD B,n
            partial(self.rotate_a, r, 128, RLC, 1),                # 0x07 RLCA
            partial(self.ex_af, r),                                # 0x08 EX AF,AF'
            partial(self.add16, r, 11, 1, H, B),                   # 0x09 ADD HL,BC
            partial(self.ld8, r, m, 7, 1, A, Bd),                  # 0x0A LD A,(BC)
            partial(self.inc_dec16, r, -1, B),                     # 0x0B DEC BC
            partial(self.inc_r, r, C),                             # 0x0C INC C
            partial(self.dec_r, r, C),                             # 0x0D DEC C
            partial(self.ld_r_n, r, m, C),                         # 0x0E LD C,n
            partial(self.rotate_a, r, 1, RRC, 1),                  # 0x0F RRCA
            partial(self.djnz, r, m),                              # 0x10 DJNZ nn
            partial(self.ld16, r, m, D),                           # 0x11 LD DE,nn
            partial(self.ld8, r, m, 7, 1, Dd, A),                  # 0x12 LD (DE),A
            partial(self.inc_dec16, r, 1, D),                      # 0x13 INC DE
            partial(self.inc_r, r, D),                             # 0x14 INC D
            partial(self.dec_r, r, D),                             # 0x15 DEC D
            partial(self.ld_r_n, r, m, D),                         # 0x16 LD D,n
            partial(self.rotate_a, r, 128, RL),                    # 0x17 RLA
            partial(self.jr, r, m, 0, 0),                          # 0x18 JR nn
            partial(self.add16, r, 11, 1, H, D),                   # 0x19 ADD HL,DE
            partial(self.ld8, r, m, 7, 1, A, Dd),                  # 0x1A LD A,(DE)
            partial(self.inc_dec16, r, -1, D),                     # 0x1B DEC DE
            partial(self.inc_r, r, E),                             # 0x1C INC E
            partial(self.dec_r, r, E),                             # 0x1D DEC E
            partial(self.ld_r_n, r, m, E),                         # 0x1E LD E,n
            partial(self.rotate_a, r, 1, RR),                      # 0x1F RRA
            partial(self.jr, r, m, 64, 0),                         # 0x20 JR NZ,nn
            partial(self.ld16, r, m, H),                           # 0x21 LD HL,nn
            partial(self.ld16addr, r, m, 16, 3, H, 1),             # 0x22 LD (nn),HL
            partial(self.inc_dec16, r, 1, H),                      # 0x23 INC HL
            partial(self.inc_r, r, H),                             # 0x24 INC H
            partial(self.dec_r, r, H),                             # 0x25 DEC H
            partial(self.ld_r_n, r, m, H),                         # 0x26 LD H,n
            partial(self.daa, r),                                  # 0x27 DAA
            partial(self.jr, r, m, 64, 64),                        # 0x28 JR Z,nn
            partial(self.add16, r, 11, 1, H, H),                   # 0x29 ADD HL,HL
            partial(self.ld16addr, r, m, 16, 3, H, 0),             # 0x2A LD HL,(nn)
            partial(self.inc_dec16, r, -1, H),                     # 0x2B DEC HL
            partial(self.inc_r, r, L),                             # 0x2C INC L
            partial(self.dec_r, r, L),                             # 0x2D DEC L
            partial(self.ld_r_n, r, m, L),                         # 0x2E LD L,n
            partial(self.cpl, r),                                  # 0x2F CPL
            partial(self.jr, r, m, 1, 0),                          # 0x30 JR NC,nn
            partial(self.ld16, r, m, SP),                          # 0x31 LD SP,nn
            partial(self.ldann, r, m, 1),                          # 0x32 LD (nn),A
            partial(self.inc_dec16, r, 1, SP),                     # 0x33 INC SP
            partial(self.inc_dec8, r, m, 11, 1, 1, Hd),            # 0x34 INC (HL)
            partial(self.inc_dec8, r, m, 11, 1, -1, Hd),           # 0x35 DEC (HL)
            partial(self.ld8, r, m, 10, 2, Hd),                    # 0x36 LD (HL),n
            partial(self.cf, r, 0),                                # 0x37 SCF
            partial(self.jr, r, m, 1, 1),                          # 0x38 JR C,nn
            partial(self.add16, r, 11, 1, H, SP),                  # 0x39 ADD HL,SP
            partial(self.ldann, r, m, 0),                          # 0x3A LD A,(nn)
            partial(self.inc_dec16, r, -1, SP),                    # 0x3B DEC SP
            partial(self.inc_r, r, A),                             # 0x3C INC A
            partial(self.dec_r, r, A),                             # 0x3D DEC A
            partial(self.ld_r_n, r, m, A),                         # 0x3E LD A,n
            partial(self.cf, r, 1),                                # 0x3F CCF
            partial(self.ld_r_r, r, B, B),                         # 0x40 LD B,B
            partial(self.ld_r_r, r, B, C),                         # 0x41 LD B,C
            partial(self.ld_r_r, r, B, D),                         # 0x42 LD B,D
            partial(self.ld_r_r, r, B, E),                         # 0x43 LD B,E
            partial(self.ld_r_r, r, B, H),                         # 0x44 LD B,H
            partial(self.ld_r_r, r, B, L),                         # 0x45 LD B,L
            partial(self.ld8, r, m, 7, 1, B, Hd),                  # 0x46 LD B,(HL)
            partial(self.ld_r_r, r, B, A),                         # 0x47 LD B,A
            partial(self.ld_r_r, r, C, B),                         # 0x48 LD C,B
            partial(self.ld_r_r, r, C, C),                         # 0x49 LD C,C
            partial(self.ld_r_r, r, C, D),                         # 0x4A LD C,D
            partial(self.ld_r_r, r, C, E),                         # 0x4B LD C,E
            partial(self.ld_r_r, r, C, H),                         # 0x4C LD C,H
            partial(self.ld_r_r, r, C, L),                         # 0x4D LD C,L
            partial(self.ld8, r, m, 7, 1, C, Hd),                  # 0x4E LD C,(HL)
            partial(self.ld_r_r, r, C, A),                         # 0x4F LD C,A
            partial(self.ld_r_r, r, D, B),                         # 0x50 LD D,B
            partial(self.ld_r_r, r, D, C),                         # 0x51 LD D,C
            partial(self.ld_r_r, r, D, D),                         # 0x52 LD D,D
            partial(self.ld_r_r, r, D, E),                         # 0x53 LD D,E
            partial(self.ld_r_r, r, D, H),                         # 0x54 LD D,H
            partial(self.ld_r_r, r, D, L),                         # 0x55 LD D,L
            partial(self.ld8, r, m, 7, 1, D, Hd),                  # 0x56 LD D,(HL)
            partial(self.ld_r_r, r, D, A),                         # 0x57 LD D,A
            partial(self.ld_r_r, r, E, B),                         # 0x58 LD E,B
            partial(self.ld_r_r, r, E, C),                         # 0x59 LD E,C
            partial(self.ld_r_r, r, E, D),                         # 0x5A LD E,D
            partial(self.ld_r_r, r, E, E),                         # 0x5B LD E,E
            partial(self.ld_r_r, r, E, H),                         # 0x5C LD E,H
            partial(self.ld_r_r, r, E, L),                         # 0x5D LD E,L
            partial(self.ld8, r, m, 7, 1, E, Hd),                  # 0x5E LD E,(HL)
            partial(self.ld_r_r, r, E, A),                         # 0x5F LD E,A
            partial(self.ld_r_r, r, H, B),                         # 0x60 LD H,B
            partial(self.ld_r_r, r, H, C),                         # 0x61 LD H,C
            partial(self.ld_r_r, r, H, D),                         # 0x62 LD H,D
            partial(self.ld_r_r, r, H, E),                         # 0x63 LD H,E
            partial(self.ld_r_r, r, H, H),                         # 0x64 LD H,H
            partial(self.ld_r_r, r, H, L),                         # 0x65 LD H,L
            partial(self.ld8, r, m, 7, 1, H, Hd),                  # 0x66 LD H,(HL)
            partial(self.ld_r_r, r, H, A),                         # 0x67 LD H,A
            partial(self.ld_r_r, r, L, B),                         # 0x68 LD L,B
            partial(self.ld_r_r, r, L, C),                         # 0x69 LD L,C
            partial(self.ld_r_r, r, L, D),                         # 0x6A LD L,D
            partial(self.ld_r_r, r, L, E),                         # 0x6B LD L,E
            partial(self.ld_r_r, r, L, H),                         # 0x6C LD L,H
            partial(self.ld_r_r, r, L, L),                         # 0x6D LD L,L
            partial(self.ld8, r, m, 7, 1, L, Hd),                  # 0x6E LD L,(HL)
            partial(self.ld_r_r, r, L, A),                         # 0x6F LD L,A
            partial(self.ld8, r, m, 7, 1, Hd, B),                  # 0x70 LD (HL),B
            partial(self.ld8, r, m, 7, 1, Hd, C),                  # 0x71 LD (HL),C
            partial(self.ld8, r, m, 7, 1, Hd, D),                  # 0x72 LD (HL),D
            partial(self.ld8, r, m, 7, 1, Hd, E),                  # 0x73 LD (HL),E
            partial(self.ld8, r, m, 7, 1, Hd, H),                  # 0x74 LD (HL),H
            partial(self.ld8, r, m, 7, 1, Hd, L),                  # 0x75 LD (HL),L
            partial(self.halt, r),                                 # 0x76 HALT
            partial(self.ld8, r, m, 7, 1, Hd, A),                  # 0x77 LD (HL),A
            partial(self.ld_r_r, r, A, B),                         # 0x78 LD A,B
            partial(self.ld_r_r, r, A, C),                         # 0x79 LD A,C
            partial(self.ld_r_r, r, A, D),                         # 0x7A LD A,D
            partial(self.ld_r_r, r, A, E),                         # 0x7B LD A,E
            partial(self.ld_r_r, r, A, H),                         # 0x7C LD A,H
            partial(self.ld_r_r, r, A, L),                         # 0x7D LD A,L
            partial(self.ld8, r, m, 7, 1, A, Hd),                  # 0x7E LD A,(HL)
            partial(self.ld_r_r, r, A, A),                         # 0x7F LD A,A
            partial(self.add_a, r, m, 4, 1, B),                    # 0x80 ADD A,B
            partial(self.add_a, r, m, 4, 1, C),                    # 0x81 ADD A,C
            partial(self.add_a, r, m, 4, 1, D),                    # 0x82 ADD A,D
            partial(self.add_a, r, m, 4, 1, E),                    # 0x83 ADD A,E
            partial(self.add_a, r, m, 4, 1, H),                    # 0x84 ADD A,H
            partial(self.add_a, r, m, 4, 1, L),                    # 0x85 ADD A,L
            partial(self.add_a, r, m, 7, 1, Hd),                   # 0x86 ADD A,(HL)
            partial(self.add_a, r, m, 4, 1, A),                    # 0x87 ADD A,A
            partial(self.adc_a, r, m, 4, 1, B),                    # 0x88 ADC A,B
            partial(self.adc_a, r, m, 4, 1, C),                    # 0x89 ADC A,C
            partial(self.adc_a, r, m, 4, 1, D),                    # 0x8A ADC A,D
            partial(self.adc_a, r, m, 4, 1, E),                    # 0x8B ADC A,E
            partial(self.adc_a, r, m, 4, 1, H),                    # 0x8C ADC A,H
            partial(self.adc_a, r, m, 4, 1, L),                    # 0x8D ADC A,L
            partial(self.adc_a, r, m, 7, 1, Hd),                   # 0x8E ADC A,(HL)
            partial(self.adc_a, r, m, 4, 1, A),                    # 0x8F ADC A,A
            partial(self.sub, r, m, 4, 1, B),                      # 0x90 SUB B
            partial(self.sub, r, m, 4, 1, C),                      # 0x91 SUB C
            partial(self.sub, r, m, 4, 1, D),                      # 0x92 SUB D
            partial(self.sub, r, m, 4, 1, E),                      # 0x93 SUB E
            partial(self.sub, r, m, 4, 1, H),                      # 0x94 SUB H
            partial(self.sub, r, m, 4, 1, L),                      # 0x95 SUB L
            partial(self.sub, r, m, 7, 1, Hd),                     # 0x96 SUB (HL)
            partial(self.sub, r, m, 4, 1, A),                      # 0x97 SUB A
            partial(self.sbc_a, r, m, 4, 1, B),                    # 0x98 SBC A,B
            partial(self.sbc_a, r, m, 4, 1, C),                    # 0x99 SBC A,C
            partial(self.sbc_a, r, m, 4, 1, D),                    # 0x9A SBC A,D
            partial(self.sbc_a, r, m, 4, 1, E),                    # 0x9B SBC A,E
            partial(self.sbc_a, r, m, 4, 1, H),                    # 0x9C SBC A,H
            partial(self.sbc_a, r, m, 4, 1, L),                    # 0x9D SBC A,L
            partial(self.sbc_a, r, m, 7, 1, Hd),                   # 0x9E SBC A,(HL)
            partial(self.sbc_a, r, m, 4, 1, A),                    # 0x9F SBC A,A
            partial(self.and_r, r, B),                             # 0xA0 AND B
            partial(self.and_r, r, C),                             # 0xA1 AND C
            partial(self.and_r, r, D),                             # 0xA2 AND D
            partial(self.and_r, r, E),                             # 0xA3 AND E
            partial(self.and_r, r, H),                             # 0xA4 AND H
            partial(self.and_r, r, L),                             # 0xA5 AND L
            partial(self.anda, r, m, 7, 1, Hd),                    # 0xA6 AND (HL)
            partial(self.and_r, r, A),                             # 0xA7 AND A
            partial(self.xor_r, r, B),                             # 0xA8 XOR B
            partial(self.xor_r, r, C),                             # 0xA9 XOR C
            partial(self.xor_r, r, D),                             # 0xAA XOR D
            partial(self.xor_r, r, E),                             # 0xAB XOR E
            partial(self.xor_r, r, H),                             # 0xAC XOR H
            partial(self.xor_r, r, L),                             # 0xAD XOR L
            partial(self.xor, r, m, 7, 1, Hd),                     # 0xAE XOR (HL)
            partial(self.xor_r, r, A),                             # 0xAF XOR A
            partial(self.or_r, r, B),                              # 0xB0 OR B
            partial(self.or_r, r, C),                              # 0xB1 OR C
            partial(self.or_r, r, D),                              # 0xB2 OR D
            partial(self.or_r, r, E),                              # 0xB3 OR E
            partial(self.or_r, r, H),                              # 0xB4 OR H
            partial(self.or_r, r, L),                              # 0xB5 OR L
            partial(self.ora, r, m, 7, 1, Hd),                     # 0xB6 OR (HL)
            partial(self.or_r, r, A),                              # 0xB7 OR A
            partial(self.cp, r, m, 4, 1, B),                       # 0xB8 CP B
            partial(self.cp, r, m, 4, 1, C),                       # 0xB9 CP C
            partial(self.cp, r, m, 4, 1, D),                       # 0xBA CP D
            partial(self.cp, r, m, 4, 1, E),                       # 0xBB CP E
            partial(self.cp, r, m, 4, 1, H),                       # 0xBC CP H
            partial(self.cp, r, m, 4, 1, L),                       # 0xBD CP L
            partial(self.cp, r, m, 7, 1, Hd),                      # 0xBE CP (HL)
            partial(self.cp, r, m, 4, 1, A),                       # 0xBF CP A
            partial(self.ret, r, m, 64, 64),                       # 0xC0 RET NZ
            partial(self.pop, r, m, B),                            # 0xC1 POP BC
            partial(self.jp, r, m, 64, 64),                        # 0xC2 JP NZ,nn
            partial(self.jp, r, m, 0, 0),                          # 0xC3 JP nn
            partial(self.call, r, m, 64, 64),                      # 0xC4 CALL NZ,nn
            partial(self.push, r, m, B),                           # 0xC5 PUSH BC
            partial(self.add_a, r, m, 7, 2, N),                    # 0xC6 ADD A,n
            partial(self.rst, r, m, 0),                            # 0xC7 RST $00
            partial(self.ret, r, m, 64, 0),                        # 0xC8 RET Z
            partial(self.ret, r, m, 0, 0),                         # 0xC9 RET
            partial(self.jp, r, m, 64, 0),                         # 0xCA JP Z,nn
            None,                                                  # 0xCB CB prefix
            partial(self.call, r, m, 64, 0),                       # 0xCC CALL Z,nn
            partial(self.call, r, m, 0, 0),                        # 0xCD CALL nn
            partial(self.adc_a, r, m, 7, 2, N),                    # 0xCE ADC A,n
            partial(self.rst, r, m, 8),                            # 0xCF RST $08
            partial(self.ret, r, m, 1, 1),                         # 0xD0 RET NC
            partial(self.pop, r, m, D),                            # 0xD1 POP DE
            partial(self.jp, r, m, 1, 1),                          # 0xD2 JP NC,nn
            partial(self.outa, r, m),                              # 0xD3 OUT (n),A
            partial(self.call, r, m, 1, 1),                        # 0xD4 CALL NC,nn
            partial(self.push, r, m, D),                           # 0xD5 PUSH DE
            partial(self.sub, r, m, 7, 2, N),                      # 0xD6 SUB n
            partial(self.rst, r, m, 16),                           # 0xD7 RST $10
            partial(self.ret, r, m, 1, 0),                         # 0xD8 RET C
            partial(self.exx, r),                                  # 0xD9 EXX
            partial(self.jp, r, m, 1, 0),                          # 0xDA JP C,nn
            partial(self.in_a, r, m),                              # 0xDB IN A,(n)
            partial(self.call, r, m, 1, 0),                        # 0xDC CALL C,nn
            None,                                                  # 0xDD DD prefix
            partial(self.sbc_a, r, m, 7, 2, N),                    # 0xDE SBC A,n
            partial(self.rst, r, m, 24),                           # 0xDF RST $18
            partial(self.ret, r, m, 4, 4),                         # 0xE0 RET PO
            partial(self.pop, r, m, H),                            # 0xE1 POP HL
            partial(self.jp, r, m, 4, 4),                          # 0xE2 JP PO,nn
            partial(self.ex_sp, r, m, H),                          # 0xE3 EX (SP),HL
            partial(self.call, r, m, 4, 4),                        # 0xE4 CALL PO,nn
            partial(self.push, r, m, H),                           # 0xE5 PUSH HL
            partial(self.and_n, r, m),                             # 0xE6 AND n
            partial(self.rst, r, m, 32),                           # 0xE7 RST $20
            partial(self.ret, r, m, 4, 0),                         # 0xE8 RET PE
            partial(self.jp, r, m, 0, H),                          # 0xE9 JP (HL)
            partial(self.jp, r, m, 4, 0),                          # 0xEA JP PE,nn
            partial(self.ex_de_hl, r),                             # 0xEB EX DE,HL
            partial(self.call, r, m, 4, 0),                        # 0xEC CALL PE,nn
            None,                                                  # 0xED ED prefix
            partial(self.xor_n, r, m),                             # 0xEE XOR n
            partial(self.rst, r, m, 40),                           # 0xEF RST $28
            partial(self.ret, r, m, 128, 128),                     # 0xF0 RET P
            partial(self.pop, r, m, A),                            # 0xF1 POP AF
            partial(self.jp, r, m, 128, 128),                      # 0xF2 JP P,nn
            partial(self.di_ei, r, 0),                             # 0xF3 DI
            partial(self.call, r, m, 128, 128),                    # 0xF4 CALL P,nn
            partial(self.push, r, m, A),                           # 0xF5 PUSH AF
            partial(self.or_n, r, m),                              # 0xF6 OR n
            partial(self.rst, r, m, 48),                           # 0xF7 RST $30
            partial(self.ret, r, m, 128, 0),                       # 0xF8 RET M
            partial(self.ldsprr, r, H),                            # 0xF9 LD SP,HL
            partial(self.jp, r, m, 128, 0),                        # 0xFA JP M,nn
            partial(self.di_ei, r, 1),                             # 0xFB EI
            partial(self.call, r, m, 128, 0),                      # 0xFC CALL M,nn
            None,                                                  # 0xFD FD prefix
            partial(self.cp, r, m, 7, 2),                          # 0xFE CP n
            partial(self.rst, r, m, 56),                           # 0xFF RST $38
        ]

        self.after_CB = [
            partial(self.rotate_r, r, 128, RLC, B, 1),             # 0x00 RLC B
            partial(self.rotate_r, r, 128, RLC, C, 1),             # 0x01 RLC C
            partial(self.rotate_r, r, 128, RLC, D, 1),             # 0x02 RLC D
            partial(self.rotate_r, r, 128, RLC, E, 1),             # 0x03 RLC E
            partial(self.rotate_r, r, 128, RLC, H, 1),             # 0x04 RLC H
            partial(self.rotate_r, r, 128, RLC, L, 1),             # 0x05 RLC L
            partial(self.rotate, r, m, 15, 2, 128, RLC, Hd, 1),    # 0x06 RLC (HL)
            partial(self.rotate_r, r, 128, RLC, A, 1),             # 0x07 RLC A
            partial(self.rotate_r, r, 1, RRC, B, 1),               # 0x08 RRC B
            partial(self.rotate_r, r, 1, RRC, C, 1),               # 0x09 RRC C
            partial(self.rotate_r, r, 1, RRC, D, 1),               # 0x0A RRC D
            partial(self.rotate_r, r, 1, RRC, E, 1),               # 0x0B RRC E
            partial(self.rotate_r, r, 1, RRC, H, 1),               # 0x0C RRC H
            partial(self.rotate_r, r, 1, RRC, L, 1),               # 0x0D RRC L
            partial(self.rotate, r, m, 15, 2, 1, RRC, Hd, 1),      # 0x0E RRC (HL)
            partial(self.rotate_r, r, 1, RRC, A, 1),               # 0x0F RRC A
            partial(self.rotate_r, r, 128, RL, B),                 # 0x10 RL B
            partial(self.rotate_r, r, 128, RL, C),                 # 0x11 RL C
            partial(self.rotate_r, r, 128, RL, D),                 # 0x12 RL D
            partial(self.rotate_r, r, 128, RL, E),                 # 0x13 RL E
            partial(self.rotate_r, r, 128, RL, H),                 # 0x14 RL H
            partial(self.rotate_r, r, 128, RL, L),                 # 0x15 RL L
            partial(self.rotate, r, m, 15, 2, 128, RL, Hd),        # 0x16 RL (HL)
            partial(self.rotate_r, r, 128, RL, A),                 # 0x17 RL A
            partial(self.rotate_r, r, 1, RR, B),                   # 0x18 RR B
            partial(self.rotate_r, r, 1, RR, C),                   # 0x19 RR C
            partial(self.rotate_r, r, 1, RR, D),                   # 0x1A RR D
            partial(self.rotate_r, r, 1, RR, E),                   # 0x1B RR E
            partial(self.rotate_r, r, 1, RR, H),                   # 0x1C RR H
            partial(self.rotate_r, r, 1, RR, L),                   # 0x1D RR L
            partial(self.rotate, r, m, 15, 2, 1, RR, Hd),          # 0x1E RR (HL)
            partial(self.rotate_r, r, 1, RR, A),                   # 0x1F RR A
            partial(self.shift, r, m, 8, 2, SLA, 128, B),          # 0x20 SLA B
            partial(self.shift, r, m, 8, 2, SLA, 128, C),          # 0x21 SLA C
            partial(self.shift, r, m, 8, 2, SLA, 128, D),          # 0x22 SLA D
            partial(self.shift, r, m, 8, 2, SLA, 128, E),          # 0x23 SLA E
            partial(self.shift, r, m, 8, 2, SLA, 128, H),          # 0x24 SLA H
            partial(self.shift, r, m, 8, 2, SLA, 128, L),          # 0x25 SLA L
            partial(self.shift, r, m, 15, 2, SLA, 128, Hd),        # 0x26 SLA (HL)
            partial(self.shift, r, m, 8, 2, SLA, 128, A),          # 0x27 SLA A
            partial(self.shift, r, m, 8, 2, SRA, 1, B),            # 0x28 SRA B
            partial(self.shift, r, m, 8, 2, SRA, 1, C),            # 0x29 SRA C
            partial(self.shift, r, m, 8, 2, SRA, 1, D),            # 0x2A SRA D
            partial(self.shift, r, m, 8, 2, SRA, 1, E),            # 0x2B SRA E
            partial(self.shift, r, m, 8, 2, SRA, 1, H),            # 0x2C SRA H
            partial(self.shift, r, m, 8, 2, SRA, 1, L),            # 0x2D SRA L
            partial(self.shift, r, m, 15, 2, SRA, 1, Hd),          # 0x2E SRA (HL)
            partial(self.shift, r, m, 8, 2, SRA, 1, A),            # 0x2F SRA A
            partial(self.shift, r, m, 8, 2, SLL, 128, B),          # 0x30 SLL B
            partial(self.shift, r, m, 8, 2, SLL, 128, C),          # 0x31 SLL C
            partial(self.shift, r, m, 8, 2, SLL, 128, D),          # 0x32 SLL D
            partial(self.shift, r, m, 8, 2, SLL, 128, E),          # 0x33 SLL E
            partial(self.shift, r, m, 8, 2, SLL, 128, H),          # 0x34 SLL H
            partial(self.shift, r, m, 8, 2, SLL, 128, L),          # 0x35 SLL L
            partial(self.shift, r, m, 15, 2, SLL, 128, Hd),        # 0x36 SLL (HL)
            partial(self.shift, r, m, 8, 2, SLL, 128, A),          # 0x37 SLL A
            partial(self.shift, r, m, 8, 2, SRL, 1, B),            # 0x38 SRL B
            partial(self.shift, r, m, 8, 2, SRL, 1, C),            # 0x39 SRL C
            partial(self.shift, r, m, 8, 2, SRL, 1, D),            # 0x3A SRL D
            partial(self.shift, r, m, 8, 2, SRL, 1, E),            # 0x3B SRL E
            partial(self.shift, r, m, 8, 2, SRL, 1, H),            # 0x3C SRL H
            partial(self.shift, r, m, 8, 2, SRL, 1, L),            # 0x3D SRL L
            partial(self.shift, r, m, 15, 2, SRL, 1, Hd),          # 0x3E SRL (HL)
            partial(self.shift, r, m, 8, 2, SRL, 1, A),            # 0x3F SRL A
            partial(self.bit, r, m, 8, 2, 1, B),                   # 0x40 BIT 0,B
            partial(self.bit, r, m, 8, 2, 1, C),                   # 0x41 BIT 0,C
            partial(self.bit, r, m, 8, 2, 1, D),                   # 0x42 BIT 0,D
            partial(self.bit, r, m, 8, 2, 1, E),                   # 0x43 BIT 0,E
            partial(self.bit, r, m, 8, 2, 1, H),                   # 0x44 BIT 0,H
            partial(self.bit, r, m, 8, 2, 1, L),                   # 0x45 BIT 0,L
            partial(self.bit, r, m, 12, 2, 1, Hd),                 # 0x46 BIT 0,(HL)
            partial(self.bit, r, m, 8, 2, 1, A),                   # 0x47 BIT 0,A
            partial(self.bit, r, m, 8, 2, 2, B),                   # 0x48 BIT 1,B
            partial(self.bit, r, m, 8, 2, 2, C),                   # 0x49 BIT 1,C
            partial(self.bit, r, m, 8, 2, 2, D),                   # 0x4A BIT 1,D
            partial(self.bit, r, m, 8, 2, 2, E),                   # 0x4B BIT 1,E
            partial(self.bit, r, m, 8, 2, 2, H),                   # 0x4C BIT 1,H
            partial(self.bit, r, m, 8, 2, 2, L),                   # 0x4D BIT 1,L
            partial(self.bit, r, m, 12, 2, 2, Hd),                 # 0x4E BIT 1,(HL)
            partial(self.bit, r, m, 8, 2, 2, A),                   # 0x4F BIT 1,A
            partial(self.bit, r, m, 8, 2, 4, B),                   # 0x50 BIT 2,B
            partial(self.bit, r, m, 8, 2, 4, C),                   # 0x51 BIT 2,C
            partial(self.bit, r, m, 8, 2, 4, D),                   # 0x52 BIT 2,D
            partial(self.bit, r, m, 8, 2, 4, E),                   # 0x53 BIT 2,E
            partial(self.bit, r, m, 8, 2, 4, H),                   # 0x54 BIT 2,H
            partial(self.bit, r, m, 8, 2, 4, L),                   # 0x55 BIT 2,L
            partial(self.bit, r, m, 12, 2, 4, Hd),                 # 0x56 BIT 2,(HL)
            partial(self.bit, r, m, 8, 2, 4, A),                   # 0x57 BIT 2,A
            partial(self.bit, r, m, 8, 2, 8, B),                   # 0x58 BIT 3,B
            partial(self.bit, r, m, 8, 2, 8, C),                   # 0x59 BIT 3,C
            partial(self.bit, r, m, 8, 2, 8, D),                   # 0x5A BIT 3,D
            partial(self.bit, r, m, 8, 2, 8, E),                   # 0x5B BIT 3,E
            partial(self.bit, r, m, 8, 2, 8, H),                   # 0x5C BIT 3,H
            partial(self.bit, r, m, 8, 2, 8, L),                   # 0x5D BIT 3,L
            partial(self.bit, r, m, 12, 2, 8, Hd),                 # 0x5E BIT 3,(HL)
            partial(self.bit, r, m, 8, 2, 8, A),                   # 0x5F BIT 3,A
            partial(self.bit, r, m, 8, 2, 16, B),                  # 0x60 BIT 4,B
            partial(self.bit, r, m, 8, 2, 16, C),                  # 0x61 BIT 4,C
            partial(self.bit, r, m, 8, 2, 16, D),                  # 0x62 BIT 4,D
            partial(self.bit, r, m, 8, 2, 16, E),                  # 0x63 BIT 4,E
            partial(self.bit, r, m, 8, 2, 16, H),                  # 0x64 BIT 4,H
            partial(self.bit, r, m, 8, 2, 16, L),                  # 0x65 BIT 4,L
            partial(self.bit, r, m, 12, 2, 16, Hd),                # 0x66 BIT 4,(HL)
            partial(self.bit, r, m, 8, 2, 16, A),                  # 0x67 BIT 4,A
            partial(self.bit, r, m, 8, 2, 32, B),                  # 0x68 BIT 5,B
            partial(self.bit, r, m, 8, 2, 32, C),                  # 0x69 BIT 5,C
            partial(self.bit, r, m, 8, 2, 32, D),                  # 0x6A BIT 5,D
            partial(self.bit, r, m, 8, 2, 32, E),                  # 0x6B BIT 5,E
            partial(self.bit, r, m, 8, 2, 32, H),                  # 0x6C BIT 5,H
            partial(self.bit, r, m, 8, 2, 32, L),                  # 0x6D BIT 5,L
            partial(self.bit, r, m, 12, 2, 32, Hd),                # 0x6E BIT 5,(HL)
            partial(self.bit, r, m, 8, 2, 32, A),                  # 0x6F BIT 5,A
            partial(self.bit, r, m, 8, 2, 64, B),                  # 0x70 BIT 6,B
            partial(self.bit, r, m, 8, 2, 64, C),                  # 0x71 BIT 6,C
            partial(self.bit, r, m, 8, 2, 64, D),                  # 0x72 BIT 6,D
            partial(self.bit, r, m, 8, 2, 64, E),                  # 0x73 BIT 6,E
            partial(self.bit, r, m, 8, 2, 64, H),                  # 0x74 BIT 6,H
            partial(self.bit, r, m, 8, 2, 64, L),                  # 0x75 BIT 6,L
            partial(self.bit, r, m, 12, 2, 64, Hd),                # 0x76 BIT 6,(HL)
            partial(self.bit, r, m, 8, 2, 64, A),                  # 0x77 BIT 6,A
            partial(self.bit, r, m, 8, 2, 128, B),                 # 0x78 BIT 7,B
            partial(self.bit, r, m, 8, 2, 128, C),                 # 0x79 BIT 7,C
            partial(self.bit, r, m, 8, 2, 128, D),                 # 0x7A BIT 7,D
            partial(self.bit, r, m, 8, 2, 128, E),                 # 0x7B BIT 7,E
            partial(self.bit, r, m, 8, 2, 128, H),                 # 0x7C BIT 7,H
            partial(self.bit, r, m, 8, 2, 128, L),                 # 0x7D BIT 7,L
            partial(self.bit, r, m, 12, 2, 128, Hd),               # 0x7E BIT 7,(HL)
            partial(self.bit, r, m, 8, 2, 128, A),                 # 0x7F BIT 7,A
            partial(self.res_set, r, m, 8, 2, 254, B, 0),          # 0x80 RES 0,B
            partial(self.res_set, r, m, 8, 2, 254, C, 0),          # 0x81 RES 0,C
            partial(self.res_set, r, m, 8, 2, 254, D, 0),          # 0x82 RES 0,D
            partial(self.res_set, r, m, 8, 2, 254, E, 0),          # 0x83 RES 0,E
            partial(self.res_set, r, m, 8, 2, 254, H, 0),          # 0x84 RES 0,H
            partial(self.res_set, r, m, 8, 2, 254, L, 0),          # 0x85 RES 0,L
            partial(self.res_set, r, m, 15, 2, 254, Hd, 0),        # 0x86 RES 0,(HL)
            partial(self.res_set, r, m, 8, 2, 254, A, 0),          # 0x87 RES 0,A
            partial(self.res_set, r, m, 8, 2, 253, B, 0),          # 0x88 RES 1,B
            partial(self.res_set, r, m, 8, 2, 253, C, 0),          # 0x89 RES 1,C
            partial(self.res_set, r, m, 8, 2, 253, D, 0),          # 0x8A RES 1,D
            partial(self.res_set, r, m, 8, 2, 253, E, 0),          # 0x8B RES 1,E
            partial(self.res_set, r, m, 8, 2, 253, H, 0),          # 0x8C RES 1,H
            partial(self.res_set, r, m, 8, 2, 253, L, 0),          # 0x8D RES 1,L
            partial(self.res_set, r, m, 15, 2, 253, Hd, 0),        # 0x8E RES 1,(HL)
            partial(self.res_set, r, m, 8, 2, 253, A, 0),          # 0x8F RES 1,A
            partial(self.res_set, r, m, 8, 2, 251, B, 0),          # 0x90 RES 2,B
            partial(self.res_set, r, m, 8, 2, 251, C, 0),          # 0x91 RES 2,C
            partial(self.res_set, r, m, 8, 2, 251, D, 0),          # 0x92 RES 2,D
            partial(self.res_set, r, m, 8, 2, 251, E, 0),          # 0x93 RES 2,E
            partial(self.res_set, r, m, 8, 2, 251, H, 0),          # 0x94 RES 2,H
            partial(self.res_set, r, m, 8, 2, 251, L, 0),          # 0x95 RES 2,L
            partial(self.res_set, r, m, 15, 2, 251, Hd, 0),        # 0x96 RES 2,(HL)
            partial(self.res_set, r, m, 8, 2, 251, A, 0),          # 0x97 RES 2,A
            partial(self.res_set, r, m, 8, 2, 247, B, 0),          # 0x98 RES 3,B
            partial(self.res_set, r, m, 8, 2, 247, C, 0),          # 0x99 RES 3,C
            partial(self.res_set, r, m, 8, 2, 247, D, 0),          # 0x9A RES 3,D
            partial(self.res_set, r, m, 8, 2, 247, E, 0),          # 0x9B RES 3,E
            partial(self.res_set, r, m, 8, 2, 247, H, 0),          # 0x9C RES 3,H
            partial(self.res_set, r, m, 8, 2, 247, L, 0),          # 0x9D RES 3,L
            partial(self.res_set, r, m, 15, 2, 247, Hd, 0),        # 0x9E RES 3,(HL)
            partial(self.res_set, r, m, 8, 2, 247, A, 0),          # 0x9F RES 3,A
            partial(self.res_set, r, m, 8, 2, 239, B, 0),          # 0xA0 RES 4,B
            partial(self.res_set, r, m, 8, 2, 239, C, 0),          # 0xA1 RES 4,C
            partial(self.res_set, r, m, 8, 2, 239, D, 0),          # 0xA2 RES 4,D
            partial(self.res_set, r, m, 8, 2, 239, E, 0),          # 0xA3 RES 4,E
            partial(self.res_set, r, m, 8, 2, 239, H, 0),          # 0xA4 RES 4,H
            partial(self.res_set, r, m, 8, 2, 239, L, 0),          # 0xA5 RES 4,L
            partial(self.res_set, r, m, 15, 2, 239, Hd, 0),        # 0xA6 RES 4,(HL)
            partial(self.res_set, r, m, 8, 2, 239, A, 0),          # 0xA7 RES 4,A
            partial(self.res_set, r, m, 8, 2, 223, B, 0),          # 0xA8 RES 5,B
            partial(self.res_set, r, m, 8, 2, 223, C, 0),          # 0xA9 RES 5,C
            partial(self.res_set, r, m, 8, 2, 223, D, 0),          # 0xAA RES 5,D
            partial(self.res_set, r, m, 8, 2, 223, E, 0),          # 0xAB RES 5,E
            partial(self.res_set, r, m, 8, 2, 223, H, 0),          # 0xAC RES 5,H
            partial(self.res_set, r, m, 8, 2, 223, L, 0),          # 0xAD RES 5,L
            partial(self.res_set, r, m, 15, 2, 223, Hd, 0),        # 0xAE RES 5,(HL)
            partial(self.res_set, r, m, 8, 2, 223, A, 0),          # 0xAF RES 5,A
            partial(self.res_set, r, m, 8, 2, 191, B, 0),          # 0xB0 RES 6,B
            partial(self.res_set, r, m, 8, 2, 191, C, 0),          # 0xB1 RES 6,C
            partial(self.res_set, r, m, 8, 2, 191, D, 0),          # 0xB2 RES 6,D
            partial(self.res_set, r, m, 8, 2, 191, E, 0),          # 0xB3 RES 6,E
            partial(self.res_set, r, m, 8, 2, 191, H, 0),          # 0xB4 RES 6,H
            partial(self.res_set, r, m, 8, 2, 191, L, 0),          # 0xB5 RES 6,L
            partial(self.res_set, r, m, 15, 2, 191, Hd, 0),        # 0xB6 RES 6,(HL)
            partial(self.res_set, r, m, 8, 2, 191, A, 0),          # 0xB7 RES 6,A
            partial(self.res_set, r, m, 8, 2, 127, B, 0),          # 0xB8 RES 7,B
            partial(self.res_set, r, m, 8, 2, 127, C, 0),          # 0xB9 RES 7,C
            partial(self.res_set, r, m, 8, 2, 127, D, 0),          # 0xBA RES 7,D
            partial(self.res_set, r, m, 8, 2, 127, E, 0),          # 0xBB RES 7,E
            partial(self.res_set, r, m, 8, 2, 127, H, 0),          # 0xBC RES 7,H
            partial(self.res_set, r, m, 8, 2, 127, L, 0),          # 0xBD RES 7,L
            partial(self.res_set, r, m, 15, 2, 127, Hd, 0),        # 0xBE RES 7,(HL)
            partial(self.res_set, r, m, 8, 2, 127, A, 0),          # 0xBF RES 7,A
            partial(self.res_set, r, m, 8, 2, 1, B, 1),            # 0xC0 SET 0,B
            partial(self.res_set, r, m, 8, 2, 1, C, 1),            # 0xC1 SET 0,C
            partial(self.res_set, r, m, 8, 2, 1, D, 1),            # 0xC2 SET 0,D
            partial(self.res_set, r, m, 8, 2, 1, E, 1),            # 0xC3 SET 0,E
            partial(self.res_set, r, m, 8, 2, 1, H, 1),            # 0xC4 SET 0,H
            partial(self.res_set, r, m, 8, 2, 1, L, 1),            # 0xC5 SET 0,L
            partial(self.res_set, r, m, 15, 2, 1, Hd, 1),          # 0xC6 SET 0,(HL)
            partial(self.res_set, r, m, 8, 2, 1, A, 1),            # 0xC7 SET 0,A
            partial(self.res_set, r, m, 8, 2, 2, B, 1),            # 0xC8 SET 1,B
            partial(self.res_set, r, m, 8, 2, 2, C, 1),            # 0xC9 SET 1,C
            partial(self.res_set, r, m, 8, 2, 2, D, 1),            # 0xCA SET 1,D
            partial(self.res_set, r, m, 8, 2, 2, E, 1),            # 0xCB SET 1,E
            partial(self.res_set, r, m, 8, 2, 2, H, 1),            # 0xCC SET 1,H
            partial(self.res_set, r, m, 8, 2, 2, L, 1),            # 0xCD SET 1,L
            partial(self.res_set, r, m, 15, 2, 2, Hd, 1),          # 0xCE SET 1,(HL)
            partial(self.res_set, r, m, 8, 2, 2, A, 1),            # 0xCF SET 1,A
            partial(self.res_set, r, m, 8, 2, 4, B, 1),            # 0xD0 SET 2,B
            partial(self.res_set, r, m, 8, 2, 4, C, 1),            # 0xD1 SET 2,C
            partial(self.res_set, r, m, 8, 2, 4, D, 1),            # 0xD2 SET 2,D
            partial(self.res_set, r, m, 8, 2, 4, E, 1),            # 0xD3 SET 2,E
            partial(self.res_set, r, m, 8, 2, 4, H, 1),            # 0xD4 SET 2,H
            partial(self.res_set, r, m, 8, 2, 4, L, 1),            # 0xD5 SET 2,L
            partial(self.res_set, r, m, 15, 2, 4, Hd, 1),          # 0xD6 SET 2,(HL)
            partial(self.res_set, r, m, 8, 2, 4, A, 1),            # 0xD7 SET 2,A
            partial(self.res_set, r, m, 8, 2, 8, B, 1),            # 0xD8 SET 3,B
            partial(self.res_set, r, m, 8, 2, 8, C, 1),            # 0xD9 SET 3,C
            partial(self.res_set, r, m, 8, 2, 8, D, 1),            # 0xDA SET 3,D
            partial(self.res_set, r, m, 8, 2, 8, E, 1),            # 0xDB SET 3,E
            partial(self.res_set, r, m, 8, 2, 8, H, 1),            # 0xDC SET 3,H
            partial(self.res_set, r, m, 8, 2, 8, L, 1),            # 0xDD SET 3,L
            partial(self.res_set, r, m, 15, 2, 8, Hd, 1),          # 0xDE SET 3,(HL)
            partial(self.res_set, r, m, 8, 2, 8, A, 1),            # 0xDF SET 3,A
            partial(self.res_set, r, m, 8, 2, 16, B, 1),           # 0xE0 SET 4,B
            partial(self.res_set, r, m, 8, 2, 16, C, 1),           # 0xE1 SET 4,C
            partial(self.res_set, r, m, 8, 2, 16, D, 1),           # 0xE2 SET 4,D
            partial(self.res_set, r, m, 8, 2, 16, E, 1),           # 0xE3 SET 4,E
            partial(self.res_set, r, m, 8, 2, 16, H, 1),           # 0xE4 SET 4,H
            partial(self.res_set, r, m, 8, 2, 16, L, 1),           # 0xE5 SET 4,L
            partial(self.res_set, r, m, 15, 2, 16, Hd, 1),         # 0xE6 SET 4,(HL)
            partial(self.res_set, r, m, 8, 2, 16, A, 1),           # 0xE7 SET 4,A
            partial(self.res_set, r, m, 8, 2, 32, B, 1),           # 0xE8 SET 5,B
            partial(self.res_set, r, m, 8, 2, 32, C, 1),           # 0xE9 SET 5,C
            partial(self.res_set, r, m, 8, 2, 32, D, 1),           # 0xEA SET 5,D
            partial(self.res_set, r, m, 8, 2, 32, E, 1),           # 0xEB SET 5,E
            partial(self.res_set, r, m, 8, 2, 32, H, 1),           # 0xEC SET 5,H
            partial(self.res_set, r, m, 8, 2, 32, L, 1),           # 0xED SET 5,L
            partial(self.res_set, r, m, 15, 2, 32, Hd, 1),         # 0xEE SET 5,(HL)
            partial(self.res_set, r, m, 8, 2, 32, A, 1),           # 0xEF SET 5,A
            partial(self.res_set, r, m, 8, 2, 64, B, 1),           # 0xF0 SET 6,B
            partial(self.res_set, r, m, 8, 2, 64, C, 1),           # 0xF1 SET 6,C
            partial(self.res_set, r, m, 8, 2, 64, D, 1),           # 0xF2 SET 6,D
            partial(self.res_set, r, m, 8, 2, 64, E, 1),           # 0xF3 SET 6,E
            partial(self.res_set, r, m, 8, 2, 64, H, 1),           # 0xF4 SET 6,H
            partial(self.res_set, r, m, 8, 2, 64, L, 1),           # 0xF5 SET 6,L
            partial(self.res_set, r, m, 15, 2, 64, Hd, 1),         # 0xF6 SET 6,(HL)
            partial(self.res_set, r, m, 8, 2, 64, A, 1),           # 0xF7 SET 6,A
            partial(self.res_set, r, m, 8, 2, 128, B, 1),          # 0xF8 SET 7,B
            partial(self.res_set, r, m, 8, 2, 128, C, 1),          # 0xF9 SET 7,C
            partial(self.res_set, r, m, 8, 2, 128, D, 1),          # 0xFA SET 7,D
            partial(self.res_set, r, m, 8, 2, 128, E, 1),          # 0xFB SET 7,E
            partial(self.res_set, r, m, 8, 2, 128, H, 1),          # 0xFC SET 7,H
            partial(self.res_set, r, m, 8, 2, 128, L, 1),          # 0xFD SET 7,L
            partial(self.res_set, r, m, 15, 2, 128, Hd, 1),        # 0xFE SET 7,(HL)
            partial(self.res_set, r, m, 8, 2, 128, A, 1),          # 0xFF SET 7,A
        ]

        self.after_ED = [
            partial(self.nop_ed, r),                               # 0x00
            partial(self.nop_ed, r),                               # 0x01
            partial(self.nop_ed, r),                               # 0x02
            partial(self.nop_ed, r),                               # 0x03
            partial(self.nop_ed, r),                               # 0x04
            partial(self.nop_ed, r),                               # 0x05
            partial(self.nop_ed, r),                               # 0x06
            partial(self.nop_ed, r),                               # 0x07
            partial(self.nop_ed, r),                               # 0x08
            partial(self.nop_ed, r),                               # 0x09
            partial(self.nop_ed, r),                               # 0x0A
            partial(self.nop_ed, r),                               # 0x0B
            partial(self.nop_ed, r),                               # 0x0C
            partial(self.nop_ed, r),                               # 0x0D
            partial(self.nop_ed, r),                               # 0x0E
            partial(self.nop_ed, r),                               # 0x0F
            partial(self.nop_ed, r),                               # 0x10
            partial(self.nop_ed, r),                               # 0x11
            partial(self.nop_ed, r),                               # 0x12
            partial(self.nop_ed, r),                               # 0x13
            partial(self.nop_ed, r),                               # 0x14
            partial(self.nop_ed, r),                               # 0x15
            partial(self.nop_ed, r),                               # 0x16
            partial(self.nop_ed, r),                               # 0x17
            partial(self.nop_ed, r),                               # 0x18
            partial(self.nop_ed, r),                               # 0x19
            partial(self.nop_ed, r),                               # 0x1A
            partial(self.nop_ed, r),                               # 0x1B
            partial(self.nop_ed, r),                               # 0x1C
            partial(self.nop_ed, r),                               # 0x1D
            partial(self.nop_ed, r),                               # 0x1E
            partial(self.nop_ed, r),                               # 0x1F
            partial(self.nop_ed, r),                               # 0x20
            partial(self.nop_ed, r),                               # 0x21
            partial(self.nop_ed, r),                               # 0x22
            partial(self.nop_ed, r),                               # 0x23
            partial(self.nop_ed, r),                               # 0x24
            partial(self.nop_ed, r),                               # 0x25
            partial(self.nop_ed, r),                               # 0x26
            partial(self.nop_ed, r),                               # 0x27
            partial(self.nop_ed, r),                               # 0x28
            partial(self.nop_ed, r),                               # 0x29
            partial(self.nop_ed, r),                               # 0x2A
            partial(self.nop_ed, r),                               # 0x2B
            partial(self.nop_ed, r),                               # 0x2C
            partial(self.nop_ed, r),                               # 0x2D
            partial(self.nop_ed, r),                               # 0x2E
            partial(self.nop_ed, r),                               # 0x2F
            partial(self.nop_ed, r),                               # 0x30
            partial(self.nop_ed, r),                               # 0x31
            partial(self.nop_ed, r),                               # 0x32
            partial(self.nop_ed, r),                               # 0x33
            partial(self.nop_ed, r),                               # 0x34
            partial(self.nop_ed, r),                               # 0x35
            partial(self.nop_ed, r),                               # 0x36
            partial(self.nop_ed, r),                               # 0x37
            partial(self.nop_ed, r),                               # 0x38
            partial(self.nop_ed, r),                               # 0x39
            partial(self.nop_ed, r),                               # 0x3A
            partial(self.nop_ed, r),                               # 0x3B
            partial(self.nop_ed, r),                               # 0x3C
            partial(self.nop_ed, r),                               # 0x3D
            partial(self.nop_ed, r),                               # 0x3E
            partial(self.nop_ed, r),                               # 0x3F
            partial(self.in_c, r, B),                              # 0x40 IN B,(C)
            partial(self.outc, r, B),                              # 0x41 OUT (C),B
            partial(self.sbc_hl, r, B),                            # 0x42 SBC HL,BC
            partial(self.ld16addr, r, m, 20, 4, B, 1),             # 0x43 LD (nn),BC
            partial(self.neg, r),                                  # 0x44 NEG
            partial(self.reti, r, m),                              # 0x45 RETN
            partial(self.im, r, 0),                                # 0x46 IM 0
            partial(self.ld8, r, m, 9, 2, I, A),                   # 0x47 LD I,A
            partial(self.in_c, r, C),                              # 0x48 IN C,(C)
            partial(self.outc, r, C),                              # 0x49 OUT (C),C
            partial(self.adc_hl, r, B),                            # 0x4A ADC HL,BC
            partial(self.ld16addr, r, m, 20, 4, B, 0),             # 0x4B LD BC,(nn)
            partial(self.neg, r),                                  # 0x4C NEG
            partial(self.reti, r, m),                              # 0x4D RETI
            partial(self.im, r, 0),                                # 0x4E IM 0
            partial(self.ld8, r, m, 9, 2, R, A),                   # 0x4F LD R,A
            partial(self.in_c, r, D),                              # 0x50 IN D,(C)
            partial(self.outc, r, D),                              # 0x51 OUT (C),D
            partial(self.sbc_hl, r, D),                            # 0x52 SBC HL,DE
            partial(self.ld16addr, r, m, 20, 4, D, 1),             # 0x53 LD (nn),DE
            partial(self.neg, r),                                  # 0x54 NEG
            partial(self.reti, r, m),                              # 0x55 RETN
            partial(self.im, r, 1),                                # 0x56 IM 1
            partial(self.ld8, r, m, 9, 2, A, I),                   # 0x57 LD A,I
            partial(self.in_c, r, E),                              # 0x58 IN E,(C)
            partial(self.outc, r, E),                              # 0x59 OUT (C),E
            partial(self.adc_hl, r, D),                            # 0x5A ADC HL,DE
            partial(self.ld16addr, r, m, 20, 4, D, 0),             # 0x5B LD DE,(nn)
            partial(self.neg, r),                                  # 0x5C NEG
            partial(self.reti, r, m),                              # 0x5D RETN
            partial(self.im, r, 2),                                # 0x5E IM 2
            partial(self.ld8, r, m, 9, 2, A, R),                   # 0x5F LD A,R
            partial(self.in_c, r, H),                              # 0x60 IN H,(C)
            partial(self.outc, r, H),                              # 0x61 OUT (C),H
            partial(self.sbc_hl, r, H),                            # 0x62 SBC HL,HL
            partial(self.ld16addr, r, m, 20, 4, H, 1),             # 0x63 LD (nn),HL
            partial(self.neg, r),                                  # 0x64 NEG
            partial(self.reti, r, m),                              # 0x65 RETN
            partial(self.im, r, 0),                                # 0x66 IM 0
            partial(self.rrd, r, m),                               # 0x67 RRD
            partial(self.in_c, r, L),                              # 0x68 IN L,(C)
            partial(self.outc, r, L),                              # 0x69 OUT (C),L
            partial(self.adc_hl, r, H),                            # 0x6A ADC HL,HL
            partial(self.ld16addr, r, m, 20, 4, H, 0),             # 0x6B LD HL,(nn)
            partial(self.neg, r),                                  # 0x6C NEG
            partial(self.reti, r, m),                              # 0x6D RETN
            partial(self.im, r, 0),                                # 0x6E IM 0
            partial(self.rld, r, m),                               # 0x6F RLD
            partial(self.in_c, r, F),                              # 0x70 IN F,(C)
            partial(self.outc, r, -1),                             # 0x71 OUT (C),0
            partial(self.sbc_hl, r, SP),                           # 0x72 SBC HL,SP
            partial(self.ld16addr, r, m, 20, 4, SP, 1),            # 0x73 LD (nn),SP
            partial(self.neg, r),                                  # 0x74 NEG
            partial(self.reti, r, m),                              # 0x75 RETN
            partial(self.im, r, 1),                                # 0x76 IM 1
            partial(self.nop_ed, r),                               # 0x77
            partial(self.in_c, r, A),                              # 0x78 IN A,(C)
            partial(self.outc, r, A),                              # 0x79 OUT (C),A
            partial(self.adc_hl, r, SP),                           # 0x7A ADC HL,SP
            partial(self.ld16addr, r, m, 20, 4, SP, 0),            # 0x7B LD SP,(nn)
            partial(self.neg, r),                                  # 0x7C NEG
            partial(self.reti, r, m),                              # 0x7D RETN
            partial(self.im, r, 2),                                # 0x7E IM 2
            partial(self.nop_ed, r),                               # 0x7F
            partial(self.nop_ed, r),                               # 0x80
            partial(self.nop_ed, r),                               # 0x81
            partial(self.nop_ed, r),                               # 0x82
            partial(self.nop_ed, r),                               # 0x83
            partial(self.nop_ed, r),                               # 0x84
            partial(self.nop_ed, r),                               # 0x85
            partial(self.nop_ed, r),                               # 0x86
            partial(self.nop_ed, r),                               # 0x87
            partial(self.nop_ed, r),                               # 0x88
            partial(self.nop_ed, r),                               # 0x89
            partial(self.nop_ed, r),                               # 0x8A
            partial(self.nop_ed, r),                               # 0x8B
            partial(self.nop_ed, r),                               # 0x8C
            partial(self.nop_ed, r),                               # 0x8D
            partial(self.nop_ed, r),                               # 0x8E
            partial(self.nop_ed, r),                               # 0x8F
            partial(self.nop_ed, r),                               # 0x90
            partial(self.nop_ed, r),                               # 0x91
            partial(self.nop_ed, r),                               # 0x92
            partial(self.nop_ed, r),                               # 0x93
            partial(self.nop_ed, r),                               # 0x94
            partial(self.nop_ed, r),                               # 0x95
            partial(self.nop_ed, r),                               # 0x96
            partial(self.nop_ed, r),                               # 0x97
            partial(self.nop_ed, r),                               # 0x98
            partial(self.nop_ed, r),                               # 0x99
            partial(self.nop_ed, r),                               # 0x9A
            partial(self.nop_ed, r),                               # 0x9B
            partial(self.nop_ed, r),                               # 0x9C
            partial(self.nop_ed, r),                               # 0x9D
            partial(self.nop_ed, r),                               # 0x9E
            partial(self.nop_ed, r),                               # 0x9F
            partial(self.ldi, r, m, 1, 0),                         # 0xA0 LDI
            partial(self.cpi, r, m, 1, 0),                         # 0xA1 CPI
            partial(self.ini, r, m, 1, 0),                         # 0xA2 INI
            partial(self.outi, r, m, 1, 0),                        # 0xA3 OUTI
            partial(self.nop_ed, r),                               # 0xA4
            partial(self.nop_ed, r),                               # 0xA5
            partial(self.nop_ed, r),                               # 0xA6
            partial(self.nop_ed, r),                               # 0xA7
            partial(self.ldi, r, m, -1, 0),                        # 0xA8 LDD
            partial(self.cpi, r, m, -1, 0),                        # 0xA9 CPD
            partial(self.ini, r, m, -1, 0),                        # 0xAA IND
            partial(self.outi, r, m, -1, 0),                       # 0xAB OUTD
            partial(self.nop_ed, r),                               # 0xAC
            partial(self.nop_ed, r),                               # 0xAD
            partial(self.nop_ed, r),                               # 0xAE
            partial(self.nop_ed, r),                               # 0xAF
            partial(self.ldi, r, m, 1, 1),                         # 0xB0 LDIR
            partial(self.cpi, r, m, 1, 1),                         # 0xB1 CPIR
            partial(self.ini, r, m, 1, 1),                         # 0xB2 INIR
            partial(self.outi, r, m, 1, 1),                        # 0xB3 OTIR
            partial(self.nop_ed, r),                               # 0xB4
            partial(self.nop_ed, r),                               # 0xB5
            partial(self.nop_ed, r),                               # 0xB6
            partial(self.nop_ed, r),                               # 0xB7
            partial(self.ldi, r, m, -1, 1),                        # 0xB8 LDDR
            partial(self.cpi, r, m, -1, 1),                        # 0xB9 CPDR
            partial(self.ini, r, m, -1, 1),                        # 0xBA INDR
            partial(self.outi, r, m, -1, 1),                       # 0xBB OTDR
            partial(self.nop_ed, r),                               # 0xBC
            partial(self.nop_ed, r),                               # 0xBD
            partial(self.nop_ed, r),                               # 0xBE
            partial(self.nop_ed, r),                               # 0xBF
            partial(self.nop_ed, r),                               # 0xC0
            partial(self.nop_ed, r),                               # 0xC1
            partial(self.nop_ed, r),                               # 0xC2
            partial(self.nop_ed, r),                               # 0xC3
            partial(self.nop_ed, r),                               # 0xC4
            partial(self.nop_ed, r),                               # 0xC5
            partial(self.nop_ed, r),                               # 0xC6
            partial(self.nop_ed, r),                               # 0xC7
            partial(self.nop_ed, r),                               # 0xC8
            partial(self.nop_ed, r),                               # 0xC9
            partial(self.nop_ed, r),                               # 0xCA
            partial(self.nop_ed, r),                               # 0xCB
            partial(self.nop_ed, r),                               # 0xCC
            partial(self.nop_ed, r),                               # 0xCD
            partial(self.nop_ed, r),                               # 0xCE
            partial(self.nop_ed, r),                               # 0xCF
            partial(self.nop_ed, r),                               # 0xD0
            partial(self.nop_ed, r),                               # 0xD1
            partial(self.nop_ed, r),                               # 0xD2
            partial(self.nop_ed, r),                               # 0xD3
            partial(self.nop_ed, r),                               # 0xD4
            partial(self.nop_ed, r),                               # 0xD5
            partial(self.nop_ed, r),                               # 0xD6
            partial(self.nop_ed, r),                               # 0xD7
            partial(self.nop_ed, r),                               # 0xD8
            partial(self.nop_ed, r),                               # 0xD9
            partial(self.nop_ed, r),                               # 0xDA
            partial(self.nop_ed, r),                               # 0xDB
            partial(self.nop_ed, r),                               # 0xDC
            partial(self.nop_ed, r),                               # 0xDD
            partial(self.nop_ed, r),                               # 0xDE
            partial(self.nop_ed, r),                               # 0xDF
            partial(self.nop_ed, r),                               # 0xE0
            partial(self.nop_ed, r),                               # 0xE1
            partial(self.nop_ed, r),                               # 0xE2
            partial(self.nop_ed, r),                               # 0xE3
            partial(self.nop_ed, r),                               # 0xE4
            partial(self.nop_ed, r),                               # 0xE5
            partial(self.nop_ed, r),                               # 0xE6
            partial(self.nop_ed, r),                               # 0xE7
            partial(self.nop_ed, r),                               # 0xE8
            partial(self.nop_ed, r),                               # 0xE9
            partial(self.nop_ed, r),                               # 0xEA
            partial(self.nop_ed, r),                               # 0xEB
            partial(self.nop_ed, r),                               # 0xEC
            partial(self.nop_ed, r),                               # 0xED
            partial(self.nop_ed, r),                               # 0xEE
            partial(self.nop_ed, r),                               # 0xEF
            partial(self.nop_ed, r),                               # 0xF0
            partial(self.nop_ed, r),                               # 0xF1
            partial(self.nop_ed, r),                               # 0xF2
            partial(self.nop_ed, r),                               # 0xF3
            partial(self.nop_ed, r),                               # 0xF4
            partial(self.nop_ed, r),                               # 0xF5
            partial(self.nop_ed, r),                               # 0xF6
            partial(self.nop_ed, r),                               # 0xF7
            partial(self.nop_ed, r),                               # 0xF8
            partial(self.nop_ed, r),                               # 0xF9
            partial(self.nop_ed, r),                               # 0xFA
            partial(self.nop_ed, r),                               # 0xFB
            partial(self.nop_ed, r),                               # 0xFC
            partial(self.nop_ed, r),                               # 0xFD
            partial(self.nop_ed, r),                               # 0xFE
            partial(self.nop_ed, r),                               # 0xFF
        ]

        self.after_DD = [
            partial(self.nop_dd_fd, r),                            # 0x00
            partial(self.nop_dd_fd, r),                            # 0x01
            partial(self.nop_dd_fd, r),                            # 0x02
            partial(self.nop_dd_fd, r),                            # 0x03
            partial(self.nop_dd_fd, r),                            # 0x04
            partial(self.nop_dd_fd, r),                            # 0x05
            partial(self.nop_dd_fd, r),                            # 0x06
            partial(self.nop_dd_fd, r),                            # 0x07
            partial(self.nop_dd_fd, r),                            # 0x08
            partial(self.add16, r, 15, 2, IXh, B),                 # 0x09 ADD IX,BC
            partial(self.nop_dd_fd, r),                            # 0x0A
            partial(self.nop_dd_fd, r),                            # 0x0B
            partial(self.nop_dd_fd, r),                            # 0x0C
            partial(self.nop_dd_fd, r),                            # 0x0D
            partial(self.nop_dd_fd, r),                            # 0x0E
            partial(self.nop_dd_fd, r),                            # 0x0F
            partial(self.nop_dd_fd, r),                            # 0x10
            partial(self.nop_dd_fd, r),                            # 0x11
            partial(self.nop_dd_fd, r),                            # 0x12
            partial(self.nop_dd_fd, r),                            # 0x13
            partial(self.nop_dd_fd, r),                            # 0x14
            partial(self.nop_dd_fd, r),                            # 0x15
            partial(self.nop_dd_fd, r),                            # 0x16
            partial(self.nop_dd_fd, r),                            # 0x17
            partial(self.nop_dd_fd, r),                            # 0x18
            partial(self.add16, r, 15, 2, IXh, D),                 # 0x19 ADD IX,DE
            partial(self.nop_dd_fd, r),                            # 0x1A
            partial(self.nop_dd_fd, r),                            # 0x1B
            partial(self.nop_dd_fd, r),                            # 0x1C
            partial(self.nop_dd_fd, r),                            # 0x1D
            partial(self.nop_dd_fd, r),                            # 0x1E
            partial(self.nop_dd_fd, r),                            # 0x1F
            partial(self.nop_dd_fd, r),                            # 0x20
            partial(self.ld16, r, m, IXh),                         # 0x21 LD IX,nn
            partial(self.ld16addr, r, m, 20, 4, IXh, 1),           # 0x22 LD (nn),IX
            partial(self.inc_dec16, r, 1, IXh),                    # 0x23 INC IX
            partial(self.inc_dec8, r, m, 8, 2, 1, IXh),            # 0x24 INC IXh
            partial(self.inc_dec8, r, m, 8, 2, -1, IXh),           # 0x25 DEC IXh
            partial(self.ld8, r, m, 11, 3, IXh),                   # 0x26 LD IXh,n
            partial(self.nop_dd_fd, r),                            # 0x27
            partial(self.nop_dd_fd, r),                            # 0x28
            partial(self.add16, r, 15, 2, IXh, IXh),               # 0x29 ADD IX,IX
            partial(self.ld16addr, r, m, 20, 4, IXh, 0),           # 0x2A LD IX,(nn)
            partial(self.inc_dec16, r, -1, IXh),                   # 0x2B DEC IX
            partial(self.inc_dec8, r, m, 8, 2, 1, IXl),            # 0x2C INC IXl
            partial(self.inc_dec8, r, m, 8, 2, -1, IXl),           # 0x2D DEC IXl
            partial(self.ld8, r, m, 11, 3, IXl),                   # 0x2E LD IXl,n
            partial(self.nop_dd_fd, r),                            # 0x2F
            partial(self.nop_dd_fd, r),                            # 0x30
            partial(self.nop_dd_fd, r),                            # 0x31
            partial(self.nop_dd_fd, r),                            # 0x32
            partial(self.nop_dd_fd, r),                            # 0x33
            partial(self.inc_dec8, r, m, 23, 3, 1, Xd),            # 0x34 INC (IX+d)
            partial(self.inc_dec8, r, m, 23, 3, -1, Xd),           # 0x35 DEC (IX+d)
            partial(self.ld8, r, m, 19, 4, Xd),                    # 0x36 LD (IX+d),n
            partial(self.nop_dd_fd, r),                            # 0x37
            partial(self.nop_dd_fd, r),                            # 0x38
            partial(self.add16, r, 15, 2, IXh, SP),                # 0x39 ADD IX,SP
            partial(self.nop_dd_fd, r),                            # 0x3A
            partial(self.nop_dd_fd, r),                            # 0x3B
            partial(self.nop_dd_fd, r),                            # 0x3C
            partial(self.nop_dd_fd, r),                            # 0x3D
            partial(self.nop_dd_fd, r),                            # 0x3E
            partial(self.nop_dd_fd, r),                            # 0x3F
            partial(self.nop_dd_fd, r),                            # 0x40
            partial(self.nop_dd_fd, r),                            # 0x41
            partial(self.nop_dd_fd, r),                            # 0x42
            partial(self.nop_dd_fd, r),                            # 0x43
            partial(self.ld8, r, m, 8, 2, B, IXh),                 # 0x44 LD B,IXh
            partial(self.ld8, r, m, 8, 2, B, IXl),                 # 0x45 LD B,IXl
            partial(self.ld8, r, m, 19, 3, B, Xd),                 # 0x46 LD B,(IX+d)
            partial(self.nop_dd_fd, r),                            # 0x47
            partial(self.nop_dd_fd, r),                            # 0x48
            partial(self.nop_dd_fd, r),                            # 0x49
            partial(self.nop_dd_fd, r),                            # 0x4A
            partial(self.nop_dd_fd, r),                            # 0x4B
            partial(self.ld8, r, m, 8, 2, C, IXh),                 # 0x4C LD C,IXh
            partial(self.ld8, r, m, 8, 2, C, IXl),                 # 0x4D LD C,IXl
            partial(self.ld8, r, m, 19, 3, C, Xd),                 # 0x4E LD C,(IX+d)
            partial(self.nop_dd_fd, r),                            # 0x4F
            partial(self.nop_dd_fd, r),                            # 0x50
            partial(self.nop_dd_fd, r),                            # 0x51
            partial(self.nop_dd_fd, r),                            # 0x52
            partial(self.nop_dd_fd, r),                            # 0x53
            partial(self.ld8, r, m, 8, 2, D, IXh),                 # 0x54 LD D,IXh
            partial(self.ld8, r, m, 8, 2, D, IXl),                 # 0x55 LD D,IXl
            partial(self.ld8, r, m, 19, 3, D, Xd),                 # 0x56 LD D,(IX+d)
            partial(self.nop_dd_fd, r),                            # 0x57
            partial(self.nop_dd_fd, r),                            # 0x58
            partial(self.nop_dd_fd, r),                            # 0x59
            partial(self.nop_dd_fd, r),                            # 0x5A
            partial(self.nop_dd_fd, r),                            # 0x5B
            partial(self.ld8, r, m, 8, 2, E, IXh),                 # 0x5C LD E,IXh
            partial(self.ld8, r, m, 8, 2, E, IXl),                 # 0x5D LD E,IXl
            partial(self.ld8, r, m, 19, 3, E, Xd),                 # 0x5E LD E,(IX+d)
            partial(self.nop_dd_fd, r),                            # 0x5F
            partial(self.ld8, r, m, 8, 2, IXh, B),                 # 0x60 LD IXh,B
            partial(self.ld8, r, m, 8, 2, IXh, C),                 # 0x61 LD IXh,C
            partial(self.ld8, r, m, 8, 2, IXh, D),                 # 0x62 LD IXh,D
            partial(self.ld8, r, m, 8, 2, IXh, E),                 # 0x63 LD IXh,E
            partial(self.ld8, r, m, 8, 2, IXh, IXh),               # 0x64 LD IXh,IXh
            partial(self.ld8, r, m, 8, 2, IXh, IXl),               # 0x65 LD IXh,IXl
            partial(self.ld8, r, m, 19, 3, H, Xd),                 # 0x66 LD H,(IX+d)
            partial(self.ld8, r, m, 8, 2, IXh, A),                 # 0x67 LD IXh,A
            partial(self.ld8, r, m, 8, 2, IXl, B),                 # 0x68 LD IXl,B
            partial(self.ld8, r, m, 8, 2, IXl, C),                 # 0x69 LD IXl,C
            partial(self.ld8, r, m, 8, 2, IXl, D),                 # 0x6A LD IXl,D
            partial(self.ld8, r, m, 8, 2, IXl, E),                 # 0x6B LD IXl,E
            partial(self.ld8, r, m, 8, 2, IXl, IXh),               # 0x6C LD IXl,IXh
            partial(self.ld8, r, m, 8, 2, IXl, IXl),               # 0x6D LD IXl,IXl
            partial(self.ld8, r, m, 19, 3, L, Xd),                 # 0x6E LD L,(IX+d)
            partial(self.ld8, r, m, 8, 2, IXl, A),                 # 0x6F LD IXl,A
            partial(self.ld8, r, m, 19, 3, Xd, B),                 # 0x70 LD (IX+d),B
            partial(self.ld8, r, m, 19, 3, Xd, C),                 # 0x71 LD (IX+d),C
            partial(self.ld8, r, m, 19, 3, Xd, D),                 # 0x72 LD (IX+d),D
            partial(self.ld8, r, m, 19, 3, Xd, E),                 # 0x73 LD (IX+d),E
            partial(self.ld8, r, m, 19, 3, Xd, H),                 # 0x74 LD (IX+d),H
            partial(self.ld8, r, m, 19, 3, Xd, L),                 # 0x75 LD (IX+d),L
            partial(self.nop_dd_fd, r),                            # 0x76
            partial(self.ld8, r, m, 19, 3, Xd, A),                 # 0x77 LD (IX+d),A
            partial(self.nop_dd_fd, r),                            # 0x78
            partial(self.nop_dd_fd, r),                            # 0x79
            partial(self.nop_dd_fd, r),                            # 0x7A
            partial(self.nop_dd_fd, r),                            # 0x7B
            partial(self.ld8, r, m, 8, 2, A, IXh),                 # 0x7C LD A,IXh
            partial(self.ld8, r, m, 8, 2, A, IXl),                 # 0x7D LD A,IXl
            partial(self.ld8, r, m, 19, 3, A, Xd),                 # 0x7E LD A,(IX+d)
            partial(self.nop_dd_fd, r),                            # 0x7F
            partial(self.nop_dd_fd, r),                            # 0x80
            partial(self.nop_dd_fd, r),                            # 0x81
            partial(self.nop_dd_fd, r),                            # 0x82
            partial(self.nop_dd_fd, r),                            # 0x83
            partial(self.add_a, r, m, 8, 2, IXh),                  # 0x84 ADD A,IXh
            partial(self.add_a, r, m, 8, 2, IXl),                  # 0x85 ADD A,IXl
            partial(self.add_a, r, m, 19, 3, Xd),                  # 0x86 ADD A,(IX+d)
            partial(self.nop_dd_fd, r),                            # 0x87
            partial(self.nop_dd_fd, r),                            # 0x88
            partial(self.nop_dd_fd, r),                            # 0x89
            partial(self.nop_dd_fd, r),                            # 0x8A
            partial(self.nop_dd_fd, r),                            # 0x8B
            partial(self.adc_a, r, m, 8, 2, IXh),                  # 0x8C ADC A,IXh
            partial(self.adc_a, r, m, 8, 2, IXl),                  # 0x8D ADC A,IXl
            partial(self.adc_a, r, m, 19, 3, Xd),                  # 0x8E ADC A,(IX+d)
            partial(self.nop_dd_fd, r),                            # 0x8F
            partial(self.nop_dd_fd, r),                            # 0x90
            partial(self.nop_dd_fd, r),                            # 0x91
            partial(self.nop_dd_fd, r),                            # 0x92
            partial(self.nop_dd_fd, r),                            # 0x93
            partial(self.sub, r, m, 8, 2, IXh),                    # 0x94 SUB IXh
            partial(self.sub, r, m, 8, 2, IXl),                    # 0x95 SUB IXl
            partial(self.sub, r, m, 19, 3, Xd),                    # 0x96 SUB (IX+d)
            partial(self.nop_dd_fd, r),                            # 0x97
            partial(self.nop_dd_fd, r),                            # 0x98
            partial(self.nop_dd_fd, r),                            # 0x99
            partial(self.nop_dd_fd, r),                            # 0x9A
            partial(self.nop_dd_fd, r),                            # 0x9B
            partial(self.sbc_a, r, m, 8, 2, IXh),                  # 0x9C SBC A,IXh
            partial(self.sbc_a, r, m, 8, 2, IXl),                  # 0x9D SBC A,IXl
            partial(self.sbc_a, r, m, 19, 3, Xd),                  # 0x9E SBC A,(IX+d)
            partial(self.nop_dd_fd, r),                            # 0x9F
            partial(self.nop_dd_fd, r),                            # 0xA0
            partial(self.nop_dd_fd, r),                            # 0xA1
            partial(self.nop_dd_fd, r),                            # 0xA2
            partial(self.nop_dd_fd, r),                            # 0xA3
            partial(self.anda, r, m, 8, 2, IXh),                   # 0xA4 AND IXh
            partial(self.anda, r, m, 8, 2, IXl),                   # 0xA5 AND IXl
            partial(self.anda, r, m, 19, 3, Xd),                   # 0xA6 AND (IX+d)
            partial(self.nop_dd_fd, r),                            # 0xA7
            partial(self.nop_dd_fd, r),                            # 0xA8
            partial(self.nop_dd_fd, r),                            # 0xA9
            partial(self.nop_dd_fd, r),                            # 0xAA
            partial(self.nop_dd_fd, r),                            # 0xAB
            partial(self.xor, r, m, 8, 2, IXh),                    # 0xAC XOR IXh
            partial(self.xor, r, m, 8, 2, IXl),                    # 0xAD XOR IXl
            partial(self.xor, r, m, 19, 3, Xd),                    # 0xAE XOR (IX+d)
            partial(self.nop_dd_fd, r),                            # 0xAF
            partial(self.nop_dd_fd, r),                            # 0xB0
            partial(self.nop_dd_fd, r),                            # 0xB1
            partial(self.nop_dd_fd, r),                            # 0xB2
            partial(self.nop_dd_fd, r),                            # 0xB3
            partial(self.ora, r, m, 8, 2, IXh),                    # 0xB4 OR IXh
            partial(self.ora, r, m, 8, 2, IXl),                    # 0xB5 OR IXl
            partial(self.ora, r, m, 19, 3, Xd),                    # 0xB6 OR (IX+d)
            partial(self.nop_dd_fd, r),                            # 0xB7
            partial(self.nop_dd_fd, r),                            # 0xB8
            partial(self.nop_dd_fd, r),                            # 0xB9
            partial(self.nop_dd_fd, r),                            # 0xBA
            partial(self.nop_dd_fd, r),                            # 0xBB
            partial(self.cp, r, m, 8, 2, IXh),                     # 0xBC CP IXh
            partial(self.cp, r, m, 8, 2, IXl),                     # 0xBD CP IXl
            partial(self.cp, r, m, 19, 3, Xd),                     # 0xBE CP (IX+d)
            partial(self.nop_dd_fd, r),                            # 0xBF
            partial(self.nop_dd_fd, r),                            # 0xC0
            partial(self.nop_dd_fd, r),                            # 0xC1
            partial(self.nop_dd_fd, r),                            # 0xC2
            partial(self.nop_dd_fd, r),                            # 0xC3
            partial(self.nop_dd_fd, r),                            # 0xC4
            partial(self.nop_dd_fd, r),                            # 0xC5
            partial(self.nop_dd_fd, r),                            # 0xC6
            partial(self.nop_dd_fd, r),                            # 0xC7
            partial(self.nop_dd_fd, r),                            # 0xC8
            partial(self.nop_dd_fd, r),                            # 0xC9
            partial(self.nop_dd_fd, r),                            # 0xCA
            None,                                                  # 0xCB DDCB prefix
            partial(self.nop_dd_fd, r),                            # 0xCC
            partial(self.nop_dd_fd, r),                            # 0xCD
            partial(self.nop_dd_fd, r),                            # 0xCE
            partial(self.nop_dd_fd, r),                            # 0xCF
            partial(self.nop_dd_fd, r),                            # 0xD0
            partial(self.nop_dd_fd, r),                            # 0xD1
            partial(self.nop_dd_fd, r),                            # 0xD2
            partial(self.nop_dd_fd, r),                            # 0xD3
            partial(self.nop_dd_fd, r),                            # 0xD4
            partial(self.nop_dd_fd, r),                            # 0xD5
            partial(self.nop_dd_fd, r),                            # 0xD6
            partial(self.nop_dd_fd, r),                            # 0xD7
            partial(self.nop_dd_fd, r),                            # 0xD8
            partial(self.nop_dd_fd, r),                            # 0xD9
            partial(self.nop_dd_fd, r),                            # 0xDA
            partial(self.nop_dd_fd, r),                            # 0xDB
            partial(self.nop_dd_fd, r),                            # 0xDC
            partial(self.nop_dd_fd, r),                            # 0xDD
            partial(self.nop_dd_fd, r),                            # 0xDE
            partial(self.nop_dd_fd, r),                            # 0xDF
            partial(self.nop_dd_fd, r),                            # 0xE0
            partial(self.pop, r, m, IXh),                          # 0xE1 POP IX
            partial(self.nop_dd_fd, r),                            # 0xE2
            partial(self.ex_sp, r, m, IXh),                        # 0xE3 EX (SP),IX
            partial(self.nop_dd_fd, r),                            # 0xE4
            partial(self.push, r, m, IXh),                         # 0xE5 PUSH IX
            partial(self.nop_dd_fd, r),                            # 0xE6
            partial(self.nop_dd_fd, r),                            # 0xE7
            partial(self.nop_dd_fd, r),                            # 0xE8
            partial(self.jp, r, m, 0, IXh),                        # 0xE9 JP (IX)
            partial(self.nop_dd_fd, r),                            # 0xEA
            partial(self.nop_dd_fd, r),                            # 0xEB
            partial(self.nop_dd_fd, r),                            # 0xEC
            partial(self.nop_dd_fd, r),                            # 0xED
            partial(self.nop_dd_fd, r),                            # 0xEE
            partial(self.nop_dd_fd, r),                            # 0xEF
            partial(self.nop_dd_fd, r),                            # 0xF0
            partial(self.nop_dd_fd, r),                            # 0xF1
            partial(self.nop_dd_fd, r),                            # 0xF2
            partial(self.nop_dd_fd, r),                            # 0xF3
            partial(self.nop_dd_fd, r),                            # 0xF4
            partial(self.nop_dd_fd, r),                            # 0xF5
            partial(self.nop_dd_fd, r),                            # 0xF6
            partial(self.nop_dd_fd, r),                            # 0xF7
            partial(self.nop_dd_fd, r),                            # 0xF8
            partial(self.ldsprr, r, IXh),                          # 0xF9 LD SP,IX
            partial(self.nop_dd_fd, r),                            # 0xFA
            partial(self.nop_dd_fd, r),                            # 0xFB
            partial(self.nop_dd_fd, r),                            # 0xFC
            partial(self.nop_dd_fd, r),                            # 0xFD
            partial(self.nop_dd_fd, r),                            # 0xFE
            partial(self.nop_dd_fd, r),                            # 0xFF
        ]

        self.after_DDCB = [
            partial(self.rotate, r, m, 23, 4, 128, RLC, Xd, 1, B), # 0x00 RLC (IX+d),B
            partial(self.rotate, r, m, 23, 4, 128, RLC, Xd, 1, C), # 0x01 RLC (IX+d),C
            partial(self.rotate, r, m, 23, 4, 128, RLC, Xd, 1, D), # 0x02 RLC (IX+d),D
            partial(self.rotate, r, m, 23, 4, 128, RLC, Xd, 1, E), # 0x03 RLC (IX+d),E
            partial(self.rotate, r, m, 23, 4, 128, RLC, Xd, 1, H), # 0x04 RLC (IX+d),H
            partial(self.rotate, r, m, 23, 4, 128, RLC, Xd, 1, L), # 0x05 RLC (IX+d),L
            partial(self.rotate, r, m, 23, 4, 128, RLC, Xd, 1),    # 0x06 RLC (IX+d)
            partial(self.rotate, r, m, 23, 4, 128, RLC, Xd, 1, A), # 0x07 RLC (IX+d),A
            partial(self.rotate, r, m, 23, 4, 1, RRC, Xd, 1, B),   # 0x08 RRC (IX+d),B
            partial(self.rotate, r, m, 23, 4, 1, RRC, Xd, 1, C),   # 0x09 RRC (IX+d),C
            partial(self.rotate, r, m, 23, 4, 1, RRC, Xd, 1, D),   # 0x0A RRC (IX+d),D
            partial(self.rotate, r, m, 23, 4, 1, RRC, Xd, 1, E),   # 0x0B RRC (IX+d),E
            partial(self.rotate, r, m, 23, 4, 1, RRC, Xd, 1, H),   # 0x0C RRC (IX+d),H
            partial(self.rotate, r, m, 23, 4, 1, RRC, Xd, 1, L),   # 0x0D RRC (IX+d),L
            partial(self.rotate, r, m, 23, 4, 1, RRC, Xd, 1),      # 0x0E RRC (IX+d)
            partial(self.rotate, r, m, 23, 4, 1, RRC, Xd, 1, A),   # 0x0F RRC (IX+d),A
            partial(self.rotate, r, m, 23, 4, 128, RL, Xd, 0, B),  # 0x10 RL (IX+d),B
            partial(self.rotate, r, m, 23, 4, 128, RL, Xd, 0, C),  # 0x11 RL (IX+d),C
            partial(self.rotate, r, m, 23, 4, 128, RL, Xd, 0, D),  # 0x12 RL (IX+d),D
            partial(self.rotate, r, m, 23, 4, 128, RL, Xd, 0, E),  # 0x13 RL (IX+d),E
            partial(self.rotate, r, m, 23, 4, 128, RL, Xd, 0, H),  # 0x14 RL (IX+d),H
            partial(self.rotate, r, m, 23, 4, 128, RL, Xd, 0, L),  # 0x15 RL (IX+d),L
            partial(self.rotate, r, m, 23, 4, 128, RL, Xd),        # 0x16 RL (IX+d)
            partial(self.rotate, r, m, 23, 4, 128, RL, Xd, 0, A),  # 0x17 RL (IX+d),A
            partial(self.rotate, r, m, 23, 4, 1, RR, Xd, 0, B),    # 0x18 RR (IX+d),B
            partial(self.rotate, r, m, 23, 4, 1, RR, Xd, 0, C),    # 0x19 RR (IX+d),C
            partial(self.rotate, r, m, 23, 4, 1, RR, Xd, 0, D),    # 0x1A RR (IX+d),D
            partial(self.rotate, r, m, 23, 4, 1, RR, Xd, 0, E),    # 0x1B RR (IX+d),E
            partial(self.rotate, r, m, 23, 4, 1, RR, Xd, 0, H),    # 0x1C RR (IX+d),H
            partial(self.rotate, r, m, 23, 4, 1, RR, Xd, 0, L),    # 0x1D RR (IX+d),L
            partial(self.rotate, r, m, 23, 4, 1, RR, Xd),          # 0x1E RR (IX+d)
            partial(self.rotate, r, m, 23, 4, 1, RR, Xd, 0, A),    # 0x1F RR (IX+d),A
            partial(self.shift, r, m, 23, 4, SLA, 128, Xd, B),     # 0x20 SLA (IX+d),B
            partial(self.shift, r, m, 23, 4, SLA, 128, Xd, C),     # 0x21 SLA (IX+d),C
            partial(self.shift, r, m, 23, 4, SLA, 128, Xd, D),     # 0x22 SLA (IX+d),D
            partial(self.shift, r, m, 23, 4, SLA, 128, Xd, E),     # 0x23 SLA (IX+d),E
            partial(self.shift, r, m, 23, 4, SLA, 128, Xd, H),     # 0x24 SLA (IX+d),H
            partial(self.shift, r, m, 23, 4, SLA, 128, Xd, L),     # 0x25 SLA (IX+d),L
            partial(self.shift, r, m, 23, 4, SLA, 128, Xd),        # 0x26 SLA (IX+d)
            partial(self.shift, r, m, 23, 4, SLA, 128, Xd, A),     # 0x27 SLA (IX+d),A
            partial(self.shift, r, m, 23, 4, SRA, 1, Xd, B),       # 0x28 SRA (IX+d),B
            partial(self.shift, r, m, 23, 4, SRA, 1, Xd, C),       # 0x29 SRA (IX+d),C
            partial(self.shift, r, m, 23, 4, SRA, 1, Xd, D),       # 0x2A SRA (IX+d),D
            partial(self.shift, r, m, 23, 4, SRA, 1, Xd, E),       # 0x2B SRA (IX+d),E
            partial(self.shift, r, m, 23, 4, SRA, 1, Xd, H),       # 0x2C SRA (IX+d),H
            partial(self.shift, r, m, 23, 4, SRA, 1, Xd, L),       # 0x2D SRA (IX+d),L
            partial(self.shift, r, m, 23, 4, SRA, 1, Xd),          # 0x2E SRA (IX+d)
            partial(self.shift, r, m, 23, 4, SRA, 1, Xd, A),       # 0x2F SRA (IX+d),A
            partial(self.shift, r, m, 23, 4, SLL, 128, Xd, B),     # 0x30 SLL (IX+d),B
            partial(self.shift, r, m, 23, 4, SLL, 128, Xd, C),     # 0x31 SLL (IX+d),C
            partial(self.shift, r, m, 23, 4, SLL, 128, Xd, D),     # 0x32 SLL (IX+d),D
            partial(self.shift, r, m, 23, 4, SLL, 128, Xd, E),     # 0x33 SLL (IX+d),E
            partial(self.shift, r, m, 23, 4, SLL, 128, Xd, H),     # 0x34 SLL (IX+d),H
            partial(self.shift, r, m, 23, 4, SLL, 128, Xd, L),     # 0x35 SLL (IX+d),L
            partial(self.shift, r, m, 23, 4, SLL, 128, Xd),        # 0x36 SLL (IX+d)
            partial(self.shift, r, m, 23, 4, SLL, 128, Xd, A),     # 0x37 SLL (IX+d),A
            partial(self.shift, r, m, 23, 4, SRL, 1, Xd, B),       # 0x38 SRL (IX+d),B
            partial(self.shift, r, m, 23, 4, SRL, 1, Xd, C),       # 0x39 SRL (IX+d),C
            partial(self.shift, r, m, 23, 4, SRL, 1, Xd, D),       # 0x3A SRL (IX+d),D
            partial(self.shift, r, m, 23, 4, SRL, 1, Xd, E),       # 0x3B SRL (IX+d),E
            partial(self.shift, r, m, 23, 4, SRL, 1, Xd, H),       # 0x3C SRL (IX+d),H
            partial(self.shift, r, m, 23, 4, SRL, 1, Xd, L),       # 0x3D SRL (IX+d),L
            partial(self.shift, r, m, 23, 4, SRL, 1, Xd),          # 0x3E SRL (IX+d)
            partial(self.shift, r, m, 23, 4, SRL, 1, Xd, A),       # 0x3F SRL (IX+d),A
            partial(self.bit, r, m, 20, 4, 1, Xd),                 # 0x40 BIT 0,(IX+d)
            partial(self.bit, r, m, 20, 4, 1, Xd),                 # 0x41 BIT 0,(IX+d)
            partial(self.bit, r, m, 20, 4, 1, Xd),                 # 0x42 BIT 0,(IX+d)
            partial(self.bit, r, m, 20, 4, 1, Xd),                 # 0x43 BIT 0,(IX+d)
            partial(self.bit, r, m, 20, 4, 1, Xd),                 # 0x44 BIT 0,(IX+d)
            partial(self.bit, r, m, 20, 4, 1, Xd),                 # 0x45 BIT 0,(IX+d)
            partial(self.bit, r, m, 20, 4, 1, Xd),                 # 0x46 BIT 0,(IX+d)
            partial(self.bit, r, m, 20, 4, 1, Xd),                 # 0x47 BIT 0,(IX+d)
            partial(self.bit, r, m, 20, 4, 2, Xd),                 # 0x48 BIT 1,(IX+d)
            partial(self.bit, r, m, 20, 4, 2, Xd),                 # 0x49 BIT 1,(IX+d)
            partial(self.bit, r, m, 20, 4, 2, Xd),                 # 0x4A BIT 1,(IX+d)
            partial(self.bit, r, m, 20, 4, 2, Xd),                 # 0x4B BIT 1,(IX+d)
            partial(self.bit, r, m, 20, 4, 2, Xd),                 # 0x4C BIT 1,(IX+d)
            partial(self.bit, r, m, 20, 4, 2, Xd),                 # 0x4D BIT 1,(IX+d)
            partial(self.bit, r, m, 20, 4, 2, Xd),                 # 0x4E BIT 1,(IX+d)
            partial(self.bit, r, m, 20, 4, 2, Xd),                 # 0x4F BIT 1,(IX+d)
            partial(self.bit, r, m, 20, 4, 4, Xd),                 # 0x50 BIT 2,(IX+d)
            partial(self.bit, r, m, 20, 4, 4, Xd),                 # 0x51 BIT 2,(IX+d)
            partial(self.bit, r, m, 20, 4, 4, Xd),                 # 0x52 BIT 2,(IX+d)
            partial(self.bit, r, m, 20, 4, 4, Xd),                 # 0x53 BIT 2,(IX+d)
            partial(self.bit, r, m, 20, 4, 4, Xd),                 # 0x54 BIT 2,(IX+d)
            partial(self.bit, r, m, 20, 4, 4, Xd),                 # 0x55 BIT 2,(IX+d)
            partial(self.bit, r, m, 20, 4, 4, Xd),                 # 0x56 BIT 2,(IX+d)
            partial(self.bit, r, m, 20, 4, 4, Xd),                 # 0x57 BIT 2,(IX+d)
            partial(self.bit, r, m, 20, 4, 8, Xd),                 # 0x58 BIT 3,(IX+d)
            partial(self.bit, r, m, 20, 4, 8, Xd),                 # 0x59 BIT 3,(IX+d)
            partial(self.bit, r, m, 20, 4, 8, Xd),                 # 0x5A BIT 3,(IX+d)
            partial(self.bit, r, m, 20, 4, 8, Xd),                 # 0x5B BIT 3,(IX+d)
            partial(self.bit, r, m, 20, 4, 8, Xd),                 # 0x5C BIT 3,(IX+d)
            partial(self.bit, r, m, 20, 4, 8, Xd),                 # 0x5D BIT 3,(IX+d)
            partial(self.bit, r, m, 20, 4, 8, Xd),                 # 0x5E BIT 3,(IX+d)
            partial(self.bit, r, m, 20, 4, 8, Xd),                 # 0x5F BIT 3,(IX+d)
            partial(self.bit, r, m, 20, 4, 16, Xd),                # 0x60 BIT 4,(IX+d)
            partial(self.bit, r, m, 20, 4, 16, Xd),                # 0x61 BIT 4,(IX+d)
            partial(self.bit, r, m, 20, 4, 16, Xd),                # 0x62 BIT 4,(IX+d)
            partial(self.bit, r, m, 20, 4, 16, Xd),                # 0x63 BIT 4,(IX+d)
            partial(self.bit, r, m, 20, 4, 16, Xd),                # 0x64 BIT 4,(IX+d)
            partial(self.bit, r, m, 20, 4, 16, Xd),                # 0x65 BIT 4,(IX+d)
            partial(self.bit, r, m, 20, 4, 16, Xd),                # 0x66 BIT 4,(IX+d)
            partial(self.bit, r, m, 20, 4, 16, Xd),                # 0x67 BIT 4,(IX+d)
            partial(self.bit, r, m, 20, 4, 32, Xd),                # 0x68 BIT 5,(IX+d)
            partial(self.bit, r, m, 20, 4, 32, Xd),                # 0x69 BIT 5,(IX+d)
            partial(self.bit, r, m, 20, 4, 32, Xd),                # 0x6A BIT 5,(IX+d)
            partial(self.bit, r, m, 20, 4, 32, Xd),                # 0x6B BIT 5,(IX+d)
            partial(self.bit, r, m, 20, 4, 32, Xd),                # 0x6C BIT 5,(IX+d)
            partial(self.bit, r, m, 20, 4, 32, Xd),                # 0x6D BIT 5,(IX+d)
            partial(self.bit, r, m, 20, 4, 32, Xd),                # 0x6E BIT 5,(IX+d)
            partial(self.bit, r, m, 20, 4, 32, Xd),                # 0x6F BIT 5,(IX+d)
            partial(self.bit, r, m, 20, 4, 64, Xd),                # 0x70 BIT 6,(IX+d)
            partial(self.bit, r, m, 20, 4, 64, Xd),                # 0x71 BIT 6,(IX+d)
            partial(self.bit, r, m, 20, 4, 64, Xd),                # 0x72 BIT 6,(IX+d)
            partial(self.bit, r, m, 20, 4, 64, Xd),                # 0x73 BIT 6,(IX+d)
            partial(self.bit, r, m, 20, 4, 64, Xd),                # 0x74 BIT 6,(IX+d)
            partial(self.bit, r, m, 20, 4, 64, Xd),                # 0x75 BIT 6,(IX+d)
            partial(self.bit, r, m, 20, 4, 64, Xd),                # 0x76 BIT 6,(IX+d)
            partial(self.bit, r, m, 20, 4, 64, Xd),                # 0x77 BIT 6,(IX+d)
            partial(self.bit, r, m, 20, 4, 128, Xd),               # 0x78 BIT 7,(IX+d)
            partial(self.bit, r, m, 20, 4, 128, Xd),               # 0x79 BIT 7,(IX+d)
            partial(self.bit, r, m, 20, 4, 128, Xd),               # 0x7A BIT 7,(IX+d)
            partial(self.bit, r, m, 20, 4, 128, Xd),               # 0x7B BIT 7,(IX+d)
            partial(self.bit, r, m, 20, 4, 128, Xd),               # 0x7C BIT 7,(IX+d)
            partial(self.bit, r, m, 20, 4, 128, Xd),               # 0x7D BIT 7,(IX+d)
            partial(self.bit, r, m, 20, 4, 128, Xd),               # 0x7E BIT 7,(IX+d)
            partial(self.bit, r, m, 20, 4, 128, Xd),               # 0x7F BIT 7,(IX+d)
            partial(self.res_set, r, m, 23, 4, 254, Xd, 0, B),     # 0x80 RES 0,(IX+d),B
            partial(self.res_set, r, m, 23, 4, 254, Xd, 0, C),     # 0x81 RES 0,(IX+d),C
            partial(self.res_set, r, m, 23, 4, 254, Xd, 0, D),     # 0x82 RES 0,(IX+d),D
            partial(self.res_set, r, m, 23, 4, 254, Xd, 0, E),     # 0x83 RES 0,(IX+d),E
            partial(self.res_set, r, m, 23, 4, 254, Xd, 0, H),     # 0x84 RES 0,(IX+d),H
            partial(self.res_set, r, m, 23, 4, 254, Xd, 0, L),     # 0x85 RES 0,(IX+d),L
            partial(self.res_set, r, m, 23, 4, 254, Xd, 0),        # 0x86 RES 0,(IX+d)
            partial(self.res_set, r, m, 23, 4, 254, Xd, 0, A),     # 0x87 RES 0,(IX+d),A
            partial(self.res_set, r, m, 23, 4, 253, Xd, 0, B),     # 0x88 RES 1,(IX+d),B
            partial(self.res_set, r, m, 23, 4, 253, Xd, 0, C),     # 0x89 RES 1,(IX+d),C
            partial(self.res_set, r, m, 23, 4, 253, Xd, 0, D),     # 0x8A RES 1,(IX+d),D
            partial(self.res_set, r, m, 23, 4, 253, Xd, 0, E),     # 0x8B RES 1,(IX+d),E
            partial(self.res_set, r, m, 23, 4, 253, Xd, 0, H),     # 0x8C RES 1,(IX+d),H
            partial(self.res_set, r, m, 23, 4, 253, Xd, 0, L),     # 0x8D RES 1,(IX+d),L
            partial(self.res_set, r, m, 23, 4, 253, Xd, 0),        # 0x8E RES 1,(IX+d)
            partial(self.res_set, r, m, 23, 4, 253, Xd, 0, A),     # 0x8F RES 1,(IX+d),A
            partial(self.res_set, r, m, 23, 4, 251, Xd, 0, B),     # 0x90 RES 2,(IX+d),B
            partial(self.res_set, r, m, 23, 4, 251, Xd, 0, C),     # 0x91 RES 2,(IX+d),C
            partial(self.res_set, r, m, 23, 4, 251, Xd, 0, D),     # 0x92 RES 2,(IX+d),D
            partial(self.res_set, r, m, 23, 4, 251, Xd, 0, E),     # 0x93 RES 2,(IX+d),E
            partial(self.res_set, r, m, 23, 4, 251, Xd, 0, H),     # 0x94 RES 2,(IX+d),H
            partial(self.res_set, r, m, 23, 4, 251, Xd, 0, L),     # 0x95 RES 2,(IX+d),L
            partial(self.res_set, r, m, 23, 4, 251, Xd, 0),        # 0x96 RES 2,(IX+d)
            partial(self.res_set, r, m, 23, 4, 251, Xd, 0, A),     # 0x97 RES 2,(IX+d),A
            partial(self.res_set, r, m, 23, 4, 247, Xd, 0, B),     # 0x98 RES 3,(IX+d),B
            partial(self.res_set, r, m, 23, 4, 247, Xd, 0, C),     # 0x99 RES 3,(IX+d),C
            partial(self.res_set, r, m, 23, 4, 247, Xd, 0, D),     # 0x9A RES 3,(IX+d),D
            partial(self.res_set, r, m, 23, 4, 247, Xd, 0, E),     # 0x9B RES 3,(IX+d),E
            partial(self.res_set, r, m, 23, 4, 247, Xd, 0, H),     # 0x9C RES 3,(IX+d),H
            partial(self.res_set, r, m, 23, 4, 247, Xd, 0, L),     # 0x9D RES 3,(IX+d),L
            partial(self.res_set, r, m, 23, 4, 247, Xd, 0),        # 0x9E RES 3,(IX+d)
            partial(self.res_set, r, m, 23, 4, 247, Xd, 0, A),     # 0x9F RES 3,(IX+d),A
            partial(self.res_set, r, m, 23, 4, 239, Xd, 0, B),     # 0xA0 RES 4,(IX+d),B
            partial(self.res_set, r, m, 23, 4, 239, Xd, 0, C),     # 0xA1 RES 4,(IX+d),C
            partial(self.res_set, r, m, 23, 4, 239, Xd, 0, D),     # 0xA2 RES 4,(IX+d),D
            partial(self.res_set, r, m, 23, 4, 239, Xd, 0, E),     # 0xA3 RES 4,(IX+d),E
            partial(self.res_set, r, m, 23, 4, 239, Xd, 0, H),     # 0xA4 RES 4,(IX+d),H
            partial(self.res_set, r, m, 23, 4, 239, Xd, 0, L),     # 0xA5 RES 4,(IX+d),L
            partial(self.res_set, r, m, 23, 4, 239, Xd, 0),        # 0xA6 RES 4,(IX+d)
            partial(self.res_set, r, m, 23, 4, 239, Xd, 0, A),     # 0xA7 RES 4,(IX+d),A
            partial(self.res_set, r, m, 23, 4, 223, Xd, 0, B),     # 0xA8 RES 5,(IX+d),B
            partial(self.res_set, r, m, 23, 4, 223, Xd, 0, C),     # 0xA9 RES 5,(IX+d),C
            partial(self.res_set, r, m, 23, 4, 223, Xd, 0, D),     # 0xAA RES 5,(IX+d),D
            partial(self.res_set, r, m, 23, 4, 223, Xd, 0, E),     # 0xAB RES 5,(IX+d),E
            partial(self.res_set, r, m, 23, 4, 223, Xd, 0, H),     # 0xAC RES 5,(IX+d),H
            partial(self.res_set, r, m, 23, 4, 223, Xd, 0, L),     # 0xAD RES 5,(IX+d),L
            partial(self.res_set, r, m, 23, 4, 223, Xd, 0),        # 0xAE RES 5,(IX+d)
            partial(self.res_set, r, m, 23, 4, 223, Xd, 0, A),     # 0xAF RES 5,(IX+d),A
            partial(self.res_set, r, m, 23, 4, 191, Xd, 0, B),     # 0xB0 RES 6,(IX+d),B
            partial(self.res_set, r, m, 23, 4, 191, Xd, 0, C),     # 0xB1 RES 6,(IX+d),C
            partial(self.res_set, r, m, 23, 4, 191, Xd, 0, D),     # 0xB2 RES 6,(IX+d),D
            partial(self.res_set, r, m, 23, 4, 191, Xd, 0, E),     # 0xB3 RES 6,(IX+d),E
            partial(self.res_set, r, m, 23, 4, 191, Xd, 0, H),     # 0xB4 RES 6,(IX+d),H
            partial(self.res_set, r, m, 23, 4, 191, Xd, 0, L),     # 0xB5 RES 6,(IX+d),L
            partial(self.res_set, r, m, 23, 4, 191, Xd, 0),        # 0xB6 RES 6,(IX+d)
            partial(self.res_set, r, m, 23, 4, 191, Xd, 0, A),     # 0xB7 RES 6,(IX+d),A
            partial(self.res_set, r, m, 23, 4, 127, Xd, 0, B),     # 0xB8 RES 7,(IX+d),B
            partial(self.res_set, r, m, 23, 4, 127, Xd, 0, C),     # 0xB9 RES 7,(IX+d),C
            partial(self.res_set, r, m, 23, 4, 127, Xd, 0, D),     # 0xBA RES 7,(IX+d),D
            partial(self.res_set, r, m, 23, 4, 127, Xd, 0, E),     # 0xBB RES 7,(IX+d),E
            partial(self.res_set, r, m, 23, 4, 127, Xd, 0, H),     # 0xBC RES 7,(IX+d),H
            partial(self.res_set, r, m, 23, 4, 127, Xd, 0, L),     # 0xBD RES 7,(IX+d),L
            partial(self.res_set, r, m, 23, 4, 127, Xd, 0),        # 0xBE RES 7,(IX+d)
            partial(self.res_set, r, m, 23, 4, 127, Xd, 0, A),     # 0xBF RES 7,(IX+d),A
            partial(self.res_set, r, m, 23, 4, 1, Xd, 1, B),       # 0xC0 SET 0,(IX+d),B
            partial(self.res_set, r, m, 23, 4, 1, Xd, 1, C),       # 0xC1 SET 0,(IX+d),C
            partial(self.res_set, r, m, 23, 4, 1, Xd, 1, D),       # 0xC2 SET 0,(IX+d),D
            partial(self.res_set, r, m, 23, 4, 1, Xd, 1, E),       # 0xC3 SET 0,(IX+d),E
            partial(self.res_set, r, m, 23, 4, 1, Xd, 1, H),       # 0xC4 SET 0,(IX+d),H
            partial(self.res_set, r, m, 23, 4, 1, Xd, 1, L),       # 0xC5 SET 0,(IX+d),L
            partial(self.res_set, r, m, 23, 4, 1, Xd, 1),          # 0xC6 SET 0,(IX+d)
            partial(self.res_set, r, m, 23, 4, 1, Xd, 1, A),       # 0xC7 SET 0,(IX+d),A
            partial(self.res_set, r, m, 23, 4, 2, Xd, 1, B),       # 0xC8 SET 1,(IX+d),B
            partial(self.res_set, r, m, 23, 4, 2, Xd, 1, C),       # 0xC9 SET 1,(IX+d),C
            partial(self.res_set, r, m, 23, 4, 2, Xd, 1, D),       # 0xCA SET 1,(IX+d),D
            partial(self.res_set, r, m, 23, 4, 2, Xd, 1, E),       # 0xCB SET 1,(IX+d),E
            partial(self.res_set, r, m, 23, 4, 2, Xd, 1, H),       # 0xCC SET 1,(IX+d),H
            partial(self.res_set, r, m, 23, 4, 2, Xd, 1, L),       # 0xCD SET 1,(IX+d),L
            partial(self.res_set, r, m, 23, 4, 2, Xd, 1),          # 0xCE SET 1,(IX+d)
            partial(self.res_set, r, m, 23, 4, 2, Xd, 1, A),       # 0xCF SET 1,(IX+d),A
            partial(self.res_set, r, m, 23, 4, 4, Xd, 1, B),       # 0xD0 SET 2,(IX+d),B
            partial(self.res_set, r, m, 23, 4, 4, Xd, 1, C),       # 0xD1 SET 2,(IX+d),C
            partial(self.res_set, r, m, 23, 4, 4, Xd, 1, D),       # 0xD2 SET 2,(IX+d),D
            partial(self.res_set, r, m, 23, 4, 4, Xd, 1, E),       # 0xD3 SET 2,(IX+d),E
            partial(self.res_set, r, m, 23, 4, 4, Xd, 1, H),       # 0xD4 SET 2,(IX+d),H
            partial(self.res_set, r, m, 23, 4, 4, Xd, 1, L),       # 0xD5 SET 2,(IX+d),L
            partial(self.res_set, r, m, 23, 4, 4, Xd, 1),          # 0xD6 SET 2,(IX+d)
            partial(self.res_set, r, m, 23, 4, 4, Xd, 1, A),       # 0xD7 SET 2,(IX+d),A
            partial(self.res_set, r, m, 23, 4, 8, Xd, 1, B),       # 0xD8 SET 3,(IX+d),B
            partial(self.res_set, r, m, 23, 4, 8, Xd, 1, C),       # 0xD9 SET 3,(IX+d),C
            partial(self.res_set, r, m, 23, 4, 8, Xd, 1, D),       # 0xDA SET 3,(IX+d),D
            partial(self.res_set, r, m, 23, 4, 8, Xd, 1, E),       # 0xDB SET 3,(IX+d),E
            partial(self.res_set, r, m, 23, 4, 8, Xd, 1, H),       # 0xDC SET 3,(IX+d),H
            partial(self.res_set, r, m, 23, 4, 8, Xd, 1, L),       # 0xDD SET 3,(IX+d),L
            partial(self.res_set, r, m, 23, 4, 8, Xd, 1),          # 0xDE SET 3,(IX+d)
            partial(self.res_set, r, m, 23, 4, 8, Xd, 1, A),       # 0xDF SET 3,(IX+d),A
            partial(self.res_set, r, m, 23, 4, 16, Xd, 1, B),      # 0xE0 SET 4,(IX+d),B
            partial(self.res_set, r, m, 23, 4, 16, Xd, 1, C),      # 0xE1 SET 4,(IX+d),C
            partial(self.res_set, r, m, 23, 4, 16, Xd, 1, D),      # 0xE2 SET 4,(IX+d),D
            partial(self.res_set, r, m, 23, 4, 16, Xd, 1, E),      # 0xE3 SET 4,(IX+d),E
            partial(self.res_set, r, m, 23, 4, 16, Xd, 1, H),      # 0xE4 SET 4,(IX+d),H
            partial(self.res_set, r, m, 23, 4, 16, Xd, 1, L),      # 0xE5 SET 4,(IX+d),L
            partial(self.res_set, r, m, 23, 4, 16, Xd, 1),         # 0xE6 SET 4,(IX+d)
            partial(self.res_set, r, m, 23, 4, 16, Xd, 1, A),      # 0xE7 SET 4,(IX+d),A
            partial(self.res_set, r, m, 23, 4, 32, Xd, 1, B),      # 0xE8 SET 5,(IX+d),B
            partial(self.res_set, r, m, 23, 4, 32, Xd, 1, C),      # 0xE9 SET 5,(IX+d),C
            partial(self.res_set, r, m, 23, 4, 32, Xd, 1, D),      # 0xEA SET 5,(IX+d),D
            partial(self.res_set, r, m, 23, 4, 32, Xd, 1, E),      # 0xEB SET 5,(IX+d),E
            partial(self.res_set, r, m, 23, 4, 32, Xd, 1, H),      # 0xEC SET 5,(IX+d),H
            partial(self.res_set, r, m, 23, 4, 32, Xd, 1, L),      # 0xED SET 5,(IX+d),L
            partial(self.res_set, r, m, 23, 4, 32, Xd, 1),         # 0xEE SET 5,(IX+d)
            partial(self.res_set, r, m, 23, 4, 32, Xd, 1, A),      # 0xEF SET 5,(IX+d),A
            partial(self.res_set, r, m, 23, 4, 64, Xd, 1, B),      # 0xF0 SET 6,(IX+d),B
            partial(self.res_set, r, m, 23, 4, 64, Xd, 1, C),      # 0xF1 SET 6,(IX+d),C
            partial(self.res_set, r, m, 23, 4, 64, Xd, 1, D),      # 0xF2 SET 6,(IX+d),D
            partial(self.res_set, r, m, 23, 4, 64, Xd, 1, E),      # 0xF3 SET 6,(IX+d),E
            partial(self.res_set, r, m, 23, 4, 64, Xd, 1, H),      # 0xF4 SET 6,(IX+d),H
            partial(self.res_set, r, m, 23, 4, 64, Xd, 1, L),      # 0xF5 SET 6,(IX+d),L
            partial(self.res_set, r, m, 23, 4, 64, Xd, 1),         # 0xF6 SET 6,(IX+d)
            partial(self.res_set, r, m, 23, 4, 64, Xd, 1, A),      # 0xF7 SET 6,(IX+d),A
            partial(self.res_set, r, m, 23, 4, 128, Xd, 1, B),     # 0xF8 SET 7,(IX+d),B
            partial(self.res_set, r, m, 23, 4, 128, Xd, 1, C),     # 0xF9 SET 7,(IX+d),C
            partial(self.res_set, r, m, 23, 4, 128, Xd, 1, D),     # 0xFA SET 7,(IX+d),D
            partial(self.res_set, r, m, 23, 4, 128, Xd, 1, E),     # 0xFB SET 7,(IX+d),E
            partial(self.res_set, r, m, 23, 4, 128, Xd, 1, H),     # 0xFC SET 7,(IX+d),H
            partial(self.res_set, r, m, 23, 4, 128, Xd, 1, L),     # 0xFD SET 7,(IX+d),L
            partial(self.res_set, r, m, 23, 4, 128, Xd, 1),        # 0xFE SET 7,(IX+d)
            partial(self.res_set, r, m, 23, 4, 128, Xd, 1, A),     # 0xFF SET 7,(IX+d),A
        ]

        self.after_FD = [
            partial(self.nop_dd_fd, r),                            # 0x00
            partial(self.nop_dd_fd, r),                            # 0x01
            partial(self.nop_dd_fd, r),                            # 0x02
            partial(self.nop_dd_fd, r),                            # 0x03
            partial(self.nop_dd_fd, r),                            # 0x04
            partial(self.nop_dd_fd, r),                            # 0x05
            partial(self.nop_dd_fd, r),                            # 0x06
            partial(self.nop_dd_fd, r),                            # 0x07
            partial(self.nop_dd_fd, r),                            # 0x08
            partial(self.add16, r, 15, 2, IYh, B),                 # 0x09 ADD IY,BC
            partial(self.nop_dd_fd, r),                            # 0x0A
            partial(self.nop_dd_fd, r),                            # 0x0B
            partial(self.nop_dd_fd, r),                            # 0x0C
            partial(self.nop_dd_fd, r),                            # 0x0D
            partial(self.nop_dd_fd, r),                            # 0x0E
            partial(self.nop_dd_fd, r),                            # 0x0F
            partial(self.nop_dd_fd, r),                            # 0x10
            partial(self.nop_dd_fd, r),                            # 0x11
            partial(self.nop_dd_fd, r),                            # 0x12
            partial(self.nop_dd_fd, r),                            # 0x13
            partial(self.nop_dd_fd, r),                            # 0x14
            partial(self.nop_dd_fd, r),                            # 0x15
            partial(self.nop_dd_fd, r),                            # 0x16
            partial(self.nop_dd_fd, r),                            # 0x17
            partial(self.nop_dd_fd, r),                            # 0x18
            partial(self.add16, r, 15, 2, IYh, D),                 # 0x19 ADD IY,DE
            partial(self.nop_dd_fd, r),                            # 0x1A
            partial(self.nop_dd_fd, r),                            # 0x1B
            partial(self.nop_dd_fd, r),                            # 0x1C
            partial(self.nop_dd_fd, r),                            # 0x1D
            partial(self.nop_dd_fd, r),                            # 0x1E
            partial(self.nop_dd_fd, r),                            # 0x1F
            partial(self.nop_dd_fd, r),                            # 0x20
            partial(self.ld16, r, m, IYh),                         # 0x21 LD IY,nn
            partial(self.ld16addr, r, m, 20, 4, IYh, 1),           # 0x22 LD (nn),IY
            partial(self.inc_dec16, r, 1, IYh),                    # 0x23 INC IY
            partial(self.inc_dec8, r, m, 8, 2, 1, IYh),            # 0x24 INC IYh
            partial(self.inc_dec8, r, m, 8, 2, -1, IYh),           # 0x25 DEC IYh
            partial(self.ld8, r, m, 11, 3, IYh),                   # 0x26 LD IYh,n
            partial(self.nop_dd_fd, r),                            # 0x27
            partial(self.nop_dd_fd, r),                            # 0x28
            partial(self.add16, r, 15, 2, IYh, IYh),               # 0x29 ADD IY,IY
            partial(self.ld16addr, r, m, 20, 4, IYh, 0),           # 0x2A LD IY,(nn)
            partial(self.inc_dec16, r, -1, IYh),                   # 0x2B DEC IY
            partial(self.inc_dec8, r, m, 8, 2, 1, IYl),            # 0x2C INC IYl
            partial(self.inc_dec8, r, m, 8, 2, -1, IYl),           # 0x2D DEC IYl
            partial(self.ld8, r, m, 11, 3, IYl),                   # 0x2E LD IYl,n
            partial(self.nop_dd_fd, r),                            # 0x2F
            partial(self.nop_dd_fd, r),                            # 0x30
            partial(self.nop_dd_fd, r),                            # 0x31
            partial(self.nop_dd_fd, r),                            # 0x32
            partial(self.nop_dd_fd, r),                            # 0x33
            partial(self.inc_dec8, r, m, 23, 3, 1, Yd),            # 0x34 INC (IY+d)
            partial(self.inc_dec8, r, m, 23, 3, -1, Yd),           # 0x35 DEC (IY+d)
            partial(self.ld8, r, m, 19, 4, Yd),                    # 0x36 LD (IY+d),n
            partial(self.nop_dd_fd, r),                            # 0x37
            partial(self.nop_dd_fd, r),                            # 0x38
            partial(self.add16, r, 15, 2, IYh, SP),                # 0x39 ADD IY,SP
            partial(self.nop_dd_fd, r),                            # 0x3A
            partial(self.nop_dd_fd, r),                            # 0x3B
            partial(self.nop_dd_fd, r),                            # 0x3C
            partial(self.nop_dd_fd, r),                            # 0x3D
            partial(self.nop_dd_fd, r),                            # 0x3E
            partial(self.nop_dd_fd, r),                            # 0x3F
            partial(self.nop_dd_fd, r),                            # 0x40
            partial(self.nop_dd_fd, r),                            # 0x41
            partial(self.nop_dd_fd, r),                            # 0x42
            partial(self.nop_dd_fd, r),                            # 0x43
            partial(self.ld8, r, m, 8, 2, B, IYh),                 # 0x44 LD B,IYh
            partial(self.ld8, r, m, 8, 2, B, IYl),                 # 0x45 LD B,IYl
            partial(self.ld8, r, m, 19, 3, B, Yd),                 # 0x46 LD B,(IY+d)
            partial(self.nop_dd_fd, r),                            # 0x47
            partial(self.nop_dd_fd, r),                            # 0x48
            partial(self.nop_dd_fd, r),                            # 0x49
            partial(self.nop_dd_fd, r),                            # 0x4A
            partial(self.nop_dd_fd, r),                            # 0x4B
            partial(self.ld8, r, m, 8, 2, C, IYh),                 # 0x4C LD C,IYh
            partial(self.ld8, r, m, 8, 2, C, IYl),                 # 0x4D LD C,IYl
            partial(self.ld8, r, m, 19, 3, C, Yd),                 # 0x4E LD C,(IY+d)
            partial(self.nop_dd_fd, r),                            # 0x4F
            partial(self.nop_dd_fd, r),                            # 0x50
            partial(self.nop_dd_fd, r),                            # 0x51
            partial(self.nop_dd_fd, r),                            # 0x52
            partial(self.nop_dd_fd, r),                            # 0x53
            partial(self.ld8, r, m, 8, 2, D, IYh),                 # 0x54 LD D,IYh
            partial(self.ld8, r, m, 8, 2, D, IYl),                 # 0x55 LD D,IYl
            partial(self.ld8, r, m, 19, 3, D, Yd),                 # 0x56 LD D,(IY+d)
            partial(self.nop_dd_fd, r),                            # 0x57
            partial(self.nop_dd_fd, r),                            # 0x58
            partial(self.nop_dd_fd, r),                            # 0x59
            partial(self.nop_dd_fd, r),                            # 0x5A
            partial(self.nop_dd_fd, r),                            # 0x5B
            partial(self.ld8, r, m, 8, 2, E, IYh),                 # 0x5C LD E,IYh
            partial(self.ld8, r, m, 8, 2, E, IYl),                 # 0x5D LD E,IYl
            partial(self.ld8, r, m, 19, 3, E, Yd),                 # 0x5E LD E,(IY+d)
            partial(self.nop_dd_fd, r),                            # 0x5F
            partial(self.ld8, r, m, 8, 2, IYh, B),                 # 0x60 LD IYh,B
            partial(self.ld8, r, m, 8, 2, IYh, C),                 # 0x61 LD IYh,C
            partial(self.ld8, r, m, 8, 2, IYh, D),                 # 0x62 LD IYh,D
            partial(self.ld8, r, m, 8, 2, IYh, E),                 # 0x63 LD IYh,E
            partial(self.ld8, r, m, 8, 2, IYh, IYh),               # 0x64 LD IYh,IYh
            partial(self.ld8, r, m, 8, 2, IYh, IYl),               # 0x65 LD IYh,IYl
            partial(self.ld8, r, m, 19, 3, H, Yd),                 # 0x66 LD H,(IY+d)
            partial(self.ld8, r, m, 8, 2, IYh, A),                 # 0x67 LD IYh,A
            partial(self.ld8, r, m, 8, 2, IYl, B),                 # 0x68 LD IYl,B
            partial(self.ld8, r, m, 8, 2, IYl, C),                 # 0x69 LD IYl,C
            partial(self.ld8, r, m, 8, 2, IYl, D),                 # 0x6A LD IYl,D
            partial(self.ld8, r, m, 8, 2, IYl, E),                 # 0x6B LD IYl,E
            partial(self.ld8, r, m, 8, 2, IYl, IYh),               # 0x6C LD IYl,IYh
            partial(self.ld8, r, m, 8, 2, IYl, IYl),               # 0x6D LD IYl,IYl
            partial(self.ld8, r, m, 19, 3, L, Yd),                 # 0x6E LD L,(IY+d)
            partial(self.ld8, r, m, 8, 2, IYl, A),                 # 0x6F LD IYl,A
            partial(self.ld8, r, m, 19, 3, Yd, B),                 # 0x70 LD (IY+d),B
            partial(self.ld8, r, m, 19, 3, Yd, C),                 # 0x71 LD (IY+d),C
            partial(self.ld8, r, m, 19, 3, Yd, D),                 # 0x72 LD (IY+d),D
            partial(self.ld8, r, m, 19, 3, Yd, E),                 # 0x73 LD (IY+d),E
            partial(self.ld8, r, m, 19, 3, Yd, H),                 # 0x74 LD (IY+d),H
            partial(self.ld8, r, m, 19, 3, Yd, L),                 # 0x75 LD (IY+d),L
            partial(self.nop_dd_fd, r),                            # 0x76
            partial(self.ld8, r, m, 19, 3, Yd, A),                 # 0x77 LD (IY+d),A
            partial(self.nop_dd_fd, r),                            # 0x78
            partial(self.nop_dd_fd, r),                            # 0x79
            partial(self.nop_dd_fd, r),                            # 0x7A
            partial(self.nop_dd_fd, r),                            # 0x7B
            partial(self.ld8, r, m, 8, 2, A, IYh),                 # 0x7C LD A,IYh
            partial(self.ld8, r, m, 8, 2, A, IYl),                 # 0x7D LD A,IYl
            partial(self.ld8, r, m, 19, 3, A, Yd),                 # 0x7E LD A,(IY+d)
            partial(self.nop_dd_fd, r),                            # 0x7F
            partial(self.nop_dd_fd, r),                            # 0x80
            partial(self.nop_dd_fd, r),                            # 0x81
            partial(self.nop_dd_fd, r),                            # 0x82
            partial(self.nop_dd_fd, r),                            # 0x83
            partial(self.add_a, r, m, 8, 2, IYh),                  # 0x84 ADD A,IYh
            partial(self.add_a, r, m, 8, 2, IYl),                  # 0x85 ADD A,IYl
            partial(self.add_a, r, m, 19, 3, Yd),                  # 0x86 ADD A,(IY+d)
            partial(self.nop_dd_fd, r),                            # 0x87
            partial(self.nop_dd_fd, r),                            # 0x88
            partial(self.nop_dd_fd, r),                            # 0x89
            partial(self.nop_dd_fd, r),                            # 0x8A
            partial(self.nop_dd_fd, r),                            # 0x8B
            partial(self.adc_a, r, m, 8, 2, IYh),                  # 0x8C ADC A,IYh
            partial(self.adc_a, r, m, 8, 2, IYl),                  # 0x8D ADC A,IYl
            partial(self.adc_a, r, m, 19, 3, Yd),                  # 0x8E ADC A,(IY+d)
            partial(self.nop_dd_fd, r),                            # 0x8F
            partial(self.nop_dd_fd, r),                            # 0x90
            partial(self.nop_dd_fd, r),                            # 0x91
            partial(self.nop_dd_fd, r),                            # 0x92
            partial(self.nop_dd_fd, r),                            # 0x93
            partial(self.sub, r, m, 8, 2, IYh),                    # 0x94 SUB IYh
            partial(self.sub, r, m, 8, 2, IYl),                    # 0x95 SUB IYl
            partial(self.sub, r, m, 19, 3, Yd),                    # 0x96 SUB (IY+d)
            partial(self.nop_dd_fd, r),                            # 0x97
            partial(self.nop_dd_fd, r),                            # 0x98
            partial(self.nop_dd_fd, r),                            # 0x99
            partial(self.nop_dd_fd, r),                            # 0x9A
            partial(self.nop_dd_fd, r),                            # 0x9B
            partial(self.sbc_a, r, m, 8, 2, IYh),                  # 0x9C SBC A,IYh
            partial(self.sbc_a, r, m, 8, 2, IYl),                  # 0x9D SBC A,IYl
            partial(self.sbc_a, r, m, 19, 3, Yd),                  # 0x9E SBC A,(IY+d)
            partial(self.nop_dd_fd, r),                            # 0x9F
            partial(self.nop_dd_fd, r),                            # 0xA0
            partial(self.nop_dd_fd, r),                            # 0xA1
            partial(self.nop_dd_fd, r),                            # 0xA2
            partial(self.nop_dd_fd, r),                            # 0xA3
            partial(self.anda, r, m, 8, 2, IYh),                   # 0xA4 AND IYh
            partial(self.anda, r, m, 8, 2, IYl),                   # 0xA5 AND IYl
            partial(self.anda, r, m, 19, 3, Yd),                   # 0xA6 AND (IY+d)
            partial(self.nop_dd_fd, r),                            # 0xA7
            partial(self.nop_dd_fd, r),                            # 0xA8
            partial(self.nop_dd_fd, r),                            # 0xA9
            partial(self.nop_dd_fd, r),                            # 0xAA
            partial(self.nop_dd_fd, r),                            # 0xAB
            partial(self.xor, r, m, 8, 2, IYh),                    # 0xAC XOR IYh
            partial(self.xor, r, m, 8, 2, IYl),                    # 0xAD XOR IYl
            partial(self.xor, r, m, 19, 3, Yd),                    # 0xAE XOR (IY+d)
            partial(self.nop_dd_fd, r),                            # 0xAF
            partial(self.nop_dd_fd, r),                            # 0xB0
            partial(self.nop_dd_fd, r),                            # 0xB1
            partial(self.nop_dd_fd, r),                            # 0xB2
            partial(self.nop_dd_fd, r),                            # 0xB3
            partial(self.ora, r, m, 8, 2, IYh),                    # 0xB4 OR IYh
            partial(self.ora, r, m, 8, 2, IYl),                    # 0xB5 OR IYl
            partial(self.ora, r, m, 19, 3, Yd),                    # 0xB6 OR (IY+d)
            partial(self.nop_dd_fd, r),                            # 0xB7
            partial(self.nop_dd_fd, r),                            # 0xB8
            partial(self.nop_dd_fd, r),                            # 0xB9
            partial(self.nop_dd_fd, r),                            # 0xBA
            partial(self.nop_dd_fd, r),                            # 0xBB
            partial(self.cp, r, m, 8, 2, IYh),                     # 0xBC CP IYh
            partial(self.cp, r, m, 8, 2, IYl),                     # 0xBD CP IYl
            partial(self.cp, r, m, 19, 3, Yd),                     # 0xBE CP (IY+d)
            partial(self.nop_dd_fd, r),                            # 0xBF
            partial(self.nop_dd_fd, r),                            # 0xC0
            partial(self.nop_dd_fd, r),                            # 0xC1
            partial(self.nop_dd_fd, r),                            # 0xC2
            partial(self.nop_dd_fd, r),                            # 0xC3
            partial(self.nop_dd_fd, r),                            # 0xC4
            partial(self.nop_dd_fd, r),                            # 0xC5
            partial(self.nop_dd_fd, r),                            # 0xC6
            partial(self.nop_dd_fd, r),                            # 0xC7
            partial(self.nop_dd_fd, r),                            # 0xC8
            partial(self.nop_dd_fd, r),                            # 0xC9
            partial(self.nop_dd_fd, r),                            # 0xCA
            None,                                                  # 0xCB FDCB prefix
            partial(self.nop_dd_fd, r),                            # 0xCC
            partial(self.nop_dd_fd, r),                            # 0xCD
            partial(self.nop_dd_fd, r),                            # 0xCE
            partial(self.nop_dd_fd, r),                            # 0xCF
            partial(self.nop_dd_fd, r),                            # 0xD0
            partial(self.nop_dd_fd, r),                            # 0xD1
            partial(self.nop_dd_fd, r),                            # 0xD2
            partial(self.nop_dd_fd, r),                            # 0xD3
            partial(self.nop_dd_fd, r),                            # 0xD4
            partial(self.nop_dd_fd, r),                            # 0xD5
            partial(self.nop_dd_fd, r),                            # 0xD6
            partial(self.nop_dd_fd, r),                            # 0xD7
            partial(self.nop_dd_fd, r),                            # 0xD8
            partial(self.nop_dd_fd, r),                            # 0xD9
            partial(self.nop_dd_fd, r),                            # 0xDA
            partial(self.nop_dd_fd, r),                            # 0xDB
            partial(self.nop_dd_fd, r),                            # 0xDC
            partial(self.nop_dd_fd, r),                            # 0xDD
            partial(self.nop_dd_fd, r),                            # 0xDE
            partial(self.nop_dd_fd, r),                            # 0xDF
            partial(self.nop_dd_fd, r),                            # 0xE0
            partial(self.pop, r, m, IYh),                          # 0xE1 POP IY
            partial(self.nop_dd_fd, r),                            # 0xE2
            partial(self.ex_sp, r, m, IYh),                        # 0xE3 EX (SP),IY
            partial(self.nop_dd_fd, r),                            # 0xE4
            partial(self.push, r, m, IYh),                         # 0xE5 PUSH IY
            partial(self.nop_dd_fd, r),                            # 0xE6
            partial(self.nop_dd_fd, r),                            # 0xE7
            partial(self.nop_dd_fd, r),                            # 0xE8
            partial(self.jp, r, m, 0, IYh),                        # 0xE9 JP (IY)
            partial(self.nop_dd_fd, r),                            # 0xEA
            partial(self.nop_dd_fd, r),                            # 0xEB
            partial(self.nop_dd_fd, r),                            # 0xEC
            partial(self.nop_dd_fd, r),                            # 0xED
            partial(self.nop_dd_fd, r),                            # 0xEE
            partial(self.nop_dd_fd, r),                            # 0xEF
            partial(self.nop_dd_fd, r),                            # 0xF0
            partial(self.nop_dd_fd, r),                            # 0xF1
            partial(self.nop_dd_fd, r),                            # 0xF2
            partial(self.nop_dd_fd, r),                            # 0xF3
            partial(self.nop_dd_fd, r),                            # 0xF4
            partial(self.nop_dd_fd, r),                            # 0xF5
            partial(self.nop_dd_fd, r),                            # 0xF6
            partial(self.nop_dd_fd, r),                            # 0xF7
            partial(self.nop_dd_fd, r),                            # 0xF8
            partial(self.ldsprr, r, IYh),                          # 0xF9 LD SP,IY
            partial(self.nop_dd_fd, r),                            # 0xFA
            partial(self.nop_dd_fd, r),                            # 0xFB
            partial(self.nop_dd_fd, r),                            # 0xFC
            partial(self.nop_dd_fd, r),                            # 0xFD
            partial(self.nop_dd_fd, r),                            # 0xFE
            partial(self.nop_dd_fd, r),                            # 0xFF
        ]

        self.after_FDCB = [
            partial(self.rotate, r, m, 23, 4, 128, RLC, Yd, 1, B), # 0x00 RLC (IY+d),B
            partial(self.rotate, r, m, 23, 4, 128, RLC, Yd, 1, C), # 0x01 RLC (IY+d),C
            partial(self.rotate, r, m, 23, 4, 128, RLC, Yd, 1, D), # 0x02 RLC (IY+d),D
            partial(self.rotate, r, m, 23, 4, 128, RLC, Yd, 1, E), # 0x03 RLC (IY+d),E
            partial(self.rotate, r, m, 23, 4, 128, RLC, Yd, 1, H), # 0x04 RLC (IY+d),H
            partial(self.rotate, r, m, 23, 4, 128, RLC, Yd, 1, L), # 0x05 RLC (IY+d),L
            partial(self.rotate, r, m, 23, 4, 128, RLC, Yd, 1),    # 0x06 RLC (IY+d)
            partial(self.rotate, r, m, 23, 4, 128, RLC, Yd, 1, A), # 0x07 RLC (IY+d),A
            partial(self.rotate, r, m, 23, 4, 1, RRC, Yd, 1, B),   # 0x08 RRC (IY+d),B
            partial(self.rotate, r, m, 23, 4, 1, RRC, Yd, 1, C),   # 0x09 RRC (IY+d),C
            partial(self.rotate, r, m, 23, 4, 1, RRC, Yd, 1, D),   # 0x0A RRC (IY+d),D
            partial(self.rotate, r, m, 23, 4, 1, RRC, Yd, 1, E),   # 0x0B RRC (IY+d),E
            partial(self.rotate, r, m, 23, 4, 1, RRC, Yd, 1, H),   # 0x0C RRC (IY+d),H
            partial(self.rotate, r, m, 23, 4, 1, RRC, Yd, 1, L),   # 0x0D RRC (IY+d),L
            partial(self.rotate, r, m, 23, 4, 1, RRC, Yd, 1),      # 0x0E RRC (IY+d)
            partial(self.rotate, r, m, 23, 4, 1, RRC, Yd, 1, A),   # 0x0F RRC (IY+d),A
            partial(self.rotate, r, m, 23, 4, 128, RL, Yd, 0, B),  # 0x10 RL (IY+d),B
            partial(self.rotate, r, m, 23, 4, 128, RL, Yd, 0, C),  # 0x11 RL (IY+d),C
            partial(self.rotate, r, m, 23, 4, 128, RL, Yd, 0, D),  # 0x12 RL (IY+d),D
            partial(self.rotate, r, m, 23, 4, 128, RL, Yd, 0, E),  # 0x13 RL (IY+d),E
            partial(self.rotate, r, m, 23, 4, 128, RL, Yd, 0, H),  # 0x14 RL (IY+d),H
            partial(self.rotate, r, m, 23, 4, 128, RL, Yd, 0, L),  # 0x15 RL (IY+d),L
            partial(self.rotate, r, m, 23, 4, 128, RL, Yd),        # 0x16 RL (IY+d)
            partial(self.rotate, r, m, 23, 4, 128, RL, Yd, 0, A),  # 0x17 RL (IY+d),A
            partial(self.rotate, r, m, 23, 4, 1, RR, Yd, 0, B),    # 0x18 RR (IY+d),B
            partial(self.rotate, r, m, 23, 4, 1, RR, Yd, 0, C),    # 0x19 RR (IY+d),C
            partial(self.rotate, r, m, 23, 4, 1, RR, Yd, 0, D),    # 0x1A RR (IY+d),D
            partial(self.rotate, r, m, 23, 4, 1, RR, Yd, 0, E),    # 0x1B RR (IY+d),E
            partial(self.rotate, r, m, 23, 4, 1, RR, Yd, 0, H),    # 0x1C RR (IY+d),H
            partial(self.rotate, r, m, 23, 4, 1, RR, Yd, 0, L),    # 0x1D RR (IY+d),L
            partial(self.rotate, r, m, 23, 4, 1, RR, Yd),          # 0x1E RR (IY+d)
            partial(self.rotate, r, m, 23, 4, 1, RR, Yd, 0, A),    # 0x1F RR (IY+d),A
            partial(self.shift, r, m, 23, 4, SLA, 128, Yd, B),     # 0x20 SLA (IY+d),B
            partial(self.shift, r, m, 23, 4, SLA, 128, Yd, C),     # 0x21 SLA (IY+d),C
            partial(self.shift, r, m, 23, 4, SLA, 128, Yd, D),     # 0x22 SLA (IY+d),D
            partial(self.shift, r, m, 23, 4, SLA, 128, Yd, E),     # 0x23 SLA (IY+d),E
            partial(self.shift, r, m, 23, 4, SLA, 128, Yd, H),     # 0x24 SLA (IY+d),H
            partial(self.shift, r, m, 23, 4, SLA, 128, Yd, L),     # 0x25 SLA (IY+d),L
            partial(self.shift, r, m, 23, 4, SLA, 128, Yd),        # 0x26 SLA (IY+d)
            partial(self.shift, r, m, 23, 4, SLA, 128, Yd, A),     # 0x27 SLA (IY+d),A
            partial(self.shift, r, m, 23, 4, SRA, 1, Yd, B),       # 0x28 SRA (IY+d),B
            partial(self.shift, r, m, 23, 4, SRA, 1, Yd, C),       # 0x29 SRA (IY+d),C
            partial(self.shift, r, m, 23, 4, SRA, 1, Yd, D),       # 0x2A SRA (IY+d),D
            partial(self.shift, r, m, 23, 4, SRA, 1, Yd, E),       # 0x2B SRA (IY+d),E
            partial(self.shift, r, m, 23, 4, SRA, 1, Yd, H),       # 0x2C SRA (IY+d),H
            partial(self.shift, r, m, 23, 4, SRA, 1, Yd, L),       # 0x2D SRA (IY+d),L
            partial(self.shift, r, m, 23, 4, SRA, 1, Yd),          # 0x2E SRA (IY+d)
            partial(self.shift, r, m, 23, 4, SRA, 1, Yd, A),       # 0x2F SRA (IY+d),A
            partial(self.shift, r, m, 23, 4, SLL, 128, Yd, B),     # 0x30 SLL (IY+d),B
            partial(self.shift, r, m, 23, 4, SLL, 128, Yd, C),     # 0x31 SLL (IY+d),C
            partial(self.shift, r, m, 23, 4, SLL, 128, Yd, D),     # 0x32 SLL (IY+d),D
            partial(self.shift, r, m, 23, 4, SLL, 128, Yd, E),     # 0x33 SLL (IY+d),E
            partial(self.shift, r, m, 23, 4, SLL, 128, Yd, H),     # 0x34 SLL (IY+d),H
            partial(self.shift, r, m, 23, 4, SLL, 128, Yd, L),     # 0x35 SLL (IY+d),L
            partial(self.shift, r, m, 23, 4, SLL, 128, Yd),        # 0x36 SLL (IY+d)
            partial(self.shift, r, m, 23, 4, SLL, 128, Yd, A),     # 0x37 SLL (IY+d),A
            partial(self.shift, r, m, 23, 4, SRL, 1, Yd, B),       # 0x38 SRL (IY+d),B
            partial(self.shift, r, m, 23, 4, SRL, 1, Yd, C),       # 0x39 SRL (IY+d),C
            partial(self.shift, r, m, 23, 4, SRL, 1, Yd, D),       # 0x3A SRL (IY+d),D
            partial(self.shift, r, m, 23, 4, SRL, 1, Yd, E),       # 0x3B SRL (IY+d),E
            partial(self.shift, r, m, 23, 4, SRL, 1, Yd, H),       # 0x3C SRL (IY+d),H
            partial(self.shift, r, m, 23, 4, SRL, 1, Yd, L),       # 0x3D SRL (IY+d),L
            partial(self.shift, r, m, 23, 4, SRL, 1, Yd),          # 0x3E SRL (IY+d)
            partial(self.shift, r, m, 23, 4, SRL, 1, Yd, A),       # 0x3F SRL (IY+d),A
            partial(self.bit, r, m, 20, 4, 1, Yd),                 # 0x40 BIT 0,(IY+d)
            partial(self.bit, r, m, 20, 4, 1, Yd),                 # 0x41 BIT 0,(IY+d)
            partial(self.bit, r, m, 20, 4, 1, Yd),                 # 0x42 BIT 0,(IY+d)
            partial(self.bit, r, m, 20, 4, 1, Yd),                 # 0x43 BIT 0,(IY+d)
            partial(self.bit, r, m, 20, 4, 1, Yd),                 # 0x44 BIT 0,(IY+d)
            partial(self.bit, r, m, 20, 4, 1, Yd),                 # 0x45 BIT 0,(IY+d)
            partial(self.bit, r, m, 20, 4, 1, Yd),                 # 0x46 BIT 0,(IY+d)
            partial(self.bit, r, m, 20, 4, 1, Yd),                 # 0x47 BIT 0,(IY+d)
            partial(self.bit, r, m, 20, 4, 2, Yd),                 # 0x48 BIT 1,(IY+d)
            partial(self.bit, r, m, 20, 4, 2, Yd),                 # 0x49 BIT 1,(IY+d)
            partial(self.bit, r, m, 20, 4, 2, Yd),                 # 0x4A BIT 1,(IY+d)
            partial(self.bit, r, m, 20, 4, 2, Yd),                 # 0x4B BIT 1,(IY+d)
            partial(self.bit, r, m, 20, 4, 2, Yd),                 # 0x4C BIT 1,(IY+d)
            partial(self.bit, r, m, 20, 4, 2, Yd),                 # 0x4D BIT 1,(IY+d)
            partial(self.bit, r, m, 20, 4, 2, Yd),                 # 0x4E BIT 1,(IY+d)
            partial(self.bit, r, m, 20, 4, 2, Yd),                 # 0x4F BIT 1,(IY+d)
            partial(self.bit, r, m, 20, 4, 4, Yd),                 # 0x50 BIT 2,(IY+d)
            partial(self.bit, r, m, 20, 4, 4, Yd),                 # 0x51 BIT 2,(IY+d)
            partial(self.bit, r, m, 20, 4, 4, Yd),                 # 0x52 BIT 2,(IY+d)
            partial(self.bit, r, m, 20, 4, 4, Yd),                 # 0x53 BIT 2,(IY+d)
            partial(self.bit, r, m, 20, 4, 4, Yd),                 # 0x54 BIT 2,(IY+d)
            partial(self.bit, r, m, 20, 4, 4, Yd),                 # 0x55 BIT 2,(IY+d)
            partial(self.bit, r, m, 20, 4, 4, Yd),                 # 0x56 BIT 2,(IY+d)
            partial(self.bit, r, m, 20, 4, 4, Yd),                 # 0x57 BIT 2,(IY+d)
            partial(self.bit, r, m, 20, 4, 8, Yd),                 # 0x58 BIT 3,(IY+d)
            partial(self.bit, r, m, 20, 4, 8, Yd),                 # 0x59 BIT 3,(IY+d)
            partial(self.bit, r, m, 20, 4, 8, Yd),                 # 0x5A BIT 3,(IY+d)
            partial(self.bit, r, m, 20, 4, 8, Yd),                 # 0x5B BIT 3,(IY+d)
            partial(self.bit, r, m, 20, 4, 8, Yd),                 # 0x5C BIT 3,(IY+d)
            partial(self.bit, r, m, 20, 4, 8, Yd),                 # 0x5D BIT 3,(IY+d)
            partial(self.bit, r, m, 20, 4, 8, Yd),                 # 0x5E BIT 3,(IY+d)
            partial(self.bit, r, m, 20, 4, 8, Yd),                 # 0x5F BIT 3,(IY+d)
            partial(self.bit, r, m, 20, 4, 16, Yd),                # 0x60 BIT 4,(IY+d)
            partial(self.bit, r, m, 20, 4, 16, Yd),                # 0x61 BIT 4,(IY+d)
            partial(self.bit, r, m, 20, 4, 16, Yd),                # 0x62 BIT 4,(IY+d)
            partial(self.bit, r, m, 20, 4, 16, Yd),                # 0x63 BIT 4,(IY+d)
            partial(self.bit, r, m, 20, 4, 16, Yd),                # 0x64 BIT 4,(IY+d)
            partial(self.bit, r, m, 20, 4, 16, Yd),                # 0x65 BIT 4,(IY+d)
            partial(self.bit, r, m, 20, 4, 16, Yd),                # 0x66 BIT 4,(IY+d)
            partial(self.bit, r, m, 20, 4, 16, Yd),                # 0x67 BIT 4,(IY+d)
            partial(self.bit, r, m, 20, 4, 32, Yd),                # 0x68 BIT 5,(IY+d)
            partial(self.bit, r, m, 20, 4, 32, Yd),                # 0x69 BIT 5,(IY+d)
            partial(self.bit, r, m, 20, 4, 32, Yd),                # 0x6A BIT 5,(IY+d)
            partial(self.bit, r, m, 20, 4, 32, Yd),                # 0x6B BIT 5,(IY+d)
            partial(self.bit, r, m, 20, 4, 32, Yd),                # 0x6C BIT 5,(IY+d)
            partial(self.bit, r, m, 20, 4, 32, Yd),                # 0x6D BIT 5,(IY+d)
            partial(self.bit, r, m, 20, 4, 32, Yd),                # 0x6E BIT 5,(IY+d)
            partial(self.bit, r, m, 20, 4, 32, Yd),                # 0x6F BIT 5,(IY+d)
            partial(self.bit, r, m, 20, 4, 64, Yd),                # 0x70 BIT 6,(IY+d)
            partial(self.bit, r, m, 20, 4, 64, Yd),                # 0x71 BIT 6,(IY+d)
            partial(self.bit, r, m, 20, 4, 64, Yd),                # 0x72 BIT 6,(IY+d)
            partial(self.bit, r, m, 20, 4, 64, Yd),                # 0x73 BIT 6,(IY+d)
            partial(self.bit, r, m, 20, 4, 64, Yd),                # 0x74 BIT 6,(IY+d)
            partial(self.bit, r, m, 20, 4, 64, Yd),                # 0x75 BIT 6,(IY+d)
            partial(self.bit, r, m, 20, 4, 64, Yd),                # 0x76 BIT 6,(IY+d)
            partial(self.bit, r, m, 20, 4, 64, Yd),                # 0x77 BIT 6,(IY+d)
            partial(self.bit, r, m, 20, 4, 128, Yd),               # 0x78 BIT 7,(IY+d)
            partial(self.bit, r, m, 20, 4, 128, Yd),               # 0x79 BIT 7,(IY+d)
            partial(self.bit, r, m, 20, 4, 128, Yd),               # 0x7A BIT 7,(IY+d)
            partial(self.bit, r, m, 20, 4, 128, Yd),               # 0x7B BIT 7,(IY+d)
            partial(self.bit, r, m, 20, 4, 128, Yd),               # 0x7C BIT 7,(IY+d)
            partial(self.bit, r, m, 20, 4, 128, Yd),               # 0x7D BIT 7,(IY+d)
            partial(self.bit, r, m, 20, 4, 128, Yd),               # 0x7E BIT 7,(IY+d)
            partial(self.bit, r, m, 20, 4, 128, Yd),               # 0x7F BIT 7,(IY+d)
            partial(self.res_set, r, m, 23, 4, 254, Yd, 0, B),     # 0x80 RES 0,(IY+d),B
            partial(self.res_set, r, m, 23, 4, 254, Yd, 0, C),     # 0x81 RES 0,(IY+d),C
            partial(self.res_set, r, m, 23, 4, 254, Yd, 0, D),     # 0x82 RES 0,(IY+d),D
            partial(self.res_set, r, m, 23, 4, 254, Yd, 0, E),     # 0x83 RES 0,(IY+d),E
            partial(self.res_set, r, m, 23, 4, 254, Yd, 0, H),     # 0x84 RES 0,(IY+d),H
            partial(self.res_set, r, m, 23, 4, 254, Yd, 0, L),     # 0x85 RES 0,(IY+d),L
            partial(self.res_set, r, m, 23, 4, 254, Yd, 0),        # 0x86 RES 0,(IY+d)
            partial(self.res_set, r, m, 23, 4, 254, Yd, 0, A),     # 0x87 RES 0,(IY+d),A
            partial(self.res_set, r, m, 23, 4, 253, Yd, 0, B),     # 0x88 RES 1,(IY+d),B
            partial(self.res_set, r, m, 23, 4, 253, Yd, 0, C),     # 0x89 RES 1,(IY+d),C
            partial(self.res_set, r, m, 23, 4, 253, Yd, 0, D),     # 0x8A RES 1,(IY+d),D
            partial(self.res_set, r, m, 23, 4, 253, Yd, 0, E),     # 0x8B RES 1,(IY+d),E
            partial(self.res_set, r, m, 23, 4, 253, Yd, 0, H),     # 0x8C RES 1,(IY+d),H
            partial(self.res_set, r, m, 23, 4, 253, Yd, 0, L),     # 0x8D RES 1,(IY+d),L
            partial(self.res_set, r, m, 23, 4, 253, Yd, 0),        # 0x8E RES 1,(IY+d)
            partial(self.res_set, r, m, 23, 4, 253, Yd, 0, A),     # 0x8F RES 1,(IY+d),A
            partial(self.res_set, r, m, 23, 4, 251, Yd, 0, B),     # 0x90 RES 2,(IY+d),B
            partial(self.res_set, r, m, 23, 4, 251, Yd, 0, C),     # 0x91 RES 2,(IY+d),C
            partial(self.res_set, r, m, 23, 4, 251, Yd, 0, D),     # 0x92 RES 2,(IY+d),D
            partial(self.res_set, r, m, 23, 4, 251, Yd, 0, E),     # 0x93 RES 2,(IY+d),E
            partial(self.res_set, r, m, 23, 4, 251, Yd, 0, H),     # 0x94 RES 2,(IY+d),H
            partial(self.res_set, r, m, 23, 4, 251, Yd, 0, L),     # 0x95 RES 2,(IY+d),L
            partial(self.res_set, r, m, 23, 4, 251, Yd, 0),        # 0x96 RES 2,(IY+d)
            partial(self.res_set, r, m, 23, 4, 251, Yd, 0, A),     # 0x97 RES 2,(IY+d),A
            partial(self.res_set, r, m, 23, 4, 247, Yd, 0, B),     # 0x98 RES 3,(IY+d),B
            partial(self.res_set, r, m, 23, 4, 247, Yd, 0, C),     # 0x99 RES 3,(IY+d),C
            partial(self.res_set, r, m, 23, 4, 247, Yd, 0, D),     # 0x9A RES 3,(IY+d),D
            partial(self.res_set, r, m, 23, 4, 247, Yd, 0, E),     # 0x9B RES 3,(IY+d),E
            partial(self.res_set, r, m, 23, 4, 247, Yd, 0, H),     # 0x9C RES 3,(IY+d),H
            partial(self.res_set, r, m, 23, 4, 247, Yd, 0, L),     # 0x9D RES 3,(IY+d),L
            partial(self.res_set, r, m, 23, 4, 247, Yd, 0),        # 0x9E RES 3,(IY+d)
            partial(self.res_set, r, m, 23, 4, 247, Yd, 0, A),     # 0x9F RES 3,(IY+d),A
            partial(self.res_set, r, m, 23, 4, 239, Yd, 0, B),     # 0xA0 RES 4,(IY+d),B
            partial(self.res_set, r, m, 23, 4, 239, Yd, 0, C),     # 0xA1 RES 4,(IY+d),C
            partial(self.res_set, r, m, 23, 4, 239, Yd, 0, D),     # 0xA2 RES 4,(IY+d),D
            partial(self.res_set, r, m, 23, 4, 239, Yd, 0, E),     # 0xA3 RES 4,(IY+d),E
            partial(self.res_set, r, m, 23, 4, 239, Yd, 0, H),     # 0xA4 RES 4,(IY+d),H
            partial(self.res_set, r, m, 23, 4, 239, Yd, 0, L),     # 0xA5 RES 4,(IY+d),L
            partial(self.res_set, r, m, 23, 4, 239, Yd, 0),        # 0xA6 RES 4,(IY+d)
            partial(self.res_set, r, m, 23, 4, 239, Yd, 0, A),     # 0xA7 RES 4,(IY+d),A
            partial(self.res_set, r, m, 23, 4, 223, Yd, 0, B),     # 0xA8 RES 5,(IY+d),B
            partial(self.res_set, r, m, 23, 4, 223, Yd, 0, C),     # 0xA9 RES 5,(IY+d),C
            partial(self.res_set, r, m, 23, 4, 223, Yd, 0, D),     # 0xAA RES 5,(IY+d),D
            partial(self.res_set, r, m, 23, 4, 223, Yd, 0, E),     # 0xAB RES 5,(IY+d),E
            partial(self.res_set, r, m, 23, 4, 223, Yd, 0, H),     # 0xAC RES 5,(IY+d),H
            partial(self.res_set, r, m, 23, 4, 223, Yd, 0, L),     # 0xAD RES 5,(IY+d),L
            partial(self.res_set, r, m, 23, 4, 223, Yd, 0),        # 0xAE RES 5,(IY+d)
            partial(self.res_set, r, m, 23, 4, 223, Yd, 0, A),     # 0xAF RES 5,(IY+d),A
            partial(self.res_set, r, m, 23, 4, 191, Yd, 0, B),     # 0xB0 RES 6,(IY+d),B
            partial(self.res_set, r, m, 23, 4, 191, Yd, 0, C),     # 0xB1 RES 6,(IY+d),C
            partial(self.res_set, r, m, 23, 4, 191, Yd, 0, D),     # 0xB2 RES 6,(IY+d),D
            partial(self.res_set, r, m, 23, 4, 191, Yd, 0, E),     # 0xB3 RES 6,(IY+d),E
            partial(self.res_set, r, m, 23, 4, 191, Yd, 0, H),     # 0xB4 RES 6,(IY+d),H
            partial(self.res_set, r, m, 23, 4, 191, Yd, 0, L),     # 0xB5 RES 6,(IY+d),L
            partial(self.res_set, r, m, 23, 4, 191, Yd, 0),        # 0xB6 RES 6,(IY+d)
            partial(self.res_set, r, m, 23, 4, 191, Yd, 0, A),     # 0xB7 RES 6,(IY+d),A
            partial(self.res_set, r, m, 23, 4, 127, Yd, 0, B),     # 0xB8 RES 7,(IY+d),B
            partial(self.res_set, r, m, 23, 4, 127, Yd, 0, C),     # 0xB9 RES 7,(IY+d),C
            partial(self.res_set, r, m, 23, 4, 127, Yd, 0, D),     # 0xBA RES 7,(IY+d),D
            partial(self.res_set, r, m, 23, 4, 127, Yd, 0, E),     # 0xBB RES 7,(IY+d),E
            partial(self.res_set, r, m, 23, 4, 127, Yd, 0, H),     # 0xBC RES 7,(IY+d),H
            partial(self.res_set, r, m, 23, 4, 127, Yd, 0, L),     # 0xBD RES 7,(IY+d),L
            partial(self.res_set, r, m, 23, 4, 127, Yd, 0),        # 0xBE RES 7,(IY+d)
            partial(self.res_set, r, m, 23, 4, 127, Yd, 0, A),     # 0xBF RES 7,(IY+d),A
            partial(self.res_set, r, m, 23, 4, 1, Yd, 1, B),       # 0xC0 SET 0,(IY+d),B
            partial(self.res_set, r, m, 23, 4, 1, Yd, 1, C),       # 0xC1 SET 0,(IY+d),C
            partial(self.res_set, r, m, 23, 4, 1, Yd, 1, D),       # 0xC2 SET 0,(IY+d),D
            partial(self.res_set, r, m, 23, 4, 1, Yd, 1, E),       # 0xC3 SET 0,(IY+d),E
            partial(self.res_set, r, m, 23, 4, 1, Yd, 1, H),       # 0xC4 SET 0,(IY+d),H
            partial(self.res_set, r, m, 23, 4, 1, Yd, 1, L),       # 0xC5 SET 0,(IY+d),L
            partial(self.res_set, r, m, 23, 4, 1, Yd, 1),          # 0xC6 SET 0,(IY+d)
            partial(self.res_set, r, m, 23, 4, 1, Yd, 1, A),       # 0xC7 SET 0,(IY+d),A
            partial(self.res_set, r, m, 23, 4, 2, Yd, 1, B),       # 0xC8 SET 1,(IY+d),B
            partial(self.res_set, r, m, 23, 4, 2, Yd, 1, C),       # 0xC9 SET 1,(IY+d),C
            partial(self.res_set, r, m, 23, 4, 2, Yd, 1, D),       # 0xCA SET 1,(IY+d),D
            partial(self.res_set, r, m, 23, 4, 2, Yd, 1, E),       # 0xCB SET 1,(IY+d),E
            partial(self.res_set, r, m, 23, 4, 2, Yd, 1, H),       # 0xCC SET 1,(IY+d),H
            partial(self.res_set, r, m, 23, 4, 2, Yd, 1, L),       # 0xCD SET 1,(IY+d),L
            partial(self.res_set, r, m, 23, 4, 2, Yd, 1),          # 0xCE SET 1,(IY+d)
            partial(self.res_set, r, m, 23, 4, 2, Yd, 1, A),       # 0xCF SET 1,(IY+d),A
            partial(self.res_set, r, m, 23, 4, 4, Yd, 1, B),       # 0xD0 SET 2,(IY+d),B
            partial(self.res_set, r, m, 23, 4, 4, Yd, 1, C),       # 0xD1 SET 2,(IY+d),C
            partial(self.res_set, r, m, 23, 4, 4, Yd, 1, D),       # 0xD2 SET 2,(IY+d),D
            partial(self.res_set, r, m, 23, 4, 4, Yd, 1, E),       # 0xD3 SET 2,(IY+d),E
            partial(self.res_set, r, m, 23, 4, 4, Yd, 1, H),       # 0xD4 SET 2,(IY+d),H
            partial(self.res_set, r, m, 23, 4, 4, Yd, 1, L),       # 0xD5 SET 2,(IY+d),L
            partial(self.res_set, r, m, 23, 4, 4, Yd, 1),          # 0xD6 SET 2,(IY+d)
            partial(self.res_set, r, m, 23, 4, 4, Yd, 1, A),       # 0xD7 SET 2,(IY+d),A
            partial(self.res_set, r, m, 23, 4, 8, Yd, 1, B),       # 0xD8 SET 3,(IY+d),B
            partial(self.res_set, r, m, 23, 4, 8, Yd, 1, C),       # 0xD9 SET 3,(IY+d),C
            partial(self.res_set, r, m, 23, 4, 8, Yd, 1, D),       # 0xDA SET 3,(IY+d),D
            partial(self.res_set, r, m, 23, 4, 8, Yd, 1, E),       # 0xDB SET 3,(IY+d),E
            partial(self.res_set, r, m, 23, 4, 8, Yd, 1, H),       # 0xDC SET 3,(IY+d),H
            partial(self.res_set, r, m, 23, 4, 8, Yd, 1, L),       # 0xDD SET 3,(IY+d),L
            partial(self.res_set, r, m, 23, 4, 8, Yd, 1),          # 0xDE SET 3,(IY+d)
            partial(self.res_set, r, m, 23, 4, 8, Yd, 1, A),       # 0xDF SET 3,(IY+d),A
            partial(self.res_set, r, m, 23, 4, 16, Yd, 1, B),      # 0xE0 SET 4,(IY+d),B
            partial(self.res_set, r, m, 23, 4, 16, Yd, 1, C),      # 0xE1 SET 4,(IY+d),C
            partial(self.res_set, r, m, 23, 4, 16, Yd, 1, D),      # 0xE2 SET 4,(IY+d),D
            partial(self.res_set, r, m, 23, 4, 16, Yd, 1, E),      # 0xE3 SET 4,(IY+d),E
            partial(self.res_set, r, m, 23, 4, 16, Yd, 1, H),      # 0xE4 SET 4,(IY+d),H
            partial(self.res_set, r, m, 23, 4, 16, Yd, 1, L),      # 0xE5 SET 4,(IY+d),L
            partial(self.res_set, r, m, 23, 4, 16, Yd, 1),         # 0xE6 SET 4,(IY+d)
            partial(self.res_set, r, m, 23, 4, 16, Yd, 1, A),      # 0xE7 SET 4,(IY+d),A
            partial(self.res_set, r, m, 23, 4, 32, Yd, 1, B),      # 0xE8 SET 5,(IY+d),B
            partial(self.res_set, r, m, 23, 4, 32, Yd, 1, C),      # 0xE9 SET 5,(IY+d),C
            partial(self.res_set, r, m, 23, 4, 32, Yd, 1, D),      # 0xEA SET 5,(IY+d),D
            partial(self.res_set, r, m, 23, 4, 32, Yd, 1, E),      # 0xEB SET 5,(IY+d),E
            partial(self.res_set, r, m, 23, 4, 32, Yd, 1, H),      # 0xEC SET 5,(IY+d),H
            partial(self.res_set, r, m, 23, 4, 32, Yd, 1, L),      # 0xED SET 5,(IY+d),L
            partial(self.res_set, r, m, 23, 4, 32, Yd, 1),         # 0xEE SET 5,(IY+d)
            partial(self.res_set, r, m, 23, 4, 32, Yd, 1, A),      # 0xEF SET 5,(IY+d),A
            partial(self.res_set, r, m, 23, 4, 64, Yd, 1, B),      # 0xF0 SET 6,(IY+d),B
            partial(self.res_set, r, m, 23, 4, 64, Yd, 1, C),      # 0xF1 SET 6,(IY+d),C
            partial(self.res_set, r, m, 23, 4, 64, Yd, 1, D),      # 0xF2 SET 6,(IY+d),D
            partial(self.res_set, r, m, 23, 4, 64, Yd, 1, E),      # 0xF3 SET 6,(IY+d),E
            partial(self.res_set, r, m, 23, 4, 64, Yd, 1, H),      # 0xF4 SET 6,(IY+d),H
            partial(self.res_set, r, m, 23, 4, 64, Yd, 1, L),      # 0xF5 SET 6,(IY+d),L
            partial(self.res_set, r, m, 23, 4, 64, Yd, 1),         # 0xF6 SET 6,(IY+d)
            partial(self.res_set, r, m, 23, 4, 64, Yd, 1, A),      # 0xF7 SET 6,(IY+d),A
            partial(self.res_set, r, m, 23, 4, 128, Yd, 1, B),     # 0xF8 SET 7,(IY+d),B
            partial(self.res_set, r, m, 23, 4, 128, Yd, 1, C),     # 0xF9 SET 7,(IY+d),C
            partial(self.res_set, r, m, 23, 4, 128, Yd, 1, D),     # 0xFA SET 7,(IY+d),D
            partial(self.res_set, r, m, 23, 4, 128, Yd, 1, E),     # 0xFB SET 7,(IY+d),E
            partial(self.res_set, r, m, 23, 4, 128, Yd, 1, H),     # 0xFC SET 7,(IY+d),H
            partial(self.res_set, r, m, 23, 4, 128, Yd, 1, L),     # 0xFD SET 7,(IY+d),L
            partial(self.res_set, r, m, 23, 4, 128, Yd, 1),        # 0xFE SET 7,(IY+d)
            partial(self.res_set, r, m, 23, 4, 128, Yd, 1, A),     # 0xFF SET 7,(IY+d),A
        ]
