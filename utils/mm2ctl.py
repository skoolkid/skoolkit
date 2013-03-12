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

HEADER = """
;
; SkoolKit control file for Manic Miner (Bug Byte version).
;
; Cavern descriptions based on reference material from Andrew Broad
; <http://webspace.webring.com/people/ja/andrewbroad/>.
;
; To build the HTML disassembly, create a z80 snapshot of Manic Miner named
; mm.z80, and run these commands from the top-level SkoolKit directory:
;   ./sna2skool.py -c examples/manic_miner.ctl mm.z80 > manic_miner.skool
;   ./skool2html.py examples/manic_miner.ref
;
b 32768 Cavern buffer
D 32768 Source code remnants. These DB directives define part of the title screen tune data at #R33902.
T 32768,19
M 32787,37 790 DB "50,48,68,50,171,192,50,136,137"
W 32787
B 32789
T 32790,34,B1:2:B1:30
M 32824,37 800 DB "50,136,137,50,114,115,50,76,77"
W 32824
B 32826
T 32827,34,B1:2:B1:30
M 32861,35 810 DB "50,7?????????????92,50,38,48"
W 32861
B 32863
T 32864,8,B1:2:B1:4
B 32872,13,13
T 32885
M 32896,35 820 DB "50,38,4??50,171,192,50,48,68"
W 32896
B 32898
T 32899,11,B1:2:B1:7
T 32912,19
M 32931,37 830 DB "50,48,????0,171,19??50,136,137"
W 32931
B 32933
T 32934,10,B1:2:B1:6
B 32944
T 32948
B 32956
T 32958,10
M 32968,37 840 DB "50,136,137,???114,115,50,76,77"
W 32968
B 32970
T 32971,15,B1:2:B1:11
B 32986
T 32989
M 33005,35 850 ?B "50,76,77,50,171,203,50,38,51"
W 33005
B 33007
T 33008,32,B2:1:B1:28
M 33040,35 860 DB "50,38,51,50,171,203,50,51,64"
W 33040
B 33042
T 33043,32,B1:2:B1,28
M 33075,37 870 DB "50,51,64,50,171,203,50,128,129"
W 33075
B 33077
T 33078,34,B1:2:B1:30
M 33112,37 880 DB "50,128,129,50,102,103,50,86,87"
W 33112
B 33114
T 33115,34,B1:2:B1:30
M 33149,35 890 DB "50,64,65,50,128,171,50,32,43"
W 33149
B 33151
T 33152,32,B1:2:B1:28
M 33184,35 900 DB "50,32,43,50,128,171,50,43,51"
W 33184
B 33186
T 33187,32,B1:2:B1:28
M 33219,37 910 DB "50,43,51,50,128,171,50,128,129"
W 33219
B 33221
T 33222,34,B1:2:B1:30
M 33256,24 920 DB "50,128,129,50,102............."
W 33256
B 33258
T 33259,21,B1:2:B1:17
b 33280 Miner Willy sprite data
D 33280 #UDGTABLE { #UDGARRAY2,56,,2;33280-33297-1-16(willy0) | #UDGARRAY2,56,,2;33312-33329-1-16(willy1) | #UDGARRAY2,56,,2;33344-33361-1-16(willy2) | #UDGARRAY2,56,,2;33376-33393-1-16(willy3) | #UDGARRAY2,56,,2;33408-33425-1-16(willy4) | #UDGARRAY2,56,,2;33440-33457-1-16(willy5) | #UDGARRAY2,56,,2;33472-33489-1-16(willy6) | #UDGARRAY2,56,,2;33504-33521-1-16(willy7) } TABLE#
B 33280,256,16
w 33536 Screen buffer address lookup table
W 33536,256,16
c 33792 The game has just loaded
b 33799 Current cavern number
b 33800 Movement lookup table
t 33816 'AIR'
b 33819 Score and high score
T 33819,4
T 33823,6 High score
T 33829,4
T 33833,6 Score
t 33839 'High Score 000000#SPACE(3)Score 000000'
t 33871 'GameOver'
T 33871,4
g 33879 Game status buffer
b 33886 6031769
B 33886,16,2
b 33902 Title screen tune data
B 33902,286,16
b 34188 In-game tune data
B 34188,64,16
c 34252 Start
c 35388
c 35445
c 35515
c 35770
c 35805
c 36101
c 36111
c 36211
c 36266
c 36344
c 36469
c 36593
c 36707
c 36805
c 37098
c 37125
c 37173
c 37403
c 37434
c 37471
c 37503
c 37562 Print a message
c 37579
c 37596
c 37675
c 37687
t 37708 Source code remnants
D 37708 The source code here corresponds to the code at #R34900.
T 37708,6,B1:3:B1:1 DEC E
M 37714,16 3960 JR NZ,NOFLP6
W 37714
B 37716
T 37717,13,B1:2:B1:9
M 37730,13 3970 LD E,(HL)
W 37730
B 37732
T 37733,10,B1:2:B1:6
M 37743,10 3980 XOR 24
W 37743
B 37745
T 37746,7,B1:3:B1:2
M 37753,19 3990 NOFLP6 DJNZ TM51
W 37753
B 37755
T 37756,16,6:B1:4:B1:4
M 37772,9 4000 DEC C
W 37772
B 37774
T 37775,6,B1:3:B1:1
M 37781,14 4010 JR NZ,TM51
W 37781
B 37783
T 37784,11,B1:2:B1:7
M 37795,22 4020 NONOTE4 LD A,(DEMO)
W 37795
B 37797
T 37798,19,7:B1:2:B1:8
M 37817,8 4030 OR A
W 37817
B 37819
T 37820,5,B1:2:B1:1
M 37825,15 4040 JR Z,NODEM1
W 37825
B 37827
T 37828,12,B1:2:B1:8
M 37840,9 4050 DEC A
W 37840
B 37842
T 37843,6,B1:3:B1:1
M 37849,16 4060 JP Z,MANDEAD
W 37849
B 37851
T 37852,13,B1:2:B1:9
M 37865,15 4070 LD (DEMO),A
W 37865
B 37867
T 37868,12,B1:2:B1:8
M 37880,14 4080 LD BC,0FEH
W 37880
B 37882
T 37883,11,B1:2:B1:7
M 37894,12 4090 IN A,(C)
W 37894
B 37896
T 37897,9,B1:2:B1:5
M 37906,10 4100 AND 31
W 37906
B 37908
T 37909,7,B1:3:B1:2
M 37916,9 4110 CP 31
W 37916
B 37918
T 37919,6,B1:2:B1:2
M 37925,15 4120 JP NZ,START
W 37925
B 37927
T 37928,12,B1:2:B1:8
M 37940,15 4130 LD A,(KEMP)
W 37940
B 37942
T 37943,12,B1:2:B1:8
M 37955,8 4140 OR A
W 37955
B 37957
T 37958,5,B1:2:B1:1
M 37963,15 4150 JR Z,NODEM1
W 37963
B 37965
T 37966,12,B1:2:B1:8
M 37978,13 4160 IN A,(31)
W 37978
B 37980
T 37981,10,B1:2:B1:6
M 37991,8 4170 OR A
W 37991
B 37993
T 37994,5,B1:2:B1:1
M 37999,15 4180 JP NZ,START
W 37999
B 38001
T 38002,12,B1:2:B1:8
M 38014,22 4190 NODEM1 LD BC,0EFFEH
W 38014
B 38016
T 38017,19,6:B1:2:B1:9
M 38036,12 4200 IN A,(C)
W 38036
B 38038
T 38039,9,B1:2:B1:5
M 38048,11 4210 BIT 4,A
W 38048
B 38050
T 38051,8,B1:3:B1:3
M 38059,17 4220 JP NZ,CKCHEAT
W 38059
B 38061
T 38062,14,B1:2:B1:10
M 38076,16 4230 LD A,(CHEAT)
W 38076
B 38078
T 38079,13,B1:2:B1:9
M 38092,8 4240 CP 7
W 38092
B 38094
T 38095,5,B1:2:B1:1
M 38100,17 4250 JP NZ,CKCHEAT
W 38100
B 38102
T 38103,14,B1:2:B1:10
M 38117,13 4260 LD B,0F7H
W 38117
B 38119
T 38120,10,B1:2:B1:6
M 38130,12 4270 IN A,(C)
W 38130
B 38132
T 38133,9,B1:2:B1:5
M 38142,7 4280 CPL
W 38142
B 38144
T 38145,4,B1:3
M 38149,10 4290 AND 31
W 38149
B 38151
T 38152,7,B1:3:B1:2
M 38159,9 4300 CP 20
W 38159
B 38161
T 38162,6,B1:2:B1:2
M 38168,17 4310 JP NC,CKCHEAT
W 38168
B 38170
T 38171,14,B1:2:B1:10
M 38185,16 4320 LD (SHEET),A
W 38185
B 38187
T 38188,13,B1:2:B1:9
M 38201,13 4330 JP NEWSHT
W 38201
B 38203
T 38204,10,B1:2:B1:6
M 38214,23 4340 CKCHEAT LD A,(CHEAT)
W 38214
B 38216
T 38217,20,7:B1:2:B1:9
M 38237,8 4350 CP 7
W 38237
B 38239
T 38240,5,B1:2:B1:1
M 38245,13 4360 JP Z,LOOP
W 38245
B 38247
T 38248,10,B1:2:B1:6
M 38258,8 4370 RLCA
W 38258
B 38260
T 38261,5,B1:4
M 38266,10 4380 LD E,A
W 38266
B 38268
T 38269,7,B1:2:B1:3
M 38276,10 4390 LD D,0
W 38276
B 38278
T 38279,7,B1:2:B1:3
M 38286,17 4400 LD IX,CHEATDT
W 38286
B 38288
T 38289,14,B1:2:B1:10
M 38303,13 4410 ADD IX,DE
W 38303
B 38305
T 38306,10,B1:3:B1:5
M 38316,16 4420 LD BC,0F7FEH
W 38316
B 38318
T 38319,13,B1:2:B1:9
M 38332,12 4430 IN A,(C)
W 38332
B 38334
T 38335,9,B1:2:B1:5
M 38344,10 4440 AND 31
W 38344
B 38346
T 38347,7,B1:3:B1:2
M 38354,13 4450 CP (IX+0)
W 38354
B 38356
T 38357,10,B1:2:B1:6
M 38367,16 4460 JR Z,CKNXCHT
W 38367
B 38369
T 38370,13,B1:2:B1:9
M 38383,9 4470 CP 31
W 38383
B 38385
T 38386,6,B1:2:B1:2
M 38392,13 4480 JP Z,LOOP
W 38392
B 38394
T 38395,10,B1:2:B1:6
M 38405,13 4490 CP (IX-2)
W 38405
B 38407
T 38408,10,B1:2:B1:6
M 38418,13 4500 JP Z,LOOP
W 38418
B 38420
T 38421,10,B1:2:B1:6
M 38431,9 4510 XOR A
W 38431
B 38433
T 38434,6,B1:3:B1:1
M 38440,16 4520 LD (CHEAT),A
W 38440
B 38442
T 38443,13,B1:2:B1:9
M 38456,11 4530 JP LOOP
W 38456
B 38458
T 38459,8,B1:2:B1:4
M 38467,20 4540 CKNXCHT LD B,0EFH
W 38467
B 38469
T 38470,17,7:B1:2:B1:6
M 38487,12 4550 IN A,(C)
W 38487
B 38489
T 38490,9,B1:2:B1:5
M 38499,10 4560 AND 31
W 38499
B 38501
T 38502,7,B1:3:B1:2
M 38509,13 4570 CP (IX+1)
W 38509
B 38511
T 38512,10,B1:2:B1:6
M 38522,15 4580 JR Z,INCCHT
W 38522
B 38524
T 38525,12,B1:2:B1:8
M 38537,9 4590 CP 31
W 38537
B 38539
T 38540,6,B1:2:B1:2
M 38546,13 4600 JP Z,LOOP
W 38546
B 38548
T 38549,10,B1:2:B1:6
M 38559,13 4610 CP (IX-1)
W 38559
B 38561
T 38562,10,B1:2:B1:6
M 38572,13 4620 JP Z,LOOP
W 38572
B 38574
T 38575,10,B1:2:B1:6
M 38585,9 4630 XOR A
W 38585
B 38587
T 38588,6,B1:3:B1:1
M 38594,16 4640 LD (CHEAT),A
W 38594
B 38596
T 38597,13,B1:2:B1:9
M 38610,11 4650 JP LOOP
W 38610
B 38612
T 38613,8,B1:2:B1:4
M 38621,22 4660 INCCHT LD A,(CHEAT)
W 38621
B 38623
T 38624,19,6:B1:2:B1:9
M 38643,9 4670 INC A
W 38643
B 38645
T 38646,6,B1:3:B1:1
M 38652,16 4680 LD (CHEAT),A
W 38652
B 38654
T 38655,13,B1:2:B1:9
M 38668,11 4690 JP LOOP
W 38668
B 38670
T 38671,8,B1:2:B1:4
M 38679,22 4700 MANDEAD LD A,(DEMO)
W 38679
B 38681
T 38682,19,7:B1:2:B1:8
M 38701,8 4710 OR A
W 38701
B 38703
T 38704,5,B1:2:B1:1
M 38709,17 4720 JP NZ,NXSHEET
W 38709
B 38711
T 38712,14,B1:2:B1:10
M 38726,12 4730 LD A,47H
W 38726
B 38728
T 38729,9,B1:2:B1:5
M 38738,22 4740 LPDEAD1 LD HL,5800H
W 38738
B 38740
T 38741,19,7:B1:2:B1:8
M 38760,15 4750 LD DE,5801H
W 38760
B 38762
T 38763,12,B1:2:B1:8
M 38775,14 4760 LD BC,1FFH
W 38775
B 38777
T 38778,11,B1:2:B1:7
M 38789,13 4770 LD (HL),A
W 38789
B 38791
T 38792,10,B1:2:B1:6
M 38802,8 4780 LDIR
W 38802
B 38804
T 38805,5,B1:4
M 38810,10 4790 LD E,A
W 38810
B 38812
T 38813,7,B1:2:B1:3
M 38820,7 4800 CPL
W 38820
B 38822
T 38823,4,B1:3
M 38827,9 4810 AND 7
W 38827
B 38829
T 38830,6,B1:3:B1:1
M 38836,8 4820 RLCA
W 38836
B 38838
T 38839,5,B1:4
M 38844,8 4830 RLCA
W 38844
B 38846
T 38847,5,B1:4
M 38852,8 4840 RLCA
W 38852
B 38854
T 38855,5,B1:4
M 38860,8 4850 OR 7
W 38860
B 38862
T 38863,5,B1:2:B1:1
M 38868,10 4860 LD D,A
W 38868
B 38870
T 38871,7,B1:2:B1:3
M 38878,10 4870 LD C,E
W 38878
B 38880
T 38881,7,B1:2:B1:3
M 38888,9 4880 RRC C
W 38888
B 38890
T 38891,6,B1:3:B1:1
M 38897,9 4890 RRC C
W 38897
B 38899
T 38900,6,B1:3:B1:1
M 38906,9 4900 RRC C
W 38906
B 38908
T 38909,6,B1:3:B1:1
M 38915,9 4910 OR 16
W 38915
B 38917
T 38918,6,B1:2:B1:2
M 38924,9 4920 XOR A
W 38924
B 38926
T 38927,6,B1:3:B1:1
M 38933,19 4930 TM21 OUT (254),A
W 38933
B 38935
T 38936,16,4:B1:3:B1:7
M 38952,10 4940 XOR 24
W 38952
B 38954
T 38955,7,B1:3:B1:2
M 38962,10 4950 LD B,D
W 38962
B 38964
T 38965,7,B1:2:B1:3
M 38972,17 4960 TM22 DJNZ TM22
W 38972
B 38974
T 38975,14,4:B1:4:B1:4
M 38989,9 4970 DEC C
W 38989
B 38991
T 38992,6,B1:3:B1:1
M 38998,14 4980 JR NZ,TM21
W 38998
B 39000
T 39001,11,B1:2:B1:7
M 39012,10 4990 LD A,E
W 39012
B 39014
T 39015,7,B1:2:B1:3
M 39022,9 5000 DEC A
W 39022
B 39024
T 39025,6,B1:3:B1:1
M 39031,10 5010 CP 3FH
W 39031
B 39033
T 39034,7,B1:2:B1:3
M 39041,17 5020 JR NZ,LPDEAD1
W 39041
B 39043
T 39044,14,B1:2:B1:10
M 39058,15 5030 LD HL,NOMEN
W 39058
B 39060
T 39061,12,B1:2:B1:8
M 39073,13 5040 LD A,(HL)
W 39073
B 39075
T 39076,10,B1:2:B1:6
M 39086,8 5050 OR A
W 39086
B 39088
T 39089,5,B1:2:B1:1
M 39094,15 5060 JP Z,ENDGAM
W 39094
B 39096
T 39097,12,B1:2:B1:8
M 39109,12 5070 DEC (HL)
W 39109
B 39111
T 39112,9,B1:3:B1:4
M 39121,13 5080 JP NEWSHT
W 39121
B 39123
T 39124,10,B1:2:B1:6
M 39134,23 5090 ENDGAM LD HL,HGHSCOR
W 39134
B 39136
T 39137,20,6:B1:2:B1:10
M 39157,17 5100 LD DE,SCORBUF
W 39157
B 39159
T 39160,14,B1:2:B1:10
M 39174,10 5110 LD B,6
W 39174
B 39176
T 39177,7,B1:2:B1:3
M 39184,18 5120 LPHGH LD A,(DE)
W 39184
B 39186
T 39187,15,5:B1:2:B1:6
M 39202,11 5130 CP (HL)
W 39202
B 39204
T 39205,8,B1:2:B1:4
M 39213,13 5140 JP C,FEET
W 39213
B 39215
T 39216,10,B1:2:B1:6
M 39226,16 5150 JP NZ,NEWHGH
W 39226
B 39228
T 39229,13,B1:2:B1:9
M 39242,10 5160 INC HL
W 39242
B 39244
T 39245,7,B1:3:B1:2
M 39252,10 5170 INC DE
W 39252
B 39254
T 39255,7,B1:3:B1:2
M 39262,14 5180 DJNZ LPHGH
W 39262
B 39264
T 39265,11,B1:4:B1:5
M 39276,23 5190 NEWHGH LD HL,SCORBUF
W 39276
B 39278
T 39279,20,6:B1:2:B1:10
M 39299,17 5200 LD DE,HGHSCOR
W 39299
B 39301
T 39302,14,B1:2:B1:10
M 39316,11 5210 LD BC,6
W 39316
B 39318
T 39319,8,B1:2:B1:4
M 39327,8 5220 LDIR
W 39327
B 39329
T 39330,5,B1:4
M 39335,19 5230 FEET LD HL,4000H
W 39335
B 39337
T 39338,16,4:B1:2:B1:8
M 39354,15 5240 LD DE,4001H
W 39354
B 39356
T 39357,12,B1:2:B1:8
M 39369,15 5250 LD BC,0FFFH
W 39369
B 39371
T 39372,12,B1:2:B1:8
M 39384,13 5260 LD (HL),0
W 39384
B 39386
T 39387,10,B1:2:B1:6
M 39397,8 5270 LDIR
W 39397
B 39399
T 39400,5,B1:4
M 39405,9 5280 XOR A
W 39405
B 39407
T 39408,6,B1:3:B1:1
M 39414,17 5290 LD (EUGHGT),A
W 39414
B 39416
T 39417,14,B1:2:B1:10
M 39431,19 5300 LD DE,MANDAT+64
W 39431
B 39433
T 39434,16,B1:2:B1:12
M 39450,15 5310 LD HL,488FH
W 39450
B 39452
T 39453,12,B1:2:B1:8
M 39465,10 5320 LD C,0
W 39465
B 39467
T 39468,7,B1:2:B1:3
M 39475,15 5330 CALL DRWFIX
W 39475
B 39477
T 39478,12,B1:4:B1:6
M 39490,16 5340 LD DE,0B6E0H
W 39490
B 39492
T 39493,13,B1:2:B1:9
M 39506,15 5350 LD HL,48CFH
W 39506
B 39508
T 39509,12,B1:2:B1:8
M 39521,10 5360 LD C,0
W 39521
B 39523
T 39524,7,B1:2:B1:3
M 39531,15 5370 CALL DRWFIX
W 39531
B 39533
T 39534,12,B1:4:B1:6
M 39546,23 5380 LOOPFT LD A,(EUGHGT)
W 39546
B 39548
T 39549,20,6:B1:2:B1:10
M 39569,10 5390 LD C,A
W 39569
B 39571
T 39572,7,B1:2:B1:3
M 39579,12 5400 LD B,83H
W 39579
B 39581
T 39582,9,B1:2:B1:5
M 39591,13 5410 LD A,(BC)
W 39591
B 39593
T 39594,10,B1:2:B1:6
M 39604,10 5420 OR 0FH
W 39604
B 39606
T 39607,7,B1:2:B1:3
M 39614,10 5430 LD L,A
W 39614
B 39616
T 39617,7,B1:2:B1:3
M 39624,10 5440 INC BC
W 39624
B 39626
T 39627,7,B1:3:B1:2
M 39634,13 5450 LD A,(BC)
W 39634
B 39636
T 39637,10,B1:2:B1:6
M 39647,11 5460 SUB 20H
W 39647
B 39649
T 39650,8,B1:3:B1:3
M 39658,10 5470 LD H,A
W 39658
B 39660
T 39661,7,B1:2:B1:3
M 39668,16 5480 LD DE,0BAE0H
W 39668
B 39670
T 39671,13,B1:2:B1:9
M 39684,10 5490 LD C,0
W 39684
B 39686
T 39687,7,B1:2:B1:3
M 39694,15 5500 CALL DRWFIX
W 39694
B 39696
T 39697,12,B1:4:B1:6
M 39709,17 5510 LD A,(EUGHGT)
W 39709
B 39711
T 39712,14,B1:2:B1:10
M 39726,7 5520 CPL
W 39726
B 39728
T 39729,4,B1:3
M 39733,10 5530 LD E,A
W 39733
B 39735
T 39736,7,B1:2:B1:3
M 39743,9 5540 XOR A
W 39743
B 39745
T 39746,6,B1:3:B1:1
M 39752,13 5550 LD BC,40H
W 39752
B 39754
T 39755,10,B1:2:B1:6
M 39765,20 5560 TM111 OUT (254),A
W 39765
B 39767
T 39768,17,5:B1:3:B1:7
M 39785,10 5570 XOR 24
W 39785
B 39787
T 39788,7,B1:3:B1:2
M 39795,10 5580 LD B,E
W 39795
B 39797
T 39798,7,B1:2:B1:3
M 39805,19 5590 TM112 DJNZ TM112
W 39805
B 39807
T 39808,16,5:B1:4:B1:5
M 39824,9 5600 DEC C
W 39824
B 39826
T 39827,6,B1:3:B1:1
M 39833,15 5610 JR NZ,TM111
W 39833
B 39835
T 39836,12,B1:2:B1:8
M 39848,15 5620 LD HL,5800H
W 39848
B 39850
T 39851,12,B1:2:B1:8
M 39863,15 5630 LD DE,5801H
W 39863
B 39865
T 39866,12,B1:2:B1:8
M 39878,14 5640 LD BC,1FFH
W 39878
B 39880
T 39881,11,B1:2:B1:7
M 39892,17 5650 LD A,(EUGHGT)
W 39892
B 39894
T 39895,14,B1:2:B1:10
M 39909,11 5660 AND 0CH
W 39909
B 39911
T 39912,8,B1:3:B1:3
M 39920,8 5670 RLCA
W 39920
B 39922
T 39923,5,B1:4
M 39928,10 5680 OR 47H
W 39928
B 39930
T 39931,7,B1:2:B1:3
M 39938,13 5690 LD (HL),A
W 39938
B 39940
T 39941,10,B1:2:B1:6
M 39951,8 5700 LDIR
W 39951
B 39953
T 39954,5,B1:4
M 39959,17 5710 LD A,(EUGHGT)
W 39959
B 39961
T 39962,14,B1:2:B1:10
M 39976,11 5720 ADD A,4
W 39976
B 39978
T 39979,8,B1:3:B1:3
M 39987,17 5730 LD (EUGHGT),A
W 39987
B 39989
T 39990,14,B1:2:B1:10
M 40004,11 5740 CP 0C4H
W 40004
B 40006
T 40007,8,B1:2:B1:4
M 40015,16 5750 JR NZ,LOOPFT
W 40015
B 40017
T 40018,13,B1:2:B1:9
M 40031,15 5760 LD IX,MESSG
W 40031
B 40033
T 40034,12,B1:2:B1:8
M 40046,10 5770 LD C,4
W 40046
B 40048
T 40049,7,B1:2:B1:3
M 40056,15 5780 LD DE,40CAH
W 40056
B 40058
T 40059,12,B1:2:B1:8
M 40071,14 5790 CALL PMESS
W 40071
B 40073
T 40074,11,B1:4:B1:5
M 40085,15 5800 LD IX,MESSO
W 40085
B 40087
T 40088,12,B1:2:B1:8
M 40100,10 5810 LD C,4
W 40100
B 40102
T 40103,7,B1:2:B1:3
M 40110,15 5820 LD DE,40D2H
W 40110
B 40112
T 40113,12,B1:2:B1:8
M 40125,14 5830 CALL PMESS
W 40125
B 40127
T 40128,11,B1:4:B1:5
M 40139,11 5840 LD BC,0
W 40139
B 40141
T 40142,8,B1:2:B1:4
M 40150,10 5850 LD D,6
W 40150
B 40152
T 40153,7,B1:2:B1:3
M 40160,17 5860 TM91 DJNZ TM91
W 40160
B 40162
T 40163,14,4:B1:4:B1:4
M 40177,10 5870 LD A,? (actually LD A,C at #R35315)
W 40177
B 40179
T 40180,7,B1:2:B1:2:B1
B 40187
T 40190,2,B1:1
t 40192 Scrolling intro text
B 40240,1 #CHR169
T 40288
T 40336
T 40382
b 40448 Attribute data for the middle third of the title screen
B 40448,512,16
b 40960 Title screen graphic data
B 40960,4096,16
""".strip()

def write(text):
    sys.stdout.write('{0}\n'.format(text))

def write_guardians(snapshot, start, g_type):
    term = start + 28
    for addr in range(start, start + 28, 7):
        if snapshot[addr] == 255:
            term = addr
            break
    num_guardians = (term - start) // 7
    g_type_lower = g_type.lower()
    if num_guardians:
        write('D {0} The next {1} bytes define the {2} guardian{3}.'.format(start, num_guardians * 7, g_type_lower, 's' if num_guardians > 1 else ''))
        addr = start
        if num_guardians > 1:
            for i in range(num_guardians):
                suffix = ' (unused)' if snapshot[addr] == 0 else ''
                write('B {0},7 {1} guardian {2}{3}'.format(addr, g_type, i + 1, suffix))
                addr += 7
        else:
            write('B {0},7 {1} guardian'.format(addr, g_type))
            addr += 7
    else:
        write('D {0} There are no {1} guardians in this room.'.format(start, g_type_lower))
    if num_guardians < 4:
        write('B {0},1 Terminator'.format(term))
        return term + 1
    return term

def write_ctl(snapshot):
    write(HEADER)
    for a in range(45056, 65536, 1024):
        cavern_num = a // 1024 - 44
        cavern = snapshot[a:a + 1024]
        cavern_name = ''.join([chr(b) for b in cavern[512:544]]).strip()
        write('b {0} {1}'.format(a, cavern_name))
        write('D {0} #UDGTABLE {{ #CALL:cavern({0}) }} TABLE#'.format(a))
        write('D {0} The first 512 bytes are the attributes that define the layout of the cavern.'.format(a))
        write('B {0},512,16 Attributes'.format(a))

        # Cavern name
        write('D {0} The next 32 bytes contain the cavern name.'.format(a + 512))
        write('T {0},32 Cavern name'.format(a + 512))

        # Block graphics
        udgs = []
        attrs = []
        for addr, tile_type in ((a + 544, 'background'), (a + 553, 'floor'), (a + 562, 'crumbling_floor'), (a + 571, 'wall'), (a + 580, 'conveyor'), (a + 589, 'nasty1'), (a + 598, 'nasty2'), (a + 607, 'spare')):
            attr = snapshot[addr]
            attrs.append(attr)
            udgs.append('#UDG{0},{1}({2}_{3})'.format(addr + 1, attr, tile_type, cavern_num))
        tile_usage = [' (unused)'] * 8
        for b in snapshot[a:a + 512]:
            if b in attrs:
                tile_usage[attrs.index(b)] = ''
        udg_table = '#UDGTABLE { ' + ' | '.join(udgs) + ' } TABLE#'
        write('D {0} The next 72 bytes contain the attributes and graphic data for the tiles used to build the room.'.format(a + 544))
        write('D {0} {1}'.format(a + 544, udg_table))
        write('B {0},9,9 Background{1}'.format(a + 544, tile_usage[0]))
        write('B {0},9,9 Floor{1}'.format(a + 553, tile_usage[1]))
        write('B {0},9,9 Crumbling floor{1}'.format(a + 562, tile_usage[2]))
        write('B {0},9,9 Wall{1}'.format(a + 571, tile_usage[3]))
        write('B {0},9,9 Conveyor{1}'.format(a + 580, tile_usage[4]))
        write('B {0},9,9 Nasty 1{1}'.format(a + 589, tile_usage[5]))
        write('B {0},9,9 Nasty 2{1}'.format(a + 598, tile_usage[6]))
        write('B {0},9,9 Spare{1}'.format(a + 607, tile_usage[7]))

        # Miner Willy's start position
        write("D {0} The next 7 bytes specify Miner Willy's initial location and appearance in the cavern.".format(a + 616))
        write("B {0} Pixel y-coordinate * 2".format(a + 616))
        write("B {0} Sprite".format(a + 617))
        write("B {0} Direction".format(a + 618))
        write("B {0} Jump flag".format(a + 619))
        write("B {0} Coordinates".format(a + 620))
        write("B {0} Distance jumped".format(a + 622))

        # Conveyor
        write('D {0} The next 4 bytes define the direction, location and length of the conveyor.'.format(a + 623))
        direction = 'left' if snapshot[a + 623] == 0 else 'right'
        p1, p2 = snapshot[a + 624:a + 626]
        x = p1 & 31
        y = p2 & 8 + (p1 & 224) // 32
        length = snapshot[a + 626]
        write('B {0} Conveyor direction ({1}), location (x={2}, y={3}) and length ({4})'.format(a + 623, direction, x, y, length))

        # Border colour
        write('D {0} The next byte specifies the border colour.'.format(a + 627))
        write('B {0} Border colour'.format(a + 627))
        write('B {0} Unused'.format(a + 628))

        # Items
        write('D {0} The next 25 bytes specify the colour and location of the items in the cavern.'.format(a + 629))
        terminated = False
        for i, addr in enumerate(range(a + 629, a + 654, 5)):
            attr = snapshot[addr]
            if attr == 255:
                terminated = True
            suffix = ' (unused)' if terminated or attr == 0 else ''
            write('B {0},5 Item {1}{2}'.format(addr, i + 1, suffix))
        write('B {0}'.format(a + 654))

        # Portal
        attr = snapshot[a + 655]
        write('D {0} The next 37 bytes define the portal graphic and its location.'.format(a + 655))
        write('D {0} #UDGTABLE {{ #UDGARRAY2,{1},4,2;{2}-{3}-1-16(portal{4:02d}) }} TABLE#'.format(a + 655, attr, a + 656, a + 673, cavern_num))
        write('B {0},1 Attribute'.format(a + 655))
        write('B {0},32,8 Graphic data'.format(a + 656))
        p1, p2 = snapshot[a + 688:a + 690]
        x = p1 & 31
        y = 8 * (p2 & 1) + (p1 & 224) // 32
        write('B {0},4 Location (x={1}, y={2})'.format(a + 688, x, y))

        # Item
        attr = snapshot[a + 629]
        write('D {0} The next 8 bytes define the item graphic.'.format(a + 692))
        write('D {0} #UDGTABLE {{ #UDG{0},{1}(item{2:02d}) }} TABLE#'.format(a + 692, attr, cavern_num))
        write('B {0},8 Item graphic data'.format(a + 692))

        # Air
        write('D {0} The next two bytes define the initial air supply in the cavern.'.format(a + 700))
        write('B {0} Air'.format(a + 700))

        # Horizontal guardians
        end = write_guardians(snapshot, a + 702, 'Horizontal')

        # Special graphics and vertical guardians
        if cavern_num in (0, 1, 2, 4):
            write('B {0},{1},16 Unused'.format(end, a + 736 - end))
            if cavern_num == 0:
                desc = 'swordfish graphic that appears in The Final Barrier when the game is completed'
            elif cavern_num == 1:
                desc = 'plinth graphic that appears on the Game Over screen'
            elif cavern_num == 2:
                desc = 'boot graphic that appears on the Game Over screen'
            else:
                desc = 'Eugene graphic'
            write('D {0} The next 32 bytes define the {1}.'.format(a + 736, desc))
            write('D {0} #UDGTABLE {{ #UDGARRAY2,56,4,2;{1}-{2}-1-16(special{3}) }} TABLE#'.format(a + 736, a + 736, a + 753, cavern_num))
            write('B {0},32,16'.format(a + 736))
        else:
            write('B {0},{1},16 Unused'.format(end, a + 733 - end))
            end = write_guardians(snapshot, a + 733, 'Vertical')
            write('B {0},{1},16 Unused'.format(end, a + 768 - end))

        # Guardian graphic data
        gg_addr = a + 768
        gg_table = '#UDGTABLE { '
        macros = []
        for addr in range(gg_addr, gg_addr + 256, 32):
            img_fname = '{0}_guardian{1}'.format(cavern_name.lower().replace(' ', '_'), (addr & 224) // 32)
            macros.append('#UDGARRAY2,56,4,2;{0}-{1}-1-16({2})'.format(addr, addr + 17, img_fname))
        gg_table += ' | '.join(macros) + ' } TABLE#'
        write('D {0} The next 256 bytes are guardian graphic data.'.format(gg_addr))
        write('D {0} {1}'.format(gg_addr, gg_table))
        write('B {0},256,16'.format(gg_addr))

def show_usage():
    sys.stderr.write("""Usage: {0} manic_miner.[sna|z80]

  Generate a control file for Manic Miner.
""".format(os.path.basename(sys.argv[0])))
    sys.exit(1)

###############################################################################
# Begin
###############################################################################
if len(sys.argv) < 2:
    show_usage()

write_ctl(get_snapshot(sys.argv[1]))
