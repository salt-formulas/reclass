#
# -*- coding: utf-8 -*-
#
# This file is part of reclass
#

from .item import Item
from reclass.defaults import REFERENCE_SENTINELS
from reclass.settings import Settings
from reclass.utils.dictpath import DictPath
from reclass.errors import ResolveError


class RefItem(Item):

    def __init__(self, items, settings):
        self.type = Item.REFERENCE
        self._settings = settings
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
                if item.allRefs() == False:
                    self._allRefs = False
        try:
            strings = [ str(i.render(context, None)) for i in self._items ]
            value = "".join(strings)
            self._refs.append(value)
        except ResolveError as e:
            self._allRefs = False

    def contents(self):
        return self._items

    def allRefs(self):
        return self._allRefs

    def has_references(self):
        return len(self._refs) > 0

    def get_references(self):
        return self._refs

    def _resolve(self, ref, context):
        path = DictPath(self._settings.delimiter, ref)
        try:
            return path.get_value(context)
        except (KeyError, TypeError) as e:
            raise ResolveError(ref)

    def render(self, context, inventory):
        if len(self._items) == 1:
            return self._resolve(self._items[0].render(context, inventory), context)
        strings = [ str(i.render(context, inventory)) for i in self._items ]
        return self._resolve("".join(strings), context)

    def __repr__(self):
        return 'RefItem(%r)' % self._items

    def __str__(self):
        strings = [ str(i) for i in self._items ]
        return '{0}{1}{2}'.format(REFERENCE_SENTINELS[0], ''.join(strings), REFERENCE_SENTINELS[1])
