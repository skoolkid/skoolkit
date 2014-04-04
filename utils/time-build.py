#!/usr/bin/env python
import sys
import os
import time
import textwrap

# Use the current development version of SkoolKit
SKOOLKIT_HOME = os.environ.get('SKOOLKIT_HOME')
if not SKOOLKIT_HOME:
    sys.stderr.write('SKOOLKIT_HOME is not set; aborting\n')
    sys.exit(1)
if not os.path.isdir(SKOOLKIT_HOME):
    sys.stderr.write('SKOOLKIT_HOME=%s; directory not found\n' % SKOOLKIT_HOME)
    sys.exit(1)
sys.path.insert(0, SKOOLKIT_HOME)

from skoolkit.image import ImageWriter
from skoolkit.skoolhtml import Udg, Frame

def write(line):
    sys.stdout.write('%s\n' % line)

def clock(method, *args):
    elapsed = []
    for n in range(3):
        start = time.time()
        method(*args)
        elapsed.append((time.time() - start) * 1000)

    trials = max((10, int(2000 / min(elapsed))))
    elapsed = []
    for n in range(trials):
        start = time.time()
        method(*args)
        elapsed.append((time.time() - start) * 1000)

    elapsed.sort()
    drop = len(elapsed) // 10
    keep = elapsed[drop:-drop]
    return sum(keep) / len(keep)

def get_method(iw, method):
    png_writer = iw.writers['png']
    if hasattr(png_writer, method):
        return getattr(iw, method)
    m_name = '_build_image_data_%s' % method
    if hasattr(png_writer, m_name):
        return getattr(png_writer, m_name)
    sys.stderr.write('%s: method not found\n' % method)
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
    palette, attr_map = iw._get_palette(colours, attrs, frame.trans)
    return attr_map

def bd4(iw, method1, method2, show_timings, udgs, scale=1):
    m1 = get_method(iw, method1)
    m2 = get_method(iw, method2)
    mask = iw.masks[0]

    if udgs:
        write('%s.%s v. %s (scale=%i):' % (iw.__class__.__name__, m1.__name__, m2.__name__, scale))
        width = len(udgs[0]) * 8 * scale
        height = len(udgs) * 8 * scale
        attr_map = _get_attr_map(iw, udgs, scale)
        t1 = clock(m1, udgs, scale, attr_map, False, False, 0, 0, width, height, 4, mask)
        t2 = clock(m2, udgs, scale, attr_map, False, False, 0, 0, width, height, 4, mask)
        write('%s: %0.4fms' % (method1, t1))
        write('%s: %0.4fms' % (method2, t2))
        return

    info = '%s.%s v. %s:' % (iw.__class__.__name__, m1.__name__, m2.__name__)
    for line in textwrap.wrap(info):
        write(line)

    udgs1 = [[Udg(i, (240,) * 8) for i in range(16)]] * 16 # u=256, a=16
    udgs2 = [[Udg(i, (240,) * 8) for i in range(24)]] * 24 # u=576, a=24

    for scale in (1, 2, 3, 4):
        write('  scale=%i' % scale)
        timings = [16, 256, 24, 576]
        for udgs in (udgs1, udgs2):
            width = len(udgs[0]) * 8 * scale
            height = len(udgs) * 8 * scale
            attr_map = _get_attr_map(iw, udgs, scale)
            timings.append(clock(m1, udgs, scale, attr_map, False, False, 0, 0, width, height, 4, mask))
            timings.append(clock(m2, udgs, scale, attr_map, False, False, 0, 0, width, height, 4, mask))
        n, m, p, q, index = ua(*timings)
        if show_timings:
            write('    %s: %0.4fms, %0.4fms; %0.4fa+%0.4fu' % (method1, timings[-4], timings[-2], n, m))
            write('    %s: %0.4fms, %0.4fms; %0.4fa+%0.4fu' % (method2, timings[-3], timings[-1], p, q))
        symbol = '<' if m - q > 0 else '>'
        write('    %s is faster than %s when u/a %s %0.4f' % (method1, method2, symbol, index))

def bd2(iw, method1, method2, show_timings, udgs, scale=1):
    m1 = get_method(iw, method1)
    m2 = get_method(iw, method2)
    mask = iw.masks[0]

    if udgs:
        write('%s.%s v. %s (scale=%i):' % (iw.__class__.__name__, m1.__name__, m2.__name__, scale))
        width = len(udgs[0]) * 8 * scale
        height = len(udgs) * 8 * scale
        attr_map = _get_attr_map(iw, udgs, scale)
        t1 = clock(m1, udgs, scale, attr_map, False, False, 0, 0, width, height, 2, mask)
        t2 = clock(m2, udgs, scale, attr_map, False, False, 0, 0, width, height, 2, mask)
        write('  %s: %0.4fms' % (method1, t1))
        write('  %s: %0.4fms' % (method2, t2))
        return

    info = '%s.%s v. %s:' % (iw.__class__.__name__, m1.__name__, m2.__name__)
    for line in textwrap.wrap(info):
        write(line)

    udgs1 = [[Udg(i, (255,) * 8) for i in range(4)] * 4] * 16 # u=256, a=4
    udgs2 = [[Udg(i, (240,) * 8) for i in (1, 19)] * 12] * 24 # u=576, a=2

    for scale in (1, 2, 3, 4, 5):
        write('  scale=%i' % scale)
        timings = [4, 256, 2, 576]
        for udgs in (udgs1, udgs2):
            width = len(udgs[0]) * 8 * scale
            height = len(udgs) * 8 * scale
            attr_map = _get_attr_map(iw, udgs, scale)
            timings.append(clock(m1, udgs, scale, attr_map, False, False, 0, 0, width, height, 2, mask))
            timings.append(clock(m2, udgs, scale, attr_map, False, False, 0, 0, width, height, 2, mask))
        n, m, p, q, index = ua(*timings)
        if show_timings:
            write('    %s: %0.4fms, %0.4fms; %0.4fa+%0.4fu' % (method1, timings[-4], timings[-2], n, m))
            write('    %s: %0.4fms, %0.4fms; %0.4fa+%0.4fu' % (method2, timings[-3], timings[-1], p, q))
        symbol = '<' if m - q > 0 else '>'
        write('    %s is faster than %s when u/a %s %0.4f' % (method1, method2, symbol, index))

def bd1(iw, method1, method2, udgs, scale=1):
    m1 = get_method(iw, method1)
    m2 = get_method(iw, method2)
    mask = iw.masks[0]

    write('%s.%s v. %s (scale=%i):' % (iw.__class__.__name__, m1.__name__, m2.__name__, scale))

    if udgs:
        width = len(udgs[0]) * 8 * scale
        height = len(udgs) * 8 * scale
        attr_map = _get_attr_map(iw, udgs, scale)
        t1 = clock(m1, udgs, scale, attr_map, False, False, 0, 0, width, height, 1, mask)
        t2 = clock(m2, udgs, scale, attr_map, False, False, 0, 0, width, height, 1, mask)
        write('  %s: %0.4fms' % (method1, t1))
        write('  %s: %0.4fms' % (method2, t2))
        return

    udg_arrays = []
    udg_arrays.append([[Udg(56, (240,) * 8)]]) # u=1, a=1
    udg_arrays.append([[Udg(56, (240,) * 8)] * 2]) # u=2, a=1
    udg_arrays.append([[Udg(56, (0,) * 8), Udg(7, (0,) * 8)]]) # u=2, a=2
    udg_arrays.append([[Udg(56, (240,) * 8)] * 3]) # u=3, a=1
    udg_arrays.append([[Udg(56, (0,) * 8), Udg(7, (0,) * 8), Udg(56, (0,) * 8)]]) # u=3, a=2
    udg_arrays.append([[Udg(56, (0,) * 8), Udg(7, (0,) * 8), Udg(0, (0,) * 8)]]) # u=3, a=3

    scale = 1
    for udgs in udg_arrays:
        for scale in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13):
            width = len(udgs[0]) * 8 * scale
            height = len(udgs) * 8 * scale
            attr_map = _get_attr_map(iw, udgs, scale)
            t1 = clock(m1, udgs, scale, attr_map, False, False, 0, 0, width, height, 1, mask)
            t2 = clock(m2, udgs, scale, attr_map, False, False, 0, 0, width, height, 1, mask)
            write('  num_udgs=%i, num_attrs=%i, scale=%i' % (len(udgs[0]) * len(udgs), len(attr_map), scale))
            write('    %s: %0.2fms' % (method1, t1))
            write('    %s: %0.2fms' % (method2, t2))

def list_methods():
    prefix = '_build_image_data_'
    methods = []
    iw = ImageWriter()
    png_writer = iw.writers['png']
    for attr in dir(png_writer):
        if attr.startswith(prefix):
            methods.append(attr)
    max_len = max([len(m) for m in methods]) - len(prefix)
    for m in methods:
        write('%s (%s)' % (m[len(prefix):].ljust(max_len), m))
    sys.exit()

def parse_args(args):
    p_args = []
    show_timings = False
    udgs = None
    scale = 1
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == '-l':
            list_methods()
        elif arg == '-t':
            show_timings = True
        elif arg == '-u':
            udgs = args[i + 1]
            i += 1
        elif arg == '-s':
            scale = int(args[i + 1])
            i += 1
        elif arg.startswith('-'):
            show_usage()
        else:
            p_args.append(arg)
        i += 1
    if len(p_args) != 3:
        show_usage()
    return p_args[0], p_args[1], int(p_args[2]), show_timings, udgs, scale

def show_usage():
    sys.stderr.write("""Usage:
    {0} -l
    {0} [options] METHOD1 METHOD2 DEPTH

  Compare the performance of two PngWriter._build_image* methods in the current
  development version of SkoolKit. DEPTH must be 1, 2 or 4.

Available options:
  -l        List methods available on PngWriter
  -t        Show timings (when DEPTH > 1)
  -u UDGS   Compare methods using this UDG array
  -s SCALE  Set the scale of the image (use with -u)
""".format(os.path.basename(sys.argv[0])))
    sys.exit()

###############################################################################
# Begin
###############################################################################
method1, method2, bit_depth, show_timings, udgs, scale = parse_args(sys.argv[1:])
iw = ImageWriter()
udg_array = eval(udgs) if udgs else None
if bit_depth == 4:
    bd4(iw, method1, method2, show_timings, udg_array, scale)
elif bit_depth == 2:
    bd2(iw, method1, method2, show_timings, udg_array, scale)
elif bit_depth == 1:
    bd1(iw, method1, method2, udg_array, scale)
