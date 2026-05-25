#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import sys
import time

SKOOLKIT_HOME = os.environ.get('SKOOLKIT_HOME')
if not SKOOLKIT_HOME:
    sys.stderr.write('SKOOLKIT_HOME is not set; aborting\n')
    sys.exit(1)
if not os.path.isdir(SKOOLKIT_HOME):
    sys.stderr.write('SKOOLKIT_HOME={}; directory not found\n'.format(SKOOLKIT_HOME))
    sys.exit(1)
sys.path.insert(0, SKOOLKIT_HOME)

SPECTRUM_RZX = os.environ.get('SPECTRUM_RZX')
if not SPECTRUM_RZX:
    sys.stderr.write('SPECTRUM_RZX is not set; aborting\n')
    sys.exit(1)
if not os.path.isdir(SPECTRUM_RZX):
    sys.stderr.write(f'SPECTRUM_RZX={SPECTRUM_RZX}; directory not found\n')
    sys.exit(1)

from skoolkit import rzxplay
from skoolkit.snapshot import Snapshot

HEADER = r"""
#!/usr/bin/env python3
import contextlib
import hashlib
import os
import sys
import unittest

SKOOLKIT_HOME = os.environ.get('SKOOLKIT_HOME')
if not SKOOLKIT_HOME:
    sys.stderr.write('SKOOLKIT_HOME is not set; aborting\n')
    sys.exit(1)
if not os.path.isdir(SKOOLKIT_HOME):
    sys.stderr.write('SKOOLKIT_HOME={}; directory not found\n'.format(SKOOLKIT_HOME))
    sys.exit(1)
sys.path.insert(0, SKOOLKIT_HOME)

from skoolkit import rzxplay
from skoolkit.snapshot import Snapshot

class RZXTest(unittest.TestCase):
    def _test_rzx(self, options, rzx, fname, reg):
        outfile = f'/tmp/{fname}'
        outfile_dir = os.path.dirname(outfile)
        try:
            if not os.path.isdir(outfile_dir):
                os.makedirs(outfile_dir)
        except:
            pass
        if not os.path.isdir(outfile_dir):
            self.fail(f"Failed to create output directory '{outfile_dir}'")
        with contextlib.redirect_stderr(sys.stdout):
            rzxplay.main(('--quiet', '--no-screen', *options, rzx, outfile))
        r = Snapshot.get(outfile)
        ram = r.ram(-1)
        md5sum = hashlib.md5(bytes(ram)).hexdigest()
        rvals = {
            "AF,BC,DE,HL": f'{r.a:02X}{r.f:02X},{r.bc:04X},{r.de:04X},{r.hl:04X}',
            "AF',BC',DE',HL'": f'{r.a2:02X}{r.f2:02X},{r.bc2:04X},{r.de2:04X},{r.hl2:04X}',
            "PC,SP,IX,IY": f'{r.pc:04X},{r.sp:04X},{r.ix:04X},{r.iy:04X}',
            "IR,iff,im,border": f'{r.i:02X}{r.r:02X},{r.iff2},{r.im},{r.border}',
            "ay": ''.join(f'{v:02X}' for v in r.ay),
            "ram": md5sum
        }
        self.assertEqual(reg, rvals)
""".lstrip()

TEST = """
    def test_{name}(self):
        self._test_rzx(
            {options},
            {rzx},
            {fname},
            {reg}
        )
"""

FOOTER = r"""
if __name__ == '__main__':
    import nose2
    from skoolkit import CSimulator
    if {c} and CSimulator is None:
        print('CSimulator not found. Run the following command and try again:\n\n  make -C $SKOOLKIT_HOME cmods')
        sys.exit(1)
    sys.argv.extend(('--plugin=nose2.plugins.mp', '-N', '{processes}', '-B'))
    nose2.main()
"""

def get_test_fname(c, num_frames):
    suffix = ''
    if c:
        suffix += '-c'
    if num_frames > 0:
        suffix += f'-{num_frames}'
    return f'test_rzxplay{suffix}.py'

def get_snapshots_json_fname(num_frames):
    if num_frames > 0:
        return f'snapshots-{num_frames}.json'
    return 'snapshots.json'

def error(msg):
    with open('errors.log', 'a') as f:
        f.write(msg + '\n')

def write_snapshots_json(fname, snapshots):
    with open(fname, 'w') as f:
        f.write(json.dumps(snapshots, sort_keys=True, indent=4))

def run(infile, gen_options):
    num_frames = gen_options.frames
    snapshots_json_fname = get_snapshots_json_fname(num_frames)
    try:
        with open(snapshots_json_fname) as f:
            snapshots = json.load(f)
        snapshots_json_tstamp = os.stat(snapshots_json_fname).st_mtime
    except:
        snapshots = {}
        snapshots_json_tstamp = 0
    stale_count = 0
    for snapshot in list(snapshots.keys()):
        if not os.path.isfile(snapshot):
            stale_count += 1
            del snapshots[snapshot]
    if stale_count:
        write_snapshots_json(snapshots_json_fname, snapshots)
        print(f'Pruned {stale_count} snapshot(s) from {snapshots_json_fname}')

    new_count = 0
    tests = []
    snapshot_r_time = 0
    snapshot_w_time = 0
    total_time_start = time.time()
    gap = False

    rzxfnames = []
    with open(infile) as f:
        for line in f:
            s_line = line.strip()
            if s_line:
                elements = s_line.split('|', 2)
                elements += [''] * (3 - len(elements))
                rzxfnames.append([e.strip() for e in elements])

    for fname, extra_options, ext_snapshot in sorted(rzxfnames):
        rzxfile = os.path.join(SPECTRUM_RZX, fname)
        options = [e for e in extra_options.split(' ') if e]
        if not gen_options.c:
            options.append('--python')
        outfile = f'{fname[:-4]}.z80'
        if num_frames > 0:
            options.extend(('--stop', str(num_frames)))
            snapshot = os.path.join(f'snapshots-{num_frames}', outfile)
        else:
            snapshot = os.path.join('snapshots', outfile)
        if ext_snapshot:
            options.extend(('--snapshot', os.path.join(os.path.dirname(rzxfile), ext_snapshot)))
        if not os.path.isfile(snapshot):
            snapshot_dir = os.path.dirname(snapshot)
            if not os.path.isdir(snapshot_dir):
                os.makedirs(snapshot_dir)
            print(f'*** Generating {snapshot}')
            start = time.time()
            try:
                rzxplay.main((*options, '--no-screen', rzxfile, snapshot))
            except Exception as e:
                msg = f'ERROR: Failed to play {rzxfile}: {e.args[0]}'
                error(msg)
                sys.stderr.write(msg + '\n')
                continue
            snapshot_w_time += time.time() - start
            gap = True
        z80file_tstamp = os.stat(snapshot).st_mtime
        if snapshot not in snapshots or z80file_tstamp > snapshots_json_tstamp:
            print(f'*** Reading {snapshot}')
            snapshot_r_time_start = time.time()
            r = Snapshot.get(snapshot)
            ram = r.ram(-1)
            ramsum = hashlib.md5(bytes(ram)).hexdigest()
            snapshots[snapshot] = {
                "AF,BC,DE,HL": f'{r.a:02X}{r.f:02X},{r.bc:04X},{r.de:04X},{r.hl:04X}',
                "AF',BC',DE',HL'": f'{r.a2:02X}{r.f2:02X},{r.bc2:04X},{r.de2:04X},{r.hl2:04X}',
                "PC,SP,IX,IY": f'{r.pc:04X},{r.sp:04X},{r.ix:04X},{r.iy:04X}',
                "IR,iff,im,border": f'{r.i:02X}{r.r:02X},{r.iff2},{r.im},{r.border}',
                "ay": ''.join(f'{v:02X}' for v in r.ay),
                "ram": ramsum
            }
            snapshot_r_time += time.time() - snapshot_r_time_start
            new_count += 1
            gap = True
        tests.append({
            'name': ''.join(c.lower() if c.isalnum() else '_' for c in fname[:-4]),
            'options': repr(tuple(options)),
            'rzx': repr(rzxfile),
            'fname': repr(outfile),
            'reg': repr(snapshots[snapshot])
        })

    if gap:
        print()
    if new_count:
        write_snapshots_json(snapshots_json_fname, snapshots)
        print(f'Added {new_count} snapshot(s) to {snapshots_json_fname}')
    else:
        print(f'{snapshots_json_fname} is up-to-date')
    print()

    test_fname = get_test_fname(gen_options.c, num_frames)
    with open(test_fname, 'w') as f:
        f.write(HEADER)
        for test in tests:
            f.write(TEST.format(**test))
        f.write(FOOTER.format(c=gen_options.c, processes=gen_options.processes))
    os.chmod(test_fname, 0o755)
    print(f'Wrote {test_fname} ({len(tests)} tests)')

    total_time = time.time() - total_time_start
    print(f'Snapshot read time: {snapshot_r_time:.2f}s')
    print(f'Snapshot write time: {snapshot_w_time:.2f}s')
    print(f'Total time: {total_time:.2f}s')

    print(f'\nNow run ./{test_fname}')

DESCRIPTION = f"""
Generate tests for all the RZX files named in FILE, along with a script to run
them. The filenames must be relative to the directory pointed at by the
SPECTRUM_RZX environment variable, which is currently:

  {SPECTRUM_RZX}

The format of each line in FILE must be:

  relpath/to/game.rzx[|extra-options[|ext-snapshot]]

where 'ext-snapshot', if given, is the name of an external snapshot file
relative to the directory containing game.rzx, and 'extra-options' are any
options required to play the RZX file (e.g. --force).

If 'N' is given, then at most N frames of each RZX file is played. By default,
each RZX file is played to the end.

Each reference snapshot (i.e. snapshot obtained by playing an RZX file)
required by the tests must exist in a subdirectory named 'snapshots' (or
'snapshots-N' if 'N' is given); if the snapshot doesn't already exist, it will
be generated.

Snapshot metadata is cached in a file named 'snapshots.json' (or
'snapshots-N.json' if 'N' is given). Any out-of-date metadata it contains is
automatically updated by this script.
""".strip()

parser = argparse.ArgumentParser(
    usage='%(prog)s [options] FILE [N]',
    description=DESCRIPTION,
    formatter_class=argparse.RawTextHelpFormatter,
    add_help=False
)
parser.add_argument('rzx_list', help=argparse.SUPPRESS, nargs='?')
parser.add_argument('frames', help=argparse.SUPPRESS, nargs='?', type=int, default=0)
group = parser.add_argument_group('Options')
group.add_argument('-c', action='store_true',
                   help="Generate tests for rzxplay.py using CSimulator.")
group.add_argument('-j', dest='processes', metavar='PROCS', type=int, default=0,
                   help="Run tests using this many processes.")
namespace, unknown_args = parser.parse_known_args()
if unknown_args or not namespace.rzx_list:
    parser.exit(2, parser.format_help())
run(namespace.rzx_list, namespace)
