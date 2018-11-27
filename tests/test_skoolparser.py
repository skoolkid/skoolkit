import textwrap
import re

from skoolkittest import SkoolKitTestCase
from skoolkit import SkoolParsingError, BASE_10, BASE_16
from skoolkit.skoolparser import SkoolParser, TableParser, set_bytes, CASE_LOWER, CASE_UPPER

TEST_BASE_CONVERSION_SKOOL = r"""
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
 31186 LD A,30000%256
 31188 LD B,40000/$100
 31190 LD BC,50000+$0A
 31193 LD DE,60000-256
 31196 LD HL,33333+%1010
 31199 LD A,12*26
 31201 LD B,$35/7
 31203 LD C,14+%101
 31205 LD D,$0A-3
 31207 LD E,25%9
 31209 LD A,(34576+$01)
 31212 LD BC,($B277-11)
 31216 LD DE,+(45678+$FF)%256
 31219 DEFB 45678%256,"\""/$11,"5"%16,"6"%$11,10%%10
 31221 DEFM $0A+"2","2"+10,"12/4"
 31227 DEFS 10*$07+3,$21-13
 31300 DEFW 128*$400
 31302 LD A,"1"%16
""".strip()

TEST_BASE_CONVERSION_DECIMAL = r"""
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
31186 LD A,30000%256
31188 LD B,40000/256
31190 LD BC,50000+10
31193 LD DE,60000-256
31196 LD HL,33333+%1010
31199 LD A,12*26
31201 LD B,53/7
31203 LD C,14+%101
31205 LD D,10-3
31207 LD E,25%9
31209 LD A,(34576+1)
31212 LD BC,(45687-11)
31216 LD DE,+(45678+255)%256
31219 DEFB 45678%256,"\""/17,"5"%16,"6"%17,10%%10
31221 DEFM 10+"2","2"+10,"12/4"
31227 DEFS 10*7+3,33-13
31300 DEFW 128*1024
31302 LD A,"1"%16
""".strip().split('\n')

TEST_BASE_CONVERSION_HEX = r"""
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
31186 LD A,$7530%$100
31188 LD B,$9C40/$100
31190 LD BC,$C350+$0A
31193 LD DE,$EA60-$0100
31196 LD HL,$8235+%1010
31199 LD A,$0C*$1A
31201 LD B,$35/$07
31203 LD C,$0E+%101
31205 LD D,$0A-$03
31207 LD E,$19%$09
31209 LD A,($8710+$01)
31212 LD BC,($B277-$000B)
31216 LD DE,+($B26E+$FF)%$0100
31219 DEFB $B26E%$100,"\""/$11,"5"%$10,"6"%$11,$0A%%10
31221 DEFM $0A+"2","2"+$0A,"12/4"
31227 DEFS $0A*$07+$03,$21-$0D
31300 DEFW $0080*$400
31302 LD A,"1"%$10
""".strip().split('\n')

class SkoolParserTest(SkoolKitTestCase):
    def _get_parser(self, contents, *args, **kwargs):
        skoolfile = self.write_text_file(textwrap.dedent(contents), suffix='.skool')
        return SkoolParser(skoolfile, *args, **kwargs)

    def _test_sub_directives(self, skool, exp_instructions, exp_subs, **kwargs):
        for index, asm_dir in ((1, 'isub'), (2, 'ssub'), (3, 'rsub')):
            for asm_mode in (0, 1, 2, 3):
                expected = exp_subs if asm_mode >= index else exp_instructions
                with self.subTest(asm_dir=asm_dir, asm_mode=asm_mode):
                    instructions = self._get_parser(skool.format(asm_dir), asm_mode=asm_mode, **kwargs).memory_map[0].instructions
                    if len(expected[0]) == 4:
                        actual = [(i.asm_label, i.addr_str, i.operation, i.comment.text if i.comment else None) for i in instructions]
                    else:
                        actual = [(i.addr_str, i.operation, i.comment.text if i.comment else None) for i in instructions]
                    self.assertEqual(expected, actual)

    def _test_fix_directives(self, skool, exp_instructions, exp_subs, **kwargs):
        for index, asm_dir in ((1, 'ofix'), (2, 'bfix'), (3, 'rfix')):
            for fix_mode in (0, 1, 2, 3):
                expected = exp_subs if fix_mode >= index else exp_instructions
                with self.subTest(asm_dir=asm_dir, fix_mode=fix_mode):
                    instructions = self._get_parser(skool.format(asm_dir), asm_mode=1, fix_mode=fix_mode, **kwargs).memory_map[0].instructions
                    if len(expected[0]) == 4:
                        actual = [(i.asm_label, i.addr_str, i.operation, i.comment.text if i.comment else None) for i in instructions]
                    else:
                        actual = [(i.addr_str, i.operation, i.comment.text if i.comment else None) for i in instructions]
                    self.assertEqual(expected, actual)

    def _test_sub_and_fix_directives(self, skool, exp_instructions, exp_subs, **kwargs):
        self._test_sub_directives(skool, exp_instructions, exp_subs, **kwargs)
        self._test_fix_directives(skool, exp_instructions, exp_subs, **kwargs)

    def _assert_sub_and_fix_directives(self, skool, assert_f=None, exp_error=None, **kwargs):
        for sub_mode, fix_mode, asm_dir in (
                (1, 0, 'isub'),
                (2, 0, 'ssub'),
                (3, 1, 'rsub'),
                (1, 1, 'ofix'),
                (1, 2, 'bfix'),
                (3, 3, 'rfix')
        ):
            with self.subTest(sub_mode=sub_mode, fix_mode=fix_mode, asm_dir=asm_dir, **kwargs):
                if assert_f:
                    assert_f(self._get_parser(skool.format(asm_dir), asm_mode=sub_mode, fix_mode=fix_mode, **kwargs))
                else:
                    self.assert_error(skool.format(asm_dir), exp_error, asm_mode=sub_mode, fix_mode=fix_mode, **kwargs)

    def assert_error(self, skool, error, *args, **kwargs):
        with self.assertRaisesRegex(SkoolParsingError, error):
            self._get_parser(skool, *args, **kwargs)

    def test_invalid_entry_address(self):
        self.assert_error('c3000f RET', "Invalid address: '3000f'")

    def test_entry_sizes(self):
        skool = """
            c65500 LD A,1
             65502 RET

            c65503 JP 65500
        """
        entries = self._get_parser(skool, html=True).memory_map
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].size, 3)
        self.assertEqual(entries[1].size, 3)

    def test_entry_sizes_with_instructionless_entry(self):
        skool = """
            c65500 RET

            i65501

            c65510 JP 65500
        """
        entries = self._get_parser(skool, html=True).memory_map
        self.assertEqual(len(entries), 3)
        self.assertEqual(entries[0].size, 1)
        self.assertEqual(entries[1].size, 1)
        self.assertEqual(entries[2].size, 3)

    def test_entry_sizes_with_gaps_between_entries(self):
        skool = """
            c65500 LD A,B
             65501 RET

            t65510 DEFM "Hi"
             65512 DEFM "Lo"

            b65520 DEFB 1,2,3
             65523 DEFB 4,5,6
        """
        entries = self._get_parser(skool, html=True).memory_map
        self.assertEqual(len(entries), 3)
        self.assertEqual(entries[0].size, 2)
        self.assertEqual(entries[1].size, 4)
        self.assertEqual(entries[2].size, 6)

    def test_entry_sizes_with_entries_out_of_order(self):
        skool = """
            c65501 JP 65500

            c65500 RET
        """
        entries = self._get_parser(skool, html=True).memory_map
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].size, 3)
        self.assertEqual(entries[1].size, 1)

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

    def test_entry_title(self):
        title = 'This is an entry title'
        skool = """
            ; {}
            c30000 RET
        """.format(title)
        parser = self._get_parser(skool, html=False)
        self.assertEqual(parser.get_entry(30000).description, title)

    def test_entry_description(self):
        description = 'This is an entry description'
        skool = """
            ; Routine at 30000
            ;
            ; {}
            c30000 RET
        """.format(description)
        parser = self._get_parser(skool, html=False)
        self.assertEqual([description], parser.get_entry(30000).details)

    def test_multi_paragraph_entry_description(self):
        description = ['Paragraph 1', 'Paragraph 2']
        skool = """
            ; Test a multi-paragraph description
            ;
            ; {}
            ; .
            ; {}
            c40000 RET
        """.format(*description)
        parser = self._get_parser(skool, html=False)
        self.assertEqual(description, parser.get_entry(40000).details)

    def test_empty_entry_description(self):
        skool = """
            ; Test an empty description
            ;
            ; .
            ;
            ; A 0
            c25600 RET
        """
        parser = self._get_parser(skool, html=False)
        entry = parser.get_entry(25600)
        self.assertEqual(entry.details, [])
        registers = entry.registers
        self.assertEqual(len(registers), 1)
        reg_a = registers[0]
        self.assertEqual(reg_a.name, 'A')

    def test_registers(self):
        skool = """
            ; Test register parsing (1)
            ;
            ; Traditional.
            ;
            ; A Some value
            ; B Some other value
            ; C
            c24589 RET

            ; Test register parsing (2)
            ;
            ; With prefixes.
            ;
            ; Input:A Some value
            ;       B Some other value
            ; Output:HL The result
            c24590 RET
        """
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
        skool = """
            ; Byte
            ;
            ; .
            ;
            ; A Some value
            b54321 DEFB 0

            ; GSB entry
            ;
            ; .
            ;
            ; B Some value
            g54322 DEFB 0

            ; Space
            ;
            ; .
            ;
            ; C Some value
            s54323 DEFS 10

            ; Message
            ;
            ; .
            ;
            ; D Some value
            t54333 DEFM "Hi"

            ; Unused code
            ;
            ; .
            ;
            ; E Some value
            u54335 LD HL,12345

            ; Words
            ;
            ; .
            ;
            ; H Some value
            w54338 DEFW 1,2
        """
        parser = self._get_parser(skool, html=False)

        for address, reg_name in ((54321, 'A'), (54322, 'B'), (54323, 'C'), (54333, 'D'), (54335, 'E'), (54338, 'H')):
            registers = parser.get_entry(address).registers
            self.assertEqual(len(registers), 1)
            reg = registers[0]
            self.assertEqual(reg.name, reg_name)
            self.assertEqual(reg.contents, 'Some value')

    def test_register_description_continuation_lines(self):
        skool = """
            ; Routine
            ;
            ; .
            ;
            ; BC This register description is long enough that it needs to be
            ;   .split over two lines
            ; DE Short register description
            ; HL Another register description that is long enough to need
            ; .  splitting over two lines
            c40000 RET
        """
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
        skool = """
            ; Title
            ;
            ; Description
            ;
            ; .
            ;
            ; Start comment.
            c49152 RET
        """
        parser = self._get_parser(skool, html=False)
        self.assertEqual([], parser.get_entry(49152).registers)

    def test_registers_html_escape(self):
        skool = """
            ; Title
            ;
            ; Description
            ;
            ; A Some value > 4
            ; B Some value < 8
            c49152 RET
        """
        parser = self._get_parser(skool, html=True)

        registers = parser.get_entry(49152).registers
        self.assertEqual(len(registers), 2)
        self.assertEqual(registers[0].contents, 'Some value &gt; 4')
        self.assertEqual(registers[1].contents, 'Some value &lt; 8')

    def test_registers_html_no_escape(self):
        skool = """
            ; Title
            ;
            ; Description
            ;
            ; A Some value > 8
            ; B Some value < 10
            c32768 RET
        """
        parser = self._get_parser(skool, html=False)

        registers = parser.get_entry(32768).registers
        self.assertEqual(len(registers), 2)
        self.assertEqual(registers[0].contents, 'Some value > 8')
        self.assertEqual(registers[1].contents, 'Some value < 10')

    def test_start_comment(self):
        exp_start_comment = 'This is a start comment.'
        skool = """
            ; Test a start comment
            ;
            ; .
            ;
            ; .
            ;
            ; {}
            c50000 RET
        """.format(exp_start_comment)
        parser = self._get_parser(skool, html=False)
        start_comment = parser.get_instruction(50000).mid_block_comment
        self.assertEqual([exp_start_comment], start_comment)

    def test_multi_paragraph_start_comment(self):
        exp_start_comment = ['First paragraph.', 'Second paragraph.']
        skool = """
            ; Test a multi-paragraph start comment
            ;
            ; .
            ;
            ; .
            ;
            ; {}
            ; .
            ; {}
            c50000 RET
        """.format(*exp_start_comment)
        parser = self._get_parser(skool, html=False)
        start_comment = parser.get_instruction(50000).mid_block_comment
        self.assertEqual(exp_start_comment, start_comment)

    def test_unpadded_comments(self):
        skool = """
            ;Routine
            ;
            ;Paragraph 1.
            ;.
            ;Paragraph 2.
            ;
            ;A Value
            ;
            ;Start comment.
            c32768 XOR A
            ;Mid-block comment.
             32769 RET   ;Done.
        """
        parser = self._get_parser(skool, html=False)
        entry = parser.get_entry(32768)
        self.assertEqual(entry.description, 'Routine')
        self.assertEqual(['Paragraph 1.', 'Paragraph 2.'], entry.details)
        self.assertEqual(entry.registers[0].name, 'A')
        self.assertEqual(entry.registers[0].contents, 'Value')
        self.assertEqual(['Start comment.'], entry.instructions[0].mid_block_comment)
        self.assertEqual(['Mid-block comment.'], entry.instructions[1].mid_block_comment)
        self.assertEqual('Done.', entry.instructions[1].comment.text)

    def test_snapshot(self):
        skool = """
            ; Test snapshot building
            b24591 DEFB 1
             24592 DEFW 300
             24594 DEFM "abc"
             24597 DEFS 3,7
             24600 DEFB $A0
             24601 DEFW $812C
             24603 DEFM "ab",$11
             24606 DEFS $03,%10101010
             24609 DEFB %00001111,"c"
             24611 DEFW %1010101000001111
             24613 DEFM %11110000,"bc"
             24616 DEFS 2
        """
        parser = self._get_parser(skool, html=True)
        self.assertEqual(parser.snapshot[24591:24600], [1, 44, 1, 97, 98, 99, 7, 7, 7])
        self.assertEqual(parser.snapshot[24600:24609], [160, 44, 129, 97, 98, 17, 170, 170, 170])
        self.assertEqual(parser.snapshot[24609:24618], [15, 99, 15, 170, 240, 98, 99, 0, 0])

    def test_nested_braces(self):
        skool = """
            ; Test nested braces in a multi-line comment
            b32768 DEFB 0 ; {These bytes are {REALLY} {{IMPORTANT}}!
             32769 DEFB 0 ; }
        """
        parser = self._get_parser(skool)
        comment = parser.get_instruction(32768).comment.text
        self.assertEqual(comment, 'These bytes are {REALLY} {{IMPORTANT}}!')

    def test_braces_in_comments(self):
        skool = """
            ; Test comments that start or end with a brace
            b30000 DEFB 0 ; {{Unmatched closing
             30001 DEFB 0 ; brace} }
             30002 DEFB 0 ; { {Matched
             30003 DEFB 0 ; braces} }
             30004 DEFB 0 ; { {Unmatched opening
             30005 DEFB 0 ; brace }}
             30006 DEFB 0 ; {{{Unmatched closing braces}} }
             30007 DEFB 0 ; { {{Matched braces (2)}} }
             30008 DEFB 0 ; { {{Unmatched opening braces}}}
             30009 DEFB 0 ; {Opening brace {
             30010 DEFB 0 ; at the end of a line}}
             30011 DEFB 0 ; {{Closing brace
             30012 DEFB 0 ; } at the beginning of a line}
        """
        parser = self._get_parser(skool)
        exp_comments = (
            (30000, 'Unmatched closing brace}'),
            (30002, '{Matched braces}'),
            (30004, '{Unmatched opening brace'),
            (30006, 'Unmatched closing braces}}'),
            (30007, '{{Matched braces (2)}}'),
            (30008, '{{Unmatched opening braces'),
            (30009, 'Opening brace { at the end of a line'),
            (30011, 'Closing brace } at the beginning of a line')
        )
        for address, exp_text in exp_comments:
            text = parser.get_instruction(address).comment.text
            self.assertEqual(text, exp_text)

    def test_unmatched_opening_braces_in_instruction_comments(self):
        skool = """
            b50000 DEFB 0 ; {The unmatched {opening brace} in this comment should be
             50001 DEFB 0 ; implicitly closed by the end of this entry

            b50002 DEFB 0 ; {The unmatched {opening brace} in this comment should be
             50003 DEFB 0 ; implicitly closed by the following mid-block comment
            ; Here is the mid-block comment.
             50004 DEFB 0 ; The closing brace in this comment is unmatched}
        """
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
        skool = """
            ; First routine
            c45192 RET
            ; The end of the first routine.
            ; .
            ; Really.

            ; Second routine
            c45193 RET
            ; The end of the second routine.
        """
        parser = self._get_parser(skool)
        memory_map = parser.memory_map
        self.assertEqual(len(memory_map), 2)
        self.assertEqual(memory_map[0].end_comment, ['The end of the first routine.', 'Really.'])
        self.assertEqual(memory_map[1].end_comment, ['The end of the second routine.'])

    def test_defb_directives(self):
        skool = """
            @defb=23296:1,$0A,%10101010,"01",32768/256
            @defb=30000:48,72,136,144,104,4,10,4 ; Key
            ; Start
            32768 JP 49152
        """
        snapshot = self._get_parser(skool, html=True).snapshot
        self.assertEqual([1, 10, 170, 48, 49, 128], snapshot[23296:23302])
        self.assertEqual([48, 72, 136, 144, 104, 4, 10, 4], snapshot[30000:30008])

    def test_defs_directives(self):
        skool = """
            @defs=23296:6,$10
            @defs=30000:4,"1" ; "1111"
            ; Start
            32768 JP 49152
        """
        snapshot = self._get_parser(skool, html=True).snapshot
        self.assertEqual([16] * 6, snapshot[23296:23302])
        self.assertEqual([49] * 4, snapshot[30000:30004])

    def test_defw_directives(self):
        skool = """
            @defw=23296:32769,$8002,%100000000,"0"
            @defw=30000:32768 ; Start address
            ; Start
            32768 JP 49152
        """
        snapshot = self._get_parser(skool, html=True).snapshot
        self.assertEqual([1, 128, 2, 128, 0, 1, 48, 0], snapshot[23296:23304])
        self.assertEqual([0, 128], snapshot[30000:30002])

    def test_if_directive_asm(self):
        skool = """
            @start
            @if({asm}==0)(replace=/#zero/0)
            @if({asm}==1)(replace=/#one/1)
            @if({asm}==1)(replace=/#two/2,replace=/#two/TWO)
            @if({asm}==2)(replace=/#three/3,replace=/#three/THREE)
            ; Routine at 40000
            ;
            ; #zero-#one-#two-#three
            c40000 RET
        """
        entry = self._get_parser(skool, asm_mode=1).get_entry(40000)
        self.assertEqual(['#zero-1-2-THREE'], entry.details)

    def test_if_directive_asm_plus_4(self):
        skool = """
            @start
            @if({asm}==0)(replace=/#zero/0)
            @if({asm}==1)(replace=/#one/1)
            @if({asm}==1)(replace=/#two/2,replace=/#two/TWO)
            @if({asm}==2)(replace=/#three/3,replace=/#three/THREE)
            ; Routine at 40000
            ;
            ; #zero-#one-#two-#three
            c40000 RET
        """
        entry = self._get_parser(skool, asm_mode=5).get_entry(40000)
        self.assertEqual(['#zero-1-2-THREE'], entry.details)

    def test_if_directive_base(self):
        skool = """
            @if({base}==0)(replace=/#zero/0)
            @if({base}==10)(replace=/#one/1)
            @if({base}==10)(replace=/#two/2,replace=/#two/TWO)
            @if({base}==16)(replace=/#three/3,replace=/#three/THREE)
            ; Routine at 40000
            ;
            ; #zero-#one-#two-#three
            c40000 RET
        """
        entry = self._get_parser(skool, base=10).get_entry(40000)
        self.assertEqual(['#zero-1-2-THREE'], entry.details)

    def test_if_directive_case(self):
        skool = """
            @if({case}==0)(replace=/#zero/0)
            @if({case}==1)(replace=/#one/1)
            @if({case}==1)(replace=/#two/2,replace=/#two/TWO)
            @if({case}==2)(replace=/#three/3,replace=/#three/THREE)
            ; Routine at 40000
            ;
            ; #zero-#one-#two-#three
            c40000 RET
        """
        entry = self._get_parser(skool, case=1).get_entry(40000)
        self.assertEqual(['#zero-1-2-THREE'], entry.details)

    def test_if_directive_fix(self):
        skool = """
            @start
            @if({fix}==0)(replace=/#zero/0)
            @if({fix}==1)(replace=/#one/1)
            @if({fix}==1)(replace=/#two/2,replace=/#two/TWO)
            @if({fix}==2)(replace=/#three/3,replace=/#three/THREE)
            ; Routine at 40000
            ;
            ; #zero-#one-#two-#three
            c40000 RET
        """
        entry = self._get_parser(skool, fix_mode=1).get_entry(40000)
        self.assertEqual(['#zero-1-2-THREE'], entry.details)

    def test_if_directive_html(self):
        skool = """
            @if({html}==0)(replace=/#zero/0)
            @if({html}==1)(replace=/#one/1)
            @if({html}==1)(replace=/#two/2,replace=/#two/TWO)
            @if({html}==0)(replace=/#three/3,replace=/#three/THREE)
            ; Routine at 40000
            ;
            ; #zero-#one-#two-#three
            c40000 RET
        """
        entry = self._get_parser(skool, html=True).get_entry(40000)
        self.assertEqual(['#zero-1-2-THREE'], entry.details)

    def test_if_directive_with_variables(self):
        skool = """
            @if({vars[foo]}==0)(replace=/#zero/0)
            @if({vars[foo]}==1)(replace=/#one/1)
            @if({vars[bar]}==2)(replace=/#two/2,replace=/#two/TWO)
            @if({vars[baz]}==1)(replace=/#three/3,replace=/#three/THREE)
            ; Routine at 40000
            ;
            ; #zero-#one-#two-#three
            c40000 RET
        """
        parser = self._get_parser(skool, html=True, variables=('foo=1', 'bar=2', 'baz:1'))
        self.assertEqual(['#zero-1-2-THREE'], parser.get_entry(40000).details)

    def test_if_directive_ignored_if_invalid(self):
        skool = """
            @if(x)(replace=/#zero/0)
            @if(1(replace=/#one/1)
            @if(2)(replace=/#two/2
            @if(3)(replace=/#three/3,replace=/#three/THREE,replace=/#three/1+2)
            ; Routine at 40000
            ;
            ; #zero-#one-#two-#three
            c40000 RET
        """
        entry = self._get_parser(skool).get_entry(40000)
        self.assertEqual(['#zero-#one-#two-#three'], entry.details)

    def test_remote_directive(self):
        skool = """
            @start
            @remote=load:32768
            ; Routine
            c49152 JP $8000
        """
        parser = self._get_parser(skool)
        memory_map = parser.memory_map
        self.assertEqual(len(memory_map), 1)
        instructions = memory_map[0].instructions
        self.assertEqual(len(instructions), 1)
        reference = instructions[0].reference
        self.assertIsNotNone(reference)
        self.assertEqual(reference.address, 32768)
        self.assertEqual(reference.addr_str, '$8000')
        entry = reference.entry
        self.assertTrue(entry.is_remote())
        self.assertEqual(entry.asm_id, 'load')
        self.assertEqual(entry.address, 32768)

    def test_remote_directive_with_entry_point(self):
        skool = """
            @start
            @remote=save:33024,33027
            ; Routine
            c49152 JP 33027
        """
        parser = self._get_parser(skool)
        memory_map = parser.memory_map
        self.assertEqual(len(memory_map), 1)
        instructions = memory_map[0].instructions
        self.assertEqual(len(instructions), 1)
        reference = instructions[0].reference
        self.assertIsNotNone(reference)
        self.assertEqual(reference.address, 33027)
        self.assertEqual(reference.addr_str, '33027')
        entry = reference.entry
        self.assertTrue(entry.is_remote())
        self.assertEqual(entry.asm_id, 'save')
        self.assertEqual(entry.address, 33024)

    def test_references(self):
        skool = """
            ; Routine
            c30000 CALL 30010
             30003 JP NZ,30011
             30004 LD BC,30012
             30006 DJNZ 30013
             30008 JR 30014

            ; Routine
            c30010 LD A,B
             30011 LD A,C
             30012 LD A,D
             30013 LD A,E
             30014 RET

            ; Data
            w30015 DEFW 30003
        """
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
        skool = """
            c00100 LD BC,100
             00103 LD DE,100
             00106 LD HL,100
             00109 LD IX,100
             00112 LD IY,100
             00115 LD SP,100
             00118 LD BC,(100)
             00122 LD DE,(100)
             00126 LD HL,(100)
             00129 LD IX,(100)
             00133 LD IY,(100)
             00137 LD SP,(100)
             00141 LD (100),BC
             00145 LD (100),DE
             00149 LD (100),HL
             00152 LD (100),IX
             00156 LD (100),IY
             00160 LD (100),SP
             00164 LD A,(100)
             00167 LD (100),A
        """
        parser = self._get_parser(skool)

        instructions = parser.memory_map[0].instructions
        self.assertEqual(len(instructions[0].referrers), 0)
        for instruction in instructions:
            self.assertIsNotNone(instruction.reference)
            self.assertEqual(instruction.reference.address, 100)

    def test_references_for_rst_instructions(self):
        skool = """
            @start
            ; Restart routines
            @label=RESTART0
            c00000 DEFS 8
            @label=RESTART8
             00008 DEFS 8
            @label=RESTART16
             00016 DEFS 8
            @label=RESTART24
             00024 DEFS 8
            @label=RESTART32
             00032 DEFS 8
            @label=RESTART40
             00040 DEFS 8
            @label=RESTART48
             00048 DEFS 8
            @label=RESTART56
             00056 RET

            ; RST instructions
            c00057 RST 0
             00058 RST $08
             00059 RST 16
             00060 RST $18
             00061 RST 32
             00062 RST $28
             00063 RST 48
             00064 RST $38
        """
        parser = self._get_parser(skool, asm_mode=1)
        self.assertEqual(len(parser.get_entry(0).instructions[0].referrers), 1)
        index = 20
        lines = textwrap.dedent(skool).strip().split('\n')
        ref_address = 0
        for instruction in parser.get_entry(57).instructions:
            self.assertEqual(instruction.operation, lines[index][7:])
            self.assertIsNotNone(instruction.reference)
            self.assertEqual(instruction.reference.address, ref_address)
            index += 1
            ref_address += 8

    def test_references_to_data_block(self):
        skool = """
            @start
            c40000 LD HL,40005

            w40003 DEFW 40005

            b40005 DEFB 0
        """
        memory_map = self._get_parser(skool, asm_mode=1).memory_map
        self.assertEqual(memory_map[0].instructions[0].reference.address, 40005)
        self.assertEqual(memory_map[1].instructions[0].reference.address, 40005)

    def test_references_to_ignored_entry(self):
        skool = """
            ; Routine
            c30000 CALL 30010
             30003 JP NZ,30010
             30004 LD BC,30010
             30006 DJNZ 30010
             30008 JR 30010

            ; Ignored
            i30010
        """
        parser = self._get_parser(skool)
        instructions = parser.memory_map[0].instructions
        self.assertEqual(len(instructions), 5)
        for instruction in instructions:
            self.assertIsNone(instruction.reference)

    def test_create_labels(self):
        skool = """
            @start
            ; Begin
            c32768 JR 32770

            ; End
            c32770 JR 32768
        """
        parser = self._get_parser(skool, create_labels=True, asm_labels=True)
        instruction = parser.get_entry(32768).instructions[0]
        self.assertEqual(instruction.asm_label, 'L32768')
        self.assertEqual(instruction.operation, 'JR L32770')
        instruction = parser.get_entry(32770).instructions[0]
        self.assertEqual(instruction.asm_label, 'L32770')
        self.assertEqual(instruction.operation, 'JR L32768')

    def test_label_overrides_auto_label(self):
        skool = """
            c32768 JR 32770
            @label=END
            *32770 RET
        """
        parser = self._get_parser(skool, create_labels=True, asm_labels=True)
        instruction = parser.get_instruction(32768)
        self.assertEqual(instruction.asm_label, 'L32768')
        self.assertEqual(instruction.operation, 'JR END')
        self.assertEqual(parser.get_instruction(32770).asm_label, 'END')

    def test_label_sets_auto_label_on_main_entry_point(self):
        skool = """
            @rem=Yes, this @label directive is redundant
            @label=*
            c32768 JR 32768
        """
        parser = self._get_parser(skool, create_labels=True, asm_labels=True)
        instruction = parser.get_instruction(32768)
        self.assertEqual(instruction.asm_label, 'L32768')
        self.assertEqual(instruction.operation, 'JR L32768')

    def test_label_sets_auto_label_on_entry_point(self):
        skool = """
            c32768 JR 32770
            @label=*
             32770 RET
        """
        parser = self._get_parser(skool, create_labels=True, asm_labels=True)
        instruction = parser.get_instruction(32768)
        self.assertEqual(instruction.asm_label, 'L32768')
        self.assertEqual(instruction.operation, 'JR L32768_0')
        self.assertEqual(parser.get_instruction(32770).asm_label, 'L32768_0')

    def test_label_sets_two_auto_labels_without_duplicate_label_error(self):
        skool = """
            c32768 JR 32770
            @label=*
             32770 JR 32772
            @label=*
             32772 RET
        """
        parser = self._get_parser(skool, create_labels=True, asm_labels=True)
        self.assertEqual(parser.get_instruction(32770).asm_label, 'L32768_0')
        self.assertEqual(parser.get_instruction(32772).asm_label, 'L32768_1')

    def test_create_no_labels(self):
        skool = """
            @start
            @label=START
            c32768 JR 32770

            @label=*
            c32770 JR 32768
        """
        parser = self._get_parser(skool, create_labels=False, asm_labels=True)
        instruction = parser.get_entry(32768).instructions[0]
        self.assertEqual(instruction.asm_label, 'START')
        self.assertEqual(instruction.operation, 'JR 32770')
        instruction = parser.get_entry(32770).instructions[0]
        self.assertIsNone(instruction.asm_label)
        self.assertEqual(instruction.operation, 'JR START')

    def test_label_marks_instruction_as_entry_point(self):
        skool = """
            c30000 INC A
            @label=LABEL1
             30001 XOR B   ; Not an entry point (no '*' in the label)
            @label=*LABEL2
             30002 AND C
            @label=*
             30003 RET
        """
        parser = self._get_parser(skool)
        self.assertEqual(parser.get_instruction(30001).ctl, ' ')
        self.assertEqual(parser.get_instruction(30002).ctl, '*')
        self.assertEqual(parser.get_instruction(30003).ctl, '*')

    def test_label_unmarks_instruction_as_entry_point(self):
        skool = """
            c30000 INC A
            @label=
            *30001 RET
        """
        parser = self._get_parser(skool)
        self.assertEqual(parser.get_instruction(30001).ctl, ' ')

    def test_set_directive(self):
        skool = """
            @start
            @set-prop1=1
            @set-prop2=abc
            ; Routine
            c30000 RET
        """
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
        skool = """
            @start
            ; Routine
            c32768 LD HL,32774
             32771 ld de,32774

            ; Next routine
            @label=DOSTUFF
            c32774 RET
        """
        self._get_parser(skool, asm_mode=1, warnings=True)
        warnings = self.err.getvalue()
        exp_warnings = """
            WARNING: LD operand replaced with routine label in unsubbed operation:
              32768 LD HL,32774 -> LD HL,DOSTUFF
            WARNING: LD operand replaced with routine label in unsubbed operation:
              32771 ld de,32774 -> ld de,DOSTUFF
        """
        self.assertEqual(textwrap.dedent(exp_warnings).strip(), warnings.strip())

    def test_instruction_addr_str_no_base(self):
        skool = """
            b00000 DEFB 0

            c24583 LD HL,$6003

            b$600A DEFB 123
        """
        parser = self._get_parser(skool)
        self.assertEqual(parser.get_instruction(0).addr_str, '00000')
        self.assertEqual(parser.get_instruction(24583).addr_str, '24583')
        self.assertEqual(parser.get_instruction(24586).addr_str, '600A')

    def test_instruction_addr_str_base_10(self):
        skool = """
            b$0000 DEFB 0

            c24583 LD HL,$6003

            b$600A DEFB 123
        """
        parser = self._get_parser(skool, base=BASE_10)
        self.assertEqual(parser.get_instruction(0).addr_str, '00000')
        self.assertEqual(parser.get_instruction(24583).addr_str, '24583')
        self.assertEqual(parser.get_instruction(24586).addr_str, '24586')

    def test_instruction_addr_str_base_16(self):
        skool = """
            b00000 DEFB 0

            c24583 LD HL,$6003

            b$600A DEFB 123
        """
        parser = self._get_parser(skool, base=BASE_16)
        self.assertEqual(parser.get_instruction(0).addr_str, '0000')
        self.assertEqual(parser.get_instruction(24583).addr_str, '6007')
        self.assertEqual(parser.get_instruction(24586).addr_str, '600A')

    def test_instruction_addr_str_base_16_lower_case(self):
        skool = """
            c24583 LD HL,$6003

            b$600A DEFB 123
        """
        parser = self._get_parser(skool, case=CASE_LOWER, base=BASE_16)
        self.assertEqual(parser.get_instruction(24583).addr_str, '6007')
        self.assertEqual(parser.get_instruction(24586).addr_str, '600a')

    def test_get_instruction_addr_str_no_base(self):
        skool = """
            c24583 LD HL,$6003

            b$600A DEFB 123
        """
        parser = self._get_parser(skool)
        self.assertEqual(parser.get_instruction_addr_str(24583, ''), '24583')
        self.assertEqual(parser.get_instruction_addr_str(24586, ''), '600A')
        self.assertEqual(parser.get_instruction_addr_str(24587, '24587'), '24587')
        self.assertEqual(parser.get_instruction_addr_str(24587, '$600b'), '600b')
        self.assertEqual(parser.get_instruction_addr_str(24586, '$600B', 'start'), '600B')

    def test_get_instruction_addr_str_base_10(self):
        skool = """
            c24583 LD HL,$6003

            b$600A DEFB 123
        """
        parser = self._get_parser(skool, base=BASE_10)
        self.assertEqual(parser.get_instruction_addr_str(24583, ''), '24583')
        self.assertEqual(parser.get_instruction_addr_str(24586, ''), '24586')
        self.assertEqual(parser.get_instruction_addr_str(24586, '', 'load'), '24586')

    def test_get_instruction_addr_str_base_16(self):
        skool = """
            c24583 LD HL,$6003

            b$600A DEFB 123
        """
        parser = self._get_parser(skool, base=BASE_16)
        self.assertEqual(parser.get_instruction_addr_str(24583, ''), '6007')
        self.assertEqual(parser.get_instruction_addr_str(24586, ''), '600A')
        self.assertEqual(parser.get_instruction_addr_str(24586, '', 'save'), '600A')

    def test_get_instruction_addr_str_base_16_lower_case(self):
        skool = """
            c24583 LD HL,$6003

            b$600A DEFB 123
        """
        parser = self._get_parser(skool, case=CASE_LOWER, base=BASE_16)
        self.assertEqual(parser.get_instruction_addr_str(24583, ''), '6007')
        self.assertEqual(parser.get_instruction_addr_str(24586, ''), '600a')
        self.assertEqual(parser.get_instruction_addr_str(24586, '', 'save'), '600a')

    def test_base_conversion_no_base(self):
        parser = self._get_parser(TEST_BASE_CONVERSION_SKOOL, base=0)
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
        skool = """
            c32768 LD A,10
             32770 LD B,$AF
             32772 LD C,%01010101
             32774 LD D,"A"
             32776 DEFB 10,$AF
             32778 DEFW 32778,$ABCD
             32782 DEFS 10,$FF
        """
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
        skool = """
            c32768 ld a,10
             32770 ld b,$af
             32772 ld c,%01010101
             32774 ld d,"a"
             32776 defb 10,$af
             32778 defw 32778,$abcd
             32782 defs 10,$ff
        """
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
        skool = """
            c40000 LD A, 10
             40002 LD ( HL ), 20
             40004 DEFB 17, "1"
             40006 DEFM 89, "2"
             40008 DEFS 8, "3"
             40016 DEFW 0, "4"
        """
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

    def test_base_conversion_on_non_numeric_operands_containing_digits(self):
        skool = """
            b40000 DEFB b1
             40001 DEFB b_2
             40002 DEFW w1
             40004 DEFW w_2
             40006 LD HL,v1
             40009 LD HL,v_2
        """
        exp_instructions = (
            (40000, 'DEFB b1'),
            (40001, 'DEFB b_2'),
            (40002, 'DEFW w1'),
            (40004, 'DEFW w_2'),
            (40006, 'LD HL,v1'),
            (40009, 'LD HL,v_2')
        )
        parser = self._get_parser(skool, base=BASE_16)
        for address, operation in exp_instructions:
            self.assertEqual(parser.get_instruction(address).operation, operation)

    def test_no_case_conversion(self):
        skool = """
            c54000 LD A,0
             54002 ld b,1
             54004 Ret
        """
        exp_instructions = (
            (54000, 'LD A,0'),
            (54002, 'ld b,1'),
            (54004, 'Ret'),
        )
        parser = self._get_parser(skool, case=0)
        for address, operation in exp_instructions:
            self.assertEqual(parser.get_instruction(address).operation, operation)

    def test_lower_case_conversion_with_character_operands(self):
        skool = """
            c54000 LD A,"A"
             54002 LD B,(IX+"B")
             54005 LD (IY+"C"),C
             54008 LD (IX+"\\""),"D"
        """
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
        skool = """
            c54000 ld a,"a"
             54002 ld b,(ix+"b")
             54005 ld (iy+"c"),c
             54008 ld (ix+"\\""),"d"
        """
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
        skool = """
            c55000 ld ixl,a
             55002 ld ixh,b
             55004 ld iyl,c
             55006 ld iyh,d
        """
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
        skool = """
            ; Test parsing of register blocks in upper case mode
            ;
            ; .
            ;
            ; Input:a Some value
            ;       b Some other value
            ; Output:c The result
            c24605 RET
        """
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
        skool = """
            ; Test parsing of register blocks in lower case mode
            ;
            ; .
            ;
            ; Input:A Some value
            ;       B Some other value
            ; Output:C The result
            c24605 RET
        """
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
        skool = """
            t32768 DEFM "AbCdEfG"
             32775 defm "hIjKlMn"
        """
        parser = self._get_parser(skool, case=CASE_UPPER)
        self.assertEqual(parser.get_instruction(32768).operation, 'DEFM "AbCdEfG"')
        self.assertEqual(parser.get_instruction(32775).operation, 'DEFM "hIjKlMn"')

    def test_defm_lower(self):
        skool = """
            t32768 DEFM "AbCdEfG"
             32775 defm "hIjKlMn"
        """
        parser = self._get_parser(skool, case=CASE_LOWER)
        self.assertEqual(parser.get_instruction(32768).operation, 'defm "AbCdEfG"')
        self.assertEqual(parser.get_instruction(32775).operation, 'defm "hIjKlMn"')

    def test_semicolons_in_instructions(self):
        skool = """
            c60000 CP ";"             ; 60000
             60002 LD A,";"           ; 60002
             60004 LD B,(IX+";")      ; 60004
             60007 LD (IX+";"),C      ; 60007
             60010 LD (IX+";"),";"    ; 60010
             60014 LD (IX+"\\""),";"  ; 60014
             60018 LD (IX+"\\\\"),";" ; 60018
             60022 DEFB 5,"hi;",6     ; 60022
             60027 DEFM ";0;",0       ; 60027
        """
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
        skool = """
            @start
            ; Start
            c30000 JR 30001
        """
        self._get_parser(skool, asm_mode=2, warnings=True)
        warnings = self.err.getvalue()
        self.assertEqual(warnings, 'WARNING: Unreplaced operand: 30000 JR 30001\n')

    def test_no_warning_for_operands_outside_disassembly_address_range(self):
        skool = """
            @start
            c30000 JR 29999
             30002 LD HL,(30005)
        """
        self._get_parser(skool, asm_mode=2, warnings=True)
        warnings = self.err.getvalue()
        self.assertEqual(warnings, '')

    def test_no_warning_for_remote_entry_address_operand_inside_disassembly_address_range(self):
        skool = """
            @start
            @remote=save:30001
            c30000 JP 30001
        """
        self._get_parser(skool, asm_mode=2, warnings=True)
        warnings = self.err.getvalue()
        self.assertEqual(warnings, '')

    def test_no_warning_when_end_address_cannot_be_calculated(self):
        skool = """
            @start
            c30000 LD BC,30004
             30003 DEFB 0,,1   ; Cannot calculate end address from faulty DEFB
        """
        self._get_parser(skool, asm_mode=2, warnings=True)
        warnings = self.err.getvalue()
        self.assertEqual(warnings, '')

    def test_address_strings_in_warnings(self):
        skool = """
            @start
            @label=START
            c$8000 LD HL,$8003
             $8003 LD DE,$8000
             $8006 CALL $8001
        """
        self._get_parser(skool, asm_mode=2, warnings=True)
        warnings = self.err.getvalue()
        exp_warnings = """
            WARNING: Found no label for operand: 8000 LD HL,$8003
            WARNING: LD operand replaced with routine label in unsubbed operation:
              8003 LD DE,$8000 -> LD DE,START
            WARNING: Unreplaced operand: 8006 CALL $8001
        """
        self.assertEqual(textwrap.dedent(exp_warnings).strip(), warnings.strip())

    def test_suppress_warnings(self):
        skool = """
            @start
            c30000 JR 30001 ; This would normally trigger an unreplaced operand warning
        """
        self._get_parser(skool, asm_mode=2, warnings=False)
        warnings = self.err.getvalue()
        self.assertEqual(warnings, '')

    def test_label_substitution_for_address_operands(self):
        skool = """
            @start
            @label=START
            c12445 LD BC,12445
             12448 LD DE,$309D
             12451 LD HL,12445
             12454 LD SP,$309d
             12457 LD IX,12445
             12460 LD IY,$309D
             12463 LD BC,(12445)
             12467 LD DE,($309d)
             12471 LD HL,(12445)
             12474 LD SP,($309D)
             12478 LD IX,(12445)
             12482 LD IY,($309d)
             12486 CALL 12445
             12489 CALL NZ,$309D
             12492 CALL Z,12445
             12495 CALL NC,$309d
             12498 CALL C,12445
             12501 CALL PO,$309D
             12504 CALL PE,12445
             12507 CALL P,$309d
             12510 CALL M,12445
             12513 JP $309D
             12516 JP NZ,12445
             12519 JP Z,$309d
             12522 JP NC,12445
             12525 JP C,$309D
             12528 JP PO,12445
             12531 JP PE,$309d
             12534 JP P,12445
             12537 JP M,$309D
             12540 JR 12445
             12542 JR NZ,$309d
             12544 JR Z,12445
             12546 JR NC,$309D
             12548 JR C,12445
             12550 DJNZ $309d
             12552 LD A,(12445)
             12555 LD ($309D),A
             12558 DEFW %0011000010011101
        """
        parser = self._get_parser(skool, asm_mode=1, asm_labels=True)
        instructions = parser.get_entry(12445).instructions
        self.assertEqual(len(instructions[0].referrers), 1)
        index = 2
        lines = textwrap.dedent(skool).strip().split('\n')
        for instruction in instructions:
            exp_operation = re.sub('(12445|\$309[Dd]|%0011000010011101)', 'START', lines[index][7:])
            self.assertEqual(instruction.operation, exp_operation)
            self.assertIsNotNone(instruction.reference)
            self.assertEqual(instruction.reference.address, 12445)
            index += 1

    def test_label_substitution_for_16_bit_ld_instruction_operands_below_256(self):
        skool = """
            @start
            @label=START
            c00000 LD BC,0
             00003 LD DE,$0000
             00006 LD HL,0
             00009 LD SP,$0000
             00012 LD IX,0
             00016 LD IY,$0000
             00020 LD BC,(0)
             00024 LD DE,($0000)
             00028 LD HL,(0)
             00031 LD SP,($0000)
             00035 LD IX,(0)
             00039 LD IY,($0000)
             00043 LD A,(0)
             00046 LD ($0000),A
        """
        parser = self._get_parser(skool, asm_mode=1, asm_labels=True)

        instructions = parser.memory_map[0].instructions
        self.assertEqual(len(instructions[0].referrers), 0)
        index = 2
        lines = textwrap.dedent(skool).strip().split('\n')
        for instruction in instructions:
            exp_operation = re.sub('(0|\$0000|%0000000000000000)', 'START', lines[index][7:])
            self.assertEqual(instruction.operation, exp_operation)
            self.assertIsNotNone(instruction.reference)
            self.assertEqual(instruction.reference.address, 0)
            index += 1

    def test_label_substitution_for_complex_operand(self):
        skool = """
            @start
            @label=START
            @ssub=LD HL,32768+$0A
            c32768 LD HL,32778
            @label=DOSTUFF
            @ssub=LD DE,10+32768
             32771 LD DE,32778
             32774 JP 32768/256+32771
        """
        parser = self._get_parser(skool, asm_mode=2, asm_labels=True)

        self.assertEqual(parser.get_instruction(32768).operation, 'LD HL,START+$0A')
        self.assertEqual(parser.get_instruction(32771).operation, 'LD DE,10+START')
        self.assertEqual(parser.get_instruction(32774).operation, 'JP START/256+DOSTUFF')

    def test_no_label_substitution_for_8_bit_numeric_operands(self):
        skool = """
            @start
            @label=DATA
            b00124 DEFB 124,132,0,0,0,0,0,0

            @label=START
            c00132 LD A,132
             00134 LD B,132
             00136 LD C,132
             00138 LD D,132
             00140 LD E,132
             00142 LD H,132
             00144 LD L,132
             00146 LD IXh,132
             00149 LD IXl,132
             00152 LD IYh,132
             00155 LD IYl,132
             00158 LD A,(IX+124)
             00161 LD B,(IX-124)
             00164 LD C,(IX+124)
             00167 LD D,(IX-124)
             00170 LD E,(IX+124)
             00173 LD H,(IX-124)
             00176 LD L,(IX+124)
             00179 LD A,(IY-124)
             00182 LD B,(IY+124)
             00185 LD C,(IY-124)
             00188 LD D,(IY+124)
             00191 LD E,(IY-124)
             00194 LD H,(IY+124)
             00197 LD L,(IY-124)
             00200 LD (IX+124),132
             00204 LD (IY-124),132
             00208 ADD A,132
             00210 ADC A,132
             00212 SBC A,132
             00214 SUB 132
             00216 AND 255
             00218 XOR 255
             00220 OR 255
             00222 CP 255
             00224 DEFB 255
             00225 SET 0,(IX+124)
             00228 RES 1,(IY-124)
             00231 BIT 2,(IX-124)
             00234 RL (IY+124)
             00237 RLC (IX+124)
             00240 RR (IY-124)
             00243 RRC (IX-124)
             00246 SLA (IY+124)
             00249 SLL (IX+124)
             00252 SRA (IY-124)

            @label=CONTINUE
            c00255 SRL (IX-124)
             00258 IN A,(132)
             00260 OUT (132),A
        """
        parser = self._get_parser(skool, asm_mode=1, asm_labels=True)
        lines = textwrap.dedent(skool).strip().split('\n')

        instruction = parser.get_entry(124).instructions[0]
        self.assertEqual(len(instruction.referrers), 0)
        self.assertEqual(instruction.operation, lines[2][7:])

        instructions = parser.get_entry(132).instructions
        self.assertEqual(len(instructions[0].referrers), 0)
        index = 5
        for instruction in instructions:
            self.assertEqual(instruction.operation, lines[index][7:])
            self.assertIsNone(instruction.reference)
            index += 1

        instructions = parser.get_entry(255).instructions
        self.assertEqual(len(instructions[0].referrers), 0)
        index += 2
        for instruction in instructions:
            self.assertEqual(instruction.operation, lines[index][7:])
            self.assertIsNone(instruction.reference)
            index += 1

    def test_no_label_substitution_in_defs_statements(self):
        skool = """
            @start
            @label=SPACE1
            s00010 DEFS 9990,10

            @label=SPACE2
            s10000 DEFS 10000,255
        """
        parser = self._get_parser(skool, asm_mode=1, asm_labels=True)
        lines = textwrap.dedent(skool).strip().split('\n')

        instruction = parser.get_instruction(10)
        self.assertEqual(len(instruction.referrers), 0)
        self.assertEqual(instruction.operation, lines[2][7:])

        instruction = parser.get_instruction(10000)
        self.assertEqual(len(instruction.referrers), 0)
        self.assertEqual(instruction.operation, lines[5][7:])

    def test_label_substitution_in_defb_statements(self):
        skool = """
            @start
            @label=START
            b30000 DEFB "30000"             ; No label here
            @label=HELLO
             30005 DEFB "Hello 30000"       ; Or here
             30016 DEFB 30000/256           ; But one here
             30017 DEFB 30000/256,30005/256 ; And two here
             30019 DEFB 1+30000%256         ; One here
             30021 DEFB 30000/256+30005/256 ; Two here
        """
        parser = self._get_parser(skool, asm_mode=1, asm_labels=True)

        self.assertEqual(parser.get_instruction(30000).operation, 'DEFB "30000"')
        self.assertEqual(parser.get_instruction(30005).operation, 'DEFB "Hello 30000"')
        self.assertEqual(parser.get_instruction(30016).operation, 'DEFB START/256')
        self.assertEqual(parser.get_instruction(30017).operation, 'DEFB START/256,HELLO/256')
        self.assertEqual(parser.get_instruction(30019).operation, 'DEFB 1+START%256')
        self.assertEqual(parser.get_instruction(30021).operation, 'DEFB START/256+HELLO/256')

    def test_label_substitution_in_defm_statements(self):
        skool = """
            @start
            @label=START
            b40000 DEFM "40000"             ; No label here
            @label=HELLO
             40005 DEFM "Hello 40000"       ; Or here
             40016 DEFM 40000/256           ; But one here
             40017 DEFM 40000/256,40005/256 ; And two here
             40019 DEFM 1+40000%256         ; One here
             40021 DEFM 40000/256+40005/256 ; Two here
        """
        parser = self._get_parser(skool, asm_mode=1, asm_labels=True)

        self.assertEqual(parser.get_instruction(40000).operation, 'DEFM "40000"')
        self.assertEqual(parser.get_instruction(40005).operation, 'DEFM "Hello 40000"')
        self.assertEqual(parser.get_instruction(40016).operation, 'DEFM START/256')
        self.assertEqual(parser.get_instruction(40017).operation, 'DEFM START/256,HELLO/256')
        self.assertEqual(parser.get_instruction(40019).operation, 'DEFM 1+START%256')
        self.assertEqual(parser.get_instruction(40021).operation, 'DEFM START/256+HELLO/256')

    def test_label_substitution_in_defw_statements(self):
        skool = """
            @start
            @label=START
            b50000 DEFW 50000               ; One label here
            @label=END
             50002 DEFW 50000,50002         ; And two here
             50006 DEFW 1+50000             ; One here
             50008 DEFW 50000+50002/256     ; Two here
        """
        parser = self._get_parser(skool, asm_mode=1, asm_labels=True)

        self.assertEqual(parser.get_instruction(50000).operation, 'DEFW START')
        self.assertEqual(parser.get_instruction(50002).operation, 'DEFW START,END')
        self.assertEqual(parser.get_instruction(50006).operation, 'DEFW 1+START')
        self.assertEqual(parser.get_instruction(50008).operation, 'DEFW START+END/256')

    def test_error_duplicate_label(self):
        skool = """
            @start
            ; Start
            @label=START
            c40000 RET

            ; False start
            @label=START
            c40001 RET
        """
        with self.assertRaisesRegex(SkoolParsingError, 'Duplicate label START at 40001'):
            self._get_parser(skool, asm_mode=1, asm_labels=True)

    def test_equ_directive_html_mode(self):
        skool = """
            @start
            @equ=DF=16384
            c32768 LD HL,16384
        """
        parser = self._get_parser(skool)
        self.assertEqual([], parser.equs)
        instruction = parser.get_instruction(32768)
        self.assertEqual(instruction.operation, 'LD HL,16384')

    def test_equ_directive_asm_mode(self):
        skool = """
            @start
            @equ=ZERO=0
            @equ=PAGE=256
            @equ=DF=16384
            c32768 LD HL,16384
             32771 LD DE,$0000
             32774 LD BC,16384+6912
             32777 LD A,0
             32779 DEFS 256
        """
        exp_equs = [('ZERO', '0'), ('PAGE', '256'), ('DF', '16384')]
        exp_instructions = (
            (32768, 'LD HL,DF'),
            (32771, 'LD DE,ZERO'),
            (32774, 'LD BC,DF+6912'),
            (32777, 'LD A,0'),        # Not applied to 8-bit operands
            (32779, 'DEFS 256')       # Not applied to DEFS statements
        )
        parser = self._get_parser(skool, asm_mode=1)
        self.assertEqual(exp_equs, parser.equs)
        for address, exp_operation in exp_instructions:
            self.assertEqual(parser.get_instruction(address).operation, exp_operation)

    def test_equ_directive_with_bad_value_is_recorded(self):
        skool = """
            @start
            @equ=DF=foo
            c32768 LD HL,16384
        """
        parser = self._get_parser(skool, asm_mode=1)
        self.assertEqual([('DF', 'foo')], parser.equs)

    def test_asm_mode(self):
        skool = """
            @start
            ; Routine
            @rsub-begin
            @label=FOO
            @rsub+else
            @label=BAR
            @rsub+end
            c32768 RET
        """
        for asm_mode, exp_label in ((0, 'FOO'), (1, 'FOO'), (2, 'FOO'), (3, 'BAR')):
            parser = self._get_parser(skool, asm_mode=asm_mode, asm_labels=True)
            self.assertEqual(parser.get_instruction(32768).asm_label, exp_label)

    def test_rsub_no_address(self):
        skool = """
            @start
            ; Routine
            c30000 XOR A
            @rsub-begin
             30001 LD L,0
            @rsub+else
                   LD HL,16384
            @rsub+end
        """
        parser = self._get_parser(skool, asm_mode=3)
        entry = parser.get_entry(30000)
        instruction = entry.instructions[1]
        self.assertEqual(instruction.operation, 'LD HL,16384')
        self.assertEqual(instruction.sub, instruction.operation)

    def test_start_and_end_directives(self):
        skool = """
            c40000 LD A,B

            @start
            c40001 LD A,C
            @end

            c40002 LD A,D

            @start
            c40003 LD A,E
            @end

            c40004 LD A,H
        """
        parser = self._get_parser(skool, asm_mode=1)
        self.assertIsNone(parser.get_entry(40000))
        self.assertIsNotNone(parser.get_entry(40001))
        self.assertIsNone(parser.get_entry(40002))
        self.assertIsNotNone(parser.get_entry(40003))
        self.assertIsNone(parser.get_entry(40004))

    def test_start_and_end_directives_ignored_when_asm_mode_not_1_or_2_or_3(self):
        skool = """
            @isub=LD A,1
            @ssub=LD A,2
            @rsub=LD A,3
            c40000 LD A,0

            @start
            c40001 LD A,C
            @end

            c40002 LD A,D
        """
        for asm_mode in (0, 4, 5, 6, 7):
            with self.subTest(asm_mode=asm_mode):
                parser = self._get_parser(skool, asm_mode=asm_mode)
                self.assertIsNotNone(parser.get_entry(40000))
                self.assertEqual(parser.get_instruction(40000).operation, 'LD A,{}'.format(asm_mode & 3))
                self.assertIsNotNone(parser.get_entry(40002))

    def test_start_directive_processed_inside_block_directive(self):
        skool = """
            @ofix-begin
            @start
            @ofix-end

            ; Start
            c32768 LD A,1

            @start
            ; End
            c32770 RET
        """
        parser = self._get_parser(skool, asm_mode=1, fix_mode=0)
        self.assertIsNotNone(parser.get_entry(32768))
        self.assertIsNotNone(parser.get_entry(32770))

    def test_start_directive_ignored_inside_block_directive(self):
        skool = """
            @ofix-begin
            @start
            @ofix-end

            ; Start
            c32768 LD A,1

            @start
            ; End
            c32770 RET
        """
        parser = self._get_parser(skool, asm_mode=1, fix_mode=1)
        self.assertIsNone(parser.get_entry(32768))
        self.assertIsNotNone(parser.get_entry(32770))

    def test_end_directive_processed_inside_block_directive(self):
        skool = """
            @start
            @ofix-begin
            ; Set A=1
            c32768 LD A,1
            @end
            @ofix-end
            ; Clear A
            c32768 LD A,0
        """
        parser = self._get_parser(skool, asm_mode=1, fix_mode=0)
        entry = parser.get_entry(32768)
        self.assertEqual(entry.description, 'Set A=1')
        self.assertEqual(entry.instructions[0].operation, 'LD A,1')

    def test_end_directive_ignored_inside_block_directive(self):
        skool = """
            @start
            @ofix-begin
            ; Set A=1
            c32768 LD A,1
            @end
            @ofix-end
            ; Clear A
            c32768 LD A,0
        """
        entry = self._get_parser(skool, asm_mode=1, fix_mode=1).get_entry(32768)
        self.assertIsNotNone(entry)
        self.assertEqual(entry.description, 'Clear A')
        self.assertEqual(entry.instructions[0].operation, 'LD A,0')

    def test_org_directive(self):
        skool = """
            @start
            @org=40000
            ; Routine
            c40000 XOR A
            @org
             40001 RET
        """
        parser = self._get_parser(skool, asm_mode=1)
        instructions = parser.get_entry(40000).instructions
        self.assertEqual(instructions[0].org, '40000')
        self.assertEqual(instructions[1].org, '40001')

    def test_replace_directive(self):
        skool = r"""
            @replace=/#COPY/#CHR169/ This text is ignored
            @replace=/#BIGUDG(\d+)/#UDG\1,57,8
            @replace=@/gap/@#SPACE10@
            @replace=/~(\w+)~/Register \1/
            @replace=:/(\d+)/:comment \1
            ; Game #COPY 1984
            ;
            ; Image: #HTML[#BIGUDG32768]
            ; .
            ; 10 spaces: "/gap/"
            ;
            ; A ~A~
            ; B ~B~
            ;
            ; Start /1/
            ; .
            ; Start /2/
            c32768 LD A,10  ; Instruction-level /1/
            ; Mid-block /1/
            ; .
            ; Mid-block /2/
             32769 RET      ; Instruction-level /2/
            ; End /1/
            ; .
            ; End /2/
        """
        entry = self._get_parser(skool).get_entry(32768)
        self.assertEqual(entry.description, 'Game #CHR169 1984')
        self.assertEqual(['Image: #HTML[#UDG32768,57,8]', '10 spaces: "#SPACE10"'], entry.details)
        self.assertEqual(entry.registers[0].contents, 'Register A')
        self.assertEqual(entry.registers[1].contents, 'Register B')
        instruction1 = entry.instructions[0]
        self.assertEqual(['Start comment 1', 'Start comment 2'], instruction1.mid_block_comment)
        self.assertEqual(instruction1.comment.text, 'Instruction-level comment 1')
        instruction2 = entry.instructions[1]
        self.assertEqual(['Mid-block comment 1', 'Mid-block comment 2'], instruction2.mid_block_comment)
        self.assertEqual(instruction2.comment.text, 'Instruction-level comment 2')
        self.assertEqual(['End comment 1', 'End comment 2'], entry.end_comment)

    def test_replace_directive_with_special_sequence_i(self):
        skool = r"""
            @replace=/#udg\((\i)\)/#UDG(\1,58)
            ; Routine at 35516
            ;
            ; #udg(35516)
            ; .
            ; #udg($8abc)
            ; .
            ; #udg($8ABC)
            b35516 DEFS 8,85
        """
        entry = self._get_parser(skool).get_entry(35516)
        exp_details = [
            '#UDG(35516,58)',
            '#UDG($8abc,58)',
            '#UDG($8ABC,58)'
        ]
        self.assertEqual(exp_details, entry.details)

    def test_replace_directive_processed_before_html_escaped(self):
        skool = r"""
            @replace=/&([0-9A-F]{2})/+\1
            ; &0A == +0A, & that is true
            c32768 RET
        """
        entry = self._get_parser(skool, html=True).get_entry(32768)
        self.assertEqual(entry.description, '+0A == +0A, &amp; that is true')

    def test_replace_directive_with_no_pattern_or_replacement(self):
        skool = """
            @replace=
            @replace=/pattern with no replacement
            ; Test pattern with no replacement
            c32768 RET
        """
        entry = self._get_parser(skool).get_entry(32768)
        self.assertEqual(entry.description, 'Test pattern with no replacement')

    def test_replace_directive_with_invalid_pattern(self):
        skool = """
            @replace=/[abc/xyz
            ; Routine
            c32768 RET
        """
        self.assert_error(skool, "Failed to compile regular expression '\[abc': (unexpected end of regular expression|unterminated character set at position 0)")

    def test_replace_directive_with_invalid_replacement(self):
        skool = r"""
            @replace=/Routine/\1
            ; Routine
            c32768 RET
        """
        self.assert_error(skool, r"Failed to replace 'Routine' with '\\1': invalid group reference")

    def test_isub_block_directive(self):
        skool = """
            @start
            ; Routine
            ;
            @isub+begin
            ; Actual description.
            @isub-else
            ; Other description.
            @isub-end
            c24576 RET
        """
        for asm_mode in (1, 2, 3):
            parser = self._get_parser(skool, asm_mode=asm_mode)
            self.assertEqual(['Actual description.'], parser.get_entry(24576).details)

    def test_ssub_block_directive(self):
        skool = """
            @start
            ; Routine
            @ssub-begin
            c50000 LD L,24 ; 24 is the LSB
            @ssub+else
            c50000 LD L,50003%256 ; This is the LSB
            @ssub+end
             50002 RET
        """
        for asm_mode, exp_operation, exp_comment in (
                (0, 'LD L,24', '24 is the LSB'),
                (1, 'LD L,24', '24 is the LSB'),
                (2, 'LD L,50003%256', 'This is the LSB'),
                (3, 'LD L,50003%256', 'This is the LSB')
        ):
            parser = self._get_parser(skool, asm_mode=asm_mode)
            instruction = parser.get_entry(50000).instructions[0]
            self.assertEqual(instruction.operation, exp_operation)
            self.assertEqual(instruction.comment.text, exp_comment)

    def test_sub_directive_precedence(self):
        skool = """
            @start
            @isub=LD A,1
            @ssub=LD A,2
            @rsub=LD A,3
            c24576 LD A,0
        """
        for asm_mode in (0, 1, 2, 3):
            with self.subTest(asm_mode=asm_mode):
                instruction = self._get_parser(skool, asm_mode=asm_mode).get_instruction(24576)
                self.assertEqual(instruction.operation, 'LD A,{}'.format(asm_mode))

    def test_fix_directive_precedence(self):
        skool = """
            @start
            @ofix=LD A,1
            @bfix=LD A,2
            @rfix=LD A,3
            c24576 LD A,0
        """
        for fix_mode in (0, 1, 2, 3):
            with self.subTest(fix_mode=fix_mode):
                instruction = self._get_parser(skool, asm_mode=1, fix_mode=fix_mode).get_instruction(24576)
                self.assertEqual(instruction.operation, 'LD A,{}'.format(fix_mode))

    def test_sub_and_fix_directives_without_comment(self):
        skool = """
            @start
            ; Routine
            @{0}=LD A,1
            c32768 LD A,0 ; Initialise A.
        """
        exp_instructions = [('32768', 'LD A,0', 'Initialise A.')]
        exp_subs = [('32768', 'LD A,1', 'Initialise A.')]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_with_comment_in_lower_and_upper_case(self):
        skool = """
            @start
            ; Routine
            @{}=INC DE ; Increment DE.
            c50000 INC E ; Add 1 to E.
        """
        for case, op in (
                (0, 'INC DE'),
                (1, 'inc de'),
                (2, 'INC DE')
        ):
            def func(parser):
                instruction = parser.get_instruction(50000)
                self.assertEqual(instruction.operation, op)
                self.assertEqual(instruction.comment.text, 'Increment DE.')
            self._assert_sub_and_fix_directives(skool, func, case=case)

    def test_sub_and_fix_directives_replacing_comment_only(self):
        skool = """
            @start
            ; Routine
            @{0}=         ; Reset A.
            c32768 LD A,0 ; Initialise A.
            @label=END
            @{0}=         ; Done.
             32770 RET    ; Finished.
        """
        exp_instructions = [
            (None, '32768', 'LD A,0', 'Initialise A.'),
            ('END', '32770', 'RET', 'Finished.')
        ]
        exp_subs = [
            (None, '32768', 'LD A,0', 'Reset A.'),
            ('END', '32770', 'RET', 'Done.')
        ]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_without_comment_do_not_remove_second_comment_line(self):
        skool = """
            @start
            ; Routine
            @{0}=XOR A
            c32768 XOR B ;
                         ; This comment should survive.
        """
        exp_instructions = [('32768', 'XOR B', 'This comment should survive.')]
        exp_subs = [('32768', 'XOR A', 'This comment should survive.')]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_replacing_single_comment_line(self):
        skool = """
            @start
            ; Routine
            @{}=LD A,(32768)    ; Get the counter from 32768.
            c60000 LD A,(32769) ; Get the value from 32769.
        """
        exp_instructions = [('60000', 'LD A,(32769)', 'Get the value from 32769.')]
        exp_subs = [('60000', 'LD A,(32768)', 'Get the counter from 32768.')]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_replacing_first_of_two_comment_lines(self):
        skool = """
            @start
            ; Routine
            @{}=LD A,(32768)    ; Get the counter from 32768
            c60000 LD A,(32769) ; Get the value from 32769
                                ; first.
        """
        exp_instructions = [('60000', 'LD A,(32769)', 'Get the value from 32769 first.')]
        exp_subs = [('60000', 'LD A,(32768)', 'Get the counter from 32768 first.')]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_replacing_one_comment_line_with_two(self):
        skool = """
            @start
            ; Routine
            @{0}=LD A,1   ; Initialise the
            @{0}=         ; counter to 1.
            c32768 LD A,0 ; Set A=0.
        """
        exp_instructions = [('32768', 'LD A,0', 'Set A=0.')]
        exp_subs = [('32768', 'LD A,1', 'Initialise the counter to 1.')]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_appending_comment_line(self):
        skool = """
            @start
            ; Routine
            @{0}=LD A,1
            @{0}=         ; to 1
            c32768 LD A,0 ; Initialise the counter
        """
        exp_instructions = [('32768', 'LD A,0', 'Initialise the counter')]
        exp_subs = [('32768', 'LD A,1', 'Initialise the counter to 1')]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_replacing_one_comment_line_with_three(self):
        skool = """
            @start
            ; Routine
            @{0}=LD A,1   ; Initialise
            @{0}=         ; the counter
            @{0}=         ; to 1.
            c32768 LD A,0 ; Set A=0.
        """
        exp_instructions = [('32768', 'LD A,0', 'Set A=0.')]
        exp_subs = [('32768', 'LD A,1', 'Initialise the counter to 1.')]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_replacing_two_comment_lines(self):
        skool = """
            @start
            ; Routine
            @{0}=LD A,1   ; Initialise the
            @{0}=         ; counter to 1.
            c32768 LD A,0 ; Reset the
                          ; counter to 0.
        """
        exp_instructions = [('32768', 'LD A,0', 'Reset the counter to 0.')]
        exp_subs = [('32768', 'LD A,1', 'Initialise the counter to 1.')]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_replacing_two_comment_lines_with_one(self):
        skool = """
            @start
            ; Routine
            @{0}=/LD A,1  ; Initialise the counter to 1.
            c32768 LD A,0 ; Reset the
                          ; counter to 0.
        """
        exp_instructions = [('32768', 'LD A,0', 'Reset the counter to 0.')]
        exp_subs = [('32768', 'LD A,1', 'Initialise the counter to 1.')]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_replacing_three_comment_lines_with_two(self):
        skool = """
            @start
            ; Routine
            @{0}=LD A,1   ; Initialise the
            @{0}=/        ; counter to 1.
            c32768 LD A,0 ; Reset the
                          ; counter
                          ; to 0.
        """
        exp_instructions = [('32768', 'LD A,0', 'Reset the counter to 0.')]
        exp_subs = [('32768', 'LD A,1', 'Initialise the counter to 1.')]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_replacing_three_comment_lines_with_one(self):
        skool = """
            @start
            ; Routine
            @{0}=/LD A,1  ; Initialise the counter to 1.
            c32768 LD A,0 ; Reset the
                          ; counter
                          ; to 0.
        """
        exp_instructions = [('32768', 'LD A,0', 'Reset the counter to 0.')]
        exp_subs = [('32768', 'LD A,1', 'Initialise the counter to 1.')]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_add_instruction(self):
        skool = """
            @start
            ; Routine
            @{0}=|LD L,0   ; Clear L
            @{0}=|LD H,L   ; And then H
            c32768 LD HL,0 ; Clear HL
        """
        exp_instructions = [('32768', 'LD HL,0', 'Clear HL')]
        exp_subs = [
            ('32768', 'LD L,0', 'Clear L'),
            ('32770', 'LD H,L', 'And then H')
        ]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_add_instruction_hex(self):
        skool = """
            @start
            ; Routine
            @{0}=|LD L,0       ; Clear L
            @{0}=|LD H,L       ; And then H
            c$800A LD HL,$0000 ; Clear HL
        """
        exp_instructions = [('800A', 'LD HL,$0000', 'Clear HL')]
        exp_subs = [
            ('800A', 'LD L,$00', 'Clear L'),
            ('800C', 'LD H,L', 'And then H')
        ]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs, base=BASE_16)

    def test_sub_and_fix_directives_add_instruction_lower_case_hex(self):
        skool = """
            @start
            ; Routine
            @{0}=|LD L,0   ; Clear L
            @{0}=|LD H,L   ; And then H
            c32778 LD HL,0 ; Clear HL
        """
        exp_instructions = [('800a', 'ld hl,$0000', 'Clear HL')]
        exp_subs = [
            ('800a', 'ld l,$00', 'Clear L'),
            ('800c', 'ld h,l', 'And then H')
        ]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs, base=BASE_16, case=CASE_LOWER)

    def test_sub_and_fix_directives_add_instruction_with_comment_continuation_line(self):
        skool = """
            @start
            ; Routine
            @{0}=|LD L,0   ; Clear L
            @{0}=|LD H,L   ; And then H,
            @{0}=          ; for good measure
            c32768 LD HL,0 ; Clear HL
        """
        exp_instructions = [('32768', 'LD HL,0', 'Clear HL')]
        exp_subs = [
            ('32768', 'LD L,0', 'Clear L'),
            ('32770', 'LD H,L', 'And then H, for good measure')
        ]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_add_instruction_after_invalid_instruction(self):
        skool = """
            @start
            ; Routine
            @{0}=|LD L,X
            @{0}=|LD H,L
            c32768 LD HL,0
        """
        exp_error = "Cannot determine address of instruction after '32768 LD L,X'"
        self._assert_sub_and_fix_directives(skool, exp_error=exp_error)

    def test_sub_and_fix_directives_override_comment_continuation_lines_when_overwriting(self):
        skool = """
            @start
            ; Routine
            @{0}=/|XOR A
            @{0}=|INC A    ;
            c32768 LD A,0 ; Clear A
                          ; in
                          ; preparation
        """
        exp_instructions = [('32768', 'LD A,0', 'Clear A in preparation')]
        exp_subs = [
            ('32768', 'XOR A', 'Clear A'),
            ('32769', 'INC A', '')
        ]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_add_instruction_cleanly(self):
        skool = """
            @start
            ; Routine
            @keep
            @ignoreua
            @label=START
            @nowarn
            @{0}=|LD L,0
            @{0}=|LD H,L
            c32768 LD HL,0
        """
        def func(parser):
            inst1 = parser.get_instruction(32768)
            inst2 = parser.get_instruction(32770)
            self.assertEqual([], inst1.keep)
            self.assertTrue(inst1.ignoreua)
            self.assertEqual(inst1.asm_label, 'START')
            self.assertIsNone(inst1.org)
            self.assertFalse(inst1.warn)
            self.assertIsNone(inst2.keep)
            self.assertFalse(inst2.ignoreua)
            self.assertIsNone(inst2.asm_label)
            self.assertEqual(inst2.org, '32770')
            self.assertTrue(inst2.warn)
        self._assert_sub_and_fix_directives(skool, func)

    def test_sub_and_fix_directives_replace_two_instructions_with_one(self):
        skool = """
            @start
            ; Routine
            @{0}=|LD HL,0 ; Clear HL
            c32768 LD L,0 ; Clear L
             32770 LD H,L ; Clear the
                          ; H register
        """
        exp_instructions = [
            ('32768', 'LD L,0', 'Clear L'),
            ('32770', 'LD H,L', 'Clear the H register')
        ]
        exp_subs = [('32768', 'LD HL,0', 'Clear HL')]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_replace_three_instructions_with_one(self):
        skool = """
            @start
            ; Routine
            @{0}=|LD HL,0 ; Clear HL
            c32768 XOR A  ; Clear A
             32769 LD H,A ; Clear H
             32770 LD L,H ; Clear the
                          ; L register
        """
        exp_instructions = [
            ('32768', 'XOR A', 'Clear A'),
            ('32769', 'LD H,A', 'Clear H'),
            ('32770', 'LD L,H', 'Clear the L register')
        ]
        exp_subs = [('32768', 'LD HL,0', 'Clear HL')]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_replace_later_instruction(self):
        skool = """
            @start
            ; Routine
            @{0}=|       ; Reset A
            @{0}=|SUB C  ; Subtract C
            c32768 XOR A ; Clear A
             32769 SUB B ; Subtract B
        """
        exp_instructions = [
            ('32768', 'XOR A', 'Clear A'),
            ('32769', 'SUB B', 'Subtract B')
        ]
        exp_subs = [
            ('32768', 'XOR A', 'Reset A'),
            ('32769', 'SUB C', 'Subtract C')
        ]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_replace_entire_comment_of_later_instruction(self):
        skool = """
            @start
            ; Routine
            @{0}=|LD A,H  ; Set A=H
            @{0}=|SUB C   ; Subtract C
            c32768 LD A,L ; Set A=L
             32769 SUB B  ; Subtract B
                          ; from A
        """
        exp_instructions = [
            ('32768', 'LD A,L', 'Set A=L'),
            ('32769', 'SUB B', 'Subtract B from A')
        ]
        exp_subs = [
            ('32768', 'LD A,H', 'Set A=H'),
            ('32769', 'SUB C', 'Subtract C')
        ]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_replace_two_later_instructions(self):
        skool = """
            @start
            ; Routine
            @{0}=|LD A,2
            @{0}=|SUB C   ; Subtract C
            @{0}=         ; from A
            @{0}=|SUB E   ; Subtract E
            c32768 LD A,1 ; Initialise A
             32770 SUB B  ; Subtract B
             32771 SUB D  ; Subtract D
        """
        exp_instructions = [
            ('32768', 'LD A,1', 'Initialise A'),
            ('32770', 'SUB B', 'Subtract B'),
            ('32771', 'SUB D', 'Subtract D')
        ]
        exp_subs = [
            ('32768', 'LD A,2', 'Initialise A'),
            ('32770', 'SUB C', 'Subtract C from A'),
            ('32771', 'SUB E', 'Subtract E')
        ]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_discard_comment_on_overwritten_instruction(self):
        skool = """
            @start
            ; Routine
            @{}=|LD A,1  ; {{Set A=1 and
            c32768 XOR A ; {{Set A to 1
             32769 INC A ; and then
             32770 RET   ; return}}
        """
        exp_instructions = [
            ('32768', 'XOR A', 'Set A to 1 and then return'),
            ('32769', 'INC A', None),
            ('32770', 'RET', None)
        ]
        exp_subs = [
            ('32768', 'LD A,1', 'Set A=1 and return'),
            ('32770', 'RET', None)
        ]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_discard_comment_with_opening_brace_on_overwritten_instruction(self):
        skool = """
            @start
            ; Yes, there will be an unmatched closing brace at 32770
            @{}=|LD A,1  ; Set A=1 and
            c32768 XOR A ; Clear A
             32769 INC A ; {{Increment A and
             32770 RET   ; return}}
        """
        exp_instructions = [
            ('32768', 'XOR A', 'Clear A'),
            ('32769', 'INC A', 'Increment A and return'),
            ('32770', 'RET', None)
        ]
        exp_subs = [
            ('32768', 'LD A,1', 'Set A=1 and'),
            ('32770', 'RET', 'return}')
        ]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_push_instructions_aside(self):
        skool = """
            @start
            ; Routine
            @{0}=LD L,1   ; Set L=1
            c32768 INC L  ; Increment L
             32769 LD H,L ; Set
                          ; H=L
        """
        exp_instructions = [
            ('32768', 'INC L', 'Increment L'),
            ('32769', 'LD H,L', 'Set H=L')
        ]
        exp_subs = [
            ('32768', 'LD L,1', 'Set L=1'),
            ('32769', 'LD H,L', 'Set H=L')
        ]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_insert_instructions_with_no_address(self):
        skool = """
            @start
            ; Routine
            @{0}=LD (HL),0   ; {{Clear the address
            @{0}=INC L       ;
            @{0}=LD (HL),0   ; }}
            c32768 LD (HL),0 ; Clear the address
             32770 RET
        """
        exp_instructions = [
            ('32768', 'LD (HL),0', 'Clear the address'),
            ('32770', 'RET', '')
        ]
        exp_subs = [
            ('32768', 'LD (HL),0', 'Clear the address'),
            ('     ', 'INC L', None),
            ('     ', 'LD (HL),0', None),
            ('32770', 'RET', '')
        ]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_override_comment_continuation_lines(self):
        skool = """
            @start
            ; Routine
            @{0}=/LD (HL),0
            @{0}=INC L       ;
            c32768 LD (HL),0 ; Clear the contents
                             ; of the address
                             ; pointed at by HL
        """
        exp_instructions = [
            ('32768', 'LD (HL),0', 'Clear the contents of the address pointed at by HL')
        ]
        exp_subs = [
            ('32768', 'LD (HL),0', 'Clear the contents'),
            ('     ', 'INC L', '')
        ]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_insert_instruction_cleanly(self):
        skool = """
            @start
            ; Routine
            @keep
            @ignoreua
            @label=START
            @nowarn
            @{0}=LD HL,0
            @{0}=XOR A
            c32768 LD L,0
        """
        def func(parser):
            instructions = parser.get_entry(32768).instructions
            inst1 = instructions[0]
            inst2 = instructions[1]
            self.assertEqual([], inst1.keep)
            self.assertTrue(inst1.ignoreua)
            self.assertEqual(inst1.asm_label, 'START')
            self.assertIsNone(inst1.org)
            self.assertFalse(inst1.warn)
            self.assertIsNone(inst2.keep)
            self.assertFalse(inst2.ignoreua)
            self.assertIsNone(inst2.asm_label)
            self.assertEqual(inst2.org, '     ')
            self.assertTrue(inst2.warn)
        self._assert_sub_and_fix_directives(skool, func)

    def test_sub_and_fix_directives_prepend_instruction(self):
        skool = """
            @start
            ; Routine
            @{}=>LD H,0   ; Clear H
            c32768 LD L,H ; Clear L
        """
        exp_instructions = [
            ('32768', 'LD L,H', 'Clear L')
        ]
        exp_subs = [
            ('     ', 'LD H,0', 'Clear H'),
            ('32768', 'LD L,H', 'Clear L')
        ]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_append_instruction(self):
        skool = """
            @start
            ; Routine
            @{}=+LD L,H   ; Clear L
            c32768 LD H,0 ; Clear H
        """
        exp_instructions = [
            ('32768', 'LD H,0', 'Clear H')
        ]
        exp_subs = [
            ('32768', 'LD H,0', 'Clear H'),
            ('     ', 'LD L,H', 'Clear L')
        ]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_prepend_instruction_with_comment_continuation_line(self):
        skool = """
            @start
            ; Routine
            @{0}=>LD H,0  ; Clear the
            @{0}=>        ; H register
            c32768 LD L,H ; Clear L
        """
        exp_instructions = [
            ('32768', 'LD L,H', 'Clear L')
        ]
        exp_subs = [
            ('     ', 'LD H,0', 'Clear the H register'),
            ('32768', 'LD L,H', 'Clear L')
        ]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_append_instruction_with_comment_continuation_line(self):
        skool = """
            @start
            ; Routine
            @{0}=+LD L,H  ; Clear the
            @{0}=         ; L register
            c32768 LD H,0 ; Clear H
        """
        exp_instructions = [
            ('32768', 'LD H,0', 'Clear H')
        ]
        exp_subs = [
            ('32768', 'LD H,0', 'Clear H'),
            ('     ', 'LD L,H', 'Clear the L register')
        ]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_prepend_two_instructions(self):
        skool = """
            @start
            ; Routine
            @{0}=>LD H,0  ; Clear H
            @{0}=>XOR A   ; Clear A
            c32768 LD L,H ; Clear L
        """
        exp_instructions = [
            ('32768', 'LD L,H', 'Clear L')
        ]
        exp_subs = [
            ('     ', 'LD H,0', 'Clear H'),
            ('     ', 'XOR A', 'Clear A'),
            ('32768', 'LD L,H', 'Clear L')
        ]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_append_two_instructions(self):
        skool = """
            @start
            ; Routine
            @{0}=+LD L,H  ; Clear L
            @{0}=XOR A    ; Clear A
            c32768 LD H,0 ; Clear H
        """
        exp_instructions = [
            ('32768', 'LD H,0', 'Clear H')
        ]
        exp_subs = [
            ('32768', 'LD H,0', 'Clear H'),
            ('     ', 'LD L,H', 'Clear L'),
            ('     ', 'XOR A', 'Clear A')
        ]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_prepend_instruction_and_replace_instruction(self):
        skool = """
            @start
            ; Routine
            @{0}=>LD H,0  ; Clear H
            @{0}=LD L,H   ; And L
            @{0}=         ; likewise
            c32768 LD L,0 ; Clear L
        """
        exp_instructions = [
            ('32768', 'LD L,0', 'Clear L')
        ]
        exp_subs = [
            ('     ', 'LD H,0', 'Clear H'),
            ('32768', 'LD L,H', 'And L likewise')
        ]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_prepend_and_replace_and_append(self):
        skool = """
            @start
            ; Routine
            @{0}=>LD H,0  ; Clear H
            @{0}=LD L,H   ; And L likewise
            @{0}=XOR A    ; And A too
            c32768 LD L,0 ; Clear L
        """
        exp_instructions = [
            ('32768', 'LD L,0', 'Clear L')
        ]
        exp_subs = [
            ('     ', 'LD H,0', 'Clear H'),
            ('32768', 'LD L,H', 'And L likewise'),
            ('     ', 'XOR A', 'And A too')
        ]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_prepend_and_append(self):
        skool = """
            @start
            ; Routine
            @{0}=>LD H,0  ; Clear H
            @{0}=+XOR A   ; And A too
            c32768 LD L,0 ; Clear L
        """
        exp_instructions = [
            ('32768', 'LD L,0', 'Clear L')
        ]
        exp_subs = [
            ('     ', 'LD H,0', 'Clear H'),
            ('32768', 'LD L,0', 'Clear L'),
            ('     ', 'XOR A', 'And A too')
        ]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_prepended_instruction_adopts_mid_block_comment(self):
        skool = """
            @start
            ; Routine
            c32768 LD L,0 ; Clear L
            ; Continue.
            @{0}=>XOR A   ; Clear A
             32770 LD H,A ; And now H
        """
        def func(parser):
            instructions = parser.get_entry(32768).instructions
            self.assertEqual(['Continue.'], instructions[1].mid_block_comment)
            self.assertIsNone(instructions[2].mid_block_comment)
        self._assert_sub_and_fix_directives(skool, func)

    def test_sub_and_fix_directives_append_instruction_before_mid_block_comment(self):
        skool = """
            @start
            ; Routine
            @{0}=+XOR A   ; Clear A
            c32768 LD L,0 ; Clear L
            ; Continue.
             32770 LD H,A ; And now H
        """
        def func(parser):
            instructions = parser.get_entry(32768).instructions
            self.assertIsNone(instructions[1].mid_block_comment)
            self.assertEqual(['Continue.'], instructions[2].mid_block_comment)
        self._assert_sub_and_fix_directives(skool, func)

    def test_sub_and_fix_directives_prepended_instruction_adopts_org(self):
        skool = """
            @start
            @org
            ; Routine
            @{}=>LD H,0
            c32768 LD L,H
        """
        def func(parser):
            instructions = parser.get_entry(32768).instructions
            self.assertEqual(instructions[0].org, '32768')
            self.assertEqual(instructions[1].org, '32768')
        self._assert_sub_and_fix_directives(skool, func)

    def test_sub_and_fix_directives_prepend_instruction_without_overriding_comment_continuation_lines(self):
        skool = """
            @start
            ; Routine
            @{0}=>INC HL
            c32768 LD (HL),0 ; Clear the contents
                             ; of (HL)
        """
        exp_instructions = [
            ('32768', 'LD (HL),0', 'Clear the contents of (HL)')
        ]
        exp_subs = [
            ('     ', 'INC HL', ''),
            ('32768', 'LD (HL),0', 'Clear the contents of (HL)'),
        ]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_append_instruction_without_overriding_comment_continuation_lines(self):
        skool = """
            @start
            ; Routine
            @{}=+INC HL
            c32768 LD (HL),0 ; Clear the contents
                             ; of (HL)
        """
        exp_instructions = [
            ('32768', 'LD (HL),0', 'Clear the contents of (HL)')
        ]
        exp_subs = [
            ('32768', 'LD (HL),0', 'Clear the contents of (HL)'),
            ('     ', 'INC HL', '')
        ]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_prepend_instruction_cleanly(self):
        skool = """
            @start
            ; Routine
            @keep
            @ignoreua
            @label=START
            @nowarn
            @{}=>LD H,0
            c32768 LD L,H
        """
        def func(parser):
            instructions = parser.get_entry(32768).instructions
            inst1 = instructions[0]
            inst2 = instructions[1]
            self.assertIsNone(inst1.keep)
            self.assertFalse(inst1.ignoreua)
            self.assertIsNone(inst1.asm_label)
            self.assertIsNone(inst1.org)
            self.assertTrue(inst1.warn)
            self.assertEqual([], inst2.keep)
            self.assertTrue(inst2.ignoreua)
            self.assertEqual(inst2.asm_label, 'START')
            self.assertIsNone(inst2.org)
            self.assertFalse(inst2.warn)
        self._assert_sub_and_fix_directives(skool, func)

    def test_sub_and_fix_directives_replace_label(self):
        skool = """
            @start
            @label=BEGIN
            @{}=START:XOR A
            c32768 XOR A ; Clear A
        """
        exp_instructions = [('BEGIN', '32768', 'XOR A', 'Clear A')]
        exp_subs = [('START', '32768', 'XOR A', 'Clear A')]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_replace_label_and_comment_only(self):
        skool = """
            @start
            @label=BEGIN
            @{}=START:   ; A=0
            c32768 XOR A ; Clear A
        """
        exp_instructions = [('BEGIN', '32768', 'XOR A', 'Clear A')]
        exp_subs = [('START', '32768', 'XOR A', 'A=0')]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_do_not_add_auto_label(self):
        skool = """
            @start
            c32768 JR 32770
            ; This should not set an auto-label, because we're not creating
            ; default labels.
            @{}=*:
             32770 RET ; Done
        """
        exp_instructions = [
            (None, '32768', 'JR 32770', ''),
            (None, '32770', 'RET', 'Done')
        ]
        exp_subs = exp_instructions
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_add_default_auto_label(self):
        skool = """
            @start
            c32768 JR 32770
            @{}=*:
             32770 RET ; Done
        """
        exp_instructions = [
            ('L32768', '32768', 'JR 32770', ''),
            (None, '32770', 'RET', 'Done')
        ]
        exp_subs = [
            ('L32768', '32768', 'JR L32768_0', ''),
            ('L32768_0', '32770', 'RET', 'Done')
        ]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs, create_labels=True)

    def test_sub_and_fix_directives_add_auto_label(self):
        skool = """
            @start
            @label=BEGIN
            c32768 XOR A ; Clear A
            @{}=*:
             32769 INC A ; A=1
        """
        exp_instructions = [
            ('BEGIN', '32768', 'XOR A', 'Clear A'),
            (None, '32769', 'INC A', 'A=1')
        ]
        exp_subs = [
            ('BEGIN', '32768', 'XOR A', 'Clear A'),
            ('BEGIN_0', '32769', 'INC A', 'A=1')
        ]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_add_two_auto_labels(self):
        skool = """
            @start
            @label=BEGIN
            c32768 XOR A ; Clear A
            @{0}=*:
             32769 INC A ; A=1
            @{0}=*:
             32770 RET ; Finished
        """
        exp_instructions = [
            ('BEGIN', '32768', 'XOR A', 'Clear A'),
            (None, '32769', 'INC A', 'A=1'),
            (None, '32770', 'RET', 'Finished')
        ]
        exp_subs = [
            ('BEGIN', '32768', 'XOR A', 'Clear A'),
            ('BEGIN_0', '32769', 'INC A', 'A=1'),
            ('BEGIN_1', '32770', 'RET', 'Finished')
        ]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_add_same_label_twice(self):
        skool = """
            @start
            @{0}=SAME:
            c32768 XOR A
            @{0}=SAME:
             32769 RET
        """
        exp_error = "Duplicate label SAME at 32769"
        self._assert_sub_and_fix_directives(skool, exp_error=exp_error)

    def test_sub_and_fix_directives_add_duplicate_label(self):
        skool = """
            @start
            @label=SAME
            c32768 XOR A
            @{}=SAME:
             32769 RET
        """
        exp_error = "Duplicate label SAME at 32769"
        self._assert_sub_and_fix_directives(skool, exp_error=exp_error)

    def test_sub_and_fix_directives_add_label_with_entry_point_marker(self):
        skool = """
            @start
            @label=BEGIN
            c32768 XOR A ; Clear A
            @{}=*END:
             32769 RET   ; Done
        """
        exp_instructions = [
            ('BEGIN', '32768', 'XOR A', 'Clear A'),
            (None, '32769', 'RET', 'Done')
        ]
        exp_subs = [
            ('BEGIN', '32768', 'XOR A', 'Clear A'),
            ('END', '32769', 'RET', 'Done')
        ]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_add_duplicate_label_with_entry_point_marker(self):
        skool = """
            @start
            @label=SAME
            c32768 XOR A ; Clear A
            @{}=*SAME:
             32769 RET   ; Done
        """
        exp_error = "Duplicate label SAME at 32769"
        self._assert_sub_and_fix_directives(skool, exp_error=exp_error)

    def test_sub_and_fix_directives_remove_label(self):
        skool = """
            @start
            @label=BEGIN
            @{}=:XOR A
            c32768 XOR A ; Clear A
        """
        exp_instructions = [('BEGIN', '32768', 'XOR A', 'Clear A')]
        exp_subs = [('', '32768', 'XOR A', 'Clear A')]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_remove_two_labels(self):
        skool = """
            @start
            @label=BEGIN
            @{0}=:XOR A
            c32768 XOR A ; Clear A
            @label=END
            @{0}=:
             32769 RET   ; Done
        """
        exp_instructions = [
            ('BEGIN', '32768', 'XOR A', 'Clear A'),
            ('END', '32769', 'RET', 'Done')
        ]
        exp_subs = [
            ('', '32768', 'XOR A', 'Clear A'),
            ('', '32769', 'RET', 'Done')
        ]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_remove_auto_label(self):
        skool = """
            @start
            @label=BEGIN
            c32768 XOR A ; Clear A
            @{}=:
            *32769 INC A ; A=1
        """
        exp_instructions = [
            ('BEGIN', '32768', 'XOR A', 'Clear A'),
            ('BEGIN_0', '32769', 'INC A', 'A=1')
        ]
        exp_subs = [
            ('BEGIN', '32768', 'XOR A', 'Clear A'),
            ('', '32769', 'INC A', 'A=1')
        ]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_define_label_for_added_instruction(self):
        skool = """
            @start
            @{0}=|XOR A
            @{0}=|ADD1 : INC A
            c32768 LD A,0 ; Clear A
        """
        exp_instructions = [(None, '32768', 'LD A,0', 'Clear A')]
        exp_subs = [
            (None, '32768', 'XOR A', 'Clear A'),
            ('ADD1', '32769', 'INC A', '')
        ]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_define_auto_label_for_added_instruction(self):
        skool = """
            @start
            @label=START
            @{0}=|XOR A
            @{0}=|*: INC A
            c32768 LD A,0 ; Clear A
        """
        exp_instructions = [('START', '32768', 'LD A,0', 'Clear A')]
        exp_subs = [
            ('START', '32768', 'XOR A', 'Clear A'),
            ('START_0', '32769', 'INC A', '')
        ]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs, create_labels=True)

    def test_sub_and_fix_directives_prepend_instruction_with_label(self):
        skool = """
            @start
            ; Routine
            @{0}=>START: LD H,0 ; Clear H
            c32768 LD L,H       ; Clear L
        """
        exp_instructions = [
            (None, '32768', 'LD L,H', 'Clear L')
        ]
        exp_subs = [
            ('START', '     ', 'LD H,0', 'Clear H'),
            (None, '32768', 'LD L,H', 'Clear L')
        ]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_append_instruction_with_label(self):
        skool = """
            @start
            ; Routine
            @{}=+START: LD H,L  ; Clear H
            c32768 LD L,0       ; Clear L
        """
        exp_instructions = [
            (None, '32768', 'LD L,0', 'Clear L')
        ]
        exp_subs = [
            (None, '32768', 'LD L,0', 'Clear L'),
            ('START', '     ', 'LD H,L', 'Clear H')
        ]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_remove_instruction(self):
        skool = """
            @start
            c49152 LD A,0
            @{}=!49154
             49154 XOR A
             49155 RET
        """
        exp_instructions = [
            ('49152', 'LD A,0', ''),
            ('49154', 'XOR A', ''),
            ('49155', 'RET', '')
        ]
        exp_subs = [
            ('49152', 'LD A,0', ''),
            ('49155', 'RET', '')
        ]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_remove_instructions_in_range(self):
        skool = """
            @start
            c49152 LD A,0
            @{}=!49154-49155
             49154 XOR A
             49155 OR A
             49156 RET
        """
        exp_instructions = [
            ('49152', 'LD A,0', ''),
            ('49154', 'XOR A', ''),
            ('49155', 'OR A', ''),
            ('49156', 'RET', '')
        ]
        exp_subs = [
            ('49152', 'LD A,0', ''),
            ('49156', 'RET', '')
        ]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_remove_instructions_with_hex_addresses(self):
        skool = """
            @start
            c49152 LD A,0
            @{}=!$C002-$c003
             49154 XOR A
             49155 OR A
             49156 RET
        """
        exp_instructions = [
            ('49152', 'LD A,0', ''),
            ('49154', 'XOR A', ''),
            ('49155', 'OR A', ''),
            ('49156', 'RET', '')
        ]
        exp_subs = [
            ('49152', 'LD A,0', ''),
            ('49156', 'RET', '')
        ]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_remove_entire_entry(self):
        skool = """
            @start
            @{}=!49152-49155
            c49152 LD A,0
             49154 XOR A
             49155 RET

            ; Data
            b49156 DEFB 0
        """
        def func(parser):
            self.assertIsNone(parser.get_entry(49152))
            self.assertIsNotNone(parser.get_entry(49156))
        self._assert_sub_and_fix_directives(skool, func)

    def test_sub_and_fix_directives_remove_current_entry_only(self):
        skool = """
            @start
            @{0}=!30000
            c30000 RET

            @{0}+begin
            b30000 DEFB 201
            @{0}+end
        """
        exp_instructions = [('30000', 'RET', '')]
        exp_subs = [('30000', 'DEFB 201', '')]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_discard_label_on_removed_instruction(self):
        skool = """
            @start
            @{0}=!30000
            @label=START
            c30000 RET

            @{0}+begin
            @label=START
            c30001 RET Z
            @{0}+end
        """
        exp_instructions = [('START', '30000', 'RET', '')]
        exp_subs = [('START', '30001', 'RET Z', '')]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_sub_and_fix_directives_retain_start_comment_on_removed_instruction(self):
        skool = """
            @start
            ; Routine
            ;
            ; .
            ;
            ; .
            ;
            ; Start.
            @{}=!30000
            c30000 XOR A
             30001 RET
        """
        func = lambda p: self.assertEqual(['Start.'], p.get_instruction(30001).mid_block_comment)
        self._assert_sub_and_fix_directives(skool, func)

    def test_sub_and_fix_directives_retain_mid_block_comment_on_removed_instruction(self):
        skool = """
            @start
            c30000 XOR A
            ; Continue.
            @{}=!30001
             30001 INC A
             30002 RET
        """
        func = lambda p: self.assertEqual(['Continue.'], p.get_instruction(30002).mid_block_comment)
        self._assert_sub_and_fix_directives(skool, func)

    def test_sub_and_fix_directives_drop_mid_block_comment_on_removed_instruction_at_end_of_entry(self):
        skool = """
            @start
            c30000 XOR A
            ; Continue.
            @{}=!30001
             30001 RET

            c30002 LD A,B
        """
        func = lambda p: self.assertEqual([], p.get_instruction(30002).mid_block_comment)
        self._assert_sub_and_fix_directives(skool, func)

    def test_sub_and_fix_directives_drop_mid_block_comment_on_removed_instruction_when_next_instruction_has_one(self):
        skool = """
            @start
            c30000 XOR A
            ; This comment should disappear...
            @{}=!30001
             30001 INC A
            ; ...and leave this one alone
             30002 RET
        """
        func = lambda p: self.assertEqual(['...and leave this one alone'], p.get_instruction(30002).mid_block_comment)
        self._assert_sub_and_fix_directives(skool, func)

    def test_sub_and_fix_directives_remove_added_instructions(self):
        skool = """
            @start
            @{0}=!30001-30002
            c30000 LD A,B
            @{1}=|CPL
            @{1}=|INC A
             30001 NEG
             30003 RET
        """
        for sub_mode, fix_mode, asm_dirs in (
                (2, 0, ('ssub', 'isub')),
                (3, 1, ('rsub', 'ssub')),
                (1, 2, ('bfix', 'ofix')),
                (3, 3, ('rfix', 'bfix'))
        ):
            with self.subTest(sub_mode=sub_mode, fix_mode=fix_mode, asm_dirs=asm_dirs):
                parser = self._get_parser(skool.format(*asm_dirs), asm_mode=sub_mode, fix_mode=fix_mode)
                instructions = parser.get_entry(30000).instructions
                self.assertEqual(len(instructions), 2)
                self.assertEqual(instructions[0].operation, 'LD A,B')
                self.assertEqual(instructions[1].operation, 'RET')

    def test_sub_and_fix_directives_ignore_invalid_removal_address_range(self):
        skool = """
            @start
            @{0}=!4000x
            b40000 DEFB 0
            @{0}=!40001-4000?
             40001 DEFB 1
             40002 DEFB 2
        """
        exp_instructions = exp_subs = [
            ('40000', 'DEFB 0', ''),
            ('40001', 'DEFB 1', ''),
            ('40002', 'DEFB 2', '')
        ]
        self._test_sub_and_fix_directives(skool, exp_instructions, exp_subs)

    def test_no_asm_labels(self):
        skool = """
            @label=START
            c49152 RET
        """
        parser = self._get_parser(skool, asm_labels=False)
        self.assertIsNone(parser.get_instruction(49152).asm_label)

    def test_html_mode_label(self):
        label = 'START'
        skool = """
            ; Routine
            @label={}
            c49152 LD BC,0
             49155 RET
        """.format(label)
        parser = self._get_parser(skool, html=True, asm_labels=True)
        entry = parser.get_entry(49152)
        self.assertEqual(entry.instructions[0].asm_label, label)
        self.assertIsNone(entry.instructions[1].asm_label)

    def test_html_mode_keep(self):
        skool = """
            ; Routine
            c40000 LD HL,40006
            @keep
             40003 LD DE,40006

            ; Another routine
            c40006 RET
        """
        parser = self._get_parser(skool, html=True)
        entry = parser.get_entry(40000)
        self.assertFalse(entry.instructions[0].keep_values())
        self.assertTrue(entry.instructions[1].keep_values())
        self.assertIsNone(entry.instructions[1].reference)

    def test_html_mode_keep_with_one_value(self):
        skool = """
            ; Routine
            @keep=40003
            c40000 LD HL,40003

            ; Another routine
            c40003 RET
        """
        parser = self._get_parser(skool, html=True)
        entry = parser.get_entry(40000)
        self.assertTrue(entry.instructions[0].keep_value(40003))
        self.assertIsNone(entry.instructions[0].reference)

    def test_html_mode_keep_with_one_unused_value(self):
        skool = """
            ; Routine
            @keep=40004
            c40000 LD HL,40003

            ; Another routine
            c40003 RET
        """
        parser = self._get_parser(skool, html=True)
        entry = parser.get_entry(40000)
        self.assertFalse(entry.instructions[0].keep_value(40003))
        self.assertIsNotNone(entry.instructions[0].reference)

    def test_html_mode_rem(self):
        skool = """
            ; Routine
            ;
            @rem=These comments
            @rem=should be ignored.
            ; Foo.
            @rem=And these
            @rem=ones too.
            c50000 RET
        """
        parser = self._get_parser(skool, html=True)
        entry = parser.get_entry(50000)
        self.assertEqual(entry.details, ['Foo.'])

    def test_html_mode_ssub_directive(self):
        skool = """
            ; Routine
            @ssub=INC DE
            c50000 INC E
        """
        parser = self._get_parser(skool, html=True)
        instruction = parser.get_entry(50000).instructions[0]
        self.assertEqual(instruction.operation, 'INC E')

    def test_html_mode_ssub_block_directive(self):
        skool = """
            ; Routine
            @ssub-begin
            c50000 LD L,24 ; 24 is the LSB
            @ssub+else
            c50000 LD L,50003%256 ; This is the LSB
            @ssub+end
             50002 RET
        """
        parser = self._get_parser(skool, html=True)
        instruction = parser.get_entry(50000).instructions[0]
        self.assertEqual(instruction.operation, 'LD L,24')
        self.assertEqual(instruction.comment.text, '24 is the LSB')

    def test_asm_mode_assemble(self):
        skool = """
            @start
            c24000 XOR A
             24001 DEFB 1
            @assemble=,1
             24002 XOR B
             24003 DEFB 2
            @assemble=,2
             24004 XOR C
             24005 DEFB 3
        """
        snapshot = self._get_parser(skool, asm_mode=1).snapshot
        self.assertEqual([0, 0, 0, 2, 169, 3], snapshot[24000:24006])

    def test_asm_mode_assemble_missing_or_bad_value(self):
        skool = """
            @start
            @assemble=,2
            c24000 XOR A
            @assemble=1
             24001 XOR B
            @assemble=1,
             24002 XOR C
            @assemble=1,x
             24003 XOR D
        """
        snapshot = self._get_parser(skool, asm_mode=1).snapshot
        self.assertEqual([175, 168, 169, 170], snapshot[24000:24004])

    def test_html_mode_assemble(self):
        skool = """
            c30000 XOR A
             30001 DEFB 1
            @assemble=2
             30002 XOR B
             30003 DEFB 2
            @assemble=0
             30004 XOR C
             30005 DEFB 3
        """
        snapshot = self._get_parser(skool, html=True).snapshot
        self.assertEqual([0, 1, 168, 2, 0, 0], snapshot[30000:30006])

    def test_html_mode_assemble_missing_or_bad_value(self):
        skool = """
            @assemble=2
            c40000 XOR A
            @assemble=off
             40001 XOR B
            @assemble=1
             40002 XOR C
            @assemble=on,0
             40003 XOR D
            @assemble=,2
             40004 XOR E
        """
        snapshot = self._get_parser(skool, html=True).snapshot
        self.assertEqual([175, 168, 0, 0, 0], snapshot[40000:40005])

    def test_asm_mode_rem(self):
        skool = """
            @start
            ; Routine
            ;
            @rem=These comments
            @rem=should be ignored.
            ; Foo.
            @rem=And these
            @rem=ones too.
            c50000 RET
        """
        parser = self._get_parser(skool, asm_mode=1)
        entry = parser.get_entry(50000)
        self.assertEqual(entry.details, ['Foo.'])

    def test_fix_mode_0(self):
        skool = """
            @start
            ; Let's test some @ofix directives
            c24593 NOP
            @ofix=LD A,C
             24594 LD A,B
            @ofix-begin
             24595 LD B,A
            @ofix+else
             24595 LD B,C
            @ofix+end

            ; Let's test some @bfix directives
            c24596 NOP
            @bfix=LD C,B
             24597 LD C,A
            @bfix-begin
             24598 LD D,A
            @bfix+else
             24598 LD D,B
            @bfix+end

            ; Let's test some @rfix directives
            c24599 NOP
            @rfix=LD E,B
             24600 LD E,A
            @rfix-begin
             24601 LD H,A
            @rfix+else
             24601 LD H,B
            @rfix+end
        """
        parser = self._get_parser(skool, asm_mode=1, fix_mode=0)
        instructions = parser.get_entry(24593).instructions
        self.assertEqual(instructions[1].operation, 'LD A,B')
        self.assertEqual(instructions[2].operation, 'LD B,A')
        instructions = parser.get_entry(24596).instructions
        self.assertEqual(instructions[1].operation, 'LD C,A')
        self.assertEqual(instructions[2].operation, 'LD D,A')
        instructions = parser.get_entry(24599).instructions
        self.assertEqual(instructions[1].operation, 'LD E,A')
        self.assertEqual(instructions[2].operation, 'LD H,A')

    def test_fix_mode_1(self):
        skool = """
            @start
            ; Let's test some @ofix directives
            c24593 NOP
            @ofix=LD A,C
             24594 LD A,B
            @ofix-begin
             24595 LD B,A
            @ofix+else
             24595 LD B,C
            @ofix+end

            ; Let's test some @bfix directives
            c24596 NOP
            @bfix=LD C,B
             24597 LD C,A
            @bfix-begin
             24598 LD D,A
            @bfix+else
             24598 LD D,B
            @bfix+end

            ; Let's test some @rfix directives
            c24599 NOP
            @rfix=LD E,B
             24600 LD E,A
            @rfix-begin
             24601 LD H,A
            @rfix+else
             24601 LD H,B
            @rfix+end
        """
        parser = self._get_parser(skool, asm_mode=1, fix_mode=1)
        instructions = parser.get_entry(24593).instructions
        self.assertEqual(instructions[1].operation, 'LD A,C')
        self.assertEqual(instructions[2].operation, 'LD B,C')
        instructions = parser.get_entry(24596).instructions
        self.assertEqual(instructions[1].operation, 'LD C,A')
        self.assertEqual(instructions[2].operation, 'LD D,A')
        instructions = parser.get_entry(24599).instructions
        self.assertEqual(instructions[1].operation, 'LD E,A')
        self.assertEqual(instructions[2].operation, 'LD H,A')

    def test_fix_mode_2(self):
        skool = """
            @start
            ; Let's test some @ofix directives
            c24593 NOP
            @ofix=LD A,C
             24594 LD A,B
            @ofix-begin
             24595 LD B,A
            @ofix+else
             24595 LD B,C
            @ofix+end

            ; Let's test some @bfix directives
            c24596 NOP
            @bfix=LD C,B
             24597 LD C,A
            @bfix-begin
             24598 LD D,A
            @bfix+else
             24598 LD D,B
            @bfix+end

            ; Let's test some @rfix directives
            c24599 NOP
            @rfix=LD E,B
             24600 LD E,A
            @rfix-begin
             24601 LD H,A
            @rfix+else
             24601 LD H,B
            @rfix+end
        """
        parser = self._get_parser(skool, asm_mode=1, fix_mode=2)
        instructions = parser.get_entry(24593).instructions
        self.assertEqual(instructions[1].operation, 'LD A,C')
        self.assertEqual(instructions[2].operation, 'LD B,C')
        instructions = parser.get_entry(24596).instructions
        self.assertEqual(instructions[1].operation, 'LD C,B')
        self.assertEqual(instructions[2].operation, 'LD D,B')
        instructions = parser.get_entry(24599).instructions
        self.assertEqual(instructions[1].operation, 'LD E,A')
        self.assertEqual(instructions[2].operation, 'LD H,A')

    def test_fix_mode_3(self):
        skool = """
            @start
            ; Let's test some @ofix directives
            c24593 NOP
            @ofix=LD A,C
             24594 LD A,B
            @ofix-begin
             24595 LD B,A
            @ofix+else
             24595 LD B,C
            @ofix+end

            ; Let's test some @bfix directives
            c24596 NOP
            @bfix=LD C,B
             24597 LD C,A
            @bfix-begin
             24598 LD D,A
            @bfix+else
             24598 LD D,B
            @bfix+end

            ; Let's test some @rfix directives
            c24599 NOP
            @rfix=LD E,B
             24600 LD E,A
            @rfix-begin
             24601 LD H,A
            @rfix+else
             24601 LD H,B
            @rfix+end
        """
        parser = self._get_parser(skool, asm_mode=3, fix_mode=3)
        instructions = parser.get_entry(24593).instructions
        self.assertEqual(instructions[1].operation, 'LD A,C')
        self.assertEqual(instructions[2].operation, 'LD B,C')
        instructions = parser.get_entry(24596).instructions
        self.assertEqual(instructions[1].operation, 'LD C,B')
        self.assertEqual(instructions[2].operation, 'LD D,B')
        instructions = parser.get_entry(24599).instructions
        self.assertEqual(instructions[1].operation, 'LD E,B')
        self.assertEqual(instructions[2].operation, 'LD H,B')

    def test_bfix_block_directive_spanning_two_entries_fix_mode_0(self):
        skool = """
            @start
            ; Data
            b32768 DEFB 1
            @bfix-begin
             32769 DEFB 2

            ; Unused
            u32770 DEFB 0
            @bfix+else
             32769 DEFB 4
             32770 DEFB 8
            @bfix+end
        """
        parser = self._get_parser(skool, asm_mode=1)
        memory_map = parser.memory_map
        self.assertEqual(len(memory_map), 2)
        instructions = memory_map[0].instructions
        self.assertEqual(len(instructions), 2)
        self.assertEqual(instructions[1].operation, 'DEFB 2')
        instructions = memory_map[1].instructions
        self.assertEqual(len(instructions), 1)
        self.assertEqual(instructions[0].operation, 'DEFB 0')

    def test_bfix_block_directive_spanning_two_entries_fix_mode_2(self):
        skool = """
            @start
            ; Data
            b32768 DEFB 1
            @bfix-begin
             32769 DEFB 2

            ; Unused
            u32770 DEFB 0
            @bfix+else
             32769 DEFB 4
             32770 DEFB 8
            @bfix+end
        """
        parser = self._get_parser(skool, asm_mode=1, fix_mode=2)
        memory_map = parser.memory_map
        self.assertEqual(len(memory_map), 1)
        instructions = memory_map[0].instructions
        self.assertEqual(len(instructions), 3)
        self.assertEqual(instructions[1].operation, 'DEFB 4')
        self.assertEqual(instructions[2].operation, 'DEFB 8')

    def test_rsub_minus_inside_rsub_minus(self):
        # @rsub-begin inside @rsub- block
        skool = """
            @start
            @rsub-begin
            @rsub-begin
            @rsub-end
            @rsub-end
        """
        error = "rsub-begin inside rsub- block"
        self.assert_error(skool, error, asm_mode=1)

    def test_isub_plus_inside_bfix_plus(self):
        # @isub+else inside @bfix+ block
        skool = """
            @start
            @bfix+begin
            @isub+else
            @isub+end
            @bfix+end
        """
        error = "isub\+else inside bfix\+ block"
        self.assert_error(skool, error, asm_mode=1)

    def test_dangling_ofix_else(self):
        # Dangling @ofix+else directive
        skool = """
            @start
            @ofix+else
            @ofix+end
        """
        error = "ofix\+else not inside block"
        self.assert_error(skool, error, asm_mode=1)

    def test_dangling_rfix_end(self):
        # Dangling @rfix+end directive
        skool = '@start\n@rfix+end'
        error = "rfix\+end has no matching start directive"
        self.assert_error(skool, error, asm_mode=1)

    def test_wrong_end_infix(self):
        # Mismatched begin/else/end (wrong infix)
        skool = """
            @start
            @rsub+begin
            @rsub-else
            @rsub+end
        """
        error = "rsub\+end cannot end rsub- block"
        self.assert_error(skool, error, asm_mode=1)

    def test_mismatched_begin_end(self):
        # Mismatched begin/end (different directive)
        skool = """
            @start
            @ofix-begin
            @bfix-end
        """
        error = "bfix-end cannot end ofix- block"
        self.assert_error(skool, error, asm_mode=1)

    def test_min_address(self):
        skool = """
            b30000 DEFB 0

            b30001 DEFB 1

            b30002 DEFB 2
        """
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
        skool = """
            b40000 DEFB 0
             40001 DEFB 1
             40002 DEFB 2

            b40003 DEFB 3
        """
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
        skool = """
            @start
            c32768 LD A,B
            @rsub+begin
                   INC A   ; This instruction should be retained
            @rsub+end
             32770 RET
        """
        parser = self._get_parser(skool, asm_mode=3, min_address=32768)
        instructions = parser.get_entry(32768).instructions
        self.assertEqual(len(instructions), 3)
        self.assertEqual(instructions[1].operation, 'INC A')
        self.assertEqual(instructions[1].comment.text, 'This instruction should be retained')

    def test_max_address(self):
        skool = """
            b30000 DEFB 0

            b30001 DEFB 1

            b30002 DEFB 2
        """
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
        skool = """
            b40000 DEFB 0

            b40001 DEFB 1
             40002 DEFB 2
             40003 DEFB 3

            b40004 DEFB 4
        """
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
        skool = """
            @start
            c32768 LD A,B
            @rsub+begin
                   INC A   ; This instruction should be retained
            @rsub+end
             32770 RET
        """
        parser = self._get_parser(skool, asm_mode=3, max_address=32771)
        instructions = parser.get_entry(32768).instructions
        self.assertEqual(len(instructions), 3)
        self.assertEqual(instructions[1].operation, 'INC A')
        self.assertEqual(instructions[1].comment.text, 'This instruction should be retained')

    def test_min_and_max_address(self):
        skool = """
            b40000 DEFB 0

            b40001 DEFB 1

            b40002 DEFB 2

            b40003 DEFB 3
        """
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
        skool = """
            b40000 DEFB 0
             40001 DEFB 1

            b40002 DEFB 2
        """
        parser = self._get_parser(skool, min_address=40001, max_address=40002)
        self.assertEqual(len(parser.memory_map), 0)
        self.assertIsNone(parser.get_entry(40000))
        self.assertIsNone(parser.get_entry(40002))
        self.assertIsNone(parser.get_instruction(40000))
        self.assertIsNone(parser.get_instruction(40001))
        self.assertIsNone(parser.get_instruction(40002))

    def test_duplicate_instruction_addresses(self):
        skool = """
            c32768 LD A,10
             32770 LD B,11  ; Comment 1
            ; First the instruction at 32772 looks like this.
             32772 LD HL,0  ; Comment 2
            ; Then it looks like this.
             32772 LD BC,0  ; Comment 3
            ; And then 32770 onwards looks like this.
             32770 LD C,12  ; Comment 4
             32772 RET
        """
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

    def test_clone(self):
        skool = 'b40000 DEFB 1,2,3,4,5,6,7,8'
        parser = self._get_parser(skool, html=True, variables=('foo=1', 'bar=2'))
        skool2 = 'b40002 DEFB 9,10,11,12'
        skool2file = self.write_text_file(skool2, suffix='.skool')
        clone = parser.clone(skool2file)
        self.assertEqual(parser.case, clone.case)
        self.assertEqual(parser.base, clone.base)
        self.assertEqual(parser.mode.asm_mode, clone.mode.asm_mode)
        self.assertEqual(parser.mode.warn, clone.mode.warn)
        self.assertEqual(parser.mode.fix_mode, clone.mode.fix_mode)
        self.assertEqual(parser.mode.html, clone.mode.html)
        self.assertEqual(parser.mode.create_labels, clone.mode.create_labels)
        self.assertEqual(parser.mode.asm_labels, clone.mode.asm_labels)
        self.assertEqual([1, 2, 3, 4, 5, 6, 7, 8], parser.snapshot[40000:40008])
        self.assertEqual([1, 2, 9, 10, 11, 12, 7, 8], clone.snapshot[40000:40008])
        self.assertEqual(parser.fields, clone.fields)

class TableParserTest(SkoolKitTestCase):
    class MockWriter:
        def expand(self, text):
            return text
    mock_writer = MockWriter()

    def assert_error(self, text, error):
        with self.assertRaises(SkoolParsingError) as cm:
            TableParser().parse_text(self.mock_writer, text, 0)
        self.assertEqual(cm.exception.args[0], error)

    def test_invalid_colspan_indicator(self):
        self.assert_error('#TABLE { =cX Hi } TABLE#', "Invalid colspan indicator: 'cX'")

    def test_invalid_rowspan_indicator(self):
        self.assert_error('#TABLE { =rY Hi } TABLE#', "Invalid rowspan indicator: 'rY'")
