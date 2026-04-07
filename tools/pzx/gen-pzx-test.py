#!/usr/bin/env python3
import argparse
import contextlib
import hashlib
import io
import json
import os
import sys
import time

SKOOLKIT_HOME = os.environ.get('SKOOLKIT_HOME')
if not SKOOLKIT_HOME:
    sys.stderr.write('SKOOLKIT_HOME is not set; aborting\n')
    sys.exit(1)
if not os.path.isdir(SKOOLKIT_HOME):
    sys.stderr.write(f'SKOOLKIT_HOME={SKOOLKIT_HOME}; directory not found\n')
    sys.exit(1)
sys.path.insert(0, SKOOLKIT_HOME)

T2SFILES_HOME = os.environ.get('T2SFILES_HOME')
if not T2SFILES_HOME:
    sys.stderr.write('T2SFILES_HOME is not set; aborting\n')
    sys.exit(1)
if not os.path.isdir(T2SFILES_HOME):
    sys.stderr.write(f'T2SFILES_HOME={T2SFILES_HOME}; directory not found\n')
    sys.exit(1)

from skoolkit import tap2sna
from skoolkit.snapshot import Snapshot

HEADER = r"""
#!/usr/bin/env python3
import hashlib
import os
import sys
import tempfile
import unittest

SKOOLKIT_HOME = os.environ.get('SKOOLKIT_HOME')
if not SKOOLKIT_HOME:
    sys.stderr.write('SKOOLKIT_HOME is not set; aborting\n')
    sys.exit(1)
if not os.path.isdir(SKOOLKIT_HOME):
    sys.stderr.write('SKOOLKIT_HOME={}; directory not found\n'.format(SKOOLKIT_HOME))
    sys.exit(1)
sys.path.insert(0, SKOOLKIT_HOME)

from skoolkit import tap2sna
from skoolkit.snapshot import Snapshot

TMP = tempfile.gettempdir()

class SimLoadTest(unittest.TestCase):
    def _test_sim_load(self, tape, fname, reg, options):
        outfile = f'{TMP}/{fname}'
        tap2sna.main((*options, tape, outfile))
        r = Snapshot.get(outfile)
        ram = r.ram(-1)
        md5sum = hashlib.md5(bytes(ram)).hexdigest()
        rvals = {
            "AF,BC,DE,HL": f'{r.a:02X}{r.f:02X},{r.bc:04X},{r.de:04X},{r.hl:04X}',
            "AF',BC',DE',HL'": f'{r.a2:02X}{r.f2:02X},{r.bc2:04X},{r.de2:04X},{r.hl2:04X}',
            "PC,SP,IX,IY": f'{r.pc:04X},{r.sp:04X},{r.ix:04X},{r.iy:04X}',
            "IR,iff,im,border": f'{r.i:02X}{r.r:02X},{r.iff2},{r.im},{r.border}',
            "ram": md5sum
        }
        self.assertEqual(reg, rvals)
""".lstrip()

TEST = """
    def test_{name}(self):
        self._test_sim_load(
            {tape},
            {fname},
            {reg},
            {options}
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

TEST_FNAME = 'test_pzx.py'

TEST_C_FNAME = 'test_pzx_c.py'

PZX_ERRORS_JSON = f'{SKOOLKIT_HOME}/tools/pzx/pzx-errors.json'

PZX_OPTIONS_JSON = f'{SKOOLKIT_HOME}/tools/pzx/pzx-options.json'

SNAPSHOTS_JSON = 'snapshots.json'

IGNORED_OPTIONS = (
    '--ini',
    '--ram',
    '--reg',
    '--sim-load-config polarity=',
    '--state',
    '--tape-name',
    '--tape-sum'
)

ALLOWED_OPTIONS = (
    "--sim-load-config",
    "--start",
)

def error(msg):
    with open('errors.log', 'a') as f:
        f.write(msg + '\n')

def find_tape(pzx_dir, t2sfile, ignore):
    if t2sfile[0].isalpha():
        tapefile = f'{pzx_dir}/{t2sfile[0]}/{t2sfile[:-4]}.pzx'
    else:
        tapefile = f'{pzx_dir}/0/{t2sfile[:-4]}.pzx'
    if os.path.isfile(tapefile):
        return tapefile
    if not ignore:
        sys.stderr.write(f'ERROR: {t2sfile}: {tapefile} not found\n')
        sys.exit(1)

def write_json(j, fname):
    with open(fname, 'w') as f:
        json.dump(j, f, sort_keys=True, indent=4)
        f.write('\n')

def run(pzx_dir, gen_options):
    try:
        with open(SNAPSHOTS_JSON) as f:
            snapshots = json.load(f)
        snapshots_json_tstamp = os.stat(SNAPSHOTS_JSON).st_mtime
    except:
        snapshots = {}
        snapshots_json_tstamp = 0
    stale_count = 0
    for snapshot in list(snapshots.keys()):
        if not os.path.isfile(snapshot):
            stale_count += 1
            del snapshots[snapshot]
    if stale_count:
        write_json(snapshots, SNAPSHOTS_JSON)
        print(f'Pruned {stale_count} snapshot(s) from {SNAPSHOTS_JSON}')

    try:
        with open(PZX_ERRORS_JSON) as f:
            pzx_errors = json.load(f)
    except FileNotFoundError:
        pzx_errors = {}
    pzx_errors_updates = 0

    try:
        with open(PZX_OPTIONS_JSON) as f:
            pzx_options = json.load(f)
    except FileNotFoundError:
        pzx_options = {}

    new_count = 0
    tests = []
    t2s_r_time = 0
    snapshot_r_time = 0
    snapshot_w_time = 0
    total_time_start = time.time()
    gap = False

    for root, subdirs, files in sorted(os.walk(f'{T2SFILES_HOME}/t2s')):
        for fname in sorted(files):
            t2sfile = os.path.join(root, fname)
            t2s_options = []
            testable = True
            t2s_r_time_start = time.time()
            url = None
            ntapes = 0
            with open(t2sfile) as f:
                for line in f:
                    if line.startswith('--'):
                        if line.startswith('--tape-name'):
                            ntapes += 1
                        if line.startswith(IGNORED_OPTIONS):
                            continue
                        s_line = line.strip()
                        if s_line.startswith(ALLOWED_OPTIONS):
                            opt, opt_arg = s_line.split(' ', 1)
                            if opt_arg.startswith("'"):
                                opt_arg = opt_arg[1:-1]
                            t2s_options.extend((opt, opt_arg))
                        else:
                            testable = False
                            break
                    elif line.startswith('http'):
                        url = line
            t2s_r_time += time.time() - t2s_r_time_start
            if not testable or not url or ntapes > 1:
                continue
            tape = find_tape(pzx_dir, fname, gen_options.ignore)
            if not tape:
                continue
            tape_fname = os.path.basename(tape)
            if tape_fname in pzx_errors:
                continue

            options = pzx_options.get(tape_fname, {}).get('options', t2s_options[:])
            if not gen_options.c:
                options.extend(('--sim-load-config', 'python=1'))
            with open(tape, 'rb') as f:
                tape_sum = hashlib.md5(f.read()).hexdigest()
            suffix = ''
            outfile = f'{fname[:-4]}.z80'
            snapshot = os.path.join('snapshots', outfile)
            write_snapshot = False
            if not os.path.isfile(snapshot):
                write_snapshot = True
            elif snapshot in snapshots:
                if tape_sum != snapshots[snapshot]['md5']:
                    write_snapshot = True
                elif t2s_options != snapshots[snapshot]['options']:
                    write_snapshot = True
            if write_snapshot:
                print(f'*** Generating {snapshot}')
                start = time.time()
                status_error = error_msg = None
                try:
                    with contextlib.redirect_stdout(io.StringIO()) as tap2sna_io:
                        tap2sna.main((*options, tape, snapshot))
                    output = tap2sna_io.getvalue()
                    if 'timed out' in output:
                        status_error = 'timed out'
                        error_msg = f'ERROR: {tape} {status_error}'
                        os.remove(snapshot)
                    print(output)
                except Exception as e:
                    status_error = e.args[0]
                    error_msg = f'ERROR: Failed to LOAD {tape}: {status_error}'
                elapsed = time.time() - start
                if error_msg:
                    tape_status = pzx_errors.setdefault(tape_fname, {})
                    tape_status['error'] = status_error
                    tape_status['options'] = options
                    pzx_errors_updates += 1
                    error(error_msg)
                    sys.stderr.write(error_msg + '\n')
                    continue
                snapshot_w_time += elapsed
                gap = True
            z80file_tstamp = os.stat(snapshot).st_mtime
            update = False
            if snapshot not in snapshots:
                update = True
            elif z80file_tstamp > snapshots_json_tstamp:
                update = True
            if update:
                print(f'*** Reading {snapshot}')
                snapshot_r_time_start = time.time()
                r = Snapshot.get(snapshot)
                ram = r.ram(-1)
                ramsum = hashlib.md5(bytes(ram)).hexdigest()
                reg = {
                    "AF,BC,DE,HL": f'{r.a:02X}{r.f:02X},{r.bc:04X},{r.de:04X},{r.hl:04X}',
                    "AF',BC',DE',HL'": f'{r.a2:02X}{r.f2:02X},{r.bc2:04X},{r.de2:04X},{r.hl2:04X}',
                    "PC,SP,IX,IY": f'{r.pc:04X},{r.sp:04X},{r.ix:04X},{r.iy:04X}',
                    "IR,iff,im,border": f'{r.i:02X}{r.r:02X},{r.iff2},{r.im},{r.border}',
                    "ram": ramsum
                }
                snapshots[snapshot] = {
                    'md5': tape_sum,
                    'options': t2s_options,
                    'state': reg,
                }
                snapshot_r_time += time.time() - snapshot_r_time_start
                new_count += 1
                gap = True
            else:
                reg = snapshots[snapshot]['state']
            name = ''.join(c.lower() if c.isalnum() else '_' for c in snapshot) + suffix
            tests.append({
                'name': name,
                'tape': repr(tape),
                'fname': repr(outfile),
                'reg': repr(reg),
                'options': repr(tuple(options))
            })

    if gap:
        print()
    if new_count:
        write_json(snapshots, SNAPSHOTS_JSON)
        print(f'Added {new_count} snapshot(s) to {SNAPSHOTS_JSON}')
    else:
        print(f'{SNAPSHOTS_JSON} is up-to-date')
    print()

    if pzx_errors_updates:
        write_json(pzx_errors, PZX_ERRORS_JSON)
        print(f'Added {pzx_errors_updates} updates to {PZX_ERRORS_JSON}')

    test_fname = TEST_C_FNAME if gen_options.c else TEST_FNAME
    with open(test_fname, 'w') as f:
        f.write(HEADER)
        for test in tests:
            f.write(TEST.format(**test))
        f.write(FOOTER.format(c=gen_options.c, processes=gen_options.processes))
    os.chmod(test_fname, 0o755)
    print(f'Wrote {test_fname} ({len(tests)} tests)')

    total_time = time.time() - total_time_start
    print(f'\nt2s read time: {t2s_r_time:.2f}s')
    print(f'Snapshot read time: {snapshot_r_time:.2f}s')
    print(f'Snapshot write time: {snapshot_w_time:.2f}s')
    print(f'Total time: {total_time:.2f}s')

    print(f'\nNow run ./{test_fname}')

DESCRIPTION = """
Generate tests for the testable PZX files in PZX_DIR and its subdirectories,
along with a script to run them. A PZX file is regarded as testable so long as
the TAP/TZX file from which it derives is loadable by tap2sna.py without any
options other than:

{}

Each reference snapshot required to generate the tests must exist in a
subdirectory named 'snapshots'. Any reference snapshot that doesn't already
exist will be generated.

Snapshot metadata is cached in a file named 'snapshots.json'. Any out-of-date
metadata it contains is automatically updated by this script.
""".format('\n'.join(f'  {option}' for option in ALLOWED_OPTIONS)).strip()

parser = argparse.ArgumentParser(
    usage='%(prog)s [options] PZX_DIR',
    description=DESCRIPTION,
    formatter_class=argparse.RawTextHelpFormatter,
    add_help=False
)
parser.add_argument('pzx_dir', help=argparse.SUPPRESS, nargs='?')
group = parser.add_argument_group('Options')
group.add_argument('-c', action='store_true',
                   help="Generate tests for tap2sna.py using CSimulator.")
group.add_argument('-i', dest='ignore', action='store_true',
                   help="Do not treat a missing PZX file as an error.")
group.add_argument('-j', dest='processes', metavar='PROCS', type=int, default=0,
                   help="Run tests using this many processes.")
namespace, unknown_args = parser.parse_known_args()
if unknown_args or not namespace.pzx_dir:
    parser.exit(2, parser.format_help())
run(namespace.pzx_dir, namespace)
