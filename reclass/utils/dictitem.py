#
# -*- coding: utf-8 -*-
#
# This file is part of reclass
#

class DictItem(object):

    def __init__(self, items):
        self._items = items
        self._refs = []
        self._allRefs = False
        self.assembleRefs()

    def assembleRefs(self, context={}):
        self._refs = []
        self._allRefs = True
        self._assembleRefs_recurse_dict(self._items)

    def _assembleRefs_recurse_dict(self, items):
        for key, item in items.iteritems():
            if isinstance(item, dict):
                self._assembleRefs_recurse_dict(item)
                continue
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

    def merge_over(self, item, options):
        from reclass.utils.scaitem import ScaItem

        if isinstance(item, ScaItem):
            if options.allow_dict_over_scalar:
                return self
            else:
                raise TypeError('allow dict over scalar = False: cannot merge %s onto %s' % (repr(self), repr(item)))
        raise TypeError('Cannot merge %s over %s' % (repr(self), repr(item)))

    def render(self, context, options):
        value = {}
        for key, item in self._items.iteritems():
            value[key] = item
        return value

    def __repr__(self):
        return 'DictItem(%r)' % self._items
