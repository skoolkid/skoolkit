# -*- coding: utf-8 -*-

# Copyright 2012-2013 Richard Dymond (rjdymond@gmail.com)
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

import inspect

from . import get_int_param, parse_int, SkoolKitError

DELIMITERS = {
    '(': ')',
    '[': ']',
    '{': '}'
}

def parse_ints(text, index, num, defaults=()):
    """Parse a string of comma-separated integer parameters. The string will be
    parsed until either the end is reached, or an invalid character is
    encountered. The set of valid characters consists of the comma, '$', the
    digits 0-9, and the letters A-F and a-f.

    :param text: The text to parse.
    :param index: The index at which to start parsing.
    :param num: The maximum number of parameters to parse.
    :param defaults: The default values of the optional parameters.
    :return: A list of the form ``[end, value1, value2...]``, where:

             * ``end`` is the index at which parsing terminated
             * ``value1``, ``value2`` etc. are the parameter values
    """
    end = index
    num_params = 1
    while end < len(text) and text[end] in '$0123456789abcdefABCDEF,':
        if text[end] == ',':
            if num_params == num:
                break
            num_params += 1
        end += 1
    params = get_params(text[index:end], num, defaults)
    return [end] + params

def parse_params(text, index, p_text=None, chars='', except_chars='', only_chars=''):
    """Parse a string of the form ``params[(p_text)]``. The parameter string
    ``params`` will be parsed until either the end is reached, or an invalid
    character is encountered. The default set of valid characters consists of
    '$', '#', the digits 0-9, and the letters A-Z and a-z.

    :param text: The text to parse.
    :param index: The index at which to start parsing.
    :param p_text: The default value to use for text found in parentheses.
    :param chars: Characters to consider valid in addition to those in the
                  default set.
    :param except_chars: If not empty, all characters except those in this
                         string are considered valid.
    :param only_chars: If not empty, only the characters in this string are
                       considered valid.
    :return: A 3-tuple of the form ``(end, params, p_text)``, where:

             * ``end`` is the index at which parsing terminated
             * ``params`` is the parameter string
             * ``p_text`` is the text found in parentheses (if any)
    """
    start = index
    if except_chars:
        while index < len(text) and text[index] not in except_chars:
            index += 1
    elif only_chars:
        while index < len(text) and text[index] in only_chars:
            index += 1
    else:
        valid_chars = '$#' + chars
        while index < len(text) and (text[index].isalnum() or text[index] in valid_chars):
            index += 1
    params = text[start:index]
    end = index
    if index < len(text) and text[index] == '(':
        p_index = index
        depth = 1
        end += 1
        while end < len(text) and depth > 0:
            if text[end] == ')':
                depth -= 1
            elif text[end] == '(':
                depth += 1
            end += 1
        if depth > 0:
            raise MacroParsingError('No closing bracket: {}'.format(text[p_index:]))
        p_text = text[index + 1:end - 1]
    return end, params, p_text

def get_params(param_string, num=0, defaults=(), ints=None):
    params = []
    if param_string:
        for i, p in enumerate(param_string.split(',')):
            if p:
                param = parse_int(p)
                if param is None:
                    if ints is None or i in ints:
                        raise MacroParsingError("Cannot parse integer '{}' in parameter string: '{}'".format(p, param_string))
                    params.append(p)
                else:
                    params.append(param)
            else:
                params.append(None)
    req = num - len(defaults)
    if len(params) < req:
        if params:
            raise MacroParsingError("Not enough parameters (expected {}): '{}'".format(req, param_string))
        raise MacroParsingError("No parameters (expected {})".format(req))
    params += [None] * (num - len(params))
    for i in range(req, num):
        if params[i] is None:
            params[i] = defaults[i - req]
    return params

def get_text_param(text, index):
    if index >= len(text):
        raise MacroParsingError("No text parameter")
    delim1 = text[index]
    delim2 = DELIMITERS.get(delim1, delim1)
    start = index + 1
    end = text.find(delim2, start)
    if end < start:
        raise MacroParsingError("No terminating delimiter: {}".format(text[index:]))
    return end + 1, text[start:end]

class UnsupportedMacroError(SkoolKitError):
    pass

class MacroParsingError(SkoolKitError):
    pass

def parse_call(text, index, writer):
    # #CALL:methodName(args)
    macro = '#CALL'
    if index >= len(text):
        raise MacroParsingError("No parameters")
    if text[index] != ':':
        raise MacroParsingError("Malformed macro: {}{}...".format(macro, text[index]))
    end, method_name, arg_string = parse_params(text, index + 1, chars='_')
    if not method_name:
        raise MacroParsingError("No method name")
    if not hasattr(writer, method_name):
        warning = "Unknown method name in {} macro: {}".format(macro, method_name)
        return end, None, None, warning
    method = getattr(writer, method_name)
    if not inspect.ismethod(method):
        raise MacroParsingError("Uncallable method name: {}".format(method_name))
    if arg_string is None:
        raise MacroParsingError("No argument list specified: {}{}".format(macro, text[index:end]))
    args = get_params(arg_string, ints=())
    return end, method, args, None

def parse_chr(text, index):
    # #CHRnum or #CHR(num)
    if index < len(text) and text[index] == '(':
        end, _, num_str = parse_params(text, index)
        try:
            num = get_int_param(num_str)
        except ValueError:
            raise MacroParsingError("Invalid integer: '{}'".format(num_str))
    else:
        end, num = parse_ints(text, index, 1)
    return end, num

def parse_d(text, index, entry_holder):
    # #Daddr
    end, addr = parse_ints(text, index, 1)
    entry = entry_holder.get_entry(addr)
    if not entry:
        raise MacroParsingError('Cannot determine description for non-existent entry at {}'.format(addr))
    if not entry.description:
        raise MacroParsingError('Entry at {} has no description'.format(addr))
    return end, entry.description

def parse_erefs(text, index, entry_holder):
    # #EREFSaddr
    end, address = parse_ints(text, index, 1)
    ereferrers = entry_holder.get_entry_point_refs(address)
    if not ereferrers:
        raise MacroParsingError('Entry point at {} has no referrers'.format(address))
    ereferrers.sort()
    rep = 'routine at '
    if len(ereferrers) > 1:
        rep = 'routines at '
        rep += ', '.join('#R{}'.format(addr) for addr in ereferrers[:-1])
        rep += ' and '
    addr = ereferrers[-1]
    rep += '#R{}'.format(addr)
    return end, rep

def parse_link(text, index):
    # #LINK:PageId[#name](link text)
    macro = '#LINK'
    if index >= len(text):
        raise MacroParsingError("No parameters")
    if text[index] != ':':
        raise MacroParsingError("Malformed macro: {}{}...".format(macro, text[index]))
    end, param_str, link_text = parse_params(text, index + 1)
    if not param_str:
        raise MacroParsingError("No page ID: {}{}".format(macro, text[index:end]))
    if link_text is None:
        raise MacroParsingError("No link text: {}{}".format(macro, text[index:end]))
    page_id, sep, anchor = param_str.partition('#')
    if sep:
        anchor = sep + anchor
    return end, page_id, anchor, link_text

def parse_pokes(text, index, snapshot):
    # #POKESaddr,byte[,length,step][;addr,byte[,length,step];...]
    end, addr, byte, length, step = parse_ints(text, index, 4, (1, 1))
    snapshot[addr:addr + length * step:step] = [byte] * length
    while end < len(text) and text[end] == ';':
        end, addr, byte, length, step = parse_ints(text, end + 1, 4, (1, 1))
        snapshot[addr:addr + length * step:step] = [byte] * length
    return end, ''

def parse_r(text, index):
    # #Raddr[@code][#anchor][(link text)]
    end, params, link_text = parse_params(text, index, chars='@')
    anchor = ''
    anchor_index = params.find('#')
    if anchor_index >= 0:
        anchor = params[anchor_index:]
        params = params[:anchor_index]
    code_id = ''
    code_id_index = params.find('@')
    if code_id_index >= 0:
        code_id = params[code_id_index + 1:]
        params = params[:code_id_index]
    addr_str = params
    if not addr_str:
        raise MacroParsingError("No address")
    try:
        address = get_int_param(addr_str)
    except ValueError:
        raise MacroParsingError("Invalid address: {}".format(addr_str))
    return end, addr_str, address, code_id, anchor, link_text

def parse_refs(text, index, entries):
    # #REFSaddr[(prefix)]
    end, addr_str, prefix = parse_params(text, index, '')
    if not addr_str:
        raise MacroParsingError("No address")
    try:
        address = get_int_param(addr_str)
    except ValueError:
        raise MacroParsingError("Invalid address: {}".format(addr_str))
    entry = entries.get(address)
    if not entry:
        raise MacroParsingError('No entry at {}'.format(addr_str))
    referrers = [ref.address for ref in entry.referrers]
    if referrers:
        referrers.sort()
        rep = '{} routine at '.format(prefix).lstrip()
        if len(referrers) > 1:
            rep = '{} routines at '.format(prefix).lstrip()
            rep += ', '.join('#R{}'.format(addr) for addr in referrers[:-1])
            rep += ' and '
        addr = referrers[-1]
        rep += '#R{}'.format(addr)
    else:
        rep = 'Not used directly by any other routines'
    return end, rep

def parse_reg(text, index, lower):
    # #REGreg
    end = index
    while end < len(text) and text[end] in "abcdefhlirspxy'":
        end += 1
    reg = text[index:end]
    if not reg:
        raise MacroParsingError('Missing register argument')
    if len(reg) > 3:
        raise MacroParsingError('Bad register: "{}"'.format(reg))
    if lower:
        return end, reg.lower()
    return end, reg.upper()

def parse_space(text, index):
    # #SPACE[num] or #SPACE([num])
    if index < len(text) and text[index] == '(':
        end, _, num_str = parse_params(text, index)
        try:
            return end, get_int_param(num_str)
        except ValueError:
            raise MacroParsingError("Invalid integer: '{}'".format(num_str))
    return parse_ints(text, index, 1, (1,))
