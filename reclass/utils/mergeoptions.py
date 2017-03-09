from reclass.defaults import *

class MergeOptions(object):
    def __init__ (self):
        self.allow_scalar_over_dict = MERGE_ALLOW_SCALAR_OVER_DICT
        self.allow_scalar_over_list = MERGE_ALLOW_SCALAR_OVER_LIST
        self.allow_list_over_scalar = MERGE_ALLOW_LIST_OVER_SCALAR
        self.allow_dict_over_scalar = MERGE_ALLOW_DICT_OVER_SCALAR
