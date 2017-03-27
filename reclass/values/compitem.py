#
# -*- coding: utf-8 -*-
#
# This file is part of reclass
#

from item import Item

class CompItem(Item):

    def __init__(self, items):
        self.type = Item.COMPOSITE
        self._items = items
        self._refs = []
        self._allRefs = False
        self.assembleRefs()

    def assembleRefs(self, context={}):
        self._refs = []
        self._allRefs = True
        for item in self._items:
            if item.has_references():
                item.assembleRefs(context)
                self._refs.extend(item.get_references())
                if item.allRefs() is False:
                    self._allRefs = False

    def contents(self):
        return self._items

    def allRefs(self):
        return self._allRefs

    def has_references(self):
        return len(self._refs) > 0

    def get_references(self):
        return self._refs

    def render(self, context, inventory):
        # Preserve type if only one item
        if len(self._items) == 1:
            return self._items[0].render(context, inventory)
        # Multiple items
        strings = [ str(i.render(context, inventory)) for i in self._items ]
        return "".join(strings)

    def __repr__(self):
        return 'CompItem(%r)' % self._items
