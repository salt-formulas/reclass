#
# -*- coding: utf-8 -*-
#
# This file is part of reclass
#

from reclass.utils.dictitem import DictItem
from reclass.utils.listitem import ListItem
from reclass.utils.item import Item

class ScaItem(Item):

    def __init__(self, value):
        self._value = value

    def contents(self):
        return self._value

    def merge_over(self, item, options):
        if isinstance(item, ScaItem):
            return self
        elif isinstance(item, ListItem):
            if options.allow_scalar_over_list:
                return self
            else:
                raise TypeError('allow scalar over list = False: cannot merge %s over %s' % (repr(self), repr(item)))
        elif isinstance(item, DictItem):
            if options.allow_scalar_over_dict:
                return self
            else:
                raise TypeError('allow scalar over dict = False: cannot merge %s over %s' % (repr(self), repr(item)))
        raise TypeError('Cannot merge %s over %s' % (repr(self), repr(item)))

    def render(self, context, exports):
        return self._value

    def __repr__(self):
        return 'ScaItem({0!r})'.format(self._value)
