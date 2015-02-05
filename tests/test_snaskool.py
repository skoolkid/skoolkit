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
DISASSEMBLY_SNAPSHOT[32814:32817] = [
    195, 0, 128 # 32814 JP 32768
]

DISASSEMBLY_SNAPSHOT[32817:32827] = [
    72, 105, 1, 2, 3, # 32817 DEFM "Hi",1,2,3
    4, 5, 76, 111, 6, # 32822 DEFB 4,5,"Lo",6
    97, 98, 1,        # 32827 DEFM "ab',1
    99, 100, 2,       # 32830 DEFM "cd",2
    101, 3,           # 32832 DEFM "e",3
    102, 4            # 32834 DEFM "f",4
]

DISASSEMBLY_CTL = """; @start:32768
; @writer:32768=skoolkit.game.GameAsmWriter
; @org:32768=32768
; @label:32768=START
; Entry #1
c 32768
D 32768 Routine description paragraph 1.
D 32768 Routine description paragraph 2.
R 32768 A Some value
R 32768 B Some other value
  32768,2 This is an instruction-level comment that spans two instructions
E 32768 Routine end comment.
; @end:32768
; Entry #2
t 32770
T 32770,4,2
; Entry #3
t 32774 Yo
; Entry #4
b 32776
B 32776,12,3*4
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
M 32809,5 A DEFS followed by two NOPs
C 32812,2
; Entry #14
c 32814 Refers to the routine at 32768
; Entry #15
b 32817
T 32817,5,2:B3
B 32822,5,2:T2:1
T 32827,10,2:B1*2,1:B1
; Entry 16
i 32837
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

WRITER_CTL = """; @start:32768
; @writer:32768=skoolkit.game.GameAsmWriter
; @set-tab:32768=1
; @org:32768=32768
; @label:32768=START
c 32768
D 32768 Routine description paragraph 1.
D 32768 Routine description paragraph 2.
R 32768 A Some value
R 32768 B Some other value
  32768,2 This is an instruction-level comment that spans two instructions and is too long to fit on two lines, so extends to three
E 32768 Routine end comment.
; @end:32768
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
    def test_disassembly(self):
        ctl_parser = CtlParser()
        ctl_parser.parse_ctl(self.write_text_file(DISASSEMBLY_CTL))
        disassembly = Disassembly(DISASSEMBLY_SNAPSHOT, ctl_parser, True)

        entries = disassembly.entries
        self.assertEqual(len(entries), 16)

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
        self.assertEqual(len(instructions), 4)
        self.assertEqual(instructions[0].operation, 'DEFB 0,0,0')
        self.assertEqual(instructions[3].operation, 'DEFB 0,0,0')

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
        self.assertEqual(len(blocks), 1)
        block = blocks[0]
        self.assertEqual(block.comment, 'A DEFS followed by two NOPs')

        # Entry #14 (32814)
        entry = entries[13]
        self.assertEqual(entry.address, 32814)
        self.assertEqual(entry.title, 'Refers to the routine at 32768')

        # Entry #15 (32817)
        entry = entries[14]
        self.assertEqual(entry.address, 32817)
        instructions = entry.instructions
        self.assertEqual(len(instructions), 6)
        self.assertEqual(instructions[0].operation, 'DEFM "Hi",1,2,3')
        self.assertEqual(instructions[1].operation, 'DEFB 4,5,"Lo",6')
        self.assertEqual(instructions[2].operation, 'DEFM "ab",1')
        self.assertEqual(instructions[3].operation, 'DEFM "cd",2')
        self.assertEqual(instructions[4].operation, 'DEFM "e",3')
        self.assertEqual(instructions[5].operation, 'DEFM "f",4')

        # Entry #16 (32837)
        entry = entries[15]
        self.assertEqual(entry.address, 32837)

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
        ctl_parser = CtlParser()
        ctl_parser.parse_ctl(self.write_text_file(ctl))
        disassembly = Disassembly(snapshot, ctl_parser, True)

        entries = disassembly.entries
        self.assertEqual(len(entries), 2)

        entry = entries[0]
        self.assertEqual(entry.address, 0)
        instructions = entry.instructions
        actual_instructions = [(i.address, i.operation) for i in instructions]
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
        self.assertEqual(actual_instructions, exp_instructions)

    def test_byte_formats_hex(self):
        snapshot = [85] * 4
        ctl = '\n'.join((
            'b 00000',
            '  00000,4,b1:d1:h1:1',
            'i 00004'
        ))
        ctl_parser = CtlParser()
        ctl_parser.parse_ctl(self.write_text_file(ctl))
        disassembly = Disassembly(snapshot, ctl_parser, True, asm_hex=True)

        entries = disassembly.entries
        self.assertEqual(len(entries), 2)

        entry = entries[0]
        self.assertEqual(entry.address, 0)
        instructions = entry.instructions
        self.assertEqual(len(instructions), 1)
        defb = instructions[0]
        self.assertEqual(defb.operation, 'DEFB %01010101,85,$55,$55')

    def test_word_formats(self):
        snapshot = [170, 53] * 32
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
            'i 00064'
        ))
        ctl_parser = CtlParser()
        ctl_parser.parse_ctl(self.write_text_file(ctl))
        disassembly = Disassembly(snapshot, ctl_parser, True)

        entries = disassembly.entries
        self.assertEqual(len(entries), 2)

        entry = entries[0]
        self.assertEqual(entry.address, 0)
        instructions = entry.instructions
        actual_instructions = [(i.address, i.operation) for i in instructions]
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
            (60, 'DEFW 13738,13738')
        ]
        self.assertEqual(actual_instructions, exp_instructions)

    def test_word_formats_hex(self):
        snapshot = [240] * 8
        ctl = '\n'.join((
            'w 00000',
            '  00000,8,b2,d2,h2,2',
            'i 00008'
        ))
        ctl_parser = CtlParser()
        ctl_parser.parse_ctl(self.write_text_file(ctl))
        disassembly = Disassembly(snapshot, ctl_parser, True, asm_hex=True)

        entries = disassembly.entries
        self.assertEqual(len(entries), 2)

        entry = entries[0]
        self.assertEqual(entry.address, 0)
        instructions = entry.instructions
        actual_instructions = [(i.address, i.operation) for i in instructions]
        exp_instructions = [
            (0, 'DEFW %1111000011110000'),
            (2, 'DEFW 61680'),
            (4, 'DEFW $F0F0'),
            (6, 'DEFW $F0F0')
        ]
        self.assertEqual(exp_instructions, actual_instructions)

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
            'i 01024'
        ))
        ctl_parser = CtlParser()
        ctl_parser.parse_ctl(self.write_text_file(ctl))
        disassembly = Disassembly(snapshot, ctl_parser, True)

        entries = disassembly.entries
        self.assertEqual(len(entries), 2)

        entry = entries[0]
        self.assertEqual(entry.address, 0)
        instructions = entry.instructions
        actual_instructions = [(i.address, i.operation) for i in instructions]
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
            (984, 'DEFS 40,$11')
        ]
        self.assertEqual(exp_instructions, actual_instructions)

    def test_s_directives_hex(self):
        snapshot = []
        ctl = '\n'.join((
            's 00000',
            '  00000,14,d2:b1,h2:128,h10:2',
            'i 00014'
        ))
        ctl_parser = CtlParser()
        ctl_parser.parse_ctl(self.write_text_file(ctl))
        disassembly = Disassembly(snapshot, ctl_parser, True, asm_hex=True)

        entries = disassembly.entries
        self.assertEqual(len(entries), 2)

        entry = entries[0]
        self.assertEqual(entry.address, 0)
        instructions = entry.instructions
        actual_instructions = [(i.address, i.operation) for i in instructions]
        exp_instructions = [
            (0, 'DEFS 2,%00000001'),
            (2, 'DEFS 2,$80'),
            (4, 'DEFS $0A,2')
        ]
        self.assertEqual(exp_instructions, actual_instructions)

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

    def _test_write_refs(self, snapshot, ctl, write_refs, exp_skool):
        writer = self._get_writer(snapshot, ctl)
        writer.write_skool(write_refs, False)
        skool = self.out.getvalue().split('\n')
        self.assertEqual(exp_skool, skool[:len(exp_skool)])

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
        writer = self._get_writer(snapshot, ctl, line_width=64)
        writer.write_skool(0, False)
        skool = self.out.getvalue().split('\n')
        self.assertEqual(exp_skool, skool[:len(exp_skool)])

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
        writer = self._get_writer(snapshot, ctl, line_width=94)
        writer.write_skool(0, False)
        skool = self.out.getvalue().split('\n')
        self.assertEqual(exp_skool, skool[:len(exp_skool)])

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
        self._test_write_refs(snapshot, ctl, -1, exp_skool)

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
            'D 40001 Mid-routine comment.',
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
            '*40003 RET           ;'
        ]
        self._test_write_refs(snapshot, ctl, 0, exp_skool)

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
            'D 50001 Mid-routine comment.',
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
            '*50003 RET           ;'
        ]
        self._test_write_refs(snapshot, ctl, 1, exp_skool)

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
            '; @ignoreua:10000:t',
            'c 10000 Routine at 10000',
            '; @ignoreua:10000:d',
            'D 10000 Description of the routine at 10000.',
            '; @ignoreua:10000:r',
            'R 10000 HL 10000',
            '; @ignoreua:10000:m',
            'N 10000 Start comment.',
            '; @ignoreua:10000',
            '  10000 Instruction-level comment at 10000',
            '; @ignoreua:10001:m',
            'D 10001 Mid-block comment above 10001.',
            '; @ignoreua:10001:i',
            '  10001 Instruction-level comment at 10001',
            '; @ignoreua:10000:e',
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
        writer = self._get_writer(snapshot, ctl)
        writer.write_skool(0, False)
        skool = self.out.getvalue().split('\n')[:-2]
        self.assertEqual(exp_skool, skool)

    def test_ignoreua_directives_write_refs(self):
        ctl = '\n'.join((
            'c 10000 Routine at 10000',
            '; @ignoreua:10000:d',
            'D 10000 Description of the routine at 10000.',
            'c 10002 Routine at 10002',
            '; @ignoreua:10003:m',
            'D 10003 Mid-block comment above 10003.',
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
        self._test_write_refs(snapshot, ctl, 1, exp_skool)

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
            '; BC This register description is long enough that it needs to be split over',
            '; .  two lines',
            '; DE Short register description',
            '; HL Another register description that is long enough to need splitting over',
            '; .  two lines',
            '; IX',
            'c00000 NOP           ;'
        ]
        writer = self._get_writer([0], ctl)
        writer.write_skool(0, False)
        skool = self.out.getvalue().split('\n')[:-2]
        self.assertEqual(exp_skool, skool[6:])

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
            ';  Input:A An important parameter with a long description that will be split',
            '; .        over two lines',
            ';        B Another important parameter',
            '; Output:DE The result',
            ';        HL',
            'c00000 NOP           ;'
        ]
        writer = self._get_writer([0], ctl)
        writer.write_skool(0, False)
        skool = self.out.getvalue().split('\n')
        self.assertEqual(exp_skool, skool[6:6 + len(exp_skool)])

    def test_start_comment(self):
        ctl = '\n'.join((
            'c 00000',
            'N 00000 Start comment.',
            'i 00001'
        ))
        exp_skool = [
            '; Routine at 0',
            ';',
            '; .',
            ';',
            '; .',
            ';',
            '; Start comment.',
            'c00000 NOP           ;'
        ]
        writer = self._get_writer([0], ctl)
        writer.write_skool(0, False)
        skool = self.out.getvalue().split('\n')[:-2]
        self.assertEqual(exp_skool, skool[2:])

    def test_multi_paragraph_start_comment(self):
        ctl = '\n'.join((
            'c 00000 Routine',
            'D 00000 Description.',
            'N 00000 Start comment paragraph 1.',
            'N 00000 Paragraph 2.',
            'i 00001'
        ))
        exp_skool = [
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
        writer = self._get_writer([0], ctl)
        writer.write_skool(0, False)
        skool = self.out.getvalue().split('\n')[:-2]
        self.assertEqual(exp_skool, skool[2:])

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
        write_ctl(ctlfile, ctls, False)
        with open(ctlfile, 'r') as f:
            lines = [line.rstrip() for line in f]
        self.assertEqual(lines, exp_ctl)

if __name__ == '__main__':
    unittest.main()
