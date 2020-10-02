#
# -*- coding: utf-8 -*-
#
# This file is part of reclass (http://github.com/madduck/reclass)
#
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from six import iteritems

from reclass.utils.parameterdict import ParameterDict
from reclass.utils.parameterlist import ParameterList
from reclass.settings import Settings
from reclass.datatypes import Exports, Parameters
from reclass.errors import ParseError
from reclass.values import NodeInventory
import unittest

SETTINGS = Settings()

class TestInvQuery(unittest.TestCase):

    def _make_inventory(self, nodes):
        return { name: NodeInventory(node, True) for name, node in iteritems(nodes) }

    def test_overwrite_method(self):
        exports = Exports({'alpha': { 'one': 1, 'two': 2}}, SETTINGS, '')
        data = {'alpha': { 'three': 3, 'four': 4}}
        exports.overwrite(data)
        exports.interpolate()
        self.assertEqual(exports.as_dict(), data)

    def test_interpolate_types(self):
        exports = Exports({'alpha': { 'one': 1, 'two': 2}, 'beta': [ 1, 2 ]}, SETTINGS, '')
        result = {'alpha': { 'one': 1, 'two': 2}, 'beta': [ 1, 2 ]}
        self.assertIs(type(exports.as_dict()['alpha']), ParameterDict)
        self.assertIs(type(exports.as_dict()['beta']), ParameterList)
        exports.interpolate()
        self.assertIs(type(exports.as_dict()['alpha']), dict)
        self.assertIs(type(exports.as_dict()['beta']), list)
        self.assertEqual(exports.as_dict(), result)

    def test_malformed_invquery(self):
        with self.assertRaises(ParseError):
            p = Parameters({'exp': '$[ exports:a exports:b == self:test_value ]'}, SETTINGS, '')
        with self.assertRaises(ParseError):
            p = Parameters({'exp': '$[ exports:a if exports:b self:test_value ]'}, SETTINGS, '')
        with self.assertRaises(ParseError):
            p = Parameters({'exp': '$[ exports:a if exports:b == ]'}, SETTINGS, '')
        with self.assertRaises(ParseError):
            p = Parameters({'exp': '$[ exports:a if exports:b == self:test_value and exports:c = self:test_value2 ]'}, SETTINGS, '')
        with self.assertRaises(ParseError):
            p = Parameters({'exp': '$[ exports:a if exports:b == self:test_value or exports:c == ]'}, SETTINGS, '')
        with self.assertRaises(ParseError):
            p = Parameters({'exp': '$[ exports:a if exports:b == self:test_value anddd exports:c == self:test_value2 ]'}, SETTINGS, '')

    def test_value_expr_invquery(self):
        inventory = self._make_inventory({'node1': {'a': 1, 'b': 2}, 'node2': {'a': 3, 'b': 4}})
        parameters = Parameters({'exp': '$[ exports:a ]'}, SETTINGS, '')
        result = {'exp': {'node1': 1, 'node2': 3}}
        parameters.interpolate(inventory)
        self.assertEqual(parameters.as_dict(), result)

    def test_if_expr_invquery(self):
        inventory = self._make_inventory({'node1': {'a': 1, 'b': 2}, 'node2': {'a': 3, 'b': 4}})
        parameters = Parameters({'exp': '$[ exports:a if exports:b == 4 ]'}, SETTINGS, '')
        result = {'exp': {'node2': 3}}
        parameters.interpolate(inventory)
        self.assertEqual(parameters.as_dict(), result)

    def test_if_expr_invquery_with_refs(self):
        inventory = self._make_inventory({'node1': {'a': 1, 'b': 2}, 'node2': {'a': 3, 'b': 4}})
        parameters = Parameters({'exp': '$[ exports:a if exports:b == self:test_value ]', 'test_value': 2}, SETTINGS, '')
        result = {'exp': {'node1': 1}, 'test_value': 2}
        parameters.interpolate(inventory)
        self.assertEqual(parameters.as_dict(), result)

    def test_list_if_expr_invquery(self):
        inventory = self._make_inventory({'node1': {'a': 1, 'b': 2}, 'node2': {'a': 3, 'b': 3}, 'node3': {'a': 3, 'b': 2}})
        parameters = Parameters({'exp': '$[ if exports:b == 2 ]'}, SETTINGS, '')
        result = {'exp': ['node1', 'node3']}
        parameters.interpolate(inventory)
        self.assertEqual(parameters.as_dict(), result)

    def test_if_expr_invquery_wth_and(self):
        inventory = self._make_inventory({'node1': {'a': 1, 'b': 4, 'c': False}, 'node2': {'a': 3, 'b': 4, 'c': True}})
        parameters = Parameters({'exp': '$[ exports:a if exports:b == 4 and exports:c == True ]'}, SETTINGS, '')
        result = {'exp': {'node2': 3}}
        parameters.interpolate(inventory)
        self.assertEqual(parameters.as_dict(), result)

    def test_if_expr_invquery_wth_or(self):
        inventory = self._make_inventory({'node1': {'a': 1, 'b': 4}, 'node2': {'a': 3, 'b': 3}})
        parameters = Parameters({'exp': '$[ exports:a if exports:b == 4 or exports:b == 3 ]'}, SETTINGS, '')
        result = {'exp': {'node1': 1, 'node2': 3}}
        parameters.interpolate(inventory)
        self.assertEqual(parameters.as_dict(), result)

    def test_list_if_expr_invquery_with_and(self):
        inventory = self._make_inventory(
                        { 'node1': {'a': 1, 'b': 2, 'c': 'green'},
                          'node2': {'a': 3, 'b': 3},
                          'node3': {'a': 3, 'b': 2, 'c': 'red'} })
        parameters = Parameters({'exp': '$[ if exports:b == 2 and exports:c == green ]'}, SETTINGS, '')
        result = {'exp': ['node1']}
        parameters.interpolate(inventory)
        self.assertEqual(parameters.as_dict(), result)

    def test_list_if_expr_invquery_with_and_missing(self):
        inventory = self._make_inventory({'node1': {'a': 1, 'b': 2, 'c': 'green'},
                                          'node2': {'a': 3, 'b': 3},
                                          'node3': {'a': 3, 'b': 2}})
        mapping = {'exp': '$[ if exports:b == 2 and exports:c == green ]'}
        expected = {'exp': ['node1']}
        parameterss = Parameters(mapping, SETTINGS, '')
        parameterss.interpolate(inventory)
        self.assertEqual(parameterss.as_dict(), expected)

    def test_list_if_expr_invquery_with_or(self):
        inventory = self._make_inventory(
                        { 'node1': {'a': 1, 'b': 2},
                          'node2': {'a': 3, 'b': 3},
                          'node3': {'a': 3, 'b': 4} })
        parameters = Parameters({'exp': '$[ if exports:b == 2 or exports:b == 4 ]'}, SETTINGS, '')
        result = {'exp': ['node1', 'node3']}
        parameters.interpolate(inventory)
        self.assertEqual(parameters.as_dict(), result)

    def test_merging_inv_queries(self):
        inventory = self._make_inventory({'node1': {'a': 1}, 'node2': {'a': 1}, 'node3': {'a': 2}})
        pars1 = Parameters({'exp': '$[ if exports:a == 1 ]'}, SETTINGS, '')
        pars2 = Parameters({'exp': '$[ if exports:a == 2 ]'}, SETTINGS, '')
        result = { 'exp': [ 'node1', 'node2', 'node3' ] }
        pars1.merge(pars2)
        pars1.interpolate(inventory)
        self.assertEqual(pars1.as_dict(), result)

    def test_same_expr_invquery_different_flags(self):
        inventory = { 'node1': NodeInventory({'a': 1}, True),
                      'node2': NodeInventory({'a': 2}, True),
                      'node3': NodeInventory({'a': 3}, False) }
        parameters = Parameters({'alpha': '$[ exports:a ]', 'beta': '$[ +AllEnvs exports:a ]'}, SETTINGS, '')
        result = { 'alpha': { 'node1': 1, 'node2': 2 },
                   'beta': { 'node1': 1 , 'node2': 2, 'node3': 3 } }
        parameters.interpolate(inventory)
        self.assertEqual(parameters.as_dict(), result)

    def test_same_if_expr_invquery_different_flags(self):
        inventory = { 'node1': NodeInventory({'a': 1, 'b': 1}, True),
                      'node2': NodeInventory({'a': 2, 'b': 2}, True),
                      'node3': NodeInventory({'a': 3, 'b': 2}, False) }
        parameters = Parameters(
                         { 'alpha': '$[ exports:a if exports:b == 2 ]',
                           'beta': '$[ +AllEnvs exports:a if exports:b == 2]' },
                         SETTINGS, '')
        result = { 'alpha': { 'node2': 2 },
                   'beta': { 'node2': 2, 'node3': 3 } }
        parameters.interpolate(inventory)
        self.assertEqual(parameters.as_dict(), result)

    def test_same_list_if_expr_invquery_different_flags(self):
        inventory = { 'node1': NodeInventory({'a': 1}, True),
                      'node2': NodeInventory({'a': 2}, True),
                      'node3': NodeInventory({'a': 2}, False) }
        parameters = Parameters(
                         { 'alpha': '$[ if exports:a == 2 ]',
                           'beta': '$[ +AllEnvs if exports:a == 2]' },
                         SETTINGS, '')
        result = { 'alpha': [ 'node2' ],
                   'beta': [ 'node2', 'node3' ] }
        parameters.interpolate(inventory)
        self.assertEqual(parameters.as_dict(), result)

if __name__ == '__main__':
    unittest.main()
