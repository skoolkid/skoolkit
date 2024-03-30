# Copyright 2023, 2024 Richard Dymond (rjdymond@gmail.com)
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

from skoolkit import ROM128, ROM_PLUS2, read_bin_file

ROMS = {'128K': ROM128, '+2': ROM_PLUS2}

class Memory:
    def __init__(self, banks=None, out7ffd=0, machine='128K'):
        self.banks = banks or tuple([0] * 16384 for b in range(8))
        self.roms = tuple(list(read_bin_file(r)) for r in ROMS.get(machine, ROM128))
        self.memory = [None, self.banks[5], self.banks[2], None]
        self.out7ffd(out7ffd)
        self.machine = machine

    def __getitem__(self, index):
        if isinstance(index, int):
            return self.memory[index // 0x4000][index % 0x4000]
        return [self.memory[a // 0x4000][a % 0x4000] for a in range(index.start, min(index.stop, 65536))]

    def __setitem__(self, index, value):
        self.memory[index // 0x4000][index % 0x4000] = value

    def __len__(self):
        return 0x20000

    def out7ffd(self, value):
        self.memory[0] = self.roms[(value % 32) // 16]
        self.memory[3] = self.banks[value % 8]
        self.o7ffd = value

    def convert(self): # pragma: no cover
        # Prepare for use by a CSimulator
        rom_id = (self.o7ffd % 32) // 16
        page = self.o7ffd % 8
        self.roms = tuple(bytearray(rom) for rom in self.roms)
        self.banks = [bytearray(bank) for bank in self.banks]
        self.memory = [self.roms[rom_id], self.banks[5], self.banks[2], self.banks[page]]

class PagingTracer:
    def write_port(self, registers, port, value):
        if port % 2 == 0:
            self.border = value % 8
            self.outfe = value
        elif port & 0x8002 == 0 and self.out7ffd & 32 == 0:
            memory = self.simulator.memory
            if isinstance(memory, Memory):
                memory.out7ffd(value)
                self.out7ffd = value
        elif port == 0xFFFD:
            self.outfffd = value
        elif port == 0xBFFD:
            self.ay[self.outfffd % 16] = value
