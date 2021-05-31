# Copyright 2021 Richard Dymond (rjdymond@gmail.com)
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.

from skoolkit.skoolhtml import HtmlWriter

def init_page(self, skoolkit, game):
    if 'alt_base' in game:
        path = skoolkit['path']
        page_id = skoolkit['page_id']
        if page_id.startswith(('Asm', 'load-Asm', 'save-Asm', 'start-Asm')):
            addr_str = path.rsplit('/', 1)[-1][:-5]
            if game['alt_base'] == 'decimal':
                path = path.replace(addr_str, str(int(addr_str, 16)))
            else:
                path = path.replace(addr_str, '{:04X}'.format(int(addr_str)))
        elif page_id.startswith('Lesson') and page_id != 'LessonIndex':
            lesson = page_id[-3:]
            if game['alt_base'] == 'decimal':
                path = path.replace('{:02X}'.format(int(lesson)), lesson)
            else:
                path = path.replace(lesson, '{:02X}'.format(int(lesson)))
        skoolkit['Path'] = skoolkit['index_href'][:-10] + game['alt_dir'] + path

HtmlWriter.init_page = init_page
