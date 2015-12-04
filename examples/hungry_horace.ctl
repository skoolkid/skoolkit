;
; SkoolKit control file for Hungry Horace
;
; To build the HTML disassembly, run these commands:
;   tap2sna.py @hungry_horace.t2s
;   sna2skool.py -c hungry_horace.ctl hungry_horace.z80 > hungry_horace.skool
;   skool2html.py hungry_horace.ref
;

b 16384 Loading screen
D 16384 #SCR(loading)
B 16384,6912,16
i 23296
S 23296
@ 24576 start
@ 24576 org=24576
@ 24576 replace=/#maze\i/#UDGARRAY#(32#FOR(\1,\1+767)||n|;(31735+8*#PEEKn),#MAP(#PEEKn)(61,2:60,3:56)||)
@ 24576 replace=/#sprite\i,\i/#UDGARRAY2,\2;\1-(\1+24)-8
@ 24576 replace=/#fruit\i/#UDGARRAY#(2#FOR(\1,\1+27,9)||n|;(n+1),#PEEKn||)
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
t 27303 Copyright #CHR169 1982 Beam Software...
T 27335
t 27367 DEMO MODE#SPACE(2)PRESS ANY KEY TO PLAY
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
D 28663 #maze28663(maze2)
B 28663,768,32
b 29431 Maze 1 layout
D 29431 #maze29431(maze1)
B 29431,768,32
b 30199 Maze 3 layout
D 30199 #maze30199(maze3)
B 30199,768,32
b 30967 Maze 4 layout
D 30967 #maze30967(maze4)
B 30967,768,32
b 31735 Maze tiles
D 31735 #UDGTABLE { #FOR31735,31807,8//n/#UDG(n,#MAPn(61,31751:60,31759:56))/ | // } TABLE#
t 31815 PASSES#SPACE(3)SCORE#SPACE(7)BEST
b 31841
b 31868 Cherry and strawberry graphics
B 31868,36,9 #fruit31868(cherry)
B 31904,36,9 #fruit31904(strawberry)
b 31940
b 31943 Horace graphics
B 31943 #sprite31943,57(horace0)
B 31975 #sprite31975,57(horace1)
B 32007 #sprite32007,57(horace2)
B 32039 #sprite32039,57(horace3)
B 32071 #sprite32071,57(horace4)
B 32103 #sprite32103,57(horace5)
B 32135 #sprite32135,57(horace6)
B 32167 #sprite32167,57(horace7)
b 32199 Guard graphics
B 32199 #sprite32199,59(guard0)
B 32231 #sprite32231,59(guard1)
B 32263 #sprite32263,59(guard2)
B 32295 #sprite32295,59(guard3)
B 32327 #sprite32327,59(guard4)
B 32359 #sprite32359,59(guard5)
B 32391 #sprite32391,59(guard6)
B 32423 #sprite32423,59(guard7)
B 32455 #sprite32455,59(guard8)
B 32487 #sprite32487,59(guard9)
b 32519 Bell graphics
B 32519 #sprite32519,58(bell0)
B 32551 #sprite32551,58(bell1)
B 32583 #sprite32583,58(bell2)
B 32615 #sprite32615,58(bell3)
i 32647
