# -*- coding: utf-8 -*-
import unittest

from skoolkittest import SkoolKitTestCase
from skoolkit.refparser import RefParser

TEST_HAS_SECTION = """[Section]
Blah
"""

TEST_HAS_SECTIONS = """[Prefix:1]
Foo

[Prefix:2]
Bar
"""

TEST_DICTIONARY = """[Section]
1=Foo
Blah=Bar
"""

class SkoolParserTest(SkoolKitTestCase):
    def _get_parser(self, contents):
        reffile = self.write_text_file(contents, suffix='.ref')
        ref_parser = RefParser()
        ref_parser.parse(reffile)
        return ref_parser

    def test_has_section(self):
        ref_parser = self._get_parser(TEST_HAS_SECTION)
        self.assertTrue(ref_parser.has_section('Section'))
        self.assertFalse(ref_parser.has_section('NonexistentSection'))

    def test_has_sections(self):
        ref_parser = self._get_parser(TEST_HAS_SECTIONS)
        self.assertTrue(ref_parser.has_sections('Prefix'))
        self.assertFalse(ref_parser.has_sections('NonexistentPrefix'))

    def test_get_dictionary(self):
        ref_parser = self._get_parser(TEST_DICTIONARY)
        section_dict = ref_parser.get_dictionary('Section')
        self.assertTrue(1 in section_dict)
        self.assertEqual(section_dict[1], 'Foo')
        self.assertTrue('Blah' in section_dict)
        self.assertEqual(section_dict['Blah'], 'Bar')

if __name__ == '__main__':
    unittest.main()
