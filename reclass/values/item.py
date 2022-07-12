#
# -*- coding: utf-8 -*-
#
# This file is part of reclass
#
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from enum import Enum
from six import iteritems

from reclass.utils.dictpath import DictPath
from reclass.utils.parameterdict import ParameterDict
from reclass.utils.parameterlist import ParameterList

ItemTypes = Enum('ItemTypes',
                 ['COMPOSITE', 'DICTIONARY', 'INV_QUERY', 'LIST',
                  'REFERENCE', 'SCALAR'])


class Item(object):

    def __init__(self, item, settings):
        self._settings = settings
        self.contents = item
        self.has_inv_query = False

    def allRefs(self):
        return True

    @property
    def has_references(self):
        return False

    def is_container(self):
        return False

    @property
    def is_complex(self):
        return (self.has_references | self.has_inv_query)

    def merge_over(self, item):
        msg = "Item class {0} does not implement merge_over()"
        raise NotImplementedError(msg.format(self.__class__.__name__))

    def render(self, context, exports):
        msg = "Item class {0} does not implement render()"
        raise NotImplementedError(msg.format(self.__class__.__name__))

    def type_str(self):
        return self.type.name.lower()

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.contents)


class ItemWithReferences(Item):

    def __init__(self, items, settings):
        super(ItemWithReferences, self).__init__(items, settings)
        try:
            iter(self.contents)
        except TypeError:
            self.contents = [self.contents]
        self.assembleRefs()

    @property
    def has_references(self):
        return len(self._refs) > 0

    def get_references(self):
        return self._refs

    # NOTE: possibility of confusion. Looks like 'assemble' should be either
    # 'gather' or 'extract'.
    def assembleRefs(self, context={}):
        self._refs = []
        self.allRefs = True
        for item in self.contents:
            if item.has_references:
                item.assembleRefs(context)
                self._refs.extend(item.get_references())
                if item.allRefs is False:
                    self.allRefs = False


class ContainerItem(Item):

    def __init__(self, items, settings):
        super(ContainerItem, self).__init__(items, settings)
        self.inv_refs = []
        self.ignore_failed_render = True
        self.needs_all_envs = False

    def get_inv_references(self):
        return self.inv_refs

    def is_container(self):
        return True

    def render(self, context, inventory):
        return self.contents
