#
# -*- coding: utf-8 -*-
#
# This file is part of reclass (http://github.com/madduck/reclass)
#

import copy

from parameters import Parameters
from reclass.errors import ResolveError
from reclass.values.value import Value
from reclass.values.valuelist import ValueList

class Exports(Parameters):

    def __init__(self, mapping, settings, uri):
        super(Exports, self).__init__(mapping, settings, uri)

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self._base)

    def delete_key(self, key):
        self._base.pop(key, None)
        self._unrendered.pop(key, None)

    def overwrite(self, other):
        overdict = {'~' + key: value for key, value in other.iteritems()}
        self.merge(overdict)

    def interpolate_from_external(self, external):
        while len(self._unrendered) > 0:
            path, v = self._unrendered.iteritems().next()
            value = path.get_value(self._base)
            if isinstance(value, (Value, ValueList)):
                external._interpolate_references(path, value, None)
                new = self._interpolate_render_from_external(external._base, path, value)
                path.set_value(self._base, new)
                del self._unrendered[path]
            else:
                # references to lists and dicts are only deepcopied when merged
                # together so it's possible a value with references in a referenced
                # list or dict has already been rendered
                del self._unrendered[path]

    def interpolate_single_from_external(self, external, query):
        paths = {}
        for r in query.get_inv_references():
            paths[r] = True

        rendered = {}
        while len(paths) > 0:
            path, v = paths.iteritems().next()
            rendpath = path.deepest_match_in(self._base)
            if rendpath in rendered:
                del paths[path]
                continue
            if rendpath.exists_in(self._base) and rendpath in self._unrendered:
                value = rendpath.get_value(self._base)
                if isinstance(value, (Value, ValueList)):
                    try:
                        external._interpolate_references(rendpath, value, None)
                        new = self._interpolate_render_from_external(external._base, rendpath, value)
                        rendpath.set_value(self._base, new)
                    except ResolveError as e:
                        if query.ignore_failed_render():
                            rendpath.delete(self._base)
                        else:
                            raise
            rendered[rendpath] = True
            paths.pop(rendpath, None)
            self._unrendered.pop(rendpath, None)

    def _interpolate_render_from_external(self, context, path, value):
        try:
            new = value.render(context, None)
        except ResolveError as e:
            e.context = path
            raise
        if isinstance(new, dict):
            self._render_simple_dict(new, path)
        elif isinstance(new, list):
            self._render_simple_list(new, path)
        return new
