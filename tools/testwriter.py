import sys
import os

PROLOGUE = """
import sys
import os

SKOOLKIT_HOME = os.environ.get('SKOOLKIT_HOME')
if not SKOOLKIT_HOME:
    sys.stderr.write('SKOOLKIT_HOME is not set; aborting\\n')
    sys.exit(1)
if not os.path.isdir(SKOOLKIT_HOME):
    sys.stderr.write('SKOOLKIT_HOME={}: directory not found\\n'.format(SKOOLKIT_HOME))
    sys.exit(1)
sys.path.insert(0, '{}/tests'.format(SKOOLKIT_HOME))
import disassemblytest
""".lstrip()

def _write_tests(test_type, snapshot, output, skool, html_writer, asm_writer, sna2skool_opts, ctl, ref, clean):
    print(PROLOGUE)
    variables = []
    if skool:
        _add_variable(variables, 'SKOOL', skool)
    else:
        _add_variable(variables, 'SNAPSHOT', snapshot)
        _add_variable(variables, 'CTL', ctl)
    if test_type == 'asm':
        if asm_writer:
            _add_variable(variables, 'WRITER', asm_writer)
        if not clean:
            _add_variable(variables, 'CLEAN', clean)
    elif test_type == 'html':
        _add_variable(variables, 'OUTPUT', output, True)
        if html_writer:
            _add_variable(variables, 'WRITER', html_writer)
        if ref:
            _add_variable(variables, 'REF', ref)
    elif test_type == 'sft':
        _add_variable(variables, 'SNAPSHOT', snapshot)
        if sna2skool_opts:
            _add_variable(variables, 'SNA2SKOOL_OPTS', sna2skool_opts)
    class_name = '{}TestCase'.format(test_type.capitalize())
    print('class {0}(disassemblytest.{0}):'.format(class_name))
    for options in OPTIONS_LISTS[test_type]:
        method_name_suffix = options.replace('-', '_').replace(' ', '')
        method_name = 'test_{}{}'.format(test_type, method_name_suffix)
        args = ["'{}'".format(options.lstrip())] + ['{}={}'.format(v.lower(), v) for v in variables]
        print("    def {}(self):".format(method_name))
        print("        self._test_{}({})".format(test_type, ', '.join(args)))
        print("")

def _add_variable(variables, name, value, multiline=False):
    if name not in variables:
        if not isinstance(value, str):
            print("{} = {}\n".format(name, value))
        elif multiline:
            print('{} = """{}"""\n'.format(name, value))
        else:
            print("{} = '{}'\n".format(name, value))
        variables.append(name)

def _get_asm_options_list():
    options_list = []
    for b in ('', '-D', '-H'):
        for c in ('', '-l', '-u'):
            for f in ('', '-f 1', '-f 2', '-f 3'):
                for p in ('', '-s', '-r'):
                    options_list.append('{} {} {} {}'.format(b, c, f, p).strip())
    return options_list

def _get_ctl_options_list():
    options_list = []
    for w in ('', '-w b', '-w bt', '-w btd', '-w btdr', '-w btdrm', '-w btdrms', '-w btdrmsc', '-w abtdrmsc'):
        for h in ('', '-h', '-l'):
            for b in ('', '-b'):
                options_list.append('{} {} {}'.format(w, h, b).strip())
    return options_list

def _get_html_options_list():
    options_list = []
    for b in ('', '-D', '-H'):
        for c in ('', '-u', '-l'):
            options_list.append('{} {}'.format(b, c).strip())
    return options_list

OPTIONS_LISTS = {
    'asm': _get_asm_options_list(),
    'ctl': _get_ctl_options_list(),
    'html': _get_html_options_list(),
    'sft': ('', '-h', '-l', '-b', '-h -b', '-l -b')
}

TEST_TYPES = sorted(OPTIONS_LISTS)

def write_tests(skool=None, snapshot=None, output=None, html_writer=None, asm_writer=None, sna2skool_opts=None, ctl=None, ref=None, clean=True):
    if len(sys.argv) != 2 or sys.argv[1] not in TEST_TYPES:
        sys.stderr.write("Usage: {} {}\n".format(os.path.basename(sys.argv[0]), '|'.join(TEST_TYPES)))
        sys.exit(1)
    _write_tests(sys.argv[1], snapshot, output, skool, html_writer, asm_writer, sna2skool_opts, ctl, ref, clean)
