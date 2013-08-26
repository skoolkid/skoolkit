# -*- coding: utf-8 -*-
import re
import unittest

from skoolkittest import PY3, SkoolKitTestCase
from skoolkit import SkoolParsingError
from skoolkit.skoolasm import AsmWriter
from skoolkit.skoolparser import SkoolParser, CASE_LOWER, CASE_UPPER, BASE_10, BASE_16

TEST_EMPTY_DESCRIPTION = """; @start
; Test an empty description
;
; #HTML(#UDG32768)
c24604 RET
"""

TEST_EMPTY_DESCRIPTION_WITH_REGISTERS = """; @start
; Test an empty description and a register section
;
; .
;
; A 0
; B 1
c25600 RET
"""

TEST_CRLF = """; @start
; Routine
c32768 RET
"""

TEST_TAB = """; @start
; Routine
c32768 LD A,B
 32769 RET
"""

TEST_LOWER = """; @start
; @org=24576

; Routine
;
; Description.
;
; A Value
; B Another value
; @label=DOSTUFF
c24576 LD HL,$6003

; Data
b$6003 DEFB 123 ; #REGa=0
 $6004 DEFB 246 ; #R24576
"""

TEST_INSTR_WIDTH = """; @start
; Data
b$6003 DEFB 123 ; #REGa=0
"""

TEST_REGISTERS = """; @start
; Test parsing of register blocks (1)
;
; Traditional.
;
; A Some value
; B Some other value
c24604 RET

; Test parsing of register blocks (2)
;
; With prefixes.
;
; Input:a Some value
;       b Some other value
; Output:c The result
c24605 RET
"""

TEST_DEFM = """; @start
; Message 1
t32768 DEFM "AbCdEfG"

; Message 2
t32775 defm "hIjKlMn"
"""

TEST_MACRO_D = """; @start

; First routine
c32768 RET

; Second routine
c32769 RET

c32770 RET
"""

TEST_MACRO_EREFS = """; @start
; First routine
c30000 CALL 30004

; Second routine
c30003 LD A,B
 30004 LD B,C

; Third routine
c30005 JP 30004
"""

TEST_MACRO_REFS = """; @start
; Used by the routines at 24583, 24586 and 24589
c24581 LD A,B
 24582 RET

; Uses 24581
c24583 CALL 24581

; Also uses 24581
c24586 CALL 24581

; Uses 24581 too
c24589 JP 24582
"""

TEST_HEADER = """; @start
; Header line 1.
; Header line 2.

; Start
c32768 JP 49152
"""

TEST_END_COMMENT = """; @start
; Start
c49152 RET
; End comment.
"""

TEST_UNCONVERTED_ADDRESSES = """; @start
; Routine at 32768
;
; Used by the routine at 32768.
c32768 LD A,B  ; This instruction is at 32768
; This mid-routine comment is above 32769.
 32769 RET
"""

TEST_LONG_LINE = """; @start
; Routine
c30000 BIT 3,(IX+101) ; Pneumonoultramicroscopicsilicovolcanoconiosis
"""

TEST_CONTINUATION_LINE = """; @start
; Routine
c40000 LD A,B ; This instruction has a long comment that will require a
              ; continuation line
"""

TEST_WIDE_TABLE = """; @start
; Routine
;
; #TABLE
; { This is cell A1 | This is cell A2 | This is cell A3 | This is cell A4 | This is cell A5 }
; TABLE#
c50000 RET
"""

TEST_END_DIRECTIVE = """; @start
; Routine
c40000 RET
; @end

; More code
c40001 NOP
"""

TEST_ISUB_DIRECTIVE = """; @start
; Routine
; @isub=LD A,(32512)
c60000 LD A,(m)
"""

TEST_ISUB_BLOCK_DIRECTIVE = """; @start
; Routine
;
; @isub+begin
; Actual description.
; @isub-else
; Other description.
; @isub-end
c24576 RET
"""

TEST_RSUB_DIRECTIVE = """; @start
; Routine
; @rsub=INC HL
c23456 INC L
"""

TEST_IGNOREUA_DIRECTIVE = """; @start
; @ignoreua
; Routine at 32768
;
; @ignoreua
; Description of routine at 32768.
; @ignoreua
c32768 LD A,B ; This is the instruction at 32768
; @ignoreua
; This is the mid-routine comment above 32769.
 32769 RET
; @ignoreua
; This is the end comment after 32769.
"""

TEST_NOWARN_DIRECTIVE = """; @start
; Routine
; @nowarn
c30000 LD HL,30003

; Routine
; @label=NEXT
; @nowarn
c30003 CALL 30000
; @nowarn
 30006 CALL 30001
"""

TEST_KEEP_DIRECTIVE = """; @start
; Routine
; @keep
c30000 LD HL,30003

; Routine
; @label=NEXT
c30003 RET
"""

TEST_NOLABEL_DIRECTIVE = """; @start
; Start
; @label=START
c32768 LD A,B
; @nolabel
*32769 RET
"""

TEST_ENTRY_POINT_LABELS = """; @start
; Routine
; @label=START
c40000 LD A,B
*40001 LD C,D
*40002 RET
"""

TEST_HEX = r"""; @start
; @org=32767
; Routine
c32768 ld a,(ix+17)
 32772 DEFW 0,1,17,273,43981
 32782 LD (IY-25),124
 32783 AND 0
 32785 OR 1
 32787 XOR 2
 32789 SUB 3
 32791 CP 4
 32793 IN A,(5)
 32795 OUT (6),A
 32797 ADD A,7
 32799 ADC A,8
 32801 SBC A,9
 32803 RST 56
 32804 LD A,11
 32806 LD B,12
 32808 LD C,13
 32810 LD D,14
 32812 LD E,15
 32814 LD H,16
 32816 LD L,17
 32818 LD IXL,18
 32821 LD IXH,19
 32824 LD IYL,20
 32827 LD IYH,21
 32830 LD (HL),22
 32832 AND B
 32833 DEFB 0,1,17,171
 32837 LD A,(30874)
 32840 DAA
 32841 defb 23,"\"Hi!\"",127
 32848 DEFM "C:\\>",171
 32853 DEFS 10
 32863 DEFS 2748,254
"""

TEST_HEX_ASM = r"""
  ORG $7FFF

; Routine
  ld a,(ix+$11)
  DEFW $0000,$0001,$0011,$0111,$ABCD
  LD (IY-$19),$7C
  AND $00
  OR $01
  XOR $02
  SUB $03
  CP $04
  IN A,($05)
  OUT ($06),A
  ADD A,$07
  ADC A,$08
  SBC A,$09
  RST $38
  LD A,$0B
  LD B,$0C
  LD C,$0D
  LD D,$0E
  LD E,$0F
  LD H,$10
  LD L,$11
  LD IXL,$12
  LD IXH,$13
  LD IYL,$14
  LD IYH,$15
  LD (HL),$16
  AND B
  DEFB $00,$01,$11,$AB
  LD A,($789A)
  DAA
  defb $17,"\"Hi!\"",$7F
  DEFM "C:\\>",$AB
  DEFS $0A
  DEFS $0ABC,$FE
""".split('\n')[1:-1]

TEST_HEX_ASM_LOWER = r"""
  org $7fff

; Routine
  ld a,(ix+$11)
  defw $0000,$0001,$0011,$0111,$abcd
  ld (iy-$19),$7c
  and $00
  or $01
  xor $02
  sub $03
  cp $04
  in a,($05)
  out ($06),a
  add a,$07
  adc a,$08
  sbc a,$09
  rst $38
  ld a,$0b
  ld b,$0c
  ld c,$0d
  ld d,$0e
  ld e,$0f
  ld h,$10
  ld l,$11
  ld ixl,$12
  ld ixh,$13
  ld iyl,$14
  ld iyh,$15
  ld (hl),$16
  and b
  defb $00,$01,$11,$ab
  ld a,($789a)
  daa
  defb $17,"\"Hi!\"",$7f
  defm "C:\\>",$ab
  defs $0a
  defs $0abc,$fe
""".split('\n')[1:-1]

TEST_HEX_ASM_UPPER = r"""
  ORG $7FFF

; Routine
  LD A,(IX+$11)
  DEFW $0000,$0001,$0011,$0111,$ABCD
  LD (IY-$19),$7C
  AND $00
  OR $01
  XOR $02
  SUB $03
  CP $04
  IN A,($05)
  OUT ($06),A
  ADD A,$07
  ADC A,$08
  SBC A,$09
  RST $38
  LD A,$0B
  LD B,$0C
  LD C,$0D
  LD D,$0E
  LD E,$0F
  LD H,$10
  LD L,$11
  LD IXL,$12
  LD IXH,$13
  LD IYL,$14
  LD IYH,$15
  LD (HL),$16
  AND B
  DEFB $00,$01,$11,$AB
  LD A,($789A)
  DAA
  DEFB $17,"\"Hi!\"",$7F
  DEFM "C:\\>",$AB
  DEFS $0A
  DEFS $0ABC,$FE
""".split('\n')[1:-1]

TEST_DECIMAL = r"""; @start
; @org=$8000
; Routine
c32768 ld a,(ix+$11)
 32772 DEFW $0000,$0001,$0011,$0111,$ABCD
 32782 LD (IY-$19),$7C
 32783 AND $00
 32785 OR $01
 32787 XOR $02
 32789 SUB $03
 32791 CP $04
 32793 IN A,($05)
 32795 OUT ($06),A
 32797 ADD A,$07
 32799 ADC A,$08
 32801 SBC A,$09
 32803 RST $38
 32804 LD A,$0B
 32806 LD B,$0C
 32808 LD C,$0D
 32810 LD D,$0E
 32812 LD E,$0F
 32814 LD H,$10
 32816 LD L,$11
 32818 LD IXL,$12
 32821 LD IXH,$13
 32824 LD IYL,$14
 32827 LD IYH,$15
 32830 LD (HL),$16
 32832 AND B
 32833 DEFB $00,$01,$11,$AB
 32837 LD A,($789A)
 32840 DAA
 32841 defb $17,"\"Hi!\"",$7f
 32848 DEFM "C:\\>",$AB
 32853 DEFS $0A
 32863 DEFS $0ABC,$FE
"""

TEST_DECIMAL_ASM = r"""
  ORG 32768

; Routine
  ld a,(ix+17)
  DEFW 0,1,17,273,43981
  LD (IY-25),124
  AND 0
  OR 1
  XOR 2
  SUB 3
  CP 4
  IN A,(5)
  OUT (6),A
  ADD A,7
  ADC A,8
  SBC A,9
  RST 56
  LD A,11
  LD B,12
  LD C,13
  LD D,14
  LD E,15
  LD H,16
  LD L,17
  LD IXL,18
  LD IXH,19
  LD IYL,20
  LD IYH,21
  LD (HL),22
  AND B
  DEFB 0,1,17,171
  LD A,(30874)
  DAA
  defb 23,"\"Hi!\"",127
  DEFM "C:\\>",171
  DEFS 10
  DEFS 2748,254
""".split('\n')[1:-1]

TEST_DECIMAL_ASM_LOWER = r"""
  org 32768

; Routine
  ld a,(ix+17)
  defw 0,1,17,273,43981
  ld (iy-25),124
  and 0
  or 1
  xor 2
  sub 3
  cp 4
  in a,(5)
  out (6),a
  add a,7
  adc a,8
  sbc a,9
  rst 56
  ld a,11
  ld b,12
  ld c,13
  ld d,14
  ld e,15
  ld h,16
  ld l,17
  ld ixl,18
  ld ixh,19
  ld iyl,20
  ld iyh,21
  ld (hl),22
  and b
  defb 0,1,17,171
  ld a,(30874)
  daa
  defb 23,"\"Hi!\"",127
  defm "C:\\>",171
  defs 10
  defs 2748,254
""".split('\n')[1:-1]

TEST_DECIMAL_ASM_UPPER = r"""
  ORG 32768

; Routine
  LD A,(IX+17)
  DEFW 0,1,17,273,43981
  LD (IY-25),124
  AND 0
  OR 1
  XOR 2
  SUB 3
  CP 4
  IN A,(5)
  OUT (6),A
  ADD A,7
  ADC A,8
  SBC A,9
  RST 56
  LD A,11
  LD B,12
  LD C,13
  LD D,14
  LD E,15
  LD H,16
  LD L,17
  LD IXL,18
  LD IXH,19
  LD IYL,20
  LD IYH,21
  LD (HL),22
  AND B
  DEFB 0,1,17,171
  LD A,(30874)
  DAA
  DEFB 23,"\"Hi!\"",127
  DEFM "C:\\>",171
  DEFS 10
  DEFS 2748,254
""".split('\n')[1:-1]

TEST_INVALID_BLOCK_DIRECTIVES = []
INVALID_BLOCK_DIRECTIVE_WARNINGS = []

# @rsub-begin inside @rsub- block
TEST_INVALID_BLOCK_DIRECTIVES.append("""; @start
; @rsub-begin
; @rsub-begin
; @rsub-end
; @rsub-end
""")
INVALID_BLOCK_DIRECTIVE_WARNINGS.append("rsub-begin inside rsub- block")

# @isub+else inside @bfix+ block
TEST_INVALID_BLOCK_DIRECTIVES.append("""; @start
; @bfix+begin
; @isub+else
; @isub+end
; @bfix+end
""")
INVALID_BLOCK_DIRECTIVE_WARNINGS.append("isub+else inside bfix+ block")

# Dangling @ofix+else directive
TEST_INVALID_BLOCK_DIRECTIVES.append("""; @start
; @ofix+else
; @ofix+end
""")
INVALID_BLOCK_DIRECTIVE_WARNINGS.append("ofix+else not inside block")

# Dangling @rfix+end directive
TEST_INVALID_BLOCK_DIRECTIVES.append("""; @start
; @rfix+end
""")
INVALID_BLOCK_DIRECTIVE_WARNINGS.append("rfix+end has no matching start directive")

# Mismatched begin/else/end (wrong infix)
TEST_INVALID_BLOCK_DIRECTIVES.append("""; @start
; @rsub+begin
; @rsub-else
; @rsub+end
""")
INVALID_BLOCK_DIRECTIVE_WARNINGS.append("rsub+end cannot end rsub- block")

# Mismatched begin/end (different directive)
TEST_INVALID_BLOCK_DIRECTIVES.append("""; @start
; @ofix-begin
; @bfix-end
""")
INVALID_BLOCK_DIRECTIVE_WARNINGS.append("bfix-end cannot end ofix- block")

TABLE_SRC = []
TABLE_TEXT = []

# Headers, colspans 1 and 2, rowspans 1 and 2
TABLE_SRC.append("""(data)
{ =h Col1 | =h Col2 | =h,c2 Cols3+4 }
{ =r2 X   | Y       | Za  | Zb }
{           Y2      | Za2 | Zb2 }
""")

TABLE_TEXT.append("""
+------+------+-----------+
| Col1 | Col2 | Cols3+4   |
+------+------+-----+-----+
| X    | Y    | Za  | Zb  |
|      | Y2   | Za2 | Zb2 |
+------+------+-----+-----+
""")

# Cell with rowspan > 1 in the middle column
TABLE_SRC.append("""
{ A1 cell | =r2 This is a cell with rowspan=2 | C1 cell }
{ A2 cell | C2 cell }
""")

TABLE_TEXT.append("""
+---------+-------------------------------+---------+
| A1 cell | This is a cell with rowspan=2 | C1 cell |
| A2 cell |                               | C2 cell |
+---------+-------------------------------+---------+
""")

# Cell with rowspan > 1 in the rightmost column
TABLE_SRC.append("""
{ A1 cell | B1 cell | =r2 This is a cell with rowspan=2 }
{ A2 cell | B2 cell }
""")

TABLE_TEXT.append("""
+---------+---------+-------------------------------+
| A1 cell | B1 cell | This is a cell with rowspan=2 |
| A2 cell | B2 cell |                               |
+---------+---------+-------------------------------+
""")

# Cell with colspan > 1 and wrapped contents
TABLE_SRC.append("""(,:w)
{ =c2 Cell with colspan=2 and contents that will be wrapped onto the following line }
{ A2 | B2 }
""")

TABLE_TEXT.append("""
+--------------------------------------------------------------------------+
| Cell with colspan=2 and contents that will be wrapped onto the following |
| line                                                                     |
| A2                                  | B2                                 |
+-------------------------------------+------------------------------------+
""")

# Cell in the first column with rowspan > 1 and wrapped contents
TABLE_SRC.append("""(,:w)
{ =r2 This cell has rowspan=2 and contains text that will wrap onto the next line | B1 }
{ B2 }
""")

TABLE_TEXT.append("""
+-------------------------------------------------------------------+----+
| This cell has rowspan=2 and contains text that will wrap onto the | B1 |
| next line                                                         | B2 |
+-------------------------------------------------------------------+----+
""")

# Cell in the middle column with rowspan > 1 and wrapped contents
TABLE_SRC.append("""(,,:w)
{ A1 | =r2 This cell has rowspan=2 and contains text that will wrap onto the next line | C1 }
{ A2 | C2 }
""")

TABLE_TEXT.append("""
+----+---------------------------------------------------------------+----+
| A1 | This cell has rowspan=2 and contains text that will wrap onto | C1 |
| A2 | the next line                                                 | C2 |
+----+---------------------------------------------------------------+----+
""")

# Cell in the last column with rowspan > 1 and wrapped contents
TABLE_SRC.append("""(,,:w)
{ A1 | =r2 This cell has rowspan=2 and contains text that will wrap onto the next line }
{ A2 }
""")

TABLE_TEXT.append("""
+----+-------------------------------------------------------------------+
| A1 | This cell has rowspan=2 and contains text that will wrap onto the |
| A2 | next line                                                         |
+----+-------------------------------------------------------------------+
""")

# Header row shorter than the remaining rows
TABLE_SRC.append("""
{ =h H1 | =h H2 }
{ A1    | B1    | C1 }
{ A2    | B2    | C2 }
""")

TABLE_TEXT.append("""
+----+----+
| H1 | H2 |
+----+----+----+
| A1 | B1 | C1 |
| A2 | B2 | C2 |
+----+----+----+
""")

# Transparent cell in the top left corner
TABLE_SRC.append("""
{ =t | =h H2 }
{ A1 | B1 }
""")

TABLE_TEXT.append("""
     +----+
     | H2 |
+----+----+
| A1 | B1 |
+----+----+
""")

# Transparent cell in the top right corner
TABLE_SRC.append("""
{ =h H1 | =t }
{ A1    | B1 }
""")

TABLE_TEXT.append("""
+----+
| H1 |
+----+----+
| A1 | B1 |
+----+----+
""")

# Transparent cell in the bottom right corner
TABLE_SRC.append("""
{ =h H1 | =h H2 }
{ A1    | =t }
""")

TABLE_TEXT.append("""
+----+----+
| H1 | H2 |
+----+----+
| A1 |
+----+
""")

# Transparent cell in the bottom left corner
TABLE_SRC.append("""
{ =h H1 | =h H2 }
{ =t    | B1 }
""")

TABLE_TEXT.append("""
+----+----+
| H1 | H2 |
+----+----+
     | B1 |
     +----+
""")

# Transparent cells with rowspan > 1 in the top corners
TABLE_SRC.append("""
{ =t,r2 | H1    | =t,r2 }
{         =h H2         }
{ A1    | B1    | C1    }
""")

TABLE_TEXT.append("""
     +----+
     | H1 |
     | H2 |
+----+----+----+
| A1 | B1 | C1 |
+----+----+----+
""")

# Transparent cells with rowspan > 1 in the bottom corners
TABLE_SRC.append("""
{ =h H1 | =h H2 | =h H3 }
{ =t,r2 | B1    | =t,r2 }
{         B2 }
""")

TABLE_TEXT.append("""
+----+----+----+
| H1 | H2 | H3 |
+----+----+----+
     | B1 |
     | B2 |
     +----+
""")

# Adjacent transparent cells
TABLE_SRC.append("""
{ =h H1 | =h H2 | =h H3 }
{ =h A1 | =h B1 | =t,r2 }
{ A2    | =t }
""")

TABLE_TEXT.append("""
+----+----+----+
| H1 | H2 | H3 |
+----+----+----+
| A1 | B1 |
+----+----+
| A2 |
+----+
""")

# More adjacent transparent cells
TABLE_SRC.append("""
{ =h H1 | =h H2 | =h H3 }
{ =t,r2 | =h B1 | =h C1 }
{         =t    | C2 }
""")

TABLE_TEXT.append("""
+----+----+----+
| H1 | H2 | H3 |
+----+----+----+
     | B1 | C1 |
     +----+----+
          | C2 |
          +----+
""")

# Short header row ending with a (redundant) transparent cell
TABLE_SRC.append("""
{ =h A1 | =t }
{ A2 | B2 | C2 }
""")

TABLE_TEXT.append("""
+----+
| A1 |
+----+----+----+
| A2 | B2 | C2 |
+----+----+----+
""")

# Transparent cell in the last column between the top and bottom rows
TABLE_SRC.append("""
{ =h A1 | =h B1 | =h C1 }
{ =h A2 | =h B2 | =t }
{ A3 | B3 | C3 }
""")

TABLE_TEXT.append("""
+----+----+----+
| A1 | B1 | C1 |
+----+----+----+
| A2 | B2 |
+----+----+----+
| A3 | B3 | C3 |
+----+----+----+
""")

# Transparent cell in the bottom row between the first and last columns
TABLE_SRC.append("""
{ =h A1 | =h B1 | =h C1 }
{ =h A2 | =h B2 | =h C2 }
{ A3 | =t | C3 }
""")

TABLE_TEXT.append("""
+----+----+----+
| A1 | B1 | C1 |
+----+----+----+
| A2 | B2 | C2 |
+----+----+----+
| A3 |    | C3 |
+----+    +----+
""")

# Transparent cell in the first column between the top and bottom rows
TABLE_SRC.append("""
{ =h A1 | =h B1 | =h C1 }
{ =t | =h B2 | =h C2 }
{ A3 | B3 | C3 }
""")

TABLE_TEXT.append("""
+----+----+----+
| A1 | B1 | C1 |
+----+----+----+
     | B2 | C2 |
+----+----+----+
| A3 | B3 | C3 |
+----+----+----+
""")

# Transparent cell in the top row between the first and last columns
TABLE_SRC.append("""
{ =h A1 | =t | =h C1 }
{ =h A2 | =h B2 | =h C2 }
{ A3 | B3 | C3 }
""")

TABLE_TEXT.append("""
+----+    +----+
| A1 |    | C1 |
+----+----+----+
| A2 | B2 | C2 |
+----+----+----+
| A3 | B3 | C3 |
+----+----+----+
""")

# Header cell with rowspan > 1 and wrapped contents in the first column
TABLE_SRC.append("""(,:w)
{ =h,r2 The contents of this cell are wrapped onto two lines because of their excessive length | =h B1 }
{ =h B2 }
""")

TABLE_TEXT.append("""
+-----------------------------------------------------------------+----+
| The contents of this cell are wrapped onto two lines because of | B1 |
| their excessive length                                          +----+
|                                                                 | B2 |
+-----------------------------------------------------------------+----+
""")

# Header cell with rowspan > 1 and wrapped contents in the last column
TABLE_SRC.append("""(,,:w)
; { =h A1 | =h,r2 The contents of this cell are wrapped onto two lines because of their excessive length }
; { =h A2 }
""")

TABLE_TEXT.append("""
+----+-----------------------------------------------------------------+
| A1 | The contents of this cell are wrapped onto two lines because of |
+----+ their excessive length                                          |
| A2 |                                                                 |
+----+-----------------------------------------------------------------+
""")

# Header cell with rowspan > 1 and wrapped contents in the middle column
TABLE_SRC.append("""(,,:w)
{ =h A1 | =h,r2 The contents of this cell are wrapped onto two lines because of their excessive length | =h C1 }
{ =h A2 | =h C2 }
""")

TABLE_TEXT.append("""
+----+-----------------------------------------------------------------+----+
| A1 | The contents of this cell are wrapped onto two lines because of | C1 |
+----+ their excessive length                                          +----+
| A2 |                                                                 | C2 |
+----+-----------------------------------------------------------------+----+
""")

TEST_TABLES = []
TABLE_ERRORS = []

# No closing ')' in CSS class list
TEST_TABLES.append("""; @start
; Routine
;
; #TABLE(class1,class2,
; { Hi }
; TABLE#
c32768 RET
""")

TABLE_ERRORS.append(("""Cannot find closing ')' in table CSS class list:
(class1,class2, { Hi } TABLE#"""))

# No space after the opening '{'
TEST_TABLES.append("""; @start
; Routine
;
; #TABLE
; {Lo }
; TABLE#
c49152 RET
""")

TABLE_ERRORS.append("""Cannot find opening '{ ' in table row:
{Lo } TABLE#""")

# No space before the closing '}'
TEST_TABLES.append("""; @start
; Routine
;
; #TABLE
; { Yo}
; TABLE#
c24576 RET
""")

TABLE_ERRORS.append("""Cannot find closing ' }' in table row:
{ Yo} TABLE#""")

LIST_BULLET = []
LIST_SRC = []
LIST_TEXT = []

LIST_BULLET.append('*')
LIST_SRC.append("""(data)
{ Really long item that should end up being wrapped onto two lines when rendered in ASM mode }
{ Short item with a skool macro: #REGa }
""")
LIST_TEXT.append("""
* Really long item that should end up being wrapped onto two lines when
  rendered in ASM mode
* Short item with a skool macro: A
""")

LIST_BULLET.append('--')
LIST_SRC.append("""
{ Really long item that should end up being wrapped onto two lines when rendered in ASM mode }
{ Short item }
""")
LIST_TEXT.append("""
-- Really long item that should end up being wrapped onto two lines when
   rendered in ASM mode
-- Short item
""")

TEST_LISTS = []
LIST_ERRORS = []

# No closing ')' in parameter list
TEST_LISTS.append("""; @start
; Routine
;
; #LIST(default
; { Item 1 }
; LIST#
c32768 RET
""")

LIST_ERRORS.append("""Cannot find closing ')' in parameter list:
(default { Item 1 } LIST#""")

# No space after the opening '{'
TEST_LISTS.append("""; @start
; Routine
;
; #LIST
; {Item }
; LIST#
c40000 RET
""")

LIST_ERRORS.append("""Cannot find opening '{ ' in list item:
{Item } LIST#""")

# No space before the closing '}'
TEST_LISTS.append("""; @start
; Routine
;
; #LIST
; { Item}
; LIST#
c50000 RET
""")

LIST_ERRORS.append("""Cannot find closing ' }' in list item:
{ Item} LIST#""")

ERROR_PREFIX = 'Error while parsing #{0} macro'

def get_chr(code):
    return chr(code) if PY3 else unichr(code).encode('utf-8')

class AsmWriterTest(SkoolKitTestCase):
    def _get_writer(self, skool='', crlf=False, tab=False, case=None, base=None, instr_width=23, warn=False, asm_mode=1, fix_mode=0):
        skoolfile = self.write_text_file(skool, suffix='.skool')
        skool_parser = SkoolParser(skoolfile, case=case, base=base, asm_mode=asm_mode, fix_mode=fix_mode)
        return AsmWriter(skool_parser, crlf, tab, skool_parser.properties, case == CASE_LOWER, instr_width, warn)

    def _get_asm(self, skool, crlf=False, tab=False, case=None, base=None, instr_width=23, warn=False, asm_mode=1, fix_mode=0):
        self.clear_streams()
        writer = self._get_writer(skool, crlf, tab, case, base, instr_width, warn, asm_mode, fix_mode)
        writer.write()
        asm = self.out.getvalue().split('\n')[:-1]
        if warn:
            return asm, self.err.getvalue().split('\n')[:-1]
        return asm

    def _test_unsupported_macro(self, text):
        search = re.search('#[A-Z]+', text)
        macro = search.group()
        writer = self._get_writer()
        with self.assertRaisesRegexp(SkoolParsingError, 'Found unsupported macro: {}'.format(macro)):
            writer.expand(text)

    def _test_reference_macro(self, macro, def_link_text):
        writer = self._get_writer()
        for link_text in ('',  '(testing)', '(testing (nested) parentheses)'):
            for anchor in ('', '#name'):
                output = writer.expand('#{0}{1}{2}'.format(macro, anchor, link_text))
                self.assertEqual(output, link_text[1:-1] or def_link_text)

    def _test_call(self, *args):
        return str(args)

    def _test_call_no_retval(self, *args):
        return

    def test_macro_bug(self):
        self._test_reference_macro('BUG', 'bug')

    def test_macro_call(self):
        writer = self._get_writer(warn=True)
        writer.test_call = self._test_call

        # All arguments given
        output = writer.expand('#CALL:test_call(10,t,5)')
        self.assertEqual(output, self._test_call(10, 't', 5))

        # One argument omitted
        output = writer.expand('#CALL:test_call(7,,test2)')
        self.assertEqual(output, self._test_call(7, None, 'test2'))

        prefix = ERROR_PREFIX.format('CALL')

        # Malformed #CALL macro
        with self.assertRaisesRegexp(SkoolParsingError, '{}: Malformed macro: #CALLt...'.format(prefix)):
            writer.expand('#CALLtest_call(5,s)')

        # #CALL a non-method
        writer.var = 'x'
        with self.assertRaisesRegexp(SkoolParsingError, '{}: Uncallable method name: var'.format(prefix)):
            writer.expand('#CALL:var(0)')

        # No argument list
        with self.assertRaisesRegexp(SkoolParsingError, '{}: No argument list specified: #CALL:test_call'.format(prefix)):
            writer.expand('#CALL:test_call')

        # No return value
        writer.test_call_no_retval = self._test_call_no_retval
        output = writer.expand('#CALL:test_call_no_retval(1,2)')
        self.assertEqual(output, '')

        # Unknown method
        method_name = 'nonexistent_method'
        output = writer.expand('#CALL:{0}(0)'.format(method_name))
        self.assertEqual(output, '')
        self.assertEqual(self.err.getvalue().split('\n')[0], 'WARNING: Unknown method name in #CALL macro: {0}'.format(method_name))

    def test_macro_chr(self):
        writer = self._get_writer()

        output = writer.expand('#CHR169')
        self.assertEqual(output, get_chr(169))

        output = writer.expand('#CHR(163)1985')
        self.assertEqual(output, '{0}1985'.format(get_chr(163)))

    def test_macro_d(self):
        writer = self._get_writer(TEST_MACRO_D)

        output = writer.expand('#D32768')
        self.assertEqual(output, 'First routine')

        output = writer.expand('#D$8001')
        self.assertEqual(output, 'Second routine')

        prefix = ERROR_PREFIX.format('D')

        # Descriptionless entry
        address = 32770
        with self.assertRaisesRegexp(SkoolParsingError, '{}: Entry at {} has no description'.format(prefix, address)):
            writer.expand('#D{0}'.format(address))

        # Nonexistent entry
        address = 32771
        with self.assertRaisesRegexp(SkoolParsingError, '{}: Cannot determine description for nonexistent entry at {}'.format(prefix, address)):
            writer.expand('#D{0}'.format(address))

    def test_macro_erefs(self):
        writer = self._get_writer(TEST_MACRO_EREFS)

        for address in ('30004', '$7534'):
            output = writer.expand('#EREFS{}'.format(address))
            self.assertEqual(output, 'routines at 30000 and 30005')

        # Entry point with no referrers
        prefix = ERROR_PREFIX.format('EREFS')
        address = 30005
        with self.assertRaisesRegexp(SkoolParsingError, '{}: Entry point at {} has no referrers'.format(prefix, address)):
            writer.expand('#EREFS{0}'.format(address))

    def test_macro_fact(self):
        self._test_reference_macro('FACT', 'fact')

    def test_macro_font(self):
        self._test_unsupported_macro('#FONT55584,96,,,1')

    def test_macro_html(self):
        writer = self._get_writer()
        delimiters = {
            '(': ')',
            '[': ']',
            '{': '}'
        }
        for text in('', 'See <a href="url">this</a>', 'A &gt; B'):
            for delim1 in '([{!@$%^*_-+|':
                delim2 = delimiters.get(delim1, delim1)
                output = writer.expand('#HTML{0}{1}{2}'.format(delim1, text, delim2))
                self.assertEqual(output, '')

        # Unterminated #HTML macro
        prefix = ERROR_PREFIX.format('HTML')
        macro = '#HTML:unterminated'
        with self.assertRaisesRegexp(SkoolParsingError, '{}: No terminating delimiter: {}'.format(prefix, macro)):
            writer.expand(macro)

    def test_macro_link(self):
        writer = self._get_writer()

        link_text = 'Testing'
        output = writer.expand('#LINK:PageID#anchor({0})'.format(link_text))
        self.assertEqual(output, link_text)

        prefix = ERROR_PREFIX.format('LINK')

        # Malformed #LINK macro
        with self.assertRaisesRegexp(SkoolParsingError, '{}: Malformed macro: #LINKp...'.format(prefix)):
            writer.expand('#LINKpageID')

        # No link text
        with self.assertRaisesRegexp(SkoolParsingError, '{}: No link text specified: #LINK:PageID'.format(prefix)):
            writer.expand('#LINK:PageID')

    def test_macro_list(self):
        writer = self._get_writer()
        for bullet, src, text in zip(LIST_BULLET, LIST_SRC, LIST_TEXT):
            writer.bullet = bullet
            list_src = '#LIST{0}\nLIST#'.format(src)
            output = '\n'.join(writer.format(list_src, 79))
            self.assertEqual(output, text.strip())

    def test_macro_poke(self):
        self._test_reference_macro('POKE', 'poke')

    def test_macro_pokes(self):
        writer = self._get_writer()
        snapshot = writer.snapshot

        output = writer.expand('#POKES32768,255')
        self.assertEqual(output, '')
        self.assertEqual(snapshot[32768], 255)

        output = writer.expand('#POKES32768,254,10')
        self.assertEqual(output, '')
        self.assertEqual(snapshot[32768:32778], [254] * 10)

        output = writer.expand('#POKES32768,253,20,2')
        self.assertEqual(output, '')
        self.assertEqual(snapshot[32768:32808:2], [253] * 20)

        output = writer.expand('#POKES49152,1;49153,2')
        self.assertEqual(output, '')
        self.assertEqual(snapshot[49152:49154], [1, 2])

    def test_macro_pops(self):
        writer = self._get_writer()
        addr, byte = 49152, 128
        writer.snapshot[addr] = byte
        writer.push_snapshot('test')
        writer.snapshot[addr] = (byte + 127) % 256
        output = writer.expand('#POPS')
        self.assertEqual(output, '')
        self.assertEqual(writer.snapshot[addr], byte)

    def test_macro_pushs(self):
        writer = self._get_writer()
        addr, byte = 32768, 64
        writer.snapshot[addr] = byte
        output = writer.expand('#PUSHStest')
        self.assertEqual(output, '')
        self.assertEqual(writer.snapshot[addr], byte)
        writer.snapshot[addr] = (byte + 127) % 256
        writer.pop_snapshot()
        self.assertEqual(writer.snapshot[addr], byte)

    def test_macro_r(self):
        skool = '\n'.join((
            '; @start',
            '; @label=DOSTUFF',
            'c24576 LD HL,0',
            '',
            'b$6003 DEFB 123'
        ))
        writer = self._get_writer(skool, warn=True)

        # Address resolves to a label
        output = writer.expand('#R24576')
        self.assertEqual(output, 'DOSTUFF')

        # Link text
        link_text = 'Testing1'
        output = writer.expand('#R24576({0})'.format(link_text))
        self.assertEqual(output, link_text)

        # Anchor
        output = writer.expand('#R24576#foo')
        self.assertEqual(output, 'DOSTUFF')

        # Anchor and link text
        link_text = 'Testing2'
        output = writer.expand('#R24576#foo({})'.format(link_text))
        self.assertEqual(output, link_text)

        # No label
        output = writer.expand('#R24579')
        self.assertEqual(output, '6003')
        self.assertEqual(self.err.getvalue(), 'WARNING: Could not convert address 24579 to label\n')
        self.clear_streams()

        # Address between instructions
        output = writer.expand('#R24577')
        self.assertEqual(output, '24577')
        self.assertEqual(self.err.getvalue(), 'WARNING: Could not convert address 24577 to label\n')
        self.clear_streams()

        # Hexadecimal address between instructions
        output = writer.expand('#R$6001')
        self.assertEqual(output, '6001')
        self.assertEqual(self.err.getvalue(), 'WARNING: Could not convert address $6001 to label\n')

    def test_macro_r_other_code(self):
        skool = '\n'.join((
            '; @start',
            'c49152 LD HL,0',
            ' $c003 RET',
            '',
            'r$c000 other',
            ' $C003'
        ))
        writer = self._get_writer(skool)

        # Reference with the same address as a remote entry
        output = writer.expand('#R49152')
        self.assertEqual(output, '49152')

        # Reference with the same address as a remote entry point
        output = writer.expand('#R49155')
        self.assertEqual(output, 'c003')

        # Other code, no remote entry
        output = writer.expand('#R32768@other')
        self.assertEqual(output, '32768')

        # Other code with remote entry
        output = writer.expand('#R49152@other')
        self.assertEqual(output, 'c000')

        # Other code with remote entry point
        output = writer.expand('#R49155@other')
        self.assertEqual(output, 'C003')

        # Other code with link text
        link_text = 'Testing2'
        output = writer.expand('#R32768@other#testing({0})'.format(link_text))
        self.assertEqual(output, link_text)

    def test_macro_r_lower(self):
        skool = '\n'.join((
            '; @start',
            '; @label=START',
            'c32000 RET',
            '',
            'b$7D01 DEFB 0',
            '',
            'r$C000 other'
        ))
        writer = self._get_writer(skool, case=CASE_LOWER)

        # Label
        output = writer.expand('#R32000')
        self.assertEqual(output, 'START')

        # No label
        output = writer.expand('#R32001')
        self.assertEqual(output, '7d01')

        # Other code, no remote entry
        output = writer.expand('#R32768@main')
        self.assertEqual(output, '32768')

        # Other code with remote entry
        output = writer.expand('#R49152@other')
        self.assertEqual(output, 'c000')

    def test_macro_r_hex(self):
        skool = '\n'.join((
            '; @start',
            'c24580 RET',
            '',
            'r49152 other',
        ))
        writer = self._get_writer(skool, base=BASE_16)

        # No label
        output = writer.expand('#R24580')
        self.assertEqual(output, '6004')

        # Other code, no remote entry
        output = writer.expand('#R32768@main')
        self.assertEqual(output, '8000')

        # Other code with remote entry
        output = writer.expand('#R49152@other')
        self.assertEqual(output, 'C000')

    def test_macro_r_hex_lower(self):
        skool = '\n'.join((
            '; @start',
            'c24590 RET',
            '',
            'r49152 other'
        ))
        writer = self._get_writer(skool, base=BASE_16, case=CASE_LOWER)

        # No label
        output = writer.expand('#R24590')
        self.assertEqual(output, '600e')

        # Other code, no remote entry
        output = writer.expand('#R43981@main')
        self.assertEqual(output, 'abcd')

        # Other code with remote entry
        output = writer.expand('#R49152@other')
        self.assertEqual(output, 'c000')

    def test_macro_r_decimal(self):
        skool = '\n'.join((
            '; @start',
            'c$8000 LD A,B',
            '',
            'r$C000 other'
        ))
        writer = self._get_writer(skool, base=BASE_10)

        # No label
        output = writer.expand('#R$8000')
        self.assertEqual(output, '32768')

        # Other code, no remote entry
        output = writer.expand('#R44444@main')
        self.assertEqual(output, '44444')

        # Other code with remote entry
        output = writer.expand('#R$c000@main')
        self.assertEqual(output, '49152')

    def test_macro_refs(self):
        writer = self._get_writer(TEST_MACRO_REFS)

        # Some referrers
        for address in ('24581', '$6005'):
            output = writer.expand('#REFS{}'.format(address))
            self.assertEqual(output, 'routines at 24583, 24586 and 24589')

        # No referrers
        output = writer.expand('#REFS24586')
        self.assertEqual(output, 'Not used directly by any other routines')

        # Nonexistent entry
        prefix = ERROR_PREFIX.format('REFS')
        address = 40000
        with self.assertRaisesRegexp(SkoolParsingError, '{}: No entry at {}'.format(prefix, address)):
            writer.expand('#REFS{0}'.format(address))

    def test_macro_reg(self):
        writer = self._get_writer()
        for reg in ("a", "b", "c", "d", "e", "h", "l", "i", "r", "ixl", "ixh", "iyl", "iyh", "b'", "c'", "d'", "e'", "h'", "l'", "bc", "de", "hl", "sp", "ix", "iy", "bc'", "de'", "hl'"):
            output = writer.expand('#REG{0}'.format(reg))
            self.assertEqual(output, reg.upper())

        prefix = ERROR_PREFIX.format('REG')

        # Missing register argument
        with self.assertRaisesRegexp(SkoolParsingError, '{}: Missing register argument'.format(prefix)):
            writer.expand('#REG')

        # Bad register arguments
        for bad_reg in ('q', 'toolong', 'az', 'mb'):
            with self.assertRaisesRegexp(SkoolParsingError, '{}: Bad register: "{}"'.format(prefix, bad_reg)):
                writer.expand('#REG{0}'.format(bad_reg))

    def test_macro_scr(self):
        self._test_unsupported_macro('#SCR2(fname)')

    def test_macro_space(self):
        writer = self._get_writer()

        output = writer.expand('"#SPACE"')
        self.assertEqual(output, '" "')

        output = writer.expand('"#SPACE5"')
        self.assertEqual(output, '"     "')

        output = writer.expand('1#SPACE(3)1')
        self.assertEqual(output, '1   1')

    def test_macro_table(self):
        writer = self._get_writer()
        for src, text in zip(TABLE_SRC, TABLE_TEXT):
            table = '#TABLE{0}\nTABLE#'.format(src)
            output = writer.format(table, 79)
            self.assertEqual(output, text.split('\n')[1:-1])

    def test_macro_udg(self):
        self._test_unsupported_macro('#UDG39144,6(safe_key)')

    def test_macro_udgarray(self):
        self._test_unsupported_macro('#UDGARRAY8,,,256;33008-33023(bubble)')

    def test_macro_udgtable(self):
        writer = self._get_writer()
        udgtable = '#UDGTABLE{0}\nUDGTABLE#'.format(TABLE_SRC[0])
        output = writer.format(udgtable, 79)
        self.assertEqual(output, [])

    def test_unknown_macro(self):
        writer = self._get_writer()
        for macro, params in (('#FOO', 'xyz'), ('#BAR', '1,2(baz)'), ('#UDGS', '#r1'), ('#LINKS', '')):
            with self.assertRaisesRegexp(SkoolParsingError, 'Found unknown macro: {}'.format(macro)):
                writer.expand(macro + params)

    def test_property_handle_unsupported_macros(self):
        skool = '; @start\n; @set-handle-unsupported-macros={}'
        macros = (
            '#FONT30000,2',
            '#SCR2{0,0,0,0}',
            '#UDG56000:56008(icon)',
            '#UDGARRAY5;40000-40016-8x4{0,0,10,10}(sprite.gif)'
        )

        # handle-unsupported-macros = 0
        writer = self._get_writer(skool.format(0))
        for macro in macros:
            with self.assertRaises(SkoolParsingError) as cm:
                writer.expand(macro)
            marker = re.search('#[A-Z]+', macro).group()
            self.assertEqual(cm.exception.args[0], 'Found unsupported macro: {}'.format(marker))

        # handle-unsupported-macros = 1
        writer = self._get_writer(skool.format(1))
        for macro in macros:
            self.assertEqual(writer.expand(macro), '')

    def test_property_label_colons(self):
        skool = '\n'.join((
            '; @start',
            '; @set-label-colons={}',
            '; @label=START',
            'c30000 RET'
        ))

        # label-colons=0
        asm = self._get_asm(skool.format(0))
        self.assertEqual(asm[0], 'START')

        # label-colons=1
        asm = self._get_asm(skool.format(1))
        self.assertEqual(asm[0], 'START:')

    def test_continuation_line(self):
        asm = self._get_asm(TEST_CONTINUATION_LINE)
        self.assertEqual(asm[2], '                          ; require a continuation line')

    def test_warn_unconverted_addresses(self):
        self._get_asm(TEST_UNCONVERTED_ADDRESSES, warn=True)
        warnings = self.err.getvalue().split('\n')[:-1]
        self.assertEqual(len(warnings), 8)
        self.assertEqual(warnings[0], 'WARNING: Comment contains address (32768) not converted to a label:')
        self.assertEqual(warnings[1], '; Routine at 32768')
        self.assertEqual(warnings[2], 'WARNING: Comment contains address (32768) not converted to a label:')
        self.assertEqual(warnings[3], '; Used by the routine at 32768.')
        self.assertEqual(warnings[4], 'WARNING: Comment at 32768 contains address (32768) not converted to a label:')
        self.assertEqual(warnings[5], '  LD A,B                  ; This instruction is at 32768')
        self.assertEqual(warnings[6], 'WARNING: Comment above 32769 contains address (32769) not converted to a label:')
        self.assertEqual(warnings[7], '; This mid-routine comment is above 32769.')

    def test_warn_long_line(self):
        self._get_asm(TEST_LONG_LINE, instr_width=30, warn=True)
        warnings = self.err.getvalue().split('\n')[:-1]
        self.assertEqual(len(warnings), 2)
        self.assertEqual(warnings[0], 'WARNING: Line is 80 characters long:')
        self.assertEqual(warnings[1], '  BIT 3,(IX+101)                 ; Pneumonoultramicroscopicsilicovolcanoconiosis')

    def test_warn_wide_table(self):
        self._get_asm(TEST_WIDE_TABLE, warn=True)
        warnings = self.err.getvalue().split('\n')[:-1]
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0], 'WARNING: Table in entry at 50000 is 91 characters wide')

    def test_option_crlf(self):
        asm = self._get_asm(TEST_CRLF, crlf=True)
        self.assertTrue(all(line.endswith('\r') for line in asm))

    def test_option_tab(self):
        asm = self._get_asm(TEST_TAB, tab=True)
        for line in asm:
            if line and line[0].isspace():
                self.assertEqual(line[0], '\t')

    def test_option_lower(self):
        asm = self._get_asm(TEST_LOWER, case=CASE_LOWER)

        # Test that the ORG directive is in lower case
        self.assertEqual(asm[0], '  org 24576')

        # Test that register names are in lower case
        self.assertEqual(asm[6], '; a Value')
        self.assertEqual(asm[7], '; b Another value')

        # Test that labels are unaffected
        self.assertEqual(asm[8], 'DOSTUFF:')

        # Test that #REG macro arguments are in lower case
        self.assertEqual(asm[12], '  defb 123                ; a=0')

        # Test that #R macro arguments that resolve to a label are unaffected
        self.assertEqual(asm[13], '  defb 246                ; DOSTUFF')

    def test_option_instr_width(self):
        for width in (5, 10, 15, 20, 25, 30):
            asm = self._get_asm(TEST_INSTR_WIDTH, instr_width=width)
            self.assertEqual(asm[1], '  {0} ; A=0'.format('DEFB 123'.ljust(width)))

    def test_header(self):
        asm = self._get_asm(TEST_HEADER)
        self.assertEqual(asm[0], '; Header line 1.')
        self.assertEqual(asm[1], '; Header line 2.')
        self.assertEqual(asm[2], '')
        self.assertEqual(asm[3], '; Start')

    def test_registers(self):
        asm = self._get_asm(TEST_REGISTERS)

        # Traditional
        self.assertEqual(asm[4], '; A Some value')
        self.assertEqual(asm[5], '; B Some other value')

        # With prefixes (right-justified to longest prefix)
        self.assertEqual(asm[12], ';  Input:a Some value')
        self.assertEqual(asm[13], ';        b Some other value')
        self.assertEqual(asm[14], '; Output:c The result')

    def test_registers_upper(self):
        asm = self._get_asm(TEST_REGISTERS, case=CASE_UPPER)
        self.assertEqual(asm[12], ';  Input:A Some value')
        self.assertEqual(asm[13], ';        B Some other value')
        self.assertEqual(asm[14], '; Output:C The result')

    def test_defm_upper(self):
        asm = self._get_asm(TEST_DEFM, case=CASE_UPPER)
        self.assertEqual(asm[1], '  DEFM "AbCdEfG"')
        self.assertEqual(asm[4], '  DEFM "hIjKlMn"')

    def test_defm_lower(self):
        asm = self._get_asm(TEST_DEFM, case=CASE_LOWER)
        self.assertEqual(asm[1], '  defm "AbCdEfG"')
        self.assertEqual(asm[4], '  defm "hIjKlMn"')

    def test_empty_description(self):
        asm = self._get_asm(TEST_EMPTY_DESCRIPTION)
        self.assertEqual(asm[0], '; Test an empty description')
        self.assertEqual(asm[1], '  RET')

    def test_empty_description_with_registers(self):
        asm = self._get_asm(TEST_EMPTY_DESCRIPTION_WITH_REGISTERS)
        self.assertEqual(asm[0], '; Test an empty description and a register section')
        self.assertEqual(asm[1], ';')
        self.assertEqual(asm[2], '; A 0')
        self.assertEqual(asm[4], '  RET')

    def test_end_comment(self):
        asm = self._get_asm(TEST_END_COMMENT)
        self.assertEqual(asm[1], '  RET')
        self.assertEqual(asm[2], '; End comment.')

    def test_entry_point_labels(self):
        asm = self._get_asm(TEST_ENTRY_POINT_LABELS)
        self.assertEqual(asm[1], 'START:')
        self.assertEqual(asm[3], 'START_0:')
        self.assertEqual(asm[5], 'START_1:')

    def test_decimal(self):
        asm = self._get_asm(TEST_DECIMAL, base=BASE_10)
        self.assertEqual(asm[:-1], TEST_DECIMAL_ASM)

    def test_decimal_lower(self):
        asm = self._get_asm(TEST_DECIMAL, base=BASE_10, case=CASE_LOWER)
        self.assertEqual(asm[:-1], TEST_DECIMAL_ASM_LOWER)

    def test_decimal_upper(self):
        asm = self._get_asm(TEST_DECIMAL, base=BASE_10, case=CASE_UPPER)
        self.assertEqual(asm[:-1], TEST_DECIMAL_ASM_UPPER)

    def test_hex(self):
        asm = self._get_asm(TEST_HEX, base=BASE_16)
        self.assertEqual(asm[:-1], TEST_HEX_ASM)

    def test_hex_lower(self):
        asm = self._get_asm(TEST_HEX, base=BASE_16, case=CASE_LOWER)
        self.assertEqual(asm[:-1], TEST_HEX_ASM_LOWER)

    def test_hex_upper(self):
        asm = self._get_asm(TEST_HEX, base=BASE_16, case=CASE_UPPER)
        self.assertEqual(asm[:-1], TEST_HEX_ASM_UPPER)

    def test_end_directive(self):
        asm = self._get_asm(TEST_END_DIRECTIVE)
        self.assertEqual(len(asm), 3)
        self.assertEqual(asm[1], '  RET')
        self.assertEqual(asm[2], '')

    def test_isub_directive(self):
        for asm_mode in (1, 2, 3):
            asm = self._get_asm(TEST_ISUB_DIRECTIVE, asm_mode=asm_mode)
            self.assertEqual(asm[1], '  LD A,(32512)')

    def test_isub_block_directive(self):
        for asm_mode in (1, 2, 3):
            asm = self._get_asm(TEST_ISUB_BLOCK_DIRECTIVE)
            self.assertEqual(asm[2], '; Actual description.')
            self.assertEqual(asm[3], '  RET')

    def test_rsub_directive(self):
        for asm_mode in (1, 2):
            asm = self._get_asm(TEST_RSUB_DIRECTIVE, asm_mode=asm_mode)
            self.assertEqual(asm[1], '  INC L')
        asm = self._get_asm(TEST_RSUB_DIRECTIVE, asm_mode=3)
        self.assertEqual(asm[1], '  INC HL')

    def test_ignoreua_directive(self):
        self._get_asm(TEST_IGNOREUA_DIRECTIVE, warn=True)
        warnings = self.err.getvalue().split('\n')[:-1]
        self.assertEqual(len(warnings), 0)

    def test_nowarn_directive(self):
        for asm_mode in (1, 2, 3):
            self._get_asm(TEST_NOWARN_DIRECTIVE, warn=True, asm_mode=asm_mode)
            warnings = self.err.getvalue().split('\n')[:-1]
            self.assertEqual(len(warnings), 0)

    def test_keep_directive(self):
        asm = self._get_asm(TEST_KEEP_DIRECTIVE)
        self.assertEqual(asm[1], '  LD HL,30003')

    def test_nolabel_directive(self):
        asm = self._get_asm(TEST_NOLABEL_DIRECTIVE)
        self.assertEqual(asm[1], 'START:')
        self.assertEqual(asm[2], '  LD A,B')
        self.assertEqual(asm[3], '  RET')

    def test_invalid_block_directives(self):
        for i, skool in enumerate(TEST_INVALID_BLOCK_DIRECTIVES):
            with self.assertRaisesRegexp(SkoolParsingError, re.escape(INVALID_BLOCK_DIRECTIVE_WARNINGS[i])):
                self._get_asm(skool)

    def test_table_parsing_errors(self):
        for i, skool in enumerate(TEST_TABLES):
            with self.assertRaisesRegexp(SkoolParsingError, re.escape(TABLE_ERRORS[i])):
                self._get_asm(skool)

    def test_list_parsing_errors(self):
        for i, skool in enumerate(TEST_LISTS):
            with self.assertRaisesRegexp(SkoolParsingError, re.escape(LIST_ERRORS[i])):
                self._get_asm(skool)

if __name__ == '__main__':
    unittest.main()
