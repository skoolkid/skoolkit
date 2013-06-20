# -*- coding: utf-8 -*-
import unittest

from skoolkittest import SkoolKitTestCase
from skoolkit.skoolctl import CtlWriter

DIRECTIVES = 'bcgituwz'

TEST_SKOOL = r"""; Dangling comment not associated with any entry

; Data definition entry (ignored)
d49153 DEFW 0

; Remote entry (ignored)
r24576 start

; @start
; @writer=package.module.classname
; @set-bullet=+
; @org=32768
; Routine
;
; Routine description
;
; A Some value
; B Another value
; @label=START
c32768 NOP          ; Do nothing
; @bfix=DEFB 2,3
 32769 DEFB 1,2     ; 1-line B sub-block
; @nowarn
 32771 defb 3       ; {2-line B sub-block
; @isub=DEFB 0,1
 32772 DEFB 4,5     ; }
; Mid-block comment
 32774 DEFM "Hello" ; T sub-block
; @keep
; @ignoreua
 32779 DEFW 12345   ; W sub-block
 32781 defs 2       ; Z sub-block
; @nolabel
 32783 LD A,5       ; {Sub-block with instructions of various types
; @ofix=DEFB 2
 32785 DEFB 0       ;
; @rsub=DEFW 0,1,2
 32786 DEFW 0,1     ; and blank lines
; @ssub=DEFM "Lo"
 32790 defm "H",105 ;
 32792 DEFS 3       ; in the comment}
 $801B RET          ; Instruction with a
                    ; comment continuation line
; End comment paragraph 1.
; .
; End comment paragraph 2.

; Ignore block
i32796

; Data block
; @rem=Hello!
b49152 DEFB 0

; Game status buffer entry
g49153 defw 0

; Message
t49155 DEFM "Lo"

; Unused block
u49157 DEFB 128

; Word block
w49158 DEFW 2
 49160 DEFW 4

; Data block beginning with an implicit 1-byte sub-block
b49162 DEFB 0
 49163 RET

; Text block beginning with an implicit 1-byte sub-block
t49164 DEFM "a"
 49165 RET

; Word block beginning with an implicit 2-byte sub-block
w49166 DEFW 23
 49168 RET

; Zero block beginning with an implicit sub-block
z49169 DEFS 9
 49178 RET

; Data block with sub-block lengths amenable to abbreviation (2*3,3*2,1)
b49179 DEFB 0,0
 49181 DEFB 0,0
 49183 DEFB 0,0
 49185 DEFB 0,0,0
 49188 DEFB 0,0,0
 49191 DEFB 0
 49192 DEFB 0

; ASM block directives
; @bfix-begin
b49193 DEFB 7
; @bfix+else
c49193 NOP
; @bfix+end

; Zero block
z49194 DEFS 128
 49322 DEFS 128
 49450 DEFS 128
; @end

; Complex DEFB statements
b49578 DEFB 1,2,3,"Hello",5,6
 49588 DEFB "Goodbye",7,8,9

; Complex DEFM statements
t49598 DEFM "\"Hi!\"",1,2,3,4,5
 49608 DEFM 6,"C:\\DOS>",7,8

; Data block with sequences of complex DEFB statements amenable to abbreviation
b49618 DEFB 1,"Hi"
 49621 DEFB 4,"Lo"
 49624 DEFB 7
 49625 DEFB 8,9,"A"
 49628 DEFB 10,11,"B"
 49631 DEFB 12,13,"C"

; Routine with an empty block description and a register section
;
; .
;
; BC 0
c49634 RET

; Another ignore block
i49635
; End comment on the final block.
"""

TEST_CTL = """; @start:32768
; @writer:32768=package.module.classname
; @set-bullet:32768=+
; @org:32768=32768
c 32768 Routine
D 32768 Routine description
R 32768 A Some value
R 32768 B Another value
; @label:32768=START
  32768,1 Do nothing
; @bfix:32769=DEFB 2,3
B 32769,2,2 1-line B sub-block
; @nowarn:32771
; @isub:32772=DEFB 0,1
B 32771,3,1,2 2-line B sub-block
D 32774 Mid-block comment
T 32774,5,5 T sub-block
; @keep:32779
; @ignoreua:32779
W 32779,2 W sub-block
Z 32781,2 Z sub-block
M 32783,12 Sub-block with instructions of various types and blank lines in the comment
; @nolabel:32783
; @ofix:32785=DEFB 2
B 32785,1
; @rsub:32786=DEFW 0,1,2
W 32786,4,4
; @ssub:32790=DEFM "Lo"
T 32790,2,1:B1
Z 32792,3
  32795 Instruction with a comment continuation line
E 32768 End comment paragraph 1.
E 32768 End comment paragraph 2.
i 32796 Ignore block
b 49152 Data block
; @rem:49152=Hello!
g 49153 Game status buffer entry
W 49153
t 49155 Message
  49155,2,2
u 49157 Unused block
w 49158 Word block
  49158,4,2
b 49162 Data block beginning with an implicit 1-byte sub-block
C 49163
t 49164 Text block beginning with an implicit 1-byte sub-block
C 49165
w 49166 Word block beginning with an implicit 2-byte sub-block
C 49168
z 49169 Zero block beginning with an implicit sub-block
C 49178
b 49179 Data block with sub-block lengths amenable to abbreviation (2*3,3*2,1)
  49179,14,2*3,3*2,1
b 49193 ASM block directives
z 49194 Zero block
  49194,384,128
; @end:49194
b 49578 Complex DEFB statements
  49578,20,3:T5:2,T7:3
t 49598 Complex DEFM statements
  49598,20,5:B5,B1:7:B2
b 49618 Data block with sequences of complex DEFB statements amenable to abbreviation
  49618,16,1:T2*2,1,2:T1
c 49634 Routine with an empty block description and a register section
R 49634 BC 0
i 49635 Another ignore block
E 49635 End comment on the final block.""".split('\n')

TEST_CTL_HEX = """; @start:$8000
; @writer:$8000=package.module.classname
; @set-bullet:$8000=+
; @org:$8000=32768
c $8000 Routine
D $8000 Routine description
R $8000 A Some value
R $8000 B Another value
; @label:$8000=START
  $8000,1 Do nothing
; @bfix:$8001=DEFB 2,3
B $8001,2,2 1-line B sub-block
; @nowarn:$8003
; @isub:$8004=DEFB 0,1
B $8003,3,1,2 2-line B sub-block
D $8006 Mid-block comment
T $8006,5,5 T sub-block
; @keep:$800B
; @ignoreua:$800B
W $800B,2 W sub-block
Z $800D,2 Z sub-block
M $800F,12 Sub-block with instructions of various types and blank lines in the comment
; @nolabel:$800F
; @ofix:$8011=DEFB 2
B $8011,1
; @rsub:$8012=DEFW 0,1,2
W $8012,4,4
; @ssub:$8016=DEFM "Lo"
T $8016,2,1:B1
Z $8018,3
  $801B Instruction with a comment continuation line
E $8000 End comment paragraph 1.
E $8000 End comment paragraph 2.
i $801C Ignore block
b $C000 Data block
; @rem:$C000=Hello!
g $C001 Game status buffer entry
W $C001
t $C003 Message
  $C003,2,2
u $C005 Unused block
w $C006 Word block
  $C006,4,2
b $C00A Data block beginning with an implicit 1-byte sub-block
C $C00B
t $C00C Text block beginning with an implicit 1-byte sub-block
C $C00D
w $C00E Word block beginning with an implicit 2-byte sub-block
C $C010
z $C011 Zero block beginning with an implicit sub-block
C $C01A
b $C01B Data block with sub-block lengths amenable to abbreviation (2*3,3*2,1)
  $C01B,14,2*3,3*2,1
b $C029 ASM block directives
z $C02A Zero block
  $C02A,384,128
; @end:$C02A
b $C1AA Complex DEFB statements
  $C1AA,20,3:T5:2,T7:3
t $C1BE Complex DEFM statements
  $C1BE,20,5:B5,B1:7:B2
b $C1D2 Data block with sequences of complex DEFB statements amenable to abbreviation
  $C1D2,16,1:T2*2,1,2:T1
c $C1E2 Routine with an empty block description and a register section
R $C1E2 BC 0
i $C1E3 Another ignore block
E $C1E3 End comment on the final block.""".split('\n')

TEST_CTL_BS = """c 32768
B 32769,2,2
B 32771,3,1,2
T 32774,5,5
W 32779,2
Z 32781,2
B 32785,1
W 32786,4,4
T 32790,2,1:B1
Z 32792,3
i 32796
b 49152
g 49153
W 49153
t 49155
  49155,2,2
u 49157
w 49158
  49158,4,2
b 49162
C 49163
t 49164
C 49165
w 49166
C 49168
z 49169
C 49178
b 49179
  49179,14,2*3,3*2,1
b 49193
z 49194
  49194,384,128
b 49578
  49578,20,3:T5:2,T7:3
t 49598
  49598,20,5:B5,B1:7:B2
b 49618
  49618,16,1:T2*2,1,2:T1
c 49634
i 49635""".split('\n')

TEST_CTL_BSC = """c 32768
  32768,1 Do nothing
B 32769,2,2 1-line B sub-block
B 32771,3,1,2 2-line B sub-block
T 32774,5,5 T sub-block
W 32779,2 W sub-block
Z 32781,2 Z sub-block
M 32783,12 Sub-block with instructions of various types and blank lines in the comment
B 32785,1
W 32786,4,4
T 32790,2,1:B1
Z 32792,3
  32795 Instruction with a comment continuation line
i 32796
b 49152
g 49153
W 49153
t 49155
  49155,2,2
u 49157
w 49158
  49158,4,2
b 49162
C 49163
t 49164
C 49165
w 49166
C 49168
z 49169
C 49178
b 49179
  49179,14,2*3,3*2,1
b 49193
z 49194
  49194,384,128
b 49578
  49578,20,3:T5:2,T7:3
t 49598
  49598,20,5:B5,B1:7:B2
b 49618
  49618,16,1:T2*2,1,2:T1
c 49634
i 49635""".split('\n')

class CtlWriterTest(SkoolKitTestCase):
    def _get_ctl(self, elements='btdrmsc', write_hex=False, write_asm_dirs=True):
        skoolfile = self.write_text_file(TEST_SKOOL, suffix='.skool')
        writer = CtlWriter(skoolfile, elements, write_hex, write_asm_dirs)
        writer.write()
        return self.out.getvalue().split('\n')[:-1]

    def _assert_ctls_equal(self, actual_ctl, expected_ctl):
        self.assertEqual(len(actual_ctl), len(expected_ctl))
        for i, line in enumerate(actual_ctl):
            self.assertEqual(line, expected_ctl[i])

    def test_default_elements(self):
        self._assert_ctls_equal(self._get_ctl(), TEST_CTL)

    def test_default_elements_hex(self):
        self._assert_ctls_equal(self._get_ctl(write_hex=True), TEST_CTL_HEX)

    def test_default_elements_no_asm_dirs(self):
        ctl = self._get_ctl(write_asm_dirs=False)
        test_ctl = [line for line in TEST_CTL if not line.startswith(';')]
        self._assert_ctls_equal(ctl, test_ctl)

    def test_wb(self):
        ctl = self._get_ctl('b', write_asm_dirs=False)
        test_ctl = [line[:7] for line in TEST_CTL if line[0] in DIRECTIVES]
        self._assert_ctls_equal(ctl, test_ctl)

    def test_wbd(self):
        ctl = self._get_ctl('bd', write_asm_dirs=False)
        test_ctl = []
        for line in TEST_CTL:
            if line[0] in DIRECTIVES:
                test_ctl.append(line[:7])
            elif line.startswith('D 32768'):
                test_ctl.append(line)
        self._assert_ctls_equal(ctl, test_ctl)

    def test_wbm(self):
        ctl = self._get_ctl('bm', write_asm_dirs=False)
        test_ctl = []
        for line in TEST_CTL:
            if line[0] in DIRECTIVES:
                test_ctl.append(line[:7])
            elif line[0] in 'DE' and not line.startswith('D 32768'):
                test_ctl.append(line)
        self._assert_ctls_equal(ctl, test_ctl)

    def test_wbr(self):
        ctl = self._get_ctl('br', write_asm_dirs=False)
        test_ctl = []
        for line in TEST_CTL:
            if line[0] in DIRECTIVES:
                test_ctl.append(line[:7])
            elif line[0] == 'R':
                test_ctl.append(line)
        self._assert_ctls_equal(ctl, test_ctl)

    def test_wbs(self):
        ctl = self._get_ctl('bs', write_asm_dirs=False)
        self._assert_ctls_equal(ctl, TEST_CTL_BS)

    def test_wbsc(self):
        ctl = self._get_ctl('bsc', write_asm_dirs=False)
        self._assert_ctls_equal(ctl, TEST_CTL_BSC)

    def test_wbt(self):
        ctl = self._get_ctl('bt', write_asm_dirs=False)
        test_ctl = [line for line in TEST_CTL if line[0] in DIRECTIVES]
        self._assert_ctls_equal(ctl, test_ctl)

if __name__ == '__main__':
    unittest.main()
