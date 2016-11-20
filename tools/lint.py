#!/usr/bin/env python
import sys
import os
import argparse
from pylint import lint

# Use the current development version of SkoolKit
SKOOLKIT_HOME = os.environ.get('SKOOLKIT_HOME')
if not SKOOLKIT_HOME:
    sys.stderr.write('SKOOLKIT_HOME is not set; aborting\n')
    sys.exit(1)
if not os.path.isdir(SKOOLKIT_HOME):
    sys.stderr.write('SKOOLKIT_HOME={}; directory not found\n'.format(SKOOLKIT_HOME))
    sys.exit(1)
os.chdir(SKOOLKIT_HOME)

# Messages to ignore by default
IGNORE_MSG_IDS = [
    'C0103', # Invalid name for variable, constant, class
    'C0111', # Missing docstring
    'C0301', # Line too long
    'C0302', # Too many lines in module
    'C0325', # Unnecessary parens after 'print' keyword
    'C1001', # Old-style class
    'E0601', # Variable used before assignment
    'E0611', # No such name in module
    'E1101', # No such member in instance
    'F0401', # Import error
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
    'W0601', # Global variable undefined at the module level
    'W0603', # Using the global statement
    'W0631', # Using possibly undefined loop variable
    'W0632', # Possible unbalanced tuple unpacking
    'W0633', # Attempting to unpack a non-sequence
    'W1401', # Anomalous backslash in string
]

# pylint options
OPTIONS = (
    "--msg-template='{path}:{line}: [{msg_id}:{symbol}:{obj}] {msg}'",
)

###############################################################################
# Begin
###############################################################################
parser = argparse.ArgumentParser(
    usage='lint.py [options]',
    description="Run pylint on the SkoolKit code or test modules.",
    add_help=False
)
group = parser.add_argument_group('Options')
group.add_argument('-d', dest='message_ids', metavar='LIST',
                   help='Disable the messages in this comma-separated list (in addition to those disabled by default)')
group.add_argument('-s', dest='ignore_similarities', action='store_true',
                   help='Ignore messages about code similarities (R0801)')
group.add_argument('-t', dest='test', action='store_true',
                   help='Run pylint on the SkoolKit test modules')
group.add_argument('-u', dest='ignore_unused', action='store_true',
                   help='Ignore messages about unused variables (W0612) and arguments (W0613)')
namespace, unknown_args = parser.parse_known_args()
if unknown_args:
    parser.exit(2, parser.format_help())

extra_ignores = []
if namespace.message_ids:
    extra_ignores.extend(namespace.message_ids.split(','))
if namespace.ignore_similarities:
    extra_ignores.append('R0801')
if namespace.ignore_unused:
    extra_ignores.append('W0612')
    extra_ignores.append('W0613')

if namespace.test:
    os.chdir('tests')
    args = [m for m in os.listdir('.') if m.endswith('.py')]
    extra_ignores.append('F0401') # Unable to import 'skoolkit.*'
else:
    args = ['skoolkit']
IGNORE_MSG_IDS.extend(extra_ignores)

args.extend(OPTIONS)
args.extend(('-d', ','.join(IGNORE_MSG_IDS)))
print('{0}\npylint {1}\n{0}'.format('-' * 80, ' '.join(args)))

lint.Run(args)
