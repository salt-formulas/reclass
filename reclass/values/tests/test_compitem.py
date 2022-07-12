from reclass.settings import Settings
from reclass.values.value import Value
from reclass.values.compitem import CompItem
from reclass.values.scaitem import ScaItem
from reclass.values.valuelist import ValueList
from reclass.values.listitem import ListItem
from reclass.values.dictitem import DictItem
from reclass.values.refitem import RefItem
from reclass.utils.parameterdict import ParameterDict
from reclass.utils.parameterlist import ParameterList

import unittest

SETTINGS = Settings()

class TestCompItem(unittest.TestCase):

    def test_assembleRefs_no_items(self):
        composite = CompItem([], SETTINGS)

        self.assertFalse(composite.has_references)

    def test_assembleRefs_one_item_without_refs(self):
        val1 = Value('foo',  SETTINGS, '')
        composite = CompItem([val1._item], SETTINGS)

        self.assertFalse(composite.has_references)

    def test_assembleRefs_one_item_with_one_ref(self):
        val1 = Value('${foo}',  SETTINGS, '')
        expected_refs = ['foo']

        composite = CompItem([val1._item], SETTINGS)

        self.assertTrue(composite.has_references)
        self.assertEquals(composite.get_references(), expected_refs)

    def test_assembleRefs_one_item_with_two_refs(self):
        val1 = Value('${foo}${bar}',  SETTINGS, '')
        expected_refs = ['foo', 'bar']

        composite = CompItem([val1._item], SETTINGS)

        self.assertTrue(composite.has_references)
        self.assertEquals(composite.get_references(), expected_refs)

    def test_assembleRefs_two_items_one_with_one_ref_one_without(self):
        val1 = Value('${foo}bar',  SETTINGS, '')
        val2 = Value('baz',  SETTINGS, '')
        expected_refs = ['foo']

        composite = CompItem([val1._item, val2._item], SETTINGS)

        self.assertTrue(composite.has_references)
        self.assertEquals(composite.get_references(), expected_refs)

    def test_assembleRefs_two_items_both_with_one_ref(self):
        val1 = Value('${foo}',  SETTINGS, '')
        val2 = Value('${bar}',  SETTINGS, '')
        expected_refs = ['foo', 'bar']

        composite = CompItem([val1._item, val2._item], SETTINGS)

        self.assertTrue(composite.has_references)
        self.assertEquals(composite.get_references(), expected_refs)

    def test_assembleRefs_two_items_with_two_refs(self):
        val1 = Value('${foo}${baz}',  SETTINGS, '')
        val2 = Value('${bar}${meep}',  SETTINGS, '')
        expected_refs = ['foo', 'baz', 'bar', 'meep']

        composite = CompItem([val1._item, val2._item], SETTINGS)

        self.assertTrue(composite.has_references)
        self.assertEquals(composite.get_references(), expected_refs)

    def test_string_representation(self):
        val1 = Value(1,  SETTINGS, '')
        composite = CompItem(val1._item, SETTINGS)
        expected = '1'

        result = str(composite)

        self.assertEquals(result, expected)

    def test_render_single_item(self):
        val1 = Value('${foo}',  SETTINGS, '')

        composite = CompItem([val1._item], SETTINGS)

        self.assertEquals(1, composite.render({'foo': 1}, None))


    def test_render_multiple_items(self):
        val1 = Value('${foo}',  SETTINGS, '')
        val2 = Value('${bar}',  SETTINGS, '')

        composite = CompItem([val1._item, val2._item], SETTINGS)

        self.assertEquals('12', composite.render({'foo': 1, 'bar': 2}, None))

    def test_merge_over_merge_scalar(self):
        val1 = Value(None, SETTINGS, '')
        scalar = ScaItem(1, SETTINGS)
        composite = CompItem([val1._item], SETTINGS)

        result = composite.merge_over(scalar)

        self.assertEquals(result, composite)

    def test_merge_over_merge_composite(self):
        val1 = Value(None, SETTINGS, '')
        val2 = Value(None, SETTINGS, '')
        composite1 = CompItem([val1._item], SETTINGS)
        composite2 = CompItem([val2._item], SETTINGS)

        result = composite2.merge_over(composite1)

        self.assertEquals(result, composite2)

    def test_merge_other_types_not_allowed(self):
        scalar1 = ScaItem(1, SETTINGS)
        scalar2 = ScaItem(2, SETTINGS)
        other = ListItem(ParameterList([ scalar1, scalar2 ]), SETTINGS)
        val1 = Value(None, SETTINGS, '')
        composite = CompItem([val1._item], SETTINGS)

        self.assertRaises(RuntimeError, composite.merge_over, other)


if __name__ == '__main__':
    unittest.main()
