#!/usr/bin/env python3

import sys
import os
import time

# Use the current development version of SkoolKit
SKOOLKIT_HOME = os.environ.get('SKOOLKIT_HOME')
if not SKOOLKIT_HOME:
    sys.stderr.write('SKOOLKIT_HOME is not set; aborting\n')
    sys.exit(1)
if not os.path.isdir(SKOOLKIT_HOME):
    sys.stderr.write('SKOOLKIT_HOME={}; directory not found\n'.format(SKOOLKIT_HOME))
    sys.exit(1)
sys.path.insert(0, SKOOLKIT_HOME)

from skoolkit.image import ImageWriter
from skoolkit.skoolhtml import Udg, Frame

def write(line):
    sys.stdout.write(line + '\n')

def clock(method, *args, **kwargs):
    elapsed = []
    for n in range(3):
        start = time.time()
        method(*args, **kwargs)
        elapsed.append((time.time() - start) * 1000)

    trials = max((10, int(2000 / min(elapsed))))
    elapsed = []
    for n in range(trials):
        start = time.time()
        method(*args, **kwargs)
        elapsed.append((time.time() - start) * 1000)

    elapsed.sort()
    drop = len(elapsed) // 10
    keep = elapsed[drop:-drop]
    return sum(keep) / len(keep)

def get_method(iw, method):
    png_writer = iw.writers['png']
    if hasattr(png_writer, method):
        return getattr(iw, method)
    m_name = '_build_image_data_{}'.format(method)
    if hasattr(png_writer, m_name):
        return getattr(png_writer, m_name)
    sys.stderr.write('{}: method not found\n'.format(method))
    sys.exit(1)

def ua(a, b, c, d, t1, t2, t3, t4):
    """Solve the equations
         aN+bM=t1
         cN+dM=t3
    for N and M, and the equations
         aP+bQ=t2
         cP+dQ=t4
    for P and Q, and return i=(N-P)/(Q-M). (When u/a>i, the method with timings
    t1 and t3 is faster than the other method.)"""
    n = (d*t1-b*t3)/(a*d-b*c)
    m = (t1-a*n)/b
    p = (d*t2-b*t4)/(a*d-b*c)
    q = (t2-a*p)/b
    return n, m, p, q, (n-p)/(q-m)

def _get_attr_map(iw, udgs, scale):
    frame = Frame(udgs, scale)
    use_flash = True
    colours, attrs, flash_rect = iw._get_colours(frame, use_flash)
    palette, attr_map = iw._get_palette(colours, attrs, frame.has_trans)
    palette_size = len(palette) // 3
    if palette_size > 4:
        bit_depth = 4
    elif palette_size > 2:
        bit_depth = 2
    else:
        bit_depth = 1
    return bit_depth, attr_map

def _compare_methods(iw, method1, method2, udg_arrays, scales, mask_type, analyse_ua=False):
    m1 = get_method(iw, method1)
    m2 = get_method(iw, method2)
    write('{} v. {}:'.format(m1.__name__, m2.__name__))
    mask = iw.masks[mask_type]

    if analyse_ua:
        for scale in scales:
            write('  scale={}:'.format(scale))
            ua_params = []
            timings = []
            for udgs in udg_arrays:
                frame = Frame(udgs, scale, mask_type)
                bit_depth, attr_map = _get_attr_map(iw, udgs, scale)
                frame.attr_map = attr_map
                num_udgs = len(udgs[0]) * len(udgs)
                num_attrs = len(attr_map)
                ua_params.append(num_attrs)
                ua_params.append(num_udgs)
                t1 = clock(m1, frame, bit_depth=bit_depth, mask=mask)
                t2 = clock(m2, frame, bit_depth=bit_depth, mask=mask)
                timings.append(t1)
                timings.append(t2)
                write('    num_udgs={}, num_attrs={}: {:0.2f}ms {:0.2f}ms'.format(num_udgs, num_attrs, t1, t2))
            n, m, p, q, index = ua(*(ua_params + timings))
            write('    {}: {:0.4f}a+{:0.4f}u'.format(method1, n, m))
            write('    {}: {:0.4f}a+{:0.4f}u'.format(method2, p, q))
            symbol = '<' if m - q > 0 else '>'
            write('    {} is faster than {} when u/a {} {:0.4f}'.format(method1, method2, symbol, index))
    else:
        method1_faster = []
        for udgs in udg_arrays:
            for scale in scales:
                frame = Frame(udgs, scale, mask_type)
                bit_depth, attr_map = _get_attr_map(iw, udgs, scale)
                frame.attr_map = attr_map
                t1 = clock(m1, frame, bit_depth=bit_depth, mask=mask)
                t2 = clock(m2, frame, bit_depth=bit_depth, mask=mask)
                num_udgs = len(udgs[0]) * len(udgs)
                num_attrs = len(attr_map)
                output = '  num_udgs={}, num_attrs={}, scale={}: {:0.3f}ms {:0.3f}ms'.format(num_udgs, num_attrs, scale, t1, t2)
                write(output)
                if t1 < t2:
                    method1_faster.append(output)
        if method1_faster:
            write('{} is faster than {} when:'.format(method1, method2))
            for output in method1_faster:
                write(output)
        else:
            write('{} is slower than {} for all UDG arrays tested'.format(method1, method2))

def bd4(iw, method1, method2, udg_arrays, scales):
    mask_type = 0
    analyse_ua = len(udg_arrays) == 2

    if not udg_arrays:
        analyse_ua = True
        udg_arrays = []
        udg_arrays.append([[Udg(i, (240,) * 8) for i in range(16)]] * 64)  # u=1024, a=16
        udg_arrays.append([[Udg(i, (240,) * 8) for i in range(24)]] * 128) # u=3072, a=24

    scales = scales or (1, 2, 3, 4)

    _compare_methods(iw, method1, method2, udg_arrays, scales, mask_type, analyse_ua)

def bd2(iw, method1, method2, udg_arrays, scales, masked=False):
    mask_type = 0
    udg_arrays = udg_arrays or []

    if masked:
        mask_type = 1
        if not udg_arrays:
            data = (240,) * 8
            mask_data = (247,) * 8
            udg_arrays.append([[Udg(56, data, mask_data)] * 3] * 5)
            udg_arrays.append([[Udg(56, data, mask_data)] * 3] * 4)
    elif not udg_arrays:
        data = (170,) * 8
        udg_arrays.append([[Udg(a, data) for a in (1, 19)]])           # u=2, a=2
        udg_arrays.append([[Udg(a, data) for a in (1, 19, 19)]])       # u=3, a=2
        udg_arrays.append([[Udg(a, data) for a in (1, 19, 1, 19)]])    # u=4, a=2
        udg_arrays.append([[Udg(a, data) for a in (1, 19, 1, 19, 1)]]) # u=5, a=2
        udg_arrays.append([[Udg(a, data) for a in (1, 8, 19)]])        # u=3, a=3
        udg_arrays.append([[Udg(a, data) for a in (1, 8, 19, 1)]])     # u=4, a=3
        udg_arrays.append([[Udg(a, data) for a in (1, 8, 19, 1, 8)]])  # u=5, a=3
        udg_arrays.append([[Udg(a, data) for a in (1, 8, 19, 26)]])    # u=4, a=4
        udg_arrays.append([[Udg(a, data) for a in (1, 8, 19, 26, 1)]]) # u=5, a=4

    scales = scales or (1, 2, 3, 4, 5)

    _compare_methods(iw, method1, method2, udg_arrays, scales, mask_type)

def bd1(iw, method1, method2, udg_arrays, scales, one_udg=False):
    udg_arrays = udg_arrays or []

    if one_udg:
        if not udg_arrays:
            udg_arrays.append([[Udg(56, (170,) * 8)]])
    elif not udg_arrays:
        attrs = (56, 7, 0, 63)
        for num_udgs in range(1, 10):
            for num_attrs in range(1, min(num_udgs, 4) + 1):
                udg_arrays.append([[Udg(attrs[i % num_attrs], (170,) * 8) for i in range(num_udgs)]])

    scales = scales or (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13)

    _compare_methods(iw, method1, method2, udg_arrays, scales, mask_type=0)

def bd1_1udg(iw, method1, method2, udg_arrays, scales):
    bd1(iw, method1, method2, udg_arrays, scales, one_udg=True)

def bd2_at(iw, method1, method2, udg_arrays, scales):
    bd2(iw, method1, method2, udg_arrays, scales, masked=True)

METHODS = (
    ('bd4_nt1', 'bd4_nt2', bd4),
    ('bd_any', 'bd4_nt1', bd4),
    ('bd_any', 'bd4_nt2', bd4),
    ('bd12', 'bd2_at', bd2_at),
    ('bd12', 'bd2_nt', bd2),
    ('bd_any', 'bd12', bd2),
    ('bd_any', 'bd2_at', bd2_at),
    ('bd_any', 'bd2_nt', bd2),
    ('bd12', 'bd1_nt', bd1),
    ('bd12', 'bd1_nt_1udg', bd1_1udg),
    ('bd1_nt', 'bd1_nt_1udg', bd1_1udg),
    ('bd_any', 'bd1_nt', bd1),
    ('bd_any', 'bd1_nt_1udg', bd1_1udg)
)

def time_methods(method1_name, method2_name, udg_arrays, scale):
    for name1, name2, f in METHODS:
        if set((name1, name2)) == set((method1_name, method2_name)):
            f(ImageWriter(), name1, name2, udg_arrays, scale)
            break
    else:
        write('{} v. {}: not implemented'.format(method1_name, method2_name))

def list_methods():
    prefix = '_build_image_data_'
    methods = []
    iw = ImageWriter()
    png_writer = iw.writers['png']
    for attr in dir(png_writer):
        if attr.startswith(prefix) and not attr.endswith('_bd0'):
            methods.append(attr)
    max_len = max([len(m) for m in methods]) - len(prefix)
    for m in methods:
        write('{} ({})'.format(m[len(prefix):].ljust(max_len), m))
    sys.exit()

def parse_args(args):
    p_args = []
    run_all = False
    udgs = []
    scales = ()
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == '-a':
            run_all = True
        elif arg == '-l':
            list_methods()
        elif arg == '-u':
            udgs.append(args[i + 1])
            i += 1
        elif arg == '-s':
            scales = [int(j) for j in args[i + 1].split(',')]
            i += 1
        elif arg.startswith('-'):
            show_usage()
        else:
            p_args.append(arg)
        i += 1
    if run_all:
        if p_args:
            show_usage()
        else:
            p_args = (None, None)
    if len(p_args) != 2:
        show_usage()
    return p_args[0], p_args[1], run_all, udgs, scales

def show_usage():
    sys.stderr.write("""Usage:
    {0} -a
    {0} -l
    {0} [options] METHOD1 METHOD2

  Compare the performance of two PngWriter._build_image* methods in the current
  development version of SkoolKit.

Available options:
  -a                      Run all method comparisons
  -l                      List methods available on PngWriter
  -s s1[,s2...]           Compare methods using these scales
  -u '[[Udg(...), ... ]'  Compare methods using this UDG array; this option may
                          be used multiple times
""".format(os.path.basename(sys.argv[0])))
    sys.exit()

###############################################################################
# Begin
###############################################################################
method1_name, method2_name, run_all, udgs, scales = parse_args(sys.argv[1:])
udg_arrays = tuple([eval(udg_array) for udg_array in udgs])
if run_all:
    for name1, name2, f in METHODS:
        time_methods(name1, name2, udg_arrays, scales)
        write('')
else:
    time_methods(method1_name, method2_name, udg_arrays, scales)
