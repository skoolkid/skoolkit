# Copyright 2022-2025 Richard Dymond (rjdymond@gmail.com)
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

from skoolkit.simutils import B, C, D, E, H

class Accelerator:
    def __init__(self, name, code, offset, counter, inc, loop_time, loop_r_inc, ear, ear_mask, polarity):
        self.name = name
        self.code = code
        self.c0 = offset
        self.c1 = len(code) - offset
        self.counter = counter
        self.inc = inc
        self.loop_time = loop_time
        self.loop_r_inc = loop_r_inc
        self.ear = ear
        self.ear_mask = ear_mask
        self.polarity = polarity
        self.hits = 0

class AnyByte:
    def __eq__(self, other):
        return True # pragma: no cover

BYTE = AnyByte()

ACCELERATORS = {
    'activision': (
        'activision',
        [
            0x24,       # LD_SAMPLE INC H          [4]
            0xC8,       #           RET Z          [11/5]
            0xED, 0x78, #           IN A,(C)       [12]
            0xA8,       #           XOR B          [4]
            0xE6, 0x40, #           AND $40        [7]
            0xCA        #           JP Z,LD_SAMPLE [10]
        ],
        2,    # Offset of IN A,(C) instruction from start of loop
        H,    # Counter register
        1,    # Counter (H) is incremented
        42,   # 42 T-states per loop iteration
        6,    # R register increment per loop iteration
        B,    # EAR bit register
        0x40, # EAR mask
        0     # Zero flag is reset upon edge detection by AND $40
    ),

    'alkatraz': (
        'alkatraz',
        [
            0x04,             # LD_SAMPLE  INC B            [4]
            0x20, 0x03,       #            JR NZ,LD_SAMPLE2 [12/7]
            BYTE, BYTE, BYTE, #
            0xDB, 0xFE,       # LD_SAMPLE2 IN A,($FE)       [11]
            0x1F,             #            RRA              [4]
            0xC8,             #            RET Z            [11/5]
            0xA9,             #            XOR C            [4]
            0xE6, 0x20,       #            AND $20          [7]
            0x28, 0xF1        #            JR Z,LD_SAMPLE   [12/7]
        ],
        6,    # Offset of IN A,($FE) instruction from start of loop
        B,    # Counter register
        1,    # Counter (B) is incremented
        59,   # 59 T-states per loop iteration
        8,    # R register increment per loop iteration
        C,    # EAR bit register
        0x20, # EAR mask
        0     # Zero flag is reset upon edge detection by AND $20
    ),

    'alkatraz-05': (
        'alkatraz-05',
        [
            0x04,                         # LD_SAMPLE  INC B            [4]
            0x20, 0x05,                   #            JR NZ,LD_SAMPLE2 [12/7]
            BYTE, 0xCD, BYTE, BYTE, 0xC7, #
            0xDB, 0xFE,                   # LD_SAMPLE2 IN A,($FE)       [11]
            0x1F,                         #            RRA              [4]
            0xC8,                         #            RET Z            [11/5]
            0xA9,                         #            XOR C            [4]
            0xE6, 0x20,                   #            AND $20          [7]
            0x28, 0xEF                    #            JR Z,LD_SAMPLE   [12/7]
        ],
        8,    # Offset of IN A,($FE) instruction from start of loop
        B,    # Counter register
        1,    # Counter (B) is incremented
        59,   # 59 T-states per loop iteration
        8,    # R register increment per loop iteration
        C,    # EAR bit register
        0x20, # EAR mask
        0     # Zero flag is reset upon edge detection by AND $20
    ),

    'alkatraz-09': (
        'alkatraz-09',
        [
            0x04,                         # LD_SAMPLE  INC B            [4]
            0x20, 0x09,                   #            JR NZ,LD_SAMPLE2 [12/7]
            BYTE, 0xCD, BYTE, BYTE, 0x31, #
            BYTE, BYTE, 0xA7, 0xC9,       #
            0xDB, 0xFE,                   # LD_SAMPLE2 IN A,($FE)       [11]
            0x1F,                         #            RRA              [4]
            0xC8,                         #            RET Z            [11/5]
            0xA9,                         #            XOR C            [4]
            0xE6, 0x20,                   #            AND $20          [7]
            0x28, 0xEB                    #            JR Z,LD_SAMPLE   [12/7]
        ],
        12,   # Offset of IN A,($FE) instruction from start of loop
        B,    # Counter register
        1,    # Counter (B) is incremented
        59,   # 59 T-states per loop iteration
        8,    # R register increment per loop iteration
        C,    # EAR bit register
        0x20, # EAR mask
        0     # Zero flag is reset upon edge detection by AND $20
    ),

    'alkatraz-0a': (
        'alkatraz-0a',
        [
            0x04,                         # LD_SAMPLE  INC B            [4]
            0x20, 0x0A,                   #            JR NZ,LD_SAMPLE2 [12/7]
            BYTE, 0xCD, BYTE, BYTE, 0x31, #
            BYTE, BYTE, 0xA7, BYTE, 0xC9, #
            0xDB, 0xFE,                   # LD_SAMPLE2 IN A,($FE)       [11]
            0x1F,                         #            RRA              [4]
            0xC8,                         #            RET Z            [11/5]
            0xA9,                         #            XOR C            [4]
            0xE6, 0x20,                   #            AND $20          [7]
            0x28, 0xEA,                   #            JR Z,LD_SAMPLE   [12/7]
        ],
        13,   # Offset of IN A,($FE) instruction from start of loop
        B,    # Counter register
        1,    # Counter (B) is incremented
        59,   # 59 T-states per loop iteration
        8,    # R register increment per loop iteration
        C,    # EAR bit register
        0x20, # EAR mask
        0     # Zero flag is reset upon edge detection by AND $20
    ),

    'alkatraz-0b': (
        'alkatraz-0b',
        [
            0x04,                         # LD_SAMPLE  INC B            [4]
            0x20, 0x0B,                   #            JR NZ,LD_SAMPLE2 [12/7]
            BYTE, 0xC7, 0xCD, 0xB1, 0xFF, #
            0x31, 0xFD, 0xFF, 0xA7, 0xFB, #
            0xC9,                         #
            0xDB, 0xFE,                   # LD_SAMPLE2 IN A,($FE)       [11]
            0x1F,                         #            RRA              [4]
            0xC8,                         #            RET Z            [11/5]
            0xA9,                         #            XOR C            [4]
            0xE6, 0x20,                   #            AND $20          [7]
            0x28, 0xE9,                   #            JR Z,LD_SAMPLE   [12/7]
        ],
        14,   # Offset of IN A,($FE) instruction from start of loop
        B,    # Counter register
        1,    # Counter (B) is incremented
        59,   # 59 T-states per loop iteration
        8,    # R register increment per loop iteration
        C,    # EAR bit register
        0x20, # EAR mask
        0     # Zero flag is reset upon edge detection by AND $20
    ),

    'alkatraz2': (
        'alkatraz2',
        [
            0x04,       # LD_SAMPLE  INC B            [4]
            0x20, 0x01, #            JR NZ,LD_SAMPLE2 [12/7]
            0xC9,       #            RET              [10]
            0xDB, 0xFE, # LD_SAMPLE2 IN A,($FE)       [11]
            0x1F,       #            RRA              [4]
            0xC8,       #            RET Z            [11/5]
            0xA9,       #            XOR C            [4]
            0xE6, 0x20, #            AND $20          [7]
            0x28, 0xF3  #            JR Z,LD_SAMPLE   [12/7]
        ],
        4,    # Offset of IN A,($FE) instruction from start of loop
        B,    # Counter register
        1,    # Counter (B) is incremented
        59,   # 59 T-states per loop iteration
        8,    # R register increment per loop iteration
        C,    # EAR bit register
        0x20, # EAR mask
        0     # Zero flag is reset upon edge detection by AND $20
    ),

    'alternative': (
        'alternative',
        [
            0x04,       # LD_SAMPLE INC B          [4]
            0xC8,       #           RET Z          [11/5]
            0x3E, 0x7F, #           LD A,$7F       [7]
            0xDB, 0xFE, #           IN A,($FE)     [11]
            0xCB, 0x1F, #           RR A           [8]
            0x00,       #           NOP            [4]
            0xA9,       #           XOR C          [4]
            0xE6, 0x20, #           AND $20        [7]
            0x28, 0xF2  #           JR Z,LD_SAMPLE [12/7]
        ],
        4,    # Offset of IN A,($FE) instruction from start of loop
        B,    # Counter register
        1,    # Counter (B) is incremented
        62,   # 62 T-states per loop iteration
        10,   # R register increment per loop iteration
        C,    # EAR bit register
        0x20, # EAR mask
        0     # Zero flag is reset upon edge detection by AND $20
    ),

    'alternative2': (
        'alternative2',
        [
            0x04,       # LD_SAMPLE INC B          [4]
            0xC8,       #           RET Z          [11/5]
            0x3E, 0x7F, #           LD A,$7F       [7]
            0xDB, 0xFE, #           IN A,($FE)     [11]
            0xCB, 0x1F, #           RR A           [8]
            0xD0,       #           RET NC         [11/5]
            0xA9,       #           XOR C          [4]
            0xE6, 0x20, #           AND $20        [7]
            0x28, 0xF2  #           JR Z,LD_SAMPLE [12/7]
        ],
        4,    # Offset of IN A,($FE) instruction from start of loop
        B,    # Counter register
        1,    # Counter (B) is incremented
        63,   # 63 T-states per loop iteration
        10,   # R register increment per loop iteration
        C,    # EAR bit register
        0x20, # EAR mask
        0     # Zero flag is reset upon edge detection by AND $20
    ),

    'antirom': (
        'antirom',
        [
            0x04,       # LD_SAMPLE INC B           [4]
            0xC8,       #           RET Z           [11/5]
            0x3E, 0x7F, #           LD A,$7F        [7]
            0xDB, 0xFE, #           IN A,($FE)      [11]
            0x1F,       #           RRA             [4]
            0xD0,       #           RET NC          [11/5]
            0xA9,       #           XOR C           [4]
            0xE6, 0x20, #           AND $20         [7]
            0x20, 0xF3  #           JR NZ,LD_SAMPLE [12/7]
        ],
        4,    # Offset of IN A,($FE) instruction from start of loop
        B,    # Counter register
        1,    # Counter (B) is incremented
        59,   # 59 T-states per loop iteration
        9,    # R register increment per loop iteration
        C,    # EAR bit register
        0x20, # EAR mask
        1     # Zero flag is set upon edge detection by AND $20
    ),

    'bleepload': (
        'bleepload',
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
        4,    # Offset of IN A,($FE) instruction from start of loop
        B,    # Counter register
        1,    # Counter (B) is incremented
        58,   # 58 T-states per loop iteration
        9,    # R register increment per loop iteration
        C,    # EAR bit register
        0x20, # EAR mask
        0     # Zero flag is reset upon edge detection by AND $20
    ),

    'boguslaw-juza': (
        'boguslaw-juza',
        [
            0x04,       # LD_SAMPLE INC B          [4]
            0xC8,       #           RET Z          [11/5]
            0x3E, 0x7F, #           LD A,$7F       [7]
            0xDB, 0xFE, #           IN A,($FE)     [11]
            0x1F,       #           RRA            [4]
            0xD6, 0x00, #           SUB $00        [7]
            0xA9,       #           XOR C          [4]
            0xE6, 0x20, #           AND $20        [7]
            0x28, 0xF2  #           JR Z,LD_SAMPLE [12/7]
        ],
        4,    # Offset of IN A,($FE) instruction from start of loop
        B,    # Counter register
        1,    # Counter (B) is incremented
        61,   # 61 T-states per loop iteration
        9,    # R register increment per loop iteration
        C,    # EAR bit register
        0x20, # EAR mask
        0     # Zero flag is reset upon edge detection by AND $20
    ),

    'bulldog': (
        'bulldog',
        [
            0x04,             # LD_SAMPLE INC B          [4]
            0xC8,             #           RET Z          [11/5]
            0x3A, 0x7F, 0x00, #           LD A,($007F)   [13]
            0xDB, 0xFE,       #           IN A,($FE)     [11]
            0x1F,             #           RRA            [4]
            0xA9,             #           XOR C          [4]
            0xE6, 0x20,       #           AND $20        [7]
            0x28, 0xF3        #           JR Z,LD_SAMPLE [12/7]
        ],
        5,    # Offset of IN A,($FE) instruction from start of loop
        B,    # Counter register
        1,    # Counter (B) is incremented
        60,   # 60 T-states per loop iteration
        8,    # R register increment per loop iteration
        C,    # EAR bit register
        0x20, # EAR mask
        0     # Zero flag is reset upon edge detection by AND $20
    ),

    'codemasters': (
        'codemasters',
        [
            0x04,       # LD_SAMPLE INC B          [4]
            0xC8,       #           RET Z          [11/5]
            0x3E, 0xFE, #           LD A,$FE       [7]
            0xDB, 0xFE, #           IN A,($FE)     [11]
            0xFD, 0x6F, #           LD IYl,A       [8]
            0xA9,       #           XOR C          [4]
            0xE6, 0x40, #           AND $40        [7]
            0x28, 0xF3, #           JR Z,LD_SAMPLE [12/7]
        ],
        4,    # Offset of IN A,($FE) instruction from start of loop
        B,    # Counter register
        1,    # Counter (B) is incremented
        58,   # 58 T-states per loop iteration
        9,    # R register increment per loop iteration
        C,    # EAR bit register
        0x40, # EAR mask
        0     # Zero flag is reset upon edge detection by AND $40
    ),

    'crl': (
        'crl',
        [
            0x04,       # LD_SAMPLE INC B          [4]
            0xC8,       #           RET Z          [11/5]
            0x3E, 0x7F, #           LD A,$7F       [7]
            0xDB, 0xFE, #           IN A,($FE)     [11]
            0xB7,       #           OR A           [4]
            0xD8,       #           RET C          [11/5]
            0xA9,       #           XOR C          [4]
            0xE6, 0x40, #           AND $40        [7]
            0x28, 0xF3  #           JR Z,LD_SAMPLE [12/7]
        ],
        4,    # Offset of IN A,($FE) instruction from start of loop
        B,    # Counter register
        1,    # Counter (B) is incremented
        59,   # 59 T-states per loop iteration
        9,    # R register increment per loop iteration
        C,    # EAR bit register
        0x40, # EAR mask
        0     # Zero flag is reset upon edge detection by AND $40
    ),

    'crl2': (
        'crl2',
        [
            0x04,       # LD_SAMPLE INC B          [4]
            0xC8,       #           RET Z          [11/5]
            0xC8,       #           RET Z          [11/5]
            0x3E, 0x7F, #           LD A,$7F       [7]
            0xDB, 0xFE, #           IN A,($FE)     [11]
            0x1F,       #           RRA            [4]
            0xA9,       #           XOR C          [4]
            0xE6, 0x20, #           AND $20        [7]
            0x28, 0xF3  #           JR Z,LD_SAMPLE [12/7]
        ],
        5,    # Offset of IN A,($FE) instruction from start of loop
        B,    # Counter register
        1,    # Counter (B) is incremented
        59,   # 59 T-states per loop iteration
        9,    # R register increment per loop iteration
        C,    # EAR bit register
        0x20, # EAR mask
        0     # Zero flag is reset upon edge detection by AND $20
    ),

    'crl3': (
        'crl3',
        [
            0x04,       # LD_SAMPLE INC B          [4]
            0x28, 0x1D, #           JR Z,NO_EDGE   [12/7]
            0x3E, 0x7F, #           LD A,$7F       [7]
            0xDB, 0xFE, #           IN A,($FE)     [11]
            0x1F,       #           RRA            [4]
            0x30, 0x1B, #           JR NC,BREAK    [12/7]
            0xA9,       #           XOR C          [4]
            0xE6, 0x20, #           AND $20        [7]
            0x28, 0xF1, #           JR Z,LD_SAMPLE [12/7]
        ],
        5,    # Offset of IN A,($FE) instruction from start of loop
        B,    # Counter register
        1,    # Counter (B) is incremented
        63,   # 63 T-states per loop iteration
        9,    # R register increment per loop iteration
        C,    # EAR bit register
        0x20, # EAR mask
        0     # Zero flag is reset upon edge detection by AND $20
    ),

    'crl4': (
        'crl4',
        [
            0x04,       # LD_SAMPLE INC B          [4]
            0xC8,       #           RET Z          [11/5]
            0x3E, 0x7F, #           LD A,$7F       [7]
            0xDB, 0xFE, #           IN A,($FE)     [11]
            0x1F,       #           RRA            [4]
            0xA9,       #           XOR C          [4]
            0xE6, 0x20, #           AND $20        [7]
            0xE6, 0x20, #           AND $20        [7]
            0x28, 0xF2  #           JR Z,LD_SAMPLE [12/7]
        ],
        4,    # Offset of IN A,($FE) instruction from start of loop
        B,    # Counter register
        1,    # Counter (B) is incremented
        61,   # 61 T-states per loop iteration
        9,    # R register increment per loop iteration
        C,    # EAR bit register
        0x20, # EAR mask
        0     # Zero flag is reset upon edge detection by AND $20
    ),

    'cybexlab': (
        'cybexlab',
        [
            0x04,       # LD_SAMPLE INC B          [4]
            0xC8,       #           RET Z          [11/5]
            0xAF,       #           XOR A          [4]
            0xDB, 0xFE, #           IN A,($FE)     [11]
            0x1F,       #           RRA            [4]
            0xD0,       #           RET NC         [11/5]
            0xA9,       #           XOR C          [4]
            0xE6, 0x20, #           AND $20        [7]
            0x28, 0xF4  #           JR Z,LD_SAMPLE [12/7]
        ],
        3,    # Offset of IN A,($FE) instruction from start of loop
        B,    # Counter register
        1,    # Counter (B) is incremented
        56,   # 56 T-states per loop iteration
        9,    # R register increment per loop iteration
        C,    # EAR bit register
        0x20, # EAR mask
        0     # Zero flag is reset upon edge detection by AND $20
    ),

    'd-and-h': (
        'd-and-h',
        [
            0x04,       # LD_SAMPLE INC B          [4]
            0xC8,       #           RET Z          [11/5]
            0x3E, 0x7F, #           LD A,$7F       [7]
            0xDB, 0xFE, #           IN A,($FE)     [11]
            0xED, 0x4F, #           LD R,A         [9]
            0xA9,       #           XOR C          [4]
            0xE6, 0x40, #           AND $40        [7]
            0x28, 0xF3, #           JR Z,LD_SAMPLE [12/7]
        ],
        4,    # Offset of IN A,($FE) instruction from start of loop
        B,    # Counter register
        1,    # Counter (B) is incremented
        59,   # 59 T-states per loop iteration
        0,    # R register increment per loop iteration (irrelevant)
        C,    # EAR bit register
        0x40, # EAR mask
        0     # Zero flag is reset upon edge detection by AND $40
    ),

    'delphine': (
        'delphine',
        [
            0x04,       # LD_SAMPLE INC B          [4]
            0xC8,       #           RET Z          [11/5]
            0x3E, 0x7F, #           LD A,$7F       [7]
            0xDB, 0xFE, #           IN A,($FE)     [11]
            0xA7,       #           AND A          [4]
            0xD8,       #           RET C          [11/5]
            0xA9,       #           XOR C          [4]
            0xE6, 0x40, #           AND $40        [7]
            0x28, 0xF3, #           JR Z,LD_SAMPLE [12/7]
        ],
        4,    # Offset of IN A,($FE) instruction from start of loop
        B,    # Counter register
        1,    # Counter (B) is incremented
        59,   # 59 T-states per loop iteration
        9,    # R register increment per loop iteration
        C,    # EAR bit register
        0x40, # EAR mask
        0     # Zero flag is reset upon edge detection by AND $40
    ),

    'design-design': (
        'design-design',
        [
            0x04,             # LD_SAMPLE INC B          [4]
            0xCA, BYTE, BYTE, #           JP Z,nn        [10]
            0x3E, 0x7F,       #           LD A,$7F       [7]
            0xDB, 0xFE,       #           IN A,($FE)     [11]
            0x1F,             #           RRA            [4]
            0xA9,             #           XOR C          [4]
            0xE6, 0x20,       #           AND $20        [7]
            0x28, 0xF2        #           JR Z,LD_SAMPLE [12/7]
        ],
        6,    # Offset of IN A,($FE) instruction from start of loop
        B,    # Counter register
        1,    # Counter (B) is incremented
        59,   # 59 T-states per loop iteration
        8,    # R register increment per loop iteration
        C,    # EAR bit register
        0x20, # EAR mask
        0     # Zero flag is reset upon edge detection by AND $20
    ),

    'digital-integration': (
        'digital-integration',
        [
            0x05,       # LD_SAMPLE DEC B          [4]
            0xC8,       #           RET Z          [11/5]
            0xDB, 0xFE, #           IN A,($FE)     [11]
            0xA9,       #           XOR C          [4]
            0xE6, 0x40, #           AND $40        [7]
            0xCA        #           JP Z,LD_SAMPLE [10]
        ],
        2,    # Offset of IN A,($FE) instruction from start of loop
        B,    # Counter register
        0,    # Counter (B) is decremented
        41,   # 41 T-states per loop iteration
        6,    # R register increment per loop iteration
        C,    # EAR bit register
        0x40, # EAR mask
        0     # Zero flag is reset upon edge detection by AND $40
    ),

    'dinaload': (
        'dinaload',
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
        4,    # Offset of IN A,($FE) instruction from start of loop
        B,    # Counter register
        1,    # Counter (B) is incremented
        59,   # 59 T-states per loop iteration
        9,    # R register increment per loop iteration
        C,    # EAR bit register
        0x20, # EAR mask
        0     # Zero flag is reset upon edge detection by AND $20
    ),

    'diver': (
        'diver',
        [
            0xDB, 0xFE, #           IN A,($FE)     [11]
            0x14,       # LD_SAMPLE INC D          [4]
            0xC8,       #           RET Z          [11/5]
            0xE6, 0x40, #           AND $40        [7]
            0xA9,       #           XOR C          [4]
            0x28, 0xF7  #           JR Z,LD_SAMPLE [12/7]
        ],
        0,    # Offset of IN A,($FE) instruction from start of loop
        D,    # Counter register
        1,    # Counter (D) is incremented
        43,   # 43 T-states per loop iteration
        6,    # R register increment per loop iteration
        C,    # EAR bit register
        0x40, # EAR mask
        0     # Zero flag is reset upon edge detection by AND $40
    ),

    'ernieware': (
        'ernieware',
        [
            0x04,             # LD_SAMPLE INC B          [4]
            0xC8,             #           RET Z          [11/5]
            0x3E, 0x7F,       #           LD A,$7F       [7]
            0xDB, 0xFE,       #           IN A,($FE)     [11]
            0x1F,             #           RRA            [4]
            0xD2, BYTE, BYTE, #           JP NC,nn       [10]
            0xA9,             #           XOR C          [4]
            0xE6, 0x20,       #           AND $20        [7]
            0x28, 0xF1,       #           JR Z,LD_SAMPLE [12/7]
        ],
        4,    # Offset of IN A,($FE) instruction from start of loop
        B,    # Counter register
        1,    # Counter (B) is incremented
        64,   # 64 T-states per loop iteration
        9,    # R register increment per loop iteration
        C,    # EAR bit register
        0x20, # EAR mask
        0     # Zero flag is reset upon edge detection by AND $20
    ),

    'gargoyle2': (
        'gargoyle2',
        [
            0x04,       # LD_SAMPLE INC B          [4]
            0xC8,       #           RET Z          [11/5]
            0x3E, 0x7F, #           LD A,$7F       [7]
            0xDB, 0xFE, #           IN A,($FE)     [11]
            0x1F,       #           RRA            [4]
            0xA9,       #           XOR C          [4]
            0xD8,       #           RET C          [11/5]
            0xE6, 0x20, #           AND $20        [7]
            0x28, 0xF3  #           JR Z,LD_SAMPLE [12/7]
        ],
        4,    # Offset of IN A,($FE) instruction from start of loop
        B,    # Counter register
        1,    # Counter (B) is incremented
        59,   # 59 T-states per loop iteration
        9,    # R register increment per loop iteration
        C,    # EAR bit register
        0x20, # EAR mask
        0     # Zero flag is reset upon edge detection by AND $20
    ),

    'gremlin': (
        'gremlin',
        [
            0x04,       # LD_SAMPLE INC B          [4]
            0xC8,       #           RET Z          [11/5]
            0x3E, 0x7F, #           LD A,$7F       [7]
            0xDB, 0xFE, #           IN A,($FE)     [11]
            0xA9,       #           XOR C          [4]
            0xE6, 0x40, #           AND $40        [7]
            0x28, 0xF5  #           JR Z,LD_SAMPLE [12/7]
        ],
        4,    # Offset of IN A,($FE) instruction from start of loop
        B,    # Counter register
        1,    # Counter (B) is incremented
        50,   # 50 T-states per loop iteration
        7,    # R register increment per loop iteration
        C,    # EAR bit register
        0x40, # EAR mask
        0     # Zero flag is reset upon edge detection by AND $40
    ),

    'gremlin2': (
        'gremlin2',
        [
            0x04,       # LD_SAMPLE INC B          [4]
            0xC8,       #           RET Z          [11/5]
            0x3E, 0xFF, #           LD A,$FF       [7]
            0xDB, 0xFE, #           IN A,($FE)     [11]
            0xA9,       #           XOR C          [4]
            0xE6, 0x40, #           AND $40        [7]
            0xD8,       #           RET C          [11/5]
            0x00,       #           NOP            [4]
            0x28, 0xF3  #           JR Z,LD_SAMPLE [12/7]
        ],
        4,    # Offset of IN A,($FE) instruction from start of loop
        B,    # Counter register
        1,    # Counter (B) is incremented
        59,   # 59 T-states per loop iteration
        9,    # R register increment per loop iteration
        C,    # EAR bit register
        0x40, # EAR mask
        0     # Zero flag is reset upon edge detection by AND $40
    ),

    'housenka': (
        'housenka',
        [
            0x04,       # LD_SAMPLE INC B          [4]
            0xC8,       #           RET Z          [11/5]
            0x3E, 0xFE, #           LD A,$FE       [7]
            0xDB, 0xFE, #           IN A,($FE)     [11]
            0x1F,       #           RRA            [4]
            0xD0,       #           RET NC         [11/5]
            0xA9,       #           XOR C          [4]
            0xE6, 0x20, #           AND $20        [7]
            0x28, 0xF3, #           JR Z,LD_SAMPLE [12/7]
        ],
        4,    # Offset of IN A,($FE) instruction from start of loop
        B,    # Counter register
        1,    # Counter (B) is incremented
        59,   # 59 T-states per loop iteration
        9,    # R register increment per loop iteration
        C,    # EAR bit register
        0x20, # EAR mask
        0     # Zero flag is reset upon edge detection by AND $20
    ),

    'microprose': (
        'microprose',
        [
            0x04,       # LD_SAMPLE INC B          [4]
            0xC8,       #           RET Z          [11/5]
            0xDB, 0xFE, #           IN A,($FE)     [11]
            0x1F,       #           RRA            [4]
            0xC8,       #           RET Z          [11/5]
            0xA9,       #           XOR C          [4]
            0xE6, 0x20, #           AND $20        [7]
            0x28, 0xF5  #           JR Z,LD_SAMPLE [12/7]
        ],
        2,    # Offset of IN A,($FE) instruction from start of loop
        B,    # Counter register
        1,    # Counter (B) is incremented
        52,   # 52 T-states per loop iteration
        8,    # R register increment per loop iteration
        C,    # EAR bit register
        0x20, # EAR mask
        0     # Zero flag is reset upon edge detection by AND $20
    ),

    'microsphere': (
        'microsphere',
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
        4,    # Offset of IN A,($FE) instruction from start of loop
        B,    # Counter register
        1,    # Counter (B) is incremented
        58,   # 58 T-states per loop iteration
        9,    # R register increment per loop iteration
        C,    # EAR bit register
        0x20, # EAR mask
        0     # Zero flag is reset upon edge detection by AND $20
    ),

    'micro-style': (
        'micro-style',
        [
            0x04,       # LD_SAMPLE INC B          [4]
            0xC8,       #           RET Z          [11/5]
            0x3E, 0x7F, #           LD A,$7F       [7]
            0x3E, 0x7F, #           LD A,$7F       [7]
            0xDB, 0xFE, #           IN A,($FE)     [11]
            0x1F,       #           RRA            [4]
            0x00,       #           NOP            [4]
            0xA9,       #           XOR C          [4]
            0xE6, 0x20, #           AND $20        [7]
            0x28, 0xF1, #           JR Z,LD_SAMPLE [12/7]
        ],
        6,    # Offset of IN A,($FE) instruction from start of loop
        B,    # Counter register
        1,    # Counter (B) is incremented
        65,   # 65 T-states per loop iteration
        10,   # R register increment per loop iteration
        C,    # EAR bit register
        0x20, # EAR mask
        0     # Zero flag is reset upon edge detection by AND $20
    ),

    'mirrorsoft': (
        'mirrorsoft',
        [
            0xA7,       # LD_SAMPLE AND A          [4]
            0x04,       #           INC B          [4]
            0xC8,       #           RET Z          [11/5]
            0x3E, 0x7F, #           LD A,$7F       [7]
            0xDB, 0xFE, #           IN A,($FE)     [11]
            0x1F,       #           RRA            [4]
            0xA9,       #           XOR C          [4]
            0xE6, 0x20, #           AND $20        [7]
            0x28, 0xF3  #           JR Z,LD_SAMPLE [12/7]
        ],
        5,    # Offset of IN A,($FE) instruction from start of loop
        B,    # Counter register
        1,    # Counter (B) is incremented
        58,   # 58 T-states per loop iteration
        9,    # R register increment per loop iteration
        C,    # EAR bit register
        0x20, # EAR mask
        0     # Zero flag is reset upon edge detection by AND $20
    ),

    'mirrorsoft2': (
        'mirrorsoft2',
        [
            0x14,       # LD_SAMPLE INC D          [4]
            0xC8,       #           RET Z          [11/5]
            0x3E, 0x7F, #           LD A,$7F       [7]
            0xDB, 0xFE, #           IN A,($FE)     [11]
            0x1F,       #           RRA            [4]
            0x00,       #           NOP            [4]
            0xAB,       #           XOR E          [4]
            0xE6, 0x20, #           AND $20        [7]
            0x28, 0xF3  #           JR Z,LD_SAMPLE [12/7]
        ],
        4,    # Offset of IN A,($FE) instruction from start of loop
        D,    # Counter register
        1,    # Counter (D) is incremented
        58,   # 58 T-states per loop iteration
        9,    # R register increment per loop iteration
        E,    # EAR bit register
        0x20, # EAR mask
        0     # Zero flag is reset upon edge detection by AND $20
    ),

    'palas': (
        'palas',
        [
            0x04,       # LD_SAMPLE INC B          [4]
            0xC8,       #           RET Z          [11/5]
            0xAF,       #           XOR A          [4]
            0xDB, 0xFE, #           IN A,($FE)     [11]
            0x1F,       #           RRA            [4]
            0xB7,       #           OR A           [4]
            0xA9,       #           XOR C          [4]
            0xE6, 0x20, #           AND $20        [7]
            0x28, 0xF4, #           JR Z,LD_SAMPLE [12/7]
        ],
        3,    # Offset of IN A,($FE) instruction from start of loop
        B,    # Counter register
        1,    # Counter (B) is incremented
        55,   # 55 T-states per loop iteration
        9,    # R register increment per loop iteration
        C,    # EAR bit register
        0x20, # EAR mask
        0     # Zero flag is reset upon edge detection by AND $20
    ),

    'paul-owens': (
        'paul-owens',
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
        4,    # Offset of IN A,($FE) instruction from start of loop
        B,    # Counter register
        1,    # Counter (B) is incremented
        59,   # 59 T-states per loop iteration
        9,    # R register increment per loop iteration
        C,    # EAR bit register
        0x20, # EAR mask
        0     # Zero flag is reset upon edge detection by AND $20
    ),

    'raxoft': (
        'raxoft',
        [
            0x04,       # LD_SAMPLE INC B          [4]
            0xC8,       #           RET Z          [11/5]
            0xAF,       #           XOR A          [4]
            0xDB, 0xFE, #           IN A,($FE)     [11]
            0x1F,       #           RRA            [4]
            0x00,       #           NOP            [4]
            0xA9,       #           XOR C          [4]
            0xE6, 0x20, #           AND $20        [7]
            0x28, 0xF4  #           JR Z,LD_SAMPLE [12/7]
        ],
        3,    # Offset of IN A,($FE) instruction from start of loop
        B,    # Counter register
        1,    # Counter (B) is incremented
        55,   # 55 T-states per loop iteration
        9,    # R register increment per loop iteration
        C,    # EAR bit register
        0x20, # EAR mask
        0     # Zero flag is reset upon edge detection by AND $20
    ),

    'realtime': (
        'realtime',
        [
            0x04,       # LD_SAMPLE INC B          [4]
            0xC8,       #           RET Z          [11/5]
            0x00,       #           NOP            [4]
            0x00,       #           NOP            [4]
            0x00,       #           NOP            [4]
            0xDB, 0xFE, #           IN A,($FE)     [11]
            0x1F,       #           RRA            [4]
            0xA9,       #           XOR C          [4]
            0xE6, 0x20, #           AND $20        [7]
            0x28, 0xF3  #           JR Z,LD_SAMPLE [12/7]
        ],
        5,    # Offset of IN A,($FE) instruction from start of loop
        B,    # Counter register
        1,    # Counter (B) is incremented
        59,   # 59 T-states per loop iteration
        10,   # R register increment per loop iteration
        C,    # EAR bit register
        0x20, # EAR mask
        0     # Zero flag is reset upon edge detection by AND $20
    ),

    'rom': (
        'rom',
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
        4,    # Offset of IN A,($FE) instruction from start of loop
        B,    # Counter register
        1,    # Counter (B) is incremented
        59,   # 59 T-states per loop iteration
        9,    # R register increment per loop iteration
        C,    # EAR bit register
        0x20, # EAR mask
        0     # Zero flag is reset upon edge detection by AND $20
    ),

    'search-loader': (
        'search-loader',
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
        4,    # Offset of IN A,($FE) instruction from start of loop
        B,    # Counter register
        1,    # Counter (B) is incremented
        59,   # 59 T-states per loop iteration
        9,    # R register increment per loop iteration
        C,    # EAR bit register
        0x40, # EAR mask
        0     # Zero flag is reset upon edge detection by AND $40
    ),

    'silverbird': (
        'silverbird',
        [
            0x04,             # LD_SAMPLE INC B          [4]
            0x28, 0x15,       #           JR Z,TIMEOUT   [12/7]
            0x3A, 0x00, 0x00, #           LD A,(0)       [13]
            0x7F,             #           LD A,A         [4]
            0xDB, 0xFE,       #           IN A,($FE)     [11]
            0xA9,             #           XOR C          [4]
            0xE6, 0x40,       #           AND $40        [7]
            0x28, 0xF2        #           JR Z,LD_SAMPLE [12/7]
        ],
        7,    # Offset of IN A,($FE) instruction from start of loop
        B,    # Counter register
        1,    # Counter (B) is incremented
        62,   # 62 T-states per loop iteration
        8,    # R register increment per loop iteration
        C,    # EAR bit register
        0x40, # EAR mask
        0     # Zero flag is reset upon edge detection by AND $40
    ),

    'software-projects': (
        'software-projects',
        [
            0x3E, 0x7F, # LD_SAMPLE LD A,$7F        [7]
            0xDB, 0xFE, #           IN A,($FE)      [11]
            0xA9,       #           XOR C           [4]
            0xE6, 0x40, #           AND $40         [7]
            0x20, 0x04, #           JR NZ,EDGE      [12/7]
            0x05,       #           DEC B           [4]
            0x20, 0xF4  #           JR NZ,LD_SAMPLE [12/7]
        ],
        2,    # Offset of IN A,($FE) instruction from start of loop
        B,    # Counter register
        0,    # Counter (B) is decremented
        52,   # 52 T-states per loop iteration
        7,    # R register increment per loop iteration
        C,    # EAR bit register
        0x40, # EAR mask
        0     # Zero flag is reset upon edge detection by AND $40
    ),

    'sparklers': (
        'sparklers',
        [
            0x04,       # LD_SAMPLE INC B          [4]
            0xC8,       #           RET Z          [11/5]
            0xAF,       #           XOR A          [4]
            0xDB, 0xFE, #           IN A,($FE)     [11]
            0x1F,       #           RRA            [4]
            0x00,       #           NOP            [4]
            0x00,       #           NOP            [4]
            0xA9,       #           XOR C          [4]
            0xE6, 0x20, #           AND $20        [7]
            0x28, 0xF3  #           JR Z,LD_SAMPLE [12/7]
        ],
        3,    # Offset of IN A,($FE) instruction from start of loop
        B,    # Counter register
        1,    # Counter (B) is incremented
        59,   # 59 T-states per loop iteration
        10,   # R register increment per loop iteration
        C,    # EAR bit register
        0x20, # EAR mask
        0     # Zero flag is reset upon edge detection by AND $20
    ),

    'speedlock': (
        'speedlock',
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
        4,    # Offset of IN A,($FE) instruction from start of loop
        B,    # Counter register
        1,    # Counter (B) is incremented
        54,   # 54 T-states per loop iteration
        8,    # R register increment per loop iteration
        C,    # EAR bit register
        0x20, # EAR mask
        0     # Zero flag is reset upon edge detection by AND $20
    ),

    'suzy-soft': (
        'suzy-soft',
        [
            0x04,       # LD_SAMPLE INC B          [4]
            0xC8,       #           RET Z          [11/5]
            0x3E, 0xFB, #           LD A,$FB       [7]
            0xDB, 0xFE, #           IN A,($FE)     [11]
            0x1F,       #           RRA            [4]
            0xD0,       #           RET NC         [11/5]
            0xA9,       #           XOR C          [4]
            0xE6, 0x20, #           AND $20        [7]
            0x28, 0xF3  #           JR Z,LD_SAMPLE [12/7]
        ],
        4,    # Offset of IN A,($FE) instruction from start of loop
        B,    # Counter register
        1,    # Counter (B) is incremented
        59,   # 59 T-states per loop iteration
        9,    # R register increment per loop iteration
        C,    # EAR bit register
        0x20, # EAR mask
        0     # Zero flag is reset upon edge detection by AND $20
    ),

    'suzy-soft2': (
        'suzy-soft2',
        [
            0x04,       # LD_SAMPLE INC B          [4]
            0xC8,       #           RET Z          [11/5]
            0x3E, 0xF7, #           LD A,$F7       [7]
            0xDB, 0xFE, #           IN A,($FE)     [11]
            0x1F,       #           RRA            [4]
            0xA9,       #           XOR C          [4]
            0xE6, 0x20, #           AND $20        [7]
            0x28, 0xF4  #           JR Z,LD_SAMPLE [12/7]
        ],
        4,    # Offset of IN A,($FE) instruction from start of loop
        B,    # Counter register
        1,    # Counter (B) is incremented
        54,   # 54 T-states per loop iteration
        8,    # R register increment per loop iteration
        C,    # EAR bit register
        0x20, # EAR mask
        0     # Zero flag is reset upon edge detection by AND $20
    ),

    'tiny': (
        'tiny',
        [
            0x04,       # LD_SAMPLE INC B          [4]
            0xC8,       #           RET Z          [11/5]
            0xDB, 0xFE, #           IN A,($FE)     [11]
            0xA9,       #           XOR C          [4]
            0xE6, 0x40, #           AND $40        [7]
            0x28, 0xF7  #           JR Z,LD_SAMPLE [12/7]
        ],
        2,    # Offset of IN A,($FE) instruction from start of loop
        B,    # Counter register
        1,    # Counter (B) is incremented
        43,   # 43 T-states per loop iteration
        6,    # R register increment per loop iteration
        C,    # EAR bit register
        0x40, # EAR mask
        0     # Zero flag is reset upon edge detection by AND $40
    ),

    'us-gold': (
        'us-gold',
        [
            0x04,       # LD_SAMPLE INC B           [4]
            0xC8,       #           RET Z           [11/5]
            0x3E, 0x7F, #           LD A,$7F        [7]
            0xDB, 0xFE, #           IN A,($FE)      [11]
            0x1F,       #           RRA             [4]
            0x00,       #           NOP             [4]
            0xA9,       #           XOR C           [4]
            0xE6, 0x20, #           AND $20         [7]
            0x20, 0xF3  #           JR NZ,LD_SAMPLE [12/7]
        ],
        4,    # Offset of IN A,($FE) instruction from start of loop
        B,    # Counter register
        1,    # Counter (B) is incremented
        58,   # 58 T-states per loop iteration
        9,    # R register increment per loop iteration
        C,    # EAR bit register
        0x20, # EAR mask
        1     # Zero flag is set upon edge detection by AND $20
    ),

    'weird-science': (
        'weird-science',
        [
            0x04,       # LD_SAMPLE INC B          [4]
            0xC8,       #           RET Z          [11/5]
            0x3E, 0x7F, #           LD A,$7F       [7]
            0xDB, 0xFE, #           IN A,($FE)     [11]
            0x37,       #           SCF            [4]
            0xD0,       #           RET NC         [11/5]
            0xA9,       #           XOR C          [4]
            0xE6, 0x40, #           AND $40        [7]
            0x28, 0xF3  #           JR Z,LD_SAMPLE [12/7]
        ],
        4,    # Offset of IN A,($FE) instruction from start of loop
        B,    # Counter register
        1,    # Counter (B) is incremented
        59,   # 59 T-states per loop iteration
        9,    # R register increment per loop iteration
        C,    # EAR bit register
        0x40, # EAR mask
        0     # Zero flag is reset upon edge detection by AND $40
    ),
}
