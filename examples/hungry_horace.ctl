;
; SkoolKit control file for Hungry Horace
;
; To build the HTML disassembly, run these commands:
;   tap2sna.py @hungry_horace.t2s
;   sna2skool.py -c hungry_horace.ctl hungry_horace.z80 > hungry_horace.skool
;   skool2html.py hungry_horace.ref
;

b 16384 Loading screen
B 16384,6912,16
i 23296
@ 24576 start
@ 24576 org=24576
@ 24576 set-handle-unsupported-macros=1
c 24576 The game has just loaded
c 25167
c 25399
c 25562
c 25886
c 25947
c 26017
c 26146
c 26173
c 26276
c 26426
c 26657
c 26730
c 26887
c 26914
c 26988
c 27022
c 27044
u 27159
C 27159
c 27166
c 27170
c 27199
c 27242
c 27255
c 27294
t 27303
t 27367
u 27400
c 27404
c 27410
c 27425
c 27464
c 27509 Draw the current maze
c 27606
c 27642
c 27663
c 27680
c 27718
c 27752
c 27797
c 27842
c 27898
c 27927
c 27982
b 28070
b 28663 Maze 2 layout
D 28663 #CALL:maze(28663,maze2)
B 28663,768,16
b 29431 Maze 1 layout
D 29431 #CALL:maze(29431,maze1)
B 29431,768,16
b 30199 Maze 3 layout
D 30199 #CALL:maze(30199,maze3)
B 30199,768,16
b 30967 Maze 4 layout
D 30967 #CALL:maze(30967,maze4)
B 30967,768,16
b 31735 Maze tiles
D 31735 #UDGTABLE { #UDG31735 | #UDG31743,61 | #UDG31751,60 | #UDG31759 | #UDG31767,61 | #UDG31775,61 | #UDG31783,61 | #UDG31791,61 | #UDG31799,61 | #UDG31807 } TABLE#
t 31815
b 31841
b 31943 Horace graphics
B 31943 #UDGARRAY2,57;31943-31967-8(horace0)
B 31975 #UDGARRAY2,57;31975-31999-8(horace1)
B 32007 #UDGARRAY2,57;32007-32031-8(horace2)
B 32039 #UDGARRAY2,57;32039-32063-8(horace3)
B 32071 #UDGARRAY2,57;32071-32095-8(horace4)
B 32103 #UDGARRAY2,57;32103-32127-8(horace5)
B 32135 #UDGARRAY2,57;32135-32159-8(horace6)
B 32167 #UDGARRAY2,57;32167-32191-8(horace7)
b 32199
i 32768
