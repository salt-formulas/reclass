#
# -*- coding: utf-8 -*-
#
# This file is part of reclass
#

from reclass.settings import Settings
from item import Item

class ScaItem(Item):

    def __init__(self, value, settings):
        self.type = Item.SCALAR
        self._value = value
        self._settings = settings

    def contents(self):
        return self._value

    def merge_over(self, item):
        if item.type == Item.SCALAR:
            return self
        elif item.type == Item.LIST:
            if self._settings.allow_scalar_over_list:
                return self
            else:
                raise TypeError('allow scalar over list = False: cannot merge %s over %s' % (repr(self), repr(item)))
        elif item.type == Item.DICTIONARY:
            if self._settings.allow_scalar_over_dict:
                return self
            else:
                raise TypeError('allow scalar over dict = False: cannot merge %s over %s' % (repr(self), repr(item)))
        raise TypeError('Cannot merge %s over %s' % (repr(self), repr(item)))

    def render(self, context, inventory):
        return self._value

    def __repr__(self):
        return 'ScaItem({0!r})'.format(self._value)
