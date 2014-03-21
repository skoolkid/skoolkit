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
[Template:prologue]
<?xml version="1.0" encoding="utf-8" ?>
<!DOCTYPE html
    PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">

[Template:html]
<html xmlns="http://www.w3.org/1999/xhtml">

[Template:head]
<meta http-equiv="content-type" content="text/html; charset=utf-8" />
<title>{Game[Game]}: {title}</title>
{t_stylesheets}
{t_javascripts}

[Template:stylesheet]
<link rel="stylesheet" type="text/css" href="{href}" />

[Template:javascript]
<script type="text/javascript" src="{src}"></script>

[Template:footer]
<div class="footer">
<div class="release">{Info[Release]}</div>
<div class="copyright">{Info[Copyright]}</div>
<div class="created">{Info[Created]}</div>
</div>

[Template:index_section]
<div class="headerText">{header}</div>
{t_link_list}

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
{t_index_sections}
{t_footer}
</body>
</html>

[Template:asm_entry]
{t_prologue}
{t_html}
<head>
{t_head}
</head>
<body class="disassembly">
{t_header}
{t_prev_next}
<div class="description">{entry_title}</div>
{t_disassembly}
{t_prev_next}
{t_footer}
</body>
</html>

[Template:header]
<table class="header">
<tr>
<td class="headerLogo"><a class="link" href="{href}">{Game[Logo]}</a></td>
<td class="headerText">{header}</td>
</tr>
</table>

[Template:routine_title]
Routine at {address}{label_suffix}

[Template:routine_header]
Routines

[Template:gsb_title]
Game status buffer entry at {address}{label_suffix}

[Template:gsb_header]
Game status buffer

[Template:data_title]
Data at {address}{label_suffix}

[Template:data_header]
Data

[Template:unused_title]
Unused RAM at {address}{label_suffix}

[Template:unused_header]
Unused

[Template:prev_next]
<table class="prevNext">
<tr>
<td class="prev">{t_prev}</td>
<td class="up">{t_up}</td>
<td class="next">{t_next}</td>
</tr>
</table>

[Template:prev]
Prev: <a class="link" href="{href}">{text}</a>

[Template:up]
Up: <a class="link" href="{href}">Map</a>

[Template:next]
Next: <a class="link" href="{href}">{text}</a>

[Template:disassembly]
<table class="{table_class}">
<tr>
<td class="routineComment" colspan="{colspan}">
<div class="details">
{entry_details}
</div>
{t_input}
{t_output}
</td>
</tr>
{t_instructions}
</table>

[Template:anchor]
<a name="{anchor}"></a>

[Template:entry_comment]
<tr>
<td class="routineComment" colspan="{colspan}">
{t_anchor}
<div class="comments">
{t_paragraphs}
</div>
</td>
</tr>

[Template:input]
<table class="input">
{t_registers_header}
{t_registers}
</table>

[Template:output]
<table class="output">
{t_registers_header}
{t_registers}
</table>

[Template:registers_header]
<tr>
<th colspan="2">{header}</th>
</tr>

[Template:register]
<tr>
<td class="register">{register.name}</td>
<td class="registerContents">{register.description}</td>
</tr>

[Template:instruction]
<tr>
{t_asm_label}
<td class="{class}">{t_anchor}{address}</td>
<td class="instruction">{instruction}</td>
{t_instruction_comment}
</tr>

[Template:instruction_comment]
<td class="{class}"{rowspan}>{comment}</td>

[Template:asm_label]
<td class="asmLabel">{label}</td>

[Template:paragraph]
<div class="paragraph">
{paragraph}
</div>

[Template:link_list]
<ul class="{list_class}">
{t_link_list_items}
</ul>

[Template:link_list_item]
<li><a class="link" href="{href}">{link_text}</a>{other_text}</li>

[Template:link]
<a class="link" href="{href}">{link_text}</a>

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
{t_map_entries}
</table>
{t_footer}
</body>
</html>

[Template:map_intro]
<div class="mapIntro">{intro}</div>

[Template:map_entry]
<tr>
{t_map_page_byte}
<td class="{class}">{t_anchor}<a class="link" href="{href}">{entry.addr_str}</a></td>
<td class="{desc_class}">{entry.title}</td>
</tr>

[Template:map_page_byte_header]
<th>Page</th>
<th>Byte</th>

[Template:map_page_byte]
<td class="mapPage">{page}</td>
<td class="mapByte">{byte}</td>

[Template:map_unused_desc]
Unused ({entry.size} byte{suffix})

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
{t_gsb_entries}
</table>
{t_footer}
</body>
</html>

[Template:gsb_entry]
<tr>
<td class="gbufAddress"><a name="{entry[location]}" class="link" href="{entry[url]}">{entry[address]}</a></td>
<td class="gbufLength">{entry[size]}</td>
<td class="gbufDesc">
<div class="gbufDesc">{entry[title]}</div>
<div class="gbufDetails">
{entry[description]}
</div>
</td>
</tr>

[Template:Changelog]
{t_prologue}
{t_html}
<head>
{t_head}
</head>
<body class="changelog">
{t_header}
{t_contents_list}
{t_changelog_entries}
{t_footer}
</body>
</html>

[Template:contents_list]
<ul class="linkList">
{t_contents_list_items}
</ul>

[Template:contents_list_item]
<li><a class="link" href="{item[url]}">{item[title]}</a></li>

[Template:changelog_entry]
<div>{t_anchor}</div>
<div class="changelog changelog{changelog_num}">
<div class="changelogTitle">{entry[title]}</div>
<div class="changelogDesc">{entry[description]}</div>
{t_changelog_item_list}
</div>

[Template:changelog_item_list]
<ul class="changelog{indent}">
{t_changelog_items}
</ul>

[Template:changelog_item]
<li>{item}</li>

[Template:Pokes]
{t_prologue}
{t_html}
<head>
{t_head}
</head>
<body class="pokes">
{t_header}
{t_contents_list}
{t_boxes}
{t_footer}
</body>
</html>

[Template:Bugs]
{t_prologue}
{t_html}
<head>
{t_head}
</head>
<body class="bugs">
{t_header}
{t_contents_list}
{t_boxes}
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
{t_boxes}
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
{t_boxes}
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
{t_boxes}
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

[Template:custom_page]
{t_prologue}
{t_html}
<head>
{t_head}
</head>
<body{class}>
{t_header}
{content}
{t_footer}
</body>
</html>

[Template:box]
<div>{t_anchor}</div>
<div class="box box{box_num}">
<div class="boxTitle">{title}</div>
{contents}
</div>

[Template:img]
<img alt="{alt}" src="{src}" />

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
