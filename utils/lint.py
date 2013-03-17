#!/usr/bin/env python
import sys
import os
from pylint import lint

# Use the current development version of SkoolKit
SKOOLKIT_HOME = os.environ.get('SKOOLKIT_HOME')
if not SKOOLKIT_HOME:
    sys.stderr.write('SKOOLKIT_HOME is not set; aborting\n')
    sys.exit(1)
if not os.path.isdir(SKOOLKIT_HOME):
    sys.stderr.write('SKOOLKIT_HOME=%s; directory not found\n' % SKOOLKIT_HOME)
    sys.exit(1)
os.chdir(SKOOLKIT_HOME)

# Messages to ignore by default
IGNORE_MSG_IDS = [
    'C0103', # Invalid name for variable, constant, class
    'C0111', # Missing docstring
    'C0301', # Line too long
    'C0302', # Too many lines in module
    'R0201', # Method could be a function
    'R0902', # Too many instance attributes
    'R0903', # Too few public methods
    'R0904', # Too many public methods
    'R0911', # Too many return statements
    'R0912', # Too many branches
    'R0913', # Too many arguments
    'R0914', # Too many local variables
    'R0915', # Too many statements
    'W0142', # Used * or ** magic
    'W0201', # Attribute defined outside __init__
    'W0232', # Class has no __init__ method
    'W0603', # Using the global statement
    'W0631', # Using possibly undefined loop variable
]

# pylint options
OPTIONS = (
    '-i y',
)

def parse_args(args):
    ignores = []
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == '-d':
            ignores.extend(args[i + 1].split(','))
            i += 1
        elif arg == '-s':
            ignores.append('R0801')
        elif arg == '-u':
            ignores.append('W0612')
            ignores.append('W0613')
        elif arg.startswith('-'):
            show_usage()
        i += 1
    return ignores

def show_usage():
    sys.stderr.write("""Usage: %s [options]

  Run pylint on the current development version of SkoolKit.

Available options:
  -d LIST  Disable the messages in this comma-separated list (in addition to
           those disabled by default)
  -s       Ignore messages about code similarities (R0801)
  -u       Ignore messages about unused variables (W0612) and arguments (W0613)
""" % os.path.basename(sys.argv[0]))
    sys.exit()

###############################################################################
# Begin
###############################################################################
extra_ignores = parse_args(sys.argv[1:])
IGNORE_MSG_IDS.extend(extra_ignores)

args = 'skoolkit %s -d %s' % (' '.join(OPTIONS), ','.join(IGNORE_MSG_IDS))
divider = '-' * 80
sys.stdout.write('%s\npylint %s\n%s\n' % (divider, args, divider))

lint.Run(args.split())
