# Copyright 2025 Richard Dymond (rjdymond@gmail.com)
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

from skoolkit import parse_int

RST_OPCODES = (0xC7, 0xCF, 0xD7, 0xDF, 0xE7, 0xEF, 0xF7, 0xFF)

class RSTHandler:
    """
    Initialise the RST instruction handler.

    :param config: The value of the ``RSTHandlerConfig`` configuration
                   parameter in *skoolkit.ini*.
    """
    # Component API
    def __init__(self, config):
        procs = {'B': ('B', ((1, 'n'),), None), 'W': ('W', ((2, 'n'),), None)}
        self.processors = {}
        for spec in config.split(','):
            addr, sep, proc = spec.partition(':')
            if sep:
                a = parse_int(addr)
                if a is not None and a + 0xC7 in RST_OPCODES:
                    self.processors[a + 0xC7] = procs.get(proc)

    # Component API
    def handle(self, snapshot, address):
        """
        If there is an RST instruction at *address* in *snapshot* and it has
        arguments, return a sub-block descriptor for those arguments. Otherwise
        return *None*.

        :param snapshot: The memory snapshot.
        :param address: The address of an instruction.
        """
        return self.processors.get(snapshot[address])
