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
@label=START
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
@rsub+else
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
@label=START
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
@rsub+else
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
@label=START
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
@rsub+else
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
    def _parse_sft(self, sft, snapshot=(), asm_hex=False, asm_lower=False, min_address=0, max_address=65536):
        sftfile = self.write_text_file(sft, suffix='.sft')
        writer = SftParser(snapshot[:], sftfile, asm_hex=asm_hex, asm_lower=asm_lower)
        writer.write_skool(min_address, max_address)
        return writer.snapshot, self.out.getvalue().split('\n')

    def _test_disassembly(self, sft, exp_skool, snapshot=(), asm_hex=False, asm_lower=False, min_address=0, max_address=65536):
        skool = self._parse_sft(sft, snapshot, asm_hex, asm_lower, min_address, max_address)[1][:-1]
        self.assertEqual(exp_skool, skool)

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

    def test_data_definition_entry(self):
        skool = '\n'.join((
            'd00000 DEFB 5,"a,b",6',
            ' 00005 DEFM "a;b"',
            ' 00008 DEFW 28527',
            ' 00010 DEFS 2,255',
        ))
        end = 12
        snapshot, skool = self._parse_sft(skool, [0] * end)
        exp_data = [5, 97, 44, 98, 6, 97, 59, 98, 111, 111, 255, 255]
        self.assertEqual(exp_data, snapshot[0:end])

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
        self._test_disassembly(sft, exp_skool, snapshot)

    def test_byte_formats_hex(self):
        snapshot = [170] * 4
        sft = 'bB00000,b1:d1:h1:1'
        exp_skool = ['b$0000 DEFB %10101010,170,$AA,$AA']
        self._test_disassembly(sft, exp_skool, snapshot, asm_hex=True)

    def test_word_formats(self):
        snapshot = [205, 85] * 20 + [32, 0] * 2
        sft = '\n'.join((
            'wW00000,4',
            ' W00004,b4',
            ' W00008,d4',
            ' W00012,h4',
            ' W00016,2,d2,h4',
            ' W00024,b4:2:h2',
            ' W00032,b2,4,h2',
            ' W00040,c2:2'
        ))
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
            ' 00038 DEFW $55CD',
            ' 00040 DEFW " ",32'
        ]
        self._test_disassembly(sft, exp_skool, snapshot)

    def test_word_formats_hex(self):
        snapshot = [170] * 8
        sft = 'wW00000,b2,d2,h2,2'
        exp_skool = [
            'w$0000 DEFW %1010101010101010',
            ' $0002 DEFW 43690',
            ' $0004 DEFW $AAAA',
            ' $0006 DEFW $AAAA'
        ]
        self._test_disassembly(sft, exp_skool, snapshot, asm_hex=True)

    def test_s_directives(self):
        sft = '\n'.join((
            'sS00000,1,b2,d3,h4',
            ' S00010,b10,d10,h10',
            ' S00040,10',
            ' S00050,b300,d300,h300',
            ' S00950,10:c",",10:c";",30:c"&"',
            ' S01000,5:c"*"*2,10:c" ",15:c":"',
            ' S01035,4:c"\\"",6:c"\\\\"'
        ))
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
            ' 00650 DEFS $012C',
            ' 00950 DEFS 10,","',
            ' 00960 DEFS 10,";"',
            ' 00970 DEFS 30,"&"',
            ' 01000 DEFS 5,"*"',
            ' 01005 DEFS 5,"*"',
            ' 01010 DEFS 10," "',
            ' 01020 DEFS 15,":"',
            ' 01035 DEFS 4,"\\""',
            ' 01039 DEFS 6,"\\\\"'
        ]
        self._test_disassembly(sft, exp_skool)

    def test_s_directives_hex(self):
        sft = 'sS00000,b10,d10,h10,10'
        exp_skool = [
            's$0000 DEFS %00001010',
            ' $000A DEFS 10',
            ' $0014 DEFS $0A',
            ' $001E DEFS $0A'
        ]
        self._test_disassembly(sft, exp_skool, asm_hex=True)

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
        sft = '\n'.join((
            'cC00000,b6',
            ' C00006,d6,h8',
            ' C00020,n6',
            ' C00026,bn6',
            ' C00032,nb6,bd4,hb6',
        ))
        exp_skool = [
            'c00000 LD A,%00000101',
            ' 00002 LD B,%00000110',
            ' 00004 LD C,%00000111',
            ' 00006 LD D,240',
            ' 00008 LD E,128',
            ' 00010 LD H,200',
            ' 00012 LD L,$64',
            ' 00014 LD IXh,$01',
            ' 00017 LD IXl,$02',
            ' 00020 LD IYh,3',
            ' 00023 LD IYl,4',
            ' 00026 LD (HL),%00011011',
            ' 00028 ADD A,%00100000',
            ' 00030 ADC A,%00100001',
            ' 00032 AND 34',
            ' 00034 CP 35',
            ' 00036 IN A,(254)',
            ' 00038 OR %00100100',
            ' 00040 OUT (%11111110),A',
            ' 00042 SBC A,$25',
            ' 00044 SUB $26',
            ' 00046 XOR $27',
        ]
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
        sft = '\n'.join((
            'cC00000,n6',
            ' C00006,h6,b6,d6',
            ' C00024,hn6',
            ' C00030,bn6',
            ' C00036,dn8',
            ' C00044,nn8',
            ' C00052,hd8,bd8,dd8,nd4',
        ))
        exp_skool = [
            'c$0000 LD A,(IX+$0F)',
            ' $0003 LD (IY-$17),B',
            ' $0006 ADC A,(IX-$0D)',
            ' $0009 ADD A,(IY+$78)',
            ' $000C SBC A,(IX+%00101111)',
            ' $000F AND (IY-%00000101)',
            ' $0012 CP (IX-19)',
            ' $0015 OR (IY+102)',
            ' $0018 SUB (IX+$63)',
            ' $001B XOR (IY-$3F)',
            ' $001E DEC (IX-%00011100)',
            ' $0021 INC (IY+%00000111)',
            ' $0024 RL (IX+77)',
            ' $0028 RLC (IY-92)',
            ' $002C RR (IX-$12)',
            ' $0030 RRC (IY+$37)',
            ' $0034 SLA (IX+$1A)',
            ' $0038 SLL (IY-$62)',
            ' $003C SRA (IX-%00000011)',
            ' $0040 SRL (IY+%00010011)',
            ' $0044 BIT 0,(IX+33)',
            ' $0048 RES 1,(IY-81)',
            ' $004C SET 2,(IX-$40)',
        ]
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
        sft = '\n'.join((
            'cC00000,b4',
            ' C00004,n4',
            ' C00008,h4,d4',
            ' C00016,hb4',
            ' C00020,hn4',
            ' C00024,nh4,hh4',
        ))
        exp_skool = [
            'c00000 LD (IX+%00101101),%01010111',
            ' 00004 LD (IY+54),78',
            ' 00008 LD (IX-$02),$EA',
            ' 00012 LD (IY-107),19',
            ' 00016 LD (IX+$0D),%11111111',
            ' 00020 LD (IY+$24),109',
            ' 00024 LD (IX-62),$6F',
            ' 00028 LD (IY-$49),$C7',
        ]
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
        sft = '\n'.join((
            'cC00000,h2',
            ' C00002,b2,d2,n2',
            ' C00008,dh2',
            ' C00010,hd2',
            ' C00012,dn2,nd2,bb2,nn2',
        ))
        exp_skool = [
            'c$0000 DJNZ $0000',
            ' $0002 JR %0000000000000100',
            ' $0004 JR NZ,2',
            ' $0006 JR NZ,$000A',
            ' $0008 JR Z,12',
            ' $000A JR NC,$0006',
            ' $000C JR C,8',
            ' $000E DJNZ $000C',
            ' $0010 JR %0000000000001110',
            ' $0012 JR NZ,$0012',
        ]
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
        sft = '\n'.join((
            'cC00000,h1',
            ' C00001,n1',
            ' C00002,d1,b1,dn1,nd1,b1'
        ))
        exp_skool = [
            'c$0000 RST $00',
            ' $0001 RST $08',
            ' $0002 RST 16',
            ' $0003 RST %00011000',
            ' $0004 RST 32',
            ' $0005 RST $28',
            ' $0006 RST %00110000',
        ]
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
        sft = '\n'.join((
            'cC00000,n9',
            ' C00009,d11',
            ' C00020,b11,h11,dn7',
            ' C00049,nd8',
            ' C00057,dh7',
            ' C00064,hd8',
            ' C00072,db6',
            ' C00078,bd6,hb6,bh6,dd6',
            ' C00102,hh6',
            ' C00108,bb6',
            ' C00114,nn12',
        ))
        exp_skool = [
            'c$0000 LD BC,$0001',
            ' $0003 LD DE,$000C',
            ' $0006 LD HL,$007B',
            ' $0009 LD SP,1234',
            ' $000C LD IX,12345',
            ' $0010 LD IY,23456',
            ' $0014 LD A,(%1000011100000111)',
            ' $0017 LD BC,(%1011001001101110)',
            ' $001B LD DE,(%1101110111010101)',
            ' $001F LD HL,($FF98)',
            ' $0022 LD SP,($D431)',
            ' $0026 LD IX,($A8CA)',
            ' $002A LD IY,(32109)',
            ' $002E LD (21098),A',
            ' $0031 LD ($2AEB),BC',
            ' $0035 LD ($2694),DE',
            ' $0039 LD (8765),HL',
            ' $003C LD (7654),SP',
            ' $0040 LD ($FF98),IX',
            ' $0044 LD ($0001),IY',
            ' $0048 CALL 11',
            ' $004B JP 111',
            ' $004E CALL NZ,%0000010001010111',
            ' $0051 CALL Z,%0010101101100111',
            ' $0054 CALL NC,$2B68',
            ' $0057 CALL C,$2B72',
            ' $005A CALL PO,%0010101111010110',
            ' $005D CALL PE,%0010111110111110',
            ' $0060 CALL P,22222',
            ' $0063 CALL M,22223',
            ' $0066 JP NZ,$56D9',
            ' $0069 JP Z,$573D',
            ' $006C JP NC,%0101101100100101',
            ' $006F JP C,%1000001000110101',
            ' $0072 JP PO,$8236',
            ' $0075 JP PE,$8240',
            ' $0078 JP P,$82A4',
            ' $007B JP M,$868C',
        ]
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
        exp_skool = [
            'c00000 LD A,"\\""',
            ' 00002 ADD A,"\\\\"',
            ' 00004 SUB "!"',
            ' 00006 CP "?"',
            ' 00008 LD (HL),"A"',
            ' 00010 LD (IX+2),"B"',
            ' 00014 LD HL,"C"',
            ' 00017 LD B,31',
            ' 00019 LD C,94',
            ' 00021 LD D,96',
            ' 00023 LD E,128',
            ' 00025 LD BC,256',
        ]
        self._test_disassembly(sft, exp_skool, snapshot)

    def test_max_address_at_mid_block_comment(self):
        snapshot = [
            120, # 00000 LD A,B
            201, # 00001 RET
        ]
        sft = '\n'.join((
            '; Routine',
            'cC00000,1;15 We are only interested',
            ' ;15 in this instruction',
            '; This comment is past the end address.',
            ' C00001,1;15 And so is this instruction',
        ))
        exp_skool = [
            '; Routine',
            'c00000 LD A,B  ; We are only interested',
            '               ; in this instruction',
        ]
        self._test_disassembly(sft, exp_skool, snapshot, max_address=1)

    def test_max_address_after_block_end_comment(self):
        snapshot = [
            120, # 00000 LD A,B
            201, # 00001 RET
        ]
        sft = '\n'.join((
            '; We are only interested in this entry',
            'cC00000,1',
            '; The only interesting entry ends here.',
            '',
            '; This entry is of no interest',
            'cC00001,1',
        ))
        exp_skool = [
            '; We are only interested in this entry',
            'c00000 LD A,B',
            '; The only interesting entry ends here.',
            '',
        ]
        self._test_disassembly(sft, exp_skool, snapshot, max_address=1)

    def test_max_address_between_two_directives(self):
        snapshot = [0] * 4
        sft = '\n'.join((
            '; Data at 0',
            'bB00000,1*2',
            '',
            '; Data at 2',
            'bB00002,1',
        ))
        exp_skool = [
            '; Data at 0',
            'b00000 DEFB 0',
        ]
        self._test_disassembly(sft, exp_skool, snapshot, max_address=1)

    def test_max_address_after_asm_block_directive(self):
        snapshot = [0] * 3
        sft = '\n'.join((
            'bB00000,1',
            '@isub-begin',
            ' B00001,1',
            '@isub+else',
            '       DEFB 1',
            '@isub+end',
            ' B00002,1',
        ))
        exp_skool = [
            'b00000 DEFB 0',
            '@isub-begin',
            ' 00001 DEFB 0',
            '@isub+else',
            '       DEFB 1',
            '@isub+end',
        ]
        self._test_disassembly(sft, exp_skool, snapshot, max_address=2)

    def test_max_address_gives_no_content(self):
        snapshot = [0] * 3
        sft = 'bB00001,1*2'
        exp_skool = []
        self._test_disassembly(sft, exp_skool, snapshot, max_address=1)

    def test_min_address_at_first_instruction_in_entry(self):
        snapshot = [0] * 4
        sft = '\n'.join((
            '; Data at 0',
            'bB00000,1',
            '',
            '; Data at 1',
            'bB00001,1*2',
            '',
            '; Data at 3',
            'bB00003,1',
        ))
        exp_skool = [
            '; Data at 1',
            'b00001 DEFB 0',
            ' 00002 DEFB 0',
            '',
            '; Data at 3',
            'b00003 DEFB 0',
        ]
        self._test_disassembly(sft, exp_skool, snapshot, min_address=1)

    def test_min_address_at_second_instruction_in_entry(self):
        snapshot = [0] * 5
        sft = '\n'.join((
            '; Data at 0',
            'bB00000,1',
            '',
            '; Data at 1',
            'bB00001,1',
            ' W00002,2',
            '',
            '; Data at 4',
            'bB00004,1',
        ))
        exp_skool = [
            '; Data at 4',
            'b00004 DEFB 0',
        ]
        self._test_disassembly(sft, exp_skool, snapshot, min_address=2)

    def test_min_address_between_two_directives(self):
        snapshot = [0] * 4
        sft = '\n'.join((
            '; Data at 0',
            'bB00000,1',
            '',
            '; Data at 1',
            'bB00001,1*2',
            '',
            '; Data at 3',
            'bB00003,1',
        ))
        exp_skool = [
            '; Data at 3',
            'b00003 DEFB 0',
        ]
        self._test_disassembly(sft, exp_skool, snapshot, min_address=2)

    def test_min_address_and_max_address(self):
        snapshot = [0] * 4
        sft = '\n'.join((
            '; Data at 0',
            'bB00000,1',
            '',
            '; Data at 1',
            'bB00001,1',
            '',
            '; Data at 2',
            'bB00002,1',
            '; Mid-block comment at 3.',
            ' B00003,1',
        ))
        exp_skool = [
            '; Data at 1',
            'b00001 DEFB 0',
            '',
            '; Data at 2',
            'b00002 DEFB 0',
        ]
        self._test_disassembly(sft, exp_skool, snapshot, min_address=1, max_address=3)

    def test_min_address_and_max_address_give_no_content(self):
        snapshot = [0] * 4
        sft = '\n'.join((
            '; Data at 0',
            'bB00000,1',
            '',
            '; Data at 1',
            'bB00001,1*2',
            '',
            '; Data at 3',
            'bB00003,1',
        ))
        exp_skool = []
        self._test_disassembly(sft, exp_skool, snapshot, min_address=2, max_address=3)

if __name__ == '__main__':
    unittest.main()
