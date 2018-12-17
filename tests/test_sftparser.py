import re
import textwrap

from skoolkittest import SkoolKitTestCase
from skoolkit.sftparser import SftParser, SftParsingError

TEST_SFT = """#
# Test sft file for SftParser unit testing
#
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
sS32793,1

; Test an invalid control directive
a32794 NOP

; Test complex DEFM statements
tT32795,5,1:B1,2:B2*2

; Test complex DEFB statements
bB32810,2:T1,1:T2*2,1
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
TEST_SNAPSHOT[32795:32820] = [ord('a')] * 25

TEST_SKOOL = """; Data at 0
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
s32793 DEFS 1

; Test an invalid control directive
a32794 NOP

; Test complex DEFM statements
t32795 DEFM "aaaaa"
 32800 DEFM "a",97
 32802 DEFM "aa",97,97
 32806 DEFM "aa",97,97

; Test complex DEFB statements
b32810 DEFB 97,97,"a"
 32813 DEFB 97,"aa"
 32816 DEFB 97,"aa"
 32819 DEFB 97
"""

TEST_SKOOL_HEX = """; Data at 0
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
s$8019 DEFS $01

; Test an invalid control directive
a32794 NOP

; Test complex DEFM statements
t$801B DEFM "aaaaa"
 $8020 DEFM "a",$61
 $8022 DEFM "aa",$61,$61
 $8026 DEFM "aa",$61,$61

; Test complex DEFB statements
b$802A DEFB $61,$61,"a"
 $802D DEFB $61,"aa"
 $8030 DEFB $61,"aa"
 $8033 DEFB $61
"""

class SftParserTest(SkoolKitTestCase):
    def _parse_sft(self, sft, snapshot=(), asm_hex=False, asm_lower=False, min_address=0, max_address=65536):
        sftfile = self.write_text_file(textwrap.dedent(sft).strip(), suffix='.sft')
        writer = SftParser(snapshot[:], sftfile, asm_hex=asm_hex, asm_lower=asm_lower)
        writer.write_skool(min_address, max_address)
        return writer.snapshot, self.out.getvalue()

    def _test_disassembly(self, sft, exp_skool, snapshot=(), asm_hex=False, asm_lower=False, min_address=0, max_address=65536):
        skool = self._parse_sft(sft, snapshot, asm_hex, asm_lower, min_address, max_address)[1]
        self.assertEqual(textwrap.dedent(exp_skool).strip(), skool.rstrip())

    def test_write_skool(self):
        snapshot, skool = self._parse_sft(TEST_SFT, TEST_SNAPSHOT)
        self.assertEqual(TEST_SKOOL, skool)

    def test_write_skool_hex(self):
        snapshot, skool = self._parse_sft(TEST_SFT, TEST_SNAPSHOT, asm_hex=True)
        self.assertEqual(TEST_SKOOL_HEX, skool)

    def test_write_skool_hex_lower(self):
        snapshot, skool = self._parse_sft('bB19132,1', [0] * 19133, asm_hex=True, asm_lower=True)
        self.assertEqual(skool.rstrip(), 'b$4abc defb $00')

    def test_defb_directives(self):
        snapshot = [0] * 5
        sft = """
            @defb=0:1,$02,%11
            @defb=3:"Hi" ; Hi
            bB00000,5
        """
        exp_skool = """
            @defb=0:1,$02,%11
            @defb=3:"Hi" ; Hi
            b00000 DEFB 1,2,3,72,105
        """
        self._test_disassembly(sft, exp_skool, snapshot)

    def test_defs_directives(self):
        snapshot = [0] * 5
        sft = """
            @defs=0:3,2
            @defs=3:2,"!" ; !!
            bB00000,5
        """
        exp_skool = """
            @defs=0:3,2
            @defs=3:2,"!" ; !!
            b00000 DEFB 2,2,2,33,33
        """
        self._test_disassembly(sft, exp_skool, snapshot)

    def test_defw_directives(self):
        snapshot = [0] * 6
        sft = """
            @defw=0:257,513
            @defw=4:$8001 ; 32769
            bB00000,6
        """
        exp_skool = """
            @defw=0:257,513
            @defw=4:$8001 ; 32769
            b00000 DEFB 1,1,1,2,1,128
        """
        self._test_disassembly(sft, exp_skool, snapshot)

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
            "cC50000,b",
            "cC50000,b5:B5",
            "cC$ABCG,20"
        ):
            with self.assertRaisesRegex(SftParsingError, re.escape("Invalid line: {}".format(line.split()[0]))):
                self._parse_sft(line)

    def test_byte_formats(self):
        snapshot = [42] * 75
        sft = """
            bB00000,b5
             B00005,h15
             B00020,b2,d1:n1,h1
             B00025,b2:d1:m1:h1
             B00030,h5:d3:b2
             B00040,b1,h2*2
             B00045,h1,T4
             B00050,b2:T3
             T00055,h2,3
             T00060,2:d2:n1
             T00065,2,B1*2,m1
             T00070,B2:h3
        """
        exp_skool = """
            b00000 DEFB %00101010,%00101010,%00101010,%00101010,%00101010
             00005 DEFB $2A,$2A,$2A,$2A,$2A,$2A,$2A,$2A,$2A,$2A,$2A,$2A,$2A,$2A,$2A
             00020 DEFB %00101010,%00101010
             00022 DEFB 42,42
             00024 DEFB $2A
             00025 DEFB %00101010,%00101010,42,-214,$2A
             00030 DEFB $2A,$2A,$2A,$2A,$2A,42,42,42,%00101010,%00101010
             00040 DEFB %00101010
             00041 DEFB $2A,$2A
             00043 DEFB $2A,$2A
             00045 DEFB $2A
             00046 DEFB "****"
             00050 DEFB %00101010,%00101010,"***"
             00055 DEFM $2A,$2A
             00057 DEFM "***"
             00060 DEFM "**",42,42,42
             00065 DEFM "**"
             00067 DEFM 42
             00068 DEFM 42
             00069 DEFM -214
             00070 DEFM 42,42,$2A,$2A,$2A
        """
        self._test_disassembly(sft, exp_skool, snapshot)

    def test_byte_formats_hex(self):
        snapshot = [33] * 12
        sft = """
            bB00000,b1:d1:h1:1:m1:n1
             T00006,b1:d1:h1:1:m1:n1
        """
        exp_skool = """
            b$0000 DEFB %00100001,33,$21,$21,-$DF,$21
             $0006 DEFM %00100001,33,$21,"!",-$DF,$21
        """
        self._test_disassembly(sft, exp_skool, snapshot, asm_hex=True)

    def test_text_containing_invalid_characters(self):
        snapshot = [65, 0, 66, 94, 67, 96, 127, 68, 255]
        sft = "tT00000,9"
        exp_skool = 't00000 DEFM "A",0,"B",94,"C",96,127,"D",255'
        self._test_disassembly(sft, exp_skool, snapshot)

    def test_text_containing_invalid_characters_hex(self):
        snapshot = [65, 0, 66, 94, 67, 96, 127, 68, 255]
        sft = "tT00000,9"
        exp_skool = 't$0000 DEFM "A",$00,"B",$5E,"C",$60,$7F,"D",$FF'
        self._test_disassembly(sft, exp_skool, snapshot, asm_hex=True)

    def test_text_containing_invalid_characters_hex_lower(self):
        snapshot = [65, 0, 66, 94, 67, 96, 127, 68, 255]
        sft = "tT00000,9"
        exp_skool = 't$0000 defm "A",$00,"B",$5e,"C",$60,$7f,"D",$ff'
        self._test_disassembly(sft, exp_skool, snapshot, asm_hex=True, asm_lower=True)

    def test_inverted_characters(self):
        snapshot = [225, 226, 72, 233, 76, 239, 225, 0, 62, 225, 225, 225, 128, 222]
        sft = """
            bB00000,T1
             T00001,1
             B00002,T1:T1
             T00004,1:1
             W00006,c2
             C00008,c2
             S00010,2:c225
             B00012,T1
             T00013,1
        """
        exp_skool = """
            b00000 DEFB "a"+128
             00001 DEFM "b"+128
             00002 DEFB "H","i"+128
             00004 DEFM "L","o"+128
             00006 DEFW "a"+128
             00008 LD A,"a"+128
             00010 DEFS 2,"a"+128
             00012 DEFB 128
             00013 DEFM 222
        """
        self._test_disassembly(sft, exp_skool, snapshot)

    def test_inverted_characters_hex(self):
        snapshot = [225, 226, 72, 233, 76, 239, 225, 0, 62, 225, 225, 225, 128, 224]
        sft = """
            bB00000,T1
             T00001,1
             B00002,T1:T1
             T00004,1:1
             W00006,c2
             C00008,c2
             S00010,2:c225
             B00012,T1
             T00013,1
        """
        exp_skool = """
            b$0000 DEFB "a"+$80
             $0001 DEFM "b"+$80
             $0002 DEFB "H","i"+$80
             $0004 DEFM "L","o"+$80
             $0006 DEFW "a"+$80
             $0008 LD A,"a"+$80
             $000A DEFS $02,"a"+$80
             $000C DEFB $80
             $000D DEFM $E0
        """
        self._test_disassembly(sft, exp_skool, snapshot, asm_hex=True)

    def test_word_formats(self):
        snapshot = [205, 85] * 20 + [32, 0] * 2
        sft = """
            wW00000,4
             W00004,b4
             W00008,d4
             W00012,h4
             W00016,2,d2,h2:n2
             W00024,b2:m2:2:h2
             W00032,b2,4,m2
             W00040,c2:2
        """
        exp_skool = """
            w00000 DEFW 21965,21965
             00004 DEFW %0101010111001101,%0101010111001101
             00008 DEFW 21965,21965
             00012 DEFW $55CD,$55CD
             00016 DEFW 21965
             00018 DEFW 21965
             00020 DEFW $55CD,21965
             00024 DEFW %0101010111001101,-43571,21965,$55CD
             00032 DEFW %0101010111001101
             00034 DEFW 21965,21965
             00038 DEFW -43571
             00040 DEFW " ",32
        """
        self._test_disassembly(sft, exp_skool, snapshot)

    def test_word_formats_hex(self):
        snapshot = [170] * 12
        sft = 'wW00000,b2,d2,h2,2,m2,n2'
        exp_skool = """
            w$0000 DEFW %1010101010101010
             $0002 DEFW 43690
             $0004 DEFW $AAAA
             $0006 DEFW $AAAA
             $0008 DEFW -$5556
             $000A DEFW $AAAA
        """
        self._test_disassembly(sft, exp_skool, snapshot, asm_hex=True)

    def test_s_directives(self):
        snapshot = [1] * 4 + [0] * 1274
        sft = """
            sS00000,4,b3,d2,h1
             S00010,b10,d10,h5,n5
             S00040,10
             S00050,b300,d300,h300
             S00950,c" ",c160,c4,c132
        """
        exp_skool = """
            s00000 DEFS 4,1
             00004 DEFS %00000011
             00007 DEFS 2
             00009 DEFS $01
             00010 DEFS %00001010
             00020 DEFS 10
             00030 DEFS $05
             00035 DEFS 5
             00040 DEFS 10
             00050 DEFS %0000000100101100
             00350 DEFS 300
             00650 DEFS $012C
             00950 DEFS " "
             00982 DEFS " "+128
             01142 DEFS 4
             01146 DEFS 132
        """
        self._test_disassembly(sft, exp_skool, snapshot)

    def test_s_directives_hex(self):
        snapshot = [1] * 10 + [0] * 40
        sft = 'sS00000,d10,b10,h10,10,n10'
        exp_skool = """
            s$0000 DEFS 10,$01
             $000A DEFS %00001010
             $0014 DEFS $0A
             $001E DEFS $0A
             $0028 DEFS $0A
        """
        self._test_disassembly(sft, exp_skool, snapshot, asm_hex=True)

    def test_s_directives_with_byte_value_base(self):
        snapshot = [1, 1, 33, 33, 3, 3, 4, 4, 5, 5, 161, 161, 7, 7, 136, 136, 255, 255]
        sft = 'sS00000,2:b,2:c,2:d,2:h,h2:n,2:c*3,2:m'
        exp_skool = """
            s00000 DEFS 2,%00000001
             00002 DEFS 2,"!"
             00004 DEFS 2,3
             00006 DEFS 2,$04
             00008 DEFS $02,5
             00010 DEFS 2,"!"+128
             00012 DEFS 2,7
             00014 DEFS 2,136
             00016 DEFS 2,-1
        """
        self._test_disassembly(sft, exp_skool, snapshot)

    def test_s_directives_with_byte_value_base_hex(self):
        snapshot = [1, 1, 33, 33, 3, 3, 4, 4, 5, 5, 161, 161, 7, 7, 136, 136, 255, 255]
        sft = 'sS00000,2:b,2:c,2:d,2:h,d2:n,2:c*3,2:m'
        exp_skool = """
            s$0000 DEFS $02,%00000001
             $0002 DEFS $02,"!"
             $0004 DEFS $02,3
             $0006 DEFS $02,$04
             $0008 DEFS 2,$05
             $000A DEFS $02,"!"+$80
             $000C DEFS $02,$07
             $000E DEFS $02,$88
             $0010 DEFS $02,-$01
        """
        self._test_disassembly(sft, exp_skool, snapshot, asm_hex=True)

    def test_s_directives_with_mixed_values(self):
        snapshot = [0, 1, 2, 3, 4, 5]
        sft = 'sS00000,2,2:h,2:n'
        exp_skool = """
            s00000 DEFB 0,1
             00002 DEFB 2,3
             00004 DEFB 4,5
        """
        self._test_disassembly(sft, exp_skool, snapshot)

    def test_byte_arg_bases(self):
        snapshot = [
            62, 5,      # 00000 LD A,5
            6, 6,       # 00002 LD B,6
            14, 7,      # 00004 LD C,7
            22, 240,    # 00006 LD D,240
            30, 128,    # 00008 LD E,128
            38, 200,    # 00010 LD H,200
            46, 100,    # 00012 LD L,100
            221, 38, 1, # 00014 LD IXh,1
            221, 46, 2, # 00017 LD IXl,2
            253, 38, 3, # 00020 LD IYh,3
            253, 46, 4, # 00023 LD IYl,4
            54, 27,     # 00026 LD (HL),27
            198, 32,    # 00028 ADD A,32
            206, 33,    # 00030 ADC A,33
            230, 34,    # 00032 AND 34
            254, 35,    # 00034 CP 35
            219, 254,   # 00036 IN A,(254)
            246, 36,    # 00038 OR 36
            211, 254,   # 00040 OUT (254),A
            222, 37,    # 00042 SBC A,37
            214, 38,    # 00044 SUB 38
            238, 39,    # 00046 XOR 39
        ]
        sft = """
            cC00000,b6
             C00006,m2,d4,h8
             C00020,n6
             C00026,bn6
             C00032,nb6,bd4,hb6
        """
        exp_skool = """
            c00000 LD A,%00000101
             00002 LD B,%00000110
             00004 LD C,%00000111
             00006 LD D,-16
             00008 LD E,128
             00010 LD H,200
             00012 LD L,$64
             00014 LD IXh,$01
             00017 LD IXl,$02
             00020 LD IYh,3
             00023 LD IYl,4
             00026 LD (HL),%00011011
             00028 ADD A,%00100000
             00030 ADC A,%00100001
             00032 AND 34
             00034 CP 35
             00036 IN A,(254)
             00038 OR %00100100
             00040 OUT (%11111110),A
             00042 SBC A,$25
             00044 SUB $26
             00046 XOR $27
        """
        self._test_disassembly(sft, exp_skool, snapshot)

    def test_index_bases(self):
        snapshot = [
            221, 126, 15,       # 00000 LD A,(IX+15)
            253, 112, 233,      # 00003 LD (IY-23),B
            221, 142, 243,      # 00006 ADC A,(IX-13)
            253, 134, 120,      # 00009 ADD A,(IY+120)
            221, 158, 47,       # 00012 SBC A,(IX+47)
            253, 166, 251,      # 00015 AND (IY-5)
            221, 190, 237,      # 00018 CP (IX-19)
            253, 182, 102,      # 00021 OR (IY+102)
            221, 150, 99,       # 00024 SUB (IX+99)
            253, 174, 193,      # 00027 XOR (IY-63)
            221, 53, 228,       # 00030 DEC (IX-28)
            253, 52, 7,         # 00033 INC (IY+7)
            221, 203, 77, 22,   # 00036 RL (IX+77)
            253, 203, 164, 6,   # 00040 RLC (IY-92)
            221, 203, 238, 30,  # 00044 RR (IX-18)
            253, 203, 55, 14,   # 00048 RRC (IY+55)
            221, 203, 26, 38,   # 00052 SLA (IX+26)
            253, 203, 158, 54,  # 00056 SLL (IY-98)
            221, 203, 253, 46,  # 00060 SRA (IX-3)
            253, 203, 19, 62,   # 00064 SRL (IY+19)
            221, 203, 33, 70,   # 00068 BIT 0,(IX+33)
            253, 203, 175, 142, # 00072 RES 1,(IY-81)
            221, 203, 192, 214, # 00076 SET 2,(IX-64)
        ]
        sft = """
            cC00000,n6
             C00006,h6,b6,d6
             C00024,hn6
             C00030,bn6
             C00036,dn8
             C00044,nn8
             C00052,hd8,bd8,dd8,nd4
        """
        exp_skool = """
            c$0000 LD A,(IX+$0F)
             $0003 LD (IY-$17),B
             $0006 ADC A,(IX-$0D)
             $0009 ADD A,(IY+$78)
             $000C SBC A,(IX+%00101111)
             $000F AND (IY-%00000101)
             $0012 CP (IX-19)
             $0015 OR (IY+102)
             $0018 SUB (IX+$63)
             $001B XOR (IY-$3F)
             $001E DEC (IX-%00011100)
             $0021 INC (IY+%00000111)
             $0024 RL (IX+77)
             $0028 RLC (IY-92)
             $002C RR (IX-$12)
             $0030 RRC (IY+$37)
             $0034 SLA (IX+$1A)
             $0038 SLL (IY-$62)
             $003C SRA (IX-%00000011)
             $0040 SRL (IY+%00010011)
             $0044 BIT 0,(IX+33)
             $0048 RES 1,(IY-81)
             $004C SET 2,(IX-$40)
        """
        self._test_disassembly(sft, exp_skool, snapshot, asm_hex=True)

    def test_index_arg_bases(self):
        snapshot = [
            221, 54, 45, 87,   # 00000 LD (IX+45),87
            253, 54, 54, 78,   # 00004 LD (IY+54),78
            221, 54, 254, 234, # 00008 LD (IX-2),234
            253, 54, 149, 19,  # 00012 LD (IY-107),19
            221, 54, 13, 255,  # 00016 LD (IX+13),255
            253, 54, 36, 109,  # 00020 LD (IY+36),109
            221, 54, 194, 111, # 00024 LD (IX-62),111
            253, 54, 183, 199, # 00028 LD (IY-73),199
        ]
        sft = """
            cC00000,b4
             C00004,n4
             C00008,h4,d4
             C00016,hb4
             C00020,hn4
             C00024,nh4,hh4
        """
        exp_skool = """
            c00000 LD (IX+%00101101),%01010111
             00004 LD (IY+54),78
             00008 LD (IX-$02),$EA
             00012 LD (IY-107),19
             00016 LD (IX+$0D),%11111111
             00020 LD (IY+$24),109
             00024 LD (IX-62),$6F
             00028 LD (IY-$49),$C7
        """
        self._test_disassembly(sft, exp_skool, snapshot)

    def test_jr_arg_bases(self):
        snapshot = [
            16, 254, # 00000 DJNZ 0
            24, 0,   # 00002 JR 4
            32, 252, # 00004 JR NZ,2
            32, 2,   # 00006 JR NZ,10
            40, 2,   # 00008 JR Z,12
            48, 250, # 00010 JR NC,6
            56, 250, # 00012 JR C,8
            16, 252, # 00014 DJNZ 12
            24, 252, # 00016 JR 14
            32, 254, # 00018 JR NZ,18
        ]
        sft = """
            cC00000,h2
             C00002,b2,d2,n2
             C00008,dh2
             C00010,hd2
             C00012,dn2,nd2,bb2,nn2
        """
        exp_skool = """
            c$0000 DJNZ $0000
             $0002 JR %0000000000000100
             $0004 JR NZ,2
             $0006 JR NZ,$000A
             $0008 JR Z,12
             $000A JR NC,$0006
             $000C JR C,8
             $000E DJNZ $000C
             $0010 JR %0000000000001110
             $0012 JR NZ,$0012
        """
        self._test_disassembly(sft, exp_skool, snapshot, asm_hex=True)

    def test_rst_arg_bases(self):
        snapshot = [
            199, # 00000 RST 0
            207, # 00001 RST 8
            215, # 00002 RST 16
            223, # 00003 RST 24
            231, # 00004 RST 32
            239, # 00005 RST 40
            247, # 00006 RST 56
        ]
        sft = """
            cC00000,h1
             C00001,n1
             C00002,d1,b1,dn1,nd1,b1
        """
        exp_skool = """
            c$0000 RST $00
             $0001 RST $08
             $0002 RST 16
             $0003 RST %00011000
             $0004 RST 32
             $0005 RST $28
             $0006 RST %00110000
        """
        self._test_disassembly(sft, exp_skool, snapshot, asm_hex=True)

    def test_word_arg_bases(self):
        snapshot = [
            1, 1, 0,           # 00000 LD BC,1
            17, 12, 0,         # 00003 LD DE,12
            33, 123, 0,        # 00006 LD HL,123
            49, 210, 4,        # 00009 LD SP,1234
            221, 33, 57, 48,   # 00012 LD IX,12345
            253, 33, 160, 91,  # 00016 LD IY,23456
            58, 7, 135,        # 00020 LD A,(34567)
            237, 75, 110, 178, # 00023 LD BC,(45678)
            237, 91, 213, 221, # 00027 LD DE,(56789)
            42, 152, 255,      # 00031 LD HL,(65432)
            237, 123, 49, 212, # 00034 LD SP,(54321)
            221, 42, 202, 168, # 00038 LD IX,(43210)
            253, 42, 109, 125, # 00042 LD IY,(32109)
            50, 106, 82,       # 00046 LD (21098),A
            237, 67, 235, 42,  # 00049 LD (10987),BC
            237, 83, 148, 38,  # 00053 LD (9876),DE
            34, 61, 34,        # 00057 LD (8765),HL
            237, 115, 230, 29, # 00060 LD (7654),SP
            221, 34, 152, 255, # 00064 LD (65432),IX
            253, 34, 1, 0,     # 00068 LD (1),IY
            205, 11, 0,        # 00072 CALL 11
            195, 111, 0,       # 00075 JP 111
            196, 87, 4,        # 00078 CALL NZ,1111
            204, 103, 43,      # 00081 CALL Z,11111
            212, 104, 43,      # 00084 CALL NC,11112
            220, 114, 43,      # 00087 CALL C,11122
            228, 214, 43,      # 00090 CALL PO,11222
            236, 190, 47,      # 00093 CALL PE,12222
            244, 206, 86,      # 00096 CALL P,22222
            252, 207, 86,      # 00099 CALL M,22223
            194, 217, 86,      # 00102 JP NZ,22233
            202, 61, 87,       # 00105 JP Z,22333
            210, 37, 91,       # 00108 JP NC,23333
            218, 53, 130,      # 00111 JP C,33333
            226, 54, 130,      # 00114 JP PO,33334
            234, 64, 130,      # 00117 JP PE,33344
            242, 164, 130,     # 00120 JP P,33444
            250, 140, 134,     # 00123 JP M,34444
        ]
        sft = """
            cC00000,n6,m3
             C00009,d11
             C00020,b11,h11,dn7
             C00049,nd8
             C00057,dh7
             C00064,hd8
             C00072,db6
             C00078,bd6,hb6,bh6,dd6
             C00102,hh6
             C00108,bb6
             C00114,nn12
        """
        exp_skool = """
            c$0000 LD BC,$0001
             $0003 LD DE,$000C
             $0006 LD HL,-$FF85
             $0009 LD SP,1234
             $000C LD IX,12345
             $0010 LD IY,23456
             $0014 LD A,(%1000011100000111)
             $0017 LD BC,(%1011001001101110)
             $001B LD DE,(%1101110111010101)
             $001F LD HL,($FF98)
             $0022 LD SP,($D431)
             $0026 LD IX,($A8CA)
             $002A LD IY,(32109)
             $002E LD (21098),A
             $0031 LD ($2AEB),BC
             $0035 LD ($2694),DE
             $0039 LD (8765),HL
             $003C LD (7654),SP
             $0040 LD ($FF98),IX
             $0044 LD ($0001),IY
             $0048 CALL 11
             $004B JP 111
             $004E CALL NZ,%0000010001010111
             $0051 CALL Z,%0010101101100111
             $0054 CALL NC,$2B68
             $0057 CALL C,$2B72
             $005A CALL PO,%0010101111010110
             $005D CALL PE,%0010111110111110
             $0060 CALL P,22222
             $0063 CALL M,22223
             $0066 JP NZ,$56D9
             $0069 JP Z,$573D
             $006C JP NC,%0101101100100101
             $006F JP C,%1000001000110101
             $0072 JP PO,$8236
             $0075 JP PE,$8240
             $0078 JP P,$82A4
             $007B JP M,$868C
        """
        self._test_disassembly(sft, exp_skool, snapshot, asm_hex=True)

    def test_character_operands(self):
        snapshot = [
            62, 34,         # 00000 LD A,34
            198, 92,        # 00002 ADD A,42
            214, 33,        # 00004 SUB 33
            254, 63,        # 00006 CP 63
            54, 65,         # 00008 LD (HL),65
            221, 54, 2, 66, # 00010 LD (IX+2),66
            33, 67, 0,      # 00014 LD HL,67
            6, 31,          # 00017 LD B,31
            14, 94,         # 00019 LD C,94
            22, 96,         # 00021 LD D,96
            30, 128,        # 00023 LD E,128
            1, 0, 1,        # 00025 LD BC,256
        ]
        sft = 'cC00000,c10,nc4,c14'
        exp_skool = """
            c00000 LD A,"\\""
             00002 ADD A,"\\\\"
             00004 SUB "!"
             00006 CP "?"
             00008 LD (HL),"A"
             00010 LD (IX+2),"B"
             00014 LD HL,"C"
             00017 LD B,31
             00019 LD C,94
             00021 LD D,96
             00023 LD E,128
             00025 LD BC,256
        """
        self._test_disassembly(sft, exp_skool, snapshot)

    def test_max_address_at_mid_block_comment(self):
        snapshot = [
            120, # 00000 LD A,B
            201, # 00001 RET
        ]
        sft = """
            ; Routine
            cC00000,1;15 We are only interested
             ;15 in this instruction
            ; This comment is past the end address.
             C00001,1;15 And so is this instruction
        """
        exp_skool = """
            ; Routine
            c00000 LD A,B  ; We are only interested
                           ; in this instruction
        """
        self._test_disassembly(sft, exp_skool, snapshot, max_address=1)

    def test_max_address_after_block_end_comment(self):
        snapshot = [
            120, # 00000 LD A,B
            201, # 00001 RET
        ]
        sft = """
            ; We are only interested in this entry
            cC00000,1
            ; The only interesting entry ends here.

            ; This entry is of no interest
            cC00001,1
        """
        exp_skool = """
            ; We are only interested in this entry
            c00000 LD A,B
            ; The only interesting entry ends here.

        """
        self._test_disassembly(sft, exp_skool, snapshot, max_address=1)

    def test_max_address_between_two_directives(self):
        snapshot = [0] * 4
        sft = """
            ; Data at 0
            bB00000,1*2

            ; Data at 2
            bB00002,1
        """
        exp_skool = """
            ; Data at 0
            b00000 DEFB 0
        """
        self._test_disassembly(sft, exp_skool, snapshot, max_address=1)

    def test_max_address_after_asm_block_directive(self):
        snapshot = [0] * 3
        sft = """
            bB00000,1
            @isub-begin
             B00001,1
            @isub+else
                   DEFB 1
            @isub+end
             B00002,1
        """
        exp_skool = """
            b00000 DEFB 0
            @isub-begin
             00001 DEFB 0
            @isub+else
                   DEFB 1
            @isub+end
        """
        self._test_disassembly(sft, exp_skool, snapshot, max_address=2)

    def test_max_address_gives_no_content(self):
        snapshot = [0] * 3
        sft = 'bB00001,1*2'
        exp_skool = ''
        self._test_disassembly(sft, exp_skool, snapshot, max_address=1)

    def test_min_address_at_first_instruction_in_entry(self):
        snapshot = [0] * 4
        sft = """
            ; Data at 0
            bB00000,1

            ; Data at 1
            bB00001,1*2

            ; Data at 3
            bB00003,1
        """
        exp_skool = """
            ; Data at 1
            b00001 DEFB 0
             00002 DEFB 0

            ; Data at 3
            b00003 DEFB 0
        """
        self._test_disassembly(sft, exp_skool, snapshot, min_address=1)

    def test_min_address_at_second_instruction_in_entry(self):
        snapshot = [0] * 5
        sft = """
            ; Data at 0
            bB00000,1

            ; Data at 1
            bB00001,1
             W00002,2

            ; Data at 4
            bB00004,1
        """
        exp_skool = """
            ; Data at 4
            b00004 DEFB 0
        """
        self._test_disassembly(sft, exp_skool, snapshot, min_address=2)

    def test_min_address_between_two_directives(self):
        snapshot = [0] * 4
        sft = """
            ; Data at 0
            bB00000,1

            ; Data at 1
            bB00001,1*2

            ; Data at 3
            bB00003,1
        """
        exp_skool = """
            ; Data at 3
            b00003 DEFB 0
        """
        self._test_disassembly(sft, exp_skool, snapshot, min_address=2)

    def test_min_address_and_max_address(self):
        snapshot = [0] * 4
        sft = """
            ; Data at 0
            bB00000,1

            ; Data at 1
            bB00001,1

            ; Data at 2
            bB00002,1
            ; Mid-block comment at 3.
             B00003,1
        """
        exp_skool = """
            ; Data at 1
            b00001 DEFB 0

            ; Data at 2
            b00002 DEFB 0
        """
        self._test_disassembly(sft, exp_skool, snapshot, min_address=1, max_address=3)

    def test_min_address_and_max_address_give_no_content(self):
        snapshot = [0] * 4
        sft = """
            ; Data at 0
            bB00000,1

            ; Data at 1
            bB00001,1*2

            ; Data at 3
            bB00003,1
        """
        exp_skool = ''
        self._test_disassembly(sft, exp_skool, snapshot, min_address=2, max_address=3)

    def test_asm_directive_assemble(self):
        snapshot = [201]
        sft = """
            @assemble=1
            cC00000,1
            @assemble=0
        """
        exp_skool = """
            @assemble=1
            c00000 RET
            @assemble=0
        """
        self._test_disassembly(sft, exp_skool, snapshot)

    def test_asm_directive_bfix(self):
        snapshot = [192]
        sft = """
            @bfix=RET Z
            cC00000,1
        """
        exp_skool = """
            @bfix=RET Z
            c00000 RET NZ
        """
        self._test_disassembly(sft, exp_skool, snapshot)

    def test_asm_directive_bfix_block(self):
        snapshot = [192]
        sft = """
            @bfix-begin
            cC00000,1
            @bfix+else
            c00000 RET Z
            @bfix+end
        """
        exp_skool = """
            @bfix-begin
            c00000 RET NZ
            @bfix+else
            c00000 RET Z
            @bfix+end
        """
        self._test_disassembly(sft, exp_skool, snapshot)

    def test_asm_directive_end(self):
        snapshot = [201]
        sft = """
            cC00000,1
            @end
        """
        exp_skool = """
            c00000 RET
            @end
        """
        self._test_disassembly(sft, exp_skool, snapshot)

    def test_asm_directive_equ(self):
        snapshot = [33, 0, 64]
        sft = """
            @equ=DISPLAY=16384
            ; Routine
            cC00000,3
        """
        exp_skool = """
            @equ=DISPLAY=16384
            ; Routine
            c00000 LD HL,16384
        """
        self._test_disassembly(sft, exp_skool, snapshot)

    def test_asm_directive_if(self):
        snapshot = [201]
        sft = """
            @if({asm})(replace=/foo/bar)
            cC00000,1
        """
        exp_skool = """
            @if({asm})(replace=/foo/bar)
            c00000 RET
        """
        self._test_disassembly(sft, exp_skool, snapshot)

    def test_asm_directive_ignoreua(self):
        snapshot = [120, 201]
        sft = """
            @ignoreua
            ; Title
            ;
            @ignoreua
            ; Description.
            ;
            @ignoreua
            ; HL Some value
            ;
            @ignoreua
            ; Start comment.
            @ignoreua
            cC00000,1;20 Comment
            @ignoreua
            ; Mid-block comment.
             C00001,1
            @ignoreua
            ; End comment.
        """
        exp_skool = """
            @ignoreua
            ; Title
            ;
            @ignoreua
            ; Description.
            ;
            @ignoreua
            ; HL Some value
            ;
            @ignoreua
            ; Start comment.
            @ignoreua
            c00000 LD A,B       ; Comment
            @ignoreua
            ; Mid-block comment.
             00001 RET
            @ignoreua
            ; End comment.
        """
        self._test_disassembly(sft, exp_skool, snapshot)

    def test_asm_directive_isub(self):
        snapshot = [192]
        sft = """
            @isub=RET Z
            cC00000,1
        """
        exp_skool = """
            @isub=RET Z
            c00000 RET NZ
        """
        self._test_disassembly(sft, exp_skool, snapshot)

    def test_asm_directive_isub_block(self):
        snapshot = [192]
        sft = """
            @isub+begin
            c00000 RET Z
            @isub-else
            cC00000,1
            @isub-end
        """
        exp_skool = """
            @isub+begin
            c00000 RET Z
            @isub-else
            c00000 RET NZ
            @isub-end
        """
        self._test_disassembly(sft, exp_skool, snapshot)

    def test_asm_directive_keep(self):
        snapshot = [1, 0, 0]
        sft = """
            @keep
            cC00000,3
        """
        exp_skool = """
            @keep
            c00000 LD BC,0
        """
        self._test_disassembly(sft, exp_skool, snapshot)

    def test_asm_directive_label(self):
        snapshot = [201]
        sft = """
            @label=START
            cC00000,1
        """
        exp_skool = """
            @label=START
            c00000 RET
        """
        self._test_disassembly(sft, exp_skool, snapshot)

    def test_asm_directive_nowarn(self):
        snapshot = [1, 0, 0]
        sft = """
            @nowarn
            cC00000,3
        """
        exp_skool = """
            @nowarn
            c00000 LD BC,0
        """
        self._test_disassembly(sft, exp_skool, snapshot)

    def test_asm_directive_ofix(self):
        snapshot = [62, 0]
        sft = """
            @ofix=LD A,1
            cC00000,2
        """
        exp_skool = """
            @ofix=LD A,1
            c00000 LD A,0
        """
        self._test_disassembly(sft, exp_skool, snapshot)

    def test_asm_directive_ofix_block(self):
        snapshot = [62, 0]
        sft = """
            @ofix-begin
            cC00000,2
            @ofix+else
            c00000 LD A,1
            @ofix+end
        """
        exp_skool = """
            @ofix-begin
            c00000 LD A,0
            @ofix+else
            c00000 LD A,1
            @ofix+end
        """
        self._test_disassembly(sft, exp_skool, snapshot)

    def test_asm_directive_org(self):
        snapshot = [175, 201]
        sft = """
            @org=0
            cC00000,1
            @org
             C00001,1
        """
        exp_skool = """
            @org=0
            c00000 XOR A
            @org
             00001 RET
        """
        self._test_disassembly(sft, exp_skool, snapshot)

    def test_asm_directive_rem(self):
        snapshot = [201]
        sft = """
            @rem=This is where it starts
            cC00000,1
        """
        exp_skool = """
            @rem=This is where it starts
            c00000 RET
        """
        self._test_disassembly(sft, exp_skool, snapshot)

    def test_asm_directive_remote(self):
        snapshot = [201]
        sft = """
            @remote=save:64000
            cC00000,1
        """
        exp_skool = """
            @remote=save:64000
            c00000 RET
        """
        self._test_disassembly(sft, exp_skool, snapshot)

    def test_asm_directive_replace(self):
        snapshot = [127, 32, 49, 57, 56, 52]
        sft = """
            @replace=/#copy/#CHR169
            ; Message
            tT00000,B1:5;25 #copy 1984
        """
        exp_skool = """
            @replace=/#copy/#CHR169
            ; Message
            t00000 DEFM 127," 1984"  ; #copy 1984
        """
        self._test_disassembly(sft, exp_skool, snapshot)

    def test_asm_directive_rfix(self):
        snapshot = [46, 0]
        sft = """
            @rfix=LD HL,0
            cC00000,2
        """
        exp_skool = """
            @rfix=LD HL,0
            c00000 LD L,0
        """
        self._test_disassembly(sft, exp_skool, snapshot)

    def test_asm_directive_rfix_block(self):
        snapshot = [14, 0]
        sft = """
            @rfix+begin
            c00000 LD BC,0
            @rfix-else
            cC00000,2
            @rfix-end
        """
        exp_skool = """
            @rfix+begin
            c00000 LD BC,0
            @rfix-else
            c00000 LD C,0
            @rfix-end
        """
        self._test_disassembly(sft, exp_skool, snapshot)

    def test_asm_directive_rsub(self):
        snapshot = [14, 0]
        sft = """
            @rsub=LD BC,0
            cC00000,2
        """
        exp_skool = """
            @rsub=LD BC,0
            c00000 LD C,0
        """
        self._test_disassembly(sft, exp_skool, snapshot)

    def test_asm_directive_rsub_block(self):
        snapshot = [14, 0]
        sft = """
            @rsub-begin
            cC00000,2
            @rsub+else
            c00000 LD BC,0
            @rsub+end
        """
        exp_skool = """
            @rsub-begin
            c00000 LD C,0
            @rsub+else
            c00000 LD BC,0
            @rsub+end
        """
        self._test_disassembly(sft, exp_skool, snapshot)

    def test_asm_directive_set(self):
        snapshot = [201]
        sft = """
            @set-bullet=.
            @set-comment-width-min=13
            @set-crlf=1
            @set-handle-unsupported-macros=1
            @set-indent=3
            @set-instruction-width=30
            @set-label-colons=0
            @set-line-width=119
            @set-tab=1
            @set-warnings=0
            @set-wrap-column-width-min=15
            cC00000,1
        """
        exp_skool = """
            @set-bullet=.
            @set-comment-width-min=13
            @set-crlf=1
            @set-handle-unsupported-macros=1
            @set-indent=3
            @set-instruction-width=30
            @set-label-colons=0
            @set-line-width=119
            @set-tab=1
            @set-warnings=0
            @set-wrap-column-width-min=15
            c00000 RET
        """
        self._test_disassembly(sft, exp_skool, snapshot)

    def test_asm_directive_ssub(self):
        snapshot = [14, 0]
        sft = """
            @ssub=LD B,0
            cC00000,2
        """
        exp_skool = """
            @ssub=LD B,0
            c00000 LD C,0
        """
        self._test_disassembly(sft, exp_skool, snapshot)

    def test_asm_directive_ssub_block(self):
        snapshot = [14, 0]
        sft = """
            @ssub+begin
            c00000 LD C,1
            @ssub-else
            cC00000,2
            @ssub-end
        """
        exp_skool = """
            @ssub+begin
            c00000 LD C,1
            @ssub-else
            c00000 LD C,0
            @ssub-end
        """
        self._test_disassembly(sft, exp_skool, snapshot)

    def test_asm_directive_start(self):
        snapshot = [201]
        sft = """
            @start
            cC00000,1
        """
        exp_skool = """
            @start
            c00000 RET
        """
        self._test_disassembly(sft, exp_skool, snapshot)

    def test_asm_directive_writer(self):
        snapshot = [201]
        sft = """
            @writer=:game.GameAsmWriter
            cC00000,1
        """
        exp_skool = """
            @writer=:game.GameAsmWriter
            c00000 RET
        """
        self._test_disassembly(sft, exp_skool, snapshot)

    def test_i_block_with_no_instructions(self):
        sft = 'iI65500'
        exp_skool = 'i65500'
        self._test_disassembly(sft, exp_skool)

    def test_i_block_with_no_instructions_and_a_comment(self):
        sft = 'iI65500;7 Ignored'
        exp_skool = 'i65500 ; Ignored'
        self._test_disassembly(sft, exp_skool)

    def test_i_block_with_one_instruction(self):
        snapshot = [0] * 3
        sft = 'iS00000,1'
        exp_skool = 'i00000 DEFS 1'
        self._test_disassembly(sft, exp_skool, snapshot)

    def test_i_block_with_one_instruction_and_a_comment(self):
        snapshot = [0] * 3
        sft = 'iS00000,1;14 Ignored'
        exp_skool = 'i00000 DEFS 1 ; Ignored'
        self._test_disassembly(sft, exp_skool, snapshot)

    def test_i_block_with_two_instructions(self):
        snapshot = [0] * 3
        sft = """
            iW00000,2
             S00002,1
        """
        exp_skool = """
            i00000 DEFW 0
             00002 DEFS 1
        """
        self._test_disassembly(sft, exp_skool, snapshot)
