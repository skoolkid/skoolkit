# Copyright 2014-2019 Richard Dymond (rjdymond@gmail.com)
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
"""

SECTIONS['Game'] = """
AddressAnchor={address}
; AsmSinglePageTemplate=
Bytes=
Copyright=
Created=Created using <a href="https://skoolkit.ca">SkoolKit</a> #VERSION.
DisassemblyTableNumCols=5
; Font=
; Game=
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
; Includes=
; Intro=
; LengthColumn=0
PageByteColumns=1
; Write=1
"""

SECTIONS['MemoryMap:RoutinesMap'] = """
; EntryDescriptions=0
EntryTypes=c
; Includes=
; Intro=
; LengthColumn=0
; PageByteColumns=0
; Write=1
"""

SECTIONS['MemoryMap:DataMap'] = """
; EntryDescriptions=0
EntryTypes=bw
; Includes=
; Intro=
; LengthColumn=0
PageByteColumns=1
; Write=1
"""

SECTIONS['MemoryMap:MessagesMap'] = """
; EntryDescriptions=0
EntryTypes=t
; Includes=
; Intro=
; LengthColumn=0
; PageByteColumns=0
; Write=1
"""

SECTIONS['MemoryMap:UnusedMap'] = """
; EntryDescriptions=0
EntryTypes=su
; Includes=
; Intro=
LengthColumn=1
PageByteColumns=1
; Write=1
"""

SECTIONS['MemoryMap:GameStatusBuffer'] = """
EntryDescriptions=1
EntryTypes=g
; Includes=
; Intro=
LengthColumn=1
; PageByteColumns=0
; Write=1
"""

SECTIONS['Page:Bugs'] = """
SectionPrefix=Bug
"""

SECTIONS['Page:Changelog'] = """
SectionPrefix=Changelog
SectionType=ListItems
"""

SECTIONS['Page:Facts'] = """
SectionPrefix=Fact
"""

SECTIONS['Page:Glossary'] = """
SectionPrefix=Glossary
"""

SECTIONS['Page:GraphicGlitches'] = """
SectionPrefix=GraphicGlitch
"""

SECTIONS['Page:Pokes'] = """
SectionPrefix=Poke
"""

SECTIONS['PageHeaders'] = """
Asm-b=Data
Asm-c=Routines
Asm-g=Game status buffer
Asm-s=Unused
Asm-t=Messages
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
FontImagePath={ImagePath}/font
ImagePath=images
JavaScriptPath=.
ScreenshotImagePath={ImagePath}/scr
StyleSheetPath=.
UDGImagePath={ImagePath}/udgs
AsmSinglePage=asm.html
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
UDGFilename=udg{addr}_{attr}x{scale}
UnusedMap=maps/unused.html
"""

SECTIONS['Template:Asm'] = """
<!DOCTYPE html>
<html>
<head>
<title>{Game[Game]}: {SkoolKit[title]} {entry[address]}</title>
<# include(head) #>
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
<td class="routine-comment" colspan="{Game[DisassemblyTableNumCols]}">
<div class="details">
<# foreach($paragraph,entry[description]) #>
<div class="paragraph">
{$paragraph}
</div>
<# endfor #>
</div>
<# if({entry[input]}) #>
<table class="input">
<tr class="asm-input-header">
<th colspan="2">{Game[InputRegisterTableHeader]}</th>
</tr>
<# foreach($reg,entry[input_registers]) #>
<tr>
<td class="register">{$reg[name]}</td>
<td class="register-desc">{$reg[description]}</td>
</tr>
<# endfor #>
</table>
<# endif #>
<# if({entry[output]}) #>
<table class="output">
<tr class="asm-output-header">
<th colspan="2">{Game[OutputRegisterTableHeader]}</th>
</tr>
<# foreach($reg,entry[output_registers]) #>
<tr>
<td class="register">{$reg[name]}</td>
<td class="register-desc">{$reg[description]}</td>
</tr>
<# endfor #>
</table>
<# endif #>
</td>
</tr>
<# foreach($instruction,entry[instructions]) #>
<# if({$instruction[has_block_comment]}) #>
<tr>
<td class="routine-comment" colspan="{Game[DisassemblyTableNumCols]}">
<span id="{$instruction[anchor]}"></span>
<div class="comments">
<# foreach($paragraph,$instruction[block_comment]) #>
<div class="paragraph">
{$paragraph}
</div>
<# endfor #>
</div>
</td>
</tr>
<# endif #>
<tr>
<td class="asm-label-{entry[labels]}">{$instruction[label]}</td>
<td class="address-{$instruction[called]}"><span id="{$instruction[anchor]}"></span>{$instruction[address]}</td>
<td class="bytes-{$instruction[show_bytes]}">{$instruction[bytes]:{Game[Bytes]}}</td>
<td class="instruction">{$instruction[operation]}</td>
<td class="comment-{$instruction[annotated]}{entry[annotated]}" rowspan="{$instruction[comment_rowspan]}">{$instruction[comment]}</td>
</tr>
<# endfor #>
<# if({entry[has_end_comment]}) #>
<tr>
<td class="routine-comment" colspan="{Game[DisassemblyTableNumCols]}">
<div class="comments">
<# foreach($paragraph,entry[end_comment]) #>
<div class="paragraph">
{$paragraph}
</div>
<# endfor #>
</div>
</td>
</tr>
<# endif #>
</table>
<table class="asm-navigation">
<tr>
<td class="prev"><span class="prev-{prev_entry[exists]}">Prev: <a href="{prev_entry[href]}">{prev_entry[address]}</a></span></td>
<td class="up">Up: <a href="{entry[map_href]}">Map</a></td>
<td class="next"><span class="next-{next_entry[exists]}">Next: <a href="{next_entry[href]}">{next_entry[address]}</a></span></td>
</tr>
</table>
<# include(footer) #>
</body>
</html>
"""

SECTIONS['Template:AsmAllInOne'] = """
<!DOCTYPE html>
<html>
<head>
<title>{Game[Game]}: {SkoolKit[title]}</title>
<# include(head) #>
</head>
<body class="{SkoolKit[page_id]}">
<table class="header">
<tr>
<td class="logo"><a href="{SkoolKit[index_href]}">{Game[Logo]}</a></td>
<td class="page-header">{SkoolKit[page_header]}</td>
</tr>
</table>
<# foreach($entry,entries) #>
<div id="{$entry[anchor]}" class="description">{$entry[address]}: {$entry[title]}</div>
<table class="disassembly">
<tr>
<td class="routine-comment" colspan="{Game[DisassemblyTableNumCols]}">
<div class="details">
<# foreach($paragraph,$entry[description]) #>
<div class="paragraph">
{$paragraph}
</div>
<# endfor #>
</div>
<# if({$entry[input]}) #>
<table class="input">
<tr class="asm-input-header">
<th colspan="2">{Game[InputRegisterTableHeader]}</th>
</tr>
<# foreach($reg,$entry[input_registers]) #>
<tr>
<td class="register">{$reg[name]}</td>
<td class="register-desc">{$reg[description]}</td>
</tr>
<# endfor #>
</table>
<# endif #>
<# if({$entry[output]}) #>
<table class="output">
<tr class="asm-output-header">
<th colspan="2">{Game[OutputRegisterTableHeader]}</th>
</tr>
<# foreach($reg,$entry[output_registers]) #>
<tr>
<td class="register">{$reg[name]}</td>
<td class="register-desc">{$reg[description]}</td>
</tr>
<# endfor #>
</table>
<# endif #>
</td>
</tr>
<# foreach($instruction,$entry[instructions]) #>
<# if({$instruction[has_block_comment]}) #>
<tr>
<td class="routine-comment" colspan="{Game[DisassemblyTableNumCols]}">
<span id="{$instruction[anchor]}"></span>
<div class="comments">
<# foreach($paragraph,$instruction[block_comment]) #>
<div class="paragraph">
{$paragraph}
</div>
<# endfor #>
</div>
</td>
</tr>
<# endif #>
<tr>
<td class="asm-label-{$entry[labels]}">{$instruction[label]}</td>
<td class="address-{$instruction[called]}"><span id="{$instruction[anchor]}"></span>{$instruction[address]}</td>
<td class="bytes-{$instruction[show_bytes]}">{$instruction[bytes]:{Game[Bytes]}}</td>
<td class="instruction">{$instruction[operation]}</td>
<td class="comment-{$instruction[annotated]}{$entry[annotated]}" rowspan="{$instruction[comment_rowspan]}">{$instruction[comment]}</td>
</tr>
<# endfor #>
<# if({$entry[has_end_comment]}) #>
<tr>
<td class="routine-comment" colspan="{Game[DisassemblyTableNumCols]}">
<div class="comments">
<# foreach($paragraph,$entry[end_comment]) #>
<div class="paragraph">
{$paragraph}
</div>
<# endfor #>
</div>
</td>
</tr>
<# endif #>
</table>
<# endfor #>
<# include(footer) #>
</body>
</html>
"""

SECTIONS['Template:GameIndex'] = """
<!DOCTYPE html>
<html>
<head>
<title>{Game[Game]}: {SkoolKit[title]}</title>
<# include(head) #>
</head>
<body class="{SkoolKit[page_id]}">
<table class="header">
<tr>
<td class="page-header">{Game[TitlePrefix]}</td>
<td class="logo">{Game[Logo]}</td>
<td class="page-header">{Game[TitleSuffix]}</td>
</tr>
</table>
<# foreach($section,sections) #>
<div class="section-header">{$section[header]}</div>
<ul class="index-list">
<# foreach($item,$section[items]) #>
<li><a href="{$item[href]}">{$item[link_text]}</a>{$item[other_text]}</li>
<# endfor #>
</ul>
<# endfor #>
<# include(footer) #>
</body>
</html>
"""

SECTIONS['Template:MemoryMap'] = """
<!DOCTYPE html>
<html>
<head>
<title>{Game[Game]}: {SkoolKit[title]}</title>
<# include(head) #>
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
<# if({MemoryMap[PageByteColumns]}) #>
<th class="map-page">Page</th>
<th class="map-byte">Byte</th>
<# endif #>
<th>Address</th>
<# if({MemoryMap[LengthColumn]}) #>
<th class="map-length">Length</th>
<# endif #>
<th>Description</th>
</tr>
<# foreach($entry,entries) #>
<tr>
<# if({MemoryMap[PageByteColumns]}) #>
<td class="map-page">{$entry[page]}</td>
<td class="map-byte">{$entry[byte]}</td>
<# endif #>
<td class="map-{$entry[type]}"><span id="{$entry[anchor]}"></span><a href="{$entry[href]}">{$entry[address]}</a></td>
<# if({MemoryMap[LengthColumn]}) #>
<td class="map-length">{$entry[size]}</td>
<# endif #>
<td class="map-{$entry[type]}-desc">
<div class="map-entry-title-1{MemoryMap[EntryDescriptions]}"><a class="map-entry-title" href="{$entry[href]}">{$entry[title]}</a></div>
<div class="map-entry-desc-{MemoryMap[EntryDescriptions]}">
<# foreach($paragraph,$entry[description]) #>
<div class="paragraph">
{$paragraph}
</div>
<# endfor #>
</div>
</td>
</tr>
<# endfor #>
</table>
<# include(footer) #>
</body>
</html>
"""

SECTIONS['Template:Page'] = """
<!DOCTYPE html>
<html>
<head>
<title>{Game[Game]}: {SkoolKit[title]}</title>
<# include(head) #>
</head>
<body class="{SkoolKit[page_id]}">
<table class="header">
<tr>
<td class="logo"><a href="{SkoolKit[index_href]}">{Game[Logo]}</a></td>
<td class="page-header">{SkoolKit[page_header]}</td>
</tr>
</table>
{content}
<# include(footer) #>
</body>
</html>
"""

SECTIONS['Template:Reference'] = """
<!DOCTYPE html>
<html>
<head>
<title>{Game[Game]}: {SkoolKit[title]}</title>
<# include(head) #>
</head>
<body class="{SkoolKit[page_id]}">
<table class="header">
<tr>
<td class="logo"><a href="{SkoolKit[index_href]}">{Game[Logo]}</a></td>
<td class="page-header">{SkoolKit[page_header]}</td>
</tr>
</table>
<ul class="contents">
<# foreach($item,contents) #>
<li><a href="{$item[href]}">{$item[title]}</a></li>
<# endfor #>
</ul>
<# if({has_list_entries}) #>
<# foreach($entry,list_entries) #>
<div><span id="{$entry[anchor]}"></span></div>
<div class="list-entry list-entry-{$entry[num]}">
<div class="list-entry-title">{$entry[title]}</div>
<div class="list-entry-desc">{$entry[description]}</div>
{$entry[item_list]}
</div>
<# endfor #>
<# else #>
<# foreach($entry,entries) #>
<div><span id="{$entry[anchor]}"></span></div>
<div class="box box-{$entry[num]}">
<div class="box-title">{$entry[title]}</div>
<# foreach($paragraph,$entry[contents]) #>
<div class="paragraph">
{$paragraph}
</div>
<# endfor #>
</div>
<# endfor #>
<# endif #>
<# include(footer) #>
</body>
</html>
"""

SECTIONS['Template:footer'] = """
<footer>
<div class="release">{Game[Release]}</div>
<div class="copyright">{Game[Copyright]}</div>
<div class="created">{Game[Created]}</div>
</footer>
"""

SECTIONS['Template:head'] = """
<meta charset="utf-8" />
<# foreach($css,stylesheets) #>
<link rel="stylesheet" type="text/css" href="{$css[href]}" />
<# endfor #>
<# foreach($js,javascripts) #>
<script type="text/javascript" src="{$js[src]}"></script>
<# endfor #>
"""

SECTIONS['Template:img'] = """
<img alt="{alt}" src="{src}" />
"""

SECTIONS['Template:item_list'] = """
<ul class="list-entry{indent}">
<# foreach($item,items) #>
<# if({$item[has_subitems]}) #>
<li>{$item[text]}
{$item[subitems]}
</li>
<# else #>
<li>{$item[text]}</li>
<# endif #>
<# endfor #>
</ul>
"""

SECTIONS['Template:link'] = """
<a href="{href}">{link_text}</a>
"""

SECTIONS['Template:list'] = """
<ul class="{list[class]}">
<# foreach($item,list[items]) #>
<li>{$item}</li>
<# endfor #>
</ul>
"""

SECTIONS['Template:reg'] = """
<span class="register">{reg}</span>
"""

SECTIONS['Template:section'] = """
<# foreach($paragraph,section) #>
<div class="paragraph">
{$paragraph}
</div>
<# endfor #>
"""

SECTIONS['Template:table'] = """
<table class="{table[class]}">
<# foreach($row,table[rows]) #>
<tr>
<# foreach($cell,$row[cells]) #>
<# if({$cell[header]}) #>
<th colspan="{$cell[colspan]}" rowspan="{$cell[rowspan]}">{$cell[contents]}</th>
<# else #>
<td class="{$cell[class]}" colspan="{$cell[colspan]}" rowspan="{$cell[rowspan]}">{$cell[contents]}</td>
<# endif #>
<# endfor #>
</tr>
<# endfor #>
</table>
"""

SECTIONS['Titles'] = """
Asm-b=Data at
Asm-c=Routine at
Asm-g=Game status buffer entry at
Asm-s=Unused RAM at
Asm-t=Text at
Asm-u=Unused RAM at
Asm-w=Data at
AsmSinglePage=Disassembly
; Bugs=
; Changelog=
DataMap=Data
Facts=Trivia
GameIndex=Index
GameStatusBuffer=Game status buffer
; Glossary=
GraphicGlitches=Graphic glitches
MemoryMap=Memory map
MessagesMap=Messages
; Pokes=
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
