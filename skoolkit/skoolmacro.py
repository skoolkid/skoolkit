# Copyright 2012-2022 Richard Dymond (rjdymond@gmail.com)
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
from functools import partial
import html
import inspect
import re
from string import Template

from skoolkit import (BASE_10, BASE_16, CASE_LOWER, CASE_UPPER, VERSION,
                      SkoolKitError, SkoolParsingError, eval_variable, evaluate)
from skoolkit.graphics import Udg
from skoolkit.simulator import (Simulator, A, F, B, C, D, E, H, L, IXh, IXl, IYh, IYl,
                                SP, I, R, xA, xF, xB, xC, xD, xE, xH, xL, PC, T)

_map_cache = {}

_writer = None

_cwd = ()

FILL_UDG = Udg(66, [129, 66, 36, 24, 24, 36, 66, 128])

MACRO_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

DELIMITERS = {
    '(': ')',
    '[': ']',
    '{': '}'
}

ZX_CHARS = {94: 8593, 96: 163, 127: 169}

INTEGER = '(\d+|\$[0-9a-fA-F]+)'

PARAM_NAME = '[a-z]+'

NAMED_PARAM = '({}=)?{}'.format(PARAM_NAME, INTEGER)

PARAMS = '{0}?(,({0})?){{,{1}}}'

RE_ANCHOR = re.compile('#[a-zA-Z0-9$#]*')

RE_CODE_ID = re.compile('@[a-zA-Z0-9$]*')

RE_EXPAND = re.compile('#[^A-Za-z0-9\s]')

RE_FRAME_ID = re.compile('[^\s,;(]+')

RE_MACRO = re.compile('#[A-Z]+')

RE_MACRO_METHOD = re.compile('expand_([a-z]+)$')

RE_METHOD_NAME = re.compile('[a-zA-Z_][a-zA-Z0-9_]*')

RE_LINK_PARAMS = re.compile('[^(\s]+')

RE_PARAM_NAME = re.compile('\s*{}\s*='.format(PARAM_NAME))

RE_REGISTER = re.compile("(af?|f|bc?|c|de?|e|hl?|l)'?|i[xy][lh]?|i|pc|r|sp")

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

class InvalidParameterError(MacroParsingError):
    pass

class FormattingError(MacroParsingError):
    pass

class ClosingBracketError(MacroParsingError):
    pass

class AudioTracer:
    def __init__(self):
        self.spkr = None
        self.out_times = []

    def write_port(self, registers, port, value):
        if port % 2 == 0 and self.spkr != value & 0x10:
            self.spkr = value & 0x10
            self.out_times.append(registers[T])

# API
def parse_ints(text, index=0, num=0, defaults=(), names=(), fields=None):
    """Parse a sequence of comma-separated integer parameters, optionally
    enclosed in parentheses. If parentheses are used, the parameters may be
    expressed using arithmetic operators and skool macros. See
    :ref:`numericParameters` for more details.

    :param text: The text to parse.
    :param index: The index at which to start parsing.
    :param num: The maximum number of parameters to parse; this is set to the
                number of elements in `names` if that list is not empty.
    :param defaults: The default values of the optional parameters.
    :param names: The names of the parameters; if not empty, keyword arguments
                  are parsed. Parameter names are restricted to lower case
                  letters (a-z).
    :param fields: A dictionary of replacement field names and values. The
                   fields named in this dictionary are replaced by their values
                   wherever they appear in the parameter string.
    :return: A list of the form ``[end, value1, value2...]``, where:

             * ``end`` is the index at which parsing terminated
             * ``value1``, ``value2`` etc. are the parameter values
    """
    if index < len(text) and text[index] == '(':
        end, params = parse_brackets(text, index)
        if _writer:
            params = _writer.expand(params, *_cwd)
        if fields is not None:
            params = _format_params(params, params, **fields)
        return [end] + get_params(params, num, defaults, names, text[index:end], False)
    if names:
        pattern = PARAMS.format(NAMED_PARAM, len(names) - 1)
    elif num > 0:
        pattern = PARAMS.format(INTEGER, num - 1)
    else:
        return [index]
    params = re.match(pattern, text[index:]).group()
    return [index + len(params)] + get_params(params, num, defaults, names, text[index:])

# API
def parse_strings(text, index=0, num=0, defaults=()):
    """Parse a sequence of comma-separated string parameters. The sequence must
    be enclosed in parentheses, square brackets or braces. If the sequence
    itself contains commas or unmatched brackets, then an alternative delimiter
    and separator may be used; see :ref:`stringParameters` for more details.

    :param text: The text to parse.
    :param index: The index at which to start parsing.
    :param num: The maximum number of parameters to parse. If 0, all parameters
                are parsed; if 1, the entire parameter string is parsed as a
                single parameter, regardless of commas.
    :param defaults: The default values of the optional parameters.
    :return: A tuple of the form ``(end, result)``, where:

             * ``end`` is the index at which parsing terminated
             * ``result`` is either the single parameter itself (when `num` is
               1), or a list of the parameters
    """
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
    if delim1 in DELIMITERS:
        end, param_string = parse_brackets(text, index, opening=delim1, closing=delim2)
    else:
        start = index + len(delim1)
        end = text.find(delim2, start)
        if end < start:
            raise MacroParsingError("No terminating delimiter: {}".format(text[index:]))
        param_string = text[start:end]
        end += len(delim2)

    if split:
        if sep == ',':
            args = _split_unbracketed(param_string)
        else:
            args = param_string.split(sep)
    else:
        args = param_string

    if num > 1:
        if len(args) > num:
            raise TooManyParametersError("Too many parameters (expected {}): '{}'".format(num, param_string), end)
        req = num - len(defaults)
        if len(args) < req:
            raise MissingParameterError("Not enough parameters (expected {}): '{}'".format(req, param_string), end)
        while len(args) < num:
            args.append(defaults[len(args) - req])

    return end, args

# API
def parse_brackets(text, index=0, default=None, opening='(', closing=')'):
    """Parse a single string parameter enclosed either in parentheses or by an
    arbitrary pair of delimiters.

    :param text: The text to parse.
    :param index: The index at which to start parsing.
    :param default: The default value if no string parameter is found.
    :param opening: The opening delimiter.
    :param closing: The closing delimiter.
    :return: A tuple of the form ``(end, param)``, where:

             * ``end`` is the index at which parsing terminated
             * ``param`` is the string parameter (or `default` if none is
               found)
    """
    if index >= len(text) or text[index] != opening:
        return index, default
    depth = 1
    end = index + 1
    while depth > 0:
        i = text.find(closing, end)
        if i < 0:
            raise ClosingBracketError('No closing bracket: {}'.format(text[index:]))
        depth += text.count(opening, end, i) - 1
        end = i + 1
    return end, text[index + 1:end - 1]

# API
def parse_image_macro(text, index=0, defaults=(), names=(), fname='', fields=None):
    """Parse a string of the form:

    ``[params][{x,y,width,height}][(fname[*frame][|alt])]``

    The parameter string ``params`` may contain comma-separated integer values,
    and may optionally be enclosed in parentheses. Parentheses are *required*
    if any parameter is expressed using arithmetic operations or skool macros.

    :param text: The text to parse.
    :param index: The index at which to start parsing.
    :param defaults: The default values of the optional parameters.
    :param names: The names of the parameters.
    :param fname: The default base name of the image file.
    :param fields: A dictionary of replacement field names and values. The
                   fields named in this dictionary are replaced by their values
                   wherever they appear in ``params`` or
                   ``{x,y,width,height}``.
    :return: A tuple of the form
             ``(end, crop_rect, fname, frame, alt, values)``, where:

             * ``end`` is the index at which parsing terminated
             * ``crop_rect`` is ``(x, y, width, height)``
             * ``fname`` is the base name of the image file
             * ``frame`` is the frame name (`None` if no frame is specified)
             * ``alt`` is the alt text (`None` if no alt text is specified)
             * ``values`` is a list of the parameter values
    """
    try:
        result = parse_ints(text, index, defaults=defaults, names=names, fields=fields)
    except InvalidParameterError:
        if len(defaults) != len(names):
            raise
        result = [index] + list(defaults)
    end, crop_rect = _parse_crop_spec(text, result[0], fields)
    end, fname, frame, alt = _parse_image_fname(text, end, fname)
    return end, crop_rect, fname, frame, alt, result[1:]

def _format_params(params, full_params, *args, **kwargs):
    try:
        return params.format(*args, **kwargs)
    except IndexError as e:
        raise FormattingError("Field index out of range: {}".format(full_params))
    except KeyError as e:
        raise FormattingError("Unrecognised field '{}': {}".format(e.args[0], full_params))
    except ValueError:
        raise FormattingError('Invalid format string: {}'.format(full_params))

def _split_unbracketed(text):
    if '(' not in text:
        return text.split(',')
    index = 0
    chunks = ['']
    start = text.index('(')
    while start >= 0:
        pieces = text[index:start].split(',')
        if pieces[0]:
            chunks[-1] += pieces[0]
        chunks.extend(pieces[1:])
        index = parse_brackets(text, start)[0]
        chunks[-1] += text[start:index]
        start = text.find('(', index)
    pieces = text[index:].split(',')
    if pieces[0]:
        chunks[-1] += pieces[0]
    chunks.extend(pieces[1:])
    return chunks

def parse_address_range(text, index, width, fields):
    elements = []
    end = index - 1
    while end < index or (len(elements) < 4 and end < len(text) and text[end] == '-'):
        end += 1
        try:
            end, value = parse_ints(text, end, 1, fields=fields)
        except FormattingError:
            raise
        except MacroParsingError:
            break
        elements.append(value)
    if not elements:
        return index, None

    num = 1
    if end < len(text) and text[end] == 'x':
        try:
            end, num = parse_ints(text, end + 1, 1, fields=fields)
        except FormattingError:
            raise
        except MacroParsingError:
            raise MacroParsingError("Invalid multiplier in address range specification: {}".format(text[index:]))

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

def _parse_crop_spec(text, index, fields=None):
    defaults = (0, 0, None, None)
    if index < len(text) and text[index] == '{':
        try:
            end, crop_spec = parse_brackets(text, index, opening='{', closing='}')
        except ClosingBracketError:
            raise MacroParsingError("No closing brace on cropping specification: {}".format(text[index:]))
        names = ('x', 'y', 'width', 'height')
        try:
            return end, tuple(parse_ints('({})'.format(crop_spec), defaults=defaults, names=names, fields=fields)[1:])
        except TooManyParametersError as e:
            raise TooManyParametersError("Too many parameters in cropping specification (expected 4 at most): {{{}}}".format(e.args[1]))
    return index, defaults

def _parse_image_fname(text, index, fname=''):
    end, p_text = parse_brackets(text, index)
    if p_text is None:
        return index, fname, None, None
    alt = frame = None
    if _writer:
        p_text = _writer.expand(p_text, *_cwd)
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

def get_params(param_string, num, defaults, names, text, safe=True):
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
                match = RE_PARAM_NAME.match(p)
                if match:
                    name = match.group()[:-1].strip()
                    if name in names:
                        value = p[match.end():]
                        index = names.index(name)
                        has_named_param = True
                    else:
                        raise MacroParsingError("Unknown keyword argument: '{}'".format(p))
                else:
                    if has_named_param:
                        raise MacroParsingError("Non-keyword argument after keyword argument: '{}'".format(p))
                    value = p
            else:
                value = p
            if value:
                try:
                    param = evaluate(value, safe)
                except ValueError:
                    raise InvalidParameterError("Cannot parse integer '{}' in parameter string: '{}'".format(value, param_string))
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
                raise MissingParameterError("Missing required argument '{}': '{}'".format(req_name, param_string))
    elif index < req:
        if params:
            raise MissingParameterError("Not enough parameters (expected {}): '{}'".format(req, param_string))
        if text:
            if len(text) > 10:
                text = text[:10] + '...'
            raise MissingParameterError(f"No parameters (expected {req}): '{text}'")
        raise MissingParameterError("No parameters (expected {})".format(req))
    elif None in params:
        missing_index = params.index(None)
        if missing_index < req:
            raise MissingParameterError("Missing required parameter in position {}/{}: '{}'".format(missing_index + 1, req, param_string))
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

def get_macros(writer):
    macros = {
        '#CALL': partial(parse_call, writer),
        '#CHR': partial(parse_chr, writer),
        '#D': partial(parse_d, writer),
        '#DEF': partial(parse_def, writer),
        '#DEFINE': partial(parse_define, writer),
        '#EVAL': partial(parse_eval, writer.fields, writer.case == CASE_LOWER),
        '#FOR': partial(parse_for, writer.fields),
        '#FOREACH': partial(parse_foreach, writer.parser),
        '#FORMAT': partial(parse_format, writer.fields),
        '#IF': partial(parse_if, writer.fields),
        '#LET': partial(parse_let, writer),
        '#MAP': partial(parse_map, writer.fields),
        '#N': partial(parse_n, writer),
        '#PC': partial(parse_pc, writer),
        '#PEEK': partial(parse_peek, writer),
        '#POKES': partial(parse_pokes, writer),
        '#POPS': partial(parse_pops, writer),
        '#PUSHS': partial(parse_pushs, writer),
        '#RAW': parse_raw,
        '#REG': partial(parse_reg, writer.get_reg, writer.case == CASE_LOWER),
        '#SIM': partial(parse_sim, writer),
        '#SPACE': partial(parse_space, writer),
        '#STR': partial(parse_str, writer),
        '#TSTATES': partial(parse_tstates, writer),
        '#VERSION': parse_version,
        '#WHILE': partial(parse_while, writer)
    }
    for name, method in inspect.getmembers(writer, inspect.ismethod):
        match = RE_MACRO_METHOD.match(name)
        if match:
            macros['#' + match.group(1).upper()] = method
    return macros

def expand_macros(writer, text, *cwd):
    global _writer, _cwd
    _writer = writer
    _cwd = cwd

    if '#' not in text:
        return text

    index = 0
    while 1:
        search = RE_MACRO.search(text, index)
        if not search:
            break
        marker = search.group()
        if marker not in writer.macros:
            raise SkoolParsingError('Found unknown macro: {}'.format(marker))
        index, start = search.span()

        while RE_EXPAND.match(text, start):
            end, expr = parse_strings(text, start + 1, 1)
            text = text[:start] + expand_macros(writer, expr, *cwd) + text[end:]

        repf = writer.macros[marker]
        try:
            end, rep = repf(text, start, *cwd)
        except UnsupportedMacroError:
            raise SkoolParsingError('Found unsupported macro: {}'.format(marker))
        except MacroParsingError as e:
            raise SkoolParsingError('Error while parsing {} macro: {}'.format(marker, e.args[0]))
        text = text[:index] + rep + text[abs(end):]
        if end < 0:
            index += len(rep)

    return text

def _flatten(elements):
    f = []
    for e in elements:
        if isinstance(e, (list, tuple)):
            f.extend(_flatten(e))
        else:
            f.append(e)
    return f

def _eval_delays(spec):
    valid_chars = frozenset(' 0123456789,*+-%()[]\n')
    if set(spec) <= valid_chars:
        try:
            return _flatten(eval(f'[{spec}]'))
        except:
            raise InvalidParameterError(f"Cannot evaluate delays: '{spec}'")
    invalid_chars = ''.join(sorted(set(spec) - valid_chars))
    raise InvalidParameterError(f"Invalid character(s) [{invalid_chars}] in delays specification: '{spec}'")

def parse_audio(writer, text, index, need_audio=None):
    # #AUDIO[flags,offset](fname)[(delays)]
    # #AUDIO[flags,offset](fname)(start,stop)
    try:
        end, flags, offset = parse_ints(text, index, 2, defaults=(0, 0), fields=writer.fields)
    except InvalidParameterError:
        end, flags, offset = index, 0, 0
    end, fname = parse_brackets(text, end)
    if not fname:
        raise MacroParsingError('Missing filename: #AUDIO{}'.format(text[index:end]))
    delays, eval_delays = None, False
    if need_audio:
        fname, eval_delays = need_audio(fname)
    if flags & 4:
        end, start, stop = parse_ints(text, end, 2, fields=writer.fields)
        if eval_delays:
            simulator = Simulator(writer.snapshot, config={'fast_djnz': True, 'fast_ldir': True})
            tracer = AudioTracer()
            simulator.set_tracer(tracer)
            simulator.run(start, stop)
            delays = [t - tracer.out_times[i] for i, t in enumerate(tracer.out_times[1:])]
    else:
        if len(text) > end and text[end] == '(':
            end, spec = parse_brackets(text, end)
            if eval_delays:
                expanded = writer.expand(spec)
                delays = _eval_delays(_format_params(expanded, expanded, **writer.fields))
    return end, flags, offset, fname, delays

def parse_call(writer, text, index, *cwd):
    # #CALL:methodName(args)
    macro = '#CALL'
    if index >= len(text):
        raise MacroParsingError("No parameters")
    if text[index] != ':':
        raise MacroParsingError("Malformed macro: {}{}...".format(macro, text[index]))

    end = index + 1
    match = RE_METHOD_NAME.match(text, end)
    if match:
        method_name = match.group()
        end += len(method_name)
    else:
        raise MacroParsingError("No method name")
    end, m_args = parse_brackets(text, end)

    if not hasattr(writer, method_name):
        writer.warn("Unknown method name in {} macro: {}".format(macro, method_name))
        return end, ''
    method = getattr(writer, method_name)
    if not inspect.ismethod(method):
        raise MacroParsingError("Uncallable method name: {}".format(method_name))

    if m_args is None:
        raise MacroParsingError("No argument list specified: {}{}".format(macro, text[index:end]))
    args = list(cwd)
    kwargs = {}
    if m_args:
        for arg in _format_params(writer.expand(m_args), m_args, **writer.fields).split(','):
            a1, sep, a2 = arg.partition('=')
            if sep:
                v = a2
            else:
                v = a1
            try:
                value = evaluate(v)
            except ValueError:
                if v:
                    value = v
                else:
                    value = None
            if sep:
                kwargs[a1] = value
            else:
                args.append(value)

    try:
        retval = method(*args, **kwargs)
    except Exception as e:
        raise MacroParsingError("Method call {} failed: {}".format(text[index + 1:end], e))
    if retval is None:
        retval = ''
    return end, retval

def parse_chr(writer, text, index, *cwd):
    # #CHRnum[,flags]
    end, num, flags = parse_ints(text, index, 2, (0,), fields=writer.fields)
    if flags & 2:
        num = ZX_CHARS.get(num, num)
    if flags & 1:
        return end, chr(num)
    return end, writer.to_chr(num)

def parse_copy(text, index, fields, frame_map=None):
    # #COPY[x,y,width,height,scale,mask,tindex,alpha][{CROP}](old,new)
    defaults = (0, 0, None, None, None, None, None, None)
    names = ('x', 'y', 'width', 'height', 'scale', 'mask', 'tindex', 'alpha')
    try:
        index, x, y, width, height, scale, mask, tindex, alpha = parse_ints(text, index, 0, defaults, names, fields)
    except InvalidParameterError:
        x, y, width, height, scale, mask, tindex, alpha = defaults
    if index < len(text) and text[index] == '{':
        end, crop_rect = _parse_crop_spec(text, index, fields)
    else:
        end, crop_rect = index, None
    end, (old, new) = parse_strings(text, end, 2)
    if frame_map is not None:
        if old not in frame_map:
            raise MacroParsingError('No such frame: "{}"'.format(old))
        frame_map[new] = frame_map[old].copy(new, x, y, width, height, scale, mask, crop_rect, tindex, alpha)
    return end, ''

def parse_d(writer, text, index, *cwd):
    # #Daddr
    end, addr = parse_ints(text, index, 1, fields=writer.fields)
    entry = writer.parser.get_entry(addr)
    if not entry:
        raise MacroParsingError('Cannot determine description for non-existent entry at {}'.format(addr))
    if not entry.description:
        raise MacroParsingError('Entry at {} has no description'.format(addr))
    return end, entry.description

def _expand_def_macro(writer, inames, idefaults, snames, sdefaults, body, flags, text, index, *cwd):
    end, ints, strings = index, [], []
    if inames:
        result = parse_ints(text, index, 0, idefaults, inames, writer.fields)
        end, ints = result[0], result[1:]
    params = dict(zip(inames, ints))
    if snames:
        if flags & 1:
            sdefaults = [s.format_map(params) for s in sdefaults]
        else:
            sdefaults = [t.safe_substitute(params) for t in sdefaults]
        if len(snames) != len(sdefaults) or (end < len(text) and text[end] == '('):
            end, strings = parse_strings(text, end, len(snames), sdefaults)
            if len(snames) == 1:
                strings = [strings]
        else:
            strings = sdefaults
        params.update(dict(zip(snames, strings)))
    if flags & 1:
        formatted = body.format_map(params)
    else:
        formatted = body.safe_substitute(params)
    if flags & 2:
        writer.sep_blocks = False
        formatted = writer.expand(formatted, *cwd).strip()
        writer.sep_blocks = True
    return end, formatted

def parse_def(writer, text, index, *cwd):
    # #DEF[flags](#MACRO[(ia[=i0],ib[=i1]...)[(sa[=s0],sb[=s1]...)]] body)
    try:
        end, flags = parse_ints(text, index, 1, (0,), fields=writer.fields)
    except SkoolKitError:
        end, flags = index, 0
    end, definition = parse_strings(text, end, 1)
    definition = definition.strip()
    match = RE_MACRO.match(definition, 0)
    if match:
        name = match.group()
        dindex = match.end()
    else:
        raise MacroParsingError("Invalid macro name: #DEF{}".format(text[index:]))
    dindex, iparams = parse_brackets(definition, dindex)
    if iparams is None:
        sparams = None
    else:
        dindex, sparams = parse_brackets(definition, dindex)
    body = definition[dindex:].strip()

    inames, idefaults = [], []
    if iparams:
        for ispec in _format_params(iparams, iparams, **writer.fields).split(','):
            iname, sep, ival = [s.strip() for s in ispec.partition('=')]
            match = re.match(PARAM_NAME, iname)
            if match and iname == match.group():
                inames.append(iname)
            else:
                raise MacroParsingError(f'Invalid macro argument name: {iname}')
            if sep:
                try:
                    idefaults.append(evaluate(ival))
                except ValueError:
                    raise InvalidParameterError(f"Cannot parse integer argument value: '{ispec}'")
            elif idefaults:
                idefaults.append(0)

    snames, sdefaults = [], []
    if sparams:
        for sspec in _split_unbracketed(sparams):
            sname, sep, sval = [s.strip() for s in sspec.partition('=')]
            snames.append(sname)
            if sep or sdefaults:
                sdefaults.append(sval)

    if flags & 1 == 0:
        sdefaults = [Template(s) for s in sdefaults]
        body = Template(body)
    writer.macros[name] = partial(_expand_def_macro, writer, inames, idefaults, snames, sdefaults, body, flags)
    return end, ''

def _expand(writer, iparams, sparams, value, text, index, *cwd):
    end, ints, strings = index, [], []
    if iparams > 0:
        result = parse_ints(text, index, iparams, fields=writer.fields)
        end, ints = result[0], result[1:]
    if sparams > 0:
        end, strings = parse_strings(text, end, sparams)
        if sparams == 1:
            strings = [strings]
    return end, _format_params(value, value, *ints, *strings)

def parse_define(writer, text, index, *cwd):
    # #DEFINEiparams[,sparams](name, value)
    end, iparams, sparams = parse_ints(text, index, 2, (0,))
    end, (name, value) = parse_strings(text, end, 2)
    writer.macros['#' + name] = partial(_expand, writer, iparams, sparams, value)
    return end, ''

def parse_eval(fields, lower, text, index, *cwd):
    # #EVALexpr[,base,width]
    end, value, base, width = parse_ints(text, index, 3, (10, 1), fields=fields)
    if base == 2:
        fmt = '{:0{}b}'
    elif base == 10:
        fmt = '{:0{}}'
    elif base == 16:
        if lower:
            fmt = '{:0{}x}'
        else:
            fmt = '{:0{}X}'
    else:
        raise MacroParsingError("Invalid base ({}): {}".format(base, text[index:end]))
    return end, fmt.format(value, width)

def parse_font(text, index=0, fields=None):
    # #FONT[:(text)]addr[,chars,attr,scale,tindex,alpha][{x,y,width,height}][(fname)]
    if index < len(text) and text[index] == ':':
        index, message = parse_strings(text, index + 1, 1)
        if not message:
            raise MacroParsingError("Empty message: {}".format(text[index - 2:index]))
    else:
        message = ''.join([chr(n) for n in range(32, 128)])
    names = ('addr', 'chars', 'attr', 'scale', 'tindex', 'alpha')
    defaults = (len(message), 56, 2, 0, -1)
    end, crop_rect, fname, frame, alt, params = parse_image_macro(text, index, defaults, names, 'font', fields)
    params.insert(0, message)
    return end, crop_rect, fname, frame, alt, params

def parse_for(fields, text, index, *cwd):
    # #FORstart,stop[,step,flags](var,string[,sep,fsep])
    end, start, stop, step, flags = parse_ints(text, index, 4, (1, 0), fields=fields)
    try:
        end, (var, s, sep, fsep) = parse_strings(text, end, 4, ('', None))
    except (NoParametersError, MissingParameterError) as e:
        raise MacroParsingError("No variable name: {}".format(text[index:e.args[1]]))
    if flags & 1:
        sep = ',' + sep
    if flags & 2:
        sep += ','
    if fields['mode']['html']:
        s = html.unescape(s)
    elements = []
    for n in range(start, stop + step // abs(step), step):
        if flags & 4:
            elements.extend((s.replace(var, str(n)), sep.replace(var, str(n))))
        else:
            elements.extend((s.replace(var, str(n)), sep))
    if elements:
        elements.pop()
    if len(elements) > 2 and fsep is not None:
        elements[-2] = fsep
    if fields['mode']['html']:
        return end, html.escape(''.join(elements))
    return end, ''.join(elements)

def parse_foreach(entry_holder, text, index, *cwd):
    # #FOREACH([v1,v2,...])(var,string[,sep,fsep])
    try:
        end, values = parse_strings(text, index)
    except NoParametersError:
        raise NoParametersError("No values")
    try:
        end, (var, s, sep, fsep) = parse_strings(text, end, 4, ('', None))
    except (NoParametersError, MissingParameterError) as e:
        raise MacroParsingError("No variable name: {}".format(text[index:e.args[1]]))
    if len(values) == 1:
        value = values[0]
        if value.startswith(('EREF', 'REF')):
            addr_str, getter, desc = {
                'E': (value[4:], entry_holder.get_instruction, 'instruction'),
                'R': (value[3:], entry_holder.get_entry, 'entry')
            }[value[0]]
            try:
                address = evaluate(addr_str)
                entity = getter(address)
                if not entity:
                    raise MacroParsingError('No {} at {}: {}'.format(desc, address, value))
                values = [str(r.address) for r in sorted(entity.referrers, key=lambda e: e.address)]
            except ValueError:
                pass
        elif value.startswith('ENTRY'):
            types = value[5:]
            values = [str(e.address) for e in entry_holder.memory_map if e.ctl != 'i' and (not types or e.ctl in types)]
    if not values:
        return end, ''
    if fsep is None:
        fsep = sep
    if entry_holder.fields['mode']['html']:
        s = html.unescape(s)
    if len(values) == 1:
        retval = s.replace(var, values[0])
    else:
        retval = fsep.join((sep.join([s.replace(var, v) for v in values[:-1]]), s.replace(var, values[-1])))
    if entry_holder.fields['mode']['html']:
        return end, html.escape(retval)
    return end, retval

def parse_format(fields, text, index, *cwd):
    # #FORMAT[case](text)
    try:
        index, case = parse_ints(text, index, 1, defaults=(0,), fields=fields)
    except InvalidParameterError:
        case = 0
    end, fmt = parse_strings(text, index, 1)
    formatted = _format_params(fmt, text[index:end], **fields)
    if case == CASE_LOWER:
        return end, formatted.lower()
    if case == CASE_UPPER:
        return end, formatted.upper()
    return end, formatted

def parse_html(text, index):
    # #HTML(text)
    return parse_strings(text, index, 1)

def parse_if(fields, text, index, *cwd):
    # #IFexpr(true[,false])
    try:
        end, value = parse_ints(text, index, 1, fields=fields)
    except MissingParameterError:
        raise MacroParsingError("No valid expression found: '#IF{}'".format(text[index:]))
    try:
        end, (s_true, s_false) = parse_strings(text, end, 2, ('',))
    except NoParametersError:
        raise NoParametersError("No output strings: {}".format(text[index:end]))
    except TooManyParametersError as e:
        raise MacroParsingError("Too many output strings (expected 2): {}".format(text[index:e.args[1]]))
    if value:
        return end, s_true
    return end, s_false

def parse_include(text, index, fields):
    # #INCLUDE[paragraphs](pattern)
    try:
        end, paragraphs = parse_ints(text, index, 1, (0,), fields=fields)
    except InvalidParameterError:
        end, paragraphs = index, 0
    end, pattern = parse_strings(text, end, 1)
    return end, paragraphs, pattern

def _eval_map(args, args_str, strings=True):
    default = args.pop(0)
    if not strings:
        try:
            default = evaluate(default)
        except ValueError:
            raise MacroParsingError("Invalid default integer value ({}): {}".format(default, args_str))
    m = defaultdict(lambda: default)
    if args:
        for pair in args:
            if ':' in pair:
                k, v = pair.split(':', 1)
            else:
                k = v = pair
            try:
                key = evaluate(k)
            except ValueError:
                raise MacroParsingError("Invalid key ({}): {}".format(k, args_str))
            if strings:
                m[key] = v
            else:
                try:
                    m[key] = evaluate(v)
                except ValueError:
                    raise MacroParsingError("Invalid integer value ({}): {}".format(v, args_str))
    return m

def parse_let(writer, text, index, *cwd):
    # #LET(name=value)
    end, stmt = parse_strings(text, index, 1)
    name, sep, value = stmt.partition('=')
    if name and sep:
        value = _format_params(writer.expand(value, *cwd), text[index:end], **writer.fields)
        if name.endswith('[]'):
            try:
                args = parse_strings(value, 0)[1]
            except NoParametersError:
                raise NoParametersError(f"No values provided: '{name}={value}'")
            writer.fields[name[:-2]] = _eval_map(args, value, name.endswith('$[]'))
        else:
            try:
                writer.fields[name] = eval_variable(name, value)
            except ValueError:
                raise InvalidParameterError("Cannot parse integer value '{}': {}".format(value, stmt))
    elif name:
        raise InvalidParameterError("Missing variable value: '{}'".format(stmt))
    else:
        raise InvalidParameterError("Missing variable name: '{}'".format(stmt))
    return end, ''

def parse_link(text, index):
    # #LINK:PageId[#name](link text)
    macro = '#LINK'
    if index >= len(text):
        raise MacroParsingError("No parameters")
    if text[index] != ':':
        raise MacroParsingError("Malformed macro: {}{}...".format(macro, text[index]))
    end = index + 1
    page_id = None
    match = RE_LINK_PARAMS.match(text, end)
    if match:
        page_id, sep, anchor = match.group().partition('#')
        if sep:
            anchor = sep + anchor
        end = match.end()
    end, link_text = parse_brackets(text, end)
    if not page_id:
        raise MacroParsingError("No page ID: {}{}".format(macro, text[index:end]))
    if link_text is None:
        raise MacroParsingError("No link text: {}{}".format(macro, text[index:end]))
    return end, page_id, anchor, link_text

def parse_map(fields, text, index, *cwd):
    # #MAPvalue(default[,k1:v1,k2:v2...])
    try:
        args_index, value = parse_ints(text, index, 1, fields=fields)
    except MissingParameterError:
        raise MacroParsingError("No valid expression found: '#MAP{}'".format(text[index:]))
    try:
        end, args = parse_strings(text, args_index)
    except NoParametersError:
        raise NoParametersError("No mappings provided: {}".format(text[index:args_index]))
    map_id = text[args_index:end]
    if map_id not in _map_cache:
        _map_cache[map_id] = _eval_map(args, map_id)
    return end, _map_cache[map_id][value]

def parse_n(writer, text, index, *cwd):
    # #Nvalue[,hwidth,dwidth,affix,hex][(prefix[,suffix])]
    end, value, hwidth, dwidth, affix, tohex = parse_ints(text, index, 5, (None, 1, 0, 0), fields=writer.fields)
    if affix:
        end, (prefix, suffix) = parse_strings(text, end, 2, ('', ''))
    else:
        prefix = suffix = ''
    if writer.base == BASE_16 or (tohex and writer.base != BASE_10):
        if hwidth is None:
            if 0 <= value < 256:
                hwidth = 2
            else:
                hwidth = 4
        if writer.case == CASE_LOWER:
            return end, '{}{:0{}x}{}'.format(prefix, value, hwidth, suffix)
        return end, '{}{:0{}X}{}'.format(prefix, value, hwidth, suffix)
    return end, '{:0{}}'.format(value, dwidth)

def _over_attr(t, fields, b, f):
    return parse_ints(t.safe_substitute(b=b, f=f), 0, 1, fields=fields)[1]

def _over_byte(t, fields, b, f, m):
    return parse_ints(t.safe_substitute(b=b, f=f, m=m), 0, 1, fields=fields)[1]

def parse_over(text, index, fields, frame_map=None):
    # #OVERx,y[,xoffset,yoffset,rmode][(attr)][(byte)](bg,fg)
    end, x, y, xoffset, yoffset, rmode = parse_ints(text, index, 2, (0, 0, 0), ('x', 'y', 'xoffset', 'yoffset', 'rmode'), fields)
    rattr, rbyte = None, None
    if rmode & 1:
        end, attr = parse_brackets(text, end)
        if attr is not None:
            rattr = partial(_over_attr, Template(f'({attr})'), fields)
    if rmode & 2:
        end, byte = parse_brackets(text, end)
        if byte is not None:
            rbyte = partial(_over_byte, Template(f'({byte})'), fields)
    end, (bg, fg) = parse_strings(text, end, 2)
    if frame_map is not None:
        if bg not in frame_map:
            raise MacroParsingError('No such frame: "{}"'.format(bg))
        if fg not in frame_map:
            raise MacroParsingError('No such frame: "{}"'.format(fg))
        frame_map[bg].overlay(frame_map[fg], x * 8 + xoffset, y * 8 + yoffset, rattr, rbyte)
    return end, ''

def parse_pc(writer, text, index, *cwd):
    # #PC
    return index, str(writer.pc)

def parse_peek(writer, text, index, *cwd):
    # #PEEKaddr
    end, addr = parse_ints(text, index, 1, fields=writer.fields)
    return end, str(writer.snapshot[addr & 65535])

def parse_plot(text, index, fields, frame_map=None):
    #PLOTx,y[,value](frame)
    end, x, y, value = parse_ints(text, index, 3, (1,), ('x', 'y', 'value'), fields)
    end, frame_id = parse_brackets(text, end)
    if frame_id is None:
        raise MacroParsingError("Missing frame name: #PLOT{}".format(text[index:end]))
    if frame_map is not None:
        if frame_id not in frame_map:
            raise MacroParsingError('No such frame: "{}"'.format(frame_id))
        frame_map[frame_id].plot(x, y, value)
    return end, ''

def parse_pokes(writer, text, index, *cwd):
    # #POKESaddr,byte[,length,step][;addr,byte[,length,step];...]
    end = index - 1
    while end < index or (end < len(text) and text[end] == ';'):
        end, addr, byte, length, step = parse_ints(text, end + 1, 4, (1, 1), fields=writer.fields)
        writer.snapshot[addr:addr + length * step:step] = [byte] * length
    return end, ''

def parse_pops(writer, text, index, *cwd):
    # #POPS
    try:
        writer.pop_snapshot()
    except SkoolKitError as e:
        raise MacroParsingError(e.args[0])
    return index, ''

def parse_pushs(writer, text, index, *cwd):
    # #PUSHS[name]
    end = index
    while end < len(text) and (text[end].isalnum() or text[end] in '$#'):
        end += 1
    writer.push_snapshot(text[index:end])
    return end, ''

def parse_r(fields, text, index):
    # #Raddr[@code][#anchor][(link text)]
    end, address = parse_ints(text, index, 1, fields=fields)
    addr_str = text[index:end]
    match = RE_CODE_ID.match(text, end)
    if match:
        code_id = match.group()[1:]
        end += len(code_id) + 1
    else:
        code_id = ''
    match = RE_ANCHOR.match(text, end)
    if match:
        anchor = match.group()
        end += len(anchor)
    else:
        anchor = ''
    end, link_text = parse_brackets(text, end)
    return end, addr_str, address, code_id, anchor, link_text

def parse_raw(text, index, *cwd):
    # #RAW(text)
    end, raw = parse_strings(text, index, 1)
    return -end, raw

def parse_reg(get_reg, lower, text, index, *cwd):
    # #REGreg
    if index >= len(text):
        raise MacroParsingError('Missing register argument')
    if text[index] in 'abcdefghijklmnopqrstuvwxyz':
        match = RE_REGISTER.match(text, index)
        if not match:
            raise MacroParsingError('Bad register: "{}"'.format(text[index:]))
        end, reg = match.end(), match.group()
    else:
        end, reg = parse_strings(text, index, 1)
        if not reg:
            raise MacroParsingError('Missing register argument')
    if lower:
        return end, get_reg(reg.lower())
    return end, get_reg(reg.upper())

def parse_scr(text, index=0, fields=None):
    # #SCR[scale,x,y,w,h,df,af,tindex,alpha][{x,y,width,height}][(fname)]
    names = ('scale', 'x', 'y', 'w', 'h', 'df', 'af', 'tindex', 'alpha')
    defaults = (1, 0, 0, 32, 24, 16384, 22528, 0, -1)
    return parse_image_macro(text, index, defaults, names, 'scr', fields)

def parse_sim(writer, text, index, *cwd):
    # #SIMstop[,start,clear,a,f,bc,de,hl,xa,xf,xbc,xde,xhl,ix,iy,i,r,sp]
    names = ('stop', 'start', 'clear', 'a', 'f', 'bc', 'de', 'hl', 'xa', 'xf',
             'xbc', 'xde', 'xhl', 'ix', 'iy', 'i', 'r', 'sp')
    defaults = (-1, 0) + (-1,) * (len(names) - 3)
    reg = {}
    (end, stop, start, clear, reg['A'], reg['F'], reg['BC'], reg['DE'], reg['HL'],
     reg['^A'], reg['^F'], reg['^BC'], reg['^DE'], reg['^HL'], reg['IX'], reg['IY'],
     reg['I'], reg['R'], reg['SP']) = parse_ints(text, index, len(names), defaults, names, writer.fields)
    registers = {}
    if clear == 0:
        registers.update(writer.fields.get('sim', {}))
    for r, v in reg.items():
        if v >= 0:
            registers[r] = v
    tstates = registers.get('tstates', 0)
    simulator = Simulator(writer.snapshot, registers, {'tstates': tstates}, {'fast_djnz': True, 'fast_ldir': True})
    if start < 0:
        start = simulator.registers[PC]
    simulator.run(start, stop)
    sim_registers = simulator.registers
    writer.fields['sim'] = {
        'A': sim_registers[A],
        'F': sim_registers[F],
        'BC': sim_registers[C] + 256 * sim_registers[B],
        'DE': sim_registers[E] + 256 * sim_registers[D],
        'HL': sim_registers[L] + 256 * sim_registers[H],
        '^A': sim_registers[xA],
        '^F': sim_registers[xF],
        '^BC': sim_registers[xC] + 256 * sim_registers[xB],
        '^DE': sim_registers[xE] + 256 * sim_registers[xD],
        '^HL': sim_registers[xL] + 256 * sim_registers[xH],
        'IX': sim_registers[IXl] + 256 * sim_registers[IXh],
        'IY': sim_registers[IYl] + 256 * sim_registers[IYh],
        'I': sim_registers[I],
        'R': sim_registers[R],
        'SP': sim_registers[SP],
        'PC': sim_registers[PC],
        'tstates': sim_registers[T]
    }
    return end, ''

def parse_space(writer, text, index, *cwd):
    # #SPACE[num] or #SPACE([num])
    end, num = parse_ints(text, index, 1, (1,), fields=writer.fields)
    return end, writer.space * num

def parse_str(writer, text, index, *cwd):
    # #STRaddr[,flags,length][(end)]
    end, addr, flags, length = parse_ints(text, index, 3, (0, -1), fields=writer.fields)
    s_data = []
    if length < 0:
        if flags & 8:
            end, end_param = parse_brackets(text, end)
            str_end = Template(f'({end_param})')
        else:
            str_end = None
        a = addr
        while a < 65536:
            b = writer.snapshot[a]
            if str_end:
                if parse_ints(str_end.safe_substitute(b=b), 0, 1, fields=writer.fields)[1]:
                    break
            elif b == 0:
                break
            elif b & 128:
                s_data.append(b & 127)
                break
            s_data.append(b)
            a += 1
    else:
        s_data.extend(writer.snapshot[addr:addr + length])
    s = ''.join(chr(ZX_CHARS.get(b, b)) for b in s_data)
    if flags & 1:
        s = s.rstrip()
    if flags & 2:
        s = s.lstrip()
    if flags & 4:
        while '  ' in s:
            i, j = re.search(' {2,}', s).span()
            s = s[:i] + f'#SPACE({j-i})' + s[j:]
    return end, s

def parse_tstates(writer, text, index, *cwd):
    # #TSTATESstart[,stop,flags(text)]
    end, start, stop, flags = parse_ints(text, index, 3, (-1, 0), fields=writer.fields)
    if flags & 2:
        end, msg = parse_strings(text, end, 1)
    else:
        msg = None
    if flags & 4:
        if stop < 0:
            raise MacroParsingError(f"Missing stop address: '{text[index:end]}'")
        simulator = Simulator(writer.snapshot[:])
        simulator.run(start, stop)
        if msg is None:
            return end, str(simulator.registers[T])
        return end, Template(msg).safe_substitute(tstates=simulator.registers[T])
    if stop < start:
        stop = start + 1
    timings = writer.parser.get_instruction_timings(start, stop)
    higher, lower = 0, 0
    for address, timing in timings:
        if timing is None:
            raise MacroParsingError(f'Failed to get timing for instruction at {address}')
        if isinstance(timing, int):
            higher, lower = higher + timing, lower + timing
        else:
            higher, lower = higher + timing[0], lower + timing[1]
    if msg is None:
        if flags & 1:
            return end, str(higher)
        return end, str(lower)
    return end, Template(msg).safe_substitute(min=lower, max=higher)

def parse_udg(text, index=0, fields=None):
    # #UDGaddr[,attr,scale,step,inc,flip,rotate,mask,tindex,alpha][:addr[,step]][{x,y,width,height}][(fname)]
    names = ('addr', 'attr', 'scale', 'step', 'inc', 'flip', 'rotate', 'mask', 'tindex', 'alpha')
    defaults = (56, 4, 1, 0, 0, 0, 1, 0, -1)
    end, addr, attr, scale, step, inc, flip, rotate, mask, tindex, alpha = parse_ints(text, index, defaults=defaults, names=names, fields=fields)
    if end < len(text) and text[end] == ':':
        end, mask_addr, mask_step = parse_ints(text, end + 1, defaults=(step,), names=('addr', 'step'), fields=fields)
    else:
        mask_addr = mask_step = None
        mask = 0
    end, crop_rect = _parse_crop_spec(text, end, fields)
    end, fname, frame, alt = _parse_image_fname(text, end)
    return end, crop_rect, fname, frame, alt, (addr, attr, scale, step, inc, flip, rotate, mask, tindex, alpha, mask_addr, mask_step)

def _parse_udg_specs(text, index, prefix, width, attr, step, inc, mask, snapshot, fields):
    end = index
    udg_array = [[]]
    has_masks = False

    while end < 0 or (end < len(text) and text[end] == ';'):
        names = ('attr', 'step', 'inc')
        defaults = (attr, step, inc)
        end, udg_addresses = parse_address_range(text, end + 1, width, fields)
        if udg_addresses is None:
            raise MacroParsingError('Expected UDG address range specification: #UDGARRAY{}{}'.format(prefix, text[max(index, 0):end]))
        if end < len(text) and text[end] == ',':
            end, udg_attr, udg_step, udg_inc = parse_ints(text, end + 1, defaults=defaults, names=names, fields=fields)
        else:
            udg_attr, udg_step, udg_inc = defaults
        mask_addresses = []
        if end < len(text) and text[end] == ':':
            end, mask_addresses = parse_address_range(text, end + 1, width, fields)
            if mask_addresses is None:
                raise MacroParsingError('Expected mask address range specification: #UDGARRAY{}{}'.format(prefix, text[max(index, 0):end]))
            if not mask:
                mask_addresses = []
            if end < len(text) and text[end] == ',':
                end, mask_step = parse_ints(text, end + 1, defaults=(udg_step,), names=('step',), fields=fields)
            else:
                mask_step = udg_step
        if snapshot:
            has_masks = has_masks or len(mask_addresses) > 0
            mask_addresses += [None] * (len(udg_addresses) - len(mask_addresses))
            for u, m in zip(udg_addresses, mask_addresses):
                udg_bytes = [(snapshot[u + n * udg_step] + udg_inc) % 256 for n in range(8)]
                udg = Udg(udg_attr, udg_bytes)
                if m is not None and mask:
                    udg.mask = [snapshot[m + n * mask_step] for n in range(8)]
                if len(udg_array[-1]) == width:
                    udg_array.append([udg])
                else:
                    udg_array[-1].append(udg)

    return end, udg_array, has_masks

def parse_udgarray(text, index, snapshot=None, req_fname=True, fields=None):
    # #UDGARRAYwidth[,attr,scale,step,inc,flip,rotate,mask,tindex,alpha](addr[,attr,step,inc][:addr[,step]];...)[{x,y,width,height}](fname)
    names = ('width', 'attr', 'scale', 'step', 'inc', 'flip', 'rotate', 'mask', 'tindex', 'alpha')
    defaults = (56, 2, 1, 0, 0, 0, 1, 0, -1)
    end, width, attr, scale, step, inc, flip, rotate, mask, tindex, alpha = parse_ints(text, index, defaults=defaults, names=names, fields=fields)

    if end < len(text) and text[end] == '(':
        prefix = text[index:end + 1]
        end, udg_specs = parse_brackets(text, end)
        udg_array, has_masks = _parse_udg_specs(udg_specs, -1, prefix, width, attr, step, inc, mask, snapshot, fields)[1:]
    else:
        end, udg_array, has_masks = _parse_udg_specs(text, end, text[index:end], width, attr, step, inc, mask, snapshot, fields)

    if len(udg_array) > 1 and len(udg_array[-1]) < width:
        udg_array[-1].extend((FILL_UDG,) * (width - len(udg_array[-1])))
    if not has_masks:
        mask = 0

    if end < len(text) and text[end] == '@':
        end, attr_addresses = parse_address_range(text, end + 1, width, fields)
        if attr_addresses is None:
            raise MacroParsingError('Expected attribute address range specification: #UDGARRAY{}'.format(text[index:end]))
        while end < len(text) and text[end] == ';':
            end, addresses = parse_address_range(text, end + 1, width, fields)
            if addresses is None:
                raise MacroParsingError('Expected attribute address range specification: #UDGARRAY{}'.format(text[index:end]))
            attr_addresses.extend(addresses)
        if snapshot:
            for i, attr_addr in enumerate(attr_addresses):
                y = i // width
                if y >= len(udg_array):
                    break
                udg_array[y][i % width].attr = snapshot[attr_addr & 65535]

    end, crop_rect = _parse_crop_spec(text, end, fields)
    end, fname, frame, alt = _parse_image_fname(text, end)
    if req_fname:
        if not fname and frame is None:
            raise MacroParsingError('Missing filename: #UDGARRAY{}'.format(text[index:end]))
        if not fname and not frame:
            raise MacroParsingError('Missing filename or frame ID: #UDGARRAY{}'.format(text[index:end]))
    return end, crop_rect, fname, frame, alt, (udg_array, scale, flip, rotate, mask, tindex, alpha)

def _parse_frame_specs(text, index, fields):
    params = []
    delay, x, y = 32, 0, 0
    end = index
    while end == index or (end < len(text) and text[end] == ';'):
        end += 1
        match = RE_FRAME_ID.match(text, end)
        if match:
            frame_id = match.group()
            end += len(frame_id)
            if end < len(text) and text[end] == ',':
                end, delay, x, y = parse_ints(text, end + 1, defaults=(delay, 0, 0), names=('delay', 'x', 'y'), fields=fields)
            params.append((frame_id, delay, x, y))
    return end, params

def parse_udgarray_with_frames(text, index, fields, frame_map=None):
    # #UDGARRAY*frame1[,delay,x,y];frame2[,delay,x,y];...(fname)
    if text[index:].startswith('*('):
        end, frame_specs = parse_brackets(text, index + 1)
        params = _parse_frame_specs(frame_specs, -1, fields)[1]
    else:
        end, params = _parse_frame_specs(text, index, fields)

    end, fname = parse_brackets(text, end)
    if not fname:
        raise MacroParsingError('Missing filename: #UDGARRAY{}'.format(text[index:end]))
    alt = None
    if '|' in fname:
        fname, alt = fname.split('|', 1)

    if not params:
        raise MacroParsingError("No frames specified: #UDGARRAY{}".format(text[index:end]))

    frames = []
    if frame_map is not None:
        for frame_id, delay, x_offset, y_offset in params:
            if frame_id not in frame_map:
                raise MacroParsingError('No such frame: "{}"'.format(frame_id))
            frame = frame_map[frame_id]
            frame.delay, frame.x_offset, frame.y_offset = delay, x_offset, y_offset
            if frames and (frame.width > frames[0].width or frame.height > frames[0].height):
                raise MacroParsingError("Frame '{}' ({}x{}) is larger than the first frame ({}x{})".format(
                    frame_id, frame.width, frame.height, frames[0].width, frames[0].height))
            frames.append(frame)

    return end, fname, alt, frames

def parse_udgs(writer, text, index, *cwd):
    # #UDGSwidth,height[,scale,flip,rotate,mask,tindex,alpha][{CROP}](fname)(uframe)
    names = ('width', 'height', 'scale', 'flip', 'rotate', 'mask', 'tindex', 'alpha')
    defaults = (None, 0, 0, None, None, None)
    end, width, height, scale, flip, rotate, mask, tindex, alpha = parse_ints(text, index, 0, defaults, names, writer.fields)
    if width < 1 or height < 1:
        raise MacroParsingError(f'Invalid dimensions: #UDGS{text[index:end]}')
    end, crop_rect = _parse_crop_spec(text, end, writer.fields)
    end, fname, frame, alt = _parse_image_fname(text, end)
    if not fname and frame is None:
        raise MacroParsingError(f'Missing filename: #UDGS{text[index:end]}')
    if not fname and not frame:
        raise MacroParsingError(f'Missing filename or frame ID: #UDGS{text[index:end]}')
    end, uframe = parse_strings(text, end, 1)

    if not hasattr(writer, 'frames'):
        return end, ''

    frames = writer.frames
    uframe_t = Template(uframe)
    udgs = []
    for y in range(height):
        udgs.append([])
        for x in range(width):
            expanded = writer.expand(uframe_t.safe_substitute(x=x, y=y), *cwd)
            udg_frame_name = _format_params(expanded, expanded, **writer.fields).strip()
            try:
                udgs[-1].append(frames[udg_frame_name].udgs[0][0])
            except KeyError:
                raise MacroParsingError(f"'{udg_frame_name}': frame not found (x={x}, y={y})")
    last_frame = frames[udg_frame_name]
    if scale is None:
        scale = last_frame.scale
    if mask is None:
        mask = last_frame.mask
    if tindex is None:
        tindex = last_frame.tindex
    if alpha is None:
        alpha = last_frame.alpha
    return end, crop_rect, fname, frame, alt, (udgs, scale, flip, rotate, mask, tindex, alpha)

def parse_version(text, index, *cwd):
    return index, VERSION

def parse_while(writer, text, index, *cwd):
    # #WHILE(expr)(body)
    end, expr = parse_brackets(text, index)
    if not expr:
        raise MissingParameterError('Missing conditional expression')
    expr = f'({expr})'
    end, body = parse_strings(text, end, 1)
    writer.sep_blocks = False
    output = ''
    while 1:
        if not parse_ints(expr, 0, 1, fields=writer.fields)[1]:
            break
        output += writer.expand(body, *cwd).strip()
    writer.sep_blocks = True
    return end, output
