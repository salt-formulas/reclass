#
# -*- coding: utf-8 -*-
#
# This file is part of reclass
#

from parser import Parser
from reclass.defaults import PARAMETER_INTERPOLATION_DELIMITER

class Value(object):

    _parser = Parser()

    def __init__(self, val, delimiter=PARAMETER_INTERPOLATION_DELIMITER):
        self._delimiter = delimiter
        self._item = self._parser.parse(val, self._delimiter)

    def is_container(self):
        return self._item.is_container()

    def allRefs(self):
        return self._item.allRefs()

    def has_references(self):
        return self._item.has_references()

    def has_exports(self):
        return self._item.has_exports()

    def is_complex(self):
        return (self.has_references() | self.has_exports())

    def get_references(self):
        return self._item.get_references()

    def assembleRefs(self, context):
        if self._item.has_references():
            self._item.assembleRefs(context)

    def render(self, context, exports, options=None):
        return self._item.render(context, exports)

    def contents(self):
        return self._item.contents()

    def merge_over(self, value, options):
        self._item = self._item.merge_over(value._item, options)
        return self

    def __repr__(self):
        return 'Value(%r)' % self._item
