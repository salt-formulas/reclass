#
# -*- coding: utf-8 -*-
#
# This file is part of reclass
#

from parser import Parser
from dictitem import DictItem
from listitem import ListItem
from scaitem import ScaItem
from reclass.defaults import PARAMETER_INTERPOLATION_DELIMITER

class Value(object):

    _parser = Parser()

    def __init__(self, value, delimiter=PARAMETER_INTERPOLATION_DELIMITER):
        self._delimiter = delimiter
        if isinstance(value, str):
            self._item = self._parser.parse(value, delimiter)
        elif isinstance(value, list):
            self._item = ListItem(value)
        elif isinstance(value, dict):
            self._item = DictItem(value)
        else:
            self._item = ScaItem(value)

    def is_container(self):
        return self._item.is_container()

    def allRefs(self):
        return self._item.allRefs()

    def has_references(self):
        return self._item.has_references()

    def has_inv_query(self):
        return self._item.has_inv_query()

    def is_complex(self):
        return self._item.is_complex()

    def get_references(self):
        return self._item.get_references()

    def assembleRefs(self, context):
        if self._item.has_references():
            self._item.assembleRefs(context)

    def render(self, context, inventory, options=None):
        return self._item.render(context, inventory)

    def contents(self):
        return self._item.contents()

    def merge_over(self, value, options):
        self._item = self._item.merge_over(value._item, options)
        return self

    def __repr__(self):
        return 'Value(%r)' % self._item
