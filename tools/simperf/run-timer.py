#!/usr/bin/env python3
import argparse
import contextlib
import io
import os
import sys
import subprocess
import time

from libtimer import (RUNS, RUN_THRESHOLD, FRAMES_PYTHON, FRAMES_C,
                      HALTS_PYTHON, HALTS_C, INSTRUCTIONS_PYTHON,
                      INSTRUCTIONS_C, read_timings, write_timings,
                      print_comparison, write_cfg)

SKOOLKIT_HOME = os.environ.get('SKOOLKIT_HOME')
if not SKOOLKIT_HOME:
    sys.stderr.write('SKOOLKIT_HOME is not set; aborting\n')
    sys.exit(1)
if not os.path.isdir(SKOOLKIT_HOME):
    sys.stderr.write(f'SKOOLKIT_HOME={SKOOLKIT_HOME}; directory not found\n')
    sys.exit(1)

SPECTRUM_RZX = os.environ.get('SPECTRUM_RZX')
if not SPECTRUM_RZX:
    sys.stderr.write('SPECTRUM_RZX is not set; aborting\n')
    sys.exit(1)
if not os.path.isdir(SPECTRUM_RZX):
    sys.stderr.write(f'SPECTRUM_RZX={SPECTRUM_RZX}; directory not found\n')
    sys.exit(1)

SPECTRUM_TAPES = os.environ.get('SPECTRUM_TAPES')
if not SPECTRUM_TAPES:
    sys.stderr.write('SPECTRUM_TAPES is not set; aborting\n')
    sys.exit(1)
if not os.path.isdir(SPECTRUM_TAPES):
    sys.stderr.write(f'SPECTRUM_TAPES={SPECTRUM_TAPES}; directory not found\n')
    sys.exit(1)

RZX = (
    f'{SPECTRUM_RZX}/s/skooldaze.rzx',
    f'{SPECTRUM_RZX}/r/robocop.rzx',
)

rom = open(f'{SKOOLKIT_HOME}/skoolkit/resources/48.rom', 'rb').read()
MEMORY = list(rom) + [0] * 49152

TAPES = {
    "c": (
        (
            f'{SPECTRUM_TAPES}/spectrumcomputing.co.uk/pub/sinclair/games/s/SkoolDaze.tzx/Skool Daze.tzx',
            ('--start', '24288')
        ),
        (
            f'{SPECTRUM_TAPES}/spectrumcomputing.co.uk/pub/sinclair/games/c/ChaseH.Q..tzx/Chase HQ - Side 1.tzx',
            ('-c', 'machine=128', '-c', 'finish-tape=1', '--start', '23384')
        ),
    ),
    "python": (
        (
            f'{SPECTRUM_TAPES}/spectrumcomputing.co.uk/pub/sinclair/games/t/TrapDoorThe.tzx/The Trapdoor.tzx',
            ('--start', '65177')
        ),
        (
            f'{SPECTRUM_TAPES}/spectrumcomputing.co.uk/pub/sinclair/games/s/SpaceHarrierII.tzx/Space Harrier 2 - Side 1.tzx',
            ('-c', 'machine=128', '--start', '27495')
        ),
    )
}

SNAPSHOTS = (
    (
        'skool-daze.z80',
        f'{SPECTRUM_TAPES}/spectrumcomputing.co.uk/pub/sinclair/games/s/SkoolDaze.tzx/Skool Daze.tzx',
        ('--start', '24288')
    ),
    (
        'chase-hq-128k.z80',
        f'{SPECTRUM_TAPES}/spectrumcomputing.co.uk/pub/sinclair/games/c/ChaseH.Q..tzx/Chase HQ - Side 1.tzx',
        ('--start', '23384', '-c', 'machine=128', '-c', 'finish-tape=1')
    ),
    ('48', None, None),
    ('128', None, None),
)


def compare(timings, options):
    if options.before:
        before = read_timings(options.before)
        print_comparison(before, timings)
        out = 'after.txt'
    else:
        hostname = subprocess.run('hostname', capture_output=True, text=True).stdout.rstrip()
        if os.path.isdir(f'{options.skoolkit}/.git'):
            cmd = ('git', '-C', options.skoolkit, 'rev-parse', '--short', 'HEAD')
        else:
            cmd = (f'{options.skoolkit}/bin2sna.py', '-V')
        v = subprocess.run(cmd, capture_output=True, text=True).stdout.strip().split(' ')[-1]
        out = f'timings-{hostname}-{v}.txt'
    if os.path.isfile(out):
        verb = 'Updated'
        u_timings = read_timings(out)
    else:
        verb = 'Wrote'
        u_timings = {}
    u_timings.update(timings)
    write_timings(u_timings, out)
    print(f'{verb} {out}')

def run_trials(timings, k, nruns, f, args):
    timings[k] = times = []
    while len(times) < nruns:
        t = f(*args)
        times.append(round(t, 3))
        print(f'{k}: {t:.3f}s ({len(times)}/{nruns})')
        tmax = max(times)
        if tmax / min(times) >= RUN_THRESHOLD:
            times.remove(tmax)
            print(f'{k}: Max time ({tmax:.3f}s) over threshold; removed')

def run_cmd(rzxplay, *args):
    with contextlib.redirect_stdout(io.StringIO()):
        start = time.time()
        rzxplay.main(args)
        return time.time() - start

def run_rzxplay(options):
    args = []
    keys = ['rzxplay']
    if options.c:
        with contextlib.chdir(options.skoolkit):
            subprocess.run(('python3', 'setup.py', 'build_ext', '-i'))
        keys.append('c')
        nframes = FRAMES_C
    else:
        args.append('--python')
        keys.append('python')
        nframes = FRAMES_PYTHON
    keys.append(str(nframes))
    args.extend(('--no-screen', '--stop', str(nframes)))
    sys.path.insert(0, options.skoolkit)
    from skoolkit import rzxplay
    timings = {}
    for rzxfile in RZX:
        k = ':'.join(keys + [os.path.basename(rzxfile)])
        run_trials(timings, k, options.nruns, run_cmd, (rzxplay, *args, rzxfile))
    compare(timings, options)

def write_code(memory, nhalts):
    nhl, nhh = nhalts % 256, (nhalts & 0xFFFF) // 256
    code = (
        0xFB,                   # $6000 EI
        0x11, nhl, nhh,         # $6001 LD DE,nhalts
        0x76,                   # $6004 HALT
        0x1B,                   # $6005 DEC DE
        0x7A,                   # $6006 LD A,D
        0xB3,                   # $6007 OR E
        0x20, 0xFA,             # $6008 JR NZ,$6004
    )
    org = 0x6000
    end = org + len(code)
    memory[org:end] = code
    return org, end

def run_sim(simulator_cls, nhalts, options):
    s = simulator_cls(MEMORY[:])
    s.run(stop=0x12A9) # Boot
    org, end = write_code(s.memory, nhalts)
    start = time.time()
    s.run(org, end, options.interrupts)
    return time.time() - start

def run_simulator(options):
    keys = ['simulator']
    if options.c:
        with contextlib.chdir(options.skoolkit):
            subprocess.run(('python3', 'setup.py', 'build_ext', '-i'))
        keys.append('c')
        nhalts = HALTS_C
    else:
        keys.append('python')
        nhalts = HALTS_PYTHON
    sys.path.insert(0, options.skoolkit)
    if options.c:
        from skoolkit import CSimulator, CCMIOSimulator
        simulator_cls = CCMIOSimulator if options.cmio else CSimulator
    else:
        from skoolkit.simulator import Simulator
        from skoolkit.cmiosimulator import CMIOSimulator
        simulator_cls = CMIOSimulator if options.cmio else Simulator
    if options.cmio:
        keys.append('cmio')
    if options.interrupts:
        keys.append('i')
    keys.append(str(nhalts))
    k = ':'.join(keys)
    timings = {}
    run_trials(timings, k, options.nruns, run_sim, (simulator_cls, nhalts, options))
    compare(timings, options)

def run_tap2sna(options):
    args = []
    keys = ['tap2sna']
    if options.c:
        with contextlib.chdir(options.skoolkit):
            subprocess.run(('python3', 'setup.py', 'build_ext', '-i'))
        keys.append('c')
        tapes = TAPES['c']
    else:
        args.extend(('-c', 'python=1'))
        keys.append('python')
        tapes = TAPES['python']
    sys.path.insert(0, options.skoolkit)
    from skoolkit import tap2sna
    timings = {}
    for tape, t2sargs in tapes:
        k = ':'.join(keys + [os.path.basename(tape)])
        run_trials(timings, k, options.nruns, run_cmd, (tap2sna, *args, *t2sargs, tape, '/tmp/out.z80'))
    compare(timings, options)

def run_trace_cmd(trace, *args):
    with contextlib.redirect_stdout(io.StringIO()) as trace_o:
        trace.main(args)
    return float(trace_o.getvalue().split('\n')[-2].split()[2][:-1])

def run_trace(options):
    args = []
    keys = ['trace']
    if options.c:
        with contextlib.chdir(options.skoolkit):
            subprocess.run(('python3', 'setup.py', 'build_ext', '-i'))
        keys.append('c')
        ninst = INSTRUCTIONS_C
    else:
        args.append('--python')
        keys.append('python')
        ninst = INSTRUCTIONS_PYTHON
    sys.path.insert(0, options.skoolkit)
    from skoolkit import trace, tap2sna
    args.extend(('--stats', '-m', str(ninst)))
    if options.cmio:
        args.append('--cmio')
        keys.append('cmio')
    keys.append(str(ninst))
    timings = {}
    for snapshot, tapefile, t2sopts in SNAPSHOTS:
        if tapefile:
            sf = f'{SKOOLKIT_HOME}/build/{snapshot}'
            if not os.path.isfile(sf):
                print(f'Building {snapshot}')
                with contextlib.redirect_stdout(io.StringIO()):
                    tap2sna.main((*t2sopts, tapefile, sf))
        else:
            sf = snapshot
        k = ':'.join(keys + [os.path.basename(snapshot)])
        run_trials(timings, k, options.nruns, run_trace_cmd, (trace, *args, sf))
    compare(timings, options)

parser = argparse.ArgumentParser(
    usage="%(prog)s [options] init|rzxplay|simulator|tap2sna|trace [before.txt]",
    description="Exercise (C)(CMIO)Simulator and collect timings. "
                "If the command is 'init', write a default configuration file if one is not already present. "
                "If before.txt is given, compare it with the collected timings (written to after.txt). "
                "Otherwise, write collected timings to a file named timings-HOSTNAME-TAG.txt, "
                "where TAG is a commit hash or (when -s is used) the SkoolKit version number.",
    add_help=False
)
parser.add_argument('cmd', help=argparse.SUPPRESS, nargs='?')
parser.add_argument('before', help=argparse.SUPPRESS, nargs='?')
group = parser.add_argument_group('Options')
group.add_argument('-c', action='store_true',
                   help='Use CSimulator.')
group.add_argument('--cmio', action='store_true',
                   help='Simulate memory and I/O contention and the MEMPTR register (simulator/trace only).')
group.add_argument('-i', dest='interrupts', action='store_true',
                   help='Execute interrupt routines (simulator only).')
group.add_argument('-n', dest='nruns', metavar='NUM', type=int, default=RUNS,
                   help=f'Number of runs per command (default: {RUNS}).')
group.add_argument('-s', dest='skoolkit', metavar='DIR', default=SKOOLKIT_HOME,
                   help=f'Use SkoolKit in this directory (default: {SKOOLKIT_HOME}).')
namespace, unknown_args = parser.parse_known_args()
if unknown_args or namespace.cmd not in ('init', 'rzxplay', 'simulator', 'tap2sna', 'trace'):
    parser.exit(2, parser.format_help())
if namespace.cmd == 'init':
    write_cfg()
elif namespace.cmd == 'rzxplay':
    run_rzxplay(namespace)
elif namespace.cmd == 'simulator':
    run_simulator(namespace)
elif namespace.cmd == 'tap2sna':
    run_tap2sna(namespace)
elif namespace.cmd == 'trace':
    run_trace(namespace)

