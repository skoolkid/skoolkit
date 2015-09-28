# -*- coding: utf-8 -*-
import unittest
import re

from skoolkittest import SkoolKitTestCase
from skoolkit import SkoolParsingError
from skoolkit.skoolparser import SkoolParser, TableParser, set_bytes, BASE_10, BASE_16, CASE_LOWER, CASE_UPPER

TEST_BASE_CONVERSION_SKOOL = """
c30000 LD A,%11101011
 30002 LD A,162
 30004 LD A,$71
 30006 LD B,%11001110
 30008 LD B,228
 30010 LD B,$CE
 30012 LD C,%01000001
 30014 LD C,21
 30016 LD C,$23
 30018 LD D,%01101110
 30020 LD D,9
 30022 LD D,$5E
 30024 LD E,%11110110
 30026 LD E,77
 30028 LD E,$4B
 30030 LD H,%11010111
 30032 LD H,23
 30034 LD H,$59
 30036 LD L,%11011010
 30038 LD L,162
 30040 LD L,$6C
 30042 LD (HL),%11100111
 30044 LD (HL),46
 30046 LD (HL),$D1
 30048 CALL %1111010101111101
 30051 CALL 53138
 30054 CALL $056C
 30057 JP %0011101010111111
 30060 JP 53901
 30063 JP $C311
 30066 DJNZ %111010101110010
 30068 DJNZ 30068
 30070 DJNZ $7576
 30072 JR %111010101111000
 30074 JR 30074
 30076 JR $757C
 30078 AND %10011011
 30080 AND 162
 30082 AND $63
 30084 OR %00101011
 30086 OR 42
 30088 OR $5F
 30090 XOR %01001101
 30092 XOR 17
 30094 XOR $3F
 30096 SUB %01011011
 30098 SUB 28
 30100 SUB $C3
 30102 CP %01001110
 30104 CP 23
 30106 CP $80
 30108 ADD A,%10101111
 30110 ADD A,187
 30112 ADD A,$D3
 30114 ADC A,%11000111
 30116 ADC A,134
 30118 ADC A,$51
 30120 SBC A,%00001000
 30122 SBC A,16
 30124 SBC A,$DC
 30126 RST %10001001
 30128 RST 107
 30130 RST $5E
 30132 IN (%11100111),A
 30134 IN (87),A
 30136 IN ($C2),A
 30138 OUT (%11110101),A
 30140 OUT (238),A
 30142 OUT ($EF),A
 30144 LD BC,(%1011110010110110)
 30148 LD BC,(27608)
 30152 LD BC,($EC3E)
 30156 LD (%0010010011011010),BC
 30160 LD (32593),BC
 30164 LD ($0B9D),BC
 30168 LD DE,(%1011111010101010)
 30172 LD DE,(42993)
 30176 LD DE,($F43F)
 30180 LD (%0100001001001001),DE
 30184 LD (40987),DE
 30188 LD ($295D),DE
 30192 LD IX,(%0000111110010010)
 30196 LD IX,(39765)
 30200 LD IX,($9F9E)
 30204 LD (%1110010100101101),IX
 30208 LD (28062),IX
 30212 LD ($349E),IX
 30216 LD IY,(%1101100010011011)
 30220 LD IY,(29840)
 30224 LD IY,($C2A3)
 30228 LD (%0001001010001001),IY
 30232 LD (52000),IY
 30236 LD ($DBA1),IY
 30240 LD SP,(%0001110010001110)
 30244 LD SP,(43260)
 30248 LD SP,($2F41)
 30252 LD (%0011110000100001),SP
 30256 LD (10862),SP
 30260 LD ($DF34),SP
 30264 LD A,(%0111100000110111)
 30267 LD A,(38950)
 30270 LD A,($9577)
 30273 LD (%0000011111001100),A
 30276 LD (40640),A
 30279 LD ($3CDE),A
 30282 LD HL,(%0110100011101011)
 30285 LD HL,(41745)
 30288 LD HL,($E51E)
 30291 LD (%0001100100111010),HL
 30294 LD (64199),HL
 30297 LD ($6F67),HL
 30300 LD BC,%0001101000111010
 30303 LD BC,41497
 30306 LD BC,$D94B
 30309 LD DE,%0000100111001011
 30312 LD DE,44845
 30315 LD DE,$47BC
 30318 LD HL,%1001000010100101
 30321 LD HL,6785
 30324 LD HL,$652B
 30327 LD SP,%0011010001010010
 30330 LD SP,42622
 30333 LD SP,$7291
 30336 RL (IX+%01100111)
 30340 RL (IX+94)
 30344 RL (IX+$77)
 30348 RR (IX+%01101001)
 30352 RR (IX+28)
 30356 RR (IX+$17)
 30360 RRC (IX+%00100111)
 30364 RRC (IX+79)
 30368 RRC (IX+$24)
 30372 RLC (IX+%01001101)
 30376 RLC (IX+114)
 30380 RLC (IX+$26)
 30384 SLA (IX+%01011110)
 30388 SLA (IX+101)
 30392 SLA (IX+$3F)
 30396 SRA (IX+%00001101)
 30400 SRA (IX+107)
 30404 SRA (IX+$34)
 30408 SLL (IX+%00001001)
 30412 SLL (IX+34)
 30416 SLL (IX+$75)
 30420 SRL (IX+%01010100)
 30424 SRL (IX+50)
 30428 SRL (IX+$3D)
 30432 INC (IX-%01101011)
 30435 INC (IX-89)
 30438 INC (IX-$4E)
 30441 DEC (IX-%01100010)
 30444 DEC (IX-75)
 30447 DEC (IX-$63)
 30450 AND (IX-%00000110)
 30453 AND (IX-32)
 30456 AND (IX-$44)
 30459 OR (IX-%01100011)
 30462 OR (IX-5)
 30465 OR (IX-$4E)
 30468 XOR (IX-%01111111)
 30471 XOR (IX-79)
 30474 XOR (IX-$76)
 30477 SUB (IX-%01011110)
 30480 SUB (IX-63)
 30483 SUB (IX-$68)
 30486 CP (IX-%00001101)
 30489 CP (IX-29)
 30492 CP (IX-$22)
 30495 LD A,(IX+%01000001)
 30498 LD A,(IX+48)
 30501 LD A,(IX+$70)
 30504 LD (IX-%01110010),A
 30507 LD (IX-96),A
 30510 LD (IX-$10),A
 30513 LD B,(IX+%00111010)
 30516 LD B,(IX+94)
 30519 LD B,(IX+$2C)
 30522 LD (IX-%00000001),B
 30525 LD (IX-81),B
 30528 LD (IX-$6F),B
 30531 LD C,(IX+%01001011)
 30534 LD C,(IX+121)
 30537 LD C,(IX+$6D)
 30540 LD (IX-%00101100),C
 30543 LD (IX-98),C
 30546 LD (IX-$67),C
 30549 LD D,(IX+%00011000)
 30552 LD D,(IX+30)
 30555 LD D,(IX+$41)
 30558 LD (IX-%00111011),D
 30561 LD (IX-103),D
 30564 LD (IX-$4A),D
 30567 LD E,(IX+%00100101)
 30570 LD E,(IX+115)
 30573 LD E,(IX+$38)
 30576 LD (IX-%01110000),E
 30579 LD (IX-108),E
 30582 LD (IX-$2E),E
 30585 LD H,(IX+%00000101)
 30588 LD H,(IX+13)
 30591 LD H,(IX+$53)
 30594 LD (IX-%00011000),H
 30597 LD (IX-79),H
 30600 LD (IX-$4C),H
 30603 LD L,(IX+%00101010)
 30606 LD L,(IX+58)
 30609 LD L,(IX+$79)
 30612 LD (IX-%00010011),L
 30615 LD (IX-26),L
 30618 LD (IX-$7A),L
 30621 BIT 0,(IX+%00000111)
 30625 BIT 0,(IX+87)
 30629 BIT 0,(IX+$5C)
 30633 SET 1,(IX+%01011010)
 30637 SET 1,(IX+36)
 30641 SET 1,(IX+$7A)
 30645 RES 2,(IX+%01110100)
 30649 RES 2,(IX+125)
 30653 RES 2,(IX+$2C)
 30657 ADD A,(IX-%01011101)
 30660 ADD A,(IX-48)
 30663 ADD A,(IX-$4F)
 30666 ADC A,(IX-%01111011)
 30669 ADC A,(IX-71)
 30672 ADC A,(IX-$40)
 30675 SBC A,(IX-%00110101)
 30678 SBC A,(IX-16)
 30681 SBC A,(IX-$17)
 30684 LD IXl,%10110101
 30687 LD IXl,17
 30690 LD IXl,$C3
 30693 LD IXh,%00000000
 30696 LD IXh,178
 30699 LD IXh,$B7
 30702 LD (IX+%00001101),%01100110
 30706 LD (IX+79),33
 30710 LD (IX+$64),$02
 30714 RL (IY+%01000011)
 30718 RL (IY+63)
 30722 RL (IY+$60)
 30726 RR (IY+%01011111)
 30730 RR (IY+104)
 30734 RR (IY+$3B)
 30738 RRC (IY+%01010101)
 30742 RRC (IY+106)
 30746 RRC (IY+$69)
 30750 RLC (IY+%01000111)
 30754 RLC (IY+43)
 30758 RLC (IY+$4B)
 30762 SLA (IY+%01010111)
 30766 SLA (IY+52)
 30770 SLA (IY+$31)
 30774 SRA (IY+%01111100)
 30778 SRA (IY+122)
 30782 SRA (IY+$24)
 30786 SLL (IY+%01001010)
 30790 SLL (IY+38)
 30794 SLL (IY+$06)
 30798 SRL (IY+%00110001)
 30802 SRL (IY+116)
 30806 SRL (IY+$61)
 30810 INC (IY-%01000101)
 30813 INC (IY-107)
 30816 INC (IY-$7A)
 30819 DEC (IY-%00010000)
 30822 DEC (IY-31)
 30825 DEC (IY-$1A)
 30828 AND (IY-%01111111)
 30831 AND (IY-115)
 30834 AND (IY-$12)
 30837 OR (IY-%00101000)
 30840 OR (IY-47)
 30843 OR (IY-$4B)
 30846 XOR (IY-%01110100)
 30849 XOR (IY-51)
 30852 XOR (IY-$7C)
 30855 SUB (IY-%01010101)
 30858 SUB (IY-87)
 30861 SUB (IY-$7F)
 30864 CP (IY-%01000001)
 30867 CP (IY-127)
 30870 CP (IY-$24)
 30873 LD A,(IY+%01000111)
 30876 LD A,(IY+6)
 30879 LD A,(IY+$25)
 30882 LD (IY-%00010011),A
 30885 LD (IY-19),A
 30888 LD (IY-$27),A
 30891 LD B,(IY+%01100100)
 30894 LD B,(IY+69)
 30897 LD B,(IY+$62)
 30900 LD (IY-%00001010),B
 30903 LD (IY-48),B
 30906 LD (IY-$4B),B
 30909 LD C,(IY+%00100110)
 30912 LD C,(IY+116)
 30915 LD C,(IY+$2B)
 30918 LD (IY-%01010010),C
 30921 LD (IY-37),C
 30924 LD (IY-$5E),C
 30927 LD D,(IY+%00000010)
 30930 LD D,(IY+68)
 30933 LD D,(IY+$7C)
 30936 LD (IY-%01101010),D
 30939 LD (IY-51),D
 30942 LD (IY-$0D),D
 30945 LD E,(IY+%00110110)
 30948 LD E,(IY+92)
 30951 LD E,(IY+$26)
 30954 LD (IY-%01100100),E
 30957 LD (IY-95),E
 30960 LD (IY-$74),E
 30963 LD H,(IY+%00010100)
 30966 LD H,(IY+54)
 30969 LD H,(IY+$23)
 30972 LD (IY-%01100011),H
 30975 LD (IY-110),H
 30978 LD (IY-$5B),H
 30981 LD L,(IY+%00101001)
 30984 LD L,(IY+101)
 30987 LD L,(IY+$08)
 30990 LD (IY-%00010010),L
 30993 LD (IY-52),L
 30996 LD (IY-$70),L
 30999 BIT 0,(IY+%01100100)
 31003 BIT 0,(IY+126)
 31007 BIT 0,(IY+$0C)
 31011 SET 1,(IY+%01100100)
 31015 SET 1,(IY+58)
 31019 SET 1,(IY+$6B)
 31023 RES 2,(IY+%00001100)
 31027 RES 2,(IY+86)
 31031 RES 2,(IY+$1F)
 31035 ADD A,(IY-%01001111)
 31038 ADD A,(IY-59)
 31041 ADD A,(IY-$3E)
 31044 ADC A,(IY-%00110010)
 31047 ADC A,(IY-111)
 31050 ADC A,(IY-$24)
 31053 SBC A,(IY-%01100011)
 31056 SBC A,(IY-63)
 31059 SBC A,(IY-$13)
 31062 LD IYl,%10100010
 31065 LD IYl,201
 31068 LD IYl,$7B
 31071 LD IYh,%00011001
 31074 LD IYh,239
 31077 LD IYh,$0A
 31080 LD (IY+%00100111),%11001110
 31084 LD (IY+56),210
 31088 LD (IY+$39),$A6
 31092 DEFB %01011110
 31093 DEFB 122
 31094 DEFB $CB
 31095 DEFM %00110010
 31096 DEFM 124
 31097 DEFM $20
 31098 DEFW %0011010100010011
 31100 DEFW 63425
 31102 DEFW $602E
 31104 DEFS 10,%11001101
 31114 DEFS 10,82
 31124 DEFS 10,$59
 31134 LD ( HL ),25
 31136 LD ( HL ),$25
 31138 LD A,"1"
 31140 LD HL,("2")
 31143 LD B,(IX+"3")
 31146 LD (IY+"4"),"4"
 31150 LD (IX+"5"),","
 31154 LD (IY+"6"),6
 31158 LD (IX+"7"),$07
 31162 LD (IY+7),"7"
 31166 LD (IX+$08),"8"
 31170 LD (IY+8),","
 31174 LD (IX+$09),","
 31178 LD (IY+","),0
 31182 LD (IX+","),$01
""".strip()

TEST_BASE_CONVERSION_DECIMAL = """
30000 LD A,%11101011
30002 LD A,162
30004 LD A,113
30006 LD B,%11001110
30008 LD B,228
30010 LD B,206
30012 LD C,%01000001
30014 LD C,21
30016 LD C,35
30018 LD D,%01101110
30020 LD D,9
30022 LD D,94
30024 LD E,%11110110
30026 LD E,77
30028 LD E,75
30030 LD H,%11010111
30032 LD H,23
30034 LD H,89
30036 LD L,%11011010
30038 LD L,162
30040 LD L,108
30042 LD (HL),%11100111
30044 LD (HL),46
30046 LD (HL),209
30048 CALL %1111010101111101
30051 CALL 53138
30054 CALL 1388
30057 JP %0011101010111111
30060 JP 53901
30063 JP 49937
30066 DJNZ %111010101110010
30068 DJNZ 30068
30070 DJNZ 30070
30072 JR %111010101111000
30074 JR 30074
30076 JR 30076
30078 AND %10011011
30080 AND 162
30082 AND 99
30084 OR %00101011
30086 OR 42
30088 OR 95
30090 XOR %01001101
30092 XOR 17
30094 XOR 63
30096 SUB %01011011
30098 SUB 28
30100 SUB 195
30102 CP %01001110
30104 CP 23
30106 CP 128
30108 ADD A,%10101111
30110 ADD A,187
30112 ADD A,211
30114 ADC A,%11000111
30116 ADC A,134
30118 ADC A,81
30120 SBC A,%00001000
30122 SBC A,16
30124 SBC A,220
30126 RST %10001001
30128 RST 107
30130 RST 94
30132 IN (%11100111),A
30134 IN (87),A
30136 IN (194),A
30138 OUT (%11110101),A
30140 OUT (238),A
30142 OUT (239),A
30144 LD BC,(%1011110010110110)
30148 LD BC,(27608)
30152 LD BC,(60478)
30156 LD (%0010010011011010),BC
30160 LD (32593),BC
30164 LD (2973),BC
30168 LD DE,(%1011111010101010)
30172 LD DE,(42993)
30176 LD DE,(62527)
30180 LD (%0100001001001001),DE
30184 LD (40987),DE
30188 LD (10589),DE
30192 LD IX,(%0000111110010010)
30196 LD IX,(39765)
30200 LD IX,(40862)
30204 LD (%1110010100101101),IX
30208 LD (28062),IX
30212 LD (13470),IX
30216 LD IY,(%1101100010011011)
30220 LD IY,(29840)
30224 LD IY,(49827)
30228 LD (%0001001010001001),IY
30232 LD (52000),IY
30236 LD (56225),IY
30240 LD SP,(%0001110010001110)
30244 LD SP,(43260)
30248 LD SP,(12097)
30252 LD (%0011110000100001),SP
30256 LD (10862),SP
30260 LD (57140),SP
30264 LD A,(%0111100000110111)
30267 LD A,(38950)
30270 LD A,(38263)
30273 LD (%0000011111001100),A
30276 LD (40640),A
30279 LD (15582),A
30282 LD HL,(%0110100011101011)
30285 LD HL,(41745)
30288 LD HL,(58654)
30291 LD (%0001100100111010),HL
30294 LD (64199),HL
30297 LD (28519),HL
30300 LD BC,%0001101000111010
30303 LD BC,41497
30306 LD BC,55627
30309 LD DE,%0000100111001011
30312 LD DE,44845
30315 LD DE,18364
30318 LD HL,%1001000010100101
30321 LD HL,6785
30324 LD HL,25899
30327 LD SP,%0011010001010010
30330 LD SP,42622
30333 LD SP,29329
30336 RL (IX+%01100111)
30340 RL (IX+94)
30344 RL (IX+119)
30348 RR (IX+%01101001)
30352 RR (IX+28)
30356 RR (IX+23)
30360 RRC (IX+%00100111)
30364 RRC (IX+79)
30368 RRC (IX+36)
30372 RLC (IX+%01001101)
30376 RLC (IX+114)
30380 RLC (IX+38)
30384 SLA (IX+%01011110)
30388 SLA (IX+101)
30392 SLA (IX+63)
30396 SRA (IX+%00001101)
30400 SRA (IX+107)
30404 SRA (IX+52)
30408 SLL (IX+%00001001)
30412 SLL (IX+34)
30416 SLL (IX+117)
30420 SRL (IX+%01010100)
30424 SRL (IX+50)
30428 SRL (IX+61)
30432 INC (IX-%01101011)
30435 INC (IX-89)
30438 INC (IX-78)
30441 DEC (IX-%01100010)
30444 DEC (IX-75)
30447 DEC (IX-99)
30450 AND (IX-%00000110)
30453 AND (IX-32)
30456 AND (IX-68)
30459 OR (IX-%01100011)
30462 OR (IX-5)
30465 OR (IX-78)
30468 XOR (IX-%01111111)
30471 XOR (IX-79)
30474 XOR (IX-118)
30477 SUB (IX-%01011110)
30480 SUB (IX-63)
30483 SUB (IX-104)
30486 CP (IX-%00001101)
30489 CP (IX-29)
30492 CP (IX-34)
30495 LD A,(IX+%01000001)
30498 LD A,(IX+48)
30501 LD A,(IX+112)
30504 LD (IX-%01110010),A
30507 LD (IX-96),A
30510 LD (IX-16),A
30513 LD B,(IX+%00111010)
30516 LD B,(IX+94)
30519 LD B,(IX+44)
30522 LD (IX-%00000001),B
30525 LD (IX-81),B
30528 LD (IX-111),B
30531 LD C,(IX+%01001011)
30534 LD C,(IX+121)
30537 LD C,(IX+109)
30540 LD (IX-%00101100),C
30543 LD (IX-98),C
30546 LD (IX-103),C
30549 LD D,(IX+%00011000)
30552 LD D,(IX+30)
30555 LD D,(IX+65)
30558 LD (IX-%00111011),D
30561 LD (IX-103),D
30564 LD (IX-74),D
30567 LD E,(IX+%00100101)
30570 LD E,(IX+115)
30573 LD E,(IX+56)
30576 LD (IX-%01110000),E
30579 LD (IX-108),E
30582 LD (IX-46),E
30585 LD H,(IX+%00000101)
30588 LD H,(IX+13)
30591 LD H,(IX+83)
30594 LD (IX-%00011000),H
30597 LD (IX-79),H
30600 LD (IX-76),H
30603 LD L,(IX+%00101010)
30606 LD L,(IX+58)
30609 LD L,(IX+121)
30612 LD (IX-%00010011),L
30615 LD (IX-26),L
30618 LD (IX-122),L
30621 BIT 0,(IX+%00000111)
30625 BIT 0,(IX+87)
30629 BIT 0,(IX+92)
30633 SET 1,(IX+%01011010)
30637 SET 1,(IX+36)
30641 SET 1,(IX+122)
30645 RES 2,(IX+%01110100)
30649 RES 2,(IX+125)
30653 RES 2,(IX+44)
30657 ADD A,(IX-%01011101)
30660 ADD A,(IX-48)
30663 ADD A,(IX-79)
30666 ADC A,(IX-%01111011)
30669 ADC A,(IX-71)
30672 ADC A,(IX-64)
30675 SBC A,(IX-%00110101)
30678 SBC A,(IX-16)
30681 SBC A,(IX-23)
30684 LD IXl,%10110101
30687 LD IXl,17
30690 LD IXl,195
30693 LD IXh,%00000000
30696 LD IXh,178
30699 LD IXh,183
30702 LD (IX+%00001101),%01100110
30706 LD (IX+79),33
30710 LD (IX+100),2
30714 RL (IY+%01000011)
30718 RL (IY+63)
30722 RL (IY+96)
30726 RR (IY+%01011111)
30730 RR (IY+104)
30734 RR (IY+59)
30738 RRC (IY+%01010101)
30742 RRC (IY+106)
30746 RRC (IY+105)
30750 RLC (IY+%01000111)
30754 RLC (IY+43)
30758 RLC (IY+75)
30762 SLA (IY+%01010111)
30766 SLA (IY+52)
30770 SLA (IY+49)
30774 SRA (IY+%01111100)
30778 SRA (IY+122)
30782 SRA (IY+36)
30786 SLL (IY+%01001010)
30790 SLL (IY+38)
30794 SLL (IY+6)
30798 SRL (IY+%00110001)
30802 SRL (IY+116)
30806 SRL (IY+97)
30810 INC (IY-%01000101)
30813 INC (IY-107)
30816 INC (IY-122)
30819 DEC (IY-%00010000)
30822 DEC (IY-31)
30825 DEC (IY-26)
30828 AND (IY-%01111111)
30831 AND (IY-115)
30834 AND (IY-18)
30837 OR (IY-%00101000)
30840 OR (IY-47)
30843 OR (IY-75)
30846 XOR (IY-%01110100)
30849 XOR (IY-51)
30852 XOR (IY-124)
30855 SUB (IY-%01010101)
30858 SUB (IY-87)
30861 SUB (IY-127)
30864 CP (IY-%01000001)
30867 CP (IY-127)
30870 CP (IY-36)
30873 LD A,(IY+%01000111)
30876 LD A,(IY+6)
30879 LD A,(IY+37)
30882 LD (IY-%00010011),A
30885 LD (IY-19),A
30888 LD (IY-39),A
30891 LD B,(IY+%01100100)
30894 LD B,(IY+69)
30897 LD B,(IY+98)
30900 LD (IY-%00001010),B
30903 LD (IY-48),B
30906 LD (IY-75),B
30909 LD C,(IY+%00100110)
30912 LD C,(IY+116)
30915 LD C,(IY+43)
30918 LD (IY-%01010010),C
30921 LD (IY-37),C
30924 LD (IY-94),C
30927 LD D,(IY+%00000010)
30930 LD D,(IY+68)
30933 LD D,(IY+124)
30936 LD (IY-%01101010),D
30939 LD (IY-51),D
30942 LD (IY-13),D
30945 LD E,(IY+%00110110)
30948 LD E,(IY+92)
30951 LD E,(IY+38)
30954 LD (IY-%01100100),E
30957 LD (IY-95),E
30960 LD (IY-116),E
30963 LD H,(IY+%00010100)
30966 LD H,(IY+54)
30969 LD H,(IY+35)
30972 LD (IY-%01100011),H
30975 LD (IY-110),H
30978 LD (IY-91),H
30981 LD L,(IY+%00101001)
30984 LD L,(IY+101)
30987 LD L,(IY+8)
30990 LD (IY-%00010010),L
30993 LD (IY-52),L
30996 LD (IY-112),L
30999 BIT 0,(IY+%01100100)
31003 BIT 0,(IY+126)
31007 BIT 0,(IY+12)
31011 SET 1,(IY+%01100100)
31015 SET 1,(IY+58)
31019 SET 1,(IY+107)
31023 RES 2,(IY+%00001100)
31027 RES 2,(IY+86)
31031 RES 2,(IY+31)
31035 ADD A,(IY-%01001111)
31038 ADD A,(IY-59)
31041 ADD A,(IY-62)
31044 ADC A,(IY-%00110010)
31047 ADC A,(IY-111)
31050 ADC A,(IY-36)
31053 SBC A,(IY-%01100011)
31056 SBC A,(IY-63)
31059 SBC A,(IY-19)
31062 LD IYl,%10100010
31065 LD IYl,201
31068 LD IYl,123
31071 LD IYh,%00011001
31074 LD IYh,239
31077 LD IYh,10
31080 LD (IY+%00100111),%11001110
31084 LD (IY+56),210
31088 LD (IY+57),166
31092 DEFB %01011110
31093 DEFB 122
31094 DEFB 203
31095 DEFM %00110010
31096 DEFM 124
31097 DEFM 32
31098 DEFW %0011010100010011
31100 DEFW 63425
31102 DEFW 24622
31104 DEFS 10,%11001101
31114 DEFS 10,82
31124 DEFS 10,89
31134 LD ( HL ),25
31136 LD ( HL ),37
31138 LD A,"1"
31140 LD HL,("2")
31143 LD B,(IX+"3")
31146 LD (IY+"4"),"4"
31150 LD (IX+"5"),","
31154 LD (IY+"6"),6
31158 LD (IX+"7"),7
31162 LD (IY+7),"7"
31166 LD (IX+8),"8"
31170 LD (IY+8),","
31174 LD (IX+9),","
31178 LD (IY+","),0
31182 LD (IX+","),1
""".strip().split('\n')

TEST_BASE_CONVERSION_HEX = """
30000 LD A,%11101011
30002 LD A,$A2
30004 LD A,$71
30006 LD B,%11001110
30008 LD B,$E4
30010 LD B,$CE
30012 LD C,%01000001
30014 LD C,$15
30016 LD C,$23
30018 LD D,%01101110
30020 LD D,$09
30022 LD D,$5E
30024 LD E,%11110110
30026 LD E,$4D
30028 LD E,$4B
30030 LD H,%11010111
30032 LD H,$17
30034 LD H,$59
30036 LD L,%11011010
30038 LD L,$A2
30040 LD L,$6C
30042 LD (HL),%11100111
30044 LD (HL),$2E
30046 LD (HL),$D1
30048 CALL %1111010101111101
30051 CALL $CF92
30054 CALL $056C
30057 JP %0011101010111111
30060 JP $D28D
30063 JP $C311
30066 DJNZ %111010101110010
30068 DJNZ $7574
30070 DJNZ $7576
30072 JR %111010101111000
30074 JR $757A
30076 JR $757C
30078 AND %10011011
30080 AND $A2
30082 AND $63
30084 OR %00101011
30086 OR $2A
30088 OR $5F
30090 XOR %01001101
30092 XOR $11
30094 XOR $3F
30096 SUB %01011011
30098 SUB $1C
30100 SUB $C3
30102 CP %01001110
30104 CP $17
30106 CP $80
30108 ADD A,%10101111
30110 ADD A,$BB
30112 ADD A,$D3
30114 ADC A,%11000111
30116 ADC A,$86
30118 ADC A,$51
30120 SBC A,%00001000
30122 SBC A,$10
30124 SBC A,$DC
30126 RST %10001001
30128 RST $6B
30130 RST $5E
30132 IN (%11100111),A
30134 IN ($57),A
30136 IN ($C2),A
30138 OUT (%11110101),A
30140 OUT ($EE),A
30142 OUT ($EF),A
30144 LD BC,(%1011110010110110)
30148 LD BC,($6BD8)
30152 LD BC,($EC3E)
30156 LD (%0010010011011010),BC
30160 LD ($7F51),BC
30164 LD ($0B9D),BC
30168 LD DE,(%1011111010101010)
30172 LD DE,($A7F1)
30176 LD DE,($F43F)
30180 LD (%0100001001001001),DE
30184 LD ($A01B),DE
30188 LD ($295D),DE
30192 LD IX,(%0000111110010010)
30196 LD IX,($9B55)
30200 LD IX,($9F9E)
30204 LD (%1110010100101101),IX
30208 LD ($6D9E),IX
30212 LD ($349E),IX
30216 LD IY,(%1101100010011011)
30220 LD IY,($7490)
30224 LD IY,($C2A3)
30228 LD (%0001001010001001),IY
30232 LD ($CB20),IY
30236 LD ($DBA1),IY
30240 LD SP,(%0001110010001110)
30244 LD SP,($A8FC)
30248 LD SP,($2F41)
30252 LD (%0011110000100001),SP
30256 LD ($2A6E),SP
30260 LD ($DF34),SP
30264 LD A,(%0111100000110111)
30267 LD A,($9826)
30270 LD A,($9577)
30273 LD (%0000011111001100),A
30276 LD ($9EC0),A
30279 LD ($3CDE),A
30282 LD HL,(%0110100011101011)
30285 LD HL,($A311)
30288 LD HL,($E51E)
30291 LD (%0001100100111010),HL
30294 LD ($FAC7),HL
30297 LD ($6F67),HL
30300 LD BC,%0001101000111010
30303 LD BC,$A219
30306 LD BC,$D94B
30309 LD DE,%0000100111001011
30312 LD DE,$AF2D
30315 LD DE,$47BC
30318 LD HL,%1001000010100101
30321 LD HL,$1A81
30324 LD HL,$652B
30327 LD SP,%0011010001010010
30330 LD SP,$A67E
30333 LD SP,$7291
30336 RL (IX+%01100111)
30340 RL (IX+$5E)
30344 RL (IX+$77)
30348 RR (IX+%01101001)
30352 RR (IX+$1C)
30356 RR (IX+$17)
30360 RRC (IX+%00100111)
30364 RRC (IX+$4F)
30368 RRC (IX+$24)
30372 RLC (IX+%01001101)
30376 RLC (IX+$72)
30380 RLC (IX+$26)
30384 SLA (IX+%01011110)
30388 SLA (IX+$65)
30392 SLA (IX+$3F)
30396 SRA (IX+%00001101)
30400 SRA (IX+$6B)
30404 SRA (IX+$34)
30408 SLL (IX+%00001001)
30412 SLL (IX+$22)
30416 SLL (IX+$75)
30420 SRL (IX+%01010100)
30424 SRL (IX+$32)
30428 SRL (IX+$3D)
30432 INC (IX-%01101011)
30435 INC (IX-$59)
30438 INC (IX-$4E)
30441 DEC (IX-%01100010)
30444 DEC (IX-$4B)
30447 DEC (IX-$63)
30450 AND (IX-%00000110)
30453 AND (IX-$20)
30456 AND (IX-$44)
30459 OR (IX-%01100011)
30462 OR (IX-$05)
30465 OR (IX-$4E)
30468 XOR (IX-%01111111)
30471 XOR (IX-$4F)
30474 XOR (IX-$76)
30477 SUB (IX-%01011110)
30480 SUB (IX-$3F)
30483 SUB (IX-$68)
30486 CP (IX-%00001101)
30489 CP (IX-$1D)
30492 CP (IX-$22)
30495 LD A,(IX+%01000001)
30498 LD A,(IX+$30)
30501 LD A,(IX+$70)
30504 LD (IX-%01110010),A
30507 LD (IX-$60),A
30510 LD (IX-$10),A
30513 LD B,(IX+%00111010)
30516 LD B,(IX+$5E)
30519 LD B,(IX+$2C)
30522 LD (IX-%00000001),B
30525 LD (IX-$51),B
30528 LD (IX-$6F),B
30531 LD C,(IX+%01001011)
30534 LD C,(IX+$79)
30537 LD C,(IX+$6D)
30540 LD (IX-%00101100),C
30543 LD (IX-$62),C
30546 LD (IX-$67),C
30549 LD D,(IX+%00011000)
30552 LD D,(IX+$1E)
30555 LD D,(IX+$41)
30558 LD (IX-%00111011),D
30561 LD (IX-$67),D
30564 LD (IX-$4A),D
30567 LD E,(IX+%00100101)
30570 LD E,(IX+$73)
30573 LD E,(IX+$38)
30576 LD (IX-%01110000),E
30579 LD (IX-$6C),E
30582 LD (IX-$2E),E
30585 LD H,(IX+%00000101)
30588 LD H,(IX+$0D)
30591 LD H,(IX+$53)
30594 LD (IX-%00011000),H
30597 LD (IX-$4F),H
30600 LD (IX-$4C),H
30603 LD L,(IX+%00101010)
30606 LD L,(IX+$3A)
30609 LD L,(IX+$79)
30612 LD (IX-%00010011),L
30615 LD (IX-$1A),L
30618 LD (IX-$7A),L
30621 BIT 0,(IX+%00000111)
30625 BIT 0,(IX+$57)
30629 BIT 0,(IX+$5C)
30633 SET 1,(IX+%01011010)
30637 SET 1,(IX+$24)
30641 SET 1,(IX+$7A)
30645 RES 2,(IX+%01110100)
30649 RES 2,(IX+$7D)
30653 RES 2,(IX+$2C)
30657 ADD A,(IX-%01011101)
30660 ADD A,(IX-$30)
30663 ADD A,(IX-$4F)
30666 ADC A,(IX-%01111011)
30669 ADC A,(IX-$47)
30672 ADC A,(IX-$40)
30675 SBC A,(IX-%00110101)
30678 SBC A,(IX-$10)
30681 SBC A,(IX-$17)
30684 LD IXl,%10110101
30687 LD IXl,$11
30690 LD IXl,$C3
30693 LD IXh,%00000000
30696 LD IXh,$B2
30699 LD IXh,$B7
30702 LD (IX+%00001101),%01100110
30706 LD (IX+$4F),$21
30710 LD (IX+$64),$02
30714 RL (IY+%01000011)
30718 RL (IY+$3F)
30722 RL (IY+$60)
30726 RR (IY+%01011111)
30730 RR (IY+$68)
30734 RR (IY+$3B)
30738 RRC (IY+%01010101)
30742 RRC (IY+$6A)
30746 RRC (IY+$69)
30750 RLC (IY+%01000111)
30754 RLC (IY+$2B)
30758 RLC (IY+$4B)
30762 SLA (IY+%01010111)
30766 SLA (IY+$34)
30770 SLA (IY+$31)
30774 SRA (IY+%01111100)
30778 SRA (IY+$7A)
30782 SRA (IY+$24)
30786 SLL (IY+%01001010)
30790 SLL (IY+$26)
30794 SLL (IY+$06)
30798 SRL (IY+%00110001)
30802 SRL (IY+$74)
30806 SRL (IY+$61)
30810 INC (IY-%01000101)
30813 INC (IY-$6B)
30816 INC (IY-$7A)
30819 DEC (IY-%00010000)
30822 DEC (IY-$1F)
30825 DEC (IY-$1A)
30828 AND (IY-%01111111)
30831 AND (IY-$73)
30834 AND (IY-$12)
30837 OR (IY-%00101000)
30840 OR (IY-$2F)
30843 OR (IY-$4B)
30846 XOR (IY-%01110100)
30849 XOR (IY-$33)
30852 XOR (IY-$7C)
30855 SUB (IY-%01010101)
30858 SUB (IY-$57)
30861 SUB (IY-$7F)
30864 CP (IY-%01000001)
30867 CP (IY-$7F)
30870 CP (IY-$24)
30873 LD A,(IY+%01000111)
30876 LD A,(IY+$06)
30879 LD A,(IY+$25)
30882 LD (IY-%00010011),A
30885 LD (IY-$13),A
30888 LD (IY-$27),A
30891 LD B,(IY+%01100100)
30894 LD B,(IY+$45)
30897 LD B,(IY+$62)
30900 LD (IY-%00001010),B
30903 LD (IY-$30),B
30906 LD (IY-$4B),B
30909 LD C,(IY+%00100110)
30912 LD C,(IY+$74)
30915 LD C,(IY+$2B)
30918 LD (IY-%01010010),C
30921 LD (IY-$25),C
30924 LD (IY-$5E),C
30927 LD D,(IY+%00000010)
30930 LD D,(IY+$44)
30933 LD D,(IY+$7C)
30936 LD (IY-%01101010),D
30939 LD (IY-$33),D
30942 LD (IY-$0D),D
30945 LD E,(IY+%00110110)
30948 LD E,(IY+$5C)
30951 LD E,(IY+$26)
30954 LD (IY-%01100100),E
30957 LD (IY-$5F),E
30960 LD (IY-$74),E
30963 LD H,(IY+%00010100)
30966 LD H,(IY+$36)
30969 LD H,(IY+$23)
30972 LD (IY-%01100011),H
30975 LD (IY-$6E),H
30978 LD (IY-$5B),H
30981 LD L,(IY+%00101001)
30984 LD L,(IY+$65)
30987 LD L,(IY+$08)
30990 LD (IY-%00010010),L
30993 LD (IY-$34),L
30996 LD (IY-$70),L
30999 BIT 0,(IY+%01100100)
31003 BIT 0,(IY+$7E)
31007 BIT 0,(IY+$0C)
31011 SET 1,(IY+%01100100)
31015 SET 1,(IY+$3A)
31019 SET 1,(IY+$6B)
31023 RES 2,(IY+%00001100)
31027 RES 2,(IY+$56)
31031 RES 2,(IY+$1F)
31035 ADD A,(IY-%01001111)
31038 ADD A,(IY-$3B)
31041 ADD A,(IY-$3E)
31044 ADC A,(IY-%00110010)
31047 ADC A,(IY-$6F)
31050 ADC A,(IY-$24)
31053 SBC A,(IY-%01100011)
31056 SBC A,(IY-$3F)
31059 SBC A,(IY-$13)
31062 LD IYl,%10100010
31065 LD IYl,$C9
31068 LD IYl,$7B
31071 LD IYh,%00011001
31074 LD IYh,$EF
31077 LD IYh,$0A
31080 LD (IY+%00100111),%11001110
31084 LD (IY+$38),$D2
31088 LD (IY+$39),$A6
31092 DEFB %01011110
31093 DEFB $7A
31094 DEFB $CB
31095 DEFM %00110010
31096 DEFM $7C
31097 DEFM $20
31098 DEFW %0011010100010011
31100 DEFW $F7C1
31102 DEFW $602E
31104 DEFS $0A,%11001101
31114 DEFS $0A,$52
31124 DEFS $0A,$59
31134 LD ( HL ),$19
31136 LD ( HL ),$25
31138 LD A,"1"
31140 LD HL,("2")
31143 LD B,(IX+"3")
31146 LD (IY+"4"),"4"
31150 LD (IX+"5"),","
31154 LD (IY+"6"),$06
31158 LD (IX+"7"),$07
31162 LD (IY+$07),"7"
31166 LD (IX+$08),"8"
31170 LD (IY+$08),","
31174 LD (IX+$09),","
31178 LD (IY+","),$00
31182 LD (IX+","),$01
""".strip().split('\n')

class SkoolParserTest(SkoolKitTestCase):
    def _get_parser(self, contents, *args, **kwargs):
        skoolfile = self.write_text_file(contents, suffix='.skool')
        return SkoolParser(skoolfile, *args, **kwargs)

    def assert_error(self, skool, error, *args, **kwargs):
        with self.assertRaises(SkoolParsingError) as cm:
            self._get_parser(skool, *args, **kwargs)
        self.assertEqual(cm.exception.args[0], error)

    def test_invalid_entry_address(self):
        self.assert_error('c3000f RET', "Invalid address: '3000f'")

    def test_entry_sizes(self):
        skool = '\n'.join((
            'c65500 RET',
            '',
            'c65501 JP 65500'
            '',
            'i65504'
        ))
        entries = self._get_parser(skool, html=True).memory_map
        self.assertEqual(len(entries), 3)
        self.assertEqual(entries[0].size, 1)
        self.assertEqual(entries[1].size, 3)
        self.assertEqual(entries[2].size, 32)

    def test_html_escape(self):
        skool = 'c24576 NOP ; Return if X<=Y & Y>=Z'
        parser = self._get_parser(skool, html=True)
        inst = parser.get_instruction(24576)
        self.assertEqual(inst.comment.text, 'Return if X&lt;=Y &amp; Y&gt;=Z')

    def test_html_no_escape(self):
        skool = 'c49152 NOP ; Return if X<=Y & Y>=Z'
        parser = self._get_parser(skool, html=False)
        inst = parser.get_instruction(49152)
        self.assertEqual(inst.comment.text, 'Return if X<=Y & Y>=Z')

    def test_html_macro(self):
        skool = '\n'.join((
            'c24577 NOP ; #HTML(1. See <a href="url">this</a>)',
            '           ; #HTML[2. See <a href="url">this</a>]',
            '           ; #HTML{3. See <a href="url">this</a>}',
            '           ; #HTML@4. See <a href="url">this</a>@',
            '           ; #HTML!5. See <a href="url">this</a>!',
            '           ; #HTML%6. See <a href="url">this</a>%',
            '           ; #HTML*7. See <a href="url">this</a>*',
            '           ; #HTML_8. See <a href="url">this</a>_',
            '           ; #HTML-9. See <a href="url">this</a>-',
            '           ; #HTML+10. See <a href="url">this</a>+',
            '           ; #HTML??',
            '           ; #HTML|#CHR169|',
            '           ; #HTML:This macro is <em>unterminated</em>',
            '; Test the HTML macro with an empty parameter string',
            ' 24588 NOP ; #HTML'
        ))
        parser = self._get_parser(skool, html=True)

        delimiters = {
            '(': ')',
            '[': ']',
            '{': '}'
        }
        text = parser.get_instruction(24577).comment.text
        lines = []
        for i, delim1 in enumerate('([{@!%*_-+', 1):
            delim2 = delimiters.get(delim1, delim1)
            lines.append('#HTML{0}{1}. See <a href="url">this</a>{2}'.format(delim1, i, delim2))
        lines.append('#HTML??')
        lines.append('#HTML|#CHR169|')
        lines.append('#HTML:This macro is <em>unterminated</em>')
        self.assertEqual(text, ' '.join(lines))

        self.assertEqual(parser.get_instruction(24588).comment.text, '#HTML')

    def test_font_macro_text_parameter(self):
        macros = (
            '#FONT:(1. A < B)0',
            '#FONT:[2. A & B]8',
            '#FONT:{3. A > B}16',
            '#FONT:@4. A <> B@24',
            '#FONT:??',
            '#FONT:*This macro is <unterminated>'
        )
        skool = '\n'.join((
            ('; Test the FONT macro text parameter',
             'c24577 NOP ; {}') +
            ('           ; {}',) * (len(macros) - 1) +
            ('; Test the FONT macro with an empty parameter string',
             ' 24588 NOP ; #FONT:')
        )).format(*macros)
        parser = self._get_parser(skool, html=True)

        text = parser.get_instruction(24577).comment.text
        self.assertEqual(text, ' '.join(macros))

        self.assertEqual(parser.get_instruction(24588).comment.text, '#FONT:')

    def test_entry_title(self):
        title = 'This is an entry title'
        skool = '\n'.join((
            '; {}'.format(title),
            'c30000 RET'
        ))
        parser = self._get_parser(skool, html=False)
        self.assertEqual(parser.get_entry(30000).description, title)

    def test_entry_description(self):
        description = 'This is an entry description'
        skool = '\n'.join((
            '; Routine at 30000',
            ';',
            '; {}'.format(description),
            'c30000 RET'
        ))
        parser = self._get_parser(skool, html=False)
        self.assertEqual([description], parser.get_entry(30000).details)

    def test_multi_paragraph_entry_description(self):
        description = ['Paragraph 1', 'Paragraph 2']
        skool = '\n'.join((
            '; Test a multi-paragraph description',
            ';',
            '; {}'.format(description[0]),
            '; .',
            '; {}'.format(description[1]),
            'c40000 RET'
        ))
        parser = self._get_parser(skool, html=False)
        self.assertEqual(description, parser.get_entry(40000).details)

    def test_empty_entry_description(self):
        skool = '\n'.join((
            '; Test an empty description',
            ';',
            '; .',
            ';',
            '; A 0',
            'c25600 RET'
        ))
        parser = self._get_parser(skool, html=False)
        entry = parser.get_entry(25600)
        self.assertEqual(entry.details, [])
        registers = entry.registers
        self.assertEqual(len(registers), 1)
        reg_a = registers[0]
        self.assertEqual(reg_a.name, 'A')

    def test_registers(self):
        skool = '\n'.join((
            '; Test register parsing (1)',
            ';',
            '; Traditional.',
            ';',
            '; A Some value',
            '; B Some other value',
            '; C',
            'c24589 RET',
            '',
            '; Test register parsing (2)',
            ';',
            '; With prefixes.',
            ';',
            '; Input:A Some value',
            ';       B Some other value',
            '; Output:HL The result',
            'c24590 RET'
        ))
        parser = self._get_parser(skool, html=False)

        # Traditional
        registers = parser.get_entry(24589).registers
        self.assertEqual(len(registers), 3)
        reg_a = registers[0]
        self.assertEqual(reg_a.prefix, '')
        self.assertEqual(reg_a.name, 'A')
        self.assertEqual(reg_a.contents, 'Some value')
        reg_b = registers[1]
        self.assertEqual(reg_b.prefix, '')
        self.assertEqual(reg_b.name, 'B')
        self.assertEqual(reg_b.contents, 'Some other value')
        reg_c = registers[2]
        self.assertEqual(reg_c.prefix, '')
        self.assertEqual(reg_c.name, 'C')
        self.assertEqual(reg_c.contents, '')

        # With prefixes
        registers = parser.get_entry(24590).registers
        self.assertEqual(len(registers), 3)
        reg_a = registers[0]
        self.assertEqual(reg_a.prefix, 'Input')
        self.assertEqual(reg_a.name, 'A')
        self.assertEqual(reg_a.contents, 'Some value')
        reg_b = registers[1]
        self.assertEqual(reg_b.prefix, '')
        self.assertEqual(reg_b.name, 'B')
        self.assertEqual(reg_b.contents, 'Some other value')
        reg_hl = registers[2]
        self.assertEqual(reg_hl.prefix, 'Output')
        self.assertEqual(reg_hl.name, 'HL')
        self.assertEqual(reg_hl.contents, 'The result')

    def test_registers_in_non_code_blocks(self):
        skool = '\n'.join((
            '; Byte',
            ';',
            '; .',
            ';',
            '; A Some value',
            'b54321 DEFB 0',
            '',
            '; GSB entry',
            ';',
            '; .',
            ';',
            '; B Some value',
            'g54322 DEFB 0',
            '',
            '; Space',
            ';',
            '; .',
            ';',
            '; C Some value',
            's54323 DEFS 10',
            '',
            '; Message',
            ';',
            '; .',
            ';',
            '; D Some value',
            't54333 DEFM "Hi"',
            '',
            '; Unused code',
            ';',
            '; .',
            ';',
            '; E Some value',
            'u54335 LD HL,12345',
            '',
            '; Words',
            ';',
            '; .',
            ';',
            '; H Some value',
            'w54338 DEFW 1,2'
        ))
        parser = self._get_parser(skool, html=False)

        for address, reg_name in ((54321, 'A'), (54322, 'B'), (54323, 'C'), (54333, 'D'), (54335, 'E'), (54338, 'H')):
            registers = parser.get_entry(address).registers
            self.assertEqual(len(registers), 1)
            reg = registers[0]
            self.assertEqual(reg.name, reg_name)
            self.assertEqual(reg.contents, 'Some value')

    def test_register_description_continuation_lines(self):
        skool = '\n'.join((
            '; Routine',
            ';',
            '; .',
            ';',
            '; BC This register description is long enough that it needs to be',
            ';   .split over two lines',
            '; DE Short register description',
            '; HL Another register description that is long enough to need',
            '; .  splitting over two lines',
            'c40000 RET'
        ))
        parser = self._get_parser(skool, html=False)

        registers = parser.get_entry(40000).registers
        self.assertEqual(len(registers), 3)
        self.assertEqual(registers[0].name, 'BC')
        self.assertEqual(registers[0].contents, 'This register description is long enough that it needs to be split over two lines')
        self.assertEqual(registers[1].name, 'DE')
        self.assertEqual(registers[1].contents, 'Short register description')
        self.assertEqual(registers[2].name, 'HL')
        self.assertEqual(registers[2].contents, 'Another register description that is long enough to need splitting over two lines')

    def test_empty_register_section(self):
        skool = '\n'.join((
            '; Title',
            ';',
            '; Description',
            ';',
            '; .',
            ';',
            '; Start comment.',
            'c49152 RET'
        ))
        parser = self._get_parser(skool, html=False)
        self.assertEqual([], parser.get_entry(49152).registers)

    def test_registers_html_escape(self):
        skool = '\n'.join((
            '; Title',
            ';',
            '; Description',
            ';',
            '; A Some value > 4',
            '; B Some value < 8',
            'c49152 RET'
        ))
        parser = self._get_parser(skool, html=True)

        registers = parser.get_entry(49152).registers
        self.assertEqual(len(registers), 2)
        self.assertEqual(registers[0].contents, 'Some value &gt; 4')
        self.assertEqual(registers[1].contents, 'Some value &lt; 8')

    def test_registers_html_no_escape(self):
        skool = '\n'.join((
            '; Title',
            ';',
            '; Description',
            ';',
            '; A Some value > 8',
            '; B Some value < 10',
            'c32768 RET'
        ))
        parser = self._get_parser(skool, html=False)

        registers = parser.get_entry(32768).registers
        self.assertEqual(len(registers), 2)
        self.assertEqual(registers[0].contents, 'Some value > 8')
        self.assertEqual(registers[1].contents, 'Some value < 10')

    def test_start_comment(self):
        exp_start_comment = 'This is a start comment.'
        skool = '\n'.join((
            '; Test a start comment',
            ';',
            '; .',
            ';',
            '; .',
            ';',
            '; {}'.format(exp_start_comment),
            'c50000 RET'
        ))
        parser = self._get_parser(skool, html=False)
        start_comment = parser.get_instruction(50000).mid_block_comment
        self.assertEqual([exp_start_comment], start_comment)

    def test_multi_paragraph_start_comment(self):
        exp_start_comment = ['First paragraph.', 'Second paragraph.']
        skool = '\n'.join((
            '; Test a multi-paragraph start comment',
            ';',
            '; .',
            ';',
            '; .',
            ';',
            '; {}'.format(exp_start_comment[0]),
            '; .',
            '; {}'.format(exp_start_comment[1]),
            'c50000 RET'
        ))
        parser = self._get_parser(skool, html=False)
        start_comment = parser.get_instruction(50000).mid_block_comment
        self.assertEqual(exp_start_comment, start_comment)

    def test_snapshot(self):
        skool = '\n'.join((
            '; Test snapshot building',
            'b24591 DEFB 1',
            ' 24592 DEFW 300',
            ' 24594 DEFM "abc"',
            ' 24597 DEFS 3,7',
            ' 24600 DEFB $A0',
            ' 24601 DEFW $812C',
            ' 24603 DEFM "ab",$11',
            ' 24606 DEFS $03,%10101010',
            ' 24609 DEFB %00001111,"c"',
            ' 24611 DEFW %1010101000001111',
            ' 24613 DEFM %11110000,"bc"',
            ' 24616 DEFS 2'
        ))
        parser = self._get_parser(skool)
        self.assertEqual(parser.snapshot[24591:24600], [1, 44, 1, 97, 98, 99, 7, 7, 7])
        self.assertEqual(parser.snapshot[24600:24609], [160, 44, 129, 97, 98, 17, 170, 170, 170])
        self.assertEqual(parser.snapshot[24609:24618], [15, 99, 15, 170, 240, 98, 99, 0, 0])

    def test_nested_braces(self):
        skool = '\n'.join((
            '; Test nested braces in a multi-line comment',
            'b32768 DEFB 0 ; {These bytes are {REALLY} {{IMPORTANT}}!',
            ' 32769 DEFB 0 ; }'
        ))
        parser = self._get_parser(skool)
        comment = parser.get_instruction(32768).comment.text
        self.assertEqual(comment, 'These bytes are {REALLY} {{IMPORTANT}}!')

    def test_braces_in_comments(self):
        skool = '\n'.join((
            '; Test comments that start or end with a brace',
            'b30000 DEFB 0 ; {{Unmatched closing',
            ' 30001 DEFB 0 ; brace} }',
            ' 30002 DEFB 0 ; { {Matched',
            ' 30003 DEFB 0 ; braces} }',
            ' 30004 DEFB 0 ; { {Unmatched opening',
            ' 30005 DEFB 0 ; brace }}',
            ' 30006 DEFB 0 ; {{{Unmatched closing braces}} }',
            ' 30007 DEFB 0 ; { {{Matched braces (2)}} }',
            ' 30008 DEFB 0 ; { {{Unmatched opening braces}}}'
        ))
        parser = self._get_parser(skool)
        exp_comments = (
            (30000, 'Unmatched closing brace}'),
            (30002, '{Matched braces}'),
            (30004, '{Unmatched opening brace'),
            (30006, 'Unmatched closing braces}}'),
            (30007, '{{Matched braces (2)}}'),
            (30008, '{{Unmatched opening braces')
        )
        for address, exp_text in exp_comments:
            text = parser.get_instruction(address).comment.text
            self.assertEqual(text, exp_text)

    def test_unmatched_opening_braces_in_instruction_comments(self):
        skool = '\n'.join((
            'b50000 DEFB 0 ; {The unmatched {opening brace} in this comment should be',
            ' 50001 DEFB 0 ; implicitly closed by the end of this entry',
            '',
            'b50002 DEFB 0 ; {The unmatched {opening brace} in this comment should be',
            ' 50003 DEFB 0 ; implicitly closed by the following mid-block comment',
            '; Here is the mid-block comment.',
            ' 50004 DEFB 0 ; The closing brace in this comment is unmatched}',
        ))
        parser = self._get_parser(skool)
        exp_comments = (
            (50000, 2, 'The unmatched {opening brace} in this comment should be implicitly closed by the end of this entry'),
            (50002, 2, 'The unmatched {opening brace} in this comment should be implicitly closed by the following mid-block comment'),
            (50004, 1, 'The closing brace in this comment is unmatched}')
        )
        for address, exp_rowspan, exp_text in exp_comments:
            comment = parser.get_instruction(address).comment
            self.assertEqual(comment.text, exp_text)
            self.assertEqual(comment.rowspan, exp_rowspan)

    def test_end_comments(self):
        skool = '\n'.join((
            '; First routine',
            'c45192 RET',
            '; The end of the first routine.',
            '; .',
            '; Really.',
            '',
            '; Second routine',
            'c45193 RET',
            '; The end of the second routine.'
        ))
        parser = self._get_parser(skool)
        memory_map = parser.memory_map
        self.assertEqual(len(memory_map), 2)
        self.assertEqual(memory_map[0].end_comment, ['The end of the first routine.', 'Really.'])
        self.assertEqual(memory_map[1].end_comment, ['The end of the second routine.'])

    def test_data_definition_entry(self):
        skool = '\n'.join((
            '; Data',
            'd30000 DEFB 1,2,3',
            ' 50000 DEFB 3,2,1'
        ))
        parser = self._get_parser(skool)
        self.assertEqual(len(parser.memory_map), 0)
        snapshot = parser.snapshot
        self.assertEqual(snapshot[30000:30003], [1, 2, 3])
        self.assertEqual(snapshot[50000:50003], [3, 2, 1])

    def test_remote_entry(self):
        skool = '\n'.join((
            'r16384 start',
            '',
            '; Routine',
            'c32768 JP $4000',
        ))
        parser = self._get_parser(skool)
        memory_map = parser.memory_map
        self.assertEqual(len(memory_map), 1)
        instructions = memory_map[0].instructions
        self.assertEqual(len(instructions), 1)
        reference = instructions[0].reference
        self.assertFalse(reference is None)
        self.assertEqual(reference.address, 16384)
        self.assertEqual(reference.addr_str, '$4000')
        entry = reference.entry
        self.assertTrue(entry.is_remote())
        self.assertEqual(entry.asm_id, 'start')
        self.assertEqual(entry.address, 16384)

    def test_references(self):
        skool = '\n'.join((
            '; Routine',
            'c30000 CALL 30010',
            ' 30003 JP NZ,30011',
            ' 30004 LD BC,30012',
            ' 30006 DJNZ 30013',
            ' 30008 JR 30014',
            '',
            '; Routine',
            'c30010 LD A,B',
            ' 30011 LD A,C',
            ' 30012 LD A,D',
            ' 30013 LD A,E',
            ' 30014 RET',
            '',
            '; Data',
            'w30015 DEFW 30003'
        ))
        parser = self._get_parser(skool)
        memory_map = parser.memory_map
        self.assertEqual(len(memory_map), 3)
        instructions = memory_map[0].instructions
        self.assertEqual(len(instructions), 5)

        ref_address = 30010
        for instruction in instructions:
            reference = instruction.reference
            self.assertIsNotNone(reference)
            self.assertEqual(reference.address, ref_address)
            self.assertEqual(reference.entry.address, 30010)
            ref_address += 1

        instructions = memory_map[2].instructions
        self.assertEqual(len(instructions), 1)
        reference = instructions[0].reference
        self.assertIsNotNone(reference)
        self.assertEqual(reference.address, 30003)
        self.assertEqual(reference.entry.address, 30000)

    def test_references_for_ld_instructions(self):
        skool = '\n'.join((
            'c00100 LD BC,100',
            ' 00103 LD DE,100',
            ' 00106 LD HL,100',
            ' 00109 LD IX,100',
            ' 00112 LD IY,100',
            ' 00115 LD SP,100',
            ' 00118 LD BC,(100)',
            ' 00122 LD DE,(100)',
            ' 00126 LD HL,(100)',
            ' 00129 LD IX,(100)',
            ' 00133 LD IY,(100)',
            ' 00137 LD SP,(100)',
            ' 00141 LD (100),BC',
            ' 00145 LD (100),DE',
            ' 00149 LD (100),HL',
            ' 00152 LD (100),IX',
            ' 00156 LD (100),IY',
            ' 00160 LD (100),SP',
            ' 00164 LD A,(100)',
            ' 00167 LD (100),A'
        ))
        parser = self._get_parser(skool)

        instructions = parser.memory_map[0].instructions
        self.assertEqual(len(instructions[0].referrers), 0)
        for instruction in instructions:
            self.assertIsNotNone(instruction.reference)
            self.assertEqual(instruction.reference.address, 100)

    def test_references_for_rst_instructions(self):
        skool = (
            '@start',
            '; Restart routines',
            '@label=RESTART0',
            'c00000 DEFS 8',
            '@label=RESTART8',
            ' 00008 DEFS 8',
            '@label=RESTART16',
            ' 00016 DEFS 8',
            '@label=RESTART24',
            ' 00024 DEFS 8',
            '@label=RESTART32',
            ' 00032 DEFS 8',
            '@label=RESTART40',
            ' 00040 DEFS 8',
            '@label=RESTART48',
            ' 00048 DEFS 8',
            '@label=RESTART56',
            ' 00056 RET',
            '',
            '; RST instructions',
            'c00057 RST 0',
            ' 00058 RST $08',
            ' 00059 RST 16',
            ' 00060 RST $18',
            ' 00061 RST 32',
            ' 00062 RST $28',
            ' 00063 RST 48',
            ' 00064 RST $38',
        )
        parser = self._get_parser('\n'.join(skool), asm_mode=1)
        self.assertEqual(len(parser.get_entry(0).instructions[0].referrers), 1)
        index = 20
        ref_address = 0
        for instruction in parser.get_entry(57).instructions:
            self.assertEqual(instruction.operation, skool[index][7:])
            self.assertIsNotNone(instruction.reference)
            self.assertEqual(instruction.reference.address, ref_address)
            index += 1
            ref_address += 8

    def test_references_to_data_block(self):
        skool = '\n'.join((
            '@start',
            'c40000 LD HL,40005',
            '',
            'w40003 DEFW 40005',
            '',
            'b40005 DEFB 0'
        ))
        memory_map = self._get_parser(skool, asm_mode=1).memory_map
        self.assertEqual(memory_map[0].instructions[0].reference.address, 40005)
        self.assertEqual(memory_map[1].instructions[0].reference.address, 40005)

    def test_references_to_ignored_entry(self):
        skool = '\n'.join((
            '; Routine',
            'c30000 CALL 30010',
            ' 30003 JP NZ,30010',
            ' 30004 LD BC,30010',
            ' 30006 DJNZ 30010',
            ' 30008 JR 30010',
            '',
            '; Ignored',
            'i30010'
        ))
        parser = self._get_parser(skool)
        instructions = parser.memory_map[0].instructions
        self.assertEqual(len(instructions), 5)
        for instruction in instructions:
            self.assertIsNone(instruction.reference)

    def test_create_labels(self):
        skool = '\n'.join((
            '@start',
            '; Begin',
            'c32768 JR 32770',
            '',
            '; End',
            'c32770 JR 32768',
        ))
        parser = self._get_parser(skool, create_labels=True, asm_labels=True)
        instruction = parser.get_entry(32768).instructions[0]
        self.assertEqual(instruction.asm_label, 'L32768')
        self.assertEqual(instruction.operation, 'JR L32770')
        instruction = parser.get_entry(32770).instructions[0]
        self.assertEqual(instruction.asm_label, 'L32770')
        self.assertEqual(instruction.operation, 'JR L32768')

    def test_create_no_labels(self):
        skool = '\n'.join((
            '@start',
            '@label=START',
            'c32768 JR 32770',
            '',
            'c32770 JR 32768',
        ))
        parser = self._get_parser(skool, create_labels=False, asm_labels=True)
        instruction = parser.get_entry(32768).instructions[0]
        self.assertEqual(instruction.asm_label, 'START')
        self.assertEqual(instruction.operation, 'JR 32770')
        instruction = parser.get_entry(32770).instructions[0]
        self.assertIsNone(instruction.asm_label)
        self.assertEqual(instruction.operation, 'JR START')

    def test_set_directive(self):
        skool = '\n'.join((
            '@start',
            '@set-prop1=1',
            '@set-prop2=abc',
            '; Routine',
            'c30000 RET'
        ))
        parser = self._get_parser(skool, asm_mode=1)
        for name, value in (('prop1', '1'), ('prop2', 'abc')):
            self.assertIn(name, parser.properties)
            self.assertEqual(parser.properties[name], value)

    def test_set_bytes(self):
        # DEFB
        snapshot = [0] * 10
        set_bytes(snapshot, 0, 'DEFB 1,2,3')
        self.assertEqual(snapshot[:3], [1, 2, 3])
        set_bytes(snapshot, 2, 'DEFB 5, "AB"')
        self.assertEqual(snapshot[2:5], [5, 65, 66])

        # DEFM
        snapshot = [0] * 10
        set_bytes(snapshot, 7, 'DEFM "ABC"')
        self.assertEqual(snapshot[7:], [65, 66, 67])
        set_bytes(snapshot, 0, 'DEFM "\\"A\\""')
        self.assertEqual(snapshot[:3], [34, 65, 34])
        set_bytes(snapshot, 5, 'DEFM "C:\\\\",12')
        self.assertEqual(snapshot[5:9], [67, 58, 92, 12])

        # DEFW
        snapshot = [0] * 10
        set_bytes(snapshot, 3, 'DEFW 1,258')
        self.assertEqual(snapshot[3:7], [1, 0, 2, 1])

        # DEFS
        snapshot = [8] * 10
        set_bytes(snapshot, 0, 'DEFS 10')
        self.assertEqual(snapshot, [0] * 10)
        set_bytes(snapshot, 0, 'DEFS 10,3')
        self.assertEqual(snapshot, [3] * 10)

    def test_warn_ld_operand(self):
        skool = '\n'.join((
            '@start',
            '; Routine',
            'c32768 LD HL,32774',
            ' 32771 ld de,32774',
            '',
            '; Next routine',
            '@label=DOSTUFF',
            'c32774 RET'
        ))
        self._get_parser(skool, asm_mode=1, warnings=True)
        warnings = self.err.getvalue().split('\n')[:-1]
        exp_warnings = [
            'WARNING: LD operand replaced with routine label in unsubbed operation:',
            '  32768 LD HL,32774 -> LD HL,DOSTUFF',
            'WARNING: LD operand replaced with routine label in unsubbed operation:',
            '  32771 ld de,32774 -> ld de,DOSTUFF'
        ]
        self.assertEqual(exp_warnings, warnings)

    def test_instruction_addr_str_no_base(self):
        skool = '\n'.join((
            'b00000 DEFB 0',
            '',
            'c24583 LD HL,$6003',
            '',
            'b$600A DEFB 123'
        ))
        parser = self._get_parser(skool)
        self.assertEqual(parser.get_instruction(0).addr_str, '00000')
        self.assertEqual(parser.get_instruction(24583).addr_str, '24583')
        self.assertEqual(parser.get_instruction(24586).addr_str, '600A')

    def test_instruction_addr_str_base_10(self):
        skool = '\n'.join((
            'b$0000 DEFB 0',
            '',
            'c24583 LD HL,$6003',
            '',
            'b$600A DEFB 123'
        ))
        parser = self._get_parser(skool, base=BASE_10)
        self.assertEqual(parser.get_instruction(0).addr_str, '00000')
        self.assertEqual(parser.get_instruction(24583).addr_str, '24583')
        self.assertEqual(parser.get_instruction(24586).addr_str, '24586')

    def test_instruction_addr_str_base_16(self):
        skool = '\n'.join((
            'b00000 DEFB 0',
            '',
            'c24583 LD HL,$6003',
            '',
            'b$600A DEFB 123'
        ))
        parser = self._get_parser(skool, base=BASE_16)
        self.assertEqual(parser.get_instruction(0).addr_str, '0000')
        self.assertEqual(parser.get_instruction(24583).addr_str, '6007')
        self.assertEqual(parser.get_instruction(24586).addr_str, '600A')

    def test_instruction_addr_str_base_16_lower_case(self):
        skool = '\n'.join((
            'c24583 LD HL,$6003',
            '',
            'b$600A DEFB 123'
        ))
        parser = self._get_parser(skool, case=CASE_LOWER, base=BASE_16)
        self.assertEqual(parser.get_instruction(24583).addr_str, '6007')
        self.assertEqual(parser.get_instruction(24586).addr_str, '600a')

    def test_get_instruction_addr_str_no_base(self):
        skool = '\n'.join((
            'c24583 LD HL,$6003',
            '',
            'b$600A DEFB 123'
        ))
        parser = self._get_parser(skool)
        self.assertEqual(parser.get_instruction_addr_str(24583, ''), '24583')
        self.assertEqual(parser.get_instruction_addr_str(24586, ''), '600A')
        self.assertEqual(parser.get_instruction_addr_str(24586, 'start'), '24586')

    def test_get_instruction_addr_str_base_10(self):
        skool = '\n'.join((
            'c24583 LD HL,$6003',
            '',
            'b$600A DEFB 123'
        ))
        parser = self._get_parser(skool, base=BASE_10)
        self.assertEqual(parser.get_instruction_addr_str(24583, ''), '24583')
        self.assertEqual(parser.get_instruction_addr_str(24586, ''), '24586')
        self.assertEqual(parser.get_instruction_addr_str(24586, 'load'), '24586')

    def test_get_instruction_addr_str_base_16(self):
        skool = '\n'.join((
            'c24583 LD HL,$6003',
            '',
            'b$600A DEFB 123'
        ))
        parser = self._get_parser(skool, base=BASE_16)
        self.assertEqual(parser.get_instruction_addr_str(24583, ''), '6007')
        self.assertEqual(parser.get_instruction_addr_str(24586, ''), '600A')
        self.assertEqual(parser.get_instruction_addr_str(24586, 'save'), '600A')

    def test_get_instruction_addr_str_base_16_lower_case(self):
        skool = '\n'.join((
            'c24583 LD HL,$6003',
            '',
            'b$600A DEFB 123'
        ))
        parser = self._get_parser(skool, case=CASE_LOWER, base=BASE_16)
        self.assertEqual(parser.get_instruction_addr_str(24583, ''), '6007')
        self.assertEqual(parser.get_instruction_addr_str(24586, ''), '600a')
        self.assertEqual(parser.get_instruction_addr_str(24586, 'save'), '600a')

    def test_base_conversion_no_base(self):
        parser = self._get_parser(TEST_BASE_CONVERSION_SKOOL, base=None)
        for line in TEST_BASE_CONVERSION_SKOOL.split('\n'):
            self.assertEqual(parser.get_instruction(int(line[1:6])).operation, line[7:])

    def test_base_conversion_decimal(self):
        parser = self._get_parser(TEST_BASE_CONVERSION_SKOOL, base=BASE_10)
        for line in TEST_BASE_CONVERSION_DECIMAL:
            self.assertEqual(parser.get_instruction(int(line[:5])).operation, line[6:])

    def test_base_conversion_hexadecimal(self):
        parser = self._get_parser(TEST_BASE_CONVERSION_SKOOL, base=BASE_16)
        for line in TEST_BASE_CONVERSION_HEX:
            self.assertEqual(parser.get_instruction(int(line[:5])).operation, line[6:])

    def test_base_conversion_hexadecimal_lower_case(self):
        skool = '\n'.join((
            'c32768 LD A,10',
            ' 32770 LD B,$AF',
            ' 32772 LD C,%01010101',
            ' 32774 LD D,"A"',
            ' 32776 DEFB 10,$AF',
            ' 32778 DEFW 32778,$ABCD',
            ' 32782 DEFS 10,$FF'
        ))
        exp_instructions = (
            (32768, 'ld a,$0a'),
            (32770, 'ld b,$af'),
            (32772, 'ld c,%01010101'),
            (32774, 'ld d,"A"'),
            (32776, 'defb $0a,$af'),
            (32778, 'defw $800a,$abcd'),
            (32782, 'defs $0a,$ff')
        )
        parser = self._get_parser(skool, base=BASE_16, case=CASE_LOWER)
        for address, exp_operation in exp_instructions:
            self.assertEqual(parser.get_instruction(address).operation, exp_operation)

    def test_base_conversion_hexadecimal_upper_case(self):
        skool = '\n'.join((
            'c32768 ld a,10',
            ' 32770 ld b,$af',
            ' 32772 ld c,%01010101',
            ' 32774 ld d,"a"',
            ' 32776 defb 10,$af',
            ' 32778 defw 32778,$abcd',
            ' 32782 defs 10,$ff'
        ))
        exp_instructions = (
            (32768, 'LD A,$0A'),
            (32770, 'LD B,$AF'),
            (32772, 'LD C,%01010101'),
            (32774, 'LD D,"a"'),
            (32776, 'DEFB $0A,$AF'),
            (32778, 'DEFW $800A,$ABCD'),
            (32782, 'DEFS $0A,$FF')
        )
        parser = self._get_parser(skool, base=BASE_16, case=CASE_UPPER)
        for address, exp_operation in exp_instructions:
            self.assertEqual(parser.get_instruction(address).operation, exp_operation)

    def test_base_conversion_retains_whitespace(self):
        skool = '\n'.join((
            'c40000 LD A, 10',
            ' 40002 LD ( HL ), 20',
            ' 40004 DEFB 17, "1"',
            ' 40006 DEFM 89, "2"',
            ' 40008 DEFS 8, "3"',
            ' 40016 DEFW 0, "4"'
        ))
        exp_instructions = (
            (40000, 'LD A, $0A'),
            (40002, 'LD ( HL ), $14'),
            (40004, 'DEFB $11, "1"'),
            (40006, 'DEFM $59, "2"'),
            (40008, 'DEFS $08, "3"'),
            (40016, 'DEFW $0000, "4"')
        )
        parser = self._get_parser(skool, base=BASE_16)
        for address, operation in exp_instructions:
            self.assertEqual(parser.get_instruction(address).operation, operation)

    def test_no_case_conversion(self):
        skool = '\n'.join((
            'c54000 LD A,0',
            ' 54002 ld b,1',
            ' 54004 Ret',
        ))
        exp_instructions = (
            (54000, 'LD A,0'),
            (54002, 'ld b,1'),
            (54004, 'Ret'),
        )
        parser = self._get_parser(skool, case=None)
        for address, operation in exp_instructions:
            self.assertEqual(parser.get_instruction(address).operation, operation)

    def test_lower_case_conversion_with_character_operands(self):
        skool = '\n'.join((
            'c54000 LD A,"A"',
            ' 54002 LD B,(IX+"B")',
            ' 54005 LD (IY+"C"),C',
            ' 54008 LD (IX+"\\""),"D"',
        ))
        exp_instructions = (
            (54000, 'ld a,"A"'),
            (54002, 'ld b,(ix+"B")'),
            (54005, 'ld (iy+"C"),c'),
            (54008, 'ld (ix+"\\""),"D"'),
        )
        parser = self._get_parser(skool, case=CASE_LOWER)
        for address, operation in exp_instructions:
            self.assertEqual(parser.get_instruction(address).operation, operation)

    def test_upper_case_conversion_with_character_operands(self):
        skool = '\n'.join((
            'c54000 ld a,"a"',
            ' 54002 ld b,(ix+"b")',
            ' 54005 ld (iy+"c"),c',
            ' 54008 ld (ix+"\\""),"d"',
        ))
        exp_instructions = (
            (54000, 'LD A,"a"'),
            (54002, 'LD B,(IX+"b")'),
            (54005, 'LD (IY+"c"),C'),
            (54008, 'LD (IX+"\\""),"d"'),
        )
        parser = self._get_parser(skool, case=CASE_UPPER)
        for address, operation in exp_instructions:
            self.assertEqual(parser.get_instruction(address).operation, operation)

    def test_upper_case_conversion_with_index_registers(self):
        skool = '\n'.join((
            'c55000 ld ixl,a',
            ' 55002 ld ixh,b',
            ' 55004 ld iyl,c',
            ' 55006 ld iyh,d'
        ))
        exp_instructions = (
            (55000, 'LD IXl,A'),
            (55002, 'LD IXh,B'),
            (55004, 'LD IYl,C'),
            (55006, 'LD IYh,D')
        )
        parser = self._get_parser(skool, case=CASE_UPPER)
        for address, operation in exp_instructions:
            self.assertEqual(parser.get_instruction(address).operation, operation)

    def test_registers_upper(self):
        skool = '\n'.join((
            '; Test parsing of register blocks in upper case mode',
            ';',
            '; .',
            ';',
            '; Input:a Some value',
            ';       b Some other value',
            '; Output:c The result',
            'c24605 RET',
        ))
        exp_registers = (
            ('Input', 'A', 'Some value'),
            ('', 'B', 'Some other value'),
            ('Output', 'C', 'The result')
        )
        parser = self._get_parser(skool, case=CASE_UPPER)
        registers = parser.get_entry(24605).registers
        for reg, (prefix, name, contents) in zip(registers, exp_registers):
            self.assertEqual(reg.prefix, prefix)
            self.assertEqual(reg.name, name)
            self.assertEqual(reg.contents, contents)

    def test_registers_lower(self):
        skool = '\n'.join((
            '; Test parsing of register blocks in lower case mode',
            ';',
            '; .',
            ';',
            '; Input:A Some value',
            ';       B Some other value',
            '; Output:C The result',
            'c24605 RET',
        ))
        exp_registers = (
            ('Input', 'a', 'Some value'),
            ('', 'b', 'Some other value'),
            ('Output', 'c', 'The result')
        )
        parser = self._get_parser(skool, case=CASE_LOWER)
        registers = parser.get_entry(24605).registers
        for reg, (prefix, name, contents) in zip(registers, exp_registers):
            self.assertEqual(reg.prefix, prefix)
            self.assertEqual(reg.name, name)
            self.assertEqual(reg.contents, contents)

    def test_defm_upper(self):
        skool = '\n'.join((
            't32768 DEFM "AbCdEfG"',
            ' 32775 defm "hIjKlMn"',
        ))
        parser = self._get_parser(skool, case=CASE_UPPER)
        self.assertEqual(parser.get_instruction(32768).operation, 'DEFM "AbCdEfG"')
        self.assertEqual(parser.get_instruction(32775).operation, 'DEFM "hIjKlMn"')

    def test_defm_lower(self):
        skool = '\n'.join((
            't32768 DEFM "AbCdEfG"',
            ' 32775 defm "hIjKlMn"',
        ))
        parser = self._get_parser(skool, case=CASE_LOWER)
        self.assertEqual(parser.get_instruction(32768).operation, 'defm "AbCdEfG"')
        self.assertEqual(parser.get_instruction(32775).operation, 'defm "hIjKlMn"')

    def test_semicolons_in_instructions(self):
        skool = '\n'.join((
            'c60000 CP ";"             ; 60000',
            ' 60002 LD A,";"           ; 60002',
            ' 60004 LD B,(IX+";")      ; 60004',
            ' 60007 LD (IX+";"),C      ; 60007',
            ' 60010 LD (IX+";"),";"    ; 60010',
            ' 60014 LD (IX+"\\""),";"  ; 60014',
            ' 60018 LD (IX+"\\\\"),";" ; 60018',
            ' 60022 DEFB 5,"hi;",6     ; 60022',
            ' 60027 DEFM ";0;",0       ; 60027'
        ))
        exp_instructions = (
            (60000, 'CP ";"'),
            (60002, 'LD A,";"'),
            (60004, 'LD B,(IX+";")'),
            (60007, 'LD (IX+";"),C'),
            (60010, 'LD (IX+";"),";"'),
            (60014, 'LD (IX+"\\""),";"'),
            (60018, 'LD (IX+"\\\\"),";"'),
            (60022, 'DEFB 5,"hi;",6'),
            (60027, 'DEFM ";0;",0')
        )
        parser = self._get_parser(skool)
        for address, operation in exp_instructions:
            instruction = parser.get_instruction(address)
            self.assertEqual(instruction.operation, operation)
            self.assertIsNotNone(instruction.comment)
            self.assertEqual(instruction.comment.text, str(address))

    def test_warn_unreplaced_operand(self):
        skool = '\n'.join((
            '@start',
            '; Start',
            'c30000 JR 30001'
        ))
        self._get_parser(skool, asm_mode=2, warnings=True)
        warnings = self.err.getvalue().split('\n')[:-1]
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0], 'WARNING: Unreplaced operand: 30000 JR 30001')

    def test_no_warning_for_operands_outside_disassembly_address_range(self):
        skool = '\n'.join((
            '@start',
            'c30000 JR 29999',
            ' 30002 LD HL,(30005)'
        ))
        self._get_parser(skool, asm_mode=2, warnings=True)
        warnings = self.err.getvalue().split('\n')[:-1]
        self.assertEqual([], warnings)

    def test_no_warning_for_remote_entry_address_operand_inside_disassembly_address_range(self):
        skool = '\n'.join((
            '@start',
            'c30000 JP 30001',
            '',
            'r30001 save'
        ))
        self._get_parser(skool, asm_mode=2, warnings=True)
        warnings = self.err.getvalue().split('\n')[:-1]
        self.assertEqual([], warnings)

    def test_address_strings_in_warnings(self):
        skool = '\n'.join((
            '@start',
            '@label=START',
            'c$8000 LD HL,$8003',
            ' $8003 LD DE,$8000',
            ' $8006 CALL $8001',
        ))
        self._get_parser(skool, asm_mode=2, warnings=True)
        warnings = self.err.getvalue().split('\n')[:-1]
        exp_warnings = [
            'WARNING: Found no label for operand: 8000 LD HL,$8003',
            'WARNING: LD operand replaced with routine label in unsubbed operation:',
            '  8003 LD DE,$8000 -> LD DE,START',
            'WARNING: Unreplaced operand: 8006 CALL $8001',
        ]
        self.assertEqual(exp_warnings, warnings)

    def test_suppress_warnings(self):
        skool = '\n'.join((
            '@start',
            'c30000 JR 30001 ; This would normally trigger an unreplaced operand warning'
        ))
        self._get_parser(skool, asm_mode=2, warnings=False)
        warnings = self.err.getvalue().split('\n')[:-1]
        self.assertEqual(len(warnings), 0)

    def test_label_substitution_for_address_operands(self):
        skool = (
            '@start',
            '@label=START',
            'c12445 LD BC,12445',
            ' 12448 LD DE,$309D',
            ' 12451 LD HL,12445',
            ' 12454 LD SP,$309d',
            ' 12457 LD IX,12445',
            ' 12460 LD IY,$309D',
            ' 12463 LD BC,(12445)',
            ' 12467 LD DE,($309d)',
            ' 12471 LD HL,(12445)',
            ' 12474 LD SP,($309D)',
            ' 12478 LD IX,(12445)',
            ' 12482 LD IY,($309d)',
            ' 12486 CALL 12445',
            ' 12489 CALL NZ,$309D',
            ' 12492 CALL Z,12445',
            ' 12495 CALL NC,$309d',
            ' 12498 CALL C,12445',
            ' 12501 CALL PO,$309D',
            ' 12504 CALL PE,12445',
            ' 12507 CALL P,$309d',
            ' 12510 CALL M,12445',
            ' 12513 JP $309D',
            ' 12516 JP NZ,12445',
            ' 12519 JP Z,$309d',
            ' 12522 JP NC,12445',
            ' 12525 JP C,$309D',
            ' 12528 JP PO,12445',
            ' 12531 JP PE,$309d',
            ' 12534 JP P,12445',
            ' 12537 JP M,$309D',
            ' 12540 JR 12445',
            ' 12542 JR NZ,$309d',
            ' 12544 JR Z,12445',
            ' 12546 JR NC,$309D',
            ' 12548 JR C,12445',
            ' 12550 DJNZ $309d',
            ' 12552 LD A,(12445)',
            ' 12555 LD ($309D),A',
            ' 12558 DEFW %0011000010011101'
        )
        parser = self._get_parser('\n'.join(skool), asm_mode=1, asm_labels=True)
        instructions = parser.get_entry(12445).instructions
        self.assertEqual(len(instructions[0].referrers), 1)
        index = 2
        for instruction in instructions:
            exp_operation = re.sub('(12445|\$309[Dd]|%0011000010011101)', 'START', skool[index][7:])
            self.assertEqual(instruction.operation, exp_operation)
            self.assertIsNotNone(instruction.reference)
            self.assertEqual(instruction.reference.address, 12445)
            index += 1

    def test_label_substitution_for_16_bit_ld_instruction_operands_below_256(self):
        skool = (
            '@start',
            '@label=START',
            'c00000 LD BC,0',
            ' 00003 LD DE,$0000',
            ' 00006 LD HL,0',
            ' 00009 LD SP,$0000',
            ' 00012 LD IX,0',
            ' 00016 LD IY,$0000',
            ' 00020 LD BC,(0)',
            ' 00024 LD DE,($0000)',
            ' 00028 LD HL,(0)',
            ' 00031 LD SP,($0000)',
            ' 00035 LD IX,(0)',
            ' 00039 LD IY,($0000)',
            ' 00043 LD A,(0)',
            ' 00046 LD ($0000),A'
        )
        parser = self._get_parser('\n'.join(skool), asm_mode=1, asm_labels=True)

        instructions = parser.memory_map[0].instructions
        self.assertEqual(len(instructions[0].referrers), 0)
        index = 2
        for instruction in instructions:
            exp_operation = re.sub('(0|\$0000|%0000000000000000)', 'START', skool[index][7:])
            self.assertEqual(instruction.operation, exp_operation)
            self.assertIsNotNone(instruction.reference)
            self.assertEqual(instruction.reference.address, 0)
            index += 1

    def test_label_substitution_for_complex_operand(self):
        skool = '\n'.join((
            '@start',
            '@label=START',
            '@ssub=LD HL,32768+$0A',
            'c32768 LD HL,32778'
        ))
        parser = self._get_parser(skool, asm_mode=2, asm_labels=True)

        instruction = parser.get_instruction(32768)
        self.assertEqual(instruction.operation, 'LD HL,START+$0A')

    def test_no_label_substitution_for_8_bit_numeric_operands(self):
        skool = (
            '@start',
            '@label=DATA',
            'b00124 DEFB 124,132,0,0,0,0,0,0',
            '',
            '@label=START',
            'c00132 LD A,132',
            ' 00134 LD B,132',
            ' 00136 LD C,132',
            ' 00138 LD D,132',
            ' 00140 LD E,132',
            ' 00142 LD H,132',
            ' 00144 LD L,132',
            ' 00146 LD IXh,132',
            ' 00149 LD IXl,132',
            ' 00152 LD IYh,132',
            ' 00155 LD IYl,132',
            ' 00158 LD A,(IX+124)',
            ' 00161 LD B,(IX-124)',
            ' 00164 LD C,(IX+124)',
            ' 00167 LD D,(IX-124)',
            ' 00170 LD E,(IX+124)',
            ' 00173 LD H,(IX-124)',
            ' 00176 LD L,(IX+124)',
            ' 00179 LD A,(IY-124)',
            ' 00182 LD B,(IY+124)',
            ' 00185 LD C,(IY-124)',
            ' 00188 LD D,(IY+124)',
            ' 00191 LD E,(IY-124)',
            ' 00194 LD H,(IY+124)',
            ' 00197 LD L,(IY-124)',
            ' 00200 LD (IX+124),132',
            ' 00204 LD (IY-124),132',
            ' 00208 ADD A,132',
            ' 00210 ADC A,132',
            ' 00212 SBC A,132',
            ' 00214 SUB 132',
            ' 00216 AND 255',
            ' 00218 XOR 255',
            ' 00220 OR 255',
            ' 00222 CP 255',
            ' 00224 DEFB 255',
            ' 00225 SET 0,(IX+124)',
            ' 00228 RES 1,(IY-124)',
            ' 00231 BIT 2,(IX-124)',
            ' 00234 RL (IY+124)',
            ' 00237 RLC (IX+124)',
            ' 00240 RR (IY-124)',
            ' 00243 RRC (IX-124)',
            ' 00246 SLA (IY+124)',
            ' 00249 SLL (IX+124)',
            ' 00252 SRA (IY-124)',
            '',
            '@label=CONTINUE',
            'c00255 SRL (IX-124)',
            ' 00258 IN A,(132)',
            ' 00260 OUT (132),A',
        )
        parser = self._get_parser('\n'.join(skool), asm_mode=1, asm_labels=True)

        instruction = parser.get_entry(124).instructions[0]
        self.assertEqual(len(instruction.referrers), 0)
        self.assertEqual(instruction.operation, skool[2][7:])

        instructions = parser.get_entry(132).instructions
        self.assertEqual(len(instructions[0].referrers), 0)
        index = 5
        for instruction in instructions:
            self.assertEqual(instruction.operation, skool[index][7:])
            self.assertIsNone(instruction.reference)
            index += 1

        instructions = parser.get_entry(255).instructions
        self.assertEqual(len(instructions[0].referrers), 0)
        index += 2
        for instruction in instructions:
            self.assertEqual(instruction.operation, skool[index][7:])
            self.assertIsNone(instruction.reference)
            index += 1

    def test_no_label_substitution_in_defs_statements(self):
        skool = (
            '@start',
            '@label=SPACE1',
            's00010 DEFS 9990,10',
            '',
            '@label=SPACE2',
            's10000 DEFS 10000,255',
        )
        parser = self._get_parser('\n'.join(skool), asm_mode=1, asm_labels=True)

        instruction = parser.get_instruction(10)
        self.assertEqual(len(instruction.referrers), 0)
        self.assertEqual(instruction.operation, skool[2][7:])

        instruction = parser.get_instruction(10000)
        self.assertEqual(len(instruction.referrers), 0)
        self.assertEqual(instruction.operation, skool[5][7:])

    def test_error_duplicate_label(self):
        skool = '\n'.join((
            '@start',
            '; Start',
            '@label=START',
            'c40000 RET',
            '',
            '; False start',
            '@label=START',
            'c40001 RET'
        ))
        with self.assertRaisesRegexp(SkoolParsingError, 'Duplicate label START at 40001'):
            self._get_parser(skool, asm_mode=1, asm_labels=True)

    def test_asm_mode(self):
        skool = '\n'.join((
            '@start',
            '; Routine',
            '@rsub-begin',
            '@label=FOO',
            '@rsub+else',
            '@label=BAR',
            '@rsub+end',
            'c32768 RET'
        ))
        for asm_mode, exp_label in ((0, 'FOO'), (1, 'FOO'), (2, 'FOO'), (3, 'BAR')):
            parser = self._get_parser(skool, asm_mode=asm_mode, asm_labels=True)
            self.assertEqual(parser.get_instruction(32768).asm_label, exp_label)

    def test_rsub_no_address(self):
        skool = '\n'.join((
            '@start',
            '; Routine',
            'c30000 XOR A',
            '@rsub-begin',
            ' 30001 LD L,0',
            '@rsub+else',
            '       LD HL,16384',
            '@rsub+end'
        ))
        parser = self._get_parser(skool, asm_mode=3)
        entry = parser.get_entry(30000)
        instruction = entry.instructions[1]
        self.assertEqual(instruction.operation, 'LD HL,16384')
        self.assertEqual(instruction.sub, instruction.operation)

    def test_start_and_end_directives(self):
        skool = '\n'.join((
            'c40000 LD A,B',
            '',
            '@start',
            'c40001 LD A,C',
            '@end',
            '',
            'c40002 LD A,D',
            '',
            '@start',
            'c40003 LD A,E',
            '@end',
            '',
            'c40004 LD A,H'
        ))
        parser = self._get_parser(skool, asm_mode=1)
        self.assertIsNone(parser.get_entry(40000))
        self.assertIsNotNone(parser.get_entry(40001))
        self.assertIsNone(parser.get_entry(40002))
        self.assertIsNotNone(parser.get_entry(40003))
        self.assertIsNone(parser.get_entry(40004))

    def test_isub_directive(self):
        skool = '\n'.join((
            '@start',
            '; Routine',
            '@isub=LD A,(32512)',
            'c60000 LD A,(m)',
        ))
        for asm_mode in (1, 2, 3):
            parser = self._get_parser(skool, asm_mode=asm_mode)
            self.assertEqual(parser.get_instruction(60000).operation, 'LD A,(32512)')

    def test_isub_block_directive(self):
        skool = '\n'.join((
            '@start',
            '; Routine',
            ';',
            '@isub+begin',
            '; Actual description.',
            '@isub-else',
            '; Other description.',
            '@isub-end',
            'c24576 RET',
        ))
        for asm_mode in (1, 2, 3):
            parser = self._get_parser(skool, asm_mode=asm_mode)
            self.assertEqual(['Actual description.'], parser.get_entry(24576).details)

    def test_rsub_directive(self):
        skool = '\n'.join((
            '@start',
            '; Routine',
            '@rsub=INC HL',
            'c23456 INC L',
        ))
        for asm_mode in (1, 2):
            parser = self._get_parser(skool, asm_mode=asm_mode)
            self.assertEqual(parser.get_instruction(23456).operation, 'INC L')
        parser = self._get_parser(skool, asm_mode=3)
        self.assertEqual(parser.get_instruction(23456).operation, 'INC HL')

    def test_no_asm_labels(self):
        skool = '\n'.join((
            '@label=START',
            'c49152 RET'
        ))
        parser = self._get_parser(skool, asm_labels=False)
        self.assertIsNone(parser.get_instruction(49152).asm_label)

    def test_html_mode_label(self):
        label = 'START'
        skool = '\n'.join((
            '; Routine',
            '@label={}'.format(label),
            'c49152 LD BC,0',
            ' 49155 RET'
        ))
        parser = self._get_parser(skool, html=True, asm_labels=True)
        entry = parser.get_entry(49152)
        self.assertEqual(entry.instructions[0].asm_label, label)
        self.assertIsNone(entry.instructions[1].asm_label)

    def test_html_mode_keep(self):
        skool = '\n'.join((
            '; Routine',
            'c40000 LD HL,40006',
            '@keep',
            ' 40003 LD DE,40006',
            '',
            '; Another routine',
            'c40006 RET'
        ))
        parser = self._get_parser(skool, html=True)
        entry = parser.get_entry(40000)
        self.assertFalse(entry.instructions[0].keep)
        self.assertTrue(entry.instructions[1].keep)

    def test_html_mode_rem(self):
        skool = '\n'.join((
            '; Routine',
            ';',
            '@rem=These comments',
            '@rem=should be ignored.',
            '; Foo.',
            '@rem=And these',
            '@rem=ones too.',
            'c50000 RET'
        ))
        parser = self._get_parser(skool, html=True)
        entry = parser.get_entry(50000)
        self.assertEqual(entry.details, ['Foo.'])

    def test_html_mode_ssub_directive(self):
        skool = '\n'.join((
            '; Routine',
            '@ssub=INC DE',
            'c50000 INC E',
        ))
        parser = self._get_parser(skool, html=True)
        instruction = parser.get_entry(50000).instructions[0]
        self.assertEqual(instruction.operation, 'INC E')

    def test_html_mode_ssub_block_directive(self):
        skool = '\n'.join((
            '; Routine',
            '@ssub-begin',
            'c50000 LD L,24 ; 24 is the LSB',
            '@ssub+else',
            'c50000 LD L,50003%256 ; This is the LSB',
            '@ssub+end',
            ' 50002 RET',
        ))
        parser = self._get_parser(skool, html=True)
        instruction = parser.get_entry(50000).instructions[0]
        self.assertEqual(instruction.operation, 'LD L,24')
        self.assertEqual(instruction.comment.text, '24 is the LSB')

    def test_html_mode_assemble(self):
        skool = '\n'.join((
            'c30000 LD A,1',
            '@assemble=1',
            ' 30002 LD A,2',
            '@assemble=0',
            ' 30004 LD A,3'
        ))
        snapshot = self._get_parser(skool, html=True).snapshot
        self.assertEqual([0, 0, 62, 2, 0, 0], snapshot[30000:30006])

    def test_html_mode_assemble_bad_values(self):
        skool = '\n'.join((
            '@assemble=1',
            'c40000 LD A,4',
            '@assemble=off',
            ' 40002 LD A,5',
            '@assemble=0',
            ' 40004 LD A,6',
            '@assemble=on',
            ' 40006 LD A,7'
        ))
        snapshot = self._get_parser(skool, html=True).snapshot
        self.assertEqual([62, 4, 62, 5, 0, 0, 0, 0], snapshot[40000:40008])

    def test_asm_mode_rem(self):
        skool = '\n'.join((
            '@start',
            '; Routine',
            ';',
            '@rem=These comments',
            '@rem=should be ignored.',
            '; Foo.',
            '@rem=And these',
            '@rem=ones too.',
            'c50000 RET'
        ))
        parser = self._get_parser(skool, asm_mode=1)
        entry = parser.get_entry(50000)
        self.assertEqual(entry.details, ['Foo.'])

    def test_asm_mode_ssub_directive(self):
        skool = '\n'.join((
            '@start',
            '; Routine',
            '@ssub=INC DE',
            'c50000 INC E',
        ))
        for asm_mode, exp_op in ((1, 'INC E'), (2, 'INC DE'), (3, 'INC DE')):
            parser = self._get_parser(skool, asm_mode=asm_mode)
            instruction = parser.get_entry(50000).instructions[0]
            self.assertEqual(instruction.operation, exp_op)

    def test_asm_mode_ssub_block_directive(self):
        skool = '\n'.join((
            '@start',
            '; Routine',
            '@ssub-begin',
            'c50000 LD L,24 ; 24 is the LSB',
            '@ssub+else',
            'c50000 LD L,50003%256 ; This is the LSB',
            '@ssub+end',
            ' 50002 RET',
        ))
        for asm_mode, exp_operation, exp_comment in (
                (1, 'LD L,24', '24 is the LSB'),
                (2, 'LD L,50003%256', 'This is the LSB'),
                (3, 'LD L,50003%256', 'This is the LSB')
        ):
            parser = self._get_parser(skool, asm_mode=asm_mode)
            instruction = parser.get_entry(50000).instructions[0]
            self.assertEqual(instruction.operation, exp_operation)
            self.assertEqual(instruction.comment.text, exp_comment)

    def test_fix_mode_0(self):
        skool = '\n'.join((
            '@start',
            "; Let's test some @ofix directives",
            'c24593 NOP',
            '@ofix=LD A,C',
            ' 24594 LD A,B',
            '@ofix-begin',
            ' 24595 LD B,A',
            '@ofix+else',
            ' 24595 LD B,C',
            '@ofix+end',
            '',
            "; Let's test some @bfix directives",
            'c24596 NOP',
            '@bfix=LD C,B',
            ' 24597 LD C,A',
            '@bfix-begin',
            ' 24598 LD D,A',
            '@bfix+else',
            ' 24598 LD D,B',
            '@bfix+end',
            '',
            "; Let's test the @rfix block directive",
            'c24599 NOP',
            '@rfix-begin',
            ' 24600 LD E,A',
            '@rfix+else',
            ' 24600 LD E,B',
            '@rfix+end',
        ))
        parser = self._get_parser(skool, asm_mode=1, fix_mode=0)
        instructions = parser.get_entry(24593).instructions
        self.assertEqual(instructions[1].operation, 'LD A,B')
        self.assertEqual(instructions[2].operation, 'LD B,A')
        instructions = parser.get_entry(24596).instructions
        self.assertEqual(instructions[1].operation, 'LD C,A')
        self.assertEqual(instructions[2].operation, 'LD D,A')
        instructions = parser.get_entry(24599).instructions
        self.assertEqual(instructions[1].operation, 'LD E,A')

    def test_fix_mode_1(self):
        skool = '\n'.join((
            '@start',
            "; Let's test some @ofix directives",
            'c24593 NOP',
            '@ofix=LD A,C',
            ' 24594 LD A,B',
            '@ofix-begin',
            ' 24595 LD B,A',
            '@ofix+else',
            ' 24595 LD B,C',
            '@ofix+end',
            '',
            "; Let's test some @bfix directives",
            'c24596 NOP',
            '@bfix=LD C,B',
            ' 24597 LD C,A',
            '@bfix-begin',
            ' 24598 LD D,A',
            '@bfix+else',
            ' 24598 LD D,B',
            '@bfix+end',
            '',
            "; Let's test the @rfix block directive",
            'c24599 NOP',
            '@rfix-begin',
            ' 24600 LD E,A',
            '@rfix+else',
            ' 24600 LD E,B',
            '@rfix+end',
        ))
        parser = self._get_parser(skool, asm_mode=1, fix_mode=1)
        instructions = parser.get_entry(24593).instructions
        self.assertEqual(instructions[1].operation, 'LD A,C')
        self.assertEqual(instructions[2].operation, 'LD B,C')
        instructions = parser.get_entry(24596).instructions
        self.assertEqual(instructions[1].operation, 'LD C,A')
        self.assertEqual(instructions[2].operation, 'LD D,A')
        instructions = parser.get_entry(24599).instructions
        self.assertEqual(instructions[1].operation, 'LD E,A')

    def test_fix_mode_2(self):
        skool = '\n'.join((
            '@start',
            "; Let's test some @ofix directives",
            'c24593 NOP',
            '@ofix=LD A,C',
            ' 24594 LD A,B',
            '@ofix-begin',
            ' 24595 LD B,A',
            '@ofix+else',
            ' 24595 LD B,C',
            '@ofix+end',
            '',
            "; Let's test some @bfix directives",
            'c24596 NOP',
            '@bfix=LD C,B',
            ' 24597 LD C,A',
            '@bfix-begin',
            ' 24598 LD D,A',
            '@bfix+else',
            ' 24598 LD D,B',
            '@bfix+end',
            '',
            "; Let's test the @rfix block directive",
            'c24599 NOP',
            '@rfix-begin',
            ' 24600 LD E,A',
            '@rfix+else',
            ' 24600 LD E,B',
            '@rfix+end',
        ))
        parser = self._get_parser(skool, asm_mode=1, fix_mode=2)
        instructions = parser.get_entry(24593).instructions
        self.assertEqual(instructions[1].operation, 'LD A,C')
        self.assertEqual(instructions[2].operation, 'LD B,C')
        instructions = parser.get_entry(24596).instructions
        self.assertEqual(instructions[1].operation, 'LD C,B')
        self.assertEqual(instructions[2].operation, 'LD D,B')
        instructions = parser.get_entry(24599).instructions
        self.assertEqual(instructions[1].operation, 'LD E,A')

    def test_fix_mode_3(self):
        skool = '\n'.join((
            '@start',
            "; Let's test some @ofix directives",
            'c24593 NOP',
            '@ofix=LD A,C',
            ' 24594 LD A,B',
            '@ofix-begin',
            ' 24595 LD B,A',
            '@ofix+else',
            ' 24595 LD B,C',
            '@ofix+end',
            '',
            "; Let's test some @bfix directives",
            'c24596 NOP',
            '@bfix=LD C,B',
            ' 24597 LD C,A',
            '@bfix-begin',
            ' 24598 LD D,A',
            '@bfix+else',
            ' 24598 LD D,B',
            '@bfix+end',
            '',
            "; Let's test the @rfix block directive",
            'c24599 NOP',
            '@rfix-begin',
            ' 24600 LD E,A',
            '@rfix+else',
            ' 24600 LD E,B',
            '@rfix+end',
        ))
        parser = self._get_parser(skool, asm_mode=3, fix_mode=3)
        instructions = parser.get_entry(24593).instructions
        self.assertEqual(instructions[1].operation, 'LD A,C')
        self.assertEqual(instructions[2].operation, 'LD B,C')
        instructions = parser.get_entry(24596).instructions
        self.assertEqual(instructions[1].operation, 'LD C,B')
        self.assertEqual(instructions[2].operation, 'LD D,B')
        instructions = parser.get_entry(24599).instructions
        self.assertEqual(instructions[1].operation, 'LD E,B')

    def test_rsub_minus_inside_rsub_minus(self):
        # @rsub-begin inside @rsub- block
        skool = '\n'.join((
            '@start',
            '@rsub-begin',
            '@rsub-begin',
            '@rsub-end',
            '@rsub-end',
        ))
        error = "rsub-begin inside rsub- block"
        self.assert_error(skool, error, asm_mode=1)

    def test_isub_plus_inside_bfix_plus(self):
        # @isub+else inside @bfix+ block
        skool = '\n'.join((
            '@start',
            '@bfix+begin',
            '@isub+else',
            '@isub+end',
            '@bfix+end',
        ))
        error = "isub+else inside bfix+ block"
        self.assert_error(skool, error, asm_mode=1)

    def test_dangling_ofix_else(self):
        # Dangling @ofix+else directive
        skool = '\n'.join((
            '@start',
            '@ofix+else',
            '@ofix+end',
        ))
        error = "ofix+else not inside block"
        self.assert_error(skool, error, asm_mode=1)

    def test_dangling_rfix_end(self):
        # Dangling @rfix+end directive
        skool = '@start\n@rfix+end'
        error = "rfix+end has no matching start directive"
        self.assert_error(skool, error, asm_mode=1)

    def test_wrong_end_infix(self):
        # Mismatched begin/else/end (wrong infix)
        skool = '\n'.join((
            '@start',
            '@rsub+begin',
            '@rsub-else',
            '@rsub+end',
        ))
        error = "rsub+end cannot end rsub- block"
        self.assert_error(skool, error, asm_mode=1)

    def test_mismatched_begin_end(self):
        # Mismatched begin/end (different directive)
        skool = '\n'.join((
            '@start',
            '@ofix-begin',
            '@bfix-end',
        ))
        error = "bfix-end cannot end ofix- block"
        self.assert_error(skool, error, asm_mode=1)

    def test_min_address(self):
        skool = '\n'.join((
            'b30000 DEFB 0',
            '',
            'b30001 DEFB 1',
            '',
            'b30002 DEFB 2',
        ))
        parser = self._get_parser(skool, min_address=30001)
        self.assertEqual([30001, 30002], [e.address for e in parser.memory_map])
        self.assertIsNone(parser.get_entry(30000))
        self.assertIsNotNone(parser.get_entry(30001))
        self.assertIsNotNone(parser.get_entry(30002))
        self.assertEqual(parser.base_address, 30001)
        self.assertIsNone(parser.get_instruction(30000))
        self.assertIsNotNone(parser.get_instruction(30001))
        self.assertIsNotNone(parser.get_instruction(30002))

    def test_min_address_between_entries(self):
        skool = '\n'.join((
            'b40000 DEFB 0',
            ' 40001 DEFB 1',
            ' 40002 DEFB 2',
            '',
            'b40003 DEFB 3',
        ))
        parser = self._get_parser(skool, min_address=40001)
        self.assertEqual([40003], [e.address for e in parser.memory_map])
        self.assertIsNone(parser.get_entry(40000))
        self.assertIsNotNone(parser.get_entry(40003))
        self.assertEqual(parser.base_address, 40003)
        self.assertIsNone(parser.get_instruction(40000))
        self.assertIsNone(parser.get_instruction(40001))
        self.assertIsNone(parser.get_instruction(40002))
        self.assertIsNotNone(parser.get_instruction(40003))

    def test_min_address_with_addressless_instruction(self):
        skool = '\n'.join((
            '@start',
            'c32768 LD A,B',
            '@rsub+begin',
            '       INC A   ; This instruction should be retained',
            '@rsub+end',
            ' 32770 RET',
        ))
        parser = self._get_parser(skool, asm_mode=3, min_address=32768)
        instructions = parser.get_entry(32768).instructions
        self.assertEqual(len(instructions), 3)
        self.assertEqual(instructions[1].operation, 'INC A')
        self.assertEqual(instructions[1].comment.text, 'This instruction should be retained')

    def test_max_address(self):
        skool = '\n'.join((
            'b30000 DEFB 0',
            '',
            'b30001 DEFB 1',
            '',
            'b30002 DEFB 2',
        ))
        parser = self._get_parser(skool, max_address=30002)
        self.assertEqual([30000, 30001], [e.address for e in parser.memory_map])
        self.assertIsNotNone(parser.get_entry(30000))
        self.assertIsNotNone(parser.get_entry(30001))
        self.assertIsNone(parser.get_entry(30002))
        self.assertEqual(parser.base_address, 30000)
        self.assertIsNotNone(parser.get_instruction(30000))
        self.assertIsNotNone(parser.get_instruction(30001))
        self.assertIsNone(parser.get_instruction(30002))

    def test_max_address_between_entries(self):
        skool = '\n'.join((
            'b40000 DEFB 0',
            '',
            'b40001 DEFB 1',
            ' 40002 DEFB 2',
            ' 40003 DEFB 3',
            '',
            'b40004 DEFB 4',
        ))
        parser = self._get_parser(skool, max_address=40003)
        self.assertEqual([40000, 40001], [e.address for e in parser.memory_map])
        self.assertIsNotNone(parser.get_entry(40000))
        self.assertIsNotNone(parser.get_entry(40001))
        self.assertIsNone(parser.get_entry(40004))
        self.assertEqual(parser.get_entry(40001).instructions[-1].address, 40002)
        self.assertEqual(parser.base_address, 40000)
        self.assertIsNotNone(parser.get_instruction(40000))
        self.assertIsNotNone(parser.get_instruction(40001))
        self.assertIsNotNone(parser.get_instruction(40002))
        self.assertIsNone(parser.get_instruction(40003))
        self.assertIsNone(parser.get_instruction(40004))

    def test_max_address_with_addressless_instruction(self):
        skool = '\n'.join((
            '@start',
            'c32768 LD A,B',
            '@rsub+begin',
            '       INC A   ; This instruction should be retained',
            '@rsub+end',
            ' 32770 RET',
        ))
        parser = self._get_parser(skool, asm_mode=3, max_address=32771)
        instructions = parser.get_entry(32768).instructions
        self.assertEqual(len(instructions), 3)
        self.assertEqual(instructions[1].operation, 'INC A')
        self.assertEqual(instructions[1].comment.text, 'This instruction should be retained')

    def test_min_and_max_address(self):
        skool = '\n'.join((
            'b40000 DEFB 0',
            '',
            'b40001 DEFB 1',
            '',
            'b40002 DEFB 2',
            '',
            'b40003 DEFB 3',
        ))
        parser = self._get_parser(skool, min_address=40001, max_address=40003)
        self.assertEqual([40001, 40002], [e.address for e in parser.memory_map])
        self.assertIsNone(parser.get_entry(40000))
        self.assertIsNotNone(parser.get_entry(40001))
        self.assertIsNotNone(parser.get_entry(40002))
        self.assertIsNone(parser.get_entry(40003))
        self.assertEqual(parser.base_address, 40001)
        self.assertIsNone(parser.get_instruction(40000))
        self.assertIsNotNone(parser.get_instruction(40001))
        self.assertIsNotNone(parser.get_instruction(40002))
        self.assertIsNone(parser.get_instruction(40003))

    def test_min_and_max_address_gives_no_content(self):
        skool = '\n'.join((
            'b40000 DEFB 0',
            ' 40001 DEFB 1',
            '',
            'b40002 DEFB 2',
        ))
        parser = self._get_parser(skool, min_address=40001, max_address=40002)
        self.assertEqual(len(parser.memory_map), 0)
        self.assertIsNone(parser.get_entry(40000))
        self.assertIsNone(parser.get_entry(40002))
        self.assertIsNone(parser.get_instruction(40000))
        self.assertIsNone(parser.get_instruction(40001))
        self.assertIsNone(parser.get_instruction(40002))

    def test_duplicate_instruction_addresses(self):
        skool = '\n'.join((
            'c32768 LD A,10',
            ' 32770 LD B,11  ; Comment 1',
            '; First the instruction at 32772 looks like this.',
            ' 32772 LD HL,0  ; Comment 2',
            '; Then it looks like this.',
            ' 32772 LD BC,0  ; Comment 3',
            '; And then 32770 onwards looks like this.',
            ' 32770 LD C,12  ; Comment 4',
            ' 32772 RET',
        ))
        instructions = self._get_parser(skool).get_entry(32768).instructions

        self.assertEqual(instructions[1].address, 32770)
        self.assertEqual(instructions[1].operation, 'LD B,11')
        self.assertIsNone(instructions[1].mid_block_comment)
        self.assertEqual(instructions[1].comment.text, 'Comment 1')

        self.assertEqual(instructions[2].address, 32772)
        self.assertEqual(instructions[2].operation, 'LD HL,0')
        self.assertEqual(['First the instruction at 32772 looks like this.'], instructions[2].mid_block_comment)
        self.assertEqual(instructions[2].comment.text, 'Comment 2')

        self.assertEqual(instructions[3].address, 32772)
        self.assertEqual(instructions[3].operation, 'LD BC,0')
        self.assertEqual(['Then it looks like this.'], instructions[3].mid_block_comment)
        self.assertEqual(instructions[3].comment.text, 'Comment 3')

        self.assertEqual(instructions[4].address, 32770)
        self.assertEqual(instructions[4].operation, 'LD C,12')
        self.assertEqual(['And then 32770 onwards looks like this.'], instructions[4].mid_block_comment)
        self.assertEqual(instructions[4].comment.text, 'Comment 4')

        self.assertEqual(instructions[5].address, 32772)
        self.assertEqual(instructions[5].operation, 'RET')
        self.assertIsNone(instructions[5].mid_block_comment)
        self.assertEqual(instructions[5].comment.text, '')

class TableParserTest(SkoolKitTestCase):
    def assert_error(self, text, error):
        with self.assertRaises(SkoolParsingError) as cm:
            TableParser().parse_text(text, 0)
        self.assertEqual(cm.exception.args[0], error)

    def test_invalid_colspan_indicator(self):
        self.assert_error('#TABLE { =cX Hi } TABLE#', "Invalid colspan indicator: 'cX'")

    def test_invalid_rowspan_indicator(self):
        self.assert_error('#TABLE { =rY Hi } TABLE#', "Invalid rowspan indicator: 'rY'")

if __name__ == '__main__':
    unittest.main()
