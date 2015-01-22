# -*- coding: utf-8 -*-
import unittest

from skoolkittest import SkoolKitTestCase
from skoolkit.skoolsft import SftWriter

TEST_SKOOL = r"""; Dangling comment not associated with any entry

; Data definition entry
d49152 DEFB 0 ; Comment 1
 49153 DEFW 0 ; Comment 2

; Remote entry
r24576 other
 24579

@start
@org=32768

; Routine
;
; @ignoredua
; Routine description
;
; A Some value
; B Another value
; @label=START
; @isub=DI
c32768 NOP          ; Do nothing
; @bfix=DEFB 1,3
 32769 DEFB 1,2     ; 1-line B sub-block
; @ignoreua
 32771 DEFB 3       ; {2-line B sub-block
; @ssub=DEFB 5,6
 32772 DEFB 4,5     ; }
; @ignoremrcua
; Mid-block comment
 32774 DEFM "Hello" ; T sub-block
; @keep
 32779 DEFW 12345   ; W sub-block
; @nowarn
 32781 DEFS 2       ; S sub-block
; @nolabel
; @ofix=LD A,6
*32783 LD A,5       ; {Sub-block with instructions of various types
; @rem=Hello!
 32785 DEFB 0       ;
; @rsub=DEFB 3
 32786 DEFW 0,1     ;
 32790 DEFM "Hi"    ;
 32792 DEFS 3       ; }
 32795 RET          ; Return
                    ; comment continuation line
; End comment paragraph 1.
; .
; End comment paragraph 2.

; Test ASM block directives
b32796 DEFB 0
@bfix-begin
 32797 DEFB 1
@bfix+else
       DEFB 101
@bfix+end
 32798 DEFB 2
; @isub+begin
       DEFB 102
; @isub-else
 32799 DEFB 3
; @isub-end
@ofix-begin
 32800 DEFB 4
; @ofix+else
 32800 DEFB 104
@ofix+end
; @rfix+begin
       DEFB 205
; @rfix+end
; @rsub-begin
 32802 DEFB 5
; @rsub-end

; Ignore block
i32803 DEFB 56  ; Set 32803 to 56
 32804 DEFW 512

; Data block
b49152 DEFB 0

; Game status buffer entry
g49153 DEFW 0

; Message
t49155 DEFM "Lo"

; Unused block
u49157 DEFB 128

; Word block
w49158 DEFW 2
 49160 DEFW 4

; Zero block
s49162 DEFS 10
@end

; Block that starts with an invalid control character
a49172 DEFB 0

; Complex DEFB statements
b49173 DEFB 1,2,3,"Hello",5,6
 49183 DEFB "Goodbye",7,8,9

; Complex DEFM statements
t49193 DEFM "\"Hi!\"",1,2,3,4,5
 49203 DEFM 6,"C:\\DOS>",7,8

; Data block with sequences of complex DEFB statements amenable to abbreviation
b49213 DEFB 1,"Hi"
 49216 DEFB 4,"Lo"
 49219 DEFB 7
 49220 DEFB 8,9,"A"
 49223 DEFB 10,11,"B"
 49226 DEFB 12,13,"C"

; Another ignore block
i49229
"""

TEST_SFT = """; Dangling comment not associated with any entry

; Data definition entry
d49152 DEFB 0 ; Comment 1
 49153 DEFW 0 ; Comment 2

; Remote entry
r24576 other
 24579

@start
@org=32768

; Routine
;
; @ignoredua
; Routine description
;
; A Some value
; B Another value
; @label=START
; @isub=DI
cC32768,1;20 Do nothing
; @bfix=DEFB 1,3
 B32769,2;20 1-line B sub-block
; @ignoreua
 B32771,1;20 {2-line B sub-block
; @ssub=DEFB 5,6
 B32772,2;20 }
; @ignoremrcua
; Mid-block comment
 T32774,5;20 T sub-block
; @keep
 W32779,2;20 W sub-block
; @nowarn
 S32781,2;20 S sub-block
; @nolabel
; @ofix=LD A,6
*C32783,2;20 {Sub-block with instructions of various types
; @rem=Hello!
 B32785,1;20
; @rsub=DEFB 3
 W32786,4;20
 T32790,2;20
 S32792,3;20 }
 C32795,1;20 Return
 ;20 comment continuation line
; End comment paragraph 1.
; .
; End comment paragraph 2.

; Test ASM block directives
bB32796,1
@bfix-begin
 B32797,1
@bfix+else
       DEFB 101
@bfix+end
 B32798,1
; @isub+begin
       DEFB 102
; @isub-else
 B32799,1
; @isub-end
@ofix-begin
 B32800,1
; @ofix+else
 32800 DEFB 104
@ofix+end
; @rfix+begin
       DEFB 205
; @rfix+end
; @rsub-begin
 B32802,1
; @rsub-end

; Ignore block
i32803 DEFB 56  ; Set 32803 to 56
 32804 DEFW 512

; Data block
bB49152,1

; Game status buffer entry
gW49153,2

; Message
tT49155,2

; Unused block
uB49157,1

; Word block
wW49158,2*2

; Zero block
sS49162,10
@end

; Block that starts with an invalid control character
a49172 DEFB 0

; Complex DEFB statements
bB49173,3:T5:2,T7:3

; Complex DEFM statements
tT49193,5:B5,B1:7:B2

; Data block with sequences of complex DEFB statements amenable to abbreviation
bB49213,1:T2*2,1,2:T1*3

; Another ignore block
i49229""".split('\n')

TEST_BYTE_FORMATS_SKOOL = """; Binary and mixed-base DEFB/DEFM statements
b30000 DEFB %10111101,$42,26
 30003 DEFB $38,$39,%11110000,%00001111,24,25,26
 30010 DEFB %11111111,%10000001
 30012 DEFB 47,34,56
 30015 DEFB $1A,$00,$00,$00,$A2
 30020 DEFB "hello"
 30025 DEFB %10101010,"hi",24,$56
 30030 DEFM %10111101,$42,26
 30033 DEFM $38,$39,%11110000,%00001111,24,25,26
 30040 DEFM %11111111,%10000001
 30042 DEFM 47,34,56
 30045 DEFM $1A,$00,$00,$00,$A2
 30050 DEFM "hello"
 30055 DEFM %10101010,"hi",24,$56
"""

TEST_WORD_FORMATS_SKOOL = """; Binary and mixed-base DEFW statements
w40000 DEFW %1111000000001111,%1111000000001111
 40004 DEFW 12345,12345,12345
 40010 DEFW $AB0C,$CD32,$102F,$0000
 40018 DEFW 54321,%1010101010101010,$F001
 40024 DEFW $1234,$543C,%1111111100000000,2345,9876
 40034 DEFW $2345,$876D,%1001001010001011,3456,8765
 40044 DEFW 65535,65534
 40048 DEFW 1,2
 40052 DEFW $0000,$FFFF
 40056 DEFW $1000,$2FFF
 40060 DEFW %0101010111110101,%1111111111111111
 40064 DEFW %1101010111110101,%0000000000000001
"""

TEST_S_DIRECTIVES_SKOOL = """; DEFS statements in various bases
s50000 DEFS %0000000111110100
 50500 DEFS 1000
 51500 DEFS $07D0
 53500 DEFS 500,%10101010
 54000 DEFS $0100,170
"""

class SftWriterTest(SkoolKitTestCase):
    def _test_sft(self, skool, exp_sft, write_hex=False, preserve_base=False):
        skoolfile = self.write_text_file(skool, suffix='.skool')
        writer = SftWriter(skoolfile, write_hex, preserve_base)
        writer.write()
        sft = self.out.getvalue().split('\n')[:-1]
        self.assertEqual(exp_sft, sft)

    def test_sftwriter(self):
        self._test_sft(TEST_SKOOL, TEST_SFT)

    def test_write_hex(self):
        self._test_sft('c40177 RET', ['cC$9CF1,1'], write_hex=True)

    def test_decimal_addresses_below_10000(self):
        skool = '\n'.join((
            'b00000 DEFB 0,0,0,0',
            ' 00004 DEFW 0,0,0,0',
            ' 00012 DEFM "Hello"',
            ' 00123 DEFS 1000',
            ' 01123 RET'
        ))
        exp_sft = [
            'bB00000,4',
            ' W00004,8',
            ' T00012,5',
            ' S00123,1000',
            ' C01123,1'
        ]
        self._test_sft(skool, exp_sft)

    def test_byte_formats_no_base(self):
        exp_sft = [
            '; Binary and mixed-base DEFB/DEFM statements',
            'bB30000,b1:2,2:b2:3,b2,3,5,T5,b1:T2:2',
            ' T30030,b1:B2,B2:b2:B3,b2,B3,B5,5,b1:2:B2'
        ]
        self._test_sft(TEST_BYTE_FORMATS_SKOOL, exp_sft, preserve_base=False)

    def test_byte_formats_preserve_base(self):
        exp_sft = [
            '; Binary and mixed-base DEFB/DEFM statements',
            'bB30000,b1:h1:d1,h2:b2:d3,b2,d3,h5,T5,b1:T2:d1:h1',
            ' T30030,b1:h1:d1,h2:b2:d3,b2,d3,h5,5,b1:2:d1:h1'
        ]
        self._test_sft(TEST_BYTE_FORMATS_SKOOL, exp_sft, preserve_base=True)

    def test_word_formats_no_base(self):
        exp_sft = [
            '; Binary and mixed-base DEFW statements',
            'wW40000,b4,6,8,2:b2:2,4:b2:4*2,4*4,b4*2'
        ]
        self._test_sft(TEST_WORD_FORMATS_SKOOL, exp_sft, preserve_base=False)

    def test_word_formats_preserve_base(self):
        exp_sft = [
            '; Binary and mixed-base DEFW statements',
            'wW40000,b4,d6,h8,d2:b2:h2,h4:b2:d4*2,d4*2,h4*2,b4*2'
        ]
        self._test_sft(TEST_WORD_FORMATS_SKOOL, exp_sft, preserve_base=True)

    def test_s_directives_no_base(self):
        exp_sft = [
            '; DEFS statements in various bases',
            'sS50000,b%0000000111110100,1000,$07D0,500:b%10101010,$0100:170'
        ]
        self._test_sft(TEST_S_DIRECTIVES_SKOOL, exp_sft, preserve_base=False)

    def test_s_directives_preserve_base(self):
        exp_sft = [
            '; DEFS statements in various bases',
            'sS50000,b%0000000111110100,d1000,h$07D0,d500:b%10101010,h$0100:d170'
        ]
        self._test_sft(TEST_S_DIRECTIVES_SKOOL, exp_sft, preserve_base=True)

if __name__ == '__main__':
    unittest.main()
