from skoolkittest import SkoolKitTestCase
from skoolkit.basic import BasicLister, VariableLister

class BasicListerTest(SkoolKitTestCase):
    def _test_basic(self, data, exp_output, prog=23755):
        snapshot = [0] * prog + data
        snapshot[23635:23637] = (prog % 256, prog // 256)
        basic = BasicLister().list_basic(snapshot)
        self.assertEqual(exp_output, basic.split('\n'))

    def test_no_program(self):
        basic = [128]
        exp_output = ['']
        self._test_basic(basic, exp_output)

    def test_program_with_no_end_marker(self):
        basic = [
            0, 10, 5, 0,     # Line 10, length
            245, 34, 65, 34, # PRINT "A"
            13,              # ENTER
            0, 0, 0, 0, 0    # No end marker
        ]
        exp_output = [
            '  10 PRINT "A"',
            '   0 {0x00}'
        ]
        self._test_basic(basic, exp_output)

    def test_line_with_no_carriage_return(self):
        basic = [
            0, 10, 5, 0,     # Line 10, length
            245, 34, 65, 34, # PRINT "A"
            33,              # "!" (instead of ENTER)
            128              # End of BASIC area
        ]
        exp_output = ['  10 PRINT "A"!{0x80}']
        self._test_basic(basic, exp_output)

    def test_line_containing_number_marker_without_floating_point_number(self):
        basic = [
            0, 10, 6, 0,       # Line 10, length
            245, 49,           # PRINT 1
            14, 1, 0, 13, 128  # Number marker, no floating point number
        ]
        exp_output = ['  10 PRINT 1{0x0E}{0x01}{0x00}{0x0D}{0x80}']
        self._test_basic(basic, exp_output)

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

    def test_floating_point_numbers_in_def_fn(self):
        basic = [
            0, 10, 24, 0,         # Line 10, length
            206, 112, 40, 120,    # DEF FN p(x
            14, 1, 41, 61, 12, 2, # floating point placeholder
            44, 121,              # ,y
            14, 0, 0, 2, 0, 0,    # floating point placeholder
            41, 61, 120, 42, 121, # )=x*y
            13,                   # ENTER
            128                   # End of BASIC area
        ]
        exp_output = ['  10 DEF FN p(x,y)=x*y']
        self._test_basic(basic, exp_output)

    def test_floating_point_number_after_non_numeric_characters(self):
        basic = [
            0, 10, 13, 0,           # Line 10, length
            245, 49, 46, 53, 32, 8, # PRINT 1.5 {0x08}
            14, 129, 64, 0, 0, 0,   # 1.5 in floating point form
            13,                     # ENTER
            128                     # End of BASIC area
        ]
        exp_output = ['  10 PRINT 1.5 {0x08}']
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

    def test_fake_floating_point_number_is_zero(self):
        basic = [
            0, 10, 9, 0,       # Line 10, length
            245, 49,           # PRINT 1
            14, 0, 0, 0, 0, 0, # 0 in floating point form
            13,                # ENTER
            128                # End of BASIC area
        ]
        exp_output = ['  10 PRINT 1{0}']
        self._test_basic(basic, exp_output)

    def test_fake_floating_point_number_after_non_numeric_characters(self):
        basic = [
            0, 10, 11, 0,         # Line 10, length
            245, 49, 32, 8,       # PRINT 1 {0x08}
            14, 129, 64, 0, 0, 0, # 1.5 in floating point form
            13,                   # ENTER
            128                   # End of BASIC area
        ]
        exp_output = ['  10 PRINT 1 {0x08}{1.5}']
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

    def test_character_codes_16_to_23(self):
        basic = [
            0, 10, 14, 0,                                  # Line 10, length
            234, 16, 1, 17, 2, 18, 3, 19, 4, 20, 1, 21, 1, # Codes 16-21
            13,                                            # ENTER
            0, 20, 8, 0,                                   # Line 20, length
            234, 22, 13, 14, 23, 16, 17,                   # Codes 22, 23
            13,                                            # ENTER
            128                                            # End of BASIC area
        ]
        exp_output = [
            '  10 REM {0x1001}{0x1102}{0x1203}{0x1304}{0x1401}{0x1501}',
            '  20 REM {0x160D0E}{0x171011}'
        ]
        self._test_basic(basic, exp_output)

    def test_other_character_codes_below_32(self):
        basic = [
            0, 10, 10, 0,                        # Line 10, length
            234, 0, 1, 2, 3, 4, 5, 6, 7,         # REM ????????
            13,                                  # ENTER
            0, 20, 8, 0,                         # Line 20, length
            234, 8, 9, 10, 11, 12, 15,           # REM ??????
            13,                                  # ENTER
            0, 30, 10, 0,                        # Line 30, length
            234, 24, 25, 26, 27, 28, 29, 30, 31, # REM ????????
            13,                                  # ENTER
            128                                  # End of BASIC area
        ]
        exp_output = [
            '  10 REM {0x00}{0x01}{0x02}{0x03}{0x04}{0x05}{0x06}{0x07}',
            '  20 REM {0x08}{0x09}{0x0A}{0x0B}{0x0C}{0x0F}',
            '  30 REM {0x18}{0x19}{0x1A}{0x1B}{0x1C}{0x1D}{0x1E}{0x1F}'
        ]
        self._test_basic(basic, exp_output)

    def test_block_graphics(self):
        basic = [
            0, 10, 10, 0,                           # Line 10, length
            234,                                    # REM
            128, 129, 130, 131, 132, 133, 134, 135, # Block graphics
            13,                                     # ENTER
            0, 20, 10, 0,                           # Line 20, length
            234,                                    # REM
            136, 137, 138, 139, 140, 141, 142, 143, # More block graphics
            13,                                     # ENTER
            128                                     # End of BASIC area
        ]
        exp_output = [
            '  10 REM {0x80}{0x81}{0x82}{0x83}{0x84}{0x85}{0x86}{0x87}',
            '  20 REM {0x88}{0x89}{0x8A}{0x8B}{0x8C}{0x8D}{0x8E}{0x8F}'
        ]
        self._test_basic(basic, exp_output)

    def test_udgs(self):
        basic = [
            0, 10, 9, 0,                       # Line 10, length
            234,                               # REM
            144, 145, 146, 147, 148, 149, 150, # UDGs A-G
            13,                                # ENTER
            0, 20, 9, 0,                       # Line 20, length
            234,                               # REM
            151, 152, 153, 154, 155, 156, 157, # UDGs H-N
            13,                                # ENTER
            0, 30, 9, 0,                       # Line 30, length
            234,                               # REM
            158, 159, 160, 161, 162, 163, 164, # UDGs O-U
            13,                                # ENTER
            128                                # End of BASIC area
        ]
        exp_output = [
            '  10 REM {UDG-A}{UDG-B}{UDG-C}{UDG-D}{UDG-E}{UDG-F}{UDG-G}',
            '  20 REM {UDG-H}{UDG-I}{UDG-J}{UDG-K}{UDG-L}{UDG-M}{UDG-N}',
            '  30 REM {UDG-O}{UDG-P}{UDG-Q}{UDG-R}{UDG-S}{UDG-T}{UDG-U}'
        ]
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

class VariableListerTest(SkoolKitTestCase):
    def _test_variables(self, data, exp_output, vars_addr=23755):
        snapshot = [0] * vars_addr + data
        snapshot[23627:23629] = (vars_addr % 256, vars_addr // 256)
        variables = VariableLister().list_variables(snapshot)
        self.assertEqual(exp_output, variables.split('\n'))

    def test_no_variables(self):
        variables = [128]
        exp_output = ['']
        self._test_variables(variables, exp_output)

    def test_variables_with_no_end_marker(self):
        variables = [
            112,           # Number variable "p"
            0, 0, 12, 0, 0 # 12
        ]
        exp_output = ['p=12']
        self._test_variables(variables, exp_output)

    def test_strings(self):
        variables = [
            67,                         # String variable "c$"
            7, 0,                       # 7 characters long
            97, 98, 99, 32, 49, 50, 51, # "abc 123"
            68,                         # String variable "d$"
            1, 0,                       # 1 character long
            166,                        # "INKEY$" (no leading/trailing spaces)
            70,                         # String variable "f$"
            1, 0,                       # 1 character long
            168,                        # "FN " (trailing space)
            90,                         # String variable "z$"
            1, 0,                       # 1 character long
            197,                        # " OR " (leading and trailing spaces)
            128                         # End of variables area
        ]
        exp_output = [
            'c$="abc 123"',
            'd$="INKEY$"',
            'f$="FN "',
            'z$=" OR "'
        ]
        self._test_variables(variables, exp_output)

    def test_number_arrays(self):
        variables = [
            147,                     # Number array variable "s"
            28, 0,                   # Length
            1,                       # 1 dimension
            5, 0,                    # Dimension 1, length 5
            0, 0, 1, 0, 0,           # s(1)=1
            0, 0, 5, 0, 0,           # s(2)=5
            0, 255, 252, 255, 0,     # s(3)=-4
            0, 0, 0, 5, 0,           # s(4)=1280
            0, 255, 0, 5, 0,         # s(5)=-64256
            145,                     # Number array variable "q"
            35, 0,                   # Length
            2,                       # 2 dimensions
            2, 0,                    # Dimension 1, length 2
            3, 0,                    # Dimension 2, length 3
            0, 0, 11, 0, 0,          # q(1,1)=11
            0, 0, 21, 0, 0,          # q(1,2)=21
            0, 0, 31, 0, 0,          # q(1,3)=31
            0, 0, 12, 0, 0,          # q(2,1)=12
            0, 0, 22, 0, 0,          # q(2,2)=22
            0, 0, 32, 0, 0,          # q(2,3)=32
            144,                     # Number array variable "p"
            67, 0,                   # Length
            3,                       # 3 dimensions
            2, 0,                    # Dimension 1, length 2
            3, 0,                    # Dimension 2, length 3
            2, 0,                    # Dimension 3, length 2
            0, 0, 1, 0, 0,           # p(1,1,1)=1
            0, 0, 2, 0, 0,           # p(1,1,2)=2
            0, 0, 3, 0, 0,           # p(1,2,1)=3
            0, 0, 4, 0, 0,           # p(1,2,2)=4
            0, 0, 5, 0, 0,           # p(1,3,1)=5
            0, 0, 6, 0, 0,           # p(1,3,2)=6
            0, 0, 7, 0, 0,           # p(2,1,1)=7
            0, 0, 8, 0, 0,           # p(2,1,2)=8
            0, 0, 9, 0, 0,           # p(2,2,1)=9
            0, 0, 10, 0, 0,          # p(2,2,2)=10
            0, 0, 11, 0, 0,          # p(2,3,1)=11
            0, 0, 12, 0, 0,          # p(2,3,2)=12
            128                      # End of variables area
        ]
        exp_output = [
            's(5)=[1, 5, -4, 1280, -64256]',
            'q(2,3)=[[11, 21, 31], [12, 22, 32]]',
            'p(2,3,2)=[[[1, 2], [3, 4], [5, 6]], [[7, 8], [9, 10], [11, 12]]]'
        ]
        self._test_variables(variables, exp_output)

    def test_numbers_long_name(self):
        variables = [
            174, 117, 237,       # Number variable "num"
            0, 0, 25, 2, 0,      # 537
            184, 121, 250,       # Number variable "xyz"
            0, 255, 179, 231, 0, # -6221
            128                  # End of variables area
        ]
        exp_output = [
            'num=537',
            'xyz=-6221'
        ]
        self._test_variables(variables, exp_output)

    def test_character_arrays(self):
        variables = [
            196,   # Character array variable "d$"
            7, 0,  # Length
            1,     # 1 dimension
            4, 0,  # Dimension 1, length 4
            97,    # d$(1)="a"
            98,    # d$(2)="b"
            120,   # d$(3)="x"
            122,   # d$(4)="z"
            199,   # Character array variable "g$"
            11, 0, # Length
            2,     # 2 dimensions
            2, 0,  # Dimension 1, length 2
            3, 0,  # Dimension 2, length 3
            49,    # g(1,1)="1"
            50,    # g(1,2)="2"
            51,    # g(1,3)="3"
            79,    # g(2,1)="O"
            84,    # g(2,2)="T"
            90,    # g(2,3)="Z"
            200,   # Character array variable "h$"
            19, 0, # Length
            3,     # 3 dimensions
            3, 0,  # Dimension 1, length 3
            2, 0,  # Dimension 2, length 2
            2, 0,  # Dimension 3, length 2
            97,    # g(1,1,1)="a"
            98,    # g(1,1,2)="b"
            99,    # g(1,2,1)="c"
            100,   # g(1,2,2)="d"
            101,   # g(2,1,1)="e"
            102,   # g(2,1,2)="f"
            103,   # g(2,2,1)="g"
            104,   # g(2,2,2)="h"
            105,   # g(3,1,1)="i"
            106,   # g(3,1,2)="j"
            107,   # g(3,2,1)="k"
            108,   # g(3,2,2)="l"
            128    # End of variables area
        ]
        exp_output = [
            "d$(4)='abxz'",
            "g$(2,3)=['123', 'OTZ']",
            "h$(3,2,2)=[['ab', 'cd'], ['ef', 'gh'], ['ij', 'kl']]"
        ]
        self._test_variables(variables, exp_output)

    def test_control_vars(self):
        variables = [
            240,                 # FOR control variable "p"
            0, 0, 3, 0, 0,       # 3
            0, 0, 7, 0, 0,       # limit=7
            0, 0, 2, 0, 0,       # step=2
            12, 0,               # line=12
            4,                   # statement=4
            244,                 # FOR control variable "t"
            0, 255, 251, 255, 0, # -5
            0, 255, 246, 255, 0, # limit=-10
            0, 255, 251, 255, 0, # step=-5
            95, 8,               # line=2143
            2,                   # statement=2
            128                  # End of variables area
        ]
        exp_output = [
            'p=3 (limit=7, step=2, line=12, statement=4)',
            't=-5 (limit=-10, step=-5, line=2143, statement=2)'
        ]
        self._test_variables(variables, exp_output)

    def test_numbers_short_name(self):
        variables = [
            112,              # Number variable "p"
            0, 0, 12, 0, 0,   # 12
            116,              # Number variable "t"
            0, 0, 64, 0, 0,   # 64
            128               # End of variables area
        ]
        exp_output = [
            'p=12',
            't=64'
        ]
        self._test_variables(variables, exp_output)

    def test_basic_lines_skipped(self):
        variables = [
            0, 10, 12, 0,                    # Line 10, length
            245, 49, 50, 51, 52,             # PRINT 1234
            14, 0, 0, 210, 4, 0,             # 1234
            13,                              # ENTER
            39, 15, 13, 0,                   # Line 9999, length
            245, 45, 49, 50, 51, 52,         # PRINT -1234
            14, 0, 0, 210, 4, 0,             # 1234
            13,                              # ENTER
            128                              # End of variables area
        ]
        exp_output = ['']
        self._test_variables(variables, exp_output)

    def test_mixed_variables(self):
        variables = [
            65, 4, 0, 97, 115, 100, 102,                 # a$="asdf"
            130, 35, 0, 2, 2, 0, 3, 0,                   # dim b(2,3)
            0, 0, 1, 0, 0,                               # b(1,1)=1
            0, 255, 255, 255, 0,                         # b(1,2)=-1
            0, 0, 64, 0, 0,                              # b(1,3)=64
            0, 0, 128, 0, 0,                             # b(2,1)=128
            0, 0, 16, 0, 0,                              # b(2,2)=16
            0, 0, 32, 0, 0,                              # b(2,3)=32
            172,111,110,103,111,110,229,                 # longone=255
            0, 0, 255, 0, 0,                             #
            195, 8, 0, 1, 5, 0,                          # dim c$(5)
            48,                                          # c$(1)="0"
            49,                                          # c$(2)="1"
            50,                                          # c$(3)="2"
            51,                                          # c$(4)="3"
            52,                                          # c$(5)="4"
            228,                                         # FOR control var "d"
            0, 0, 1, 0, 0,                               # 1
            0, 0, 8, 0, 0,                               # limit=8
            0, 0, 1, 0, 0,                               # step=1
            4, 0,                                        # line=4
            7,                                           # statement=7
            101, 0, 0, 250, 255, 0,                      # e=65530
            0, 12, 3, 0, 243, 105, 13,                   # 12 NEXT i
            39, 7, 6, 0, 234, 116, 101, 115, 116, 13,    # 9991 REM test
            70, 5, 0, 122, 120, 99, 118, 98,             # f$="zxcvb"
            135, 33, 0, 1, 6, 0,                         # dim g(6)
            0, 0, 12, 0, 0,                              # g(1)=12
            0, 0, 13, 0, 0,                              # g(2)=13
            0, 0, 14, 0, 0,                              # g(3)=14
            0, 0, 15, 0, 0,                              # g(4)=15
            0, 0, 16, 0, 0,                              # g(5)=16
            0, 0, 17, 0, 0,                              # g(6)=17
            172, 111, 110, 103, 101, 114, 111, 110, 229, # longerone=-63741
            0, 255, 3, 7, 0,                             #
            200, 11, 0, 2, 3, 0, 2, 0,                   # dim h$(3,2)
            97,                                          # h$(1,1)="a"
            122,                                         # h$(1,2)="z"
            98,                                          # h$(2,1)="b"
            121,                                         # h$(2,2)="y"
            99,                                          # h$(3,1)="c"
            120,                                         # h$(3,2)="x"
            233,                                         # FOR control var "i"
            0, 0, 0, 1, 0,                               # 256
            0, 0, 0, 2, 0,                               # limit=512
            0, 0, 0, 1, 0,                               # step=256
            17, 0,                                       # line=17
            1,                                           # statement=1
            106, 0, 0, 36, 0, 0,                         # j=36
            0, 10, 3, 0, 245, 112, 13,                   # 10 PRINT p
            39, 15, 2, 0, 230, 13,                       # 9999 NEW
            128                                          # End of variables
        ]
        exp_output = [
            'a$="asdf"',
            'b(2,3)=[[1, -1, 64], [128, 16, 32]]',
            'longone=255',
            "c$(5)='01234'",
            'd=1 (limit=8, step=1, line=4, statement=7)',
            'e=65530',
            'f$="zxcvb"',
            'g(6)=[12, 13, 14, 15, 16, 17]',
            'longerone=-63741',
            "h$(3,2)=['az', 'by', 'cx']",
            'i=256 (limit=512, step=256, line=17, statement=1)',
            'j=36'
        ]
        self._test_variables(variables, exp_output)
