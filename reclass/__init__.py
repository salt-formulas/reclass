#
# -*- coding: utf-8 -*-
#
# This file is part of reclass (http://github.com/madduck/reclass)
#
# Copyright © 2007–14 martin f. krafft <madduck@madduck.net>
# Released under the terms of the Artistic Licence 2.0
#

from reclass.output import OutputLoader
from reclass.storage.loader import StorageBackendLoader
from reclass.storage.memcache_proxy import MemcacheProxy


def get_storage(storage_type, nodes_uri, classes_uri, **kwargs):
    storage_class = StorageBackendLoader(storage_type).load()
    return MemcacheProxy(storage_class(nodes_uri, classes_uri, **kwargs))

def get_path_mangler(storage_type,**kwargs):
    return StorageBackendLoader(storage_type).path_mangler()

def output(data, fmt, pretty_print=False, no_refs=False):
    output_class = OutputLoader(fmt).load()
    outputter = output_class()
    return outputter.dump(data, pretty_print=pretty_print, no_refs=no_refs)
