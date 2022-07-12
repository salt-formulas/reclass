from reclass.settings import Settings
from reclass.values.value import Value
from reclass.values.compitem import CompItem
from reclass.values.scaitem import ScaItem
from reclass.values.valuelist import ValueList
from reclass.values.listitem import ListItem
from reclass.values.dictitem import DictItem
from reclass.utils.parameterdict import ParameterDict
from reclass.utils.parameterlist import ParameterList

import unittest

SETTINGS = Settings()

class TestListItem(unittest.TestCase):

    def test_merge_over_merge_list(self):
        val1 = Value(1, SETTINGS, '')
        val2 = Value(2, SETTINGS, '')
        listitem1 = ListItem(ParameterList([ val1 ]), SETTINGS)
        listitem2 = ListItem(ParameterList([ val2 ]), SETTINGS)
        expected = ListItem(ParameterList([ val1, val2 ]), SETTINGS)

        result = listitem2.merge_over(listitem1)

        self.assertEquals(result.contents, expected.contents)

    def test_merge_other_types_not_allowed(self):
        other = Value(1, SETTINGS, '')
        listitem = ListItem(ParameterList([other]), SETTINGS)

        self.assertRaises(RuntimeError, listitem.merge_over, other._item)

if __name__ == '__main__':
    unittest.main()
