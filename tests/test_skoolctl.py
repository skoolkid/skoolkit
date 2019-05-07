from io import StringIO
import textwrap

from skoolkittest import SkoolKitTestCase
from skoolkit import SkoolParsingError
from skoolkit.skoolctl import CtlWriter

DIRECTIVES = 'bcgistuw'

TEST_SKOOL = r"""; Dangling comment not associated with any entry

; Address 0
@label=START0
c00000 RET

; Address with 1 digit
@label=START1
c00001 RET

; Address with 2 digits
@label=START33
c00033 RET

; Address with 3 digits
@label=START555
c00555 RET

; Address with 4 digits
@label=START7890
c07890 RET

@start
@writer=package.module.classname
@set-bullet=+
@org=32768
; Routine
;
; Routine description
;
; A Some value
; B Another value
;
; Start comment
@label=START
c32768 NOP          ; Do nothing
@bfix=DEFB 2,3
 32769 DEFB 1,2     ; 1-line B sub-block
@nowarn
 32771 defb 3       ; {2-line B sub-block
@isub=DEFB 0,1
 32772 DEFB 4,5     ; }
; Mid-block comment
 32774 DEFM "Hello" ; T sub-block
@keep
 32779 DEFW 12345   ; W sub-block
 32781 defs 2       ; S sub-block
 32783 LD A,5       ; {Sub-block with instructions of various types
@ofix=DEFB 2
 32785 DEFB 0       ;
@rsub=DEFW 0,1,2
 32786 DEFW 0,1     ; and blank lines
@ssub=DEFM "Lo"
 32790 defm "H",105 ;
@rfix=DEFB 0
 32792 DEFS 3       ; in the comment}
 $801B RET          ; Instruction with a
                    ; comment continuation line
; End comment paragraph 1.
; .
; End comment paragraph 2.

; Ignore block
i32796

; Data block
@rem=Hello!
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

; Data block beginning with a 1-byte sub-block
b49162 DEFB 0
 49163 RET

; Text block beginning with a 1-byte sub-block
t49164 DEFM "a"
 49165 RET

; Word block beginning with a 2-byte sub-block
w49166 DEFW 23
 49168 RET

; Zero block
s49169 DEFS 9
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
@bfix-begin
b49193 DEFB 7
@bfix+else
c49193 NOP
@bfix+end

; Zero block
s49194 DEFS 128
 49322 DEFS 128
 49450 DEFS 128
@end

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

; Routine with an empty multi-instruction comment and instruction comments that
; start with a '.'
c49635 XOR B ; {
 49636 XOR C ; }
 49637 XOR D ; {...and so on
 49638 XOR E ; }
 49639 XOR H ; {...
 49640 XOR L ; }
 49641 XOR A ; ...
 49642 RET   ; ...until the end

; Another ignore block
i49643
; End comment on the final block.
"""

TEST_CTL = """> 00000 ; Dangling comment not associated with any entry
c 00000 Address 0
@ 00000 label=START0
c 00001 Address with 1 digit
@ 00001 label=START1
c 00033 Address with 2 digits
@ 00033 label=START33
c 00555 Address with 3 digits
@ 00555 label=START555
c 07890 Address with 4 digits
@ 07890 label=START7890
@ 32768 start
@ 32768 writer=package.module.classname
@ 32768 set-bullet=+
@ 32768 org=32768
c 32768 Routine
D 32768 Routine description
R 32768 A Some value
R 32768 B Another value
N 32768 Start comment
@ 32768 label=START
C 32768,1 Do nothing
@ 32769 bfix=DEFB 2,3
B 32769,2,2 1-line B sub-block
@ 32771 nowarn
@ 32772 isub=DEFB 0,1
B 32771,3,1,2 2-line B sub-block
N 32774 Mid-block comment
T 32774,5,5 T sub-block
@ 32779 keep
W 32779,2,2 W sub-block
S 32781,2,2 S sub-block
M 32783,12 Sub-block with instructions of various types and blank lines in the comment
@ 32785 ofix=DEFB 2
B 32785,1,1
@ 32786 rsub=DEFW 0,1,2
W 32786,4,4
@ 32790 ssub=DEFM "Lo"
T 32790,2,1:B1
@ 32792 rfix=DEFB 0
S 32792,3,3
C 32795,1 Instruction with a comment continuation line
E 32768 End comment paragraph 1.
E 32768 End comment paragraph 2.
i 32796 Ignore block
b 49152 Data block
@ 49152 rem=Hello!
B 49152,1,1
g 49153 Game status buffer entry
W 49153,2,2
t 49155 Message
T 49155,2,2
u 49157 Unused block
B 49157,1,1
w 49158 Word block
W 49158,4,2
b 49162 Data block beginning with a 1-byte sub-block
B 49162,1,1
C 49163,1
t 49164 Text block beginning with a 1-byte sub-block
T 49164,1,1
C 49165,1
w 49166 Word block beginning with a 2-byte sub-block
W 49166,2,2
C 49168,1
s 49169 Zero block
S 49169,9,9
C 49178,1
b 49179 Data block with sub-block lengths amenable to abbreviation (2*3,3*2,1)
B 49179,14,2*3,3*2,1
b 49193 ASM block directives
B 49193,1,1
s 49194 Zero block
S 49194,384,128
@ 49578 end
b 49578 Complex DEFB statements
B 49578,20,3:T5:2,T7:3
t 49598 Complex DEFM statements
T 49598,20,5:B5,B1:7:B2
b 49618 Data block with sequences of complex DEFB statements amenable to abbreviation
B 49618,16,1:T2*2,1,2:T1
c 49634 Routine with an empty block description and a register section
R 49634 BC 0
c 49635 Routine with an empty multi-instruction comment and instruction comments that start with a '.'
C 49635,2 .
C 49637,2 ...and so on
C 49639,2 ....
C 49641,1 ...
C 49642,1 ...until the end
i 49643 Another ignore block
E 49643 End comment on the final block.""".split('\n')

TEST_CTL_HEX = """> $0000 ; Dangling comment not associated with any entry
c $0000 Address 0
@ $0000 label=START0
c $0001 Address with 1 digit
@ $0001 label=START1
c $0021 Address with 2 digits
@ $0021 label=START33
c $022B Address with 3 digits
@ $022B label=START555
c $1ED2 Address with 4 digits
@ $1ED2 label=START7890
@ $8000 start
@ $8000 writer=package.module.classname
@ $8000 set-bullet=+
@ $8000 org=32768
c $8000 Routine
D $8000 Routine description
R $8000 A Some value
R $8000 B Another value
N $8000 Start comment
@ $8000 label=START
C $8000,1 Do nothing
@ $8001 bfix=DEFB 2,3
B $8001,2,2 1-line B sub-block
@ $8003 nowarn
@ $8004 isub=DEFB 0,1
B $8003,3,1,2 2-line B sub-block
N $8006 Mid-block comment
T $8006,5,5 T sub-block
@ $800B keep
W $800B,2,2 W sub-block
S $800D,2,2 S sub-block
M $800F,12 Sub-block with instructions of various types and blank lines in the comment
@ $8011 ofix=DEFB 2
B $8011,1,1
@ $8012 rsub=DEFW 0,1,2
W $8012,4,4
@ $8016 ssub=DEFM "Lo"
T $8016,2,1:B1
@ $8018 rfix=DEFB 0
S $8018,3,3
C $801B,1 Instruction with a comment continuation line
E $8000 End comment paragraph 1.
E $8000 End comment paragraph 2.
i $801C Ignore block
b $C000 Data block
@ $C000 rem=Hello!
B $C000,1,1
g $C001 Game status buffer entry
W $C001,2,2
t $C003 Message
T $C003,2,2
u $C005 Unused block
B $C005,1,1
w $C006 Word block
W $C006,4,2
b $C00A Data block beginning with a 1-byte sub-block
B $C00A,1,1
C $C00B,1
t $C00C Text block beginning with a 1-byte sub-block
T $C00C,1,1
C $C00D,1
w $C00E Word block beginning with a 2-byte sub-block
W $C00E,2,2
C $C010,1
s $C011 Zero block
S $C011,9,9
C $C01A,1
b $C01B Data block with sub-block lengths amenable to abbreviation (2*3,3*2,1)
B $C01B,14,2*3,3*2,1
b $C029 ASM block directives
B $C029,1,1
s $C02A Zero block
S $C02A,384,128
@ $C1AA end
b $C1AA Complex DEFB statements
B $C1AA,20,3:T5:2,T7:3
t $C1BE Complex DEFM statements
T $C1BE,20,5:B5,B1:7:B2
b $C1D2 Data block with sequences of complex DEFB statements amenable to abbreviation
B $C1D2,16,1:T2*2,1,2:T1
c $C1E2 Routine with an empty block description and a register section
R $C1E2 BC 0
c $C1E3 Routine with an empty multi-instruction comment and instruction comments that start with a '.'
C $C1E3,2 .
C $C1E5,2 ...and so on
C $C1E7,2 ....
C $C1E9,1 ...
C $C1EA,1 ...until the end
i $C1EB Another ignore block
E $C1EB End comment on the final block."""

TEST_CTL_ABS = """c 00000
@ 00000 label=START0
c 00001
@ 00001 label=START1
c 00033
@ 00033 label=START33
c 00555
@ 00555 label=START555
c 07890
@ 07890 label=START7890
@ 32768 start
@ 32768 writer=package.module.classname
@ 32768 set-bullet=+
@ 32768 org=32768
c 32768
@ 32768 label=START
@ 32769 bfix=DEFB 2,3
B 32769,2,2
@ 32771 nowarn
@ 32772 isub=DEFB 0,1
B 32771,3,1,2
T 32774,5,5
@ 32779 keep
W 32779,2,2
S 32781,2,2
@ 32785 ofix=DEFB 2
B 32785,1,1
@ 32786 rsub=DEFW 0,1,2
W 32786,4,4
@ 32790 ssub=DEFM "Lo"
T 32790,2,1:B1
@ 32792 rfix=DEFB 0
S 32792,3,3
i 32796
b 49152
@ 49152 rem=Hello!
B 49152,1,1
g 49153
W 49153,2,2
t 49155
T 49155,2,2
u 49157
B 49157,1,1
w 49158
W 49158,4,2
b 49162
B 49162,1,1
C 49163,1
t 49164
T 49164,1,1
C 49165,1
w 49166
W 49166,2,2
C 49168,1
s 49169
S 49169,9,9
C 49178,1
b 49179
B 49179,14,2*3,3*2,1
b 49193
B 49193,1,1
s 49194
S 49194,384,128
@ 49578 end
b 49578
B 49578,20,3:T5:2,T7:3
t 49598
T 49598,20,5:B5,B1:7:B2
b 49618
B 49618,16,1:T2*2,1,2:T1
c 49634
c 49635
i 49643""".split('\n')

TEST_CTL_BSC = """c 00000
c 00001
c 00033
c 00555
c 07890
c 32768
C 32768,1 Do nothing
B 32769,2,2 1-line B sub-block
B 32771,3,1,2 2-line B sub-block
T 32774,5,5 T sub-block
W 32779,2,2 W sub-block
S 32781,2,2 S sub-block
M 32783,12 Sub-block with instructions of various types and blank lines in the comment
B 32785,1,1
W 32786,4,4
T 32790,2,1:B1
S 32792,3,3
C 32795,1 Instruction with a comment continuation line
i 32796
b 49152
B 49152,1,1
g 49153
W 49153,2,2
t 49155
T 49155,2,2
u 49157
B 49157,1,1
w 49158
W 49158,4,2
b 49162
B 49162,1,1
C 49163,1
t 49164
T 49164,1,1
C 49165,1
w 49166
W 49166,2,2
C 49168,1
s 49169
S 49169,9,9
C 49178,1
b 49179
B 49179,14,2*3,3*2,1
b 49193
B 49193,1,1
s 49194
S 49194,384,128
b 49578
B 49578,20,3:T5:2,T7:3
t 49598
T 49598,20,5:B5,B1:7:B2
b 49618
B 49618,16,1:T2*2,1,2:T1
c 49634
c 49635
C 49635,2 .
C 49637,2 ...and so on
C 49639,2 ....
C 49641,1 ...
C 49642,1 ...until the end
i 49643"""

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
 40004 DEFW 12345,"a",12345
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

TEST_S_DIRECTIVES_SKOOL = r"""; DEFS statements in various bases
s50000 DEFS %0000000111110100
 50500 DEFS 1000
 51500 DEFS $07D0
 53500 DEFS 500,%10101010
 54000 DEFS $0100,170
 54256 DEFS 256,"\""          ; {Tricky characters
 54512 DEFS 88,"\\"           ;
 54600 DEFS 60,","            ;
 54660 DEFS 40,";"            ; }
"""

TEST_OPERAND_BASES_SKOOL = """; Operations in various bases
c60000 LD A,5                    ; Decimal
 60002 ld b,%11110000            ; {Binary, hexadecimal
 60004 LD C,$5a                  ; }
 60006 LD D, %01010101           ; Space
 60008 ld\te,$23                 ; Tab
 60010 LD H,\t7                  ; Another tab
 60012 ld\tl, $3F                ; Tab, space
 60014 LD  IXh,100               ; Two spaces
 60017 ld  ixl,  %10101010       ; Two spaces, two spaces
 60020 LD\tIYh,\t$12             ; Tab, tab
 60023 ld iyl,%00001111
 60026 LD A,(IX+2)
 60029 ld b,(ix-%00001111)
 60032 ld c,(IY+$44)             ; {Hexadecimal, decimal
 60035 LD D,(iy-57)              ; }
 60038 LD (IX+77),E
 60041 ld (ix-$34),h
 60044 ld (iy+%00000000),L
 60047 LD (IY-$7A),h
 60050 LD (IX+$3F),%10101010
 60054 ld (ix-5),$9b
 60058 ld (iy+%00000001),23
 60062 LD (IY-$05),$ff
 60066 LD (HL),%01000100
 60068 ld bc,$4567
 60071 ld de,%1111111100000000
 60074 LD HL,765
 60077 LD SP,$567A
 60080 ld ix,%0000111111110000
 60084 ld iy,12345
 60088 LD A,($8000)
 60091 LD BC,(%0000000011111111)
 60095 ld de,(16384)
 60099 ld hl,($A001)
 60102 LD SP,(%0101010101010101)
 60106 LD IX,(32768)
 60110 ld iy,($dead)
 60114 ld (%0110111011110111),A
 60117 LD (1),bc
 60121 LD ($DAFF),DE
 60125 ld (%1001000100001000),hl
 60128 ld (49152),SP
 60132 LD ($ACE5),ix
 60136 LD (%0011001100110011),IY
 60140 adc a,34
 60142 add a,$8A
 60144 SBC A,%11100011
 60146 ADC A,(IX-$2B)
 60149 add a,(iy+%00000000)
 60152 sbc a,(IY-52)
 60155 AND $04
 60157 CP %00000001
 60159 or 128
 60161 sub $FF
 60163 XOR %10001000
 60165 AND (IX+$04)
 60168 cp (ix-%00000001)
 60171 or (IY+12)
 60174 SUB (iy-$0f)
 60177 XOR (IX+%00001000)
 60180 dec (ix-44)
 60183 inc (IY+$3B)
 60186 RL (iy-%00001000)
 60190 RLC (IX+3)
 60194 rr (ix-$44)
 60198 rrc (IY+%00001001)
 60202 SLA (iy-54)
 60206 SLL (IX+$00)
 60210 sra (ix-%00001110)
 60214 srl (IY+38)
 60218 BIT 0,a                   ; {No operands
 60220 RES 1,B                   ;
 60222 set 2,c                   ; }
 60224 bit 3,(IY-$1A)
 60228 RES 4,(iy-%00011000)
 60232 SET 5,(IY-99)
 60236 call 60200
 60239 djnz $EB27
 60241 jp $8000
 60244 JR 60200
 60246 CALL NZ,$A001
 60249 jp m,60000
 60252 jr nc,$EB27
 60254 IN A,($fe)
 60256 OUT (254),A
"""

TEST_CHARACTER_OPERANDS_SKOOL = """; Instruction operands as characters
c61000 LD A,"@"
 61002 ADD A,"#"
 61004 SUB "B"
 61006 AND 7
 61008 CP "~"
 61010 LD HL,"."
 61013 LD (IX+$02),"="
"""

TEST_OPERANDS_WITH_COMMAS_SKOOL = """; Instruction operands that contain commas
c62000 LD A,","
 62002 LD A,(IY+",")
 62005 LD (IX+","),B
 62008 LD (IX+0),","
 62012 LD (IY+","),$45
 62016 LD (IX+","),","
"""

class CtlWriterTest(SkoolKitTestCase):
    def _get_ctl(self, elements='abtdrmscn', write_hex=0, skool=TEST_SKOOL,
                 preserve_base=0, min_address=0, max_address=65536, keep_lines=0):
        skoolfile = StringIO(textwrap.dedent(skool).strip())
        writer = CtlWriter(skoolfile, elements, write_hex, preserve_base, min_address, max_address, keep_lines)
        writer.write()
        return self.out.getvalue().rstrip()

    def _test_ctl(self, skool, exp_ctl, write_hex=0, preserve_base=0,
                  min_address=0, max_address=65536, keep_lines=0):
        ctl = self._get_ctl(skool=skool, write_hex=write_hex, preserve_base=preserve_base,
                            min_address=min_address, max_address=max_address, keep_lines=keep_lines)
        self.assertEqual(textwrap.dedent(exp_ctl).strip(), ctl)

    def test_invalid_address(self):
        with self.assertRaises(SkoolParsingError) as cm:
            CtlWriter(self.write_text_file('c3000f RET'))
        self.assertEqual(cm.exception.args[0], "Invalid address (3000f):\nc3000f RET")

    def test_default_elements(self):
        self.assertEqual('\n'.join(TEST_CTL), self._get_ctl())

    def test_default_elements_hex(self):
        self.assertEqual(TEST_CTL_HEX, self._get_ctl(write_hex=2))

    def test_default_elements_no_asm_dirs(self):
        ctl = self._get_ctl('btdrmscn')
        test_ctl = '\n'.join([line for line in TEST_CTL if not line.startswith('@')])
        self.assertEqual(test_ctl, ctl)

    def test_wb(self):
        ctl = self._get_ctl('b')
        test_ctl = '\n'.join([line[:7] for line in TEST_CTL if line[0] in DIRECTIVES])
        self.assertEqual(test_ctl, ctl)

    def test_wbd(self):
        ctl = self._get_ctl('bd')
        test_ctl = []
        for line in TEST_CTL:
            if line[0] in DIRECTIVES:
                test_ctl.append(line[:7])
            elif line.startswith('D'):
                test_ctl.append(line)
        self.assertEqual('\n'.join(test_ctl), ctl)

    def test_wbm(self):
        ctl = self._get_ctl('bm')
        test_ctl = []
        for line in TEST_CTL:
            if line[0] in DIRECTIVES:
                test_ctl.append(line[:7])
            elif line[0] in 'NE':
                test_ctl.append(line)
        self.assertEqual('\n'.join(test_ctl), ctl)

    def test_wbr(self):
        ctl = self._get_ctl('br')
        test_ctl = []
        for line in TEST_CTL:
            if line[0] in DIRECTIVES:
                test_ctl.append(line[:7])
            elif line[0] in 'R':
                test_ctl.append(line)
        self.assertEqual('\n'.join(test_ctl), ctl)

    def test_wbs(self):
        ctl = self._get_ctl('bs')
        test_ctl = '\n'.join([line for line in TEST_CTL_ABS if line[0] != '@'])
        self.assertEqual(test_ctl, ctl)

    def test_wabs(self):
        ctl = self._get_ctl('abs')
        self.assertEqual('\n'.join(TEST_CTL_ABS), ctl)

    def test_wbsc(self):
        ctl = self._get_ctl('bsc')
        self.assertEqual(TEST_CTL_BSC, ctl)

    def test_wbt(self):
        ctl = self._get_ctl('bt')
        test_ctl = '\n'.join([line for line in TEST_CTL if line[0] in DIRECTIVES])
        self.assertEqual(test_ctl, ctl)

    def test_hex_lower(self):
        skool = 'c40177 RET'
        exp_ctl = """
            c $9cf1
            i $9cf2
        """
        self._test_ctl(skool, exp_ctl, write_hex=1)

    def test_byte_formats_no_base(self):
        exp_ctl = """
            b 30000 Binary and mixed-base DEFB/DEFM statements
            B 30000,30,b1:2,2:b2:3,b2,3,5,T5,b1:T2:2
            T 30030,30,b1:B2,B2:b2:B3,b2,B3,B5,5,b1:2:B2
            i 30060
        """
        self._test_ctl(TEST_BYTE_FORMATS_SKOOL, exp_ctl, preserve_base=0)

    def test_byte_formats_preserve_base(self):
        exp_ctl = """
            b 30000 Binary and mixed-base DEFB/DEFM statements
            B 30000,30,b1:h1:d1,h2:b2:d3,b2,d3,h5,T5,b1:T2:d1:h1
            T 30030,30,b1:h1:d1,h2:b2:d3,b2,d3,h5,5,b1:2:d1:h1
            i 30060
        """
        self._test_ctl(TEST_BYTE_FORMATS_SKOOL, exp_ctl, preserve_base=1)

    def test_word_formats_no_base(self):
        exp_ctl = """
            w 40000 Binary and mixed-base DEFW statements
            W 40000,68,b4,2:c2:2,8,2:b2:2,4:b2:4*2,4*4,b4
            i 40068
        """
        self._test_ctl(TEST_WORD_FORMATS_SKOOL, exp_ctl, preserve_base=0)

    def test_word_formats_preserve_base(self):
        exp_ctl = """
            w 40000 Binary and mixed-base DEFW statements
            W 40000,68,b4,d2:c2:d2,h8,d2:b2:h2,h4:b2:d4*2,d4*2,h4*2,b4
            i 40068
        """
        self._test_ctl(TEST_WORD_FORMATS_SKOOL, exp_ctl, preserve_base=1)

    def test_s_directives_no_base(self):
        exp_ctl = """
            s 50000 DEFS statements in various bases
            S 50000,4256,b%0000000111110100,1000,$07D0,500:b,$0100:n
            S 54256,444,256:c,88:c,60:c,40:c Tricky characters
            i 54700
        """
        self._test_ctl(TEST_S_DIRECTIVES_SKOOL, exp_ctl, preserve_base=0)

    def test_s_directives_preserve_base(self):
        exp_ctl = """
            s 50000 DEFS statements in various bases
            S 50000,4256,b%0000000111110100,d1000,h$07D0,d500:b,h$0100:d
            S 54256,444,d256:c,d88:c,d60:c,d40:c Tricky characters
            i 54700
        """
        self._test_ctl(TEST_S_DIRECTIVES_SKOOL, exp_ctl, preserve_base=1)

    def test_s_directive_invalid_size(self):
        with self.assertRaisesRegex(SkoolParsingError, "^Invalid integer 'x': DEFS x,1$"):
            CtlWriter(StringIO('s30000 DEFS x,1'))

    def test_s_directive_invalid_value_ignored(self):
        skool = 's30000 DEFS 10,y$'
        exp_ctl = """
            s 30000
            S 30000,10,10:n
            i 30010
        """
        self._test_ctl(skool, exp_ctl)

    def test_operand_bases_no_base(self):
        exp_ctl = """
            c 60000 Operations in various bases
            C 60000,2 Decimal
            C 60002,4,b2,2 Binary, hexadecimal
            C 60006,b2 Space
            C 60008,2 Tab
            C 60010,2 Another tab
            C 60012,2 Tab, space
            C 60014,3 Two spaces
            C 60017,b3 Two spaces, two spaces
            C 60020,3 Tab, tab
            C 60023,9,b3,3,b3
            C 60032,6 Hexadecimal, decimal
            C 60044,170,b3,3,nb4,4,bn4,4,b2,3,b3,6,b4,7,b4,7,b4,8,b3,8,b3,8,b4,4,b2,3,b3,5,b2,4,b2,3,b3,6,b3,6,b4,8,b4,8,b4
            C 60218,6 No operands
            C 60228,b4
            i 60258
        """
        self._test_ctl(TEST_OPERAND_BASES_SKOOL, exp_ctl, preserve_base=0)

    def test_operand_bases_preserve_base(self):
        exp_ctl = """
            c 60000 Operations in various bases
            C 60000,d2 Decimal
            C 60002,4,b2,h2 Binary, hexadecimal
            C 60006,b2 Space
            C 60008,h2 Tab
            C 60010,d2 Another tab
            C 60012,h2 Tab, space
            C 60014,d3 Two spaces
            C 60017,b3 Two spaces, two spaces
            C 60020,h3 Tab, tab
            C 60023,9,b3,d3,b3
            C 60032,6,h3,d3 Hexadecimal, decimal
            C 60038,180,d3,h3,b3,h3,hb4,dh4,bd4,hh4,b2,h3,b3,d3,h3,b4,d4,h3,b4,d4,h3,b4,d4,h4,b3,d4,h4,b3,d4,h4,b4,d2,h2,b2,h3,b3,d3,h2,b2,d2,h2,b2,h3,b3,d3,h3,b3,d3,h3,b4,d4,h4,b4,d4,h4,b4,d4
            C 60218,6 No operands
            C 60224,34,h4,b4,d7,h5,d2,h3,d3,h4,d2
            i 60258
        """
        self._test_ctl(TEST_OPERAND_BASES_SKOOL, exp_ctl, preserve_base=1)

    def test_character_operands_no_base(self):
        exp_ctl = """
            c 61000 Instruction operands as characters
            C 61000,17,c6,2,c5,nc4
            i 61017
        """
        self._test_ctl(TEST_CHARACTER_OPERANDS_SKOOL, exp_ctl, preserve_base=0)

    def test_character_operands_preserve_base(self):
        exp_ctl = """
            c 61000 Instruction operands as characters
            C 61000,17,c6,d2,c5,hc4
            i 61017
        """
        self._test_ctl(TEST_CHARACTER_OPERANDS_SKOOL, exp_ctl, preserve_base=1)

    def test_operands_with_commas_no_base(self):
        exp_ctl = """
            c 62000 Instruction operands that contain commas
            C 62000,20,c8,nc4,cn4,cc4
            i 62020
        """
        self._test_ctl(TEST_OPERANDS_WITH_COMMAS_SKOOL, exp_ctl, preserve_base=0)

    def test_operands_with_commas_preserve_base(self):
        exp_ctl = """
            c 62000 Instruction operands that contain commas
            C 62000,20,c8,dc4,ch4,cc4
            i 62020
        """
        self._test_ctl(TEST_OPERANDS_WITH_COMMAS_SKOOL, exp_ctl, preserve_base=1)

    def test_semicolons_in_instructions(self):
        skool = """
            c60000 CP ";"             ; First comment
             60002 LD A,";"           ; Comment 2
             60004 LD B,(IX+";")      ; Comment 3
             60007 LD (IX+";"),C      ; Comment 4
             60010 LD (IX+";"),";"    ; Comment 5
             60014 LD (IX+"\\""),";"  ; Comment 6
             60018 LD (IX+"\\\\"),";" ; Comment 7
             60022 DEFB 5,"hi;",6     ; Comment 8
             60027 DEFM ";0;",0       ; Last comment
        """
        exp_ctl = """
            c 60000
            C 60000,c2 First comment
            C 60002,c2 Comment 2
            C 60004,c3 Comment 3
            C 60007,c3 Comment 4
            C 60010,cc4 Comment 5
            C 60014,cc4 Comment 6
            C 60018,cc4 Comment 7
            B 60022,5,1:T3:1 Comment 8
            T 60027,4,3:B1 Last comment
            i 60031
        """
        self._test_ctl(skool, exp_ctl)

    def test_arithmetic_expressions(self):
        skool = """
            b40000 DEFB 32768/256,32768%256,1+2,3*4,5-6
             40005 DEFM 32768/256,32768%256,1+2,3*4,5-6
             40010 DEFS 256*2,128/2
             40522 DEFS "A"*4,"z"+38
        """
        exp_ctl = """
            b 40000
            B 40000,5,5
            T 40005,5,B5
            S 40010,772,512:n,c260:c
            i 40782
        """
        self._test_ctl(skool, exp_ctl)

    def test_invalid_arithmetic_expressions(self):
        skool = """
            b30000 DEFB 1,35/0,"!"
             30003 DEFB "H","ey"+128
             30005 DEFM 1,35/0,"!"
             30008 DEFM "H","ey"+128
        """
        exp_ctl = """
            b 30000
            B 30000,5,2:T1,T1:1
            T 30005,5,B2:1,1:B1
            i 30010
        """
        self._test_ctl(skool, exp_ctl)

    def test_inverted_characters(self):
        skool = """
            b40000 DEFB "a"+128
             40001 DEFB "H","i"+$80
             40003 DEFM "a"+128
             40004 DEFM "H","i"+$80
             40006 DEFW "a"+128
             40008 DEFW "H","i"+$80
             40012 LD A,"a"+128
             40014 DEFS 2,"a"+$80
        """
        exp_ctl = """
            b 40000
            B 40000,3,T1,T1:T1
            T 40003,3,1,1:1
            W 40006,6,c2,c4
            C 40012,c2
            S 40014,2,2:c
            i 40016
        """
        self._test_ctl(skool, exp_ctl)

    def test_negative_operands(self):
        skool = """
            b50000 DEFB -1
             50001 DEFB 0,-$01,-2
             50004 DEFM -3
             50005 DEFM -2,-$01,"!"
             50008 DEFW -1
             50010 DEFW 0,-$01
             50014 LD A,-1
             50016 LD BC,-$0001
             50019 DEFS 2,-1
        """
        exp_ctl = """
            b 50000
            B 50000,4,m1,1:m2
            T 50004,4,m1,m2:1
            W 50008,6,m2,2:m2
            C 50014,m5
            S 50019,2,2:m
            i 50021
        """
        self._test_ctl(skool, exp_ctl)

    def test_ignoreua_directives(self):
        skool = """
            @ignoreua
            ; Routine at 30000
            c30000 RET

            ; Routine
            ;
            @ignoreua
            ; Description of the routine at 30001
            ;
            @ignoreua
            ; HL 30001
            @ignoreua
            c30001 RET    ; Instruction-level comment at 30001

            ; Routine
            c30002 LD A,B
            @ignoreua
            ; Mid-block comment above 30003.
            @ignoreua
             30003 RET    ; Instruction-level comment at 30003

            ; Routine
            @ignoreua
            c30004 LD A,C ; Instruction-level comment at 30004
            @ignoreua
            ; Mid-block comment above 30005.
             30005 RET
            @ignoreua
            ; End comment for the routine at 30004.

            ; The @ignoreua directive above should not spill over
            c30006 RET
        """
        exp_ctl = """
            @ 30000 ignoreua:t
            c 30000 Routine at 30000
            c 30001 Routine
            @ 30001 ignoreua:d
            D 30001 Description of the routine at 30001
            @ 30001 ignoreua:r
            R 30001 HL 30001
            @ 30001 ignoreua:i
            C 30001,1 Instruction-level comment at 30001
            c 30002 Routine
            @ 30003 ignoreua:m
            N 30003 Mid-block comment above 30003.
            @ 30003 ignoreua:i
            C 30003,1 Instruction-level comment at 30003
            c 30004 Routine
            @ 30004 ignoreua:i
            C 30004,1 Instruction-level comment at 30004
            @ 30005 ignoreua:m
            N 30005 Mid-block comment above 30005.
            @ 30004 ignoreua:e
            E 30004 End comment for the routine at 30004.
            c 30006 The @ignoreua directive above should not spill over
            i 30007
        """
        self._test_ctl(skool, exp_ctl)

    def test_ignoreua_directive_on_start_comment(self):
        skool = """
            ; Routine
            ;
            ; .
            ;
            ; .
            ;
            @ignoreua
            ; Start comment above 30000.
            c30000 RET
        """
        exp_ctl = """
            c 30000 Routine
            @ 30000 ignoreua:m
            N 30000 Start comment above 30000.
            i 30001
        """
        self._test_ctl(skool, exp_ctl)

    def test_ignoreua_directives_hex(self):
        skool = """
            @ignoreua
            ; Routine at 40000
            ;
            @ignoreua
            ; Description of the routine at 40000
            ;
            @ignoreua
            ; HL 40000
            @ignoreua
            c40000 LD A,B ; Instruction-level comment at 40000
            @ignoreua
            ; Mid-block comment above 40001.
             40001 RET
            @ignoreua
            ; End comment for the routine at 40000.
        """
        exp_ctl = """
            @ $9C40 ignoreua:t
            c $9C40 Routine at 40000
            @ $9C40 ignoreua:d
            D $9C40 Description of the routine at 40000
            @ $9C40 ignoreua:r
            R $9C40 HL 40000
            @ $9C40 ignoreua:i
            C $9C40,1 Instruction-level comment at 40000
            @ $9C41 ignoreua:m
            N $9C41 Mid-block comment above 40001.
            @ $9C40 ignoreua:e
            E $9C40 End comment for the routine at 40000.
            i $9C42
        """
        self._test_ctl(skool, exp_ctl, write_hex=2)

    def test_assemble_directives(self):
        skool = """
            @assemble=2,0
            c30000 LD A,1
            @assemble=1
             30002 LD B,2
            @assemble=0
             30004 LD C,3
        """
        exp_ctl = """
            @ 30000 assemble=2,0
            c 30000
            @ 30002 assemble=1
            @ 30004 assemble=0
            i 30006
        """
        self._test_ctl(skool, exp_ctl)

    def test_defb_directives(self):
        skool = """
            @defb=23296:128
            ; Routine
            c32768 LD A,B
            @defb=23297:129
             32769 RET
        """
        exp_ctl = """
            @ 32768 defb=23296:128
            c 32768 Routine
            @ 32769 defb=23297:129
            i 32770
        """
        self._test_ctl(skool, exp_ctl)

    def test_defs_directives(self):
        skool = """
            @defs=23296:10,128
            ; Routine
            c32768 LD A,B
            @defs=23306:10,129
             32769 RET
        """
        exp_ctl = """
            @ 32768 defs=23296:10,128
            c 32768 Routine
            @ 32769 defs=23306:10,129
            i 32770
        """
        self._test_ctl(skool, exp_ctl)

    def test_defw_directives(self):
        skool = """
            @defw=23296:256
            ; Routine
            c32768 LD A,B
            @defw=23298:32768
             32769 RET
        """
        exp_ctl = """
            @ 32768 defw=23296:256
            c 32768 Routine
            @ 32769 defw=23298:32768
            i 32770
        """
        self._test_ctl(skool, exp_ctl)

    def test_end_directives(self):
        skool = """
            ; Routine
            c32768 LD A,B
            @end
             32769 RET
            @end

            ; Another routine
            c32770 RET
            @end' # Not preserved (appears after last instruction)
        """
        exp_ctl = """
            c 32768 Routine
            @ 32769 end
            @ 32770 end
            c 32770 Another routine
            i 32771
        """
        self._test_ctl(skool, exp_ctl)

    def test_equ_directives(self):
        skool = """
            @equ=ATTRS=22528
            ; Routine
            c32768 LD A,B
            @equ=SEED=23670
             32769 RET
        """
        exp_ctl = """
            @ 32768 equ=ATTRS=22528
            c 32768 Routine
            @ 32769 equ=SEED=23670
            i 32770
        """
        self._test_ctl(skool, exp_ctl)

    def test_if_directives(self):
        skool = """
            @if({base}==16)(replace=/#base/16)
            ; Routine
            c32768 LD A,B
            @if({case}==1)(replace=/#case/lower)
             32769 RET
        """
        exp_ctl = """
            @ 32768 if({base}==16)(replace=/#base/16)
            c 32768 Routine
            @ 32769 if({case}==1)(replace=/#case/lower)
            i 32770
        """
        self._test_ctl(skool, exp_ctl)

    def test_org_directives(self):
        skool = """
            @org=32768
            ; Routine
            c32768 LD A,B
            @org
             32769 RET
            @org
            ; Another routine
            c32770 LD A,C
            @org=32771
             32771 RET
        """
        exp_ctl = """
            @ 32768 org=32768
            c 32768 Routine
            @ 32769 org
            @ 32770 org
            c 32770 Another routine
            @ 32771 org=32771
            i 32772
        """
        self._test_ctl(skool, exp_ctl)

    def test_remote_directives(self):
        skool = """
            @remote=main:55213
            ; Routine
            c32768 LD A,B
            @remote=start:41123,41127
             32769 RET
        """
        exp_ctl = """
            @ 32768 remote=main:55213
            c 32768 Routine
            @ 32769 remote=start:41123,41127
            i 32770
        """
        self._test_ctl(skool, exp_ctl)

    def test_replace_directives(self):
        skool = """
            @replace=/foo/bar
            ; Routine
            c32768 LD A,B
            @replace=/bar/baz
             32769 RET
        """
        exp_ctl = """
            @ 32768 replace=/foo/bar
            c 32768 Routine
            @ 32769 replace=/bar/baz
            i 32770
        """
        self._test_ctl(skool, exp_ctl)

    def test_set_directives(self):
        skool = """
            @set-crlf=1
            ; Routine
            c32768 LD A,B
            @set-tab=1
             32769 RET
        """
        exp_ctl = """
            @ 32768 set-crlf=1
            c 32768 Routine
            @ 32769 set-tab=1
            i 32770
        """
        self._test_ctl(skool, exp_ctl)

    def test_start_directives(self):
        skool = """
            @start
            ; Routine
            c32768 LD A,B
            @start
             32769 RET
        """
        exp_ctl = """
            @ 32768 start
            c 32768 Routine
            @ 32769 start
            i 32770
        """
        self._test_ctl(skool, exp_ctl)

    def test_writer_directives(self):
        skool = """
            @writer=foo.bar.Baz
            ; Routine
            c32768 LD A,B
            @writer=bar.baz.Qux
             32769 RET
        """
        exp_ctl = """
            @ 32768 writer=foo.bar.Baz
            c 32768 Routine
            @ 32769 writer=bar.baz.Qux
            i 32770
        """
        self._test_ctl(skool, exp_ctl)

    def test_order_of_entry_asm_directives_is_preserved(self):
        skool = """
            @start
            @equ=ATTRS=22528
            @replace=/foo/bar
            @replace=/baz/qux
            ; Routine
            c49152 RET           ;
        """
        exp_ctl = """
            @ 49152 start
            @ 49152 equ=ATTRS=22528
            @ 49152 replace=/foo/bar
            @ 49152 replace=/baz/qux
            c 49152 Routine
            i 49153
        """
        self._test_ctl(skool, exp_ctl)

    def test_isub_block_directives(self):
        skool = """
            b40000 DEFB 0
            @isub-begin
             40001 DEFW 0
            @isub+else
             40001 DEFS 2
            @isub+end
             40003 DEFM "a"
        """
        exp_ctl = """
            b 40000
            B 40000,1,1
            W 40001,2,2
            T 40003,1,1
            i 40004
        """
        self._test_ctl(skool, exp_ctl)

    def test_ssub_block_directives(self):
        skool = """
            b40000 DEFB 0
            @ssub+begin
             40001 DEFW 0
            @ssub-else
             40001 DEFS 2
            @ssub-end
             40003 DEFM "a"
        """
        exp_ctl = """
            b 40000
            B 40000,1,1
            S 40001,2,2
            T 40003,1,1
            i 40004
        """
        self._test_ctl(skool, exp_ctl)

    def test_rsub_block_directives(self):
        skool = """
            b40000 DEFB 0
            @rsub-begin
             40001 DEFW 0
            @rsub+else
             40001 DEFS 2
            @rsub+end
             40003 DEFM "a"
        """
        exp_ctl = """
            b 40000
            B 40000,1,1
            W 40001,2,2
            T 40003,1,1
            i 40004
        """
        self._test_ctl(skool, exp_ctl)

    def test_ofix_block_directives(self):
        skool = """
            b40000 DEFB 0
            @ofix+begin
             40001 DEFW 0
            @ofix-else
             40001 DEFS 2
            @ofix-end
             40003 DEFM "a"
        """
        exp_ctl = """
            b 40000
            B 40000,1,1
            S 40001,2,2
            T 40003,1,1
            i 40004
        """
        self._test_ctl(skool, exp_ctl)

    def test_rfix_block_directives(self):
        skool = """
            b40000 DEFB 0
            @rfix-begin
             40001 DEFW 0
            @rfix+else
             40001 DEFS 2
            @rfix+end
             40003 DEFM "a"
        """
        exp_ctl = """
            b 40000
            B 40000,1,1
            W 40001,2,2
            T 40003,1,1
            i 40004
        """
        self._test_ctl(skool, exp_ctl)

    def test_registers(self):
        skool = """
            ; Routine
            ;
            ; .
            ;
            ; BC This register description is long enough that it needs to be
            ;   .split over two lines
            ; DE Short register description
            ; HL Another register description that is long enough to need
            ; .  splitting over two lines
            ; IX
            c40000 RET
        """
        exp_ctl = """
            c 40000 Routine
            R 40000 BC This register description is long enough that it needs to be split over two lines
            R 40000 DE Short register description
            R 40000 HL Another register description that is long enough to need splitting over two lines
            R 40000 IX
            i 40001
        """
        self._test_ctl(skool, exp_ctl)

    def test_register_prefixes(self):
        skool = """
            ; Test registers with prefixes
            ;
            ; .
            ;
            ; Input:A Some value
            ;       B Some other value
            ; Output:HL The result
            c24576 RET
        """
        exp_ctl = """
            c 24576 Test registers with prefixes
            R 24576 Input:A Some value
            R 24576 B Some other value
            R 24576 Output:HL The result
            i 24577
        """
        self._test_ctl(skool, exp_ctl)

    def test_start_comment(self):
        start_comment = 'This is a start comment.'
        skool = """
            ; Routine
            ;
            ; Description
            ;
            ; .
            ;
            ; {}
            c50000 RET
        """.format(start_comment)
        exp_ctl = """
            c 50000 Routine
            D 50000 Description
            N 50000 {}
            i 50001
        """.format(start_comment)
        self._test_ctl(skool, exp_ctl)

    def test_multi_paragraph_start_comment(self):
        start_comment = ('Start comment paragraph 1.', 'Paragraph 2.')
        skool = """
            ; Routine
            ;
            ; .
            ;
            ; .
            ;
            ; {}
            ; .
            ; {}
            c60000 RET
        """.format(*start_comment)
        exp_ctl = """
            c 60000 Routine
            N 60000 {}
            N 60000 {}
            i 60001
        """.format(*start_comment)
        self._test_ctl(skool, exp_ctl)

    def test_unpadded_comments(self):
        skool = """
            ;Routine
            ;
            ;Paragraph 1.
            ;.
            ;Paragraph 2.
            ;
            ;A Value
            ;
            ;Start comment.
            c32768 XOR A
            ;Mid-block comment.
             32769 RET   ;Done.
        """
        exp_ctl = """
            c 32768 Routine
            D 32768 Paragraph 1.
            D 32768 Paragraph 2.
            R 32768 A Value
            N 32768 Start comment.
            N 32769 Mid-block comment.
            C 32769,1 Done.
            i 32770
        """
        self._test_ctl(skool, exp_ctl)

    def test_indented_comment_lines_are_ignored(self):
        skool = """
            ; Routine
            ;
             ; Ignore me.
            ; Paragraph 1.
             ; Ignore me too
            ; .
             ; Ignore me three.
            ; Paragraph 2.
            ;
            ; HL Address
             ; Ignore me four.
            ;
             ; Ignore me five.
            ; Start comment paragraph 1.
            ; .
             ; Ignore me six.
            ; Start comment paragraph 2.
            c50000 XOR A
            ; Mid-block comment.
             ; Ignore me seven.
            ; Mid-block comment continued.
             50001 RET
            ; End comment.
             ; Ignore me eight.
            ; End comment continued.
        """
        exp_ctl = """
            c 50000 Routine
            D 50000 Paragraph 1.
            D 50000 Paragraph 2.
            R 50000 HL Address
            N 50000 Start comment paragraph 1.
            N 50000 Start comment paragraph 2.
            N 50001 Mid-block comment. Mid-block comment continued.
            E 50000 End comment. End comment continued.
            i 50002
        """
        self._test_ctl(skool, exp_ctl)

    def test_M_directives(self):
        skool = """
            c30000 LD A,B   ; {Regular M directive
             30001 DEFB 0   ; (should have an explicit length)}
             30002 SUB D    ; {M directive just before a mid-block comment
             30003 DEFB 0   ; (should have an explicit length)}
            ; Mid-block comment.
             30004 XOR H    ; {M directive extending to the end of the block
             30005 DEFB 0   ; (no explicit length)}

            b30006 DEFW 0   ; {M directive covering a multi-instruction
             30008 DEFB 0   ; sub-block (3 DEFBs)
             30009 DEFB 0
             30010 DEFB 0   ; }
             30011 DEFW 0   ; {A word and a byte to end
             30013 DEFB 0   ; }

            b30014 DEFW 0   ; {Another M directive covering a multi-instruction
             30016 DEFB 0   ; sub-block (2 DEFBs)
             30017 DEFB 0   ; }
             30018 DEFW 0
             30020 DEFB 0
        """
        exp_ctl = """
            c 30000
            M 30000,2 Regular M directive (should have an explicit length)
            B 30001,1,1
            M 30002,2 M directive just before a mid-block comment (should have an explicit length)
            B 30003,1,1
            N 30004 Mid-block comment.
            M 30004 M directive extending to the end of the block (no explicit length)
            B 30005,1,1
            b 30006
            M 30006,5 M directive covering a multi-instruction sub-block (3 DEFBs)
            W 30006,2,2
            B 30008,3,1
            M 30011 A word and a byte to end
            W 30011,2,2
            B 30013,1,1
            b 30014
            M 30014,4 Another M directive covering a multi-instruction sub-block (2 DEFBs)
            W 30014,2,2
            B 30016,2,1
            W 30018,2,2
            B 30020,1,1
            i 30021
        """
        self._test_ctl(skool, exp_ctl)

    def test_instructions_in_wrong_order(self):
        skool = """
            c30002 LD B,%00000010
             30004 LD C,3
             30000 LD A,"1
        """
        exp_ctl = """
            c 30000
            C 30000,4,c2,b2
            i 30006
        """
        self._test_ctl(skool, exp_ctl)

    def test_invalid_instruction_at_end_of_entry_is_excluded_from_sublengths(self):
        skool = """
            c40000 LD A,%00001111
             40002 SBC IX,DE
        """
        exp_ctl = """
            c 40000
            C 40000,b2
            i 40003
        """
        self._test_ctl(skool, exp_ctl)

    def test_commentless_C_directive_in_c_block_is_trimmed(self):
        skool = """
            c50000 LD A,1    ; {Do stuff
             50002 LD B,"!"  ;
             50004 LD C,3    ; }
             50006 LD D,4    ;
             50008 LD E,"$"  ;
             50010 LD H,6    ;
        """
        exp_ctl = """
            c 50000
            C 50000,6,2,c2,2 Do stuff
            C 50008,c2
            i 50012
        """
        self._test_ctl(skool, exp_ctl)

    def test_min_address(self):
        skool = """
            b40000 DEFB 0

            ; Data at 40001
            b40001 DEFB 1

            b40002 DEFB 2
        """
        exp_ctl = """
            b 40001 Data at 40001
            B 40001,1,1
            b 40002
            B 40002,1,1
            i 40003
        """
        self._test_ctl(skool, exp_ctl, min_address=40001)

    def test_min_address_between_entries(self):
        skool = """
            c40000 LD A,B
            ; Mid-block comment.
             40001 INC A
             40002 RET

            ; Routine at 40003
            c40003 RET

            c40004 RET
        """
        exp_ctl = """
            c 40003 Routine at 40003
            c 40004
            i 40005
        """
        self._test_ctl(skool, exp_ctl, min_address=40001)

    def test_min_address_gives_no_content(self):
        skool = """
            b40000 DEFB 0

            b40001 DEFB 1
        """
        exp_ctl = ''
        self._test_ctl(skool, exp_ctl, min_address=40002)

    def test_max_address(self):
        skool = """
            b40000 DEFB 0

            b40001 DEFB 1
            ; End comment.

            b40002 DEFB 2
        """
        exp_ctl = """
            b 40000
            B 40000,1,1
            b 40001
            B 40001,1,1
            E 40001 End comment.
            i 40002
        """
        self._test_ctl(skool, exp_ctl, max_address=40002)

    def test_max_address_at_mid_block_comment(self):
        skool = """
            c50000 RET

            c50001 LD A,B
             50002 INC A
            ; And here we return.
             50003 RET
        """
        exp_ctl = """
            c 50000
            c 50001
            i 50003
        """
        self._test_ctl(skool, exp_ctl, max_address=50003)

    def test_max_address_gives_no_content(self):
        skool = """
            b40000 DEFB 0

            b40001 DEFB 1
        """
        exp_ctl = ''
        self._test_ctl(skool, exp_ctl, max_address=40000)

    def test_min_and_max_address(self):
        skool = """
            b40000 DEFB 0

            b40001 DEFB 1

            b40002 DEFB 2

            b40003 DEFB 3
        """
        exp_ctl = """
            b 40001
            B 40001,1,1
            b 40002
            B 40002,1,1
            i 40003
        """
        self._test_ctl(skool, exp_ctl, min_address=40001, max_address=40003)

    def test_min_and_max_address_give_no_content(self):
        skool = """
            b40000 DEFB 0

            b40001 DEFB 1

            b40002 DEFB 2
        """
        exp_ctl = ''
        self._test_ctl(skool, exp_ctl, min_address=40001, max_address=40001)

    def test_braces_in_comments(self):
        skool = """
            ; Test comments that start or end with a brace
            b30000 DEFB 0 ; {{Unmatched closing
             30001 DEFB 0 ; brace} }
             30002 DEFB 0 ; { {Matched
             30003 DEFB 0 ; braces} }
             30004 DEFB 0 ; { {Unmatched opening
             30005 DEFB 0 ; brace }}
             30006 DEFB 0 ; {{{Unmatched closing braces}} }
             30007 DEFB 0 ; { {{Matched braces (2)}} }
             30008 DEFB 0 ; { {{Unmatched opening braces}}}
             30009 DEFB 0 ; {Opening brace {
             30010 DEFB 0 ; at the end of a line}}
             30011 DEFB 0 ; {{Closing brace
             30012 DEFB 0 ; } at the beginning of a line}
        """
        exp_ctl = """
            b 30000 Test comments that start or end with a brace
            B 30000,2,1 Unmatched closing brace}
            B 30002,2,1 {Matched braces}
            B 30004,2,1 {Unmatched opening brace
            B 30006,1,1 Unmatched closing braces}}
            B 30007,1,1 {{Matched braces (2)}}
            B 30008,1,1 {{Unmatched opening braces
            B 30009,2,1 Opening brace { at the end of a line
            B 30011,2,1 Closing brace } at the beginning of a line
            i 30013
        """
        self._test_ctl(skool, exp_ctl)

    def test_unmatched_opening_braces_in_instruction_comments(self):
        skool = """
            b50000 DEFB 0 ; {The unmatched {opening brace} in this comment should be
             50001 DEFB 0 ; implicitly closed by the end of this entry

            b50002 DEFB 0 ; {The unmatched {opening brace} in this comment should be
             50003 DEFB 0 ; implicitly closed by the following mid-block comment
            ; Here is the mid-block comment.
             50004 DEFB 0 ; The closing brace in this comment is unmatched}
        """
        exp_ctl = """
            b 50000
            B 50000,2,1 The unmatched {opening brace} in this comment should be implicitly closed by the end of this entry
            b 50002
            B 50002,2,1 The unmatched {opening brace} in this comment should be implicitly closed by the following mid-block comment
            N 50004 Here is the mid-block comment.
            B 50004,1,1 The closing brace in this comment is unmatched}
            i 50005
        """
        self._test_ctl(skool, exp_ctl)

    def test_asm_block_directive_spanning_two_entries(self):
        skool = """
            ; Data
            b32768 DEFB 1
            @bfix-begin
             32769 DEFB 2

            ; Unused
            u32770 DEFB 0
            @bfix+else
             32769 DEFB 4
             32770 DEFB 8
            @bfix+end
        """
        exp_ctl = """
            b 32768 Data
            B 32768,2,1
            u 32770 Unused
            B 32770,1,1
            i 32771
        """
        self._test_ctl(skool, exp_ctl)

    def test_skool_file_ending_with_blank_line(self):
        skool = "c32768 RET\n\n"
        exp_ctl = "c 32768\ni 32769\n"
        CtlWriter(StringIO(skool)).write()
        self.assertEqual(self.out.getvalue(), exp_ctl)

    def test_header(self):
        skool = """
            ; This is a header.
            @rem=It should be preserved verbatim.

            ; Routine
            c32768 RET
        """
        exp_ctl = """
            > 32768 ; This is a header.
            > 32768 @rem=It should be preserved verbatim.
            c 32768 Routine
            i 32769
        """
        self._test_ctl(skool, exp_ctl)

    def test_two_headers(self):
        skool = """
            ; This is a header.

            ; This is another header.

            ; Routine
            c32768 RET
        """
        exp_ctl = """
            > 32768 ; This is a header.
            > 32768
            > 32768 ; This is another header.
            c 32768 Routine
            i 32769
        """
        self._test_ctl(skool, exp_ctl)

    def test_header_before_second_entry(self):
        skool = """
            ; Routine
            c32768 RET

            ; This is between two entries.

            ; Another routine
            c32769 RET
        """
        exp_ctl = """
            c 32768 Routine
            > 32769 ; This is between two entries.
            c 32769 Another routine
            i 32770
        """
        self._test_ctl(skool, exp_ctl)

    def test_header_preserves_asm_block_directives(self):
        skool = """
            ; Disassembly.
            @isub+begin
            ; isub mode.
            @isub+end
            @ssub+begin
            ; ssub mode.
            @ssub+end
            @rsub+begin
            ; rsub mode.
            @rsub+end
            @ofix+begin
            ; ofix mode.
            @ofix+end
            @bfix+begin
            ; bfix mode.
            @bfix+end
            @rfix+begin
            ; rfix mode.
            @rfix+end

            c24576 RET
        """
        exp_ctl = """
            > 24576 ; Disassembly.
            > 24576 @isub+begin
            > 24576 ; isub mode.
            > 24576 @isub+end
            > 24576 @ssub+begin
            > 24576 ; ssub mode.
            > 24576 @ssub+end
            > 24576 @rsub+begin
            > 24576 ; rsub mode.
            > 24576 @rsub+end
            > 24576 @ofix+begin
            > 24576 ; ofix mode.
            > 24576 @ofix+end
            > 24576 @bfix+begin
            > 24576 ; bfix mode.
            > 24576 @bfix+end
            > 24576 @rfix+begin
            > 24576 ; rfix mode.
            > 24576 @rfix+end
            c 24576
            i 24577
        """
        self._test_ctl(skool, exp_ctl)

    def test_header_containing_unclosed_block_directive(self):
        skool = """
            ; This block contains an unclosed block directive.
            @bfix+begin
            ; Bug fixes.

            ; This block should appear in the control file.

            ; This block closes the block directive.
            @bfix+end

            ; Routine
            c32768 RET
        """
        exp_ctl = """
            > 32768 ; This block contains an unclosed block directive.
            > 32768 @bfix+begin
            > 32768 ; Bug fixes.
            > 32768
            > 32768 ; This block should appear in the control file.
            > 32768
            > 32768 ; This block closes the block directive.
            > 32768 @bfix+end
            c 32768 Routine
            i 32769
        """
        self._test_ctl(skool, exp_ctl)

    def test_header_included_with_min_address(self):
        skool = """
            ; This header should be included.

            ; Routine
            c65535 RET
        """
        exp_ctl = """
            > 65535 ; This header should be included.
            c 65535 Routine
        """
        self._test_ctl(skool, exp_ctl, min_address=65535)

    def test_header_excluded_by_min_address(self):
        skool = """
            ; This header should be excluded.

            ; First routine
            c65534 RET

            ; Second routine
            c65535 RET
        """
        exp_ctl = "c 65535 Second routine"
        self._test_ctl(skool, exp_ctl, min_address=65535)

    def test_header_excluded_by_max_address(self):
        skool = """
            ; First routine
            c65534 RET

            ; This header should be excluded.

            ; Second routine
            c65535 RET
        """
        exp_ctl = """
            c 65534 First routine
            i 65535
        """
        self._test_ctl(skool, exp_ctl, max_address=65535)

    def test_footer(self):
        skool = """
            ; Routine
            c32768 RET

            ; This is a footer.
            @rem=It should be preserved verbatim.
        """
        exp_ctl = """
            c 32768 Routine
            > 32768,1 ; This is a footer.
            > 32768,1 @rem=It should be preserved verbatim.
            i 32769
        """
        self._test_ctl(skool, exp_ctl)

    def test_two_footers(self):
        skool = """
            ; Routine
            c32768 RET

            ; This is a footer.

            ; This is another footer.
        """
        exp_ctl = """
            c 32768 Routine
            > 32768,1 ; This is a footer.
            > 32768,1
            > 32768,1 ; This is another footer.
            i 32769
        """
        self._test_ctl(skool, exp_ctl)

    def test_footer_preserves_asm_block_directives(self):
        skool = """
            c24576 RET

            ; That was a disassembly.
            @isub+begin
            ; isub mode.
            @isub+end
            @ssub+begin
            ; ssub mode.
            @ssub+end
            @rsub+begin
            ; rsub mode.
            @rsub+end
            @ofix+begin
            ; ofix mode.
            @ofix+end
            @bfix+begin
            ; bfix mode.
            @bfix+end
            @rfix+begin
            ; rfix mode.
            @rfix+end
        """
        exp_ctl = """
            c 24576
            > 24576,1 ; That was a disassembly.
            > 24576,1 @isub+begin
            > 24576,1 ; isub mode.
            > 24576,1 @isub+end
            > 24576,1 @ssub+begin
            > 24576,1 ; ssub mode.
            > 24576,1 @ssub+end
            > 24576,1 @rsub+begin
            > 24576,1 ; rsub mode.
            > 24576,1 @rsub+end
            > 24576,1 @ofix+begin
            > 24576,1 ; ofix mode.
            > 24576,1 @ofix+end
            > 24576,1 @bfix+begin
            > 24576,1 ; bfix mode.
            > 24576,1 @bfix+end
            > 24576,1 @rfix+begin
            > 24576,1 ; rfix mode.
            > 24576,1 @rfix+end
            i 24577
        """
        self._test_ctl(skool, exp_ctl)

    def test_footer_included_with_max_address(self):
        skool = """
            ; Routine
            c60000 RET

            ; This footer should be included.
        """
        exp_ctl = """
            c 60000 Routine
            > 60000,1 ; This footer should be included.
            i 60001
        """
        self._test_ctl(skool, exp_ctl, max_address=60001)

    def test_footer_excluded_by_max_address(self):
        skool = """
            ; First routine
            c65534 RET

            ; Second routine
            c65535 RET

            ; This footer should be excluded.
        """
        exp_ctl = """
            c 65534 First routine
            i 65535
        """
        self._test_ctl(skool, exp_ctl, max_address=65535)

    def test_keep_lines_in_entry_titles(self):
        skool = """
            ; Entry title with
            ;       an indented second line
            c65526 RET

            ; Entry title on one line
            b65527 DEFB 0

            ; Entry title split
            ; over two lines
            c65528 RET

            ; Entry title
            ; split over
            ; three lines
            g65529 DEFB 0

            ; Another entry title on one line
            i65530

            ; Another entry title
            ; split over two lines
            s65531 DEFS 1

            ; Another entry title
            ; split over
            ; three lines
            t65532 DEFM "a"

            ; Yet another entry title on one line
            u65533 DEFB 0

            ; Yet another entry title
            ; split over two lines
            w65534 DEFW 0
        """
        exp_ctl = """
            c 65526
            . Entry title with
            .       an indented second line
            b 65527
            . Entry title on one line
            B 65527,1,1
            c 65528
            . Entry title split
            . over two lines
            g 65529
            . Entry title
            . split over
            . three lines
            B 65529,1,1
            i 65530
            . Another entry title on one line
            s 65531
            . Another entry title
            . split over two lines
            S 65531,1,1
            t 65532
            . Another entry title
            . split over
            . three lines
            T 65532,1,1
            u 65533
            . Yet another entry title on one line
            B 65533,1,1
            w 65534
            . Yet another entry title
            . split over two lines
            W 65534,2,2
        """
        self._test_ctl(skool, exp_ctl, keep_lines=1)

    def test_keep_lines_in_entry_descriptions(self):
        skool = """
            ; Routine
            ;
            ; Description with an
            ;             indented second line.
            c65531 RET

            ; Routine with no description
            ;
            ; .
            ;
            ; BC Counter
            c65532 RET

            ; Routine
            ;
            ; Description on one line.
            c65533 RET

            ; Routine
            ;
            ; Description on
            ; two lines.
            c65534 RET

            ; Routine
            ;
            ; Paragraph 1 is
            ; two lines.
            ; .
            ; Paragraph 2
            ; is three
            ; lines.
            c65535 RET
        """
        exp_ctl = """
            c 65531
            . Routine
            D 65531
            . Description with an
            .             indented second line.
            c 65532
            . Routine with no description
            R 65532
            . BC Counter
            c 65533
            . Routine
            D 65533
            . Description on one line.
            c 65534
            . Routine
            D 65534
            . Description on
            . two lines.
            c 65535
            . Routine
            D 65535
            . Paragraph 1 is
            . two lines.
            . .
            . Paragraph 2
            . is three
            . lines.
        """
        self._test_ctl(skool, exp_ctl, keep_lines=1)

    def test_keep_lines_in_register_descriptions(self):
        skool = """
            ; Routine
            ;
            ; .
            ;
            ; BC Counter
            ; DE Register
            ; .  pair
            ; HL Another
            ; . register
            ; . pair
            ;   IX Index
            ; O:A The
            ; .   answer
            c65534 RET

            ; Routine with no registers
            ;
            ; .
            ;
            ; .
            ;
            ; Start comment.
            c65535 RET
        """
        exp_ctl = """
            c 65534
            . Routine
            R 65534
            . BC Counter
            . DE Register
            . .  pair
            . HL Another
            . . register
            . . pair
            .   IX Index
            . O:A The
            . .   answer
            c 65535
            . Routine with no registers
            N 65535
            . Start comment.
        """
        self._test_ctl(skool, exp_ctl, keep_lines=1)

    def test_keep_lines_in_block_start_and_mid_block_comments(self):
        skool = """
            ; Routine with no start comment
            c65532 XOR A
            ; Paragraph spanning
            ; two lines.
             65533 RET

            ; Routine
            ;
            ; .
            ;
            ; .
            ;
            ; One line paragraph.
            ; .
            ; Two-line
            ; paragraph.
            c65534 XOR A
            ; Paragraph one.
            ; .
            ; Paragraph two
            ;    with an indented second line.
             65535 RET
        """
        exp_ctl = """
            c 65532
            . Routine with no start comment
            N 65533
            . Paragraph spanning
            . two lines.
            c 65534
            . Routine
            N 65534
            . One line paragraph.
            . .
            . Two-line
            . paragraph.
            N 65535
            . Paragraph one.
            . .
            . Paragraph two
            .    with an indented second line.
        """
        self._test_ctl(skool, exp_ctl, keep_lines=1)

    def test_keep_lines_in_block_end_comments(self):
        skool = """
            ; Routine with no end comment
            c65533 RET

            ; Routine
            c65534 RET
            ; End comment
            ; over two lines.

            ; Routine
            c65535 RET
            ; Paragraph one.
            ; .
            ; Paragraph two
            ;    with an indented second line.
        """
        exp_ctl = """
            c 65533
            . Routine with no end comment
            c 65534
            . Routine
            E 65534
            . End comment
            . over two lines.
            c 65535
            . Routine
            E 65535
            . Paragraph one.
            . .
            . Paragraph two
            .    with an indented second line.
        """
        self._test_ctl(skool, exp_ctl, keep_lines=1)

    def test_keep_lines_in_instruction_comments(self):
        skool = """
            ; Data
            b60000 DEFB 0    ; This byte
                             ; is zero.

            ; Routine
            c60001 XOR A     ; {Clear the accumulator
             60002 RET       ; before returning.}

            ; Various
            b60003 DEFS 10   ; 10 bytes
                             ; of padding.
             60013 DEFM "Hi" ; {Hi.
             60015 DEFM "Lo" ; Lo.}
             60017 DEFW 0    ; {More comment
             60019 DEFW 0    ; lines than
                             ; instructions.}
             60021 DEFB 0    ; {Fewer comment lines than instructions.
             60022 DEFB 0    ; }
             60023 DEFB 0    ; {A mixture
             60024 DEFM "a"  ; of instruction
             60025 DEFW 0    ; types.}
            @rem=Test single-instruction comments consisting of zero, one or two dots (data)
             60027 DEFB 0    ;
             60028 DEFB 0    ; .
             60029 DEFB 0    ; ..
            @rem=Test multi-instruction comments consisting of zero, one or two dots (data)
             60030 DEFB 0    ; {
             60031 DEFB 0    ; }
             60032 DEFB 0    ; {.
             60033 DEFB 0    ; }
             60034 DEFB 0    ; {
             60035 DEFB 0    ; ..}

            ; Test a commentless sequence of mixed-base instructions
            c60036 LD A,0
             60038 LD A,%00000001
             60040 LD A,$00
            @rem=Test a comment with an indent
             60042 XOR A    ; This comment has
                            ;      an indented second line.
            @rem=Test comments starting or ending with a brace
             60043 XOR B    ; { {}}
             60044 XOR C    ; {{} }
            @rem=Test single-instruction comments consisting of zero, one or two dots (code)
             60045 XOR D    ;
             60046 XOR E    ; .
             60047 XOR H    ; ..
            @rem=Test multi-instruction comments consisting of zero, one or two dots (code)
             60048 XOR L    ; {
             60049 AND A    ; }
             60050 AND B    ; {.
             60051 AND C    ; }
             60052 AND D    ; {
             60053 AND E    ; ..}
            @rem=Test blank comments with continuation lines
             60054 AND H    ;
                            ;
             60055 AND L    ; {
             60056 OR A     ;
                            ; }
            @rem=Test blank leading and trailing comment lines
             60057 OR B     ;
                            ; Leading blank line
             60058 OR C     ; Trailing blank line
                            ;
        """
        exp_ctl = """
            b 60000
            . Data
            B 60000,1,1
            . This byte
            . is zero.
            c 60001
            . Routine
            C 60001,2
            . Clear the accumulator
            . before returning.
            b 60003
            . Various
            S 60003,10,10
            . 10 bytes
            . of padding.
            T 60013,4,2
            . Hi.
            . Lo.
            W 60017,4,2
            . More comment
            . lines than
            . instructions.
            B 60021,2,1
            . Fewer comment lines than instructions.
            M 60023,4
            . A mixture
            . of instruction
            . types.
            B 60023,1,1
            T 60024,1,1
            W 60025,2,2
            @ 60027 rem=Test single-instruction comments consisting of zero, one or two dots (data)
            B 60027,1,1
            B 60028,1,1
            . .
            B 60029,1,1
            . ..
            @ 60030 rem=Test multi-instruction comments consisting of zero, one or two dots (data)
            B 60030,2,1
            .
            B 60032,2,1
            . .
            B 60034,2,1
            .
            . ..
            c 60036
            . Test a commentless sequence of mixed-base instructions
            C 60038,b2
            @ 60042 rem=Test a comment with an indent
            C 60042,1
            . This comment has
            .      an indented second line.
            @ 60043 rem=Test comments starting or ending with a brace
            C 60043,1
            . {
            C 60044,1
            . }
            @ 60045 rem=Test single-instruction comments consisting of zero, one or two dots (code)
            C 60046,1
            . .
            C 60047,1
            . ..
            @ 60048 rem=Test multi-instruction comments consisting of zero, one or two dots (code)
            C 60048,2
            .
            C 60050,2
            . .
            C 60052,2
            .
            . ..
            @ 60054 rem=Test blank comments with continuation lines
            C 60054,1
            .
            .
            C 60055,2
            .
            .
            .
            @ 60057 rem=Test blank leading and trailing comment lines
            C 60057,1
            .
            . Leading blank line
            C 60058,1
            . Trailing blank line
            .
            i 60059
        """
        self._test_ctl(skool, exp_ctl, keep_lines=1)

    def test_keep_continuation_lines_in_instruction_comments(self):
        skool = """
            ; Data
            b50000 DEFB 0    ; {This byte
                             ; is zero.
             50001 DEFB 1    ; And this byte
                             ; is one.}
             50002 DEFB 2    ; {This byte is two.
             50003 DEFB 3    ; But this byte
                             ; is three.
             50004 DEFB 4    ; And this byte is four.}
        """
        exp_ctl = """
            b 50000
            . Data
            B 50000,2,1
            . This byte
            : is zero.
            . And this byte
            . is one.
            B 50002,3,1
            . This byte is two.
            . But this byte
            : is three.
            . And this byte is four.
            i 50005
        """
        self._test_ctl(skool, exp_ctl, keep_lines=1)
