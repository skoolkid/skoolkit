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

class Accelerator:
    def __init__(self, code, in_time, loop_time, loop_r_inc, ear_mask):
        self.opcode = code[0]
        self.code = code[1:]
        self.in_time = in_time
        self.loop_time = loop_time
        self.loop_r_inc = loop_r_inc
        self.ear_mask = ear_mask

ACCELERATORS = {
    'bleepload': Accelerator(
        [
            0x04,       # LD_SAMPLE INC B          [4]
            0xC8,       #           RET Z          [11/5]
            0x3E, 0x7F, #           LD A,$7F       [7]
            0xDB, 0xFE, #           IN A,($FE)     [11]
            0x1F,       #           RRA            [4]
            0x00,       #           NOP            [4]
            0xA9,       #           XOR C          [4]
            0xE6, 0x20, #           AND $20        [7]
            0x28, 0xF3  #           JR Z,LD_SAMPLE [12/7]
        ],
        16,   # 16 T-states until first IN A,($FE)
        58,   # 58 T-states per loop iteration
        9,    # R register increment per loop iteration
        0x20  # EAR mask
    ),

    'digital-integration': Accelerator(
        [
            0x05,       # LD_SAMPLE DEC B          [4]
            0xC8,       #           RET Z          [11/5]
            0xDB, 0xFE, #           IN A,($FE)     [11]
            0xA9,       #           XOR C          [4]
            0xE6, 0x40, #           AND $40        [7]
            0xCA        #           JP Z,LD_SAMPLE [10]
        ],
        9,    # 9 T-states until first IN A,($FE)
        41,   # 41 T-states per loop iteration
        6,    # R register increment per loop iteration
        0x40  # EAR mask
    ),

    'dinaload': Accelerator(
        [
            0x04,       # LD_SAMPLE INC B          [4]
            0xC8,       #           RET Z          [11/5]
            0x3E, 0xFF, #           LD A,$FF       [7]
            0xDB, 0xFE, #           IN A,($FE)     [11]
            0x1F,       #           RRA            [4]
            0xD0,       #           RET NC         [11/5]
            0xA9,       #           XOR C          [4]
            0xE6, 0x20, #           AND $20        [7]
            0x28, 0xF3  #           JR Z,LD_SAMPLE [12/7]
        ],
        16,   # 16 T-states until first IN A,($FE)
        59,   # 59 T-states per loop iteration
        9,    # R register increment per loop iteration
        0x20  # EAR mask
    ),

    'microsphere': Accelerator(
        [
            0x04,       # LD_SAMPLE INC B          [4]
            0xC8,       #           RET Z          [11/5]
            0x3E, 0x7F, #           LD A,$7F       [7]
            0xDB, 0xFE, #           IN A,($FE)     [11]
            0x1F,       #           RRA            [4]
            0xA7,       #           AND A          [4]
            0xA9,       #           XOR C          [4]
            0xE6, 0x20, #           AND $20        [7]
            0x28, 0xF3  #           JR Z,LD_SAMPLE [12/7]
        ],
        16,   # 16 T-states until first IN A,($FE)
        58,   # 58 T-states per loop iteration
        9,    # R register increment per loop iteration
        0x20  # EAR mask
    ),

    'paul-owens': Accelerator(
        [
            0x04,       # LD_SAMPLE INC B          [4]
            0xC8,       #           RET Z          [11/5]
            0x3E, 0x7F, #           LD A,$7F       [7]
            0xDB, 0xFE, #           IN A,($FE)     [11]
            0x1F,       #           RRA            [4]
            0xC8,       #           RET Z          [11/5]
            0xA9,       #           XOR C          [4]
            0xE6, 0x20, #           AND $20        [7]
            0x28, 0xF3  #           JR Z,LD_SAMPLE [12/7]
        ],
        16,   # 16 T-states until first IN A,($FE)
        59,   # 59 T-states per loop iteration
        9,    # R register increment per loop iteration
        0x20  # EAR mask
    ),

    'rom': Accelerator(
        [
            0x04,       # LD_SAMPLE INC B          [4]
            0xC8,       #           RET Z          [11/5]
            0x3E, 0x7F, #           LD A,$7F       [7]
            0xDB, 0xFE, #           IN A,($FE)     [11]
            0x1F,       #           RRA            [4]
            0xD0,       #           RET NC         [11/5]
            0xA9,       #           XOR C          [4]
            0xE6, 0x20, #           AND $20        [7]
            0x28, 0xF3  #           JR Z,LD_SAMPLE [12/7]
        ],
        16,   # 16 T-states until first IN A,($FE)
        59,   # 59 T-states per loop iteration
        9,    # R register increment per loop iteration
        0x20  # EAR mask
    ),

    'search-loader': Accelerator(
        [
            0x04,       # LD_SAMPLE INC B          [4]
            0xC8,       #           RET Z          [11/5]
            0x3E, 0x00, #           LD A,$00       [7]
            0xDB, 0xFE, #           IN A,($FE)     [11]
            0xA9,       #           XOR C          [4]
            0xE6, 0x40, #           AND $40        [7]
            0xD8,       #           RET C          [11/5]
            0x00,       #           NOP            [4]
            0x28, 0xF3  #           JR Z,LD_SAMPLE [12/7]
        ],
        16,   # 16 T-states until first IN A,($FE)
        59,   # 59 T-states per loop iteration
        9,    # R register increment per loop iteration
        0x40  # EAR mask
    ),

    'speedlock': Accelerator(
        [
            0x04,       # LD_SAMPLE INC B          [4]
            0xC8,       #           RET Z          [11/5]
            0x3E, 0x7F, #           LD A,$7F       [7]
            0xDB, 0xFE, #           IN A,($FE)     [11]
            0x1F,       #           RRA            [4]
            0xA9,       #           XOR C          [4]
            0xE6, 0x20, #           AND $20        [7]
            0x28, 0xF4  #           JR Z,LD_SAMPLE [12/7]
        ],
        16,   # 16 T-states until first IN A,($FE)
        54,   # 54 T-states per loop iteration
        8,    # R register increment per loop iteration
        0x20  # EAR mask
    ),
}

ACCELERATORS['cyberlode'] = ACCELERATORS['bleepload']
ACCELERATORS['edge'] = ACCELERATORS['rom']
ACCELERATORS['elite-uni-loader'] = ACCELERATORS['speedlock']
ACCELERATORS['excelerator'] = ACCELERATORS['bleepload']
ACCELERATORS['flash-loader'] = ACCELERATORS['rom']
ACCELERATORS['ftl'] = ACCELERATORS['speedlock']
ACCELERATORS['gargoyle'] = ACCELERATORS['speedlock']
ACCELERATORS['hewson-slowload'] = ACCELERATORS['rom']
ACCELERATORS['injectaload'] = ACCELERATORS['bleepload']
ACCELERATORS['poliload'] = ACCELERATORS['dinaload']
ACCELERATORS['power-load'] = ACCELERATORS['bleepload']
ACCELERATORS['softlock'] = ACCELERATORS['rom']
ACCELERATORS['zydroload'] = ACCELERATORS['speedlock']
