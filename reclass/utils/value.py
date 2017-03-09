#
# -*- coding: utf-8 -*-
#
# This file is part of reclass
#

import pyparsing as pp

from reclass.utils.mergeoptions import *
from reclass.utils.dictitem import *
from reclass.utils.listitem import *
from reclass.utils.refitem import *
from reclass.utils.scaitem import *
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
        self._items = []
        self._refs = []
        self._allRefs = False
        self._container = False
        if isinstance(val, str):
            tokens = Value._parser.leaveWhitespace().parseString(val).asList()
            self._items = self._createItems(tokens)
        elif isinstance(val, list):
            self._items.append(ListItem(val))
            self._container = True
        elif isinstance(val, dict):
            self._items.append(DictItem(val))
            self._container = True
        else:
            self._items.append(ScaItem(val))
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
        self._refs = []
        self._allRefs = True
        for item in self._items:
            if item.has_references():
                item.assembleRefs(context)
                self._refs.extend(item.get_references())
            if item.allRefs() is False:
                self._allRefs = False

    def is_container(self):
        return self._container

    def allRefs(self):
        return self._allRefs

    def has_references(self):
        return len(self._refs) > 0

    def get_references(self):
        return self._refs

    def render(self, context, options=None):
        if options is None:
            options = MergeOptions()
        if len(self._items) == 1:
            return self._items[0].render(context, options)
        value = ''
        for item in self._items:
            value += str(item.render(context, options))
        return value

    def contents(self):
        if len(self._items) == 1:
            return self._items[0].contents()
        value = ''
        for item in self._items:
            value += str(item.contents())
        return value

    def merge_over(self, value, options):
        if len(self._items) is 1 and len(value._items) is 1:
            self._items[0] = self._items[0].merge_over(value._items[0], options)
            return self
        raise TypeError('Cannot merge %s onto %s' % (repr(self), repr(value)))

    def __repr__(self):
        return 'Value(%r)' % self._items
