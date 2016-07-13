# -*- coding: utf-8 -*-

# Copyright 2016 Richard Dymond (rjdymond@gmail.com) and Philip M. Anderson
# (weyoun47@gmail.com)
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

from skoolkit import get_word

def get_number(snapshot, i):
    if snapshot[i] == 0:
        # Small integer (signed)
        num = _get_integer(snapshot, i)
    else:
        # Floating point number (unsigned)
        num = _get_float(snapshot, i)
    return num

def _get_integer(snapshot, i):
    # See ZX Spectrum ROM routine INT_FETCH at 0x2D7F
    sign = snapshot[i + 1]
    lsb = (snapshot[i + 2] ^ sign) - sign
    if (lsb < 0):
        lsb += 256
        carry = 1
    else:
        carry = 0

    msb = ((snapshot[i + 3] + sign + carry) & 255) ^ sign

    num = 256 * msb + lsb
    if ((sign & 128) != 0):
        num *= -1

    return num

def _get_float(snapshot, i):
    exponent = snapshot[i] - 160
    mantissa = float(16777216 * (snapshot[i + 1] | 128)
                     + 65536 * snapshot[i + 2]
                     + 256 * snapshot[i + 3]
                     + snapshot[i + 4])
    num = mantissa * (2 ** exponent)
    return num
