# Copyright 2014-2021 Richard Dymond (rjdymond@gmail.com)
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
Address=
AddressAnchor={address}
AsmSinglePage=0
Bytes=
Copyright=
Created=Created using <a href="https://skoolkit.ca">SkoolKit</a> #VERSION.
DisassemblyTableNumCols=5
; Font=
; Game=
InputRegisterTableHeader=Input
; JavaScript=
Length={size}
LinkInternalOperands=0
LinkOperands=CALL,DEFW,DJNZ,JP,JR
; Logo=
; LogoImage=
OutputRegisterTableHeader=Output
Release=
StyleSheet=skoolkit.css
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
EntryTypes=bcgstuw
; Includes=
; Intro=
; LabelColumn=0
; LengthColumn=0
PageByteColumns=1
; Write=1
"""

SECTIONS['MemoryMap:RoutinesMap'] = """
; EntryDescriptions=0
EntryTypes=c
; Includes=
; Intro=
; LabelColumn=0
; LengthColumn=0
; PageByteColumns=0
; Write=1
"""

SECTIONS['MemoryMap:DataMap'] = """
; EntryDescriptions=0
EntryTypes=bw
; Includes=
; Intro=
; LabelColumn=0
; LengthColumn=0
PageByteColumns=1
; Write=1
"""

SECTIONS['MemoryMap:MessagesMap'] = """
; EntryDescriptions=0
EntryTypes=t
; Includes=
; Intro=
; LabelColumn=0
; LengthColumn=0
; PageByteColumns=0
; Write=1
"""

SECTIONS['MemoryMap:UnusedMap'] = """
; EntryDescriptions=0
EntryTypes=su
; Includes=
; Intro=
; LabelColumn=0
LengthColumn=1
PageByteColumns=1
; Write=1
"""

SECTIONS['MemoryMap:GameStatusBuffer'] = """
EntryDescriptions=1
EntryTypes=g
; Includes=
; Intro=
; LabelColumn=0
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
GameIndex=The complete<>RAM disassembly
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

SECTIONS['Template:Layout'] = """
<!DOCTYPE html>
<html>
<head>
<title>{Game[Game]}: {SkoolKit[title]}</title>
<meta charset="utf-8" />
<# foreach($css,SkoolKit[stylesheets]) #>
<link rel="stylesheet" type="text/css" href="{$css[href]}" />
<# endfor #>
<# foreach($js,SkoolKit[javascripts]) #>
<script type="text/javascript" src="{$js[src]}"></script>
<# endfor #>
</head>
<body class="{SkoolKit[page_id]}">
<table class="header">
<tr>
<# if(SkoolKit[page_header][0]) #>
<td class="page-header">{SkoolKit[page_header][0]}</td>
<# endif #>
<# if(SkoolKit[page_id]=='GameIndex') #>
<td class="logo">{Game[Logo]}</td>
<# else #>
<td class="logo"><a href="{SkoolKit[index_href]}">{Game[Logo]}</a></td>
<# endif #>
<td class="page-header">{SkoolKit[page_header][1]}</td>
</tr>
</table>
<# include({SkoolKit[include]}) #>
<# include(footer) #>
</body>
</html>
"""

SECTIONS['Template:asm'] = """
<table class="asm-navigation">
<tr>
<td class="prev">
<# if({prev_entry[exists]}) #>
Prev: <a href="{prev_entry[href]}">{prev_entry[address]}</a>
<# endif #>
</td>
<td class="up">Up: <a href="{entry[map_href]}">Map</a></td>
<td class="next">
<# if({next_entry[exists]}) #>
Next: <a href="{next_entry[href]}">{next_entry[address]}</a>
<# endif #>
</td>
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
<# if(entry[input_registers]) #>
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
<# if(entry[output_registers]) #>
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
<# if($instruction[block_comment]) #>
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
<# if({entry[labels]}) #>
<td class="asm-label">{$instruction[label]}</td>
<# endif #>
<td class="address-{$instruction[called]}"><span id="{$instruction[anchor]}"></span>{$instruction[address]}</td>
<# if({entry[show_bytes]}) #>
<td class="bytes">{$instruction[bytes]:{Game[Bytes]}}</td>
<# endif #>
<td class="instruction">{$instruction[operation]}</td>
<# if($instruction[comment_rowspan]) #>
<td class="comment-{entry[annotated]}" rowspan="{$instruction[comment_rowspan]}">{$instruction[comment]}</td>
<# endif #>
</tr>
<# endfor #>
<# if(entry[end_comment]) #>
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
<td class="prev">
<# if({prev_entry[exists]}) #>
Prev: <a href="{prev_entry[href]}">{prev_entry[address]}</a>
<# endif #>
</td>
<td class="up">Up: <a href="{entry[map_href]}">Map</a></td>
<td class="next">
<# if({next_entry[exists]}) #>
Next: <a href="{next_entry[href]}">{next_entry[address]}</a>
<# endif #>
</td>
</tr>
</table>
"""

SECTIONS['Template:asm_single_page'] = """
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
<# if($entry[input_registers]) #>
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
<# if($entry[output_registers]) #>
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
<# if($instruction[block_comment]) #>
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
<# if({$entry[labels]}) #>
<td class="asm-label">{$instruction[label]}</td>
<# endif #>
<td class="address-{$instruction[called]}"><span id="{$instruction[anchor]}"></span>{$instruction[address]}</td>
<# if({$entry[show_bytes]}) #>
<td class="bytes">{$instruction[bytes]:{Game[Bytes]}}</td>
<# endif #>
<td class="instruction">{$instruction[operation]}</td>
<# if($instruction[comment_rowspan]) #>
<td class="comment-{$entry[annotated]}" rowspan="{$instruction[comment_rowspan]}">{$instruction[comment]}</td>
<# endif #>
</tr>
<# endfor #>
<# if($entry[end_comment]) #>
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
"""

SECTIONS['Template:box_entries'] = """
<ul class="contents">
<# foreach($entry,entries) #>
<li><a href="#{$entry[anchor]}">{$entry[title]}</a></li>
<# endfor #>
</ul>
<# foreach($entry,entries) #>
<div><span id="{$entry[anchor]}"></span></div>
<div class="box box-{$entry[order]}">
<div class="box-title">{$entry[title]}</div>
<# foreach($paragraph,$entry[contents]) #>
<div class="paragraph">
{$paragraph}
</div>
<# endfor #>
</div>
<# endfor #>
"""

SECTIONS['Template:box_list_entries'] = """
<ul class="contents">
<# foreach($entry,entries) #>
<li><a href="#{$entry[anchor]}">{$entry[title]}</a></li>
<# endfor #>
</ul>
<# foreach($entry,entries) #>
<div><span id="{$entry[anchor]}"></span></div>
<div class="list-entry list-entry-{$entry[order]}">
<div class="list-entry-title">{$entry[title]}</div>
<div class="list-entry-desc">{$entry[intro]}</div>
{$entry[item_list]}
</div>
<# endfor #>
"""

SECTIONS['Template:footer'] = """
<footer>
<div class="release">{Game[Release]}</div>
<div class="copyright">{Game[Copyright]}</div>
<div class="created">{Game[Created]}</div>
</footer>
"""

SECTIONS['Template:home'] = """
<# foreach($section,sections) #>
<div class="section-header">{$section[header]}</div>
<ul class="index-list">
<# foreach($item,$section[items]) #>
<li><a href="{$item[href]}">{$item[link_text]}</a>{$item[other_text]}</li>
<# endfor #>
</ul>
<# endfor #>
"""

SECTIONS['Template:img'] = """
<img alt="{alt}" src="{src}" />
"""

SECTIONS['Template:item_list'] = """
<ul class="list-entry{indent}">
<# foreach($item,items) #>
<# if($item[subitems]) #>
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
<ul class="{class}">
<# foreach($item,items) #>
<li>{$item}</li>
<# endfor #>
</ul>
"""

SECTIONS['Template:memory_map'] = """
<div class="map-intro">{MemoryMap[Intro]}</div>
<table class="map">
<tr>
<# if({MemoryMap[PageByteColumns]}) #>
<th class="map-page">Page</th>
<th class="map-byte">Byte</th>
<# endif #>
<# if({MemoryMap[LabelColumn]}) #>
<th>Label</th>
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
<# if({MemoryMap[LabelColumn]}) #>
<td class="map-label"><a href="{$entry[href]}">{$entry[label]}</a></td>
<# endif #>
<td class="map-{$entry[type]}"><span id="{$entry[anchor]}"></span><a href="{$entry[href]}">{$entry[address]}</a></td>
<# if({MemoryMap[LengthColumn]}) #>
<td class="map-length">{$entry[length]}</td>
<# endif #>
<td class="map-{$entry[type]}-desc">
<div class="map-entry-title-1{MemoryMap[EntryDescriptions]}"><a class="map-entry-title" href="{$entry[href]}">{$entry[title]}</a></div>
<# if({MemoryMap[EntryDescriptions]}) #>
<div class="map-entry-desc">
<# foreach($paragraph,$entry[description]) #>
<div class="paragraph">
{$paragraph}
</div>
<# endfor #>
</div>
<# endif #>
</td>
</tr>
<# endfor #>
</table>
"""

SECTIONS['Template:page'] = """
{Page[PageContent]}
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
<table class="{class}">
<# foreach($row,rows) #>
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
Asm-b=Data at {entry[address]}
Asm-c=Routine at {entry[address]}
Asm-g=Game status buffer entry at {entry[address]}
Asm-s=Unused RAM at {entry[address]}
Asm-t=Text at {entry[address]}
Asm-u=Unused RAM at {entry[address]}
Asm-w=Data at {entry[address]}
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
