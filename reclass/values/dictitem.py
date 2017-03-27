#
# -*- coding: utf-8 -*-
#
# This file is part of reclass
#

from item import Item

class DictItem(Item):

    def __init__(self, item):
        self.type = Item.DICTIONARY
        self._dict = item

    def contents(self):
        return self._dict

    def is_container(self):
        return True

    def merge_over(self, item, options):
        if item.type == Item.SCALAR:
            if item.contents() is None or options.allow_dict_over_scalar:
                return self
            else:
                raise TypeError('allow dict over scalar = False: cannot merge %s onto %s' % (repr(self), repr(item)))
        raise TypeError('Cannot merge %s over %s' % (repr(self), repr(item)))

    def render(self, context, inventory):
        return self._dict

    def __repr__(self):
        return 'DictItem(%r)' % self._dict
