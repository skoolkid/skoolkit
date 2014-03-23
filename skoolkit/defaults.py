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
Font=
Game=
GameStatusBufferIncludes=
InputRegisterTableHeader=
JavaScript=
LinkOperands=CALL,DEFW,DJNZ,JP,JR
Logo=
LogoImage=
OutputRegisterTableHeader=
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
Graphics
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

INFO = """
[Info]
Copyright=
Created=Created using <a class="link" href="http://pyskool.ca/?page_id=177">SkoolKit</a> $VERSION.
Release=
"""

LINKS = """
[Links]
Bugs=
Changelog=
DataMap=
Facts=
GameStatusBuffer=
Glossary=
GraphicGlitches=
Graphics=
MemoryMap=Everything
MessagesMap=
Pokes=
RoutinesMap=
UnusedMap=
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
Graphics=graphics/graphics.html
MemoryMap=maps/all.html
MessagesMap=maps/messages.html
Pokes=reference/pokes.html
RoutinesMap=maps/routines.html
UnusedMap=maps/unused.html
"""

TEMPLATES = """
[Template:Bugs]
{t_prologue}
{t_html}
<head>
{t_head}
</head>
<body class="bugs">
{t_header}
{t_contents_list}
{m_box}
{t_footer}
</body>
</html>

[Template:Changelog]
{t_prologue}
{t_html}
<head>
{t_head}
</head>
<body class="changelog">
{t_header}
{t_contents_list}
{m_changelog_entry}
{t_footer}
</body>
</html>

[Template:Code]
{t_prologue}
{t_html}
<head>
{t_head}
</head>
<body class="disassembly">
{t_header}
{t_asm_navigation}
<div class="description">{entry[label_prefix]}{entry[address]}: {entry[title]}</div>
{asm}
{t_asm_navigation}
{t_footer}
</body>
</html>

[Template:Facts]
{t_prologue}
{t_html}
<head>
{t_head}
</head>
<body class="facts">
{t_header}
{t_contents_list}
{m_box}
{t_footer}
</body>
</html>

[Template:GameIndex]
{t_prologue}
{t_html}
<head>
{t_head}
</head>
<body class="main">
<table class="header">
<tr>
<td class="headerText">{Game[TitlePrefix]}</td>
<td class="headerLogo">{Game[Logo]}</td>
<td class="headerText">{Game[TitleSuffix]}</td>
</tr>
</table>
{m_index_section}
{t_footer}
</body>
</html>

[Template:GameStatusBuffer]
{t_prologue}
{t_html}
<head>
{t_head}
</head>
<body class="gbuffer">
{t_header}
<table class="gbuffer">
<tr>
<th>Address</th>
<th>Length</th>
<th>Purpose</th>
</tr>
{m_gsb_entry}
</table>
{t_footer}
</body>
</html>

[Template:Glossary]
{t_prologue}
{t_html}
<head>
{t_head}
</head>
<body class="glossary">
{t_header}
{t_contents_list}
{m_box}
{t_footer}
</body>
</html>

[Template:GraphicGlitches]
{t_prologue}
{t_html}
<head>
{t_head}
</head>
<body class="graphics">
{t_header}
{t_contents_list}
{m_box}
{t_footer}
</body>
</html>

[Template:Graphics]
{t_prologue}
{t_html}
<head>
{t_head}
</head>
<body class="graphics">
{t_header}
{Graphics}
{t_footer}
</body>
</html>

[Template:MemoryMap]
{t_prologue}
{t_html}
<head>
{t_head}
</head>
<body class="map">
{t_header}
{t_map_intro}
<table class="map">
<tr>
{t_map_page_byte_header}
<th>Address</th>
<th>Description</th>
</tr>
{m_map_entry}
</table>
{t_footer}
</body>
</html>

[Template:Page]
{t_prologue}
{t_html}
<head>
{t_head}
</head>
<body{class}>
{t_header}
{PageContent}
{t_footer}
</body>
</html>

[Template:Pokes]
{t_prologue}
{t_html}
<head>
{t_head}
</head>
<body class="pokes">
{t_header}
{t_contents_list}
{m_box}
{t_footer}
</body>
</html>

[Template:anchor]
<a name="{anchor}"></a>

[Template:asm_code]
<table class="disassembly">
<tr>
<td class="routineComment" colspan="{colspan}">
<div class="details">
{entry[description]}
</div>
{t_asm_registers_input}
{t_asm_registers_output}
</td>
</tr>
{disassembly}
</table>

[Template:asm_comment]
<tr>
<td class="routineComment" colspan="{colspan}">
{t_anchor}
<div class="comments">
{m_paragraph}
</div>
</td>
</tr>

[Template:asm_data]
<table class="dataDisassembly">
<tr>
<td class="routineComment" colspan="{colspan}">
<div class="details">
{entry[description]}
</div>
</td>
</tr>
{disassembly}
</table>

[Template:asm_header_data]
Data

[Template:asm_header_gsb]
Game status buffer

[Template:asm_header_routine]
Routines

[Template:asm_header_unused]
Unused

[Template:asm_instruction]
<tr>
{o_asm_instruction_label}
<td class="address">{t_anchor}{instruction[address]}</td>
<td class="instruction">{instruction[operation]}</td>
{comment}
</tr>

[Template:asm_instruction_comment_code]
<td class="comment"{rowspan}>{instruction[comment]}</td>

[Template:asm_instruction_comment_code_transparent]
<td class="transparentComment"{rowspan}></td>

[Template:asm_instruction_comment_data]
<td class="dataComment"{rowspan}>{instruction[comment]}</td>

[Template:asm_instruction_comment_data_transparent]
<td class="transparentDataComment"{rowspan}></td>

[Template:asm_instruction_label]
<td class="asmLabel">{instruction[label]}</td>

[Template:asm_instruction_labelled]
<tr>
{o_asm_instruction_label}
<td class="label">{t_anchor}{instruction[address]}</td>
<td class="instruction">{instruction[operation]}</td>
{comment}
</tr>

[Template:asm_navigation]
<table class="prevNext">
<tr>
<td class="prev">{t_asm_navigation_prev}</td>
<td class="up">{t_asm_navigation_up}</td>
<td class="next">{t_asm_navigation_next}</td>
</tr>
</table>

[Template:asm_navigation_next]
Next: <a class="link" href="{entry[url]}">{entry[address]}</a>

[Template:asm_navigation_prev]
Prev: <a class="link" href="{entry[url]}">{entry[address]}</a>

[Template:asm_navigation_up]
Up: <a class="link" href="{entry[map_url]}">Map</a>

[Template:asm_register]
<tr>
<td class="register">{register[name]}</td>
<td class="registerContents">{register[description]}</td>
</tr>

[Template:asm_registers_header_input]
<tr>
<th colspan="2">{Game[InputRegisterTableHeader]}</th>
</tr>

[Template:asm_registers_header_output]
<tr>
<th colspan="2">{Game[OutputRegisterTableHeader]}</th>
</tr>

[Template:asm_registers_input]
<table class="input">
{o_asm_registers_header_input}
{m_asm_register}
</table>

[Template:asm_registers_output]
<table class="output">
{o_asm_registers_header_output}
{m_asm_register}
</table>

[Template:asm_title_data]
Data at {entry[address]}{label_suffix}

[Template:asm_title_gsb]
Game status buffer entry at {entry[address]}{label_suffix}

[Template:asm_title_routine]
Routine at {entry[address]}{label_suffix}

[Template:asm_title_unused]
Unused RAM at {entry[address]}{label_suffix}

[Template:box]
<div>{t_anchor}</div>
<div class="box box{box_num}">
<div class="boxTitle">{title}</div>
{contents}
</div>

[Template:changelog_entry]
<div>{t_anchor}</div>
<div class="changelog changelog{changelog_num}">
<div class="changelogTitle">{entry[title]}</div>
<div class="changelogDesc">{entry[description]}</div>
{t_changelog_item_list}
</div>

[Template:changelog_item]
<li>{item}</li>

[Template:changelog_item_list]
<ul class="changelog{indent}">
{m_changelog_item}
</ul>

[Template:contents_list]
<ul class="linkList">
{m_contents_list_item}
</ul>

[Template:contents_list_item]
<li><a class="link" href="{item[url]}">{item[title]}</a></li>

[Template:entry_size_unit]
byte

[Template:entry_size_unit_plural]
bytes

[Template:footer]
<div class="footer">
<div class="release">{Info[Release]}</div>
<div class="copyright">{Info[Copyright]}</div>
<div class="created">{Info[Created]}</div>
</div>

[Template:gsb_entry]
<tr>
<td class="gbufAddress">{t_anchor}<a class="link" href="{entry[url]}">{entry[address]}</a></td>
<td class="gbufLength">{entry[size]}</td>
<td class="gbufDesc">
<div class="gbufDesc">{entry[title]}</div>
<div class="gbufDetails">
{entry[description]}
</div>
</td>
</tr>

[Template:head]
<meta http-equiv="content-type" content="text/html; charset=utf-8" />
<title>{Game[Game]}: {title}</title>
{m_head_stylesheet}
{m_head_javascript}

[Template:head_javascript]
<script type="text/javascript" src="{src}"></script>

[Template:head_stylesheet]
<link rel="stylesheet" type="text/css" href="{href}" />

[Template:header]
<table class="header">
<tr>
<td class="headerLogo"><a class="link" href="{href}">{Game[Logo]}</a></td>
<td class="headerText">{header}</td>
</tr>
</table>

[Template:html]
<html xmlns="http://www.w3.org/1999/xhtml">

[Template:img]
<img alt="{alt}" src="{src}" />

[Template:index_section]
<div class="headerText">{header}</div>
<ul class="indexList">
{m_index_section_item}
</ul>

[Template:index_section_item]
<li><a class="link" href="{href}">{link_text}</a>{other_text}</li>

[Template:link]
<a class="link" href="{href}">{link_text}</a>

[Template:map_entry]
<tr>
{t_map_page_byte}
{map_entry}
</tr>

[Template:map_entry_data]
<td class="data">{t_anchor}<a class="link" href="{entry[url]}">{entry[address]}</a></td>
<td class="dataDesc">{entry[title]}</td>

[Template:map_entry_gsb]
<td class="gbuffer">{t_anchor}<a class="link" href="{entry[url]}">{entry[address]}</a></td>
<td class="gbufferDesc">{entry[title]}</td>

[Template:map_entry_message]
<td class="message">{t_anchor}<a class="link" href="{entry[url]}">{entry[address]}</a></td>
<td class="messageDesc">{entry[title]}</td>

[Template:map_entry_routine]
<td class="routine">{t_anchor}<a class="link" href="{entry[url]}">{entry[address]}</a></td>
<td class="routineDesc">{entry[title]}</td>

[Template:map_entry_unused]
<td class="unused">{t_anchor}<a class="link" href="{entry[url]}">{entry[address]}</a></td>
<td class="unusedDesc">Unused ({entry[size]} {entry[unit]})</td>

[Template:map_intro]
<div class="mapIntro">{intro}</div>

[Template:map_page_byte]
<td class="mapPage">{entry[page]}</td>
<td class="mapByte">{entry[byte]}</td>

[Template:map_page_byte_header]
<th>Page</th>
<th>Byte</th>

[Template:paragraph]
<div class="paragraph">
{paragraph}
</div>

[Template:prologue]
<?xml version="1.0" encoding="utf-8" ?>
<!DOCTYPE html
    PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">

[Template:reg]
<span class="register">{reg}</span>
"""

TITLES = """
[Titles]
Bugs=Bugs
Changelog=Changelog
DataMap=Data
Facts=Trivia
GameIndex=Index
GameStatusBuffer=Game status buffer
Glossary=Glossary
GraphicGlitches=Graphic glitches
Graphics=Graphics
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
{INFO}
{LINKS}
{MEMORY_MAPS}
{PATHS}
{TEMPLATES}
{TITLES}
""".format(**locals())
