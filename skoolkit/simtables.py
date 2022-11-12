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

PARITY = tuple((1 - bin(r).count('1') % 2) * 4 for r in range(256))

SZ53P = tuple(
    (r & 0xA8)           # S.5.3...
    + (r == 0) * 0x40    # .Z......
    + PARITY[r]          # .....P..
    for r in range(256)
)

ADC = tuple(tuple(tuple((
        v % 256,
        (v & 0xA8)                                           # S.5.3.N.
        + (v % 256 == 0) * 0x40                              # .Z......
        + (((a % 16) + ((v - a) % 16)) & 0x10)               # ...H....
        + ((a ^ (v - c - a) ^ 0x80) & (a ^ v) & 0x80) // 32  # .....P..
        + (v > 0xFF)                                         # .......C
    ) for v in range(a + c, a + c + 256)
    ) for a in range(256)
    ) for c in (0, 1)
)

ADC_A_A = tuple(tuple((
        ADC[f % 2][a][a][0],
        ADC[f % 2][a][a][1] | ((a % 16 == 0x0F) * 0x10)
    ) for f in range(256)
    ) for a in range(256)
)

ADD = ADC[0]

AND = tuple(tuple((
        a & n,
        SZ53P[a & n] + 0x10
    ) for n in range(256)
    ) for a in range(256)
)

BIT = tuple(tuple(tuple(
        (b == 7 and r & 0x80)         # S.....N.
        + (r & (1 << b) == 0) * 0x44  # .Z...P..
        + (r & 0x28)                  # ..5.3...
        + 0x10                        # ...H....
        + c                           # .......C
    for r in range(256)
    ) for b in range(8)
    ) for c in (0, 1)
)

CCF = tuple(tuple((
        (f & 0xC4)           # SZ...PN.
        + (a & 0x28)         # ..5.3...
        + (f & 0x01) * 0x10  # ...H....
        + (f & 0x01) ^ 0x01  # .......C
    ) for a in range(256)
    ) for f in range(256)
)

CP = tuple(tuple((
        a,
        ((a - n) & 0x80)                          # S.......
        + 0x40 * (a == n)                         # .Z......
        + (n & 0x28)                              # ..5.3...
        + (((a % 16) - (n % 16)) & 0x10)          # ...H....
        + ((a ^ n) & (a ^ (a - n)) & 0x80) // 32  # .....P..
        + 0x02                                    # ......N.
        + (n > a)                                 # .......C
    ) for n in range(256)
    ) for a in range(256)
)

CPL = tuple(tuple((
        a ^ 255,
        (f & 0xC5)            # SZ...P.C
        + ((a ^ 255) & 0x28)  # ..5.3...
        + 0x12                # ...H..N.
    ) for f in range(256)
    ) for a in range(256)
)

DAA_a = tuple(tuple(
        (a + ((f & 16 > 0 or a % 16 > 9) * 6 + (f % 2 or a > 0x99) * 0x60) * (1 - (f & 2))) % 256
    for f in range(32)
    ) for a in range(256)
)

DAA = tuple(tuple((
        DAA_a[a][f % 32],
        SZ53P[DAA_a[a][f % 32]]                                                      # SZ5.3P..
        + ((f & 0x12 == 0x12 and a % 16 < 6) or (f & 2 == 0 and a % 16 > 9)) * 0x10  # ...H....
        + (f & 0x02)                                                                 # ......N.
        + (f % 2 or a > 0x99)                                                        # .......C
    ) for f in range(256)
    ) for a in range(256)
)

DEC_r = tuple(tuple((
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

DEC = tuple(tuple(DEC_r[f % 2][r] for r in range(256)) for f in range(256))

INC_r = tuple(tuple((
        v % 256,
        (v & 0xA8)                 # S.5.3.N.
        + (v == 256) * 0x40        # .Z......
        + (v % 16 == 0x00) * 0x10  # ...H....
        + (v == 0x80) * 0x04       # .....P..
        + c                        # .......C
    ) for v in range(1, 257)
    ) for c in (0, 1)
)

INC = tuple(tuple(INC_r[f % 2][r] for r in range(256)) for f in range(256))

NEG = tuple((
        (256 - a) % 256,
        ((256 - a) & 0xA8)     # S.5.3...
        + (a == 0) * 0x40      # .Z......
        + (a % 16 > 0) * 0x10  # ...H....
        + (a == 0x80) * 0x04   # .....P..
        + 0x02                 # ......N.
        + (a > 0)              # .......C
    ) for a in range(256)
)

OR = tuple(tuple((
        a | n,
        SZ53P[a | n]
    ) for n in range(256)
    ) for a in range(256)
)

RL_r = (
    tuple((r * 2) % 256 for r in range(256)),
    tuple((r * 2) % 256 + 1 for r in range(256))
)

RL = tuple(tuple((
        RL_r[f % 2][r],
        SZ53P[RL_r[f % 2][r]]  # SZ5H3PN.
        + (r & 0x80) // 0x80   # .......C
    ) for r in range(256)
    ) for f in range(256)
)

RLC_r = tuple(r // 128 + ((r * 2) % 256) for r in range(256))

RLC = tuple((
        RLC_r[r],
        SZ53P[RLC_r[r]]       # SZ5H3PN.
        + (r & 0x80) // 0x80  # .......C
    ) for r in range(256)
)

RR_r = (
    tuple(r // 2 for r in range(256)),
    tuple(128 + r // 2 for r in range(256))
)

RR = tuple(tuple((
        RR_r[f % 2][r],
        SZ53P[RR_r[f % 2][r]]  # SZ5H3PN.
        + (r & 0x01)           # .......C
    ) for r in range(256)
    ) for f in range(256)
)

RRC_r = tuple(((r * 128) % 256) + r // 2 for r in range(256))

RRC = tuple((
        RRC_r[r],
        SZ53P[RRC_r[r]]  # SZ5H3PN.
        + (r & 0x01)     # .......C
    ) for r in range(256)
)

RLA = tuple(tuple((
        RL_r[f % 2][a],
        (f & 0xC4)                 # SZ.H.PN.
        + (RL_r[f % 2][a] & 0x28)  # ..5.3...
        + (a & 0x80) // 0x80       # .......C
    ) for f in range(256)
    ) for a in range(256)
)

RLCA = tuple(tuple((
        RLC_r[a],
        (f & 0xC4)              # SZ.H.PN.
        + (RLC_r[a] & 0x28)     # ..5.3...
        + (a & 0x80) // 0x80    # .......C
    ) for f in range(256)
    ) for a in range(256)
)

RRA = tuple(tuple((
        RR_r[f % 2][a],
        (f & 0xC4)                 # SZ.H.PN.
        + (RR_r[f % 2][a] & 0x28)  # ..5.3...
        + (a & 0x01)               # .......C
    ) for f in range(256)
    ) for a in range(256)
)

RRCA = tuple(tuple((
        RRC_r[a],
        (f & 0xC4)           # SZ.H.PN.
        + (RRC_r[a] & 0x28)  # ..5.3...
        + (a & 0x01)         # .......C
    ) for f in range(256)
    ) for a in range(256)
)

SBC = tuple(tuple(tuple((
        v % 256,
        (v & 0xA8)                                    # S.5.3...
        + (v % 256 == 0) * 0x40                       # .Z......
        + (((a % 16) - ((a - v) % 16)) & 0x10)        # ...H....
        + ((a ^ (a - v - c)) & (a ^ v) & 0x80) // 32  # .....P..
        + 0x02                                        # ......N.
        + (v < 0)                                     # .......C
    ) for v in range(a - c, a - c - 256, -1)
    ) for a in range(256)
    ) for c in (0, 1)
)

SBC_A_A = (((0x00, 0x42), (0xFF, 0xBB)) * 128,) * 256

SCF = tuple(tuple((
        (f & 0xC4)    # SZ.H.PN.
        + (a & 0x28)  # ..5.3...
        + 0x01        # .......C
    ) for a in range(256)
    ) for f in range(256)
)

SLA = RL[0]

SLL = RL[1]

SRA = tuple((
        (r & 0x80) + r // 2,
        SZ53P[(r & 0x80) + r // 2]  # SZ5H3PN.
        + (r & 0x01)                # .......C
   ) for r in range(256)
)

SRL = RR[0]

SUB = SBC[0]

XOR = tuple(tuple((
        a ^ n,
        SZ53P[a ^ n]
    ) for n in range(256)
    ) for a in range(256)
)
