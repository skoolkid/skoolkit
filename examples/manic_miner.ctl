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
b 45056 Central Cavern
D 45056 #UDGTABLE { #CALL:cavern(45056) } TABLE#
D 45056 The first 512 bytes are the attributes that define the layout of the cavern.
B 45056,512,16 Attributes
D 45568 The next 32 bytes contain the cavern name.
T 45568,32 Cavern name
D 45600 The next 72 bytes contain the attributes and graphic data for the tiles used to build the room.
D 45600 #UDGTABLE { #UDG45601,0(background_0) | #UDG45610,66(floor_0) | #UDG45619,2(crumbling_floor_0) | #UDG45628,22(wall_0) | #UDG45637,4(conveyor_0) | #UDG45646,68(nasty1_0) | #UDG45655,5(nasty2_0) | #UDG45664,0(spare_0) } TABLE#
B 45600,9,9 Background
B 45609,9,9 Floor
B 45618,9,9 Crumbling floor
B 45627,9,9 Wall
B 45636,9,9 Conveyor
B 45645,9,9 Nasty 1
B 45654,9,9 Nasty 2
B 45663,9,9 Spare (unused)
D 45672 The next 7 bytes specify Miner Willy's initial location and appearance in the cavern.
B 45672 Pixel y-coordinate * 2
B 45673 Sprite
B 45674 Direction
B 45675 Jump flag
B 45676 Coordinates
B 45678 Distance jumped
D 45679 The next 4 bytes define the direction, location and length of the conveyor.
B 45679 Conveyor direction (left), location (x=8, y=8) and length (20)
D 45683 The next byte specifies the border colour.
B 45683 Border colour
B 45684 Unused
D 45685 The next 25 bytes specify the colour and location of the items in the cavern.
B 45685,5 Item 1
B 45690,5 Item 2
B 45695,5 Item 3
B 45700,5 Item 4
B 45705,5 Item 5
B 45710
D 45711 The next 37 bytes define the portal graphic and its location.
D 45711 #UDGTABLE { #UDGARRAY2,14,4,2;45712-45729-1-16(portal00) } TABLE#
B 45711,1 Attribute
B 45712,32,8 Graphic data
B 45744,4 Location (x=29, y=13)
D 45748 The next 8 bytes define the item graphic.
D 45748 #UDGTABLE { #UDG45748,3(item00) } TABLE#
B 45748,8 Item graphic data
D 45756 The next two bytes define the initial air supply in the cavern.
B 45756 Air
D 45758 The next 7 bytes define the horizontal guardian.
B 45758,7 Horizontal guardian
B 45765,1 Terminator
B 45766,26,16 Unused
D 45792 The next 32 bytes define the swordfish graphic that appears in The Final Barrier when the game is completed.
D 45792 #UDGTABLE { #UDGARRAY2,56,4,2;45792-45809-1-16(special0) } TABLE#
B 45792,32,16
D 45824 The next 256 bytes are guardian graphic data.
D 45824 #UDGTABLE { #UDGARRAY2,56,4,2;45824-45841-1-16(central_cavern_guardian0) | #UDGARRAY2,56,4,2;45856-45873-1-16(central_cavern_guardian1) | #UDGARRAY2,56,4,2;45888-45905-1-16(central_cavern_guardian2) | #UDGARRAY2,56,4,2;45920-45937-1-16(central_cavern_guardian3) | #UDGARRAY2,56,4,2;45952-45969-1-16(central_cavern_guardian4) | #UDGARRAY2,56,4,2;45984-46001-1-16(central_cavern_guardian5) | #UDGARRAY2,56,4,2;46016-46033-1-16(central_cavern_guardian6) | #UDGARRAY2,56,4,2;46048-46065-1-16(central_cavern_guardian7) } TABLE#
B 45824,256,16
b 46080 The Cold Room
D 46080 #UDGTABLE { #CALL:cavern(46080) } TABLE#
D 46080 The first 512 bytes are the attributes that define the layout of the cavern.
B 46080,512,16 Attributes
D 46592 The next 32 bytes contain the cavern name.
T 46592,32 Cavern name
D 46624 The next 72 bytes contain the attributes and graphic data for the tiles used to build the room.
D 46624 #UDGTABLE { #UDG46625,8(background_1) | #UDG46634,75(floor_1) | #UDG46643,11(crumbling_floor_1) | #UDG46652,22(wall_1) | #UDG46661,14(conveyor_1) | #UDG46670,12(nasty1_1) | #UDG46679,13(nasty2_1) | #UDG46688,0(spare_1) } TABLE#
B 46624,9,9 Background
B 46633,9,9 Floor
B 46642,9,9 Crumbling floor
B 46651,9,9 Wall
B 46660,9,9 Conveyor
B 46669,9,9 Nasty 1 (unused)
B 46678,9,9 Nasty 2
B 46687,9,9 Spare (unused)
D 46696 The next 7 bytes specify Miner Willy's initial location and appearance in the cavern.
B 46696 Pixel y-coordinate * 2
B 46697 Sprite
B 46698 Direction
B 46699 Jump flag
B 46700 Coordinates
B 46702 Distance jumped
D 46703 The next 4 bytes define the direction, location and length of the conveyor.
B 46703 Conveyor direction (right), location (x=3, y=8) and length (4)
D 46707 The next byte specifies the border colour.
B 46707 Border colour
B 46708 Unused
D 46709 The next 25 bytes specify the colour and location of the items in the cavern.
B 46709,5 Item 1
B 46714,5 Item 2
B 46719,5 Item 3
B 46724,5 Item 4
B 46729,5 Item 5
B 46734
D 46735 The next 37 bytes define the portal graphic and its location.
D 46735 #UDGTABLE { #UDGARRAY2,83,4,2;46736-46753-1-16(portal01) } TABLE#
B 46735,1 Attribute
B 46736,32,8 Graphic data
B 46768,4 Location (x=29, y=13)
D 46772 The next 8 bytes define the item graphic.
D 46772 #UDGTABLE { #UDG46772,11(item01) } TABLE#
B 46772,8 Item graphic data
D 46780 The next two bytes define the initial air supply in the cavern.
B 46780 Air
D 46782 The next 14 bytes define the horizontal guardians.
B 46782,7 Horizontal guardian 1
B 46789,7 Horizontal guardian 2
B 46796,1 Terminator
B 46797,19,16 Unused
D 46816 The next 32 bytes define the plinth graphic that appears on the Game Over screen.
D 46816 #UDGTABLE { #UDGARRAY2,56,4,2;46816-46833-1-16(special1) } TABLE#
B 46816,32,16
D 46848 The next 256 bytes are guardian graphic data.
D 46848 #UDGTABLE { #UDGARRAY2,56,4,2;46848-46865-1-16(the_cold_room_guardian0) | #UDGARRAY2,56,4,2;46880-46897-1-16(the_cold_room_guardian1) | #UDGARRAY2,56,4,2;46912-46929-1-16(the_cold_room_guardian2) | #UDGARRAY2,56,4,2;46944-46961-1-16(the_cold_room_guardian3) | #UDGARRAY2,56,4,2;46976-46993-1-16(the_cold_room_guardian4) | #UDGARRAY2,56,4,2;47008-47025-1-16(the_cold_room_guardian5) | #UDGARRAY2,56,4,2;47040-47057-1-16(the_cold_room_guardian6) | #UDGARRAY2,56,4,2;47072-47089-1-16(the_cold_room_guardian7) } TABLE#
B 46848,256,16
b 47104 The Menagerie
D 47104 #UDGTABLE { #CALL:cavern(47104) } TABLE#
D 47104 The first 512 bytes are the attributes that define the layout of the cavern.
B 47104,512,16 Attributes
D 47616 The next 32 bytes contain the cavern name.
T 47616,32 Cavern name
D 47648 The next 72 bytes contain the attributes and graphic data for the tiles used to build the room.
D 47648 #UDGTABLE { #UDG47649,0(background_2) | #UDG47658,69(floor_2) | #UDG47667,5(crumbling_floor_2) | #UDG47676,13(wall_2) | #UDG47685,2(conveyor_2) | #UDG47694,6(nasty1_2) | #UDG47703,67(nasty2_2) | #UDG47712,3(spare_2) } TABLE#
B 47648,9,9 Background
B 47657,9,9 Floor
B 47666,9,9 Crumbling floor
B 47675,9,9 Wall
B 47684,9,9 Conveyor
B 47693,9,9 Nasty 1 (unused)
B 47702,9,9 Nasty 2
B 47711,9,9 Spare
D 47720 The next 7 bytes specify Miner Willy's initial location and appearance in the cavern.
B 47720 Pixel y-coordinate * 2
B 47721 Sprite
B 47722 Direction
B 47723 Jump flag
B 47724 Coordinates
B 47726 Distance jumped
D 47727 The next 4 bytes define the direction, location and length of the conveyor.
B 47727 Conveyor direction (left), location (x=6, y=8) and length (6)
D 47731 The next byte specifies the border colour.
B 47731 Border colour
B 47732 Unused
D 47733 The next 25 bytes specify the colour and location of the items in the cavern.
B 47733,5 Item 1
B 47738,5 Item 2
B 47743,5 Item 3
B 47748,5 Item 4
B 47753,5 Item 5
B 47758
D 47759 The next 37 bytes define the portal graphic and its location.
D 47759 #UDGTABLE { #UDGARRAY2,14,4,2;47760-47777-1-16(portal02) } TABLE#
B 47759,1 Attribute
B 47760,32,8 Graphic data
B 47792,4 Location (x=29, y=11)
D 47796 The next 8 bytes define the item graphic.
D 47796 #UDGTABLE { #UDG47796,3(item02) } TABLE#
B 47796,8 Item graphic data
D 47804 The next two bytes define the initial air supply in the cavern.
B 47804 Air
D 47806 The next 21 bytes define the horizontal guardians.
B 47806,7 Horizontal guardian 1
B 47813,7 Horizontal guardian 2
B 47820,7 Horizontal guardian 3
B 47827,1 Terminator
B 47828,12,16 Unused
D 47840 The next 32 bytes define the boot graphic that appears on the Game Over screen.
D 47840 #UDGTABLE { #UDGARRAY2,56,4,2;47840-47857-1-16(special2) } TABLE#
B 47840,32,16
D 47872 The next 256 bytes are guardian graphic data.
D 47872 #UDGTABLE { #UDGARRAY2,56,4,2;47872-47889-1-16(the_menagerie_guardian0) | #UDGARRAY2,56,4,2;47904-47921-1-16(the_menagerie_guardian1) | #UDGARRAY2,56,4,2;47936-47953-1-16(the_menagerie_guardian2) | #UDGARRAY2,56,4,2;47968-47985-1-16(the_menagerie_guardian3) | #UDGARRAY2,56,4,2;48000-48017-1-16(the_menagerie_guardian4) | #UDGARRAY2,56,4,2;48032-48049-1-16(the_menagerie_guardian5) | #UDGARRAY2,56,4,2;48064-48081-1-16(the_menagerie_guardian6) | #UDGARRAY2,56,4,2;48096-48113-1-16(the_menagerie_guardian7) } TABLE#
B 47872,256,16
b 48128 Abandoned Uranium Workings
D 48128 #UDGTABLE { #CALL:cavern(48128) } TABLE#
D 48128 The first 512 bytes are the attributes that define the layout of the cavern.
B 48128,512,16 Attributes
D 48640 The next 32 bytes contain the cavern name.
T 48640,32 Cavern name
D 48672 The next 72 bytes contain the attributes and graphic data for the tiles used to build the room.
D 48672 #UDGTABLE { #UDG48673,0(background_3) | #UDG48682,70(floor_3) | #UDG48691,6(crumbling_floor_3) | #UDG48700,41(wall_3) | #UDG48709,3(conveyor_3) | #UDG48718,4(nasty1_3) | #UDG48727,5(nasty2_3) | #UDG48736,0(spare_3) } TABLE#
B 48672,9,9 Background
B 48681,9,9 Floor
B 48690,9,9 Crumbling floor
B 48699,9,9 Wall
B 48708,9,9 Conveyor
B 48717,9,9 Nasty 1 (unused)
B 48726,9,9 Nasty 2
B 48735,9,9 Spare (unused)
D 48744 The next 7 bytes specify Miner Willy's initial location and appearance in the cavern.
B 48744 Pixel y-coordinate * 2
B 48745 Sprite
B 48746 Direction
B 48747 Jump flag
B 48748 Coordinates
B 48750 Distance jumped
D 48751 The next 4 bytes define the direction, location and length of the conveyor.
B 48751 Conveyor direction (right), location (x=1, y=8) and length (3)
D 48755 The next byte specifies the border colour.
B 48755 Border colour
B 48756 Unused
D 48757 The next 25 bytes specify the colour and location of the items in the cavern.
B 48757,5 Item 1
B 48762,5 Item 2
B 48767,5 Item 3
B 48772,5 Item 4
B 48777,5 Item 5
B 48782
D 48783 The next 37 bytes define the portal graphic and its location.
D 48783 #UDGTABLE { #UDGARRAY2,14,4,2;48784-48801-1-16(portal03) } TABLE#
B 48783,1 Attribute
B 48784,32,8 Graphic data
B 48816,4 Location (x=29, y=1)
D 48820 The next 8 bytes define the item graphic.
D 48820 #UDGTABLE { #UDG48820,3(item03) } TABLE#
B 48820,8 Item graphic data
D 48828 The next two bytes define the initial air supply in the cavern.
B 48828 Air
D 48830 The next 14 bytes define the horizontal guardians.
B 48830,7 Horizontal guardian 1
B 48837,7 Horizontal guardian 2
B 48844,1 Terminator
B 48845,16,16 Unused
D 48861 There are no vertical guardians in this room.
B 48861,1 Terminator
B 48862,34,16 Unused
D 48896 The next 256 bytes are guardian graphic data.
D 48896 #UDGTABLE { #UDGARRAY2,56,4,2;48896-48913-1-16(abandoned_uranium_workings_guardian0) | #UDGARRAY2,56,4,2;48928-48945-1-16(abandoned_uranium_workings_guardian1) | #UDGARRAY2,56,4,2;48960-48977-1-16(abandoned_uranium_workings_guardian2) | #UDGARRAY2,56,4,2;48992-49009-1-16(abandoned_uranium_workings_guardian3) | #UDGARRAY2,56,4,2;49024-49041-1-16(abandoned_uranium_workings_guardian4) | #UDGARRAY2,56,4,2;49056-49073-1-16(abandoned_uranium_workings_guardian5) | #UDGARRAY2,56,4,2;49088-49105-1-16(abandoned_uranium_workings_guardian6) | #UDGARRAY2,56,4,2;49120-49137-1-16(abandoned_uranium_workings_guardian7) } TABLE#
B 48896,256,16
b 49152 Eugene's Lair
D 49152 #UDGTABLE { #CALL:cavern(49152) } TABLE#
D 49152 The first 512 bytes are the attributes that define the layout of the cavern.
B 49152,512,16 Attributes
D 49664 The next 32 bytes contain the cavern name.
T 49664,32 Cavern name
D 49696 The next 72 bytes contain the attributes and graphic data for the tiles used to build the room.
D 49696 #UDGTABLE { #UDG49697,16(background_4) | #UDG49706,21(floor_4) | #UDG49715,20(crumbling_floor_4) | #UDG49724,46(wall_4) | #UDG49733,86(conveyor_4) | #UDG49742,22(nasty1_4) | #UDG49751,19(nasty2_4) | #UDG49760,0(spare_4) } TABLE#
B 49696,9,9 Background
B 49705,9,9 Floor
B 49714,9,9 Crumbling floor
B 49723,9,9 Wall
B 49732,9,9 Conveyor
B 49741,9,9 Nasty 1
B 49750,9,9 Nasty 2
B 49759,9,9 Spare (unused)
D 49768 The next 7 bytes specify Miner Willy's initial location and appearance in the cavern.
B 49768 Pixel y-coordinate * 2
B 49769 Sprite
B 49770 Direction
B 49771 Jump flag
B 49772 Coordinates
B 49774 Distance jumped
D 49775 The next 4 bytes define the direction, location and length of the conveyor.
B 49775 Conveyor direction (left), location (x=18, y=8) and length (10)
D 49779 The next byte specifies the border colour.
B 49779 Border colour
B 49780 Unused
D 49781 The next 25 bytes specify the colour and location of the items in the cavern.
B 49781,5 Item 1
B 49786,5 Item 2
B 49791,5 Item 3
B 49796,5 Item 4
B 49801,5 Item 5
B 49806
D 49807 The next 37 bytes define the portal graphic and its location.
D 49807 #UDGTABLE { #UDGARRAY2,87,4,2;49808-49825-1-16(portal04) } TABLE#
B 49807,1 Attribute
B 49808,32,8 Graphic data
B 49840,4 Location (x=15, y=13)
D 49844 The next 8 bytes define the item graphic.
D 49844 #UDGTABLE { #UDG49844,19(item04) } TABLE#
B 49844,8 Item graphic data
D 49852 The next two bytes define the initial air supply in the cavern.
B 49852 Air
D 49854 The next 14 bytes define the horizontal guardians.
B 49854,7 Horizontal guardian 1
B 49861,7 Horizontal guardian 2
B 49868,1 Terminator
B 49869,19,16 Unused
D 49888 The next 32 bytes define the Eugene graphic.
D 49888 #UDGTABLE { #UDGARRAY2,56,4,2;49888-49905-1-16(special4) } TABLE#
B 49888,32,16
D 49920 The next 256 bytes are guardian graphic data.
D 49920 #UDGTABLE { #UDGARRAY2,56,4,2;49920-49937-1-16(eugene's_lair_guardian0) | #UDGARRAY2,56,4,2;49952-49969-1-16(eugene's_lair_guardian1) | #UDGARRAY2,56,4,2;49984-50001-1-16(eugene's_lair_guardian2) | #UDGARRAY2,56,4,2;50016-50033-1-16(eugene's_lair_guardian3) | #UDGARRAY2,56,4,2;50048-50065-1-16(eugene's_lair_guardian4) | #UDGARRAY2,56,4,2;50080-50097-1-16(eugene's_lair_guardian5) | #UDGARRAY2,56,4,2;50112-50129-1-16(eugene's_lair_guardian6) | #UDGARRAY2,56,4,2;50144-50161-1-16(eugene's_lair_guardian7) } TABLE#
B 49920,256,16
b 50176 Processing Plant
D 50176 #UDGTABLE { #CALL:cavern(50176) } TABLE#
D 50176 The first 512 bytes are the attributes that define the layout of the cavern.
B 50176,512,16 Attributes
D 50688 The next 32 bytes contain the cavern name.
T 50688,32 Cavern name
D 50720 The next 72 bytes contain the attributes and graphic data for the tiles used to build the room.
D 50720 #UDGTABLE { #UDG50721,0(background_5) | #UDG50730,68(floor_5) | #UDG50739,4(crumbling_floor_5) | #UDG50748,22(wall_5) | #UDG50757,5(conveyor_5) | #UDG50766,67(nasty1_5) | #UDG50775,6(nasty2_5) | #UDG50784,0(spare_5) } TABLE#
B 50720,9,9 Background
B 50729,9,9 Floor
B 50738,9,9 Crumbling floor (unused)
B 50747,9,9 Wall
B 50756,9,9 Conveyor
B 50765,9,9 Nasty 1
B 50774,9,9 Nasty 2
B 50783,9,9 Spare (unused)
D 50792 The next 7 bytes specify Miner Willy's initial location and appearance in the cavern.
B 50792 Pixel y-coordinate * 2
B 50793 Sprite
B 50794 Direction
B 50795 Jump flag
B 50796 Coordinates
B 50798 Distance jumped
D 50799 The next 4 bytes define the direction, location and length of the conveyor.
B 50799 Conveyor direction (left), location (x=3, y=8) and length (4)
D 50803 The next byte specifies the border colour.
B 50803 Border colour
B 50804 Unused
D 50805 The next 25 bytes specify the colour and location of the items in the cavern.
B 50805,5 Item 1
B 50810,5 Item 2
B 50815,5 Item 3
B 50820,5 Item 4
B 50825,5 Item 5
B 50830
D 50831 The next 37 bytes define the portal graphic and its location.
D 50831 #UDGTABLE { #UDGARRAY2,14,4,2;50832-50849-1-16(portal05) } TABLE#
B 50831,1 Attribute
B 50832,32,8 Graphic data
B 50864,4 Location (x=29, y=0)
D 50868 The next 8 bytes define the item graphic.
D 50868 #UDGTABLE { #UDG50868,3(item05) } TABLE#
B 50868,8 Item graphic data
D 50876 The next two bytes define the initial air supply in the cavern.
B 50876 Air
D 50878 The next 28 bytes define the horizontal guardians.
B 50878,7 Horizontal guardian 1
B 50885,7 Horizontal guardian 2
B 50892,7 Horizontal guardian 3
B 50899,7 Horizontal guardian 4
B 50906,3,16 Unused
D 50909 There are no vertical guardians in this room.
B 50909,1 Terminator
B 50910,34,16 Unused
D 50944 The next 256 bytes are guardian graphic data.
D 50944 #UDGTABLE { #UDGARRAY2,56,4,2;50944-50961-1-16(processing_plant_guardian0) | #UDGARRAY2,56,4,2;50976-50993-1-16(processing_plant_guardian1) | #UDGARRAY2,56,4,2;51008-51025-1-16(processing_plant_guardian2) | #UDGARRAY2,56,4,2;51040-51057-1-16(processing_plant_guardian3) | #UDGARRAY2,56,4,2;51072-51089-1-16(processing_plant_guardian4) | #UDGARRAY2,56,4,2;51104-51121-1-16(processing_plant_guardian5) | #UDGARRAY2,56,4,2;51136-51153-1-16(processing_plant_guardian6) | #UDGARRAY2,56,4,2;51168-51185-1-16(processing_plant_guardian7) } TABLE#
B 50944,256,16
b 51200 The Vat
D 51200 #UDGTABLE { #CALL:cavern(51200) } TABLE#
D 51200 The first 512 bytes are the attributes that define the layout of the cavern.
B 51200,512,16 Attributes
D 51712 The next 32 bytes contain the cavern name.
T 51712,32 Cavern name
D 51744 The next 72 bytes contain the attributes and graphic data for the tiles used to build the room.
D 51744 #UDGTABLE { #UDG51745,0(background_6) | #UDG51754,70(floor_6) | #UDG51763,2(crumbling_floor_6) | #UDG51772,77(wall_6) | #UDG51781,4(conveyor_6) | #UDG51790,21(nasty1_6) | #UDG51799,22(nasty2_6) | #UDG51808,0(spare_6) } TABLE#
B 51744,9,9 Background
B 51753,9,9 Floor
B 51762,9,9 Crumbling floor
B 51771,9,9 Wall
B 51780,9,9 Conveyor
B 51789,9,9 Nasty 1 (unused)
B 51798,9,9 Nasty 2
B 51807,9,9 Spare (unused)
D 51816 The next 7 bytes specify Miner Willy's initial location and appearance in the cavern.
B 51816 Pixel y-coordinate * 2
B 51817 Sprite
B 51818 Direction
B 51819 Jump flag
B 51820 Coordinates
B 51822 Distance jumped
D 51823 The next 4 bytes define the direction, location and length of the conveyor.
B 51823 Conveyor direction (left), location (x=7, y=0) and length (5)
D 51827 The next byte specifies the border colour.
B 51827 Border colour
B 51828 Unused
D 51829 The next 25 bytes specify the colour and location of the items in the cavern.
B 51829,5 Item 1
B 51834,5 Item 2
B 51839,5 Item 3
B 51844,5 Item 4
B 51849,5 Item 5
B 51854
D 51855 The next 37 bytes define the portal graphic and its location.
D 51855 #UDGTABLE { #UDGARRAY2,11,4,2;51856-51873-1-16(portal06) } TABLE#
B 51855,1 Attribute
B 51856,32,8 Graphic data
B 51888,4 Location (x=15, y=13)
D 51892 The next 8 bytes define the item graphic.
D 51892 #UDGTABLE { #UDG51892,19(item06) } TABLE#
B 51892,8 Item graphic data
D 51900 The next two bytes define the initial air supply in the cavern.
B 51900 Air
D 51902 The next 21 bytes define the horizontal guardians.
B 51902,7 Horizontal guardian 1
B 51909,7 Horizontal guardian 2
B 51916,7 Horizontal guardian 3
B 51923,1 Terminator
B 51924,9,16 Unused
D 51933 There are no vertical guardians in this room.
B 51933,1 Terminator
B 51934,34,16 Unused
D 51968 The next 256 bytes are guardian graphic data.
D 51968 #UDGTABLE { #UDGARRAY2,56,4,2;51968-51985-1-16(the_vat_guardian0) | #UDGARRAY2,56,4,2;52000-52017-1-16(the_vat_guardian1) | #UDGARRAY2,56,4,2;52032-52049-1-16(the_vat_guardian2) | #UDGARRAY2,56,4,2;52064-52081-1-16(the_vat_guardian3) | #UDGARRAY2,56,4,2;52096-52113-1-16(the_vat_guardian4) | #UDGARRAY2,56,4,2;52128-52145-1-16(the_vat_guardian5) | #UDGARRAY2,56,4,2;52160-52177-1-16(the_vat_guardian6) | #UDGARRAY2,56,4,2;52192-52209-1-16(the_vat_guardian7) } TABLE#
B 51968,256,16
b 52224 Miner Willy meets the Kong Beast
D 52224 #UDGTABLE { #CALL:cavern(52224) } TABLE#
D 52224 The first 512 bytes are the attributes that define the layout of the cavern.
B 52224,512,16 Attributes
D 52736 The next 32 bytes contain the cavern name.
T 52736,32 Cavern name
D 52768 The next 72 bytes contain the attributes and graphic data for the tiles used to build the room.
D 52768 #UDGTABLE { #UDG52769,0(background_7) | #UDG52778,66(floor_7) | #UDG52787,2(crumbling_floor_7) | #UDG52796,114(wall_7) | #UDG52805,68(conveyor_7) | #UDG52814,4(nasty1_7) | #UDG52823,5(nasty2_7) | #UDG52832,6(spare_7) } TABLE#
B 52768,9,9 Background
B 52777,9,9 Floor
B 52786,9,9 Crumbling floor (unused)
B 52795,9,9 Wall
B 52804,9,9 Conveyor
B 52813,9,9 Nasty 1
B 52822,9,9 Nasty 2
B 52831,9,9 Spare
D 52840 The next 7 bytes specify Miner Willy's initial location and appearance in the cavern.
B 52840 Pixel y-coordinate * 2
B 52841 Sprite
B 52842 Direction
B 52843 Jump flag
B 52844 Coordinates
B 52846 Distance jumped
D 52847 The next 4 bytes define the direction, location and length of the conveyor.
B 52847 Conveyor direction (right), location (x=11, y=8) and length (3)
D 52851 The next byte specifies the border colour.
B 52851 Border colour
B 52852 Unused
D 52853 The next 25 bytes specify the colour and location of the items in the cavern.
B 52853,5 Item 1
B 52858,5 Item 2
B 52863,5 Item 3
B 52868,5 Item 4
B 52873,5 Item 5 (unused)
B 52878
D 52879 The next 37 bytes define the portal graphic and its location.
D 52879 #UDGTABLE { #UDGARRAY2,14,4,2;52880-52897-1-16(portal07) } TABLE#
B 52879,1 Attribute
B 52880,32,8 Graphic data
B 52912,4 Location (x=15, y=13)
D 52916 The next 8 bytes define the item graphic.
D 52916 #UDGTABLE { #UDG52916,3(item07) } TABLE#
B 52916,8 Item graphic data
D 52924 The next two bytes define the initial air supply in the cavern.
B 52924 Air
D 52926 The next 28 bytes define the horizontal guardians.
B 52926,7 Horizontal guardian 1
B 52933,7 Horizontal guardian 2
B 52940,7 Horizontal guardian 3 (unused)
B 52947,7 Horizontal guardian 4
B 52954,3,16 Unused
D 52957 There are no vertical guardians in this room.
B 52957,1 Terminator
B 52958,34,16 Unused
D 52992 The next 256 bytes are guardian graphic data.
D 52992 #UDGTABLE { #UDGARRAY2,56,4,2;52992-53009-1-16(miner_willy_meets_the_kong_beast_guardian0) | #UDGARRAY2,56,4,2;53024-53041-1-16(miner_willy_meets_the_kong_beast_guardian1) | #UDGARRAY2,56,4,2;53056-53073-1-16(miner_willy_meets_the_kong_beast_guardian2) | #UDGARRAY2,56,4,2;53088-53105-1-16(miner_willy_meets_the_kong_beast_guardian3) | #UDGARRAY2,56,4,2;53120-53137-1-16(miner_willy_meets_the_kong_beast_guardian4) | #UDGARRAY2,56,4,2;53152-53169-1-16(miner_willy_meets_the_kong_beast_guardian5) | #UDGARRAY2,56,4,2;53184-53201-1-16(miner_willy_meets_the_kong_beast_guardian6) | #UDGARRAY2,56,4,2;53216-53233-1-16(miner_willy_meets_the_kong_beast_guardian7) } TABLE#
B 52992,256,16
b 53248 Wacky Amoebatrons
D 53248 #UDGTABLE { #CALL:cavern(53248) } TABLE#
D 53248 The first 512 bytes are the attributes that define the layout of the cavern.
B 53248,512,16 Attributes
D 53760 The next 32 bytes contain the cavern name.
T 53760,32 Cavern name
D 53792 The next 72 bytes contain the attributes and graphic data for the tiles used to build the room.
D 53792 #UDGTABLE { #UDG53793,0(background_8) | #UDG53802,6(floor_8) | #UDG53811,66(crumbling_floor_8) | #UDG53820,22(wall_8) | #UDG53829,4(conveyor_8) | #UDG53838,68(nasty1_8) | #UDG53847,5(nasty2_8) | #UDG53856,0(spare_8) } TABLE#
B 53792,9,9 Background
B 53801,9,9 Floor
B 53810,9,9 Crumbling floor (unused)
B 53819,9,9 Wall
B 53828,9,9 Conveyor
B 53837,9,9 Nasty 1 (unused)
B 53846,9,9 Nasty 2 (unused)
B 53855,9,9 Spare (unused)
D 53864 The next 7 bytes specify Miner Willy's initial location and appearance in the cavern.
B 53864 Pixel y-coordinate * 2
B 53865 Sprite
B 53866 Direction
B 53867 Jump flag
B 53868 Coordinates
B 53870 Distance jumped
D 53871 The next 4 bytes define the direction, location and length of the conveyor.
B 53871 Conveyor direction (right), location (x=12, y=8) and length (8)
D 53875 The next byte specifies the border colour.
B 53875 Border colour
B 53876 Unused
D 53877 The next 25 bytes specify the colour and location of the items in the cavern.
B 53877,5 Item 1
B 53882,5 Item 2 (unused)
B 53887,5 Item 3 (unused)
B 53892,5 Item 4 (unused)
B 53897,5 Item 5 (unused)
B 53902
D 53903 The next 37 bytes define the portal graphic and its location.
D 53903 #UDGTABLE { #UDGARRAY2,14,4,2;53904-53921-1-16(portal08) } TABLE#
B 53903,1 Attribute
B 53904,32,8 Graphic data
B 53936,4 Location (x=1, y=0)
D 53940 The next 8 bytes define the item graphic.
D 53940 #UDGTABLE { #UDG53940,3(item08) } TABLE#
B 53940,8 Item graphic data
D 53948 The next two bytes define the initial air supply in the cavern.
B 53948 Air
D 53950 The next 28 bytes define the horizontal guardians.
B 53950,7 Horizontal guardian 1
B 53957,7 Horizontal guardian 2
B 53964,7 Horizontal guardian 3 (unused)
B 53971,7 Horizontal guardian 4 (unused)
B 53978,3,16 Unused
D 53981 The next 28 bytes define the vertical guardians.
B 53981,7 Vertical guardian 1
B 53988,7 Vertical guardian 2
B 53995,7 Vertical guardian 3
B 54002,7 Vertical guardian 4
B 54009,7,16 Unused
D 54016 The next 256 bytes are guardian graphic data.
D 54016 #UDGTABLE { #UDGARRAY2,56,4,2;54016-54033-1-16(wacky_amoebatrons_guardian0) | #UDGARRAY2,56,4,2;54048-54065-1-16(wacky_amoebatrons_guardian1) | #UDGARRAY2,56,4,2;54080-54097-1-16(wacky_amoebatrons_guardian2) | #UDGARRAY2,56,4,2;54112-54129-1-16(wacky_amoebatrons_guardian3) | #UDGARRAY2,56,4,2;54144-54161-1-16(wacky_amoebatrons_guardian4) | #UDGARRAY2,56,4,2;54176-54193-1-16(wacky_amoebatrons_guardian5) | #UDGARRAY2,56,4,2;54208-54225-1-16(wacky_amoebatrons_guardian6) | #UDGARRAY2,56,4,2;54240-54257-1-16(wacky_amoebatrons_guardian7) } TABLE#
B 54016,256,16
b 54272 The Endorian Forest
D 54272 #UDGTABLE { #CALL:cavern(54272) } TABLE#
D 54272 The first 512 bytes are the attributes that define the layout of the cavern.
B 54272,512,16 Attributes
D 54784 The next 32 bytes contain the cavern name.
T 54784,32 Cavern name
D 54816 The next 72 bytes contain the attributes and graphic data for the tiles used to build the room.
D 54816 #UDGTABLE { #UDG54817,0(background_9) | #UDG54826,68(floor_9) | #UDG54835,2(crumbling_floor_9) | #UDG54844,22(wall_9) | #UDG54853,67(conveyor_9) | #UDG54862,69(nasty1_9) | #UDG54871,4(nasty2_9) | #UDG54880,5(spare_9) } TABLE#
B 54816,9,9 Background
B 54825,9,9 Floor
B 54834,9,9 Crumbling floor
B 54843,9,9 Wall
B 54852,9,9 Conveyor (unused)
B 54861,9,9 Nasty 1 (unused)
B 54870,9,9 Nasty 2
B 54879,9,9 Spare
D 54888 The next 7 bytes specify Miner Willy's initial location and appearance in the cavern.
B 54888 Pixel y-coordinate * 2
B 54889 Sprite
B 54890 Direction
B 54891 Jump flag
B 54892 Coordinates
B 54894 Distance jumped
D 54895 The next 4 bytes define the direction, location and length of the conveyor.
B 54895 Conveyor direction (left), location (x=19, y=0) and length (1)
D 54899 The next byte specifies the border colour.
B 54899 Border colour
B 54900 Unused
D 54901 The next 25 bytes specify the colour and location of the items in the cavern.
B 54901,5 Item 1
B 54906,5 Item 2
B 54911,5 Item 3
B 54916,5 Item 4
B 54921,5 Item 5
B 54926
D 54927 The next 37 bytes define the portal graphic and its location.
D 54927 #UDGTABLE { #UDGARRAY2,30,4,2;54928-54945-1-16(portal09) } TABLE#
B 54927,1 Attribute
B 54928,32,8 Graphic data
B 54960,4 Location (x=12, y=13)
D 54964 The next 8 bytes define the item graphic.
D 54964 #UDGTABLE { #UDG54964,3(item09) } TABLE#
B 54964,8 Item graphic data
D 54972 The next two bytes define the initial air supply in the cavern.
B 54972 Air
D 54974 The next 28 bytes define the horizontal guardians.
B 54974,7 Horizontal guardian 1
B 54981,7 Horizontal guardian 2
B 54988,7 Horizontal guardian 3
B 54995,7 Horizontal guardian 4
B 55002,3,16 Unused
D 55005 There are no vertical guardians in this room.
B 55005,1 Terminator
B 55006,34,16 Unused
D 55040 The next 256 bytes are guardian graphic data.
D 55040 #UDGTABLE { #UDGARRAY2,56,4,2;55040-55057-1-16(the_endorian_forest_guardian0) | #UDGARRAY2,56,4,2;55072-55089-1-16(the_endorian_forest_guardian1) | #UDGARRAY2,56,4,2;55104-55121-1-16(the_endorian_forest_guardian2) | #UDGARRAY2,56,4,2;55136-55153-1-16(the_endorian_forest_guardian3) | #UDGARRAY2,56,4,2;55168-55185-1-16(the_endorian_forest_guardian4) | #UDGARRAY2,56,4,2;55200-55217-1-16(the_endorian_forest_guardian5) | #UDGARRAY2,56,4,2;55232-55249-1-16(the_endorian_forest_guardian6) | #UDGARRAY2,56,4,2;55264-55281-1-16(the_endorian_forest_guardian7) } TABLE#
B 55040,256,16
b 55296 Attack of the Mutant Telephones
D 55296 #UDGTABLE { #CALL:cavern(55296) } TABLE#
D 55296 The first 512 bytes are the attributes that define the layout of the cavern.
B 55296,512,16 Attributes
D 55808 The next 32 bytes contain the cavern name.
T 55808,32 Cavern name
D 55840 The next 72 bytes contain the attributes and graphic data for the tiles used to build the room.
D 55840 #UDGTABLE { #UDG55841,0(background_10) | #UDG55850,65(floor_10) | #UDG55859,1(crumbling_floor_10) | #UDG55868,14(wall_10) | #UDG55877,6(conveyor_10) | #UDG55886,70(nasty1_10) | #UDG55895,66(nasty2_10) | #UDG55904,69(spare_10) } TABLE#
B 55840,9,9 Background
B 55849,9,9 Floor
B 55858,9,9 Crumbling floor
B 55867,9,9 Wall
B 55876,9,9 Conveyor
B 55885,9,9 Nasty 1
B 55894,9,9 Nasty 2
B 55903,9,9 Spare
D 55912 The next 7 bytes specify Miner Willy's initial location and appearance in the cavern.
B 55912 Pixel y-coordinate * 2
B 55913 Sprite
B 55914 Direction
B 55915 Jump flag
B 55916 Coordinates
B 55918 Distance jumped
D 55919 The next 4 bytes define the direction, location and length of the conveyor.
B 55919 Conveyor direction (left), location (x=5, y=8) and length (2)
D 55923 The next byte specifies the border colour.
B 55923 Border colour
B 55924 Unused
D 55925 The next 25 bytes specify the colour and location of the items in the cavern.
B 55925,5 Item 1
B 55930,5 Item 2
B 55935,5 Item 3
B 55940,5 Item 4
B 55945,5 Item 5
B 55950
D 55951 The next 37 bytes define the portal graphic and its location.
D 55951 #UDGTABLE { #UDGARRAY2,86,4,2;55952-55969-1-16(portal10) } TABLE#
B 55951,1 Attribute
B 55952,32,8 Graphic data
B 55984,4 Location (x=1, y=1)
D 55988 The next 8 bytes define the item graphic.
D 55988 #UDGTABLE { #UDG55988,3(item10) } TABLE#
B 55988,8 Item graphic data
D 55996 The next two bytes define the initial air supply in the cavern.
B 55996 Air
D 55998 The next 21 bytes define the horizontal guardians.
B 55998,7 Horizontal guardian 1
B 56005,7 Horizontal guardian 2
B 56012,7 Horizontal guardian 3
B 56019,1 Terminator
B 56020,9,16 Unused
D 56029 The next 28 bytes define the vertical guardians.
B 56029,7 Vertical guardian 1
B 56036,7 Vertical guardian 2
B 56043,7 Vertical guardian 3
B 56050,7 Vertical guardian 4
B 56057,7,16 Unused
D 56064 The next 256 bytes are guardian graphic data.
D 56064 #UDGTABLE { #UDGARRAY2,56,4,2;56064-56081-1-16(attack_of_the_mutant_telephones_guardian0) | #UDGARRAY2,56,4,2;56096-56113-1-16(attack_of_the_mutant_telephones_guardian1) | #UDGARRAY2,56,4,2;56128-56145-1-16(attack_of_the_mutant_telephones_guardian2) | #UDGARRAY2,56,4,2;56160-56177-1-16(attack_of_the_mutant_telephones_guardian3) | #UDGARRAY2,56,4,2;56192-56209-1-16(attack_of_the_mutant_telephones_guardian4) | #UDGARRAY2,56,4,2;56224-56241-1-16(attack_of_the_mutant_telephones_guardian5) | #UDGARRAY2,56,4,2;56256-56273-1-16(attack_of_the_mutant_telephones_guardian6) | #UDGARRAY2,56,4,2;56288-56305-1-16(attack_of_the_mutant_telephones_guardian7) } TABLE#
B 56064,256,16
b 56320 Return of the Alien Kong Beast
D 56320 #UDGTABLE { #CALL:cavern(56320) } TABLE#
D 56320 The first 512 bytes are the attributes that define the layout of the cavern.
B 56320,512,16 Attributes
D 56832 The next 32 bytes contain the cavern name.
T 56832,32 Cavern name
D 56864 The next 72 bytes contain the attributes and graphic data for the tiles used to build the room.
D 56864 #UDGTABLE { #UDG56865,0(background_11) | #UDG56874,67(floor_11) | #UDG56883,3(crumbling_floor_11) | #UDG56892,101(wall_11) | #UDG56901,70(conveyor_11) | #UDG56910,4(nasty1_11) | #UDG56919,5(nasty2_11) | #UDG56928,6(spare_11) } TABLE#
B 56864,9,9 Background
B 56873,9,9 Floor
B 56882,9,9 Crumbling floor
B 56891,9,9 Wall
B 56900,9,9 Conveyor
B 56909,9,9 Nasty 1
B 56918,9,9 Nasty 2
B 56927,9,9 Spare
D 56936 The next 7 bytes specify Miner Willy's initial location and appearance in the cavern.
B 56936 Pixel y-coordinate * 2
B 56937 Sprite
B 56938 Direction
B 56939 Jump flag
B 56940 Coordinates
B 56942 Distance jumped
D 56943 The next 4 bytes define the direction, location and length of the conveyor.
B 56943 Conveyor direction (right), location (x=18, y=8) and length (11)
D 56947 The next byte specifies the border colour.
B 56947 Border colour
B 56948 Unused
D 56949 The next 25 bytes specify the colour and location of the items in the cavern.
B 56949,5 Item 1
B 56954,5 Item 2
B 56959,5 Item 3
B 56964,5 Item 4
B 56969,5 Item 5
B 56974
D 56975 The next 37 bytes define the portal graphic and its location.
D 56975 #UDGTABLE { #UDGARRAY2,94,4,2;56976-56993-1-16(portal11) } TABLE#
B 56975,1 Attribute
B 56976,32,8 Graphic data
B 57008,4 Location (x=15, y=13)
D 57012 The next 8 bytes define the item graphic.
D 57012 #UDGTABLE { #UDG57012,3(item11) } TABLE#
B 57012,8 Item graphic data
D 57020 The next two bytes define the initial air supply in the cavern.
B 57020 Air
D 57022 The next 28 bytes define the horizontal guardians.
B 57022,7 Horizontal guardian 1
B 57029,7 Horizontal guardian 2
B 57036,7 Horizontal guardian 3 (unused)
B 57043,7 Horizontal guardian 4
B 57050,3,16 Unused
D 57053 There are no vertical guardians in this room.
B 57053,1 Terminator
B 57054,34,16 Unused
D 57088 The next 256 bytes are guardian graphic data.
D 57088 #UDGTABLE { #UDGARRAY2,56,4,2;57088-57105-1-16(return_of_the_alien_kong_beast_guardian0) | #UDGARRAY2,56,4,2;57120-57137-1-16(return_of_the_alien_kong_beast_guardian1) | #UDGARRAY2,56,4,2;57152-57169-1-16(return_of_the_alien_kong_beast_guardian2) | #UDGARRAY2,56,4,2;57184-57201-1-16(return_of_the_alien_kong_beast_guardian3) | #UDGARRAY2,56,4,2;57216-57233-1-16(return_of_the_alien_kong_beast_guardian4) | #UDGARRAY2,56,4,2;57248-57265-1-16(return_of_the_alien_kong_beast_guardian5) | #UDGARRAY2,56,4,2;57280-57297-1-16(return_of_the_alien_kong_beast_guardian6) | #UDGARRAY2,56,4,2;57312-57329-1-16(return_of_the_alien_kong_beast_guardian7) } TABLE#
B 57088,256,16
b 57344 Ore Refinery
D 57344 #UDGTABLE { #CALL:cavern(57344) } TABLE#
D 57344 The first 512 bytes are the attributes that define the layout of the cavern.
B 57344,512,16 Attributes
D 57856 The next 32 bytes contain the cavern name.
T 57856,32 Cavern name
D 57888 The next 72 bytes contain the attributes and graphic data for the tiles used to build the room.
D 57888 #UDGTABLE { #UDG57889,0(background_12) | #UDG57898,5(floor_12) | #UDG57907,66(crumbling_floor_12) | #UDG57916,22(wall_12) | #UDG57925,4(conveyor_12) | #UDG57934,68(nasty1_12) | #UDG57943,69(nasty2_12) | #UDG57952,6(spare_12) } TABLE#
B 57888,9,9 Background
B 57897,9,9 Floor
B 57906,9,9 Crumbling floor (unused)
B 57915,9,9 Wall
B 57924,9,9 Conveyor
B 57933,9,9 Nasty 1 (unused)
B 57942,9,9 Nasty 2 (unused)
B 57951,9,9 Spare
D 57960 The next 7 bytes specify Miner Willy's initial location and appearance in the cavern.
B 57960 Pixel y-coordinate * 2
B 57961 Sprite
B 57962 Direction
B 57963 Jump flag
B 57964 Coordinates
B 57966 Distance jumped
D 57967 The next 4 bytes define the direction, location and length of the conveyor.
B 57967 Conveyor direction (right), location (x=3, y=8) and length (26)
D 57971 The next byte specifies the border colour.
B 57971 Border colour
B 57972 Unused
D 57973 The next 25 bytes specify the colour and location of the items in the cavern.
B 57973,5 Item 1
B 57978,5 Item 2
B 57983,5 Item 3
B 57988,5 Item 4
B 57993,5 Item 5
B 57998
D 57999 The next 37 bytes define the portal graphic and its location.
D 57999 #UDGTABLE { #UDGARRAY2,79,4,2;58000-58017-1-16(portal12) } TABLE#
B 57999,1 Attribute
B 58000,32,8 Graphic data
B 58032,4 Location (x=1, y=13)
D 58036 The next 8 bytes define the item graphic.
D 58036 #UDGTABLE { #UDG58036,3(item12) } TABLE#
B 58036,8 Item graphic data
D 58044 The next two bytes define the initial air supply in the cavern.
B 58044 Air
D 58046 The next 28 bytes define the horizontal guardians.
B 58046,7 Horizontal guardian 1
B 58053,7 Horizontal guardian 2
B 58060,7 Horizontal guardian 3
B 58067,7 Horizontal guardian 4
B 58074,3,16 Unused
D 58077 The next 7 bytes define the vertical guardian.
B 58077,7 Vertical guardian
B 58084,1 Terminator
B 58085,27,16 Unused
D 58112 The next 256 bytes are guardian graphic data.
D 58112 #UDGTABLE { #UDGARRAY2,56,4,2;58112-58129-1-16(ore_refinery_guardian0) | #UDGARRAY2,56,4,2;58144-58161-1-16(ore_refinery_guardian1) | #UDGARRAY2,56,4,2;58176-58193-1-16(ore_refinery_guardian2) | #UDGARRAY2,56,4,2;58208-58225-1-16(ore_refinery_guardian3) | #UDGARRAY2,56,4,2;58240-58257-1-16(ore_refinery_guardian4) | #UDGARRAY2,56,4,2;58272-58289-1-16(ore_refinery_guardian5) | #UDGARRAY2,56,4,2;58304-58321-1-16(ore_refinery_guardian6) | #UDGARRAY2,56,4,2;58336-58353-1-16(ore_refinery_guardian7) } TABLE#
B 58112,256,16
b 58368 Skylab Landing Bay
D 58368 #UDGTABLE { #CALL:cavern(58368) } TABLE#
D 58368 The first 512 bytes are the attributes that define the layout of the cavern.
B 58368,512,16 Attributes
D 58880 The next 32 bytes contain the cavern name.
T 58880,32 Cavern name
D 58912 The next 72 bytes contain the attributes and graphic data for the tiles used to build the room.
D 58912 #UDGTABLE { #UDG58913,8(background_13) | #UDG58922,76(floor_13) | #UDG58931,2(crumbling_floor_13) | #UDG58940,104(wall_13) | #UDG58949,75(conveyor_13) | #UDG58958,0(nasty1_13) | #UDG58967,0(nasty2_13) | #UDG58976,12(spare_13) } TABLE#
B 58912,9,9 Background
B 58921,9,9 Floor
B 58930,9,9 Crumbling floor (unused)
B 58939,9,9 Wall
B 58948,9,9 Conveyor
B 58957,9,9 Nasty 1 (unused)
B 58966,9,9 Nasty 2 (unused)
B 58975,9,9 Spare
D 58984 The next 7 bytes specify Miner Willy's initial location and appearance in the cavern.
B 58984 Pixel y-coordinate * 2
B 58985 Sprite
B 58986 Direction
B 58987 Jump flag
B 58988 Coordinates
B 58990 Distance jumped
D 58991 The next 4 bytes define the direction, location and length of the conveyor.
B 58991 Conveyor direction (left), location (x=15, y=8) and length (6)
D 58995 The next byte specifies the border colour.
B 58995 Border colour
B 58996 Unused
D 58997 The next 25 bytes specify the colour and location of the items in the cavern.
B 58997,5 Item 1
B 59002,5 Item 2
B 59007,5 Item 3
B 59012,5 Item 4
B 59017,5 Item 5 (unused)
B 59022
D 59023 The next 37 bytes define the portal graphic and its location.
D 59023 #UDGTABLE { #UDGARRAY2,30,4,2;59024-59041-1-16(portal13) } TABLE#
B 59023,1 Attribute
B 59024,32,8 Graphic data
B 59056,4 Location (x=15, y=0)
D 59060 The next 8 bytes define the item graphic.
D 59060 #UDGTABLE { #UDG59060,11(item13) } TABLE#
B 59060,8 Item graphic data
D 59068 The next two bytes define the initial air supply in the cavern.
B 59068 Air
D 59070 There are no horizontal guardians in this room.
B 59070,1 Terminator
B 59071,30,16 Unused
D 59101 The next 21 bytes define the vertical guardians.
B 59101,7 Vertical guardian 1
B 59108,7 Vertical guardian 2
B 59115,7 Vertical guardian 3
B 59122,1 Terminator
B 59123,13,16 Unused
D 59136 The next 256 bytes are guardian graphic data.
D 59136 #UDGTABLE { #UDGARRAY2,56,4,2;59136-59153-1-16(skylab_landing_bay_guardian0) | #UDGARRAY2,56,4,2;59168-59185-1-16(skylab_landing_bay_guardian1) | #UDGARRAY2,56,4,2;59200-59217-1-16(skylab_landing_bay_guardian2) | #UDGARRAY2,56,4,2;59232-59249-1-16(skylab_landing_bay_guardian3) | #UDGARRAY2,56,4,2;59264-59281-1-16(skylab_landing_bay_guardian4) | #UDGARRAY2,56,4,2;59296-59313-1-16(skylab_landing_bay_guardian5) | #UDGARRAY2,56,4,2;59328-59345-1-16(skylab_landing_bay_guardian6) | #UDGARRAY2,56,4,2;59360-59377-1-16(skylab_landing_bay_guardian7) } TABLE#
B 59136,256,16
b 59392 The Bank
D 59392 #UDGTABLE { #CALL:cavern(59392) } TABLE#
D 59392 The first 512 bytes are the attributes that define the layout of the cavern.
B 59392,512,16 Attributes
D 59904 The next 32 bytes contain the cavern name.
T 59904,32 Cavern name
D 59936 The next 72 bytes contain the attributes and graphic data for the tiles used to build the room.
D 59936 #UDGTABLE { #UDG59937,0(background_14) | #UDG59946,65(floor_14) | #UDG59955,1(crumbling_floor_14) | #UDG59964,14(wall_14) | #UDG59973,69(conveyor_14) | #UDG59982,70(nasty1_14) | #UDG59991,66(nasty2_14) | #UDG60000,6(spare_14) } TABLE#
B 59936,9,9 Background
B 59945,9,9 Floor
B 59954,9,9 Crumbling floor
B 59963,9,9 Wall
B 59972,9,9 Conveyor
B 59981,9,9 Nasty 1
B 59990,9,9 Nasty 2
B 59999,9,9 Spare
D 60008 The next 7 bytes specify Miner Willy's initial location and appearance in the cavern.
B 60008 Pixel y-coordinate * 2
B 60009 Sprite
B 60010 Direction
B 60011 Jump flag
B 60012 Coordinates
B 60014 Distance jumped
D 60015 The next 4 bytes define the direction, location and length of the conveyor.
B 60015 Conveyor direction (left), location (x=8, y=0) and length (16)
D 60019 The next byte specifies the border colour.
B 60019 Border colour
B 60020 Unused
D 60021 The next 25 bytes specify the colour and location of the items in the cavern.
B 60021,5 Item 1
B 60026,5 Item 2
B 60031,5 Item 3
B 60036,5 Item 4 (unused)
B 60041,5 Item 5 (unused)
B 60046
D 60047 The next 37 bytes define the portal graphic and its location.
D 60047 #UDGTABLE { #UDGARRAY2,86,4,2;60048-60065-1-16(portal14) } TABLE#
B 60047,1 Attribute
B 60048,32,8 Graphic data
B 60080,4 Location (x=1, y=3)
D 60084 The next 8 bytes define the item graphic.
D 60084 #UDGTABLE { #UDG60084,3(item14) } TABLE#
B 60084,8 Item graphic data
D 60092 The next two bytes define the initial air supply in the cavern.
B 60092 Air
D 60094 The next 28 bytes define the horizontal guardians.
B 60094,7 Horizontal guardian 1
B 60101,7 Horizontal guardian 2 (unused)
B 60108,7 Horizontal guardian 3 (unused)
B 60115,7 Horizontal guardian 4 (unused)
B 60122,3,16 Unused
D 60125 The next 21 bytes define the vertical guardians.
B 60125,7 Vertical guardian 1
B 60132,7 Vertical guardian 2
B 60139,7 Vertical guardian 3
B 60146,1 Terminator
B 60147,13,16 Unused
D 60160 The next 256 bytes are guardian graphic data.
D 60160 #UDGTABLE { #UDGARRAY2,56,4,2;60160-60177-1-16(the_bank_guardian0) | #UDGARRAY2,56,4,2;60192-60209-1-16(the_bank_guardian1) | #UDGARRAY2,56,4,2;60224-60241-1-16(the_bank_guardian2) | #UDGARRAY2,56,4,2;60256-60273-1-16(the_bank_guardian3) | #UDGARRAY2,56,4,2;60288-60305-1-16(the_bank_guardian4) | #UDGARRAY2,56,4,2;60320-60337-1-16(the_bank_guardian5) | #UDGARRAY2,56,4,2;60352-60369-1-16(the_bank_guardian6) | #UDGARRAY2,56,4,2;60384-60401-1-16(the_bank_guardian7) } TABLE#
B 60160,256,16
b 60416 The Sixteenth Cavern
D 60416 #UDGTABLE { #CALL:cavern(60416) } TABLE#
D 60416 The first 512 bytes are the attributes that define the layout of the cavern.
B 60416,512,16 Attributes
D 60928 The next 32 bytes contain the cavern name.
T 60928,32 Cavern name
D 60960 The next 72 bytes contain the attributes and graphic data for the tiles used to build the room.
D 60960 #UDGTABLE { #UDG60961,0(background_15) | #UDG60970,66(floor_15) | #UDG60979,2(crumbling_floor_15) | #UDG60988,101(wall_15) | #UDG60997,70(conveyor_15) | #UDG61006,4(nasty1_15) | #UDG61015,5(nasty2_15) | #UDG61024,6(spare_15) } TABLE#
B 60960,9,9 Background
B 60969,9,9 Floor
B 60978,9,9 Crumbling floor
B 60987,9,9 Wall
B 60996,9,9 Conveyor
B 61005,9,9 Nasty 1
B 61014,9,9 Nasty 2 (unused)
B 61023,9,9 Spare (unused)
D 61032 The next 7 bytes specify Miner Willy's initial location and appearance in the cavern.
B 61032 Pixel y-coordinate * 2
B 61033 Sprite
B 61034 Direction
B 61035 Jump flag
B 61036 Coordinates
B 61038 Distance jumped
D 61039 The next 4 bytes define the direction, location and length of the conveyor.
B 61039 Conveyor direction (left), location (x=3, y=8) and length (24)
D 61043 The next byte specifies the border colour.
B 61043 Border colour
B 61044 Unused
D 61045 The next 25 bytes specify the colour and location of the items in the cavern.
B 61045,5 Item 1
B 61050,5 Item 2
B 61055,5 Item 3
B 61060,5 Item 4
B 61065,5 Item 5 (unused)
B 61070
D 61071 The next 37 bytes define the portal graphic and its location.
D 61071 #UDGTABLE { #UDGARRAY2,94,4,2;61072-61089-1-16(portal15) } TABLE#
B 61071,1 Attribute
B 61072,32,8 Graphic data
B 61104,4 Location (x=12, y=5)
D 61108 The next 8 bytes define the item graphic.
D 61108 #UDGTABLE { #UDG61108,3(item15) } TABLE#
B 61108,8 Item graphic data
D 61116 The next two bytes define the initial air supply in the cavern.
B 61116 Air
D 61118 The next 28 bytes define the horizontal guardians.
B 61118,7 Horizontal guardian 1
B 61125,7 Horizontal guardian 2
B 61132,7 Horizontal guardian 3
B 61139,7 Horizontal guardian 4
B 61146,3,16 Unused
D 61149 There are no vertical guardians in this room.
B 61149,1 Terminator
B 61150,34,16 Unused
D 61184 The next 256 bytes are guardian graphic data.
D 61184 #UDGTABLE { #UDGARRAY2,56,4,2;61184-61201-1-16(the_sixteenth_cavern_guardian0) | #UDGARRAY2,56,4,2;61216-61233-1-16(the_sixteenth_cavern_guardian1) | #UDGARRAY2,56,4,2;61248-61265-1-16(the_sixteenth_cavern_guardian2) | #UDGARRAY2,56,4,2;61280-61297-1-16(the_sixteenth_cavern_guardian3) | #UDGARRAY2,56,4,2;61312-61329-1-16(the_sixteenth_cavern_guardian4) | #UDGARRAY2,56,4,2;61344-61361-1-16(the_sixteenth_cavern_guardian5) | #UDGARRAY2,56,4,2;61376-61393-1-16(the_sixteenth_cavern_guardian6) | #UDGARRAY2,56,4,2;61408-61425-1-16(the_sixteenth_cavern_guardian7) } TABLE#
B 61184,256,16
b 61440 The Warehouse
D 61440 #UDGTABLE { #CALL:cavern(61440) } TABLE#
D 61440 The first 512 bytes are the attributes that define the layout of the cavern.
B 61440,512,16 Attributes
D 61952 The next 32 bytes contain the cavern name.
T 61952,32 Cavern name
D 61984 The next 72 bytes contain the attributes and graphic data for the tiles used to build the room.
D 61984 #UDGTABLE { #UDG61985,0(background_16) | #UDG61994,4(floor_16) | #UDG62003,68(crumbling_floor_16) | #UDG62012,22(wall_16) | #UDG62021,32(conveyor_16) | #UDG62030,6(nasty1_16) | #UDG62039,33(nasty2_16) | #UDG62048,0(spare_16) } TABLE#
B 61984,9,9 Background
B 61993,9,9 Floor
B 62002,9,9 Crumbling floor
B 62011,9,9 Wall
B 62020,9,9 Conveyor
B 62029,9,9 Nasty 1
B 62038,9,9 Nasty 2
B 62047,9,9 Spare (unused)
D 62056 The next 7 bytes specify Miner Willy's initial location and appearance in the cavern.
B 62056 Pixel y-coordinate * 2
B 62057 Sprite
B 62058 Direction
B 62059 Jump flag
B 62060 Coordinates
B 62062 Distance jumped
D 62063 The next 4 bytes define the direction, location and length of the conveyor.
B 62063 Conveyor direction (right), location (x=14, y=8) and length (5)
D 62067 The next byte specifies the border colour.
B 62067 Border colour
B 62068 Unused
D 62069 The next 25 bytes specify the colour and location of the items in the cavern.
B 62069,5 Item 1
B 62074,5 Item 2
B 62079,5 Item 3
B 62084,5 Item 4
B 62089,5 Item 5
B 62094
D 62095 The next 37 bytes define the portal graphic and its location.
D 62095 #UDGTABLE { #UDGARRAY2,76,4,2;62096-62113-1-16(portal16) } TABLE#
B 62095,1 Attribute
B 62096,32,8 Graphic data
B 62128,4 Location (x=29, y=1)
D 62132 The next 8 bytes define the item graphic.
D 62132 #UDGTABLE { #UDG62132,35(item16) } TABLE#
B 62132,8 Item graphic data
D 62140 The next two bytes define the initial air supply in the cavern.
B 62140 Air
D 62142 The next 14 bytes define the horizontal guardians.
B 62142,7 Horizontal guardian 1
B 62149,7 Horizontal guardian 2
B 62156,1 Terminator
B 62157,16,16 Unused
D 62173 The next 28 bytes define the vertical guardians.
B 62173,7 Vertical guardian 1
B 62180,7 Vertical guardian 2
B 62187,7 Vertical guardian 3
B 62194,7 Vertical guardian 4
B 62201,7,16 Unused
D 62208 The next 256 bytes are guardian graphic data.
D 62208 #UDGTABLE { #UDGARRAY2,56,4,2;62208-62225-1-16(the_warehouse_guardian0) | #UDGARRAY2,56,4,2;62240-62257-1-16(the_warehouse_guardian1) | #UDGARRAY2,56,4,2;62272-62289-1-16(the_warehouse_guardian2) | #UDGARRAY2,56,4,2;62304-62321-1-16(the_warehouse_guardian3) | #UDGARRAY2,56,4,2;62336-62353-1-16(the_warehouse_guardian4) | #UDGARRAY2,56,4,2;62368-62385-1-16(the_warehouse_guardian5) | #UDGARRAY2,56,4,2;62400-62417-1-16(the_warehouse_guardian6) | #UDGARRAY2,56,4,2;62432-62449-1-16(the_warehouse_guardian7) } TABLE#
B 62208,256,16
b 62464 Amoebatrons' Revenge
D 62464 #UDGTABLE { #CALL:cavern(62464) } TABLE#
D 62464 The first 512 bytes are the attributes that define the layout of the cavern.
B 62464,512,16 Attributes
D 62976 The next 32 bytes contain the cavern name.
T 62976,32 Cavern name
D 63008 The next 72 bytes contain the attributes and graphic data for the tiles used to build the room.
D 63008 #UDGTABLE { #UDG63009,0(background_17) | #UDG63018,66(floor_17) | #UDG63027,2(crumbling_floor_17) | #UDG63036,22(wall_17) | #UDG63045,4(conveyor_17) | #UDG63054,68(nasty1_17) | #UDG63063,5(nasty2_17) | #UDG63072,0(spare_17) } TABLE#
B 63008,9,9 Background
B 63017,9,9 Floor
B 63026,9,9 Crumbling floor (unused)
B 63035,9,9 Wall
B 63044,9,9 Conveyor (unused)
B 63053,9,9 Nasty 1 (unused)
B 63062,9,9 Nasty 2 (unused)
B 63071,9,9 Spare (unused)
D 63080 The next 7 bytes specify Miner Willy's initial location and appearance in the cavern.
B 63080 Pixel y-coordinate * 2
B 63081 Sprite
B 63082 Direction
B 63083 Jump flag
B 63084 Coordinates
B 63086 Distance jumped
D 63087 The next 4 bytes define the direction, location and length of the conveyor.
B 63087 Conveyor direction (right), location (x=7, y=8) and length (3)
D 63091 The next byte specifies the border colour.
B 63091 Border colour
B 63092 Unused
D 63093 The next 25 bytes specify the colour and location of the items in the cavern.
B 63093,5 Item 1
B 63098,5 Item 2 (unused)
B 63103,5 Item 3 (unused)
B 63108,5 Item 4 (unused)
B 63113,5 Item 5 (unused)
B 63118
D 63119 The next 37 bytes define the portal graphic and its location.
D 63119 #UDGTABLE { #UDGARRAY2,14,4,2;63120-63137-1-16(portal17) } TABLE#
B 63119,1 Attribute
B 63120,32,8 Graphic data
B 63152,4 Location (x=29, y=0)
D 63156 The next 8 bytes define the item graphic.
D 63156 #UDGTABLE { #UDG63156,3(item17) } TABLE#
B 63156,8 Item graphic data
D 63164 The next two bytes define the initial air supply in the cavern.
B 63164 Air
D 63166 The next 28 bytes define the horizontal guardians.
B 63166,7 Horizontal guardian 1
B 63173,7 Horizontal guardian 2
B 63180,7 Horizontal guardian 3
B 63187,7 Horizontal guardian 4
B 63194,3,16 Unused
D 63197 The next 28 bytes define the vertical guardians.
B 63197,7 Vertical guardian 1
B 63204,7 Vertical guardian 2
B 63211,7 Vertical guardian 3
B 63218,7 Vertical guardian 4
B 63225,7,16 Unused
D 63232 The next 256 bytes are guardian graphic data.
D 63232 #UDGTABLE { #UDGARRAY2,56,4,2;63232-63249-1-16(amoebatrons'_revenge_guardian0) | #UDGARRAY2,56,4,2;63264-63281-1-16(amoebatrons'_revenge_guardian1) | #UDGARRAY2,56,4,2;63296-63313-1-16(amoebatrons'_revenge_guardian2) | #UDGARRAY2,56,4,2;63328-63345-1-16(amoebatrons'_revenge_guardian3) | #UDGARRAY2,56,4,2;63360-63377-1-16(amoebatrons'_revenge_guardian4) | #UDGARRAY2,56,4,2;63392-63409-1-16(amoebatrons'_revenge_guardian5) | #UDGARRAY2,56,4,2;63424-63441-1-16(amoebatrons'_revenge_guardian6) | #UDGARRAY2,56,4,2;63456-63473-1-16(amoebatrons'_revenge_guardian7) } TABLE#
B 63232,256,16
b 63488 Solar Power Generator
D 63488 #UDGTABLE { #CALL:cavern(63488) } TABLE#
D 63488 The first 512 bytes are the attributes that define the layout of the cavern.
B 63488,512,16 Attributes
D 64000 The next 32 bytes contain the cavern name.
T 64000,32 Cavern name
D 64032 The next 72 bytes contain the attributes and graphic data for the tiles used to build the room.
D 64032 #UDGTABLE { #UDG64033,36(background_18) | #UDG64042,32(floor_18) | #UDG64051,2(crumbling_floor_18) | #UDG64060,22(wall_18) | #UDG64069,38(conveyor_18) | #UDG64078,68(nasty1_18) | #UDG64087,5(nasty2_18) | #UDG64096,0(spare_18) } TABLE#
B 64032,9,9 Background
B 64041,9,9 Floor
B 64050,9,9 Crumbling floor (unused)
B 64059,9,9 Wall
B 64068,9,9 Conveyor
B 64077,9,9 Nasty 1 (unused)
B 64086,9,9 Nasty 2 (unused)
B 64095,9,9 Spare (unused)
D 64104 The next 7 bytes specify Miner Willy's initial location and appearance in the cavern.
B 64104 Pixel y-coordinate * 2
B 64105 Sprite
B 64106 Direction
B 64107 Jump flag
B 64108 Coordinates
B 64110 Distance jumped
D 64111 The next 4 bytes define the direction, location and length of the conveyor.
B 64111 Conveyor direction (left), location (x=7, y=8) and length (4)
D 64115 The next byte specifies the border colour.
B 64115 Border colour
B 64116 Unused
D 64117 The next 25 bytes specify the colour and location of the items in the cavern.
B 64117,5 Item 1
B 64122,5 Item 2
B 64127,5 Item 3
B 64132,5 Item 4 (unused)
B 64137,5 Item 5 (unused)
B 64142
D 64143 The next 37 bytes define the portal graphic and its location.
D 64143 #UDGTABLE { #UDGARRAY2,78,4,2;64144-64161-1-16(portal18) } TABLE#
B 64143,1 Attribute
B 64144,32,8 Graphic data
B 64176,4 Location (x=1, y=1)
D 64180 The next 8 bytes define the item graphic.
D 64180 #UDGTABLE { #UDG64180,35(item18) } TABLE#
B 64180,8 Item graphic data
D 64188 The next two bytes define the initial air supply in the cavern.
B 64188 Air
D 64190 The next 28 bytes define the horizontal guardians.
B 64190,7 Horizontal guardian 1
B 64197,7 Horizontal guardian 2
B 64204,7 Horizontal guardian 3
B 64211,7 Horizontal guardian 4
B 64218,3,16 Unused
D 64221 The next 21 bytes define the vertical guardians.
B 64221,7 Vertical guardian 1
B 64228,7 Vertical guardian 2
B 64235,7 Vertical guardian 3
B 64242,1 Terminator
B 64243,13,16 Unused
D 64256 The next 256 bytes are guardian graphic data.
D 64256 #UDGTABLE { #UDGARRAY2,56,4,2;64256-64273-1-16(solar_power_generator_guardian0) | #UDGARRAY2,56,4,2;64288-64305-1-16(solar_power_generator_guardian1) | #UDGARRAY2,56,4,2;64320-64337-1-16(solar_power_generator_guardian2) | #UDGARRAY2,56,4,2;64352-64369-1-16(solar_power_generator_guardian3) | #UDGARRAY2,56,4,2;64384-64401-1-16(solar_power_generator_guardian4) | #UDGARRAY2,56,4,2;64416-64433-1-16(solar_power_generator_guardian5) | #UDGARRAY2,56,4,2;64448-64465-1-16(solar_power_generator_guardian6) | #UDGARRAY2,56,4,2;64480-64497-1-16(solar_power_generator_guardian7) } TABLE#
B 64256,256,16
b 64512 The Final Barrier
D 64512 #UDGTABLE { #CALL:cavern(64512) } TABLE#
D 64512 The first 512 bytes are the attributes that define the layout of the cavern.
B 64512,512,16 Attributes
D 65024 The next 32 bytes contain the cavern name.
T 65024,32 Cavern name
D 65056 The next 72 bytes contain the attributes and graphic data for the tiles used to build the room.
D 65056 #UDGTABLE { #UDG65057,0(background_19) | #UDG65066,66(floor_19) | #UDG65075,2(crumbling_floor_19) | #UDG65084,38(wall_19) | #UDG65093,5(conveyor_19) | #UDG65102,68(nasty1_19) | #UDG65111,10(nasty2_19) | #UDG65120,0(spare_19) } TABLE#
B 65056,9,9 Background
B 65065,9,9 Floor
B 65074,9,9 Crumbling floor
B 65083,9,9 Wall
B 65092,9,9 Conveyor
B 65101,9,9 Nasty 1
B 65110,9,9 Nasty 2 (unused)
B 65119,9,9 Spare (unused)
D 65128 The next 7 bytes specify Miner Willy's initial location and appearance in the cavern.
B 65128 Pixel y-coordinate * 2
B 65129 Sprite
B 65130 Direction
B 65131 Jump flag
B 65132 Coordinates
B 65134 Distance jumped
D 65135 The next 4 bytes define the direction, location and length of the conveyor.
B 65135 Conveyor direction (right), location (x=1, y=8) and length (22)
D 65139 The next byte specifies the border colour.
B 65139 Border colour
B 65140 Unused
D 65141 The next 25 bytes specify the colour and location of the items in the cavern.
B 65141,5 Item 1
B 65146,5 Item 2
B 65151,5 Item 3
B 65156,5 Item 4
B 65161,5 Item 5
B 65166
D 65167 The next 37 bytes define the portal graphic and its location.
D 65167 #UDGTABLE { #UDGARRAY2,30,4,2;65168-65185-1-16(portal19) } TABLE#
B 65167,1 Attribute
B 65168,32,8 Graphic data
B 65200,4 Location (x=19, y=5)
D 65204 The next 8 bytes define the item graphic.
D 65204 #UDGTABLE { #UDG65204,3(item19) } TABLE#
B 65204,8 Item graphic data
D 65212 The next two bytes define the initial air supply in the cavern.
B 65212 Air
D 65214 The next 7 bytes define the horizontal guardian.
B 65214,7 Horizontal guardian
B 65221,1 Terminator
B 65222,23,16 Unused
D 65245 The next 7 bytes define the vertical guardian.
B 65245,7 Vertical guardian
B 65252,1 Terminator
B 65253,27,16 Unused
D 65280 The next 256 bytes are guardian graphic data.
D 65280 #UDGTABLE { #UDGARRAY2,56,4,2;65280-65297-1-16(the_final_barrier_guardian0) | #UDGARRAY2,56,4,2;65312-65329-1-16(the_final_barrier_guardian1) | #UDGARRAY2,56,4,2;65344-65361-1-16(the_final_barrier_guardian2) | #UDGARRAY2,56,4,2;65376-65393-1-16(the_final_barrier_guardian3) | #UDGARRAY2,56,4,2;65408-65425-1-16(the_final_barrier_guardian4) | #UDGARRAY2,56,4,2;65440-65457-1-16(the_final_barrier_guardian5) | #UDGARRAY2,56,4,2;65472-65489-1-16(the_final_barrier_guardian6) | #UDGARRAY2,56,4,2;65504-65521-1-16(the_final_barrier_guardian7) } TABLE#
B 65280,256,16
