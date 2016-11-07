# -*- coding: utf-8 -*-
import unittest
try:
    from mock import patch
except ImportError:
    from unittest.mock import patch

from skoolkittest import SkoolKitTestCase
from skoolkit import SkoolKitError, sna2img, VERSION
from skoolkit.skoolhtml import Udg

class MockImageWriter:
    def __init__(self, options):
        global image_writer
        image_writer = self
        self.options = options

    def write_image(self, frames, img_file, img_format):
        self.frames = frames
        self.img_format = img_format

class Sna2ImgTest(SkoolKitTestCase):
    def _test_sna2img(self, mock_open, options, scr, udgs, scale=1, outfile=None, iw_options=None):
        scrfile = self.write_bin_file(scr, suffix='.scr')
        args = '{} {}'.format(options, scrfile)
        if outfile:
            exp_outfile = outfile
            img_format = outfile[:-3]
            args += ' {}'.format(outfile)
        else:
            img_format = 'png'
            exp_outfile = scrfile[:-3] + img_format
        output, error = self.run_sna2img(args)
        self.assertEqual([], output)
        self.assertEqual(error, '')
        self.assertEqual(iw_options or {}, image_writer.options)
        self.assertEqual(image_writer.img_format, img_format)
        mock_open.assert_called_with(exp_outfile, 'wb')
        self.assertEqual(len(image_writer.frames), 1)
        frame = image_writer.frames[0]
        self.assertEqual(frame.scale, scale)
        self.assertEqual(len(udgs), len(frame.udgs))
        for i, row in enumerate(udgs):
            self.assertEqual(udgs[i], frame.udgs[i], "Row {}/{} differs from expected value".format(i + 1, len(udgs)))

    def _test_bad_spec(self, option, exp_error):
        scrfile = self.write_bin_file(suffix='.scr')
        with self.assertRaises(SkoolKitError) as cm:
            self.run_sna2img('{} {}'.format(option, scrfile))
        self.assertEqual(cm.exception.args[0], exp_error)

    def test_no_arguments(self):
        output, error = self.run_sna2img(catch_exit=2)
        self.assertEqual(len(output), 0)
        self.assertTrue(error.startswith('usage: sna2img.py'))

    def test_invalid_option(self):
        output, error = self.run_sna2img('-x test.z80', catch_exit=2)
        self.assertEqual(len(output), 0)
        self.assertTrue(error.startswith('usage: sna2img.py'))

    def test_unrecognised_snapshot_type(self):
        with self.assertRaisesRegexp(SkoolKitError, 'Unrecognised input file type$'):
            self.run_sna2img('unknown.snap')

    def test_nonexistent_input_file(self):
        infile = 'non-existent.z80'
        with self.assertRaises(SkoolKitError) as cm:
            self.run_sna2img(infile)
        self.assertEqual(cm.exception.args[0], '{}: file not found'.format(infile))

    @patch.object(sna2img, 'ImageWriter', MockImageWriter)
    @patch.object(sna2img, 'open')
    def test_option_f_1(self, mock_open):
        scr = [170] * 6144 + [56] * 768
        exp_udgs = [[Udg(56, [85] * 8)] * 32] * 24
        for option in ('-f', '--flip'):
            self._test_sna2img(mock_open, '{} 1'.format(option), scr, exp_udgs)

    @patch.object(sna2img, 'ImageWriter', MockImageWriter)
    @patch.object(sna2img, 'open')
    def test_option_f_2(self, mock_open):
        scr = ([255] * 256 + [0] * 256) * 12 + [1] * 768
        exp_udgs = [[Udg(1, [0, 255] * 4)] * 32] * 24
        self._test_sna2img(mock_open, '-f 2', scr, exp_udgs)

    @patch.object(sna2img, 'ImageWriter', MockImageWriter)
    @patch.object(sna2img, 'open')
    def test_option_f_3(self, mock_open):
        scr = ([170] * 256 + [0] * 256) * 12 + [2] * 768
        exp_udgs = [[Udg(2, [0, 85] * 4)] * 32] * 24
        self._test_sna2img(mock_open, '--flip 3', scr, exp_udgs)

    def test_option_f_invalid_value(self):
        scrfile = self.write_bin_file(suffix='.scr')
        output, error = self.run_sna2img('-f ? {}'.format(scrfile), catch_exit=2)
        self.assertEqual(len(output), 0)
        self.assertTrue(error.startswith('usage: sna2img.py'))
        self.assertTrue(error.endswith("error: argument -f/--flip: invalid int value: '?'\n"))

    @patch.object(sna2img, 'ImageWriter', MockImageWriter)
    @patch.object(sna2img, 'open')
    def test_option_i(self, mock_open):
        scr = [85] * 6144 + [135, 7] * 384
        udg1 = Udg(7, [170] * 8) # Inverted
        udg2 = Udg(7, [85] * 8)  # Unchanged
        exp_udgs = [[udg1, udg2] * 16] * 24
        for option in ('-i', '--invert'):
            self._test_sna2img(mock_open, option, scr, exp_udgs)

    @patch.object(sna2img, 'ImageWriter', MockImageWriter)
    @patch.object(sna2img, 'open')
    def test_option_n(self, mock_open):
        scr = [0] * 6144 + [248] * 768
        exp_udgs = [[Udg(248, [0, 0, 0, 0, 0, 0, 0, 0])] * 32] * 24
        exp_iw_options = {'GIFEnableAnimation': 0, 'PNGEnableAnimation': 0}
        for option in ('-n', '--no-animation'):
            self._test_sna2img(mock_open, option, scr, exp_udgs, iw_options=exp_iw_options)

    @patch.object(sna2img, 'ImageWriter', MockImageWriter)
    @patch.object(sna2img, 'open')
    def test_option_p(self, mock_open):
        scr = [0] * 6912
        exp_udgs = [[Udg(0, [0] * 8)] * 32 for i in range(24)]
        exp_udgs[0][0] = Udg(0, [255, 0, 0, 0, 0, 0, 0, 0])
        for option in ('-p', '--poke'):
            self._test_sna2img(mock_open, '{} 16384,255'.format(option), scr, exp_udgs)

    @patch.object(sna2img, 'ImageWriter', MockImageWriter)
    @patch.object(sna2img, 'open')
    def test_option_p_address_range(self, mock_open):
        scr = [0] * 6912
        exp_udgs = [[Udg(0, [0] * 8)] * 32 for i in range(24)]
        exp_udgs[0][0].data[0] = 255
        self._test_sna2img(mock_open, '-p 16384-16415,255', scr, exp_udgs)

    @patch.object(sna2img, 'ImageWriter', MockImageWriter)
    @patch.object(sna2img, 'open')
    def test_option_p_address_range_with_step(self, mock_open):
        scr = [0] * 6912
        exp_udgs = [[Udg(0, [0] * 8)] * 32 for i in range(24)]
        exp_udgs[0][0] = Udg(0, [15] * 8)
        self._test_sna2img(mock_open, '-p 16384-18176-256,15', scr, exp_udgs)

    @patch.object(sna2img, 'ImageWriter', MockImageWriter)
    @patch.object(sna2img, 'open')
    def test_option_p_hexadecimal_values(self, mock_open):
        scr = [0] * 6912
        exp_udgs = [[Udg(0, [0] * 8)] * 32 for i in range(24)]
        exp_udgs[0][0] = Udg(0, [15] * 8)
        self._test_sna2img(mock_open, '-p $4000-$4700-$100,$0f', scr, exp_udgs)

    @patch.object(sna2img, 'ImageWriter', MockImageWriter)
    @patch.object(sna2img, 'open')
    def test_option_p_with_add_operation(self, mock_open):
        scr = [0] * 6912
        exp_udgs = [[Udg(0, [0] * 8)] * 32 for i in range(24)]
        exp_udgs[0][0].data[0] = 5
        self._test_sna2img(mock_open, '-p 16384-16415,+5', scr, exp_udgs)

    @patch.object(sna2img, 'ImageWriter', MockImageWriter)
    @patch.object(sna2img, 'open')
    def test_option_p_with_xor_operation(self, mock_open):
        scr = [255] * 6912
        exp_udgs = [[Udg(255, [255] * 8)] * 32 for i in range(24)]
        exp_udgs[0][0].data[0] = 240
        self._test_sna2img(mock_open, '-p 16384-16415,^15', scr, exp_udgs)

    @patch.object(sna2img, 'ImageWriter', MockImageWriter)
    @patch.object(sna2img, 'open')
    def test_option_p_multiple(self, mock_open):
        scr = [0] * 6912
        exp_udgs = [[Udg(0, [0] * 8)] * 32 for i in range(24)]
        exp_udgs[0][0] = Udg(0, [255, 0, 0, 0, 0, 0, 0, 0])
        exp_udgs[0][1] = Udg(0, [170, 0, 0, 0, 0, 0, 0, 0])
        self._test_sna2img(mock_open, '-p 16384,255 --poke 16385,170', scr, exp_udgs)

    def test_option_p_invalid_values(self):
        self._test_bad_spec('-p 1', 'Value missing in poke spec: 1')
        self._test_bad_spec('-p q', 'Value missing in poke spec: q')
        self._test_bad_spec('-p 1,x', 'Invalid value in poke spec: 1,x')
        self._test_bad_spec('-p x,1', 'Invalid address range in poke spec: x,1')
        self._test_bad_spec('-p 1-y,1', 'Invalid address range in poke spec: 1-y,1')
        self._test_bad_spec('-p 1-3-z,1', 'Invalid address range in poke spec: 1-3-z,1')

    @patch.object(sna2img, 'ImageWriter', MockImageWriter)
    @patch.object(sna2img, 'open')
    def test_option_s(self, mock_open):
        scr = [0] * 6144 + [1] * 768
        exp_udgs = [[Udg(1, [0] * 8)] * 32] * 24
        for option, scale in (('-s ', 2), ('--scale', 3)):
            args = '{} {}'.format(option, scale)
            self._test_sna2img(mock_open, args, scr, exp_udgs, scale)

    def test_option_V(self):
        for option in ('-V', '--version'):
            output, error = self.run_sna2img(option, err_lines=True, catch_exit=0)
            self.assertEqual(['SkoolKit {}'.format(VERSION)], output + error)

if __name__ == '__main__':
    unittest.main()
