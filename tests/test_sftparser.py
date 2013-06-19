# -*- coding: utf-8 -*-
import unittest

from skoolkittest import SkoolKitTestCase
from skoolkit.sftparser import SftParser, SftParsingError

TEST_SFT = """#
# Test sft file for SftParser unit testing
#
; Test processing of a data definition entry
d24576 DEFB 128

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

; Test the Z directive
zZ32793,10

; Test an invalid control directive
a32794 NOP

; Test a block ASM directive
; @rsub-begin
bB32795,5
; @rsub+else
 32795 DEFS 6
; @rsub+end

; Test complex DEFM statements
tT32800,5,1:B1,2:B2*2

; Test complex DEFB statements
bB32815,2:T1,1:T2*2,1
"""

TEST_SNAPSHOT = [0] * 32826
TEST_SNAPSHOT[32768] = 47  # 32768 CPL
TEST_SNAPSHOT[32769] = 201 # 32769 RET
TEST_SNAPSHOT[32770] = 55  # 32770 SCF
TEST_SNAPSHOT[32771] = 63  # 32771 CCF
TEST_SNAPSHOT[32772] = 118 # 32772 HALT
TEST_SNAPSHOT[32784:32789] = [ord(c) for c in "Hello"]
TEST_SNAPSHOT[32800:32825] = [ord('a')] * 25

TEST_SKOOL = """; Test processing of a data definition entry
d24576 DEFB 128

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

; Test the Z directive
z32793 DEFS 10

; Test an invalid control directive
a32794 NOP

; Test a block ASM directive
; @rsub-begin
b32795 DEFB 0,0,0,0,0
; @rsub+else
 32795 DEFS 6
; @rsub+end

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

; Test the Z directive
z$8019 DEFS $0A

; Test an invalid control directive
a32794 NOP

; Test a block ASM directive
; @rsub-begin
b$801B DEFB $00,$00,$00,$00,$00
; @rsub+else
 32795 DEFS 6
; @rsub+end

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
        self.assertEqual(len(skool), len(TEST_SKOOL))
        for i, line in enumerate(skool):
            self.assertEqual(line, TEST_SKOOL[i])
        self.assertEqual(snapshot[24576], 128)

    def test_write_skool_hex(self):
        snapshot, skool = self._parse_sft(TEST_SFT, TEST_SNAPSHOT, asm_hex=True)
        self.assertEqual(len(skool), len(TEST_SKOOL_HEX))
        for i, line in enumerate(skool):
            self.assertEqual(line, TEST_SKOOL_HEX[i])
        self.assertEqual(snapshot[24576], 128)

    def test_write_skool_hex_lower(self):
        snapshot, skool = self._parse_sft('bB19132,1', [0] * 19133, asm_hex=True, asm_lower=True)
        self.assertEqual(skool[0], 'b$4abc defb $00')

    def test_invalid_line(self):
        for line in (
            "bB30000,5,1:X3",
            "tT30000,a",
            "wW40000,1:B2",
            "cC$ABCG,20"
        ):
            try:
                self._parse_sft(line)
                self.fail("Line '{}' did not cause an SftParsingError".format(line))
            except SftParsingError as e:
                self.assertEqual(e.args[0], "Invalid line: {0}".format(line))

if __name__ == '__main__':
    unittest.main()
