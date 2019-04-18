import textwrap

from skoolkittest import SkoolKitTestCase
from skoolkit.ctlparser import CtlParser

CTL = """; Test control file for parse_ctl

@ 30000 start
b $7530 Data at 30000
N 30000 Block start comment
T 30002,10 Message in the data block
N 30012 Mid-block comment
M 30012,15 This comment covers the following two sub-blocks
W 30012,8
C 30020,7
  30050,5,3:T2 Complex DEFB with a blank directive
# This is a control file comment
c 30100 Routine at 30100
D 30100 Description of routine at 30100
R 30100 A Some value
R 30100 BC Some other value
@ $7595 label=LOOP
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
B 30530,20,2*7,1*3,3
B 30560,21,6,5,4,3,2,1
; This is yet another control file comment
w 30600 Words at 30600
S 30620,7
s 30700 Zeroes at 30700
B 30720,10,1,T3:2,1:T1*2
N 30730 Another mid-block comment
T 30730,15,10:B5"""

class CtlParserTest(SkoolKitTestCase):
    def _get_ctl_parser(self, ctl, min_address=0, max_address=65536):
        ctl_parser = CtlParser()
        ctls = [ctl] if isinstance(ctl, str) else ctl
        ctlfiles = [self.write_text_file(textwrap.dedent(s).strip()) for s in ctls]
        ctl_parser.parse_ctls(ctlfiles, min_address, max_address)
        return ctl_parser

    def _check_blocks(self, blocks):
        addresses = [b.start for b in blocks]
        self.assertEqual(sorted(addresses), addresses)

    def _check_ctls(self, exp_ctls, blocks):
        ctls = {b.start: b.ctl for b in blocks}
        self.assertEqual(exp_ctls, ctls)

    def _check_headers(self, exp_headers, blocks):
        headers = {b.start: b.header for b in blocks}
        self.assertEqual(exp_headers, headers)

    def _check_footers(self, exp_footers, blocks):
        footers = {b.start: b.footer for b in blocks}
        self.assertEqual(exp_footers, footers)

    def _check_entry_asm_directives(self, exp_entry_asm_directives, blocks):
        entry_asm_directives = {b.start: b.asm_directives for b in blocks}
        self.assertEqual(exp_entry_asm_directives, entry_asm_directives)

    def _check_titles(self, exp_titles, blocks):
        titles = {b.start: b.title for b in blocks}
        self.assertEqual(exp_titles, titles)

    def _check_descriptions(self, exp_descriptions, blocks):
        descriptions = {b.start: b.description for b in blocks}
        self.assertEqual(exp_descriptions, descriptions)

    def _check_registers(self, exp_registers, blocks):
        registers = {b.start: b.registers for b in blocks}
        self.assertEqual(exp_registers, registers)

    def _check_end_comments(self, exp_end_comments, blocks):
        end_comments = {b.start: b.end_comment for b in blocks}
        self.assertEqual(exp_end_comments, end_comments)

    def _check_subctls(self, exp_subctls, blocks):
        subctls = {s.start: s.ctl for b in blocks for s in b.blocks}
        self.assertEqual(exp_subctls, subctls)

    def _check_mid_block_comments(self, exp_mid_block_comments, blocks):
        mid_block_comments = {s.start: s.header for b in blocks for s in b.blocks}
        self.assertEqual(exp_mid_block_comments, mid_block_comments)

    def _check_instruction_comments(self, exp_instruction_comments, blocks):
        instruction_comments = {s.start: s.comment for b in blocks for s in b.blocks}
        self.assertEqual(exp_instruction_comments, instruction_comments)

    def _check_sublengths(self, exp_sublengths, blocks):
        sublengths = {s.start: s.sublengths for b in blocks for s in b.blocks}
        self.assertEqual(exp_sublengths, sublengths)

    def _check_multiline_comments(self, exp_multiline_comments, blocks):
        multiline_comments = {s.start: s.multiline_comment for b in blocks for s in b.blocks}
        self.assertEqual(exp_multiline_comments, multiline_comments)

    def _check_instruction_asm_directives(self, exp_directives, blocks):
        directives = {}
        for b in blocks:
            for s in b.blocks:
                directives.update(s.asm_directives)
        self.assertEqual(exp_directives, directives)

    def _check_ignoreua_directives(self, exp_entry_directives, exp_other_directives, blocks):
        entry_directives = {}
        other_directives = {}
        for b in blocks:
            entry_directives[b.start] = sorted(b.ignoreua_directives)
            for s in b.blocks:
                for address, dirs in s.ignoreua_directives.items():
                    other_directives[address] = sorted(dirs)
        self.assertEqual(exp_entry_directives, entry_directives)
        self.assertEqual(exp_other_directives, other_directives)

    def _test_asm_directives(self, ctl, exp_entry_directives, exp_instruction_directives):
        blocks = self._get_ctl_parser(ctl).get_blocks()
        self._check_entry_asm_directives(exp_entry_directives, blocks)
        self._check_instruction_asm_directives(exp_instruction_directives, blocks)

    def test_predefined_ctls_acquire_start_and_org_directives(self):
        ctl_parser = CtlParser({16384: 'c', 32768: 'i'})
        exp_entry_asm_directives = {16384: ['start', 'org']}
        self._check_entry_asm_directives(exp_entry_asm_directives, ctl_parser.get_blocks())

    def test_parse_ctl(self):
        ctl_parser = self._get_ctl_parser(CTL)
        blocks = ctl_parser.get_blocks()
        self._check_blocks(blocks)

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
        self._check_ctls(exp_ctls, blocks)

        exp_subctls = {
            30000: 'b',
            30002: 't',
            30012: 'w',
            30020: 'c',
            30027: 'b',
            30050: 'b',
            30055: 'b',
            30100: 'c',
            30200: 'b',
            30210: 'g',
            30300: 'i',
            30400: 't',
            30450: 't',
            30457: 't',
            30500: 'b',
            30502: 'b',
            30505: 'u',
            30510: 'b',
            30522: 'u',
            30530: 'b',
            30532: 'b',
            30534: 'b',
            30536: 'b',
            30538: 'b',
            30540: 'b',
            30542: 'b',
            30544: 'b',
            30545: 'b',
            30546: 'b',
            30547: 'b',
            30550: 'u',
            30560: 'b',
            30566: 'b',
            30571: 'b',
            30575: 'b',
            30578: 'b',
            30580: 'b',
            30581: 'u',
            30600: 'w',
            30620: 's',
            30627: 'w',
            30700: 's',
            30720: 'b',
            30721: 'b',
            30726: 'b',
            30728: 'b',
            30730: 't',
            30745: 's'
        }
        self._check_subctls(exp_subctls, blocks)

        exp_mid_block_comments = {
            30000: [['Block start comment']],
            30002: (),
            30012: [['Mid-block comment']],
            30020: (),
            30027: (),
            30050: (),
            30055: (),
            30100: (),
            30200: (),
            30210: (),
            30300: (),
            30400: (),
            30450: (),
            30457: (),
            30500: (),
            30502: (),
            30505: (),
            30510: (),
            30522: (),
            30530: (),
            30532: (),
            30534: (),
            30536: (),
            30538: (),
            30540: (),
            30542: (),
            30544: (),
            30545: (),
            30546: (),
            30547: (),
            30550: (),
            30560: (),
            30566: (),
            30571: (),
            30575: (),
            30578: (),
            30580: (),
            30581: (),
            30600: (),
            30620: (),
            30627: (),
            30700: (),
            30720: (),
            30721: (),
            30726: (),
            30728: (),
            30730: [['Another mid-block comment']],
            30745: ()
        }
        self._check_mid_block_comments(exp_mid_block_comments, blocks)

        exp_titles = {
            30000: ['Data at 30000'],
            30100: ['Routine at 30100'],
            30200: ['Game status buffer entry at 30200'],
            30300: ['Ignored block at 30300'],
            30400: ['Message at 30400'],
            30500: ['Unused block at 30500'],
            30600: ['Words at 30600'],
            30700: ['Zeroes at 30700']
        }
        self._check_titles(exp_titles, blocks)

        exp_instruction_comments = {
            30000: (),
            30002: [(0, 'Message in the data block')],
            30012: [(0, '')],
            30020: [(0, '')],
            30027: (),
            30050: [(0, 'Complex DEFB with a blank directive')],
            30055: (),
            30100: (),
            30200: [(0, "Blank directive in a 'g' block")],
            30210: (),
            30300: (),
            30400: (),
            30450: [(0, 'Complex DEFM with a blank directive')],
            30457: (),
            30500: [(0, "Blank directive in a 'u' block")],
            30502: [(0, '')],
            30505: (),
            30510: [(0, '')],
            30522: (),
            30530: [(0, '')],
            30532: (),
            30534: (),
            30536: (),
            30538: (),
            30540: (),
            30542: (),
            30544: (),
            30545: (),
            30546: (),
            30547: (),
            30550: (),
            30560: [(0, '')],
            30566: (),
            30571: (),
            30575: (),
            30578: (),
            30580: (),
            30581: (),
            30600: (),
            30620: [(0, '')],
            30627: (),
            30700: (),
            30720: [(0, '')],
            30721: (),
            30726: (),
            30728: (),
            30730: [(0, '')],
            30745: ()
        }
        self._check_instruction_comments(exp_instruction_comments, blocks)

        exp_descriptions = {
            30000: (),
            30100: [['Description of routine at 30100']],
            30200: (),
            30300: (),
            30400: (),
            30500: (),
            30600: (),
            30700: ()
        }
        self._check_descriptions(exp_descriptions, blocks)

        exp_registers = {
            30000: (),
            30100: [['A Some value'], ['BC Some other value']],
            30200: (),
            30300: (),
            30400: (),
            30500: (),
            30600: (),
            30700: ()
        }
        self._check_registers(exp_registers, blocks)

        exp_end_comments = {
            30000: (),
            30100: [
                ['First paragraph of the end comment for the routine at 30100'],
                ['Second paragraph of the end comment for the routine at 30100']
            ],
            30200: (),
            30300: (),
            30400: (),
            30500: (),
            30600: (),
            30700: ()
        }
        self._check_end_comments(exp_end_comments, blocks)

        exp_sublengths = {
            30000: ((None, None),),
            30002: ((None, None),),
            30012: ((None, None),),
            30020: ((None, None),),
            30027: ((None, None),),
            30050: ((3, None), (2, 'T')),
            30055: ((None, None),),
            30100: ((None, None),),
            30200: ((1, None),),
            30210: ((None, None),),
            30300: ((None, None),),
            30400: ((None, None),),
            30450: ((4, None), (3, 'B')),
            30457: ((None, None),),
            30500: ((None, None),),
            30502: ((None, None),),
            30505: ((None, None),),
            30510: ((3, None),),
            30522: ((None, None),),
            30530: ((2, None),),
            30532: ((2, None),),
            30534: ((2, None),),
            30536: ((2, None),),
            30538: ((2, None),),
            30540: ((2, None),),
            30542: ((2, None),),
            30544: ((1, None),),
            30545: ((1, None),),
            30546: ((1, None),),
            30547: ((3, None),),
            30550: ((None, None),),
            30560: ((6, None),),
            30566: ((5, None),),
            30571: ((4, None),),
            30575: ((3, None),),
            30578: ((2, None),),
            30580: ((1, None),),
            30581: ((None, None),),
            30600: ((None, None),),
            30620: ((None, None),),
            30627: ((None, None),),
            30700: ((None, None),),
            30720: ((1, None),),
            30721: ((3, 'T'), (2, None)),
            30726: ((1, None), (1, 'T')),
            30728: ((1, None), (1, 'T')),
            30730: ((10, None), (5, 'B')),
            30745: ((None, None),)
        }
        self._check_sublengths(exp_sublengths, blocks)

        exp_multiline_comments = {
            30000: None,
            30002: None,
            30012: (30027, [(0, 'This comment covers the following two sub-blocks')]),
            30020: None,
            30027: None,
            30050: None,
            30055: None,
            30100: None,
            30200: None,
            30210: None,
            30300: None,
            30400: None,
            30450: None,
            30457: None,
            30500: None,
            30502: None,
            30505: None,
            30510: None,
            30522: None,
            30530: (30550, [(0, '')]),
            30532: None,
            30534: None,
            30536: None,
            30538: None,
            30540: None,
            30542: None,
            30544: None,
            30545: None,
            30546: None,
            30547: None,
            30550: None,
            30560: (30581, [(0, '')]),
            30566: None,
            30571: None,
            30575: None,
            30578: None,
            30580: None,
            30581: None,
            30600: None,
            30620: None,
            30627: None,
            30700: None,
            30720: (30730, [(0, '')]),
            30721: None,
            30726: None,
            30728: None,
            30730: None,
            30745: None
        }
        self._check_multiline_comments(exp_multiline_comments, blocks)

        exp_entry_asm_directives = {
            30000: ['start'],
            30100: [],
            30200: [],
            30300: [],
            30400: [],
            30500: [],
            30600: [],
            30700: []
        }
        self._check_entry_asm_directives(exp_entry_asm_directives, blocks)

        exp_instruction_asm_directives = {
            30101: ['label=LOOP']
        }
        self._check_instruction_asm_directives(exp_instruction_asm_directives, blocks)

    def test_two_ctl_files(self):
        ctl1 = """
            b 30000
            c 30010
        """
        ctl2 = """
            g 30020
            w 30022
        """
        blocks = self._get_ctl_parser((ctl1, ctl2)).get_blocks()

        exp_ctls = {
            30000: 'b',
            30010: 'c',
            30020: 'g',
            30022: 'w'
        }
        self._check_ctls(exp_ctls, blocks)

    def test_blank_directive_out_of_order(self):
        ctl = """
            c 65534
            b 65535
              65534,1 This is a C directive
        """
        blocks = self._get_ctl_parser(ctl).get_blocks()

        exp_subctls = {
            65534: 'c',
            65535: 'b'
        }
        self._check_subctls(exp_subctls, blocks)

    def test_blank_directive_with_no_containing_block(self):
        ctl = """
              30000
            b 30001
        """
        ctl_parser = CtlParser()
        ctlfile = self.write_text_file(textwrap.dedent(ctl))
        ctl_parser.parse_ctls([ctlfile])

        warnings = self.err.getvalue().split('\n')[0:-1:2]
        exp_warnings = ['WARNING: Ignoring line 1 in {} (blank directive with no containing block):'.format(ctlfile)]
        self.assertEqual(exp_warnings, warnings)

        exp_subctls = {30001: 'b'}
        self._check_subctls(exp_subctls, ctl_parser.get_blocks())

    def test_parse_ctl_with_min_address(self):
        ctl_parser = self._get_ctl_parser(CTL, 30700)
        blocks = ctl_parser.get_blocks()

        exp_ctls = {30700: 's'}
        self._check_ctls(exp_ctls, blocks)

        exp_subctls = {
            30700: 's',
            30720: 'b',
            30721: 'b',
            30726: 'b',
            30728: 'b',
            30730: 't',
            30745: 's'
        }
        self._check_subctls(exp_subctls, blocks)

        exp_mid_block_comments = {
            30700: (),
            30720: (),
            30721: (),
            30726: (),
            30728: (),
            30730: [['Another mid-block comment']],
            30745: ()
        }
        self._check_mid_block_comments(exp_mid_block_comments, blocks)

        exp_titles = {30700: ['Zeroes at 30700']}
        self._check_titles(exp_titles, blocks)

        exp_instruction_comments = {
            30700: (),
            30720: [(0, '')],
            30721: (),
            30726: (),
            30728: (),
            30730: [(0, '')],
            30745: ()
        }
        self._check_instruction_comments(exp_instruction_comments, blocks)

        exp_descriptions = {30700: ()}
        self._check_descriptions(exp_descriptions, blocks)

        exp_registers = {30700: ()}
        self._check_registers(exp_registers, blocks)

        exp_end_comments = {30700: ()}
        self._check_end_comments(exp_end_comments, blocks)

        exp_sublengths = {
            30700: ((None, None),),
            30720: ((1, None),),
            30721: ((3, 'T'), (2, None)),
            30726: ((1, None), (1, 'T')),
            30728: ((1, None), (1, 'T')),
            30730: ((10, None), (5, 'B')),
            30745: ((None, None),)
        }
        self._check_sublengths(exp_sublengths, blocks)

        exp_multiline_comments = {
            30700: None,
            30720: (30730, [(0, '')]),
            30721: None,
            30726: None,
            30728: None,
            30730: None,
            30745: None
        }
        self._check_multiline_comments(exp_multiline_comments, blocks)

        exp_entry_asm_directives = {30700: []}
        self._check_entry_asm_directives(exp_entry_asm_directives, blocks)

        self._check_instruction_asm_directives({}, blocks)

    def test_parse_ctl_with_max_address(self):
        ctl_parser = self._get_ctl_parser(CTL, max_address=30200)
        blocks = ctl_parser.get_blocks()
        self._check_blocks(blocks)

        exp_ctls = {
            30000: 'b',
            30100: 'c'
        }
        self._check_ctls(exp_ctls, blocks)

        exp_subctls = {
            30000: 'b',
            30002: 't',
            30012: 'w',
            30020: 'c',
            30027: 'b',
            30050: 'b',
            30055: 'b',
            30100: 'c'
        }
        self._check_subctls(exp_subctls, blocks)

        exp_mid_block_comments = {
            30000: [['Block start comment']],
            30002: (),
            30012: [['Mid-block comment']],
            30020: (),
            30027: (),
            30050: (),
            30055: (),
            30100: ()
        }
        self._check_mid_block_comments(exp_mid_block_comments, blocks)

        exp_titles = {
            30000: ['Data at 30000'],
            30100: ['Routine at 30100']
        }
        self._check_titles(exp_titles, blocks)

        exp_instruction_comments = {
            30000: (),
            30002: [(0, 'Message in the data block')],
            30012: [(0, '')],
            30020: [(0, '')],
            30027: (),
            30050: [(0, 'Complex DEFB with a blank directive')],
            30055: (),
            30100: ()
        }
        self._check_instruction_comments(exp_instruction_comments, blocks)

        exp_descriptions = {
            30000: (),
            30100: [['Description of routine at 30100']]
        }
        self._check_descriptions(exp_descriptions, blocks)

        exp_registers = {
            30000: (),
            30100: [['A Some value'], ['BC Some other value']]
        }
        self._check_registers(exp_registers, blocks)

        exp_end_comments = {
            30000: (),
            30100: [
                ['First paragraph of the end comment for the routine at 30100'],
                ['Second paragraph of the end comment for the routine at 30100']
            ]
        }
        self._check_end_comments(exp_end_comments, blocks)

        exp_sublengths = {
            30000: ((None, None),),
            30002: ((None, None),),
            30012: ((None, None),),
            30020: ((None, None),),
            30027: ((None, None),),
            30050: ((3, None), (2, 'T')),
            30055: ((None, None),),
            30100: ((None, None),)
        }
        self._check_sublengths(exp_sublengths, blocks)

        exp_multiline_comments = {
            30000: None,
            30002: None,
            30012: (30027, [(0, 'This comment covers the following two sub-blocks')]),
            30020: None,
            30027: None,
            30050: None,
            30055: None,
            30100: None
        }
        self._check_multiline_comments(exp_multiline_comments, blocks)

        exp_entry_asm_directives = {
            30000: ['start'],
            30100: []
        }
        self._check_entry_asm_directives(exp_entry_asm_directives, blocks)

        exp_instruction_asm_directives = {
            30101: ['label=LOOP']
        }
        self._check_instruction_asm_directives(exp_instruction_asm_directives, blocks)

    def test_parse_ctl_with_min_and_max_addresses(self):
        ctl_parser = self._get_ctl_parser(CTL, 30100, 30300)
        blocks = ctl_parser.get_blocks()
        self._check_blocks(blocks)

        exp_ctls = {
            30100: 'c',
            30200: 'g'
        }
        self._check_ctls(exp_ctls, blocks)

        exp_subctls = {
            30100: 'c',
            30200: 'b',
            30210: 'g'
        }
        self._check_subctls(exp_subctls, blocks)

        exp_mid_block_comments = {
            30100: (),
            30200: (),
            30210: ()
        }
        self._check_mid_block_comments(exp_mid_block_comments, blocks)

        exp_titles = {
            30100: ['Routine at 30100'],
            30200: ['Game status buffer entry at 30200']
        }
        self._check_titles(exp_titles, blocks)

        exp_instruction_comments = {
            30100: (),
            30200: [(0, "Blank directive in a 'g' block")],
            30210: ()
        }
        self._check_instruction_comments(exp_instruction_comments, blocks)

        exp_descriptions = {
            30100: [['Description of routine at 30100']],
            30200: ()
        }
        self._check_descriptions(exp_descriptions, blocks)

        exp_registers = {
            30100: [['A Some value'], ['BC Some other value']],
            30200: ()
        }
        self._check_registers(exp_registers, blocks)

        exp_end_comments = {
            30100: [
                ['First paragraph of the end comment for the routine at 30100'],
                ['Second paragraph of the end comment for the routine at 30100']
            ],
            30200: ()
        }
        self._check_end_comments(exp_end_comments, blocks)

        exp_sublengths = {
            30100: ((None, None),),
            30200: ((1, None),),
            30210: ((None, None),)
        }
        self._check_sublengths(exp_sublengths, blocks)

        exp_multiline_comments = {
            30100: None,
            30200: None,
            30210: None
        }
        self._check_multiline_comments(exp_multiline_comments, blocks)

        exp_entry_asm_directives = {
            30100: [],
            30200: []
        }
        self._check_entry_asm_directives(exp_entry_asm_directives, blocks)

        exp_instruction_asm_directives = {
            30101: ['label=LOOP']
        }
        self._check_instruction_asm_directives(exp_instruction_asm_directives, blocks)

    def test_invalid_lines(self):
        ctl_specs = [
            ('  30000,1',           'blank directive with no containing block'),
            ('B 30745,15,5:X10',    'invalid integer'),
            ('T 30760,5,2:Y3',      'invalid integer'),
            ('W 30765,5,1:B4',      'invalid integer'),
            ('S 30770,10,T8:2',     'invalid integer'),
            ('B 30780,10,h,5',      'invalid integer'),
            ('C 40000,Q',           'invalid integer'),
            ('@ FEDCB label=Z',     'invalid ASM directive address'),
            ('@ 49152',             'invalid ASM directive declaration'),
            ('b 50000,20',          'extra parameters after address'),
            ('c 50000,20',          'extra parameters after address'),
            ('g 50000,20',          'extra parameters after address'),
            ('i 50000,20',          'extra parameters after address'),
            ('s 50000,20',          'extra parameters after address'),
            ('t 50000,20',          'extra parameters after address'),
            ('u 50000,20',          'extra parameters after address'),
            ('w 50000,20',          'extra parameters after address'),
            ('D 50000,20 Desc.',    'extra parameters after address'),
            ('E 50000,20 End.',     'extra parameters after address'),
            ('N 50000,20 Note.',    'extra parameters after address'),
            ('R 50000,20 A 10',     'extra parameters after address'),
            ('b b50010',            'invalid address'),
            ('d 50020',             'invalid directive'),
            ('! 50030',             'invalid directive'),
            ('@ 50000 ignoreua:g',  "invalid @ignoreua directive suffix: 'g'"),
            ('L 51000',             'loop length not specified'),
            ('L 51000,10',          'loop count not specified')
        ]
        ctls = [spec[0] for spec in ctl_specs]
        ctl_parser = CtlParser()
        ctlfile = self.write_text_file('\n'.join(ctls))
        ctl_parser.parse_ctls([ctlfile])
        exp_warnings = []
        for line_no, (ctl, error_msg) in enumerate(ctl_specs, 1):
            if error_msg:
                exp_warnings.append('WARNING: Ignoring line {} in {} ({}):'.format(line_no, ctlfile, error_msg))
        warnings = self.err.getvalue().split('\n')[:-1]
        self.assertEqual(exp_warnings, warnings[0::2])
        invalid_ctls = [spec[0] for spec in ctl_specs if spec[1]]
        self.assertEqual(invalid_ctls, warnings[1::2])

    def test_comments(self):
        ctl = """
            # This is a comment
            b 32768
            % This is also a comment
            w 32769
            ; This is a comment too
        """
        ctl_parser = self._get_ctl_parser(ctl)

        self.assertEqual(self.err.getvalue(), '')
        self._check_ctls({32768: 'b', 32769: 'w'}, ctl_parser.get_blocks())

    def test_bases(self):
        ctl = """
            c 50000 Test numeric instruction operand bases
              50000,b
              50002,h2
              50006,hb
              50010,6,d2,nb4
              50016,,c2,dc4
              50022,6,b2
              50028,b6,n2,2,h2
        """
        ctl_parser = self._get_ctl_parser(ctl)

        exp_sublengths = {
            50000: ((None, 'b'),),
            50002: ((None, 'h'),),
            50004: ((None, None),),
            50006: ((None, 'hb'),),
            50010: ((2, 'd'),),
            50012: ((4, 'nb'),),
            50016: ((2, 'c'),),
            50018: ((4, 'dc'),),
            50022: ((2, 'b'),),
            50028: ((2, 'n'),),
            50030: ((2, 'b'),),
            50032: ((2, 'h'),),
            50034: ((None, None),)
        }
        self._check_sublengths(exp_sublengths, ctl_parser.get_blocks())

    def test_byte_formats(self):
        ctl = """
            b 40000 Test byte formats
              40000,b 5 bytes in binary format
              40005,b5 5 more bytes in binary format
            B 40010,b10,5,d3,h2 5 binary, 3 decimal, 2 hex
            B 40020,b,2:d3:h5 2 binary, 3 decimal, 5 hex, one line
              40030,,b6,3,h1 6 binary, 3 default, 1 hex
              40040,10,b5:2:h3 5 binary, 2 default, 3 hex, one line
              40050,10,1,T9 1 default, 9 text
              40060,10,h4:T6 4 hex, 6 text, one line
            T 40070,10,3,b7 3 text, 7 binary
            T 40080,10,2:h8 2 text, 8 hex, one line
            T 40090,10,5,B5 5 text, 5 default
        """
        ctl_parser = self._get_ctl_parser(ctl)

        exp_sublengths = {
            40000: ((None, 'b'),),
            40005: ((None, 'b'),),
            40010: ((5, 'b'),),
            40015: ((3, 'd'),),
            40018: ((2, 'h'),),
            40020: ((2, 'b'), (3, 'd'), (5, 'h')),
            40030: ((6, 'b'),),
            40036: ((3, None),),
            40039: ((1, 'h'),),
            40040: ((5, 'b'), (2, None), (3, 'h')),
            40050: ((1, None),),
            40051: ((9, 'T'),),
            40060: ((4, 'h'), (6, 'T')),
            40070: ((3, None),),
            40073: ((7, 'b'),),
            40080: ((2, None), (8, 'h')),
            40090: ((5, None),),
            40095: ((5, 'B'),),
            40100: ((None, None),)
        }
        self._check_sublengths(exp_sublengths, ctl_parser.get_blocks())

    def test_word_formats(self):
        ctl = """
            w 40000 Test word formats
              40000,10 5 default
              40010,b10 5 words in binary format
            W 40020,b10,6,d2,h2 3 binary, 1 decimal, 1 hex
            W 40030,b10,4:d4:h2 2 binary, 2 decimal, 1 hex, one line
              40040,10,b2,4,h4 1 binary, 2 default, 2 hex
              40050,10,b2:6:h2 1 binary, 3 default, 1 hex, one line
        """
        ctl_parser = self._get_ctl_parser(ctl)

        exp_sublengths = {
            40000: ((None, None),),
            40010: ((None, 'b'),),
            40020: ((6, 'b'),),
            40026: ((2, 'd'),),
            40028: ((2, 'h'),),
            40030: ((4, 'b'), (4, 'd'), (2, 'h')),
            40040: ((2, 'b'),),
            40042: ((4, None),),
            40046: ((4, 'h'),),
            40050: ((2, 'b'), (6, None), (2, 'h')),
            40060: ((None, None),)
        }
        self._check_sublengths(exp_sublengths, ctl_parser.get_blocks())

    def test_s_directives_with_no_byte_value(self):
        ctl = """
            s 50000 Test s/S directives with no byte value
              50000,10
              50010,b10
              50020,d10
              50030,h10
            S 50040,b20,5,d5,h5
            S 50060,d20,b5,5,h5
            S 50080,h20,b5,d5,5
              50100,20,b5,d5,5
        """
        ctl_parser = self._get_ctl_parser(ctl)

        exp_sublengths = {
            50000: ((None, None),),
            50010: ((None, 'b'),),
            50020: ((None, 'd'),),
            50030: ((None, 'h'),),
            50040: ((5, 'b'),),
            50045: ((5, 'd'),),
            50050: ((5, 'h'),),
            50060: ((5, 'b'),),
            50065: ((5, 'd'),),
            50070: ((5, 'h'),),
            50080: ((5, 'b'),),
            50085: ((5, 'd'),),
            50090: ((5, 'h'),),
            50100: ((5, 'b'),),
            50105: ((5, 'd'),),
            50110: ((5, None),),
            50120: ((None, None),)
        }
        self._check_sublengths(exp_sublengths, ctl_parser.get_blocks())

    def test_s_directives_with_byte_values(self):
        ctl = """
            s 50120 Test s/S directives with byte values
              50120,20,d20:b%10001000
              50140,20,20:h$44
              50160,12,10:h10,h2:2
              50172,8,2:c",",2:c";",4:c"!"
              50180,70,5:c"*"*2,58:c":",2:c" "
              50250,10,4:c"\\"",6:c"\\\\"
        """
        ctl_parser = self._get_ctl_parser(ctl)

        exp_sublengths = {
            50120: ((20, 'd'), (136, 'b')),
            50140: ((20, None), (68, 'h')),
            50160: ((10, None), (10, 'h')),
            50170: ((2, 'h'), (2, None)),
            50172: ((2, None), (44, 'c')),
            50174: ((2, None), (59, 'c')),
            50176: ((4, None), (33, 'c')),
            50180: ((5, None), (42, 'c')),
            50185: ((5, None), (42, 'c')),
            50190: ((58, None), (58, 'c')),
            50248: ((2, None), (32, 'c')),
            50250: ((4, None), (34, 'c')),
            50254: ((6, None), (92, 'c')),
            50260: ((None, None),)
        }
        self._check_sublengths(exp_sublengths, ctl_parser.get_blocks())

    def test_s_directives_with_blank_byte_values(self):
        ctl = """
            s 60000 Test s/S directives with blank byte values
              60000,20,20:c
              60020,40,c"(":b
              60060,10,h$0A:d
              60070,10,10:h
              60080,10,b%1010:n
              60090,10,5:c*2
        """
        ctl_parser = self._get_ctl_parser(ctl)

        exp_sublengths = {
            60000: ((20, None), (None, 'c')),
            60020: ((40, 'c'), (None, 'b')),
            60060: ((10, 'h'), (None, 'd')),
            60070: ((10, None), (None, 'h')),
            60080: ((10, 'b'), (None, 'n')),
            60090: ((5, None), (None, 'c')),
            60095: ((5, None), (None, 'c')),
            60100: ((None, None),)
        }
        self._check_sublengths(exp_sublengths, ctl_parser.get_blocks())

    def test_assemble_directives(self):
        ctl = """
            @ 30000 assemble=1
            c 30000 Routine at 30000
            @ 30001 assemble=0
        """
        exp_entry_directives = {
            30000: ['assemble=1']
        }
        exp_instruction_directives = {
            30001: ['assemble=0']
        }
        self._test_asm_directives(ctl, exp_entry_directives, exp_instruction_directives)

    def test_bfix_directives(self):
        ctl = """
            @ 40000 bfix=XOR A
            c 40000 Routine at 40000
            @ 40001 bfix=XOR B
        """
        exp_entry_directives = {
            40000: []
        }
        exp_instruction_directives = {
            40000: ['bfix=XOR A'],
            40001: ['bfix=XOR B']
        }
        self._test_asm_directives(ctl, exp_entry_directives, exp_instruction_directives)

    def test_defb_directives(self):
        ctl = """
            @ 30000 defb=49152:13
            c 30000 Routine at 30000
            @ 30001 defb=49153:14
        """
        exp_entry_directives = {
            30000: ['defb=49152:13']
        }
        exp_instruction_directives = {
            30001: ['defb=49153:14']
        }
        self._test_asm_directives(ctl, exp_entry_directives, exp_instruction_directives)

    def test_defs_directives(self):
        ctl = """
            @ 40000 defs=32768:10,2
            c 40000 Routine at 40000
            @ 40001 defs=32778:11,3
        """
        exp_entry_directives = {
            40000: ['defs=32768:10,2']
        }
        exp_instruction_directives = {
            40001: ['defs=32778:11,3']
        }
        self._test_asm_directives(ctl, exp_entry_directives, exp_instruction_directives)

    def test_defw_directives(self):
        ctl = """
            @ 50000 defw=24576:32767
            c 50000 Routine at 50000
            @ 50001 defw=24577:65535
        """
        exp_entry_directives = {
            50000: ['defw=24576:32767']
        }
        exp_instruction_directives = {
            50001: ['defw=24577:65535']
        }
        self._test_asm_directives(ctl, exp_entry_directives, exp_instruction_directives)

    def test_end_directives(self):
        ctl = """
            c 40000 Routine at 40000
            @ 40001 end
            @ 40002 end
            c 40002 Routine at 40002
        """
        exp_entry_directives = {
            40000: [],
            40002: ['end']
        }
        exp_instruction_directives = {
            40001: ['end']
        }
        self._test_asm_directives(ctl, exp_entry_directives, exp_instruction_directives)

    def test_equ_directives(self):
        ctl = """
            @ 50000 equ=ATTRS=22528
            c 50000 Routine at 50000
            @ 50001 equ=UDG=23675
        """
        exp_entry_directives = {
            50000: ['equ=ATTRS=22528'],
        }
        exp_instruction_directives = {
            50001: ['equ=UDG=23675']
        }
        self._test_asm_directives(ctl, exp_entry_directives, exp_instruction_directives)

    def test_if_directives(self):
        ctl = """
            @ 40000 if({asm})(replace=/foo/bar)
            c 40000 Routine at 40000
            @ 40001 if({case}==1)(replace=/FOO/foo)
        """
        exp_entry_directives = {
            40000: ['if({asm})(replace=/foo/bar)']
        }
        exp_instruction_directives = {
            40001: ['if({case}==1)(replace=/FOO/foo)']
        }
        self._test_asm_directives(ctl, exp_entry_directives, exp_instruction_directives)

    def test_ignoreua_directives(self):
        ctl = """
            @ 30000 ignoreua:t
            c 30000 Routine at 30000
            c 30001 Routine
            @ 30001 ignoreua:d
            D 30001 Description of the routine at 30001
            @ 30001 ignoreua:r
            R 30001 HL 30001
            @ 30001 ignoreua
              30001 Instruction-level comment at 30001
            c 30002 Routine
            @ 30003 ignoreua:m
            N 30003 Mid-block comment above 30003.
            @ 30003 ignoreua:i
              30003 Instruction-level comment at 30003
            c 30004 Routine
            @ 30004 ignoreua:i
              30004,1 Instruction-level comment at 30004
            @ 30005 ignoreua:m
            N 30005 Mid-block comment above 30005.
            @ 30004 ignoreua:e
            E 30004 End comment for the routine at 30004.
        """
        blocks = self._get_ctl_parser(ctl).get_blocks()

        exp_entry_directives = {
            30000: ['t'],
            30001: ['d', 'r'],
            30002: [],
            30004: ['e']
        }
        exp_other_directives = {
            30000: [],
            30001: ['i'],
            30003: ['i', 'm'],
            30004: ['i'],
            30005: ['m']
        }
        self._check_ignoreua_directives(exp_entry_directives, exp_other_directives, blocks)

    def test_isub_directives(self):
        ctl = """
            @ 40000 isub=LD A,1
            c 40000 Routine at 40000
            @ 40002 isub=LD A,2
        """
        exp_entry_directives = {
            40000: []
        }
        exp_instruction_directives = {
            40000: ['isub=LD A,1'],
            40002: ['isub=LD A,2']
        }
        self._test_asm_directives(ctl, exp_entry_directives, exp_instruction_directives)

    def test_keep_directives(self):
        ctl = """
            @ 50000 keep
            c 50000 Routine at 50000
            @ 50003 keep
        """
        exp_entry_directives = {
            50000: []
        }
        exp_instruction_directives = {
            50000: ['keep'],
            50003: ['keep']
        }
        self._test_asm_directives(ctl, exp_entry_directives, exp_instruction_directives)

    def test_label_directives(self):
        ctl = """
            @ 60000 label=START
            c 60000 Routine at 60000
            @ 60003 label=LOOP
        """
        exp_entry_directives = {
            60000: []
        }
        exp_instruction_directives = {
            60000: ['label=START'],
            60003: ['label=LOOP']
        }
        self._test_asm_directives(ctl, exp_entry_directives, exp_instruction_directives)

    def test_nowarn_directives(self):
        ctl = """
            @ 40000 nowarn
            c 40000 Routine at 40000
            @ 40003 nowarn
        """
        exp_entry_directives = {
            40000: []
        }
        exp_instruction_directives = {
            40000: ['nowarn'],
            40003: ['nowarn']
        }
        self._test_asm_directives(ctl, exp_entry_directives, exp_instruction_directives)

    def test_ofix_directives(self):
        ctl = """
            @ 50000 ofix=LD HL,12345
            c 50000 Routine at 50000
            @ 50003 ofix=CALL 34567
        """
        exp_entry_directives = {
            50000: []
        }
        exp_instruction_directives = {
            50000: ['ofix=LD HL,12345'],
            50003: ['ofix=CALL 34567']
        }
        self._test_asm_directives(ctl, exp_entry_directives, exp_instruction_directives)

    def test_org_directives(self):
        ctl = """
            @ 60000 org=60000
            c 60000 Routine at 60000
            @ 60001 org
        """
        exp_entry_directives = {
            60000: ['org=60000'],
        }
        exp_instruction_directives = {
            60001: ['org']
        }
        self._test_asm_directives(ctl, exp_entry_directives, exp_instruction_directives)

    def test_rem_directives(self):
        ctl = """
            @ 30000 rem=It begins
            c 30000 Routine at 30000
            @ 30010 rem=It ends
        """
        exp_entry_directives = {
            30000: []
        }
        exp_instruction_directives = {
            30000: ['rem=It begins'],
            30010: ['rem=It ends']
        }
        self._test_asm_directives(ctl, exp_entry_directives, exp_instruction_directives)

    def test_remote_directives(self):
        ctl = """
            @ 32768 remote=main:29012,29015
            c 32768 Routine at 32768
            @ 32769 remote=start:20112
        """
        exp_entry_directives = {
            32768: ['remote=main:29012,29015']
        }
        exp_instruction_directives = {
            32769: ['remote=start:20112']
        }
        self._test_asm_directives(ctl, exp_entry_directives, exp_instruction_directives)

    def test_replace_directives(self):
        ctl = """
            @ 40000 replace=/foo/bar
            c 40000 Routine at 40000
            @ 40001 replace=/baz/qux
        """
        exp_entry_directives = {
            40000: ['replace=/foo/bar'],
        }
        exp_instruction_directives = {
            40001: ['replace=/baz/qux']
        }
        self._test_asm_directives(ctl, exp_entry_directives, exp_instruction_directives)

    def test_rfix_directives(self):
        ctl = """
            @ 50000 rfix=LD BC,0
            c 50000 Routine at 50000
            @ 50002 rfix=LD HL,0
        """
        exp_entry_directives = {
            50000: []
        }
        exp_instruction_directives = {
            50000: ['rfix=LD BC,0'],
            50002: ['rfix=LD HL,0']
        }
        self._test_asm_directives(ctl, exp_entry_directives, exp_instruction_directives)

    def test_rsub_directives(self):
        ctl = """
            @ 60000 rsub=LD DE,0
            c 60000 Routine at 60000
            @ 60002 rsub=LD IX,0
        """
        exp_entry_directives = {
            60000: []
        }
        exp_instruction_directives = {
            60000: ['rsub=LD DE,0'],
            60002: ['rsub=LD IX,0']
        }
        self._test_asm_directives(ctl, exp_entry_directives, exp_instruction_directives)

    def test_set_directives(self):
        ctl = """
            @ 30000 set-crlf=1
            c 30000 Routine at 30000
            @ 30001 set-tab=1
        """
        exp_entry_directives = {
            30000: ['set-crlf=1'],
        }
        exp_instruction_directives = {
            30001: ['set-tab=1']
        }
        self._test_asm_directives(ctl, exp_entry_directives, exp_instruction_directives)

    def test_ssub_directives(self):
        ctl = """
            @ 40000 ssub=INC HL
            c 40000 Routine at 60000
            @ 40001 ssub=INC BC
        """
        exp_entry_directives = {
            40000: []
        }
        exp_instruction_directives = {
            40000: ['ssub=INC HL'],
            40001: ['ssub=INC BC']
        }
        self._test_asm_directives(ctl, exp_entry_directives, exp_instruction_directives)

    def test_start_directives(self):
        ctl = """
            @ 50000 start
            c 50000 Routine at 50000
            @ 50001 start
        """
        exp_entry_directives = {
            50000: ['start'],
        }
        exp_instruction_directives = {
            50001: ['start']
        }
        self._test_asm_directives(ctl, exp_entry_directives, exp_instruction_directives)

    def test_writer_directives(self):
        ctl = """
            @ 60000 writer=x.y.z
            c 60000 Routine at 60000
            @ 60001 writer=foo.bar.baz
        """
        exp_entry_directives = {
            60000: ['writer=x.y.z'],
        }
        exp_instruction_directives = {
            60001: ['writer=foo.bar.baz']
        }
        self._test_asm_directives(ctl, exp_entry_directives, exp_instruction_directives)

    def test_order_of_entry_asm_directives_is_preserved(self):
        ctl = """
            @ 30000 start
            @ 30000 equ=ATTRS=22528
            @ 30000 replace=/foo/bar
            @ 30000 replace=/baz/qux
            c 30000 Routine at 30000
        """
        blocks = self._get_ctl_parser(ctl).get_blocks()

        exp_entry_directives = {
            30000: ['start', 'equ=ATTRS=22528', 'replace=/foo/bar', 'replace=/baz/qux']
        }
        self._check_entry_asm_directives(exp_entry_directives, blocks)

    def test_header_block(self):
        ctl = """
            > 60000 ; This is a header.
            c 60000 Routine
        """
        exp_headers = {60000: ['; This is a header.']}
        exp_footers = {60000: ()}

        blocks = self._get_ctl_parser(ctl).get_blocks()
        self._check_headers(exp_headers, blocks)
        self._check_footers(exp_footers, blocks)

    def test_two_header_blocks(self):
        ctl = """
            > 30000 ; This is a header.
            > 30000
            > 30000 ; This is another header.
            c 30000 Routine
        """
        exp_headers = {
            30000: [
                '; This is a header.',
                '',
                '; This is another header.'
            ]
        }
        exp_footers = {30000: ()}

        blocks = self._get_ctl_parser(ctl).get_blocks()
        self._check_headers(exp_headers, blocks)
        self._check_footers(exp_footers, blocks)

    def test_header_block_unaffected_by_dot_directives(self):
        ctl = """
            > 40000 ; This is the start of the header.
            . This is an intervening dot directive.
            > 40000 ; This is the end of the header.
            . Another dot directive to ignore.
            c 40000 Routine
        """
        exp_headers = {
            40000: [
                '; This is the start of the header.',
                '; This is the end of the header.'
            ]
        }

        blocks = self._get_ctl_parser(ctl).get_blocks()
        self._check_headers(exp_headers, blocks)

    def test_footer_block(self):
        ctl = """
            c 50000 Routine
            > 50000,1 ; This is a footer.
        """
        exp_headers = {50000: ()}
        exp_footers = {50000: ['; This is a footer.']}

        blocks = self._get_ctl_parser(ctl).get_blocks()
        self._check_headers(exp_headers, blocks)
        self._check_footers(exp_footers, blocks)

    def test_two_footer_blocks(self):
        ctl = """
            c 60000 Routine
            > 60000,1 ; This is a footer.
            > 60000,1
            > 60000,1 ; This is another footer.
        """
        exp_headers = {60000: ()}
        exp_footers = {
            60000: [
                '; This is a footer.',
                '',
                '; This is another footer.'
            ]
        }

        blocks = self._get_ctl_parser(ctl).get_blocks()
        self._check_headers(exp_headers, blocks)
        self._check_footers(exp_footers, blocks)

    def test_footer_block_unaffected_by_dot_directives(self):
        ctl = """
            c 40000 Routine
            > 40000,1 ; This is the start of the footer.
            . This is an intervening dot directive.
            > 40000,1 ; This is the end of the footer.
            . Another dot directive to ignore.
        """
        exp_footers = {
            40000: [
                '; This is the start of the footer.',
                '; This is the end of the footer.'
            ]
        }

        blocks = self._get_ctl_parser(ctl).get_blocks()
        self._check_footers(exp_footers, blocks)

    def test_registers(self):
        ctl = """
            c 40000 Routine
            R 40000 BC Important value
            R 40000 DE
            R 40000
            R 40000 HL Another important value
        """
        ctl_parser = self._get_ctl_parser(ctl)
        blocks = ctl_parser.get_blocks()
        self.assertEqual(len(blocks), 1)

        exp_registers = [
            ['BC Important value'],
            ['DE'],
            [''],
            ['HL Another important value']
        ]
        self.assertEqual(exp_registers, blocks[0].registers)

    def test_N_directive(self):
        ctl = """
            c 40000 Routine
            D 40000 Description.
            N 40000 Paragraph 1.
            N 40000 Paragraph 2.
            N 40001 Mid-routine comment.
        """
        ctl_parser = self._get_ctl_parser(ctl)
        blocks = ctl_parser.get_blocks()
        self.assertEqual(len(blocks), 1)

        self.assertEqual([['Description.']], blocks[0].description)
        sub_blocks = blocks[0].blocks
        self.assertEqual(len(sub_blocks), 2)
        self.assertEqual([['Paragraph 1.'], ['Paragraph 2.']], sub_blocks[0].header)
        self.assertEqual([['Mid-routine comment.']], sub_blocks[1].header)

    def test_M_directive_terminates_previous_sub_block(self):
        ctl = """
            c 65533
              65533 This sub-block is terminated by the following M directive
            M 65534,2 This spans an implicit "C" sub-block and a "B" sub-block
            B 65535,1
        """
        ctl_parser = self._get_ctl_parser(ctl)
        blocks = ctl_parser.get_blocks()

        self.assertEqual(len(blocks), 1)
        sub_blocks = blocks[0].blocks
        exp_subctls = {
            65533: ('c', [(0, 'This sub-block is terminated by the following M directive')], None),
            65534: ('c', (), (65536, [(0, 'This spans an implicit "C" sub-block and a "B" sub-block')])),
            65535: ('b', [(0, '')], None)
        }
        subctls = {b.start:(b.ctl, b.comment, b.multiline_comment) for b in sub_blocks}
        self.assertEqual(exp_subctls, subctls)

    def test_loop(self):
        start = 30000
        length = 25
        count = 2
        end = start + length * count
        ctl = """
            @ 30000 start
            @ 30000 org=30000
            c 30000 This entry should not be repeated
            D 30000 This entry description should not be repeated
            R 30000 HL This register should not be repeated
              30000,5 Begin
            B 30005,5,1,2
            N 30010 A mid-block comment
            M 30010,10 A multi-line comment
            S 30010,6
            W 30016,4,4
            @ 30020 label=END
            T 30020,5,4:B1 End
            E 30000 This end comment should not be repeated
            L {},{},{}
        """.format(start, length, count)
        ctl_parser = self._get_ctl_parser(ctl)
        blocks = ctl_parser.get_blocks()
        self.assertEqual(len(blocks), 1)
        block = blocks[0]
        sub_blocks = block.blocks
        sub_block_map = {b.start: b for b in sub_blocks}

        # Check B, C, S, T and W sub-blocks
        i = 0
        exp_subctls = {}
        exp_sublengths = {}
        for a in range(start, end, length):
            for offset, subctl, sublengths in (
                (0, 'c', ((None, None),)),
                (5, 'b', ((1, None),)),
                (6, 'b', ((2, None),)),
                (10, 's', ((None, None),)),
                (16, 'w', ((4, None),)),
                (20, 't', ((4, None), (1, 'B')),),
                (25, 'c', ((None, None),))
            ):
                address = a + offset
                exp_subctls[address] = subctl
                exp_sublengths[address] = sublengths
                i += 1
        self._check_subctls(exp_subctls, blocks)
        self._check_sublengths(exp_sublengths, blocks)

        # Check mid-block comments
        offset = 10
        for a in range(start + offset, end, length):
            self.assertEqual([['A mid-block comment']], sub_block_map[a].header)

        # Check multi-line comments
        offset = 10
        for a in range(start + offset, end, length):
            self.assertEqual((a + offset, [(0, 'A multi-line comment')]), sub_block_map[a].multiline_comment)

        # Check entry-level directives (c, D, E, R)
        self._check_ctls({start: 'c'}, blocks)
        self.assertEqual([['This entry description should not be repeated']], block.description)
        self.assertEqual([['HL This register should not be repeated']], block.registers)
        self.assertEqual([['This end comment should not be repeated']], block.end_comment)

        # Check entry-level ASM directives
        self.assertEqual(['start', 'org=30000'], block.asm_directives)

        # Check instruction-level ASM directives
        exp_directives = {start + 20: ['label=END']}
        self._check_instruction_asm_directives(exp_directives, blocks)

    def test_loop_including_entries(self):
        start = 40000
        length = 25
        count = 3
        end = start + length * count
        ctl = """
            @ 40000 start
            @ 40000 org=40000
            c 40000 This entry should be repeated
            D 40000 This entry description should be repeated
            R 40000 HL This register should be repeated
              40000,5 Begin
            B 40005,5,1,2
            N 40010 A mid-block comment
            M 40010,10 A multi-line comment
            S 40010,6
            W 40016,4,4
            @ 40020 label=END
            T 40020,5,4:B1 End
            E 40000 This end comment should be repeated
            L {},{},{},1
        """.format(start, length, count)
        ctl_parser = self._get_ctl_parser(ctl)
        blocks = ctl_parser.get_blocks()
        sub_block_map = {s.start: s for b in blocks for s in b.blocks}

        # Check B, C, S, T and W sub-blocks
        i = 0
        exp_subctls = {}
        exp_sublengths = {}
        for a in range(start, end, length):
            sub_blocks = blocks[i].blocks
            for offset, subctl, sublengths in (
                (0, 'c', ((None, None),)),
                (5, 'b', ((1, None),)),
                (6, 'b', ((2, None),)),
                (10, 's', ((None, None),)),
                (16, 'w', ((4, None),)),
                (20, 't', ((4, None), (1, 'B')),),
                (25, 'c', ((None, None),))
            ):
                address = a + offset
                exp_subctls[address] = subctl
                exp_sublengths[address] = sublengths
            i += 1
        self._check_subctls(exp_subctls, blocks)
        self._check_sublengths(exp_sublengths, blocks)

        # Check mid-block comments
        offset = 10
        for a in range(start + offset, end, length):
            self.assertEqual([['A mid-block comment']], sub_block_map[a].header)

        # Check multi-line comments
        exp_multiline_comments = {}
        for a in range(start, end, length):
            for b in (0, 5, 6, 10, 16, 20, 25):
                address = a + b
                if b == 5:
                    exp_multiline_comments[address] = (address + 3, [(0, '')])
                elif b == 10:
                    exp_multiline_comments[address] = (address + 10, [(0, 'A multi-line comment')])
                else:
                    exp_multiline_comments[address] = None
        self._check_multiline_comments(exp_multiline_comments, blocks)

        # Check entry-level directives (c, D, E, R)
        exp_ctls = {}
        exp_descriptions = {}
        exp_registers = {}
        exp_end_comments = {}
        for i, a in enumerate(range(start, end, length)):
            exp_ctls[a] = 'c'
            exp_descriptions[a] = [['This entry description should be repeated']]
            exp_registers[a] = [['HL This register should be repeated']]
            exp_end_comments[a] = [['This end comment should be repeated']]
        self._check_ctls(exp_ctls, blocks)
        self._check_descriptions(exp_descriptions, blocks)
        self._check_registers(exp_registers, blocks)
        self._check_end_comments(exp_end_comments, blocks)

        # Check entry-level ASM directives
        self.assertEqual(['start', 'org=40000'], blocks[0].asm_directives)
        for block in blocks[1:]:
            self.assertEqual([], block.asm_directives)

        # Check instruction-level ASM directives
        exp_directives = {start + 20: ['label=END']}
        self._check_instruction_asm_directives(exp_directives, blocks)

    def test_loop_crossing_64k_boundary(self):
        ctl = """
            u 65532
            W 65532,2
            L 65532,2,3
        """
        ctl_parser = self._get_ctl_parser(ctl)
        warnings = self.err.getvalue().split('\n')

        # Check warning
        self.assertEqual(warnings[0], 'WARNING: Loop crosses 64K boundary:')
        self.assertEqual(warnings[1], 'L 65532,2,3')

        # Check that the W sub-block is repeated anyway
        exp_subctls = {65532: 'w', 65534: 'w'}
        self._check_subctls(exp_subctls, ctl_parser.get_blocks())

    def test_loop_with_entries_crossing_64k_boundary(self):
        ctl = """
            b 65534
            L 65534,1,4,1
        """
        ctl_parser = self._get_ctl_parser(ctl)
        warnings = self.err.getvalue().split('\n')

        # Check warning
        self.assertEqual(warnings[0], 'WARNING: Loop crosses 64K boundary:')
        self.assertEqual(warnings[1], 'L 65534,1,4,1')

        # Check that there is no block that starts past the boundary
        blocks = ctl_parser.get_blocks()
        self.assertEqual(blocks[-1].start, 65535)

    def test_loop_is_trimmed_by_max_address(self):
        ctl = """
            b 30000
            N 30000 A comment
            M 30000,10 Some bytes and text
            B 30000,5
            T 30005,5,4:B1
            B 30010,10 Some more bytes
            L 30000,20,3
        """
        blocks = self._get_ctl_parser(ctl, max_address=30040).get_blocks()

        exp_subctls = {
            30000: 'b',
            30005: 't',
            30010: 'b',
            30020: 'b',
            30025: 't',
            30030: 'b'
        }
        self._check_subctls(exp_subctls, blocks)

        exp_mid_block_comments = {
            30000: [['A comment']],
            30005: (),
            30010: (),
            30020: [['A comment']],
            30025: (),
            30030: ()
        }
        self._check_mid_block_comments(exp_mid_block_comments, blocks)

        exp_instruction_comments = {
            30000: [(0, '')],
            30005: [(0, '')],
            30010: [(0, 'Some more bytes')],
            30020: [(0, '')],
            30025: [(0, '')],
            30030: [(0, 'Some more bytes')]
        }
        self._check_instruction_comments(exp_instruction_comments, blocks)

        exp_multiline_comments = {
            30000: (30010, [(0, 'Some bytes and text')]),
            30005: None,
            30010: None,
            30020: (30030, [(0, 'Some bytes and text')]),
            30025: None,
            30030: None,
        }
        self._check_multiline_comments(exp_multiline_comments, blocks)

        exp_sublengths = {
            30000: ((None, None),),
            30005: ((4, None), (1, 'B')),
            30010: ((None, None),),
            30020: ((None, None),),
            30025: ((4, None), (1, 'B')),
            30030: ((None, None),)
        }
        self._check_sublengths(exp_sublengths, blocks)

    def test_loop_with_entries_is_trimmed_by_max_address(self):
        ctl = """
            b 30000 A block of bytes
            D 30000 This is a block of bytes
            R 30000 A 0
            B 30000,5
            T 30005,5
            E 30000 The end
            L 30000,10,3,1
        """
        blocks = self._get_ctl_parser(ctl, max_address=30020).get_blocks()

        exp_ctls = {
            30000: 'b',
            30010: 'b'
        }
        self._check_ctls(exp_ctls, blocks)

        exp_subctls = {
            30000: 'b',
            30005: 't',
            30010: 'b',
            30015: 't'
        }
        self._check_subctls(exp_subctls, blocks)

        exp_descriptions = {
            30000: [['This is a block of bytes']],
            30010: [['This is a block of bytes']]
        }
        self._check_descriptions(exp_descriptions, blocks)

        exp_registers = {
            30000: [['A 0']],
            30010: [['A 0']]
        }
        self._check_registers(exp_registers, blocks)

        exp_end_comments = {
            30000: [['The end']],
            30010: [['The end']]
        }
        self._check_end_comments(exp_end_comments, blocks)

    def test_terminate_multiline_comments(self):
        ctl = """
            c 30000
            M 30000 No length specified, should end at 30002
            c 30002
            M 30002 No length specified, should end at 30003
            N 30003 This comment implicitly terminates the M directive above
            c 30004
            M 30004,5 Excessive length specified, should end at 30006
            c 30006
            M 30006,2 Excessive length specified, should end at 30007
            N 30007 This comment implicitly terminates the M directive above
            c 30008
        """
        blocks = self._get_ctl_parser(ctl).get_blocks()
        m_comment_end_map = {s.start: s.multiline_comment[0] for b in blocks for s in b.blocks if s.multiline_comment}
        exp_end_map = {
            30000: 30002,
            30002: 30003,
            30004: 30006,
            30006: 30007
        }
        self.assertEqual(exp_end_map, m_comment_end_map)

    def test_dot_directive_with_entry_titles(self):
        ctl = """
            b 30000 A title split
            . over two lines
            c 30100 A title
            . split over
            . three lines
            g 30200 One line, never wrapped
            .
            i 30300 One
            . Two
            s 30400 One
            . Two
            . Three
            t 30500 Another one-liner, never wrapped
            .
            u 30600 Not
            . used
            w 30700 Some
            . words
            ; Test a blank title with a blank continuation line
            b 30800
            .
            c 30900
            . Line 1 here
            g 31000
            . Trailing blank line
            .
            i 31100
            .
            . Leading blank line
            s 31200
            . Title
            .
            . Description.
            .
            . A The accumulator
            .
            . Start comment.
            t 31300
            . This title has
            .   an indent on the second line
        """
        exp_titles = {
            30000: ['A title split', 'over two lines'],
            30100: ['A title', 'split over', 'three lines'],
            30200: ['One line, never wrapped', ''],
            30300: ['One', 'Two'],
            30400: ['One', 'Two', 'Three'],
            30500: ['Another one-liner, never wrapped', ''],
            30600: ['Not', 'used'],
            30700: ['Some', 'words'],
            30800: ['', ''],
            30900: ['', 'Line 1 here'],
            31000: ['', 'Trailing blank line', ''],
            31100: ['', '', 'Leading blank line'],
            31200: ['', 'Title', '', 'Description.', '', 'A The accumulator', '', 'Start comment.'],
            31300: ['', 'This title has', '  an indent on the second line']
        }

        blocks = self._get_ctl_parser(ctl).get_blocks()
        self._check_titles(exp_titles, blocks)

    def test_dot_directive_with_instruction_comments(self):
        ctl = """
            b 30000
            B 30000,1 Single instruction,
            . two comment lines
            C 30001,1 Single instruction, one comment line, never wrapped
            .
            S 30002,2,1 Two instructions,
            . two comment lines
            T 30004,2,1 Two instructions,
            . three comment
            . lines
            W 30006,2,2 Two instructions, one comment line, never wrapped
            .
            M 30010,2 Two instructions of different types,
            . two comment lines
            B 30010,1
            S 30011,1
            ; Test a blank comment with a blank continuation line
            B 30012,1
            .
            C 30013,1
            . Line 1 here
            S 30014,1
            . Trailing blank line
            .
            T 30015,1
            .
            . Leading blank line
            W 30016,2
            . Line 1
            .
            . Line 3 (with a blank line 2)
            B 30018,1
            . This comment has
            .      an indent on the second line
        """
        blocks = self._get_ctl_parser(ctl).get_blocks()

        exp_instruction_comments = {
            30000: [(0, 'Single instruction,'), (0, 'two comment lines')],
            30001: [(0, 'Single instruction, one comment line, never wrapped'), (0, '')],
            30002: [(0, 'Two instructions,'), (0, 'two comment lines')],
            30004: [(0, 'Two instructions,'), (0, 'three comment'), (0, 'lines')],
            30006: [(0, 'Two instructions, one comment line, never wrapped'), (0, '')],
            30008: (),
            30010: [(0, '')],
            30011: [(0, '')],
            30012: [(0, ''), (0, '')],
            30013: [(0, ''), (0, 'Line 1 here')],
            30014: [(0, ''), (0, 'Trailing blank line'), (0, '')],
            30015: [(0, ''), (0, ''), (0, 'Leading blank line')],
            30016: [(0, ''), (0, 'Line 1'), (0, ''), (0, 'Line 3 (with a blank line 2)')],
            30018: [(0, ''), (0, 'This comment has'), (0, '     an indent on the second line')],
            30019: ()
        }
        self._check_instruction_comments(exp_instruction_comments, blocks)

        exp_multiline_comments = {
            30000: None,
            30001: None,
            30002: None,
            30004: None,
            30006: None,
            30008: None,
            30010: (30012, [(0, 'Two instructions of different types,'), (0, 'two comment lines')]),
            30011: None,
            30012: None,
            30013: None,
            30014: None,
            30015: None,
            30016: None,
            30018: None,
            30019: None
        }
        self._check_multiline_comments(exp_multiline_comments, blocks)

    def test_dot_directive_with_entry_descriptions(self):
        ctl = """
            b 40000
            D 40000 This description
            . spans two lines.
            b 40001 Two 'D' directives
            D 40001 This description spans only one line even though it would normally be wrapped over two lines.
            .
            D 40001
            . This description
            . spans three
            . lines.
            b 40002
            D 40002
            . Another long description that spans only one line but would normally be wrapped over two lines.
            b 40003 Test a blank description with a blank continuation line
            D 40003
            .
            b 40004
            D 40004
            . Trailing blank line.
            .
            b 40005
            D 40005
            .
            . Leading blank line.
            b 40006
            D 40006
            . Paragraph 1.
            .
            . Paragraph 2.
            b 40007
            D 40007
            . This description has
            .      an indented second line.
        """
        exp_descriptions = {
            40000: [['This description', 'spans two lines.']],
            40001: [
                ['This description spans only one line even though it would normally be wrapped over two lines.', ''],
                ['', 'This description', 'spans three', 'lines.']
            ],
            40002: [['', 'Another long description that spans only one line but would normally be wrapped over two lines.']],
            40003: [['', '']],
            40004: [['', 'Trailing blank line.', '']],
            40005: [['', '', 'Leading blank line.']],
            40006: [['', 'Paragraph 1.', '', 'Paragraph 2.']],
            40007: [['', 'This description has', '     an indented second line.']]
        }

        blocks = self._get_ctl_parser(ctl).get_blocks()
        self._check_descriptions(exp_descriptions, blocks)

    def test_dot_directive_with_block_start_and_mid_block_comments(self):
        ctl = """
            b 50000
            N 50000 This comment
            . spans two lines.
            N 50000 This comment spans only one line even though it would normally be wrapped over two lines.
            .
            N 50001
            . This comment
            . spans three
            . lines.
            N 50002
            . Another long comment that spans only one line but would normally be wrapped over two lines.
            ; Test a blank comment with a blank continuation line
            N 50003
            .
            N 50004
            . Trailing blank line.
            .
            N 50005
            .
            . Leading blank line.
            N 50006
            . Paragraph 1.
            .
            . Paragraph 2.
            N 50007
            . This comment has
            .      an indented second line.
        """
        exp_mid_block_comments = {
            50000: [
                ['This comment', 'spans two lines.'],
                ['This comment spans only one line even though it would normally be wrapped over two lines.', '']
            ],
            50001: [['', 'This comment', 'spans three', 'lines.']],
            50002: [['', 'Another long comment that spans only one line but would normally be wrapped over two lines.']],
            50003: [['', '']],
            50004: [['', 'Trailing blank line.', '']],
            50005: [['', '', 'Leading blank line.']],
            50006: [['', 'Paragraph 1.', '', 'Paragraph 2.']],
            50007: [['', 'This comment has', '     an indented second line.']]
        }

        blocks = self._get_ctl_parser(ctl).get_blocks()
        self._check_mid_block_comments(exp_mid_block_comments, blocks)

    def test_dot_directive_with_block_end_comments(self):
        ctl = """
            b 50000
            E 50000 This comment
            . spans two lines.
            E 50000 This comment spans only one line even though it would normally be wrapped over two lines.
            .
            b 50001
            E 50001
            . This comment
            . spans three
            . lines.
            b 50002
            E 50002
            . Another long comment that spans only one line but would normally be wrapped over two lines.
            b 50003 Test a blank comment with a blank continuation line
            E 50003
            .
            b 50004
            E 50004
            . Trailing blank line.
            .
            b 50005
            E 50005
            .
            . Leading blank line.
            b 50006
            E 50006
            . Paragraph 1.
            .
            . Paragraph 2.
            b 50007
            E 50007
            . This comment has
            .      an indented second line.
        """
        exp_end_comments = {
            50000: [
                ['This comment', 'spans two lines.'],
                ['This comment spans only one line even though it would normally be wrapped over two lines.', '']
            ],
            50001: [['', 'This comment', 'spans three', 'lines.']],
            50002: [['', 'Another long comment that spans only one line but would normally be wrapped over two lines.']],
            50003: [['', '']],
            50004: [['', 'Trailing blank line.', '']],
            50005: [['', '', 'Leading blank line.']],
            50006: [['', 'Paragraph 1.', '', 'Paragraph 2.']],
            50007: [['', 'This comment has', '     an indented second line.']]
        }

        blocks = self._get_ctl_parser(ctl).get_blocks()
        self._check_end_comments(exp_end_comments, blocks)

    def test_dot_directive_with_registers(self):
        snapshot = [201]
        ctl = """
            c 60000
            R 60000 BC This description
            . spans two lines
            R 60000 DE This description spans only one line even though it would normally be wrapped over two lines
            .
            c 60001
            R 60001
            . HL This description
            . spans three
            . lines
            c 60002
            R 60002
            . A Another long description that spans only one line but would normally be wrapped over two lines
            c 60003 Test a blank register description with a blank continuation line
            R 60003
            .
            c 60004
            R 60004
            . IX Trailing blank line
            .
            c 60005
            R 60005
            .
            . IY Leading blank line
            c 60006
            R 60006
            . SP
            .
            . Stack pointer
            c 60007
            R 60007
            .   A Input
            . O:B Output
        """
        exp_registers = {
            60000: [
                ['BC This description', 'spans two lines'],
                ['DE This description spans only one line even though it would normally be wrapped over two lines', '']
            ],
            60001: [['', 'HL This description', 'spans three', 'lines']],
            60002: [['', 'A Another long description that spans only one line but would normally be wrapped over two lines']],
            60003: [['', '']],
            60004: [['', 'IX Trailing blank line', '']],
            60005: [['', '', 'IY Leading blank line']],
            60006: [['', 'SP', '', 'Stack pointer']],
            60007: [['', '  A Input', 'O:B Output']]
        }

        blocks = self._get_ctl_parser(ctl).get_blocks()
        self._check_registers(exp_registers, blocks)

    def test_colon_directive(self):
        snapshot = [0] * 23
        ctl = """
            b 30000
            B 30000,2,1
            . The first two comment lines
            : belong to the first DEFB.
            . And these two comment lines
            : belong to the second DEFB.
        """
        blocks = self._get_ctl_parser(ctl).get_blocks()

        exp_instruction_comments = {
            30000: [
                (0, ''),
                (0, 'The first two comment lines'),
                (1, 'belong to the first DEFB.'),
                (0, 'And these two comment lines'),
                (1, 'belong to the second DEFB.')
            ],
            30002: ()
        }
        self._check_instruction_comments(exp_instruction_comments, blocks)
