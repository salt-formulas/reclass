#
# -*- coding: utf-8 -*-
#
# This file is part of reclass

import collections
import fnmatch
import os
import pygit2

import reclass.errors
from reclass.storage import NodeStorageBase
from reclass.storage.common import NameMangler
from reclass.storage.yamldata import YamlData

FILE_EXTENSION = '.yml'
STORAGE_NAME = 'git_fs'

def path_mangler(inventory_base_uri, nodes_uri, classes_uri):
    if nodes_uri == classes_uri:
        raise errors.DuplicateUriError(nodes_uri, classes_uri)
    return nodes_uri, classes_uri


def list_files_in_branch(repo, branch):
    def _files_in_tree(tree, path):
        files = []
        for entry in tree:
            if entry.filemode == pygit2.GIT_FILEMODE_TREE:
                subtree = repo.get(entry.id)
                if path == '':
                    subpath = entry.name
                else:
                    subpath = '/'.join([path, entry.name])
                files.extend(_files_in_tree(subtree, subpath))
            else:
                if path == '':
                    relpath = entry.name
                else:
                    relpath = '/'.join([path, entry.name])
                files.append(GitMD(entry.name, relpath, entry.id))
        return files

    tree = repo.revparse_single('master').tree
    return _files_in_tree(tree, '')


GitMD = collections.namedtuple("GitMD", ["name", "path", "id"], verbose=False, rename=False)


class ExternalNodeStorage(NodeStorageBase):

    def __init__(self, nodes_uri, classes_uri, default_environment=None):
        super(ExternalNodeStorage, self).__init__(STORAGE_NAME)

        self._nodes_uri = nodes_uri
        self._nodes_repo = pygit2.Repository(self._nodes_uri)
        self._nodes = self._enumerate_nodes()

        self._classes_uri = classes_uri
        self._classes_repo = pygit2.Repository(self._classes_uri)
        self._classes_branches = self._classes_repo.listall_branches()
        self._classes = self._enumerate_classes()
        self._default_environment = default_environment

    nodes_uri = property(lambda self: self._nodes_uri)
    classes_uri = property(lambda self: self._classes_uri)

    def get_node(self, name):
        blob = self._nodes_repo.get(self._nodes[name].id)
        entity = YamlData.from_string(blob.data, 'git_fs://{0}:master/{1}'.format(self._nodes_uri, self._nodes[name].path)).get_entity(name, self._default_environment)
        return entity

    def get_class(self, name, nodename=None, branch='master'):
        blob = self._classes_repo.get(self._classes[branch][name].id)
        entity = YamlData.from_string(blob.data, 'git_fs://{0}:{1}/{2}'.format(self._classes_uri, branch, self._classes[branch][name].path)).get_entity(name, self._default_environment)
        return entity

    def enumerate_nodes(self):
        return self._nodes.keys()

    def _enumerate_nodes(self):
        ret = {}
        files = list_files_in_branch(self._nodes_repo, 'master')
        for file in files:
            if fnmatch.fnmatch(file.name, '*{0}'.format(FILE_EXTENSION)):
                name = os.path.splitext(file.name)[0]
                if name in ret:
                    raise reclass.errors.DuplicateNodeNameError(self.name, name, ret[name], path)
                else:
                    ret[name] = file
        return ret

    def _enumerate_classes(self):
        ret = {}
        for bname in self._classes_branches:
            branch = {}
            files = list_files_in_branch(self._classes_repo, bname)
            for file in files:
                if fnmatch.fnmatch(file.name, '*{0}'.format(FILE_EXTENSION)):
                    name = os.path.splitext(file.name)[0]
                    relpath = os.path.dirname(file.path)
                    relpath, name = NameMangler.classes(relpath, name)
                    if name in ret:
                        raise reclass.errors.DuplicateNodeNameError(self.name, name, ret[name], path)
                    else:
                        branch[name] = file
            ret[bname] = branch
        return ret
