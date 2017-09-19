#
# -*- coding: utf-8 -*-
#
# This file is part of reclass
#

import copy

class ValueList(object):

    def __init__(self, value, settings):
        self._settings = settings
        self._refs = []
        self._allRefs = True
        self._values = [ value ]
        self._inv_refs = []
        self._has_inv_query = False
        self._ignore_failed_render = False
        self._update()

    def append(self, value):
        self._values.append(value)
        self._update()

    def extend(self, values):
        self._values.extend(values._values)
        self._update()

    def _update(self):
        self.assembleRefs()
        self._check_for_inv_query()

    def has_references(self):
        return len(self._refs) > 0

    def has_inv_query(self):
        return self._has_inv_query

    def get_inv_references(self):
        return self._inv_refs

    def is_complex(self):
        return (self.has_references() | self.has_inv_query())

    def get_references(self):
        return self._refs

    def allRefs(self):
        return self._allRefs

    def ignore_failed_render(self):
        return self._ignore_failed_render

    def _check_for_inv_query(self):
        self._has_inv_query = False
        self._ignore_failed_render = True
        for value in self._values:
            if value.has_inv_query():
                self._inv_refs.extend(value.get_inv_references)
                self._has_inv_query = True
                if vale.ignore_failed_render() is False:
                    self._ignore_failed_render = False
        if self._has_inv_query is False:
            self._ignore_failed_render = False

    def assembleRefs(self, context={}):
        self._refs = []
        self._allRefs = True
        for value in self._values:
            value.assembleRefs(context)
            if value.has_references():
                self._refs.extend(value.get_references())
            if value.allRefs() is False:
                self._allRefs = False

    def merge(self):
        output = None
        for n, value in enumerate(self._values):
            if output is None:
                output = value
            else:
                output = value.merge_over(output)
        return output

    def render(self, context, inventory):
        from reclass.datatypes.parameters import Parameters

        output = None
        deepCopied = False
        for n, value in enumerate(self._values):
            if output is None:
                output = self._values[n].render(context, inventory)
                deepCopied = False
            else:
                new = value.render(context, inventory)
                if isinstance(output, dict) and isinstance(new, dict):
                    p1 = Parameters(output, self._settings, None)
                    p2 = Parameters(new, self._settings, None)
                    p1.merge(p2)
                    output = p1.as_dict()
                    continue
                elif isinstance(output, list) and isinstance(new, list):
                    if not deepCopied:
                        output = copy.deepcopy(output)
                        deepCopied = True
                    output.extend(new)
                    continue
                elif isinstance(output, (dict, list)) or isinstance(new, (dict, list)):
                    raise TypeError('Cannot merge %s over %s' % (repr(self._values[n]), repr(self._values[n-1])))
                else:
                    output = new
        return output

    def __repr__(self):
        return 'ValueList(%r)' % self._values
