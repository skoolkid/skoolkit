# -*- coding: utf-8 -*-
import random
from os.path import join, basename
import unittest

from skoolkittest import SkoolKitTestCase, StringIO
from skoolkit import VERSION, SkoolKitError, SkoolParsingError
from skoolkit.skoolmacro import UnsupportedMacroError
from skoolkit.skoolhtml import HtmlWriter, FileInfo, Udg
from skoolkit.skoolparser import SkoolParser, Register, BASE_10, BASE_16, CASE_LOWER, CASE_UPPER
from skoolkit.refparser import RefParser

GAMEDIR = 'test'
ASMDIR = 'asm'
MAPS_DIR = 'maps'
GRAPHICS_DIR = 'graphics'
BUFFERS_DIR = 'buffers'
REFERENCE_DIR = 'reference'
UDGDIR = 'images/udgs'
TEMPLATES_DIR = 'templates'

TEST_PARSING_REF = """[Info]
Release=Test HTML disassembly
Copyright=Me, 2012

[Links]
Bugs=[Bugs] (program errors)
Pokes=[Pokes [with square brackets in the link text]] (cheats)

[MemoryMap:TestMap]
EntryTypes=w
"""

HEADER = """<?xml version="1.0" encoding="utf-8" ?>
<!DOCTYPE html
    PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="content-type" content="text/html; charset=utf-8" />
<title>{name}: {title}</title>
<link rel="stylesheet" type="text/css" href="{path}skoolkit.css" />{script}
</head>
{body}
<table class="header">
<tr>
<td class="headerLogo"><a class="link" href="{path}index.html">{logo}</a></td>
<td class="headerText">{header}</td>
</tr>
</table>
"""

INDEX_HEADER = """<?xml version="1.0" encoding="utf-8" ?>
<!DOCTYPE html
    PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="content-type" content="text/html; charset=utf-8" />
<title>{name}: {title}</title>
<link rel="stylesheet" type="text/css" href="{path}skoolkit.css" />{script}
</head>
{body}
<table class="header">
<tr>
<td class="headerText">{header_prefix}</td>
<td class="headerLogo">{logo}</td>
<td class="headerText">{header_suffix}</td>
</tr>
</table>
"""

BARE_FOOTER = """<div class="footer">
<div class="created">Created using <a class="link" href="http://pyskool.ca/?page_id=177">SkoolKit</a> {0}.</div>
</div>
</body>
</html>""".format(VERSION)

FOOTER = """<div class="footer">
<div class="release">Test HTML disassembly</div>
<div class="copyright">Me, 2012</div>
<div class="created">Created using <a class="link" href="http://pyskool.ca/?page_id=177">SkoolKit</a> {0}.</div>
</div>
</body>
</html>""".format(VERSION)

TABLE_SRC = """(data)
{ =h Col1 | =h Col2 | =h,c2 Cols3+4 }
{ =r2 X   | Y       | Za  | Zb }
{           Y2      | Za2 | =t }
"""

TABLE_HTML = """<table class="data">
<tr>
<th>Col1</th>
<th>Col2</th>
<th colspan="2">Cols3+4</th>
</tr>
<tr>
<td rowspan="2">X</td>
<td>Y</td>
<td>Za</td>
<td>Zb</td>
</tr>
<tr>
<td>Y2</td>
<td>Za2</td>
<td class="transparent"></td>
</tr>
</table>"""

TABLE2_SRC = """(,centre)
{ =h Header }
{ Cell }
"""

TABLE2_HTML = """<table>
<tr>
<th>Header</th>
</tr>
<tr>
<td class="centre">Cell</td>
</tr>
</table>"""

TEST_HTML_SKOOL = """; Text
t24576 DEFM "<&>" ; a <= b & b >= c
"""

TEST_HTML_REF = """
[Bug:test:Test]
<p>Hello</p>
"""

TEST_WRITE_ASM_ENTRIES_REF = """[OtherCode:start]
Header=Startup code
Index=start/index.html
Path=start
Source=start.skool
Title=Startup code
"""

TEST_WRITE_ASM_ENTRIES_SKOOL = """; Routine at 24576
;
; Description of routine at 24576.
;
; A Some value
; B Some other value
c24576 LD A,B  ; Comment for instruction at 24576
; Mid-routine comment above 24577.
*24577 RET
; End comment for routine at 24576.

; Data block at 24578
b24578 DEFB 0

; Routine at 24579
c24579 JR 24577

; GSB entry at 24581
g24581 DEFW 123

; Unused
u24583 DEFB 0

; Routine at 24584 (register section but no description)
;
; .
;
; A 0
c24584 CALL 30000  ; {Comment for the instructions at 24584 and 24587
 24587 JP 30003    ; }

r30000 start
 30003
"""

PREV_UP_NEXT = """<table class="prevNext">
<tr>
<td class="prev">{prev_link}</td>
<td class="up">{up_link}</td>
<td class="next">{next_link}</td>
</tr>
</table>
"""

ENTRY1 = """<div class="description">24576: Routine at 24576</div>
<table class="disassembly">
<tr>
<td class="routineComment" colspan="3">
<div class="details">
<div class="paragraph">
Description of routine at 24576.
</div>
</div>
<table class="input">
<tr>
<td class="register">A</td>
<td class="registerContents">Some value</td>
</tr>
<tr>
<td class="register">B</td>
<td class="registerContents">Some other value</td>
</tr>
</table>
</td>
</tr>
<tr>
<td class="label"><a name="24576"></a>24576</td>
<td class="instruction">LD A,B</td>
<td class="comment">Comment for instruction at 24576</td>
</tr>
<tr>
<td class="routineComment" colspan="3">
<a name="24577"></a>
<div class="comments">
<div class="paragraph">
Mid-routine comment above 24577.
</div>
</div>
</td>
</tr>
<tr>
<td class="label">24577</td>
<td class="instruction">RET</td>
<td class="comment"></td>
</tr>
<tr>
<td class="routineComment" colspan="3">
<div class="comments">
<div class="paragraph">
End comment for routine at 24576.
</div>
</div>
</td>
</tr>
</table>
"""

ENTRY2 = """<div class="description">24578: Data block at 24578</div>
<table class="dataDisassembly">
<tr>
<td class="routineComment" colspan="3">
<div class="details">
</div>
</td>
</tr>
<tr>
<td class="address"><a name="24578"></a>24578</td>
<td class="instruction">DEFB 0</td>
<td class="transparentDataComment" />
</tr>
</table>
"""

ENTRY3 = """<div class="description">24579: Routine at 24579</div>
<table class="disassembly">
<tr>
<td class="routineComment" colspan="3">
<div class="details">
</div>
</td>
</tr>
<tr>
<td class="label"><a name="24579"></a>24579</td>
<td class="instruction">JR <a class="link" href="24576.html#24577">24577</a></td>
<td class="transparentComment" />
</tr>
</table>
"""

ENTRY4 = """<div class="description">24581: GSB entry at 24581</div>
<table class="dataDisassembly">
<tr>
<td class="routineComment" colspan="3">
<div class="details">
</div>
</td>
</tr>
<tr>
<td class="address"><a name="24581"></a>24581</td>
<td class="instruction">DEFW 123</td>
<td class="transparentDataComment" />
</tr>
</table>
"""

ENTRY5 = """<div class="description">24583: Unused</div>
<table class="disassembly">
<tr>
<td class="routineComment" colspan="3">
<div class="details">
</div>
</td>
</tr>
<tr>
<td class="address"><a name="24583"></a>24583</td>
<td class="instruction">DEFB 0</td>
<td class="transparentComment" />
</tr>
</table>
"""

ENTRY6 = """<div class="description">24584: Routine at 24584 (register section but no description)</div>
<table class="disassembly">
<tr>
<td class="routineComment" colspan="3">
<div class="details">
</div>
<table class="input">
<tr>
<td class="register">A</td>
<td class="registerContents">0</td>
</tr>
</table>
</td>
</tr>
<tr>
<td class="label"><a name="24584"></a>24584</td>
<td class="instruction">CALL <a class="link" href="../start/30000.html">30000</a></td>
<td class="comment" rowspan="2">Comment for the instructions at 24584 and 24587</td>
</tr>
<tr>
<td class="address"><a name="24587"></a>24587</td>
<td class="instruction">JP <a class="link" href="../start/30000.html#30003">30003</a></td>
</tr>
</table>
"""

TEST_ASM_LABELS_SKOOL = """; Routine with a label
; @label=START
c50000 LD B,5     ; Loop 5 times
 50002 DJNZ 50002
 50004 RET

; Routine without a label
c50005 JP 50000

; DEFW statement with a @keep directive
; @keep
b50008 DEFW 50000
"""

ASM_LABELS_ENTRY1 = """<div class="description">START: 50000: Routine with a label</div>
<table class="disassembly">
<tr>
<td class="routineComment" colspan="4">
<div class="details">
</div>
</td>
</tr>
<tr>
<td class="asmLabel">START</td>
<td class="label"><a name="50000"></a>50000</td>
<td class="instruction">LD B,5</td>
<td class="comment">Loop 5 times</td>
</tr>
<tr>
<td class="asmLabel"></td>
<td class="address"><a name="50002"></a>50002</td>
<td class="instruction">DJNZ <a class="link" href="50000.html#50002">50002</a></td>
<td class="comment"></td>
</tr>
<tr>
<td class="asmLabel"></td>
<td class="address"><a name="50004"></a>50004</td>
<td class="instruction">RET</td>
<td class="comment"></td>
</tr>
</table>
"""

ASM_LABELS_ENTRY2 = """<div class="description">50005: Routine without a label</div>
<table class="disassembly">
<tr>
<td class="routineComment" colspan="3">
<div class="details">
</div>
</td>
</tr>
<tr>
<td class="label"><a name="50005"></a>50005</td>
<td class="instruction">JP <a class="link" href="50000.html">START</a></td>
<td class="transparentComment" />
</tr>
</table>
"""

ASM_LABELS_ENTRY3 = """<div class="description">50008: DEFW statement with a @keep directive</div>
<table class="dataDisassembly">
<tr>
<td class="routineComment" colspan="3">
<div class="details">
</div>
</td>
</tr>
<tr>
<td class="address"><a name="50008"></a>50008</td>
<td class="instruction">DEFW 50000</td>
<td class="transparentDataComment" />
</tr>
</table>
"""

TEST_WRITE_MAP = """; Routine
c30000 RET

; Bytes
b30001 DEFB 1,2

; Words
b30003 DEFW 257,65534

; GSB entry
g30007 DEFB 0

; Unused
u30008 DEFB 0

; Zeroes
z30009 DEFS 6

; Text
t30015 DEFM "Hi"
"""

MEMORY_MAP = """<table class="map">
<tr>
<th>Page</th>
<th>Byte</th>
<th>Address</th>
<th>Description</th>
</tr>
<tr>
<td class="mapPage">117</td>
<td class="mapByte">48</td>
<td class="routine"><a class="link" name="30000" href="../asm/30000.html">30000</a></td>
<td class="routineDesc">Routine</td>
</tr>
<tr>
<td class="mapPage">117</td>
<td class="mapByte">49</td>
<td class="data"><a class="link" name="30001" href="../asm/30001.html">30001</a></td>
<td class="dataDesc">Bytes</td>
</tr>
<tr>
<td class="mapPage">117</td>
<td class="mapByte">51</td>
<td class="data"><a class="link" name="30003" href="../asm/30003.html">30003</a></td>
<td class="dataDesc">Words</td>
</tr>
<tr>
<td class="mapPage">117</td>
<td class="mapByte">55</td>
<td class="gbuffer"><a class="link" name="30007" href="../asm/30007.html">30007</a></td>
<td class="gbufferDesc">GSB entry</td>
</tr>
<tr>
<td class="mapPage">117</td>
<td class="mapByte">56</td>
<td class="unused"><a class="link" name="30008" href="../asm/30008.html">30008</a></td>
<td class="unusedDesc">Unused (1 byte)</td>
</tr>
<tr>
<td class="mapPage">117</td>
<td class="mapByte">57</td>
<td class="unused"><a class="link" name="30009" href="../asm/30009.html">30009</a></td>
<td class="unusedDesc">Unused (6 bytes)</td>
</tr>
<tr>
<td class="mapPage">117</td>
<td class="mapByte">63</td>
<td class="message"><a class="link" name="30015" href="../asm/30015.html">30015</a></td>
<td class="messageDesc">Text</td>
</tr>
</table>
"""

ROUTINES_MAP = """<table class="map">
<tr>
<th>Address</th>
<th>Description</th>
</tr>
<tr>
<td class="routine"><a class="link" name="30000" href="../asm/30000.html">30000</a></td>
<td class="routineDesc">Routine</td>
</tr>
</table>
"""

DATA_MAP = """<table class="map">
<tr>
<th>Page</th>
<th>Byte</th>
<th>Address</th>
<th>Description</th>
</tr>
<tr>
<td class="mapPage">117</td>
<td class="mapByte">49</td>
<td class="data"><a class="link" name="30001" href="../asm/30001.html">30001</a></td>
<td class="dataDesc">Bytes</td>
</tr>
<tr>
<td class="mapPage">117</td>
<td class="mapByte">51</td>
<td class="data"><a class="link" name="30003" href="../asm/30003.html">30003</a></td>
<td class="dataDesc">Words</td>
</tr>
</table>
"""

MESSAGES_MAP = """<table class="map">
<tr>
<th>Address</th>
<th>Description</th>
</tr>
<tr>
<td class="message"><a class="link" name="30015" href="../asm/30015.html">30015</a></td>
<td class="messageDesc">Text</td>
</tr>
</table>
"""

UNUSED_MAP = """<table class="map">
<tr>
<th>Page</th>
<th>Byte</th>
<th>Address</th>
<th>Description</th>
</tr>
<tr>
<td class="mapPage">117</td>
<td class="mapByte">56</td>
<td class="unused"><a class="link" name="30008" href="../asm/30008.html">30008</a></td>
<td class="unusedDesc">Unused (1 byte)</td>
</tr>
<tr>
<td class="mapPage">117</td>
<td class="mapByte">57</td>
<td class="unused"><a class="link" name="30009" href="../asm/30009.html">30009</a></td>
<td class="unusedDesc">Unused (6 bytes)</td>
</tr>
</table>
"""

CUSTOM_MAP = """<div class="mapIntro">Introduction.</div>
<table class="map">
<tr>
<th>Address</th>
<th>Description</th>
</tr>
<tr>
<td class="routine"><a class="link" name="30000" href="../asm/30000.html">30000</a></td>
<td class="routineDesc">Routine</td>
</tr>
<tr>
<td class="gbuffer"><a class="link" name="30007" href="../asm/30007.html">30007</a></td>
<td class="gbufferDesc">GSB entry</td>
</tr>
</table>
"""

TEST_WRITE_CHANGELOG_REF = """
[Changelog:20120704]
Intro.

1
  2
    3
    4
  5

[Changelog:20120703]
-

1
  2
    3
"""

CHANGELOG = """<ul class="linkList">
<li><a class="link" href="#20120704">20120704</a></li>
<li><a class="link" href="#20120703">20120703</a></li>
</ul>
<div><a name="20120704"></a></div>
<div class="changelog changelog1">
<div class="changelogTitle">20120704</div>
<div class="changelogDesc">Intro.</div>
<ul class="changelog">
<li>1
<ul class="changelog1">
<li>2
<ul class="changelog2">
<li>3</li>
<li>4</li>
</ul>
</li>
<li>5</li>
</ul>
</li>
</ul>
</div>
<div><a name="20120703"></a></div>
<div class="changelog changelog2">
<div class="changelogTitle">20120703</div>
<ul class="changelog">
<li>1
<ul class="changelog1">
<li>2
<ul class="changelog2">
<li>3</li>
</ul>
</li>
</ul>
</li>
</ul>
</div>
"""

TEST_WRITE_GLOSSARY_REF = """
[Glossary:Term1]
Definition 1.

[Glossary:Term2]
Definition 2. Paragraph 1.

Definition 2. Paragraph 2.
"""

GLOSSARY = """<ul class="linkList">
<li><a class="link" href="#term1">Term1</a></li>
<li><a class="link" href="#term2">Term2</a></li>
</ul>
<div><a name="term1"></a></div>
<div class="box box1">
<div class="boxTitle">Term1</div>
<div class="paragraph">
Definition 1.
</div>
</div>
<div><a name="term2"></a></div>
<div class="box box2">
<div class="boxTitle">Term2</div>
<div class="paragraph">
Definition 2. Paragraph 1.
</div>
<div class="paragraph">
Definition 2. Paragraph 2.
</div>
</div>
"""

GBUFFER = """<table class="gbuffer">
<tr>
<th>Address</th>
<th>Length</th>
<th>Purpose</th>
</tr>
<tr>
<td class="gbufAddress"><a name="24595" class="link" href="../asm/24595.html">24595</a></td>
<td class="gbufLength">1</td>
<td class="gbufDesc">
<div class="gbufDesc">Game status buffer entry</div>
</td>
</tr>
<tr>
<td class="gbufAddress"><a name="24596" class="link" href="../asm/24596.html">24596</a></td>
<td class="gbufLength">1</td>
<td class="gbufDesc">
<div class="gbufDesc">Another game status buffer entry</div>
</td>
</tr>
</table>
"""

TEST_WRITE_GRAPHICS_REF = """
[Graphics]
<em>This is the graphics page.</em>
"""

TEST_WRITE_PAGE_REF = """
[Page:CustomPage]
Title=Custom page
Path=page.html
JavaScript=test-html.js

[PageContent:CustomPage]
<b>This is the content of the custom page.</b>
"""

REGISTERS_1 = """<table class="input">
<tr>
<td class="register">A</td>
<td class="registerContents">Some value</td>
</tr>
<tr>
<td class="register">B</td>
<td class="registerContents">Some other value</td>
</tr>
</table>
"""

REGISTERS_2 = """<table class="input">
<tr>
<th colspan="2">Input</th>
</tr>
<tr>
<td class="register">A</td>
<td class="registerContents">Some value</td>
</tr>
<tr>
<td class="register">B</td>
<td class="registerContents">Some other value</td>
</tr>
</table>
<table class="output">
<tr>
<th colspan="2">Output</th>
</tr>
<tr>
<td class="register">D</td>
<td class="registerContents">The result</td>
</tr>
<tr>
<td class="register">E</td>
<td class="registerContents">Result flags</td>
</tr>
</table>
"""

TEST_WRITE_BUGS_REF = """[Bug:b1:Showstopper]
This bug is bad.

Really bad.
"""

BUGS = """<ul class="linkList">
<li><a class="link" href="#b1">Showstopper</a></li>
</ul>
<div><a name="b1"></a></div>
<div class="box box1">
<div class="boxTitle">Showstopper</div>
<div class="paragraph">
This bug is bad.
</div>
<div class="paragraph">
Really bad.
</div>
</div>
"""

TEST_WRITE_FACTS_REF = """[Fact:f1:Interesting fact]
Hello.

Goodbye.

[Fact:f2:Another interesting fact]
Yes.
"""

FACTS = """<ul class="linkList">
<li><a class="link" href="#f1">Interesting fact</a></li>
<li><a class="link" href="#f2">Another interesting fact</a></li>
</ul>
<div><a name="f1"></a></div>
<div class="box box1">
<div class="boxTitle">Interesting fact</div>
<div class="paragraph">
Hello.
</div>
<div class="paragraph">
Goodbye.
</div>
</div>
<div><a name="f2"></a></div>
<div class="box box2">
<div class="boxTitle">Another interesting fact</div>
<div class="paragraph">
Yes.
</div>
</div>
"""

TEST_WRITE_POKES_REF = """[Poke:p1:Infinite everything]
POKE 12345,0
"""

POKES = """<ul class="linkList">
<li><a class="link" href="#p1">Infinite everything</a></li>
</ul>
<div><a name="p1"></a></div>
<div class="box box1">
<div class="boxTitle">Infinite everything</div>
<div class="paragraph">
POKE 12345,0
</div>
</div>
"""

TEST_WRITE_GRAPHIC_GLITCHES_REF = """[GraphicGlitch:g0:Wrong arms]
Hello.
"""

GRAPHIC_GLITCHES = """<ul class="linkList">
<li><a class="link" href="#g0">Wrong arms</a></li>
</ul>
<div><a name="g0"></a></div>
<div class="box box1">
<div class="boxTitle">Wrong arms</div>
<div class="paragraph">
Hello.
</div>
</div>
"""

TEST_WRITE_GBUFFER_REF = """[Game]
GameStatusBufferIncludes=30003,30004
"""

TEST_WRITE_GBUFFER_SKOOL = """; GSB entry 1
;
; Number of lives.
g30000 DEFB 4

; GSB entry 2
g30001 DEFW 78

; Message ID
t30003 DEFB 0

; Another message ID
t30004 DEFB 0

; Not a game status buffer entry
c30005 RET

i30006
"""

GAME_STATUS_BUFFER = """<table class="gbuffer">
<tr>
<th>Address</th>
<th>Length</th>
<th>Purpose</th>
</tr>
<tr>
<td class="gbufAddress"><a name="30000" class="link" href="../asm/30000.html">30000</a></td>
<td class="gbufLength">1</td>
<td class="gbufDesc">
<div class="gbufDesc">GSB entry 1</div>
<div class="gbufDetails">
<div class="paragraph">
Number of lives.
</div>
</div>
</td>
</tr>
<tr>
<td class="gbufAddress"><a name="30001" class="link" href="../asm/30001.html">30001</a></td>
<td class="gbufLength">2</td>
<td class="gbufDesc">
<div class="gbufDesc">GSB entry 2</div>
</td>
</tr>
<tr>
<td class="gbufAddress"><a name="30003" class="link" href="../asm/30003.html">30003</a></td>
<td class="gbufLength">1</td>
<td class="gbufDesc">
<div class="gbufDesc">Message ID</div>
</td>
</tr>
<tr>
<td class="gbufAddress"><a name="30004" class="link" href="../asm/30004.html">30004</a></td>
<td class="gbufLength">1</td>
<td class="gbufDesc">
<div class="gbufDesc">Another message ID</div>
</td>
</tr>
</table>
"""

TEST_MACRO_D = """; @start

; First routine
c32768 RET

; Second routine
c32769 RET

c32770 RET
"""

TEST_MACRO_EREFS = """; @start
; First routine
c30000 CALL 30004

; Second routine
c30003 LD A,B
 30004 LD B,C

; Third routine
c30005 JP 30004
"""

TEST_MACRO_LINK_REF = """[Page:CustomPage1]
Title=Custom page
Path=page.html

[Page:CustomPage2]
Path=page2.html
Link=Custom page 2
"""

TEST_MACRO_REFS_SKOOL = """; Not used directly by any other routines
c24576 LD HL,$6003

; Used by the routines at 24581, 24584 and 24590
c24579 LD A,H
 24580 RET

; Calls 24579
c24581 CALL 24579

; Also calls 24579
c24584 CALL 24579
 24587 JP 24580

; Calls 24579 too
c24590 CALL 24580
"""

TEST_INDEX_PAGE_ID_REF = """[OtherCode:secondary]
Source=secondary.skool
Path=secondary
Index=secondary/secondary.html
Title=Secondary code
Header=Secondary code
IndexPageId=SecondaryCode
"""

TEST_PAGE_CONTENT_REF = """[Page:ExistingPage]
Content=asm/32768.html
"""

TEST_SHOULD_WRITE_MAP_REF = """[MemoryMap:UnusedMap]
Write=0
"""

TEST_SHOULD_WRITE_MAP_SKOOL = """; Routine
c40000 RET

; Data
b40001 DEFB 0

; Unused
u40002 DEFB 0
"""

TEST_WRITE_INDEX_REF = []
TEST_WRITE_INDEX_FILES = []
INDEX = []

# Index (empty)
TEST_WRITE_INDEX_REF.append("")
TEST_WRITE_INDEX_FILES.append([])
INDEX.append("")

# Index (memory map, routines map)
TEST_WRITE_INDEX_REF.append("")
TEST_WRITE_INDEX_FILES.append([
    join(MAPS_DIR, 'all.html'),
    join(MAPS_DIR, 'routines.html')
])
INDEX.append("""<div class="headerText">Memory maps</div>
<ul class="indexList">
<li><a class="link" href="maps/all.html">Everything</a></li>
<li><a class="link" href="maps/routines.html">Routines</a></li>
</ul>
""")

# Index (memory map, routines map, data map)
TEST_WRITE_INDEX_REF.append("")
TEST_WRITE_INDEX_FILES.append([
    join(MAPS_DIR, 'all.html'),
    join(MAPS_DIR, 'routines.html'),
    join(MAPS_DIR, 'data.html')
])
INDEX.append("""<div class="headerText">Memory maps</div>
<ul class="indexList">
<li><a class="link" href="maps/all.html">Everything</a></li>
<li><a class="link" href="maps/routines.html">Routines</a></li>
<li><a class="link" href="maps/data.html">Data</a></li>
</ul>
""")

# Index (memory map, routines map, data map, messages map)
TEST_WRITE_INDEX_REF.append("")
TEST_WRITE_INDEX_FILES.append([
    join(MAPS_DIR, 'all.html'),
    join(MAPS_DIR, 'routines.html'),
    join(MAPS_DIR, 'data.html'),
    join(MAPS_DIR, 'messages.html')
])
INDEX.append("""<div class="headerText">Memory maps</div>
<ul class="indexList">
<li><a class="link" href="maps/all.html">Everything</a></li>
<li><a class="link" href="maps/routines.html">Routines</a></li>
<li><a class="link" href="maps/data.html">Data</a></li>
<li><a class="link" href="maps/messages.html">Messages</a></li>
</ul>
""")

# Index (other code)
TEST_WRITE_INDEX_REF.append("""[OtherCode:otherCode]
Header=Startup
Index=other/other.html
Path=other
Source=other.skool
Title=Startup code
""")
TEST_WRITE_INDEX_FILES.append([
    'other/other.html'
])
INDEX.append("""<div class="headerText">Other code</div>
<ul class="indexList">
<li><a class="link" href="other/other.html">Startup code</a></li>
</ul>
""")

# Index (defined by [Index], [Index:*:*], [Links] and [Paths] sections)
TEST_WRITE_INDEX_REF.append("""[Index]
Reference
MemoryMaps

[Index:Reference:Reference material]
Bugs
Facts

[Index:MemoryMaps:RAM maps]
RoutinesMap
MemoryMap

[Links]
MemoryMap=Entire RAM
Facts=Facts

[Paths]
MemoryMap=memorymaps/ram.html
RoutinesMap=memorymaps/routines.html
Bugs=ref/bugs.html
Facts=ref/facts.html
Changelog=ref/changelog.html
""")
TEST_WRITE_INDEX_FILES.append([
    'ref/bugs.html',
    'ref/facts.html',
    'ref/changelog.html',
    'memorymaps/ram.html',
    'memorymaps/routines.html',
    'memorymaps/data.html'
])
INDEX.append("""<div class="headerText">Reference material</div>
<ul class="indexList">
<li><a class="link" href="ref/bugs.html">Bugs</a></li>
<li><a class="link" href="ref/facts.html">Facts</a></li>
</ul>
<div class="headerText">RAM maps</div>
<ul class="indexList">
<li><a class="link" href="memorymaps/routines.html">Routines</a></li>
<li><a class="link" href="memorymaps/ram.html">Entire RAM</a></li>
</ul>
""")

ERROR_PREFIX = 'Error while parsing #{0} macro'

class TestHtmlWriter(HtmlWriter):
    def write_image(self, img_file, udgs=(), crop_rect=(), scale=2, mask=False):
        self.image_writer.write_image(udgs, scale, mask, *crop_rect)

class MockSkoolParser:
    def __init__(self, snapshot=None, entries=(), memory_map=()):
        self.snapshot = snapshot
        self.entries = entries
        self.memory_map = memory_map
        self.skoolfile = ''
        self.base = None

class MockFileInfo:
    def __init__(self, topdir, game_dir):
        self.odir = join(topdir, game_dir)
        self.path = None
        self.mode = None

    # PY: open_file(self, *names, mode='w') in Python 3
    def open_file(self, *names, **kwargs):
        path = self.odir
        for name in names:
            path = join(path, name)
        self.path = path
        self.mode = kwargs.get('mode', 'w') # PY: Not needed in Python 3
        return StringIO()

    def need_image(self, image_path):
        return True

class MockImageWriter:
    def __init__(self):
        self.build_images = True
        self.default_format = 'png'

    def write_image(self, udg_array, scale, mask, x, y, width, height):
        self.udg_array = udg_array
        self.scale = scale
        self.mask = mask
        self.x = x
        self.y = y
        self.width = width
        self.height = height

class MockImageWriter2:
    def __init__(self):
        self.default_format = 'png'

    def write_image(self, udg_array, img_file, img_format, scale, mask, x=0, y=0, width=None, height=None):
        self.udg_array = udg_array
        self.img_format = img_format
        self.scale = scale
        self.mask = mask
        self.x = x
        self.y = y
        self.width = width
        self.height = height

class HtmlWriterTest(SkoolKitTestCase):
    def read_file(self, fname, lines=False):
        f = open(join(self.odir, GAMEDIR, fname), 'r')
        if lines:
            contents = [line.rstrip('\n') for line in f]
        else:
            contents = f.read()
        f.close()
        return contents

    def assert_files_equal(self, d_fname, subs, index=False):
        d_html_lines = self.read_file(d_fname, True)
        body = subs['content']
        body_class = subs.get('body_class')
        body_class_attr = ' class="{0}"'.format(body_class) if body_class else ''
        subs['body'] = '<body{0}>'.format(body_class_attr)
        js = subs.get('js')
        subs['script'] = '\n<script type="text/javascript" src="{0}"></script>'.format(js) if js else ''
        subs.setdefault('header', subs['title'])
        subs.setdefault('logo', subs['name'])
        footer = subs.get('footer', FOOTER)
        prev_up_next = ''
        if 'up' in subs:
            subs['prev_link'] = ''
            subs['up_link'] = 'Up: <a class="link" href="{path}maps/all.html#{up}">Map</a>'.format(**subs)
            subs['next_link'] = ''
            prev_entry = subs.get('prev')
            if prev_entry:
                subs['prev_link'] = 'Prev: <a class="link" href="{0}.html">{0}</a>'.format(prev_entry)
            next_entry = subs.get('next')
            if next_entry:
                subs['next_link'] = 'Next: <a class="link" href="{0}.html">{0}</a>'.format(next_entry)
            prev_up_next = PREV_UP_NEXT.format(**subs)
        header_template = INDEX_HEADER if index else HEADER
        t_html_lines = (header_template + prev_up_next + body + prev_up_next + footer).format(**subs).split('\n')
        self.assertEqual(d_html_lines, t_html_lines)

    def _test_reference_macro(self, macro, def_link_text, page):
        writer = self._get_writer()
        for link_text in ('', '(test)', '(test (nested) parentheses)'):
            for anchor in ('', '#test'):
                output = writer.expand('#{0}{1}{2}'.format(macro, anchor, link_text), ASMDIR)
                self.link_equals(output, '../{0}/{1}.html{2}'.format(REFERENCE_DIR, page, anchor), link_text[1:-1] or def_link_text)

    def _test_call(self, *args):
        # Method used to test the #CALL macro
        return str(args)

    def _test_call_no_retval(self, *args):
        return

    def _unsupported_macro(self, *args):
        raise UnsupportedMacroError()

    def _get_writer(self, ref=None, snapshot=(), case=None, base=None, skool=None, create_labels=False, asm_labels=False):
        self.reffile = None
        self.skoolfile = None
        ref_parser = RefParser()
        if ref is not None:
            self.reffile = self.write_text_file(ref, suffix='.ref')
            ref_parser.parse(self.reffile)
        if skool is None:
            skool_parser = MockSkoolParser(snapshot)
        else:
            self.skoolfile = self.write_text_file(skool, suffix='.skool')
            skool_parser = SkoolParser(self.skoolfile, case=case, base=base, html=True, create_labels=create_labels, asm_labels=asm_labels)
        self.odir = self.make_directory()
        file_info = FileInfo(self.odir, GAMEDIR, False)
        return TestHtmlWriter(skool_parser, ref_parser, file_info, MockImageWriter())

    def _assert_scr_equal(self, game, x0=0, y0=0, w=32, h=24):
        snapshot = game.snapshot[:]
        scr = game.screenshot(x0, y0, w, h)
        self.assertEqual(len(scr),  min((h, 24 - y0)))
        self.assertEqual(len(scr[0]), min((w, 32 - x0)))
        for j, row in enumerate(scr):
            for i, udg in enumerate(row):
                x, y = x0 + i, y0 + j
                df_addr = 16384 + 2048 * (y // 8) + 32 * (y % 8) + x
                af_addr = 22528 + 32 * y + x
                self.assertEqual(udg.data, snapshot[df_addr:df_addr + 2048:256], 'Graphic data for cell at ({0},{1}) is incorrect'.format(x, y))
                self.assertEqual(udg.attr, snapshot[af_addr], 'Attribute byte for cell at ({0},{1}) is incorrect'.format(x, y))

    def link_equals(self, html, href, text):
        self.assertEqual(html, '<a class="link" href="{0}">{1}</a>'.format(href, text))

    def img_equals(self, html, alt, src):
        self.assertEqual(html, '<img alt="{0}" src="{1}" />'.format(alt, src))

    def _check_image(self, image_writer, udg_array, scale, mask, x, y, width, height):
        self.assertEqual(image_writer.scale, scale)
        self.assertEqual(image_writer.mask, mask)
        self.assertEqual(image_writer.x, x)
        self.assertEqual(image_writer.y, y)
        self.assertEqual(image_writer.width, width)
        self.assertEqual(image_writer.height, height)
        self.assertEqual(len(image_writer.udg_array), len(udg_array))
        for i, row in enumerate(image_writer.udg_array):
            exp_row = udg_array[i]
            self.assertEqual(len(row), len(exp_row))
            for j, udg in enumerate(row):
                exp_udg = exp_row[j]
                self.assertEqual(udg.attr, exp_udg.attr)
                self.assertEqual(udg.data, exp_udg.data)
                self.assertEqual(udg.mask, exp_udg.mask)

    def test_get_screenshot(self):
        snapshot = [0] * 65536
        for a in range(16384, 23296):
            snapshot[a] = random.randint(0, 255)
        writer = self._get_writer(snapshot=snapshot)
        self._assert_scr_equal(writer)
        self._assert_scr_equal(writer, 1, 2, 12, 10)
        self._assert_scr_equal(writer, 10, 10)

    def test_get_font_udg_array(self):
        snapshot = [0] * 65536
        char1 = [1, 2, 3, 4, 5, 6, 7, 8]
        char2 = [8, 7, 6, 5, 4, 3, 2, 1]
        chars = [char1, char2]
        char_data = []
        for char in chars:
            char_data.extend(char)
        address = 32768
        snapshot[address:address + sum(len(c) for c in chars)] = char_data
        writer = self._get_writer(snapshot=snapshot)
        attr = 56
        width, font_udg_array = writer.get_font_udg_array(address, len(chars), attr)
        self.assertEqual(width, 8 * len(chars))
        self.assertEqual(len(font_udg_array[0]), len(chars))
        for i, udg in enumerate(font_udg_array[0]):
            self.assertEqual(udg.attr, attr)
            self.assertEqual(udg.data, chars[i])

    def test_ref_parsing(self):
        writer = self._get_writer(ref=TEST_PARSING_REF)

        # [Info]
        self.assertEqual(writer.info['Release'], 'Test HTML disassembly')
        self.assertEqual(writer.info['Copyright'], 'Me, 2012')

        # [Links]
        self.assertEqual(writer.links['Bugs'], ('Bugs', ' (program errors)'))
        self.assertEqual(writer.links['Pokes'], ('Pokes [with square brackets in the link text]', ' (cheats)'))

        # [MemoryMap:*]
        self.assertTrue('TestMap' in writer.memory_map_names)
        self.assertTrue('TestMap' in writer.memory_maps)
        self.assertEqual(writer.memory_maps['TestMap'], {'EntryTypes': 'w', 'Name': 'TestMap'})

    def test_parse_image_params(self):
        writer = self._get_writer()
        def_crop_rect = (0, 0, None, None)

        text = '1,2,$3'
        end, img_path, crop_rect, p1, p2, p3 = writer.parse_image_params(text, 0, 3)
        self.assertEqual(img_path, None)
        self.assertEqual(crop_rect, def_crop_rect)
        self.assertEqual((p1, p2, p3), (1, 2, 3))
        self.assertEqual(end, len(text))

        text = '4,$a,6{0,1,24,32}'
        end, img_path, crop_rect, p1, p2, p3, p4, p5 = writer.parse_image_params(text, 0, 5, (7, 8))
        self.assertEqual(img_path, None)
        self.assertEqual(crop_rect, (0, 1, 24, 32))
        self.assertEqual((p1, p2, p3, p4, p5), (4, 10, 6, 7, 8))
        self.assertEqual(end, len(text))

        text = '$ff,8,9(img)'
        end, img_path, crop_rect, p1, p2, p3 = writer.parse_image_params(text, 0, 3)
        self.assertEqual(img_path, 'images/udgs/img.png')
        self.assertEqual(crop_rect, def_crop_rect)
        self.assertEqual((p1, p2, p3), (255, 8, 9))
        self.assertEqual(end, len(text))

        text = '0,1{1,2}(scr)'
        end, img_path, crop_rect, p1, p2 = writer.parse_image_params(text, 0, 2, path_id='ScreenshotImagePath')
        self.assertEqual(img_path, 'images/scr/scr.png')
        self.assertEqual(crop_rect, (1, 2, None, None))
        self.assertEqual((p1, p2), (0, 1))
        self.assertEqual(end, len(text))

        text = '0,1,2,3{1,2}(x)'
        end, img_path, crop_rect, p1, p2, p3 = writer.parse_image_params(text, 0, 3)
        self.assertEqual(img_path, None)
        self.assertEqual(crop_rect, def_crop_rect)
        self.assertEqual((p1, p2, p3), (0, 1, 2))
        self.assertEqual(end, 5)

    def test_image_path(self):
        writer = self._get_writer()
        def_img_format = writer.default_image_format

        img_path = writer.image_path('img')
        self.assertEqual(img_path, '{0}/img.{1}'.format(writer.paths['UDGImagePath'], def_img_format))

        img_path = writer.image_path('/pics/foo.png')
        self.assertEqual(img_path, 'pics/foo.png')

        path_id = 'ScreenshotImagePath'
        img_path = writer.image_path('img.gif', path_id)
        self.assertEqual(img_path, '{0}/img.gif'.format(writer.paths[path_id]))

        path_id = 'UnknownImagePath'
        fname = 'img.png'
        with self.assertRaisesRegexp(SkoolKitError, "Unknown path ID '{}' for image file '{}'".format(path_id, fname)):
            writer.image_path(fname, path_id)

    def test_flip_udgs(self):
        writer = self._get_writer()
        udg1 = Udg(0, [1, 2, 4, 8, 16, 32, 64, 128], [1, 2, 4, 8, 16, 32, 64, 128])
        udg2 = Udg(0, [1, 2, 3, 4, 5, 6, 7, 8], [2, 4, 6, 8, 10, 12, 14, 16])
        udg3 = Udg(0, [1, 2, 3, 4, 5, 6, 7, 8], [8, 7, 6, 5, 4, 3, 2, 1])
        udg4 = Udg(0, [8, 7, 6, 5, 4, 3, 2, 1], [255, 254, 253, 252, 251, 250, 249, 248])

        udgs = [[udg1.copy(), udg2.copy()], [udg3.copy(), udg4.copy()]]
        writer.flip_udgs(udgs, 0)
        self.assertEqual(udgs, [[udg1, udg2], [udg3, udg4]])

        udgs = [[udg1.copy(), udg2.copy()], [udg3.copy(), udg4.copy()]]
        writer.flip_udgs(udgs, 1)
        udg1_f, udg2_f, udg3_f, udg4_f = udg1.copy(), udg2.copy(), udg3.copy(), udg4.copy()
        udg1_f.flip(1)
        udg2_f.flip(1)
        udg3_f.flip(1)
        udg4_f.flip(1)
        self.assertEqual(udgs, [[udg2_f, udg1_f], [udg4_f, udg3_f]])

        udgs = [[udg1.copy(), udg2.copy()], [udg3.copy(), udg4.copy()]]
        writer.flip_udgs(udgs, 2)
        udg1_f, udg2_f, udg3_f, udg4_f = udg1.copy(), udg2.copy(), udg3.copy(), udg4.copy()
        udg1_f.flip(2)
        udg2_f.flip(2)
        udg3_f.flip(2)
        udg4_f.flip(2)
        self.assertEqual(udgs, [[udg3_f, udg4_f], [udg1_f, udg2_f]])

        udgs = [[udg1.copy(), udg2.copy()], [udg3.copy(), udg4.copy()]]
        writer.flip_udgs(udgs, 3)
        udg1_f, udg2_f, udg3_f, udg4_f = udg1.copy(), udg2.copy(), udg3.copy(), udg4.copy()
        udg1_f.flip(3)
        udg2_f.flip(3)
        udg3_f.flip(3)
        udg4_f.flip(3)
        self.assertEqual(udgs, [[udg4_f, udg3_f], [udg2_f, udg1_f]])

    def test_rotate_udgs(self):
        writer = self._get_writer()
        udg1 = Udg(0, [1, 2, 4, 8, 16, 32, 64, 128], [1, 2, 4, 8, 16, 32, 64, 128])
        udg2 = Udg(0, [1, 2, 3, 4, 5, 6, 7, 8], [2, 4, 6, 8, 10, 12, 14, 16])
        udg3 = Udg(0, [1, 2, 3, 4, 5, 6, 7, 8], [8, 7, 6, 5, 4, 3, 2, 1])
        udg4 = Udg(0, [8, 7, 6, 5, 4, 3, 2, 1], [255, 254, 253, 252, 251, 250, 249, 248])

        udgs = [[udg1.copy(), udg2.copy()], [udg3.copy(), udg4.copy()]]
        writer.rotate_udgs(udgs, 0)
        self.assertEqual(udgs, [[udg1, udg2], [udg3, udg4]])

        udgs = [[udg1.copy(), udg2.copy()], [udg3.copy(), udg4.copy()]]
        writer.rotate_udgs(udgs, 1)
        udg1_r, udg2_r, udg3_r, udg4_r = udg1.copy(), udg2.copy(), udg3.copy(), udg4.copy()
        udg1_r.rotate(1)
        udg2_r.rotate(1)
        udg3_r.rotate(1)
        udg4_r.rotate(1)
        self.assertEqual(udgs, [[udg3_r, udg1_r], [udg4_r, udg2_r]])

        udgs = [[udg1.copy(), udg2.copy()], [udg3.copy(), udg4.copy()]]
        writer.rotate_udgs(udgs, 2)
        udg1_r, udg2_r, udg3_r, udg4_r = udg1.copy(), udg2.copy(), udg3.copy(), udg4.copy()
        udg1_r.rotate(2)
        udg2_r.rotate(2)
        udg3_r.rotate(2)
        udg4_r.rotate(2)
        self.assertEqual(udgs, [[udg4_r, udg3_r], [udg2_r, udg1_r]])

        udgs = [[udg1.copy(), udg2.copy()], [udg3.copy(), udg4.copy()]]
        writer.rotate_udgs(udgs, 3)
        udg1_r, udg2_r, udg3_r, udg4_r = udg1.copy(), udg2.copy(), udg3.copy(), udg4.copy()
        udg1_r.rotate(3)
        udg2_r.rotate(3)
        udg3_r.rotate(3)
        udg4_r.rotate(3)
        self.assertEqual(udgs, [[udg2_r, udg4_r], [udg1_r, udg3_r]])

    def test_macro_bug(self):
        self._test_reference_macro('BUG', 'bug', 'bugs')

        # Anchor with empty link text
        writer = self._get_writer()
        anchor = 'bug1'
        title = 'Bad bug'
        writer.bugs = [(anchor, title, None)]
        output = writer.expand('#BUG#{0}()'.format(anchor), ASMDIR)
        self.link_equals(output, '../reference/bugs.html#{0}'.format(anchor), title)

        # Nonexistent item
        prefix = ERROR_PREFIX.format('BUG')
        writer = self._get_writer()
        macro = '#BUG#nonexistentBug()'
        with self.assertRaisesRegexp(SkoolParsingError, '{}: Cannot determine title of item: {}'.format(prefix, macro)):
            writer.expand(macro, ASMDIR)

    def test_macro_call(self):
        writer = self._get_writer()
        writer.test_call = self._test_call

        # All arguments given
        output = writer.expand('#CALL:test_call(10,test)', ASMDIR)
        self.assertEqual(output, self._test_call(ASMDIR, 10, 'test'))

        # One argument omitted
        output = writer.expand('#CALL:test_call(3,,test2)', ASMDIR)
        self.assertEqual(output, self._test_call(ASMDIR, 3, None, 'test2'))

        prefix = ERROR_PREFIX.format('CALL')

        # Malformed #CALL macro
        with self.assertRaisesRegexp(SkoolParsingError, '{}: Malformed macro: #CALLt...'.format(prefix)):
            writer.expand('#CALLtest_call(5,s)', ASMDIR)

        # #CALL a non-method
        writer.var = 'x'
        with self.assertRaisesRegexp(SkoolParsingError, '{}: Uncallable method name: var'.format(prefix)):
            writer.expand('#CALL:var(0)', ASMDIR)

        # No argument list
        with self.assertRaisesRegexp(SkoolParsingError, '{}: No argument list specified: #CALL:test_call'.format(prefix)):
            writer.expand('#CALL:test_call', ASMDIR)

        # No return value
        writer.test_call_no_retval = self._test_call_no_retval
        output = writer.expand('#CALL:test_call_no_retval(1,2)', ASMDIR)
        self.assertEqual(output, '')

        # Unknown method
        method_name = 'nonexistent_method'
        output = writer.expand('#CALL:{0}(0)'.format(method_name), ASMDIR)
        self.assertEqual(output, '')
        self.assertEqual(self.err.getvalue().split('\n')[0], 'WARNING: Unknown method name in #CALL macro: {0}'.format(method_name))

    def test_macro_chr(self):
        writer = self._get_writer()

        output = writer.expand('#CHR169', ASMDIR)
        self.assertEqual(output, '&#169;')

        output = writer.expand('#CHR(163)1984', ASMDIR)
        self.assertEqual(output, '&#163;1984')

    def test_macro_d(self):
        writer = self._get_writer(skool=TEST_MACRO_D)

        output = writer.expand('#D32768', ASMDIR)
        self.assertEqual(output, 'First routine')

        output = writer.expand('#D$8001', ASMDIR)
        self.assertEqual(output, 'Second routine')

        prefix = ERROR_PREFIX.format('D')

        # Descriptionless entry
        address = 32770
        with self.assertRaisesRegexp(SkoolParsingError, '{}: Entry at {} has no description'.format(prefix, address)):
            writer.expand('#D{0}'.format(address), ASMDIR)

        # Nonexistent entry
        address = 32771
        with self.assertRaisesRegexp(SkoolParsingError, '{}: Cannot determine description for nonexistent entry at {}'.format(prefix, address)):
            writer.expand('#D{0}'.format(address), ASMDIR)

    def test_macro_erefs(self):
        # Entry point with one referrer
        skool = '\n'.join((
            '; Referrer',
            'c40000 JP 40004',
            '',
            '; Routine',
            'c40003 LD A,B',
            ' 40004 INC A'
        ))
        writer = self._get_writer(skool=skool)
        output = writer.expand('#EREFS40004', ASMDIR)
        self.assertEqual(output, 'routine at <a class="link" href="40000.html">40000</a>')

        writer = self._get_writer(skool=TEST_MACRO_EREFS)

        # Entry point with more than one referrer
        output = writer.expand('#EREFS30004', ASMDIR)
        self.assertEqual(output, 'routines at <a class="link" href="30000.html">30000</a> and <a class="link" href="30005.html">30005</a>')

        # Entry point with no referrers
        prefix = ERROR_PREFIX.format('EREFS')
        address = 30005
        with self.assertRaisesRegexp(SkoolParsingError, '{}: Entry point at {} has no referrers'.format(prefix, address)):
            writer.expand('#EREFS{0}'.format(address), ASMDIR)

    def test_macro_fact(self):
        self._test_reference_macro('FACT', 'fact', 'facts')

        # Anchor with empty link text
        writer = self._get_writer()
        anchor = 'fact1'
        title = 'Amazing fact'
        writer.facts = [(anchor, title, None)]
        output = writer.expand('#FACT#{0}()'.format(anchor), ASMDIR)
        self.link_equals(output, '../reference/facts.html#{0}'.format(anchor), title)

        # Nonexistent item
        prefix = ERROR_PREFIX.format('FACT')
        writer = self._get_writer()
        macro = '#FACT#nonexistentFact()'
        with self.assertRaisesRegexp(SkoolParsingError, '{}: Cannot determine title of item: {}'.format(prefix, macro)):
            writer.expand(macro, ASMDIR)

    def test_macro_font(self):
        snapshot = [0] * 65536
        writer = self._get_writer(snapshot=snapshot)

        output = writer.expand('#FONT32768,96', ASMDIR)
        self.img_equals(output, 'font', '../images/font/font.png')

        img_fname = 'font2'
        output = writer.expand('#FONT55584,96({0})'.format(img_fname), ASMDIR)
        self.img_equals(output, img_fname, '../images/font/{0}.png'.format(img_fname))

        img_fname = 'font3'
        font_addr = 32768
        char1 = [1, 2, 3, 4, 5, 6, 7, 8]
        char2 = [8, 7, 6, 5, 4, 3, 2, 1]
        char3 = [1, 3, 7, 15, 31, 63, 127, 255]
        chars = (char1, char2, char3)
        for i, char in enumerate(chars):
            snapshot[font_addr + i * 8:font_addr + (i + 1) * 8] = char
        attr = 4
        scale = 2
        x, y, w, h = 1, 2, 3, 4
        macro = '#FONT{0},{1},{2},{3}{{{4},{5},{6},{7}}}({8})'.format(font_addr, len(chars), attr, scale, x, y, w, h, img_fname)
        output = writer.expand(macro, ASMDIR)
        self.img_equals(output, img_fname, '../images/font/{0}.png'.format(img_fname))
        udg_array = [[Udg(4, char) for char in chars]]
        self._check_image(writer.image_writer, udg_array, scale, False, x, y, w, h)

    def test_macro_html(self):
        writer = self._get_writer()

        delimiters = {
            '(': ')',
            '[': ']',
            '{': '}'
        }
        for text in('', 'See <a href="url">this</a>', 'A &gt; B'):
            for delim1 in '([{!@$%^*_-+|':
                delim2 = delimiters.get(delim1, delim1)
                output = writer.expand('#HTML{0}{1}{2}'.format(delim1, text, delim2), ASMDIR)
                self.assertEqual(output, text)

        output = writer.expand('#HTML?#CHR169?', ASMDIR)
        self.assertEqual(output, '&#169;')

        # Unterminated #HTML macro
        prefix = ERROR_PREFIX.format('HTML')
        macro = '#HTML:unterminated'
        with self.assertRaisesRegexp(SkoolParsingError, '{}: No terminating delimiter: {}'.format(prefix, macro)):
            writer.expand(macro, ASMDIR)

    def test_macro_link(self):
        writer = self._get_writer(ref=TEST_MACRO_LINK_REF)

        link_text = 'bugs'
        output = writer.expand('#LINK:Bugs({0})'.format(link_text), ASMDIR)
        self.link_equals(output, '../{0}/bugs.html'.format(REFERENCE_DIR), link_text)

        link_text = 'pokes'
        anchor = '#poke1'
        output = writer.expand('#LINK:Pokes{0}({1})'.format(anchor, link_text), ASMDIR)
        self.link_equals(output, '../{0}/pokes.html{1}'.format(REFERENCE_DIR, anchor), link_text)

        output = writer.expand('#LINK:CustomPage1()', ASMDIR)
        self.link_equals(output, '../page.html', 'Custom page')

        output = writer.expand('#LINK:CustomPage2()', ASMDIR)
        self.link_equals(output, '../page2.html', 'Custom page 2')

        prefix = ERROR_PREFIX.format('LINK')

        # Malformed #LINK macro
        with self.assertRaisesRegexp(SkoolParsingError, '{}: Malformed macro: #LINKp...'.format(prefix)):
            writer.expand('#LINKpageID(text)', ASMDIR)

        # Unknown page ID
        nonexistent_page_id = 'nonexistentPageID'
        with self.assertRaisesRegexp(SkoolParsingError, '{}: Unknown page ID: {}'.format(prefix, nonexistent_page_id)):
            writer.expand('#LINK:{0}(text)'.format(nonexistent_page_id), ASMDIR)

        # No link text
        macro = '#LINK:Bugs'
        with self.assertRaisesRegexp(SkoolParsingError, '{}: No link text: {}'.format(prefix, macro)):
            writer.expand(macro, ASMDIR)

    def test_macro_list(self):
        writer = self._get_writer()

        # List with a CSS class and an item containing a skool macro
        src = "(default){ Item 1 }{ Item 2 }{ #REGa }"
        html = '\n'.join((
            '<ul class="default">',
            '<li>Item 1</li>',
            '<li>Item 2</li>',
            '<li><span class="register">A</span></li>',
            '</ul>'
        ))
        output = writer.expand('#LIST{0}\nLIST#'.format(src), ASMDIR)
        self.assertEqual(output, html)

        # List with no CSS class
        src = "{ Item 1 }"
        html = '\n'.join((
            '<ul>',
            '<li>Item 1</li>',
            '</ul>'
        ))
        output = writer.expand('#LIST{0}\nLIST#'.format(src), ASMDIR)
        self.assertEqual(output, html)

    def test_macro_poke(self):
        self._test_reference_macro('POKE', 'poke', 'pokes')

        # Anchor with empty link text
        writer = self._get_writer()
        anchor = 'poke1'
        title = 'Awesome POKE'
        writer.pokes = [(anchor, title, None)]
        output = writer.expand('#POKE#{0}()'.format(anchor), ASMDIR)
        self.link_equals(output, '../reference/pokes.html#{0}'.format(anchor), title)

        # Nonexistent item
        prefix = ERROR_PREFIX.format('POKE')
        writer = self._get_writer()
        macro = '#POKE#nonexistentPoke()'
        with self.assertRaisesRegexp(SkoolParsingError, '{}: Cannot determine title of item: {}'.format(prefix, macro)):
            writer.expand(macro, ASMDIR)

    def test_macro_pokes(self):
        writer = self._get_writer(snapshot=[0] * 65536)
        snapshot = writer.snapshot

        output = writer.expand('#POKES32768,255', ASMDIR)
        self.assertEqual(output, '')
        self.assertEqual(snapshot[32768], 255)

        output = writer.expand('#POKES32768,254,10', ASMDIR)
        self.assertEqual(output, '')
        self.assertEqual(snapshot[32768:32778], [254] * 10)

        output = writer.expand('#POKES32768,253,20,2', ASMDIR)
        self.assertEqual(output, '')
        self.assertEqual(snapshot[32768:32808:2], [253] * 20)

        output = writer.expand('#POKES49152,1;49153,2', ASMDIR)
        self.assertEqual(output, '')
        self.assertEqual(snapshot[49152:49154], [1, 2])

    def test_macro_pops(self):
        writer = self._get_writer(snapshot=[0] * 65536)
        addr, byte = 49152, 128
        writer.snapshot[addr] = byte
        writer.push_snapshot('test')
        writer.snapshot[addr] = (byte + 127) % 256
        output = writer.expand('#POPS', ASMDIR)
        self.assertEqual(output, '')
        self.assertEqual(writer.snapshot[addr], byte)

    def test_macro_pushs(self):
        writer = self._get_writer(snapshot=[0] * 65536)
        addr, byte = 32768, 64
        writer.snapshot[addr] = byte
        output = writer.expand('#PUSHStest', ASMDIR)
        self.assertEqual(output, '')
        self.assertEqual(writer.snapshot[addr], byte)
        writer.snapshot[addr] = (byte + 127) % 256
        writer.pop_snapshot()
        self.assertEqual(writer.snapshot[addr], byte)

    def test_macro_r(self):
        skool = '\n'.join((
            '; Routine',
            'c24576 LD HL,$6003',
            '',
            '; Data',
            'b$6003 DEFB 123',
            ' $6004 DEFB 246',
            '',
            '; Another routine',
            'c24581 NOP',
            ' 24582 NOP',
            '',
            '; Yet another routine',
            'c24583 CALL 24581',
            '',
            '; Another routine still',
            'c24586 CALL 24581',
            ' 24589 JP 24582',
            '',
            '; The final routine',
            'c24592 CALL 24582'
        ))
        writer = self._get_writer(skool=skool)

        # Routine reference
        output = writer.expand('#R24576', ASMDIR)
        self.link_equals(output, '24576.html', '24576')

        # Link text
        link_text = 'Testing1'
        output = writer.expand('#R24576({0})'.format(link_text), ASMDIR)
        self.link_equals(output, '24576.html', link_text)

        # Different current working directory
        output = writer.expand('#R24576', 'other')
        self.link_equals(output, '../{0}/24576.html'.format(ASMDIR), '24576')

        # Routine with a hexadecimal address
        output = writer.expand('#R24579', ASMDIR)
        self.link_equals(output, '24579.html', '6003')

        # Entry point reference
        output = writer.expand('#R24580', ASMDIR)
        self.link_equals(output, '24579.html#24580', '6004')

        # Nonexistent reference
        prefix = ERROR_PREFIX.format('R')
        address = '$ABCD'
        with self.assertRaisesRegexp(SkoolParsingError, '{}: Could not find routine file containing \{}'.format(prefix, address)):
            writer.expand('#R{0}'.format(address), ASMDIR)

    def test_macro_r_other_code(self):
        ref = '\n'.join((
            '[OtherCode:other]',
            'Source=other.skool',
            'Path=other',
            'Index=other.html',
            'Title=Other code',
            'Header=Other code'
        ))
        skool = '\n'.join((
            'c49152 LD DE,0',
            ' 49155 RET',
            '',
            'r$C000 other',
            ' $c003'
        ))
        writer = self._get_writer(ref=ref, skool=skool)

        # Reference with the same address as a remote entry
        output = writer.expand('#R49152', ASMDIR)
        self.link_equals(output, '49152.html', '49152')

        # Reference with the same address as a remote entry point
        output = writer.expand('#R49155', ASMDIR)
        self.link_equals(output, '49152.html#49155', '49155')

        # Other code, no remote entry
        output = writer.expand('#R32768@other', ASMDIR)
        self.link_equals(output, '../other/32768.html', '32768')

        # Other code with remote entry
        output = writer.expand('#R49152@other', ASMDIR)
        self.link_equals(output, '../other/49152.html', 'C000')

        # Other code with remote entry point
        output = writer.expand('#R49155@other', ASMDIR)
        self.link_equals(output, '../other/49152.html#49155', 'c003')

        # Other code with anchor and link text
        link_text = 'Testing2'
        anchor = 'testing3'
        output = writer.expand('#R32768@other#{0}({1})'.format(anchor, link_text), ASMDIR)
        self.link_equals(output, '../other/32768.html#{0}'.format(anchor), link_text)

        # Nonexistent other code reference
        prefix = ERROR_PREFIX.format('R')
        code_id = 'nonexistent'
        with self.assertRaisesRegexp(SkoolParsingError, "{}: Could not find code path for '{}' disassembly".format(prefix, code_id)):
            writer.expand('#R24576@{}'.format(code_id), ASMDIR)

    def test_macro_r_decimal(self):
        ref = '\n'.join((
            '[OtherCode:other]',
            'Source=other.skool',
            'Path=other',
            'Index=other.html',
            'Title=Other code',
            'Header=Other code'
        ))
        skool = '\n'.join((
            'c32768 LD A,B',
            ' 32769 RET',
            '',
            'r$C000 other',
            ' $C003'
        ))
        writer = self._get_writer(ref=ref, skool=skool, base=BASE_10)

        # Routine
        output = writer.expand('#R32768', ASMDIR)
        self.link_equals(output, '32768.html', '32768')

        # Routine entry point
        output = writer.expand('#R32769', ASMDIR)
        self.link_equals(output, '32768.html#32769', '32769')

        # Other code, no remote entry
        output = writer.expand('#R32768@other', ASMDIR)
        self.link_equals(output, '../other/32768.html', '32768')

        # Other code with remote entry
        output = writer.expand('#R49152@other', ASMDIR)
        self.link_equals(output, '../other/49152.html', '49152')

        # Other code with remote entry point
        output = writer.expand('#R49155@other', ASMDIR)
        self.link_equals(output, '../other/49152.html#49155', '49155')

    def test_macro_r_hex(self):
        ref = '\n'.join((
            '[OtherCode:other]',
            'Source=other.skool',
            'Path=other',
            'Index=other.html',
            'Title=Other code',
            'Header=Other code'
        ))
        skool = '\n'.join((
            'c32768 LD A,B',
            ' 32769 RET',
            '',
            'r$C000 other',
            ' $C003'
        ))
        writer = self._get_writer(ref=ref, skool=skool, base=BASE_16)

        # Routine
        output = writer.expand('#R32768', ASMDIR)
        self.link_equals(output, '32768.html', '8000')

        # Routine entry point
        output = writer.expand('#R32769', ASMDIR)
        self.link_equals(output, '32768.html#32769', '8001')

        # Other code, no remote entry
        output = writer.expand('#R32768@other', ASMDIR)
        self.link_equals(output, '../other/32768.html', '8000')

        # Other code with remote entry
        output = writer.expand('#R49152@other', ASMDIR)
        self.link_equals(output, '../other/49152.html', 'C000')

        # Other code with remote entry point
        output = writer.expand('#R49155@other', ASMDIR)
        self.link_equals(output, '../other/49152.html#49155', 'C003')

    def test_macro_r_hex_lower(self):
        ref = '\n'.join((
            '[OtherCode:Other]',
            'Source=other.skool',
            'Path=other',
            'Index=other.html',
            'Title=Other code',
            'Header=Other code'
        ))
        skool = '\n'.join((
            'c40970 LD A,B',
            ' 40971 RET',
            '',
            'r$C000 other',
            ' $C003'
        ))
        writer = self._get_writer(ref=ref, skool=skool, case=CASE_LOWER, base=BASE_16)

        # Routine
        output = writer.expand('#R40970', ASMDIR)
        self.link_equals(output, '40970.html', 'a00a')

        # Routine entry point
        output = writer.expand('#R40971', ASMDIR)
        self.link_equals(output, '40970.html#40971', 'a00b')

        # Other code, no remote entry
        output = writer.expand('#R45066@Other', ASMDIR)
        self.link_equals(output, '../other/45066.html', 'b00a')

        # Other code with remote entry
        output = writer.expand('#R49152@Other', ASMDIR)
        self.link_equals(output, '../other/49152.html', 'c000')

        # Other code with remote entry point
        output = writer.expand('#R49155@Other', ASMDIR)
        self.link_equals(output, '../other/49152.html#49155', 'c003')

    def test_macro_r_hex_upper(self):
        ref = '\n'.join((
            '[OtherCode:other]',
            'Source=other.skool',
            'Path=other',
            'Index=other.html',
            'Title=Other code',
            'Header=Other code'
        ))
        skool = '\n'.join((
            'c$a00a LD A,B',
            ' 40971 RET',
            '',
            'r$c000 other',
            ' $c003'
        ))
        writer = self._get_writer(ref=ref, skool=skool, case=CASE_UPPER, base=BASE_16)

        # Routine
        output = writer.expand('#R40970', ASMDIR)
        self.link_equals(output, '40970.html', 'A00A')

        # Routine entry point
        output = writer.expand('#R40971', ASMDIR)
        self.link_equals(output, '40970.html#40971', 'A00B')

        # Other code, no remote entry
        output = writer.expand('#R45066@other', ASMDIR)
        self.link_equals(output, '../other/45066.html', 'B00A')

        # Other code with remote entry
        output = writer.expand('#R49152@other', ASMDIR)
        self.link_equals(output, '../other/49152.html', 'C000')

        # Other code with remote entry point
        output = writer.expand('#R49155@other', ASMDIR)
        self.link_equals(output, '../other/49152.html#49155', 'C003')

    def test_macro_refs(self):
        # One referrer
        skool = '\n'.join((
            '; Referrer',
            'c40000 JP 40003',
            '',
            '; Routine',
            'c40003 LD A,B'
        ))
        writer = self._get_writer(skool=skool)
        output = writer.expand('#REFS40003', ASMDIR)
        self.assertEqual(output, 'routine at <a class="link" href="40000.html">40000</a>')

        writer = self._get_writer(skool=TEST_MACRO_REFS_SKOOL)

        # Some referrers
        for address in ('24579', '$6003'):
            output = writer.expand('#REFS{}'.format(address), ASMDIR)
            self.assertEqual(output, 'routines at <a class="link" href="24581.html">24581</a>, <a class="link" href="24584.html">24584</a> and <a class="link" href="24590.html">24590</a>')

        # No referrers
        output = writer.expand('#REFS24576', ASMDIR)
        self.assertEqual(output, 'Not used directly by any other routines')

        # Nonexistent entry
        prefix = ERROR_PREFIX.format('REFS')
        address = 40000
        with self.assertRaisesRegexp(SkoolParsingError, '{}: No entry at {}'.format(prefix, address)):
            writer.expand('#REFS{0}'.format(address), ASMDIR)

    def test_macro_reg(self):
        # Lower case
        writer = self._get_writer()
        writer.case = CASE_LOWER
        output = writer.expand('#REGhl', ASMDIR)
        self.assertEqual(output, '<span class="register">hl</span>')
        writer.case = None

        # Upper case, all registers
        for reg in ("a", "b", "c", "d", "e", "h", "l", "i", "r", "ixl", "ixh", "iyl", "iyh", "b'", "c'", "d'", "e'", "h'", "l'", "bc", "de", "hl", "sp", "ix", "iy", "bc'", "de'", "hl'"):
            output = writer.expand('#REG{0}'.format(reg), ASMDIR)
            self.assertEqual(output, '<span class="register">{0}</span>'.format(reg.upper()))

        prefix = ERROR_PREFIX.format('REG')

        # Missing register argument
        with self.assertRaisesRegexp(SkoolParsingError, '{}: Missing register argument'.format(prefix)):
            writer.expand('#REG', ASMDIR)

        # Bad register argument
        bad_reg = 'abcd'
        with self.assertRaisesRegexp(SkoolParsingError, '{}: Bad register: "{}"'.format(prefix, bad_reg)):
            writer.expand('#REG{0}'.format(bad_reg), ASMDIR)

    def test_macro_scr(self):
        snapshot = [0] * 65536
        writer = self._get_writer(snapshot=snapshot)

        output = writer.expand('#SCR', ASMDIR)
        self.img_equals(output, 'scr', '../images/scr/scr.png')

        scr_fname = 'scr2'
        output = writer.expand('#SCR2,0,0,10,10({0})'.format(scr_fname), ASMDIR)
        self.img_equals(output, scr_fname, '../images/scr/{0}.png'.format(scr_fname))

        scr_fname = 'scr3'
        data = [128, 64, 32, 16, 8, 4, 2, 1]
        attr = 48
        snapshot[16384:18432:256] = data
        snapshot[22528] = attr
        scale = 2
        x, y, w, h = 1, 2, 5, 6
        macro = '#SCR{0},0,0,1,1{{{1},{2},{3},{4}}}({5})'.format(scale, x, y, w, h, scr_fname)
        output = writer.expand(macro, ASMDIR)
        self.img_equals(output, scr_fname, '../images/scr/{0}.png'.format(scr_fname))
        udg_array = [[Udg(attr, data)]]
        self._check_image(writer.image_writer, udg_array, scale, False, x, y, w, h)

    def test_macro_space(self):
        writer = self._get_writer()

        output = writer.expand('#SPACE', ASMDIR)
        self.assertEqual(output, '&#160;')

        num = 10
        output = writer.expand('#SPACE{0}'.format(num), ASMDIR)
        self.assertEqual(output, '&#160;' * num)

        num = 7
        output = writer.expand('1#SPACE({0})1'.format(num), ASMDIR)
        self.assertEqual(output, '1{0}1'.format('&#160;' * num))

    def test_macro_table(self):
        writer = self._get_writer()
        for src, html in ((TABLE_SRC, TABLE_HTML), (TABLE2_SRC, TABLE2_HTML)):
            output = writer.expand('#TABLE{0}\nTABLE#'.format(src), ASMDIR)
            self.assertEqual(output, html)

    def test_macro_udg(self):
        snapshot = [0] * 65536
        writer = self._get_writer(snapshot=snapshot)

        udg_fname = 'udg32768_56x4'
        output = writer.expand('#UDG32768', ASMDIR)
        self.img_equals(output, udg_fname, '../{0}/{1}.png'.format(UDGDIR, udg_fname))

        udg_fname = 'udg40000_2x3'
        output = writer.expand('#UDG40000,2,3', ASMDIR)
        self.img_equals(output, udg_fname, '../{0}/{1}.png'.format(UDGDIR, udg_fname))

        udg_fname = 'test_udg'
        output = writer.expand('#UDG32768,2,6,1,0:49152,2({0})'.format(udg_fname), ASMDIR)
        self.img_equals(output, udg_fname, '../{0}/{1}.png'.format(UDGDIR, udg_fname))

        udg_fname = 'test_udg2'
        udg_addr = 32768
        attr = 2
        scale = 1
        step = 1
        inc = 0
        mask_addr = 32776
        x, y, w, h = 2, 1, 3, 4
        udg_data = [136] * 8
        udg_mask = [255] * 8
        snapshot[udg_addr:udg_addr + 8 * step:step] = udg_data
        snapshot[mask_addr:mask_addr + 8 * step:step] = udg_mask
        macro = '#UDG{0},{1},{2},{3},{4}:{5},{6}{{{7},{8},{9},{10}}}({11})'.format(udg_addr, attr, scale, step, inc, mask_addr, step, x, y, w, h, udg_fname)
        output = writer.expand(macro, ASMDIR)
        self.img_equals(output, udg_fname, '../{0}/{1}.png'.format(UDGDIR, udg_fname))
        udg_array = [[Udg(attr, udg_data, udg_mask)]]
        self._check_image(writer.image_writer, udg_array, scale, True, x, y, w, h)

    def test_macro_udgarray(self):
        snapshot = [0] * 65536
        writer = self._get_writer(snapshot=snapshot)

        udg_fname = 'test_udg_array'
        output = writer.expand('#UDGARRAY8;32768-32784-1-8({0})'.format(udg_fname), ASMDIR)
        self.img_equals(output, udg_fname, '../{0}/{1}.png'.format(UDGDIR, udg_fname))

        udg_fname = 'test_udg_array2'
        output = writer.expand('#UDGARRAY8,56,2,256,0;32768;32769;32770;32771;32772x12({0})'.format(udg_fname), ASMDIR)
        self.img_equals(output, udg_fname, '../{0}/{1}.png'.format(UDGDIR, udg_fname))

        udg_fname = 'test_udg_array3'
        udg_addr = 32768
        mask_addr = 32769
        width = 2
        attr = 5
        scale = 1
        step = 256
        inc = 0
        x, y, w, h = 4, 6, 8, 5
        udg_data = [195] * 8
        udg_mask = [255] * 8
        snapshot[udg_addr:udg_addr + 8 * step:step] = udg_data
        snapshot[mask_addr:mask_addr + 8 * step:step] = udg_mask
        macro = '#UDGARRAY{0},{1},{2},{3},{4};{5}x4:{6}x4{{{7},{8},{9},{10}}}({11})'.format(width, attr, scale, step, inc, udg_addr, mask_addr, x, y, w, h, udg_fname)
        output = writer.expand(macro, ASMDIR)
        self.img_equals(output, udg_fname, '../{0}/{1}.png'.format(UDGDIR, udg_fname))
        udg_array = [[Udg(attr, udg_data, udg_mask)] * width] * 2
        self._check_image(writer.image_writer, udg_array, scale, True, x, y, w, h)

        # Flip
        udg_fname = 'test_udg_array4'
        udg = Udg(56, [128, 64, 32, 16, 8, 4, 2, 1])
        udg_addr = 40000
        snapshot[udg_addr:udg_addr + 8] = udg.data
        output = writer.expand('#UDGARRAY1,,,,,1;{0}({1})'.format(udg_addr, udg_fname), ASMDIR)
        self.img_equals(output, udg_fname, '../{0}/{1}.png'.format(UDGDIR, udg_fname))
        udg.flip(1)
        self._check_image(writer.image_writer, [[udg]], 2, False, 0, 0, None, None)

        # Rotate
        udg_fname = 'test_udg_array5'
        udg = Udg(56, [128, 64, 32, 16, 8, 4, 2, 1])
        udg_addr = 50000
        snapshot[udg_addr:udg_addr + 8] = udg.data
        output = writer.expand('#UDGARRAY1,,,,,,2;{0}({1})'.format(udg_addr, udg_fname), ASMDIR)
        self.img_equals(output, udg_fname, '../{0}/{1}.png'.format(UDGDIR, udg_fname))
        udg.rotate(2)
        self._check_image(writer.image_writer, [[udg]], 2, False, 0, 0, None, None)

        # Missing filename argument
        prefix = ERROR_PREFIX.format('UDGARRAY')
        macro = '#UDGARRAY1;30000'
        with self.assertRaisesRegexp(SkoolParsingError, '{}: Missing filename: {}'.format(prefix, macro)):
            writer.expand(macro, ASMDIR)

    def test_macro_udgtable(self):
        writer = self._get_writer()
        output = writer.expand('#UDGTABLE{0}\nUDGTABLE#'.format(TABLE_SRC), ASMDIR)
        self.assertEqual(output, TABLE_HTML)

    def test_unsupported_macro(self):
        writer = self._get_writer()
        macro = '#BUG'
        writer.macros[macro] = self._unsupported_macro
        with self.assertRaisesRegexp(SkoolParsingError, 'Found unsupported macro: {}'.format(macro)):
            writer.expand('{0}#bug1'.format(macro), ASMDIR)

    def test_unknown_macro(self):
        writer = self._get_writer()
        for macro, params in (('#FOO', 'xyz'), ('#BAR', '1,2(baz)'), ('#UDGS', '#r1'), ('#LINKS', '')):
            with self.assertRaisesRegexp(SkoolParsingError, 'Found unknown macro: {}'.format(macro)):
                writer.expand(macro + params, ASMDIR)

    def test_parameter_LinkOperands(self):
        ref = '[Game]\nLinkOperands={}'
        skool = '\n'.join((
            '; Routine at 32768',
            'c32768 RET',
            '',
            '; Routine at 32769',
            'c32769 CALL 32768',
            ' 32772 DEFW 32768',
            ' 32774 DJNZ 32768',
            ' 32776 JP 32768',
            ' 32779 JR 32768',
            ' 32781 LD HL,32768'
        ))
        for param_value in ('CALL,JP,JR', 'CALL,DEFW,djnz,JP,LD'):
            writer = self._get_writer(ref=ref.format(param_value), skool=skool)
            link_operands = tuple(param_value.upper().split(','))
            self.assertEqual(writer.link_operands, link_operands)
            writer.write_asm_entries()
            html = self.read_file(join(ASMDIR, '32769.html'), True)
            link = '<a class="link" href="32768.html">32768</a>'
            line_no = 34
            for prefix in ('CALL ', 'DEFW ', 'DJNZ ', 'JP ', 'JR ', 'LD HL,'):
                inst_type = prefix.split()[0]
                exp_html = prefix + (link if inst_type in link_operands else '32768')
                self.assertEqual(html[line_no], '<td class="instruction">{}</td>'.format(exp_html))
                line_no += 5

    def test_html_escape(self):
        # Check that HTML characters from the skool file are escaped
        writer = self._get_writer(skool=TEST_HTML_SKOOL)
        fname = 'test.html'
        writer.write_entry(ASMDIR, writer.entries[24576], fname)
        html = self.read_file(join(ASMDIR, fname))
        self.assertTrue('DEFM "&lt;&amp;&gt;"' in html)
        self.assertTrue('a &lt;= b &amp; b &gt;= c' in html)

    def test_html_no_escape(self):
        # Check that HTML characters from the ref file are not escaped
        writer = self._get_writer(ref=TEST_HTML_REF)
        writer.write_bugs()
        html = self.read_file(join(REFERENCE_DIR, 'bugs.html'))
        self.assertTrue('<p>Hello</p>' in html)

    def test_write_index(self):
        for i, ref in enumerate(TEST_WRITE_INDEX_REF):
            writer = self._get_writer(ref=ref, skool='')
            for f in TEST_WRITE_INDEX_FILES[i]:
                self.write_text_file(path=join(self.odir, GAMEDIR, f))
            writer.write_index()
            subs = {
                'name': basename(self.skoolfile)[:-6],
                'title': 'Index',
                'header_prefix': 'The complete',
                'header_suffix': 'RAM disassembly',
                'path': '',
                'body_class': 'main',
                'content': INDEX[i],
                'footer': BARE_FOOTER
            }
            self.assert_files_equal('index.html', subs, True)
            self.remove_files()

        # Empty index with logo image
        writer = self._get_writer(skool='')
        logo_image_path = 'logo.png'
        writer.game_vars['LogoImage'] = logo_image_path
        self.write_bin_file(path=join(self.odir, GAMEDIR, logo_image_path))
        writer.write_index()
        game = basename(self.skoolfile)[:-6]
        subs = {
            'name': game,
            'title': 'Index',
            'header_prefix': 'The complete',
            'logo': '<img src="{0}" alt="{1}" />'.format(logo_image_path, game),
            'header_suffix': 'RAM disassembly',
            'path': '',
            'body_class': 'main',
            'content': INDEX[0],
            'footer': BARE_FOOTER
        }
        self.assert_files_equal('index.html', subs, True)

    def test_write_asm_entries(self):
        writer = self._get_writer(ref=TEST_WRITE_ASM_ENTRIES_REF, skool=TEST_WRITE_ASM_ENTRIES_SKOOL)
        common_subs = {
            'name': basename(self.skoolfile)[:-6],
            'path': '../',
            'body_class': 'disassembly',
            'footer': BARE_FOOTER,
        }
        writer.write_asm_entries()

        # Routine at 24576
        subs = {
            'title': 'Routine at 24576',
            'header': 'Routines',
            'up': 24576,
            'next': 24578,
            'content': ENTRY1
        }
        subs.update(common_subs)
        self.assert_files_equal(join(ASMDIR, '24576.html'), subs)

        # Data at 24578
        subs = {
            'title': 'Data at 24578',
            'header': 'Data',
            'prev': 24576,
            'up': 24578,
            'next': 24579,
            'content': ENTRY2
        }
        subs.update(common_subs)
        self.assert_files_equal(join(ASMDIR, '24578.html'), subs)

        # Routine at 24579
        subs = {
            'title': 'Routine at 24579',
            'header': 'Routines',
            'prev': 24578,
            'up': 24579,
            'next': 24581,
            'content': ENTRY3
        }
        subs.update(common_subs)
        self.assert_files_equal(join(ASMDIR, '24579.html'), subs)

        # Game status buffer entry at 24581
        subs = {
            'title': 'Game status buffer entry at 24581',
            'header': 'Game status buffer',
            'prev': 24579,
            'up': 24581,
            'next': 24583,
            'content': ENTRY4
        }
        subs.update(common_subs)
        self.assert_files_equal(join(ASMDIR, '24581.html'), subs)

        # Unused RAM at 24583
        subs = {
            'title': 'Unused RAM at 24583',
            'header': 'Unused',
            'prev': 24581,
            'up': 24583,
            'next': 24584,
            'content': ENTRY5
        }
        subs.update(common_subs)
        self.assert_files_equal(join(ASMDIR, '24583.html'), subs)

        # Routine at 24584
        subs = {
            'title': 'Routine at 24584',
            'header': 'Routines',
            'prev': 24583,
            'up': 24584,
            'content': ENTRY6
        }
        subs.update(common_subs)
        self.assert_files_equal(join(ASMDIR, '24584.html'), subs)

    def test_asm_labels(self):
        writer = self._get_writer(skool=TEST_ASM_LABELS_SKOOL, asm_labels=True)
        common_subs = {
            'name': basename(self.skoolfile)[:-6],
            'path': '../',
            'body_class': 'disassembly',
            'footer': BARE_FOOTER,
        }
        writer.write_asm_entries()

        # Routine at 50000
        subs = {
            'header': 'Routines',
            'title': 'Routine at 50000 (START)',
            'up': 50000,
            'next': 50005,
            'content': ASM_LABELS_ENTRY1
        }
        subs.update(common_subs)
        self.assert_files_equal(join(ASMDIR, '50000.html'), subs)

        # Routine at 50005
        subs = {
            'header': 'Routines',
            'title': 'Routine at 50005',
            'prev': 50000,
            'up': 50005,
            'next': 50008,
            'content': ASM_LABELS_ENTRY2
        }
        subs.update(common_subs)
        self.assert_files_equal(join(ASMDIR, '50005.html'), subs)

        # DEFW statement at 50008
        subs = {
            'header': 'Data',
            'title': 'Data at 50008',
            'prev': 50005,
            'up': 50008,
            'content': ASM_LABELS_ENTRY3
        }
        subs.update(common_subs)
        self.assert_files_equal(join(ASMDIR, '50008.html'), subs)

    def test_write_map(self):
        writer = self._get_writer(skool=TEST_WRITE_MAP)
        common_subs = {
            'name': basename(self.skoolfile)[:-6],
            'path': '../',
            'body_class': 'map',
            'footer': BARE_FOOTER
        }

        # Memory map
        writer.write_map(writer.memory_maps['MemoryMap'])
        subs = {
            'title': 'Memory map',
            'content': MEMORY_MAP
        }
        subs.update(common_subs)
        self.assert_files_equal(join(MAPS_DIR, 'all.html'), subs)

        # Routines map
        writer.write_map(writer.memory_maps['RoutinesMap'])
        subs = {
            'title': 'Routines',
            'content': ROUTINES_MAP
        }
        subs.update(common_subs)
        self.assert_files_equal(join(MAPS_DIR, 'routines.html'), subs)

        # Data map
        writer.write_map(writer.memory_maps['DataMap'])
        subs = {
            'title': 'Data',
            'content': DATA_MAP
        }
        subs.update(common_subs)
        self.assert_files_equal(join(MAPS_DIR, 'data.html'), subs)

        # Messages map
        writer.write_map(writer.memory_maps['MessagesMap'])
        subs = {
            'title': 'Messages',
            'content': MESSAGES_MAP
        }
        subs.update(common_subs)
        self.assert_files_equal(join(MAPS_DIR, 'messages.html'), subs)

        # Unused map
        writer.write_map(writer.memory_maps['UnusedMap'])
        subs = {
            'title': 'Unused addresses',
            'content': UNUSED_MAP
        }
        subs.update(common_subs)
        self.assert_files_equal(join(MAPS_DIR, 'unused.html'), subs)

        # Custom map
        map_details = {
            'Path': join(MAPS_DIR, 'custom.html'),
            'Title': 'Custom map',
            'Intro': 'Introduction.',
            'EntryTypes': 'cg'
        }
        writer.write_map(map_details)
        subs = {
            'title': map_details['Title'],
            'content': CUSTOM_MAP
        }
        subs.update(common_subs)
        self.assert_files_equal(map_details['Path'], subs)

    def test_write_changelog(self):
        writer = self._get_writer(ref=TEST_WRITE_CHANGELOG_REF, skool='')
        writer.write_changelog()
        subs = {
            'name': basename(self.skoolfile)[:-6],
            'title': 'Changelog',
            'path': '../',
            'body_class': 'changelog',
            'content': CHANGELOG,
            'footer': BARE_FOOTER
        }
        self.assert_files_equal(join(REFERENCE_DIR, 'changelog.html'), subs)

    def test_write_glossary(self):
        writer = self._get_writer(ref=TEST_WRITE_GLOSSARY_REF, skool='')
        writer.write_glossary()
        subs = {
            'name': basename(self.skoolfile)[:-6],
            'title': 'Glossary',
            'path': '../',
            'body_class': 'glossary',
            'content': GLOSSARY,
            'footer': BARE_FOOTER
        }
        self.assert_files_equal(join(REFERENCE_DIR, 'glossary.html'), subs)

    def test_write_graphics(self):
        writer = self._get_writer(ref=TEST_WRITE_GRAPHICS_REF, skool='')
        writer.write_graphics()
        subs = {
            'name': basename(self.skoolfile)[:-6],
            'title': 'Graphics',
            'path': '../',
            'body_class': 'graphics',
            'content': '<em>This is the graphics page.</em>\n',
            'footer': BARE_FOOTER
        }
        self.assert_files_equal(join(GRAPHICS_DIR, 'graphics.html'), subs)

    def test_write_page(self):
        writer = self._get_writer(ref=TEST_WRITE_PAGE_REF, skool='')
        writer.write_page('CustomPage')
        subs = {
            'name': basename(self.skoolfile)[:-6],
            'title': 'Custom page',
            'path': '',
            'js': 'test-html.js',
            'content': '<b>This is the content of the custom page.</b>\n',
            'footer': BARE_FOOTER
        }
        self.assert_files_equal('page.html', subs)

    def test_write_bugs(self):
        writer = self._get_writer(ref=TEST_WRITE_BUGS_REF, skool='')
        writer.write_bugs()
        subs = {
            'name': basename(self.skoolfile)[:-6],
            'title': 'Bugs',
            'path': '../',
            'body_class': 'bugs',
            'content': BUGS,
            'footer': BARE_FOOTER
        }
        self.assert_files_equal(join(REFERENCE_DIR, 'bugs.html'), subs)

    def test_write_facts(self):
        writer = self._get_writer(ref=TEST_WRITE_FACTS_REF, skool='')
        writer.write_facts()
        subs = {
            'name': basename(self.skoolfile)[:-6],
            'title': 'Trivia',
            'path': '../',
            'body_class': 'facts',
            'content': FACTS,
            'footer': BARE_FOOTER
        }
        self.assert_files_equal(join(REFERENCE_DIR, 'facts.html'), subs)

    def test_write_pokes(self):
        writer = self._get_writer(ref=TEST_WRITE_POKES_REF, skool='')
        writer.write_pokes()
        subs = {
            'name': basename(self.skoolfile)[:-6],
            'title': 'Pokes',
            'path': '../',
            'body_class': 'pokes',
            'content': POKES,
            'footer': BARE_FOOTER
        }
        self.assert_files_equal(join(REFERENCE_DIR, 'pokes.html'), subs)

    def test_write_graphic_glitches(self):
        writer = self._get_writer(ref=TEST_WRITE_GRAPHIC_GLITCHES_REF, skool='')
        writer.write_graphic_glitches()
        subs = {
            'name': basename(self.skoolfile)[:-6],
            'title': 'Graphic glitches',
            'path': '../',
            'body_class': 'graphics',
            'content': GRAPHIC_GLITCHES,
            'footer': BARE_FOOTER
        }
        self.assert_files_equal(join(GRAPHICS_DIR, 'glitches.html'), subs)

    def test_write_gbuffer(self):
        writer = self._get_writer(ref=TEST_WRITE_GBUFFER_REF, skool=TEST_WRITE_GBUFFER_SKOOL)
        writer.write_gbuffer()
        subs = {
            'name': basename(self.skoolfile)[:-6],
            'title': 'Game status buffer',
            'path': '../',
            'body_class': 'gbuffer',
            'content': GAME_STATUS_BUFFER,
            'footer': BARE_FOOTER
        }
        self.assert_files_equal(join(BUFFERS_DIR, 'gbuffer.html'), subs)

    def test_index_page_id(self):
        writer = self._get_writer(ref=TEST_INDEX_PAGE_ID_REF)
        self.assertTrue('SecondaryCode' in writer.paths)
        self.assertEqual(writer.paths['SecondaryCode'], 'secondary/secondary.html')

    def test_page_content(self):
        writer = self._get_writer(ref=TEST_PAGE_CONTENT_REF)
        self.assertFalse('ExistingPage' in writer.page_ids)
        self.assertTrue('ExistingPage' in writer.paths)
        self.assertTrue(writer.paths['ExistingPage'], 'asm/32768.html')

    def test_get_udg_addresses(self):
        writer = self._get_writer(snapshot=())
        addr_specs = [
            (0, 1, [0]),
            ('1', 1, [1]),
            ('2x3', 1, [2] * 3),
            ('0-3', 1, [0, 1, 2, 3]),
            ('0-2x3', 1, [0, 1, 2] * 3),
            ('0-6-2', 1, [0, 2, 4, 6]),
            ('0-6-3x2', 1, [0, 3, 6] * 2),
            ('0-49-1-16', 2, [0, 1, 16, 17, 32, 33, 48, 49]),
            ('0-528-8-256x4', 3, [0, 8, 16, 256, 264, 272, 512, 520, 528] * 4)
        ]
        for addr_spec, width, exp_addresses in addr_specs:
            self.assertEqual(writer._get_udg_addresses(addr_spec, width), exp_addresses)

    def test_get_snapshot_name(self):
        writer = self._get_writer()
        names = ['snapshot1', 'next', 'final']
        for name in names:
            writer.push_snapshot(name)
        while names:
            self.assertEqual(writer.get_snapshot_name(), names.pop())
            writer.pop_snapshot()

    def test_should_write_map(self):
        writer = self._get_writer(ref=TEST_SHOULD_WRITE_MAP_REF, skool=TEST_SHOULD_WRITE_MAP_SKOOL)
        self.assertTrue(writer.should_write_map(writer.memory_maps['MemoryMap']))
        self.assertTrue(writer.should_write_map(writer.memory_maps['RoutinesMap']))
        self.assertTrue(writer.should_write_map(writer.memory_maps['DataMap']))
        self.assertFalse(writer.should_write_map(writer.memory_maps['MessagesMap']))
        self.assertFalse(writer.should_write_map(writer.memory_maps['UnusedMap']))

    def test_write_registers(self):
        writer = self._get_writer(snapshot=())

        # Traditional
        registers = []
        registers.append(Register('', 'A', 'Some value'))
        registers.append(Register('', 'B', 'Some other value'))
        stream = StringIO()
        writer.write_registers(stream, registers, ASMDIR)
        self.assertEqual(stream.getvalue(), REGISTERS_1)

        # With prefixes
        writer.game_vars['InputRegisterTableHeader'] = 'Input'
        writer.game_vars['OutputRegisterTableHeader'] = 'Output'
        registers = []
        registers.append(Register('Input', 'A', 'Some value'))
        registers.append(Register('', 'B', 'Some other value'))
        registers.append(Register('Output', 'D', 'The result'))
        registers.append(Register('', 'E', 'Result flags'))
        stream = StringIO()
        writer.write_registers(stream, registers, ASMDIR)
        self.assertEqual(stream.getvalue(), REGISTERS_2)

    def test_write_image(self):
        file_info = MockFileInfo('html', 'test_write_image')
        image_writer = MockImageWriter2()
        writer = HtmlWriter(MockSkoolParser(), RefParser(), file_info, image_writer)

        # PNG
        image_path = 'images/test.png'
        udgs = [[]]
        writer.write_image(image_path, udgs)
        self.assertEqual(file_info.path, join(file_info.odir, image_path))
        self.assertEqual(file_info.mode, 'wb')
        self.assertEqual(image_writer.udg_array, udgs)
        self.assertEqual(image_writer.img_format, 'png')
        self.assertEqual(image_writer.scale, 2)
        self.assertFalse(image_writer.mask)
        self.assertEqual(image_writer.x, 0)
        self.assertEqual(image_writer.y, 0)
        self.assertEqual(image_writer.width, None)
        self.assertEqual(image_writer.height, None)

        # GIF
        image_path = 'images/test.gif'
        writer.write_image(image_path, None)
        self.assertEqual(file_info.path, join(file_info.odir, image_path))
        self.assertEqual(image_writer.img_format, 'gif')

        # Unsupported format
        image_path = 'images/test.jpg'
        with self.assertRaisesRegexp(SkoolKitError, 'Unsupported image file format: {}'.format(image_path)):
            writer.write_image(image_path, None)

    def test_write_header_with_title(self):
        writer = self._get_writer(skool='')
        ofile = StringIO()
        title = 'Main page'
        cwd = ''
        writer.write_header(ofile, title, cwd, body_class=None, body_title=None, js=None)
        header = ofile.getvalue().split('\n')
        index = FileInfo.relpath(cwd, writer.paths['GameIndex'])
        game_name = self.skoolfile[:-6]
        self.assertEqual(header[7], '<title>{}: {}</title>'.format(game_name, title))
        self.assertEqual(header[14], '<td class="headerText">{}</td>'.format(title))

    def test_write_header_with_body_class(self):
        writer = self._get_writer(skool='')
        ofile = StringIO()
        cwd = 'subdir'
        body_class = 'default'
        writer.write_header(ofile, title='', cwd=cwd, body_class=body_class, body_title=None, js=None)
        header = ofile.getvalue().split('\n')
        index = FileInfo.relpath(cwd, writer.paths['GameIndex'])
        self.assertEqual(header[10], '<body class="{}">'.format(body_class))

    def test_write_header_with_body_title(self):
        writer = self._get_writer(skool='')
        ofile = StringIO()
        cwd = 'subdir'
        body_title = 'ABCD'
        writer.write_header(ofile, title='', cwd=cwd, body_class=None, body_title=body_title, js=None)
        header = ofile.getvalue().split('\n')
        index = FileInfo.relpath(cwd, writer.paths['GameIndex'])
        game_name = self.skoolfile[:-6]
        self.assertEqual(header[14], '<td class="headerText">{}</td>'.format(body_title))

    def test_write_header_with_single_js(self):
        writer = self._get_writer(skool='')
        ofile = StringIO()
        cwd = 'subdir/subdir2'
        js = 'js/script.js'
        writer.write_header(ofile, title='', cwd=cwd, body_class=None, body_title=None, js=js)
        header = ofile.getvalue().split('\n')
        js_path = FileInfo.relpath(cwd, '{}/{}'.format(writer.paths['JavaScriptPath'], basename(js)))
        self.assertEqual(header[9], '<script type="text/javascript" src="{}"></script>'.format(js_path))

    def test_write_header_with_multiple_js(self):
        writer = self._get_writer(skool='')
        ofile = StringIO()
        cwd = 'subdir'
        js_files = ['js/script1.js', 'js/script2.js']
        js = ';'.join(js_files)
        writer.write_header(ofile, title='', cwd=cwd, body_class=None, body_title=None, js=js)
        header = ofile.getvalue().split('\n')
        js_paths = [FileInfo.relpath(cwd, '{}/{}'.format(writer.paths['JavaScriptPath'], basename(js))) for js in js_files]
        self.assertEqual(header[9], '<script type="text/javascript" src="{}"></script>'.format(js_paths[0]))
        self.assertEqual(header[10], '<script type="text/javascript" src="{}"></script>'.format(js_paths[1]))

    def test_write_header_with_single_css(self):
        css = 'css/game.css'
        ref = '[Game]\nStyleSheet={}'.format(css)
        writer = self._get_writer(ref=ref, skool='')
        ofile = StringIO()
        cwd = ''
        writer.write_header(ofile, title='', cwd=cwd, body_class=None, body_title=None, js=None)
        header = ofile.getvalue().split('\n')
        css_path = FileInfo.relpath(cwd, '{}/{}'.format(writer.paths['StyleSheetPath'], basename(css)))
        self.assertEqual(header[8], '<link rel="stylesheet" type="text/css" href="{}" />'.format(css_path))

    def test_write_header_with_multiple_css(self):
        css_files = ['css/game.css', 'css/foo.css']
        ref = '[Game]\nStyleSheet={}'.format(';'.join(css_files))
        writer = self._get_writer(ref=ref, skool='')
        ofile = StringIO()
        cwd = ''
        writer.write_header(ofile, title='', cwd=cwd, body_class=None, body_title=None, js=None)
        header = ofile.getvalue().split('\n')
        css_paths = [FileInfo.relpath(cwd, '{}/{}'.format(writer.paths['StyleSheetPath'], basename(css))) for css in css_files]
        self.assertEqual(header[8], '<link rel="stylesheet" type="text/css" href="{}" />'.format(css_paths[0]))
        self.assertEqual(header[9], '<link rel="stylesheet" type="text/css" href="{}" />'.format(css_paths[1]))

    def test_write_header_no_game_name(self):
        writer = self._get_writer(skool='')
        ofile = StringIO()
        cwd = ''
        writer.write_header(ofile, title='', cwd=cwd, body_class=None, body_title=None, js=None)
        header = ofile.getvalue().split('\n')
        index = FileInfo.relpath(cwd, writer.paths['GameIndex'])
        game_name = self.skoolfile[:-6]
        self.assertEqual(header[10], '<body>')
        self.assertEqual(header[13], '<td class="headerLogo"><a class="link" href="{}">{}</a></td>'.format(index, game_name))

    def test_write_header_with_game_name(self):
        game_name = 'Some game'
        writer = self._get_writer(ref='[Game]\nGame={}'.format(game_name), skool='')
        ofile = StringIO()
        cwd = 'subdir'
        writer.write_header(ofile, title='', cwd=cwd, body_class=None, body_title=None, js=None)
        header = ofile.getvalue().split('\n')
        index = FileInfo.relpath(cwd, writer.paths['GameIndex'])
        self.assertEqual(header[13], '<td class="headerLogo"><a class="link" href="{}">{}</a></td>'.format(index, game_name))

    def test_write_header_with_nonexistent_logo_image(self):
        writer = self._get_writer(ref='[Game]\nLogoImage=images/nonexistent.png', skool='')
        ofile = StringIO()
        cwd = 'subdir'
        writer.write_header(ofile, title='', cwd=cwd, body_class=None, body_title=None, js=None)
        header = ofile.getvalue().split('\n')
        index = FileInfo.relpath(cwd, writer.paths['GameIndex'])
        game_name = self.skoolfile[:-6]
        self.assertEqual(header[13], '<td class="headerLogo"><a class="link" href="{}">{}</a></td>'.format(index, game_name))

    def test_write_header_with_logo_image(self):
        logo_image_fname = 'logo.png'
        ref = '[Game]\nLogoImage={}'.format(logo_image_fname)
        writer = self._get_writer(ref=ref, skool='')
        logo_image = self.write_bin_file(path=join(writer.file_info.odir, logo_image_fname))
        ofile = StringIO()
        cwd = 'subdir/subdir2'
        writer.write_header(ofile, title='', cwd=cwd, body_class=None, body_title=None, js=None)
        header = ofile.getvalue().split('\n')
        index = FileInfo.relpath(cwd, writer.paths['GameIndex'])
        logo = FileInfo.relpath(cwd, logo_image_fname)
        game_name = self.skoolfile[:-6]
        self.assertEqual(header[13], '<td class="headerLogo"><a class="link" href="{}"><img src="{}" alt="{}" /></a></td>'.format(index, logo, game_name))

    def test_write_header_with_logo(self):
        logo = 'ABC #UDG30000 123'
        writer = self._get_writer(ref='[Game]\nLogo={}'.format(logo), skool='')
        ofile = StringIO()
        cwd = ''
        writer.write_header(ofile, title='', cwd=cwd, body_class=None, body_title=None, js=None)
        header = ofile.getvalue().split('\n')
        index = FileInfo.relpath(cwd, writer.paths['GameIndex'])
        logo_value = writer.expand(logo, cwd)
        self.assertEqual(header[13], '<td class="headerLogo"><a class="link" href="{}">{}</a></td>'.format(index, logo_value))

class UdgTest(SkoolKitTestCase):
    def test_flip(self):
        udg = Udg(0, [1, 2, 4, 8, 16, 32, 64, 128], [1, 2, 4, 8, 16, 32, 64, 128])
        udg.flip(0)
        self.assertEqual(udg.data, [1, 2, 4, 8, 16, 32, 64, 128])
        self.assertEqual(udg.mask, [1, 2, 4, 8, 16, 32, 64, 128])

        udg = Udg(0, [1, 2, 4, 8, 16, 32, 64, 128], [1, 2, 4, 8, 16, 32, 64, 128])
        udg.flip(1)
        self.assertEqual(udg.data, [128, 64, 32, 16, 8, 4, 2, 1])
        self.assertEqual(udg.mask, [128, 64, 32, 16, 8, 4, 2, 1])

        udg = Udg(0, [1, 2, 3, 4, 5, 6, 7, 8], [2, 4, 6, 8, 10, 12, 14, 16])
        udg.flip(2)
        self.assertEqual(udg.data, [8, 7, 6, 5, 4, 3, 2, 1])
        self.assertEqual(udg.mask, [16, 14, 12, 10, 8, 6, 4, 2])

        udg = Udg(0, [1, 2, 3, 4, 5, 6, 7, 8], [8, 7, 6, 5, 4, 3, 2, 1])
        udg.flip(3)
        self.assertEqual(udg.data, [16, 224, 96, 160, 32, 192, 64, 128])
        self.assertEqual(udg.mask, [128, 64, 192, 32, 160, 96, 224, 16])

    def test_rotate(self):
        udg = Udg(0, [1, 2, 4, 8, 16, 32, 64, 128], [1, 2, 4, 8, 16, 32, 64, 128])
        udg.rotate(0)
        self.assertEqual(udg.data, [1, 2, 4, 8, 16, 32, 64, 128])
        self.assertEqual(udg.mask, [1, 2, 4, 8, 16, 32, 64, 128])

        udg = Udg(0, [1, 2, 4, 8, 16, 32, 64, 128], [1, 2, 4, 8, 16, 32, 64, 128])
        udg.rotate(1)
        self.assertEqual(udg.data, [128, 64, 32, 16, 8, 4, 2, 1])
        self.assertEqual(udg.mask, [128, 64, 32, 16, 8, 4, 2, 1])

        udg = Udg(0, [1, 2, 3, 4, 5, 6, 7, 8], [8, 7, 6, 5, 4, 3, 2, 1])
        udg.rotate(2)
        self.assertEqual(udg.data, [16, 224, 96, 160, 32, 192, 64, 128])
        self.assertEqual(udg.mask, [128, 64, 192, 32, 160, 96, 224, 16])

        udg = Udg(0, [1, 2, 3, 4, 5, 6, 7, 8], [255, 254, 253, 252, 251, 250, 249, 248])
        udg.rotate(3)
        self.assertEqual(udg.data, [170, 102, 30, 1, 0, 0, 0, 0])
        self.assertEqual(udg.mask, [170, 204, 240, 255, 255, 255, 255, 255])

    def test_copy(self):
        udg = Udg(23, [1] * 8)
        replica = udg.copy()
        self.assertEqual(udg.attr, replica.attr)
        self.assertEqual(udg.data, replica.data)
        self.assertEqual(udg.mask, replica.mask)
        self.assertFalse(udg.data is replica.data)

        udg = Udg(47, [2] * 8, [3] * 8)
        replica = udg.copy()
        self.assertEqual(udg.attr, replica.attr)
        self.assertEqual(udg.data, replica.data)
        self.assertEqual(udg.mask, replica.mask)
        self.assertFalse(udg.data is replica.data)
        self.assertFalse(udg.mask is replica.mask)

    def test_eq(self):
        udg1 = Udg(1, [7] * 8)
        udg2 = Udg(1, [7] * 8)
        udg3 = Udg(2, [7] * 8)
        self.assertTrue(udg1 == udg2)
        self.assertFalse(udg1 == udg3)
        self.assertFalse(udg1 == 1)

    def test_repr(self):
        udg1 = Udg(1, [2, 3, 4, 5, 6, 7, 8, 9])
        self.assertEqual(repr(udg1), 'Udg(1, [2, 3, 4, 5, 6, 7, 8, 9])')

        udg2 = Udg(1, [2] * 8, [3, 4, 5, 6, 7, 8, 9, 10])
        self.assertEqual(repr(udg2), 'Udg(1, [2, 2, 2, 2, 2, 2, 2, 2], [3, 4, 5, 6, 7, 8, 9, 10])')

if __name__ == '__main__':
    unittest.main()
