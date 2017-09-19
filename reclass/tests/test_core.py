#
# -*- coding: utf-8 -*-
#
# This file is part of reclass (http://github.com/madduck/reclass)
#

import os

from reclass import get_storage, get_path_mangler
from reclass.core import Core
from reclass.settings import Settings
from reclass.errors import ClassNotFound

import unittest
try:
    import unittest.mock as mock
except ImportError:
    import mock

class TestCore(unittest.TestCase):

    def _core(self, dataset, opts={}):
        inventory_uri = os.path.dirname(os.path.abspath(__file__)) + '/data/' + dataset
        path_mangler = get_path_mangler('yaml_fs')
        nodes_uri, classes_uri = path_mangler(inventory_uri, 'nodes', 'classes')
        storage = get_storage('yaml_fs', nodes_uri, classes_uri)
        settings = Settings(opts)
        return Core(storage, None, settings)

    def test_type_conversion(self):
        reclass = self._core('01')
        node = reclass.nodeinfo('data_types')
        params = { 'int': 1, 'bool': True, 'string': '1', '_reclass_': { 'environment': 'base', 'name': {'full': 'data_types', 'short': 'data_types' } } }
        self.assertEqual(node['parameters'], params)

    def test_raise_class_notfound(self):
        reclass = self._core('01')
        with self.assertRaises(ClassNotFound):
            node = reclass.nodeinfo('class_notfound')

    def test_ignore_class_notfound(self):
        reclass = self._core('01', opts={ 'ignore_class_notfound': True, 'ignore_class_notfound_warning': False })
        node = reclass.nodeinfo('class_notfound')
        params = { 'node_test': 'class not found', '_reclass_': { 'environment': 'base', 'name': {'full': 'class_notfound', 'short': 'class_notfound' } } }
        self.assertEqual(node['parameters'], params)

    def test_raise_class_notfound_with_regexp(self):
        reclass = self._core('01', opts={ 'ignore_class_notfound': True, 'ignore_class_notfound_warning': False, 'ignore_class_notfound_regexp': 'notmatched.*' })
        with self.assertRaises(ClassNotFound):
            node = reclass.nodeinfo('class_notfound')

    def test_ignore_class_notfound_with_regexp(self):
        reclass = self._core('01', opts={ 'ignore_class_notfound': True, 'ignore_class_notfound_warning': False, 'ignore_class_notfound_regexp': 'miss.*' })
        node = reclass.nodeinfo('class_notfound')
        params = { 'node_test': 'class not found', '_reclass_': { 'environment': 'base', 'name': {'full': 'class_notfound', 'short': 'class_notfound' } } }
        self.assertEqual(node['parameters'], params)


if __name__ == '__main__':
    unittest.main()
