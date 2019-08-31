# Copyright 2019 Richard Dymond (rjdymond@gmail.com)
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

from skoolkit import get_object
from skoolkit.config import get_config

SK_CONFIG = None

def get_component(component, *args):
    global SK_CONFIG
    if SK_CONFIG is None:
        SK_CONFIG = get_config('skoolkit')
    obj = get_object(SK_CONFIG[component])
    if callable(obj):
        return obj(*args)
    return obj

def get_assembler():
    return get_component('Assembler')

def get_snapshot_reader():
    return get_component('SnapshotReader')
