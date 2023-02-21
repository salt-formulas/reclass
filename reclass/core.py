#
# -*- coding: utf-8 -*-
#
# This file is part of reclass (http://github.com/madduck/reclass)
#
# Copyright © 2007–14 martin f. krafft <madduck@madduck.net>
# Released under the terms of the Artistic Licence 2.0
#
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import copy
import time
import re
import fnmatch
import shlex
import string
import sys
import yaml

from six import iteritems

from reclass.settings import Settings
from reclass.datatypes import Entity, Classes, Parameters, Exports
from reclass.errors import MappingFormatError, ClassNameResolveError, ClassNotFound, InvQueryClassNameResolveError, InvQueryClassNotFound, InvQueryError, InterpolationError, ResolveError
from reclass.values.parser import Parser


class Core(object):

    _parser = Parser()

    def __init__(self, storage, class_mappings, settings, input_data=None):
        self._storage = storage
        self._class_mappings = class_mappings
        self._settings = settings
        self._input_data = input_data
        if self._settings.ignore_class_notfound:
            self._cnf_r = re.compile(
                '|'.join(self._settings.ignore_class_notfound_regexp))

    @staticmethod
    def _get_timestamp():
        return time.strftime('%c')

    @staticmethod
    def _match_regexp(key, nodename):
        return re.search(key, nodename)

    @staticmethod
    def _match_glob(key, nodename):
        return fnmatch.fnmatchcase(nodename, key)

    @staticmethod
    def _shlex_split(instr):
        lexer = shlex.shlex(instr, posix=True)
        lexer.whitespace_split = True
        lexer.commenters = ''
        regexp = False
        if instr[0] == '/':
            lexer.quotes += '/'
            lexer.escapedquotes += '/'
            regexp = True
        try:
            key = lexer.get_token()
        except ValueError as e:
            raise MappingFormatError('Error in mapping "{0}": missing closing '
                                     'quote (or slash)'.format(instr))
        if regexp:
            key = '/{0}/'.format(key)
        return key, list(lexer)

    def _get_class_mappings_entity(self, entity):
        if not self._class_mappings:
            return Entity(self._settings, name='empty (class mappings)')
        c = Classes()
        if self._settings.class_mappings_match_path:
            matchname = entity.pathname
        else:
            matchname = entity.name
        for mapping in self._class_mappings:
            matched = False
            key, klasses = Core._shlex_split(mapping)
            if key[0] == ('/'):
                matched = Core._match_regexp(key[1:-1], matchname)
                if matched:
                    for klass in klasses:
                        c.append_if_new(matched.expand(klass))

            else:
                if Core._match_glob(key, matchname):
                    for klass in klasses:
                        c.append_if_new(klass)

        return Entity(self._settings, classes=c,
                      name='class mappings for node {0}'.format(entity.name))

    def _get_input_data_entity(self):
        if not self._input_data:
            return Entity(self._settings, name='empty (input data)')
        p = Parameters(self._input_data, self._settings)
        return Entity(self._settings, parameters=p, name='input data')

    def _recurse_entity(self, entity, merge_base=None, seen=None, nodename=None, environment=None):
        if seen is None:
            seen = {}

        if environment is None:
            environment = self._settings.default_environment

        if merge_base is None:
            merge_base = Entity(self._settings, name='empty (@{0})'.format(nodename))

        for klass in entity.classes.as_list():
            # class name contain reference
            num_references = klass.count(self._settings.reference_sentinels[0]) +\
                             klass.count(self._settings.export_sentinels[0])
            if num_references > 0:
                # Make a copy of merge_base.parameters to avoid running into
                # issues as new data is merged into merge_base.parameters.
                # We need to make a new copy on each pass to ensure we don't
                # try to resolve references using a stale set of parameters,
                # as merge_base is updated in the loop.
                mbparams = copy.deepcopy(merge_base.parameters)
                # Enable interpolation for copy of parameters before using the
                # copy to resolve references in class names
                mbparams.initialise_interpolation()
                try:
                    klass = str(self._parser.parse(klass, self._settings).render(mbparams.as_dict(), {}))
                except ResolveError as e:
                    raise ClassNameResolveError(klass, nodename, entity.uri)

            if klass not in seen:
                try:
                    class_entity = self._storage.get_class(klass, environment, self._settings)
                except ClassNotFound as e:
                    if self._settings.ignore_class_notfound:
                        if self._cnf_r.match(klass):
                            if self._settings.ignore_class_notfound_warning:
                                # TODO, add logging handler
                                print("[WARNING] Reclass class not found: '%s'. Skipped!" % klass, file=sys.stderr)
                            continue
                    e.nodename = nodename
                    e.uri = entity.uri
                    raise

                # on every iteration, we pass what we have so far into the
                # recursive descent …
                descent = self._recurse_entity(class_entity, merge_base=merge_base, seen=seen,
                                               nodename=nodename, environment=environment)
                # … therefore, we don't need to merge the result of the
                # recursive descent as the result is a reference to the same
                # merge_base object we passed to the call originally, with the
                # new values merged in …
                assert descent == merge_base
                seen[klass] = True

        # … and finally, we merge what we have at this level into the
        # result of the iteration, so that elements at the current level
        # overwrite stuff defined by parents
        merge_base.merge(entity)
        return merge_base

    def _get_automatic_parameters(self, nodename, environment):
        if self._settings.automatic_parameters:
            pars = {
                '_reclass_': {
                    'name': {
                        'full': nodename,
                        'short': nodename.split('.').pop(),
                        'parts': nodename.split('.')
                    },
                'environment': environment
                }
            }
            return Parameters(pars, self._settings, '__auto__')
        else:
            return Parameters({}, self._settings, '')

    def _get_inventory(self, all_envs, environment, queries):
        inventory = {}
        for nodename in self._storage.enumerate_nodes():
            try:
                node_base = self._storage.get_node(nodename, self._settings)
                if node_base.environment is None:
                    node_base.environment = self._settings.default_environment
            except yaml.scanner.ScannerError as e:
                if self._settings.inventory_ignore_failed_node:
                    continue
                raise

            if all_envs or node_base.environment == environment:
                try:
                    node = self._node_entity(nodename)
                except ClassNotFound as e:
                    raise InvQueryClassNotFound(e)
                except ClassNameResolveError as e:
                    raise InvQueryClassNameResolveError(e)
                if queries is None:
                    try:
                        node.interpolate_exports()
                    except InterpolationError as e:
                        e.nodename = nodename
                else:
                    node.initialise_interpolation()
                    for p, q in queries:
                        try:
                            node.interpolate_single_export(q)
                        except InterpolationError as e:
                            e.nodename = nodename
                            raise InvQueryError(q.contents, e, context=p, uri=q.uri)
                inventory[nodename] = node.exports.as_dict()
        return inventory

    def _node_entity(self, nodename):
        node_entity = self._storage.get_node(nodename, self._settings)
        if node_entity.environment == None:
            node_entity.environment = self._settings.default_environment
        base_entity = Entity(self._settings, name='base')
        base_entity.merge(self._get_class_mappings_entity(node_entity))
        base_entity.merge(self._get_input_data_entity())
        base_entity.merge_parameters(self._get_automatic_parameters(nodename, node_entity.environment))
        seen = {}
        merge_base = self._recurse_entity(base_entity, seen=seen, nodename=nodename,
                                          environment=node_entity.environment)
        return self._recurse_entity(node_entity, merge_base=merge_base, seen=seen,
                                    nodename=nodename, environment=node_entity.environment)

    def _nodeinfo(self, nodename, inventory):
        try:
            node = self._node_entity(nodename)
            node.initialise_interpolation()
            if node.parameters.has_inv_query and inventory is None:
                inventory = self._get_inventory(node.parameters.needs_all_envs, node.environment, node.parameters.get_inv_queries())
            node.interpolate(inventory)
            return node
        except InterpolationError as e:
            e.nodename = nodename
            raise

    def _nodeinfo_as_dict(self, nodename, entity):
        ret = {'__reclass__' : {'node': entity.name,
                                'name': nodename,
                                'uri': entity.uri,
                                'environment': entity.environment,
                                'timestamp': Core._get_timestamp()
                               },
              }
        ret.update(entity.as_dict())
        return ret

    def nodeinfo(self, nodename):
        return self._nodeinfo_as_dict(nodename, self._nodeinfo(nodename, None))

    def inventory(self):
        query_nodes = set()
        entities = {}
        inventory = self._get_inventory(True, '', None)
        for n in self._storage.enumerate_nodes():
            entities[n] = self._nodeinfo(n, inventory)
            if entities[n].parameters.has_inv_query:
                nodes.add(n)
        for n in query_nodes:
            entities[n] = self._nodeinfo(n, inventory)

        nodes = {}
        applications = {}
        classes = {}
        for (f, nodeinfo) in iteritems(entities):
            d = nodes[f] = self._nodeinfo_as_dict(f, nodeinfo)
            for a in d['applications']:
                if a in applications:
                    applications[a].append(f)
                else:
                    applications[a] = [f]
            for c in d['classes']:
                if c in classes:
                    classes[c].append(f)
                else:
                    classes[c] = [f]

        return {'__reclass__' : {'timestamp': Core._get_timestamp()},
                'nodes': nodes,
                'classes': classes,
                'applications': applications
               }
