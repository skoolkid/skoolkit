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
c 27509
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
t 31815
b 31841
i 32768
