#!/usr/bin/env python3
import argparse
import re
import sys

DELIMITERS = {
    '(': ')',
    '[': ']',
    '{': '}'
}

INTEGER = r'(\d+|\$[0-9a-fA-F]+)'

RE_METHOD_NAME = re.compile('[a-zA-Z_][a-zA-Z0-9_]*')

RE_LINK_PARAMS = re.compile(r'[^(\s]+')

RE_FRAME_ID = re.compile(r'[^\s,;(]+')

PARAMS = '{0}?(,({0})?){{,{1}}}'

AE_CHARS = frozenset(' !=+-*/<>&|^%$ABCDEFabcdef0123456789()')

class InvalidParameterError(Exception):
    pass

def get_int_param(num_str):
    try:
        return int(num_str)
    except ValueError:
        pass
    if num_str.startswith('$'):
        return int(num_str[1:], 16)
    raise ValueError

def evaluate(param, safe=False):
    try:
        return get_int_param(param)
    except ValueError:
        pass
    if safe or set(param) <= AE_CHARS:
        try:
            return int(eval(param.replace('$', '0x').replace('/', '//').replace('&&', ' and ').replace('||', ' or ')))
        except:
            pass
    raise ValueError

def get_params(param_string, num, defaults, safe=True):
    params = []
    index = 0
    if param_string:
        for value in param_string.split(','):
            if value:
                try:
                    param = evaluate(value, safe)
                except ValueError:
                    raise InvalidParameterError(f"Cannot parse integer '{value}' in parameter string: '{param_string}'")
                params.append(param)
            else:
                params.append(None)
            index += 1
            if index == num:
                break
    params += [None] * (num - len(params))
    for i in range(num):
        if params[i] is None:
            params[i] = defaults[i]
    return params

def parse_ints_ex(text, index, num, defaults):
    if index < len(text) and text[index] == '(':
        end, params = parse_brackets(text, index)
        return [end] + get_params(params, num, defaults, False)
    pattern = PARAMS.format(INTEGER, num - 1)
    params = re.match(pattern, text[index:]).group()
    return [index + len(params)] + get_params(params, num, defaults)

def parse_ints(text, index, max_params):
    if index < len(text) and text[index] == '(':
        end, params = parse_brackets(text, index)
        if end is None:
            return None, None
        return end, f'({params})'
    pattern = PARAMS.format(f'([a-z]+=)?{INTEGER}', max_params - 1)
    params = re.match(pattern, text[index:]).group()
    return index + len(params), params

def parse_brackets(text, index, opening='(', closing=')'):
    if index >= len(text) or text[index] != opening:
        return None, None
    depth = 1
    end = index + 1
    while depth > 0:
        i = text.find(closing, end)
        if i < 0:
            return None, None
        depth += text.count(opening, end, i) - 1
        end = i + 1
    return end, text[index + 1:end - 1]

def parse_string(text, index):
    if index >= len(text) or text[index].isspace():
        return None, None
    delim1 = text[index]
    delim2 = DELIMITERS.get(delim1, delim1)
    if delim1 in DELIMITERS:
        end, param_string = parse_brackets(text, index, delim1, delim2)
    else:
        start = index + len(delim1)
        end = text.find(delim2, start)
        if end < start:
            return None, None
        param_string = text[start:end]
        end += len(delim2)
    return end, param_string

def _convert_audio(line):
    index = line.find('#AUDIO')
    while index >= 0:
        index2 = index + 6
        try:
            end, flags, offset = parse_ints_ex(line, index2, 2, (0, None))
        except InvalidParameterError:
            end, flags, offset = index2, 0, None
        end, fname = parse_brackets(line, end)
        if fname:
            sim = (flags & 4) // 4
            execint = flags & 2
            cmio = flags & 1 or ''
            if offset is None:
                offset = ''
            maf = flags & 8
            delays = ''
            if sim:
                end, sparams = parse_brackets(line, end)
                sparams += ',' * (3 - sparams.count(','))
                start, stop, execint2, cmio2 = sparams.split(',')
                params = f',{start},{stop}'
                try:
                    execint2 = evaluate(execint2)
                except ValueError:
                    execint2 = 0
                if execint == 0:
                    execint = execint2 or ''
                try:
                    cmio = evaluate(cmio2) or cmio
                except ValueError:
                    pass
            else:
                execint = (execint // 2) or ''
                params = ''
                start = stop = ''
                if len(line) > end and line[end] == '(':
                    end, delays = parse_brackets(line, end)
                    delays = f'({delays})'
            if maf:
                params = f',{start},{stop},{execint},{cmio},{offset},1'
            elif offset:
                params = f',{start},{stop},{execint},{cmio},{offset}'
            elif cmio:
                params = f',{start},{stop},{execint},1'
            elif execint:
                params = f',{start},{stop},{execint}'
            line = line.replace(line[index:end], f'#AUDIO{sim}{params}({fname}){delays}')
        index = line.find('#AUDIO', index2)
    return line

def _convert_call(line):
    index = line.find('#CALL:')
    while index >= 0:
        start = index + 6
        match = RE_METHOD_NAME.match(line, start)
        if match:
            method_name = match.group()
            end, m_args = parse_brackets(line, start + len(method_name))
            if end:
                line = line.replace(line[index:end], f'#CALL({method_name}({m_args}))')
        index = line.find('#CALL:', start)
    return line

def _convert_font(line):
    index = line.find('#FONT:')
    while index >= 0:
        start = index + 6
        end, msg = parse_string(line, start)
        if end:
            text = line[start:end]
            end, params = parse_ints(line, end, 6)
            if end:
                p = params.startswith('(')
                if '=' in params:
                    if 'chars=' in params:
                        params = re.sub(f'chars={INTEGER}', 'chars=0', params)
                    elif p:
                        params = params[:-1] + ',chars=0)'
                    else:
                        params += ',chars=0'
                else:
                    if p:
                        params_s = params[1:-1].split(',')
                    else:
                        params_s = params.split(',')
                    if len(params_s) == 1:
                        params_s.append('0')
                    else:
                        params_s[1] = '0'
                    params = ','.join(params_s)
                    if p:
                        params = f'({params})'
                line = line[:index] + f'#FONT{params}{text}' + line[end:]
        index = line.find('#FONT:', start)
    return line

def _convert_link(line):
    index = line.find('#LINK:')
    while index >= 0:
        start = index + 6
        match = RE_LINK_PARAMS.match(line, start)
        if match:
            param = match.group()
            end = match.end()
            end2, link_text = parse_brackets(line, end)
            if end2:
                line = line[:index] + f'#LINK({param})' + line[end:]
        index = line.find('#LINK:', start)
    return line

def _parse_frame_specs(text, index):
    end = index
    while end == index or (end < len(text) and text[end] == ';'):
        end += 1
        match = RE_FRAME_ID.match(text, end)
        if not match:
            return None, None
        end = match.end()
        if end < len(text) and text[end] == ',':
            end = parse_ints(text, end + 1, 3)[0]
    return end, text[index + 1:end]

def _convert_udgarray_frames(line):
    line = line.replace('#UDGARRAY*(', '#FRAMES(')
    index = line.find('#UDGARRAY*')
    while index >= 0:
        start = index + 9
        end, frame_specs = _parse_frame_specs(line, start)
        if end and end < len(line) and line[end] == '(':
            line = line[:index] + f'#FRAMES({frame_specs})' + line[end:]
        index = line.find('#UDGARRAY*', start)
    return line

def parse_address_range(text, index):
    elements = []
    end = index - 1
    while end < index or (len(elements) < 4 and end < len(text) and text[end] == '-'):
        start = end + 1
        end, param = parse_ints(text, start, 1)
        if end is None or end == start:
            return None
        elements.append(param)
    if end < len(text) and text[end] == 'x':
        end, param = parse_ints(text, end + 1, 1)
    return end

def _parse_udg_specs(text, index):
    end = index
    while end < 0 or (end < len(text) and text[end] == ';'):
        end = parse_address_range(text, end + 1)
        if end is None:
            break
        if end < len(text) and text[end] == ',':
            end, udg_params = parse_ints(text, end + 1, 3)
            if end is None:
                break
        if end < len(text) and text[end] == ':':
            end = parse_address_range(text, end + 1)
            if end is None:
                break
            if end < len(text) and text[end] == ',':
                end, mask_params = parse_ints(text, end + 1, 1)
                if end is None:
                    break
    if end is None:
        return None, None
    return end, text[index + 1:end]

def _get_udgs(text, index):
    if index < len(text) and text[index] == '(':
        end, udg_specs = parse_brackets(text, index)
    else:
        end, udg_specs = _parse_udg_specs(text, index)
    if end is None:
        return None, None, None
    attr_specs = ''
    if text[end:end + 1].startswith(('[', '@')):
        if text[end] == '[':
            end, attr_specs = parse_brackets(text, end, '[', ']')
        else:
            attrs_i = end + 1
            end = parse_address_range(text, attrs_i)
            if end is None:
                return None, None, None
            while end < len(text) and text[end] == ';':
                end = parse_address_range(text, end + 1)
                if end is None:
                    return None, None, None
            attr_specs = text[attrs_i:end]
    if attr_specs:
        attr_specs = f'[{attr_specs}]'
    return end, f'({udg_specs})', attr_specs

def _convert_udgarray(line):
    index = line.find('#UDGARRAY')
    while index >= 0:
        start = index + 9
        if start < len(line) and line[start] not in '*#':
            end, params = parse_ints(line, start, 6)
            if end:
                end, udg_specs, attr_specs = _get_udgs(line, end)
                if end and end < len(line) and line[end] in '{(':
                    line = line[:index] + f'#UDGARRAY{params}{udg_specs}{attr_specs}' + line[end:]
        index = line.find('#UDGARRAY', start)
    return line

def convert(f):
    count = 0
    for line in f:
        o_line = line
        line = _convert_audio(line)
        line = _convert_call(line)
        line = _convert_font(line)
        line = _convert_link(line)
        line = _convert_udgarray_frames(line)
        line = _convert_udgarray(line)
        if o_line != line:
            sys.stderr.write(f'< {o_line}')
            sys.stderr.write(f'> {line}\n')
            count += 1
        sys.stdout.write(line)
    sys.stderr.write(f'{count} line(s) changed\n')

def main(args):
    parser = argparse.ArgumentParser(
        usage='skoolkit9to10.py FILE',
        description="Convert a skool file, control file or ref file from SkoolKit 9 format "
                    "to SkoolKit 10 format and print it on standard output.",
        add_help=False
    )
    parser.add_argument('infile', help=argparse.SUPPRESS, nargs='?')
    namespace, unknown_args = parser.parse_known_args(args)
    infile = namespace.infile
    if unknown_args or infile is None:
        parser.exit(2, parser.format_help())
    with open(infile) as f:
        convert(f)

if __name__ == '__main__':
    main(sys.argv[1:])
