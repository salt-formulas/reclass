from reclass.settings import Settings
from reclass.values.value import Value
from reclass.values.compitem import CompItem
from reclass.values.scaitem import ScaItem
from reclass.values.valuelist import ValueList
from reclass.values.listitem import ListItem
from reclass.values.dictitem import DictItem
from reclass.values.item import ContainerItem
from reclass.values.item import ItemWithReferences
from reclass.utils.parameterdict import ParameterDict
from reclass.utils.parameterlist import ParameterList

import unittest
from mock import MagicMock

SETTINGS = Settings()


class TestItemWithReferences(unittest.TestCase):

    def test_assembleRef_allrefs(self):
        phonyitem = MagicMock()
        phonyitem.has_references = True
        phonyitem.get_references = lambda *x: [1]

        iwr = ItemWithReferences([phonyitem], {})

        self.assertEquals(iwr.get_references(), [1])
        self.assertTrue(iwr.allRefs)

    def test_assembleRef_partial(self):
        phonyitem = MagicMock()
        phonyitem.has_references = True
        phonyitem.allRefs = False
        phonyitem.get_references = lambda *x: [1]

        iwr = ItemWithReferences([phonyitem], {})

        self.assertEquals(iwr.get_references(), [1])
        self.assertFalse(iwr.allRefs)


class TestContainerItem(unittest.TestCase):

    def test_render(self):
        scalar1 = ScaItem(1, SETTINGS)
        scalar2 = ScaItem(2, SETTINGS)
        container = ContainerItem(ParameterList([ scalar1, scalar2 ]), SETTINGS)

        self.assertEquals(container.render(None, None), ParameterList([ scalar1, scalar2 ]))

if __name__ == '__main__':
    unittest.main()
