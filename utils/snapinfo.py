#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import argparse

SKOOLKIT_HOME = os.environ.get('SKOOLKIT_HOME')
if SKOOLKIT_HOME:
    if not os.path.isdir(SKOOLKIT_HOME):
        sys.stderr.write('SKOOLKIT_HOME={}: directory not found\n'.format(SKOOLKIT_HOME))
        sys.exit(1)
    sys.path.insert(0, SKOOLKIT_HOME)
else:
    try:
        import skoolkit
    except ImportError:
        sys.stderr.write('Error: SKOOLKIT_HOME is not set, and SkoolKit is not installed\n')
        sys.exit(1)

from skoolkit.snapshot import get_snapshot
from skoolkit import get_int_param

# http://www.worldofspectrum.org/faq/reference/z80format.htm
# http://www.worldofspectrum.org/faq/reference/128kreference.htm

BLOCK_ADDRESSES_48K = {
    4: '32768-49151',
    5: '49152-65535',
    8: '16384-32767'
}

BLOCK_ADDRESSES_128K = {
    5: '32768-49151',
    8: '16384-32767'
}

V2_MACHINES = {
    0: ('48K Spectrum', '16K Spectrum', True),
    1: ('48K Spectrum + IF1', '16K Spectrum + IF1', True),
    2: ('SamRam', 'SamRam', False),
    3: ('128K Spectrum', 'Spectrum +2', False),
    4: ('128K Spectrum + IF1', 'Spectrum +2 + IF1', False)
}

V3_MACHINES = {
    0: ('48K Spectrum', '16K Spectrum', True),
    1: ('48K Spectrum + IF1', '16K Spectrum + IF1', True),
    2: ('SamRam', 'SamRam', False),
    3: ('48K Spectrum + MGT', '16K Spectrum + MGT', True),
    4: ('128K Spectrum', 'Spectrum +2', False),
    5: ('128K Spectrum + IF1', 'Spectrum +2 + IF1', False),
    6: ('128K Spectrum + MGT' 'Spectrum +2 + MGT', False),
}

MACHINES = {
    7: ('Spectrum +3', 'Spectrum +2A', False),
    8: ('Spectrum +3', 'Spectrum +2A', False),
    9: ('Pentagon (128K)', 'Pentagon (128K)', False),
    10: ('Scorpion (256K)', 'Scorpion (256K)', False),
    11: ('Didaktik+Kompakt', 'Didaktik+Kompakt', False),
    12: ('Spectrum +2', 'Spectrum +2', False),
    13: ('Spectrum +2A', 'Spectrum +2A', False),
    14: ('TC2048', 'TC2048', False),
    15: ('TC2068', 'TC2068', False),
    128: ('TS2068', 'TS2068', False),
}

TOKENS = {
    165: 'RND',
    166: 'INKEY$',
    167: 'PI',
    168: 'FN',
    169: 'POINT',
    170: 'SCREEN$',
    171: 'ATTR',
    172: 'AT',
    173: 'TAB',
    174: 'VAL$',
    175: 'CODE',
    176: 'VAL',
    177: 'LEN',
    178: 'SIN',
    179: 'COS',
    180: 'TAN',
    181: 'ASN',
    182: 'ACS',
    183: 'ATN',
    184: 'LN',
    185: 'EXP',
    186: 'INT',
    187: 'SQR',
    188: 'SGN',
    189: 'ABS',
    190: 'PEEK',
    191: 'IN',
    192: 'USR',
    193: 'STR$',
    194: 'CHR$',
    195: 'NOT',
    196: 'BIN',
    197: 'OR',
    198: 'AND',
    199: '<=',
    200: '>=',
    201: '<>',
    202: 'LINE',
    203: 'THEN',
    204: 'TO',
    205: 'STEP',
    206: 'DEF FN',
    207: 'CAT',
    208: 'FORMAT',
    209: 'MOVE',
    210: 'ERASE',
    211: 'OPEN #',
    212: 'CLOSE #',
    213: 'MERGE',
    214: 'VERIFY',
    215: 'BEEP',
    216: 'CIRCLE',
    217: 'INK',
    218: 'PAPER',
    219: 'FLASH',
    220: 'BRIGHT',
    221: 'INVERSE',
    222: 'OVER',
    223: 'OUT',
    224: 'LPRINT',
    225: 'LLIST',
    226: 'STOP',
    227: 'READ',
    228: 'DATA',
    229: 'RESTORE',
    230: 'NEW',
    231: 'BORDER',
    232: 'CONTINUE',
    233: 'DIM',
    234: 'REM',
    235: 'FOR',
    236: 'GO TO',
    237: 'GO SUB',
    238: 'INPUT',
    239: 'LOAD',
    240: 'LIST',
    241: 'LET',
    242: 'PAUSE',
    243: 'NEXT',
    244: 'POKE',
    245: 'PRINT',
    246: 'PLOT',
    247: 'RUN',
    248: 'SAVE',
    249: 'RANDOMIZE',
    250: 'IF',
    251: 'CLS',
    252: 'DRAW',
    253: 'CLEAR',
    254: 'RETURN',
    255: 'COPY'
}

class BasicLister:
    def list_basic(self, snapshot):
        self.snapshot = snapshot
        i = (snapshot[23635] + 256 * snapshot[23636]) or 23755
        while i < len(snapshot) and snapshot[i] < 64:
            self._write('{: 4} '.format(snapshot[i] * 256 + snapshot[i + 1]))
            self.lspace = False
            i = self._print_basic_line(i + 4)

    def _print_basic_line(self, i):
        while self.snapshot[i] != 13:
            if self.snapshot[i] == 14:
                self._write(self._get_fp_num(i))
                i += 6
            else:
                self._write(self._get_chars(self.snapshot[i]))
                i += 1
        self._write('\n')
        return i + 1

    def _get_chars(self, code):
        if code <= 32:
            self.lspace = False
            return self._get_char(code)
        if code <= 164:
            self.lspace = True
            return self._get_char(code)
        return self._get_token(code)

    def _get_fp_num(self, i):
        j = i - 1
        num_str = ''
        while chr(self.snapshot[j]) in '0123456789.':
            num_str = chr(self.snapshot[j]) + num_str
            j -= 1
        if num_str:
            if self.snapshot[i + 1] == 0:
                sign = -1 if self.snapshot[i + 2] else 1
                num = sign * get_word(self.snapshot, i + 3)
            else:
                exponent = self.snapshot[i + 1] - 160
                sign = -1 if self.snapshot[i + 2] & 128 else 1
                mantissa = float(16777216 * (self.snapshot[i + 2] | 128)
                                 + 65536 * self.snapshot[i + 3]
                                 + 256 * self.snapshot[i + 4]
                                 + self.snapshot[i + 5])
                num = sign * mantissa * (2 ** exponent)
            if num and abs(1 - float(num_str) / num) > 1e-10:
                return '{{{}}}'.format(num)
        return ''

    def _get_char(self, code):
        if code == 94:
            return '↑'
        if code == 96:
            return '£'
        if code == 127:
            return '©'
        if 32 <= code <= 126:
            return chr(code)
        return '{{0x{:02X}}}'.format(code)

    def _get_token(self, code):
        token = TOKENS[code]
        if self.lspace and code >= 197 and token[0] >= 'A':
            token = ' ' + token
        self.lspace = True
        if code < 168 or code == 203 or token[-1] in '#=>':
            # RND, INKEY$, PI, THEN, '<=', '>=', '<>', 'OPEN #', 'CLOSE #'
            return token
        return token + ' '

    def _write(self, text):
        sys.stdout.write(text)

def get_word(data, index):
    return data[index] + 256 * data[index + 1]

def to_binary(b):
    return '{:08b}'.format(b)

def analyse_z80(z80file):
    # Read the Z80 file
    with open(z80file, 'rb') as f:
        data = bytearray(f.read())

    # Extract header and RAM block(s)
    if get_word(data, 6) > 0:
        version = 1
        header = data[:30]
        ram_blocks = data[30:]
    else:
        header_len = 32 + get_word(data, 30)
        header = data[:header_len]
        ram_blocks = data[header_len:]
        version = 2 if header_len == 55 else 3

    # Print file name, version, machine, interrupt status, border, port $7FFD
    print('Z80 file: {}'.format(z80file))
    print('Version: {}'.format(version))
    bank = None
    if version == 1:
        machine = '48K Spectrum'
        block_dict = BLOCK_ADDRESSES_48K
    else:
        machine_dict = V2_MACHINES if version == 2 else V3_MACHINES
        machine_id = header[34]
        index = header[37] // 128
        machine_spec = machine_dict.get(machine_id, MACHINES.get(machine_id, ('Unknown', 'Unknown')))
        machine = machine_spec[index]
        if machine_spec[2]:
            block_dict = BLOCK_ADDRESSES_48K
        else:
            block_dict = BLOCK_ADDRESSES_128K
            bank = header[35] & 7
    print('Machine: {}'.format(machine))
    print('Interrupts: {}abled'.format('en' if header[27] else 'dis'))
    print('Interrupt mode: {}'.format(header[29] & 3))
    print('Border: {}'.format((header[12] // 2) & 7))
    if bank is not None:
        print('Port $7FFD: {} - bank {} (block {}) paged into 49152-65535'.format(header[35], bank, bank + 3))

    # Print register contents
    width = 11
    flags = "SZ5H3PNC"
    print('Registers:')
    if version == 1:
        print('  PC={}'.format(get_word(header, 6)))
    else:
        print('  PC={}'.format(get_word(header, 32)))
    print('  SP={}'.format(get_word(header, 8)))
    print('  I={}'.format(header[10]))
    print('  R={}'.format(header[11]))
    print("  {} A'={}".format('A={}'.format(header[0]).ljust(width), header[21]))
    print("    {}    {}".format(flags.ljust(width - 2), flags))
    print("  {} F'={}".format('F={}'.format(to_binary(header[1])).ljust(width), to_binary(header[22])))
    print("  {} B'={}".format('B={}'.format(header[3]).ljust(width), header[16]))
    print("  {} C'={}".format('C={}'.format(header[2]).ljust(width), header[15]))
    print("  {} D'={}".format('D={}'.format(header[14]).ljust(width), header[18]))
    print("  {} E'={}".format('E={}'.format(header[13]).ljust(width), header[17]))
    print("  {} H'={}".format('H={}'.format(header[5]).ljust(width), header[20]))
    print("  {} L'={}".format('L={}'.format(header[4]).ljust(width), header[19]))
    print('  IX={}'.format(get_word(header, 25)))
    print('  IY={}'.format(get_word(header, 23)))

    # Print RAM block info
    if version == 1:
        block_len = len(ram_blocks)
        prefix = '' if header[12] & 32 else 'un'
        print('48K RAM block (16384-65535): {} bytes ({}compressed)'.format(block_len, prefix))
    else:
        i = 0
        while i < len(ram_blocks):
            block_len = get_word(ram_blocks, i)
            page_num = ram_blocks[i + 2]
            addr_range = block_dict.get(page_num)
            if addr_range is None:
                if page_num == bank + 3:
                    addr_range = '49152-65535'
            if addr_range:
                addr_range = ' ({})'.format(addr_range)
            else:
                addr_range = ''
            i += 3
            if block_len == 65535:
                block_len = 16384
                prefix = 'un'
            else:
                prefix = ''
            print('RAM block {}{}: {} bytes ({}compressed)'.format(page_num, addr_range, block_len, prefix))
            i += block_len

###############################################################################

# http://www.spectaculator.com/docs/zx-state/intro.shtml

SZX_MACHINES = {
    0: '16K ZX Spectrum',
    1: '48K ZX Spectrum',
    2: 'ZX Spectrum 128',
    3: 'ZX Spectrum +2',
    4: 'ZX Spectrum +2A/+2B',
    5: 'ZX Spectrum +3',
    6: 'ZX Spectrum +3e'
}

def get_block_id(data, index):
    return ''.join([chr(b) for b in data[index:index+ 4]])

def get_dword(data, index):
    return data[index] + 256 * data[index + 1] + 65536 * data[index + 2] + 16777216 * data[index + 3]

def print_ramp(block, variables):
    lines = []
    flags = get_word(block, 0)
    compressed = 'compressed' if flags & 1 else 'uncompressed'
    page = block[2]
    ram = block[3:]
    lines.append("Page: {}".format(page))
    machine_id = variables['chMachineId']
    addresses = ''
    if page == 5:
        addresses = '16384-32767'
    elif page == 2:
        addresses = '32768-49151'
    elif machine_id > 1 and page == variables['ch7ffd'] & 7:
        addresses = '49152-65535'
    if addresses:
        addresses += ' - '
    lines.append("RAM: {}{} bytes, {}".format(addresses, len(ram), compressed))
    return lines

def print_spcr(block, variables):
    lines = []
    lines.append('Border: {}'.format(block[0]))
    ch7ffd = block[1]
    variables['ch7ffd'] = ch7ffd
    bank = ch7ffd & 7
    lines.append('Port $7FFD: {} (bank {} paged into 49152-65535)'.format(ch7ffd, bank))
    return lines

def print_z80r(block, variables):
    lines = []
    width = 11
    flags = "SZ5H3PNC"
    lines.append('Interrupts: {}abled'.format('en' if block[27] else 'dis'))
    lines.append('Interrupt mode: {}'.format(block[28]))
    lines.append('PC={}'.format(get_word(block, 22)))
    lines.append('SP={}'.format(get_word(block, 20)))
    lines.append('I={}'.format(block[24]))
    lines.append('R={}'.format(block[25]))
    lines.append("{} A'={}".format('A={}'.format(block[9]).ljust(width), block[1]))
    lines.append("  {}    {}".format(flags.ljust(width - 2), flags))
    lines.append("{} F'={}".format('F={}'.format(to_binary(block[8])).ljust(width), to_binary(block[0])))
    lines.append("{} B'={}".format('B={}'.format(block[11]).ljust(width), block[3]))
    lines.append("{} C'={}".format('C={}'.format(block[10]).ljust(width), block[2]))
    lines.append("{} D'={}".format('D={}'.format(block[13]).ljust(width), block[5]))
    lines.append("{} E'={}".format('E={}'.format(block[12]).ljust(width), block[4]))
    lines.append("{} H'={}".format('H={}'.format(block[15]).ljust(width), block[7]))
    lines.append("{} L'={}".format('L={}'.format(block[14]).ljust(width), block[6]))
    lines.append('IX={}'.format(get_word(block, 16)))
    lines.append('IY={}'.format(get_word(block, 18)))
    return lines

SZX_BLOCK_PRINTERS = {
    'RAMP': print_ramp,
    'SPCR': print_spcr,
    'Z80R': print_z80r
}

def analyse_szx(szxfile):
    with open(szxfile, 'rb') as f:
        szx = bytearray(f.read())

    magic = get_block_id(szx, 0)
    if magic != 'ZXST':
        sys.stderr.write("{} is not an SZX file\n".format(namespace.szxfile))
        sys.exit(1)

    print('Version: {}.{}'.format(szx[4], szx[5]))
    machine_id = szx[6]
    print('Machine: {}'.format(SZX_MACHINES.get(machine_id, 'Unknown')))
    variables = {'chMachineId': machine_id}

    i = 8
    while i < len(szx):
        block_id = get_block_id(szx, i)
        block_size = get_dword(szx, i + 4)
        i += 8
        print('{}: {} bytes'.format(block_id, block_size))
        printer = SZX_BLOCK_PRINTERS.get(block_id)
        if printer:
            for line in printer(szx[i:i + block_size], variables):
                print("  " + line)
        i += block_size

###############################################################################

# http://www.worldofspectrum.org/faq/reference/formats.htm#SNA

def analyse_sna(snafile):
    with open(snafile, 'rb') as f:
        sna = bytearray(f.read(49179))
    print('Interrupts: {}abled'.format('en' if sna[19] & 4 else 'dis'))
    print('Interrupt mode: {}'.format(sna[25]))
    print('Border: {}'.format(sna[26] & 7))
    width = 11
    flags = "SZ5H3PNC"
    lines = []
    sp = get_word(sna, 23)
    lines.append('PC=(SP)={}'.format(get_word(sna, sp - 16357)))
    lines.append('SP={}'.format(sp))
    lines.append('I={}'.format(sna[0]))
    lines.append('R={}'.format(sna[20]))
    lines.append("{} A'={}".format('A={}'.format(sna[22]).ljust(width), sna[8]))
    lines.append("  {}    {}".format(flags.ljust(width - 2), flags))
    lines.append("{} F'={}".format('F={}'.format(to_binary(sna[21])).ljust(width), to_binary(sna[7])))
    lines.append("{} B'={}".format('B={}'.format(sna[14]).ljust(width), sna[6]))
    lines.append("{} C'={}".format('C={}'.format(sna[13]).ljust(width), sna[5]))
    lines.append("{} D'={}".format('D={}'.format(sna[12]).ljust(width), sna[4]))
    lines.append("{} E'={}".format('E={}'.format(sna[11]).ljust(width), sna[3]))
    lines.append("{} H'={}".format('H={}'.format(sna[10]).ljust(width), sna[2]))
    lines.append("{} L'={}".format('L={}'.format(sna[9]).ljust(width), sna[1]))
    lines.append('IX={}'.format(get_word(sna, 17)))
    lines.append('IY={}'.format(get_word(sna, 15)))
    print('Registers:')
    for line in lines:
        print('  ' + line)

def find(infile, byte_seq):
    step = 1
    if '-' in byte_seq:
        byte_seq, step = byte_seq.split('-', 1)
        step = get_int_param(step)
    byte_values = [get_int_param(i) for i in byte_seq.split(',')]
    offset = step * len(byte_values)
    snapshot = get_snapshot(infile)
    for a in range(16384, 65537 - offset):
        if snapshot[a:a + offset:step] == byte_values:
            print("{}-{}-{}: {}".format(a, a + offset - step, step, byte_seq))

def peek(infile, addr_range):
    step = 1
    if '-' in addr_range:
        addr1, addr2 = addr_range.split('-', 1)
        addr1 = get_int_param(addr1)
        if '-' in addr2:
            addr2, step = [get_int_param(i) for i in addr2.split('-', 1)]
        else:
            addr2 = get_int_param(addr2)
    else:
        addr1 = addr2 = get_int_param(addr_range)
    snapshot = get_snapshot(infile)
    for a in range(addr1, addr2 + 1, step):
        value = snapshot[a]
        if 32 <= value <= 126:
            char = chr(value)
        else:
            char = ''
        print('{0:>5}: {1:>3}  {1:02X}  {1:08b}  {2}'.format(a, value, char))

###############################################################################
# Begin
###############################################################################
parser = argparse.ArgumentParser(
    usage='snapinfo.py [options] file',
    description="Analyse an SNA, SZX or Z80 snapshot.",
    add_help=False
)
parser.add_argument('infile', help=argparse.SUPPRESS, nargs='?')
group = parser.add_argument_group('Options')
group.add_argument('--basic', action='store_true',
                   help='List the BASIC program')
group.add_argument('--find', metavar='A[,B...[-N]]',
                   help='Search for the byte sequence A,B... with distance N (default=1) between bytes')
group.add_argument('--peek', metavar='A[-B[-C]]',
                   help='Show the contents of addresses A TO B STEP C')
namespace, unknown_args = parser.parse_known_args()
if unknown_args or namespace.infile is None:
    parser.exit(2, parser.format_help())
infile = namespace.infile
snapshot_type = infile[-4:].lower()
if snapshot_type not in ('.sna', '.szx', '.z80'):
    sys.stderr.write('Error: unrecognized snapshot type\n')
    sys.exit(1)

if namespace.find is not None:
    find(infile, namespace.find)
elif namespace.peek is not None:
    peek(infile, namespace.peek)
elif namespace.basic:
    BasicLister().list_basic(get_snapshot(infile))
elif snapshot_type == '.sna':
    analyse_sna(infile)
elif snapshot_type == '.z80':
    analyse_z80(infile)
else:
    analyse_szx(infile)
