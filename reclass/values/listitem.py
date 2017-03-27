#
# -*- coding: utf-8 -*-
#
# This file is part of reclass
#

from item import Item

class ListItem(Item):

    def __init__(self, item):
        self.type = Item.LIST
        self._list = item

    def contents(self):
        return self._list

    def is_container(self):
        return True

    def render(self, context, inventory):
        return self._list

    def merge_over(self, item, options):
        if item.type == Item.LIST:
            item._list.extend(self._list)
            return item
        elif item.type == Item.SCALAR:
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
