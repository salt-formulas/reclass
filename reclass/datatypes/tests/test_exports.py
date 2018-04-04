#
# -*- coding: utf-8 -*-
#
# This file is part of reclass (http://github.com/madduck/reclass)
#

from reclass.settings import Settings
from reclass.datatypes import Exports, Parameters
from reclass.errors import ParseError
import unittest

SETTINGS = Settings()

class TestInvQuery(unittest.TestCase):

    def test_overwrite_method(self):
        e = Exports({'alpha': { 'one': 1, 'two': 2}}, SETTINGS, '')
        d = {'alpha': { 'three': 3, 'four': 4}}
        e.overwrite(d)
        e.initialise_interpolation()
        self.assertEqual(e.as_dict(), d)

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
        e = {'node1': {'a': 1, 'b': 2}, 'node2': {'a': 3, 'b': 4}}
        p = Parameters({'exp': '$[ exports:a ]'}, SETTINGS, '')
        r = {'exp': {'node1': 1, 'node2': 3}}
        p.interpolate(e)
        self.assertEqual(p.as_dict(), r)

    def test_if_expr_invquery(self):
        e = {'node1': {'a': 1, 'b': 2}, 'node2': {'a': 3, 'b': 4}}
        p = Parameters({'exp': '$[ exports:a if exports:b == 4 ]'}, SETTINGS, '')
        r = {'exp': {'node2': 3}}
        p.interpolate(e)
        self.assertEqual(p.as_dict(), r)

    def test_if_expr_invquery_with_refs(self):
        e = {'node1': {'a': 1, 'b': 2}, 'node2': {'a': 3, 'b': 4}}
        p = Parameters({'exp': '$[ exports:a if exports:b == self:test_value ]', 'test_value': 2}, SETTINGS, '')
        r = {'exp': {'node1': 1}, 'test_value': 2}
        p.interpolate(e)
        self.assertEqual(p.as_dict(), r)

    def test_list_if_expr_invquery(self):
        e = {'node1': {'a': 1, 'b': 2}, 'node2': {'a': 3, 'b': 3}, 'node3': {'a': 3, 'b': 2}}
        p = Parameters({'exp': '$[ if exports:b == 2 ]'}, SETTINGS, '')
        r = {'exp': ['node1', 'node3']}
        p.interpolate(e)
        self.assertEqual(p.as_dict(), r)

    def test_if_expr_invquery_wth_and(self):
        e = {'node1': {'a': 1, 'b': 4, 'c': False}, 'node2': {'a': 3, 'b': 4, 'c': True}}
        p = Parameters({'exp': '$[ exports:a if exports:b == 4 and exports:c == True ]'}, SETTINGS, '')
        r = {'exp': {'node2': 3}}
        p.interpolate(e)
        self.assertEqual(p.as_dict(), r)

    def test_if_expr_invquery_wth_or(self):
        e = {'node1': {'a': 1, 'b': 4}, 'node2': {'a': 3, 'b': 3}}
        p = Parameters({'exp': '$[ exports:a if exports:b == 4 or exports:b == 3 ]'}, SETTINGS, '')
        r = {'exp': {'node1': 1, 'node2': 3}}
        p.interpolate(e)
        self.assertEqual(p.as_dict(), r)

    def test_list_if_expr_invquery_with_and(self):
        e = {'node1': {'a': 1, 'b': 2, 'c': 'green'}, 'node2': {'a': 3, 'b': 3}, 'node3': {'a': 3, 'b': 2, 'c': 'red'}}
        p = Parameters({'exp': '$[ if exports:b == 2 and exports:c == green ]'}, SETTINGS, '')
        r = {'exp': ['node1']}
        p.interpolate(e)
        self.assertEqual(p.as_dict(), r)

    def test_list_if_expr_invquery_with_and_missing(self):
        e = {'node1': {'a': 1, 'b': 2, 'c': 'green'}, 'node2': {'a': 3, 'b': 3}, 'node3': {'a': 3, 'b': 2}}
        p = Parameters({'exp': '$[ if exports:b == 2 and exports:c == green ]'}, SETTINGS, '')
        r = {'exp': ['node1']}
        p.interpolate(e)
        self.assertEqual(p.as_dict(), r)

    def test_list_if_expr_invquery_with_and(self):
        e = {'node1': {'a': 1, 'b': 2}, 'node2': {'a': 3, 'b': 3}, 'node3': {'a': 3, 'b': 4}}
        p = Parameters({'exp': '$[ if exports:b == 2 or exports:b == 4 ]'}, SETTINGS, '')
        r = {'exp': ['node1', 'node3']}
        p.interpolate(e)
        self.assertEqual(p.as_dict(), r)

if __name__ == '__main__':
    unittest.main()
