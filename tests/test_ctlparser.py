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
  30200,10,1 Blank directive in a 'g' block
i 30300 Ignored block at 30300
t 30400 Message at 30400
  30450,7,4:B3 Complex DEFM with a blank directive
u 30500 Unused block at 30500
  30500,2 Blank directive in a 'u' block
B 30502,3
B 30510,12,3
B 30530-30549,2*7,1*3,3
B 30560,21,6,5,4,3,2,1
; This is yet another control file comment
w 30600 Words at 30600
S 30620,7
s 30700 Zeroes at 30700
B 30720,10,1,T3:2,1:T1*2
T 30730-30744,10:B5"""

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
            30700: 's'
        }
        self.assertEqual(exp_ctls, ctl_parser.ctls)

        exp_subctls = {
            30002: 't',
            30012: 'w',
            30020: 'c',
            30027: None,
            30050: 'b',
            30055: None,
            30100: None,
            30200: 'b',
            30210: None,
            30450: 't',
            30457: None,
            30500: 'b',
            30502: 'b',
            30505: None,
            30510: 'b',
            30522: None,
            30530: 'b',
            30550: None,
            30560: 'b',
            30581: None,
            30620: 's',
            30627: None,
            30720: 'b',
            30730: 't',
            30745: None
        }
        self.assertEqual(exp_subctls, ctl_parser.subctls)

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
        self.assertEqual(exp_titles, ctl_parser.titles)

        exp_instruction_comments = {
            30002: 'Message in the data block',
            30012: None,
            30020: None,
            30050: 'Complex DEFB with a blank directive',
            30200: "Blank directive in a 'g' block",
            30450: 'Complex DEFM with a blank directive',
            30500: "Blank directive in a 'u' block",
            30502: None,
            30510: None,
            30530: None,
            30560: None,
            30620: None,
            30720: None,
            30730: None
        }
        self.assertEqual(exp_instruction_comments, ctl_parser.instruction_comments)

        exp_comments = {
            30100: ['Description of routine at 30100']
        }
        self.assertEqual(exp_comments, ctl_parser.comments)

        exp_registers = {
            30100: [['A', 'Some value'], ['BC', 'Some other value']]
        }
        self.assertEqual(exp_registers, ctl_parser.registers)

        exp_end_comments = {
            30100: ['First paragraph of the end comment for the routine at 30100',
                    'Second paragraph of the end comment for the routine at 30100']
        }
        self.assertEqual(exp_end_comments, ctl_parser.end_comments)

        exp_lengths = {
            30050: [(5, [(3, None), (2, 'T')])],
            30200: [(1, None)],
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
        self.assertEqual(exp_lengths, ctl_parser.lengths)

        exp_multiline_comments = {
            30012: (30026, 'This comment covers the following two sub-blocks')
        }
        self.assertEqual(exp_multiline_comments, ctl_parser.multiline_comments)

        exp_entry_asm_directives = {
            30000: [('start', None)]
        }
        self.assertEqual(exp_entry_asm_directives, ctl_parser.entry_asm_directives)

        exp_instruction_asm_directives = {
            30101: [('label', 'LOOP')]
        }
        self.assertEqual(exp_instruction_asm_directives, ctl_parser.instruction_asm_directives)

    def test_invalid_lines(self):
        ctl_specs = [
            ('  30000,1',        'blank directive with no containing block'),
            ('B 30745,15,5:X10', 'invalid integer'),
            ('T 30760,5,2:Y3',   'invalid integer'),
            ('W 30765,5,1:B4',   'invalid integer'),
            ('S 30770,10,T8:2',  'invalid integer'),
            ('C 40000,Q',        'invalid integer'),
            ('; @label:EDCBA=Z', 'invalid ASM directive address'),
            ('; @label=Z',       'invalid ASM directive declaration'),
            ('b 50000,20',       'extra parameters after address'),
            ('d 50020',          'invalid directive'),
            ('! 50030',          'invalid directive')
        ]
        ctls = [spec[0] for spec in ctl_specs]
        ctl_parser = CtlParser()
        ctlfile = self.write_text_file('\n'.join(ctls))
        ctl_parser.parse_ctl(ctlfile)
        exp_warnings = []
        for line_no, (ctl, error_msg) in enumerate(ctl_specs, 1):
            if error_msg:
                exp_warnings.append('WARNING: Ignoring line {} in {} ({}):'.format(line_no, ctlfile, error_msg))
        warnings = self.err.getvalue().split('\n')[:-1]
        self.assertEqual(exp_warnings, warnings[0::2])
        invalid_ctls = [spec[0] for spec in ctl_specs if spec[1]]
        self.assertEqual(invalid_ctls, warnings[1::2])

    def test_comments(self):
        ctl = '\n'.join((
            '# This is a comment',
            'b 32768',
            '% This is also a comment',
            'w 32769',
            '; This is a comment too'
        ))
        ctl_parser = CtlParser()
        ctlfile = self.write_text_file(ctl)
        ctl_parser.parse_ctl(ctlfile)

        self.assertEqual(self.err.getvalue(), '')
        self.assertEqual({32768: 'b', 32769: 'w'}, ctl_parser.ctls)

    def test_byte_formats(self):
        ctl = '\n'.join((
            'b 40000 Test byte formats',
            '  40000,b10 10 bytes in binary format',
            'B 40010,b10,5,d3,h2 5 binary, 3 decimal, 2 hex',
            'B 40020,b10,2:d3:h5 2 binary, 3 decimal, 5 hex, one line',
            '  40030,10,b6,3,h1 6 binary, 3 default, 1 hex',
            '  40040,10,b5:2:h3 5 binary, 2 default, 3 hex, one line',
            '  40050,10,1,T9 1 default, 9 text',
            '  40060,10,h4:T6 4 hex, 6 text, one line',
            'T 40070,10,3,b7 3 text, 7 binary',
            'T 40080,10,2:h8 2 text, 8 hex, one line',
            'T 40090,10,5,B5 5 text, 5 default'
        ))
        ctl_parser = CtlParser()
        ctlfile = self.write_text_file(ctl)
        ctl_parser.parse_ctl(ctlfile)

        exp_lengths = {
            40000: [(None, [(None, 'b')])],
            40010: [
                (5, [(5, 'b')]),
                (3, [(3, 'd')]),
                (2, [(2, 'h')])
            ],
            40020: [(10, [(2, 'b'), (3, 'd'), (5, 'h')])],
            40030: [
                (6, [(6, 'b')]),
                (3, None),
                (1, [(1, 'h')])
            ],
            40040: [(10, [(5, 'b'), (2, None), (3, 'h')])],
            40050: [
                (1, None),
                (9, [(9, 'T')])
            ],
            40060: [(10, [(4, 'h'), (6, 'T')])],
            40070: [
                (3, None),
                (7, [(7, 'b')])
            ],
            40080: [(10, [(2, None), (8, 'h')])],
            40090: [
                (5, None),
                (5, [(5, 'B')])
            ],
        }
        self.assertEqual(exp_lengths, ctl_parser.lengths)

    def test_word_formats(self):
        ctl = '\n'.join((
            'w 40000 Test word formats',
            '  40000,10 5 default',
            '  40010,b10 5 words in binary format',
            'W 40020,b10,6,d2,h2 3 binary, 1 decimal, 1 hex',
            'W 40030,b10,4:d4:h2 2 binary, 2 decimal, 1 hex, one line',
            '  40040,10,b2,4,h4 1 binary, 2 default, 2 hex',
            '  40050,10,b2:6:h2 1 binary, 3 default, 1 hex, one line',
        ))
        ctl_parser = CtlParser()
        ctlfile = self.write_text_file(ctl)
        ctl_parser.parse_ctl(ctlfile)

        exp_lengths = {
            40010: [(None, [(None, 'b')])],
            40020: [
                (6, [(6, 'b')]),
                (2, [(2, 'd')]),
                (2, [(2, 'h')])
            ],
            40030: [(10, [(4, 'b'), (4, 'd'), (2, 'h')])],
            40040: [
                (2, [(2, 'b')]),
                (4, None),
                (4, [(4, 'h')])
            ],
            40050: [(10, [(2, 'b'), (6, None), (2, 'h')])]
        }
        self.assertEqual(exp_lengths, ctl_parser.lengths)

    def test_s_directives(self):
        ctl = '\n'.join((
            's 50000 Test s/S directives',
            '  50000,10',
            '  50010,b10',
            '  50020,d10',
            '  50030,h10',
            'S 50040,b20,5,d5,h5',
            'S 50060,d20,b5,5,h5',
            'S 50080,h20,b5,d5,5',
            '  50100,20,b5,d5,5',
            '  50120,20,d20:b%10001000',
            '  50140,20,20:h$44',
            '  50160,12,10:h10,h2:2'
        ))
        ctl_parser = CtlParser()
        ctlfile = self.write_text_file(ctl)
        ctl_parser.parse_ctl(ctlfile)

        exp_lengths = {
            50010: [(None, [(None, 'b')])],
            50020: [(None, [(None, 'd')])],
            50030: [(None, [(None, 'h')])],
            50040: [
                (5, [(5, 'b')]),
                (5, [(5, 'd')]),
                (5, [(5, 'h')])
            ],
            50060: [
                (5, [(5, 'b')]),
                (5, [(5, 'd')]),
                (5, [(5, 'h')])
            ],
            50080: [
                (5, [(5, 'b')]),
                (5, [(5, 'd')]),
                (5, [(5, 'h')])
            ],
            50100: [
                (5, [(5, 'b')]),
                (5, [(5, 'd')]),
                (5, None)
            ],
            50120: [(20, [(20, 'd'), (136, 'b')])],
            50140: [(20, [(20, None), (68, 'h')])],
            50160: [
                (10, [(10, None), (10, 'h')]),
                (2, [(2, 'h'), (2, None)]),
            ]
        }
        self.assertEqual(exp_lengths, ctl_parser.lengths)

if __name__ == '__main__':
    unittest.main()
