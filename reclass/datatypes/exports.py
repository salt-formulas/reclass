#
# -*- coding: utf-8 -*-
#
# This file is part of reclass (http://github.com/madduck/reclass)
#
from parameters import Parameters
from reclass.errors import UndefinedVariableError

class Exports(Parameters):

    def __init__(self, mapping=None, delimiter=None, options=None):
        super(Exports, self).__init__(mapping, delimiter, options)

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
            external._interpolate_references(path, value, None)
            new = self._interpolate_render_from_external(external._base, path, value)
            path.set_value(self._base, new)
            del self._unrendered[path]

    def _interpolate_render_from_external(self, context, path, value):
        try:
            new = value.render(context, None, self._options)
        except UndefinedVariableError as e:
            raise UndefinedVariableError(e.var, path)
        if isinstance(new, dict):
            self._render_simple_dict(new, path)
        elif isinstance(new, list):
            self._render_simple_list(new, path)
        return new
