#
# -*- coding: utf-8 -*-
#
# This file is part of reclass
#

from reclass.utils.mergeoptions import MergeOptions

class ValueList(object):

    def __init__(self, value=None):
        self._refs = []
        self._allRefs = True
        self._values = []
        if value is not None:
            self._values.append(value)
        self.assembleRefs()

    def append(self, value):
        self._values.append(value)
        self._refs.extend(value._refs)
        if value.allRefs() is False:
            self._allRefs = True

    def extend(self, values):
        self._values.extend(values._values)
        self.assembleRefs()

    def has_references(self):
        return len(self._refs) > 0

    def get_references(self):
        return self._refs

    def allRefs(self):
        return self._allRefs

    def assembleRefs(self, context={}):
        self._refs = []
        self._allRefs = True
        for value in self._values:
            value.assembleRefs(context)
            if value.has_references():
                self._refs.extend(value.get_references())
            if value.allRefs() is False:
                self._allRefs = False

    def merge(self, options=None):
        if options is None:
            options = MergeOptions()
        output = None
        for n, value in enumerate(self._values):
            if n is 0:
                output = self._values[0]
            else:
                output = value.merge_over(output, options)
        return output

    def render(self, context, options=None):
        from reclass.datatypes.parameters import Parameters

        if options is None:
            options = MergeOptions()
        output = None
        for n, value in enumerate(self._values):
            if n is 0:
                output = self._values[0].render(context, options)
            else:
                new = value.render(context, options)
                if isinstance(output, dict) and isinstance(new, dict):
                    p1 = Parameters(output, value._delimiter)
                    p2 = Parameters(new, value._delimiter)
                    p1.merge(p2)
                    output = p1.as_dict()
                    continue
                elif isinstance(output, list) and isinstance(new, list):
                    output.extend(new)
                    continue
                elif isinstance(output, (dict, list)) or isinstance(new, (dict, list)):
                    raise TypeError('Cannot merge %s over %s' % (repr(self._values[n]), repr(self._values[n-1])))
                else:
                    output = new
        return output

    def __repr__(self):
        return 'ValueList(%r)' % self._values
