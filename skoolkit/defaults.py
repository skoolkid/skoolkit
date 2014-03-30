# -*- coding: utf-8 -*-

# Copyright 2014 Richard Dymond (rjdymond@gmail.com)
#
# This file is part of SkoolKit.
#
# SkoolKit is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# SkoolKit is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# SkoolKit. If not, see <http://www.gnu.org/licenses/>.

COLOURS = """
[Colours]
TRANSPARENT=0,254,0
BLACK=0,0,0
BLUE=0,0,197
RED=197,0,0
MAGENTA=197,0,197
GREEN=0,198,0
CYAN=0,198,197
YELLOW=197,198,0
WHITE=205,198,205
BRIGHT_BLUE=0,0,255
BRIGHT_RED=255,0,0
BRIGHT_MAGENTA=255,0,255
BRIGHT_GREEN=0,255,0
BRIGHT_CYAN=0,255,255
BRIGHT_YELLOW=255,255,0
BRIGHT_WHITE=255,255,255
"""

CONFIG = """
[Config]
HtmlWriterClass=skoolkit.skoolhtml.HtmlWriter
SkoolFile=
GameDir=
"""

GAME = """
[Game]
Copyright=
Created=Created using <a class="link" href="http://pyskool.ca/?page_id=177">SkoolKit</a> $VERSION.
Font=
Game=
GameStatusBufferIncludes=
InputRegisterTableHeader=Input
JavaScript=
LinkOperands=CALL,DEFW,DJNZ,JP,JR
Logo=
LogoImage=
OutputRegisterTableHeader=Output
Release=
StyleSheet=skoolkit.css
TitlePrefix=The complete
TitleSuffix=RAM disassembly
"""

IMAGE_WRITER = """
[ImageWriter]
DefaultFormat=png
GIFCompression=1
GIFEnableAnimation=1
GIFTransparency=0
PNGAlpha=255
PNGCompressionLevel=9
PNGEnableAnimation=1
"""

INDEX = """
[Index]
MemoryMaps
Graphics
DataTables
OtherCode
Reference

[Index:MemoryMaps:Memory maps]
MemoryMap
RoutinesMap
DataMap
MessagesMap
UnusedMap

[Index:Graphics:Graphics]
GraphicGlitches

[Index:DataTables:Data tables and buffers]
GameStatusBuffer

[Index:Reference:Reference]
Changelog
Glossary
Facts
Bugs
Pokes
"""

LINKS = """
[Links]
Bugs=Bugs
Changelog=Changelog
DataMap=Data
Facts=Trivia
GameIndex=Index
GameStatusBuffer=Game status buffer
Glossary=Glossary
GraphicGlitches=Graphic glitches
MemoryMap=Everything
MessagesMap=Messages
Pokes=Pokes
RoutinesMap=Routines
UnusedMap=Unused addresses
"""

MEMORY_MAPS = """
[MemoryMap:MemoryMap]
PageByteColumns=1

[MemoryMap:RoutinesMap]
EntryTypes=c

[MemoryMap:DataMap]
EntryTypes=bw
PageByteColumns=1

[MemoryMap:MessagesMap]
EntryTypes=t

[MemoryMap:UnusedMap]
EntryTypes=suz
PageByteColumns=1
"""

PAGE_HEADERS = """
[PageHeaders]
Asm-b=Data
Asm-c=Routines
Asm-g=Game status buffer
Asm-s=Unused
Asm-t=Data
Asm-u=Unused
Asm-w=Data
Bugs=Bugs
Changelog=Changelog
DataMap=Data
Facts=Trivia
GameIndex=Index
GameStatusBuffer=Game status buffer
Glossary=Glossary
GraphicGlitches=Graphic glitches
MemoryMap=Memory map
MessagesMap=Messages
Pokes=Pokes
RoutinesMap=Routines
UnusedMap=Unused addresses
"""

PATHS = """
[Paths]
CodePath=asm
FontPath=.
FontImagePath=images/font
JavaScriptPath=.
ScreenshotImagePath=images/scr
StyleSheetPath=.
UDGImagePath=images/udgs
Bugs=reference/bugs.html
Changelog=reference/changelog.html
DataMap=maps/data.html
Facts=reference/facts.html
GameIndex=index.html
GameStatusBuffer=buffers/gbuffer.html
Glossary=reference/glossary.html
GraphicGlitches=graphics/glitches.html
MemoryMap=maps/all.html
MessagesMap=maps/messages.html
Pokes=reference/pokes.html
RoutinesMap=maps/routines.html
UnusedMap=maps/unused.html
"""

TEMPLATES = """
[Template:Asm]
<?xml version="1.0" encoding="utf-8" ?>
<!DOCTYPE html
    PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<title>{Game[Game]}: {SkoolKit[title]} {entry[address]}</title>
<meta http-equiv="content-type" content="text/html; charset=utf-8" />
{m_stylesheet}
{m_javascript}
</head>
<body class="{SkoolKit[page_id]}">
<table class="header">
<tr>
<td class="headerLogo"><a class="link" href="{SkoolKit[home]}">{Game[Logo]}</a></td>
<td class="headerText">{SkoolKit[page_header]}</td>
</tr>
</table>
<table class="asm-navigation">
<tr>
<td class="prev"><span class="prev-{prev_entry[exists]}">Prev: <a class="link" href="{prev_entry[url]}">{prev_entry[address]}</a></span></td>
<td class="up">Up: <a class="link" href="{entry[map_url]}">Map</a></td>
<td class="next"><span class="next-{next_entry[exists]}">Next: <a class="link" href="{next_entry[url]}">{next_entry[address]}</a></span></td>
</tr>
</table>
<div class="description">{entry[address]}: {entry[title]}</div>
<table class="disassembly">
<tr>
<td class="routineComment" colspan="4">
<div class="details">
{entry[description]}
</div>
<table class="input-{entry[input]}">
<tr class="asm-input-header">
<th colspan="2">{Game[InputRegisterTableHeader]}</th>
</tr>
{m_asm_register_input}
</table>
<table class="output-{entry[output]}">
<tr class="asm-output-header">
<th colspan="2">{Game[OutputRegisterTableHeader]}</th>
</tr>
{m_asm_register_output}
</table>
</td>
</tr>
{disassembly}
</table>
<table class="asm-navigation">
<tr>
<td class="prev"><span class="prev-{prev_entry[exists]}">Prev: <a class="link" href="{prev_entry[url]}">{prev_entry[address]}</a></span></td>
<td class="up">Up: <a class="link" href="{entry[map_url]}">Map</a></td>
<td class="next"><span class="next-{next_entry[exists]}">Next: <a class="link" href="{next_entry[url]}">{next_entry[address]}</a></span></td>
</tr>
</table>
<div class="footer">
<div class="release">{Game[Release]}</div>
<div class="copyright">{Game[Copyright]}</div>
<div class="created">{Game[Created]}</div>
</div>
</body>
</html>

[Template:GameIndex]
<?xml version="1.0" encoding="utf-8" ?>
<!DOCTYPE html
    PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<title>{Game[Game]}: {SkoolKit[title]}</title>
<meta http-equiv="content-type" content="text/html; charset=utf-8" />
{m_stylesheet}
{m_javascript}
</head>
<body class="{SkoolKit[page_id]}">
<table class="header">
<tr>
<td class="headerText">{Game[TitlePrefix]}</td>
<td class="headerLogo">{Game[Logo]}</td>
<td class="headerText">{Game[TitleSuffix]}</td>
</tr>
</table>
{m_index_section}
<div class="footer">
<div class="release">{Game[Release]}</div>
<div class="copyright">{Game[Copyright]}</div>
<div class="created">{Game[Created]}</div>
</div>
</body>
</html>

[Template:MemoryMap]
<?xml version="1.0" encoding="utf-8" ?>
<!DOCTYPE html
    PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<title>{Game[Game]}: {SkoolKit[title]}</title>
<meta http-equiv="content-type" content="text/html; charset=utf-8" />
{m_stylesheet}
{m_javascript}
</head>
<body class="{SkoolKit[page_id]}">
<table class="header">
<tr>
<td class="headerLogo"><a class="link" href="{SkoolKit[home]}">{Game[Logo]}</a></td>
<td class="headerText">{SkoolKit[page_header]}</td>
</tr>
</table>
<div class="mapIntro">{MemoryMap[Intro]}</div>
<table class="map">
<tr>
<th class="map-page-{MemoryMap[PageByteColumns]}">Page</th>
<th class="map-byte-{MemoryMap[PageByteColumns]}">Byte</th>
<th>Address</th>
<th class="map-length-{MemoryMap[LengthColumn]}">Length</th>
<th>Description</th>
</tr>
{m_map_entry}
</table>
<div class="footer">
<div class="release">{Game[Release]}</div>
<div class="copyright">{Game[Copyright]}</div>
<div class="created">{Game[Created]}</div>
</div>
</body>
</html>

[Template:Page]
<?xml version="1.0" encoding="utf-8" ?>
<!DOCTYPE html
    PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<title>{Game[Game]}: {SkoolKit[title]}</title>
<meta http-equiv="content-type" content="text/html; charset=utf-8" />
{m_stylesheet}
{m_javascript}
</head>
<body class="{SkoolKit[page_id]}">
<table class="header">
<tr>
<td class="headerLogo"><a class="link" href="{SkoolKit[home]}">{Game[Logo]}</a></td>
<td class="headerText">{SkoolKit[page_header]}</td>
</tr>
</table>
{PageContent}
<div class="footer">
<div class="release">{Game[Release]}</div>
<div class="copyright">{Game[Copyright]}</div>
<div class="created">{Game[Created]}</div>
</div>
</body>
</html>

[Template:Reference]
<?xml version="1.0" encoding="utf-8" ?>
<!DOCTYPE html
    PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<title>{Game[Game]}: {SkoolKit[title]}</title>
<meta http-equiv="content-type" content="text/html; charset=utf-8" />
{m_stylesheet}
{m_javascript}
</head>
<body class="{SkoolKit[page_id]}">
<table class="header">
<tr>
<td class="headerLogo"><a class="link" href="{SkoolKit[home]}">{Game[Logo]}</a></td>
<td class="headerText">{SkoolKit[page_header]}</td>
</tr>
</table>
<ul class="linkList">
{m_contents_list_item}
</ul>
{items}
<div class="footer">
<div class="release">{Game[Release]}</div>
<div class="copyright">{Game[Copyright]}</div>
<div class="created">{Game[Created]}</div>
</div>
</body>
</html>

[Template:anchor]
<a name="{anchor}"></a>

[Template:asm_comment]
<tr>
<td class="routineComment" colspan="4">
{t_anchor}
<div class="comments">
{m_paragraph}
</div>
</td>
</tr>

[Template:asm_instruction]
<tr>
<td class="asm-label-{entry[labels]}">{instruction[label]}</td>
<td class="address">{t_anchor}{instruction[address]}</td>
<td class="instruction">{instruction[operation]}</td>
<td class="comment-{instruction[annotated]}" rowspan="{instruction[comment_rowspan]}">{instruction[comment]}</td>
</tr>

[Template:asm_register_input]
<tr>
<td class="register">{register[name]}</td>
<td class="registerContents">{register[description]}</td>
</tr>

[Template:asm_register_output]
<tr>
<td class="register">{register[name]}</td>
<td class="registerContents">{register[description]}</td>
</tr>

[Template:box]
<div>{t_anchor}</div>
<div class="box box{box_num}">
<div class="boxTitle">{title}</div>
{contents}
</div>

[Template:changelog_entry]
<div>{t_anchor}</div>
<div class="changelog changelog{changelog_num}">
<div class="changelogTitle">{release[title]}</div>
<div class="changelogDesc">{release[description]}</div>
{t_changelog_item_list}
</div>

[Template:changelog_item]
<li>{item}</li>

[Template:changelog_item_list]
<ul class="changelog{indent}">
{m_changelog_item}
</ul>

[Template:contents_list_item]
<li><a class="link" href="{item[url]}">{item[title]}</a></li>

[Template:img]
<img alt="{alt}" src="{src}" />

[Template:index_section]
<div class="headerText">{header}</div>
<ul class="indexList">
{m_index_section_item}
</ul>

[Template:index_section_item]
<li><a class="link" href="{href}">{link_text}</a>{other_text}</li>

[Template:javascript]
<script type="text/javascript" src="{src}"></script>

[Template:link]
<a class="link" href="{href}">{link_text}</a>

[Template:map_entry]
<tr>
<td class="map-page-{MemoryMap[PageByteColumns]}">{entry[page]}</td>
<td class="map-byte-{MemoryMap[PageByteColumns]}">{entry[byte]}</td>
<td class="map-{entry[type]}">{t_anchor}<a class="link" href="{entry[url]}">{entry[address]}</a></td>
<td class="map-length-{MemoryMap[LengthColumn]}">{entry[size]}</td>
<td class="map-{entry[type]}-desc">
<div class="map-entry-title">{entry[title]}</div>
<div class="map-entry-desc-{MemoryMap[EntryDescriptions]}">
{entry[description]}
</div>
</td>
</tr>

[Template:paragraph]
<div class="paragraph">
{paragraph}
</div>

[Template:reg]
<span class="register">{reg}</span>

[Template:stylesheet]
<link rel="stylesheet" type="text/css" href="{href}" />
"""

TITLES = """
[Titles]
Asm-b=Data at
Asm-c=Routine at
Asm-g=Game status buffer entry at
Asm-s=Unused RAM at
Asm-t=Data at
Asm-u=Unused RAM at
Asm-w=Data at
Bugs=Bugs
Changelog=Changelog
DataMap=Data
Facts=Trivia
GameIndex=Index
GameStatusBuffer=Game status buffer
Glossary=Glossary
GraphicGlitches=Graphic glitches
MemoryMap=Memory map
MessagesMap=Messages
Pokes=Pokes
RoutinesMap=Routines
UnusedMap=Unused addresses
"""

REF_FILE = """
{COLOURS}
{CONFIG}
{GAME}
{IMAGE_WRITER}
{INDEX}
{LINKS}
{MEMORY_MAPS}
{PAGE_HEADERS}
{PATHS}
{TEMPLATES}
{TITLES}
""".format(**locals())
