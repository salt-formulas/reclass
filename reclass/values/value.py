#
# -*- coding: utf-8 -*-
#
# This file is part of reclass
#

import pyparsing as pp

from mergeoptions import MergeOptions
from compitem import CompItem
from dictitem import DictItem
from expitem import ExpItem
from listitem import ListItem
from refitem import RefItem
from scaitem import ScaItem
from reclass.defaults import PARAMETER_INTERPOLATION_DELIMITER, ESCAPE_CHARACTER, REFERENCE_SENTINELS, EXPORT_SENTINELS
from reclass.errors import *

_STR = 'STR'
_REF = 'REF'
_EXP = 'EXP'

_ESCAPE = ESCAPE_CHARACTER
_DOUBLE_ESCAPE = _ESCAPE + _ESCAPE

_REF_OPEN = REFERENCE_SENTINELS[0]
_REF_CLOSE = REFERENCE_SENTINELS[1]
_REF_CLOSE_FIRST = _REF_CLOSE[0]
_REF_ESCAPE_OPEN = _ESCAPE + _REF_OPEN
_REF_ESCAPE_CLOSE = _ESCAPE + _REF_CLOSE
_REF_DOUBLE_ESCAPE_OPEN = _DOUBLE_ESCAPE + _REF_OPEN
_REF_DOUBLE_ESCAPE_CLOSE = _DOUBLE_ESCAPE + _REF_CLOSE
_REF_EXCLUDES = _ESCAPE + _REF_OPEN + _REF_CLOSE

_EXP_OPEN = EXPORT_SENTINELS[0]
_EXP_CLOSE = EXPORT_SENTINELS[1]
_EXP_CLOSE_FIRST = _EXP_CLOSE[0]
_EXP_ESCAPE_OPEN = _ESCAPE + _EXP_OPEN
_EXP_ESCAPE_CLOSE = _ESCAPE + _EXP_CLOSE
_EXP_DOUBLE_ESCAPE_OPEN = _DOUBLE_ESCAPE + _EXP_OPEN
_EXP_DOUBLE_ESCAPE_CLOSE = _DOUBLE_ESCAPE + _EXP_CLOSE
_EXP_EXCLUDES = _ESCAPE + _EXP_OPEN + _EXP_CLOSE

_EXCLUDES = _ESCAPE + _REF_OPEN + _REF_CLOSE + _EXP_OPEN + _EXP_CLOSE

def _string(string, location, tokens):
    token = tokens[0]
    tokens[0] = (_STR, token)

def _reference(string, location, tokens):
    token = list(tokens[0])
    tokens[0] = (_REF, token)

def _export(string, location, tokens):
    token = list(tokens[0])
    tokens[0] = (_EXP, token)

def _get_parser():
    white_space = pp.White()
    double_escape = pp.Combine(pp.Literal(_DOUBLE_ESCAPE) + pp.MatchFirst([pp.FollowedBy(_REF_OPEN), pp.FollowedBy(_REF_CLOSE)])).setParseAction(pp.replaceWith(_ESCAPE))

    ref_open = pp.Literal(_REF_OPEN).suppress()
    ref_close = pp.Literal(_REF_CLOSE).suppress()
    ref_not_open = ~pp.Literal(_REF_OPEN) + ~pp.Literal(_REF_ESCAPE_OPEN) + ~pp.Literal(_REF_DOUBLE_ESCAPE_OPEN)
    ref_not_close = ~pp.Literal(_REF_CLOSE) + ~pp.Literal(_REF_ESCAPE_CLOSE) + ~pp.Literal(_REF_DOUBLE_ESCAPE_CLOSE)
    ref_escape_open = pp.Literal(_REF_ESCAPE_OPEN).setParseAction(pp.replaceWith(_REF_OPEN))
    ref_escape_close = pp.Literal(_REF_ESCAPE_CLOSE).setParseAction(pp.replaceWith(_REF_CLOSE))
    ref_text = pp.MatchFirst([pp.Word(pp.printables, excludeChars=_REF_EXCLUDES), pp.CharsNotIn(_REF_CLOSE_FIRST, exact=1)])
    ref_content = pp.Combine(pp.OneOrMore(ref_not_open + ref_not_close + ref_text))
    ref_string = pp.MatchFirst([double_escape, ref_escape_open, ref_escape_close, ref_content, white_space]).setParseAction(_string)
    ref_item = pp.Forward()
    ref_items = pp.OneOrMore(ref_item)
    reference = (ref_open + pp.Group(ref_items) + ref_close).setParseAction(_reference)
    ref_item << (reference | ref_string)

    exp_open = pp.Literal(_EXP_OPEN).suppress()
    exp_close = pp.Literal(_EXP_CLOSE).suppress()
    exp_not_open = ~pp.Literal(_EXP_OPEN) + ~pp.Literal(_EXP_ESCAPE_OPEN) + ~pp.Literal(_EXP_DOUBLE_ESCAPE_OPEN)
    exp_not_close = ~pp.Literal(_EXP_CLOSE) + ~pp.Literal(_EXP_ESCAPE_CLOSE) + ~pp.Literal(_EXP_DOUBLE_ESCAPE_CLOSE)
    exp_escape_open = pp.Literal(_EXP_ESCAPE_OPEN).setParseAction(pp.replaceWith(_EXP_OPEN))
    exp_escape_close = pp.Literal(_EXP_ESCAPE_CLOSE).setParseAction(pp.replaceWith(_EXP_CLOSE))
    exp_text = pp.Word(pp.printables, excludeChars=_EXP_CLOSE_FIRST)
    exp_content = pp.Combine(pp.OneOrMore(exp_not_close + exp_text))
    exp_string = pp.MatchFirst([double_escape, exp_escape_open, exp_escape_close, exp_content, white_space]).setParseAction(_string)
    exp_items = pp.OneOrMore(exp_string)
    export = (exp_open + pp.Group(exp_items) + exp_close).setParseAction(_export)

    text = pp.MatchFirst([pp.Word(pp.printables, excludeChars=_EXCLUDES), pp.CharsNotIn('', exact=1)])
    content = pp.Combine(pp.OneOrMore(ref_not_open + exp_not_open + text))
    string = pp.MatchFirst([double_escape, ref_escape_open, exp_escape_open, content, white_space]).setParseAction(_string)

    item = reference | export | string
    line = pp.OneOrMore(item) + pp.StringEnd()
    return line

def _get_simple_ref_parser():
    white_space = pp.White()
    text = pp.Word(pp.printables, excludeChars=_EXCLUDES)
    string = pp.OneOrMore(text | white_space).setParseAction(_string)

    ref_open = pp.Literal(_REF_OPEN).suppress()
    ref_close = pp.Literal(_REF_CLOSE).suppress()
    reference = (ref_open + pp.Group(string) + ref_close).setParseAction(_reference)

    line = pp.StringStart() + reference + pp.StringEnd()
    return line

class Value(object):

    _parser = _get_parser()
    _simple_ref_parser = _get_simple_ref_parser()

    def __init__(self, val, delimiter=PARAMETER_INTERPOLATION_DELIMITER):
        self._delimiter = delimiter
        self._refs = []
        self._allRefs = False
        self._container = False
        if isinstance(val, str):
            self._item = self._parse_value_str(val)
        elif isinstance(val, list):
            self._item = ListItem(val)
            self._container = True
        elif isinstance(val, dict):
            self._item = DictItem(val)
            self._container = True
        else:
            self._item = ScaItem(val)
        self.assembleRefs()

    def _parse_value_str(self, val):
        dollars = val.count('$')
        if dollars == 0:
            # speed up: only use pyparsing if there is a $ in the string
            return ScaItem(val)
        elif dollars == 1:
            # speed up: try a simple reference
            try:
                tokens = Value._simple_ref_parser.leaveWhitespace().parseString(val).asList()
            except pp.ParseException as e:
                # fall back on the full parser
                try:
                    tokens = Value._parser.leaveWhitespace().parseString(val).asList()
                except pp.ParseException as e:
                    raise ParseError(e.msg, e.line, e.col, e.lineno)
        else:
            # use the full parser
            try:
                tokens = Value._parser.leaveWhitespace().parseString(val).asList()
            except pp.ParseException as e:
                raise ParseError(e.msg, e.line, e.col, e.lineno)

        items = self._createItems(tokens)
        if len(items) == 1:
            return items[0]
        else:
            return CompItem(items)

    def _createRef(self, tokens):
        items = []
        for token in tokens:
            if token[0] == _STR:
                items.append(ScaItem(token[1]))
            elif token[0] == _REF:
                items.append(self._createRef(token[1]))
        return RefItem(items, self._delimiter)

    def _createExp(self, tokens):
        items = []
        for token in tokens:
            items.append(ScaItem(token[1]))
        if len(items) == 1:
            return ExpItem(items[0], self._delimiter)
        else:
            return ExpItem(CompItem(items), self._delimiter)

    def _createItems(self, tokens):
        items = []
        for token in tokens:
            if token[0] == _STR:
                items.append(ScaItem(token[1]))
            elif token[0] == _REF:
                items.append(self._createRef(token[1]))
            elif token[0] == _EXP:
                items.append(self._createExp(token[1]))
        return items

    def assembleRefs(self, context={}):
        if self._item.has_references():
            self._item.assembleRefs(context)
            self._refs = self._item.get_references()
            self._allRefs = self._item.allRefs()
        else:
            self._refs = []
            self._allRefs = True

    def is_container(self):
        return self._container

    def allRefs(self):
        return self._allRefs

    def has_references(self):
        return len(self._refs) > 0

    def has_exports(self):
        return self._item.has_exports()

    def is_complex(self):
        return (self.has_references() | self.has_exports())

    def get_references(self):
        return self._refs

    def render(self, context, exports, dummy=None):
        return self._item.render(context, exports)

    def contents(self):
        return self._item.contents()

    def merge_over(self, value, options):
        self._item = self._item.merge_over(value._item, options)
        return self

    def __repr__(self):
        return 'Value(%r)' % self._item
