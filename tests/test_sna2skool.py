import os.path
from textwrap import dedent
from unittest.mock import patch, Mock

from skoolkittest import SkoolKitTestCase
from skoolkit import components, sna2skool, snapshot, SkoolKitError, VERSION
from skoolkit.config import COMMANDS

def mock_make_snapshot(fname, org, start, end, page):
    return [0] * 65536, 16384 if start is None else start, end

class MockCtlParser:
    def __init__(self, ctls=None):
        global mock_ctl_parser
        self.ctls = ctls
        mock_ctl_parser = self

    def parse_ctls(self, ctlfiles, min_address, max_address):
        self.ctlfiles = ctlfiles
        self.min_address = min_address
        self.max_address = max_address

class MockSkoolWriter:
    def __init__(self, snapshot, ctl_parser, options, config):
        global mock_skool_writer
        mock_skool_writer = self
        self.snapshot = snapshot
        self.ctl_parser = ctl_parser
        self.options = options
        self.config = config
        self.wrote_skool = False

    def write_skool(self, write_refs, text):
        self.write_refs = write_refs
        self.text = text
        self.wrote_skool = True

def mock_run(*args):
    global run_args
    run_args = args

def mock_config(name):
    return {k: v[0] for k, v in COMMANDS[name].items()}

class Sna2SkoolTest(SkoolKitTestCase):
    @patch.object(sna2skool, 'run', mock_run)
    @patch.object(sna2skool, 'get_config', mock_config)
    def test_default_option_values(self):
        sna = '{}/test.sna'.format(self.make_directory())
        sna2skool.main((sna,))
        snafile, options = run_args[:2]
        self.assertEqual(snafile, sna)
        self.assertEqual([], options.ctls)
        self.assertEqual(options.base, 10)
        self.assertEqual(options.case, 2)
        self.assertIsNone(options.start)
        self.assertEqual(options.end, 65536)
        self.assertIsNone(options.org)
        self.assertIsNone(options.page)
        self.assertEqual(options.line_width, 79)
        self.assertEqual(options.params, [])

    @patch.object(sna2skool, 'run', mock_run)
    def test_config_read_from_file(self):
        ini = """
            [sna2skool]
            Base=16
            Case=1
            DefbSize=12
            DefmSize=92
            LineWidth=119
            ListRefs=2
            Text=1
            Title-b=Data at {address}
            Title-c=Code at {address}
        """
        self.write_text_file(dedent(ini).strip(), 'skoolkit.ini')
        sna = '{}/test.sna'.format(self.make_directory())
        sna2skool.main((sna,))
        snafile, options, config = run_args
        self.assertEqual(snafile, sna)
        self.assertEqual([], options.ctls)
        self.assertEqual(options.base, 16)
        self.assertEqual(options.case, 1)
        self.assertIsNone(options.start)
        self.assertEqual(options.end, 65536)
        self.assertIsNone(options.org)
        self.assertIsNone(options.page)
        self.assertEqual(config.get('Text'), 1)
        self.assertEqual(config.get('ListRefs'), 2)
        self.assertEqual(config.get('DefbSize'), 12)
        self.assertEqual(options.line_width, 119)
        self.assertEqual(config.get('DefmSize'), 92)
        self.assertEqual(config.get('Title-b'), 'Data at {address}')
        self.assertEqual(config.get('Title-c'), 'Code at {address}')

    @patch.object(sna2skool, 'run', mock_run)
    def test_invalid_option_values_read_from_file(self):
        ini = """
            [sna2skool]
            Base=?
            Case=2
            DefbSize=x
        """
        self.write_text_file(dedent(ini).strip(), 'skoolkit.ini')
        sna2skool.main(('test.sna',))
        snafile, options, config = run_args
        self.assertEqual(snafile, 'test.sna')
        self.assertEqual(options.base, 10)
        self.assertEqual(config.get('Case'), 2)
        self.assertEqual(config.get('DefbSize'), 8)

    @patch.object(sna2skool, 'make_snapshot', mock_make_snapshot)
    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_writer_config_read_from_file(self):
        ini = """
            [sna2skool]
            Title-b=Data at {address}
            Title-c=Code at {address}
        """
        self.write_text_file(dedent(ini).strip(), 'skoolkit.ini')
        output, error = self.run_sna2skool('{}/test.sna'.format(self.make_directory()))
        self.assertEqual(error, '')
        config = mock_skool_writer.config
        self.assertEqual(config.get('Title-b'), 'Data at {address}')
        self.assertEqual(config.get('Title-c'), 'Code at {address}')
        self.assertTrue(mock_skool_writer.wrote_skool)

    def test_invalid_option(self):
        output, error = self.run_sna2skool('-x dummy.bin', catch_exit=2)
        self.assertEqual(output, '')
        self.assertTrue(error.startswith('usage: sna2skool.py'))

    def test_invalid_option_value(self):
        for option in (('-s ABC'), ('-o +'), ('-p ='), ('-n q'), ('-m .'), ('-L ?')):
            output, error = self.run_sna2skool(option, catch_exit=2)
            self.assertEqual(output, '')
            self.assertTrue(error.startswith('usage: sna2skool.py'))

    def test_no_arguments(self):
        output, error = self.run_sna2skool(catch_exit=2)
        self.assertEqual(output, '')
        self.assertTrue(error.startswith('usage: sna2skool.py'))

    def test_nonexistent_input_file(self):
        nonexistent_bin = '{}/nonexistent.bin'.format(self.make_directory())
        with self.assertRaisesRegex(SkoolKitError, '{}: file not found'.format(nonexistent_bin)):
            self.run_sna2skool(nonexistent_bin)

    def test_nonexistent_control_file(self):
        nonexistent_ctl = '{}/nonexistent.ctl'.format(self.make_directory())
        with self.assertRaisesRegex(SkoolKitError, '{}: file not found'.format(nonexistent_ctl)):
            self.run_sna2skool('-c {} {}'.format(nonexistent_ctl, self.write_bin_file(suffix='.bin')))

    def test_option_V(self):
        for option in ('-V', '--version'):
            output, error = self.run_sna2skool(option, catch_exit=0)
            self.assertEqual(output, 'SkoolKit {}\n'.format(VERSION))

    @patch.object(sna2skool, 'make_snapshot', mock_make_snapshot)
    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_option_H(self):
        for option in ('-H', '--hex'):
            output, error = self.run_sna2skool('{} {}/test.sna'.format(option, self.make_directory()))
            self.assertEqual(error, '')
            self.assertEqual(mock_skool_writer.options.base, 16)
            self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'make_snapshot', mock_make_snapshot)
    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_option_L(self):
        for option in ('-l', '--lower'):
            output, error = self.run_sna2skool('{} {}/test.sna'.format(option, self.make_directory()))
            self.assertEqual(error, '')
            self.assertEqual(mock_skool_writer.options.case, 1)
            self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'make_snapshot', mock_make_snapshot)
    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_option_c(self):
        ctlfile = 'test-c.ctl'
        for option in ('-c', '--ctl'):
            output, error = self.run_sna2skool('{} {} test.sna'.format(option, ctlfile))
            self.assertEqual(error, 'Using control file: {}\n'.format(ctlfile))
            self.assertEqual([ctlfile], mock_ctl_parser.ctlfiles)
            self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'make_snapshot', mock_make_snapshot)
    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_option_c_multiple(self):
        ctlfiles = ['test-c-multiple-1.ctl', 'test-c-multiple-2.ctl']
        options = ['-c ' + ctlfile for ctlfile in ctlfiles]
        output, error = self.run_sna2skool('{} test.sna'.format(' '.join(options)))
        self.assertEqual(error, 'Using control files: {}\n'.format(', '.join(ctlfiles)))
        self.assertEqual(ctlfiles, mock_ctl_parser.ctlfiles)
        self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'make_snapshot', mock_make_snapshot)
    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_option_c_0(self):
        output, error = self.run_sna2skool('-c 0 test.sna')
        self.assertEqual(error, '')
        self.assertEqual(mock_ctl_parser.ctls, {16384: 'c', 65536: 'i'})
        self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_option_ctl_0_ignores_default_control_file(self):
        binfile = self.write_bin_file([0] * 3, suffix='.bin')
        self.write_text_file('b 65533', '{}.ctl'.format(binfile[:-4]))
        output, error = self.run_sna2skool('--ctl 0 {}'.format(binfile))
        self.assertEqual(error, '')
        self.assertEqual(mock_ctl_parser.ctls, {65533: 'c', 65536: 'i'})
        self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'make_snapshot', mock_make_snapshot)
    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_option_c_with_directory(self):
        ctldir = self.make_directory()
        ctlfiles = [self.write_text_file(path=os.path.join(ctldir, c)) for c in ('bar.ctl', 'foo.ctl')]
        self.write_text_file(path='{}/not-a-ctl.txt'.format(ctldir))
        output, error = self.run_sna2skool('-c {} test-c-dir.bin'.format(ctldir))
        self.assertEqual(error, 'Using control files: {}\n'.format(', '.join(ctlfiles)))
        self.assertEqual(ctlfiles, mock_ctl_parser.ctlfiles)
        self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'make_snapshot', mock_make_snapshot)
    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_option_ctl_with_two_directories(self):
        ctldir1 = self.make_directory()
        ctlfiles = [self.write_text_file(path=os.path.join(ctldir1, c)) for c in ('bar.ctl', 'foo.ctl')]
        ctldir2 = self.make_directory()
        ctlfiles.append(self.write_text_file(path=os.path.join(ctldir2, 'baz.ctl')))
        output, error = self.run_sna2skool('--ctl {} --ctl {} test-c-dirs.bin'.format(ctldir1, ctldir2))
        self.assertEqual(error, 'Using control files: {}\n'.format(', '.join(ctlfiles)))
        self.assertEqual(ctlfiles, mock_ctl_parser.ctlfiles)
        self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'make_snapshot', mock_make_snapshot)
    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_option_c_with_directory_and_file(self):
        ctldir = self.make_directory()
        ctlfiles = [self.write_text_file(path=os.path.join(ctldir, c)) for c in ('bar.ctl', 'foo.ctl')]
        ctl3 = self.write_text_file(suffix='.ctl')
        ctlfiles.append(ctl3)
        output, error = self.run_sna2skool('-c {} -c {} test-c-dir-file.bin'.format(ctldir, ctl3))
        self.assertEqual(error, 'Using control files: {}\n'.format(', '.join(ctlfiles)))
        self.assertEqual(ctlfiles, mock_ctl_parser.ctlfiles)
        self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_option_ctl_with_empty_directory(self):
        binfile = self.write_bin_file([0] * 2, suffix='.bin')
        output, error = self.run_sna2skool('--ctl {} {}'.format(self.make_directory(), binfile))
        self.assertEqual(error, '')
        self.assertEqual(mock_ctl_parser.ctls, {65534: 'c', 65536: 'i'})
        self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'make_snapshot', mock_make_snapshot)
    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_option_c_with_current_directory(self):
        ctl1 = self.write_text_file(suffix='.ctl')
        ctl2 = self.write_text_file(suffix='.ctl')
        ctlfiles = sorted(os.path.join('.', f) for f in (ctl1, ctl2))
        output, error = self.run_sna2skool('-c . test-c-cwd.bin')
        self.assertEqual(error, 'Using control files: {}\n'.format(', '.join(ctlfiles)))
        self.assertEqual(ctlfiles, mock_ctl_parser.ctlfiles)
        self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_option_e(self):
        binfile = self.write_bin_file([0] * 3)
        for option, value in (('-e', 65534), ('--end', 65535)):
            output, error = self.run_sna2skool('{} {} {}'.format(option, value, binfile))
            self.assertEqual(error, '')
            ctls = mock_skool_writer.ctl_parser.ctls
            self.assertIn(value, ctls)
            self.assertEqual(ctls[value], 'i')
            self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_option_e_with_hex_address(self):
        binfile = self.write_bin_file([0] * 3)
        for option, value in (('-e', '0xfffe'), ('--end', '0xFFFF')):
            output, error = self.run_sna2skool('{} {} {}'.format(option, value, binfile))
            self.assertEqual(error, '')
            ctls = mock_skool_writer.ctl_parser.ctls
            end = int(value[2:], 16)
            self.assertIn(end, ctls)
            self.assertEqual(ctls[end], 'i')
            self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'make_snapshot', mock_make_snapshot)
    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_options_e_and_c(self):
        ctlfile = 'test.ctl'
        end = 34576
        output, error = self.run_sna2skool('-c {} -e {} test.sna'.format(ctlfile, end))
        self.assertEqual(error, 'Using control file: {}\n'.format(ctlfile))
        self.assertEqual([ctlfile], mock_ctl_parser.ctlfiles)
        self.assertEqual(mock_ctl_parser.min_address, 0)
        self.assertEqual(mock_ctl_parser.max_address, end)
        self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'run', mock_run)
    @patch.object(sna2skool, 'get_config', mock_config)
    def test_option_I(self):
        for option, spec, attr, exp_value in (('-I', 'Base=16', 'base', 16), ('--ini', 'Case=1', 'case', 1)):
            self.run_sna2skool('{} {} test-I.skool'.format(option, spec))
            options, config = run_args[1:]
            self.assertEqual(options.params, [spec])
            self.assertEqual(getattr(options, attr), exp_value)
            self.assertEqual(config.get(spec.split('=')[0]), exp_value)

    @patch.object(sna2skool, 'run', mock_run)
    @patch.object(sna2skool, 'get_config', mock_config)
    def test_option_I_multiple(self):
        self.run_sna2skool('-I DefbSize=12 --ini LineWidth=99 test-I-multiple.skool')
        options, config = run_args[1:]
        self.assertEqual(options.params, ['DefbSize=12', 'LineWidth=99'])
        self.assertEqual(config.get('DefbSize'), 12)
        self.assertEqual(options.line_width, 99)
        self.assertEqual(config.get('LineWidth'), 99)

    @patch.object(sna2skool, 'run', mock_run)
    @patch.object(sna2skool, 'get_config', mock_config)
    def test_option_I_overrides_other_options(self):
        self.run_sna2skool('-H -I Base=10 -l --ini Case=2 test.skool')
        options = run_args[1]
        self.assertEqual(options.params, ['Base=10', 'Case=2'])
        self.assertEqual(options.base, 10)
        self.assertEqual(options.case, 2)

    @patch.object(sna2skool, 'run', mock_run)
    def test_option_I_overrides_config_read_from_file(self):
        ini = """
            [sna2skool]
            Base=16
            Case=2
        """
        self.write_text_file(dedent(ini).strip(), 'skoolkit.ini')
        self.run_sna2skool('-I Base=10 --ini Case=1 test.skool')
        options = run_args[1]
        self.assertEqual(options.params, ['Base=10', 'Case=1'])
        self.assertEqual(options.base, 10)
        self.assertEqual(options.case, 1)

    @patch.object(sna2skool, 'run', mock_run)
    @patch.object(sna2skool, 'get_config', mock_config)
    def test_option_I_invalid_value(self):
        self.run_sna2skool('-I Text=x test-I-invalid.skool')
        config = run_args[2]
        self.assertEqual(config.get('Text'), 0)

    @patch.object(snapshot, 'read_bin_file', Mock(return_value=[201]))
    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_option_o(self):
        for option, value in (('-o', 49152), ('--org', 32768)):
            output, error = self.run_sna2skool('{} {} {}/test.bin'.format(option, value, self.make_directory()))
            self.assertEqual(error, '')
            self.assertEqual({value: 'c', value + 1: 'i'}, mock_ctl_parser.ctls)
            self.assertEqual(mock_skool_writer.snapshot[value], 201)
            self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(snapshot, 'read_bin_file', Mock(return_value=[201]))
    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_option_o_with_hex_address(self):
        for option, value in (('-o', '0x7f00'), ('--org', '0xAB0C')):
            output, error = self.run_sna2skool('{} {} {}/test.bin'.format(option, value, self.make_directory()))
            self.assertEqual(error, '')
            org = int(value[2:], 16)
            self.assertEqual({org: 'c', org + 1: 'i'}, mock_ctl_parser.ctls)
            self.assertEqual(mock_skool_writer.snapshot[org], 201)
            self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_option_p(self):
        ram = [0] * 49152
        pages = {3: [201] + [0] * 16383}
        ctlfile = self.write_text_file('c49152\ni49153', suffix='.ctl')
        z80file = self.write_z80(ram, version=3, machine_id=4, pages=pages)[1]
        for option in ('-p', '--page'):
            self.run_sna2skool('-c {} {} 3 {}'.format(ctlfile, option, z80file))
            self.assertEqual(mock_skool_writer.snapshot[49152], 201)
            self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'get_config', mock_config)
    def test_option_show_config(self):
        output, error = self.run_sna2skool('--show-config', catch_exit=0)
        self.assertEqual(error, '')
        exp_output = """
            [sna2skool]
            Base=10
            Case=2
            CommentWidthMin=10
            DefbSize=8
            DefmSize=65
            DefwSize=1
            EntryPointRef=This entry point is used by the routine at {ref}.
            EntryPointRefs=This entry point is used by the routines at {refs} and {ref}.
            InstructionWidth=13
            LineWidth=79
            ListRefs=1
            Ref=Used by the routine at {ref}.
            Refs=Used by the routines at {refs} and {ref}.
            Semicolons=c
            Text=0
            Title-b=Data block at {address}
            Title-c=Routine at {address}
            Title-g=Game status buffer entry at {address}
            Title-i=Ignored
            Title-s=Unused
            Title-t=Message at {address}
            Title-u=Unused
            Title-w=Data block at {address}
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    def test_option_show_config_read_from_file(self):
        ini = """
            [sna2skool]
            Case=1
            Ref=Called by the routine at {ref}.
            Title-t=Text at {address}
        """
        self.write_text_file(dedent(ini).strip(), 'skoolkit.ini')
        output, error = self.run_sna2skool('--show-config', catch_exit=0)
        self.assertEqual(error, '')
        exp_output = """
            [sna2skool]
            Base=10
            Case=1
            CommentWidthMin=10
            DefbSize=8
            DefmSize=65
            DefwSize=1
            EntryPointRef=This entry point is used by the routine at {ref}.
            EntryPointRefs=This entry point is used by the routines at {refs} and {ref}.
            InstructionWidth=13
            LineWidth=79
            ListRefs=1
            Ref=Called by the routine at {ref}.
            Refs=Used by the routines at {refs} and {ref}.
            Semicolons=c
            Text=0
            Title-b=Data block at {address}
            Title-c=Routine at {address}
            Title-g=Game status buffer entry at {address}
            Title-i=Ignored
            Title-s=Unused
            Title-t=Text at {address}
            Title-u=Unused
            Title-w=Data block at {address}
        """
        self.assertEqual(dedent(exp_output).strip(), output.rstrip())

    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_start_address_defaults_to_16384_for_snapshot(self):
        snafile = self.write_bin_file([0] * 49179, suffix='.sna')
        output, error = self.run_sna2skool('{}'.format(snafile))
        self.assertEqual(error, '')
        exp_ctls = {16384: 'c', 65536: 'i'}
        self.assertEqual(exp_ctls, mock_ctl_parser.ctls)
        self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_start_address_defaults_to_org_address_for_raw_memory_file(self):
        data = [0] * 10
        binfile = self.write_bin_file(data, suffix='.bin')
        org = 37
        output, error = self.run_sna2skool('-o {} {}'.format(org, binfile))
        self.assertEqual(error, '')
        exp_ctls = {org: 'c', org + len(data): 'i'}
        self.assertEqual(exp_ctls, mock_ctl_parser.ctls)
        self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'make_snapshot', mock_make_snapshot)
    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_option_s(self):
        start = 65534
        exp_ctls = {start: 'c', 65536: 'i'}
        for option in ('-s', '--start'):
            output, error = self.run_sna2skool('{} {} {}/test.sna'.format(option, start, self.make_directory()))
            self.assertEqual(error, '')
            self.assertEqual(exp_ctls, mock_ctl_parser.ctls)
            self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'make_snapshot', mock_make_snapshot)
    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_option_s_with_hex_address(self):
        start = 65534
        exp_ctls = {start: 'c', 65536: 'i'}
        for option in ('-s', '--start'):
            output, error = self.run_sna2skool('{} 0x{:04x} {}/test.sna'.format(option, start, self.make_directory()))
            self.assertEqual(error, '')
            self.assertEqual(exp_ctls, mock_ctl_parser.ctls)
            self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_option_s_below_16384_with_snapshot(self):
        start = 8192
        exp_ctls = {start: 'c', 65536: 'i'}
        snafile = self.write_bin_file([0] * 49179, suffix='.sna')
        output, error = self.run_sna2skool('-s {} {}'.format(start, snafile))
        self.assertEqual(error, '')
        self.assertEqual(exp_ctls, mock_ctl_parser.ctls)
        self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'make_snapshot', mock_make_snapshot)
    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_options_s_and_c(self):
        ctlfile = 'test.ctl'
        start = 12345
        output, error = self.run_sna2skool('-c {} -s {} test.sna'.format(ctlfile, start))
        self.assertEqual(error, 'Using control file: {}\n'.format(ctlfile))
        self.assertEqual([ctlfile], mock_ctl_parser.ctlfiles)
        self.assertEqual(mock_ctl_parser.min_address, start)
        self.assertEqual(mock_ctl_parser.max_address, 65536)
        self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'make_snapshot', mock_make_snapshot)
    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_options_s_and_e_and_c(self):
        ctlfile = 'test.ctl'
        start = 12345
        end = 23456
        output, error = self.run_sna2skool('-c {} -s {} -e {} test.z80'.format(ctlfile, start, end))
        self.assertEqual(error, 'Using control file: {}\n'.format(ctlfile))
        self.assertEqual([ctlfile], mock_ctl_parser.ctlfiles)
        self.assertEqual(mock_ctl_parser.min_address, start)
        self.assertEqual(mock_ctl_parser.max_address, end)
        self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_option_w(self):
        binfile = self.write_bin_file(suffix='.bin')
        line_width = 120
        for option in ('-w', '--line-width'):
            output, error = self.run_sna2skool('{} {} {}'.format(option, line_width, binfile))
            self.assertEqual(error, '')
            self.assertEqual(mock_skool_writer.options.line_width, line_width)
            self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_unrecognised_snapshot_format_is_treated_as_binary(self):
        data = [1, 2, 3]
        binfile = self.write_bin_file(data, suffix='.qux')
        self.run_sna2skool(binfile)
        self.assertEqual(data, mock_skool_writer.snapshot[65533:65536])
        self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'make_snapshot', mock_make_snapshot)
    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_default_ctl(self):
        snafile = os.path.join(self.make_directory(), 'test-default-ctl.sna')
        ctlfile = '{}.ctl'.format(snafile[:-4])
        self.write_text_file(path=ctlfile)
        output, error = self.run_sna2skool(snafile)
        self.assertEqual(error, 'Using control file: {}\n'.format(ctlfile))
        self.assertEqual([ctlfile], mock_ctl_parser.ctlfiles)
        self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'make_snapshot', mock_make_snapshot)
    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_multiple_default_ctls(self):
        snafile = os.path.join(self.make_directory(), 'test-default-ctls.sna')
        prefix = snafile[:-4]
        suffixes = ('-1', '-2', '-last')
        ctlfiles = [self.write_text_file(path='{}{}.ctl'.format(prefix, s)) for s in suffixes]
        output, error = self.run_sna2skool(snafile)
        self.assertEqual(error, 'Using control files: {}\n'.format(', '.join(ctlfiles)))
        self.assertEqual(ctlfiles, mock_ctl_parser.ctlfiles)
        self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(sna2skool, 'make_snapshot', mock_make_snapshot)
    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_default_ctl_for_unrecognised_snapshot_format(self):
        binfile = os.path.join(self.make_directory(), 'input.bar')
        ctlfile = self.write_text_file(path='{}.ctl'.format(binfile))
        output, error = self.run_sna2skool(binfile)
        self.assertEqual(error, 'Using control file: {}\n'.format(ctlfile))
        self.assertEqual([ctlfile], mock_ctl_parser.ctlfiles)
        self.assertTrue(mock_skool_writer.wrote_skool)

    @patch.object(components, 'SK_CONFIG', None)
    @patch.object(sna2skool, 'CtlParser', MockCtlParser)
    @patch.object(sna2skool, 'SkoolWriter', MockSkoolWriter)
    def test_custom_snapshot_reader(self):
        custom_snapshot_reader = """
            def can_read(fname):
                return fname.endswith('.snap')
            def get_snapshot(fname, page=None):
                return [128]
        """
        self.write_component_config('SnapshotReader', '*', custom_snapshot_reader)
        binfile = self.write_bin_file(suffix='.snap')
        output, error = self.run_sna2skool(binfile)
        self.assertEqual(error, '')
        self.assertEqual([128], mock_skool_writer.snapshot)
        self.assertTrue(mock_skool_writer.wrote_skool)
