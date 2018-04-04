#
# -*- coding: utf-8 -*-
#
# This file is part of reclass (http://github.com/madduck/reclass)
#

import copy

from six import iteritems, next

from .parameters import Parameters
from reclass.errors import ResolveError
from reclass.values.value import Value
from reclass.values.valuelist import ValueList
from reclass.utils.dictpath import DictPath

class Exports(Parameters):

    def __init__(self, mapping, settings, uri):
        super(Exports, self).__init__(mapping, settings, uri)

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self._base)

    def delete_key(self, key):
        self._base.pop(key, None)
        self._unrendered.pop(key, None)

    def overwrite(self, other):
        overdict = {'~' + key: value for (key, value) in iteritems(other)}
        self.merge(overdict)

    def interpolate_from_external(self, external):
        while len(self._unrendered) > 0:
            path, v = next(iteritems(self._unrendered))
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
        for r in query.get_inv_references():
            self._interpolate_single_path_from_external(r, external, query)

    def _interpolate_single_path_from_external(self, mainpath, external, query):
        required = self._get_required_paths(mainpath)
        while len(required) > 0:
            while len(required) > 0:
                path, v = next(iteritems(required))
                value = path.get_value(self._base)
                if isinstance(value, (Value, ValueList)):
                    try:
                        external._interpolate_references(path, value, None)
                        new = self._interpolate_render_from_external(external._base, path, value)
                        path.set_value(self._base, new)
                    except ResolveError as e:
                        if query.ignore_failed_render():
                            path.delete(self._base)
                        else:
                            raise
                del required[path]
                del self._unrendered[path]
            required = self._get_required_paths(mainpath)

    def _get_required_paths(self, mainpath):
        paths = {}
        path = DictPath(self._settings.delimiter)
        for i in mainpath.key_parts():
            path.add_subpath(i)
            if path in self._unrendered:
                paths[path] = True
        for i in self._unrendered:
            if mainpath.is_ancestor_of(i) or mainpath == i:
                paths[i] = True
        return paths

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
