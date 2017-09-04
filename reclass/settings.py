import reclass.values.parser_funcs
from reclass.defaults import *

class Settings(object):

    def __init__(self, options={}):
        self.allow_scalar_over_dict = options.get('allow_scalar_over_dict', ALLOW_SCALAR_OVER_DICT)
        self.allow_scalar_over_list = options.get('allow_scalar_over_list', ALLOW_SCALAR_OVER_LIST)
        self.allow_list_over_scalar = options.get('allow_list_over_scalar', ALLOW_LIST_OVER_SCALAR)
        self.allow_dict_over_scalar = options.get('allow_dict_over_scalar', ALLOW_DICT_OVER_SCALAR)
        self.automatic_parameters = options.get('automatic_parameters', AUTOMATIC_RECLASS_PARAMETERS)
        self.default_environment = options.get('default_environment', DEFAULT_ENVIRONMENT)
        self.delimiter = options.get('delimiter', PARAMETER_INTERPOLATION_DELIMITER)
        self.dict_key_override_prefix = options.get('dict_key_override_prefix', PARAMETER_DICT_KEY_OVERRIDE_PREFIX)
        self.escape_character = options.get('escape_character', ESCAPE_CHARACTER)
        self.export_sentinels = options.get('export_sentinels', EXPORT_SENTINELS)
        self.inventory_ignore_failed_node = options.get('inventory_ignore_failed_node', INVENTORY_IGNORE_FAILED_NODE)
        self.inventory_ignore_failed_render = options.get('inventory_ignore_failed_render', INVENTORY_IGNORE_FAILED_RENDER)
        self.reference_sentinels = options.get('reference_sentinels', REFERENCE_SENTINELS)
        self.ignore_class_notfound = options.get('ignore_class_notfound', OPT_IGNORE_CLASS_NOTFOUND)

        self.ref_parser = reclass.values.parser_funcs.get_ref_parser(self.escape_character, self.reference_sentinels, self.export_sentinels)
        self.simple_ref_parser = reclass.values.parser_funcs.get_simple_ref_parser(self.escape_character, self.reference_sentinels, self.export_sentinels)

    def __eq__(self, other):
        return isinstance(other, type(self)) \
               and self.allow_scalar_over_dict == other.allow_scalar_over_dict \
               and self.allow_scalar_over_list == other.allow_scalar_over_list \
               and self.allow_list_over_scalar == other.allow_list_over_scalar \
               and self.allow_dict_over_scalar == other.allow_dict_over_scalar \
               and self.automatic_parameters == other.automatic_parameters \
               and self.default_environment == other.default_environment \
               and self.delimiter == other.delimiter \
               and self.dict_key_override_prefix == other.dict_key_override_prefix \
               and self.escape_character == other.escape_character \
               and self.export_sentinels == other.export_sentinels \
               and self.reference_sentinels == other.reference_sentinels \
               and self.ignore_class_notfound == other.ignore_class_notfound
