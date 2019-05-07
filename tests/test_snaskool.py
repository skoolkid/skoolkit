from io import StringIO
import re
import textwrap

from skoolkittest import SkoolKitTestCase
from skoolkit import SkoolKitError
from skoolkit.config import COMMANDS
from skoolkit.snaskool import Disassembly, SkoolWriter
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
@ 32768 replace=/#copy/#CHR(169)
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
@ 32768 replace=/foo/bar
@ 32768 org=32768
@ 32768 label=START
c 32768
D 32768 Routine description paragraph 1.
D 32768 Routine description paragraph 2.
R 32768 A Some value
R 32768 B Some other value
  32768,2 This is an instruction-level comment that spans two instructions and is too long to fit on two lines, so extends to three
E 32768 Routine end comment.
@ 32770 end
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
i 32782
"""

SKOOL = """@start
@writer=skoolkit.game.GameAsmWriter
@set-tab=1
@replace=/foo/bar
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

CONFIG = {k: v[0] for k, v in COMMANDS['sna2skool'].items()}

class DisassemblyTest(SkoolKitTestCase):
    def _test_disassembly(self, snapshot, ctl, exp_instructions, **kwargs):
        ctl_parser = CtlParser()
        ctl_parser.parse_ctls([StringIO(textwrap.dedent(ctl).strip())])
        disassembly = Disassembly(snapshot, ctl_parser, CONFIG, True, **kwargs)
        entries = disassembly.entries
        self.assertEqual(len(entries), 2)
        entry = entries[0]
        self.assertEqual(entry.address, 0)
        instructions = entry.instructions
        actual_instructions = [(i.address, i.operation) for i in instructions]
        self.assertEqual(exp_instructions, actual_instructions)

    def test_disassembly(self):
        ctl_parser = CtlParser()
        ctl_parser.parse_ctls([StringIO(DISASSEMBLY_CTL)])
        disassembly = Disassembly(DISASSEMBLY_SNAPSHOT, ctl_parser, CONFIG, True)

        entries = disassembly.entries
        self.assertEqual(len(entries), 17)

        # Entry #1 (32768)
        entry = entries[0]
        self.assertEqual(entry.address, 32768)
        self.assertEqual(['Routine at 32768'], entry.title)
        self.assertEqual([['Routine description paragraph 1.'], ['Routine description paragraph 2.']], entry.description)
        self.assertEqual(entry.ctl, 'c')
        self.assertEqual([['A Some value'], ['B Some other value']], entry.registers)
        self.assertEqual([['Routine end comment.']], entry.end_comment)
        exp_asm_directives = [
            'start',
            'writer=skoolkit.game.GameAsmWriter',
            'replace=/#copy/#CHR(169)',
            'org=32768',
            'end'
        ]
        self.assertEqual(exp_asm_directives, entry.asm_directives)

        blocks = entry.blocks
        self.assertEqual(len(blocks), 1)
        block = blocks[0]
        self.assertEqual(block.header, ())
        self.assertEqual([(0, 'This is an instruction-level comment that spans two instructions')], block.comment)
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
        self.assertEqual(['label=START'], instruction.asm_directives)

        # Entry #2 (32770)
        entry = entries[1]
        self.assertEqual(entry.address, 32770)
        self.assertEqual(['Message at {}'.format(entry.address)], entry.title)
        instructions = entry.instructions
        self.assertEqual(len(instructions), 2)
        self.assertEqual(instructions[0].operation, 'DEFM "Hi"')
        self.assertEqual(instructions[1].operation, 'DEFM "Lo"')

        # Entry #3 (32774)
        entry = entries[2]
        self.assertEqual(entry.address, 32774)
        self.assertEqual(['Yo'], entry.title)

        # Entry #4 (32776)
        entry = entries[3]
        self.assertEqual(entry.address, 32776)
        self.assertEqual(['Data block at 32776'], entry.title)
        instructions = entry.instructions
        self.assertEqual(len(instructions), 5)
        self.assertEqual(instructions[0].operation, 'DEFB 0,0')
        self.assertEqual(instructions[1].operation, 'DEFB 0,0')
        self.assertEqual(instructions[2].operation, 'DEFB 0,0')
        self.assertEqual(instructions[3].operation, 'DEFB 0,0,0')
        self.assertEqual(instructions[4].operation, 'DEFB 0,0,0')
        blocks = entry.blocks
        self.assertEqual(len(blocks), 2)
        self.assertEqual([(0, 'This comment spans three DEFB statements')], blocks[0].comment)
        self.assertEqual(instructions[:3], blocks[0].instructions)
        self.assertEqual([(0, 'This comment spans two DEFB statements')], blocks[1].comment)
        self.assertEqual(instructions[3:], blocks[1].instructions)

        # Entry #5 (32788)
        entry = entries[4]
        self.assertEqual(entry.address, 32788)
        self.assertEqual(['Important byte'], entry.title)

        # Entry #6 (32789)
        entry = entries[5]
        self.assertEqual(entry.address, 32789)
        self.assertEqual(['Data block at 32789'], entry.title)
        instructions = entry.instructions
        self.assertEqual(len(instructions), 1)
        self.assertEqual(instructions[0].operation, 'DEFW 0,0')

        # Entry #7 (32793)
        entry = entries[6]
        self.assertEqual(entry.address, 32793)
        self.assertEqual(['Important word'], entry.title)

        # Entry #8 (32795)
        entry = entries[7]
        self.assertEqual(entry.address, 32795)
        self.assertEqual(['Game status buffer entry at 32795'], entry.title)

        # Entry #9 (32796)
        entry = entries[8]
        self.assertEqual(entry.address, 32796)
        self.assertEqual(['Important game status buffer byte'], entry.title)

        # Entry #10 (32797)
        entry = entries[9]
        self.assertEqual(entry.address, 32797)
        self.assertEqual(['Unused'], entry.title)

        # Entry #11 (32798)
        entry = entries[10]
        self.assertEqual(entry.address, 32798)
        self.assertEqual(['Unimportant unused byte'], entry.title)

        # Entry #12 (32799)
        entry = entries[11]
        self.assertEqual(entry.address, 32799)
        self.assertEqual(['Unused'], entry.title)
        instructions = entry.instructions
        self.assertEqual(len(instructions), 2)
        self.assertEqual(instructions[0].operation, 'DEFS 5')
        self.assertEqual(instructions[1].operation, 'DEFS 5')

        # Entry #13 (32809)
        entry = entries[12]
        self.assertEqual(entry.address, 32809)
        self.assertEqual(['Block of zeroes'], entry.title)
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
        self.assertEqual([(0, 'A DEFS and a NOP')], block1.comment)
        block2 = blocks[1]
        self.assertEqual(block2.start, block1.end)
        self.assertEqual(block2.end, 32814)
        self.assertEqual(instructions[2:], block2.instructions)
        self.assertEqual([(0, 'Another NOP')], block2.comment)

        # Entry #14 (32814)
        entry = entries[13]
        self.assertEqual(entry.address, 32814)
        self.assertEqual(['Refers to the routine at 32768'], entry.title)

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
        self.assertEqual([(0, '')], block1.comment)
        self.assertEqual(instructions[:1], block1.instructions)
        block2 = blocks[1]
        self.assertEqual(block2.start, block1.end)
        self.assertEqual(block2.end, 32827)
        self.assertEqual([(0, 'This comment spans two DEFB statements')], block2.comment)
        self.assertEqual(instructions[1:3], block2.instructions)
        block3 = blocks[2]
        self.assertEqual(block3.start, block2.end)
        self.assertEqual(block3.end, 32837)
        self.assertEqual([(0, 'This comment spans four DEFM statements')], block3.comment)
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
        self.assertEqual([(0, 'This comment spans two instructions with different operand bases')], block1.comment)
        self.assertEqual(instructions, block1.instructions)

        # Entry #17 (32841)
        entry = entries[16]
        self.assertEqual(entry.address, 32841)

    def test_empty_disassembly(self):
        ctl_parser = CtlParser({0: 'i'})
        disassembly = Disassembly([], ctl_parser, True)
        self.assertEqual(len(disassembly.entries), 0)
        self.assertIsNone(disassembly.org)

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
        ctl_parser.parse_ctls([StringIO('\n'.join(ctls))])
        disassembly = Disassembly(snapshot, ctl_parser, CONFIG, True)

        referrers = disassembly.entries[0].instructions[0].referrers
        ref_addresses = set([entry.address for entry in referrers])
        self.assertEqual(set(exp_ref_addresses), ref_addresses)

    def test_byte_formats(self):
        snapshot = [42] * 75
        ctl = """
            b 00000
              00000,b5
              00005,b15
              00020,b5,2,d1:n1,h1
            B 00025,b5,2:d1:m1:h1
              00030,h10,5:d3:b2
            B 00040,5,b1,h2
              00045,5,h1,T4
              00050,5,b2:T3
            T 00055,5,h2,3
            T 00060,5,2:d2:n1
            T 00065,5,3,B1,m1
            T 00070,5,B2:h3
            i 00075
        """
        exp_instructions = [
            ( 0, 'DEFB %00101010,%00101010,%00101010,%00101010,%00101010'),
            ( 5, 'DEFB %00101010,%00101010,%00101010,%00101010,%00101010,%00101010,%00101010,%00101010'),
            (13, 'DEFB %00101010,%00101010,%00101010,%00101010,%00101010,%00101010,%00101010'),
            (20, 'DEFB %00101010,%00101010'),
            (22, 'DEFB 42,42'),
            (24, 'DEFB $2A'),
            (25, 'DEFB %00101010,%00101010,42,-214,$2A'),
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
            (69, 'DEFM -214'),
            (70, 'DEFM 42,42,$2A,$2A,$2A')
        ]
        self._test_disassembly(snapshot, ctl, exp_instructions)

    def test_byte_formats_hex(self):
        snapshot = [85] * 12
        ctl = """
            b 00000
              00000,6,1:b1:d1:h1:m1:n1
            T 00006,6,1:b1:d1:h1:m1:n1
            i 00012
        """
        exp_instructions = [
            (0, 'DEFB $55,%01010101,85,$55,-$AB,$55'),
            (6, 'DEFM "U",%01010101,85,$55,-$AB,$55')
        ]
        self._test_disassembly(snapshot, ctl, exp_instructions, asm_hex=True)

    def test_text_containing_invalid_characters(self):
        snapshot = [65, 0, 66, 94, 67, 96, 127, 68, 255]
        ctl = """
            t 00000
            T 00000,9,9
            i 00009
        """
        exp_instructions = [(0, 'DEFM "A",0,"B",94,"C",96,127,"D",255')]
        self._test_disassembly(snapshot, ctl, exp_instructions)

    def test_text_containing_invalid_characters_hex(self):
        snapshot = [65, 0, 66, 94, 67, 96, 127, 68, 255]
        ctl = """
            t 00000
            T 00000,9,9
            i 00009
        """
        exp_instructions = [(0, 'DEFM "A",$00,"B",$5E,"C",$60,$7F,"D",$FF')]
        self._test_disassembly(snapshot, ctl, exp_instructions, asm_hex=True)

    def test_text_containing_invalid_characters_hex_lower(self):
        snapshot = [65, 0, 66, 94, 67, 96, 127, 68, 255]
        ctl = """
            t 00000
            T 00000,9,9
            i 00009
        """
        exp_instructions = [(0, 'defm "A",$00,"B",$5e,"C",$60,$7f,"D",$ff')]
        self._test_disassembly(snapshot, ctl, exp_instructions, asm_hex=True, asm_lower=True)

    def test_inverted_characters(self):
        snapshot = [225, 226, 72, 233, 76, 239, 225, 0, 62, 225, 225, 225, 128, 222]
        ctl = """
            b 00000
              00000,1,T1
            T 00001,1,1
              00002,2,T1:T1
            T 00004,2,1:1
            W 00006,2,c2
            C 00008,c2
            S 00010,2,2:c225
              00012,1,T1
            T 00013,1,1
            i 00014
        """
        exp_instructions = [
            (0, 'DEFB "a"+128'),
            (1, 'DEFM "b"+128'),
            (2, 'DEFB "H","i"+128'),
            (4, 'DEFM "L","o"+128'),
            (6, 'DEFW "a"+128'),
            (8, 'LD A,"a"+128'),
            (10, 'DEFS 2,"a"+128'),
            (12, 'DEFB 128'),
            (13, 'DEFM 222')
        ]
        self._test_disassembly(snapshot, ctl, exp_instructions)

    def test_inverted_characters_hex(self):
        snapshot = [225, 226, 72, 233, 76, 239, 225, 0, 62, 225, 225, 225, 128, 224]
        ctl = """
            b 00000
              00000,1,T1
            T 00001,1,1
              00002,2,T1:T1
            T 00004,2,1:1
            W 00006,2,c2
            C 00008,c2
            S 00010,2,2:c225
              00012,1,T1
            T 00013,1,1
            i 00014
        """
        exp_instructions = [
            (0, 'DEFB "a"+$80'),
            (1, 'DEFM "b"+$80'),
            (2, 'DEFB "H","i"+$80'),
            (4, 'DEFM "L","o"+$80'),
            (6, 'DEFW "a"+$80'),
            (8, 'LD A,"a"+$80'),
            (10, 'DEFS $02,"a"+$80'),
            (12, 'DEFB $80'),
            (13, 'DEFM $E0')
        ]
        self._test_disassembly(snapshot, ctl, exp_instructions, asm_hex=True)

    def test_word_formats(self):
        snapshot = [170, 53] * 32 + [33, 0] * 2
        ctl = """
            w 00000
              00000,4
              00004,b4
              00008,d4
            W 00012,h4
            W 00016,b8,2,d2,h2:n2
              00024,d8,b4:2:h2
              00032,h8,b2:d4:2
              00040,8,b2,2,m2,h2
            W 00048,8,b2:2:m2:h2
              00056,8,4
              00064,4,c2:2
            i 00068
        """
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
            (20, 'DEFW $35AA,13738'),
            (24, 'DEFW %0011010110101010,%0011010110101010,13738,$35AA'),
            (32, 'DEFW %0011010110101010,13738,13738,$35AA'),
            (40, 'DEFW %0011010110101010'),
            (42, 'DEFW 13738'),
            (44, 'DEFW -51798'),
            (46, 'DEFW $35AA'),
            (48, 'DEFW %0011010110101010,13738,-51798,$35AA'),
            (56, 'DEFW 13738,13738'),
            (60, 'DEFW 13738,13738'),
            (64, 'DEFW "!",33')
        ]
        self._test_disassembly(snapshot, ctl, exp_instructions)

    def test_word_formats_hex(self):
        snapshot = [240] * 12
        ctl = """
            w 00000
              00000,10,b2,d2,h2,2,m2,n2
            i 00012
        """
        exp_instructions = [
            (0, 'DEFW %1111000011110000'),
            (2, 'DEFW 61680'),
            (4, 'DEFW $F0F0'),
            (6, 'DEFW $F0F0'),
            (8, 'DEFW -$0F10'),
            (10, 'DEFW $F0F0')
        ]
        self._test_disassembly(snapshot, ctl, exp_instructions, asm_hex=True)

    def test_s_directives(self):
        snapshot = [1] * 4 + [0] * 1292
        ctl = """
            s 00000
              00000,4
              00004,b4
            S 00008,d4
              00012,h8
              00020,40,b10,10,h10
            S 00060,b40,10,d10,h10
              00100,d40,b5,n5,10,h10
              00140,h60,b10,d10,40
            S 00200,768,b256,d256,h256
            S 00968,328,c" ",c160,c4,c132
            i 01296
        """
        exp_instructions = [
            (  0, 'DEFS 4,1'),
            (  4, 'DEFS %00000100'),
            (  8, 'DEFS 4'),
            ( 12, 'DEFS $08'),
            ( 20, 'DEFS %00001010'),
            ( 30, 'DEFS 10'),
            ( 40, 'DEFS $0A'),
            ( 50, 'DEFS $0A'),
            ( 60, 'DEFS %00001010'),
            ( 70, 'DEFS 10'),
            ( 80, 'DEFS $0A'),
            ( 90, 'DEFS $0A'),
            (100, 'DEFS %00000101'),
            (105, 'DEFS 5'),
            (110, 'DEFS 10'),
            (120, 'DEFS $0A'),
            (130, 'DEFS $0A'),
            (140, 'DEFS %00001010'),
            (150, 'DEFS 10'),
            (160, 'DEFS $28'),
            (200, 'DEFS %0000000100000000'),
            (456, 'DEFS 256'),
            (712, 'DEFS $0100'),
            (968, 'DEFS " "'),
            (1000, 'DEFS " "+128'),
            (1160, 'DEFS 4'),
            (1164, 'DEFS 132')
        ]
        self._test_disassembly(snapshot, ctl, exp_instructions)

    def test_s_directives_hex(self):
        snapshot = [1, 1, 128, 128, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1]
        ctl = """
            s 00000
              00000,20,d2,h2,b10,n6
            i 00020
        """
        exp_instructions = [
            (0, 'DEFS 2,$01'),
            (2, 'DEFS $02,$80'),
            (4, 'DEFS %00001010,$02'),
            (14, 'DEFS $06,$01')
        ]
        self._test_disassembly(snapshot, ctl, exp_instructions, asm_hex=True)

    def test_s_directives_with_byte_value_base(self):
        snapshot = [1, 1, 33, 33, 3, 3, 4, 4, 5, 5, 161, 161, 7, 7, 136, 136, 255, 255]
        ctl = """
            s 00000
              00000,18,2:b,2:c,2:d,2:h,h2:n,2:c*3,2:m
            i 00018
        """
        exp_instructions = [
            (0, 'DEFS 2,%00000001'),
            (2, 'DEFS 2,"!"'),
            (4, 'DEFS 2,3'),
            (6, 'DEFS 2,$04'),
            (8, 'DEFS $02,5'),
            (10, 'DEFS 2,"!"+128'),
            (12, 'DEFS 2,7'),
            (14, 'DEFS 2,136'),
            (16, 'DEFS 2,-1')
        ]
        self._test_disassembly(snapshot, ctl, exp_instructions)

    def test_s_directives_with_byte_value_base_hex(self):
        snapshot = [1, 1, 33, 33, 3, 3, 4, 4, 5, 5, 161, 161, 7, 7, 136, 136, 255, 255]
        ctl = """
            s 00000
              00000,18,2:b,2:c,2:d,2:h,d2:n,2:c*3,2:m
            i 00018
        """
        exp_instructions = [
            (0, 'DEFS $02,%00000001'),
            (2, 'DEFS $02,"!"'),
            (4, 'DEFS $02,3'),
            (6, 'DEFS $02,$04'),
            (8, 'DEFS 2,$05'),
            (10, 'DEFS $02,"!"+$80'),
            (12, 'DEFS $02,$07'),
            (14, 'DEFS $02,$88'),
            (16, 'DEFS $02,-$01')
        ]
        self._test_disassembly(snapshot, ctl, exp_instructions, asm_hex=True)

    def test_s_directives_with_mixed_values(self):
        snapshot = [0, 1, 2, 3, 4, 5]
        ctl = """
            s 00000
              00000,6,2,2:h,2:n
            i 00006
        """
        exp_instructions = [
            (0, 'DEFB 0,1'),
            (2, 'DEFB 2,3'),
            (4, 'DEFB 4,5')
        ]
        self._test_disassembly(snapshot, ctl, exp_instructions)

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
        ctl = """
            c 00000
              00000,b14,6,m2,h2,4
              00014,,h12,d2
              00028,d
              00032,bd4
              00036,h4
              00040,d4
              00044,n4
            i 00048
        """
        exp_instructions = [
            (0, 'LD A,%00000101'),
            (2, 'LD B,%00000110'),
            (4, 'LD C,%00000111'),
            (6, 'LD D,-$10'),
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
        ctl = """
            c 00000
              00000,h,3,d3
              00009,b9,3,d3,3
              00018,,3,d6
              00027,h6
              00033,b7
              00040,d12
              00052,bn
              00060,nb
              00068,dn8
              00076,nb4
            i 00080
        """
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
        ctl = """
            c 00000
              00000,d
              00004,db
              00008,b4
              00012,bd4
              00016,n
              00020,dn
              00024,,nd4,nn4
            i 00032
        """
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
        ctl = """
            c 00000
              00000,9,d3,h3,m3
              00009,b,3,d4,4
              00020,,3,d8
              00031,n
              00042,h7
              00049,d8
              00057,b7
              00064,n8
              00072,dn
              00084,nb
              00096,dn9
              00105,nd9
              00114,bh
              00120,dh
            i 00126
        """
        exp_instructions = [
            (0, 'LD BC,1'),
            (3, 'LD DE,$000C'),
            (6, 'LD HL,-$FF85'),
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
        ctl = """
            c 00000
              00000,d
              00002,b
              00004,h
              00006,n
              00008,d2
              00010,b2
              00012,h2
              00014,n2
              00016,,dn2,nd2
            i 00020
        """
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
        ctl = """
            c 00000
              00000,b
              00001,n
              00002,h
              00003,d
              00004,4,b1,n1,h1,d1
              00008,dn1
              00009,nd1
            i 00010
        """
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
        ctl = """
            c 00000
              00000,c
              00010,nc
              00014,c
            i 00028
        """
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

    def test_config(self):
        params = {
            'Title-b': 'Bytes at {address}',
            'Title-c': 'Code at {address}',
            'Title-g': 'Game state at {address}',
            'Title-i': 'Ignored RAM at {address}',
            'Title-s': 'Unused space at {address}',
            'Title-t': 'Text at {address}',
            'Title-u': 'Unused bytes at {address}',
            'Title-w': 'Words at {address}'
        }
        snapshot = [0] * 9
        ctl = """
            b 00000
            c 00001
            g 00002
            i 00003
            D 00003 Force a title for this ignored block.
            s 00004
            t 00005
            u 00006
            w 00007
            i 00009
        """
        exp_titles = (
            'Bytes at 0',
            'Code at 1',
            'Game state at 2',
            'Ignored RAM at 3',
            'Unused space at 4',
            'Text at 5',
            'Unused bytes at 6',
            'Words at 7',
            ''
        )
        ctl_parser = CtlParser()
        ctl_parser.parse_ctls([StringIO(textwrap.dedent(ctl).strip())])
        config = CONFIG.copy()
        config.update(params)
        disassembly = Disassembly(snapshot, ctl_parser, config, True)

        self.assertEqual([[t] for t in exp_titles], [e.title for e in disassembly.entries])

    def test_invalid_title_templates(self):
        snapshot = [0, 0]
        for entry_type in 'bcgistuw':
            params = {'Title-' + entry_type: 'Stuff at {address:04X}'}
            ctl = """
                {} 00000
                D 00000 Comment.
                i 00002
            """.format(entry_type)
            ctl_parser = CtlParser()
            ctl_parser.parse_ctls([StringIO(textwrap.dedent(ctl).strip())])
            config = CONFIG.copy()
            config.update(params)
            error = "^Failed to format Title-{} template: Unknown format code 'X' for object of type 'str'$".format(entry_type)
            with self.assertRaisesRegex(SkoolKitError, error):
                Disassembly(snapshot, ctl_parser, config, True)

class MockOptions:
    def __init__(self, line_width, base, case):
        self.line_width = line_width
        self.base = base
        self.case = case

class SkoolWriterTest(SkoolKitTestCase):
    def _get_writer(self, snapshot, ctl, params=None, line_width=79, base=10, case=2):
        ctl_parser = CtlParser()
        ctl_parser.parse_ctls([StringIO(textwrap.dedent(ctl).strip())])
        options = MockOptions(line_width, base, case)
        config = CONFIG.copy()
        config.update(params or {})
        return SkoolWriter(snapshot, ctl_parser, options, config)

    def _test_write_skool(self, snapshot, ctl, exp_skool, write_refs=1, show_text=False, **kwargs):
        self.clear_streams()
        writer = self._get_writer(snapshot, ctl, **kwargs)
        writer.write_skool(write_refs, show_text)
        skool = self.out.getvalue().rstrip()
        self.assertEqual(textwrap.dedent(exp_skool).strip(), skool)

    def test_write_skool(self):
        writer = self._get_writer(WRITER_SNAPSHOT, WRITER_CTL)
        writer.write_skool(1, False)
        skool = self.out.getvalue().split('\n')[:-1]
        self.assertEqual(SKOOL, skool)

    def test_empty_disassembly(self):
        snapshot = []
        ctl = ''
        exp_skool = ''
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_line_width_short(self):
        snapshot = [175, 201]
        ctl = """
            c 00000 A routine at address 0 with a title that will be wrapped over two lines
            D 00000 A description of the routine at address 0 that will be wrapped over two lines
            R 00000 HL A description of the HL register for the routine at address 0 (also wrapped over two lines)
            N 00000 A start comment for the routine at address 0 that will be wrapped over two lines
              00000 An instruction-level comment at address 0 that will be wrapped over two lines
            N 00001 A mid-routine comment above the instruction at address 1 (again, wrapped over two lines)
            E 00000 An end comment for the routine at address 0 that will be wrapped over two lines
            i 00002
        """
        exp_skool = """
            ; A routine at address 0 with a title that will be wrapped over
            ; two lines
            ;
            ; A description of the routine at address 0 that will be wrapped
            ; over two lines
            ;
            ; HL A description of the HL register for the routine at address
            ; .  0 (also wrapped over two lines)
            ;
            ; A start comment for the routine at address 0 that will be
            ; wrapped over two lines
            c00000 XOR A         ; An instruction-level comment at address 0
                                 ; that will be wrapped over two lines
            ; A mid-routine comment above the instruction at address 1
            ; (again, wrapped over two lines)
             00001 RET           ;
            ; An end comment for the routine at address 0 that will be
            ; wrapped over two lines
        """
        self._test_write_skool(snapshot, ctl, exp_skool, line_width=64)

    def test_line_width_long(self):
        snapshot = [175, 201]
        ctl = """
            c 00000 A routine at address zero with a 92-character title that will actually fit on a single line!
            D 00000 A particularly long description of the routine at address 0 that, sadly, will not quite fit on one line
            R 00000 HL A long description of the HL register for the routine at address 0 (on one line only)
            N 00000 An extremely long start comment for the routine at address 0 that will, despite its extraordinary length (and large number of characters), take up only two lines
              00000 A long instruction-level comment that has no continuation line
            N 00001 A rather long mid-routine comment above the instruction at address 1 that does not quite fit on one line
            E 00000 A long end comment for the routine at address 0 that confines itself to one line
            i 00002
        """
        exp_skool = """
            ; A routine at address zero with a 92-character title that will actually fit on a single line!
            ;
            ; A particularly long description of the routine at address 0 that, sadly, will not quite fit
            ; on one line
            ;
            ; HL A long description of the HL register for the routine at address 0 (on one line only)
            ;
            ; An extremely long start comment for the routine at address 0 that will, despite its
            ; extraordinary length (and large number of characters), take up only two lines
            c00000 XOR A         ; A long instruction-level comment that has no continuation line
            ; A rather long mid-routine comment above the instruction at address 1 that does not quite fit
            ; on one line
             00001 RET           ;
            ; A long end comment for the routine at address 0 that confines itself to one line
        """
        self._test_write_skool(snapshot, ctl, exp_skool, line_width=94)

    def test_multi_line_comment_wrap(self):
        snapshot = [175, 60, 7, 55, 31, 168, 61, 169, 201]
        ctl = """
            c 00000 Wrap test for 55-character lines
              00000,2 This line should not be wrapped
              00002,3 And neither should this line be
              00005,2 The second line of this comment should not wrap to the next line
              00007,2 This comment spans three lines, and the third line should not be wrapped over to the fourth line.
            i 00009
        """
        exp_skool = """
            ; Wrap test for 55-character lines
            c00000 XOR A         ; {This line should not be wrapped
             00001 INC A         ; }
             00002 RLCA          ; {And neither should this line be
             00003 SCF           ;
             00004 RRA           ; }
             00005 XOR B         ; {The second line of this comment
             00006 DEC A         ; should not wrap to the next line
                                 ; }
             00007 XOR C         ; {This comment spans three lines,
             00008 RET           ; and the third line should not be
                                 ; wrapped over to the fourth line.
                                 ; }
        """
        self._test_write_skool(snapshot, ctl, exp_skool, line_width=55)

    def test_write_refs_never(self):
        snapshot = [0] * 65536
        snapshot[30000:30007] = [
            175,     # 30000 XOR A
            2,       # 30001 LD (BC),A
            201,     # 30002 RET
            24, 251, # 30003 JR 30000
            24, 250  # 30005 JR 30001
        ]
        ctl = """
            c 30000
            c 30003
            c 30005
            i 30007
        """
        exp_skool = """
            ; Routine at 30000
            c30000 XOR A         ;
            *30001 LD (BC),A     ;
             30002 RET           ;

            ; Routine at 30003
            c30003 JR 30000      ;

            ; Routine at 30005
            c30005 JR 30001      ;
        """
        self._test_write_skool(snapshot, ctl, exp_skool, write_refs=0)

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
        ctl = """
            c 40000
            D 40000 Routine description.
            N 40001 Mid-routine comment.
            c 40002
            c 40004
            i 40012
        """
        exp_skool = """
            ; Routine at 40000
            ;
            ; Routine description.
            c40000 XOR A         ;
            ; Mid-routine comment.
            *40001 RET           ;

            ; Routine at 40002
            ;
            ; Used by the routine at #R40004.
            c40002 XOR A         ;
            ; This entry point is used by the routine at #R40004.
            *40003 RET           ;

            ; Routine at 40004
            c40004 JR 40000      ;
             40006 JR 40001      ;
             40008 JR 40002      ;
             40010 JR 40003      ;
        """
        self._test_write_skool(snapshot, ctl, exp_skool, write_refs=1)

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
        ctl = """
            c 50000
            D 50000 Routine description.
            N 50001 Mid-routine comment.
            c 50002
            c 50004
            i 50012
        """
        exp_skool = """
            ; Routine at 50000
            ;
            ; Used by the routine at #R50004.
            ; .
            ; Routine description.
            c50000 XOR A         ;
            ; This entry point is used by the routine at #R50004.
            ; .
            ; Mid-routine comment.
            *50001 RET           ;

            ; Routine at 50002
            ;
            ; Used by the routine at #R50004.
            c50002 XOR A         ;
            ; This entry point is used by the routine at #R50004.
            *50003 RET           ;

            ; Routine at 50004
            c50004 JR 50000      ;
             50006 JR 50001      ;
             50008 JR 50002      ;
             50010 JR 50003      ;
        """
        self._test_write_skool(snapshot, ctl, exp_skool, write_refs=2)

    def test_code_block_overlaps_code_block(self):
        snapshot = [175, 6, 175, 201]
        ctl = """
            c 00000
            c 00002
            i 00004
        """
        writer = self._get_writer(snapshot, ctl)
        writer.write_skool(0, False)
        warnings = self.err.getvalue().split('\n')[:-1]
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0], 'WARNING: Instruction at 1 overlaps the following instruction at 2')

    def test_code_block_overlaps_data_block(self):
        snapshot = [175, 6, 0]
        ctl = """
            c 00000
            b 00002
            i 00003
        """
        writer = self._get_writer(snapshot, ctl)
        writer.write_skool(0, False)
        warnings = self.err.getvalue().split('\n')[:-1]
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0], 'WARNING: Instruction at 1 overlaps the following instruction at 2')

    def test_data_block_overlaps_code_block(self):
        snapshot = [175, 201]
        ctl = """
            w 00000
            c 00001
            i 00002
        """
        writer = self._get_writer(snapshot, ctl)
        writer.write_skool(0, False)
        warnings = self.err.getvalue().split('\n')[:-1]
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0], 'WARNING: Instruction at 0 overlaps the following instruction at 1')

    def test_data_block_overlaps_data_block(self):
        snapshot = [0] * 2
        ctl = """
            w 00000
            b 00001
            i 00002
        """
        writer = self._get_writer(snapshot, ctl)
        writer.write_skool(0, False)
        warnings = self.err.getvalue().split('\n')[:-1]
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0], 'WARNING: Instruction at 0 overlaps the following instruction at 1')

    def test_blank_multi_instruction_comment(self):
        ctl = """
            c 65534
              65534,2 .
        """
        writer = self._get_writer([0] * 65536, ctl)
        writer.write_skool(0, False)
        skool = self.out.getvalue().split('\n')[:-1]
        self.assertEqual(skool[-2], 'c65534 NOP           ; {')
        self.assertEqual(skool[-1], ' 65535 NOP           ; }')

    def test_instruction_comments_starting_with_a_dot(self):
        comment1 = '...'
        comment2 = '...and so it ends'
        ctl = """
            c 65534
              65534,1 {}
              65535,1 {}
        """.format(comment1, comment2)
        writer = self._get_writer([0] * 65536, ctl)
        writer.write_skool(0, False)
        skool = self.out.getvalue().split('\n')[:-1]
        self.assertEqual(skool[-2], 'c65534 NOP           ; {}'.format(comment1))
        self.assertEqual(skool[-1], ' 65535 NOP           ; {}'.format(comment2))

    def test_multi_instruction_comments_starting_with_a_dot(self):
        comment1 = '...'
        comment2 = '...and so it ends'
        ctl = """
            c 65532
              65532,2 .{}
              65534,2 {}
        """.format(comment1, comment2)
        writer = self._get_writer([0] * 65536, ctl)
        writer.write_skool(0, False)
        skool = self.out.getvalue().split('\n')[:-1]
        self.assertEqual(skool[-4], 'c65532 NOP           ; {{{}'.format(comment1))
        self.assertEqual(skool[-3], ' 65533 NOP           ; }')
        self.assertEqual(skool[-2], ' 65534 NOP           ; {{{}'.format(comment2))
        self.assertEqual(skool[-1], ' 65535 NOP           ; }')

    def test_decimal_addresses_below_10000(self):
        snapshot = [0] * 1877
        ctl = """
            b 00000
            i 00001
            b 00003
            i 00004
            b 00023
            i 00024
            b 00573
            i 00574
            b 01876
            i 01877
        """
        exp_skool = """
            ; Data block at 0
            b00000 DEFB 0

            i00001

            ; Data block at 3
            b00003 DEFB 0

            i00004

            ; Data block at 23
            b00023 DEFB 0

            i00024

            ; Data block at 573
            b00573 DEFB 0

            i00574

            ; Data block at 1876
            b01876 DEFB 0
        """
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_table_with_nowrap_flag(self):
        snapshot = [0]
        rows = (
            "{ This table's rows should not be wrapped, because the TABLE macro has a nowrap flag }",
            "{ The nowrap flag is between the angle brackets (<nowrap>) before the first row }"
        )
        ctl = """
            b 00000 Test table nowrap flag
            D 00000 #*<nowrap> {} TABLE#
            i 00001
        """.format(' '.join(rows))
        exp_skool = """
            ; Test table nowrap flag
            ;
            ; #*<nowrap>
            ; { This table's rows should not be wrapped, because the TABLE macro has a nowrap flag }
            ; { The nowrap flag is between the angle brackets (<nowrap>) before the first row }
            ; TABLE#
            b00000 DEFB 0
        """
        for macro in ('TABLE', 'UDGTABLE'):
            for params in ('', '(default)'):
                args = macro + params
                with self.subTest(args=args):
                    self._test_write_skool(snapshot, ctl.replace('*', args), exp_skool.replace('*', args))

    def test_table_with_wrapalign_flag(self):
        snapshot = [0]
        rows = (
            '{ Single column with text that should wrap over to the next line with a small indent to maintain alignment }',
            '{      Another single column with text that should wrap over to the next line with a larger indent to maintain alignment }',
            '{ First column | Second column | Third column | Fourth column with text that should wrap over to the next two lines with an indent }',
            '{ First column | Second column | Third column | Fourth column ends here | Fifth column indented on the next line }'
        )
        ctl = """
            b 00000 Test table wrapalign flag
            D 00000 #*<wrapalign> {} TABLE#
            i 00001
        """.format(' '.join(rows))
        exp_skool = """
            ; Test table wrapalign flag
            ;
            ; #*<wrapalign>
            ; { Single column with text that should wrap over to the next line with a small
            ;   indent to maintain alignment }
            ; {      Another single column with text that should wrap over to the next line
            ;        with a larger indent to maintain alignment }
            ; { First column | Second column | Third column | Fourth column with text that
            ;                                                 should wrap over to the next
            ;                                                 two lines with an indent }
            ; { First column | Second column | Third column | Fourth column ends here |
            ;   Fifth column indented on the next line }
            ; TABLE#
            b00000 DEFB 0
        """
        for macro in ('TABLE', 'UDGTABLE'):
            for params in ('', '(default)'):
                args = macro + params
                with self.subTest(args=args):
                    self._test_write_skool(snapshot, ctl.replace('*', args), exp_skool.replace('*', args))

    def test_table_with_no_whitespace_around_rows(self):
        snapshot = [0]
        ctl = """
            b 00000 Test no whitespace around rows
            D 00000 #*{ Row 1 }{ Row 2 }TABLE#
            i 00001
        """
        exp_skool = """
            ; Test no whitespace around rows
            ;
            ; #*
            ; { Row 1 }
            ; { Row 2 }
            ; TABLE#
            b00000 DEFB 0
        """
        for macro in ('TABLE', 'UDGTABLE'):
            for params in ('', '(default)', '<nowrap>', '(default)<nowrap>'):
                args = macro + params
                with self.subTest(args=args):
                    self._test_write_skool(snapshot, ctl.replace('*', args), exp_skool.replace('*', args))

    def test_table_without_closing_bracket_on_parameters(self):
        ctl = """
            b 00000
            D 00000 #*(Oops { No closing bracket } TABLE#
            i 00001
        """
        for macro in ('TABLE', 'UDGTABLE'):
            with self.subTest(macro=macro):
                writer = self._get_writer([0], ctl.replace('*', macro))
                with self.assertRaisesRegex(SkoolKitError, re.escape("No closing ')' on parameter list: (Oops { No clos...")):
                    writer.write_skool(0, False)

    def test_table_without_closing_bracket_on_flags(self):
        ctl = """
            b 00000
            D 00000 #*<nowrap { No closing angle bracket } TABLE#
            i 00001
        """
        for macro in ('TABLE', 'UDGTABLE'):
            with self.subTest(macro=macro):
                writer = self._get_writer([0], ctl.replace('*', macro))
                with self.assertRaisesRegex(SkoolKitError, re.escape("No closing '>' on flags: <nowrap { No cl...")):
                    writer.write_skool(0, False)

    def test_table_without_end_marker(self):
        ctl = """
            b 00000
            D 00000 #* { this table has no end marker }
            i 00001
        """
        for macro in ('TABLE', 'UDGTABLE'):
            with self.subTest(macro=macro):
                writer = self._get_writer([0], ctl.replace('*', macro))
                with self.assertRaisesRegex(SkoolKitError, re.escape("No end marker found: #* { this table h...".replace('*', macro))):
                    writer.write_skool(0, False)

    def test_table_without_row_end_marker(self):
        ctl = """
            b 00000
            D 00000 #* { this row has no end marker} TABLE#
            i 00001
        """
        for macro in ('TABLE', 'UDGTABLE'):
            with self.subTest(macro=macro):
                writer = self._get_writer([0], ctl.replace('*', macro))
                with self.assertRaisesRegex(SkoolKitError, re.escape("No closing ' }' on row/item: { this row has ...")):
                    writer.write_skool(0, False)

    def test_list_with_nowrap_flag(self):
        snapshot = [0]
        ctl = """
            b 00000 Test list nowrap flag
            D 00000 #LIST{}<nowrap> {{ This list's items should not be wrapped, because the LIST macro has a nowrap flag }} {{ The nowrap flag is between the angle brackets (<nowrap>) before the first item }} LIST#
            i 00001
        """
        exp_skool = """
            ; Test list nowrap flag
            ;
            ; #LIST{}<nowrap>
            ; {{ This list's items should not be wrapped, because the LIST macro has a nowrap flag }}
            ; {{ The nowrap flag is between the angle brackets (<nowrap>) before the first item }}
            ; LIST#
            b00000 DEFB 0
        """
        for params in ('', '(default)'):
            with self.subTest(params=params):
                self._test_write_skool(snapshot, ctl.format(params), exp_skool.format(params))

    def test_list_with_wrapalign_flag(self):
        snapshot = [0]
        items = (
            '{ The text of this item should wrap over to the next line with a small indent to maintain alignment }',
            '{      The text of this item should wrap over to the next line with a larger indent to maintain alignment }'
        )
        ctl = """
            b 00000 Test list wrapalign flag
            D 00000 #LIST*<wrapalign> {} LIST#
            i 00001
        """.format(' '.join(items))
        exp_skool = """
            ; Test list wrapalign flag
            ;
            ; #LIST*<wrapalign>
            ; { The text of this item should wrap over to the next line with a small indent
            ;   to maintain alignment }
            ; {      The text of this item should wrap over to the next line with a larger
            ;        indent to maintain alignment }
            ; LIST#
            b00000 DEFB 0
        """
        for params in ('', '(default)'):
            with self.subTest(params=params):
                self._test_write_skool(snapshot, ctl.replace('*', params), exp_skool.replace('*', params))

    def test_list_with_no_whitespace_around_items(self):
        snapshot = [0]
        ctl = """
            b 00000 Test no whitespace around items
            D 00000 #LIST{}{{ Item 1 }}{{ Item 2 }}LIST#
            i 00001
        """
        exp_skool = """
            ; Test no whitespace around items
            ;
            ; #LIST{}
            ; {{ Item 1 }}
            ; {{ Item 2 }}
            ; LIST#
            b00000 DEFB 0
        """
        for params in ('', '(default)', '<nowrap>', '(default)<nowrap>'):
            with self.subTest(params=params):
                self._test_write_skool(snapshot, ctl.format(params), exp_skool.format(params))

    def test_list_without_closing_bracket_on_parameters(self):
        ctl = """
            b 00000
            D 00000 #LIST(Oops { No closing bracket } LIST#
            i 00001
        """
        writer = self._get_writer([0], ctl)
        with self.assertRaisesRegex(SkoolKitError, re.escape("No closing ')' on parameter list: (Oops { No clos...")):
            writer.write_skool(0, False)

    def test_list_without_closing_bracket_on_flags(self):
        ctl = """
            b 00000
            D 00000 #LIST<nowrap { No closing angle bracket } LIST#
            i 00001
        """
        writer = self._get_writer([0], ctl)
        with self.assertRaisesRegex(SkoolKitError, re.escape("No closing '>' on flags: <nowrap { No cl...")):
            writer.write_skool(0, False)

    def test_list_without_end_marker(self):
        ctl = """
            b 00000
            D 00000 #LIST { this list has no end marker }
            i 00001
        """
        writer = self._get_writer([0], ctl)
        with self.assertRaisesRegex(SkoolKitError, re.escape("No end marker found: #LIST { this list ha...")):
            writer.write_skool(0, False)

    def test_list_without_item_end_marker(self):
        ctl = """
            b 00000
            D 00000 #LIST { this item has no end marker} LIST#
            i 00001
        """
        writer = self._get_writer([0], ctl)
        with self.assertRaisesRegex(SkoolKitError, re.escape("No closing ' }' on row/item: { this item has...")):
            writer.write_skool(0, False)

    def test_defb_directives(self):
        snapshot = [0] * 5
        ctl = """
            @ 00000 defb=0:1,$02,%11
            @ 00000 defb=3:"Hi" ; Hi
            b 00000 Data defined by @defb directives
            i 00005
        """
        exp_skool = """
            @defb=0:1,$02,%11
            @defb=3:"Hi" ; Hi
            ; Data defined by @defb directives
            b00000 DEFB 1,2,3,72,105
        """
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_defs_directives(self):
        snapshot = [0] * 5
        ctl = """
            @ 00000 defs=0:3,2
            @ 00000 defs=3:2,"!" ; !!
            b 00000 Data defined by @defs directives
            i 00005
        """
        exp_skool = """
            @defs=0:3,2
            @defs=3:2,"!" ; !!
            ; Data defined by @defs directives
            b00000 DEFB 2,2,2,33,33
        """
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_defw_directives(self):
        snapshot = [0] * 6
        ctl = """
            @ 00000 defw=0:257,513
            @ 00000 defw=4:$8001 ; 32769
            b 00000 Data defined by @defw directives
            i 00006
        """
        exp_skool = """
            @defw=0:257,513
            @defw=4:$8001 ; 32769
            ; Data defined by @defw directives
            b00000 DEFB 1,1,1,2,1,128
        """
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_end_directives(self):
        ctl = """
            c 00000 Routine at 0
            @ 00001 end
            @ 00002 end
            c 00002 Routine at 2
            i 00003
        """
        exp_skool = """
            ; Routine at 0
            c00000 XOR A         ;
            @end
             00001 RET           ;

            @end
            ; Routine at 2
            c00002 RET           ;
        """
        snapshot = [175, 201, 201]
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_equ_directives(self):
        ctl = """
            @ 00000 equ=ATTRS=22528
            c 00000 Routine at 0
            @ 00001 equ=UDG=23675
            i 00002
        """
        exp_skool = """
            @equ=ATTRS=22528
            ; Routine at 0
            c00000 XOR A         ;
            @equ=UDG=23675
             00001 RET           ;
        """
        snapshot = [175, 201]
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_if_directives(self):
        ctl = """
            @ 00000 if({asm})(replace=/foo/bar)
            c 00000 Routine at 0
            @ 00001 if({fix})(label=NEXT)
            i 00002
        """
        exp_skool = """
            @if({asm})(replace=/foo/bar)
            ; Routine at 0
            c00000 XOR A         ;
            @if({fix})(label=NEXT)
             00001 RET           ;
        """
        snapshot = [175, 201]
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_org_directives(self):
        ctl = """
            @ 00000 org=0
            c 00000 Routine at 0
            @ 00001 org
            i 00002
        """
        exp_skool = """
            @org=0
            ; Routine at 0
            c00000 XOR A         ;
            @org
             00001 RET           ;
        """
        snapshot = [175, 201]
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_remote_directives(self):
        ctl = """
            @ 00000 remote=main:24576
            c 00000 Routine at 0
            @ 00001 remote=load:32768
            i 00002
        """
        exp_skool = """
            @remote=main:24576
            ; Routine at 0
            c00000 XOR A         ;
            @remote=load:32768
             00001 RET           ;
        """
        snapshot = [175, 201]
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_replace_directives(self):
        ctl = """
            @ 00000 replace=/foo/bar
            c 00000 Routine at 0
            @ 00001 replace=/baz/qux
            i 00002
        """
        exp_skool = """
            @replace=/foo/bar
            ; Routine at 0
            c00000 XOR A         ;
            @replace=/baz/qux
             00001 RET           ;
        """
        snapshot = [175, 201]
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_set_directives(self):
        ctl = """
            @ 00000 set-crlf=1
            c 00000 Routine at 0
            @ 00001 set-tab=1
            i 00002
        """
        exp_skool = """
            @set-crlf=1
            ; Routine at 0
            c00000 XOR A         ;
            @set-tab=1
             00001 RET           ;
        """
        snapshot = [175, 201]
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_start_directives(self):
        ctl = """
            @ 00000 start
            c 00000 Routine at 0
            @ 00001 start
            i 00002
        """
        exp_skool = """
            @start
            ; Routine at 0
            c00000 XOR A         ;
            @start
             00001 RET           ;
        """
        snapshot = [175, 201]
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_writer_directives(self):
        ctl = """
            @ 00000 writer=x.y.z
            c 00000 Routine at 0
            @ 00001 writer=foo.bar.baz
            i 00002
        """
        exp_skool = """
            @writer=x.y.z
            ; Routine at 0
            c00000 XOR A         ;
            @writer=foo.bar.baz
             00001 RET           ;
        """
        snapshot = [175, 201]
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_order_of_entry_asm_directives_is_preserved(self):
        ctl = """
            @ 00000 start
            @ 00000 equ=ATTRS=22528
            @ 00000 replace=/foo/bar
            @ 00000 replace=/baz/qux
            c 00000 Routine at 0
            i 00001
        """
        exp_skool = """
            @start
            @equ=ATTRS=22528
            @replace=/foo/bar
            @replace=/baz/qux
            ; Routine at 0
            c00000 RET           ;
        """
        snapshot = [201]
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_ignoreua_directives(self):
        ctl = """
            @ 10000 ignoreua:t
            c 10000 Routine at 10000
            @ 10000 ignoreua:d
            D 10000 Description of the routine at 10000.
            @ 10000 ignoreua:r
            R 10000 HL 10000
            @ 10000 ignoreua:m
            N 10000 Start comment.
            @ 10000 ignoreua
              10000 Instruction-level comment at 10000
            @ 10001 ignoreua:m
            N 10001 Mid-block comment above 10001.
            @ 10001 ignoreua:i
              10001 Instruction-level comment at 10001
            @ 10000 ignoreua:e
            E 10000 End comment for the routine at 10000.
            i 10002
        """
        exp_skool = """
            @ignoreua
            ; Routine at 10000
            ;
            @ignoreua
            ; Description of the routine at 10000.
            ;
            @ignoreua
            ; HL 10000
            ;
            @ignoreua
            ; Start comment.
            @ignoreua
            c10000 LD A,B        ; Instruction-level comment at 10000
            @ignoreua
            ; Mid-block comment above 10001.
            @ignoreua
             10001 RET           ; Instruction-level comment at 10001
            @ignoreua
            ; End comment for the routine at 10000.
        """
        snapshot = [0] * 10000 + [120, 201]
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_ignoreua_directives_write_refs(self):
        ctl = """
            c 10000 Routine at 10000
            @ 10000 ignoreua:d
            D 10000 Description of the routine at 10000.
            c 10002 Routine at 10002
            @ 10003 ignoreua:m
            N 10003 Mid-block comment above 10003.
            i 10005
        """
        exp_skool = """
            ; Routine at 10000
            ;
            @ignoreua
            ; Used by the routine at #R10002.
            ; .
            ; Description of the routine at 10000.
            c10000 JR 10003      ;

            ; Routine at 10002
            c10002 LD A,B        ;
            @ignoreua
            ; This entry point is used by the routine at #R10000.
            ; .
            ; Mid-block comment above 10003.
            *10003 JR 10000      ;
        """
        snapshot = [0] * 10000 + [24, 1, 120, 24, 251]
        self._test_write_skool(snapshot, ctl, exp_skool, write_refs=2)

    def test_assemble_directives(self):
        ctl = """
            @ 00000 assemble=2,0
            c 00000
            @ 00001 assemble=1
            @ 00002 assemble=0
            i 00003
        """
        exp_skool = """
            @assemble=2,0
            ; Routine at 0
            c00000 NOP           ;
            @assemble=1
             00001 NOP           ;
            @assemble=0
             00002 NOP           ;
        """
        self._test_write_skool([0] * 3, ctl, exp_skool)

    def test_bfix_directives(self):
        ctl = """
            c 00000 Routine at 0
            @ 00000 bfix=XOR B
            @ 00001 bfix=RET Z
            i 00002
        """
        exp_skool = """
            ; Routine at 0
            @bfix=XOR B
            c00000 XOR A         ;
            @bfix=RET Z
             00001 RET           ;
        """
        snapshot = [175, 201]
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_isub_directives(self):
        ctl = """
            c 00000 Routine at 0
            @ 00000 isub=XOR B
            @ 00001 isub=RET Z
            i 00002
        """
        exp_skool = """
            ; Routine at 0
            @isub=XOR B
            c00000 XOR A         ;
            @isub=RET Z
             00001 RET           ;
        """
        snapshot = [175, 201]
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_keep_directives(self):
        ctl = """
            c 00000 Routine at 0
            @ 00000 keep
            @ 00003 keep
            i 00006
        """
        exp_skool = """
            ; Routine at 0
            @keep
            c00000 LD BC,0       ;
            @keep
             00003 LD DE,0       ;
        """
        snapshot = [1, 0, 0, 17, 0, 0]
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_label_directive_marks_entry_point(self):
        ctl = """
            c 00000 Routine at 0
            @ 00001 label=*
            @ 00002 label=*END
            i 00003
        """
        exp_skool = """
            ; Routine at 0
            c00000 XOR A         ;
            @label=*
            *00001 INC A         ;
            @label=*END
            *00002 RET           ;
        """
        snapshot = [175, 60, 201]
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_label_directive_unmarks_entry_point(self):
        ctl = """
            c 00000 Routine at 0
            @ 00001 label=
            c 00002 Routine at 2
            i 00004
        """
        exp_skool = """
            ; Routine at 0
            c00000 XOR A         ;
            @label=
             00001 RET           ;

            ; Routine at 2
            c00002 JR 1          ;
        """
        snapshot = [175, 201, 24, 253]
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_nowarn_directive(self):
        ctl = """
            c 00000 Routine at 0
            @ 00000 nowarn
            i 00004
        """
        exp_skool = """
            ; Routine at 0
            @nowarn
            c00000 LD BC,3       ;
             00003 RET           ;
        """
        snapshot = [1, 3, 0, 201]
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_ofix_directives(self):
        ctl = """
            c 00000 Routine at 0
            @ 00000 ofix=LD A,0
            @ 00002 ofix=LD B,0
            i 00004
        """
        exp_skool = """
            ; Routine at 0
            @ofix=LD A,0
            c00000 LD A,1        ;
            @ofix=LD B,0
             00002 LD B,1        ;
        """
        snapshot = [62, 1, 6, 1]
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_rem_directives(self):
        ctl = """
            c 00000 Routine at 0
            @ 00000 rem=It begins
            @ 00001 rem=Done
            i 00002
        """
        exp_skool = """
            ; Routine at 0
            @rem=It begins
            c00000 XOR A         ;
            @rem=Done
             00001 RET           ;
        """
        snapshot = [175, 201]
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_rfix_directive(self):
        ctl = """
            c 00000
            @ 00000 rfix=LD DE,0
            i 00002
        """
        exp_skool = """
            ; Routine at 0
            @rfix=LD DE,0
            c00000 LD D,0        ;
        """
        self._test_write_skool([22, 0], ctl, exp_skool)

    def test_rsub_directives(self):
        ctl = """
            c 00000 Routine at 0
            @ 00000 rsub=LD BC,0
            @ 00002 rsub=LD DE,0
            i 00004
        """
        exp_skool = """
            ; Routine at 0
            @rsub=LD BC,0
            c00000 LD B,0        ;
            @rsub=LD DE,0
             00002 LD E,0        ;
        """
        snapshot = [6, 0, 30, 0]
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_ssub_directives(self):
        ctl = """
            c 00000 Routine at 0
            @ 00000 ssub=LD A,32768%256
            @ 00002 ssub=LD B,32768%256
            i 00004
        """
        exp_skool = """
            ; Routine at 0
            @ssub=LD A,32768%256
            c00000 LD A,0        ;
            @ssub=LD B,32768%256
             00002 LD B,0        ;
        """
        snapshot = [62, 0, 6, 0]
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_header(self):
        ctl = """
            > 00000 ; This is a header.
            c 00000 Routine
            i 00001
        """
        exp_skool = """
            ; This is a header.

            ; Routine
            c00000 RET           ;
        """
        snapshot = [201]
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_two_headers(self):
        ctl = """
            > 00000 ; This is a header.
            > 00000
            > 00000 ; This is another header.
            c 00000 Routine
            i 00001
        """
        exp_skool = """
            ; This is a header.

            ; This is another header.

            ; Routine
            c00000 RET           ;
        """
        snapshot = [201]
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_header_before_second_entry(self):
        ctl = """
            c 00000 Routine
            > 00001 ; This is between two entries.
            c 00001 Another routine
            i 00002
        """
        exp_skool = """
            ; Routine
            c00000 RET           ;

            ; This is between two entries.

            ; Another routine
            c00001 RET           ;
        """
        snapshot = [201, 201]
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_header_unaffected_by_dot_directives(self):
        ctl = """
            > 00000 ; This is the start of the header.
            . This is an intervening dot directive.
            > 00000 ; This is the end of the header.
            . Another dot directive to ignore.
            c 00000 Routine
            i 00001
        """
        exp_skool = """
            ; This is the start of the header.
            ; This is the end of the header.

            ; Routine
            c00000 RET           ;
        """
        snapshot = [201]
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_footer(self):
        ctl = """
            c 00000 Routine
            > 00000,1 ; This is a footer.
            i 00001
        """
        exp_skool = """
            ; Routine
            c00000 RET           ;

            ; This is a footer.
        """
        snapshot = [201]
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_two_footers(self):
        ctl = """
            c 00000 Routine
            > 00000,1 ; This is a footer.
            > 00000,1
            > 00000,1 ; This is another footer.
            i 00001
        """
        exp_skool = """
            ; Routine
            c00000 RET           ;

            ; This is a footer.

            ; This is another footer.
        """
        snapshot = [201]
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_footer_unaffected_by_dot_directives(self):
        ctl = """
            c 00000 Routine
            > 00000,1 ; This is the start of the footer.
            . This is an intervening dot directive.
            > 00000,1 ; This is the end of the footer.
            . Another dot directive to ignore.
            i 00001
        """
        exp_skool = """
            ; Routine
            c00000 RET           ;

            ; This is the start of the footer.
            ; This is the end of the footer.
        """
        snapshot = [201]
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_registers(self):
        ctl = """
            c 00000 Routine
            R 00000 BC This register description is long enough that it needs to be split over two lines
            R 00000 DE Short register description
            R 00000
            R 00000 HL Another register description that is long enough to need splitting over two lines
            R 00000 IX
            i 00001
        """
        exp_skool = """
            ; Routine
            ;
            ; .
            ;
            ; BC This register description is long enough that it needs to be split over
            ; .  two lines
            ; DE Short register description
            ; HL Another register description that is long enough to need splitting over
            ; .  two lines
            ; IX
            c00000 NOP           ;
        """
        self._test_write_skool([0], ctl, exp_skool)

    def test_registers_with_prefixes(self):
        ctl = """
            c 00000 Routine
            R 00000 Input:A An important parameter with a long description that will be split over two lines
            R 00000 B Another important parameter
            R 00000 Output:DE The result
            R 00000 HL
            i 00001
        """
        exp_skool = """
            ; Routine
            ;
            ; .
            ;
            ;  Input:A An important parameter with a long description that will be split
            ; .        over two lines
            ;        B Another important parameter
            ; Output:DE The result
            ;        HL
            c00000 NOP           ;
        """
        self._test_write_skool([0], ctl, exp_skool)

    def test_start_comment(self):
        ctl = """
            c 00000
            N 00000 Start comment.
            i 00001
        """
        exp_skool = """
            ; Routine at 0
            ;
            ; .
            ;
            ; .
            ;
            ; Start comment.
            c00000 NOP           ;
        """
        self._test_write_skool([0], ctl, exp_skool)

    def test_multi_paragraph_start_comment(self):
        ctl = """
            c 00000 Routine
            D 00000 Description.
            N 00000 Start comment paragraph 1.
            N 00000 Paragraph 2.
            i 00001
        """
        exp_skool = """
            ; Routine
            ;
            ; Description.
            ;
            ; .
            ;
            ; Start comment paragraph 1.
            ; .
            ; Paragraph 2.
            c00000 NOP           ;
        """
        self._test_write_skool([0], ctl, exp_skool)

    def test_loop(self):
        ctl = """
            b 00000 Two bytes and one word, times ten
            B 00000,2
            W 00002
            L 00000,4,10
            i 00040
        """
        writer = self._get_writer([0] * 40, ctl)
        writer.write_skool(0, False)
        skool = self.out.getvalue().split('\n')[:-2]
        address = 0
        ctl = 'b'
        for i in range(1, 21, 2):
            self.assertEqual(skool[i], '{}{:05} DEFB 0,0'.format(ctl, address))
            self.assertEqual(skool[i + 1], ' {:05} DEFW 0'.format(address + 2))
            ctl = ' '
            address += 4

    def test_loop_with_entries(self):
        ctl = """
            b 00000 A block of five pairs of bytes
            B 00000,10,2
            L 00000,10,3,1
            i 00030
        """
        writer = self._get_writer([0] * 30, ctl)
        writer.write_skool(0, False)
        skool = self.out.getvalue().split('\n')[:-2]
        address = 0
        index = 1
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
        ctl = """
            c 00000
            M 00000,3 This is really LD A,0
            B 00000,1
            N 00002 This comment should not be swallowed by the overlong M directive.
            i 00003
        """
        exp_skool = """
            ; Routine at 0
            c00000 DEFB 62       ; {This is really LD A,0
             00001 NOP           ; }
            ; This comment should not be swallowed by the overlong M directive.
             00002 RET           ;
        """
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_lower_case_hexadecimal(self):
        snapshot = [0] * 10 + [255]
        ctl = """
            b 00010
            i 00011
        """
        exp_skool = """
            ; Data block at 000a
            b$000a defb $ff
        """
        self._test_write_skool(snapshot, ctl, exp_skool, base=16, case=1)

    def test_comment_width_min_small(self):
        snapshot = [100] * 75
        ctl = """
            b 00000
              00000,75,15 One word per line
            i 00075
        """
        exp_skool = """
            ; Data block at 0
            b00000 DEFB 100,100,100,100,100,100,100,100,100,100,100,100,100,100,100 ; {One
             00015 DEFB 100,100,100,100,100,100,100,100,100,100,100,100,100,100,100 ; word
             00030 DEFB 100,100,100,100,100,100,100,100,100,100,100,100,100,100,100 ; per
             00045 DEFB 100,100,100,100,100,100,100,100,100,100,100,100,100,100,100 ; line
             00060 DEFB 100,100,100,100,100,100,100,100,100,100,100,100,100,100,100 ; }
        """
        self._test_write_skool(snapshot, ctl, exp_skool, params={'CommentWidthMin': 4})

    def test_comment_width_min_large(self):
        snapshot = [100] * 30
        ctl = """
            b 00000
              00000,30,15 At least 23 characters on each comment line
            i 00030
        """
        exp_skool = """
            ; Data block at 0
            b00000 DEFB 100,100,100,100,100,100,100,100,100,100,100,100,100,100,100 ; {At least 23 characters
             00015 DEFB 100,100,100,100,100,100,100,100,100,100,100,100,100,100,100 ; on each comment line}
        """
        self._test_write_skool(snapshot, ctl, exp_skool, params={'CommentWidthMin': 23})

    def test_defm_size(self):
        snapshot = [65] * 4
        ctl = """
            t 00000
            i 00004
        """
        exp_skool = """
            ; Message at 0
            t00000 DEFM "AA"
             00002 DEFM "AA"
        """
        self._test_write_skool(snapshot, ctl, exp_skool, params={'DefmSize': 2})

    def test_defb_mod(self):
        snapshot = [0] * 14
        ctl = """
            b 00002
            i 00014
        """
        exp_skool = """
            ; Data block at 2
            b00002 DEFB 0,0
             00004 DEFB 0,0,0,0,0,0,0,0
             00012 DEFB 0,0
        """
        self._test_write_skool(snapshot, ctl, exp_skool, params={'DefbMod': 4})

    def test_defb_size(self):
        snapshot = [0] * 5
        ctl = """
            b 00000
            i 00005
        """
        exp_skool = """
            ; Data block at 0
            b00000 DEFB 0,0,0
             00003 DEFB 0,0
        """
        self._test_write_skool(snapshot, ctl, exp_skool, params={'DefbSize': 3})

    def test_instruction_width_very_small(self):
        snapshot = [175, 201]
        ctl = """
            c 00000
              00000 These comments should
              00001 hug the instructions
            i 00002
        """
        exp_skool = """
            ; Routine at 0
            c00000 XOR A ; These comments should
             00001 RET   ; hug the instructions
        """
        self._test_write_skool(snapshot, ctl, exp_skool, params={'InstructionWidth': 1})

    def test_instruction_width_small(self):
        snapshot = [175, 201]
        ctl = """
            c 00000
              00000 These comments should be
              00001 close to the instructions
            i 00002
        """
        exp_skool = """
            ; Routine at 0
            c00000 XOR A   ; These comments should be
             00001 RET     ; close to the instructions
        """
        self._test_write_skool(snapshot, ctl, exp_skool, params={'InstructionWidth': 7})

    def test_instruction_width_large(self):
        snapshot = [175, 201]
        ctl = """
            c 00000
              00000 These comments should be far
              00001 away from the instructions
            i 00002
        """
        exp_skool = """
            ; Routine at 0
            c00000 XOR A             ; These comments should be far
             00001 RET               ; away from the instructions
        """
        self._test_write_skool(snapshot, ctl, exp_skool, params={'InstructionWidth': 17})

    def test_semicolons_bcgi(self):
        snapshot = [0, 201, 0, 0, 0, 65, 0, 0, 0]
        ctl = """
            b 00000
            c 00001
            g 00002
            i 00003
            B 00003
            s 00004
            t 00005
            u 00006
            w 00007
            i 00009
        """
        exp_skool = """
            ; Data block at 0
            b00000 DEFB 0        ;

            ; Routine at 1
            c00001 RET           ;

            ; Game status buffer entry at 2
            g00002 DEFB 0        ;

            i00003 DEFB 0        ;

            ; Unused
            s00004 DEFS 1

            ; Message at 5
            t00005 DEFM "A"

            ; Unused
            u00006 DEFB 0

            ; Data block at 7
            w00007 DEFW 0
        """
        self._test_write_skool(snapshot, ctl, exp_skool, params={'Semicolons': 'bcgi'})

    def test_semicolons_stuw(self):
        snapshot = [0, 201, 0, 0, 0, 65, 0, 0, 0]
        ctl = """
            b 00000
            c 00001
            g 00002
            i 00003
            B 00003
            s 00004
            t 00005
            u 00006
            w 00007
            i 00009
        """
        exp_skool = """
            ; Data block at 0
            b00000 DEFB 0

            ; Routine at 1
            c00001 RET

            ; Game status buffer entry at 2
            g00002 DEFB 0

            i00003 DEFB 0

            ; Unused
            s00004 DEFS 1        ;

            ; Message at 5
            t00005 DEFM "A"      ;

            ; Unused
            u00006 DEFB 0        ;

            ; Data block at 7
            w00007 DEFW 0        ;
        """
        self._test_write_skool(snapshot, ctl, exp_skool, params={'Semicolons': 'stuw'})

    def test_zfill(self):
        snapshot = [0] * 5
        ctl = """
            b 00000
            i 00005
        """
        exp_skool = """
            ; Data block at 0
            b00000 DEFB 000,000,000,000,000
        """
        self._test_write_skool(snapshot, ctl, exp_skool, params={'DefbZfill': 1})

    def test_show_text(self):
        snapshot = [49, 127, 50]
        ctl = """
            c 00000
            i 00003
        """
        exp_skool = """
            ; Routine at 0
            c00000 LD SP,12927   ; [1.2]
        """
        self._test_write_skool(snapshot, ctl, exp_skool, show_text=True)

    def test_braces_in_instruction_comments(self):
        snapshot = [0] * 39
        ctl = """
            b 00000
              00000,1,1 {unmatched opening brace
              00001,1,1 unmatched closing brace}
              00002,1,1 {matched braces}
              00003,2,1 {unmatched opening brace
              00005,2,1 unmatched closing brace}
              00007,2,1 {matched braces}
              00009,2,1 { unmatched opening brace with a space
              00011,2,1 unmatched closing brace with a space }
              00013,2,1 { matched braces with spaces }
              00015,1,1 {{unmatched opening braces}
              00016,1,1 {unmatched closing braces}}
              00017,1,1 {{matched pairs of braces}}
              00018,2,1 {{unmatched opening braces}
              00020,2,1 {unmatched closing braces}}
              00022,2,1 {{matched pairs of braces}}
              00024,2,1 {{{unmatched opening braces on a comment that spans two lines}}
              00026,2,1 {{unmatched closing braces on a comment that spans two lines}}}
              00028,2,1 {{{matched pairs of braces on a comment that spans two lines}}}
              00030,1,1 unmatched {opening brace in the middle
              00031,1,1 unmatched closing brace} in the middle
              00032,1,1 matched {braces} in the middle
              00033,2,1 unmatched {opening brace in the middle
              00035,2,1 unmatched closing brace} in the middle
              00037,2,1 matched {{braces}} in the middle
            i 00039
        """
        exp_skool = """
            ; Data block at 0
            b00000 DEFB 0        ; { {unmatched opening brace}}
             00001 DEFB 0        ; unmatched closing brace}
             00002 DEFB 0        ; { {matched braces} }
             00003 DEFB 0        ; { {unmatched opening brace
             00004 DEFB 0        ; }}
             00005 DEFB 0        ; {{unmatched closing brace}
             00006 DEFB 0        ; }
             00007 DEFB 0        ; { {matched braces}
             00008 DEFB 0        ; }
             00009 DEFB 0        ; { { unmatched opening brace with a space
             00010 DEFB 0        ; }}
             00011 DEFB 0        ; {{unmatched closing brace with a space }
             00012 DEFB 0        ; }
             00013 DEFB 0        ; { { matched braces with spaces }
             00014 DEFB 0        ; }
             00015 DEFB 0        ; { {{unmatched opening braces} }}
             00016 DEFB 0        ; { {unmatched closing braces}} }
             00017 DEFB 0        ; { {{matched pairs of braces}} }
             00018 DEFB 0        ; { {{unmatched opening braces}
             00019 DEFB 0        ; }}
             00020 DEFB 0        ; {{ {unmatched closing braces}}
             00021 DEFB 0        ; }
             00022 DEFB 0        ; { {{matched pairs of braces}}
             00023 DEFB 0        ; }
             00024 DEFB 0        ; { {{{unmatched opening braces on a comment that spans
             00025 DEFB 0        ; two lines}} }}
             00026 DEFB 0        ; {{ {{unmatched closing braces on a comment that spans
             00027 DEFB 0        ; two lines}}} }
             00028 DEFB 0        ; { {{{matched pairs of braces on a comment that spans two
             00029 DEFB 0        ; lines}}} }
             00030 DEFB 0        ; unmatched {opening brace in the middle
             00031 DEFB 0        ; unmatched closing brace} in the middle
             00032 DEFB 0        ; matched {braces} in the middle
             00033 DEFB 0        ; {unmatched {opening brace in the middle
             00034 DEFB 0        ; }}
             00035 DEFB 0        ; {{unmatched closing brace} in the middle
             00036 DEFB 0        ; }
             00037 DEFB 0        ; {matched {{braces}} in the middle
             00038 DEFB 0        ; }
        """
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_ignore_blocks_with_no_title_and_no_sub_blocks(self):
        snapshot = [0] * 3
        ctl = """
            b 00000
            i 00001
            b 00002
            i 00003
        """
        exp_skool = """
            ; Data block at 0
            b00000 DEFB 0

            i00001

            ; Data block at 2
            b00002 DEFB 0
        """
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_ignore_blocks_with_title_but_no_sub_blocks(self):
        snapshot = [0] * 3
        ctl = """
            b 00000
            i 00001 The middle
            b 00002
            i 00003 The end
        """
        exp_skool = """
            ; Data block at 0
            b00000 DEFB 0

            ; The middle
            i00001

            ; Data block at 2
            b00002 DEFB 0

            ; The end
            i00003
        """
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_ignore_blocks_with_sub_block_but_no_title(self):
        snapshot = [0] * 4
        ctl = """
            b 00000
            i 00001
            B 00001
            b 00002
            i 00003
            S 00003
            i 00004
        """
        exp_skool = """
            ; Data block at 0
            b00000 DEFB 0

            i00001 DEFB 0

            ; Data block at 2
            b00002 DEFB 0

            i00003 DEFS 1
        """
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_ignore_blocks_with_title_and_sub_block(self):
        snapshot = [0] * 4
        ctl = """
            b 00000
            i 00001 The middle
            S 00001
            b 00002
            i 00003 The end
            D 00003 Unused from here on out.
            S 00003
            i 00004
        """
        exp_skool = """
            ; Data block at 0
            b00000 DEFB 0

            ; The middle
            i00001 DEFS 1

            ; Data block at 2
            b00002 DEFB 0

            ; The end
            ;
            ; Unused from here on out.
            i00003 DEFS 1
        """
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_ignore_block_with_description_but_no_title(self):
        snapshot = [0] * 3
        ctl = """
            b 00000
            i 00001
            D 00001 Unused from here on out.
        """
        exp_skool = """
            ; Data block at 0
            b00000 DEFB 0

            ; Ignored
            ;
            ; Unused from here on out.
            i00001
        """
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_ignore_block_with_registers_but_no_title(self):
        snapshot = [0, 201]
        ctl = """
            b 00000
            i 00001
            R 00001 A 0
            C 00001,1
            i 00002
        """
        exp_skool = """
            ; Data block at 0
            b00000 DEFB 0

            ; Ignored
            ;
            ; .
            ;
            ; A 0
            i00001 RET
        """
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_ignore_block_with_start_comment_but_no_title(self):
        snapshot = [0]
        ctl = """
            b 00000
            i 00001
            N 00001 It ends here.
        """
        exp_skool = """
            ; Data block at 0
            b00000 DEFB 0

            ; Ignored
            ;
            ; .
            ;
            ; .
            ;
            ; It ends here.
            i00001
        """
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_references_to_and_from_a_non_code_block(self):
        snapshot = [24, 0, 24, 0, 24, 250]
        ctl = """
            c 00000
            b 00002
            C 00002 This will create a reference
            C 00004 And so will this
            i 00006
        """
        exp_skool = """
            ; Routine at 0
            ;
            ; Used by the routine at #R2.
            c00000 JR 2          ;

            ; Data block at 2
            ;
            ; Used by the routine at #R0.
            b00002 JR 4          ; This will create a reference
            *00004 JR 0          ; And so will this
        """
        self._test_write_skool(snapshot, ctl, exp_skool, write_refs=2)

    def test_references_to_and_from_an_unused_code_block(self):
        snapshot = [24, 0, 24, 0, 24, 250]
        ctl = """
            c 00000
            u 00002
            C 00002 This will create a reference
            C 00004 But this won't
            i 00006
        """
        exp_skool = """
            ; Routine at 0
            c00000 JR 2          ;

            ; Unused
            ;
            ; Used by the routine at #R0.
            u00002 JR 4          ; This will create a reference
            *00004 JR 0          ; But this won't
        """
        self._test_write_skool(snapshot, ctl, exp_skool, write_refs=2)

    def test_M_directive_terminates_previous_sub_block(self):
        snapshot = [120, 207, 2]
        ctl = """
            c 00000
              00000 This sub-block is terminated by the M directive
            M 00001,2 This spans an implicit "C" sub-block and a "B" sub-block
            B 00002,1
            i 00003
        """
        exp_skool = """
            ; Routine at 0
            c00000 LD A,B        ; This sub-block is terminated by the M directive
             00001 RST 8         ; {This spans an implicit "C" sub-block and a "B"
             00002 DEFB 2        ; sub-block}
        """
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_custom_Ref(self):
        params = {'Ref': 'Used by the subroutine at {ref}.'}
        snapshot = [201, 24, 253]
        ctl = """
            c 00000
            c 00001
            i 00003
        """
        exp_skool = """
            ; Routine at 0
            ;
            ; Used by the subroutine at #R1.
            c00000 RET           ;

            ; Routine at 1
            c00001 JR 0          ;
        """
        self._test_write_skool(snapshot, ctl, exp_skool, params=params)

    def test_invalid_custom_Ref(self):
        params = {'Ref': 'Used by the subroutine at {ref:04X}.'}
        snapshot = [201, 24, 253]
        ctl = """
            c 00000
            c 00001
            i 00003
        """
        writer = self._get_writer(snapshot, ctl, params=params)

        with self.assertRaisesRegex(SkoolKitError, "^Failed to format Ref template: Unknown format code 'X' for object of type 'str'$"):
            writer.write_skool(1, 0)

    def test_custom_Refs_with_two_referrers(self):
        params = {'Refs': 'Used by the subroutines at {refs} and {ref}.'}
        snapshot = [201, 24, 253, 24, 251]
        ctl = """
            c 00000
            c 00001
            c 00003
            i 00005
        """
        exp_skool = """
            ; Routine at 0
            ;
            ; Used by the subroutines at #R1 and #R3.
            c00000 RET           ;

            ; Routine at 1
            c00001 JR 0          ;

            ; Routine at 3
            c00003 JR 0          ;
        """
        self._test_write_skool(snapshot, ctl, exp_skool, params=params)

    def test_custom_Refs_with_three_referrers(self):
        params = {'Refs': 'Used by the subroutines at {refs} and {ref}.'}
        snapshot = [201, 24, 253, 24, 251, 24, 249]
        ctl = """
            c 00000
            c 00001
            c 00003
            c 00005
            i 00007
        """
        exp_skool = """
            ; Routine at 0
            ;
            ; Used by the subroutines at #R1, #R3 and #R5.
            c00000 RET           ;

            ; Routine at 1
            c00001 JR 0          ;

            ; Routine at 3
            c00003 JR 0          ;

            ; Routine at 5
            c00005 JR 0          ;
        """
        self._test_write_skool(snapshot, ctl, exp_skool, params=params)

    def test_invalid_custom_Refs(self):
        params = {'Refs': 'Used by the subroutines at {refs} and {lastref}.'}
        snapshot = [201, 24, 253, 24, 251]
        ctl = """
            c 00000
            c 00001
            c 00003
            i 00005
        """
        writer = self._get_writer(snapshot, ctl, params=params)

        with self.assertRaisesRegex(SkoolKitError, "^Unknown field 'lastref' in Refs template$"):
            writer.write_skool(1, 0)

    def test_custom_EntryPointRef(self):
        params = {'EntryPointRef': 'Used by the subroutine at {ref}.'}
        snapshot = [175, 201, 24, 253]
        ctl = """
            c 00000
            c 00002
            i 00004
        """
        exp_skool = """
            ; Routine at 0
            c00000 XOR A         ;
            ; Used by the subroutine at #R2.
            *00001 RET           ;

            ; Routine at 2
            c00002 JR 1          ;
        """
        self._test_write_skool(snapshot, ctl, exp_skool, params=params)

    def test_invalid_custom_EntryPointRef(self):
        params = {'EntryPointRef': 'Used by the subroutine at {ref:04x}.'}
        snapshot = [175, 201, 24, 253]
        ctl = """
            c 00000
            c 00002
            i 00004
        """
        writer = self._get_writer(snapshot, ctl, params=params)

        with self.assertRaisesRegex(SkoolKitError, "^Failed to format EntryPointRef template: Unknown format code 'x' for object of type 'str'$"):
            writer.write_skool(1, 0)

    def test_custom_EntryPointRefs_with_two_referrers(self):
        params = {'EntryPointRefs': 'Used by the subroutines at {refs} and {ref}.'}
        snapshot = [175, 201, 24, 253, 24, 251]
        ctl = """
            c 00000
            c 00002
            c 00004
            i 00006
        """
        exp_skool = """
            ; Routine at 0
            c00000 XOR A         ;
            ; Used by the subroutines at #R2 and #R4.
            *00001 RET           ;

            ; Routine at 2
            c00002 JR 1          ;

            ; Routine at 4
            c00004 JR 1          ;
        """
        self._test_write_skool(snapshot, ctl, exp_skool, params=params)

    def test_custom_EntryPointRefs_with_three_referrers(self):
        params = {'EntryPointRefs': 'Used by the subroutines at {refs} and {ref}.'}
        snapshot = [175, 201, 24, 253, 24, 251, 24, 249]
        ctl = """
            c 00000
            c 00002
            c 00004
            c 00006
            i 00008
        """
        exp_skool = """
            ; Routine at 0
            c00000 XOR A         ;
            ; Used by the subroutines at #R2, #R4 and #R6.
            *00001 RET           ;

            ; Routine at 2
            c00002 JR 1          ;

            ; Routine at 4
            c00004 JR 1          ;

            ; Routine at 6
            c00006 JR 1          ;
        """
        self._test_write_skool(snapshot, ctl, exp_skool, params=params)

    def test_invalid_custom_EntryPointRefs(self):
        params = {'EntryPointRefs': 'Used by the subroutines at {refs} and {finalref}.'}
        snapshot = [175, 201, 24, 253, 24, 251, 24, 249]
        ctl = """
            c 00000
            c 00002
            c 00004
            c 00006
            i 00008
        """
        writer = self._get_writer(snapshot, ctl, params=params)

        with self.assertRaisesRegex(SkoolKitError, "^Unknown field 'finalref' in EntryPointRefs template$"):
            writer.write_skool(1, 0)

    def test_custom_config_passed_to_disassembly(self):
        params = {
            'Title-b': 'Data at {address}',
            'Title-c': 'Code at {address}'
        }
        snapshot = [201, 0]
        ctl = """
            c 00000
            b 00001
            i 00002
        """
        exp_skool = """
            ; Code at 0
            c00000 RET           ;

            ; Data at 1
            b00001 DEFB 0
        """
        self._test_write_skool(snapshot, ctl, exp_skool, params=params)

    def test_comment_semicolons(self):
        snapshot = [0] * 48
        ctl = """
            c 00000
              00000,3 Even the blank comment line has a semicolon
            N 00003 Every line in a code block has semicolon even when there's no comment
            b 00006
              00006,3,1 Even the blank comment line has a semicolon
            N 00009 No semicolons in a data block when there's no comment
              00009,3,1
            g 00012
              00012,3,1 Even the blank comment line has a semicolon
            N 00015 No semicolons in a data block when there's no comment
              00015,3,1
            s 00018
              00018,3,1 Even the blank comment line has a semicolon
            N 00021 No semicolons in a data block when there's no comment
              00021,3,1
            t 00024
            B 00024,3,1 Even the blank comment line has a semicolon
            N 00027 No semicolons in a data block when there's no comment
            B 00027,3,1
            u 00030
              00030,3,1 Even the blank comment line has a semicolon
            N 00033 No semicolons in a data block when there's no comment
              00033,3,1
            w 00036
              00036,6,2 Even the blank comment line has a semicolon
            N 00042 No semicolons in a data block when there's no comment
              00042,6,2
            i 00048
        """
        exp_skool = """
            ; Routine at 0
            c00000 NOP           ; {Even the blank comment line has a semicolon
             00001 NOP           ;
             00002 NOP           ; }
            ; Every line in a code block has semicolon even when there's no comment
             00003 NOP           ;
             00004 NOP           ;
             00005 NOP           ;

            ; Data block at 6
            b00006 DEFB 0        ; {Even the blank comment line has a semicolon
             00007 DEFB 0        ;
             00008 DEFB 0        ; }
            ; No semicolons in a data block when there's no comment
             00009 DEFB 0
             00010 DEFB 0
             00011 DEFB 0

            ; Game status buffer entry at 12
            g00012 DEFB 0        ; {Even the blank comment line has a semicolon
             00013 DEFB 0        ;
             00014 DEFB 0        ; }
            ; No semicolons in a data block when there's no comment
             00015 DEFB 0
             00016 DEFB 0
             00017 DEFB 0

            ; Unused
            s00018 DEFS 1        ; {Even the blank comment line has a semicolon
             00019 DEFS 1        ;
             00020 DEFS 1        ; }
            ; No semicolons in a data block when there's no comment
             00021 DEFS 1
             00022 DEFS 1
             00023 DEFS 1

            ; Message at 24
            t00024 DEFB 0        ; {Even the blank comment line has a semicolon
             00025 DEFB 0        ;
             00026 DEFB 0        ; }
            ; No semicolons in a data block when there's no comment
             00027 DEFB 0
             00028 DEFB 0
             00029 DEFB 0

            ; Unused
            u00030 DEFB 0        ; {Even the blank comment line has a semicolon
             00031 DEFB 0        ;
             00032 DEFB 0        ; }
            ; No semicolons in a data block when there's no comment
             00033 DEFB 0
             00034 DEFB 0
             00035 DEFB 0

            ; Data block at 36
            w00036 DEFW 0        ; {Even the blank comment line has a semicolon
             00038 DEFW 0        ;
             00040 DEFW 0        ; }
            ; No semicolons in a data block when there's no comment
             00042 DEFW 0
             00044 DEFW 0
             00046 DEFW 0
        """
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_newlines_in_entry_titles(self):
        snapshot = [0] * 13
        ctl = """
            b 00000 The title of this entry
            . spans two lines
            c 00001 The title of this entry spans only one line even though it would normally be wrapped over two lines
            .
            g 00002
            . The title
            . of this entry
            . spans three lines
            i 00003 Testing the
            . dot directive
            s 00004
            . Another long entry title that spans only one line but would normally be wrapped over two lines
            t 00005 One
            . two
            u 00006 One
            . two
            . three
            w 00007 Yet another entry title on one line that is long enough to be wrapped over two lines normally
            .
            ; Test a blank title with a blank continuation line
            b 00008
            .
            c 00009
            . Line 1 here
            g 00010
            . Trailing blank line
            .
            i 00011
            .
            . Leading blank line
            s 00012
            . Title
            .
            . Description paragraph 1.
            . .
            . Description paragraph 2.
            .
            . A The accumulator
            .
            . Start comment paragraph 1.
            . .
            . Start comment paragraph 2.
            i 00013
        """
        exp_skool = """
            ; The title of this entry
            ; spans two lines
            b00000 DEFB 0

            ; The title of this entry spans only one line even though it would normally be wrapped over two lines
            c00001 NOP           ;

            ; The title
            ; of this entry
            ; spans three lines
            g00002 DEFB 0

            ; Testing the
            ; dot directive
            i00003

            ; Another long entry title that spans only one line but would normally be wrapped over two lines
            s00004 DEFS 1

            ; One
            ; two
            t00005 DEFB 0

            ; One
            ; two
            ; three
            u00006 DEFB 0

            ; Yet another entry title on one line that is long enough to be wrapped over two lines normally
            w00007 DEFW 0

            ; Data block at 8
            b00008 DEFB 0

            ; Line 1 here
            c00009 NOP           ;

            ; Trailing blank line
            g00010 DEFB 0

            ; Leading blank line
            i00011

            ; Title
            ;
            ; Description paragraph 1.
            ; .
            ; Description paragraph 2.
            ;
            ; A The accumulator
            ;
            ; Start comment paragraph 1.
            ; .
            ; Start comment paragraph 2.
            s00012 DEFS 1
        """
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_newlines_in_instruction_comments(self):
        snapshot = [0] * 23
        ctl = """
            b 00000 Newline test
            B 00000,1 This comment
            . spans two lines
            C 00001
            . This comment spans only one line even though it would normally be wrapped over two lines
            S 00002,2,1 Line 1
            . Line 2
            T 00004
            . One
            . two
            . three
            W 00005,4,2 First word
            . Second word
            . No third word
            ; Blank comment
            B 00009,1
            .
            C 00010,1
            . Line 1 here
            S 00011,1
            . Trailing blank line
            .
            T 00012,1
            .
            . Leading blank line
            W 00013,2
            . Line 1
            .
            . Line 3 (with a blank line 2)
            ; Blank comment over two instructions
            B 00015,2,1
            .
            ; Comments consisting of a single dot
            B 00017,1
            . .
            B 00018,2,1
            . .
            ; Comments consisting of two dots
            B 00020,1
            . ..
            B 00021,2,1
            . ..
            i 00023
        """
        exp_skool = """
            ; Newline test
            b00000 DEFB 0        ; This comment
                                 ; spans two lines
             00001 NOP           ; This comment spans only one line even though it would normally be wrapped over two lines
             00002 DEFS 1        ; {Line 1
             00003 DEFS 1        ; Line 2}
             00004 DEFB 0        ; One
                                 ; two
                                 ; three
             00005 DEFW 0        ; {First word
             00007 DEFW 0        ; Second word
                                 ; No third word}
             00009 DEFB 0        ;
             00010 NOP           ; Line 1 here
             00011 DEFS 1        ; Trailing blank line
                                 ;
             00012 DEFB 0        ;
                                 ; Leading blank line
             00013 DEFW 0        ; Line 1
                                 ;
                                 ; Line 3 (with a blank line 2)
             00015 DEFB 0        ; {
             00016 DEFB 0        ; }
             00017 DEFB 0        ; .
             00018 DEFB 0        ; {.
             00019 DEFB 0        ; }
             00020 DEFB 0        ; ..
             00021 DEFB 0        ; {..
             00022 DEFB 0        ; }
        """
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_newlines_in_entry_descriptions(self):
        snapshot = [0]
        ctl = """
            b 00000
            D 00000 This description
            . spans two lines.
            D 00000 This description spans only one line even though it would normally be wrapped over two lines.
            .
            D 00000
            . This description
            . spans three
            . lines.
            D 00000
            . Another long description that spans only one line but would normally be wrapped over two lines.
            ; Test a blank description with a blank continuation line (should be ignored)
            D 00000
            .
            D 00000
            . Trailing blank line.
            .
            D 00000
            .
            . Leading blank line.
            D 00000
            . Paragraph 1.
            .
            . Paragraph 2.
            i 00001
        """
        exp_skool = """
            ; Data block at 0
            ;
            ; This description
            ; spans two lines.
            ; .
            ; This description spans only one line even though it would normally be wrapped over two lines.
            ; .
            ; This description
            ; spans three
            ; lines.
            ; .
            ; Another long description that spans only one line but would normally be wrapped over two lines.
            ; .
            ; Trailing blank line.
            ; .
            ; Leading blank line.
            ; .
            ; Paragraph 1.
            ; .
            ; Paragraph 2.
            b00000 DEFB 0
        """
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_newlines_in_block_start_and_mid_block_comments(self):
        snapshot = [0] * 2
        ctl = """
            b 00000
            N 00000 This comment
            . spans two lines.
            N 00000 This comment spans only one line even though it would normally be wrapped over two lines.
            .
            B 00000,1
            N 00001
            . This comment
            . spans three
            . lines.
            N 00001
            . Another long comment that spans only one line but would normally be wrapped over two lines.
            ; Test a blank comment with a blank continuation line (should be ignored)
            N 00001
            .
            N 00001
            . Trailing blank line.
            .
            N 00001
            .
            . Leading blank line.
            N 00001
            . Paragraph 1.
            .
            . Paragraph 2.
            i 00002
        """
        exp_skool = """
            ; Data block at 0
            ;
            ; .
            ;
            ; .
            ;
            ; This comment
            ; spans two lines.
            ; .
            ; This comment spans only one line even though it would normally be wrapped over two lines.
            b00000 DEFB 0
            ; This comment
            ; spans three
            ; lines.
            ; .
            ; Another long comment that spans only one line but would normally be wrapped over two lines.
            ; .
            ; Trailing blank line.
            ; .
            ; Leading blank line.
            ; .
            ; Paragraph 1.
            ; .
            ; Paragraph 2.
             00001 DEFB 0
        """
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_newlines_in_block_end_comments(self):
        snapshot = [0]
        ctl = """
            b 00000
            B 00000,1
            E 00000 This comment
            . spans two lines.
            E 00000 This comment spans only one line even though it would normally be wrapped over two lines.
            .
            E 00000
            . This comment
            . spans three
            . lines.
            E 00000
            . Another long comment that spans only one line but would normally be wrapped over two lines.
            ; Test a blank comment with a blank continuation line (should be ignored)
            E 00000
            .
            E 00000
            . Trailing blank line.
            .
            E 00000
            .
            . Leading blank line.
            E 00000
            . Paragraph 1.
            .
            . Paragraph 2.
            i 00001
        """
        exp_skool = """
            ; Data block at 0
            b00000 DEFB 0
            ; This comment
            ; spans two lines.
            ; .
            ; This comment spans only one line even though it would normally be wrapped over two lines.
            ; .
            ; This comment
            ; spans three
            ; lines.
            ; .
            ; Another long comment that spans only one line but would normally be wrapped over two lines.
            ; .
            ; Trailing blank line.
            ; .
            ; Leading blank line.
            ; .
            ; Paragraph 1.
            ; .
            ; Paragraph 2.
        """
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_newlines_in_register_blocks(self):
        snapshot = [201] * 8
        ctl = """
            c 00000
            R 00000 BC This description
            . .     spans two lines
            c 00001
            R 00001 DE This description spans only one line even though it would normally be wrapped over two lines
            .
            c 00002
            R 00002
            . HL This description
            . .  spans three
            . .  lines
            c 00003
            R 00003
            . A Another long description that spans only one line but would normally be wrapped over two lines
            c 00004 Test a blank register description with a blank continuation line (should be ignored)
            R 00004
            .
            N 00004 Start comment.
            c 00005 Two 'R' directives
            R 00005
            . IX Trailing blank line
            .
            R 00005
            .
            . IY Leading blank line
            c 00006 One 'R' directive, two registers
            R 00006
            . BC Counts
            . .  the bytes
            . DE Destination
            c 00007 Registers with prefixes
            R 00007
            .   A First
            . .   input
            . B Input 2
            . O:C Output 1
            . O:D Second
            . .   output
            i 00008
        """
        exp_skool = """
            ; Routine at 0
            ;
            ; .
            ;
            ; BC This description
            ; .     spans two lines
            c00000 RET           ;

            ; Routine at 1
            ;
            ; .
            ;
            ; DE This description spans only one line even though it would normally be wrapped over two lines
            c00001 RET           ;

            ; Routine at 2
            ;
            ; .
            ;
            ; HL This description
            ; .  spans three
            ; .  lines
            c00002 RET           ;

            ; Routine at 3
            ;
            ; .
            ;
            ; A Another long description that spans only one line but would normally be wrapped over two lines
            c00003 RET           ;

            ; Test a blank register description with a blank continuation line (should be
            ; ignored)
            ;
            ; .
            ;
            ; .
            ;
            ; Start comment.
            c00004 RET           ;

            ; Two 'R' directives
            ;
            ; .
            ;
            ; IX Trailing blank line
            ; IY Leading blank line
            c00005 RET           ;

            ; One 'R' directive, two registers
            ;
            ; .
            ;
            ; BC Counts
            ; .  the bytes
            ; DE Destination
            c00006 RET           ;

            ; Registers with prefixes
            ;
            ; .
            ;
            ;   A First
            ; .   input
            ; B Input 2
            ; O:C Output 1
            ; O:D Second
            ; .   output
            c00007 RET           ;
        """
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_entire_entry_header_preserved_by_dot_directives(self):
        snapshot = [0]
        ctl = """
            b 00000
            . This is the title of the entry.
            .
            . This is the description.
            .
            .   A Input
            . O:B Output
            .
            . This is the start comment.
            i 00001
        """
        exp_skool = """
            ; This is the title of the entry.
            ;
            ; This is the description.
            ;
            ;   A Input
            ; O:B Output
            ;
            ; This is the start comment.
            b00000 DEFB 0
        """
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_colon_directive_with_instruction_comments(self):
        snapshot = [0] * 12
        ctl = """
            b 00000 Colon directive test
            B 00000,2,1
            . The first two comment lines
            : belong to the first DEFB.
            . And this comment line belongs to the second DEFB.
            C 00002,2
            : A colon directive on the first line
            : is equivalent to a dot directive.
            . Comment for the second NOP.
            S 00004,1
            . A colon directive works on a single
            : instruction too (but is not required).
            T 00005,1
            : A colon directive on the first line for a single
            . instruction is still equivalent to a dot directive.
            W 00006,4,2
            . The first two comment lines
            : belong to the first DEFW.
            . A colon directive on the last line
            : is not required but still works.
            B 00010,2,1
            . These two comment lines belong to the
            : first DEFB and the second DEFB has none.
            i 00012
        """
        exp_skool = """
            ; Colon directive test
            b00000 DEFB 0        ; {The first two comment lines
                                 ; belong to the first DEFB.
             00001 DEFB 0        ; And this comment line belongs to the second DEFB.}
             00002 NOP           ; {A colon directive on the first line
                                 ; is equivalent to a dot directive.
             00003 NOP           ; Comment for the second NOP.}
             00004 DEFS 1        ; A colon directive works on a single
                                 ; instruction too (but is not required).
             00005 DEFB 0        ; A colon directive on the first line for a single
                                 ; instruction is still equivalent to a dot directive.
             00006 DEFW 0        ; {The first two comment lines
                                 ; belong to the first DEFW.
             00008 DEFW 0        ; A colon directive on the last line
                                 ; is not required but still works.}
             00010 DEFB 0        ; {These two comment lines belong to the
                                 ; first DEFB and the second DEFB has none.
             00011 DEFB 0        ; }
        """
        self._test_write_skool(snapshot, ctl, exp_skool)

    def test_colon_directive_with_non_instruction_comments(self):
        snapshot = [175, 201]
        ctl = """
            c 00000
            . The first
            : routine
            D 00000
            : The description of
            . the first routine.
            R 00000
            . A The accumulator
            : B One half of the BC register pair
            N 00000
            . The start comment of
            : the first routine.
            C 00000,1
            N 00001
            : A mid-block
            : comment.
            C 00001,1
            E 00000
            . The end comment of
            : the first routine.
            i 00002
        """
        exp_skool = """
            ; The first
            ; routine
            ;
            ; The description of
            ; the first routine.
            ;
            ; A The accumulator
            ; B One half of the BC register pair
            ;
            ; The start comment of
            ; the first routine.
            c00000 XOR A         ;
            ; A mid-block
            ; comment.
             00001 RET           ;
            ; The end comment of
            ; the first routine.
        """
        self._test_write_skool(snapshot, ctl, exp_skool)
