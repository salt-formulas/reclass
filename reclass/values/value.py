#
# -*- coding: utf-8 -*-
#
# This file is part of reclass
#

from .parser import Parser
from .dictitem import DictItem
from .listitem import ListItem
from .scaitem import ScaItem
from reclass.errors import InterpolationError

class Value(object):

    _parser = Parser()

    def __init__(self, value, settings, uri, parse_string=True):
        self._settings = settings
        self._uri = uri
        self._overwrite = False
        if isinstance(value, str):
            if parse_string:
                try:
                    self._item = self._parser.parse(value, self._settings)
                except InterpolationError as e:
                    e.uri = self._uri
                    raise
            else:
                self._item = ScaItem(value, self._settings)
        elif isinstance(value, list):
            self._item = ListItem(value, self._settings)
        elif isinstance(value, dict):
            self._item = DictItem(value, self._settings)
        else:
            self._item = ScaItem(value, self._settings)

    @property
    def overwrite(self):
        return self._overwrite

    @overwrite.setter
    def overwrite(self, overwrite):
        self._overwrite = overwrite

    def uri(self):
        return self._uri

    def is_container(self):
        return self._item.is_container()

    def allRefs(self):
        return self._item.allRefs()

    def has_references(self):
        return self._item.has_references()

    def has_inv_query(self):
        return self._item.has_inv_query()

    def needs_all_envs(self):
        if self._item.has_inv_query():
            return self._item.needs_all_envs()
        else:
            return False

    def ignore_failed_render(self):
        return self._item.ignore_failed_render()

    def is_complex(self):
        return self._item.is_complex()

    def get_references(self):
        return self._item.get_references()

    def get_inv_references(self):
        return self._item.get_inv_references()

    def assembleRefs(self, context):
        if self._item.has_references():
            self._item.assembleRefs(context)

    def render(self, context, inventory):
        try:
            return self._item.render(context, inventory)
        except InterpolationError as e:
            e.uri = self._uri
            raise

    def contents(self):
        return self._item.contents()

    def merge_over(self, value):
        self._item = self._item.merge_over(value._item)
        return self

    def __repr__(self):
        return 'Value(%r)' % self._item

    def __str__(self):
        return str(self._item)
