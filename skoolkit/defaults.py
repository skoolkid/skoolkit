# -*- coding: utf-8 -*-

# Copyright 2014, 2015 Richard Dymond (rjdymond@gmail.com)
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

from collections import OrderedDict
import re

SECTIONS = OrderedDict()

SECTIONS['Colours'] = """
; TRANSPARENT=0,254,0
; BLACK=0,0,0
; BLUE=0,0,197
; RED=197,0,0
; MAGENTA=197,0,197
; GREEN=0,198,0
; CYAN=0,198,197
; YELLOW=197,198,0
; WHITE=205,198,205
; BRIGHT_BLUE=0,0,255
; BRIGHT_RED=255,0,0
; BRIGHT_MAGENTA=255,0,255
; BRIGHT_GREEN=0,255,0
; BRIGHT_CYAN=0,255,255
; BRIGHT_YELLOW=255,255,0
; BRIGHT_WHITE=255,255,255
"""

SECTIONS['Config'] = """
; GameDir=
HtmlWriterClass=skoolkit.skoolhtml.HtmlWriter
; RefFiles=
; SkoolFile=
"""

SECTIONS['Game'] = """
AddressAnchor={address}
Copyright=
Created=Created using <a href="http://skoolkit.ca/">SkoolKit</a> $VERSION.
; Font=
; Game=
; GameStatusBufferIncludes=
InputRegisterTableHeader=Input
; JavaScript=
LinkInternalOperands=0
LinkOperands=CALL,DEFW,DJNZ,JP,JR
; Logo=
; LogoImage=
OutputRegisterTableHeader=Output
Release=
StyleSheet=skoolkit.css
TitlePrefix=The complete
TitleSuffix=RAM disassembly
"""

SECTIONS['ImageWriter'] = """
; DefaultFormat=png
; GIFEnableAnimation=1
; GIFTransparency=0
; PNGAlpha=255
; PNGCompressionLevel=9
; PNGEnableAnimation=1
"""

SECTIONS['Index'] = """
MemoryMaps
Graphics
DataTables
OtherCode
Reference
"""

SECTIONS['Index:MemoryMaps:Memory maps'] = """
MemoryMap
RoutinesMap
DataMap
MessagesMap
UnusedMap
"""

SECTIONS['Index:Graphics:Graphics'] = """
GraphicGlitches
"""

SECTIONS['Index:DataTables:Data tables and buffers'] = """
GameStatusBuffer
"""

SECTIONS['Index:Reference:Reference'] = """
Changelog
Glossary
Facts
Bugs
Pokes
"""

SECTIONS['Links'] = """
; Bugs=
; Changelog=
; DataMap=
; Facts=
; GameStatusBuffer=
; Glossary=
; GraphicGlitches=
MemoryMap=Everything
; MessagesMap=
; Pokes=
; RoutinesMap=
; UnusedMap=
"""

SECTIONS['MemoryMap:MemoryMap'] = """
; EntryDescriptions=0
; EntryTypes=bcgstuw
; Intro=
; LengthColumn=0
PageByteColumns=1
; Write=1
"""

SECTIONS['MemoryMap:RoutinesMap'] = """
; EntryDescriptions=0
EntryTypes=c
; Intro=
; LengthColumn=0
; PageByteColumns=0
; Write=1
"""

SECTIONS['MemoryMap:DataMap'] = """
; EntryDescriptions=0
EntryTypes=bw
; Intro=
; LengthColumn=0
PageByteColumns=1
; Write=1
"""

SECTIONS['MemoryMap:MessagesMap'] = """
; EntryDescriptions=0
EntryTypes=t
; Intro=
; LengthColumn=0
; PageByteColumns=0
; Write=1
"""

SECTIONS['MemoryMap:UnusedMap'] = """
; EntryDescriptions=0
EntryTypes=su
; Intro=
LengthColumn=1
PageByteColumns=1
; Write=1
"""

SECTIONS['MemoryMap:GameStatusBuffer'] = """
EntryDescriptions=1
EntryTypes=gG
; Intro=
LengthColumn=1
; PageByteColumns=0
; Write=1
"""

SECTIONS['PageHeaders'] = """
Asm-b=Data
Asm-c=Routines
Asm-g=Game status buffer
Asm-s=Unused
Asm-t=Data
Asm-u=Unused
Asm-w=Data
; Bugs=
; Changelog=
; DataMap=
; Facts=
; GameStatusBuffer=
; Glossary=
; GraphicGlitches=
; MemoryMap=
; MessagesMap=
; Pokes=
; RoutinesMap=
; UnusedMap=
"""

SECTIONS['Paths'] = """
CodePath=asm
FontPath=.
FontImagePath=images/font
JavaScriptPath=.
ScreenshotImagePath=images/scr
StyleSheetPath=.
UDGImagePath=images/udgs
Bugs=reference/bugs.html
Changelog=reference/changelog.html
CodeFiles={address}.html
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

SECTIONS['Template:Asm'] = """
<!DOCTYPE html>
<html>
<head>
<title>{Game[Game]}: {SkoolKit[title]} {entry[address]}</title>
<meta charset="utf-8" />
{m_stylesheet}
{m_javascript}
</head>
<body class="{SkoolKit[page_id]}">
<table class="header">
<tr>
<td class="logo"><a href="{SkoolKit[index_href]}">{Game[Logo]}</a></td>
<td class="page-header">{SkoolKit[page_header]}</td>
</tr>
</table>
<table class="asm-navigation">
<tr>
<td class="prev"><span class="prev-{prev_entry[exists]}">Prev: <a href="{prev_entry[href]}">{prev_entry[address]}</a></span></td>
<td class="up">Up: <a href="{entry[map_href]}">Map</a></td>
<td class="next"><span class="next-{next_entry[exists]}">Next: <a href="{next_entry[href]}">{next_entry[address]}</a></span></td>
</tr>
</table>
<div class="description">{entry[address]}: {entry[title]}</div>
<table class="disassembly">
<tr>
<td class="routine-comment" colspan="4">
<div class="details">
{entry[description]}
</div>
<table class="input-{entry[input]}">
<tr class="asm-input-header">
<th colspan="2">{Game[InputRegisterTableHeader]}</th>
</tr>
{registers_input}
</table>
<table class="output-{entry[output]}">
<tr class="asm-output-header">
<th colspan="2">{Game[OutputRegisterTableHeader]}</th>
</tr>
{registers_output}
</table>
</td>
</tr>
{disassembly}
</table>
<table class="asm-navigation">
<tr>
<td class="prev"><span class="prev-{prev_entry[exists]}">Prev: <a href="{prev_entry[href]}">{prev_entry[address]}</a></span></td>
<td class="up">Up: <a href="{entry[map_href]}">Map</a></td>
<td class="next"><span class="next-{next_entry[exists]}">Next: <a href="{next_entry[href]}">{next_entry[address]}</a></span></td>
</tr>
</table>
{t_footer}
</body>
</html>
"""

SECTIONS['Template:GameIndex'] = """
<!DOCTYPE html>
<html>
<head>
<title>{Game[Game]}: {SkoolKit[title]}</title>
<meta charset="utf-8" />
{m_stylesheet}
{m_javascript}
</head>
<body class="{SkoolKit[page_id]}">
<table class="header">
<tr>
<td class="page-header">{Game[TitlePrefix]}</td>
<td class="logo">{Game[Logo]}</td>
<td class="page-header">{Game[TitleSuffix]}</td>
</tr>
</table>
{m_index_section}
{t_footer}
</body>
</html>
"""

SECTIONS['Template:MemoryMap'] = """
<!DOCTYPE html>
<html>
<head>
<title>{Game[Game]}: {SkoolKit[title]}</title>
<meta charset="utf-8" />
{m_stylesheet}
{m_javascript}
</head>
<body class="{SkoolKit[page_id]}">
<table class="header">
<tr>
<td class="logo"><a href="{SkoolKit[index_href]}">{Game[Logo]}</a></td>
<td class="page-header">{SkoolKit[page_header]}</td>
</tr>
</table>
<div class="map-intro">{MemoryMap[Intro]}</div>
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
{t_footer}
</body>
</html>
"""

SECTIONS['Template:Page'] = """
<!DOCTYPE html>
<html>
<head>
<title>{Game[Game]}: {SkoolKit[title]}</title>
<meta charset="utf-8" />
{m_stylesheet}
{m_javascript}
</head>
<body class="{SkoolKit[page_id]}">
<table class="header">
<tr>
<td class="logo"><a href="{SkoolKit[index_href]}">{Game[Logo]}</a></td>
<td class="page-header">{SkoolKit[page_header]}</td>
</tr>
</table>
{content}
{t_footer}
</body>
</html>
"""

SECTIONS['Template:Reference'] = """
<!DOCTYPE html>
<html>
<head>
<title>{Game[Game]}: {SkoolKit[title]}</title>
<meta charset="utf-8" />
{m_stylesheet}
{m_javascript}
</head>
<body class="{SkoolKit[page_id]}">
<table class="header">
<tr>
<td class="logo"><a href="{SkoolKit[index_href]}">{Game[Logo]}</a></td>
<td class="page-header">{SkoolKit[page_header]}</td>
</tr>
</table>
<ul class="contents">
{m_contents_list_item}
</ul>
{entries}
{t_footer}
</body>
</html>
"""

SECTIONS['Template:anchor'] = """
<span id="{anchor}"></span>
"""

SECTIONS['Template:asm_comment'] = """
<tr>
<td class="routine-comment" colspan="4">
{t_anchor}
<div class="comments">
{m_paragraph}
</div>
</td>
</tr>
"""

SECTIONS['Template:asm_instruction'] = """
<tr>
<td class="asm-label-{entry[labels]}">{label}</td>
<td class="address-{called}">{t_anchor}{address}</td>
<td class="instruction">{operation}</td>
<td class="comment-{annotated}{entry[annotated]}" rowspan="{comment_rowspan}">{comment}</td>
</tr>
"""

SECTIONS['Template:asm_register'] = """
<tr>
<td class="register">{name}</td>
<td class="register-desc">{description}</td>
</tr>
"""

SECTIONS['Template:changelog_entry'] = """
<div>{t_anchor}</div>
<div class="changelog changelog-{num}">
<div class="changelog-title">{title}</div>
<div class="changelog-desc">{description}</div>
{t_changelog_item_list}
</div>
"""

SECTIONS['Template:changelog_item_list'] = """
<ul class="changelog{indent}">
{m_changelog_item}
</ul>
"""

SECTIONS['Template:contents_list_item'] = """
<li><a href="{href}">{title}</a></li>
"""

SECTIONS['Template:footer'] = """
<footer>
<div class="release">{Game[Release]}</div>
<div class="copyright">{Game[Copyright]}</div>
<div class="created">{Game[Created]}</div>
</footer>
"""

SECTIONS['Template:img'] = """
<img alt="{alt}" src="{src}" />
"""

SECTIONS['Template:index_section'] = """
<div class="section-header">{header}</div>
<ul class="index-list">
{m_index_section_item}
</ul>
"""

SECTIONS['Template:index_section_item'] = """
<li><a href="{href}">{link_text}</a>{other_text}</li>
"""

SECTIONS['Template:javascript'] = """
<script type="text/javascript" src="{src}"></script>
"""

SECTIONS['Template:link'] = """
<a href="{href}">{link_text}</a>
"""

SECTIONS['Template:list'] = """
<ul class="{class}">
{m_list_item}
</ul>
"""

SECTIONS['Template:list_item'] = """
<li>{item}</li>
"""

SECTIONS['Template:map_entry'] = """
<tr>
<td class="map-page-{MemoryMap[PageByteColumns]}">{entry[page]}</td>
<td class="map-byte-{MemoryMap[PageByteColumns]}">{entry[byte]}</td>
<td class="map-{entry[type]}">{t_anchor}<a href="{entry[href]}">{entry[address]}</a></td>
<td class="map-length-{MemoryMap[LengthColumn]}">{entry[size]}</td>
<td class="map-{entry[type]}-desc">
<div class="map-entry-title-1{MemoryMap[EntryDescriptions]}">{entry[title]}</div>
<div class="map-entry-desc-{MemoryMap[EntryDescriptions]}">
{entry[description]}
</div>
</td>
</tr>
"""

SECTIONS['Template:paragraph'] = """
<div class="paragraph">
{paragraph}
</div>
"""

SECTIONS['Template:reference_entry'] = """
<div>{t_anchor}</div>
<div class="box box-{num}">
<div class="box-title">{title}</div>
{contents}
</div>
"""

SECTIONS['Template:reg'] = """
<span class="register">{reg}</span>
"""

SECTIONS['Template:stylesheet'] = """
<link rel="stylesheet" type="text/css" href="{href}" />
"""

SECTIONS['Template:table'] = """
<table class="{class}">
{m_table_row}
</table>
"""

SECTIONS['Template:table_cell'] = """
<td class="{class}" colspan="{colspan}" rowspan="{rowspan}">{contents}</td>
"""

SECTIONS['Template:table_header_cell'] = """
<th colspan="{colspan}" rowspan="{rowspan}">{contents}</th>
"""

SECTIONS['Template:table_row'] = """
<tr>
{cells}
</tr>
"""

SECTIONS['Titles'] = """
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

def _format_section(name):
    return '[{}]{}'.format(name, SECTIONS[name])

REF_FILE = '\n'.join([_format_section(name) for name in SECTIONS])

def get_section(name):
    return _format_section(name)

def get_sections(prefix):
    sections = []
    for section_name in SECTIONS:
        if re.match(prefix, section_name):
            sections.append(_format_section(section_name))
    return '\n'.join(sections)
