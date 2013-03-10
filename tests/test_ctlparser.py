# -*- coding: utf-8 -*-
import unittest

from skoolkittest import SkoolKitTestCase
from skoolkit.ctlparser import CtlParser

CTL = """; Test control file for parse_ctl

; @start:30000
b $7530 Data at 30000
T 30002,10 Message in the data block
M 30012,15 This comment covers the following two sub-blocks
W 30012-30019
C 30020,7
  30050,5,3:T2 Complex DEFB with a blank directive
# This is a control file comment
c 30100 Routine at 30100
D 30100 Description of routine at 30100
R 30100 A Some value
R 30100 BC Some other value
; @label:$7595=LOOP
E 30100 First paragraph of the end comment for the routine at 30100
E 30100 Second paragraph of the end comment for the routine at 30100
% This is another control file comment
g 30200 Game status buffer entry at 30200
i 30300 Ignored block at 30300
t 30400 Message at 30400
  30450,7,4:B3 Complex DEFM with a blank directive
u 30500 Unused block at 30500
B 30502,3
B 30510,12,3
B 30530-30549,2*7,1*3,3
B 30560,21,6,5,4,3,2,1
! This is yet another control file comment
w 30600 Words at 30600
Z 30620,7
z 30700 Zeroes at 30700
B 30720,10,1,T3:2,1:T1*2
T 30730-30744,10:B5
B 30745,15,5:X10
T 30760,5,2:Y3
W 30765,5,1:B4
Z 30770,10,T8:2
c ABCDE Invalid
C 40000,Q Invalid
; @label:EDCBA=INVALID"""

class CtlParserTest(SkoolKitTestCase):
    def test_parse_ctl(self):
        ctl_parser = CtlParser()
        ctlfile = self.write_text_file(CTL)
        ctl_parser.parse_ctl(ctlfile)

        exp_ctls = {
            30000: 'b',
            30100: 'c',
            30200: 'g',
            30300: 'i',
            30400: 't',
            30500: 'u',
            30600: 'w',
            30700: 'z'
        }
        self.assertEqual(ctl_parser.ctls, exp_ctls)

        exp_subctls = {
            30002: 't',
            30012: 'w',
            30020: 'c',
            30027: None,
            30050: '',
            30055: None,
            30100: None,
            30450: '',
            30457: None,
            30502: 'b',
            30505: None,
            30510: 'b',
            30522: None,
            30530: 'b',
            30550: None,
            30560: 'b',
            30581: None,
            30620: 'z',
            30627: None,
            30720: 'b',
            30730: 't',
            30745: None
        }
        self.assertEqual(ctl_parser.subctls, exp_subctls)

        exp_titles = {
            30000: 'Data at 30000',
            30100: 'Routine at 30100',
            30200: 'Game status buffer entry at 30200',
            30300: 'Ignored block at 30300',
            30400: 'Message at 30400',
            30500: 'Unused block at 30500',
            30600: 'Words at 30600',
            30700: 'Zeroes at 30700'
        }
        self.assertEqual(ctl_parser.titles, exp_titles)

        exp_instruction_comments = {
            30002: 'Message in the data block',
            30012: None,
            30020: None,
            30050: 'Complex DEFB with a blank directive',
            30450: 'Complex DEFM with a blank directive',
            30502: None,
            30510: None,
            30530: None,
            30560: None,
            30620: None,
            30720: None,
            30730: None
        }
        self.assertEqual(ctl_parser.instruction_comments, exp_instruction_comments)

        exp_comments = {
            30100: ['Description of routine at 30100']
        }
        self.assertEqual(ctl_parser.comments, exp_comments)

        exp_registers = {
            30100: [['A', 'Some value'], ['BC', 'Some other value']]
        }
        self.assertEqual(ctl_parser.registers, exp_registers)

        exp_end_comments = {
            30100: ['First paragraph of the end comment for the routine at 30100',
                    'Second paragraph of the end comment for the routine at 30100']
        }
        self.assertEqual(ctl_parser.end_comments, exp_end_comments)

        exp_lengths = {
            30050: [(5, [(3, None), (2, 'T')])],
            30450: [(7, [(4, None), (3, 'B')])],
            30510: [(3, None)],
            30530: list(zip([2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 3], [None] * 11)),
            30560: list(zip([6, 5, 4, 3, 2, 1], [None] * 6)),
            30720: [
                (1, None),
                (5, [(3, 'T'), (2, None)]),
                (2, [(1, None), (1, 'T')]),
                (2, [(1, None), (1, 'T')])
            ],
            30730: [(15, [(10, None), (5, 'B')])]
        }
        self.assertEqual(ctl_parser.lengths, exp_lengths)

        exp_multiline_comments = {
            30012: (30026, 'This comment covers the following two sub-blocks')
        }
        self.assertEqual(ctl_parser.multiline_comments, exp_multiline_comments)

        exp_entry_asm_directives = {
            30000: [('start', None)]
        }
        self.assertEqual(ctl_parser.entry_asm_directives, exp_entry_asm_directives)

        exp_instruction_asm_directives = {
            30101: [('label', 'LOOP')]
        }
        self.assertEqual(ctl_parser.instruction_asm_directives, exp_instruction_asm_directives)

        text = 'WARNING: Ignoring invalid control directive in {0}:'.format(ctlfile)
        invalid_lines = [
            'B 30745,15,5:X10',
            'T 30760,5,2:Y3',
            'W 30765,5,1:B4',
            'Z 30770,10,T8:2',
            'c ABCDE Invalid',
            'C 40000,Q Invalid',
            '; @label:EDCBA=INVALID'
        ]
        exp_warnings = len(invalid_lines)
        warnings = self.err.getvalue().split('\n')[:-1]
        self.assertEqual(len(warnings), exp_warnings * 2)
        self.assertEqual(warnings[0::2], [text] * exp_warnings)
        self.assertEqual(warnings[1::2], invalid_lines)

if __name__ == '__main__':
    unittest.main()
