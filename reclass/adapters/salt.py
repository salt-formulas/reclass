#!/usr/bin/env python
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

import os, sys, posix

from six import iteritems

from reclass import get_storage, output, get_path_mangler
from reclass.core import Core
from reclass.errors import ReclassException
from reclass.config import find_and_read_configfile, get_options
from reclass.constants import MODE_NODEINFO, MODE_NODEAPPS
from reclass.defaults import *
from reclass.settings import Settings
from reclass.version import *

def ext_pillar(minion_id, pillar,
               pillarenv=None,
               storage_type=OPT_STORAGE_TYPE,
               inventory_base_uri=OPT_INVENTORY_BASE_URI,
               nodes_uri=OPT_NODES_URI,
               classes_uri=OPT_CLASSES_URI,
               class_mappings=None,
               propagate_pillar_data_to_reclass=False,
               compose_node_name=OPT_COMPOSE_NODE_NAME,
               allow_adapter_env_override=OPT_ALLOW_ADAPTER_ENV_OVERRIDE,
               **kwargs):

    path_mangler = get_path_mangler(storage_type)
    nodes_uri, classes_uri = path_mangler(inventory_base_uri, nodes_uri, classes_uri)
    storage = get_storage(storage_type, nodes_uri, classes_uri, compose_node_name)
    input_data = None
    if propagate_pillar_data_to_reclass:
        input_data = pillar
    if not allow_adapter_env_override:
        pillarenv = None

    settings = Settings(kwargs)
    reclass = Core(storage, class_mappings, settings, input_data=input_data)

    data = reclass.nodeinfo(minion_id, override_environment=pillarenv)
    params = data.get('parameters', {})
    params['__reclass__'] = {}
    params['__reclass__']['nodename'] = minion_id
    params['__reclass__']['applications'] = data['applications']
    params['__reclass__']['classes'] = data['classes']
    params['__reclass__']['environment'] = data['environment']
    return params


def top(minion_id,
        pillarenv=None,
        storage_type=OPT_STORAGE_TYPE,
        inventory_base_uri=OPT_INVENTORY_BASE_URI,
        nodes_uri=OPT_NODES_URI,
        classes_uri=OPT_CLASSES_URI,
        class_mappings=None,
        compose_node_name=OPT_COMPOSE_NODE_NAME,
        allow_adapter_env_override=OPT_ALLOW_ADAPTER_ENV_OVERRIDE,
        **kwargs):

    path_mangler = get_path_mangler(storage_type)
    nodes_uri, classes_uri = path_mangler(inventory_base_uri, nodes_uri, classes_uri)
    storage = get_storage(storage_type, nodes_uri, classes_uri, compose_node_name)
    settings = Settings(kwargs)
    reclass = Core(storage, class_mappings, settings, input_data=None)

    if not allow_adapter_env_override:
        pillarenv = None

    # if the minion_id is not None, then return just the applications for the
    # specific minion, otherwise return the entire top data (which we need for
    # CLI invocations of the adapter):
    if minion_id is not None:
        data = reclass.nodeinfo(minion_id, override_environment=pillarenv)
        applications = data.get('applications', [])
        env = data['environment']
        return {env: applications}

    else:
        data = reclass.inventory()
        nodes = {}
        for (node_id, node_data) in iteritems(data['nodes']):
            env = node_data['environment']
            if env not in nodes:
                nodes[env] = {}
            nodes[env][node_id] = node_data['applications']

        return nodes


def cli():
    try:
        inventory_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
        defaults = {'pretty_print' : True,
                    'no_refs' : False,
                    'output' : 'yaml',
                    'inventory_base_uri': inventory_dir
                   }
        defaults.update(find_and_read_configfile())
        options = get_options(RECLASS_NAME, VERSION, DESCRIPTION,
                              inventory_shortopt='-t',
                              inventory_longopt='--top',
                              inventory_help='output the state tops (inventory)',
                              nodeapps_shortopt='-f',
                              nodeapps_longopt='--formulas',
                              nodeapps_dest='nodename',
                              nodeapps_help='output applications list for a specific node',
                              nodeinfo_shortopt='-p',
                              nodeinfo_longopt='--pillar',
                              nodeinfo_dest='nodename',
                              nodeinfo_help='output pillar data for a specific node',
                              defaults=defaults)
        class_mappings = defaults.get('class_mappings')
        defaults.update(vars(options))
        defaults.pop("storage_type", None)
        defaults.pop("inventory_base_uri", None)
        defaults.pop("nodes_uri", None)
        defaults.pop("classes_uri", None)
        defaults.pop("class_mappings", None)
        defaults.pop("pillarenv", None)

        if options.mode == MODE_NODEINFO:
            data = ext_pillar(
                     options.nodename, {},
                     pillarenv=options.environment,
                     storage_type=options.storage_type,
                     inventory_base_uri=options.inventory_base_uri,
                     nodes_uri=options.nodes_uri,
                     classes_uri=options.classes_uri,
                     class_mappings=class_mappings,
                     **defaults)
        elif options.mode == MODE_NODEAPPS:
            data = top(
                     minion_id=options.nodename,
                     pillarenv=options.environment,
                     storage_type=options.storage_type,
                     inventory_base_uri=options.inventory_base_uri,
                     nodes_uri=options.nodes_uri,
                     classes_uri=options.classes_uri,
                     class_mappings=class_mappings,
                     **defaults)
        else:
            data = top(
                     minion_id=None,
                     pillarenv=None,
                     storage_type=options.storage_type,
                     inventory_base_uri=options.inventory_base_uri,
                     nodes_uri=options.nodes_uri,
                     classes_uri=options.classes_uri,
                     class_mappings=class_mappings,
                     **defaults)

        print(output(data, options.output, options.pretty_print, options.no_refs))

    except ReclassException as e:
        e.exit_with_message(sys.stderr)

    sys.exit(posix.EX_OK)

if __name__ == '__main__':
    cli()
