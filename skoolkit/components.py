# Copyright 2019-2021 Richard Dymond (rjdymond@gmail.com)
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

# API
def get_value(name):
    """Return a parameter value from the ``[skoolkit]`` section of
    `skoolkit.ini`.

    :param name: The parameter name.
    """
    global SK_CONFIG
    if SK_CONFIG is None:
        SK_CONFIG = get_config('skoolkit')
    return SK_CONFIG[name]

# API
def get_component(name, *args):
    """Return a component declared in the ``[skoolkit]`` section of
    `skoolkit.ini`.

    :param name: The component name.
    :param args: Arguments passed to the component's constructor.
    """
    obj = get_object(get_value(name))
    if callable(obj):
        return obj(*args)
    return obj

def get_assembler():
    return get_component('Assembler')

def get_image_writer(*args):
    return get_component('ImageWriter', *args)

def get_instruction_utility():
    return get_component('InstructionUtility')

def get_operand_evaluator():
    return get_component('OperandEvaluator')

def get_snapshot_reader():
    return get_component('SnapshotReader')
