from configparser import ConfigParser
import os
import sys

RED = '\033[31m'
GREEN = '\033[32m'
RESET = '\033[0m'

DEF = {
    'runs': 5,
    'run_threshold': 1.1, # Max time must be less than this * min time
    'cp_threshold': 2,    # Highlight before/after times that differ by more than this %
    'frames_python': 2500,
    'frames_c': 100000,
    'halts_python': 4096,
    'halts_c': 65536,
    'instructions_python': 10000000,
    'instructions_c': 500000000,
}

cfgfile = 'simperf.cfg'
if not os.path.isfile(cfgfile):
    cfg = ConfigParser()
    cfg['simperf'] = {k: DEF[k] for k in ('runs', 'run_threshold', 'cp_threshold')}
    cfg['rzxplay'] = {k: DEF[k] for k in ('frames_python', 'frames_c')}
    cfg['simulator'] = {k: DEF[k] for k in ('halts_python', 'halts_c')}
    cfg['trace'] = {k: DEF[k] for k in ('instructions_python', 'instructions_c')}
    with open(cfgfile, 'w') as f:
        cfg.write(f)
cfg = ConfigParser()
cfg.read(cfgfile)

RUNS = cfg.getint('simperf', 'runs', fallback=DEF['runs'])
RUN_THRESHOLD = cfg.getfloat('simperf', 'run_threshold', fallback=DEF['run_threshold'])
CP_THRESHOLD = cfg.getint('simperf', 'cp_threshold', fallback=DEF['cp_threshold'])
FRAMES_PYTHON = cfg.getint('rzxplay', 'frames_python', fallback=DEF['frames_python'])
FRAMES_C = cfg.getint('rzxplay', 'frames_c', fallback=DEF['frames_c'])
HALTS_PYTHON = cfg.getint('simulator', 'halts_python', fallback=DEF['halts_python'])
HALTS_C = cfg.getint('simulator', 'halts_c', fallback=DEF['halts_c'])
INSTRUCTIONS_PYTHON = cfg.getint('trace', 'instructions_python', fallback=DEF['instructions_python'])
INSTRUCTIONS_C = cfg.getint('trace', 'instructions_c', fallback=DEF['instructions_c'])

def read_timings(fname):
    timings = {}
    with open(fname) as f:
        for line in f:
            parts = line.strip().split(' | ')
            timings[parts[0]] = [float(f) for f in parts[1].split()]
    return timings

def write_timings(timings, fname):
    with open(fname, 'w') as f:
        for k in sorted(timings):
            f.write('{} | {}\n'.format(k, ' '.join(str(t) for t in timings[k])))

def _compose_line(b, a, d, desc):
    if d < -CP_THRESHOLD:
        colour = RED
    elif d > CP_THRESHOLD:
        colour = GREEN
    else:
        colour = ''
    return f'  {colour}{b:.3f} -> {a:.3f} {d:+.1f}% ({desc}){RESET}'

def _compute_pc_diff(before, after):
    return (before / after - 1) * 100

def print_comparison(before, after, show_faster=False, show_slower=False, key=None):
    lines = []
    for k, at in after.items():
        if key and not k.startswith(key):
            continue
        bt = before.get(k)
        if not bt:
            print(f'WARNING: Key "{k}" not found', file=sys.stderr)
            continue
        bmin, bmax = min(bt), max(bt)
        amin, amax = min(at), max(at)
        dmin = _compute_pc_diff(bmin, amin)
        bmean = sum(bt) / len(bt)
        amean = sum(at) / len(at)
        dmean = _compute_pc_diff(bmean, amean)
        btmean = (sum(bt) - bmin - bmax) / (len(bt) - 2)
        atmean = (sum(at) - amin - amax) / (len(at) - 2)
        dtmean = _compute_pc_diff(btmean, atmean)
        show = True
        if show_faster:
            show = any(d > CP_THRESHOLD for d in (dmin, dmean, dtmean))
        elif show_slower:
            show = any(d < -CP_THRESHOLD for d in (dmin, dmean, dtmean))
        if show:
            lines.append(f'{k}:')
            lines.append(_compose_line(bmin, amin, dmin, 'min'))
            lines.append(_compose_line(bmean, amean, dmean, 'mean'))
            lines.append(_compose_line(btmean, atmean, dtmean, 'trimmed mean'))
    for line in lines:
        print(line)
    return lines
