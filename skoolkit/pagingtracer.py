# Copyright 2023 Richard Dymond (rjdymond@gmail.com)
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

from skoolkit.snapshot import BANKS_128K

class PagingTracer:
    def write_port(self, registers, port, value):
        if port % 2 == 0: # pragma: no cover
            self.border = value % 8
        elif port & 0x8002 == 0:
            mem = self.simulator.memory
            if len(mem) == 0x28000:
                cur_bank = self.out7ffd & 7
                new_bank = value & 7
                if cur_bank != new_bank:
                    c = BANKS_128K[cur_bank]
                    mem[c:c + 0x4000], mem[0xC000:0x10000] = mem[0xC000:0x10000], mem[c:c + 0x4000]
                    if new_bank:
                        n = BANKS_128K[new_bank]
                        mem[n:n + 0x4000], mem[0xC000:0x10000] = mem[0xC000:0x10000], mem[n:n + 0x4000]
                if (self.out7ffd ^ value) & 16:
                    mem[0x0000:0x4000], mem[0x24000:] = mem[0x24000:], mem[0x0000:0x4000]
                self.out7ffd = value
