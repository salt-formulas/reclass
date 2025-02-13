from reclass.settings import Settings
from reclass.values.value import Value
from reclass.values.compitem import CompItem
from reclass.values.scaitem import ScaItem
from reclass.values.valuelist import ValueList
from reclass.values.listitem import ListItem
from reclass.values.dictitem import DictItem
from reclass.values.item import ContainerItem
from reclass.values.item import ItemWithReferences
import unittest
try:
    import unittest.mock as mock
except ImportError:
    import mock

SETTINGS = Settings()


class TestItemWithReferences(unittest.TestCase):

    def test_assembleRef_allrefs(self):
        phonyitem = mock.MagicMock()
        phonyitem.has_references = True
        phonyitem.get_references = lambda *x: [1]

        iwr = ItemWithReferences([phonyitem], {})

        self.assertEquals(iwr.get_references(), [1])
        self.assertTrue(iwr.allRefs)

    def test_assembleRef_partial(self):
        phonyitem = mock.MagicMock()
        phonyitem.has_references = True
        phonyitem.allRefs = False
        phonyitem.get_references = lambda *x: [1]

        iwr = ItemWithReferences([phonyitem], {})

        self.assertEquals(iwr.get_references(), [1])
        self.assertFalse(iwr.allRefs)


class TestContainerItem(unittest.TestCase):

    def test_render(self):
        container = ContainerItem('foo', SETTINGS)

        self.assertEquals(container.render(None, None), 'foo')

if __name__ == '__main__':
    unittest.main()
