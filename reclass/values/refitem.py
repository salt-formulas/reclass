#
# -*- coding: utf-8 -*-
#
# This file is part of reclass
#

from item import Item
from reclass.settings import Settings
from reclass.utils.dictpath import DictPath
from reclass.errors import ResolveError
from reclass.defaults import REFERENCE_SENTINELS, EXPORT_SENTINELS
import sys

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
            print >>sys.stderr, "[WARNING] Reference '%s' undefined. Possibly used too early and defined later in class hierarchy." % (ref)
            if self._settings.return_missing_reference:
                return "%s" % ref.join(REFERENCE_SENTINELS)
            else:
                raise ResolveError(ref)

    def render(self, context, inventory):
        if len(self._items) == 1:
            return self._resolve(self._items[0].render(context, inventory), context)
        strings = [ str(i.render(context, inventory)) for i in self._items ]
        return self._resolve("".join(strings), context)

    def __repr__(self):
        return 'RefItem(%r)' % self._items
