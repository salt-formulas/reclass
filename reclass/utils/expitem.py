#
# -*- coding: utf-8 -*-
#
# This file is part of reclass
#

from reclass.utils.dictpath import DictPath
from reclass.utils.item import Item
from reclass.errors import UndefinedVariableError

class ExpItem(Item):

    def __init__(self, items, delimiter):
        self._delimiter = delimiter
        self._items = items

    def contents(self):
        return self._items

    def has_exports(self):
        return True

    def _resolve(self, path, key, dictionary):
        try:
            return path.get_value(dictionary)
        except KeyError as e:
            raise UndefinedVariableError(key)

    def _key(self):
        if len(self._items) == 1:
            return self._items[0].contents()
        string = ''
        for item in self._items:
            string += item.contents()
        return string

    def render(self, context, exports):
        result = []
        exp_key = self._key()
        exp_path = DictPath(self._delimiter, exp_key)
        exp_path.drop_first()
        for node, items in exports.iteritems():
            if exp_path.exists_in(items):
                result.append(self._resolve(exp_path, exp_key, items))
        return result

    def __repr__(self):
        return 'ExpItem(%r)' % self._items
