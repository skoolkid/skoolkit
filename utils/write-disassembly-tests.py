#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os

def write_tests(class_name, options_list):
    print('from disassemblytest import {}Case'.format(class_name))
    print('')
    print('class {0}({0}Case):'.format(class_name))
    for game in ('rom',):
        for options in options_list:
            method_name_suffix = options.replace('-', '_').replace(' ', '')
            method_name = 'test_{}{}'.format(game, method_name_suffix)
            print("    def {}(self):".format(method_name))
            print("        self.write_{}('{}')".format(game, options))
            print("")

def get_asm_options_list():
    options_list = []
    for b in ('', '-D', '-H'):
        for c in ('', '-l', '-u'):
            for f in ('', '-f 1', '-f 2', '-f 3'):
                for p in ('', '-s', '-r'):
                    options_list.append('{} {} {} {}'.format(b, c, f, p).strip())
    return options_list

def get_ctl_options_list():
    options_list = []
    for w in ('', '-w b', '-w bt', '-w btd', '-w btdr', '-w btdrm', '-w btdrms', '-w btdrmsc'):
        for h in ('', '-h'):
            for a in ('', '-a'):
                for b in ('', '-b'):
                    options_list.append('{} {} {} {}'.format(w, h, a, b).strip())
    return options_list

def get_html_options_list():
    options_list = []
    for b in ('', '-D', '-H'):
        for c in ('', '-u', '-l'):
            options_list.append('{} {}'.format(b, c).strip())
    return options_list

TEST_TYPES = {
    'asm': get_asm_options_list(),
    'ctl': get_ctl_options_list(),
    'html': get_html_options_list(),
    'sft': ('', '-h', '-b', '-h -b')
}

###############################################################################
# Begin
###############################################################################
if len(sys.argv) != 2 or sys.argv[1].lower() not in TEST_TYPES:
    sys.stderr.write("Usage: {} asm|ctl|html|sft\n".format(os.path.basename(sys.argv[0])))
    sys.exit(1)
test_type = sys.argv[1].lower()
class_name = '{}Test'.format(test_type.capitalize())
write_tests(class_name, TEST_TYPES[test_type])
