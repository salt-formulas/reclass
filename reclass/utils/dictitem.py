#
# -*- coding: utf-8 -*-
#
# This file is part of reclass
#

from reclass.utils.item import Item

class DictItem(Item):

    def __init__(self, item):
        self._dict = item

    def contents(self):
        return self._dict

    def merge_over(self, item, options):
        from reclass.utils.scaitem import ScaItem

        if isinstance(item, ScaItem):
            if item.contents() is None or options.allow_dict_over_scalar:
                return self
            else:
                raise TypeError('allow dict over scalar = False: cannot merge %s onto %s' % (repr(self), repr(item)))
        raise TypeError('Cannot merge %s over %s' % (repr(self), repr(item)))

    def render(self, context, exports):
        return self._dict

    def __repr__(self):
        return 'DictItem(%r)' % self._dict
