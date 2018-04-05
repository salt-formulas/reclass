#
# -*- coding: utf-8 -*-
#
# This file is part of reclass
#

from reclass.settings import Settings
from .item import Item

class DictItem(Item):

    def __init__(self, item, settings):
        self.type = Item.DICTIONARY
        self._dict = item
        self._settings = settings

    def contents(self):
        return self._dict

    def is_container(self):
        return True

    def merge_over(self, item):
        if item.type == Item.SCALAR:
            if item.contents() is None or self._settings.allow_dict_over_scalar:
                return self
            else:
                raise TypeError('allow dict over scalar = False: cannot merge %s onto %s' % (repr(self), repr(item)))
        raise TypeError('Cannot merge %s over %s' % (repr(self), repr(item)))

    def render(self, context, inventory):
        return self._dict

    def __repr__(self):
        return 'DictItem(%r)' % self._dict
