#
# -*- coding: utf-8 -*-
#
# This file is part of reclass
#

import pyparsing as pp

STR = 1
REF = 2
INV = 3

def _string(string, location, tokens):
    token = tokens[0]
    tokens[0] = (STR, token)

def _reference(string, location, tokens):
    token = list(tokens[0])
    tokens[0] = (REF, token)

def _invquery(string, location, tokens):
    token = list(tokens[0])
    tokens[0] = (INV, token)

def get_ref_parser(escape_character, reference_sentinels, export_sentinels):
    _ESCAPE = escape_character
    _DOUBLE_ESCAPE = _ESCAPE + _ESCAPE

    _REF_OPEN = reference_sentinels[0]
    _REF_CLOSE = reference_sentinels[1]
    _REF_CLOSE_FIRST = _REF_CLOSE[0]
    _REF_ESCAPE_OPEN = _ESCAPE + _REF_OPEN
    _REF_ESCAPE_CLOSE = _ESCAPE + _REF_CLOSE
    _REF_DOUBLE_ESCAPE_OPEN = _DOUBLE_ESCAPE + _REF_OPEN
    _REF_DOUBLE_ESCAPE_CLOSE = _DOUBLE_ESCAPE + _REF_CLOSE
    _REF_EXCLUDES = _ESCAPE + _REF_OPEN + _REF_CLOSE

    _INV_OPEN = export_sentinels[0]
    _INV_CLOSE = export_sentinels[1]
    _INV_CLOSE_FIRST = _INV_CLOSE[0]
    _INV_ESCAPE_OPEN = _ESCAPE + _INV_OPEN
    _INV_ESCAPE_CLOSE = _ESCAPE + _INV_CLOSE
    _INV_DOUBLE_ESCAPE_OPEN = _DOUBLE_ESCAPE + _INV_OPEN
    _INV_DOUBLE_ESCAPE_CLOSE = _DOUBLE_ESCAPE + _INV_CLOSE
    _INV_EXCLUDES = _ESCAPE + _INV_OPEN + _INV_CLOSE

    _EXCLUDES = _ESCAPE + _REF_OPEN + _REF_CLOSE + _INV_OPEN + _INV_CLOSE

    double_escape = pp.Combine(pp.Literal(_DOUBLE_ESCAPE) + pp.MatchFirst([pp.FollowedBy(_REF_OPEN), pp.FollowedBy(_REF_CLOSE),
                               pp.FollowedBy(_INV_OPEN), pp.FollowedBy(_INV_CLOSE)])).setParseAction(pp.replaceWith(_ESCAPE))

    ref_open = pp.Literal(_REF_OPEN).suppress()
    ref_close = pp.Literal(_REF_CLOSE).suppress()
    ref_not_open = ~pp.Literal(_REF_OPEN) + ~pp.Literal(_REF_ESCAPE_OPEN) + ~pp.Literal(_REF_DOUBLE_ESCAPE_OPEN)
    ref_not_close = ~pp.Literal(_REF_CLOSE) + ~pp.Literal(_REF_ESCAPE_CLOSE) + ~pp.Literal(_REF_DOUBLE_ESCAPE_CLOSE)
    ref_escape_open = pp.Literal(_REF_ESCAPE_OPEN).setParseAction(pp.replaceWith(_REF_OPEN))
    ref_escape_close = pp.Literal(_REF_ESCAPE_CLOSE).setParseAction(pp.replaceWith(_REF_CLOSE))
    ref_text = pp.CharsNotIn(_REF_EXCLUDES) | pp.CharsNotIn(_REF_CLOSE_FIRST, exact=1)
    ref_content = pp.Combine(pp.OneOrMore(ref_not_open + ref_not_close + ref_text))
    ref_string = pp.MatchFirst([double_escape, ref_escape_open, ref_escape_close, ref_content]).setParseAction(_string)
    ref_item = pp.Forward()
    ref_items = pp.OneOrMore(ref_item)
    reference = (ref_open + pp.Group(ref_items) + ref_close).setParseAction(_reference)
    ref_item << (reference | ref_string)

    inv_open = pp.Literal(_INV_OPEN).suppress()
    inv_close = pp.Literal(_INV_CLOSE).suppress()
    inv_not_open = ~pp.Literal(_INV_OPEN) + ~pp.Literal(_INV_ESCAPE_OPEN) + ~pp.Literal(_INV_DOUBLE_ESCAPE_OPEN)
    inv_not_close = ~pp.Literal(_INV_CLOSE) + ~pp.Literal(_INV_ESCAPE_CLOSE) + ~pp.Literal(_INV_DOUBLE_ESCAPE_CLOSE)
    inv_escape_open = pp.Literal(_INV_ESCAPE_OPEN).setParseAction(pp.replaceWith(_INV_OPEN))
    inv_escape_close = pp.Literal(_INV_ESCAPE_CLOSE).setParseAction(pp.replaceWith(_INV_CLOSE))
    inv_text = pp.CharsNotIn(_INV_CLOSE_FIRST)
    inv_content = pp.Combine(pp.OneOrMore(inv_not_close + inv_text))
    inv_string = pp.MatchFirst([double_escape, inv_escape_open, inv_escape_close, inv_content]).setParseAction(_string)
    inv_items = pp.OneOrMore(inv_string)
    export = (inv_open + pp.Group(inv_items) + inv_close).setParseAction(_invquery)

    text = pp.CharsNotIn(_EXCLUDES) | pp.CharsNotIn('', exact=1)
    content = pp.Combine(pp.OneOrMore(ref_not_open + inv_not_open + text))
    string = pp.MatchFirst([double_escape, ref_escape_open, inv_escape_open, content]).setParseAction(_string)

    item = reference | export | string
    line = pp.OneOrMore(item) + pp.StringEnd()
    return line

def get_simple_ref_parser(escape_character, reference_sentinels, export_sentinels):
    _ESCAPE = escape_character
    _REF_OPEN = reference_sentinels[0]
    _REF_CLOSE = reference_sentinels[1]
    _INV_OPEN = export_sentinels[0]
    _INV_CLOSE = export_sentinels[1]
    _EXCLUDES = _ESCAPE + _REF_OPEN + _REF_CLOSE + _INV_OPEN + _INV_CLOSE

    string = pp.CharsNotIn(_EXCLUDES).setParseAction(_string)
    ref_open = pp.Literal(_REF_OPEN).suppress()
    ref_close = pp.Literal(_REF_CLOSE).suppress()
    reference = (ref_open + pp.Group(string) + ref_close).setParseAction(_reference)
    line = pp.StringStart() + pp.Optional(string) + reference + pp.Optional(string) + pp.StringEnd()
    return line
