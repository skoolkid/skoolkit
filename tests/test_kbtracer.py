from io import StringIO
from textwrap import dedent

from skoolkittest import SkoolKitTestCase
from skoolkit import SkoolKitError
from skoolkit.kbtracer import KeyboardTracer
from skoolkit.simulator import Simulator
from skoolkit.simutils import PC, T

KEYS = {
    '1': (0xF7, 0b11111110),
    '2': (0xF7, 0b11111101),
    '3': (0xF7, 0b11111011),
    '4': (0xF7, 0b11110111),
    '5': (0xF7, 0b11101111),
    '6': (0xEF, 0b11101111),
    '7': (0xEF, 0b11110111),
    '8': (0xEF, 0b11111011),
    '9': (0xEF, 0b11111101),
    '0': (0xEF, 0b11111110),
    'q': (0xFB, 0b11111110),
    'w': (0xFB, 0b11111101),
    'e': (0xFB, 0b11111011),
    'r': (0xFB, 0b11110111),
    't': (0xFB, 0b11101111),
    'y': (0xDF, 0b11101111),
    'u': (0xDF, 0b11110111),
    'i': (0xDF, 0b11111011),
    'o': (0xDF, 0b11111101),
    'p': (0xDF, 0b11111110),
    'a': (0xFD, 0b11111110),
    's': (0xFD, 0b11111101),
    'd': (0xFD, 0b11111011),
    'f': (0xFD, 0b11110111),
    'g': (0xFD, 0b11101111),
    'h': (0xBF, 0b11101111),
    'j': (0xBF, 0b11110111),
    'k': (0xBF, 0b11111011),
    'l': (0xBF, 0b11111101),
    'ENTER': (0xBF, 0b11111110), # ENTER
    'CS': (0xFE, 0b11111110),    # CAPS SHIFT
    'z': (0xFE, 0b11111101),
    'x': (0xFE, 0b11111011),
    'c': (0xFE, 0b11110111),
    'v': (0xFE, 0b11101111),
    'b': (0x7F, 0b11101111),
    'n': (0x7F, 0b11110111),
    'm': (0x7F, 0b11111011),
    'SS': (0x7F, 0b11111101),    # SYMBOL SHIFT
    'SPACE': (0x7F, 0b11111110), # SPACE
}

class KeyboardTracerTest(SkoolKitTestCase):
    def _test_kbtracer(self, keys, exp_readings):
        memory = [0] * 65536
        loop = (
            0x21, 0xFF, 0x7F,   # $0000 LD HL,$7FFF
            0x22, 0xFE, 0x7F,   # $0003 LD ($7FFE),HL
            0xFB,               # $0006 EI
            0x18, 0xFE,         # $0007 JR $0007
        )
        memory[0:len(loop)] = loop
        int_r = (
            0x2A, 0xFE, 0x7F,   # $0038 LD HL,($7FFE)
            0x01, 0xFE, 0x7F,   # $003B LD BC,$7FFE
            0xED, 0x78,         # $003E IN A,(C)
            0xFE, 0xFF,         # $0040 CP $FF
            0x28, 0x04,         # $0042 JR Z,$0048
            0x23,               # $0044 INC HL
            0x70,               # $0045 LD (HL),B
            0x23,               # $0046 INC HL
            0x77,               # $0047 LD (HL),A
            0xCB, 0x08,         # $0048 RRC B
            0x38, 0xF2,         # $004A JR C,$003E
            0x7E,               # $004C LD A,(HL)
            0xFE, 0xFC,         # $004D CP $FC
            0x20, 0x08,         # $004F JR NZ,$0059
            0x2B,               # $0051 DEC HL
            0x7E,               # $0052 LD A,(HL)
            0x23,               # $0053 INC HL
            0xFE, 0xF7,         # $0054 CP $F7        ; Were 1 and 2 pressed?
            0xCA, 0x00, 0xC0,   # $0056 JP Z,$C000    ; Jump if so.
            0x23,               # $0059 INC HL
            0x22, 0xFE, 0x7F,   # $005A LD ($7FFE),HL
            0xFB,               # $005D EI
            0xC9,               # $005E RET
       )
        memory[56:56 + len(int_r)] = int_r
        config = {'frame_duration': 1000}
        simulator = Simulator(memory, config=config)
        delay = 0
        kbtracer = KeyboardTracer(simulator, list(keys) + ['1+2'], delay)
        simulator.set_tracer(kbtracer)
        exp_data = [0] * 3
        for reading in exp_readings:
            if len(reading) == 4:
                if reading[0] == reading[2]:
                    reading = (reading[0], reading[1] & reading[3])
                elif reading[0] > reading[2]:
                    reading = (reading[2], reading[3], reading[0], reading[1])
            exp_data.extend(reading)
            exp_data.append(0)
        exp_data.extend((0xF7, 0b11111100)) # 1+2 triggers jump to 0xC000
        kbtracer.run(0xC000, 3500000, None, None, None, None, None)
        self.assertEqual(exp_data, memory[0x8000:0x8000 + len(exp_data)])

    def test_unmodified_keys(self):
        keys = (
            '1', '2', '3', '4', '5', '6', '7', '8', '9', '0',
            'q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p',
            'a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'ENTER',
            'CS', 'z', 'x', 'c', 'v', 'b', 'n', 'm', 'SS', 'SPACE'
        )
        exp_readings = [KEYS[k] for k in keys]
        self._test_kbtracer(keys, exp_readings)

    def test_upper_case_letters(self):
        keys = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
        exp_readings = [(*KEYS['CS'], *KEYS[k.lower()]) for k in keys]
        self._test_kbtracer(keys, exp_readings)

    def test_k_mode_tokens(self):
        keys = (
            'NEW', 'BORDER', 'CONTINUE', 'DIM', 'REM', 'FOR', 'GOTO', 'GOSUB',
            'INPUT', 'LOAD', 'LIST', 'LET', 'PAUSE', 'NEXT', 'POKE', 'PRINT',
            'PLOT', 'RUN', 'SAVE', 'RANDOMIZE', 'IF', 'CLS', 'DRAW', 'CLEAR',
            'RETURN', 'COPY'
        )
        exp_readings = [KEYS[k] for k in 'abcdefghijklmnopqrstuvwxyz']
        self._test_kbtracer(keys, exp_readings)

    def test_symbol_shift_tokens(self):
        keys = (
            '!', '@', '#', '$', '%', '&', "'", '(', ')', '_', 'STOP', '*', '?',
            'STEP', '>=', 'TO', 'THEN', '^', 'AT', '-', '+', '=', '.', ',',
            ';', '"', '<=', '<', 'NOT', '>', 'OR', '/', '<>', '£', 'AND', ':'
        )
        exp_readings = [(*KEYS['SS'], *KEYS[k]) for k in '1234567890abcdefghijklmnopqrstuvwxyz']
        self._test_kbtracer(keys, exp_readings)

    def test_e_mode_tokens(self):
        keys = (
            'READ', 'BIN', 'LPRINT', 'DATA', 'TAN', 'SGN', 'ABS', 'SQR', 'CODE',
            'VAL', 'LEN', 'USR', 'PI', 'INKEY$', 'PEEK', 'TAB', 'SIN', 'INT',
            'RESTORE', 'RND', 'CHR$', 'LLIST', 'COS', 'EXP', 'STR$', 'LN'
        )
        exp_readings = []
        for k in 'abcdefghijklmnopqrstuvwxyz':
            exp_readings.append((*KEYS['CS'], *KEYS['SS']))
            exp_readings.append(KEYS[k])
        self._test_kbtracer(keys, exp_readings)

    def test_shifted_e_mode_tokens(self):
        keys = (
            'DEFFN', 'FN', 'LINE', 'OPEN#', 'CLOSE#', 'MOVE', 'ERASE', 'POINT',
            'CAT', 'FORMAT', '~', 'BRIGHT', 'PAPER', '\\', 'ATN', '{', '}',
            'CIRCLE', 'IN', 'VAL$', 'SCREEN$', 'ATTR', 'INVERSE', 'OVER', 'OUT',
            '©', 'ASN', 'VERIFY', '|', 'MERGE', ']', 'FLASH', 'ACS', 'INK', '[',
            'BEEP'
        )
        exp_readings = []
        for k in '1234567890abcdefghijklmnopqrstuvwxyz':
            exp_readings.append((*KEYS['CS'], *KEYS['SS']))
            exp_readings.append((*KEYS['SS'], *KEYS[k]))
        self._test_kbtracer(keys, exp_readings)

    def test_down(self):
        keys = ['DOWN']
        exp_readings = [(*KEYS['CS'], *KEYS['6'])]
        self._test_kbtracer(keys, exp_readings)

    def test_plus_notation(self):
        keys = []
        for k in (
                '1', '2', '3', '4', '5', '6', '7', '8', '9', '0',
                'q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p',
                'a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'ENTER',
                'CS', 'z', 'x', 'c', 'v', 'b', 'n', 'm', 'SS', 'SPACE'
        ):
            keys.extend((f'CS+{k}', f'SS+{k}'))
        exp_readings = []
        for k in keys:
            k1, k2 = k.split('+')
            exp_readings.append((*KEYS[k1], *KEYS[k2]))
        self._test_kbtracer(keys, exp_readings)

    def test_unrecognised_token(self):
        with self.assertRaises(SkoolKitError) as cm:
            KeyboardTracer(None, ['`'], 0)
        self.assertEqual(cm.exception.args[0], 'Unrecognised token: `')

    def test_unrecognised_key(self):
        with self.assertRaises(SkoolKitError) as cm:
            KeyboardTracer(None, ['CS+WHAT'], 0)
        self.assertEqual(cm.exception.args[0], 'Unrecognised key: WHAT')

    def test_trace(self):
        memory = [0] * 65536
        code = (
            0x01, 0x39, 0x30,       # $0000 LD BC,$3039
            0x11, 0xA0, 0x5B,       # $0003 LD DE,$5BA0
            0x21, 0x07, 0x87,       # $0006 LD HL,$8707
            0xDD, 0x21, 0x6E, 0xB2, # $0009 LD IX,$B26E
            0xFD, 0x21, 0xD5, 0xDD, # $000D LD IY,$DDD5
            0x90,                   # $0011 SUB B
            0xED, 0x4F,             # $0012 LD R,A
            0xED, 0x47,             # $0014 LD I,A
            0xD9,                   # $0016 EXX
            0x01, 0x98, 0xFF,       # $0017 LD BC,$FF98
            0x11, 0x31, 0xD4,       # $001A LD DE,$D431
            0x21, 0xCA, 0xA8,       # $001D LD HL,$A8CA
            0x08,                   # $0020 EX AF,AF'
            0x90,                   # $0021 SUB B
            0x31, 0x6D, 0x7D,       # $0022 LD SP,$7D6D
        )
        memory[:len(code)] = code
        stop = len(code)
        simulator = Simulator(memory)
        kbtracer = KeyboardTracer(simulator, ['ENTER'], 0)
        simulator.set_tracer(kbtracer)
        tracefile = StringIO()
        trace_line = "{t:03} ${pc:04X} {i:<13} AFBCDEHL={r[a]:02X}{r[f]:02X}{r[b]:02X}{r[c]:02X}{r[d]:02X}{r[e]:02X}{r[h]:02X}{r[l]:02X}"
        trace_line += " AFBCDEHL'={r[^a]:02X}{r[^f]:02X}{r[^b]:02X}{r[^c]:02X}{r[^d]:02X}{r[^e]:02X}{r[^h]:02X}{r[^l]:02X}"
        trace_line += " IX={r[ixh]:02X}{r[ixl]:02X} IY={r[iyh]:02X}{r[iyl]:02X} SP={r[sp]:04X} IR={r[i]:02X}{r[r]:02X}\n"
        kbtracer.run(stop, 200, tracefile, trace_line, '$', '02X', '04X')
        exp_output = """
             000 $0000 LD BC,$3039   AFBCDEHL=0000303900000000 AFBCDEHL'=0000000000000000 IX=0000 IY=5C3A SP=5C00 IR=3F01
             010 $0003 LD DE,$5BA0   AFBCDEHL=000030395BA00000 AFBCDEHL'=0000000000000000 IX=0000 IY=5C3A SP=5C00 IR=3F02
             020 $0006 LD HL,$8707   AFBCDEHL=000030395BA08707 AFBCDEHL'=0000000000000000 IX=0000 IY=5C3A SP=5C00 IR=3F03
             030 $0009 LD IX,$B26E   AFBCDEHL=000030395BA08707 AFBCDEHL'=0000000000000000 IX=B26E IY=5C3A SP=5C00 IR=3F05
             044 $000D LD IY,$DDD5   AFBCDEHL=000030395BA08707 AFBCDEHL'=0000000000000000 IX=B26E IY=DDD5 SP=5C00 IR=3F07
             058 $0011 SUB B         AFBCDEHL=D08330395BA08707 AFBCDEHL'=0000000000000000 IX=B26E IY=DDD5 SP=5C00 IR=3F08
             062 $0012 LD R,A        AFBCDEHL=D08330395BA08707 AFBCDEHL'=0000000000000000 IX=B26E IY=DDD5 SP=5C00 IR=3FD0
             071 $0014 LD I,A        AFBCDEHL=D08330395BA08707 AFBCDEHL'=0000000000000000 IX=B26E IY=DDD5 SP=5C00 IR=D0D2
             080 $0016 EXX           AFBCDEHL=D083000000000000 AFBCDEHL'=000030395BA08707 IX=B26E IY=DDD5 SP=5C00 IR=D0D3
             084 $0017 LD BC,$FF98   AFBCDEHL=D083FF9800000000 AFBCDEHL'=000030395BA08707 IX=B26E IY=DDD5 SP=5C00 IR=D0D4
             094 $001A LD DE,$D431   AFBCDEHL=D083FF98D4310000 AFBCDEHL'=000030395BA08707 IX=B26E IY=DDD5 SP=5C00 IR=D0D5
             104 $001D LD HL,$A8CA   AFBCDEHL=D083FF98D431A8CA AFBCDEHL'=000030395BA08707 IX=B26E IY=DDD5 SP=5C00 IR=D0D6
             114 $0020 EX AF,AF'     AFBCDEHL=0000FF98D431A8CA AFBCDEHL'=D08330395BA08707 IX=B26E IY=DDD5 SP=5C00 IR=D0D7
             118 $0021 SUB B         AFBCDEHL=0113FF98D431A8CA AFBCDEHL'=D08330395BA08707 IX=B26E IY=DDD5 SP=5C00 IR=D0D8
             122 $0022 LD SP,$7D6D   AFBCDEHL=0113FF98D431A8CA AFBCDEHL'=D08330395BA08707 IX=B26E IY=DDD5 SP=7D6D IR=D0D9
        """
        self.assertEqual(dedent(exp_output).strip(), tracefile.getvalue().rstrip())

    def test_trace_with_register_pairs(self):
        memory = [0] * 65536
        code = (
            0x01, 0x39, 0x30,       # $0000 LD BC,$3039
            0x11, 0xA0, 0x5B,       # $0003 LD DE,$5BA0
            0x21, 0x07, 0x87,       # $0006 LD HL,$8707
            0xDD, 0x21, 0x6E, 0xB2, # $0009 LD IX,$B26E
            0xFD, 0x21, 0xD5, 0xDD, # $000D LD IY,$DDD5
            0xD9,                   # $0011 EXX
            0x01, 0x98, 0xFF,       # $0012 LD BC,$FF98
            0x11, 0x31, 0xD4,       # $0015 LD DE,$D431
            0x21, 0xCA, 0xA8,       # $0018 LD HL,$A8CA
        )
        memory[:len(code)] = code
        stop = len(code)
        simulator = Simulator(memory)
        kbtracer = KeyboardTracer(simulator, ['ENTER'], 0)
        simulator.set_tracer(kbtracer)
        tracefile = StringIO()
        trace_line = "${pc:04X} {i:<13} BCDEHL={r[bc]:04X}{r[de]:04X}{r[hl]:04X}"
        trace_line += " BCDEHL'={r[^bc]:04X}{r[^de]:04X}{r[^hl]:04X}"
        trace_line += " IX={r[ix]:04X} IY={r[iy]:04X}\n"
        kbtracer.run(stop, 200, tracefile, trace_line, '$', '02X', '04X')
        exp_output = """
            $0000 LD BC,$3039   BCDEHL=303900000000 BCDEHL'=000000000000 IX=0000 IY=5C3A
            $0003 LD DE,$5BA0   BCDEHL=30395BA00000 BCDEHL'=000000000000 IX=0000 IY=5C3A
            $0006 LD HL,$8707   BCDEHL=30395BA08707 BCDEHL'=000000000000 IX=0000 IY=5C3A
            $0009 LD IX,$B26E   BCDEHL=30395BA08707 BCDEHL'=000000000000 IX=B26E IY=5C3A
            $000D LD IY,$DDD5   BCDEHL=30395BA08707 BCDEHL'=000000000000 IX=B26E IY=DDD5
            $0011 EXX           BCDEHL=000000000000 BCDEHL'=30395BA08707 IX=B26E IY=DDD5
            $0012 LD BC,$FF98   BCDEHL=FF9800000000 BCDEHL'=30395BA08707 IX=B26E IY=DDD5
            $0015 LD DE,$D431   BCDEHL=FF98D4310000 BCDEHL'=30395BA08707 IX=B26E IY=DDD5
            $0018 LD HL,$A8CA   BCDEHL=FF98D431A8CA BCDEHL'=30395BA08707 IX=B26E IY=DDD5
        """
        self.assertEqual(dedent(exp_output).strip(), tracefile.getvalue().rstrip())

    def test_timeout(self):
        memory = [0] * 65536
        stop = 4
        simulator = Simulator(memory)
        kbtracer = KeyboardTracer(simulator, ['ENTER'], 0)
        simulator.set_tracer(kbtracer)
        timeout = 10
        kbtracer.run(stop, timeout, None, None, None, None, None)
        self.assertEqual(simulator.registers[T], 12)
        self.assertNotEqual(simulator.registers[PC], stop)
