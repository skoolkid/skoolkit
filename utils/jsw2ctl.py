#!/usr/bin/env python
import sys
import os

# Use the current development version of SkoolKit
SKOOLKIT_HOME = os.environ.get('SKOOLKIT_HOME')
if not SKOOLKIT_HOME:
    sys.stderr.write('SKOOLKIT_HOME is not set; aborting\n')
    sys.exit(1)
if not os.path.isdir(SKOOLKIT_HOME):
    sys.stderr.write('SKOOLKIT_HOME={0}; directory not found\n'.format(SKOOLKIT_HOME))
    sys.exit(1)
sys.path.insert(0, SKOOLKIT_HOME)

from skoolkit.snapshot import get_snapshot

TEMPLATE = """
;
; SkoolKit control file for Jet Set Willy.
;
; Room descriptions based on reference material from Andrew Broad
; <http://webspace.webring.com/people/ja/andrewbroad/> and J. G. Harston
; <http://mdfs.net/Software/JSW/Docs/>.
;
; To build the HTML disassembly, create a z80 snapshot of Jet Set Willy named
; jsw.z80, and run these commands:
;   sna2skool.py -c jet_set_willy.ctl jsw.z80 > jet_set_willy.skool
;   skool2html.py jet_set_willy.ref
;

; @start:32768
; @org:32768=32768
b 32768 Room buffer
S 32768,256
b 33024 Guardian buffer
S 33024,64
B 33088 Terminator
s 33089
w 33280 Screen buffer address lookup table
W 33280,256,16
b 33536 Rope animation table
B 33536,256,16
c 33792 Start
b 33824 Current room number
b 33825 Conveyor data
b 33841 Triangle UDGs
D 33841 #UDGTABLE {{ #UDG33841,56(triangle0) | #UDG33849,56(triangle1) | #UDG33857,56(triangle2) | #UDG33865,56(triangle3) }} TABLE#
t 33873 'AIR'
t 33876 '+++++ Press ENTER to Start +++++'
t 33908 '#SPACE(2)JET-SET WILLY by Matthew Smith...'
B 33942 #CHR169
T 33943
T 33980
T 34024
T 34050
T 34100
t 34132 'Items collected 000 Time 00:00 m'
t 34164 'GameOver'
t 34172 '000'
t 34175 ' 7:00a'
t 34181 ' 7:00a'
t 34187 'Enter Code at grid location#SPACE5'
t 34219 'Sorry, try code at location#SPACE5'
g 34251 Game status buffer
B 34251,26,16
b 34277 WRITETYPER
B 34277,22,2
b 34299 Title screen tune data
B 34299,100,16
b 34399 In-game tune data
B 34399,64,16
c 34463
c 34499
c 34620
c 34762
c 35211
c 35245
c 35841
c 35914
c 36147
c 36203
c 36288
c 36307
c 36564
c 37056
c 37310
c 37819
c 37841
c 37974
c 38026
c 38046
c 38064
c 38098
c 38137
c 38196
c 38276
c 38298
c 38344
c 38430
c 38455
c 38504
c 38528
c 38545
c 38562
c 38622
s 38680
b 38912 Attributes for the top two-thirds of the title screen
B 38912,512,16
b 39424 Attributes for the bottom third of the screen during gameplay
B 39424,256,16
b 39680 Number key graphics
D 39680 #UDGTABLE {{ #UDGARRAY2,65,,2;39680;39681,121;39696;39697(number_key0) | #UDGARRAY2,66,,2;39712;39713,122;39728;39729(number_key1) | #UDGARRAY2,3,,2;39744;39745,59;39760;39761(number_key2) | #UDGARRAY2,4,,2;39776;39777,60;39792;39793(number_key3) }} TABLE#
B 39680,128,16
b 39808 Attributes for the code entry screen
B 39808,128,16
t 39936 Source code remnants
D 39936 The source code here corresponds to the code at #R35545.
T 39936 [JR ]NZ,ENDPAUSE
M 39947,9 INC E
W 39947
B 39949
T 39950,6,B1:3:B1:1
M 39956,15 JR NZ,PAUSE
W 39956
B 39958
T 39959,12,B1:2:B1:8
M 39971,9 INC D
W 39971
B 39973
T 39974,6,B1:3:B1:1
M 39980,15 JR NZ,PAUSE
W 39980
B 39982
T 39983,12,B1:2:B1:8
W 39995
B 39997
T 39998,2,B1:1
b 40000 Foot/barrel graphic data
D 40000 The foot appears as a guardian in #R56576(The Nightmare Room).
{foot}
D 40032 The barrel appears as a guardian in #R54272(Ballroom East) and #R57856(Top Landing).
{barrel}
b 40064 Maria sprite graphic data
D 40064 Maria appears as a guardian in #R56576(The Nightmare Room).
{maria}
b 40192 Willy sprite graphic data
{willy}
b 40448 Codes
{codes}
u 40627
C 40627
S 40704
b 40960 Guardian definitions
B 40960,1023,8
b 41983 Index of first object
b 41984 Object table
b 42496 Toilet graphics
{toilet}
u 42624
B 42624,128,16
S 42752
b 43776 {guardians}
{rooms}
u 64768 Unused TRS-DOS code
C 64768
B 65005,136,16
T 65141
C 65147
B 65203,2
T 65205
C 65236
B 65410,16,8
C 65426
S 65517
""".lstrip()

GUARDIANS = {
    43776: 4,
    43904: 4,
    44032: 4,
    44160: 4,
    44288: 4,
    44416: 4,
    44544: 4,
    44672: 4,
    44800: 4,
    44928: 4,
    45056: 4,
    45184: 2,
    45248: 2,
    45312: 8,
    45568: 4,
    45696: 4,
    45824: 0,
    46080: 8,
    46336: 8,
    46592: 8,
    46848: 2,
    46912: 2,
    46976: 4,
    47104: 8,
    47360: 4,
    47488: 4,
    47616: 4,
    47744: 4,
    47872: 4,
    48000: 4,
    48128: 8,
    48384: 8,
    48640: 4,
    48768: 4,
    48896: 4,
    49024: 2,
    49088: 2
}

def get_codes(snapshot):
    lines = []
    for i in range(179):
        addr = 40448 + i
        value = (snapshot[addr] + i) & 255
        code = '{}{}{}{}'.format((value >> 6) + 1, ((value >> 4) & 3) + 1, ((value >> 2) & 3) + 1, (value & 3) + 1)
        grid_loc = chr(65 + (i % 18)) + chr(48 + i // 18)
        lines.append('B {},1 {}: {}'.format(addr, grid_loc, code))
    return '\n'.join(lines)

def get_udg_table(addr, fname, num=8, rows=1, animation='', delay=None, attr=56):
    macros = []
    start = addr
    suffix = '*' if animation else ''
    if isinstance(attr, int):
        attrs = [attr] * num
    else:
        attrs = list(attr)
    for r in range(rows):
        macros.append([])
        frames = []
        end = start + (32 * num) // rows
        for b in range(start, end, 32):
            if num == 1:
                frame = fname
            else:
                frame = '{}{}'.format(fname, (b - addr) // 32)
            if r % 2:
                frames.insert(0, frame)
            else:
                frames.append(frame)
            macros[-1].append('#UDGARRAY2,{},,2;{}-{}-1-16({}{})'.format(attrs.pop(0), b, b + 17, frame, suffix))
        start = end
        if r < len(animation):
            if delay:
                frames[0] += ',{}'.format(delay)
            macros[-1].append('#UDGARRAY*{}({}_{}.gif)'.format(';'.join(frames), fname, animation[r]))
    udgtable = '#UDGTABLE'
    for r in range(rows):
        udgtable += ' {{ {} }}'.format(' | '.join(macros[r]))
    return udgtable + ' TABLE#'

def get_graphics(address, img_fname_prefix, num_sprites, rows=1, animation='', delay=None, attr=56):
    lines = []
    udg_table = get_udg_table(address, img_fname_prefix, num_sprites, rows, animation, delay, attr)
    lines.append('D {0} {1}'.format(address, udg_table))
    lines.append('B {0},{1},16'.format(address, 32 * num_sprites))
    return '\n'.join(lines)

def get_guardian_graphics(snapshot):
    rooms = {}
    guardians = {}
    attrs = {}
    for room_num in range(61):
        addr = 256 * (room_num + 192)
        name = ''.join([chr(b) for b in snapshot[addr + 128:addr + 160]]).strip()
        rooms[room_num] = '#R{}({})'.format(addr, name)
        for a in range(addr + 240, addr + 256, 2):
            num, start = snapshot[a:a + 2]
            if num == 255:
                break
            def_addr = 40960 + num * 8
            guardian_def = snapshot[def_addr:def_addr + 8]
            guardian_type = guardian_def[0] & 7
            if guardian_type & 3 in (1, 2):
                sprite_addr = 256 * guardian_def[5] + (start & 224)
                if sprite_addr >= 43776:
                    while sprite_addr not in GUARDIANS:
                        sprite_addr -= 32
                    guardians.setdefault(sprite_addr, set()).add(room_num)
                    b1 = guardian_def[1]
                    bright = 8 * (b1 & 8)
                    paper = snapshot[addr + 160] & 56
                    ink = b1 & 7
                    attrs.setdefault(sprite_addr, []).append(bright + paper + ink)

    lines = ['Guardian graphics']
    prev_page = 0
    for a in sorted(GUARDIANS.keys()):
        page = a // 256
        if page > prev_page:
            index = 0
        else:
            index += 1
        prev_page = page
        if a not in guardians:
            if any(snapshot[a:a + 256]):
                # 45312
                comment = 'This guardian is not used.'
                attr = 7
            else:
                # 45824
                comment = 'The next 256 bytes are unused.'
        else:
            macros = [rooms[n] for n in sorted(guardians[a])]
            if a == 45056:
                attr = (3, 6, 5, 5)
            else:
                attr = attrs[a][0]
            if len(macros) == 1:
                room_links = macros[0]
            else:
                room_links = '{} and {}'.format(', '.join(macros[:-1]), macros[-1])
            comment = 'This guardian appears in {}.'.format(room_links)
        lines.append('D {} {}'.format(a, comment))
        num = GUARDIANS[a]
        if num:
            udg_table = get_udg_table(a, 'guardian{}_{}_'.format(page, index), num, attr=attr)
            lines.append('D {} {}'.format(a, udg_table))
            lines.append('B {},{},16'.format(a, 32 * num))
        else:
            lines.append('S {},256'.format(a))
    return '\n'.join(lines)

def get_rooms(snapshot):
    lines = []

    start = 41984 + snapshot[41983]
    items = {}
    for a in range(start, 42240):
        b1 = snapshot[a]
        b2 = snapshot[a + 256]
        room_num = b1 & 63
        x = b2 & 31
        y = 8 * (b1 >> 7) + b2 // 32
        items.setdefault(room_num, []).append((x, y))

    rooms = {}
    rooms_wp = {}
    for a in range(49152, 64768, 256):
        room_num = a // 256 - 192
        room_name = ''.join([chr(b) for b in snapshot[a + 128:a + 160]]).strip()
        room_name_wp = room_name
        if room_name.find('  ') > 0:
            room_name_wp = ''
            start = 0
            in_word = False
            for end, c in enumerate(room_name + ' '):
                if c == ' ':
                    if in_word:
                        room_name_wp += room_name[start:end]
                        start = end
                    in_word = False
                else:
                    if not in_word:
                        room_name_wp += '#SPACE({0})'.format(end - start)
                        start = end
                    in_word = True
        rooms[room_num] = room_name
        rooms_wp[room_num] = room_name_wp

    for a in range(49152, 64768, 256):
        room = snapshot[a:a + 256]
        room_num = a // 256 - 192
        room_name = rooms[room_num]
        lines.append('b {0} Room {1}: {2}'.format(a, room_num, rooms_wp[room_num]))
        if a in (50688, 56320, 56576, 59904, 61440):
            # Rooms with flashing cells
            room_image = '#ROOM{0}({1}.gif)'.format(a, room_name.lower().replace(' ', '_'))
        elif a == 61184:
            # [
            room_image = '#ROOM{0}(left_square_bracket)'.format(a)
        else:
            room_image = '#ROOM{0}'.format(a)
        lines.append('D {0} #UDGTABLE {{ {1} }} TABLE#'.format(a, room_image))
        lines.append('D {0} The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.'.format(a))
        lines.append('B {0},128,8 Room layout'.format(a))

        # Room name
        lines.append('D {0} The next 32 bytes contain the room name.'.format(a + 128))
        lines.append('T {0},32 Room name'.format(a + 128))

        # Tiles
        udgs = []
        for addr, tile_type in ((a + 160, 'background'), (a + 169, 'floor'), (a + 178, 'wall'), (a + 187, 'nasty'), (a + 196, 'ramp'), (a + 205, 'conveyor')):
            attr = snapshot[addr]
            if tile_type == 'background':
                room_paper = attr & 120
            img_type = ''
            if attr >= 128:
                paper = (attr & 56) // 8
                ink = attr & 7
                if paper != ink:
                    udg_bytes = snapshot[addr + 1:addr + 9]
                    if not all([b == 0 for b in udg_bytes]) and not all([b == 255 for b in udg_bytes]):
                        # This tile is flashing
                        img_type = '.gif'
            udgs.append('#UDG{0},{1}({2}{3:02d}{4})'.format(addr + 1, attr, tile_type, room_num, img_type))
        tiles_table = '#UDGTABLE { ' + ' | '.join(udgs) + ' } TABLE#'
        comment = 'The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.'
        tile_usage = [' (unused)'] * 6
        for b in snapshot[a:a + 128]:
            for i in range(4):
                tile_usage[b & 3] = ''
                b >>= 2
        ramp_length = snapshot[a + 221]
        if ramp_length:
            tile_usage[4] = ''
        conveyor_length = snapshot[a + 217]
        if conveyor_length:
            tile_usage[5] = ''
            conveyor_attr = snapshot[a + 205]
            b = a + 160
            while b < a + 205 and snapshot[b] != conveyor_attr:
                b += 1
            if b < a + 205:
                comment += ' Note that because of a bug in the game engine, the conveyor tile is not drawn correctly (see the room image above).'
        lines.append('D {0} {1}'.format(a + 160, comment))
        lines.append('D {0} {1}'.format(a + 160, tiles_table))
        lines.append('B {0},9,9 Background{1}'.format(a + 160, tile_usage[0]))
        lines.append('B {0},9,9 Floor{1}'.format(a + 169, tile_usage[1]))
        lines.append('B {0},9,9 Wall{1}'.format(a + 178, tile_usage[2]))
        lines.append('B {0},9,9 Nasty{1}'.format(a + 187, tile_usage[3]))
        lines.append('B {0},9,9 Ramp{1}'.format(a + 196, tile_usage[4]))
        lines.append('B {0},9,9 Conveyor{1}'.format(a + 205, tile_usage[5]))

        # Conveyor/ramp direction, location and length
        lines.append('D {0} The next 8 bytes define the direction, location and length of the conveyor and ramp.'.format(a + 214))
        conveyor_d, p1, p2 = snapshot[a + 214:a + 217]
        conveyor_x = p1 & 31
        conveyor_y = 8 * (p2 & 1) + (p1 & 224) // 32
        lines.append('B {0},4 Conveyor direction ({1}), location (x={2}, y={3}) and length ({4})'.format(a + 214, 'right' if conveyor_d else 'left', conveyor_x, conveyor_y, conveyor_length))
        ramp_d, p1, p2 = snapshot[a + 218:a + 221]
        ramp_x = p1 & 31
        ramp_y = 8 * (p2 & 1) + (p1 & 224) // 32
        lines.append('B {0},4 Ramp direction ({1}), location (x={2}, y={3}) and length ({4})'.format(a + 218, 'right' if ramp_d else 'left', ramp_x, ramp_y, ramp_length))

        # Border colour
        lines.append('D {0} The next byte specifies the border colour.'.format(a + 222))
        lines.append('B {0} Border colour'.format(a + 222))
        lines.append('B {0} Unused'.format(a + 223))

        # Object graphic
        lines.append('D {0} The next 8 bytes define the object graphic.'.format(a + 225))
        lines.append('D {0} #UDGTABLE {{ #UDG{0},{1}(object{2:02d}) }} TABLE#'.format(a + 225, room_paper + 3, room_num))
        lines.append('B {0},8,8 Object graphic{1}'.format(a + 225, '' if items.get(room_num) else ' (unused)'))

        # Rooms to the left, to the right, above and below
        lines.append('D {0} The next 4 bytes specify the rooms to the left, to the right, above and below.'.format(a + 233))
        room_left, room_right, room_up, room_down = room[233:237]
        for addr, num, name, desc in (
            (a + 233, room_left, rooms_wp.get(room_left), 'to the left'),
            (a + 234, room_right, rooms_wp.get(room_right), 'to the right'),
            (a + 235, room_up, rooms_wp.get(room_up), 'above'),
            (a + 236, room_down, rooms_wp.get(room_down), 'below'),
        ):
            if name and name != room_name:
                lines.append('B {0} Room {1} (#R{2}({3}))'.format(addr, desc, 256 * (num + 192), name))
            elif name:
                lines.append('B {0} Room {1} ({2})'.format(addr, desc, name))
            else:
                lines.append('B {0} Room {1} (none)'.format(addr, desc))

        lines.append('B {0} Unused'.format(a + 237))

        # Guardians
        start = a + 240
        end = a + 256
        for addr in range(start, end, 2):
            if snapshot[addr] == 255:
                end = addr
                break
        num_guardians = (end - start) // 2
        if num_guardians:
            lines.append('D {0} The next {1} bytes define the guardians.'.format(start, num_guardians * 2))
            addr = start
            for i in range(num_guardians):
                lines.append('B {0},2 Guardian {1}'.format(addr, i + 1))
                addr += 2
        else:
            lines.append('D {0} There are no guardians in this room.'.format(start))
        if num_guardians < 8:
            lines.append('B {0},1 Terminator'.format(addr))
            lines.append('B {0},{1},{2} Unused'.format(addr + 1, a + 255 - addr, a + 255 - addr))

    return '\n'.join(lines)

def write_ctl(snapshot):   
    sys.stdout.write(TEMPLATE.format(
        foot=get_graphics(40000, 'foot', 1, attr=6),
        barrel=get_graphics(40032, 'barrel', 1, attr=66),
        maria=get_graphics(40064, 'maria', 4, attr=5),
        willy=get_graphics(40192, 'willy', 8, 2, ('r', 'l'), attr=7),
        codes=get_codes(snapshot),
        toilet=get_graphics(42496, 'toilet', 4, 2, ('empty', 'full'), 10, attr=7),
        guardians=get_guardian_graphics(snapshot),
        rooms=get_rooms(snapshot)
    ))

def show_usage():
    sys.stderr.write("""Usage: {0} jet_set_willy.[sna|z80]

  Generate a control file for Jet Set Willy.
""".format(os.path.basename(sys.argv[0])))
    sys.exit(1)

###############################################################################
# Begin
###############################################################################
if len(sys.argv) < 2:
    show_usage()

write_ctl(get_snapshot(sys.argv[1]))
