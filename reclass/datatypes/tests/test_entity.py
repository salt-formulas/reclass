#
# -*- coding: utf-8 -*-
#
# This file is part of reclass (http://github.com/madduck/reclass)
#
# Copyright © 2007–14 martin f. krafft <madduck@madduck.net>
# Released under the terms of the Artistic Licence 2.0
#

from reclass.settings import Settings
from reclass.datatypes import Entity, Classes, Parameters, Applications, Exports
from reclass.errors import ResolveError
import unittest
try:
    import unittest.mock as mock
except ImportError:
    import mock

SETTINGS = Settings()

@mock.patch.multiple('reclass.datatypes', autospec=True, Classes=mock.DEFAULT,
                     Applications=mock.DEFAULT, Parameters=mock.DEFAULT,
                     Exports=mock.DEFAULT)
class TestEntity(unittest.TestCase):

    def _make_instances(self, Classes, Applications, Parameters, Exports):
        return Classes(), Applications(), Parameters({}, SETTINGS, ""), Exports({}, SETTINGS, "")

    def test_constructor_default(self, **mocks):
        # Actually test the real objects by calling the default constructor,
        # all other tests shall pass instances to the constructor
        e = Entity(SETTINGS)
        self.assertEqual(e.name, '')
        self.assertEqual(e.uri, '')
        self.assertIsInstance(e.classes, Classes)
        self.assertIsInstance(e.applications, Applications)
        self.assertIsInstance(e.parameters, Parameters)
        self.assertIsInstance(e.exports, Exports)

    def test_constructor_empty(self, **types):
        instances = self._make_instances(**types)
        e = Entity(SETTINGS, *instances)
        self.assertEqual(e.name, '')
        self.assertEqual(e.uri, '')
        cl, al, pl, ex = [getattr(i, '__len__') for i in instances]
        self.assertEqual(len(e.classes), cl.return_value)
        cl.assert_called_once_with()
        self.assertEqual(len(e.applications), al.return_value)
        al.assert_called_once_with()
        self.assertEqual(len(e.parameters), pl.return_value)
        pl.assert_called_once_with()
        self.assertEqual(len(e.exports), pl.return_value)
        ex.assert_called_once_with()

    def test_constructor_empty_named(self, **types):
        name = 'empty'
        e = Entity(SETTINGS, *self._make_instances(**types), name=name)
        self.assertEqual(e.name, name)

    def test_constructor_empty_uri(self, **types):
        uri = 'test://uri'
        e = Entity(SETTINGS, *self._make_instances(**types), uri=uri)
        self.assertEqual(e.uri, uri)

    def test_constructor_empty_env(self, **types):
        env = 'not base'
        e = Entity(SETTINGS, *self._make_instances(**types), environment=env)
        self.assertEqual(e.environment, env)

    def test_equal_empty(self, **types):
        instances = self._make_instances(**types)
        self.assertEqual(Entity(SETTINGS, *instances), Entity(SETTINGS, *instances))
        for i in instances:
            i.__eq__.assert_called_once_with(i)

    def test_equal_empty_named(self, **types):
        instances = self._make_instances(**types)
        self.assertEqual(Entity(SETTINGS, *instances), Entity(SETTINGS, *instances))
        name = 'empty'
        self.assertEqual(Entity(SETTINGS, *instances, name=name),
                         Entity(SETTINGS, *instances, name=name))

    def test_unequal_empty_uri(self, **types):
        instances = self._make_instances(**types)
        uri = 'test://uri'
        self.assertNotEqual(Entity(SETTINGS, *instances, uri=uri),
                            Entity(SETTINGS, *instances, uri=uri[::-1]))
        for i in instances:
            i.__eq__.assert_called_once_with(i)

    def test_unequal_empty_named(self, **types):
        instances = self._make_instances(**types)
        name = 'empty'
        self.assertNotEqual(Entity(SETTINGS, *instances, name=name),
                            Entity(SETTINGS, *instances, name=name[::-1]))
        for i in instances:
            i.__eq__.assert_called_once_with(i)

    def test_unequal_types(self, **types):
        instances = self._make_instances(**types)
        self.assertNotEqual(Entity(SETTINGS, *instances, name='empty'),
                            None)
        for i in instances:
            self.assertEqual(i.__eq__.call_count, 0)

    def _test_constructor_wrong_types(self, which_replace, **types):
        instances = self._make_instances(**types)
        instances[which_replace] = 'Invalid type'
        e = Entity(SETTINGS, *instances)

    def test_constructor_wrong_type_classes(self, **types):
        self.assertRaises(TypeError, self._test_constructor_wrong_types, 0)

    def test_constructor_wrong_type_applications(self, **types):
        self.assertRaises(TypeError, self._test_constructor_wrong_types, 1)

    def test_constructor_wrong_type_parameters(self, **types):
        self.assertRaises(TypeError, self._test_constructor_wrong_types, 2)

    def test_merge(self, **types):
        instances = self._make_instances(**types)
        e = Entity(SETTINGS, *instances)
        e.merge(e)
        for i, fn in zip(instances, ('merge_unique', 'merge_unique', 'merge')):
            getattr(i, fn).assert_called_once_with(i)

    def test_merge_newname(self, **types):
        instances = self._make_instances(**types)
        newname = 'newname'
        e1 = Entity(SETTINGS, *instances, name='oldname')
        e2 = Entity(SETTINGS, *instances, name=newname)
        e1.merge(e2)
        self.assertEqual(e1.name, newname)

    def test_merge_newuri(self, **types):
        instances = self._make_instances(**types)
        newuri = 'test://uri2'
        e1 = Entity(SETTINGS, *instances, uri='test://uri1')
        e2 = Entity(SETTINGS, *instances, uri=newuri)
        e1.merge(e2)
        self.assertEqual(e1.uri, newuri)

    def test_merge_newenv(self, **types):
        instances = self._make_instances(**types)
        newenv = 'new env'
        e1 = Entity(SETTINGS, *instances, environment='env')
        e2 = Entity(SETTINGS, *instances, environment=newenv)
        e1.merge(e2)
        self.assertEqual(e1.environment, newenv)

    def test_as_dict(self, **types):
        instances = self._make_instances(**types)
        entity = Entity(SETTINGS, *instances, name='test', environment='test')
        comp = {}
        comp['classes'] = instances[0].as_list()
        comp['applications'] = instances[1].as_list()
        comp['parameters'] = instances[2].as_dict()
        comp['exports'] = instances[3].as_dict()
        comp['environment'] = 'test'
        d = entity.as_dict()
        self.assertDictEqual(d, comp)

class TestEntityNoMock(unittest.TestCase):

    def test_exports_with_refs(self):
        inventory = {'node1': {'a': 1, 'b': 2}, 'node2': {'a': 3, 'b': 4}}
        node3_exports = Exports({'a': '${a}', 'b': '${b}'}, SETTINGS, '')
        node3_parameters = Parameters({'name': 'node3', 'a': '${c}', 'b': 5}, SETTINGS, '')
        node3_parameters.merge({'c': 3})
        node3_entity = Entity(SETTINGS, classes=None, applications=None, parameters=node3_parameters, exports=node3_exports)
        node3_entity.interpolate_exports()
        inventory['node3'] = node3_entity.exports.as_dict()
        r = {'node1': {'a': 1, 'b': 2}, 'node2': {'a': 3, 'b': 4}, 'node3': {'a': 3, 'b': 5}}
        self.assertDictEqual(inventory, r)

    def test_reference_to_an_export(self):
        inventory = {'node1': {'a': 1, 'b': 2}, 'node2': {'a': 3, 'b': 4}}
        node3_exports = Exports({'a': '${a}', 'b': '${b}'}, SETTINGS, '')
        node3_parameters = Parameters({'name': 'node3', 'ref': '${exp}', 'a': '${c}', 'b': 5}, SETTINGS, '')
        node3_parameters.merge({'c': 3, 'exp': '$[ exports:a ]'})
        node3_entity = Entity(SETTINGS, classes=None, applications=None, parameters=node3_parameters, exports=node3_exports)
        node3_entity.interpolate_exports()
        inventory['node3'] = node3_entity.exports.as_dict()
        node3_entity.interpolate(inventory)
        res_inv = {'node1': {'a': 1, 'b': 2}, 'node2': {'a': 3, 'b': 4}, 'node3': {'a': 3, 'b': 5}}
        res_params = {'a': 3, 'c': 3, 'b': 5, 'name': 'node3', 'exp': {'node1': 1, 'node3': 3, 'node2': 3}, 'ref': {'node1': 1, 'node3': 3, 'node2': 3}}
        self.assertDictEqual(node3_parameters.as_dict(), res_params)
        self.assertDictEqual(inventory, res_inv)

    def test_exports_multiple_nodes(self):
        node1_exports = Exports({'a': '${a}'}, SETTINGS, '')
        node1_parameters = Parameters({'name': 'node1', 'a': { 'test': '${b}' }, 'b': 1, 'exp': '$[ exports:a ]'}, SETTINGS, '')
        node1_entity = Entity(SETTINGS, classes=None, applications=None, parameters=node1_parameters, exports=node1_exports)
        node2_exports = Exports({'a': '${a}'}, SETTINGS, '')
        node2_parameters = Parameters({'name': 'node2', 'a': { 'test': '${b}' }, 'b': 2 }, SETTINGS, '')
        node2_entity = Entity(SETTINGS, classes=None, applications=None, parameters=node2_parameters, exports=node2_exports)
        node1_entity.initialise_interpolation()
        node2_entity.initialise_interpolation()
        queries = node1_entity.parameters.get_inv_queries()
        for p, q in queries:
            node1_entity.interpolate_single_export(q)
            node2_entity.interpolate_single_export(q)
        res_inv = {'node1': {'a': {'test': 1}}, 'node2': {'a': {'test': 2}}}
        res_params = {'a': {'test': 1}, 'b': 1, 'name': 'node1', 'exp': {'node1': {'test': 1}, 'node2': {'test': 2}}}
        inventory = {}
        inventory['node1'] = node1_entity.exports.as_dict()
        inventory['node2'] = node2_entity.exports.as_dict()
        node1_entity.interpolate(inventory)
        self.assertDictEqual(node1_parameters.as_dict(), res_params)
        self.assertDictEqual(inventory, res_inv)

    def test_exports_with_ancestor_references(self):
        inventory = {'node1': {'alpha' : {'beta': {'a': 1, 'b': 2}}}, 'node2': {'alpha' : {'beta': {'a': 3, 'b': 4}}}}
        node3_exports = Exports({'alpha': '${alpha}'}, SETTINGS, '')
        node3_parameters = Parameters({'name': 'node3', 'alpha': {'beta' : {'a': 5, 'b': 6}}, 'exp': '$[ exports:alpha:beta ]'}, SETTINGS, '')
        node3_entity = Entity(SETTINGS, classes=None, applications=None, parameters=node3_parameters, exports=node3_exports)
        res_params = {'exp': {'node1': {'a': 1, 'b': 2}, 'node2': {'a': 3, 'b': 4}, 'node3': {'a': 5, 'b': 6}}, 'name': 'node3', 'alpha': {'beta': {'a': 5, 'b': 6}}}
        res_inv = {'node1': {'alpha' : {'beta': {'a': 1, 'b': 2}}}, 'node2': {'alpha' : {'beta': {'a': 3, 'b': 4}}}, 'node3': {'alpha' : {'beta': {'a': 5, 'b': 6}}}}
        node3_entity.initialise_interpolation()
        queries = node3_entity.parameters.get_inv_queries()
        for p, q in queries:
            node3_entity.interpolate_single_export(q)
        inventory['node3'] = node3_entity.exports.as_dict()
        node3_entity.interpolate(inventory)
        self.assertDictEqual(node3_parameters.as_dict(), res_params)
        self.assertDictEqual(inventory, res_inv)

    def test_exports_with_nested_references(self):
        inventory = {'node1': {'alpha': {'a': 1, 'b': 2}}, 'node2': {'alpha': {'a': 3, 'b': 4}}}
        node3_exports = Exports({'alpha': '${alpha}'}, SETTINGS, '')
        node3_parameters = Parameters({'name': 'node3', 'alpha': {'a': '${one}', 'b': '${two}'}, 'beta': '$[ exports:alpha ]', 'one': '111', 'two': '${three}', 'three': '123'}, SETTINGS, '')
        node3_entity = Entity(SETTINGS, classes=None, applications=None, parameters=node3_parameters, exports=node3_exports)
        res_params = {'beta': {'node1': {'a': 1, 'b': 2}, 'node3': {'a': '111', 'b': '123'}, 'node2': {'a': 3, 'b': 4}}, 'name': 'node3', 'alpha': {'a': '111', 'b': '123'}, 'three': '123', 'two': '123', 'one': '111'}
        res_inv = {'node1': {'alpha': {'a': 1, 'b': 2}}, 'node2': {'alpha': {'a': 3, 'b': 4}}, 'node3': {'alpha': {'a': '111', 'b': '123'}}}
        node3_entity.interpolate_exports()
        inventory['node3'] = node3_entity.exports.as_dict()
        node3_entity.interpolate(inventory)
        self.assertDictEqual(node3_parameters.as_dict(), res_params)
        self.assertDictEqual(inventory, res_inv)

    def test_exports_failed_render(self):
        node1_exports = Exports({'a': '${a}'}, SETTINGS, '')
        node1_parameters = Parameters({'name': 'node1', 'a': 1, 'exp': '$[ exports:a ]'}, SETTINGS, '')
        node1_entity = Entity(SETTINGS, classes=None, applications=None, parameters=node1_parameters, exports=node1_exports)
        node2_exports = Exports({'a': '${b}'}, SETTINGS, '')
        node2_parameters = Parameters({'name': 'node2', 'a': 2}, SETTINGS, '')
        node2_entity = Entity(SETTINGS, classes=None, applications=None, parameters=node2_parameters, exports=node2_exports)
        node1_entity.initialise_interpolation()
        node2_entity.initialise_interpolation()
        queries = node1_entity.parameters.get_inv_queries()
        with self.assertRaises(ResolveError):
            for p, q in queries:
                node1_entity.interpolate_single_export(q)
                node2_entity.interpolate_single_export(q)

    def test_exports_failed_render_ignore(self):
        node1_exports = Exports({'a': '${a}'}, SETTINGS, '')
        node1_parameters = Parameters({'name': 'node1', 'a': 1, 'exp': '$[ +IgnoreErrors exports:a ]'}, SETTINGS, '')
        node1_entity = Entity(SETTINGS, classes=None, applications=None, parameters=node1_parameters, exports=node1_exports)
        node2_exports = Exports({'a': '${b}'}, SETTINGS, '')
        node2_parameters = Parameters({'name': 'node1', 'a': 2}, SETTINGS, '')
        node2_entity = Entity(SETTINGS, classes=None, applications=None, parameters=node2_parameters, exports=node2_exports)
        node1_entity.initialise_interpolation()
        node2_entity.initialise_interpolation()
        queries = node1_entity.parameters.get_inv_queries()
        for p, q in queries:
            node1_entity.interpolate_single_export(q)
            node2_entity.interpolate_single_export(q)
        res_inv = {'node1': {'a': 1}, 'node2': {}}
        res_params = { 'a': 1, 'name': 'node1', 'exp': {'node1': 1} }
        inventory = {}
        inventory['node1'] = node1_entity.exports.as_dict()
        inventory['node2'] = node2_entity.exports.as_dict()
        node1_entity.interpolate(inventory)
        self.assertDictEqual(node1_parameters.as_dict(), res_params)
        self.assertDictEqual(inventory, res_inv)

if __name__ == '__main__':
    unittest.main()
