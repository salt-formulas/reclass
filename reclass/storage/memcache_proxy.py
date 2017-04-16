#
# -*- coding: utf-8 -*-
#
# This file is part of reclass (http://github.com/madduck/reclass)
#
# Copyright © 2007–14 martin f. krafft <madduck@madduck.net>
# Released under the terms of the Artistic Licence 2.0
#

from reclass.storage import NodeStorageBase

STORAGE_NAME = 'memcache_proxy'

class MemcacheProxy(NodeStorageBase):

    def __init__(self, real_storage, cache_classes=True, cache_nodes=True,
                 cache_nodelist=True, cache_exports=True):
        name = '{0}({1})'.format(STORAGE_NAME, real_storage.name)
        super(MemcacheProxy, self).__init__(name)
        self._real_storage = real_storage
        self._cache_classes = cache_classes
        if cache_classes:
            self._classes_cache = {}
        self._cache_nodes = cache_nodes
        if cache_nodes:
            self._nodes_cache = {}
        self._cache_nodelist = cache_nodelist
        if cache_nodelist:
            self._nodelist_cache = None
        self._cache_exports = cache_exports
        if cache_exports:
            self._exports_cache = None

    name = property(lambda self: self._real_storage.name)

    @staticmethod
    def _cache_proxy(name, cache, getter):
        try:
            ret = cache[name]

        except KeyError, e:
            ret = getter(name)
            cache[name] = ret

        return ret

    @staticmethod
    def _cache(cache, getter):
        if cache is None:
            cache = getter()
        return cache

    def get_node(self, name):
        if not self._cache_nodes:
            return self._real_storage.get_node(name)

        return MemcacheProxy._cache_proxy(name, self._nodes_cache,
                                          self._real_storage.get_node)

    def get_class(self, name, environment):
        if not self._cache_classes:
            return self._real_storage.get_class(name, environment)

        return MemcacheProxy._cache_proxy(name, self._classes_cache,
                                          self._real_storage.get_class)

    def get_exports(self):
        if not self._cache_exports:
             return self._real_storage.get_exports()
        return MemcacheProxy._cache(self._exports_cache, self._real_storage.get_exports)

    def put_exports(self, new):
        self._real_storage.put_exports(new)

    def enumerate_nodes(self):
        if not self._cache_nodelist:
            return self._real_storage.enumerate_nodes()

        elif self._nodelist_cache is None:
            self._nodelist_cache = self._real_storage.enumerate_nodes()

        return self._nodelist_cache
