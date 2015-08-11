# -*- coding: utf-8 -*-
import re
import unittest

from skoolkittest import SkoolKitTestCase
from skoolkit import SkoolKitError
from skoolkit.snaskool import Disassembly, SkoolWriter, write_ctl
from skoolkit.ctlparser import CtlParser

DISASSEMBLY_SNAPSHOT = [0] * 65536
DISASSEMBLY_SNAPSHOT[32768:32776] = [
    175,        # 32768 XOR A
    201,        # 32769 RET
    72, 105,    # 32770 DEFM "Hi"
    76, 111,    # 32772 DEFM "Lo"
    89, 111     # 32774 DEFM "Yo"
]
DISASSEMBLY_SNAPSHOT[32814:32841] = [
    195, 0, 128,      # 32814 JP 32768
    72, 105, 1, 2, 3, # 32817 DEFM "Hi",1,2,3
    4, 5, 76, 111, 6, # 32822 DEFB 4,5,"Lo",6
    97, 98, 1,        # 32827 DEFM "ab',1
    99, 100, 2,       # 32830 DEFM "cd",2
    101, 3,           # 32833 DEFM "e",3
    102, 4,           # 32835 DEFM "f",4
    62, 38,           # 32837 LD A,"&"
    6, 1              # 32839 LD B,%00000001
]

DISASSEMBLY_CTL = """@ 32768 start
@ 32768 writer=skoolkit.game.GameAsmWriter
@ 32768 org=32768
@ 32768 label=START
; Entry #1
c 32768
D 32768 Routine description paragraph 1.
D 32768 Routine description paragraph 2.
R 32768 A Some value
R 32768 B Some other value
  32768,2 This is an instruction-level comment that spans two instructions
E 32768 Routine end comment.
@ 32768 end
; Entry #2
t 32770
T 32770,4,2
; Entry #3
t 32774 Yo
; Entry #4
b 32776
B 32776,6,2 This comment spans three DEFB statements
B 32782,6,3,3 This comment spans two DEFB statements
; Entry #5
b 32788 Important byte
; Entry #6
w 32789
W 32789,4,4
; Entry #7
w 32793 Important word
; Entry #8
g 32795
; Entry #9
g 32796 Important game status buffer byte
; Entry #10
u 32797
; Entry #11
u 32798 Unimportant unused byte
; Entry #12
s 32799
S 32799,10,5
; Entry #13
s 32809 Block of zeroes
M 32809,4 A DEFS and a NOP
C 32812,1
C 32813,1 Another NOP
; Entry #14
c 32814 Refers to the routine at 32768
; Entry #15
b 32817
T 32817,5,2:B3
B 32822,5,2:T2,1 This comment spans two DEFB statements
T 32827,,2:B1*2,1:B1 This comment spans four DEFM statements
; Entry 16
c 32837
  32837,,c2,b2 This comment spans two instructions with different operand bases
; Entry 17
i 32841
"""

WRITER_SNAPSHOT = [0] * 65536
WRITER_SNAPSHOT[32768:32781] = [
    175,     # 32768 XOR A
    201,     # 32769 RET
    167,     # 32770 AND A
    201,     # 32771 RET
    0,
    39,      # 32773 DAA
    201,     # 32774 RET
    32, 252, # 32775 JR NZ,32773
    24, 251, # 32777 JR 32774
    24, 248  # 32779 JR 32773
]

WRITER_CTL = """@ 32768 start
@ 32768 writer=skoolkit.game.GameAsmWriter
@ 32768 set-tab=1
@ 32768 org=32768
@ 32768 label=START
c 32768
D 32768 Routine description paragraph 1.
D 32768 Routine description paragraph 2.
R 32768 A Some value
R 32768 B Some other value
  32768,2 This is an instruction-level comment that spans two instructions and is too long to fit on two lines, so extends to three
E 32768 Routine end comment.
@ 32768 end
c 32770 Routine with registers but no description
R 32770 HL Some value
R 32770 BC Some other value
C 32770,2 One-line multi-instruction comment
i 32772 Ignore block with a title
c 32773 Routine with referrers
c 32775 Routine that refers to the routine at 32773
c 32779 Another routine that refers to the routine at 32773
b 32781
D 32781 #TABLE { A1 | B1 } { A2 | B2 } TABLE#
D 32781 Intro text: #TABLE { A1 } { A2 } TABLE# Outro text.
D 32781 #UDGTABLE { #SCR } TABLE#
D 32781 This is a screenshot: #UDGTABLE { #SCR } UDGTABLE# Isn't it nice?
D 32781 #LIST { Item 1 } { Item 2 } LIST#
D 32781 List intro text: #LIST { Item } LIST#
i 32782 Final ignore block
"""

SKOOL = """@start
@writer=skoolkit.game.GameAsmWriter
@set-tab=1
@org=32768
; Routine at 32768
;
; Routine description paragraph 1.
; .
; Routine description paragraph 2.
;
; A Some value
; B Some other value
@label=START
c32768 XOR A         ; {This is an instruction-level comment that spans two
 32769 RET           ; instructions and is too long to fit on two lines, so
                     ; extends to three}
; Routine end comment.
@end

; Routine with registers but no description
;
; .
;
; HL Some value
; BC Some other value
c32770 AND A         ; {One-line multi-instruction comment
 32771 RET           ; }

; Ignore block with a title
i32772

; Routine with referrers
;
; Used by the routines at #R32775 and #R32779.
c32773 DAA           ;
; This entry point is used by the routine at #R32775.
*32774 RET           ;

; Routine that refers to the routine at 32773
c32775 JR NZ,32773   ;
 32777 JR 32774      ;

; Another routine that refers to the routine at 32773
c32779 JR 32773      ;

; Data block at 32781
;
; #TABLE
; { A1 | B1 }
; { A2 | B2 }
; TABLE#
; .
; Intro text:
; #TABLE
; { A1 }
; { A2 }
; TABLE#
; Outro text.
; .
; #UDGTABLE
; { #SCR }
; TABLE#
; .
; This is a screenshot:
; #UDGTABLE
; { #SCR }
; UDGTABLE#
; Isn't it nice?
; .
; #LIST
; { Item 1 }
; { Item 2 }
; LIST#
; .
; List intro text:
; #LIST
; { Item }
; LIST#
b32781 DEFB 0
""".split('\n')

class DisassemblyTest(SkoolKitTestCase):
    def _test_disassembly(self, snapshot, ctl, exp_instructions, **kwargs):
        ctl_parser = CtlParser()
        ctl_parser.parse_ctl(self.write_text_file(ctl))
        disassembly = Disassembly(snapshot, ctl_parser, True, **kwargs)
        entries = disassembly.entries
        self.assertEqual(len(entries), 2)
        entry = entries[0]
        self.assertEqual(entry.address, 0)
        instructions = entry.instructions
        actual_instructions = [(i.address, i.operation) for i in instructions]
        self.assertEqual(exp_instructions, actual_instructions)

    def test_disassembly(self):
        ctl_parser = CtlParser()
        ctl_parser.parse_ctl(self.write_text_file(DISASSEMBLY_CTL))
        disassembly = Disassembly(DISASSEMBLY_SNAPSHOT, ctl_parser, True)

        entries = disassembly.entries
        self.assertEqual(len(entries), 17)

        # Entry #1 (32768)
        entry = entries[0]
        self.assertEqual(entry.address, 32768)
        self.assertEqual(entry.title, 'Routine at 32768')
        self.assertEqual(entry.description, ['Routine description paragraph 1.', 'Routine description paragraph 2.'])
        self.assertEqual(entry.ctl, 'c')
        self.assertEqual(entry.registers, [['A', 'Some value'], ['B', 'Some other value']])
        self.assertEqual(entry.end_comment, ['Routine end comment.'])
        self.assertEqual(entry.start, True)
        self.assertEqual(entry.end, True)
        self.assertEqual(entry.writer, 'skoolkit.game.GameAsmWriter')
        self.assertEqual(entry.org, '32768')

        blocks = entry.blocks
        self.assertEqual(len(blocks), 1)
        block = blocks[0]
        self.assertEqual(block.header, ())
        self.assertEqual(block.comment, 'This is an instruction-level comment that spans two instructions')
        self.assertEqual(block.instructions, entry.instructions)
        self.assertEqual(block.end, 32770)

        instructions = entry.instructions
        self.assertEqual(len(instructions), 2)
        instruction = instructions[0]
        self.assertEqual(instruction.address, 32768)
        self.assertEqual(instruction.operation, 'XOR A')
        self.assertEqual(instruction.bytes, [175])
        self.assertEqual(instruction.referrers, [entries[13]])
        self.assertEqual(instruction.entry, entry)
        self.assertEqual(instruction.ctl, 'c')
        self.assertEqual(instruction.comment, None)
        self.assertEqual(instruction.asm_directives, [('label', 'START')])

        # Entry #2 (32770)
        entry = entries[1]
        self.assertEqual(entry.address, 32770)
        self.assertEqual(entry.title, 'Message at {0}'.format(entry.address))
        instructions = entry.instructions
        self.assertEqual(len(instructions), 2)
        self.assertEqual(instructions[0].operation, 'DEFM "Hi"')
        self.assertEqual(instructions[1].operation, 'DEFM "Lo"')

        # Entry #3 (32774)
        entry = entries[2]
        self.assertEqual(entry.address, 32774)
        self.assertEqual(entry.title, 'Yo')

        # Entry #4 (32776)
        entry = entries[3]
        self.assertEqual(entry.address, 32776)
        self.assertEqual(entry.title, 'Data block at {0}'.format(entry.address))
        instructions = entry.instructions
        self.assertEqual(len(instructions), 5)
        self.assertEqual(instructions[0].operation, 'DEFB 0,0')
        self.assertEqual(instructions[1].operation, 'DEFB 0,0')
        self.assertEqual(instructions[2].operation, 'DEFB 0,0')
        self.assertEqual(instructions[3].operation, 'DEFB 0,0,0')
        self.assertEqual(instructions[4].operation, 'DEFB 0,0,0')
        blocks = entry.blocks
        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0].comment, 'This comment spans three DEFB statements')
        self.assertEqual(instructions[:3], blocks[0].instructions)
        self.assertEqual(blocks[1].comment, 'This comment spans two DEFB statements')
        self.assertEqual(instructions[3:], blocks[1].instructions)

        # Entry #5 (32788)
        entry = entries[4]
        self.assertEqual(entry.address, 32788)
        self.assertEqual(entry.title, 'Important byte')

        # Entry #6 (32789)
        entry = entries[5]
        self.assertEqual(entry.address, 32789)
        self.assertEqual(entry.title, 'Data block at {0}'.format(entry.address))
        instructions = entry.instructions
        self.assertEqual(len(instructions), 1)
        self.assertEqual(instructions[0].operation, 'DEFW 0,0')

        # Entry #7 (32793)
        entry = entries[6]
        self.assertEqual(entry.address, 32793)
        self.assertEqual(entry.title, 'Important word')

        # Entry #8 (32795)
        entry = entries[7]
        self.assertEqual(entry.address, 32795)
        self.assertEqual(entry.title, 'Game status buffer entry at {0}'.format(entry.address))

        # Entry #9 (32796)
        entry = entries[8]
        self.assertEqual(entry.address, 32796)
        self.assertEqual(entry.title, 'Important game status buffer byte')

        # Entry #10 (32797)
        entry = entries[9]
        self.assertEqual(entry.address, 32797)
        self.assertEqual(entry.title, 'Unused')

        # Entry #11 (32798)
        entry = entries[10]
        self.assertEqual(entry.address, 32798)
        self.assertEqual(entry.title, 'Unimportant unused byte')

        # Entry #12 (32799)
        entry = entries[11]
        self.assertEqual(entry.address, 32799)
        self.assertEqual(entry.title, 'Unused')
        instructions = entry.instructions
        self.assertEqual(len(instructions), 2)
        self.assertEqual(instructions[0].operation, 'DEFS 5')
        self.assertEqual(instructions[1].operation, 'DEFS 5')

        # Entry #13 (32809)
        entry = entries[12]
        self.assertEqual(entry.address, 32809)
        self.assertEqual(entry.title, 'Block of zeroes')
        instructions = entry.instructions
        self.assertEqual(len(instructions), 3)
        self.assertEqual(instructions[0].operation, 'DEFS 3')
        self.assertEqual(instructions[1].operation, 'NOP')
        self.assertEqual(instructions[2].operation, 'NOP')
        blocks = entry.blocks
        self.assertEqual(len(blocks), 2)
        block1 = blocks[0]
        self.assertEqual(block1.start, 32809)
        self.assertEqual(block1.end, 32813)
        self.assertEqual(instructions[:2], block1.instructions)
        self.assertEqual(block1.comment, 'A DEFS and a NOP')
        block2 = blocks[1]
        self.assertEqual(block2.start, block1.end)
        self.assertEqual(block2.end, 32814)
        self.assertEqual(instructions[2:], block2.instructions)
        self.assertEqual(block2.comment, 'Another NOP')

        # Entry #14 (32814)
        entry = entries[13]
        self.assertEqual(entry.address, 32814)
        self.assertEqual(entry.title, 'Refers to the routine at 32768')

        # Entry #15 (32817)
        entry = entries[14]
        self.assertEqual(entry.address, 32817)
        instructions = entry.instructions
        self.assertEqual(len(instructions), 7)
        self.assertEqual(instructions[0].operation, 'DEFM "Hi",1,2,3')
        self.assertEqual(instructions[1].operation, 'DEFB 4,5,"Lo"')
        self.assertEqual(instructions[2].operation, 'DEFB 6')
        self.assertEqual(instructions[3].operation, 'DEFM "ab",1')
        self.assertEqual(instructions[4].operation, 'DEFM "cd",2')
        self.assertEqual(instructions[5].operation, 'DEFM "e",3')
        self.assertEqual(instructions[6].operation, 'DEFM "f",4')
        blocks = entry.blocks
        self.assertEqual(len(blocks), 3)
        block1 = blocks[0]
        self.assertEqual(block1.start, 32817)
        self.assertEqual(block1.end, 32822)
        self.assertEqual(block1.comment, '')
        self.assertEqual(instructions[:1], block1.instructions)
        block2 = blocks[1]
        self.assertEqual(block2.start, block1.end)
        self.assertEqual(block2.end, 32827)
        self.assertEqual(block2.comment, 'This comment spans two DEFB statements')
        self.assertEqual(instructions[1:3], block2.instructions)
        block3 = blocks[2]
        self.assertEqual(block3.start, block2.end)
        self.assertEqual(block3.end, 32837)
        self.assertEqual(block3.comment, 'This comment spans four DEFM statements')
        self.assertEqual(instructions[3:], block3.instructions)

        # Entry #16 (32837)
        entry = entries[15]
        self.assertEqual(entry.address, 32837)
        instructions = entry.instructions
        self.assertEqual(len(instructions), 2)
        self.assertEqual(instructions[0].operation, 'LD A,"&"')
        self.assertEqual(instructions[1].operation, 'LD B,%00000001')
        blocks = entry.blocks
        self.assertEqual(len(blocks), 1)
        block1 = blocks[0]
        self.assertEqual(block1.start, 32837)
        self.assertEqual(block1.end, 32841)
        self.assertEqual(block1.comment, 'This comment spans two instructions with different operand bases')
        self.assertEqual(instructions, block1.instructions)

        # Entry #17 (32841)
        entry = entries[16]
        self.assertEqual(entry.address, 32841)

    def test_referrers(self):
        snapshot = [
            201,       # 00000 RET
            199,       # 00001 RST 0
            16, 252,   # 00002 DJNZ 0
            24, 250,   # 00004 JR 0
            32, 248,   # 00006 JR NZ,0
            40, 246,   # 00008 JR Z,0
            48, 244,   # 00010 JR NC,0
            56, 242,   # 00012 JR C,0
            196, 0, 0, # 00014 CALL NZ,0
            204, 0, 0, # 00017 CALL Z,0
            205, 0, 0, # 00020 CALL 0
            212, 0, 0, # 00023 CALL NC,0
            220, 0, 0, # 00026 CALL C,0
            228, 0, 0, # 00029 CALL PO,0
            236, 0, 0, # 00032 CALL PE,0
            244, 0, 0, # 00035 CALL P,0
            252, 0, 0, # 00038 CALL M,0
            194, 0, 0, # 00041 JP NZ,0
            195, 0, 0, # 00044 JP 0
            202, 0, 0, # 00047 JP Z,0
            210, 0, 0, # 00050 JP NC,0
            218, 0, 0, # 00053 JP C,0
            226, 0, 0, # 00056 JP PO,0
            234, 0, 0, # 00059 JP PE,0
            242, 0, 0, # 00062 JP P,0
            250, 0, 0  # 00065 JP M,0
        ]
        exp_ref_addresses = [1] + list(range(2, 14, 2)) + list(range(14, 68, 3))
        ctls = ['c 00000'] + ['c {:05d}'.format(a) for a in exp_ref_addresses] + ['i 00068']
        ctl_parser = CtlParser()
        ctl_parser.parse_ctl(self.write_text_file('\n'.join(ctls)))
        disassembly = Disassembly(snapshot, ctl_parser, True)

        referrers = disassembly.entries[0].instructions[0].referrers
        ref_addresses = set([entry.address for entry in referrers])
        self.assertEqual(set(exp_ref_addresses), ref_addresses)

    def test_byte_formats(self):
        snapshot = [42] * 75
        ctl = '\n'.join((
            'b 00000',
            '  00000,b5',
            '  00005,b15',
            '  00020,b5,2,d2,h1',
            'B 00025,b5,2:d2:h1',
            '  00030,h10,5:d3:b2',
            'B 00040,5,b1,h2',
            '  00045,5,h1,T4',
            '  00050,5,b2:T3',
            'T 00055,5,h2,3',
            'T 00060,5,2:d3',
            'T 00065,5,3,B1',
            'T 00070,5,B2:h3',
            'i 00075'
        ))
        exp_instructions = [
            ( 0, 'DEFB %00101010,%00101010,%00101010,%00101010,%00101010'),
            ( 5, 'DEFB %00101010,%00101010,%00101010,%00101010,%00101010,%00101010,%00101010,%00101010'),
            (13, 'DEFB %00101010,%00101010,%00101010,%00101010,%00101010,%00101010,%00101010'),
            (20, 'DEFB %00101010,%00101010'),
            (22, 'DEFB 42,42'),
            (24, 'DEFB $2A'),
            (25, 'DEFB %00101010,%00101010,42,42,$2A'),
            (30, 'DEFB $2A,$2A,$2A,$2A,$2A,42,42,42,%00101010,%00101010'),
            (40, 'DEFB %00101010'),
            (41, 'DEFB $2A,$2A'),
            (43, 'DEFB $2A,$2A'),
            (45, 'DEFB $2A'),
            (46, 'DEFB "****"'),
            (50, 'DEFB %00101010,%00101010,"***"'),
            (55, 'DEFM $2A,$2A'),
            (57, 'DEFM "***"'),
            (60, 'DEFM "**",42,42,42'),
            (65, 'DEFM "***"'),
            (68, 'DEFM 42'),
            (69, 'DEFM 42'),
            (70, 'DEFM 42,42,$2A,$2A,$2A')
        ]
        self._test_disassembly(snapshot, ctl, exp_instructions)

    def test_byte_formats_hex(self):
        snapshot = [85] * 4
        ctl = '\n'.join((
            'b 00000',
            '  00000,4,b1:d1:h1:1',
            'i 00004'
        ))
        exp_instructions = [(0, 'DEFB %01010101,85,$55,$55')]
        self._test_disassembly(snapshot, ctl, exp_instructions, asm_hex=True)

    def test_word_formats(self):
        snapshot = [170, 53] * 32 + [33, 0] * 2
        ctl = '\n'.join((
            'w 00000',
            '  00000,4',
            '  00004,b4',
            '  00008,d4',
            'W 00012,h4',
            'W 00016,b8,2,d2,h4',
            '  00024,d8,b4:2:h2',
            '  00032,h8,b2:d4:2',
            '  00040,8,b2,4,h2',
            'W 00048,8,b2:2:h4',
            '  00056,8,4',
            '  00064,4,c2:2',
            'i 00068'
        ))
        exp_instructions = [
            ( 0, 'DEFW 13738'),
            ( 2, 'DEFW 13738'),
            ( 4, 'DEFW %0011010110101010'),
            ( 6, 'DEFW %0011010110101010'),
            ( 8, 'DEFW 13738'),
            (10, 'DEFW 13738'),
            (12, 'DEFW $35AA'),
            (14, 'DEFW $35AA'),
            (16, 'DEFW %0011010110101010'),
            (18, 'DEFW 13738'),
            (20, 'DEFW $35AA,$35AA'),
            (24, 'DEFW %0011010110101010,%0011010110101010,13738,$35AA'),
            (32, 'DEFW %0011010110101010,13738,13738,$35AA'),
            (40, 'DEFW %0011010110101010'),
            (42, 'DEFW 13738,13738'),
            (46, 'DEFW $35AA'),
            (48, 'DEFW %0011010110101010,13738,$35AA,$35AA'),
            (56, 'DEFW 13738,13738'),
            (60, 'DEFW 13738,13738'),
            (64, 'DEFW "!",33')
        ]
        self._test_disassembly(snapshot, ctl, exp_instructions)

    def test_word_formats_hex(self):
        snapshot = [240] * 8
        ctl = '\n'.join((
            'w 00000',
            '  00000,8,b2,d2,h2,2',
            'i 00008'
        ))
        exp_instructions = [
            (0, 'DEFW %1111000011110000'),
            (2, 'DEFW 61680'),
            (4, 'DEFW $F0F0'),
            (6, 'DEFW $F0F0')
        ]
        self._test_disassembly(snapshot, ctl, exp_instructions, asm_hex=True)

    def test_s_directives(self):
        snapshot = []
        ctl = '\n'.join((
            's 00000',
            '  00000,4',
            '  00004,b4',
            'S 00008,d4',
            '  00012,h8',
            '  00020,40,b10,10,h10',
            'S 00060,b40,10,d10,h10',
            '  00100,d40,b10,10,h10',
            '  00140,h60,b10,d10,40',
            'S 00200,768,b256,d256,h256',
            '  00968,56,16:b%10101010,40:h17',
            '  01024,32,16:c";",16:c"?"',
            '  01056,8,4:c",",4:c" "',
            '  01064,10,3:c"*"*2,4:c":"',
            '  01074,16,8:c43',
            '  01090,10,4:c"\\"",6:c"\\\\"',
            'i 01100'
        ))
        exp_instructions = [
            (  0, 'DEFS 4'),
            (  4, 'DEFS %00000100'),
            (  8, 'DEFS 4'),
            ( 12, 'DEFS 8'),
            ( 20, 'DEFS %00001010'),
            ( 30, 'DEFS 10'),
            ( 40, 'DEFS $0A'),
            ( 50, 'DEFS $0A'),
            ( 60, 'DEFS %00001010'),
            ( 70, 'DEFS 10'),
            ( 80, 'DEFS $0A'),
            ( 90, 'DEFS $0A'),
            (100, 'DEFS %00001010'),
            (110, 'DEFS 10'),
            (120, 'DEFS $0A'),
            (130, 'DEFS $0A'),
            (140, 'DEFS %00001010'),
            (150, 'DEFS 10'),
            (160, 'DEFS $28'),
            (200, 'DEFS %0000000100000000'),
            (456, 'DEFS 256'),
            (712, 'DEFS $0100'),
            (968, 'DEFS 16,%10101010'),
            (984, 'DEFS 40,$11'),
            (1024, 'DEFS 16,";"'),
            (1040, 'DEFS 16,"?"'),
            (1056, 'DEFS 4,","'),
            (1060, 'DEFS 4," "'),
            (1064, 'DEFS 3,"*"'),
            (1067, 'DEFS 3,"*"'),
            (1070, 'DEFS 4,":"'),
            (1074, 'DEFS 8,"+"'),
            (1082, 'DEFS 8,"+"'),
            (1090, 'DEFS 4,"\\""'),
            (1094, 'DEFS 6,"\\\\"')
        ]
        self._test_disassembly(snapshot, ctl, exp_instructions)

    def test_s_directives_hex(self):
        snapshot = []
        ctl = '\n'.join((
            's 00000',
            '  00000,14,d2:b1,h2:128,h10:2',
            'i 00014'
        ))
        exp_instructions = [
            (0, 'DEFS 2,%00000001'),
            (2, 'DEFS 2,$80'),
            (4, 'DEFS $0A,2')
        ]
        self._test_disassembly(snapshot, ctl, exp_instructions, asm_hex=True)

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
            238, 39     # 00046 XOR 39
        ]
        ctl = '\n'.join((
            'c 00000',
            '  00000,b14,8,h2,4',
            '  00014,,h12,d2',
            '  00028,d',
            '  00032,bd4',
            '  00036,h4',
            '  00040,d4',
            '  00044,n4',
            'i 00048'
        ))
        exp_instructions = [
            (0, 'LD A,%00000101'),
            (2, 'LD B,%00000110'),
            (4, 'LD C,%00000111'),
            (6, 'LD D,%11110000'),
            (8, 'LD E,$80'),
            (10, 'LD H,%11001000'),
            (12, 'LD L,%01100100'),
            (14, 'LD IXh,$01'),
            (17, 'LD IXl,$02'),
            (20, 'LD IYh,$03'),
            (23, 'LD IYl,$04'),
            (26, 'LD (HL),27'),
            (28, 'ADD A,32'),
            (30, 'ADC A,33'),
            (32, 'AND %00100010'),
            (34, 'CP %00100011'),
            (36, 'IN A,($FE)'),
            (38, 'OR $24'),
            (40, 'OUT (254),A'),
            (42, 'SBC A,37'),
            (44, 'SUB $26'),
            (46, 'XOR $27')
        ]
        self._test_disassembly(snapshot, ctl, exp_instructions, asm_hex=True)

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
        ctl = '\n'.join((
            'c 00000',
            '  00000,h,3,d3',
            '  00009,b9,3,d3,3',
            '  00018,,3,d6',
            '  00027,h6',
            '  00033,b7',
            '  00040,d12',
            '  00052,bn',
            '  00060,nb',
            '  00068,dn8',
            '  00076,nb4',
            'i 00080',
        ))
        exp_instructions = [
            (0, 'LD A,(IX+$0F)'),
            (3, 'LD (IY-23),B'),
            (6, 'ADC A,(IX-13)'),
            (9, 'ADD A,(IY+%01111000)'),
            (12, 'SBC A,(IX+47)'),
            (15, 'AND (IY-%00000101)'),
            (18, 'CP (IX-$13)'),
            (21, 'OR (IY+102)'),
            (24, 'SUB (IX+99)'),
            (27, 'XOR (IY-$3F)'),
            (30, 'DEC (IX-$1C)'),
            (33, 'INC (IY+%00000111)'),
            (36, 'RL (IX+%01001101)'),
            (40, 'RLC (IY-92)'),
            (44, 'RR (IX-18)'),
            (48, 'RRC (IY+55)'),
            (52, 'SLA (IX+%00011010)'),
            (56, 'SLL (IY-%01100010)'),
            (60, 'SRA (IX-$03)'),
            (64, 'SRL (IY+$13)'),
            (68, 'BIT 0,(IX+33)'),
            (72, 'RES 1,(IY-81)'),
            (76, 'SET 2,(IX-$40)'),
        ]
        self._test_disassembly(snapshot, ctl, exp_instructions, asm_hex=True)

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
        ctl = '\n'.join((
            'c 00000',
            '  00000,d',
            '  00004,db',
            '  00008,b4',
            '  00012,bd4',
            '  00016,n',
            '  00020,dn',
            '  00024,,nd4,nn4',
            'i 00032',
        ))
        exp_instructions = [
            (0, 'LD (IX+45),87'),
            (4, 'LD (IY+54),%01001110'),
            (8, 'LD (IX-%00000010),%11101010'),
            (12, 'LD (IY-%01101011),19'),
            (16, 'LD (IX+$0D),$FF'),
            (20, 'LD (IY+36),$6D'),
            (24, 'LD (IX-$3E),111'),
            (28, 'LD (IY-$49),$C7'),
        ]
        self._test_disassembly(snapshot, ctl, exp_instructions, asm_hex=True)

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
        ctl = '\n'.join((
            'c 00000',
            '  00000,h9,d3,h3',
            '  00009,b,3,d4,4',
            '  00020,,3,d8',
            '  00031,n',
            '  00042,h7',
            '  00049,d8',
            '  00057,b7',
            '  00064,n8',
            '  00072,dn',
            '  00084,nb',
            '  00096,dn9',
            '  00105,nd9',
            '  00114,bh',
            '  00120,dh',
            'i 00126',
        ))
        exp_instructions = [
            (0, 'LD BC,1'),
            (3, 'LD DE,$000C'),
            (6, 'LD HL,$007B'),
            (9, 'LD SP,%0000010011010010'),
            (12, 'LD IX,12345'),
            (16, 'LD IY,%0101101110100000'),
            (20, 'LD A,($8707)'),
            (23, 'LD BC,(45678)'),
            (27, 'LD DE,(56789)'),
            (31, 'LD HL,($FF98)'),
            (34, 'LD SP,($D431)'),
            (38, 'LD IX,($A8CA)'),
            (42, 'LD IY,($7D6D)'),
            (46, 'LD ($526A),A'),
            (49, 'LD (10987),BC'),
            (53, 'LD (9876),DE'),
            (57, 'LD (%0010001000111101),HL'),
            (60, 'LD (%0001110111100110),SP'),
            (64, 'LD ($FF98),IX'),
            (68, 'LD ($0001),IY'),
            (72, 'CALL 11'),
            (75, 'JP 111'),
            (78, 'CALL NZ,1111'),
            (81, 'CALL Z,11111'),
            (84, 'CALL NC,$2B68'),
            (87, 'CALL C,$2B72'),
            (90, 'CALL PO,$2BD6'),
            (93, 'CALL PE,$2FBE'),
            (96, 'CALL P,22222'),
            (99, 'CALL M,22223'),
            (102, 'JP NZ,22233'),
            (105, 'JP Z,$573D'),
            (108, 'JP NC,$5B25'),
            (111, 'JP C,$8235'),
            (114, 'JP PO,%1000001000110110'),
            (117, 'JP PE,%1000001001000000'),
            (120, 'JP P,33444'),
            (123, 'JP M,34444'),
        ]
        self._test_disassembly(snapshot, ctl, exp_instructions, asm_hex=True)

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
        ctl = '\n'.join((
            'c 00000',
            '  00000,d',
            '  00002,b',
            '  00004,h',
            '  00006,n',
            '  00008,d2',
            '  00010,b2',
            '  00012,h2',
            '  00014,n2',
            '  00016,,dn2,nd2',
            'i 00020',
        ))
        exp_instructions = [
            (0, 'DJNZ 0'),
            (2, 'JR %0000000000000100'),
            (4, 'JR NZ,$0002'),
            (6, 'JR NZ,$000A'),
            (8, 'JR Z,12'),
            (10, 'JR NC,%0000000000000110'),
            (12, 'JR C,$0008'),
            (14, 'DJNZ $000C'),
            (16, 'JR 14'),
            (18, 'JR NZ,$0012'),
        ]
        self._test_disassembly(snapshot, ctl, exp_instructions, asm_hex=True)

    def test_rst_arg_bases(self):
        snapshot = [
            199, # 00000 RST 0
            207, # 00001 RST 8
            215, # 00002 RST 16
            223, # 00003 RST 24
            231, # 00004 RST 32
            239, # 00005 RST 40
            247, # 00006 RST 48
            255, # 00007 RST 56
            199, # 00008 RST 0
            207, # 00009 RST 8
        ]
        ctl = '\n'.join((
            'c 00000',
            '  00000,b',
            '  00001,n',
            '  00002,h',
            '  00003,d',
            '  00004,4,b1,n1,h1,d1',
            '  00008,dn1',
            '  00009,nd1',
            'i 00010',
        ))
        exp_instructions = [
            (0, 'RST %00000000'),
            (1, 'RST $08'),
            (2, 'RST $10'),
            (3, 'RST 24'),
            (4, 'RST %00100000'),
            (5, 'RST $28'),
            (6, 'RST $30'),
            (7, 'RST 56'),
            (8, 'RST 0'),
            (9, 'RST $08'),
        ]
        self._test_disassembly(snapshot, ctl, exp_instructions, asm_hex=True)

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
        ctl = '\n'.join((
            'c 00000',
            '  00000,c',
            '  00010,nc',
            '  00014,c',
            'i 00028',
        ))
        exp_instructions = [
            (0, 'LD A,"\\""'),
            (2, 'ADD A,"\\\\"'),
            (4, 'SUB "!"'),
            (6, 'CP "?"'),
            (8, 'LD (HL),"A"'),
            (10, 'LD (IX+2),"B"'),
            (14, 'LD HL,"C"'),
            (17, 'LD B,31'),
            (19, 'LD C,94'),
            (21, 'LD D,96'),
            (23, 'LD E,128'),
            (25, 'LD BC,256'),
        ]
        self._test_disassembly(snapshot, ctl, exp_instructions)

class MockOptions:
    def __init__(self, line_width, defb_size, defb_mod, zfill, defm_width, asm_hex, asm_lower):
        self.line_width = line_width
        self.defb_size = defb_size
        self.defb_mod = defb_mod
        self.zfill = zfill
        self.defm_width = defm_width
        self.asm_hex = asm_hex
        self.asm_lower = asm_lower

class SkoolWriterTest(SkoolKitTestCase):
    def _get_writer(self, snapshot, ctl, line_width=79, defb_size=8, defb_mod=1, zfill=False, defm_width=66,
                    asm_hex=False, asm_lower=False):
        ctl_parser = CtlParser()
        ctl_parser.parse_ctl(self.write_text_file(ctl))
        options = MockOptions(line_width, defb_size, defb_mod, zfill, defm_width, asm_hex, asm_lower)
        return SkoolWriter(snapshot, ctl_parser, options)

    def _test_write_skool(self, snapshot, ctl, exp_skool, write_refs=0, show_text=False, **kwargs):
        writer = self._get_writer(snapshot, ctl, **kwargs)
        writer.write_skool(write_refs, show_text)
        skool = self.out.getvalue().rstrip().split('\n')
        self.assertEqual(exp_skool, skool)

    def test_write_skool(self):
        writer = self._get_writer(WRITER_SNAPSHOT, WRITER_CTL)
        writer.write_skool(0, False)
        skool = self.out.getvalue().split('\n')[:-1]
        self.assertEqual(skool, SKOOL)

    def test_line_width_short(self):
        snapshot = [175, 201]
        ctl = '\n'.join((
            'c 00000 A routine at address 0 with a title that will be wrapped over two lines',
            'D 00000 A description of the routine at address 0 that will be wrapped over two lines',
            'R 00000 HL A description of the HL register for the routine at address 0 (also wrapped over two lines)',
            'N 00000 A start comment for the routine at address 0 that will be wrapped over two lines',
            '  00000 An instruction-level comment at address 0 that will be wrapped over two lines',
            'N 00001 A mid-routine comment above the instruction at address 1 (again, wrapped over two lines)',
            'E 00000 An end comment for the routine at address 0 that will be wrapped over two lines',
            'i 00002'
        ))
        exp_skool = [
            '@start',
            '@org=0',
            '; A routine at address 0 with a title that will be wrapped over',
            '; two lines',
            ';',
            '; A description of the routine at address 0 that will be wrapped',
            '; over two lines',
            ';',
            '; HL A description of the HL register for the routine at address',
            '; .  0 (also wrapped over two lines)',
            ';',
            '; A start comment for the routine at address 0 that will be',
            '; wrapped over two lines',
            'c00000 XOR A         ; An instruction-level comment at address 0',
            '                     ; that will be wrapped over two lines',
            '; A mid-routine comment above the instruction at address 1',
            '; (again, wrapped over two lines)',
            ' 00001 RET           ;',
            '; An end comment for the routine at address 0 that will be',
            '; wrapped over two lines'
        ]
        self._test_write_skool(snapshot, ctl, exp_skool, line_width=64)

    def test_line_width_long(self):
        snapshot = [175, 201]
        ctl = '\n'.join((
            'c 00000 A routine at address zero with a 92-character title that will actually fit on a single line!',
            'D 00000 A particularly long description of the routine at address 0 that, sadly, will not quite fit on one line',
            'R 00000 HL A long description of the HL register for the routine at address 0 (on one line only)',
            'N 00000 An extremely long start comment for the routine at address 0 that will, despite its extraordinary length (and large number of characters), take up only two lines',
            '  00000 A long instruction-level comment that has no continuation line',
            'N 00001 A rather long mid-routine comment above the instruction at address 1 that does not quite fit on one line',
            'E 00000 A long end comment for the routine at address 0 that confines itself to one line',
            'i 00002'
        ))
        exp_skool = [
            '@start',
            '@org=0',
            '; A routine at address zero with a 92-character title that will actually fit on a single line!',
            ';',
            '; A particularly long description of the routine at address 0 that, sadly, will not quite fit',
            '; on one line',
            ';',
            '; HL A long description of the HL register for the routine at address 0 (on one line only)',
            ';',
            '; An extremely long start comment for the routine at address 0 that will, despite its',
            '; extraordinary length (and large number of characters), take up only two lines',
            'c00000 XOR A         ; A long instruction-level comment that has no continuation line',
            '; A rather long mid-routine comment above the instruction at address 1 that does not quite fit',
            '; on one line',
            ' 00001 RET           ;',
            '; A long end comment for the routine at address 0 that confines itself to one line'
        ]
        self._test_write_skool(snapshot, ctl, exp_skool, line_width=94)

    def test_write_refs_never(self):
        snapshot = [0] * 65536
        snapshot[30000:30007] = [
            175,     # 30000 XOR A
            2,       # 30001 LD (BC),A
            201,     # 30002 RET
            24, 251, # 30003 JR 30000
            24, 250  # 30005 JR 30001
        ]
        ctl = '\n'.join((
            'c 30000',
            'c 30003',
            'c 30005',
            'i 30007'
        ))
        exp_skool = [
            '@start',
            '@org=30000',
            '; Routine at 30000',
            'c30000 XOR A         ;',
            '*30001 LD (BC),A     ;',
            ' 30002 RET           ;',
            '',
            '; Routine at 30003',
            'c30003 JR 30000      ;',
            '',
            '; Routine at 30005',
            'c30005 JR 30001      ;'
        ]
        self._test_write_skool(snapshot, ctl, exp_skool, write_refs=-1)

    def test_write_refs_default(self):
        snapshot = [0] * 65536
        snapshot[40000:40012] = [
            175,     # 40000 XOR A
            201,     # 40001 RET
            175,     # 40002 XOR A
            201,     # 40003 RET
            24, 250, # 40004 JR 40000
            24, 249, # 40006 JR 40001
            24, 248, # 40008 JR 40002
            24, 247  # 40010 JR 40003
        ]
        ctl = '\n'.join((
            'c 40000',
            'D 40000 Routine description.',
            'N 40001 Mid-routine comment.',
            'c 40002',
            'c 40004',
            'i 40012'
        ))
        exp_skool = [
            '@start',
            '@org=40000',
            '; Routine at 40000',
            ';',
            '; Routine description.',
            'c40000 XOR A         ;',
            '; Mid-routine comment.',
            '*40001 RET           ;',
            '',
            '; Routine at 40002',
            ';',
            '; Used by the routine at #R40004.',
            'c40002 XOR A         ;',
            '; This entry point is used by the routine at #R40004.',
            '*40003 RET           ;',
            '',
            '; Routine at 40004',
            'c40004 JR 40000      ;',
            ' 40006 JR 40001      ;',
            ' 40008 JR 40002      ;',
            ' 40010 JR 40003      ;'
        ]
        self._test_write_skool(snapshot, ctl, exp_skool, write_refs=0)

    def test_write_refs_always(self):
        snapshot = [0] * 65536
        snapshot[50000:50012] = [
            175,     # 50000 XOR A
            201,     # 50001 RET
            175,     # 50002 XOR A
            201,     # 50003 RET
            24, 250, # 50004 JR 50000
            24, 249, # 50006 JR 50001
            24, 248, # 50008 JR 50002
            24, 247  # 50010 JR 50003
        ]
        ctl = '\n'.join((
            'c 50000',
            'D 50000 Routine description.',
            'N 50001 Mid-routine comment.',
            'c 50002',
            'c 50004',
            'i 50012'
        ))
        exp_skool = [
            '@start',
            '@org=50000',
            '; Routine at 50000',
            ';',
            '; Used by the routine at #R50004.',
            '; .',
            '; Routine description.',
            'c50000 XOR A         ;',
            '; This entry point is used by the routine at #R50004.',
            '; .',
            '; Mid-routine comment.',
            '*50001 RET           ;',
            '',
            '; Routine at 50002',
            ';',
            '; Used by the routine at #R50004.',
            'c50002 XOR A         ;',
            '; This entry point is used by the routine at #R50004.',
            '*50003 RET           ;',
            '',
            '; Routine at 50004',
            'c50004 JR 50000      ;',
            ' 50006 JR 50001      ;',
            ' 50008 JR 50002      ;',
            ' 50010 JR 50003      ;'
        ]
        self._test_write_skool(snapshot, ctl, exp_skool, write_refs=1)

    def test_bad_blocks(self):
        snapshot = [0] * 65537
        snapshot[65533:65535] = [62, 195]
        ctls = ('c 65533', 'c 65534')
        writer = self._get_writer(snapshot, '\n'.join(ctls))
        writer.write_skool(0, False)
        warnings = self.err.getvalue().split('\n')[:-1]
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0], 'WARNING: Code block at 65533 overlaps the following block at 65534')

    def test_blank_multi_instruction_comment(self):
        ctl = '\n'.join((
            'c 65534',
            '  65534,2 .'
        ))
        writer = self._get_writer([0] * 65536, ctl)
        writer.write_skool(0, False)
        skool = self.out.getvalue().split('\n')[:-1]
        self.assertEqual(skool[-2], 'c65534 NOP           ; {')
        self.assertEqual(skool[-1], ' 65535 NOP           ; }')

    def test_instruction_comments_starting_with_a_dot(self):
        comment1 = '...'
        comment2 = '...and so it ends'
        ctl = '\n'.join((
            'c 65534',
            '  65534,1 {}'.format(comment1),
            '  65535,1 {}'.format(comment2)
        ))
        writer = self._get_writer([0] * 65536, ctl)
        writer.write_skool(0, False)
        skool = self.out.getvalue().split('\n')[:-1]
        self.assertEqual(skool[-2], 'c65534 NOP           ; {}'.format(comment1))
        self.assertEqual(skool[-1], ' 65535 NOP           ; {}'.format(comment2))

    def test_multi_instruction_comments_starting_with_a_dot(self):
        comment1 = '...'
        comment2 = '...and so it ends'
        ctl = '\n'.join((
            'c 65532',
            '  65532,2 .{}'.format(comment1),
            '  65534,2 {}'.format(comment2)
        ))
        writer = self._get_writer([0] * 65536, ctl)
        writer.write_skool(0, False)
        skool = self.out.getvalue().split('\n')[:-1]
        self.assertEqual(skool[-4], 'c65532 NOP           ; {{{}'.format(comment1))
        self.assertEqual(skool[-3], ' 65533 NOP           ; }')
        self.assertEqual(skool[-2], ' 65534 NOP           ; {{{}'.format(comment2))
        self.assertEqual(skool[-1], ' 65535 NOP           ; }')

    def test_decimal_addresses_below_10000(self):
        ctl = '\n'.join((
            'b 00000',
            'i 00001',
            'b 00003',
            'i 00004',
            'b 00023',
            'i 00024',
            'b 00573',
            'i 00574',
            'b 01876',
            'i 01877',
        ))
        writer = self._get_writer([0] * 1877, ctl)
        writer.write_skool(0, False)
        skool = self.out.getvalue().split('\n')[:-1]
        self.assertEqual(skool[3], 'b00000 DEFB 0')
        self.assertEqual(skool[8], 'b00003 DEFB 0')
        self.assertEqual(skool[13], 'b00023 DEFB 0')
        self.assertEqual(skool[18], 'b00573 DEFB 0')
        self.assertEqual(skool[23], 'b01876 DEFB 0')

    def test_decimal_org_addresses_below_10000(self):
        snapshot = [0] * 1235
        for org in (0, 1, 12, 123, 1234):
            ctl = 'b {:05d}\ni {:05d}'.format(org, org + 1)
            writer = self._get_writer(snapshot, ctl)
            self.clear_streams()
            writer.write_skool(0, False)
            skool = self.out.getvalue().split('\n')[:-1]
            self.assertEqual(skool[1], '@org={}'.format(org))

    def test_no_table_end_marker(self):
        ctl = '\n'.join((
            'b 00000',
            'D 00000 #TABLE { this table has no end marker }',
            'i 00001'
        ))
        writer = self._get_writer([0], ctl)
        with self.assertRaisesRegexp(SkoolKitError, re.escape("No end marker found: #TABLE { this table h...")):
            writer.write_skool(0, False)

    def test_no_udgtable_end_marker(self):
        ctl = '\n'.join((
            'b 00000',
            'D 00000 #UDGTABLE { this table has no end marker }',
            'i 00001'
        ))
        writer = self._get_writer([0], ctl)
        with self.assertRaisesRegexp(SkoolKitError, re.escape("No end marker found: #UDGTABLE { this table h...")):
            writer.write_skool(0, False)

    def test_no_list_end_marker(self):
        ctl = '\n'.join((
            'b 00000',
            'D 00000 #LIST { this list has no end marker }',
            'i 00001'
        ))
        writer = self._get_writer([0], ctl)
        with self.assertRaisesRegexp(SkoolKitError, re.escape("No end marker found: #LIST { this list ha...")):
            writer.write_skool(0, False)

    def test_ignoreua_directives(self):
        ctl = '\n'.join((
            '@ 10000 ignoreua:t',
            'c 10000 Routine at 10000',
            '@ 10000 ignoreua:d',
            'D 10000 Description of the routine at 10000.',
            '@ 10000 ignoreua:r',
            'R 10000 HL 10000',
            '@ 10000 ignoreua:m',
            'N 10000 Start comment.',
            '@ 10000 ignoreua',
            '  10000 Instruction-level comment at 10000',
            '@ 10001 ignoreua:m',
            'N 10001 Mid-block comment above 10001.',
            '@ 10001 ignoreua:i',
            '  10001 Instruction-level comment at 10001',
            '@ 10000 ignoreua:e',
            'E 10000 End comment for the routine at 10000.',
            'i 10002'
        ))
        exp_skool = [
            '@start',
            '@org=10000',
            '@ignoreua',
            '; Routine at 10000',
            ';',
            '@ignoreua',
            '; Description of the routine at 10000.',
            ';',
            '@ignoreua',
            '; HL 10000',
            ';',
            '@ignoreua',
            '; Start comment.',
            '@ignoreua',
            'c10000 LD A,B        ; Instruction-level comment at 10000',
            '@ignoreua',
            '; Mid-block comment above 10001.',
            '@ignoreua',
            ' 10001 RET           ; Instruction-level comment at 10001',
            '@ignoreua',
            '; End comment for the routine at 10000.'
        ]
        snapshot = [0] * 10000 + [120, 201]
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_ignoreua_directives_write_refs(self):
        ctl = '\n'.join((
            'c 10000 Routine at 10000',
            '@ 10000 ignoreua:d',
            'D 10000 Description of the routine at 10000.',
            'c 10002 Routine at 10002',
            '@ 10003 ignoreua:m',
            'N 10003 Mid-block comment above 10003.',
            'i 10005'
        ))
        exp_skool = [
            '@start',
            '@org=10000',
            '; Routine at 10000',
            ';',
            '@ignoreua',
            '; Used by the routine at #R10002.',
            '; .',
            '; Description of the routine at 10000.',
            'c10000 JR 10003      ;',
            '',
            '; Routine at 10002',
            'c10002 LD A,B        ;',
            '@ignoreua',
            '; This entry point is used by the routine at #R10000.',
            '; .',
            '; Mid-block comment above 10003.',
            '*10003 JR 10000      ;',
        ]
        snapshot = [0] * 10000 + [24, 1, 120, 24, 251]
        self._test_write_skool(snapshot, ctl, exp_skool, 1)

    def test_assemble_directives(self):
        ctl = '\n'.join((
            'c 00000',
            '@ 00001 assemble=1',
            '@ 00002 assemble=0',
            'i 00003'
        ))
        exp_skool = [
            '@start',
            '@org=0',
            '; Routine at 0',
            'c00000 NOP           ;',
            '@assemble=1',
            ' 00001 NOP           ;',
            '@assemble=0',
            ' 00002 NOP           ;'
        ]
        self._test_write_skool([0] * 3, ctl, exp_skool)

    def test_registers(self):
        ctl = '\n'.join((
            'c 00000 Routine',
            'R 00000 BC This register description is long enough that it needs to be split over two lines',
            'R 00000 DE Short register description',
            'R 00000',
            'R 00000 HL Another register description that is long enough to need splitting over two lines',
            'R 00000 IX',
            'i 00001'
        ))
        exp_skool = [
            '@start',
            '@org=0',
            '; Routine',
            ';',
            '; .',
            ';',
            '; BC This register description is long enough that it needs to be split over',
            '; .  two lines',
            '; DE Short register description',
            '; HL Another register description that is long enough to need splitting over',
            '; .  two lines',
            '; IX',
            'c00000 NOP           ;'
        ]
        self._test_write_skool([0], ctl, exp_skool)

    def test_registers_with_prefixes(self):
        ctl = '\n'.join((
            'c 00000 Routine',
            'R 00000 Input:A An important parameter with a long description that will be split over two lines',
            'R 00000 B Another important parameter',
            'R 00000 Output:DE The result',
            'R 00000 HL',
            'i 00001'
        ))
        exp_skool = [
            '@start',
            '@org=0',
            '; Routine',
            ';',
            '; .',
            ';',
            ';  Input:A An important parameter with a long description that will be split',
            '; .        over two lines',
            ';        B Another important parameter',
            '; Output:DE The result',
            ';        HL',
            'c00000 NOP           ;'
        ]
        self._test_write_skool([0], ctl, exp_skool)

    def test_start_comment(self):
        ctl = '\n'.join((
            'c 00000',
            'N 00000 Start comment.',
            'i 00001'
        ))
        exp_skool = [
            '@start',
            '@org=0',
            '; Routine at 0',
            ';',
            '; .',
            ';',
            '; .',
            ';',
            '; Start comment.',
            'c00000 NOP           ;'
        ]
        self._test_write_skool([0], ctl, exp_skool)

    def test_multi_paragraph_start_comment(self):
        ctl = '\n'.join((
            'c 00000 Routine',
            'D 00000 Description.',
            'N 00000 Start comment paragraph 1.',
            'N 00000 Paragraph 2.',
            'i 00001'
        ))
        exp_skool = [
            '@start',
            '@org=0',
            '; Routine',
            ';',
            '; Description.',
            ';',
            '; .',
            ';',
            '; Start comment paragraph 1.',
            '; .',
            '; Paragraph 2.',
            'c00000 NOP           ;'
        ]
        self._test_write_skool([0], ctl, exp_skool)

    def test_loop(self):
        ctl = '\n'.join((
            'b 00000 Two bytes and one word, times ten',
            'B 00000,2',
            'W 00002',
            'L 00000,4,10',
            'i 00040'
        ))
        writer = self._get_writer([0] * 40, ctl)
        writer.write_skool(0, False)
        skool = self.out.getvalue().split('\n')[:-2]
        address = 0
        ctl = 'b'
        for i in range(3, 23, 2):
            self.assertEqual(skool[i], '{}{:05} DEFB 0,0'.format(ctl, address))
            self.assertEqual(skool[i + 1], ' {:05} DEFW 0'.format(address + 2))
            ctl = ' '
            address += 4

    def test_loop_with_entries(self):
        ctl = '\n'.join((
            'b 00000 A block of five pairs of bytes',
            'B 00000,10,2',
            'L 00000,10,3,1',
            'i 00030'
        ))
        writer = self._get_writer([0] * 30, ctl)
        writer.write_skool(0, False)
        skool = self.out.getvalue().split('\n')[:-2]
        address = 0
        index = 3
        for i in range(3):
            ctl = 'b'
            for j in range(5):
                self.assertEqual(skool[index], '{}{:05} DEFB 0,0'.format(ctl, address))
                ctl = ' '
                address += 2
                index += 1
            index += 2

    def test_overlong_multiline_comment_ends_at_mid_block_comment(self):
        snapshot = [
            62,  # 00000 DEFB 62
            0,   # 00001 NOP
            201, # 00002 RET
        ]
        ctl = '\n'.join((
            'c 00000',
            'M 00000,3 This is really LD A,0',
            'B 00000,1',
            'N 00002 This comment should not be swallowed by the overlong M directive.',
            'i 00003',
        ))
        exp_skool = [
            '@start',
            '@org=0',
            '; Routine at 0',
            'c00000 DEFB 62       ; {This is really LD A,0',
            ' 00001 NOP           ; }',
            '; This comment should not be swallowed by the overlong M directive.',
            ' 00002 RET           ;',
        ]
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_lower_case_hexadecimal(self):
        snapshot = [0] * 10 + [255]
        ctl = '\n'.join((
            'b 00010',
            'i 00011'
        ))
        exp_skool = [
            '@start',
            '@org=$000a',
            '; Data block at 000a',
            'b$000a defb $ff'
        ]
        self._test_write_skool(snapshot, ctl, exp_skool, asm_hex=True, asm_lower=True)

    def test_defm_width(self):
        snapshot = [65] * 4
        ctl = '\n'.join((
            't 00000',
            'i 00004'
        ))
        exp_skool = [
            '@start',
            '@org=0',
            '; Message at 0',
            't00000 DEFM "AA"',
            ' 00002 DEFM "AA"'
        ]
        self._test_write_skool(snapshot, ctl, exp_skool, defm_width=2)

    def test_defb_mod(self):
        snapshot = [0] * 14
        ctl = '\n'.join((
            'b 00002',
            'i 00014'
        ))
        exp_skool = [
            '@start',
            '@org=2',
            '; Data block at 2',
            'b00002 DEFB 0,0',
            ' 00004 DEFB 0,0,0,0,0,0,0,0',
            ' 00012 DEFB 0,0'
        ]
        self._test_write_skool(snapshot, ctl, exp_skool, defb_mod=4)

    def test_defb_size(self):
        snapshot = [0] * 5
        ctl = '\n'.join((
            'b 00000',
            'i 00005'
        ))
        exp_skool = [
            '@start',
            '@org=0',
            '; Data block at 0',
            'b00000 DEFB 0,0,0',
            ' 00003 DEFB 0,0'
        ]
        self._test_write_skool(snapshot, ctl, exp_skool, defb_size=3)

    def test_zfill(self):
        snapshot = [0] * 5
        ctl = '\n'.join((
            'b 00000',
            'i 00005'
        ))
        exp_skool = [
            '@start',
            '@org=0',
            '; Data block at 0',
            'b00000 DEFB 000,000,000,000,000'
        ]
        self._test_write_skool(snapshot, ctl, exp_skool, zfill=True)

    def test_show_text(self):
        snapshot = [49, 127, 50]
        ctl = '\n'.join((
            'c 00000',
            'i 00003'
        ))
        exp_skool = [
            '@start',
            '@org=0',
            '; Routine at 0',
            'c00000 LD SP,12927   ; [1.2]',
        ]
        self._test_write_skool(snapshot, ctl, exp_skool, show_text=True)

    def test_braces_in_instruction_comments(self):
        snapshot = [0] * 39
        ctl = '\n'.join((
            'b 00000',
            '  00000,1,1 {unmatched opening brace',
            '  00001,1,1 unmatched closing brace}',
            '  00002,1,1 {matched braces}',
            '  00003,2,1 {unmatched opening brace',
            '  00005,2,1 unmatched closing brace}',
            '  00007,2,1 {matched braces}',
            '  00009,2,1 { unmatched opening brace with a space',
            '  00011,2,1 unmatched closing brace with a space }',
            '  00013,2,1 { matched braces with spaces }',
            '  00015,1,1 {{unmatched opening braces}',
            '  00016,1,1 {unmatched closing braces}}',
            '  00017,1,1 {{matched pairs of braces}}',
            '  00018,2,1 {{unmatched opening braces}',
            '  00020,2,1 {unmatched closing braces}}',
            '  00022,2,1 {{matched pairs of braces}}',
            '  00024,2,1 {{{unmatched opening braces on a comment that spans two lines}}',
            '  00026,2,1 {{unmatched closing braces on a comment that spans two lines}}}',
            '  00028,2,1 {{{matched pairs of braces on a comment that spans two lines}}}',
            '  00030,1,1 unmatched {opening brace in the middle',
            '  00031,1,1 unmatched closing brace} in the middle',
            '  00032,1,1 matched {braces} in the middle',
            '  00033,2,1 unmatched {opening brace in the middle',
            '  00035,2,1 unmatched closing brace} in the middle',
            '  00037,2,1 matched {{braces}} in the middle',
            'i 00039'
        ))
        exp_skool = [
            '@start',
            '@org=0',
            '; Data block at 0',
            'b00000 DEFB 0        ; { {unmatched opening brace}}',
            ' 00001 DEFB 0        ; unmatched closing brace}',
            ' 00002 DEFB 0        ; { {matched braces} }',
            ' 00003 DEFB 0        ; { {unmatched opening brace',
            ' 00004 DEFB 0        ; }}',
            ' 00005 DEFB 0        ; {{unmatched closing brace}',
            ' 00006 DEFB 0        ; }',
            ' 00007 DEFB 0        ; { {matched braces}',
            ' 00008 DEFB 0        ; }',
            ' 00009 DEFB 0        ; { { unmatched opening brace with a space',
            ' 00010 DEFB 0        ; }}',
            ' 00011 DEFB 0        ; {{unmatched closing brace with a space }',
            ' 00012 DEFB 0        ; }',
            ' 00013 DEFB 0        ; { { matched braces with spaces }',
            ' 00014 DEFB 0        ; }',
            ' 00015 DEFB 0        ; { {{unmatched opening braces} }}',
            ' 00016 DEFB 0        ; { {unmatched closing braces}} }',
            ' 00017 DEFB 0        ; { {{matched pairs of braces}} }',
            ' 00018 DEFB 0        ; { {{unmatched opening braces}',
            ' 00019 DEFB 0        ; }}',
            ' 00020 DEFB 0        ; {{ {unmatched closing braces}}',
            ' 00021 DEFB 0        ; }',
            ' 00022 DEFB 0        ; { {{matched pairs of braces}}',
            ' 00023 DEFB 0        ; }',
            ' 00024 DEFB 0        ; { {{{unmatched opening braces on a comment that spans',
            ' 00025 DEFB 0        ; two lines}} }}',
            ' 00026 DEFB 0        ; {{ {{unmatched closing braces on a comment that spans',
            ' 00027 DEFB 0        ; two lines}}} }',
            ' 00028 DEFB 0        ; { {{{matched pairs of braces on a comment that spans two',
            ' 00029 DEFB 0        ; lines}}} }',
            ' 00030 DEFB 0        ; unmatched {opening brace in the middle',
            ' 00031 DEFB 0        ; unmatched closing brace} in the middle',
            ' 00032 DEFB 0        ; matched {braces} in the middle',
            ' 00033 DEFB 0        ; {unmatched {opening brace in the middle',
            ' 00034 DEFB 0        ; }}',
            ' 00035 DEFB 0        ; {{unmatched closing brace} in the middle',
            ' 00036 DEFB 0        ; }',
            ' 00037 DEFB 0        ; {matched {{braces}} in the middle',
            ' 00038 DEFB 0        ; }',
        ]
        self._test_write_skool(snapshot, ctl, exp_skool)

class CtlWriterTest(SkoolKitTestCase):
    def test_decimal_addresses_below_10000(self):
        ctls = {0: 'b', 1: 'c', 22: 't', 333: 'w', 4444: 's'}
        exp_ctl = [
            'b 00000',
            'c 00001',
            't 00022',
            'w 00333',
            's 04444'
        ]
        ctlfile = self.write_bin_file()
        write_ctl(ctlfile, ctls, 0)
        with open(ctlfile, 'r') as f:
            ctl = [line.rstrip() for line in f]
        self.assertEqual(exp_ctl, ctl)

    def test_lower_case_hexadecimal_addresses(self):
        ctls = {57005: 'c', 64181: 'b'}
        ctlfile = self.write_bin_file()
        write_ctl(ctlfile, ctls, -1)
        with open(ctlfile, 'r') as f:
            ctl = [line.rstrip() for line in f]
        self.assertEqual(['c $dead', 'b $fab5'], ctl)

if __name__ == '__main__':
    unittest.main()
