#
# -*- coding: utf-8 -*-
#
# This file is part of reclass (http://github.com/madduck/reclass)
#

from reclass.datatypes import Exports, Parameters
import unittest
try:
    import unittest.mock as mock
except ImportError:
    import mock

class TestExportsNoMock(unittest.TestCase):

    def test_overwrite_method(self):
        e = Exports({'alpha': { 'one': 1, 'two': 2}})
        d = {'alpha': { 'three': 3, 'four': 4}}
        e.overwrite(d)
        e.initialise_interpolation()
        self.assertEqual(e.as_dict(), d)

    def test_value_expr_exports(self):
        e = {'node1': {'a': 1, 'b': 2}, 'node2': {'a': 3, 'b': 4}}
        p = Parameters({'exp': '$[ exports:a ]'})
        r = {'exp': {'node1': 1, 'node2': 3}}
        p.interpolate(e)
        self.assertEqual(p.as_dict(), r)

    def test_if_expr_exports(self):
        e = {'node1': {'a': 1, 'b': 2}, 'node2': {'a': 3, 'b': 4}}
        p = Parameters({'exp': '$[ exports:a if exports:b == 4 ]'})
        r = {'exp': {'node2': 3}}
        p.interpolate(e)
        self.assertEqual(p.as_dict(), r)

    def test_if_expr_exports_with_refs(self):
        e = {'node1': {'a': 1, 'b': 2}, 'node2': {'a': 3, 'b': 4}}
        p = Parameters({'exp': '$[ exports:a if exports:b == self:test_value ]', 'test_value': 2})
        r = {'exp': {'node1': 1}, 'test_value': 2}
        p.interpolate(e)
        self.assertEqual(p.as_dict(), r)

    def test_list_if_expr_exports(self):
        e = {'node1': {'a': 1, 'b': 2}, 'node2': {'a': 3, 'b': 3}, 'node3': {'a': 3, 'b': 2}}
        p = Parameters({'exp': '$[ if exports:b == 2 ]'})
        r = {'exp': ['node1', 'node3']}
        p.interpolate(e)
        self.assertEqual(p.as_dict(), r)

if __name__ == '__main__':
    unittest.main()
