# -*- coding: utf-8 -*-
import unittest

from skoolkittest import SkoolKitTestCase
from skoolkit.refparser import RefParser

class RefParserTest(SkoolKitTestCase):
    def _get_parser(self, contents):
        reffile = self.write_text_file(contents, suffix='.ref')
        ref_parser = RefParser()
        ref_parser.parse(reffile)
        return ref_parser

    def test_has_section(self):
        ref_parser = self._get_parser('[Section]\nBlah')
        self.assertTrue(ref_parser.has_section('Section'))
        self.assertFalse(ref_parser.has_section('NonexistentSection'))

    def test_has_sections(self):
        ref = '\n'.join((
            '[Prefix:1]',
            'Foo',
            '[Prefix:2]',
            'Bar'
        ))
        ref_parser = self._get_parser(ref)
        self.assertTrue(ref_parser.has_sections('Prefix'))
        self.assertFalse(ref_parser.has_sections('NonexistentPrefix'))

    def test_get_dictionary(self):
        ref = '\n'.join((
            '[Section]',
            '1=Foo',
            'Blah=Bar'
        ))
        ref_parser = self._get_parser(ref)
        section_dict = ref_parser.get_dictionary('Section')
        self.assertIn(1, section_dict)
        self.assertEqual(section_dict[1], 'Foo')
        self.assertIn('Blah', section_dict)
        self.assertEqual(section_dict['Blah'], 'Bar')

    def test_get_dictionary_with_invalid_line(self):
        ref = '\n'.join((
            '[Section]',
            'Blah=Foo',
            'Bar',
            'Baz=Qux'
        ))
        ref_parser = self._get_parser(ref)
        section_dict = ref_parser.get_dictionary('Section')
        self.assertIn('Blah', section_dict)
        self.assertNotIn('Bar', section_dict)
        self.assertIn('Baz', section_dict)

    def test_get_dictionaries(self):
        ref = '\n'.join((
            '[Section:Foo]',
            'A=B=C',
            '[Section:Bar]',
            'baz=qux',
            '[Section]',
            'x=y'
        ))
        ref_parser = self._get_parser(ref)
        section_dicts = ref_parser.get_dictionaries('Section')
        self.assertEqual(len(section_dicts), 2)

        suffix1, dict1 = section_dicts[0]
        self.assertEqual(suffix1, 'Foo')
        self.assertIn('A', dict1)
        self.assertEqual(dict1['A'], 'B=C')

        suffix2, dict2 = section_dicts[1]
        self.assertEqual(suffix2, 'Bar')
        self.assertIn('baz', dict2)
        self.assertEqual(dict2['baz'], 'qux')

    def test_get_section(self):
        ref = '\n'.join((
            '[Apple]',
            'Line 1',
            'Line 2'
        ))
        ref_parser = self._get_parser(ref)
        section = ref_parser.get_section('Apple')
        self.assertEqual(section, 'Line 1\nLine 2')

    def test_get_section_as_lines(self):
        ref = '\n'.join((
            '[Apple]',
            'Line 1',
            'Line 2'
        ))
        ref_parser = self._get_parser(ref)
        section = ref_parser.get_section('Apple', lines=True)
        self.assertEqual(section, ['Line 1', 'Line 2'])

    def test_get_section_as_paragraphs(self):
        ref = '\n'.join((
            '[Apple]',
            'P1, L1',
            'P1, L2',
            '',
            'P2, L1'
        ))
        ref_parser = self._get_parser(ref)
        paragraphs = ref_parser.get_section('Apple', paragraphs=True)
        self.assertEqual(len(paragraphs), 2)
        self.assertEqual(paragraphs[0], 'P1, L1\nP1, L2')
        self.assertEqual(paragraphs[1], 'P2, L1')

    def test_get_section_as_paragraphs_and_lines(self):
        ref = '\n'.join((
            '[Apple]',
            'P1, L1',
            'P1, L2',
            '',
            'P2, L1'
        ))
        ref_parser = self._get_parser(ref)
        paragraphs = ref_parser.get_section('Apple', paragraphs=True, lines=True)
        self.assertEqual(len(paragraphs), 2)
        self.assertEqual(paragraphs[0], ['P1, L1', 'P1, L2'])
        self.assertEqual(paragraphs[1], ['P2, L1'])

    def test_get_section_that_does_not_exist(self):
        ref_parser = self._get_parser('[Foo]\nBar')
        section = ref_parser.get_section('Bar')
        self.assertEqual(section, '')

    def test_get_sections(self):
        ref = '\n'.join((
            '[Prefix:1]',
            'Foo',
            '[Prefix:2]',
            'Bar'
        ))
        ref_parser = self._get_parser(ref)
        sections = ref_parser.get_sections('Prefix')
        self.assertEqual(len(sections), 2)
        self.assertEqual(len(sections[0]), 2)
        self.assertEqual(len(sections[1]), 2)

        suffix1, section1 = sections[0]
        self.assertEqual(suffix1, '1')
        self.assertEqual(section1, 'Foo')

        suffix2, section2 = sections[1]
        self.assertEqual(suffix2, '2')
        self.assertEqual(section2, 'Bar')

    def test_get_sections_with_two_colons(self):
        ref = '\n'.join((
            '[Prefix:1:A]',
            'Foo',
            '[Prefix:2:B]',
            'Bar'
        ))
        ref_parser = self._get_parser(ref)
        sections = ref_parser.get_sections('Prefix')
        self.assertEqual(len(sections), 2)
        self.assertEqual(len(sections[0]), 3)
        self.assertEqual(len(sections[1]), 3)

        infix1, suffix1, section1 = sections[0]
        self.assertEqual(infix1, '1')
        self.assertEqual(suffix1, 'A')
        self.assertEqual(section1, 'Foo')

        infix2, suffix2, section2 = sections[1]
        self.assertEqual(infix2, '2')
        self.assertEqual(suffix2, 'B')
        self.assertEqual(section2, 'Bar')

    def test_add_line_to_existing_section(self):
        ref_parser = self._get_parser('[Blah]\nA=1')
        ref_parser.add_line('Blah', 'B=2')
        blah = ref_parser.get_dictionary('Blah')
        self.assertIn('B', blah)
        self.assertEqual(blah['B'], '2')

    def test_add_line_to_nonexistent_section(self):
        ref_parser = self._get_parser('')
        ref_parser.add_line('Foo', 'Q=0')
        foo = ref_parser.get_dictionary('Foo')
        self.assertIn('Q', foo)
        self.assertEqual(foo['Q'], '0')

    def test_section_content_is_trimmed(self):
        ref = '\n'.join((
            '[Xyzzy]',
            'Hi',
            '',
            ''
        ))
        ref_parser = self._get_parser(ref)
        section = ref_parser.get_section('Xyzzy')
        self.assertEqual(section, 'Hi')

    def test_comment(self):
        ref = '\n'.join((
            '[Foo]',
            '; This is a comment',
            'Bar',
            '; This is another comment'
        ))
        ref_parser = self._get_parser(ref)
        section = ref_parser.get_section('Foo')
        self.assertEqual(section, 'Bar')

    def test_escaped_semicolon(self):
        ref = '[Baz]\n;; This is not a comment'
        ref_parser = self._get_parser(ref)
        section = ref_parser.get_section('Baz')
        self.assertEqual(section, '; This is not a comment')

    def test_unclosed_section_header(self):
        ref = '\n'.join((
            '[Foo',
            'Bar',
            '[Baz]',
            'Qux'
        ))
        ref_parser = self._get_parser(ref)
        self.assertEqual(ref_parser.get_section('Foo'), '')
        self.assertEqual(ref_parser.get_section('Baz'), 'Qux')

    def test_escaped_square_brackets(self):
        ref = '\n'.join((
            '[Foo]',
            'Bar',
            '[[Baz]',
            'Qux',
            '[[Xyzzy'
        ))
        exp_contents = '\n'.join((
            'Bar',
            '[Baz]',
            'Qux',
            '[Xyzzy'
        ))
        ref_parser = self._get_parser(ref)
        section = ref_parser.get_section('Foo')
        self.assertEqual(exp_contents, section)

if __name__ == '__main__':
    unittest.main()
