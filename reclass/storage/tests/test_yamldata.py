#
# -*- coding: utf-8 -*-
#
# This file is part of reclass (http://github.com/madduck/reclass)
#

from reclass.storage.yamldata import YamlData

import unittest

class TestYamlData(unittest.TestCase):

    def setUp(self):
        lines = [ 'classes:',
                  '  - testdir.test1',
                  '  - testdir.test2',
                  '  - test3',
                  '',
                  'environment: base',
                  '',
                  'parameters:',
                  '  _TEST_:',
                  '    alpha: 1',
                  '    beta: two' ]
        self.data = '\n'.join(lines)
        self.yamldict = { 'classes': [ 'testdir.test1', 'testdir.test2', 'test3' ],
                          'environment': 'base',
                          'parameters': { '_TEST_': { 'alpha': 1, 'beta': 'two' } }
                        }

    def test_yaml_from_string(self):
        res = YamlData.from_string(self.data, 'testpath')
        self.assertEqual(res.uri, 'testpath')
        self.assertEqual(res.get_data(), self.yamldict)

if __name__ == '__main__':
    unittest.main()
