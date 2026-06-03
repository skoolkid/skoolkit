#!/usr/bin/env python3
import argparse

from libtimer import read_timings, print_comparison

def run(before, after, options):
    bt = read_timings(before)
    at = read_timings(after)
    print_comparison(bt, at, options.faster, options.slower, options.key)

parser = argparse.ArgumentParser(
    usage="%(prog)s [options] before.txt after.txt",
    description="Compare timings in before.txt with those in after.txt.",
    add_help=False
)
parser.add_argument('before', help=argparse.SUPPRESS, nargs='?')
parser.add_argument('after', help=argparse.SUPPRESS, nargs='?')
group = parser.add_argument_group('Options')
group.add_argument('-f', dest='faster', action='store_true',
                   help='Only show timings that are now faster.')
group.add_argument('-k', dest='key',
                   help='Only compare timings for this key.')
group.add_argument('-s', dest='slower', action='store_true',
                   help='Only show timings that are now slower.')
namespace, unknown_args = parser.parse_known_args()
if unknown_args or namespace.after is None:
    parser.exit(2, parser.format_help())
run(namespace.before, namespace.after, namespace)
