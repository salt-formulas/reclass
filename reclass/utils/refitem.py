#
# -*- coding: utf-8 -*-
#
# This file is part of reclass
#

from reclass.utils.dictpath import DictPath
from reclass.utils.item import Item
from reclass.errors import UndefinedVariableError

class RefItem(Item):

    def __init__(self, items, delimiter):
        self._delimiter = delimiter
        self._items = items
        self._refs = []
        self._allRefs = False
        self.assembleRefs()

    def assembleRefs(self, context={}):
        self._refs = []
        self._allRefs = True
        value = ''
        for item in self._items:
            if item.has_references():
                item.assembleRefs(context)
                self._refs.extend(item.get_references())
            try:
                value += str(item.render(context, None))
            except UndefinedVariableError as e:
                self._allRefs = False
        if self._allRefs:
            self._refs.append(value)

    def contents(self):
        return self._items

    def allRefs(self):
        return self._allRefs

    def has_references(self):
        return len(self._refs) > 0

    def get_references(self):
        return self._refs

    def _resolve(self, ref, context):
        path = DictPath(self._delimiter, ref)
        try:
            return path.get_value(context)
        except KeyError as e:
            raise UndefinedVariableError(ref)

    def render(self, context, exports):
        if len(self._items) == 1:
            return self._resolve(self._items[0].render(context, exports), context)
        string = ''
        for item in self._items:
            string += str(item.render(context, exports))
        return self._resolve(string, context)

    def __repr__(self):
        return 'RefItem(%r)' % self._items
