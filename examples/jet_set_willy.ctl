;
; SkoolKit control file for Jet Set Willy.
;
; Room descriptions based on reference material from Andrew Broad
; <http://webspace.webring.com/people/ja/andrewbroad/> and J. G. Harston
; <http://mdfs.net/Software/JSW/Docs/>.
;
; To build the HTML disassembly, create a z80 snapshot of Jet Set Willy named
; jsw.z80, and run these commands from the top-level SkoolKit directory:
;   ./sna2skool.py -c examples/jet_set_willy.ctl jsw.z80 > jet_set_willy.skool
;   ./skool2html.py examples/jet_set_willy.ref
;
b 32768 Room buffer
Z 32768,256
b 33024 Guardian buffer
Z 33024,64
B 33088 Terminator
z 33089
w 33280 Screen buffer address lookup table
W 33280,256,16
b 33536 Rope animation table
B 33536,256,16
c 33792 Start
b 33824 Current room number
b 33825 Conveyor data
b 33841 Triangle UDGs
D 33841 #UDGTABLE { #UDG33841,56(triangle0) | #UDG33849,56(triangle1) | #UDG33857,56(triangle2) | #UDG33865,56(triangle3) } TABLE#
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
z 38680
b 38912 Attributes for the top two-thirds of the title screen
B 38912,512,16
b 39424 Attributes for the bottom third of the screen during gameplay
B 39424,256,16
b 39680 Number key graphics
D 39680 #UDGTABLE { #UDGARRAY2,56,,2;39680-39697-1-16(number_key0) | #UDGARRAY2,56,,2;39712-39729-1-16(number_key1) | #UDGARRAY2,56,,2;39744-39761-1-16(number_key2) | #UDGARRAY2,56,,2;39776-39793-1-16(number_key3) } TABLE#
B 39680,128,16
b 39808 Attributes for the password screen
B 39808,128,16
u 39936
B 39936,64,16
b 40000 Foot/barrel graphic data
D 40000 #UDGTABLE { #UDGARRAY2,56,,2;40000-40017-1-16(fb0) | #UDGARRAY2,56,,2;40032-40049-1-16(fb1) } TABLE#
B 40000,64,16
b 40064 Maria sprite graphic data
D 40064 #UDGTABLE { #UDGARRAY2,56,,2;40064-40081-1-16(maria0) | #UDGARRAY2,56,,2;40096-40113-1-16(maria1) | #UDGARRAY2,56,,2;40128-40145-1-16(maria2) | #UDGARRAY2,56,,2;40160-40177-1-16(maria3) } TABLE#
B 40064,128,16
b 40192 Willy sprite graphic data
D 40192 #UDGTABLE { #UDGARRAY2,56,,2;40192-40209-1-16(willy0) | #UDGARRAY2,56,,2;40224-40241-1-16(willy1) | #UDGARRAY2,56,,2;40256-40273-1-16(willy2) | #UDGARRAY2,56,,2;40288-40305-1-16(willy3) | #UDGARRAY2,56,,2;40320-40337-1-16(willy4) | #UDGARRAY2,56,,2;40352-40369-1-16(willy5) | #UDGARRAY2,56,,2;40384-40401-1-16(willy6) | #UDGARRAY2,56,,2;40416-40433-1-16(willy7) } TABLE#
B 40192,256,16
b 40448 Password codes
B 40448,256,16
z 40704
b 40960 Guardian definitions
B 40960,1023,8
b 41983 Index of first object
b 41984 Object table
b 42496 Toilet graphics
D 42496 #UDGTABLE { #UDGARRAY2,56,,2;42496-42513-1-16(toilet0) | #UDGARRAY2,56,,2;42528-42545-1-16(toilet1) | #UDGARRAY2,56,,2;42560-42577-1-16(toilet2) | #UDGARRAY2,56,,2;42592-42609-1-16(toilet3) } TABLE#
B 42496,128,16
u 42624
B 42624,128,16
Z 42752
b 43776 Guardian graphics
D 43776 #UDGTABLE { #UDGARRAY2,56,,2;43776-43793-1-16(guardian171_0) | #UDGARRAY2,56,,2;43808-43825-1-16(guardian171_1) | #UDGARRAY2,56,,2;43840-43857-1-16(guardian171_2) | #UDGARRAY2,56,,2;43872-43889-1-16(guardian171_3) | #UDGARRAY2,56,,2;43904-43921-1-16(guardian171_4) | #UDGARRAY2,56,,2;43936-43953-1-16(guardian171_5) | #UDGARRAY2,56,,2;43968-43985-1-16(guardian171_6) | #UDGARRAY2,56,,2;44000-44017-1-16(guardian171_7) } TABLE#
B 43776,256,16
D 44032 #UDGTABLE { #UDGARRAY2,56,,2;44032-44049-1-16(guardian172_0) | #UDGARRAY2,56,,2;44064-44081-1-16(guardian172_1) | #UDGARRAY2,56,,2;44096-44113-1-16(guardian172_2) | #UDGARRAY2,56,,2;44128-44145-1-16(guardian172_3) | #UDGARRAY2,56,,2;44160-44177-1-16(guardian172_4) | #UDGARRAY2,56,,2;44192-44209-1-16(guardian172_5) | #UDGARRAY2,56,,2;44224-44241-1-16(guardian172_6) | #UDGARRAY2,56,,2;44256-44273-1-16(guardian172_7) } TABLE#
B 44032,256,16
D 44288 #UDGTABLE { #UDGARRAY2,56,,2;44288-44305-1-16(guardian173_0) | #UDGARRAY2,56,,2;44320-44337-1-16(guardian173_1) | #UDGARRAY2,56,,2;44352-44369-1-16(guardian173_2) | #UDGARRAY2,56,,2;44384-44401-1-16(guardian173_3) | #UDGARRAY2,56,,2;44416-44433-1-16(guardian173_4) | #UDGARRAY2,56,,2;44448-44465-1-16(guardian173_5) | #UDGARRAY2,56,,2;44480-44497-1-16(guardian173_6) | #UDGARRAY2,56,,2;44512-44529-1-16(guardian173_7) } TABLE#
B 44288,256,16
D 44544 #UDGTABLE { #UDGARRAY2,56,,2;44544-44561-1-16(guardian174_0) | #UDGARRAY2,56,,2;44576-44593-1-16(guardian174_1) | #UDGARRAY2,56,,2;44608-44625-1-16(guardian174_2) | #UDGARRAY2,56,,2;44640-44657-1-16(guardian174_3) | #UDGARRAY2,56,,2;44672-44689-1-16(guardian174_4) | #UDGARRAY2,56,,2;44704-44721-1-16(guardian174_5) | #UDGARRAY2,56,,2;44736-44753-1-16(guardian174_6) | #UDGARRAY2,56,,2;44768-44785-1-16(guardian174_7) } TABLE#
B 44544,256,16
D 44800 #UDGTABLE { #UDGARRAY2,56,,2;44800-44817-1-16(guardian175_0) | #UDGARRAY2,56,,2;44832-44849-1-16(guardian175_1) | #UDGARRAY2,56,,2;44864-44881-1-16(guardian175_2) | #UDGARRAY2,56,,2;44896-44913-1-16(guardian175_3) | #UDGARRAY2,56,,2;44928-44945-1-16(guardian175_4) | #UDGARRAY2,56,,2;44960-44977-1-16(guardian175_5) | #UDGARRAY2,56,,2;44992-45009-1-16(guardian175_6) | #UDGARRAY2,56,,2;45024-45041-1-16(guardian175_7) } TABLE#
B 44800,256,16
D 45056 #UDGTABLE { #UDGARRAY2,56,,2;45056-45073-1-16(guardian176_0) | #UDGARRAY2,56,,2;45088-45105-1-16(guardian176_1) | #UDGARRAY2,56,,2;45120-45137-1-16(guardian176_2) | #UDGARRAY2,56,,2;45152-45169-1-16(guardian176_3) | #UDGARRAY2,56,,2;45184-45201-1-16(guardian176_4) | #UDGARRAY2,56,,2;45216-45233-1-16(guardian176_5) | #UDGARRAY2,56,,2;45248-45265-1-16(guardian176_6) | #UDGARRAY2,56,,2;45280-45297-1-16(guardian176_7) } TABLE#
B 45056,256,16
D 45312 #UDGTABLE { #UDGARRAY2,56,,2;45312-45329-1-16(guardian177_0) | #UDGARRAY2,56,,2;45344-45361-1-16(guardian177_1) | #UDGARRAY2,56,,2;45376-45393-1-16(guardian177_2) | #UDGARRAY2,56,,2;45408-45425-1-16(guardian177_3) | #UDGARRAY2,56,,2;45440-45457-1-16(guardian177_4) | #UDGARRAY2,56,,2;45472-45489-1-16(guardian177_5) | #UDGARRAY2,56,,2;45504-45521-1-16(guardian177_6) | #UDGARRAY2,56,,2;45536-45553-1-16(guardian177_7) } TABLE#
B 45312,256,16
D 45568 #UDGTABLE { #UDGARRAY2,56,,2;45568-45585-1-16(guardian178_0) | #UDGARRAY2,56,,2;45600-45617-1-16(guardian178_1) | #UDGARRAY2,56,,2;45632-45649-1-16(guardian178_2) | #UDGARRAY2,56,,2;45664-45681-1-16(guardian178_3) | #UDGARRAY2,56,,2;45696-45713-1-16(guardian178_4) | #UDGARRAY2,56,,2;45728-45745-1-16(guardian178_5) | #UDGARRAY2,56,,2;45760-45777-1-16(guardian178_6) | #UDGARRAY2,56,,2;45792-45809-1-16(guardian178_7) } TABLE#
B 45568,256,16
D 45824 #UDGTABLE { #UDGARRAY2,56,,2;45824-45841-1-16(guardian179_0) | #UDGARRAY2,56,,2;45856-45873-1-16(guardian179_1) | #UDGARRAY2,56,,2;45888-45905-1-16(guardian179_2) | #UDGARRAY2,56,,2;45920-45937-1-16(guardian179_3) | #UDGARRAY2,56,,2;45952-45969-1-16(guardian179_4) | #UDGARRAY2,56,,2;45984-46001-1-16(guardian179_5) | #UDGARRAY2,56,,2;46016-46033-1-16(guardian179_6) | #UDGARRAY2,56,,2;46048-46065-1-16(guardian179_7) } TABLE#
B 45824,256,16
D 46080 #UDGTABLE { #UDGARRAY2,56,,2;46080-46097-1-16(guardian180_0) | #UDGARRAY2,56,,2;46112-46129-1-16(guardian180_1) | #UDGARRAY2,56,,2;46144-46161-1-16(guardian180_2) | #UDGARRAY2,56,,2;46176-46193-1-16(guardian180_3) | #UDGARRAY2,56,,2;46208-46225-1-16(guardian180_4) | #UDGARRAY2,56,,2;46240-46257-1-16(guardian180_5) | #UDGARRAY2,56,,2;46272-46289-1-16(guardian180_6) | #UDGARRAY2,56,,2;46304-46321-1-16(guardian180_7) } TABLE#
B 46080,256,16
D 46336 #UDGTABLE { #UDGARRAY2,56,,2;46336-46353-1-16(guardian181_0) | #UDGARRAY2,56,,2;46368-46385-1-16(guardian181_1) | #UDGARRAY2,56,,2;46400-46417-1-16(guardian181_2) | #UDGARRAY2,56,,2;46432-46449-1-16(guardian181_3) | #UDGARRAY2,56,,2;46464-46481-1-16(guardian181_4) | #UDGARRAY2,56,,2;46496-46513-1-16(guardian181_5) | #UDGARRAY2,56,,2;46528-46545-1-16(guardian181_6) | #UDGARRAY2,56,,2;46560-46577-1-16(guardian181_7) } TABLE#
B 46336,256,16
D 46592 #UDGTABLE { #UDGARRAY2,56,,2;46592-46609-1-16(guardian182_0) | #UDGARRAY2,56,,2;46624-46641-1-16(guardian182_1) | #UDGARRAY2,56,,2;46656-46673-1-16(guardian182_2) | #UDGARRAY2,56,,2;46688-46705-1-16(guardian182_3) | #UDGARRAY2,56,,2;46720-46737-1-16(guardian182_4) | #UDGARRAY2,56,,2;46752-46769-1-16(guardian182_5) | #UDGARRAY2,56,,2;46784-46801-1-16(guardian182_6) | #UDGARRAY2,56,,2;46816-46833-1-16(guardian182_7) } TABLE#
B 46592,256,16
D 46848 #UDGTABLE { #UDGARRAY2,56,,2;46848-46865-1-16(guardian183_0) | #UDGARRAY2,56,,2;46880-46897-1-16(guardian183_1) | #UDGARRAY2,56,,2;46912-46929-1-16(guardian183_2) | #UDGARRAY2,56,,2;46944-46961-1-16(guardian183_3) | #UDGARRAY2,56,,2;46976-46993-1-16(guardian183_4) | #UDGARRAY2,56,,2;47008-47025-1-16(guardian183_5) | #UDGARRAY2,56,,2;47040-47057-1-16(guardian183_6) | #UDGARRAY2,56,,2;47072-47089-1-16(guardian183_7) } TABLE#
B 46848,256,16
D 47104 #UDGTABLE { #UDGARRAY2,56,,2;47104-47121-1-16(guardian184_0) | #UDGARRAY2,56,,2;47136-47153-1-16(guardian184_1) | #UDGARRAY2,56,,2;47168-47185-1-16(guardian184_2) | #UDGARRAY2,56,,2;47200-47217-1-16(guardian184_3) | #UDGARRAY2,56,,2;47232-47249-1-16(guardian184_4) | #UDGARRAY2,56,,2;47264-47281-1-16(guardian184_5) | #UDGARRAY2,56,,2;47296-47313-1-16(guardian184_6) | #UDGARRAY2,56,,2;47328-47345-1-16(guardian184_7) } TABLE#
B 47104,256,16
D 47360 #UDGTABLE { #UDGARRAY2,56,,2;47360-47377-1-16(guardian185_0) | #UDGARRAY2,56,,2;47392-47409-1-16(guardian185_1) | #UDGARRAY2,56,,2;47424-47441-1-16(guardian185_2) | #UDGARRAY2,56,,2;47456-47473-1-16(guardian185_3) | #UDGARRAY2,56,,2;47488-47505-1-16(guardian185_4) | #UDGARRAY2,56,,2;47520-47537-1-16(guardian185_5) | #UDGARRAY2,56,,2;47552-47569-1-16(guardian185_6) | #UDGARRAY2,56,,2;47584-47601-1-16(guardian185_7) } TABLE#
B 47360,256,16
D 47616 #UDGTABLE { #UDGARRAY2,56,,2;47616-47633-1-16(guardian186_0) | #UDGARRAY2,56,,2;47648-47665-1-16(guardian186_1) | #UDGARRAY2,56,,2;47680-47697-1-16(guardian186_2) | #UDGARRAY2,56,,2;47712-47729-1-16(guardian186_3) | #UDGARRAY2,56,,2;47744-47761-1-16(guardian186_4) | #UDGARRAY2,56,,2;47776-47793-1-16(guardian186_5) | #UDGARRAY2,56,,2;47808-47825-1-16(guardian186_6) | #UDGARRAY2,56,,2;47840-47857-1-16(guardian186_7) } TABLE#
B 47616,256,16
D 47872 #UDGTABLE { #UDGARRAY2,56,,2;47872-47889-1-16(guardian187_0) | #UDGARRAY2,56,,2;47904-47921-1-16(guardian187_1) | #UDGARRAY2,56,,2;47936-47953-1-16(guardian187_2) | #UDGARRAY2,56,,2;47968-47985-1-16(guardian187_3) | #UDGARRAY2,56,,2;48000-48017-1-16(guardian187_4) | #UDGARRAY2,56,,2;48032-48049-1-16(guardian187_5) | #UDGARRAY2,56,,2;48064-48081-1-16(guardian187_6) | #UDGARRAY2,56,,2;48096-48113-1-16(guardian187_7) } TABLE#
B 47872,256,16
D 48128 #UDGTABLE { #UDGARRAY2,56,,2;48128-48145-1-16(guardian188_0) | #UDGARRAY2,56,,2;48160-48177-1-16(guardian188_1) | #UDGARRAY2,56,,2;48192-48209-1-16(guardian188_2) | #UDGARRAY2,56,,2;48224-48241-1-16(guardian188_3) | #UDGARRAY2,56,,2;48256-48273-1-16(guardian188_4) | #UDGARRAY2,56,,2;48288-48305-1-16(guardian188_5) | #UDGARRAY2,56,,2;48320-48337-1-16(guardian188_6) | #UDGARRAY2,56,,2;48352-48369-1-16(guardian188_7) } TABLE#
B 48128,256,16
D 48384 #UDGTABLE { #UDGARRAY2,56,,2;48384-48401-1-16(guardian189_0) | #UDGARRAY2,56,,2;48416-48433-1-16(guardian189_1) | #UDGARRAY2,56,,2;48448-48465-1-16(guardian189_2) | #UDGARRAY2,56,,2;48480-48497-1-16(guardian189_3) | #UDGARRAY2,56,,2;48512-48529-1-16(guardian189_4) | #UDGARRAY2,56,,2;48544-48561-1-16(guardian189_5) | #UDGARRAY2,56,,2;48576-48593-1-16(guardian189_6) | #UDGARRAY2,56,,2;48608-48625-1-16(guardian189_7) } TABLE#
B 48384,256,16
D 48640 #UDGTABLE { #UDGARRAY2,56,,2;48640-48657-1-16(guardian190_0) | #UDGARRAY2,56,,2;48672-48689-1-16(guardian190_1) | #UDGARRAY2,56,,2;48704-48721-1-16(guardian190_2) | #UDGARRAY2,56,,2;48736-48753-1-16(guardian190_3) | #UDGARRAY2,56,,2;48768-48785-1-16(guardian190_4) | #UDGARRAY2,56,,2;48800-48817-1-16(guardian190_5) | #UDGARRAY2,56,,2;48832-48849-1-16(guardian190_6) | #UDGARRAY2,56,,2;48864-48881-1-16(guardian190_7) } TABLE#
B 48640,256,16
D 48896 #UDGTABLE { #UDGARRAY2,56,,2;48896-48913-1-16(guardian191_0) | #UDGARRAY2,56,,2;48928-48945-1-16(guardian191_1) | #UDGARRAY2,56,,2;48960-48977-1-16(guardian191_2) | #UDGARRAY2,56,,2;48992-49009-1-16(guardian191_3) | #UDGARRAY2,56,,2;49024-49041-1-16(guardian191_4) | #UDGARRAY2,56,,2;49056-49073-1-16(guardian191_5) | #UDGARRAY2,56,,2;49088-49105-1-16(guardian191_6) | #UDGARRAY2,56,,2;49120-49137-1-16(guardian191_7) } TABLE#
B 48896,256,16
b 49152 Room 0: The Off Licence
D 49152 #UDGTABLE { #ROOM49152 } TABLE#
D 49152 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 49152,128,8 Room layout
D 49280 The next 32 bytes contain the room name.
T 49280,32 Room name
D 49312 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 49312 #UDGTABLE { #UDG49313,0(background00) | #UDG49322,68(floor00) | #UDG49331,22(wall00) | #UDG49340,5(nasty00) | #UDG49349,7(ramp00) | #UDG49358,67(conveyor00) } TABLE#
B 49312,9,9 Background
B 49321,9,9 Floor
B 49330,9,9 Wall
B 49339,9,9 Nasty
B 49348,9,9 Ramp
B 49357,9,9 Conveyor
D 49366 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 49366,4 Conveyor direction (left), location (x=19, y=9) and length (12)
B 49370,4 Ramp direction (right), location (x=23, y=14) and length (4)
D 49374 The next byte specifies the border colour.
B 49374 Border colour
B 49375 Unused
D 49377 The next 8 bytes define the object graphic.
D 49377 #UDGTABLE { #UDG49377,3(object00) } TABLE#
B 49377,8,8 Object graphic
D 49385 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 49385 Room to the left (#R49408(The Bridge))
B 49386 Room to the right (The Off Licence)
B 49387 Room above (The Off Licence)
B 49388 Room below (The Off Licence)
B 49389 Unused
D 49392 The next 6 bytes define the guardians.
B 49392,2 Guardian 1
B 49394,2 Guardian 2
B 49396,2 Guardian 3
B 49398,1 Terminator
B 49399,9,9 Unused
b 49408 Room 1: The Bridge
D 49408 #UDGTABLE { #ROOM49408 } TABLE#
D 49408 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 49408,128,8 Room layout
D 49536 The next 32 bytes contain the room name.
T 49536,32 Room name
D 49568 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 49568 #UDGTABLE { #UDG49569,0(background01) | #UDG49578,68(floor01) | #UDG49587,70(wall01) | #UDG49596,47(nasty01) | #UDG49605,7(ramp01) | #UDG49614,44(conveyor01) } TABLE#
B 49568,9,9 Background
B 49577,9,9 Floor
B 49586,9,9 Wall
B 49595,9,9 Nasty
B 49604,9,9 Ramp
B 49613,9,9 Conveyor
D 49622 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 49622,4 Conveyor direction (right), location (x=12, y=15) and length (5)
B 49626,4 Ramp direction (right), location (x=7, y=14) and length (3)
D 49630 The next byte specifies the border colour.
B 49630 Border colour
B 49631 Unused
D 49633 The next 8 bytes define the object graphic.
D 49633 #UDGTABLE { #UDG49633,3(object01) } TABLE#
B 49633,8,8 Object graphic (unused)
D 49641 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 49641 Room to the left (#R49664(Under the MegaTree))
B 49642 Room to the right (#R49152(The Off Licence))
B 49643 Room above (#R49152(The Off Licence))
B 49644 Room below (#R49152(The Off Licence))
B 49645 Unused
D 49648 The next 6 bytes define the guardians.
B 49648,2 Guardian 1
B 49650,2 Guardian 2
B 49652,2 Guardian 3
B 49654,1 Terminator
B 49655,9,9 Unused
b 49664 Room 2: Under the MegaTree
D 49664 #UDGTABLE { #ROOM49664 } TABLE#
D 49664 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 49664,128,8 Room layout
D 49792 The next 32 bytes contain the room name.
T 49792,32 Room name
D 49824 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 49824 #UDGTABLE { #UDG49825,0(background02) | #UDG49834,68(floor02) | #UDG49843,66(wall02) | #UDG49852,70(nasty02) | #UDG49861,255(ramp02) | #UDG49870,255(conveyor02) } TABLE#
B 49824,9,9 Background
B 49833,9,9 Floor
B 49842,9,9 Wall
B 49851,9,9 Nasty
B 49860,9,9 Ramp (unused)
B 49869,9,9 Conveyor (unused)
D 49878 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 49878,4 Conveyor direction (left), location (x=0, y=0) and length (0)
B 49882,4 Ramp direction (left), location (x=0, y=0) and length (0)
D 49886 The next byte specifies the border colour.
B 49886 Border colour
B 49887 Unused
D 49889 The next 8 bytes define the object graphic.
D 49889 #UDGTABLE { #UDG49889,3(object02) } TABLE#
B 49889,8,8 Object graphic
D 49897 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 49897 Room to the left (#R49920(At the Foot of the MegaTree))
B 49898 Room to the right (#R49408(The Bridge))
B 49899 Room above (#R49152(The Off Licence))
B 49900 Room below (#R49152(The Off Licence))
B 49901 Unused
D 49904 The next 6 bytes define the guardians.
B 49904,2 Guardian 1
B 49906,2 Guardian 2
B 49908,2 Guardian 3
B 49910,1 Terminator
B 49911,9,9 Unused
b 49920 Room 3: At the Foot of the MegaTree
D 49920 #UDGTABLE { #ROOM49920 } TABLE#
D 49920 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 49920,128,8 Room layout
D 50048 The next 32 bytes contain the room name.
T 50048,32 Room name
D 50080 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 50080 #UDGTABLE { #UDG50081,0(background03) | #UDG50090,4(floor03) | #UDG50099,22(wall03) | #UDG50108,6(nasty03) | #UDG50117,7(ramp03) | #UDG50126,255(conveyor03) } TABLE#
B 50080,9,9 Background
B 50089,9,9 Floor
B 50098,9,9 Wall
B 50107,9,9 Nasty
B 50116,9,9 Ramp
B 50125,9,9 Conveyor (unused)
D 50134 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 50134,4 Conveyor direction (left), location (x=0, y=0) and length (0)
B 50138,4 Ramp direction (left), location (x=15, y=12) and length (3)
D 50142 The next byte specifies the border colour.
B 50142 Border colour
B 50143 Unused
D 50145 The next 8 bytes define the object graphic.
D 50145 #UDGTABLE { #UDG50145,3(object03) } TABLE#
B 50145,8,8 Object graphic
D 50153 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 50153 Room to the left (#R50176(The Drive))
B 50154 Room to the right (#R49664(Under the MegaTree))
B 50155 Room above (#R51200(Inside the MegaTrunk))
B 50156 Room below (#R49152(The Off Licence))
B 50157 Unused
D 50160 The next 8 bytes define the guardians.
B 50160,2 Guardian 1
B 50162,2 Guardian 2
B 50164,2 Guardian 3
B 50166,2 Guardian 4
B 50168,1 Terminator
B 50169,7,7 Unused
b 50176 Room 4: The Drive
D 50176 #UDGTABLE { #ROOM50176 } TABLE#
D 50176 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 50176,128,8 Room layout
D 50304 The next 32 bytes contain the room name.
T 50304,32 Room name
D 50336 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 50336 #UDGTABLE { #UDG50337,0(background04) | #UDG50346,6(floor04) | #UDG50355,13(wall04) | #UDG50364,68(nasty04) | #UDG50373,5(ramp04) | #UDG50382,66(conveyor04) } TABLE#
B 50336,9,9 Background
B 50345,9,9 Floor
B 50354,9,9 Wall
B 50363,9,9 Nasty (unused)
B 50372,9,9 Ramp
B 50381,9,9 Conveyor
D 50390 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 50390,4 Conveyor direction (right), location (x=0, y=13) and length (2)
B 50394,4 Ramp direction (left), location (x=9, y=14) and length (7)
D 50398 The next byte specifies the border colour.
B 50398 Border colour
B 50399 Unused
D 50401 The next 8 bytes define the object graphic.
D 50401 #UDGTABLE { #UDG50401,3(object04) } TABLE#
B 50401,8,8 Object graphic (unused)
D 50409 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 50409 Room to the left (#R50432(The Security Guard))
B 50410 Room to the right (#R49920(At the Foot of the MegaTree))
B 50411 Room above (#R50688(Entrance to Hades))
B 50412 Room below (#R60672(Under the Drive))
B 50413 Unused
D 50416 The next 10 bytes define the guardians.
B 50416,2 Guardian 1
B 50418,2 Guardian 2
B 50420,2 Guardian 3
B 50422,2 Guardian 4
B 50424,2 Guardian 5
B 50426,1 Terminator
B 50427,5,5 Unused
b 50432 Room 5: The Security Guard
D 50432 #UDGTABLE { #ROOM50432 } TABLE#
D 50432 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 50432,128,8 Room layout
D 50560 The next 32 bytes contain the room name.
T 50560,32 Room name
D 50592 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 50592 #UDGTABLE { #UDG50593,0(background05) | #UDG50602,4(floor05) | #UDG50611,13(wall05) | #UDG50620,255(nasty05) | #UDG50629,7(ramp05) | #UDG50638,66(conveyor05) } TABLE#
B 50592,9,9 Background
B 50601,9,9 Floor
B 50610,9,9 Wall
B 50619,9,9 Nasty (unused)
B 50628,9,9 Ramp
B 50637,9,9 Conveyor
D 50646 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 50646,4 Conveyor direction (right), location (x=29, y=13) and length (3)
B 50650,4 Ramp direction (left), location (x=8, y=7) and length (8)
D 50654 The next byte specifies the border colour.
B 50654 Border colour
B 50655 Unused
D 50657 The next 8 bytes define the object graphic.
D 50657 #UDGTABLE { #UDG50657,3(object05) } TABLE#
B 50657,8,8 Object graphic (unused)
D 50665 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 50665 Room to the left (#R54016(The Forgotten Abbey))
B 50666 Room to the right (#R50176(The Drive))
B 50667 Room above (#R51712(The Front Door))
B 50668 Room below (#R50688(Entrance to Hades))
B 50669 Unused
D 50672 The next 8 bytes define the guardians.
B 50672,2 Guardian 1
B 50674,2 Guardian 2
B 50676,2 Guardian 3
B 50678,2 Guardian 4
B 50680,1 Terminator
B 50681,7,7 Unused
b 50688 Room 6: Entrance to Hades
D 50688 #UDGTABLE { #ROOM50688(entrance_to_hades.gif) } TABLE#
D 50688 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 50688,128,8 Room layout
D 50816 The next 32 bytes contain the room name.
T 50816,32 Room name
D 50848 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 50848 #UDGTABLE { #UDG50849,52(background06) | #UDG50858,163(floor06.gif) | #UDG50867,99(wall06) | #UDG50876,50(nasty06) | #UDG50885,7(ramp06) | #UDG50894,255(conveyor06) } TABLE#
B 50848,9,9 Background
B 50857,9,9 Floor
B 50866,9,9 Wall
B 50875,9,9 Nasty
B 50884,9,9 Ramp (unused)
B 50893,9,9 Conveyor (unused)
D 50902 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 50902,4 Conveyor direction (left), location (x=0, y=0) and length (0)
B 50906,4 Ramp direction (left), location (x=7, y=14) and length (0)
D 50910 The next byte specifies the border colour.
B 50910 Border colour
B 50911 Unused
D 50913 The next 8 bytes define the object graphic.
D 50913 #UDGTABLE { #UDG50913,51(object06) } TABLE#
B 50913,8,8 Object graphic (unused)
D 50921 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 50921 Room to the left (#R52736(Rescue Esmerelda))
B 50922 Room to the right (#R50432(The Security Guard))
B 50923 Room above (#R49152(The Off Licence))
B 50924 Room below (#R49152(The Off Licence))
B 50925 Unused
D 50928 The next 6 bytes define the guardians.
B 50928,2 Guardian 1
B 50930,2 Guardian 2
B 50932,2 Guardian 3
B 50934,1 Terminator
B 50935,9,9 Unused
b 50944 Room 7: Cuckoo's Nest
D 50944 #UDGTABLE { #ROOM50944 } TABLE#
D 50944 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 50944,128,8 Room layout
D 51072 The next 32 bytes contain the room name.
T 51072,32 Room name
D 51104 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 51104 #UDGTABLE { #UDG51105,0(background07) | #UDG51114,4(floor07) | #UDG51123,22(wall07) | #UDG51132,6(nasty07) | #UDG51141,7(ramp07) | #UDG51150,255(conveyor07) } TABLE#
B 51104,9,9 Background
B 51113,9,9 Floor
B 51122,9,9 Wall
B 51131,9,9 Nasty
B 51140,9,9 Ramp
B 51149,9,9 Conveyor (unused)
D 51158 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 51158,4 Conveyor direction (left), location (x=0, y=0) and length (0)
B 51162,4 Ramp direction (right), location (x=13, y=12) and length (2)
D 51166 The next byte specifies the border colour.
B 51166 Border colour
B 51167 Unused
D 51169 The next 8 bytes define the object graphic.
D 51169 #UDGTABLE { #UDG51169,3(object07) } TABLE#
B 51169,8,8 Object graphic
D 51177 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 51177 Room to the left (#R51200(Inside the MegaTrunk))
B 51178 Room to the right (#R49152(The Off Licence))
B 51179 Room above (#R49152(The Off Licence))
B 51180 Room below (#R49664(Under the MegaTree))
B 51181 Unused
D 51184 The next 6 bytes define the guardians.
B 51184,2 Guardian 1
B 51186,2 Guardian 2
B 51188,2 Guardian 3
B 51190,1 Terminator
B 51191,9,9 Unused
b 51200 Room 8: Inside the MegaTrunk
D 51200 #UDGTABLE { #ROOM51200 } TABLE#
D 51200 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 51200,128,8 Room layout
D 51328 The next 32 bytes contain the room name.
T 51328,32 Room name
D 51360 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 51360 #UDGTABLE { #UDG51361,0(background08) | #UDG51370,4(floor08) | #UDG51379,22(wall08) | #UDG51388,6(nasty08) | #UDG51397,7(ramp08) | #UDG51406,255(conveyor08) } TABLE#
B 51360,9,9 Background
B 51369,9,9 Floor
B 51378,9,9 Wall
B 51387,9,9 Nasty
B 51396,9,9 Ramp
B 51405,9,9 Conveyor (unused)
D 51414 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 51414,4 Conveyor direction (left), location (x=0, y=0) and length (0)
B 51418,4 Ramp direction (left), location (x=27, y=7) and length (3)
D 51422 The next byte specifies the border colour.
B 51422 Border colour
B 51423 Unused
D 51425 The next 8 bytes define the object graphic.
D 51425 #UDGTABLE { #UDG51425,3(object08) } TABLE#
B 51425,8,8 Object graphic (unused)
D 51433 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 51433 Room to the left (#R51456(On a Branch Over the Drive))
B 51434 Room to the right (#R50944(Cuckoo's Nest))
B 51435 Room above (#R52224(Tree Top))
B 51436 Room below (#R49920(At the Foot of the MegaTree))
B 51437 Unused
D 51440 The next 14 bytes define the guardians.
B 51440,2 Guardian 1
B 51442,2 Guardian 2
B 51444,2 Guardian 3
B 51446,2 Guardian 4
B 51448,2 Guardian 5
B 51450,2 Guardian 6
B 51452,2 Guardian 7
B 51454,1 Terminator
B 51455,1,1 Unused
b 51456 Room 9: On a Branch Over the Drive
D 51456 #UDGTABLE { #ROOM51456 } TABLE#
D 51456 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 51456,128,8 Room layout
D 51584 The next 32 bytes contain the room name.
T 51584,32 Room name
D 51616 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 51616 #UDGTABLE { #UDG51617,8(background09) | #UDG51626,10(floor09) | #UDG51635,74(wall09) | #UDG51644,12(nasty09) | #UDG51653,15(ramp09) | #UDG51662,255(conveyor09) } TABLE#
B 51616,9,9 Background
B 51625,9,9 Floor
B 51634,9,9 Wall
B 51643,9,9 Nasty
B 51652,9,9 Ramp
B 51661,9,9 Conveyor (unused)
D 51670 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 51670,4 Conveyor direction (left), location (x=0, y=0) and length (0)
B 51674,4 Ramp direction (right), location (x=14, y=10) and length (4)
D 51678 The next byte specifies the border colour.
B 51678 Border colour
B 51679 Unused
D 51681 The next 8 bytes define the object graphic.
D 51681 #UDGTABLE { #UDG51681,11(object09) } TABLE#
B 51681,8,8 Object graphic
D 51689 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 51689 Room to the left (#R51712(The Front Door))
B 51690 Room to the right (#R51200(Inside the MegaTrunk))
B 51691 Room above (#R52480(Out on a limb))
B 51692 Room below (#R50176(The Drive))
B 51693 Unused
D 51696 The next 10 bytes define the guardians.
B 51696,2 Guardian 1
B 51698,2 Guardian 2
B 51700,2 Guardian 3
B 51702,2 Guardian 4
B 51704,2 Guardian 5
B 51706,1 Terminator
B 51707,5,5 Unused
b 51712 Room 10: The Front Door
D 51712 #UDGTABLE { #ROOM51712 } TABLE#
D 51712 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 51712,128,8 Room layout
D 51840 The next 32 bytes contain the room name.
T 51840,32 Room name
D 51872 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 51872 #UDGTABLE { #UDG51873,40(background10) | #UDG51882,71(floor10) | #UDG51891,58(wall10) | #UDG51900,255(nasty10) | #UDG51909,47(ramp10) | #UDG51918,255(conveyor10) } TABLE#
B 51872,9,9 Background
B 51881,9,9 Floor
B 51890,9,9 Wall
B 51899,9,9 Nasty (unused)
B 51908,9,9 Ramp
B 51917,9,9 Conveyor (unused)
D 51926 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 51926,4 Conveyor direction (left), location (x=0, y=0) and length (0)
B 51930,4 Ramp direction (left), location (x=2, y=15) and length (2)
D 51934 The next byte specifies the border colour.
B 51934 Border colour
B 51935 Unused
D 51937 The next 8 bytes define the object graphic.
D 51937 #UDGTABLE { #UDG51937,43(object10) } TABLE#
B 51937,8,8 Object graphic
D 51945 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 51945 Room to the left (#R51968(The Hall))
B 51946 Room to the right (#R51456(On a Branch Over the Drive))
B 51947 Room above (#R49152(The Off Licence))
B 51948 Room below (#R50432(The Security Guard))
B 51949 Unused
D 51952 There are no guardians in this room.
B 51952,1 Terminator
B 51953,15,15 Unused
b 51968 Room 11: The Hall
D 51968 #UDGTABLE { #ROOM51968 } TABLE#
D 51968 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 51968,128,8 Room layout
D 52096 The next 32 bytes contain the room name.
T 52096,32 Room name
D 52128 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 52128 #UDGTABLE { #UDG52129,0(background11) | #UDG52138,71(floor11) | #UDG52147,58(wall11) | #UDG52156,68(nasty11) | #UDG52165,7(ramp11) | #UDG52174,255(conveyor11) } TABLE#
B 52128,9,9 Background
B 52137,9,9 Floor (unused)
B 52146,9,9 Wall
B 52155,9,9 Nasty
B 52164,9,9 Ramp
B 52173,9,9 Conveyor (unused)
D 52182 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 52182,4 Conveyor direction (left), location (x=0, y=0) and length (0)
B 52186,4 Ramp direction (left), location (x=5, y=13) and length (6)
D 52190 The next byte specifies the border colour.
B 52190 Border colour
B 52191 Unused
D 52193 The next 8 bytes define the object graphic.
D 52193 #UDGTABLE { #UDG52193,3(object11) } TABLE#
B 52193,8,8 Object graphic (unused)
D 52201 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 52201 Room to the left (#R54272(Ballroom East))
B 52202 Room to the right (#R51712(The Front Door))
B 52203 Room above (#R49152(The Off Licence))
B 52204 Room below (#R49152(The Off Licence))
B 52205 Unused
D 52208 The next 10 bytes define the guardians.
B 52208,2 Guardian 1
B 52210,2 Guardian 2
B 52212,2 Guardian 3
B 52214,2 Guardian 4
B 52216,2 Guardian 5
B 52218,1 Terminator
B 52219,5,5 Unused
b 52224 Room 12: Tree Top
D 52224 #UDGTABLE { #ROOM52224 } TABLE#
D 52224 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 52224,128,8 Room layout
D 52352 The next 32 bytes contain the room name.
T 52352,32 Room name
D 52384 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 52384 #UDGTABLE { #UDG52385,0(background12) | #UDG52394,4(floor12) | #UDG52403,22(wall12) | #UDG52412,66(nasty12) | #UDG52421,7(ramp12) | #UDG52430,255(conveyor12) } TABLE#
B 52384,9,9 Background
B 52393,9,9 Floor
B 52402,9,9 Wall
B 52411,9,9 Nasty
B 52420,9,9 Ramp
B 52429,9,9 Conveyor (unused)
D 52438 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 52438,4 Conveyor direction (left), location (x=0, y=0) and length (0)
B 52442,4 Ramp direction (left), location (x=15, y=14) and length (2)
D 52446 The next byte specifies the border colour.
B 52446 Border colour
B 52447 Unused
D 52449 The next 8 bytes define the object graphic.
D 52449 #UDGTABLE { #UDG52449,3(object12) } TABLE#
B 52449,8,8 Object graphic
D 52457 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 52457 Room to the left (#R52480(Out on a limb))
B 52458 Room to the right (#R49152(The Off Licence))
B 52459 Room above (#R49152(The Off Licence))
B 52460 Room below (#R51200(Inside the MegaTrunk))
B 52461 Unused
D 52464 The next 8 bytes define the guardians.
B 52464,2 Guardian 1
B 52466,2 Guardian 2
B 52468,2 Guardian 3
B 52470,2 Guardian 4
B 52472,1 Terminator
B 52473,7,7 Unused
b 52480 Room 13: Out on a limb
D 52480 #UDGTABLE { #ROOM52480 } TABLE#
D 52480 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 52480,128,8 Room layout
D 52608 The next 32 bytes contain the room name.
T 52608,32 Room name
D 52640 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 52640 #UDGTABLE { #UDG52641,0(background13) | #UDG52650,4(floor13) | #UDG52659,66(wall13) | #UDG52668,2(nasty13) | #UDG52677,4(ramp13) | #UDG52686,255(conveyor13) } TABLE#
B 52640,9,9 Background
B 52649,9,9 Floor
B 52658,9,9 Wall
B 52667,9,9 Nasty
B 52676,9,9 Ramp (unused)
B 52685,9,9 Conveyor (unused)
D 52694 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 52694,4 Conveyor direction (left), location (x=0, y=0) and length (0)
B 52698,4 Ramp direction (right), location (x=0, y=0) and length (0)
D 52702 The next byte specifies the border colour.
B 52702 Border colour
B 52703 Unused
D 52705 The next 8 bytes define the object graphic.
D 52705 #UDGTABLE { #UDG52705,3(object13) } TABLE#
B 52705,8,8 Object graphic
D 52713 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 52713 Room to the left (#R51712(The Front Door))
B 52714 Room to the right (#R52224(Tree Top))
B 52715 Room above (#R49152(The Off Licence))
B 52716 Room below (#R51456(On a Branch Over the Drive))
B 52717 Unused
D 52720 The next 6 bytes define the guardians.
B 52720,2 Guardian 1
B 52722,2 Guardian 2
B 52724,2 Guardian 3
B 52726,1 Terminator
B 52727,9,9 Unused
b 52736 Room 14: Rescue Esmerelda
D 52736 #UDGTABLE { #ROOM52736 } TABLE#
D 52736 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 52736,128,8 Room layout
D 52864 The next 32 bytes contain the room name.
T 52864,32 Room name
D 52896 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 52896 #UDGTABLE { #UDG52897,16(background14) | #UDG52906,23(floor14) | #UDG52915,4(wall14) | #UDG52924,85(nasty14) | #UDG52933,23(ramp14) | #UDG52942,22(conveyor14) } TABLE#
B 52896,9,9 Background
B 52905,9,9 Floor
B 52914,9,9 Wall
B 52923,9,9 Nasty
B 52932,9,9 Ramp (unused)
B 52941,9,9 Conveyor
D 52950 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 52950,4 Conveyor direction (right), location (x=24, y=4) and length (4)
B 52954,4 Ramp direction (right), location (x=0, y=0) and length (0)
D 52958 The next byte specifies the border colour.
B 52958 Border colour
B 52959 Unused
D 52961 The next 8 bytes define the object graphic.
D 52961 #UDGTABLE { #UDG52961,19(object14) } TABLE#
B 52961,8,8 Object graphic
D 52969 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 52969 Room to the left (#R52992(I'm sure I've seen this before..))
B 52970 Room to the right (#R60416(On top of the house))
B 52971 Room above (#R54272(Ballroom East))
B 52972 Room below (#R59136(Emergency Generator))
B 52973 Unused
D 52976 The next 8 bytes define the guardians.
B 52976,2 Guardian 1
B 52978,2 Guardian 2
B 52980,2 Guardian 3
B 52982,2 Guardian 4
B 52984,1 Terminator
B 52985,7,7 Unused
b 52992 Room 15: I'm sure I've seen this before..
D 52992 #UDGTABLE { #ROOM52992 } TABLE#
D 52992 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 52992,128,8 Room layout
D 53120 The next 32 bytes contain the room name.
T 53120,32 Room name
D 53152 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 53152 #UDGTABLE { #UDG53153,8(background15) | #UDG53162,12(floor15) | #UDG53171,83(wall15) | #UDG53180,76(nasty15) | #UDG53189,12(ramp15) | #UDG53198,255(conveyor15) } TABLE#
B 53152,9,9 Background
B 53161,9,9 Floor
B 53170,9,9 Wall
B 53179,9,9 Nasty
B 53188,9,9 Ramp (unused)
B 53197,9,9 Conveyor (unused)
D 53206 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 53206,4 Conveyor direction (left), location (x=0, y=0) and length (0)
B 53210,4 Ramp direction (left), location (x=0, y=0) and length (0)
D 53214 The next byte specifies the border colour.
B 53214 Border colour
B 53215 Unused
D 53217 The next 8 bytes define the object graphic.
D 53217 #UDGTABLE { #UDG53217,11(object15) } TABLE#
B 53217,8,8 Object graphic
D 53225 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 53225 Room to the left (#R53248(We must perform a Quirkafleeg))
B 53226 Room to the right (#R52736(Rescue Esmerelda))
B 53227 Room above (#R49152(The Off Licence))
B 53228 Room below (#R49152(The Off Licence))
B 53229 Unused
D 53232 The next 14 bytes define the guardians.
B 53232,2 Guardian 1
B 53234,2 Guardian 2
B 53236,2 Guardian 3
B 53238,2 Guardian 4
B 53240,2 Guardian 5
B 53242,2 Guardian 6
B 53244,2 Guardian 7
B 53246,1 Terminator
B 53247,1,1 Unused
b 53248 Room 16: We must perform a Quirkafleeg
D 53248 #UDGTABLE { #ROOM53248 } TABLE#
D 53248 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 53248,128,8 Room layout
D 53376 The next 32 bytes contain the room name.
T 53376,32 Room name
D 53408 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 53408 #UDGTABLE { #UDG53409,6(background16) | #UDG53418,56(floor16) | #UDG53427,13(wall16) | #UDG53436,69(nasty16) | #UDG53445,7(ramp16) | #UDG53454,255(conveyor16) } TABLE#
B 53408,9,9 Background
B 53417,9,9 Floor
B 53426,9,9 Wall
B 53435,9,9 Nasty
B 53444,9,9 Ramp
B 53453,9,9 Conveyor (unused)
D 53462 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 53462,4 Conveyor direction (left), location (x=0, y=0) and length (0)
B 53466,4 Ramp direction (left), location (x=4, y=9) and length (1)
D 53470 The next byte specifies the border colour.
B 53470 Border colour
B 53471 Unused
D 53473 The next 8 bytes define the object graphic.
D 53473 #UDGTABLE { #UDG53473,3(object16) } TABLE#
B 53473,8,8 Object graphic
D 53481 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 53481 Room to the left (#R53504(Up on the Battlements))
B 53482 Room to the right (#R52992(I'm sure I've seen this before..))
B 53483 Room above (#R61952(Watch Tower))
B 53484 Room below (#R49152(The Off Licence))
B 53485 Unused
D 53488 The next 6 bytes define the guardians.
B 53488,2 Guardian 1
B 53490,2 Guardian 2
B 53492,2 Guardian 3
B 53494,1 Terminator
B 53495,9,9 Unused
b 53504 Room 17: Up on the Battlements
D 53504 #UDGTABLE { #ROOM53504 } TABLE#
D 53504 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 53504,128,8 Room layout
D 53632 The next 32 bytes contain the room name.
T 53632,32 Room name
D 53664 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 53664 #UDGTABLE { #UDG53665,0(background17) | #UDG53674,4(floor17) | #UDG53683,14(wall17) | #UDG53692,32(nasty17) | #UDG53701,4(ramp17) | #UDG53710,66(conveyor17) } TABLE#
B 53664,9,9 Background
B 53673,9,9 Floor
B 53682,9,9 Wall
B 53691,9,9 Nasty
B 53700,9,9 Ramp (unused)
B 53709,9,9 Conveyor
D 53718 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 53718,4 Conveyor direction (left), location (x=13, y=9) and length (5)
B 53722,4 Ramp direction (left), location (x=0, y=0) and length (0)
D 53726 The next byte specifies the border colour.
B 53726 Border colour
B 53727 Unused
D 53729 The next 8 bytes define the object graphic.
D 53729 #UDGTABLE { #UDG53729,3(object17) } TABLE#
B 53729,8,8 Object graphic
D 53737 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 53737 Room to the left (#R53760(On the Roof))
B 53738 Room to the right (#R53248(We must perform a Quirkafleeg))
B 53739 Room above (#R49152(The Off Licence))
B 53740 Room below (#R49152(The Off Licence))
B 53741 Unused
D 53744 The next 10 bytes define the guardians.
B 53744,2 Guardian 1
B 53746,2 Guardian 2
B 53748,2 Guardian 3
B 53750,2 Guardian 4
B 53752,2 Guardian 5
B 53754,1 Terminator
B 53755,5,5 Unused
b 53760 Room 18: On the Roof
D 53760 #UDGTABLE { #ROOM53760 } TABLE#
D 53760 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 53760,128,8 Room layout
D 53888 The next 32 bytes contain the room name.
T 53888,32 Room name
D 53920 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 53920 #UDGTABLE { #UDG53921,68(background18) | #UDG53930,7(floor18) | #UDG53939,38(wall18) | #UDG53948,70(nasty18) | #UDG53957,7(ramp18) | #UDG53966,10(conveyor18) } TABLE#
B 53920,9,9 Background
B 53929,9,9 Floor
B 53938,9,9 Wall
B 53947,9,9 Nasty
B 53956,9,9 Ramp (unused)
B 53965,9,9 Conveyor
D 53974 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 53974,4 Conveyor direction (right), location (x=14, y=15) and length (8)
B 53978,4 Ramp direction (left), location (x=0, y=0) and length (0)
D 53982 The next byte specifies the border colour.
B 53982 Border colour
B 53983 Unused
D 53985 The next 8 bytes define the object graphic.
D 53985 #UDGTABLE { #UDG53985,67(object18) } TABLE#
B 53985,8,8 Object graphic
D 53993 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 53993 Room to the left (#R61440(Nomen Luni))
B 53994 Room to the right (#R53504(Up on the Battlements))
B 53995 Room above (On the Roof)
B 53996 Room below (#R49152(The Off Licence))
B 53997 Unused
D 54000 The next 4 bytes define the guardians.
B 54000,2 Guardian 1
B 54002,2 Guardian 2
B 54004,1 Terminator
B 54005,11,11 Unused
b 54016 Room 19: The Forgotten Abbey
D 54016 #UDGTABLE { #ROOM54016 } TABLE#
D 54016 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 54016,128,8 Room layout
D 54144 The next 32 bytes contain the room name.
T 54144,32 Room name
D 54176 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 54176 #UDGTABLE { #UDG54177,0(background19) | #UDG54186,4(floor19) | #UDG54195,29(wall19) | #UDG54204,66(nasty19) | #UDG54213,7(ramp19) | #UDG54222,15(conveyor19) } TABLE#
B 54176,9,9 Background
B 54185,9,9 Floor
B 54194,9,9 Wall
B 54203,9,9 Nasty
B 54212,9,9 Ramp
B 54221,9,9 Conveyor
D 54230 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 54230,4 Conveyor direction (left), location (x=4, y=7) and length (26)
B 54234,4 Ramp direction (left), location (x=4, y=14) and length (2)
D 54238 The next byte specifies the border colour.
B 54238 Border colour
B 54239 Unused
D 54241 The next 8 bytes define the object graphic.
D 54241 #UDGTABLE { #UDG54241,3(object19) } TABLE#
B 54241,8,8 Object graphic
D 54249 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 54249 Room to the left (#R61696(The Wine Cellar))
B 54250 Room to the right (#R50432(The Security Guard))
B 54251 Room above (#R49152(The Off Licence))
B 54252 Room below (#R49152(The Off Licence))
B 54253 Unused
D 54256 The next 16 bytes define the guardians.
B 54256,2 Guardian 1
B 54258,2 Guardian 2
B 54260,2 Guardian 3
B 54262,2 Guardian 4
B 54264,2 Guardian 5
B 54266,2 Guardian 6
B 54268,2 Guardian 7
B 54270,2 Guardian 8
b 54272 Room 20: Ballroom East
D 54272 #UDGTABLE { #ROOM54272 } TABLE#
D 54272 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 54272,128,8 Room layout
D 54400 The next 32 bytes contain the room name.
T 54400,32 Room name
D 54432 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 54432 #UDGTABLE { #UDG54433,0(background20) | #UDG54442,6(floor20) | #UDG54451,15(wall20) | #UDG54460,255(nasty20) | #UDG54469,255(ramp20) | #UDG54478,255(conveyor20) } TABLE#
B 54432,9,9 Background
B 54441,9,9 Floor
B 54450,9,9 Wall
B 54459,9,9 Nasty (unused)
B 54468,9,9 Ramp (unused)
B 54477,9,9 Conveyor (unused)
D 54486 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 54486,4 Conveyor direction (left), location (x=0, y=0) and length (0)
B 54490,4 Ramp direction (left), location (x=0, y=0) and length (0)
D 54494 The next byte specifies the border colour.
B 54494 Border colour
B 54495 Unused
D 54497 The next 8 bytes define the object graphic.
D 54497 #UDGTABLE { #UDG54497,3(object20) } TABLE#
B 54497,8,8 Object graphic (unused)
D 54505 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 54505 Room to the left (#R54528(Ballroom West))
B 54506 Room to the right (#R51968(The Hall))
B 54507 Room above (#R55808(East Wall Base))
B 54508 Room below (#R49152(The Off Licence))
B 54509 Unused
D 54512 The next 10 bytes define the guardians.
B 54512,2 Guardian 1
B 54514,2 Guardian 2
B 54516,2 Guardian 3
B 54518,2 Guardian 4
B 54520,2 Guardian 5
B 54522,1 Terminator
B 54523,5,5 Unused
b 54528 Room 21: Ballroom West
D 54528 #UDGTABLE { #ROOM54528 } TABLE#
D 54528 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 54528,128,8 Room layout
D 54656 The next 32 bytes contain the room name.
T 54656,32 Room name
D 54688 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 54688 #UDGTABLE { #UDG54689,0(background21) | #UDG54698,50(floor21) | #UDG54707,35(wall21) | #UDG54716,66(nasty21) | #UDG54725,7(ramp21) | #UDG54734,70(conveyor21) } TABLE#
B 54688,9,9 Background
B 54697,9,9 Floor
B 54706,9,9 Wall
B 54715,9,9 Nasty (unused)
B 54724,9,9 Ramp
B 54733,9,9 Conveyor
D 54742 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 54742,4 Conveyor direction (right), location (x=16, y=13) and length (12)
B 54746,4 Ramp direction (left), location (x=3, y=13) and length (4)
D 54750 The next byte specifies the border colour.
B 54750 Border colour
B 54751 Unused
D 54753 The next 8 bytes define the object graphic.
D 54753 #UDGTABLE { #UDG54753,3(object21) } TABLE#
B 54753,8,8 Object graphic
D 54761 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 54761 Room to the left (#R54784(#SPACE(0)To#SPACE(1)the#SPACE(1)Kitchens#SPACE(4)Main#SPACE(1)Stairway))
B 54762 Room to the right (#R54272(Ballroom East))
B 54763 Room above (#R56064(The Chapel))
B 54764 Room below (#R49152(The Off Licence))
B 54765 Unused
D 54768 The next 6 bytes define the guardians.
B 54768,2 Guardian 1
B 54770,2 Guardian 2
B 54772,2 Guardian 3
B 54774,1 Terminator
B 54775,9,9 Unused
b 54784 Room 22: #SPACE(0)To#SPACE(1)the#SPACE(1)Kitchens#SPACE(4)Main#SPACE(1)Stairway
D 54784 #UDGTABLE { #ROOM54784 } TABLE#
D 54784 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 54784,128,8 Room layout
D 54912 The next 32 bytes contain the room name.
T 54912,32 Room name
D 54944 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 54944 #UDGTABLE { #UDG54945,8(background22) | #UDG54954,13(floor22) | #UDG54963,58(wall22) | #UDG54972,77(nasty22) | #UDG54981,15(ramp22) | #UDG54990,107(conveyor22) } TABLE#
B 54944,9,9 Background
B 54953,9,9 Floor
B 54962,9,9 Wall
B 54971,9,9 Nasty
B 54980,9,9 Ramp
B 54989,9,9 Conveyor
D 54998 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 54998,4 Conveyor direction (left), location (x=14, y=8) and length (2)
B 55002,4 Ramp direction (left), location (x=31, y=11) and length (12)
D 55006 The next byte specifies the border colour.
B 55006 Border colour
B 55007 Unused
D 55009 The next 8 bytes define the object graphic.
D 55009 #UDGTABLE { #UDG55009,11(object22) } TABLE#
B 55009,8,8 Object graphic
D 55017 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 55017 Room to the left (#R55040(The Kitchen))
B 55018 Room to the right (#R54528(Ballroom West))
B 55019 Room above (#R56320(First Landing))
B 55020 Room below (#R49152(The Off Licence))
B 55021 Unused
D 55024 The next 12 bytes define the guardians.
B 55024,2 Guardian 1
B 55026,2 Guardian 2
B 55028,2 Guardian 3
B 55030,2 Guardian 4
B 55032,2 Guardian 5
B 55034,2 Guardian 6
B 55036,1 Terminator
B 55037,3,3 Unused
b 55040 Room 23: The Kitchen
D 55040 #UDGTABLE { #ROOM55040 } TABLE#
D 55040 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 55040,128,8 Room layout
D 55168 The next 32 bytes contain the room name.
T 55168,32 Room name
D 55200 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 55200 #UDGTABLE { #UDG55201,0(background23) | #UDG55210,4(floor23) | #UDG55219,77(wall23) | #UDG55228,255(nasty23) | #UDG55237,71(ramp23) | #UDG55246,255(conveyor23) } TABLE#
B 55200,9,9 Background
B 55209,9,9 Floor
B 55218,9,9 Wall
B 55227,9,9 Nasty (unused)
B 55236,9,9 Ramp
B 55245,9,9 Conveyor (unused)
D 55254 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 55254,4 Conveyor direction (left), location (x=0, y=0) and length (0)
B 55258,4 Ramp direction (right), location (x=22, y=14) and length (7)
D 55262 The next byte specifies the border colour.
B 55262 Border colour
B 55263 Unused
D 55265 The next 8 bytes define the object graphic.
D 55265 #UDGTABLE { #UDG55265,3(object23) } TABLE#
B 55265,8,8 Object graphic (unused)
D 55273 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 55273 Room to the left (#R55296(West of Kitchen))
B 55274 Room to the right (#R54784(#SPACE(0)To#SPACE(1)the#SPACE(1)Kitchens#SPACE(4)Main#SPACE(1)Stairway))
B 55275 Room above (#R49152(The Off Licence))
B 55276 Room below (#R49152(The Off Licence))
B 55277 Unused
D 55280 The next 8 bytes define the guardians.
B 55280,2 Guardian 1
B 55282,2 Guardian 2
B 55284,2 Guardian 3
B 55286,2 Guardian 4
B 55288,1 Terminator
B 55289,7,7 Unused
b 55296 Room 24: West of Kitchen
D 55296 #UDGTABLE { #ROOM55296 } TABLE#
D 55296 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 55296,128,8 Room layout
D 55424 The next 32 bytes contain the room name.
T 55424,32 Room name
D 55456 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room. Note that because of a bug in the game engine, the conveyor tile is not drawn correctly (see the room image above).
D 55456 #UDGTABLE { #UDG55457,0(background24) | #UDG55466,5(floor24) | #UDG55475,34(wall24) | #UDG55484,255(nasty24) | #UDG55493,71(ramp24) | #UDG55502,66(conveyor24) } TABLE#
B 55456,9,9 Background
B 55465,9,9 Floor
B 55474,9,9 Wall
B 55483,9,9 Nasty (unused)
B 55492,9,9 Ramp
B 55501,9,9 Conveyor
D 55510 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 55510,4 Conveyor direction (left), location (x=22, y=12) and length (5)
B 55514,4 Ramp direction (left), location (x=8, y=14) and length (7)
D 55518 The next byte specifies the border colour.
B 55518 Border colour
B 55519 Unused
D 55521 The next 8 bytes define the object graphic.
D 55521 #UDGTABLE { #UDG55521,3(object24) } TABLE#
B 55521,8,8 Object graphic (unused)
D 55529 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 55529 Room to the left (#R55552(Cold Store))
B 55530 Room to the right (#R55040(The Kitchen))
B 55531 Room above (#R56832(The Banyan Tree))
B 55532 Room below (#R49152(The Off Licence))
B 55533 Unused
D 55536 The next 8 bytes define the guardians.
B 55536,2 Guardian 1
B 55538,2 Guardian 2
B 55540,2 Guardian 3
B 55542,2 Guardian 4
B 55544,1 Terminator
B 55545,7,7 Unused
b 55552 Room 25: Cold Store
D 55552 #UDGTABLE { #ROOM55552 } TABLE#
D 55552 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 55552,128,8 Room layout
D 55680 The next 32 bytes contain the room name.
T 55680,32 Room name
D 55712 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 55712 #UDGTABLE { #UDG55713,14(background25) | #UDG55722,13(floor25) | #UDG55731,34(wall25) | #UDG55740,79(nasty25) | #UDG55749,255(ramp25) | #UDG55758,255(conveyor25) } TABLE#
B 55712,9,9 Background
B 55721,9,9 Floor
B 55730,9,9 Wall
B 55739,9,9 Nasty
B 55748,9,9 Ramp (unused)
B 55757,9,9 Conveyor (unused)
D 55766 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 55766,4 Conveyor direction (left), location (x=0, y=0) and length (0)
B 55770,4 Ramp direction (left), location (x=0, y=0) and length (0)
D 55774 The next byte specifies the border colour.
B 55774 Border colour
B 55775 Unused
D 55777 The next 8 bytes define the object graphic.
D 55777 #UDGTABLE { #UDG55777,11(object25) } TABLE#
B 55777,8,8 Object graphic
D 55785 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 55785 Room to the left (#R62464(Back Stairway))
B 55786 Room to the right (#R55296(West of Kitchen))
B 55787 Room above (#R57088(Swimming Pool))
B 55788 Room below (#R49152(The Off Licence))
B 55789 Unused
D 55792 The next 10 bytes define the guardians.
B 55792,2 Guardian 1
B 55794,2 Guardian 2
B 55796,2 Guardian 3
B 55798,2 Guardian 4
B 55800,2 Guardian 5
B 55802,1 Terminator
B 55803,5,5 Unused
b 55808 Room 26: East Wall Base
D 55808 #UDGTABLE { #ROOM55808 } TABLE#
D 55808 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 55808,128,8 Room layout
D 55936 The next 32 bytes contain the room name.
T 55936,32 Room name
D 55968 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 55968 #UDGTABLE { #UDG55969,0(background26) | #UDG55978,5(floor26) | #UDG55987,38(wall26) | #UDG55996,255(nasty26) | #UDG56005,255(ramp26) | #UDG56014,255(conveyor26) } TABLE#
B 55968,9,9 Background
B 55977,9,9 Floor
B 55986,9,9 Wall
B 55995,9,9 Nasty (unused)
B 56004,9,9 Ramp (unused)
B 56013,9,9 Conveyor (unused)
D 56022 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 56022,4 Conveyor direction (left), location (x=0, y=0) and length (0)
B 56026,4 Ramp direction (left), location (x=0, y=0) and length (0)
D 56030 The next byte specifies the border colour.
B 56030 Border colour
B 56031 Unused
D 56033 The next 8 bytes define the object graphic.
D 56033 #UDGTABLE { #UDG56033,3(object26) } TABLE#
B 56033,8,8 Object graphic (unused)
D 56041 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 56041 Room to the left (#R56064(The Chapel))
B 56042 Room to the right (#R49152(The Off Licence))
B 56043 Room above (#R57344(Halfway up the East Wall))
B 56044 Room below (#R54272(Ballroom East))
B 56045 Unused
D 56048 The next 4 bytes define the guardians.
B 56048,2 Guardian 1
B 56050,2 Guardian 2
B 56052,1 Terminator
B 56053,11,11 Unused
b 56064 Room 27: The Chapel
D 56064 #UDGTABLE { #ROOM56064 } TABLE#
D 56064 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 56064,128,8 Room layout
D 56192 The next 32 bytes contain the room name.
T 56192,32 Room name
D 56224 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 56224 #UDGTABLE { #UDG56225,0(background27) | #UDG56234,13(floor27) | #UDG56243,22(wall27) | #UDG56252,66(nasty27) | #UDG56261,7(ramp27) | #UDG56270,7(conveyor27) } TABLE#
B 56224,9,9 Background
B 56233,9,9 Floor
B 56242,9,9 Wall
B 56251,9,9 Nasty (unused)
B 56260,9,9 Ramp
B 56269,9,9 Conveyor (unused)
D 56278 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 56278,4 Conveyor direction (left), location (x=0, y=0) and length (0)
B 56282,4 Ramp direction (right), location (x=17, y=13) and length (7)
D 56286 The next byte specifies the border colour.
B 56286 Border colour
B 56287 Unused
D 56289 The next 8 bytes define the object graphic.
D 56289 #UDGTABLE { #UDG56289,3(object27) } TABLE#
B 56289,8,8 Object graphic
D 56297 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 56297 Room to the left (#R56320(First Landing))
B 56298 Room to the right (#R55808(East Wall Base))
B 56299 Room above (#R57600(The Bathroom))
B 56300 Room below (#R54528(Ballroom West))
B 56301 Unused
D 56304 The next 12 bytes define the guardians.
B 56304,2 Guardian 1
B 56306,2 Guardian 2
B 56308,2 Guardian 3
B 56310,2 Guardian 4
B 56312,2 Guardian 5
B 56314,2 Guardian 6
B 56316,1 Terminator
B 56317,3,3 Unused
b 56320 Room 28: First Landing
D 56320 #UDGTABLE { #ROOM56320(first_landing.gif) } TABLE#
D 56320 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 56320,128,8 Room layout
D 56448 The next 32 bytes contain the room name.
T 56448,32 Room name
D 56480 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 56480 #UDGTABLE { #UDG56481,0(background28) | #UDG56490,4(floor28) | #UDG56499,14(wall28) | #UDG56508,214(nasty28.gif) | #UDG56517,7(ramp28) | #UDG56526,255(conveyor28) } TABLE#
B 56480,9,9 Background
B 56489,9,9 Floor
B 56498,9,9 Wall
B 56507,9,9 Nasty
B 56516,9,9 Ramp
B 56525,9,9 Conveyor (unused)
D 56534 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 56534,4 Conveyor direction (left), location (x=0, y=0) and length (0)
B 56538,4 Ramp direction (right), location (x=9, y=14) and length (15)
D 56542 The next byte specifies the border colour.
B 56542 Border colour
B 56543 Unused
D 56545 The next 8 bytes define the object graphic.
D 56545 #UDGTABLE { #UDG56545,3(object28) } TABLE#
B 56545,8,8 Object graphic
D 56553 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 56553 Room to the left (#R56576(The Nightmare Room))
B 56554 Room to the right (#R56064(The Chapel))
B 56555 Room above (#R57856(Top Landing))
B 56556 Room below (#R54784(#SPACE(0)To#SPACE(1)the#SPACE(1)Kitchens#SPACE(4)Main#SPACE(1)Stairway))
B 56557 Unused
D 56560 The next 2 bytes define the guardians.
B 56560,2 Guardian 1
B 56562,1 Terminator
B 56563,13,13 Unused
b 56576 Room 29: The Nightmare Room
D 56576 #UDGTABLE { #ROOM56576(the_nightmare_room.gif) } TABLE#
D 56576 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 56576,128,8 Room layout
D 56704 The next 32 bytes contain the room name.
T 56704,32 Room name
D 56736 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room. Note that because of a bug in the game engine, the conveyor tile is not drawn correctly (see the room image above).
D 56736 #UDGTABLE { #UDG56737,0(background29) | #UDG56746,68(floor29) | #UDG56755,51(wall29) | #UDG56764,69(nasty29) | #UDG56773,7(ramp29) | #UDG56782,165(conveyor29.gif) } TABLE#
B 56736,9,9 Background
B 56745,9,9 Floor
B 56754,9,9 Wall
B 56763,9,9 Nasty (unused)
B 56772,9,9 Ramp
B 56781,9,9 Conveyor
D 56790 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 56790,4 Conveyor direction (left), location (x=27, y=7) and length (1)
B 56794,4 Ramp direction (left), location (x=9, y=14) and length (3)
D 56798 The next byte specifies the border colour.
B 56798 Border colour
B 56799 Unused
D 56801 The next 8 bytes define the object graphic.
D 56801 #UDGTABLE { #UDG56801,3(object29) } TABLE#
B 56801,8,8 Object graphic
D 56809 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 56809 Room to the left (#R56832(The Banyan Tree))
B 56810 Room to the right (#R56320(First Landing))
B 56811 Room above (#R49152(The Off Licence))
B 56812 Room below (#R49152(The Off Licence))
B 56813 Unused
D 56816 The next 14 bytes define the guardians.
B 56816,2 Guardian 1
B 56818,2 Guardian 2
B 56820,2 Guardian 3
B 56822,2 Guardian 4
B 56824,2 Guardian 5
B 56826,2 Guardian 6
B 56828,2 Guardian 7
B 56830,1 Terminator
B 56831,1,1 Unused
b 56832 Room 30: The Banyan Tree
D 56832 #UDGTABLE { #ROOM56832 } TABLE#
D 56832 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 56832,128,8 Room layout
D 56960 The next 32 bytes contain the room name.
T 56960,32 Room name
D 56992 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 56992 #UDGTABLE { #UDG56993,0(background30) | #UDG57002,72(floor30) | #UDG57011,22(wall30) | #UDG57020,14(nasty30) | #UDG57029,7(ramp30) | #UDG57038,255(conveyor30) } TABLE#
B 56992,9,9 Background
B 57001,9,9 Floor
B 57010,9,9 Wall
B 57019,9,9 Nasty (unused)
B 57028,9,9 Ramp
B 57037,9,9 Conveyor (unused)
D 57046 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 57046,4 Conveyor direction (left), location (x=0, y=0) and length (0)
B 57050,4 Ramp direction (right), location (x=4, y=11) and length (8)
D 57054 The next byte specifies the border colour.
B 57054 Border colour
B 57055 Unused
D 57057 The next 8 bytes define the object graphic.
D 57057 #UDGTABLE { #UDG57057,3(object30) } TABLE#
B 57057,8,8 Object graphic
D 57065 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 57065 Room to the left (#R57088(Swimming Pool))
B 57066 Room to the right (#R56576(The Nightmare Room))
B 57067 Room above (#R58368(A bit of tree))
B 57068 Room below (#R55296(West of Kitchen))
B 57069 Unused
D 57072 The next 8 bytes define the guardians.
B 57072,2 Guardian 1
B 57074,2 Guardian 2
B 57076,2 Guardian 3
B 57078,2 Guardian 4
B 57080,1 Terminator
B 57081,7,7 Unused
b 57088 Room 31: Swimming Pool
D 57088 #UDGTABLE { #ROOM57088 } TABLE#
D 57088 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 57088,128,8 Room layout
D 57216 The next 32 bytes contain the room name.
T 57216,32 Room name
D 57248 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 57248 #UDGTABLE { #UDG57249,7(background31) | #UDG57258,41(floor31) | #UDG57267,58(wall31) | #UDG57276,255(nasty31) | #UDG57285,47(ramp31) | #UDG57294,255(conveyor31) } TABLE#
B 57248,9,9 Background
B 57257,9,9 Floor
B 57266,9,9 Wall
B 57275,9,9 Nasty (unused)
B 57284,9,9 Ramp
B 57293,9,9 Conveyor (unused)
D 57302 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 57302,4 Conveyor direction (left), location (x=0, y=0) and length (0)
B 57306,4 Ramp direction (right), location (x=25, y=14) and length (3)
D 57310 The next byte specifies the border colour.
B 57310 Border colour
B 57311 Unused
D 57313 The next 8 bytes define the object graphic.
D 57313 #UDGTABLE { #UDG57313,3(object31) } TABLE#
B 57313,8,8 Object graphic
D 57321 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 57321 Room to the left (#R62976(#SPACE(0)West#SPACE(2)Wing))
B 57322 Room to the right (#R56832(The Banyan Tree))
B 57323 Room above (#R58624(Orangery))
B 57324 Room below (#R49152(The Off Licence))
B 57325 Unused
D 57328 The next 4 bytes define the guardians.
B 57328,2 Guardian 1
B 57330,2 Guardian 2
B 57332,1 Terminator
B 57333,11,11 Unused
b 57344 Room 32: Halfway up the East Wall
D 57344 #UDGTABLE { #ROOM57344 } TABLE#
D 57344 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 57344,128,8 Room layout
D 57472 The next 32 bytes contain the room name.
T 57472,32 Room name
D 57504 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 57504 #UDGTABLE { #UDG57505,0(background32) | #UDG57514,5(floor32) | #UDG57523,15(wall32) | #UDG57532,255(nasty32) | #UDG57541,7(ramp32) | #UDG57550,7(conveyor32) } TABLE#
B 57504,9,9 Background
B 57513,9,9 Floor
B 57522,9,9 Wall
B 57531,9,9 Nasty (unused)
B 57540,9,9 Ramp
B 57549,9,9 Conveyor (unused)
D 57558 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 57558,4 Conveyor direction (right), location (x=0, y=0) and length (0)
B 57562,4 Ramp direction (left), location (x=11, y=7) and length (6)
D 57566 The next byte specifies the border colour.
B 57566 Border colour
B 57567 Unused
D 57569 The next 8 bytes define the object graphic.
D 57569 #UDGTABLE { #UDG57569,3(object32) } TABLE#
B 57569,8,8 Object graphic (unused)
D 57577 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 57577 Room to the left (#R57600(The Bathroom))
B 57578 Room to the right (#R49152(The Off Licence))
B 57579 Room above (#R58880(Priests' Hole))
B 57580 Room below (#R55808(East Wall Base))
B 57581 Unused
D 57584 The next 2 bytes define the guardians.
B 57584,2 Guardian 1
B 57586,1 Terminator
B 57587,13,13 Unused
b 57600 Room 33: The Bathroom
D 57600 #UDGTABLE { #ROOM57600 } TABLE#
D 57600 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 57600,128,8 Room layout
D 57728 The next 32 bytes contain the room name.
T 57728,32 Room name
D 57760 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 57760 #UDGTABLE { #UDG57761,0(background33) | #UDG57770,22(floor33) | #UDG57779,14(wall33) | #UDG57788,255(nasty33) | #UDG57797,7(ramp33) | #UDG57806,61(conveyor33) } TABLE#
B 57760,9,9 Background
B 57769,9,9 Floor
B 57778,9,9 Wall
B 57787,9,9 Nasty (unused)
B 57796,9,9 Ramp
B 57805,9,9 Conveyor
D 57814 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 57814,4 Conveyor direction (left), location (x=20, y=14) and length (4)
B 57818,4 Ramp direction (right), location (x=9, y=12) and length (8)
D 57822 The next byte specifies the border colour.
B 57822 Border colour
B 57823 Unused
D 57825 The next 8 bytes define the object graphic.
D 57825 #UDGTABLE { #UDG57825,3(object33) } TABLE#
B 57825,8,8 Object graphic
D 57833 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 57833 Room to the left (#R57856(Top Landing))
B 57834 Room to the right (#R57344(Halfway up the East Wall))
B 57835 Room above (#R59136(Emergency Generator))
B 57836 Room below (#R56064(The Chapel))
B 57837 Unused
D 57840 The next 2 bytes define the guardians.
B 57840,2 Guardian 1
B 57842,1 Terminator
B 57843,13,13 Unused
b 57856 Room 34: Top Landing
D 57856 #UDGTABLE { #ROOM57856 } TABLE#
D 57856 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 57856,128,8 Room layout
D 57984 The next 32 bytes contain the room name.
T 57984,32 Room name
D 58016 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 58016 #UDGTABLE { #UDG58017,0(background34) | #UDG58026,6(floor34) | #UDG58035,26(wall34) | #UDG58044,255(nasty34) | #UDG58053,7(ramp34) | #UDG58062,255(conveyor34) } TABLE#
B 58016,9,9 Background
B 58025,9,9 Floor
B 58034,9,9 Wall
B 58043,9,9 Nasty (unused)
B 58052,9,9 Ramp
B 58061,9,9 Conveyor (unused)
D 58070 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 58070,4 Conveyor direction (left), location (x=0, y=0) and length (0)
B 58074,4 Ramp direction (right), location (x=17, y=11) and length (7)
D 58078 The next byte specifies the border colour.
B 58078 Border colour
B 58079 Unused
D 58081 The next 8 bytes define the object graphic.
D 58081 #UDGTABLE { #UDG58081,3(object34) } TABLE#
B 58081,8,8 Object graphic
D 58089 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 58089 Room to the left (#R58112(Master Bedroom))
B 58090 Room to the right (#R57600(The Bathroom))
B 58091 Room above (#R59392(Dr Jones will never believe this))
B 58092 Room below (#R56320(First Landing))
B 58093 Unused
D 58096 The next 6 bytes define the guardians.
B 58096,2 Guardian 1
B 58098,2 Guardian 2
B 58100,2 Guardian 3
B 58102,1 Terminator
B 58103,9,9 Unused
b 58112 Room 35: Master Bedroom
D 58112 #UDGTABLE { #ROOM58112 } TABLE#
D 58112 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 58112,128,8 Room layout
D 58240 The next 32 bytes contain the room name.
T 58240,32 Room name
D 58272 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 58272 #UDGTABLE { #UDG58273,0(background35) | #UDG58282,6(floor35) | #UDG58291,51(wall35) | #UDG58300,71(nasty35) | #UDG58309,7(ramp35) | #UDG58318,41(conveyor35) } TABLE#
B 58272,9,9 Background
B 58281,9,9 Floor
B 58290,9,9 Wall
B 58299,9,9 Nasty
B 58308,9,9 Ramp
B 58317,9,9 Conveyor
D 58326 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 58326,4 Conveyor direction (right), location (x=2, y=12) and length (4)
B 58330,4 Ramp direction (left), location (x=18, y=14) and length (2)
D 58334 The next byte specifies the border colour.
B 58334 Border colour
B 58335 Unused
D 58337 The next 8 bytes define the object graphic.
D 58337 #UDGTABLE { #UDG58337,3(object35) } TABLE#
B 58337,8,8 Object graphic (unused)
D 58345 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 58345 Room to the left (#R58368(A bit of tree))
B 58346 Room to the right (#R57856(Top Landing))
B 58347 Room above (#R59648(The Attic))
B 58348 Room below (#R56576(The Nightmare Room))
B 58349 Unused
D 58352 There are no guardians in this room.
B 58352,1 Terminator
B 58353,15,15 Unused
b 58368 Room 36: A bit of tree
D 58368 #UDGTABLE { #ROOM58368 } TABLE#
D 58368 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 58368,128,8 Room layout
D 58496 The next 32 bytes contain the room name.
T 58496,32 Room name
D 58528 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 58528 #UDGTABLE { #UDG58529,0(background36) | #UDG58538,4(floor36) | #UDG58547,30(wall36) | #UDG58556,2(nasty36) | #UDG58565,68(ramp36) | #UDG58574,255(conveyor36) } TABLE#
B 58528,9,9 Background
B 58537,9,9 Floor
B 58546,9,9 Wall
B 58555,9,9 Nasty
B 58564,9,9 Ramp
B 58573,9,9 Conveyor (unused)
D 58582 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 58582,4 Conveyor direction (left), location (x=0, y=0) and length (0)
B 58586,4 Ramp direction (right), location (x=20, y=9) and length (2)
D 58590 The next byte specifies the border colour.
B 58590 Border colour
B 58591 Unused
D 58593 The next 8 bytes define the object graphic.
D 58593 #UDGTABLE { #UDG58593,3(object36) } TABLE#
B 58593,8,8 Object graphic (unused)
D 58601 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 58601 Room to the left (#R58624(Orangery))
B 58602 Room to the right (#R58112(Master Bedroom))
B 58603 Room above (#R59904(Under the Roof))
B 58604 Room below (#R56832(The Banyan Tree))
B 58605 Unused
D 58608 The next 6 bytes define the guardians.
B 58608,2 Guardian 1
B 58610,2 Guardian 2
B 58612,2 Guardian 3
B 58614,1 Terminator
B 58615,9,9 Unused
b 58624 Room 37: Orangery
D 58624 #UDGTABLE { #ROOM58624 } TABLE#
D 58624 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 58624,128,8 Room layout
D 58752 The next 32 bytes contain the room name.
T 58752,32 Room name
D 58784 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 58784 #UDGTABLE { #UDG58785,0(background37) | #UDG58794,4(floor37) | #UDG58803,22(wall37) | #UDG58812,6(nasty37) | #UDG58821,5(ramp37) | #UDG58830,38(conveyor37) } TABLE#
B 58784,9,9 Background
B 58793,9,9 Floor
B 58802,9,9 Wall
B 58811,9,9 Nasty (unused)
B 58820,9,9 Ramp
B 58829,9,9 Conveyor
D 58838 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 58838,4 Conveyor direction (left), location (x=28, y=10) and length (4)
B 58842,4 Ramp direction (right), location (x=0, y=13) and length (14)
D 58846 The next byte specifies the border colour.
B 58846 Border colour
B 58847 Unused
D 58849 The next 8 bytes define the object graphic.
D 58849 #UDGTABLE { #UDG58849,3(object37) } TABLE#
B 58849,8,8 Object graphic
D 58857 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 58857 Room to the left (#R63488(West Wing Roof))
B 58858 Room to the right (#R58368(A bit of tree))
B 58859 Room above (#R60160(Conservatory Roof))
B 58860 Room below (#R57088(Swimming Pool))
B 58861 Unused
D 58864 The next 6 bytes define the guardians.
B 58864,2 Guardian 1
B 58866,2 Guardian 2
B 58868,2 Guardian 3
B 58870,1 Terminator
B 58871,9,9 Unused
b 58880 Room 38: Priests' Hole
D 58880 #UDGTABLE { #ROOM58880 } TABLE#
D 58880 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 58880,128,8 Room layout
D 59008 The next 32 bytes contain the room name.
T 59008,32 Room name
D 59040 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 59040 #UDGTABLE { #UDG59041,0(background38) | #UDG59050,6(floor38) | #UDG59059,42(wall38) | #UDG59068,255(nasty38) | #UDG59077,255(ramp38) | #UDG59086,255(conveyor38) } TABLE#
B 59040,9,9 Background
B 59049,9,9 Floor
B 59058,9,9 Wall
B 59067,9,9 Nasty (unused)
B 59076,9,9 Ramp (unused)
B 59085,9,9 Conveyor (unused)
D 59094 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 59094,4 Conveyor direction (left), location (x=0, y=0) and length (0)
B 59098,4 Ramp direction (left), location (x=0, y=0) and length (0)
D 59102 The next byte specifies the border colour.
B 59102 Border colour
B 59103 Unused
D 59105 The next 8 bytes define the object graphic.
D 59105 #UDGTABLE { #UDG59105,3(object38) } TABLE#
B 59105,8,8 Object graphic
D 59113 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 59113 Room to the left (#R59136(Emergency Generator))
B 59114 Room to the right (#R49152(The Off Licence))
B 59115 Room above (#R64512(The Bow))
B 59116 Room below (#R57344(Halfway up the East Wall))
B 59117 Unused
D 59120 The next 8 bytes define the guardians.
B 59120,2 Guardian 1
B 59122,2 Guardian 2
B 59124,2 Guardian 3
B 59126,2 Guardian 4
B 59128,1 Terminator
B 59129,7,7 Unused
b 59136 Room 39: Emergency Generator
D 59136 #UDGTABLE { #ROOM59136 } TABLE#
D 59136 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 59136,128,8 Room layout
D 59264 The next 32 bytes contain the room name.
T 59264,32 Room name
D 59296 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 59296 #UDGTABLE { #UDG59297,8(background39) | #UDG59306,47(floor39) | #UDG59315,51(wall39) | #UDG59324,13(nasty39) | #UDG59333,15(ramp39) | #UDG59342,22(conveyor39) } TABLE#
B 59296,9,9 Background
B 59305,9,9 Floor
B 59314,9,9 Wall
B 59323,9,9 Nasty
B 59332,9,9 Ramp
B 59341,9,9 Conveyor
D 59350 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 59350,4 Conveyor direction (left), location (x=9, y=11) and length (14)
B 59354,4 Ramp direction (right), location (x=18, y=10) and length (6)
D 59358 The next byte specifies the border colour.
B 59358 Border colour
B 59359 Unused
D 59361 The next 8 bytes define the object graphic.
D 59361 #UDGTABLE { #UDG59361,11(object39) } TABLE#
B 59361,8,8 Object graphic (unused)
D 59369 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 59369 Room to the left (#R59392(Dr Jones will never believe this))
B 59370 Room to the right (#R58880(Priests' Hole))
B 59371 Room above (#R52736(Rescue Esmerelda))
B 59372 Room below (#R49152(The Off Licence))
B 59373 Unused
D 59376 The next 2 bytes define the guardians.
B 59376,2 Guardian 1
B 59378,1 Terminator
B 59379,13,13 Unused
b 59392 Room 40: Dr Jones will never believe this
D 59392 #UDGTABLE { #ROOM59392 } TABLE#
D 59392 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 59392,128,8 Room layout
D 59520 The next 32 bytes contain the room name.
T 59520,32 Room name
D 59552 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 59552 #UDGTABLE { #UDG59553,0(background40) | #UDG59562,2(floor40) | #UDG59571,31(wall40) | #UDG59580,67(nasty40) | #UDG59589,5(ramp40) | #UDG59598,38(conveyor40) } TABLE#
B 59552,9,9 Background
B 59561,9,9 Floor
B 59570,9,9 Wall
B 59579,9,9 Nasty
B 59588,9,9 Ramp
B 59597,9,9 Conveyor
D 59606 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 59606,4 Conveyor direction (left), location (x=0, y=15) and length (32)
B 59610,4 Ramp direction (left), location (x=24, y=10) and length (5)
D 59614 The next byte specifies the border colour.
B 59614 Border colour
B 59615 Unused
D 59617 The next 8 bytes define the object graphic.
D 59617 #UDGTABLE { #UDG59617,3(object40) } TABLE#
B 59617,8,8 Object graphic
D 59625 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 59625 Room to the left (#R59648(The Attic))
B 59626 Room to the right (#R59136(Emergency Generator))
B 59627 Room above (#R53248(We must perform a Quirkafleeg))
B 59628 Room below (#R49152(The Off Licence))
B 59629 Unused
D 59632 The next 4 bytes define the guardians.
B 59632,2 Guardian 1
B 59634,2 Guardian 2
B 59636,1 Terminator
B 59637,11,11 Unused
b 59648 Room 41: The Attic
D 59648 #UDGTABLE { #ROOM59648 } TABLE#
D 59648 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 59648,128,8 Room layout
D 59776 The next 32 bytes contain the room name.
T 59776,32 Room name
D 59808 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 59808 #UDGTABLE { #UDG59809,0(background41) | #UDG59818,22(floor41) | #UDG59827,30(wall41) | #UDG59836,68(nasty41) | #UDG59845,255(ramp41) | #UDG59854,66(conveyor41) } TABLE#
B 59808,9,9 Background
B 59817,9,9 Floor
B 59826,9,9 Wall
B 59835,9,9 Nasty
B 59844,9,9 Ramp (unused)
B 59853,9,9 Conveyor
D 59862 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 59862,4 Conveyor direction (right), location (x=24, y=8) and length (4)
B 59866,4 Ramp direction (left), location (x=0, y=0) and length (0)
D 59870 The next byte specifies the border colour.
B 59870 Border colour
B 59871 Unused
D 59873 The next 8 bytes define the object graphic.
D 59873 #UDGTABLE { #UDG59873,3(object41) } TABLE#
B 59873,8,8 Object graphic (unused)
D 59881 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 59881 Room to the left (#R59904(Under the Roof))
B 59882 Room to the right (#R59392(Dr Jones will never believe this))
B 59883 Room above (#R49152(The Off Licence))
B 59884 Room below (#R57856(Top Landing))
B 59885 Unused
D 59888 The next 16 bytes define the guardians.
B 59888,2 Guardian 1
B 59890,2 Guardian 2
B 59892,2 Guardian 3
B 59894,2 Guardian 4
B 59896,2 Guardian 5
B 59898,2 Guardian 6
B 59900,2 Guardian 7
B 59902,2 Guardian 8
b 59904 Room 42: Under the Roof
D 59904 #UDGTABLE { #ROOM59904(under_the_roof.gif) } TABLE#
D 59904 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 59904,128,8 Room layout
D 60032 The next 32 bytes contain the room name.
T 60032,32 Room name
D 60064 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 60064 #UDGTABLE { #UDG60065,8(background42) | #UDG60074,12(floor42) | #UDG60083,30(wall42) | #UDG60092,245(nasty42.gif) | #UDG60101,15(ramp42) | #UDG60110,14(conveyor42) } TABLE#
B 60064,9,9 Background
B 60073,9,9 Floor
B 60082,9,9 Wall
B 60091,9,9 Nasty
B 60100,9,9 Ramp
B 60109,9,9 Conveyor
D 60118 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 60118,4 Conveyor direction (right), location (x=12, y=6) and length (20)
B 60122,4 Ramp direction (right), location (x=4, y=6) and length (7)
D 60126 The next byte specifies the border colour.
B 60126 Border colour
B 60127 Unused
D 60129 The next 8 bytes define the object graphic.
D 60129 #UDGTABLE { #UDG60129,11(object42) } TABLE#
B 60129,8,8 Object graphic (unused)
D 60137 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 60137 Room to the left (#R60160(Conservatory Roof))
B 60138 Room to the right (#R59648(The Attic))
B 60139 Room above (#R61440(Nomen Luni))
B 60140 Room below (#R58368(A bit of tree))
B 60141 Unused
D 60144 The next 6 bytes define the guardians.
B 60144,2 Guardian 1
B 60146,2 Guardian 2
B 60148,2 Guardian 3
B 60150,1 Terminator
B 60151,9,9 Unused
b 60160 Room 43: Conservatory Roof
D 60160 #UDGTABLE { #ROOM60160 } TABLE#
D 60160 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 60160,128,8 Room layout
D 60288 The next 32 bytes contain the room name.
T 60288,32 Room name
D 60320 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 60320 #UDGTABLE { #UDG60321,0(background43) | #UDG60330,4(floor43) | #UDG60339,5(wall43) | #UDG60348,67(nasty43) | #UDG60357,7(ramp43) | #UDG60366,255(conveyor43) } TABLE#
B 60320,9,9 Background
B 60329,9,9 Floor
B 60338,9,9 Wall
B 60347,9,9 Nasty
B 60356,9,9 Ramp
B 60365,9,9 Conveyor
D 60374 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 60374,4 Conveyor direction (right), location (x=26, y=13) and length (6)
B 60378,4 Ramp direction (right), location (x=12, y=15) and length (9)
D 60382 The next byte specifies the border colour.
B 60382 Border colour
B 60383 Unused
D 60385 The next 8 bytes define the object graphic.
D 60385 #UDGTABLE { #UDG60385,3(object43) } TABLE#
B 60385,8,8 Object graphic
D 60393 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 60393 Room to the left (#R49152(The Off Licence))
B 60394 Room to the right (#R59904(Under the Roof))
B 60395 Room above (#R49152(The Off Licence))
B 60396 Room below (#R58624(Orangery))
B 60397 Unused
D 60400 The next 4 bytes define the guardians.
B 60400,2 Guardian 1
B 60402,2 Guardian 2
B 60404,1 Terminator
B 60405,11,11 Unused
b 60416 Room 44: On top of the house
D 60416 #UDGTABLE { #ROOM60416 } TABLE#
D 60416 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 60416,128,8 Room layout
D 60544 The next 32 bytes contain the room name.
T 60544,32 Room name
D 60576 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 60576 #UDGTABLE { #UDG60577,8(background44) | #UDG60586,14(floor44) | #UDG60595,75(wall44) | #UDG60604,255(nasty44) | #UDG60613,15(ramp44) | #UDG60622,255(conveyor44) } TABLE#
B 60576,9,9 Background
B 60585,9,9 Floor
B 60594,9,9 Wall
B 60603,9,9 Nasty (unused)
B 60612,9,9 Ramp
B 60621,9,9 Conveyor (unused)
D 60630 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 60630,4 Conveyor direction (left), location (x=0, y=0) and length (0)
B 60634,4 Ramp direction (right), location (x=12, y=10) and length (6)
D 60638 The next byte specifies the border colour.
B 60638 Border colour
B 60639 Unused
D 60641 The next 8 bytes define the object graphic.
D 60641 #UDGTABLE { #UDG60641,11(object44) } TABLE#
B 60641,8,8 Object graphic
D 60649 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 60649 Room to the left (#R52736(Rescue Esmerelda))
B 60650 Room to the right (#R49152(The Off Licence))
B 60651 Room above (#R49152(The Off Licence))
B 60652 Room below (#R58880(Priests' Hole))
B 60653 Unused
D 60656 The next 2 bytes define the guardians.
B 60656,2 Guardian 1
B 60658,1 Terminator
B 60659,13,13 Unused
b 60672 Room 45: Under the Drive
D 60672 #UDGTABLE { #ROOM60672 } TABLE#
D 60672 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 60672,128,8 Room layout
D 60800 The next 32 bytes contain the room name.
T 60800,32 Room name
D 60832 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 60832 #UDGTABLE { #UDG60833,0(background45) | #UDG60842,6(floor45) | #UDG60851,12(wall45) | #UDG60860,4(nasty45) | #UDG60869,7(ramp45) | #UDG60878,2(conveyor45) } TABLE#
B 60832,9,9 Background
B 60841,9,9 Floor
B 60850,9,9 Wall
B 60859,9,9 Nasty
B 60868,9,9 Ramp
B 60877,9,9 Conveyor
D 60886 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 60886,4 Conveyor direction (left), location (x=18, y=10) and length (14)
B 60890,4 Ramp direction (left), location (x=13, y=14) and length (12)
D 60894 The next byte specifies the border colour.
B 60894 Border colour
B 60895 Unused
D 60897 The next 8 bytes define the object graphic.
D 60897 #UDGTABLE { #UDG60897,3(object45) } TABLE#
B 60897,8,8 Object graphic (unused)
D 60905 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 60905 Room to the left (#R50688(Entrance to Hades))
B 60906 Room to the right (#R60928(Tree Root))
B 60907 Room above (#R50176(The Drive))
B 60908 Room below (#R49152(The Off Licence))
B 60909 Unused
D 60912 The next 6 bytes define the guardians.
B 60912,2 Guardian 1
B 60914,2 Guardian 2
B 60916,2 Guardian 3
B 60918,1 Terminator
B 60919,9,9 Unused
b 60928 Room 46: Tree Root
D 60928 #UDGTABLE { #ROOM60928 } TABLE#
D 60928 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 60928,128,8 Room layout
D 61056 The next 32 bytes contain the room name.
T 61056,32 Room name
D 61088 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 61088 #UDGTABLE { #UDG61089,0(background46) | #UDG61098,6(floor46) | #UDG61107,10(wall46) | #UDG61116,2(nasty46) | #UDG61125,67(ramp46) | #UDG61134,4(conveyor46) } TABLE#
B 61088,9,9 Background
B 61097,9,9 Floor
B 61106,9,9 Wall
B 61115,9,9 Nasty
B 61124,9,9 Ramp
B 61133,9,9 Conveyor
D 61142 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 61142,4 Conveyor direction (left), location (x=0, y=10) and length (13)
B 61146,4 Ramp direction (right), location (x=24, y=14) and length (6)
D 61150 The next byte specifies the border colour.
B 61150 Border colour
B 61151 Unused
D 61153 The next 8 bytes define the object graphic.
D 61153 #UDGTABLE { #UDG61153,3(object46) } TABLE#
B 61153,8,8 Object graphic
D 61161 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 61161 Room to the left (#R60672(Under the Drive))
B 61162 Room to the right (#R61184([))
B 61163 Room above (#R49920(At the Foot of the MegaTree))
B 61164 Room below (#R49152(The Off Licence))
B 61165 Unused
D 61168 The next 8 bytes define the guardians.
B 61168,2 Guardian 1
B 61170,2 Guardian 2
B 61172,2 Guardian 3
B 61174,2 Guardian 4
B 61176,1 Terminator
B 61177,7,7 Unused
b 61184 Room 47: [
D 61184 #UDGTABLE { #ROOM61184(left_square_bracket) } TABLE#
D 61184 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 61184,128,8 Room layout
D 61312 The next 32 bytes contain the room name.
T 61312,32 Room name
D 61344 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 61344 #UDGTABLE { #UDG61345,0(background47) | #UDG61354,0(floor47) | #UDG61363,54(wall47) | #UDG61372,255(nasty47) | #UDG61381,7(ramp47) | #UDG61390,245(conveyor47.gif) } TABLE#
B 61344,9,9 Background
B 61353,9,9 Floor (unused)
B 61362,9,9 Wall (unused)
B 61371,9,9 Nasty (unused)
B 61380,9,9 Ramp (unused)
B 61389,9,9 Conveyor (unused)
D 61398 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 61398,4 Conveyor direction (right), location (x=18, y=7) and length (0)
B 61402,4 Ramp direction (right), location (x=9, y=14) and length (0)
D 61406 The next byte specifies the border colour.
B 61406 Border colour
B 61407 Unused
D 61409 The next 8 bytes define the object graphic.
D 61409 #UDGTABLE { #UDG61409,3(object47) } TABLE#
B 61409,8,8 Object graphic (unused)
D 61417 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 61417 Room to the left (#R56576(The Nightmare Room))
B 61418 Room to the right (none)
B 61419 Room above (#R56320(First Landing))
B 61420 Room below (#R60160(Conservatory Roof))
B 61421 Unused
D 61424 There are no guardians in this room.
B 61424,1 Terminator
B 61425,15,15 Unused
b 61440 Room 48: Nomen Luni
D 61440 #UDGTABLE { #ROOM61440(nomen_luni.gif) } TABLE#
D 61440 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 61440,128,8 Room layout
D 61568 The next 32 bytes contain the room name.
T 61568,32 Room name
D 61600 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 61600 #UDGTABLE { #UDG61601,0(background48) | #UDG61610,13(floor48) | #UDG61619,243(wall48.gif) | #UDG61628,6(nasty48) | #UDG61637,7(ramp48) | #UDG61646,255(conveyor48) } TABLE#
B 61600,9,9 Background
B 61609,9,9 Floor
B 61618,9,9 Wall
B 61627,9,9 Nasty (unused)
B 61636,9,9 Ramp
B 61645,9,9 Conveyor (unused)
D 61654 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 61654,4 Conveyor direction (left), location (x=0, y=0) and length (0)
B 61658,4 Ramp direction (right), location (x=9, y=15) and length (5)
D 61662 The next byte specifies the border colour.
B 61662 Border colour
B 61663 Unused
D 61665 The next 8 bytes define the object graphic.
D 61665 #UDGTABLE { #UDG61665,3(object48) } TABLE#
B 61665,8,8 Object graphic (unused)
D 61673 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 61673 Room to the left (#R49152(The Off Licence))
B 61674 Room to the right (#R53760(On the Roof))
B 61675 Room above (#R49152(The Off Licence))
B 61676 Room below (#R59904(Under the Roof))
B 61677 Unused
D 61680 The next 8 bytes define the guardians.
B 61680,2 Guardian 1
B 61682,2 Guardian 2
B 61684,2 Guardian 3
B 61686,2 Guardian 4
B 61688,1 Terminator
B 61689,7,7 Unused
b 61696 Room 49: The Wine Cellar
D 61696 #UDGTABLE { #ROOM61696 } TABLE#
D 61696 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 61696,128,8 Room layout
D 61824 The next 32 bytes contain the room name.
T 61824,32 Room name
D 61856 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room. Note that because of a bug in the game engine, the conveyor tile is not drawn correctly (see the room image above).
D 61856 #UDGTABLE { #UDG61857,0(background49) | #UDG61866,66(floor49) | #UDG61875,41(wall49) | #UDG61884,70(nasty49) | #UDG61893,7(ramp49) | #UDG61902,13(conveyor49) } TABLE#
B 61856,9,9 Background
B 61865,9,9 Floor
B 61874,9,9 Wall
B 61883,9,9 Nasty
B 61892,9,9 Ramp
B 61901,9,9 Conveyor
D 61910 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 61910,4 Conveyor direction (right), location (x=27, y=12) and length (5)
B 61914,4 Ramp direction (right), location (x=24, y=14) and length (3)
D 61918 The next byte specifies the border colour.
B 61918 Border colour
B 61919 Unused
D 61921 The next 8 bytes define the object graphic.
D 61921 #UDGTABLE { #UDG61921,3(object49) } TABLE#
B 61921,8,8 Object graphic
D 61929 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 61929 Room to the left (#R62208(#SPACE(0)Tool#SPACE(2)Shed))
B 61930 Room to the right (#R54016(The Forgotten Abbey))
B 61931 Room above (#R62464(Back Stairway))
B 61932 Room below (#R49152(The Off Licence))
B 61933 Unused
D 61936 The next 8 bytes define the guardians.
B 61936,2 Guardian 1
B 61938,2 Guardian 2
B 61940,2 Guardian 3
B 61942,2 Guardian 4
B 61944,1 Terminator
B 61945,7,7 Unused
b 61952 Room 50: Watch Tower
D 61952 #UDGTABLE { #ROOM61952 } TABLE#
D 61952 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 61952,128,8 Room layout
D 62080 The next 32 bytes contain the room name.
T 62080,32 Room name
D 62112 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 62112 #UDGTABLE { #UDG62113,8(background50) | #UDG62122,6(floor50) | #UDG62131,29(wall50) | #UDG62140,12(nasty50) | #UDG62149,15(ramp50) | #UDG62158,13(conveyor50) } TABLE#
B 62112,9,9 Background
B 62121,9,9 Floor
B 62130,9,9 Wall
B 62139,9,9 Nasty
B 62148,9,9 Ramp
B 62157,9,9 Conveyor
D 62166 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 62166,4 Conveyor direction (right), location (x=12, y=4) and length (8)
B 62170,4 Ramp direction (right), location (x=7, y=8) and length (5)
D 62174 The next byte specifies the border colour.
B 62174 Border colour
B 62175 Unused
D 62177 The next 8 bytes define the object graphic.
D 62177 #UDGTABLE { #UDG62177,11(object50) } TABLE#
B 62177,8,8 Object graphic
D 62185 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 62185 Room to the left (#R49152(The Off Licence))
B 62186 Room to the right (#R49152(The Off Licence))
B 62187 Room above (#R49152(The Off Licence))
B 62188 Room below (#R53248(We must perform a Quirkafleeg))
B 62189 Unused
D 62192 The next 4 bytes define the guardians.
B 62192,2 Guardian 1
B 62194,2 Guardian 2
B 62196,1 Terminator
B 62197,11,11 Unused
b 62208 Room 51: #SPACE(0)Tool#SPACE(2)Shed
D 62208 #UDGTABLE { #ROOM62208 } TABLE#
D 62208 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 62208,128,8 Room layout
D 62336 The next 32 bytes contain the room name.
T 62336,32 Room name
D 62368 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room. Note that because of a bug in the game engine, the conveyor tile is not drawn correctly (see the room image above).
D 62368 #UDGTABLE { #UDG62369,0(background51) | #UDG62378,5(floor51) | #UDG62387,30(wall51) | #UDG62396,6(nasty51) | #UDG62405,7(ramp51) | #UDG62414,68(conveyor51) } TABLE#
B 62368,9,9 Background
B 62377,9,9 Floor
B 62386,9,9 Wall
B 62395,9,9 Nasty
B 62404,9,9 Ramp
B 62413,9,9 Conveyor
D 62422 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 62422,4 Conveyor direction (right), location (x=7, y=15) and length (18)
B 62426,4 Ramp direction (right), location (x=3, y=7) and length (8)
D 62430 The next byte specifies the border colour.
B 62430 Border colour
B 62431 Unused
D 62433 The next 8 bytes define the object graphic.
D 62433 #UDGTABLE { #UDG62433,3(object51) } TABLE#
B 62433,8,8 Object graphic
D 62441 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 62441 Room to the left (#R64000(The Beach))
B 62442 Room to the right (#R61696(The Wine Cellar))
B 62443 Room above (#R62720(Back Door))
B 62444 Room below (#R49152(The Off Licence))
B 62445 Unused
D 62448 The next 6 bytes define the guardians.
B 62448,2 Guardian 1
B 62450,2 Guardian 2
B 62452,2 Guardian 3
B 62454,1 Terminator
B 62455,9,9 Unused
b 62464 Room 52: Back Stairway
D 62464 #UDGTABLE { #ROOM62464 } TABLE#
D 62464 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 62464,128,8 Room layout
D 62592 The next 32 bytes contain the room name.
T 62592,32 Room name
D 62624 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 62624 #UDGTABLE { #UDG62625,0(background52) | #UDG62634,67(floor52) | #UDG62643,30(wall52) | #UDG62652,255(nasty52) | #UDG62661,71(ramp52) | #UDG62670,255(conveyor52) } TABLE#
B 62624,9,9 Background
B 62633,9,9 Floor
B 62642,9,9 Wall
B 62651,9,9 Nasty (unused)
B 62660,9,9 Ramp
B 62669,9,9 Conveyor (unused)
D 62678 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 62678,4 Conveyor direction (left), location (x=0, y=0) and length (0)
B 62682,4 Ramp direction (right), location (x=2, y=15) and length (16)
D 62686 The next byte specifies the border colour.
B 62686 Border colour
B 62687 Unused
D 62689 The next 8 bytes define the object graphic.
D 62689 #UDGTABLE { #UDG62689,3(object52) } TABLE#
B 62689,8,8 Object graphic (unused)
D 62697 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 62697 Room to the left (#R62720(Back Door))
B 62698 Room to the right (#R55552(Cold Store))
B 62699 Room above (#R62976(#SPACE(0)West#SPACE(2)Wing))
B 62700 Room below (#R61696(The Wine Cellar))
B 62701 Unused
D 62704 The next 6 bytes define the guardians.
B 62704,2 Guardian 1
B 62706,2 Guardian 2
B 62708,2 Guardian 3
B 62710,1 Terminator
B 62711,9,9 Unused
b 62720 Room 53: Back Door
D 62720 #UDGTABLE { #ROOM62720 } TABLE#
D 62720 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 62720,128,8 Room layout
D 62848 The next 32 bytes contain the room name.
T 62848,32 Room name
D 62880 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 62880 #UDGTABLE { #UDG62881,0(background53) | #UDG62890,3(floor53) | #UDG62899,38(wall53) | #UDG62908,255(nasty53) | #UDG62917,7(ramp53) | #UDG62926,34(conveyor53) } TABLE#
B 62880,9,9 Background
B 62889,9,9 Floor
B 62898,9,9 Wall
B 62907,9,9 Nasty (unused)
B 62916,9,9 Ramp
B 62925,9,9 Conveyor
D 62934 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 62934,4 Conveyor direction (right), location (x=18, y=15) and length (14)
B 62938,4 Ramp direction (right), location (x=9, y=15) and length (5)
D 62942 The next byte specifies the border colour.
B 62942 Border colour
B 62943 Unused
D 62945 The next 8 bytes define the object graphic.
D 62945 #UDGTABLE { #UDG62945,3(object53) } TABLE#
B 62945,8,8 Object graphic (unused)
D 62953 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 62953 Room to the left (#R49152(The Off Licence))
B 62954 Room to the right (#R62464(Back Stairway))
B 62955 Room above (#R63232(West Bedroom))
B 62956 Room below (#R62208(#SPACE(0)Tool#SPACE(2)Shed))
B 62957 Unused
D 62960 There are no guardians in this room.
B 62960,1 Terminator
B 62961,15,15 Unused
b 62976 Room 54: #SPACE(0)West#SPACE(2)Wing
D 62976 #UDGTABLE { #ROOM62976 } TABLE#
D 62976 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 62976,128,8 Room layout
D 63104 The next 32 bytes contain the room name.
T 63104,32 Room name
D 63136 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 63136 #UDGTABLE { #UDG63137,0(background54) | #UDG63146,65(floor54) | #UDG63155,39(wall54) | #UDG63164,255(nasty54) | #UDG63173,7(ramp54) | #UDG63182,255(conveyor54) } TABLE#
B 63136,9,9 Background
B 63145,9,9 Floor
B 63154,9,9 Wall
B 63163,9,9 Nasty (unused)
B 63172,9,9 Ramp
B 63181,9,9 Conveyor (unused)
D 63190 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 63190,4 Conveyor direction (left), location (x=0, y=0) and length (0)
B 63194,4 Ramp direction (right), location (x=16, y=15) and length (16)
D 63198 The next byte specifies the border colour.
B 63198 Border colour
B 63199 Unused
D 63201 The next 8 bytes define the object graphic.
D 63201 #UDGTABLE { #UDG63201,3(object54) } TABLE#
B 63201,8,8 Object graphic (unused)
D 63209 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 63209 Room to the left (#R63232(West Bedroom))
B 63210 Room to the right (#R57088(Swimming Pool))
B 63211 Room above (#R63488(West Wing Roof))
B 63212 Room below (#R62464(Back Stairway))
B 63213 Unused
D 63216 The next 6 bytes define the guardians.
B 63216,2 Guardian 1
B 63218,2 Guardian 2
B 63220,2 Guardian 3
B 63222,1 Terminator
B 63223,9,9 Unused
b 63232 Room 55: West Bedroom
D 63232 #UDGTABLE { #ROOM63232 } TABLE#
D 63232 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 63232,128,8 Room layout
D 63360 The next 32 bytes contain the room name.
T 63360,32 Room name
D 63392 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 63392 #UDGTABLE { #UDG63393,0(background55) | #UDG63402,6(floor55) | #UDG63411,13(wall55) | #UDG63420,255(nasty55) | #UDG63429,255(ramp55) | #UDG63438,66(conveyor55) } TABLE#
B 63392,9,9 Background
B 63401,9,9 Floor
B 63410,9,9 Wall
B 63419,9,9 Nasty (unused)
B 63428,9,9 Ramp (unused)
B 63437,9,9 Conveyor
D 63446 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 63446,4 Conveyor direction (left), location (x=26, y=3) and length (3)
B 63450,4 Ramp direction (left), location (x=0, y=0) and length (0)
D 63454 The next byte specifies the border colour.
B 63454 Border colour
B 63455 Unused
D 63457 The next 8 bytes define the object graphic.
D 63457 #UDGTABLE { #UDG63457,3(object55) } TABLE#
B 63457,8,8 Object graphic (unused)
D 63465 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 63465 Room to the left (#R49152(The Off Licence))
B 63466 Room to the right (#R62976(#SPACE(0)West#SPACE(2)Wing))
B 63467 Room above (#R63744(Above the West Bedroom))
B 63468 Room below (#R62720(Back Door))
B 63469 Unused
D 63472 The next 4 bytes define the guardians.
B 63472,2 Guardian 1
B 63474,2 Guardian 2
B 63476,1 Terminator
B 63477,11,11 Unused
b 63488 Room 56: West Wing Roof
D 63488 #UDGTABLE { #ROOM63488 } TABLE#
D 63488 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 63488,128,8 Room layout
D 63616 The next 32 bytes contain the room name.
T 63616,32 Room name
D 63648 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 63648 #UDGTABLE { #UDG63649,0(background56) | #UDG63658,3(floor56) | #UDG63667,37(wall56) | #UDG63676,66(nasty56) | #UDG63685,7(ramp56) | #UDG63694,255(conveyor56) } TABLE#
B 63648,9,9 Background
B 63657,9,9 Floor
B 63666,9,9 Wall
B 63675,9,9 Nasty
B 63684,9,9 Ramp
B 63693,9,9 Conveyor (unused)
D 63702 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 63702,4 Conveyor direction (left), location (x=0, y=0) and length (0)
B 63706,4 Ramp direction (right), location (x=28, y=15) and length (4)
D 63710 The next byte specifies the border colour.
B 63710 Border colour
B 63711 Unused
D 63713 The next 8 bytes define the object graphic.
D 63713 #UDGTABLE { #UDG63713,3(object56) } TABLE#
B 63713,8,8 Object graphic
D 63721 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 63721 Room to the left (#R63744(Above the West Bedroom))
B 63722 Room to the right (#R58624(Orangery))
B 63723 Room above (#R49152(The Off Licence))
B 63724 Room below (#R62976(#SPACE(0)West#SPACE(2)Wing))
B 63725 Unused
D 63728 The next 6 bytes define the guardians.
B 63728,2 Guardian 1
B 63730,2 Guardian 2
B 63732,2 Guardian 3
B 63734,1 Terminator
B 63735,9,9 Unused
b 63744 Room 57: Above the West Bedroom
D 63744 #UDGTABLE { #ROOM63744 } TABLE#
D 63744 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 63744,128,8 Room layout
D 63872 The next 32 bytes contain the room name.
T 63872,32 Room name
D 63904 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 63904 #UDGTABLE { #UDG63905,0(background57) | #UDG63914,4(floor57) | #UDG63923,35(wall57) | #UDG63932,6(nasty57) | #UDG63941,7(ramp57) | #UDG63950,255(conveyor57) } TABLE#
B 63904,9,9 Background
B 63913,9,9 Floor
B 63922,9,9 Wall
B 63931,9,9 Nasty
B 63940,9,9 Ramp
B 63949,9,9 Conveyor (unused)
D 63958 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 63958,4 Conveyor direction (left), location (x=0, y=0) and length (0)
B 63962,4 Ramp direction (right), location (x=17, y=13) and length (8)
D 63966 The next byte specifies the border colour.
B 63966 Border colour
B 63967 Unused
D 63969 The next 8 bytes define the object graphic.
D 63969 #UDGTABLE { #UDG63969,3(object57) } TABLE#
B 63969,8,8 Object graphic
D 63977 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 63977 Room to the left (#R49152(The Off Licence))
B 63978 Room to the right (#R63488(West Wing Roof))
B 63979 Room above (#R49152(The Off Licence))
B 63980 Room below (#R63232(West Bedroom))
B 63981 Unused
D 63984 The next 4 bytes define the guardians.
B 63984,2 Guardian 1
B 63986,2 Guardian 2
B 63988,1 Terminator
B 63989,11,11 Unused
b 64000 Room 58: The Beach
D 64000 #UDGTABLE { #ROOM64000 } TABLE#
D 64000 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 64000,128,8 Room layout
D 64128 The next 32 bytes contain the room name.
T 64128,32 Room name
D 64160 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 64160 #UDGTABLE { #UDG64161,13(background58) | #UDG64170,50(floor58) | #UDG64179,42(wall58) | #UDG64188,48(nasty58) | #UDG64197,14(ramp58) | #UDG64206,44(conveyor58) } TABLE#
B 64160,9,9 Background
B 64169,9,9 Floor
B 64178,9,9 Wall
B 64187,9,9 Nasty
B 64196,9,9 Ramp
B 64205,9,9 Conveyor
D 64214 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 64214,4 Conveyor direction (left), location (x=0, y=15) and length (5)
B 64218,4 Ramp direction (right), location (x=5, y=14) and length (1)
D 64222 The next byte specifies the border colour.
B 64222 Border colour
B 64223 Unused
D 64225 The next 8 bytes define the object graphic.
D 64225 #UDGTABLE { #UDG64225,11(object58) } TABLE#
B 64225,8,8 Object graphic
D 64233 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 64233 Room to the left (#R64256(The Yacht))
B 64234 Room to the right (#R62208(#SPACE(0)Tool#SPACE(2)Shed))
B 64235 Room above (The Beach)
B 64236 Room below (#R49152(The Off Licence))
B 64237 Unused
D 64240 The next 4 bytes define the guardians.
B 64240,2 Guardian 1
B 64242,2 Guardian 2
B 64244,1 Terminator
B 64245,11,11 Unused
b 64256 Room 59: The Yacht
D 64256 #UDGTABLE { #ROOM64256 } TABLE#
D 64256 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 64256,128,8 Room layout
D 64384 The next 32 bytes contain the room name.
T 64384,32 Room name
D 64416 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 64416 #UDGTABLE { #UDG64417,0(background59) | #UDG64426,6(floor59) | #UDG64435,61(wall59) | #UDG64444,66(nasty59) | #UDG64453,7(ramp59) | #UDG64462,13(conveyor59) } TABLE#
B 64416,9,9 Background
B 64425,9,9 Floor
B 64434,9,9 Wall
B 64443,9,9 Nasty
B 64452,9,9 Ramp
B 64461,9,9 Conveyor
D 64470 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 64470,4 Conveyor direction (left), location (x=21, y=15) and length (11)
B 64474,4 Ramp direction (left), location (x=10, y=9) and length (5)
D 64478 The next byte specifies the border colour.
B 64478 Border colour
B 64479 Unused
D 64481 The next 8 bytes define the object graphic.
D 64481 #UDGTABLE { #UDG64481,3(object59) } TABLE#
B 64481,8,8 Object graphic
D 64489 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 64489 Room to the left (#R64512(The Bow))
B 64490 Room to the right (#R64000(The Beach))
B 64491 Room above (#R49152(The Off Licence))
B 64492 Room below (#R49152(The Off Licence))
B 64493 Unused
D 64496 The next 4 bytes define the guardians.
B 64496,2 Guardian 1
B 64498,2 Guardian 2
B 64500,1 Terminator
B 64501,11,11 Unused
b 64512 Room 60: The Bow
D 64512 #UDGTABLE { #ROOM64512 } TABLE#
D 64512 The first 128 bytes define the room layout. Each bit-pair (bits 7 and 6, 5 and 4, 3 and 2, or 1 and 0 of each byte) determines the type of tile (background, floor, wall or nasty) that will be drawn at the corresponding location.
B 64512,128,8 Room layout
D 64640 The next 32 bytes contain the room name.
T 64640,32 Room name
D 64672 The next 54 bytes contain the attributes and graphic data for the tiles used to build the room.
D 64672 #UDGTABLE { #UDG64673,0(background60) | #UDG64682,68(floor60) | #UDG64691,61(wall60) | #UDG64700,79(nasty60) | #UDG64709,7(ramp60) | #UDG64718,14(conveyor60) } TABLE#
B 64672,9,9 Background
B 64681,9,9 Floor
B 64690,9,9 Wall
B 64699,9,9 Nasty
B 64708,9,9 Ramp
B 64717,9,9 Conveyor
D 64726 The next 8 bytes define the direction, location and length of the conveyor and ramp.
B 64726,4 Conveyor direction (right), location (x=17, y=15) and length (15)
B 64730,4 Ramp direction (left), location (x=16, y=14) and length (6)
D 64734 The next byte specifies the border colour.
B 64734 Border colour
B 64735 Unused
D 64737 The next 8 bytes define the object graphic.
D 64737 #UDGTABLE { #UDG64737,3(object60) } TABLE#
B 64737,8,8 Object graphic
D 64745 The next 4 bytes specify the rooms to the left, to the right, above and below.
B 64745 Room to the left (#R49152(The Off Licence))
B 64746 Room to the right (#R64256(The Yacht))
B 64747 Room above (#R49152(The Off Licence))
B 64748 Room below (#R49152(The Off Licence))
B 64749 Unused
D 64752 The next 4 bytes define the guardians.
B 64752,2 Guardian 1
B 64754,2 Guardian 2
B 64756,1 Terminator
B 64757,11,11 Unused
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
Z 65517
