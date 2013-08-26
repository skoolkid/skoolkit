# -*- coding: utf-8 -*-
import unittest

from skoolkittest import SkoolKitTestCase
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
z 32799
Z 32799,10,5
; Entry #13
z 32809 Block of zeroes
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

SKOOL = """; @start
; @writer=skoolkit.game.GameAsmWriter
; @set-tab=1
; @org=32768
; Routine at 32768
;
; Routine description paragraph 1.
; .
; Routine description paragraph 2.
;
; A Some value
; B Some other value
; @label=START
c32768 XOR A         ; {This is an instruction-level comment that spans two
 32769 RET           ; instructions and is too long to fit on two lines, so
                     ; extends to three}
; Routine end comment.
; @end

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
        self.assertEqual(block.header, None)
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

class SkoolWriterTest(SkoolKitTestCase):
    def _get_writer(self, snapshot, ctl, defb_size=8, defb_mod=1, zfill=False, defm_width=66, asm_hex=False, asm_lower=False):
        ctl_parser = CtlParser()
        ctl_parser.parse_ctl(self.write_text_file(ctl))
        return SkoolWriter(snapshot, ctl_parser, defb_size, defb_mod, zfill, defm_width, asm_hex, asm_lower)

    def _test_write_refs(self, snapshot, ctl, write_refs, exp_skool):
        writer = self._get_writer(snapshot, ctl)
        writer.write_skool(write_refs, False)
        skool = self.out.getvalue().split('\n')
        self.assertEqual(skool[:len(exp_skool)], exp_skool)

    def test_write_skool(self):
        writer = self._get_writer(WRITER_SNAPSHOT, WRITER_CTL)
        writer.write_skool(0, False)
        skool = self.out.getvalue().split('\n')[:-1]
        self.assertEqual(skool, SKOOL)

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
            '; @start',
            '; @org=30000',
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
            '; @start',
            '; @org=40000',
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
            '; @start',
            '; @org=50000',
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

if __name__ == '__main__':
    unittest.main()
