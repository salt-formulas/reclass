#
# -*- coding: utf-8 -*-
#
# This file is part of reclass
#

from reclass.utils.dictpath import DictPath
from reclass.errors import UndefinedVariableError

class Item(object):

    COMPOSITE = 1
    DICTIONARY = 2
    EXPORT = 3
    LIST = 4
    REFERENCE = 5
    SCALAR = 6

    def allRefs(self):
        return True

    def has_references(self):
        return False

    def has_exports(self):
        return False

    def is_container(self):
        return False

    def is_complex():
        return (self.has_references | self.has_exports)

    def contents(self):
        msg = "Item class {0} does not implement contents()"
        raise NotImplementedError(msg.format(self.__class__.__name__))

    def merge_over(self, item, options):
        msg = "Item class {0} does not implement merge_over()"
        raise NotImplementedError(msg.format(self.__class__.__name__))

    def render(self, context, exports):
        msg = "Item class {0} does not implement render()"
        raise NotImplementedError(msg.format(self.__class__.__name__))
