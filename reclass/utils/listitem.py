#
# -*- coding: utf-8 -*-
#
# This file is part of reclass
#

from reclass.utils.item import Item

class ListItem(Item):

    def __init__(self, item):
        self._list = item

    def contents(self):
        return self._list

    def render(self, context, exports):
        return self._list

    def merge_over(self, item, options):
        from reclass.utils.scaitem import ScaItem

        if isinstance(item, ListItem):
            for i in self._list:
                item._list.append(i)
            return item
        elif isinstance(item, ScaItem):
            if item.contents() is None:
                return self
            elif options.allow_list_over_scalar:
                self._list.insert(0, item.contents())
                return self
            else:
                raise TypeError('allow list over scalar = False: cannot merge %s onto %s' % (repr(self), repr(item)))
        raise TypeError('Cannot merge %s over %s' % (repr(self), repr(item)))

    def __repr__(self):
        return 'ListItem(%r)' % (self._list)
