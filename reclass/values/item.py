#
# -*- coding: utf-8 -*-
#
# This file is part of reclass
#

from reclass.utils.dictpath import DictPath

class Item(object):

    COMPOSITE = 1
    DICTIONARY = 2
    INV_QUERY = 3
    LIST = 4
    REFERENCE = 5
    SCALAR = 6

    def allRefs(self):
        return True

    def has_references(self):
        return False

    def has_inv_query(self):
        return False

    def is_container(self):
        return False

    def is_complex(self):
        return (self.has_references() | self.has_inv_query())

    def contents(self):
        msg = "Item class {0} does not implement contents()"
        raise NotImplementedError(msg.format(self.__class__.__name__))

    def merge_over(self, item):
        msg = "Item class {0} does not implement merge_over()"
        raise NotImplementedError(msg.format(self.__class__.__name__))

    def render(self, context, exports):
        msg = "Item class {0} does not implement render()"
        raise NotImplementedError(msg.format(self.__class__.__name__))
