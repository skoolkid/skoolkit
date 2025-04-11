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

from skoolkit.snactl import get_entries

class RSTHandler:
    """
    Initialise this control directive post-processor.

    :param config: A dictionary constructed from the contents of the section of
                   *skoolkit.ini* whose name matches this post-processor.
    """
    # Component API
    def __init__(self, config):
        procs = {'DEFB': self._defb, 'DEFW': self._defw}
        self.processors = {a: procs.get(config.get(f'RST{a:02X}')) for a in range(0, 57, 8)}

    # Component API
    def process_ctls(self, ctls, subctls, snapshot):
        """
        Process control directives.

        :param ctls: A dictionary of block-level control directives.
        :param subctls: A dictionary of sub-block control directives.
        :param snapshot: The corresponding memory snapshot.
        """
        for start, end, contents in get_entries(ctls, subctls, snapshot):
            for addr, subctl, length, sublengths, comment in contents:
                if subctl == 'C':
                    processor = self.processors.get(snapshot[addr] - 0xC7)
                    if processor:
                        processor(subctls, snapshot, addr, end)

    def _defb(self, subctls, snapshot, addr, end):
        if addr + 1 < end:
            subctls[addr + 1] = ['B', 1, None, None]

    def _defw(self, subctls, snapshot, addr, end):
        if addr + 2 < end:
            subctls[addr + 1] = ['W', 2, None, None]
