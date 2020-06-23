# -*- coding: utf-8

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import reclass.defaults as defaults

from six import string_types, iteritems


class Settings(object):

    known_opts = {
        'allow_adapter_env_override': defaults.OPT_ALLOW_ADAPTER_ENV_OVERRIDE,
        'allow_scalar_over_dict': defaults.OPT_ALLOW_SCALAR_OVER_DICT,
        'allow_scalar_over_list': defaults.OPT_ALLOW_SCALAR_OVER_LIST,
        'allow_list_over_scalar': defaults.OPT_ALLOW_LIST_OVER_SCALAR,
        'allow_dict_over_scalar': defaults.OPT_ALLOW_DICT_OVER_SCALAR,
        'allow_none_override': defaults.OPT_ALLOW_NONE_OVERRIDE,
        'automatic_parameters': defaults.AUTOMATIC_RECLASS_PARAMETERS,
        'class_mappings_match_path': defaults.CLASS_MAPPINGS_MATCH_PATH,
        'default_environment': defaults.DEFAULT_ENVIRONMENT,
        'delimiter': defaults.PARAMETER_INTERPOLATION_DELIMITER,
        'dict_key_override_prefix':
            defaults.PARAMETER_DICT_KEY_OVERRIDE_PREFIX,
        'dict_key_constant_prefix':
            defaults.PARAMETER_DICT_KEY_CONSTANT_PREFIX,
        'escape_character': defaults.ESCAPE_CHARACTER,
        'export_sentinels': defaults.EXPORT_SENTINELS,
        'inventory_ignore_failed_node':
            defaults.OPT_INVENTORY_IGNORE_FAILED_NODE,
        'inventory_ignore_failed_render':
            defaults.OPT_INVENTORY_IGNORE_FAILED_RENDER,
        'reference_sentinels': defaults.REFERENCE_SENTINELS,
        'ignore_class_notfound': defaults.OPT_IGNORE_CLASS_NOTFOUND,
        'strict_constant_parameters':
            defaults.OPT_STRICT_CONSTANT_PARAMETERS,
        'ignore_class_notfound_regexp':
            defaults.OPT_IGNORE_CLASS_NOTFOUND_REGEXP,
        'ignore_class_notfound_warning':
            defaults.OPT_IGNORE_CLASS_NOTFOUND_WARNING,
        'ignore_overwritten_missing_references':
            defaults.OPT_IGNORE_OVERWRITTEN_MISSING_REFERENCES,
        'group_errors': defaults.OPT_GROUP_ERRORS,
        'compose_node_name': defaults.OPT_COMPOSE_NODE_NAME,
    }

    def __init__(self, options={}):
        for opt_name, opt_value in iteritems(self.known_opts):
            setattr(self, opt_name, options.get(opt_name, opt_value))

        self.dict_key_prefixes = [str(self.dict_key_override_prefix),
                                  str(self.dict_key_constant_prefix)]
        if isinstance(self.ignore_class_notfound_regexp, string_types):
            self.ignore_class_notfound_regexp = [
                    self.ignore_class_notfound_regexp]

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return all(getattr(self, opt) == getattr(other, opt)
                       for opt in self.known_opts)
        return False

    def __copy__(self):
        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__)
        return result

    def __deepcopy__(self, memo):
        return self.__copy__()
