# -*- coding: utf-8 -*-
import unittest

from skoolkittest import SkoolKitTestCase
from skoolkit.basic import BasicLister

class BasicListerTest(SkoolKitTestCase):
    def _test_basic(self, data, exp_output, prog=23755):
        snapshot = [0] * prog + data
        snapshot[23635:23637] = (prog % 256, prog // 256)
        basic = BasicLister().list_basic(snapshot)
        self.assertEqual(exp_output, basic.split('\n'))

    def test_incorrect_line_length(self):
        basic = [
            0, 10, 5, 0,     # Line 10, length (5 instead of 8)
            245, 34, 65, 34, # PRINT "A"
            33, 33, 33,      # !!!
            13,              # ENTER
            128              # End of BASIC area
        ]
        exp_output = ['  10 PRINT "A"!!!']
        self._test_basic(basic, exp_output)

    def test_prog_not_23755(self):
        basic = [
            0, 10, 5, 0,     # Line 10, length
            245, 34, 65, 34, # PRINT "A"
            13,              # ENTER
            128              # End of BASIC area
        ]
        exp_output = ['  10 PRINT "A"']
        self._test_basic(basic, exp_output, 23800)

    def test_integers(self):
        basic = [
            0, 10, 12, 0,                    # Line 10, length
            245, 49, 50, 51, 52,             # PRINT 1234
            14, 0, 0, 210, 4, 0,             # 1234
            13,                              # ENTER
            0, 20, 13, 0,                    # Line 20, length
            245, 45, 49, 50, 51, 52,         # PRINT -1234
            14, 0, 0, 210, 4, 0,             # 1234
            13,                              # ENTER
            0, 30, 14, 0,                    # Line 30, length
            245, 49, 50, 51, 52, 53, 54,     # PRINT 123456
            14, 145, 113, 32, 0, 0,          # 123456
            13,                              # ENTER
            0, 40, 15, 0,                    # Line 40, length
            245, 45, 49, 50, 51, 52, 53, 54, # PRINT -123456
            14, 145, 113, 32, 0, 0,          # 123456
            13,                              # ENTER
            128                              # End of BASIC area
        ]
        exp_output = [
            '  10 PRINT 1234',
            '  20 PRINT -1234',
            '  30 PRINT 123456',
            '  40 PRINT -123456'
        ]
        self._test_basic(basic, exp_output)

    def test_floating_point_numbers(self):
        basic = [
            0, 10, 11, 0,               # Line 10, length
            245, 49, 46, 51,            # PRINT 1.3
            14, 129, 38, 102, 102, 102, # 1.3 in floating point form
            13,                         # ENTER
            0, 20, 13, 0,               # Line 20, length
            245, 49, 48, 101, 50, 48,   # PRINT 10e20
            14, 198, 88, 215, 38, 183,  # 10e20 in floating point form
            13,                         # ENTER
            0, 30, 12, 0,               # Line 30, length
            245, 55, 101, 45, 56,       # PRINT 7e-8
            14, 105, 22, 82, 232, 47,   # 7e-8 in floating point form
            13,                         # ENTER
            0, 40, 12, 0,               # Line 40, length
            245, 45, 53, 46, 55,        # PRINT -5.7
            14, 131, 54, 102, 102, 102, # 5.7 in floating point form (sign is
                                        # not stored here)
            13,                         # ENTER
            128                         # End of BASIC area
        ]
        exp_output = [
            '  10 PRINT 1.3',
            '  20 PRINT 10e20',
            '  30 PRINT 7e-8',
            '  40 PRINT -5.7'
        ]
        self._test_basic(basic, exp_output)

    def test_fake_floating_point_number(self):
        basic = [
            0, 10, 11, 0,         # Line 10, length
            245, 49, 50, 51,      # PRINT 123
            14, 129, 64, 0, 0, 0, # 1.5 in floating point form
            13,                   # ENTER
            128                   # End of BASIC area
        ]
        exp_output = ['  10 PRINT 123{1.5}']
        self._test_basic(basic, exp_output)

    def test_non_ascii_characters(self):
        basic = [
            0, 10, 7, 0,              # Line 10, length
            245, 34, 94, 96, 127, 34, # PRINT "↑£©"
            13,                       # ENTER
            128                       # End of BASIC area
        ]
        exp_output = ['  10 PRINT "↑£©"']
        self._test_basic(basic, exp_output)

    def test_undefined_character_codes(self):
        basic = [
            0, 10, 6, 0,       # Line 10, length
            234, 0, 1, 30, 31, # REM ????
            13,                # ENTER
            128                # End of BASIC area
        ]
        exp_output = ['  10 REM {0x00}{0x01}{0x1E}{0x1F}']
        self._test_basic(basic, exp_output)

    def test_all_tokens(self):
        basic = [
            0,10,5,0,239,34,34,175,13,
            0,20,10,0,249,192,176,34,49,51,54,54,34,13,
            0,30,43,0,245,173,52,14,0,0,4,0,0,59,49,14,0,0,1,0,0,59,172,48,14,0,0,0,0,0,44,56,14,0,0,8,0,0,59,50,14,0,0,2,0,0,13,
            0,40,10,0,236,51,48,14,0,0,30,0,0,13,
            0,50,28,0,235,110,61,49,14,0,0,1,0,0,204,49,48,14,0,0,10,0,0,205,50,14,0,0,2,0,0,13,
            0,60,6,0,244,110,44,190,110,13,
            0,70,3,0,243,110,13,
            0,80,23,0,241,97,36,61,170,40,48,14,0,0,0,0,0,44,48,14,0,0,0,0,0,41,13,
            0,90,19,0,250,97,36,61,34,48,34,203,237,49,48,48,14,0,0,100,0,0,13,
            0,100,2,0,254,13,
            0,110,63,0,217,48,14,0,0,0,0,0,58,218,49,14,0,0,1,0,0,58,219,49,14,0,0,1,0,0,58,220,48,14,0,0,0,0,0,58,222,49,14,0,0,1,0,0,58,221,48,14,0,0,0,0,0,58,231,50,14,0,0,2,0,0,13,
            0,120,13,0,253,50,52,53,55,54,14,0,0,0,96,0,13,
            0,130,15,0,215,179,167,44,186,184,185,49,14,0,0,1,0,0,13,
            0,140,13,0,251,58,240,58,242,49,14,0,0,1,0,0,13,
            0,150,23,0,250,49,14,0,0,1,0,0,198,50,14,0,0,2,0,0,197,177,97,36,203,230,13,
            0,160,51,0,250,49,14,0,0,1,0,0,199,50,14,0,0,2,0,0,197,50,14,0,0,2,0,0,200,49,14,0,0,1,0,0,197,49,14,0,0,1,0,0,201,50,14,0,0,2,0,0,203,232,13,
            0,170,12,0,241,97,61,188,178,180,181,182,183,165,13,
            0,180,14,0,241,98,61,187,189,191,48,14,0,0,0,0,0,13,
            0,190,20,0,223,50,53,52,14,0,0,254,0,0,44,196,49,14,0,0,1,0,0,13,
            0,200,17,0,248,34,116, 104,105,115,34,202,49,48,14,0,0,10,0,0,13,
            0,210,23,0,250,195,171,40,48,14,0,0,0,0,0,44,48,14, 0,0,0,0,0,41,203,247,13,
            0,220,5,0,227,99,44,100,13,
            0,230,17,0,228,49,14,0,0,1,0,0,44,50,14,0,0,2,0,0,13,
            0,240,2,0,229,13,
            0,250,8,0,213,34,34,58,214,34,34,13,
            1,4,43,0,250,166,61,34,97,34,203,246,48,14,0,0,0,0,0,44,48,14,0,0,0,0,0,58,252,49,48,14,0,0,10,0,0,44,49,48,14,0,0,10,0,0,13,
            1,14,27,0,216,57,57,14,0,0,99,0,0,44,57,57,14,0,0,99,0,0,44,57,14,0,0,9,0,0,13,
            1,24,20,0,245,169,40,48,14,0,0,0,0,0,44,48,14,0,0,0,0,0,41,13,
            1,34,29,0,206,115,40,120,14,61,120,42,120,120,41,61,120,42,120,58,245,168,115,40,50,14,0,0,2,0,0,41,13,
            1,44,16,0,233,100,40,53,14,0,0,5,0,0,41,58,238,100,36,13,
            1,54,11,0,245,194,51,51,14,0,0,33,0,0,13,
            1,64,17,0,245,193,49,48,14,0,0,10,0,0,59,174,34,100,36,34,13,
            1,74,10,0,224,34,72,105,34,58,225,58,255,13,
            1,84,27,0,211,48,14,0,0,0,0,0,44,34,75,34,58,212,48,14,0,0,0,0,0,58,208,34,110,34,13,
            1,94,5,0,234,207,209,210,13,
            39,15,2,0,226,13,
            128
        ]
        exp_output = [
            '  10 LOAD ""CODE ',
            '  20 RANDOMIZE USR VAL "1366"',
            '  30 PRINT TAB 4;1;AT 0,8;2',
            '  40 GO TO 30',
            '  50 FOR n=1 TO 10 STEP 2',
            '  60 POKE n,PEEK n',
            '  70 NEXT n',
            '  80 LET a$=SCREEN$ (0,0)',
            '  90 IF a$="0" THEN GO SUB 100',
            ' 100 RETURN ',
            ' 110 INK 0: PAPER 1: FLASH 1: BRIGHT 0: OVER 1: INVERSE 0: BORDER 2',
            ' 120 CLEAR 24576',
            ' 130 BEEP COS PI,INT LN EXP 1',
            ' 140 CLS : LIST : PAUSE 1',
            ' 150 IF 1 AND 2 OR LEN a$ THEN NEW ',
            ' 160 IF 1<=2 OR 2>=1 OR 1<>2 THEN CONTINUE ',
            ' 170 LET a=SGN SIN TAN ASN ACS ATN RND',
            ' 180 LET b=SQR ABS IN 0',
            ' 190 OUT 254,BIN 1',
            ' 200 SAVE "this" LINE 10',
            ' 210 IF NOT ATTR (0,0) THEN RUN ',
            ' 220 READ c,d',
            ' 230 DATA 1,2',
            ' 240 RESTORE ',
            ' 250 MERGE "": VERIFY ""',
            ' 260 IF INKEY$="a" THEN PLOT 0,0: DRAW 10,10',
            ' 270 CIRCLE 99,99,9',
            ' 280 PRINT POINT (0,0)',
            ' 290 DEF FN s(x)=x*x: PRINT FN s(2)',
            ' 300 DIM d(5): INPUT d$',
            ' 310 PRINT CHR$ 33',
            ' 320 PRINT STR$ 10;VAL$ "d$"',
            ' 330 LPRINT "Hi": LLIST : COPY ',
            ' 340 OPEN #0,"K": CLOSE #0: FORMAT "n"',
            ' 350 REM CAT MOVE ERASE ',
            '9999 STOP '
        ]
        self._test_basic(basic, exp_output)

if __name__ == '__main__':
    unittest.main()
