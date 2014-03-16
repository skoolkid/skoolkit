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

REF_FILE = """
[Template:head]
<?xml version="1.0" encoding="utf-8" ?>
<!DOCTYPE html
    PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="content-type" content="text/html; charset=utf-8" />
<title>{Game}: {title}</title>
{t_stylesheets}
{t_javascripts}
</head>

[Template:stylesheet]
<link rel="stylesheet" type="text/css" href="{href}" />

[Template:javascript]
<script type="text/javascript" src="{src}"></script>

[Template:footer]
<div class="footer">
<div class="release">{Release}</div>
<div class="copyright">{Copyright}</div>
<div class="created">{Created}</div>
</div>

[Template:index_section]
<div class="headerText">{header}</div>
{t_link_list}

[Template:index]
{t_head}
<body class="main">
<table class="header">
<tr>
<td class="headerText">{TitlePrefix}</td>
<td class="headerLogo">{Logo}</td>
<td class="headerText">{TitleSuffix}</td>
</tr>
</table>
{t_index_sections}
{t_footer}
</body>
</html>

[Template:link_list]
<ul class="{list_class}">
{t_link_list_items}
</ul>

[Template:link_list_item]
<li><a class="link" href="{href}">{link_text}</a>{other_text}</li>
""".lstrip()
