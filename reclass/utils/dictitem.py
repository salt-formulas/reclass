#
# -*- coding: utf-8 -*-
#
# This file is part of reclass
#

class DictItem(object):

    def __init__(self, item):
        self._dict = item
        self._refs = []
        self._allRefs = False
        self.assembleRefs()

    def assembleRefs(self, context={}):
        self._refs = []
        self._allRefs = True
        self._assembleRefs_recurse_dict(self._dict)

    def _assembleRefs_recurse_dict(self, items):
        from reclass.utils.value import Value
        from reclass.utils.valuelist import ValueList

        for key, item in items.iteritems():
            if isinstance(item, dict):
                self._assembleRefs_recurse_dict(item)
                continue
            if isinstance(item, (Value, ValueList)) and item.has_references():
                for ref in item.get_references():
                    self._refs.append(ref)
                if not item.allRefs():
                    self._allRefs = False

    def contents(self):
        return self._dict

    def allRefs(self):
        return self._allRefs

    def has_references(self):
        return len(self._refs) > 0

    def has_exports(self):
        return False

    def get_references(self):
        return self._refs

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
