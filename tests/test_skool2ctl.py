from textwrap import dedent
from unittest.mock import patch

from skoolkittest import SkoolKitTestCase
from skoolkit import skool2ctl, VERSION
from skoolkit.config import COMMANDS

ELEMENTS = 'abtdrmscn'

def mock_config(name):
    return {k: v[0] for k, v in COMMANDS[name].items()}

class MockCtlWriter:
    def __init__(self, skoolfile, elements, write_hex, preserve_base, min_address, max_address, keep_lines):
        global mock_ctl_writer
        self.skoolfile = skoolfile
        self.elements = elements
        self.write_hex = write_hex
        self.preserve_base = preserve_base
        self.min_address = min_address
        self.max_address = max_address
        self.keep_lines = keep_lines
        self.write_called = False
        mock_ctl_writer = self

    def write(self):
        self.write_called = True

class Skool2CtlTest(SkoolKitTestCase):
    def _check_ctl_writer(self, skoolfile, elements=ELEMENTS, write_hex=0, preserve_base=0,
                          min_address=0, max_address=65536, keep_lines=0):
        self.assertEqual(mock_ctl_writer.skoolfile, skoolfile)
        self.assertEqual(mock_ctl_writer.elements, elements)
        self.assertEqual(mock_ctl_writer.write_hex, write_hex)
        self.assertEqual(mock_ctl_writer.preserve_base, preserve_base)
        self.assertEqual(mock_ctl_writer.min_address, min_address)
        self.assertEqual(mock_ctl_writer.max_address, max_address)
        self.assertEqual(mock_ctl_writer.keep_lines, keep_lines)
        self.assertTrue(mock_ctl_writer.write_called)

    def test_no_arguments(self):
        output, error = self.run_skool2ctl(catch_exit=2)
        self.assertEqual(output, '')
        self.assertTrue(error.startswith('usage: skool2ctl.py'))

    def test_invalid_arguments(self):
        for args in ('-h', '-x test.skool'):
            output, error = self.run_skool2ctl(args, catch_exit=2)
            self.assertEqual(output, '')
            self.assertTrue(error.startswith('usage: skool2ctl.py'))

    @patch.object(skool2ctl, 'CtlWriter', MockCtlWriter)
    @patch.object(skool2ctl, 'get_config', mock_config)
    def test_default_option_values(self):
        skoolfile = 'test.skool'
        skool2ctl.main((skoolfile,))
        self._check_ctl_writer(skoolfile)

    @patch.object(skool2ctl, 'CtlWriter', MockCtlWriter)
    def test_config_read_from_file(self):
        ini = """
            [skool2ctl]
            Hex=1
            KeepLines=1
        """
        self.write_text_file(dedent(ini).strip(), 'skoolkit.ini')
        skoolfile = 'test.skool'
        skool2ctl.main((skoolfile,))
        self._check_ctl_writer(skoolfile, write_hex=1, keep_lines=1)

    @patch.object(skool2ctl, 'CtlWriter', MockCtlWriter)
    def test_invalid_option_values_read_from_file(self):
        ini = """
            [skool2ctl]
            Hex=?
            KeepLines=x
        """
        self.write_text_file(dedent(ini).strip(), 'skoolkit.ini')
        skoolfile = 'test.skool'
        skool2ctl.main((skoolfile,))
        self._check_ctl_writer(skoolfile)

    def test_option_V(self):
        for option in ('-V', '--version'):
            output, error = self.run_skool2ctl(option, catch_exit=0)
            self.assertEqual(output, 'SkoolKit {}\n'.format(VERSION))

    @patch.object(skool2ctl, 'CtlWriter', MockCtlWriter)
    def test_option_w(self):
        skoolfile = 'test.skool'
        for w in ('a', 'b', 't', 'd', 'r', 'm', 's', 'c', 'btd', ELEMENTS):
            for option in ('-w', '--write'):
                skool2ctl.main((option, w, skoolfile))
                self._check_ctl_writer(skoolfile, elements=w)

    @patch.object(skool2ctl, 'CtlWriter', MockCtlWriter)
    def test_option_k(self):
        skoolfile = 'test.skool'
        for option in ('-k', '--keep-lines'):
            skool2ctl.main((option, skoolfile))
            self._check_ctl_writer(skoolfile, keep_lines=1)

    @patch.object(skool2ctl, 'CtlWriter', MockCtlWriter)
    def test_option_h(self):
        skoolfile = 'test.skool'
        for option in ('-h', '--hex'):
            skool2ctl.main((option, skoolfile))
            self._check_ctl_writer(skoolfile, write_hex=2)

    @patch.object(skool2ctl, 'CtlWriter', MockCtlWriter)
    def test_option_l(self):
        skoolfile = 'test.skool'
        for option in ('-l', '--hex-lower'):
            skool2ctl.main((option, skoolfile))
            self._check_ctl_writer(skoolfile, write_hex=1)

    @patch.object(skool2ctl, 'CtlWriter', MockCtlWriter)
    def test_option_b(self):
        skoolfile = 'test.skool'
        for option in ('-b', '--preserve-base'):
            skool2ctl.main((option, skoolfile))
            self._check_ctl_writer(skoolfile, preserve_base=1)

    @patch.object(skool2ctl, 'CtlWriter', MockCtlWriter)
    def test_option_S(self):
        skoolfile = 'test.skool'
        for option, start in (('-S', 30000), ('--start', 40000)):
            skool2ctl.main((option, str(start), skoolfile))
            self._check_ctl_writer(skoolfile, min_address=start)

    @patch.object(skool2ctl, 'CtlWriter', MockCtlWriter)
    def test_option_S_with_hex_address(self):
        skoolfile = 'test.skool'
        for option, start in (('-S', '0x70fa'), ('--start', '0xBCDE')):
            skool2ctl.main((option, str(start), skoolfile))
            self._check_ctl_writer(skoolfile, min_address=int(start[2:], 16))

    @patch.object(skool2ctl, 'CtlWriter', MockCtlWriter)
    def test_option_E(self):
        skoolfile = 'test.skool'
        for option, end in (('-E', 40000), ('--end', 50000)):
            skool2ctl.main((option, str(end), skoolfile))
            self._check_ctl_writer(skoolfile, max_address=end)

    @patch.object(skool2ctl, 'CtlWriter', MockCtlWriter)
    def test_option_E_with_hex_address(self):
        skoolfile = 'test.skool'
        for option, end in (('-E', '0x6ff0'), ('--end', '0x9ABC')):
            skool2ctl.main((option, str(end), skoolfile))
            self._check_ctl_writer(skoolfile, max_address=int(end[2:], 16))

    @patch.object(skool2ctl, 'CtlWriter', MockCtlWriter)
    def test_options_S_and_E(self):
        skoolfile = 'test.skool'
        start = 24576
        end = 32768
        skool2ctl.main(('-S', str(start), '-E', str(end), skoolfile))
        self._check_ctl_writer(skoolfile, min_address=start, max_address=end)

    @patch.object(skool2ctl, 'CtlWriter', MockCtlWriter)
    @patch.object(skool2ctl, 'get_config', mock_config)
    def test_option_I(self):
        self.run_skool2ctl('-I Hex=1 test.skool')
        self._check_ctl_writer('test.skool', write_hex=1)

    @patch.object(skool2ctl, 'CtlWriter', MockCtlWriter)
    @patch.object(skool2ctl, 'get_config', mock_config)
    def test_option_I_overrides_other_options(self):
        self.run_skool2ctl('-h -I Hex=1 test.skool')
        self._check_ctl_writer('test.skool', write_hex=1)

    @patch.object(skool2ctl, 'CtlWriter', MockCtlWriter)
    def test_option_I_overrides_config_read_from_file(self):
        ini = """
            [skool2ctl]
            Hex=2
            KeepLines=1
        """
        self.write_text_file(dedent(ini).strip(), 'skoolkit.ini')
        self.run_skool2ctl('--ini Hex=1 -I KeepLines=0 test.skool')
        self._check_ctl_writer('test.skool', write_hex=1, keep_lines=0)

    @patch.object(skool2ctl, 'CtlWriter', MockCtlWriter)
    @patch.object(skool2ctl, 'get_config', mock_config)
    def test_option_I_multiple(self):
        self.run_skool2ctl('-I Hex=1 --ini PreserveBase=1 test.skool')
        self._check_ctl_writer('test.skool', write_hex=1, preserve_base=1)

    @patch.object(skool2ctl, 'CtlWriter', MockCtlWriter)
    @patch.object(skool2ctl, 'get_config', mock_config)
    def test_option_I_invalid_value(self):
        self.run_skool2ctl('-I Hex=x test.skool')
        self._check_ctl_writer('test.skool')

    @patch.object(skool2ctl, 'get_config', mock_config)
    def test_option_show_config(self):
        output, error = self.run_skool2ctl('--show-config', catch_exit=0)
        self.assertEqual(error, '')
        exp_output = """
            [skool2ctl]
            Hex=0
            KeepLines=0
            PreserveBase=0
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_option_show_config_read_from_file(self):
        ini = """
            [skool2ctl]
            Hex=1
            KeepLines=1
            PreserveBase=1
        """
        self.write_text_file(dedent(ini).strip(), 'skoolkit.ini')
        output, error = self.run_skool2ctl('--show-config', catch_exit=0)
        self.assertEqual(error, '')
        exp_output = """
            [skool2ctl]
            Hex=1
            KeepLines=1
            PreserveBase=1
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_run(self):
        skool = """
            ; Test skool file for skool2ctl testing
            c65535 RET
        """
        skoolfile = self.write_text_file(dedent(skool).strip(), suffix='.skool')
        output, error = self.run_skool2ctl(skoolfile)
        self.assertEqual(error, '')
        self.assertEqual(output, 'c 65535 Test skool file for skool2ctl testing\n')
