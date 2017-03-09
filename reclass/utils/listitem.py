#
# -*- coding: utf-8 -*-
#
# This file is part of reclass
#

import scaitem

class ListItem(object):

    def __init__(self, items):
        self._items = items
        self._refs = []
        self._allRefs = False
        self.assembleRefs()

    def assembleRefs(self, context={}):
        self._refs = []
        self._allRefs = True
        for item in self._items:
            if item.has_references():
                for ref in item.get_references():
                    self._refs.append(ref)
                if not item.allRefs():
                    self._allRefs = False

    def contents(self):
        return self._items

    def allRefs(self):
        return self._allRefs

    def has_references(self):
        return len(self._refs) > 0

    def get_references(self):
        return self._refs

    def render(self, context):
        value = []
        for item in self._items:
            value.append(item)
        return value

    def merge_over(self, item, options):
        if isinstance(item, ListItem):
            for i in self._items:
                item._items.append(i)
            return item
        elif isinstance(item, scaitem.ScaItem):
            if options.allow_list_over_scalar:
                self._items.insert(0, item.contents())
                return self
            else:
                raise TypeError('allow list over scalar = False: cannot merge %s onto %s' % (repr(self), repr(item)))
        raise TypeError('Cannot merge %s over %s' % (repr(self), repr(item)))

    def __repr__(self):
        return 'ListItem(%r)' % (self._items)
