#
# -*- coding: utf-8 -*-
#
# This file is part of reclass
#

class ListItem(object):

    def __init__(self, item):
        self._list = item
        self._refs = []
        self._allRefs = False
        self.assembleRefs()

    def assembleRefs(self, context={}):
        from reclass.utils.value import Value
        from reclass.utils.valuelist import ValueList

        self._refs = []
        self._allRefs = True
        for item in self._list:
            if isinstance(item, (Value, ValueList)) and item.has_references():
                for ref in item.get_references():
                    self._refs.append(ref)
                if not item.allRefs():
                    self._allRefs = False

    def contents(self):
        return self._list

    def allRefs(self):
        return self._allRefs

    def has_references(self):
        return len(self._refs) > 0

    def get_references(self):
        return self._refs

    def render(self, context):
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
