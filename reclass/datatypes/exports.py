#
# -*- coding: utf-8 -*-
#
# This file is part of reclass (http://github.com/madduck/reclass)
#
from parameters import Parameters

class Exports(Parameters):

    def __init__(self, mapping=None, delimiter=None):
        super(Exports, self).__init__(mapping, delimiter)

    def __repr__(self):
        return '%s(%r, %r)' % (self.__class__.__name__, self._base,
                               self.delimiter)

    def delete_key(self, key):
        self._base.pop(key, None)
        self._unrendered.pop(key, None)

    def overwrite(self, other):
        overdict = {'~' + key: value for key, value in other.iteritems()}
        self.merge(overdict)

    def interpolate_from_external(self, external, options=None):
        self._initialise_interpolate(options)
        external._initialise_interpolate(options)
        while len(self._unrendered) > 0:
            path, v = self._unrendered.iteritems().next()
            value = path.get_value(self._base)
            external._interpolate_references(path, value, None)
            new = value.render(external._base, self._options)
            path.set_value(self._base, new)
            del self._unrendered[path]
