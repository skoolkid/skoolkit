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

from skoolkit import SkoolKitError
from skoolkit.simulator import FRAME_DURATION

KEYS = {
    '1': (0xF7FE, 0b11111110),
    '2': (0xF7FE, 0b11111101),
    '3': (0xF7FE, 0b11111011),
    '4': (0xF7FE, 0b11110111),
    '5': (0xF7FE, 0b11101111),

    '6': (0xEFFE, 0b11101111),
    '7': (0xEFFE, 0b11110111),
    '8': (0xEFFE, 0b11111011),
    '9': (0xEFFE, 0b11111101),
    '0': (0xEFFE, 0b11111110),

    'Q': (0xFBFE, 0b11111110),
    'W': (0xFBFE, 0b11111101),
    'E': (0xFBFE, 0b11111011),
    'R': (0xFBFE, 0b11110111),
    'T': (0xFBFE, 0b11101111),

    'Y': (0xDFFE, 0b11101111),
    'U': (0xDFFE, 0b11110111),
    'I': (0xDFFE, 0b11111011),
    'O': (0xDFFE, 0b11111101),
    'P': (0xDFFE, 0b11111110),

    'A': (0xFDFE, 0b11111110),
    'S': (0xFDFE, 0b11111101),
    'D': (0xFDFE, 0b11111011),
    'F': (0xFDFE, 0b11110111),
    'G': (0xFDFE, 0b11101111),

    'H': (0xBFFE, 0b11101111),
    'J': (0xBFFE, 0b11110111),
    'K': (0xBFFE, 0b11111011),
    'L': (0xBFFE, 0b11111101),
    'ENTER': (0xBFFE, 0b11111110), # ENTER

    'CS': (0xFEFE, 0b11111110),    # CAPS SHIFT
    'Z': (0xFEFE, 0b11111101),
    'X': (0xFEFE, 0b11111011),
    'C': (0xFEFE, 0b11110111),
    'V': (0xFEFE, 0b11101111),

    'B': (0x7FFE, 0b11101111),
    'N': (0x7FFE, 0b11110111),
    'M': (0x7FFE, 0b11111011),
    'SS': (0x7FFE, 0b11111101),    # SYMBOL SHIFT
    'SPACE': (0x7FFE, 0b11111110), # SPACE
}

TOKENS = {
    'NEW': 'A',
    'BORDER': 'B',
    'CONTINUE': 'C',
    'DIM': 'D',
    'REM': 'E',
    'FOR': 'F',
    'GOTO': 'G',  # GO TO
    'GOSUB': 'H', # GO SUB
    'INPUT': 'I',
    'LOAD': 'J',
    'LIST': 'K',
    'LET': 'L',
    'PAUSE': 'M',
    'NEXT': 'N',
    'POKE': 'O',
    'PRINT': 'P',
    'PLOT': 'Q',
    'RUN': 'R',
    'SAVE': 'S',
    'RANDOMIZE': 'T',
    'IF': 'U',
    'CLS': 'V',
    'DRAW': 'W',
    'CLEAR': 'X',
    'RETURN': 'Y',
    'COPY': 'Z',

    '!': 'SS+1',
    '@': 'SS+2',
    '#': 'SS+3',
    '$': 'SS+4',
    '%': 'SS+5',
    '&': 'SS+6',
    "'": 'SS+7',
    '(': 'SS+8',
    ')': 'SS+9',
    '_': 'SS+0',
    'STOP': 'SS+A',
    '*': 'SS+B',
    '?': 'SS+C',
    'STEP': 'SS+D',
    '>=': 'SS+E',
    'TO': 'SS+F',
    'THEN': 'SS+G',
    '^': 'SS+H',
    'AT': 'SS+I',
    '-': 'SS+J',
    '+': 'SS+K',
    '=': 'SS+L',
    '.': 'SS+M',
    ',': 'SS+N',
    ';': 'SS+O',
    '"': 'SS+P',
    '<=': 'SS+Q',
    '<': 'SS+R',
    'NOT': 'SS+S',
    'T': 'SS+T',
    'OR': 'SS+U',
    '/': 'SS+V',
    '<>': 'SS+W',
    '£': 'SS+X',
    'AND': 'SS+Y',
    ':': 'SS+Z',

    'READ': 'CS+SS A',
    'BIN': 'CS+SS B',
    'LPRINT': 'CS+SS C',
    'DATA': 'CS+SS D',
    'TAN': 'CS+SS E',
    'SGN': 'CS+SS F',
    'ABS': 'CS+SS G',
    'SQR': 'CS+SS H',
    'CODE': 'CS+SS I',
    'VAL': 'CS+SS J',
    'LEN': 'CS+SS K',
    'USR': 'CS+SS L',
    'PI': 'CS+SS M',
    'INKEY$': 'CS+SS N',
    'PEEK': 'CS+SS O',
    'TAB': 'CS+SS P',
    'SIN': 'CS+SS Q',
    'INT': 'CS+SS R',
    'RESTORE': 'CS+SS S',
    'RND': 'CS+SS T',
    'CHR$': 'CS+SS U',
    'LLIST': 'CS+SS V',
    'COS': 'CS+SS W',
    'EXP': 'CS+SS X',
    'STR$': 'CS+SS Y',
    'LN': 'CS+SS Z',

    'FORMAT': 'CS+SS SS+0',
    'DEFFN': 'CS+SS SS+1',  # DEF FN
    'FN': 'CS+SS SS+2',
    'LINE': 'CS+SS SS+3',
    'OPEN#': 'CS+SS SS+4',  # OPEN #
    'CLOSE#': 'CS+SS SS+5', # CLOSE #
    'MOVE': 'CS+SS SS+6',
    'ERASE': 'CS+SS SS+7',
    'POINT': 'CS+SS SS+8',
    'CAT': 'CS+SS SS+9',
    '~': 'CS+SS SS+A',
    'BRIGHT': 'CS+SS SS+B',
    'PAPER': 'CS+SS SS+C',
    '\\': 'CS+SS SS+D',
    'ATN': 'CS+SS SS+E',
    '{': 'CS+SS SS+F',
    '}': 'CS+SS SS+G',
    'CIRCLE': 'CS+SS SS+H',
    'IN': 'CS+SS SS+I',
    'VAL$': 'CS+SS SS+J',
    'SCREEN$': 'CS+SS SS+K',
    'ATTR': 'CS+SS SS+L',
    'INVERSE': 'CS+SS SS+M',
    'OVER': 'CS+SS SS+N',
    'OUT': 'CS+SS SS+O',
    '(C)': 'CS+SS SS+P',   # ©
    'ASN': 'CS+SS SS+Q',
    'VERIFY': 'CS+SS SS+R',
    '|': 'CS+SS SS+S',
    'MERGE': 'CS+SS SS+T',
    ']': 'CS+SS SS+U',
    'FLASH': 'CS+SS SS+V',
    'ACS': 'CS+SS SS+W',
    'INK': 'CS+SS SS+X',
    '[': 'CS+SS SS+Y',
    'BEEP': 'CS+SS SS+Z',
}

NO_KEY = {}

BOOT_DELAY = 4

KEY_DELAY = 4

def get_keys(keyspecs): # pragma: no cover
    keys = [NO_KEY] * BOOT_DELAY # Allow time for the boot to finish

    specs = []
    for spec in keyspecs.split():
        specs.extend(TOKENS.get(spec, spec).split())

    for spec in specs:
        kb = {}
        for p in spec.split('+', 1):
            try:
                port, a = KEYS[p]
                kb[port] = kb.get(port, 0xFF) & a
            except KeyError:
                raise SkoolKitError(f'Unrecognised token: {p}')
        if kb:
            keys.append(kb)
            # Allow time for the '5 call counter' (see 0x02BF) to reach 0
            # before the next keypress
            keys.extend([NO_KEY] * KEY_DELAY)

    return keys

class KeyboardTracer: # pragma: no cover
    def __init__(self, simulator, keys):
        self.simulator = simulator
        self.keys = get_keys(keys)
        self.border = 7

    def run(self, stop):
        simulator = self.simulator
        opcodes = simulator.opcodes
        memory = simulator.memory
        registers = simulator.registers
        keys = self.keys
        pc = registers[24]
        tstates = 0
        accept_int = False

        while True:
            t0 = tstates
            opcodes[memory[pc]]()
            tstates = registers[25]

            if simulator.iff:
                if tstates // FRAME_DURATION > t0 // FRAME_DURATION:
                    accept_int = True
                if accept_int:
                    accept_int = simulator.accept_interrupt(registers, memory, pc)
                    if not accept_int and (keys and not keys[0]):
                        keys.pop(0)

            pc = registers[24]
            if pc == stop:
                break

    def read_port(self, registers, port):
        if self.keys:
            kb = self.keys[0]
            if port in kb:
                return kb.pop(port)
        return 255

    def write_port(self, registers, port, value):
        if port % 2 == 0:
            self.border = value % 8
