# -*- coding: utf-8 -*-

# Copyright 2012-2015 Richard Dymond (rjdymond@gmail.com)
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

from collections import defaultdict
import inspect
import re

from skoolkit import SkoolKitError, SkoolParsingError

_map_cache = {}

MACRO_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

DELIMITERS = {
    '(': ')',
    '[': ']',
    '{': '}'
}

SIMPLE_INTEGER = '(\d+|\$[0-9a-fA-F]+)'

INTEGER = '[-+]?{0}([-+*/]{0})*'.format(SIMPLE_INTEGER)

INT = '({0}|\({0}\))$'.format(INTEGER)

CONDITION = '{0}((==|!=|<|>|<=|>=){0})?'.format(INTEGER)

EXPRESSION = '({0}|\({0}\))'.format(CONDITION)

PARAM_NAME = '[a-z]+'

SIMPLE_PARAM = '({}=)?{}'.format(PARAM_NAME, SIMPLE_INTEGER)

PARAM = '({}=)?{}'.format(PARAM_NAME, INTEGER)

ADDR_RANGE_PARAM = '({0}([+*/]{0})*|\({1}\))'.format(SIMPLE_INTEGER, INTEGER)

ADDR_RANGE = '{0}(-{0}){{,3}}(x{1})?'.format(ADDR_RANGE_PARAM, INTEGER)

class UnsupportedMacroError(SkoolKitError):
    pass

class MacroParsingError(SkoolKitError):
    pass

class NoParametersError(MacroParsingError):
    pass

class MissingParameterError(MacroParsingError):
    pass

class TooManyParametersError(MacroParsingError):
    pass

def parse_ints(text, index=0, num=0, defaults=(), names=()):
    """Parse a string of comma-separated integer parameters. The string will be
    parsed until either the end is reached, or an invalid character is
    encountered. The set of valid characters consists of the comma, '$', the
    digits 0-9, and the letters A-F and a-f; if `names` is not empty, the set
    of valid characters also includes '=' and the letters g-z.

    :param text: The text to parse.
    :param index: The index at which to start parsing.
    :param num: The maximum number of parameters to parse; this is set to the
                number of elements in `names` if that list is not empty.
    :param defaults: The default values of the optional parameters.
    :param names: The names of the parameters; if not empty, keyword arguments
                  are parsed.
    :return: A list of the form ``[end, value1, value2...]``, where:

             * ``end`` is the index at which parsing terminated
             * ``value1``, ``value2`` etc. are the parameter values
    """
    if index < len(text) and text[index] == '(':
        return _parse_ints_in_brackets(text, index, num, defaults, names)
    if names:
        pattern = '{0}(,({0})?)*'.format(SIMPLE_PARAM)
    else:
        pattern = '{0}(,({0})?){{,{1}}}'.format(SIMPLE_PARAM, num - 1)
    match = re.match(pattern, text[index:])
    if match:
        params = match.group()
    else:
        params = ''
    return [index + len(params)] + get_params(params, num, defaults, names=names)

def _parse_ints_in_brackets(text, index, num, defaults, names):
    end, params = _parse_brackets(text, index)
    if re.match('({0}(,({0})?)*)?$'.format(PARAM), params):
        return [end] + get_params(params, num, defaults, names=names)
    if len(defaults) == max(num, len(names)) > 0:
        return [index] + list(defaults)
    raise MacroParsingError("Invalid integer(s) in parameter string: ({})".format(params))

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
    end, p_text = _parse_brackets(text, index, p_text)
    return end, text[start:index], p_text

def parse_image_macro(text, index=0, defaults=(), names=(), fname=''):
    result = parse_ints(text, index, defaults=defaults, names=names)
    end, crop_rect = _parse_crop_spec(text, result[0])
    end, fname, frame, alt = _parse_image_fname(text, end, fname)
    return end, crop_rect, fname, frame, alt, result[1:]

def parse_address_range(text, index, width):
    match = re.match(ADDR_RANGE, text[index:])
    if not match:
        return index, None
    addr = match.group()
    end = index + len(addr)

    num = 1
    if 'x' in addr:
        addr, num = addr.split('x', 1)
        num = evaluate(num, True)

    elements = [evaluate(m.group(), True) for m in re.finditer(ADDR_RANGE_PARAM, addr)]
    if len(elements) < 2:
        elements.append(elements[0])
    if len(elements) < 3:
        elements.append(1)
    if len(elements) < 4:
        elements.append(elements[2] * width)

    address, end_address, h_step, v_step = elements
    addresses = []
    while address <= end_address:
        addresses.append(address)
        if len(addresses) % width:
            address += h_step
        else:
            address += v_step - (width - 1) * h_step

    return end, addresses * num

def _parse_crop_spec(text, index):
    defaults = (0, 0, None, None)
    if index < len(text) and text[index] == '{':
        names = ('x', 'y', 'width', 'height')
        try:
            end, x, y, width, height = parse_ints(text, index + 1, defaults=defaults, names=names)
        except TooManyParametersError as e:
            raise TooManyParametersError("Too many parameters in cropping specification (expected 4 at most): {{{}}}".format(e[1]))
        if end < len(text) and text[end] == '}':
            return end + 1, (x, y, width, height)
        raise MacroParsingError("No closing brace on cropping specification: {}".format(text[index:]))
    return index, defaults

def _parse_image_fname(text, index, fname=''):
    end, p_text = _parse_brackets(text, index)
    if p_text is None:
        return index, fname, None, None
    alt = frame = None
    if p_text:
        if '|' in p_text:
            p_text, alt = p_text.split('|', 1)
        if '*' in p_text:
            p_text, frame = p_text.split('*', 1)
        if p_text:
            fname = p_text
        elif frame:
            fname = ''
        if frame == '':
            frame = fname
    return end, fname, frame, alt

def _parse_brackets(text, index, default=None):
    if index >= len(text) or text[index] != '(':
        return index, default
    depth = 1
    end = index + 1
    while end < len(text) and depth > 0:
        if text[end] == ')':
            depth -= 1
        elif text[end] == '(':
            depth += 1
        end += 1
    if depth > 0:
        raise MacroParsingError('No closing bracket: {}'.format(text[index:]))
    return end, text[index + 1:end - 1]

def evaluate(param, safe=False):
    if safe or re.match(INT, param):
        return eval(re.sub('\$([0-9a-fA-F]+)', r'int("\1",16)', param).replace('/', '//'))
    raise ValueError

def get_params(param_string, num=0, defaults=(), ints=None, names=()):
    params = []
    named_params = {}
    index = 0
    has_named_param = False
    if names:
        num = len(names)
    if param_string:
        for p in param_string.split(','):
            if index < len(names):
                name = names[index]
            else:
                name = index
            if p and names:
                param_name, eq, value = p.partition('=')
                if not eq:
                    if has_named_param:
                        raise MacroParsingError("Non-keyword argument after keyword argument: '{}'".format(p))
                    value = param_name
                elif param_name in names:
                    name = param_name
                    index = names.index(name)
                    has_named_param = True
                else:
                    raise MacroParsingError("Unknown keyword argument: '{}'".format(p))
            else:
                value = p
            if value:
                try:
                    param = evaluate(value)
                except ValueError:
                    if ints is None or index in ints:
                        raise MacroParsingError("Cannot parse integer '{}' in parameter string: '{}'".format(value, param_string))
                    param = value
                if names and name:
                    named_params[name] = param
                else:
                    params.append(param)
            elif not names:
                params.append(None)
            index += 1

    req = num - len(defaults)
    if named_params:
        for i in range(req):
            req_name = names[i]
            if req_name not in named_params:
                raise MissingParameterError("Missing required argument '{}'".format(req_name))
    elif index < req:
        if params:
            raise MissingParameterError("Not enough parameters (expected {}): '{}'".format(req, param_string))
        raise MissingParameterError("No parameters (expected {})".format(req))
    if index > num > 0:
        raise TooManyParametersError("Too many parameters (expected {}): '{}'".format(num, param_string), param_string)

    if names:
        for i in range(req, num):
            name = names[i]
            if name not in named_params:
                named_params[name] = defaults[i - req]
        return [named_params[name] for name in names]

    params += [None] * (num - len(params))
    for i in range(req, num):
        if params[i] is None:
            params[i] = defaults[i - req]
    return params

def parse_text(text, index, num=0, defaults=()):
    if index >= len(text) or text[index].isspace():
        raise NoParametersError("No text parameter", index)

    sep = ','
    delim1 = text[index]
    delim2 = DELIMITERS.get(delim1, delim1)
    split = num != 1
    if split and delim1 == delim2 and index + 1 < len(text):
        sep = text[index + 1]
        delim1 += sep
        delim2 = sep + delim2
    start = index + len(delim1)
    if delim1 == '(':
        match = re.search(r'(?<=[^\\])\)', text[index:])
        if match:
            end = index + match.span()[0]
        else:
            end = -1
    else:
        end = text.find(delim2, start)
    if end < start:
        raise MacroParsingError("No terminating delimiter: {}".format(text[index:]))

    param_string = text[start:end]
    end += len(delim2)
    if delim1 == '(':
        param_string = param_string.replace('\\)', ')')

    if split:
        if param_string:
            if sep == ',':
                args = [s.replace('\\,', ',') for s in re.split(r'^,|(?<=[^\\]),', param_string)]
            else:
                args = param_string.split(sep)
        else:
            args = []
    else:
        args = param_string

    if num > 1:
        if len(args) > num:
            raise TooManyParametersError("Too many parameters (expected {}): '{}'".format(num, param_string), end)
        req = num - len(defaults)
        if len(args) < req:
            raise MissingParameterError("Not enough parameters (expected {}): '{}'".format(req, param_string), end, args)
        while len(args) < num:
            args.append(defaults[len(args) - req])

    return end, args

def get_macros(writer):
    macros = {}
    prefix = 'expand_'
    for name, method in inspect.getmembers(writer, inspect.ismethod):
        search = re.search('{}[a-z]+'.format(prefix), name)
        if search and name == search.group():
            macros['#' + name[len(prefix):].upper()] = method
    return macros

def _rfind_macro(text, macro):
    index = len(text)
    m_len = len(macro)
    max_index = index - m_len
    while 1:
        index = text.rfind(macro, 0, index)
        if index < 0 or index == max_index or macro[-1] not in MACRO_CHARS or text[index + m_len] not in MACRO_CHARS:
            return index

def _rfind_macros(text, *macros):
    index = -1
    macro = None
    for m in macros:
        m_index = _rfind_macro(text, m)
        if m_index > index:
            index = m_index
            macro = m
    if macro:
        return macro, index, index + len(macro)

def expand_macros(macros, text, *args):
    if text.find('#') < 0:
        return text

    while 1:
        search = _rfind_macros(text, '#FOR:', '#FOREACH:')
        if search:
            search = (search[0][:-1], search[1], search[2])
        else:
            search = _rfind_macros(text, '#EVAL', '#FOR', '#FOREACH', '#IF', '#MAP', '#PEEK')
            if not search:
                search = re.search('#[A-Z]+', text)
                if search:
                    search = (search.group(),) + search.span()
        if not search:
            break
        marker, start, index = search
        if not marker in macros:
            raise SkoolParsingError('Found unknown macro: {}'.format(marker))
        repf = macros[marker]
        try:
            end, rep = repf(text, index, *args)
        except UnsupportedMacroError:
            raise SkoolParsingError('Found unsupported macro: {}'.format(marker))
        except MacroParsingError as e:
            raise SkoolParsingError('Error while parsing {} macro: {}'.format(marker, e.args[0]))
        text = text[:start] + rep + text[end:]

    return text

def parse_item_macro(text, index, macro, def_link_text):
    end = index
    anchor = ''
    match = re.match('#[a-zA-Z0-9$#]*', text[end:])
    if match:
        anchor = match.group()
        end += match.span()[1]
    end, link_text = _parse_brackets(text, end, def_link_text)
    if anchor == '#':
        raise MacroParsingError("No item name: {}{}".format(macro, text[index:end]))
    return end, anchor[1:], link_text

def parse_bug(text, index):
    # #BUG[#name][(link text)]
    return parse_item_macro(text, index, '#BUG', 'bug')

def parse_call(text, index, writer, cwd=None):
    # #CALL:methodName(args)
    macro = '#CALL'
    if index >= len(text):
        raise MacroParsingError("No parameters")
    if text[index] != ':':
        raise MacroParsingError("Malformed macro: {}{}...".format(macro, text[index]))

    end = index + 1
    match = re.match('[a-zA-Z_][a-zA-Z0-9_]*', text[end:])
    if match:
        method_name = match.group()
        end += match.span()[1]
    else:
        raise MacroParsingError("No method name")
    end, arg_string = _parse_brackets(text, end)

    if not hasattr(writer, method_name):
        writer.warn("Unknown method name in {} macro: {}".format(macro, method_name))
        return end, ''
    method = getattr(writer, method_name)
    if not inspect.ismethod(method):
        raise MacroParsingError("Uncallable method name: {}".format(method_name))

    if arg_string is None:
        raise MacroParsingError("No argument list specified: {}{}".format(macro, text[index:end]))
    args = []
    if arg_string:
        for arg in arg_string.split(','):
            try:
                args.append(evaluate(arg))
            except ValueError:
                if arg:
                    args.append(arg)
                else:
                    args.append(None)

    if writer.needs_cwd():
        args.insert(0, cwd)
    try:
        retval = method(*args)
    except Exception as e:
        raise MacroParsingError("Method call {} failed: {}".format(text[index + 1:end], e))
    if retval is None:
        retval = ''
    return end, retval

def parse_chr(text, index):
    # #CHRnum or #CHR(num)
    return parse_ints(text, index, 1)

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

def parse_eval(text, index):
    # #EVAL(arg[,base,width])
    end, value, base, width = parse_ints(text, index, 3, (10, 1))
    if base == 2:
        value = '{:0{}b}'.format(value, width)
    elif base == 10:
        value = '{:0{}}'.format(value, width)
    elif base == 16:
        value = '{:0{}X}'.format(value, width)
    else:
        raise MacroParsingError("Invalid base ({}): {}".format(base, text[index:end]))
    return end, value

def parse_fact(text, index):
    # #FACT[#name][(link text)]
    return parse_item_macro(text, index, '#FACT', 'fact')

def parse_font(text, index):
    # #FONT[:(text)]addr[,chars,attr,scale][{x,y,width,height}][(fname)]
    if index < len(text) and text[index] == ':':
        index, message = parse_text(text, index + 1, 1)
        if not message:
            raise MacroParsingError("Empty message: {}".format(text[index - 2:index]))
    else:
        message = ''.join([chr(n) for n in range(32, 128)])
    names = ('addr', 'chars', 'attr', 'scale')
    defaults = (len(message), 56, 2)
    end, crop_rect, fname, frame, alt, params = parse_image_macro(text, index, defaults, names, 'font')
    params.insert(0, message)
    return end, crop_rect, fname, frame, alt, params

def parse_for(text, index):
    # #FOR[:]start,stop[,step](var,string[,sep,fsep])
    end, start, stop, step = parse_ints(text, index, 3, (1,))
    try:
        end, (var, s, sep, fsep) = parse_text(text, end, 4, ('', None))
    except (NoParametersError, MissingParameterError) as e:
        raise MacroParsingError("No variable name: {}".format(text[index:e[1]]))
    if fsep is None:
        fsep = sep
    if start == stop:
        return end, s.replace(var, str(start))
    return end, fsep.join((sep.join([s.replace(var, str(n)) for n in range(start, stop, step)]), s.replace(var, str(stop))))

def parse_foreach(text, index, entry_holder):
    # #FOREACH[:]([v1,v2,...])(var,string[,sep,fsep])
    try:
        end, values = parse_text(text, index)
    except NoParametersError:
        raise NoParametersError("No values")
    try:
        end, (var, s, sep, fsep) = parse_text(text, end, 4, ('', None))
    except (NoParametersError, MissingParameterError) as e:
        raise MacroParsingError("No variable name: {}".format(text[index:e[1]]))
    if len(values) == 1:
        value = values[0]
        if re.match('EREF{}'.format(INT), value):
            values = [str(a) for a in entry_holder.get_entry_point_refs(evaluate(value[4:], True))]
        elif re.match('REF{}'.format(INT), value):
            address = evaluate(value[3:], True)
            entry = entry_holder.get_entry(address)
            if not entry:
                raise MacroParsingError('No entry at {}: {}'.format(address, value))
            values = [str(addr) for addr in sorted([ref.address for ref in entry.referrers])]
        elif re.match('ENTRY[a-z]*$', value):
            types = value[5:]
            values = [str(e.address) for e in entry_holder.memory_map if not types or e.ctl in types]
    if not values:
        return end, ''
    if fsep is None:
        fsep = sep
    if len(values) == 1:
        return end, s.replace(var, values[0])
    return end, fsep.join((sep.join([s.replace(var, v) for v in values[:-1]]), s.replace(var, values[-1])))

def parse_html(text, index):
    # #HTML(text)
    return parse_text(text, index, 1)

def parse_if(text, index):
    # #IFexpr(true,false)
    match = re.match(EXPRESSION, text[index:])
    if match:
        expr = match.group()
        value = evaluate(expr, True)
        end = index + len(expr)
    else:
        raise MacroParsingError("No valid expression found: '#IF{}'".format(text[index:]))
    try:
        end, (true, false) = parse_text(text, end, 2)
    except NoParametersError:
        raise NoParametersError("No output strings: {}".format(text[index:end]))
    except MissingParameterError as e:
        if len(e[2]) == 0:
            raise MissingParameterError("No output strings: {}".format(text[index:e[1]]))
        raise MacroParsingError("Only one output string (expected 2): {}".format(text[index:e[1]]))
    except TooManyParametersError as e:
        raise MacroParsingError("Too many output strings (expected 2): {}".format(text[index:e[1]]))
    if value:
        return end, true
    return end, false

def parse_link(text, index):
    # #LINK:PageId[#name](link text)
    macro = '#LINK'
    if index >= len(text):
        raise MacroParsingError("No parameters")
    if text[index] != ':':
        raise MacroParsingError("Malformed macro: {}{}...".format(macro, text[index]))
    end = index + 1
    page_id = None
    match = re.match('[^(\s]+', text[end:])
    if match:
        page_id, sep, anchor = match.group().partition('#')
        if sep:
            anchor = sep + anchor
        end += match.span()[1]
    end, link_text = _parse_brackets(text, end)
    if not page_id:
        raise MacroParsingError("No page ID: {}{}".format(macro, text[index:end]))
    if link_text is None:
        raise MacroParsingError("No link text: {}{}".format(macro, text[index:end]))
    return end, page_id, anchor, link_text

def parse_map(text, index):
    # #MAPvalue(default,k1:v1[,k2:v2...])
    args_index, value = parse_ints(text, index, 1)
    try:
        end, args = parse_text(text, args_index)
    except NoParametersError:
        raise NoParametersError("No mappings provided: {}".format(text[index:args_index]))
    map_id = text[args_index:end]
    if map_id in _map_cache:
        return end, _map_cache[map_id][value]
    if args:
        default = args.pop(0)
    else:
        default = ''
    m = defaultdict(lambda: default)
    if args:
        for pair in args:
            if ':' in pair:
                k, v = pair.split(':', 1)
            else:
                k = v = pair
            try:
                m[evaluate(k)] = v
            except ValueError:
                raise MacroParsingError("Invalid key ({}): {}".format(k, text[args_index:end]))
    _map_cache[map_id] = m
    return end, m[value]

def parse_peek(text, index, snapshot):
    # #PEEKaddr or #PEEK(addr)
    end, addr = parse_ints(text, index, 1)
    return end, str(snapshot[addr & 65535])

def parse_poke(text, index):
    # #POKE[#name][(link text)]
    return parse_item_macro(text, index, '#POKE', 'poke')

def parse_pokes(text, index, snapshot):
    # #POKESaddr,byte[,length,step][;addr,byte[,length,step];...]
    end = index - 1
    while end < index or (end < len(text) and text[end] == ';'):
        end, addr, byte, length, step = parse_ints(text, end + 1, 4, (1, 1))
        snapshot[addr:addr + length * step:step] = [byte] * length
    return end, ''

def parse_pops(text, index, writer):
    # #POPS
    try:
        writer.pop_snapshot()
    except SkoolKitError as e:
        raise MacroParsingError(e.args[0])
    return index, ''

def parse_pushs(text, index, writer):
    # #PUSHS[name]
    end = index
    while end < len(text) and (text[end].isalnum() or text[end] in '$#'):
        end += 1
    writer.push_snapshot(text[index:end])
    return end, ''

def parse_r(text, index):
    # #Raddr[@code][#anchor][(link text)]
    end, address = parse_ints(text, index, 1)
    addr_str = text[index:end]
    match = re.match('@[a-zA-Z0-9$]*', text[end:])
    if match:
        code_id = match.group()[1:]
        end += len(code_id) + 1
    else:
        code_id = ''
    match = re.match('#[a-zA-Z0-9$#]*', text[end:])
    if match:
        anchor = match.group()
        end += len(anchor)
    else:
        anchor = ''
    end, link_text = _parse_brackets(text, end)
    return end, addr_str, address, code_id, anchor, link_text

def parse_refs(text, index, entry_holder):
    # #REFSaddr[(prefix)]
    end, address = parse_ints(text, index, 1)
    end, prefix = _parse_brackets(text, end, '')
    entry = entry_holder.get_entry(address)
    if not entry:
        raise MacroParsingError('No entry at {}'.format(address))
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
    if index >= len(text):
        raise MacroParsingError('Missing register argument')
    match = re.match("(af?|bc?|c|de?|e|hl?|l)'?|i[xy][lh]?|i|pc|r|sp", text[index:])
    if not match:
        raise MacroParsingError('Bad register: "{}"'.format(text[index:]))
    reg = match.group()
    end = index + len(reg)
    if lower:
        return end, reg
    return end, reg.upper()

def parse_scr(text, index):
    # #SCR[scale,x,y,w,h,df,af][{x,y,width,height}][(fname)]
    names = ('scale', 'x', 'y', 'w', 'h', 'df', 'af')
    defaults = (1, 0, 0, 32, 24, 16384, 22528)
    return parse_image_macro(text, index, defaults, names, 'scr')

def parse_space(text, index):
    # #SPACE[num] or #SPACE([num])
    return parse_ints(text, index, 1, (1,))

def parse_udg(text, index):
    # #UDGaddr[,attr,scale,step,inc,flip,rotate,mask][:addr[,step]][{x,y,width,height}][(fname)]
    names = ('addr', 'attr', 'scale', 'step', 'inc', 'flip', 'rotate', 'mask')
    defaults = (56, 4, 1, 0, 0, 0, 1)
    end, addr, attr, scale, step, inc, flip, rotate, mask = parse_ints(text, index, defaults=defaults, names=names)
    if end < len(text) and text[end] == ':':
        end, mask_addr, mask_step = parse_ints(text, end + 1, defaults=(step,), names=('addr', 'step'))
    else:
        mask_addr = mask_step = None
        mask = 0
    end, crop_rect = _parse_crop_spec(text, end)
    end, fname, frame, alt = _parse_image_fname(text, end)
    return end, crop_rect, fname, frame, alt, (addr, attr, scale, step, inc, flip, rotate, mask, mask_addr, mask_step)

def parse_udgarray(text, index, udg_class=None, snapshot=None):
    # #UDGARRAYwidth[,attr,scale,step,inc,flip,rotate,mask];addr[,attr,step,inc][:addr[,step]];...[{x,y,width,height}](fname)
    names = ('width', 'attr', 'scale', 'step', 'inc', 'flip', 'rotate', 'mask')
    defaults = (56, 2, 1, 0, 0, 0, 1)
    end, width, attr, scale, step, inc, flip, rotate, mask = parse_ints(text, index, defaults=defaults, names=names)
    udg_array = [[]]
    has_masks = False
    while end < len(text) and text[end] == ';':
        names = ('attr', 'step', 'inc')
        defaults = (attr, step, inc)
        end, udg_addresses = parse_address_range(text, end + 1, width)
        if udg_addresses is None:
            raise MacroParsingError('Expected UDG address range specification: #UDGARRAY{}'.format(text[index:end]))
        if end < len(text) and text[end] == ',':
            end, udg_attr, udg_step, udg_inc = parse_ints(text, end + 1, defaults=defaults, names=names)
        else:
            udg_attr, udg_step, udg_inc = defaults
        mask_addresses = []
        if end < len(text) and text[end] == ':':
            end, mask_addresses = parse_address_range(text, end + 1, width)
            if mask_addresses is None:
                raise MacroParsingError('Expected mask address range specification: #UDGARRAY{}'.format(text[index:end]))
            if not mask:
                mask_addresses = []
            if end < len(text) and text[end] == ',':
                end, mask_step = parse_ints(text, end + 1, defaults=(udg_step,), names=('step',))
            else:
                mask_step = udg_step
        if udg_class:
            has_masks = has_masks or len(mask_addresses) > 0
            mask_addresses += [None] * (len(udg_addresses) - len(mask_addresses))
            for u, m in zip(udg_addresses, mask_addresses):
                udg_bytes = [(snapshot[u + n * udg_step] + udg_inc) % 256 for n in range(8)]
                udg = udg_class(udg_attr, udg_bytes)
                if m is not None and mask:
                    udg.mask = [snapshot[m + n * mask_step] for n in range(8)]
                if len(udg_array[-1]) == width:
                    udg_array.append([udg])
                else:
                    udg_array[-1].append(udg)
    if not has_masks:
        mask = 0
    end, crop_rect = _parse_crop_spec(text, end)
    end, fname, frame, alt = _parse_image_fname(text, end)
    if not fname and frame is None:
        raise MacroParsingError('Missing filename: #UDGARRAY{}'.format(text[index:end]))
    if not fname and not frame:
        raise MacroParsingError('Missing filename or frame ID: #UDGARRAY{}'.format(text[index:end]))
    return end, crop_rect, fname, frame, alt, (udg_array, scale, flip, rotate, mask)

def parse_udgarray_with_frames(text, index, frame_map=None):
    # #UDGARRAY*frame1[,delay];frame2[,delay];...(fname)
    params = []
    delay = 32 # 0.32s
    end = index
    while end == index or (end < len(text) and text[end] == ';'):
        end += 1
        match = re.match('[^\s,;(]+', text[end:])
        if match:
            frame_id = match.group()
            end += len(frame_id)
            if end < len(text) and text[end] == ',':
                try:
                    end, delay = parse_ints(text, end + 1, names=('delay',))
                except MissingParameterError:
                    raise MissingParameterError("Missing 'delay' parameter for frame '{}'".format(frame_id))
            params.append((frame_id, delay))

    end, fname = _parse_brackets(text, end)
    if not fname:
        raise MacroParsingError('Missing filename: #UDGARRAY{}'.format(text[index:end]))
    alt = None
    if '|' in fname:
        fname, alt = fname.split('|', 1)

    if not params:
        raise MacroParsingError("No frames specified: #UDGARRAY{}".format(text[index:end]))

    frames = []
    if frame_map is not None:
        for frame_id, delay in params:
            if frame_id not in frame_map:
                raise MacroParsingError('No such frame: "{}"'.format(frame_id))
            frame = frame_map[frame_id]
            frame.delay = delay
            frames.append(frame)

    return end, fname, alt, frames
