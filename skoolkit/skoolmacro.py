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

from . import parse_int, SkoolKitError

def parse_ints(text, index, num, defaults=()):
    """Parse a string of comma-separated integer parameters. The string will be
    parsed until either the end of the text is reached, or some character other
    than one of ``$0123456789abcdefABCDEF`` is encountered.

    :param text: The text to parse.
    :param index: The index at which to start parsing.
    :param num: The maximum number of parameters to parse.
    :param defaults: The default values of the optional parameters.
    :return: A list of the form ``[end, value1, value2...]``, where ``end``
             is the index at which parsing terminated, and ``value1``,
             ``value2`` etc. are the parameter values.
    """
    end = index
    num_params = 1
    while end < len(text) and text[end] in '$0123456789abcdefABCDEF,':
        if text[end] == ',':
            if num_params == num:
                break
            num_params += 1
        end += 1
    params = get_params(text[index:end], num, defaults, True)
    return [end] + params

def parse_params(text, index, p_text=None, chars=''):
    """Parse a string of the form ``params[(p_text)]``. The parameter string
    ``params`` will be parsed until either the end of the text is reached, or
    an invalid character is encountered.

    :param text: The text to parse.
    :param index: The index at which to start parsing.
    :param p_text: The default value to use for text found in parentheses.
    :param chars: Characters to consider valid in the parameter string in
                  addition to '$', '#', the digits 0-9, and the letters A-Z and
                  a-z.
    :return: A 3-tuple of the form ``(end, params, p_text)``, where ``end``
             is the index at which parsing terminated (because either an
             invalid character or the end of the text was encountered),
             ``params`` is the parameter string, and ``p_text`` is the text
             found in parentheses (if any).
    """
    start = index
    valid_chars = '$#' + chars
    while index < len(text) and (text[index].isalnum() or text[index] in valid_chars):
        index += 1
    params = text[start:index]
    end = index
    if index < len(text) and text[index] == '(':
        depth = 1
        end += 1
        while end < len(text) and depth > 0:
            if text[end] == ')':
                depth -= 1
            elif text[end] == '(':
                depth += 1
            end += 1
        p_text = text[index + 1:end - 1]
    return end, params, p_text

def get_params(param_string, num=0, defaults=(), ints_only=False):
    params = []
    if param_string:
        for p in param_string.split(','):
            if p:
                param = parse_int(p)
                if param is None:
                    if ints_only:
                        raise MacroParsingError("Cannot parse integer '{0}' in macro parameter list: '{1}'".format(p, param_string))
                    params.append(p)
                else:
                    params.append(param)
            else:
                params.append(None)
    req = num - len(defaults)
    if len(params) < req:
        raise MacroParsingError("Not enough parameters (expected {0}): '{1}'".format(req, param_string))
    params += [None] * (num - len(params))
    for i in range(req, num):
        if params[i] is None:
            params[i] = defaults[i - req]
    return params

class UnsupportedMacroError(SkoolKitError):
    pass

class MacroParsingError(SkoolKitError):
    pass
