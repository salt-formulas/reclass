#
# -*- coding: utf-8 -*-
#
# This file is part of reclass
#

import copy

from item import Item
from reclass.utils.dictpath import DictPath
from reclass.errors import UndefinedVariableError

class ExpItem(Item):

    def __init__(self, item, delimiter):
        self._delimiter = delimiter
        self._expr = item.render(None, None)

    def contents(self):
        return self._expr

    def has_exports(self):
        return True

    def _resolve(self, path, dictionary):
        try:
            return path.get_value(dictionary)
        except KeyError as e:
            raise UndefinedVariableError(str(path))

    def render(self, context, exports):
        result = []
        exp_path = DictPath(self._delimiter, self._expr)
        exp_path.drop_first()
        for node, items in exports.iteritems():
            if exp_path.exists_in(items):
                value = { node: copy.deepcopy(self._resolve(exp_path, items)) }
                result.append(value)
        return result

    def __repr__(self):
        return 'ExpItem(%r)' % self._items
