#
# -*- coding: utf-8 -*-
#
# This file is part of reclass
#

from reclass.values import item


class ListItem(item.ContainerItem):

    type = item.ItemTypes.LIST

    def __init__(self, items, settings):
        super(ListItem, self).__init__(items, settings)
        for item in self.contents:
            if item.has_inv_query:
                self.inv_refs += item.get_inv_references()
                if item.needs_all_envs:
                    self.needs_all_envs = True
                if item.ignore_failed_render is False:
                    self.ignore_failed_render = False

        if len(self.inv_refs) > 0:
            self.has_inv_query = True

    def merge_over(self, other):
        if other.type == item.ItemTypes.LIST:
            other.contents.extend(self.contents)
            return other
        raise RuntimeError('Failed to merge %s over %s'  % (self, other))
