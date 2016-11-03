# -*- coding: utf-8 -*-
import unittest
try:
    from mock import patch
except ImportError:
    from unittest.mock import patch

from skoolkittest import SkoolKitTestCase
from skoolkit import SkoolKitError, scr2img, VERSION
from skoolkit.skoolhtml import Udg

class MockImageWriter:
    def __init__(self, options):
        global image_writer
        image_writer = self
        self.options = options

    def write_image(self, frames, img_file, img_format):
        self.frames = frames
        self.img_format = img_format

class Scr2ImgTest(SkoolKitTestCase):
    def _test_scr2img(self, mock_open, options, scr, udgs, scale=1, outfile=None, iw_options=None):
        scrfile = self.write_bin_file(scr, suffix='.scr')
        args = '{} {}'.format(options, scrfile)
        if outfile:
            exp_outfile = outfile
            img_format = outfile[:-3]
            args += ' {}'.format(outfile)
        else:
            img_format = 'png'
            exp_outfile = scrfile[:-3] + img_format
        output, error = self.run_scr2img(args)
        self.assertEqual([], output)
        self.assertEqual(error, '')
        self.assertEqual(iw_options or {}, image_writer.options)
        self.assertEqual(image_writer.img_format, img_format)
        mock_open.assert_called_with(exp_outfile, 'wb')
        self.assertEqual(len(image_writer.frames), 1)
        frame = image_writer.frames[0]
        self.assertEqual(frame.scale, scale)
        self.assertEqual(udgs, frame.udgs)

    def test_no_arguments(self):
        output, error = self.run_scr2img(catch_exit=2)
        self.assertEqual(len(output), 0)
        self.assertTrue(error.startswith('usage: scr2img.py'))

    def test_invalid_option(self):
        output, error = self.run_scr2img('-x test.z80', catch_exit=2)
        self.assertEqual(len(output), 0)
        self.assertTrue(error.startswith('usage: scr2img.py'))

    def test_unrecognised_snapshot_type(self):
        with self.assertRaisesRegexp(SkoolKitError, 'Unrecognised input file type$'):
            self.run_scr2img('unknown.snap')

    def test_nonexistent_input_file(self):
        infile = 'non-existent.z80'
        with self.assertRaises(SkoolKitError) as cm:
            self.run_scr2img(infile)
        self.assertEqual(cm.exception.args[0], '{}: file not found'.format(infile))

    @patch.object(scr2img, 'ImageWriter', MockImageWriter)
    @patch.object(scr2img, 'open')
    def test_option_i(self, mock_open):
        scr = [85] * 6144 + [135, 7] * 384
        udg1 = Udg(7, [170] * 8) # Inverted
        udg2 = Udg(7, [85] * 8)  # Unchanged
        exp_udgs = [[udg1, udg2] * 16] * 24
        for option in ('-i', '--invert'):
            self._test_scr2img(mock_open, option, scr, exp_udgs)

    @patch.object(scr2img, 'ImageWriter', MockImageWriter)
    @patch.object(scr2img, 'open')
    def test_option_n(self, mock_open):
        scr = [0] * 6144 + [248] * 768
        exp_udgs = [[Udg(248, [0, 0, 0, 0, 0, 0, 0, 0])] * 32] * 24
        exp_iw_options = {'GIFEnableAnimation': 0, 'PNGEnableAnimation': 0}
        for option in ('-n', '--no-animation'):
            self._test_scr2img(mock_open, option, scr, exp_udgs, iw_options=exp_iw_options)

    def test_option_V(self):
        for option in ('-V', '--version'):
            output, error = self.run_scr2img(option, err_lines=True, catch_exit=0)
            self.assertEqual(['SkoolKit {}'.format(VERSION)], output + error)

if __name__ == '__main__':
    unittest.main()
