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
        self.assertTrue(1 in section_dict)
        self.assertEqual(section_dict[1], 'Foo')
        self.assertTrue('Blah' in section_dict)
        self.assertEqual(section_dict['Blah'], 'Bar')

if __name__ == '__main__':
    unittest.main()
