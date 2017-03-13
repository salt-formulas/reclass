#
# -*- coding: utf-8 -*-
#
# This file is part of reclass
#


class CompItem(object):

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

    def render(self, context):
        # Preserve type if only one item
        if len(self._items) == 1:
            return self._items[0].render(context)
        # Multiple items
        string = ''
        for item in self._items:
            string += str(item.render(context))
        return string

    def __repr__(self):
        return 'CompItem(%r)' % self._items
