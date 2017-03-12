#
# -*- coding: utf-8 -*-
#
# This file is part of reclass
#

import pyparsing as pp

from reclass.utils.mergeoptions import MergeOptions
from reclass.utils.compitem import CompItem
from reclass.utils.dictitem import DictItem
from reclass.utils.listitem import ListItem
from reclass.utils.refitem import RefItem
from reclass.utils.scaitem import ScaItem
from reclass.defaults import PARAMETER_INTERPOLATION_DELIMITER, PARAMETER_INTERPOLATION_SENTINELS, ESCAPE_CHARACTER
from reclass.errors import *


_STR = 'STR'
_REF = 'REF'
_OPEN = PARAMETER_INTERPOLATION_SENTINELS[0]
_CLOSE = PARAMETER_INTERPOLATION_SENTINELS[1]
_CLOSE_FIRST = _CLOSE[0]
_ESCAPE = ESCAPE_CHARACTER
_DOUBLE_ESCAPE = _ESCAPE + _ESCAPE
_ESCAPE_OPEN = _ESCAPE + _OPEN
_ESCAPE_CLOSE = _ESCAPE + _CLOSE
_DOUBLE_ESCAPE_OPEN = _DOUBLE_ESCAPE + _OPEN
_DOUBLE_ESCAPE_CLOSE = _DOUBLE_ESCAPE + _CLOSE
_EXCLUDES = _ESCAPE + _OPEN + _CLOSE


class Value(object):

    def _getParser():

        def _string(string, location, tokens):
            token = tokens[0]
            tokens[0] = (_STR, token)

        def _reference(string, location, tokens):
            token = list(tokens[0])
            tokens[0] = (_REF, token)

        ref_open = pp.Literal(_OPEN).suppress()
        ref_close = pp.Literal(_CLOSE).suppress()
        not_open = ~pp.Literal(_OPEN) + ~pp.Literal(_ESCAPE_OPEN) + ~pp.Literal(_DOUBLE_ESCAPE_OPEN)
        not_close = ~pp.Literal(_CLOSE) + ~pp.Literal(_ESCAPE_CLOSE) + ~pp.Literal(_DOUBLE_ESCAPE_CLOSE)
        escape_open = pp.Literal(_ESCAPE_OPEN).setParseAction(pp.replaceWith(_OPEN))
        escape_close = pp.Literal(_ESCAPE_CLOSE).setParseAction(pp.replaceWith(_CLOSE))
        double_escape = pp.Combine(pp.Literal(_DOUBLE_ESCAPE) + pp.MatchFirst([pp.FollowedBy(_OPEN), pp.FollowedBy(_CLOSE)])).setParseAction(pp.replaceWith(_ESCAPE))
        text = pp.MatchFirst([pp.Word(pp.printables, excludeChars=_EXCLUDES), pp.CharsNotIn('', exact=1)])
        text_ref = pp.MatchFirst([pp.Word(pp.printables, excludeChars=_EXCLUDES), pp.CharsNotIn(_CLOSE_FIRST, exact=1)])
        white_space = pp.White()

        content = pp.Combine(pp.OneOrMore(not_open + text))
        ref_content = pp.Combine(pp.OneOrMore(not_open + not_close + text_ref))
        string = pp.MatchFirst([double_escape, escape_open, content, white_space]).setParseAction(_string)
        refString = pp.MatchFirst([double_escape, escape_open, escape_close, ref_content, white_space]).setParseAction(_string)

        refItem = pp.Forward()
        refItems = pp.OneOrMore(refItem)
        reference = (ref_open + pp.Group(refItems) + ref_close).setParseAction(_reference)
        refItem << (reference | refString)

        item = reference | string
        line = pp.OneOrMore(item) + pp.StringEnd()
        return line

    _parser = _getParser()

    def __init__(self, val, delimiter=PARAMETER_INTERPOLATION_DELIMITER):
        self._delimiter = delimiter
        self._refs = []
        self._allRefs = False
        self._container = False
        if isinstance(val, str):
            try:
                tokens = Value._parser.leaveWhitespace().parseString(val).asList()
            except pp.ParseException as e:
                raise ParseError(e.msg, e.line, e.col, e.lineno)
            items = self._createItems(tokens)
            if len(items) is 1:
                self._item = items[0]
            else:
                self._item = CompItem(items)
        elif isinstance(val, list):
            self._item = ListItem(val)
            self._container = True
        elif isinstance(val, dict):
            self._item = DictItem(val)
            self._container = True
        else:
            self._item = ScaItem(val)
        self.assembleRefs()

    def _createRef(self, tokens):
        items = []
        for token in tokens:
            if token[0] == _STR:
                items.append(ScaItem(token[1]))
            elif token[0] == _REF:
                items.append(self._createRef(token[1]))
        return RefItem(items, self._delimiter)

    def _createItems(self, tokens):
        items = []
        for token in tokens:
            if token[0] == _STR:
                items.append(ScaItem(token[1]))
            elif token[0] == _REF:
                items.append(self._createRef(token[1]))
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

    def get_references(self):
        return self._refs

    def render(self, context, dummy=None):
        return self._item.render(context)

    def contents(self):
        return self._item.contents()

    def merge_over(self, value, options):
        self._item = self._item.merge_over(value._item, options)
        return self

    def __repr__(self):
        return 'Value(%r)' % self._item
