#
# -*- coding: utf-8 -*-
#
# This file is part of reclass
#

from six import iteritems

from reclass.values import item


class DictItem(item.ContainerItem):

    type = item.ItemTypes.DICTIONARY

    def __init__(self, items, settings):
        super(DictItem, self).__init__(items, settings)
        for key, item in iteritems(self.contents):
            if item.has_inv_query:
                self.inv_refs += item.get_inv_references()
                if item.needs_all_envs:
                    self.needs_all_envs = True
                if item.ignore_failed_render is False:
                    self.ignore_failed_render = False

        if len(self.inv_refs) > 0:
            self.has_inv_query = True
