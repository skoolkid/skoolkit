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

from skoolkit import SkoolKitError
from skoolkit.pagingtracer import PagingTracer
from skoolkit.traceutils import Registers, disassemble

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

    'q': (0xFBFE, 0b11111110),
    'w': (0xFBFE, 0b11111101),
    'e': (0xFBFE, 0b11111011),
    'r': (0xFBFE, 0b11110111),
    't': (0xFBFE, 0b11101111),

    'y': (0xDFFE, 0b11101111),
    'u': (0xDFFE, 0b11110111),
    'i': (0xDFFE, 0b11111011),
    'o': (0xDFFE, 0b11111101),
    'p': (0xDFFE, 0b11111110),

    'a': (0xFDFE, 0b11111110),
    's': (0xFDFE, 0b11111101),
    'd': (0xFDFE, 0b11111011),
    'f': (0xFDFE, 0b11110111),
    'g': (0xFDFE, 0b11101111),

    'h': (0xBFFE, 0b11101111),
    'j': (0xBFFE, 0b11110111),
    'k': (0xBFFE, 0b11111011),
    'l': (0xBFFE, 0b11111101),
    'ENTER': (0xBFFE, 0b11111110), # ENTER

    'CS': (0xFEFE, 0b11111110),    # CAPS SHIFT
    'z': (0xFEFE, 0b11111101),
    'x': (0xFEFE, 0b11111011),
    'c': (0xFEFE, 0b11110111),
    'v': (0xFEFE, 0b11101111),

    'b': (0x7FFE, 0b11101111),
    'n': (0x7FFE, 0b11110111),
    'm': (0x7FFE, 0b11111011),
    'SS': (0x7FFE, 0b11111101),    # SYMBOL SHIFT
    'SPACE': (0x7FFE, 0b11111110), # SPACE
}

TOKENS = {
    '1': '1',
    '2': '2',
    '3': '3',
    '4': '4',
    '5': '5',
    '6': '6',
    '7': '7',
    '8': '8',
    '9': '9',
    '0': '0',

    'a': 'a',
    'b': 'b',
    'c': 'c',
    'd': 'd',
    'e': 'e',
    'f': 'f',
    'g': 'g',
    'h': 'h',
    'i': 'i',
    'j': 'j',
    'k': 'k',
    'l': 'l',
    'm': 'm',
    'n': 'n',
    'o': 'o',
    'p': 'p',
    'q': 'q',
    'r': 'r',
    's': 's',
    't': 't',
    'u': 'u',
    'v': 'v',
    'w': 'w',
    'x': 'x',
    'y': 'y',
    'z': 'z',

    'CS': 'CS', # CAPS SHIFT
    'SS': 'SS', # SYMBOL SHIFT
    'SPACE': 'SPACE',
    'ENTER': 'ENTER',

    'DOWN': 'CS+6', # Cursor down

    'A': 'CS+a',
    'B': 'CS+b',
    'C': 'CS+c',
    'D': 'CS+d',
    'E': 'CS+e',
    'F': 'CS+f',
    'G': 'CS+g',
    'H': 'CS+h',
    'I': 'CS+i',
    'J': 'CS+j',
    'K': 'CS+k',
    'L': 'CS+l',
    'M': 'CS+m',
    'N': 'CS+n',
    'O': 'CS+o',
    'P': 'CS+p',
    'Q': 'CS+q',
    'R': 'CS+r',
    'S': 'CS+s',
    'T': 'CS+t',
    'U': 'CS+u',
    'V': 'CS+v',
    'W': 'CS+w',
    'X': 'CS+x',
    'Y': 'CS+y',
    'Z': 'CS+z',

    'NEW': 'a',
    'BORDER': 'b',
    'CONTINUE': 'c',
    'DIM': 'd',
    'REM': 'e',
    'FOR': 'f',
    'GOTO': 'g',  # GO TO
    'GOSUB': 'h', # GO SUB
    'INPUT': 'i',
    'LOAD': 'j',
    'LIST': 'k',
    'LET': 'l',
    'PAUSE': 'm',
    'NEXT': 'n',
    'POKE': 'o',
    'PRINT': 'p',
    'PLOT': 'q',
    'RUN': 'r',
    'SAVE': 's',
    'RANDOMIZE': 't',
    'IF': 'u',
    'CLS': 'v',
    'DRAW': 'w',
    'CLEAR': 'x',
    'RETURN': 'y',
    'COPY': 'z',

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
    'STOP': 'SS+a',
    '*': 'SS+b',
    '?': 'SS+c',
    'STEP': 'SS+d',
    '>=': 'SS+e',
    'TO': 'SS+f',
    'THEN': 'SS+g',
    '^': 'SS+h',
    'AT': 'SS+i',
    '-': 'SS+j',
    '+': 'SS+k',
    '=': 'SS+l',
    '.': 'SS+m',
    ',': 'SS+n',
    ';': 'SS+o',
    '"': 'SS+p',
    '<=': 'SS+q',
    '<': 'SS+r',
    'NOT': 'SS+s',
    '>': 'SS+t',
    'OR': 'SS+u',
    '/': 'SS+v',
    '<>': 'SS+w',
    '£': 'SS+x',
    'AND': 'SS+y',
    ':': 'SS+z',

    'READ': 'CS+SS a',
    'BIN': 'CS+SS b',
    'LPRINT': 'CS+SS c',
    'DATA': 'CS+SS d',
    'TAN': 'CS+SS e',
    'SGN': 'CS+SS f',
    'ABS': 'CS+SS g',
    'SQR': 'CS+SS h',
    'CODE': 'CS+SS i',
    'VAL': 'CS+SS j',
    'LEN': 'CS+SS k',
    'USR': 'CS+SS l',
    'PI': 'CS+SS m',
    'INKEY$': 'CS+SS n',
    'PEEK': 'CS+SS o',
    'TAB': 'CS+SS p',
    'SIN': 'CS+SS q',
    'INT': 'CS+SS r',
    'RESTORE': 'CS+SS s',
    'RND': 'CS+SS t',
    'CHR$': 'CS+SS u',
    'LLIST': 'CS+SS v',
    'COS': 'CS+SS w',
    'EXP': 'CS+SS x',
    'STR$': 'CS+SS y',
    'LN': 'CS+SS z',

    'DEFFN': 'CS+SS SS+1',  # DEF FN
    'FN': 'CS+SS SS+2',
    'LINE': 'CS+SS SS+3',
    'OPEN#': 'CS+SS SS+4',  # OPEN #
    'CLOSE#': 'CS+SS SS+5', # CLOSE #
    'MOVE': 'CS+SS SS+6',
    'ERASE': 'CS+SS SS+7',
    'POINT': 'CS+SS SS+8',
    'CAT': 'CS+SS SS+9',
    'FORMAT': 'CS+SS SS+0',
    '~': 'CS+SS SS+a',
    'BRIGHT': 'CS+SS SS+b',
    'PAPER': 'CS+SS SS+c',
    '\\': 'CS+SS SS+d',
    'ATN': 'CS+SS SS+e',
    '{': 'CS+SS SS+f',
    '}': 'CS+SS SS+g',
    'CIRCLE': 'CS+SS SS+h',
    'IN': 'CS+SS SS+i',
    'VAL$': 'CS+SS SS+j',
    'SCREEN$': 'CS+SS SS+k',
    'ATTR': 'CS+SS SS+l',
    'INVERSE': 'CS+SS SS+m',
    'OVER': 'CS+SS SS+n',
    'OUT': 'CS+SS SS+o',
    '©': 'CS+SS SS+p',
    'ASN': 'CS+SS SS+q',
    'VERIFY': 'CS+SS SS+r',
    '|': 'CS+SS SS+s',
    'MERGE': 'CS+SS SS+t',
    ']': 'CS+SS SS+u',
    'FLASH': 'CS+SS SS+v',
    'ACS': 'CS+SS SS+w',
    'INK': 'CS+SS SS+x',
    '[': 'CS+SS SS+y',
    'BEEP': 'CS+SS SS+z',
}

NO_KEY = {}

def get_keys(keyspecs, delay):
    keys = [NO_KEY] * 4 # Delay before first keypress

    specs = []
    for spec in keyspecs:
        if '+' in spec and spec != '+':
            specs.append(spec)
        elif spec in TOKENS:
            specs.extend(TOKENS[spec].split())
        else:
            try:
                for k in spec:
                    specs.extend(TOKENS[k].split())
            except KeyError as ke:
                raise SkoolKitError(f'Unrecognised token: {ke.args[0]}')

    for spec in specs:
        kb = {}
        for p in spec.split('+', 1):
            try:
                port, a = KEYS[p]
                kb[port] = kb.get(port, 0xFF) & a
            except KeyError as ke:
                raise SkoolKitError(f'Unrecognised key: {ke.args[0]}')
        if kb:
            keys.append(kb)
            # Allow enough time between keypresses for each one to register
            keys.extend([NO_KEY] * delay)

    return keys

class KeyboardTracer(PagingTracer):
    def __init__(self, simulator, keys, delay):
        self.simulator = simulator
        self.keys = get_keys(keys, delay)
        self.border = 7
        self.out7ffd = 0
        self.outfffd = 0
        self.ay = [0] * 16
        self.outfe = 0

    def run(self, stop, timeout, tracefile, trace_line, prefix, byte_fmt, word_fmt):
        simulator = self.simulator
        memory = simulator.memory
        registers = simulator.registers
        keys = self.keys
        if tracefile:
            r = Registers(registers)

        if hasattr(simulator, 'press_keys'): # pragma: no cover
            if trace_line:
                df = lambda pc: disassemble(memory, pc, prefix, byte_fmt, word_fmt)[0]
                tf = lambda pc, i, t0: tracefile.write(trace_line.format(pc=pc, i=i, r=r, t=t0))
            else:
                df = tf = None
            simulator.press_keys(keys, stop, timeout, df, tf)
        else:
            opcodes = simulator.opcodes
            frame_duration = simulator.frame_duration
            int_active = simulator.int_active
            pc = registers[24]
            tstates = registers[25]
            while True:
                t0 = tstates
                if tracefile:
                    i = disassemble(memory, pc, prefix, byte_fmt, word_fmt)[0]
                    opcodes[memory[pc]]()
                    tracefile.write(trace_line.format(pc=pc, i=i, r=r, t=t0))
                else:
                    opcodes[memory[pc]]()
                tstates = registers[25]

                if registers[26] and tstates % frame_duration < int_active:
                    if simulator.accept_interrupt(registers, memory, pc) and keys and not keys[0]:
                        keys.pop(0)
                    tstates = registers[25]

                pc = registers[24]
                if pc == stop:
                    break

                if tstates > timeout:
                    break

    def read_port(self, registers, port):
        if self.keys:
            kb = self.keys[0]
            if port in kb:
                return kb.pop(port)
        return 255
