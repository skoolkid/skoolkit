# -*- coding: utf-8 -*-
import re
import unittest

from skoolkittest import SkoolKitTestCase
from skoolkit.sftparser import SftParser, SftParsingError

TEST_SFT = """#
# Test sft file for SftParser unit testing
#
; Test processing of a data definition entry
d24576 DEFB 128

; Data at 0
bB0,1

; Data at 15
bB$f,1

; Data at 23
bB23,1

; Data at 91
bB$5b,1

; Data at 456
bB456,1

; Data at 1018
bB$3FA,1

; Data at 7890
bB7890,1

; Data at 9642
bB$25aa,1

; Routine at 32768
;
; Test code disassembly with no comments.
;
; A Some value
; B Some other value
; @label=START
cC32768,2

; Test code disassembly with a comment marker but no comment
cC32770,1;20

; Test code disassembly with comments
cC32771,1;21 This is a comment on a single line
*C32772,1;21 This is a comment that spans two lines
 ;21 and is followed by an empty comment line
 ;21

; Test the B directive
bB32773,1;22 Single byte
; Two pairs of bytes.
 B32774,2,2
; Two triplets.
 B32778,3*2

; Test the T directive
tT32784,5

; Test the W directive
wW32789,4

; Test the S directive
sS32793,10

; Test an invalid control directive
a32794 NOP

; Test a block ASM directive
@rsub-begin
bB32795,5
; @rsub+else
 32795 DEFS 6
@rsub+end

; Test complex DEFM statements
tT32800,5,1:B1,2:B2*2

; Test complex DEFB statements
bB32815,2:T1,1:T2*2,1
"""

TEST_SNAPSHOT = [0] * 32826
TEST_SNAPSHOT[15] = 15
TEST_SNAPSHOT[23] = 23
TEST_SNAPSHOT[91] = 91
TEST_SNAPSHOT[456] = 56
TEST_SNAPSHOT[1018] = 18
TEST_SNAPSHOT[7890] = 90
TEST_SNAPSHOT[9642] = 42
TEST_SNAPSHOT[32768] = 47  # 32768 CPL
TEST_SNAPSHOT[32769] = 201 # 32769 RET
TEST_SNAPSHOT[32770] = 55  # 32770 SCF
TEST_SNAPSHOT[32771] = 63  # 32771 CCF
TEST_SNAPSHOT[32772] = 118 # 32772 HALT
TEST_SNAPSHOT[32784:32789] = [ord(c) for c in "Hello"]
TEST_SNAPSHOT[32800:32825] = [ord('a')] * 25

TEST_SKOOL = """; Test processing of a data definition entry
d24576 DEFB 128

; Data at 0
b00000 DEFB 0

; Data at 15
b00015 DEFB 15

; Data at 23
b00023 DEFB 23

; Data at 91
b00091 DEFB 91

; Data at 456
b00456 DEFB 56

; Data at 1018
b01018 DEFB 18

; Data at 7890
b07890 DEFB 90

; Data at 9642
b09642 DEFB 42

; Routine at 32768
;
; Test code disassembly with no comments.
;
; A Some value
; B Some other value
; @label=START
c32768 CPL
 32769 RET

; Test code disassembly with a comment marker but no comment
c32770 SCF          ;

; Test code disassembly with comments
c32771 CCF           ; This is a comment on a single line
*32772 HALT          ; This is a comment that spans two lines
                     ; and is followed by an empty comment line
                     ;

; Test the B directive
b32773 DEFB 0         ; Single byte
; Two pairs of bytes.
 32774 DEFB 0,0
 32776 DEFB 0,0
; Two triplets.
 32778 DEFB 0,0,0
 32781 DEFB 0,0,0

; Test the T directive
t32784 DEFM "Hello"

; Test the W directive
w32789 DEFW 0,0

; Test the S directive
s32793 DEFS 10

; Test an invalid control directive
a32794 NOP

; Test a block ASM directive
@rsub-begin
b32795 DEFB 0,0,0,0,0
; @rsub+else
 32795 DEFS 6
@rsub+end

; Test complex DEFM statements
t32800 DEFM "aaaaa"
 32805 DEFM "a",97
 32807 DEFM "aa",97,97
 32811 DEFM "aa",97,97

; Test complex DEFB statements
b32815 DEFB 97,97,"a"
 32818 DEFB 97,"aa"
 32821 DEFB 97,"aa"
 32824 DEFB 97
""".split('\n')

TEST_SKOOL_HEX = """; Test processing of a data definition entry
d24576 DEFB 128

; Data at 0
b$0000 DEFB $00

; Data at 15
b$000F DEFB $0F

; Data at 23
b$0017 DEFB $17

; Data at 91
b$005B DEFB $5B

; Data at 456
b$01C8 DEFB $38

; Data at 1018
b$03FA DEFB $12

; Data at 7890
b$1ED2 DEFB $5A

; Data at 9642
b$25AA DEFB $2A

; Routine at 32768
;
; Test code disassembly with no comments.
;
; A Some value
; B Some other value
; @label=START
c$8000 CPL
 $8001 RET

; Test code disassembly with a comment marker but no comment
c$8002 SCF          ;

; Test code disassembly with comments
c$8003 CCF           ; This is a comment on a single line
*$8004 HALT          ; This is a comment that spans two lines
                     ; and is followed by an empty comment line
                     ;

; Test the B directive
b$8005 DEFB $00       ; Single byte
; Two pairs of bytes.
 $8006 DEFB $00,$00
 $8008 DEFB $00,$00
; Two triplets.
 $800A DEFB $00,$00,$00
 $800D DEFB $00,$00,$00

; Test the T directive
t$8010 DEFM "Hello"

; Test the W directive
w$8015 DEFW $0000,$0000

; Test the S directive
s$8019 DEFS $0A

; Test an invalid control directive
a32794 NOP

; Test a block ASM directive
@rsub-begin
b$801B DEFB $00,$00,$00,$00,$00
; @rsub+else
 32795 DEFS 6
@rsub+end

; Test complex DEFM statements
t$8020 DEFM "aaaaa"
 $8025 DEFM "a",$61
 $8027 DEFM "aa",$61,$61
 $802B DEFM "aa",$61,$61

; Test complex DEFB statements
b$802F DEFB $61,$61,"a"
 $8032 DEFB $61,"aa"
 $8035 DEFB $61,"aa"
 $8038 DEFB $61
""".split('\n')

class SftParserTest(SkoolKitTestCase):
    def _parse_sft(self, sft, snapshot=(), asm_hex=False, asm_lower=False):
        sftfile = self.write_text_file(sft, suffix='.sft')
        writer = SftParser(snapshot[:], sftfile, asm_hex=asm_hex, asm_lower=asm_lower)
        writer.write_skool()
        return writer.snapshot, self.out.getvalue().split('\n')

    def test_write_skool(self):
        snapshot, skool = self._parse_sft(TEST_SFT, TEST_SNAPSHOT)
        self.assertEqual(TEST_SKOOL, skool)
        self.assertEqual(snapshot[24576], 128)

    def test_write_skool_hex(self):
        snapshot, skool = self._parse_sft(TEST_SFT, TEST_SNAPSHOT, asm_hex=True)
        self.assertEqual(TEST_SKOOL_HEX, skool)
        self.assertEqual(snapshot[24576], 128)

    def test_write_skool_hex_lower(self):
        snapshot, skool = self._parse_sft('bB19132,1', [0] * 19133, asm_hex=True, asm_lower=True)
        self.assertEqual(skool[0], 'b$4abc defb $00')

    def test_invalid_line(self):
        for line in (
            "b",
            "bX",
            "bB",
            "bB30000",
            "bB30000;",
            "bB30000,",
            "bB30000,;",
            "bB30000,3;q",
            "bB30000,3;k ...",
            "bB30000,5,1:X3",
            "tT30000,a",
            "wW40000,1:C2",
            "cC$ABCG,20"
        ):
            with self.assertRaisesRegexp(SftParsingError, re.escape("Invalid line: {}".format(line.split()[0]))):
                self._parse_sft(line)

    def test_byte_formats(self):
        snapshot = [42] * 75
        sft = '\n'.join((
            'bB00000,b5',
            ' B00005,h15',
            ' B00020,b2,d2,h1',
            ' B00025,b2:d2:h1',
            ' B00030,h5:d3:b2',
            ' B00040,b1,h2*2',
            ' B00045,h1,T4',
            ' B00050,b2:T3',
            ' T00055,h2,3',
            ' T00060,2:d3',
            ' T00065,3,B1*2',
            ' T00070,B2:h3'
        ))
        skool = self._parse_sft(sft, snapshot)[1]

        exp_skool = [
            'b00000 DEFB %00101010,%00101010,%00101010,%00101010,%00101010',
            ' 00005 DEFB $2A,$2A,$2A,$2A,$2A,$2A,$2A,$2A,$2A,$2A,$2A,$2A,$2A,$2A,$2A',
            ' 00020 DEFB %00101010,%00101010',
            ' 00022 DEFB 42,42',
            ' 00024 DEFB $2A',
            ' 00025 DEFB %00101010,%00101010,42,42,$2A',
            ' 00030 DEFB $2A,$2A,$2A,$2A,$2A,42,42,42,%00101010,%00101010',
            ' 00040 DEFB %00101010',
            ' 00041 DEFB $2A,$2A',
            ' 00043 DEFB $2A,$2A',
            ' 00045 DEFB $2A',
            ' 00046 DEFB "****"',
            ' 00050 DEFB %00101010,%00101010,"***"',
            ' 00055 DEFM $2A,$2A',
            ' 00057 DEFM "***"',
            ' 00060 DEFM "**",42,42,42',
            ' 00065 DEFM "***"',
            ' 00068 DEFM 42',
            ' 00069 DEFM 42',
            ' 00070 DEFM 42,42,$2A,$2A,$2A'
        ]
        self.assertEqual(exp_skool, skool[:-1])

    def test_byte_formats_hex(self):
        snapshot = [170] * 4
        skool = self._parse_sft('bB00000,b1:d1:h1:1', snapshot, asm_hex=True)[1]
        self.assertEqual('b$0000 DEFB %10101010,170,$AA,$AA', skool[0])

    def test_word_formats(self):
        snapshot = [205, 85] * 20
        sft = '\n'.join((
            'wW00000,4',
            ' W00004,b4',
            ' W00008,d4',
            ' W00012,h4',
            ' W00016,2,d2,h4',
            ' W00024,b4:2:h2',
            ' W00032,b2,4,h2'
        ))
        skool = self._parse_sft(sft, snapshot)[1]

        exp_skool = [
            'w00000 DEFW 21965,21965',
            ' 00004 DEFW %0101010111001101,%0101010111001101',
            ' 00008 DEFW 21965,21965',
            ' 00012 DEFW $55CD,$55CD',
            ' 00016 DEFW 21965',
            ' 00018 DEFW 21965',
            ' 00020 DEFW $55CD,$55CD',
            ' 00024 DEFW %0101010111001101,%0101010111001101,21965,$55CD',
            ' 00032 DEFW %0101010111001101',
            ' 00034 DEFW 21965,21965',
            ' 00038 DEFW $55CD'
        ]
        self.assertEqual(exp_skool, skool[:-1])

    def test_word_formats_hex(self):
        snapshot = [170] * 8
        skool = self._parse_sft('wW00000,b2,d2,h2,2', snapshot, asm_hex=True)[1]

        exp_skool = [
            'w$0000 DEFW %1010101010101010',
            ' $0002 DEFW 43690',
            ' $0004 DEFW $AAAA',
            ' $0006 DEFW $AAAA'
        ]
        self.assertEqual(exp_skool, skool[:-1])

    def test_s_directives(self):
        sft = '\n'.join((
            'sS00000,1,b2,d3,h4',
            ' S00010,b10,d10,h10',
            ' S00040,10',
            ' S00050,b300,d300,h300'
        ))
        skool = self._parse_sft(sft)[1]

        exp_skool = [
            's00000 DEFS 1',
            ' 00001 DEFS %00000010',
            ' 00003 DEFS 3',
            ' 00006 DEFS 4',
            ' 00010 DEFS %00001010',
            ' 00020 DEFS 10',
            ' 00030 DEFS $0A',
            ' 00040 DEFS 10',
            ' 00050 DEFS %0000000100101100',
            ' 00350 DEFS 300',
            ' 00650 DEFS $012C'
        ]
        self.assertEqual(exp_skool, skool[:-1])

    def test_s_directives_hex(self):
        sft = 'sS00000,b10,d10,h10,10'
        skool = self._parse_sft(sft, asm_hex=True)[1]

        exp_skool = [
            's$0000 DEFS %00001010',
            ' $000A DEFS 10',
            ' $0014 DEFS $0A',
            ' $001E DEFS $0A'
        ]
        self.assertEqual(exp_skool, skool[:-1])

if __name__ == '__main__':
    unittest.main()
