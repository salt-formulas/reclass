#
# -*- coding: utf-8 -*-
#
# This file is part of reclass
#

from reclass.utils.dictpath import DictPath
from reclass.errors import UndefinedVariableError

class Item(object):

    def __init__(self):
        return

    def allRefs(self):
        return True

    def has_references(self):
        return False

    def has_exports(self):
        return False

    def is_complex():
        return (self.has_references | self.has_exports)
