#
# -*- coding: utf-8 -*-
#
# This file is part of reclass (http://github.com/madduck/reclass)
#
# Copyright © 2007–14 martin f. krafft <madduck@madduck.net>
# Released under the terms of the Artistic Licence 2.0
#

import copy
import time
import re
import sys
import fnmatch
import shlex
import string
import yaml
from reclass.output.yaml_outputter import ExplicitDumper
from reclass.datatypes import Entity, Classes, Parameters, Exports
from reclass.errors import MappingFormatError, ClassNotFound
from reclass.defaults import AUTOMATIC_RECLASS_PARAMETERS

class Core(object):

    def __init__(self, storage, class_mappings, input_data=None, default_environment=None,
            ignore_class_notfound=False, ignore_class_regexp=['*']):
        self._storage = storage
        self._class_mappings = class_mappings
        self._ignore_class_notfound = ignore_class_notfound
        self._input_data = input_data
        self._default_environment = default_environment

        if type(ignore_class_regexp) == type(''):
          self._ignore_class_regexp = [ignore_class_regexp]
        else:
          self._ignore_class_regexp = ignore_class_regexp

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
        except ValueError, e:
            raise MappingFormatError('Error in mapping "{0}": missing closing '
                                     'quote (or slash)'.format(instr))
        if regexp:
            key = '/{0}/'.format(key)
        return key, list(lexer)

    def _get_class_mappings_entity(self, nodename):
        if not self._class_mappings:
            return Entity(name='empty (class mappings)')
        c = Classes()
        for mapping in self._class_mappings:
            matched = False
            key, klasses = Core._shlex_split(mapping)
            if key[0] == ('/'):
                matched = Core._match_regexp(key[1:-1], nodename)
                if matched:
                    for klass in klasses:
                        c.append_if_new(matched.expand(klass))

            else:
                if Core._match_glob(key, nodename):
                    for klass in klasses:
                        c.append_if_new(klass)

        return Entity(classes=c,
                      name='class mappings for node {0}'.format(nodename))

    def _get_input_data_entity(self):
        if not self._input_data:
            return Entity(name='empty (input data)')
        p = Parameters(self._input_data)
        return Entity(parameters=p, name='input data')

    def _recurse_entity(self, entity, merge_base=None, seen=None, nodename=None, environment=None):
        if seen is None:
            seen = {}

        if environment is None:
            environment = self._default_environment

        if merge_base is None:
            merge_base = Entity(name='empty (@{0})'.format(nodename))

        cnf_r = None # class_notfound_regexp compiled
        for klass in entity.classes.as_list():
            if klass not in seen:
                try:
                    class_entity = self._storage.get_class(klass, environment)
                except ClassNotFound, e:
                    if self._ignore_class_notfound:
                        if not cnf_r:
                            cnf_r = re.compile('|'.join([x for x in self._ignore_class_regexp]))
                        if cnf_r.match(klass):
                            # TODO, add logging handler
                            print >>sys.stderr, "[WARNING] Reclass class not found: '%s'. Skipped!" % klass
                            continue
                    e.set_nodename(nodename)
                    raise e

                descent = self._recurse_entity(class_entity, seen=seen,
                                               nodename=nodename, environment=environment)
                # on every iteration, we merge the result of the recursive
                # descent into what we have so far…
                merge_base.merge(descent)
                seen[klass] = True

        # … and finally, we merge what we have at this level into the
        # result of the iteration, so that elements at the current level
        # overwrite stuff defined by parents
        merge_base.merge(entity)
        return merge_base

    def _get_automatic_parameters(self, nodename, environment):
        if AUTOMATIC_RECLASS_PARAMETERS:
            return Parameters({ '_reclass_': { 'name': { 'full': nodename, 'short': string.split(nodename, '.')[0] },
                                               'environment': environment } })
        else:
            return Parameters()

    def _get_inventory(self):
        inventory = {}
        for nodename in self._storage.enumerate_nodes():
            node = self._node_entity(nodename)
            node.interpolate_exports()
            inventory[nodename] = node.exports.as_dict()
        return inventory

    def _node_entity(self, nodename):
        node_entity = self._storage.get_node(nodename)
        if node_entity.environment == None:
            node_entity.environment = self._default_environment
        base_entity = Entity(name='base')
        base_entity.merge(self._get_class_mappings_entity(node_entity.name))
        base_entity.merge(self._get_input_data_entity())
        base_entity.merge_parameters(self._get_automatic_parameters(nodename, node_entity.environment))
        seen = {}
        merge_base = self._recurse_entity(base_entity, seen=seen, nodename=base_entity.name,
                                          environment=node_entity.environment)
        return self._recurse_entity(node_entity, merge_base, seen=seen, nodename=node_entity.name,
                                    environment=node_entity.environment)

    def _nodeinfo(self, nodename, inventory):
        ret = self._node_entity(nodename)
        ret.initialise_interpolation()
        if ret.parameters.has_inv_query() and inventory is None:
            inventory = self._get_inventory()
        ret.interpolate(nodename, inventory)
        return ret

    def _nodeinfo_as_dict(self, nodename, entity):
        ret = {'__reclass__' : {'node': entity.name, 'name': nodename,
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
        inventory = self._get_inventory()
        for n in self._storage.enumerate_nodes():
            entities[n] = self._nodeinfo(n, inventory)
            if entities[n].parameters.has_inv_query():
                nodes.add(n)
        for n in query_nodes:
            entities[n] = self._nodeinfo(n, inventory)

        nodes = {}
        applications = {}
        classes = {}
        for f, nodeinfo in entities.iteritems():
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
