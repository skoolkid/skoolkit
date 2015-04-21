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

def _write_tests(test_type, skool, snapshot, output, html_writer, asm_writer):
    print(PROLOGUE)
    print("SKOOL = '{}'\n".format(skool))
    variables = []
    if test_type == 'asm' and asm_writer:
        print("ASM_WRITER = '{}'\n".format(asm_writer))
        variables.append('ASM_WRITER')
    elif test_type == 'html':
        print('OUTPUT = """{}"""\n'.format(output))
        variables.append('OUTPUT')
        if html_writer:
            print("HTML_WRITER = '{}'\n".format(html_writer))
            variables.append('HTML_WRITER')
    elif test_type == 'sft':
        print("SNAPSHOT = '{}'\n".format(snapshot))
        variables.append('SNAPSHOT')
    class_name = '{}TestCase'.format(test_type.capitalize())
    print('class {0}(disassemblytest.{0}):'.format(class_name))
    for options in OPTIONS_LISTS[test_type]:
        method_name_suffix = options.replace('-', '_').replace(' ', '')
        method_name = 'test_{}{}'.format(test_type, method_name_suffix)
        args = ["'{}'".format(options.lstrip()), 'SKOOL'] + variables
        print("    def {}(self):".format(method_name))
        print("        self._test_{}({})".format(test_type, ', '.join(args)))
        print("")

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
    for w in ('', '-w b', '-w bt', '-w btd', '-w btdr', '-w btdrm', '-w btdrms', '-w btdrmsc'):
        for h in ('', '-h'):
            for a in ('', '-a'):
                for b in ('', '-b'):
                    options_list.append('{} {} {} {}'.format(w, h, a, b).strip())
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
    'sft': ('', '-h', '-b', '-h -b')
}

TEST_TYPES = sorted(OPTIONS_LISTS)

def write_tests(skool, snapshot, output, html_writer=None, asm_writer=None):
    if len(sys.argv) != 2 or sys.argv[1] not in TEST_TYPES:
        sys.stderr.write("Usage: {} {}\n".format(os.path.basename(sys.argv[0]), '|'.join(TEST_TYPES)))
        sys.exit(1)
    _write_tests(sys.argv[1], skool, snapshot, output, html_writer, asm_writer)
