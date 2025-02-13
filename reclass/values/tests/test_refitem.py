from reclass import errors

from reclass.settings import Settings
from reclass.values.value import Value
from reclass.values.compitem import CompItem
from reclass.values.scaitem import ScaItem
from reclass.values.valuelist import ValueList
from reclass.values.listitem import ListItem
from reclass.values.dictitem import DictItem
from reclass.values.refitem import RefItem
import unittest
try:
    import unittest.mock as mock
except ImportError:
    import mock

SETTINGS = Settings()

class TestRefItem(unittest.TestCase):

    def test_assembleRefs_ok(self):
        phonyitem = mock.MagicMock()
        phonyitem.render = lambda x, k: 'bar'
        phonyitem.has_references = True
        phonyitem.get_references = lambda *x: ['foo']

        iwr = RefItem([phonyitem], {})

        self.assertEquals(iwr.get_references(), ['foo', 'bar'])
        self.assertTrue(iwr.allRefs)

    def test_assembleRefs_failedrefs(self):
        phonyitem = mock.MagicMock()
        phonyitem.render.side_effect = errors.ResolveError('foo')
        phonyitem.has_references = True
        phonyitem.get_references = lambda *x: ['foo']

        iwr = RefItem([phonyitem], {})

        self.assertEquals(iwr.get_references(), ['foo'])
        self.assertFalse(iwr.allRefs)

    def test__resolve_ok(self):
        reference = RefItem('', Settings({'delimiter': ':'}))

        result = reference._resolve('foo:bar', {'foo':{'bar': 1}})

        self.assertEquals(result, 1)

    def test__resolve_fails(self):
        refitem = RefItem('', Settings({'delimiter': ':'}))
        context = {'foo':{'bar': 1}}
        reference = 'foo:baz'

        self.assertRaises(errors.ResolveError, refitem._resolve, reference,
                          context)


if __name__ == '__main__':
    unittest.main()
