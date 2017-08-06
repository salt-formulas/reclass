#
# -*- coding: utf-8 -*-
#
# This file is part of reclass (http://github.com/madduck/reclass)
#
from parameters import Parameters
from reclass.errors import ResolveError
from reclass.values.value import Value
from reclass.values.valuelist import ValueList

class Exports(Parameters):

    def __init__(self, mapping=None, uri=None, delimiter=None, options=None):
        super(Exports, self).__init__(mapping, uri, delimiter, options)

    def __repr__(self):
        return '%s(%r, %r)' % (self.__class__.__name__, self._base,
                               self.delimiter)

    def delete_key(self, key):
        self._base.pop(key, None)
        self._unrendered.pop(key, None)

    def overwrite(self, other):
        overdict = {'~' + key: value for key, value in other.iteritems()}
        self.merge(overdict)

    def interpolate_from_external(self, external):
        self._initialise_interpolate()
        external._initialise_interpolate()
        while len(self._unrendered) > 0:
            path, v = self._unrendered.iteritems().next()
            value = path.get_value(self._base)
            if not isinstance(value, (Value, ValueList)):
                # references to lists and dicts are only deepcopied when merged
                # together so it's possible a value with references in a referenced
                # list or dict has already been rendered
                del self._unrendered[path]
            else:
                external._interpolate_references(path, value, None)
                new = self._interpolate_render_from_external(external._base, path, value)
                path.set_value(self._base, new)
                del self._unrendered[path]

    def _interpolate_render_from_external(self, context, path, value):
        try:
            new = value.render(context, None, self._options)
        except ResolveError as e:
            e.context = path
            raise e
        if isinstance(new, dict):
            self._render_simple_dict(new, path)
        elif isinstance(new, list):
            self._render_simple_list(new, path)
        return new
