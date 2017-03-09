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
from reclass.defaults import PARAMETER_INTERPOLATION_DELIMITER, PARAMETER_INTERPOLATION_SENTINELS

_STR = 'STR'
_REF = 'REF'

class Value(object):

    def _getParser():

        def _string(string, location, tokens):
            token = tokens[0]
            tokens[0] = (_STR, token)

        def _reference(string, location, tokens):
            token = list(tokens[0])
            tokens[0] = (_REF, token)

        string = (pp.Literal('\\\\').setParseAction(pp.replaceWith('\\')) |
                  pp.Literal('\\$').setParseAction(pp.replaceWith('$')) |
                  pp.White() |
                  pp.Word(pp.printables, excludeChars='\\$')).setParseAction(_string)

        refString = (pp.Literal('\\\\').setParseAction(pp.replaceWith('\\')) |
                     pp.Literal('\\$').setParseAction(pp.replaceWith('$')) |
                     pp.Literal('\\{').setParseAction(pp.replaceWith('{')) |
                     pp.Literal('\\}').setParseAction(pp.replaceWith('}')) |
                     pp.White() |
                     pp.Word(pp.printables, excludeChars='\\${}')).setParseAction(_string)

        refItem = pp.Forward()
        refItems = pp.OneOrMore(refItem)
        reference = (pp.Literal(PARAMETER_INTERPOLATION_SENTINELS[0]).suppress() +
                     pp.Group(refItems) +
                     pp.Literal(PARAMETER_INTERPOLATION_SENTINELS[1]).suppress()).setParseAction(_reference)
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
            tokens = Value._parser.leaveWhitespace().parseString(val).asList()
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
