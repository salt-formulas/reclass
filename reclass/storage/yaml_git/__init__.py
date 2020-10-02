#
# -*- coding: utf-8 -*-
#
# This file is part of reclass
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import collections
import distutils.version
import errno
import fcntl
import os
import time

# Squelch warning on centos7 due to upgrading cffi
# see https://github.com/saltstack/salt/pull/39871
import warnings
with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    try:
        # NOTE: in some distros pygit2 could require special effort to acquire.
        # It is not a problem per se, but it breaks tests for no real reason.
        # This try block is for keeping tests sane.
        import pygit2
    except ImportError:
        pygit2 = None

from six import iteritems

import reclass.errors
from reclass.storage import ExternalNodeStorageBase
from reclass.storage.yamldata import YamlData

FILE_EXTENSION = ('.yml', '.yaml')
STORAGE_NAME = 'yaml_git'

def path_mangler(inventory_base_uri, nodes_uri, classes_uri):
    if nodes_uri == classes_uri:
        raise errors.DuplicateUriError(nodes_uri, classes_uri)
    return nodes_uri, classes_uri


GitMD = collections.namedtuple('GitMD', ['name', 'path', 'id'], rename=False)


class GitURI(object):

    def __init__(self, dictionary):
        self.repo = None
        self.branch = None
        self.root = None
        self.cache_dir = None
        self.lock_dir = None
        self.pubkey = None
        self.privkey = None
        self.password = None
        self.update(dictionary)

    def update(self, dictionary):
        if 'repo' in dictionary: self.repo = dictionary['repo']
        if 'branch' in dictionary: self.branch = dictionary['branch']
        if 'cache_dir' in dictionary: self.cache_dir = dictionary['cache_dir']
        if 'lock_dir' in dictionary: self.lock_dir = dictionary['lock_dir']
        if 'pubkey' in dictionary: self.pubkey = dictionary['pubkey']
        if 'privkey' in dictionary: self.privkey = dictionary['privkey']
        if 'password' in dictionary: self.password = dictionary['password']
        if 'root' in dictionary:
            if dictionary['root'] is None:
                self.root = None
            else:
                self.root = dictionary['root'].replace('/', '.')

    def __repr__(self):
        return '<{0}: {1} {2} {3}>'.format(self.__class__.__name__, self.repo, self.branch, self.root)


class LockFile():
    def __init__(self, file):
        self._file = file

    def __enter__(self):
        self._fd = open(self._file, 'w+')
        start = time.time()
        while True:
            if (time.time() - start) > 120:
                raise IOError('Timeout waiting to lock file: {0}'.format(self._file))
            try:
                fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except IOError as e:
                # raise on unrelated IOErrors
                if e.errno != errno.EAGAIN:
                    raise
                else:
                    time.sleep(0.1)

    def __exit__(self, type, value, traceback):
        self._fd.close()


class GitRepo(object):
    def __init__(self, uri, node_name_mangler, class_name_mangler):
        if pygit2 is None:
            raise errors.MissingModuleError('pygit2')
        self.transport, _, self.url = uri.repo.partition('://')
        self.name = self.url.replace('/', '_')
        self.credentials = None
        self.remotecallbacks = None
        if uri.cache_dir is None:
            self.cache_dir = '{0}/{1}/{2}'.format(os.path.expanduser("~"), '.reclass/cache/git', self.name)
        else:
            self.cache_dir = '{0}/{1}'.format(uri.cache_dir, self.name)
        if uri.lock_dir is None:
            self.lock_file = '{0}/{1}/{2}'.format(os.path.expanduser("~"), '.reclass/cache/lock', self.name)
        else:
            self.lock_file = '{0}/{1}'.format(uri.lock_dir, self.name)
        lock_dir = os.path.dirname(self.lock_file)
        if not os.path.exists(lock_dir):
            os.makedirs(lock_dir)
        self._node_name_mangler = node_name_mangler
        self._class_name_mangler = class_name_mangler
        with LockFile(self.lock_file):
            self._init_repo(uri)
            self._fetch()
        self.branches = self.repo.listall_branches()
        self.files = self.files_in_repo()

    def _init_repo(self, uri):
        if os.path.exists(self.cache_dir):
            self.repo = pygit2.Repository(self.cache_dir)
        else:
            os.makedirs(self.cache_dir)
            self.repo = pygit2.init_repository(self.cache_dir, bare=True)
            self.repo.create_remote('origin', self.url)
        if 'ssh' in self.transport:
            if '@' in self.url:
                user, _, _ = self.url.partition('@')
            else:
                user = 'gitlab'

            if uri.pubkey is not None:
                creds = pygit2.Keypair(user, uri.pubkey, uri.privkey, uri.password)
            else:
                creds = pygit2.KeypairFromAgent(user)

            pygit2_version = pygit2.__version__
            if distutils.version.LooseVersion(pygit2_version) >= distutils.version.LooseVersion('0.23.2'):
                self.remotecallbacks = pygit2.RemoteCallbacks(credentials=creds)
                self.credentials = None
            else:
                self.remotecallbacks = None
                self.credentials = creds

    def _fetch(self):
        origin = self.repo.remotes[0]
        fetch_kwargs = {}
        if self.remotecallbacks is not None:
            fetch_kwargs['callbacks'] = self.remotecallbacks
        if self.credentials is not None:
            origin.credentials = self.credentials
        fetch_results = origin.fetch(**fetch_kwargs)
        remote_branches = self.repo.listall_branches(pygit2.GIT_BRANCH_REMOTE)
        local_branches = self.repo.listall_branches()
        for remote_branch_name in remote_branches:
            _, _, local_branch_name = remote_branch_name.partition('/')
            remote_branch = self.repo.lookup_branch(remote_branch_name, pygit2.GIT_BRANCH_REMOTE)
            if local_branch_name not in local_branches:
                local_branch = self.repo.create_branch(local_branch_name, self.repo[remote_branch.target.hex])
                local_branch.upstream = remote_branch
            else:
                local_branch = self.repo.lookup_branch(local_branch_name)
                if local_branch.target != remote_branch.target:
                    local_branch.set_target(remote_branch.target)

        local_branches = self.repo.listall_branches()
        for local_branch_name in local_branches:
            remote_branch_name = '{0}/{1}'.format(origin.name, local_branch_name)
            if remote_branch_name not in remote_branches:
                local_branch = self.repo.lookup_branch(local_branch_name)
                local.branch.delete()

    def get(self, id):
        return self.repo.get(id)

    def files_in_tree(self, tree, path):
        files = []
        for entry in tree:
            if entry.filemode == pygit2.GIT_FILEMODE_TREE:
                subtree = self.repo.get(entry.id)
                if path == '':
                    subpath = entry.name
                else:
                    subpath = '/'.join([path, entry.name])
                files.extend(self.files_in_tree(subtree, subpath))
            else:
                if path == '':
                   relpath = entry.name
                else:
                   relpath = '/'.join([path, entry.name])
                files.append(GitMD(entry.name, relpath, entry.id))
        return files

    def files_in_branch(self, branch):
        tree = self.repo.revparse_single(branch).tree
        return self.files_in_tree(tree, '')

    def files_in_repo(self):
        ret = {}
        for bname in self.branches:
            branch = {}
            files = self.files_in_branch(bname)
            for file in files:
                if file.name.endswith(FILE_EXTENSION):
                    name = os.path.splitext(file.name)[0]
                    relpath = os.path.dirname(file.path)
                    if callable(self._class_name_mangler):
                        relpath, name = self._class_name_mangler(relpath, name)
                    if name in ret:
                        raise reclass.errors.DuplicateNodeNameError(self.url + ' - ' + bname, name, ret[name], file)
                    else:
                        branch[name] = file
            ret[bname] = branch
        return ret

    def nodes(self, branch, subdir):
        ret = {}
        for (name, file) in iteritems(self.files[branch]):
            if subdir is None or name.startswith(subdir):
                node_name = os.path.splitext(file.name)[0]
                relpath = os.path.dirname(file.path)
                if callable(self._node_name_mangler):
                    relpath, node_name = self._node_name_mangler(relpath, node_name)
                if node_name in ret:
                    raise reclass.errors.DuplicateNodeNameError(self.url, name, ret[node_name].path, file.path)
                else:
                    ret[node_name] = file
        return ret


class ExternalNodeStorage(ExternalNodeStorageBase):
    def __init__(self, nodes_uri, classes_uri, compose_node_name):
        super(ExternalNodeStorage, self).__init__(STORAGE_NAME, compose_node_name)
        self._repos = dict()

        if nodes_uri is not None:
            self._nodes_uri = GitURI({ 'branch': 'master' })
            self._nodes_uri.update(nodes_uri)
            self._load_repo(self._nodes_uri)
            self._nodes = self._repos[self._nodes_uri.repo].nodes(self._nodes_uri.branch, self._nodes_uri.root)

        if classes_uri is not None:
            self._classes_default_uri = GitURI({ 'branch': '__env__' })
            self._classes_default_uri.update(classes_uri)
            self._load_repo(self._classes_default_uri)

            self._classes_uri = []
            if 'env_overrides' in classes_uri:
                for override in classes_uri['env_overrides']:
                    for (env, options) in iteritems(override):
                        uri = GitURI(self._classes_default_uri)
                        uri.update({ 'branch': env })
                        uri.update(options)
                        self._classes_uri.append((env, uri))
                        self._load_repo(uri)

            self._classes_uri.append(('*', self._classes_default_uri))

    nodes_uri = property(lambda self: self._nodes_uri)
    classes_uri = property(lambda self: self._classes_uri)

    def get_node(self, name, settings):
        file = self._nodes[name]
        blob = self._repos[self._nodes_uri.repo].get(file.id)
        uri = 'git_fs://{0} {1} {2}'.format(self._nodes_uri.repo, self._nodes_uri.branch, file.path)
        pathname = os.path.splitext(file.path)[0]
        entity = YamlData.from_string(blob.data, uri).get_entity(name, pathname, settings)
        return entity

    def get_class(self, name, environment, settings):
        uri = self._env_to_uri(environment)
        if uri.root is not None:
            name = '{0}.{1}'.format(uri.root, name)
        if uri.repo not in self._repos:
            raise reclass.errors.NotFoundError("Repo " + uri.repo + " unknown or missing")
        if uri.branch not in self._repos[uri.repo].files:
            raise reclass.errors.NotFoundError("Branch " + uri.branch + " missing from " + uri.repo)
        if name not in self._repos[uri.repo].files[uri.branch]:
            raise reclass.errors.NotFoundError("File " + name + " missing from " + uri.repo + " branch " + uri.branch)
        file = self._repos[uri.repo].files[uri.branch][name]
        blob = self._repos[uri.repo].get(file.id)
        uri = 'git_fs://{0} {1} {2}'.format(uri.repo, uri.branch, file.path)
        pathname = os.path.splitext(file.path)[0]
        entity = YamlData.from_string(blob.data, uri).get_entity(name, pathname, settings)
        return entity

    def enumerate_nodes(self):
        return self._nodes.keys()

    def _load_repo(self, uri):
        if uri.repo not in self._repos:
            self._repos[uri.repo] = GitRepo(uri, self.node_name_mangler, self.class_name_mangler)

    def _env_to_uri(self, environment):
        ret = None
        if environment is None:
            ret = self._classes_default_uri
        else:
            for env, uri in self._classes_uri:
                if env == environment:
                    ret = uri
                    break
        if ret is None:
            ret = self._classes_default_uri
        if ret.branch == '__env__':
            ret.branch = environment
        if ret.branch == None:
            ret.branch = 'master'
        return ret
