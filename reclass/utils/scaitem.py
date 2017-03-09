#
# -*- coding: utf-8 -*-
#
# This file is part of reclass
#

import dictitem
import listitem

class ScaItem(object):

    def __init__(self, value):
        self._value = value

    def assembleRefs(self, context={}):
        return

    def allRefs(self):
        return True

    def has_references(self):
        return False

    def contents(self):
        return self._value

    def merge_over_with_context(self, item, context, options):
        pass

    def merge_over(self, item, options):
        if isinstance(item, ScaItem):
            return self
        elif isinstance(item, listitem.ListItem):
            if options.allow_scalar_over_list:
                return self
            else:
                raise TypeError('allow scalar over list = False: cannot merge %s over %s' % (repr(self), repr(item)))
        elif isinstance(item, dictitem.DictItem):
            if options.allow_scalar_over_dict:
                return self
            else:
                raise TypeError('allow scalar over dict = False: cannot merge %s over %s' % (repr(self), repr(item)))
        raise TypeError('Cannot merge %s over %s' % (repr(self), repr(item)))

    def render(self, context, options):
        return self._value

    def __repr__(self):
        return 'ScaItem({0!r})'.format(self._value)