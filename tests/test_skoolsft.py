# -*- coding: utf-8 -*-
import unittest

from skoolkittest import SkoolKitTestCase
from skoolkit import SkoolParsingError
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
@ignoredua
; Routine description
;
; A Some value
; B Another value
@label=START
@isub=DI
c32768 NOP          ; Do nothing
@bfix=DEFB 1,3
 32769 DEFB 1,2     ; 1-line B sub-block
@ignoreua
 32771 DEFB 3       ; {2-line B sub-block
@ssub=DEFB 5,6
 32772 DEFB 4,5     ; }
@ignoremrcua
; Mid-block comment
 32774 DEFM "Hello" ; T sub-block
@keep
 32779 DEFW 12345   ; W sub-block
@nowarn
 32781 DEFS 2       ; S sub-block
@nolabel
@ofix=LD A,6
*32783 LD A,5       ; {Sub-block with instructions of various types
@rem=Hello!
 32785 DEFB 0       ;
@rsub=DEFB 3
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
@isub+begin
       DEFB 102
@isub-else
 32799 DEFB 3
@isub-end
@ofix-begin
 32800 DEFB 4
@ofix+else
 32800 DEFB 104
@ofix+end
@rfix+begin
       DEFB 205
@rfix+end
@rsub-begin
 32802 DEFB 5
@rsub-end

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
@ignoredua
; Routine description
;
; A Some value
; B Another value
@label=START
@isub=DI
cC32768,1;20 Do nothing
@bfix=DEFB 1,3
 B32769,2;20 1-line B sub-block
@ignoreua
 B32771,1;20 {2-line B sub-block
@ssub=DEFB 5,6
 B32772,2;20 }
@ignoremrcua
; Mid-block comment
 T32774,5;20 T sub-block
@keep
 W32779,2;20 W sub-block
@nowarn
 S32781,2;20 S sub-block
@nolabel
@ofix=LD A,6
*C32783,2;20 {Sub-block with instructions of various types
@rem=Hello!
 B32785,1;20
@rsub=DEFB 3
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
@isub+begin
       DEFB 102
@isub-else
 B32799,1
@isub-end
@ofix-begin
 B32800,1
@ofix+else
 32800 DEFB 104
@ofix+end
@rfix+begin
       DEFB 205
@rfix+end
@rsub-begin
 B32802,1
@rsub-end

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
 54600 DEFS 50,","            ;
 54650 DEFS 50,";"            ; }
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

class SftWriterTest(SkoolKitTestCase):
    def _test_sft(self, skool, exp_sft, write_hex=0, preserve_base=False, min_address=0, max_address=65536):
        skoolfile = self.write_text_file(skool, suffix='.skool')
        writer = SftWriter(skoolfile, write_hex, preserve_base)
        writer.write(min_address, max_address)
        sft = self.out.getvalue().split('\n')[:-1]
        self.assertEqual(exp_sft, sft)

    def test_invalid_address(self):
        writer = SftWriter(self.write_text_file('c4000f RET'))
        with self.assertRaises(SkoolParsingError) as cm:
            writer.write()
        self.assertEqual(cm.exception.args[0], "Invalid address (4000f):\nc4000f RET")

    def test_sftwriter(self):
        self._test_sft(TEST_SKOOL, TEST_SFT)

    def test_write_hex(self):
        self._test_sft('c40177 RET', ['cC$9CF1,1'], write_hex=1)

    def test_write_hex_lower(self):
        self._test_sft('c40177 RET', ['cC$9cf1,1'], write_hex=-1)

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
            'wW40000,b4,2:c2:2,8,2:b2:2,4:b2:4*2,4*4,b4*2'
        ]
        self._test_sft(TEST_WORD_FORMATS_SKOOL, exp_sft, preserve_base=False)

    def test_word_formats_preserve_base(self):
        exp_sft = [
            '; Binary and mixed-base DEFW statements',
            'wW40000,b4,d2:c2:d2,h8,d2:b2:h2,h4:b2:d4*2,d4*2,h4*2,b4*2'
        ]
        self._test_sft(TEST_WORD_FORMATS_SKOOL, exp_sft, preserve_base=True)

    def test_s_directives_no_base(self):
        exp_sft = [
            '; DEFS statements in various bases',
            'sS50000,b%0000000111110100,1000,$07D0,500:b%10101010,$0100:170',
            ' S54256,256:c"\\"";30 {Tricky characters',
            ' S54512,88:c"\\\\",50:c",";30',
            ' S54650,50:c";";30 }'
        ]
        self._test_sft(TEST_S_DIRECTIVES_SKOOL, exp_sft, preserve_base=False)

    def test_s_directives_preserve_base(self):
        exp_sft = [
            '; DEFS statements in various bases',
            'sS50000,b%0000000111110100,d1000,h$07D0,d500:b%10101010,h$0100:d170',
            ' S54256,d256:c"\\"";30 {Tricky characters',
            ' S54512,d88:c"\\\\",d50:c",";30',
            ' S54650,d50:c";";30 }'
        ]
        self._test_sft(TEST_S_DIRECTIVES_SKOOL, exp_sft, preserve_base=True)

    def test_operand_bases_no_base(self):
        exp_sft = [
            '; Operations in various bases',
            'cC60000,2;33 Decimal',
            ' C60002,b2;33 {Binary, hexadecimal',
            ' C60004,2;33 }',
            ' C60006,b2;33 Space',
            ' C60008,2;32 Tab',
            ' C60010,2;32 Another tab',
            ' C60012,2;32 Tab, space',
            ' C60014,3;33 Two spaces',
            ' C60017,b3;33 Two spaces, two spaces',
            ' C60020,3;31 Tab, tab',
            ' C60023,b3,3,b3',
            ' C60032,3;33 {Hexadecimal, decimal',
            ' C60035,3;33 }',
            ' C60038,6,b3,3,nb4,4,bn4,4,b2,3,b3,6,b4,7,b4,7,b4,8,b3,8,b3,8,b4,4,b2,3,b3,5,b2,4,b2,3,b3,6,b3,6,b4,8,b4,8,b4,4',
            ' C60218,2;33 {No operands',
            ' C60220,2;33',
            ' C60222,2;33 }',
            ' C60224,4,b4,26'
        ]
        self._test_sft(TEST_OPERAND_BASES_SKOOL, exp_sft, preserve_base=False)

    def test_operand_bases_preserve_base(self):
        exp_sft = [
            '; Operations in various bases',
            'cC60000,d2;33 Decimal',
            ' C60002,b2;33 {Binary, hexadecimal',
            ' C60004,h2;33 }',
            ' C60006,b2;33 Space',
            ' C60008,h2;32 Tab',
            ' C60010,d2;32 Another tab',
            ' C60012,h2;32 Tab, space',
            ' C60014,d3;33 Two spaces',
            ' C60017,b3;33 Two spaces, two spaces',
            ' C60020,h3;31 Tab, tab',
            ' C60023,b3,d3,b3',
            ' C60032,h3;33 {Hexadecimal, decimal',
            ' C60035,d3;33 }',
            ' C60038,d3,h3,b3,h3,hb4,dh4,bd4,hh4,b2,h3,b3,d3,h3,b4,d4,h3,b4,d4,h3,b4,d4,h4,b3,d4,h4,b3,d4,h4,b4,d2,h2,b2,h3,b3,d3,h2,b2,d2,h2,b2,h3,b3,d3,h3,b3,d3,h3,b4,d4,h4,b4,d4,h4,b4,d4',
            ' C60218,2;33 {No operands',
            ' C60220,2;33',
            ' C60222,2;33 }',
            ' C60224,h4,b4,d7,h5,d2,h3,d3,h4,d2'
        ]
        self._test_sft(TEST_OPERAND_BASES_SKOOL, exp_sft, preserve_base=True)

    def test_character_operands_no_base(self):
        exp_sft = [
            '; Instruction operands as characters',
            'cC61000,c6,2,c5,nc4'
        ]
        self._test_sft(TEST_CHARACTER_OPERANDS_SKOOL, exp_sft, preserve_base=False)

    def test_character_operands_preserve_base(self):
        exp_sft = [
            '; Instruction operands as characters',
            'cC61000,c6,d2,c5,hc4'
        ]
        self._test_sft(TEST_CHARACTER_OPERANDS_SKOOL, exp_sft, preserve_base=True)

    def test_operands_with_commas_no_base(self):
        exp_sft = [
            '; Instruction operands that contain commas',
            'cC62000,c8,nc4,cn4,cc4'
        ]
        self._test_sft(TEST_OPERANDS_WITH_COMMAS_SKOOL, exp_sft, preserve_base=False)

    def test_operands_with_commas_preserve_base(self):
        exp_sft = [
            '; Instruction operands that contain commas',
            'cC62000,c8,dc4,ch4,cc4'
        ]
        self._test_sft(TEST_OPERANDS_WITH_COMMAS_SKOOL, exp_sft, preserve_base=True)

    def test_semicolons_in_instructions(self):
        skool = '\n'.join((
            'c60000 CP ";"             ; First comment',
            ' 60002 LD A,";"           ; Comment 2',
            ' 60004 LD B,(IX+";")      ; Comment 3',
            ' 60007 LD (IX+";"),C      ; Comment 4',
            ' 60010 LD (IX+";"),";"    ; Comment 5',
           r' 60014 LD (IX+"\""),";"   ; Comment 6',
           r' 60018 LD (IX+"\\"),";"   ; Comment 7',
            ' 60022 DEFB 5,"hi;",6     ; Comment 8',
            ' 60027 DEFM ";0;",0       ; Last comment'
        ))
        exp_sft = [
            'cC60000,c2;26 First comment',
            ' C60002,c2;26 Comment 2',
            ' C60004,c3;26 Comment 3',
            ' C60007,c3;26 Comment 4',
            ' C60010,cc4;26 Comment 5',
            ' C60014,cc4;26 Comment 6',
            ' C60018,cc4;26 Comment 7',
            ' B60022,1:T3:1;26 Comment 8',
            ' T60027,3:B1;26 Last comment',
        ]
        self._test_sft(skool, exp_sft)

    def test_gap_between_instructions(self):
        skool = '\n'.join((
            'c25000 LD A,10',
            ' 26000 LD C,D'
        ))
        exp_sft = [
            'cC25000,2',
            ' C26000,1',
        ]
        self._test_sft(skool, exp_sft)

    def test_instructions_in_wrong_order(self):
        skool = '\n'.join((
            'c26000 LD C,10',
            ' 25000 LD A,B'
        ))
        exp_sft = [
            'cC26000,2',
            ' C25000,1',
        ]
        self._test_sft(skool, exp_sft)

    def test_invalid_instruction_has_size_one_and_is_not_compressed(self):
        skool = '\n'.join((
            'c30000 LD A,n  ;',
            ' 30002 INC A   ;',
            ' 30003 SUB B   ;',
            ' 30004 RET     ;',
        ))
        exp_sft = [
            'cC30000,1;15',
            ' C30002,3;15',
        ]
        self._test_sft(skool, exp_sft)

    def test_compression_of_commentless_defb_sequence(self):
        skool = '\n'.join((
            'b40000 DEFB 0     ;',
            ' 40001 DEFB 0,0   ;',
            ' 40003 DEFB 0,0,0 ;',
        ))
        exp_sft = ['bB40000,1,2,3;18']
        self._test_sft(skool, exp_sft)

    def test_min_address(self):
        skool = '\n'.join((
            'b40000 DEFB 0',
            '',
            '; Data at 40001',
            'b40001 DEFB 1',
            '',
            'b40002 DEFB 2',
        ))
        exp_sft = [
            '; Data at 40001',
            'bB40001,1',
            '',
            'bB40002,1',
        ]
        self._test_sft(skool, exp_sft, min_address=40001)

    def test_min_address_between_entries(self):
        skool = '\n'.join((
            'c40000 LD A,B',
            '; Mid-block comment.',
            ' 40001 INC A',
            ' 40002 RET',
            '',
            '; Routine at 40003',
            'c40003 RET',
            '',
            'c40004 RET',
        ))
        exp_sft = [
            '; Routine at 40003',
            'cC40003,1',
            '',
            'cC40004,1',
        ]
        self._test_sft(skool, exp_sft, min_address=40001)

    def test_min_address_gives_no_content(self):
        skool = '\n'.join((
            'b40000 DEFB 0',
            '',
            'b40001 DEFB 1',
        ))
        exp_sft = []
        self._test_sft(skool, exp_sft, min_address=40002)

    def test_max_address(self):
        skool = '\n'.join((
            'b40000 DEFB 0',
            '',
            'b40001 DEFB 1',
            '; End comment.',
            '',
            'b40002 DEFB 2',
        ))
        exp_sft = [
            'bB40000,1',
            '',
            'bB40001,1',
            '; End comment.',
        ]
        self._test_sft(skool, exp_sft, max_address=40002)

    def test_max_address_at_mid_block_comment(self):
        skool = '\n'.join((
            'c50000 RET',
            '',
            'c50001 LD A,B',
            ' 50002 INC A',
            '; And here we return.',
            ' 50003 RET',
        ))
        exp_sft = [
            'cC50000,1',
            '',
            'cC50001,2',
        ]
        self._test_sft(skool, exp_sft, max_address=50003)

    def test_max_address_gives_no_content(self):
        skool = '\n'.join((
            'b40000 DEFB 0',
            '',
            'b40001 DEFB 1',
        ))
        exp_sft = []
        self._test_sft(skool, exp_sft, max_address=40000)

    def test_min_and_max_address(self):
        skool = '\n'.join((
            'b40000 DEFB 0',
            '',
            'b40001 DEFB 1',
            '',
            'b40002 DEFB 2',
            '',
            'b40003 DEFB 3',
        ))
        exp_sft = [
            'bB40001,1',
            '',
            'bB40002,1',
        ]
        self._test_sft(skool, exp_sft, min_address=40001, max_address=40003)

    def test_min_and_max_address_give_no_content(self):
        skool = '\n'.join((
            'b40000 DEFB 0',
            '',
            'b40001 DEFB 1',
            '',
            'b40002 DEFB 2',
        ))
        exp_sft = []
        self._test_sft(skool, exp_sft, min_address=40001, max_address=40001)

    def test_max_address_after_asm_block_directive(self):
        skool = '\n'.join((
            'c30000 LD A,(HL)',
            '@ssub-begin',
            ' 30001 INC L',
            '@ssub+else',
            '       INC HL',
            '@ssub+end',
            ' 30002 RET',
        ))
        exp_sft = [
            'cC30000,1',
            '@ssub-begin',
            ' C30001,1',
            '@ssub+else',
            '       INC HL',
            '@ssub+end',
        ]
        self._test_sft(skool, exp_sft, max_address=30002)

if __name__ == '__main__':
    unittest.main()
