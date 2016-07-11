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
    if snapshot[i + 1] == 0:
        # Small integer (unsigned)
        num = get_word(snapshot, i + 3)
    else:
        # Floating point number (unsigned)
        exponent = snapshot[i + 1] - 160
        mantissa = float(16777216 * (snapshot[i + 2] | 128)
                         + 65536 * snapshot[i + 3]
                         + 256 * snapshot[i + 4]
                         + snapshot[i + 5])
        num = mantissa * (2 ** exponent)
    return num
