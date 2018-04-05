#
# -*- coding: utf-8 -*-
#
# This file is part of reclass

import collections
import copy

from six import iteritems

import reclass.errors
from reclass import get_storage
from reclass.storage import NodeStorageBase

def path_mangler(inventory_base_uri, nodes_uri, classes_uri):
    if nodes_uri == classes_uri:
        raise errors.DuplicateUriError(nodes_uri, classes_uri)
    return nodes_uri, classes_uri

STORAGE_NAME = 'mixed'

class ExternalNodeStorage(NodeStorageBase):

    MixedUri = collections.namedtuple('MixedURI', 'storage_type options')

    def __init__(self, nodes_uri, classes_uri):
        super(ExternalNodeStorage, self).__init__(STORAGE_NAME)

        self._nodes_uri = self._uri(nodes_uri)
        self._nodes_storage = get_storage(self._nodes_uri.storage_type, self._nodes_uri.options, None)
        self._classes_default_uri = self._uri(classes_uri)
        self._classes_default_storage = get_storage(self._classes_default_uri.storage_type, None, self._classes_default_uri.options)

        self._classes_storage = dict()
        if 'env_overrides' in classes_uri:
            for override in classes_uri['env_overrides']:
                for (env, options) in iteritems(override):
                        uri = copy.deepcopy(classes_uri)
                        uri.update(options)
                        uri = self._uri(uri)
                        self._classes_storage[env] = get_storage(uri.storage_type, None, uri.options)

    def _uri(self, uri):
        ret = copy.deepcopy(uri)
        ret['storage_type'] = uri['storage_type']
        if 'env_overrides' in ret:
            del ret['env_overrides']
        if uri['storage_type'] == 'yaml_fs':
            ret = ret['uri']
        return self.MixedUri(uri['storage_type'], ret)

    def get_node(self, name, settings):
        return self._nodes_storage.get_node(name, settings)

    def get_class(self, name, environment, settings):
        storage = self._classes_storage.get(environment, self._classes_default_storage)
        return storage.get_class(name, environment, settings)

    def enumerate_nodes(self):
        return self._nodes_storage.enumerate_nodes()
