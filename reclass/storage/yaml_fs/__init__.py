#
# -*- coding: utf-8 -*-
#
# This file is part of reclass (http://github.com/madduck/reclass)
#
# Copyright © 2007–14 martin f. krafft <madduck@madduck.net>
# Released under the terms of the Artistic Licence 2.0
#
import os, sys
import fnmatch
import yaml
from reclass.output.yaml_outputter import ExplicitDumper
from reclass.storage import NodeStorageBase
from reclass.storage.common import NameMangler
from reclass.storage.yamldata import YamlData
from .directory import Directory
from reclass.datatypes import Entity
import reclass.errors

FILE_EXTENSION = '.yml'
STORAGE_NAME = 'yaml_fs'

def vvv(msg):
    #print >>sys.stderr, msg
    pass

def path_mangler(inventory_base_uri, nodes_uri, classes_uri):

    if inventory_base_uri is None:
        # if inventory_base is not given, default to current directory
        inventory_base_uri = os.getcwd()

    nodes_uri = nodes_uri or 'nodes'
    classes_uri = classes_uri or 'classes'

    def _path_mangler_inner(path):
        ret = os.path.join(inventory_base_uri, path)
        ret = os.path.expanduser(ret)
        return os.path.abspath(ret)

    n, c = map(_path_mangler_inner, (nodes_uri, classes_uri))
    if n == c:
        raise errors.DuplicateUriError(n, c)
    common = os.path.commonprefix((n, c))
    if common == n or common == c:
        raise errors.UriOverlapError(n, c)

    return n, c


class ExternalNodeStorage(NodeStorageBase):

    def __init__(self, nodes_uri, classes_uri):
        super(ExternalNodeStorage, self).__init__(STORAGE_NAME)

        if nodes_uri is not None:
            self._nodes_uri = nodes_uri
            self._nodes = self._enumerate_inventory(nodes_uri, NameMangler.nodes)

        if classes_uri is not None:
            self._classes_uri = classes_uri
            self._classes = self._enumerate_inventory(classes_uri, NameMangler.classes)

    nodes_uri = property(lambda self: self._nodes_uri)
    classes_uri = property(lambda self: self._classes_uri)

    def _enumerate_inventory(self, basedir, name_mangler):
        ret = {}
        def register_fn(dirpath, filenames):
            filenames = fnmatch.filter(filenames, '*{0}'.format(FILE_EXTENSION))
            vvv('REGISTER {0} in path {1}'.format(filenames, dirpath))
            for f in filenames:
                name = os.path.splitext(f)[0]
                relpath = os.path.relpath(dirpath, basedir)
                if callable(name_mangler):
                    relpath, name = name_mangler(relpath, name)
                uri = os.path.join(dirpath, f)
                if name in ret:
                    E = reclass.errors.DuplicateNodeNameError
                    raise E(self.name, name,
                            os.path.join(basedir, ret[name]), uri)
                if relpath:
                    f = os.path.join(relpath, f)
                ret[name] = f

        d = Directory(basedir)
        d.walk(register_fn)
        return ret

    def get_node(self, name, settings):
        vvv('GET NODE {0}'.format(name))
        try:
            relpath = self._nodes[name]
            path = os.path.join(self.nodes_uri, relpath)
            name = os.path.splitext(relpath)[0]
        except KeyError as e:
            raise reclass.errors.NodeNotFound(self.name, name, self.nodes_uri)
        entity = YamlData.from_file(path).get_entity(name, settings)
        return entity

    def get_class(self, name, environment, settings):
        vvv('GET CLASS {0}'.format(name))
        try:
            path = os.path.join(self.classes_uri, self._classes[name])
        except KeyError as e:
            raise reclass.errors.ClassNotFound(self.name, name, self.classes_uri)
        entity = YamlData.from_file(path).get_entity(name, settings)
        return entity

    def enumerate_nodes(self):
        return self._nodes.keys()
