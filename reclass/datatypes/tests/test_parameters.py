#
# -*- coding: utf-8 -*-
#
# This file is part of reclass (http://github.com/madduck/reclass)
#
# Copyright © 2007–14 martin f. krafft <madduck@madduck.net>
# Released under the terms of the Artistic Licence 2.0
#
from reclass.datatypes import Parameters
from reclass.defaults import REFERENCE_SENTINELS, ESCAPE_CHARACTER
from reclass.errors import InfiniteRecursionError
from reclass.values.mergeoptions import MergeOptions
import unittest
try:
    import unittest.mock as mock
except ImportError:
    import mock

SIMPLE = {'one': 1, 'two': 2, 'three': 3}

class TestParameters(unittest.TestCase):

    def _construct_mocked_params(self, iterable=None, delimiter=None):
        p = Parameters(iterable, delimiter)
        self._base = base = p._base
        p._base = mock.MagicMock(spec_set=dict, wraps=base)
        p._base.__repr__ = mock.MagicMock(autospec=dict.__repr__,
                                          return_value=repr(base))
        return p, p._base

    def test_len_empty(self):
        p, b = self._construct_mocked_params()
        l = 0
        b.__len__.return_value = l
        self.assertEqual(len(p), l)
        b.__len__.assert_called_with()

    def test_constructor(self):
        p, b = self._construct_mocked_params(SIMPLE)
        l = len(SIMPLE)
        b.__len__.return_value = l
        self.assertEqual(len(p), l)
        b.__len__.assert_called_with()

    def test_repr_empty(self):
        p, b = self._construct_mocked_params()
        b.__repr__.return_value = repr({})
        self.assertEqual('%r' % p, '%s(%r, %r)' % (p.__class__.__name__, {},
                                                   Parameters.DEFAULT_PATH_DELIMITER))
        b.__repr__.assert_called_once_with()

    def test_repr(self):
        p, b = self._construct_mocked_params(SIMPLE)
        b.__repr__.return_value = repr(SIMPLE)
        self.assertEqual('%r' % p, '%s(%r, %r)' % (p.__class__.__name__, SIMPLE,
                                                   Parameters.DEFAULT_PATH_DELIMITER))
        b.__repr__.assert_called_once_with()

    def test_repr_delimiter(self):
        delim = '%'
        p, b = self._construct_mocked_params(SIMPLE, delim)
        b.__repr__.return_value = repr(SIMPLE)
        self.assertEqual('%r' % p, '%s(%r, %r)' % (p.__class__.__name__, SIMPLE, delim))
        b.__repr__.assert_called_once_with()

    def test_equal_empty(self):
        p1, b1 = self._construct_mocked_params()
        p2, b2 = self._construct_mocked_params()
        b1.__eq__.return_value = True
        self.assertEqual(p1, p2)
        b1.__eq__.assert_called_once_with(b2)

    def test_equal_default_delimiter(self):
        p1, b1 = self._construct_mocked_params(SIMPLE)
        p2, b2 = self._construct_mocked_params(SIMPLE,
                                        Parameters.DEFAULT_PATH_DELIMITER)
        b1.__eq__.return_value = True
        self.assertEqual(p1, p2)
        b1.__eq__.assert_called_once_with(b2)

    def test_equal_contents(self):
        p1, b1 = self._construct_mocked_params(SIMPLE)
        p2, b2 = self._construct_mocked_params(SIMPLE)
        b1.__eq__.return_value = True
        self.assertEqual(p1, p2)
        b1.__eq__.assert_called_once_with(b2)

    def test_unequal_content(self):
        p1, b1 = self._construct_mocked_params()
        p2, b2 = self._construct_mocked_params(SIMPLE)
        b1.__eq__.return_value = False
        self.assertNotEqual(p1, p2)
        b1.__eq__.assert_called_once_with(b2)

    def test_unequal_delimiter(self):
        p1, b1 = self._construct_mocked_params(delimiter=':')
        p2, b2 = self._construct_mocked_params(delimiter='%')
        b1.__eq__.return_value = False
        self.assertNotEqual(p1, p2)
        b1.__eq__.assert_called_once_with(b2)

    def test_unequal_types(self):
        p1, b1 = self._construct_mocked_params()
        self.assertNotEqual(p1, None)
        self.assertEqual(b1.__eq__.call_count, 0)

    def test_construct_wrong_type(self):
        with self.assertRaises(TypeError):
            self._construct_mocked_params('wrong type')

    def test_merge_wrong_type(self):
        p, b = self._construct_mocked_params()
        with self.assertRaises(TypeError):
            p.merge('wrong type')

    """def test_get_dict(self):
        p, b = self._construct_mocked_params(SIMPLE)
        p.render_simple()
        self.assertDictEqual(p.as_dict(), SIMPLE)

    def test_merge_scalars(self):
        p1, b1 = self._construct_mocked_params(SIMPLE)
        mergee = {'five':5,'four':4,'None':None,'tuple':(1,2,3)}
        p2, b2 = self._construct_mocked_params(mergee)
        p1.merge(p2)
        p1.render_simple()
        for key, value in mergee.iteritems():
            # check that each key, value in mergee resulted in a get call and
            # a __setitem__ call against b1 (the merge target)
            self.assertIn(mock.call(key), b1.get.call_args_list)
            self.assertIn(mock.call(key, value), b1.__setitem__.call_args_list)

    def test_stray_occurrence_overwrites_during_interpolation(self):
        p1 = Parameters({'r' : mock.sentinel.ref, 'b': '${r}'})
        p2 = Parameters({'b' : mock.sentinel.goal})
        p1.merge(p2)
        p1.interpolate()
        p2.render_simple()
        self.assertEqual(p1.as_dict()['b'], mock.sentinel.goal)"""


class TestParametersNoMock(unittest.TestCase):

    def test_merge_scalars(self):
        p = Parameters(SIMPLE)
        mergee = {'five':5,'four':4,'None':None,'tuple':(1,2,3)}
        p.merge(mergee)
        p.initialise_interpolation()
        goal = SIMPLE.copy()
        goal.update(mergee)
        self.assertDictEqual(p.as_dict(), goal)

    def test_merge_scalars_overwrite(self):
        p = Parameters(SIMPLE)
        mergee = {'two':5,'four':4,'three':None,'one':(1,2,3)}
        p.merge(mergee)
        p.initialise_interpolation()
        goal = SIMPLE.copy()
        goal.update(mergee)
        self.assertDictEqual(p.as_dict(), goal)

    def test_merge_lists(self):
        l1 = [1,2,3]
        l2 = [2,3,4]
        p1 = Parameters(dict(list=l1[:]))
        p2 = Parameters(dict(list=l2))
        p1.merge(p2)
        p1.initialise_interpolation()
        self.assertListEqual(p1.as_dict()['list'], l1+l2)

    def test_merge_list_into_scalar(self):
        l = ['foo', 1, 2]
        options = MergeOptions()
        options.allow_list_over_scalar = True
        p1 = Parameters(dict(key=l[0]))
        p1.merge(Parameters(dict(key=l[1:])))
        p1.initialise_interpolation(options)
        self.assertListEqual(p1.as_dict()['key'], l)

    def test_merge_scalar_over_list(self):
        l = ['foo', 1, 2]
        options = MergeOptions()
        options.allow_scalar_over_list = True
        p1 = Parameters(dict(key=l[:2]))
        p1.merge(Parameters(dict(key=l[2])))
        p1.initialise_interpolation(options)
        self.assertEqual(p1.as_dict()['key'], l[2])

    def test_merge_dicts(self):
        mergee = {'five':5,'four':4,'None':None,'tuple':(1,2,3)}
        p = Parameters(dict(dict=SIMPLE))
        p.merge(Parameters(dict(dict=mergee)))
        p.initialise_interpolation()
        goal = SIMPLE.copy()
        goal.update(mergee)
        self.assertDictEqual(p.as_dict(), dict(dict=goal))

    def test_merge_dicts_overwrite(self):
        mergee = {'two':5,'four':4,'three':None,'one':(1,2,3)}
        p = Parameters(dict(dict=SIMPLE))
        p.merge(Parameters(dict(dict=mergee)))
        p.initialise_interpolation()
        goal = SIMPLE.copy()
        goal.update(mergee)
        self.assertDictEqual(p.as_dict(), dict(dict=goal))

    def test_merge_dicts_override(self):
        """Validate that tilde merge overrides function properly."""
        mergee = {'~one': {'a': 'alpha'},
                  '~two': ['gamma']}
        base = {'one': {'b': 'beta'},
                'two': ['delta']}
        goal = {'one': {'a': 'alpha'},
                'two': ['gamma']}
        p = Parameters(dict(dict=base))
        p.merge(Parameters(dict(dict=mergee)))
        p.initialise_interpolation()
        self.assertDictEqual(p.as_dict(), dict(dict=goal))

    def test_merge_dict_into_scalar(self):
        p = Parameters(dict(base='foo'))
        with self.assertRaises(TypeError):
            p.merge(Parameters(dict(base=SIMPLE)))
            p.interpolate()

    def test_merge_scalar_over_dict(self):
        p = Parameters(dict(base=SIMPLE))
        mergee = {'base':'foo'}
        options = MergeOptions()
        options.allow_scalar_over_dict = True
        p.merge(Parameters(mergee))
        p.initialise_interpolation(options)
        self.assertDictEqual(p.as_dict(), mergee)

    def test_interpolate_single(self):
        v = 42
        d = {'foo': 'bar'.join(REFERENCE_SENTINELS),
             'bar': v}
        p = Parameters(d)
        p.interpolate()
        self.assertEqual(p.as_dict()['foo'], v)

    def test_interpolate_multiple(self):
        v = '42'
        d = {'foo': 'bar'.join(REFERENCE_SENTINELS) + 'meep'.join(REFERENCE_SENTINELS),
             'bar': v[0],
             'meep': v[1]}
        p = Parameters(d)
        p.interpolate()
        self.assertEqual(p.as_dict()['foo'], v)

    def test_interpolate_multilevel(self):
        v = 42
        d = {'foo': 'bar'.join(REFERENCE_SENTINELS),
             'bar': 'meep'.join(REFERENCE_SENTINELS),
             'meep': v}
        p = Parameters(d)
        p.interpolate()
        self.assertEqual(p.as_dict()['foo'], v)

    def test_interpolate_list(self):
        l = [41,42,43]
        d = {'foo': 'bar'.join(REFERENCE_SENTINELS),
             'bar': l}
        p = Parameters(d)
        p.interpolate()
        self.assertEqual(p.as_dict()['foo'], l)

    def test_interpolate_infrecursion(self):
        v = 42
        d = {'foo': 'bar'.join(REFERENCE_SENTINELS),
             'bar': 'foo'.join(REFERENCE_SENTINELS)}
        p = Parameters(d)
        with self.assertRaises(InfiniteRecursionError):
            p.interpolate()

    def test_nested_references(self):
        d = {'a': '${${z}}', 'b': 2, 'z': 'b'}
        r = {'a': 2, 'b': 2, 'z': 'b'}
        p = Parameters(d)
        p.interpolate()
        self.assertEqual(p.as_dict(), r)

    def test_nested_deep_references(self):
        d = {'one': { 'a': 1, 'b': '${one:${one:c}}', 'c': 'a' } }
        r = {'one': { 'a': 1, 'b': 1, 'c': 'a'} }
        p = Parameters(d)
        p.interpolate()
        self.assertEqual(p.as_dict(), r)

    def test_stray_occurrence_overwrites_during_interpolation(self):
        p1 = Parameters({'r' : 1, 'b': '${r}'})
        p2 = Parameters({'b' : 2})
        p1.merge(p2)
        p1.interpolate()
        self.assertEqual(p1.as_dict()['b'], 2)

    def test_referenced_dict_deep_overwrite(self):
        p1 = Parameters({'alpha': {'one': {'a': 1, 'b': 2} } })
        p2 = Parameters({'beta': '${alpha}'})
        p3 = Parameters({'alpha': {'one': {'c': 3, 'd': 4} },
                         'beta':  {'one': {'a': 99} } })
        r = {'alpha': {'one': {'a':1, 'b': 2, 'c': 3, 'd':4} },
             'beta': {'one': {'a':99, 'b': 2, 'c': 3, 'd':4} } }
        p1.merge(p2)
        p1.merge(p3)
        p1.interpolate()
        self.assertEqual(p1.as_dict(), r)

    def test_complex_reference_overwriting(self):
        p1 = Parameters({'one': 'abc_123_${two}_${three}', 'two': 'XYZ', 'four': 4})
        p2 = Parameters({'one': 'QWERTY_${three}_${four}', 'three': '999'})
        r = {'one': 'QWERTY_999_4', 'two': 'XYZ', 'three': '999', 'four': 4}
        p1.merge(p2)
        p1.interpolate()
        self.assertEqual(p1.as_dict(), r)

    def test_nested_reference_with_overwriting(self):
        p1 = Parameters({'one': {'a': 1, 'b': 2, 'z': 'a'},
                         'two': '${one:${one:z}}' })
        p2 = Parameters({'one': {'z': 'b'} })
        r = {'one': {'a': 1, 'b':2, 'z': 'b'}, 'two': 2}
        p1.merge(p2)
        p1.interpolate()
        self.assertEqual(p1.as_dict(), r)

    def test_merge_referenced_lists(self):
        p1 = Parameters({'one': [ 1, 2, 3 ], 'two': [ 4, 5, 6 ], 'three': '${one}'})
        p2 = Parameters({'three': '${two}'})
        r = {'one': [ 1, 2, 3 ], 'two': [ 4, 5, 6], 'three': [ 1, 2, 3, 4, 5, 6 ]}
        p1.merge(p2)
        p1.interpolate()
        self.assertEqual(p1.as_dict(), r)

    def test_merge_referenced_dicts(self):
        p1 = Parameters({'one': {'a': 1, 'b': 2}, 'two': {'c': 3, 'd': 4}, 'three': '${one}'})
        p2 = Parameters({'three': '${two}'})
        r = {'one': {'a': 1, 'b': 2}, 'two': {'c': 3, 'd': 4}, 'three': {'a': 1, 'b': 2, 'c': 3, 'd': 4}}
        p1.merge(p2)
        p1.interpolate()
        self.assertEqual(p1.as_dict(), r)

    def test_deep_refs_in_referenced_dicts(self):
        p = Parameters({'A': '${C:a}', 'B': {'a': 1, 'b': 2}, 'C': '${B}'})
        r = {'A': 1, 'B': {'a': 1, 'b': 2}, 'C': {'a': 1, 'b': 2}}
        p.interpolate()
        self.assertEqual(p.as_dict(), r)

    def test_overwrite_none(self):
        p1 = Parameters({'A': None, 'B': None, 'C': None, 'D': None, 'E': None, 'F': None})
        p2 = Parameters({'A': 'abc', 'B': [1, 2, 3], 'C': {'a': 'aaa', 'b': 'bbb'}, 'D': '${A}', 'E': '${B}', 'F': '${C}'})
        r = {'A': 'abc', 'B': [1, 2, 3], 'C': {'a': 'aaa', 'b': 'bbb'}, 'D': 'abc', 'E': [1, 2, 3], 'F': {'a': 'aaa', 'b': 'bbb'}}
        p1.merge(p2)
        p1.interpolate()
        self.assertEqual(p1.as_dict(), r)

    def test_interpolate_escaping(self):
        v = 'bar'.join(REFERENCE_SENTINELS)
        d = {'foo': ESCAPE_CHARACTER + 'bar'.join(REFERENCE_SENTINELS),
             'bar': 'unused'}
        p = Parameters(d)
        p.initialise_interpolation()
        self.assertEqual(p.as_dict()['foo'], v)

    def test_interpolate_double_escaping(self):
        v = ESCAPE_CHARACTER + 'meep'
        d = {'foo': ESCAPE_CHARACTER + ESCAPE_CHARACTER + 'bar'.join(REFERENCE_SENTINELS),
             'bar': 'meep'}
        p = Parameters(d)
        p.interpolate()
        self.assertEqual(p.as_dict()['foo'], v)

    def test_interpolate_escaping_backwards_compatibility(self):
        """In all following cases, escaping should not happen and the escape character
        needs to be printed as-is, to ensure backwards compatibility to older versions."""
        v = ' '.join([
            # Escape character followed by unescapable character
            '1', ESCAPE_CHARACTER,
            # Escape character followed by escape character
            '2', ESCAPE_CHARACTER + ESCAPE_CHARACTER,
            # Escape character followed by interpolation end sentinel
            '3', ESCAPE_CHARACTER + REFERENCE_SENTINELS[1],
            # Escape character at the end of the string
            '4', ESCAPE_CHARACTER
            ])
        d = {'foo': v}
        p = Parameters(d)
        p.initialise_interpolation()
        self.assertEqual(p.as_dict()['foo'], v)

    def test_escape_close_in_ref(self):
        p1 = Parameters({'one}': 1, 'two': '${one\\}}'})
        r = {'one}': 1, 'two': 1}
        p1.interpolate()
        self.assertEqual(p1.as_dict(), r)

    def test_double_escape_in_ref(self):
        d = {'one\\': 1, 'two': '${one\\\\}'}
        p1 = Parameters(d)
        r = {'one\\': 1, 'two': 1}
        p1.interpolate()
        self.assertEqual(p1.as_dict(), r)

    def test_merging_for_multiple_nodes(self):
        p1 = Parameters({ 'alpha': { 'one': 111 }})
        p2 = Parameters({ 'beta': {'two': '${alpha:one}' }})
        p3 = Parameters({ 'beta': {'two': 222 }})
        n1 = Parameters({ 'name': 'node1'})
        r1 = { 'alpha': { 'one': 111 }, 'beta': { 'two': 111 }, 'name': 'node1' }
        r2 = { 'alpha': { 'one': 111 }, 'beta': { 'two': 222 }, 'name': 'node2' }
        n1.merge(p1)
        n1.merge(p2)
        n1.interpolate()
        n2 = Parameters({'name': 'node2'})
        n2.merge(p1)
        n2.merge(p2)
        n2.merge(p3)
        n2.interpolate()
        self.assertEqual(n1.as_dict(), r1)
        self.assertEqual(n2.as_dict(), r2)

    def test_list_merging_for_multiple_nodes(self):
        p1 = Parameters({ 'alpha': { 'one': [1, 2] }})
        p2 = Parameters({ 'beta': {'two': '${alpha:one}' }})
        p3 = Parameters({ 'beta': {'two': [3] }})
        n1 = Parameters({ 'name': 'node1'})
        r1 = { 'alpha': { 'one': [1, 2] }, 'beta': { 'two': [1, 2] }, 'name': 'node1' }
        r2 = { 'alpha': { 'one': [1, 2] }, 'beta': { 'two': [1, 2, 3] }, 'name': 'node2' }
        n1.merge(p1)
        n1.merge(p2)
        n1.interpolate()
        n2 = Parameters({'name': 'node2'})
        n2.merge(p1)
        n2.merge(p2)
        n2.merge(p3)
        n2.interpolate()
        self.assertEqual(n1.as_dict(), r1)
        self.assertEqual(n2.as_dict(), r2)

    def test_dict_merging_for_multiple_nodes(self):
        p1 = Parameters({ 'alpha': { 'one': { 'a': 'aa', 'b': 'bb' }}})
        p2 = Parameters({ 'beta': {'two': '${alpha:one}' }})
        p3 = Parameters({ 'beta': {'two': {'c': 'cc' }}})
        n1 = Parameters({ 'name': 'node1'})
        r1 = { 'alpha': { 'one': {'a': 'aa', 'b': 'bb'} }, 'beta': { 'two': {'a': 'aa', 'b': 'bb'} }, 'name': 'node1' }
        r2 = { 'alpha': { 'one': {'a': 'aa', 'b': 'bb'} }, 'beta': { 'two': {'a': 'aa', 'b': 'bb', 'c': 'cc'} }, 'name': 'node2' }
        n1.merge(p1)
        n1.merge(p2)
        n1.interpolate()
        n2 = Parameters({'name': 'node2'})
        n2.merge(p1)
        n2.merge(p2)
        n2.merge(p3)
        n2.interpolate()
        self.assertEqual(n1.as_dict(), r1)
        self.assertEqual(n2.as_dict(), r2)

    def test_list_merging_with_refs_for_multiple_nodes(self):
        p1 = Parameters({ 'alpha': { 'one': [1, 2], 'two': [3, 4] }})
        p2 = Parameters({ 'beta': { 'three': '${alpha:one}' }})
        p3 = Parameters({ 'beta': { 'three': '${alpha:two}' }})
        p4 = Parameters({ 'beta': { 'three': '${alpha:one}' }})
        n1 = Parameters({ 'name': 'node1' })
        r1 = {'alpha': {'one': [1, 2], 'two': [3, 4]}, 'beta': {'three': [1, 2]}, 'name': 'node1'}
        r2 = {'alpha': {'one': [1, 2], 'two': [3, 4]}, 'beta': {'three': [1, 2, 3, 4, 1, 2]}, 'name': 'node2'}
        n2 = Parameters({ 'name': 'node2' })
        n2.merge(p1)
        n2.merge(p2)
        n2.merge(p3)
        n2.merge(p4)
        n2.interpolate()
        n1.merge(p1)
        n1.merge(p2)
        n1.interpolate()
        self.assertEqual(n1.as_dict(), r1)
        self.assertEqual(n2.as_dict(), r2)

    def test_nested_refs_with_multiple_nodes(self):
        p1 = Parameters({ 'alpha': { 'one': 1, 'two': 2 } })
        p2 = Parameters({ 'beta': { 'three': 'one' } })
        p3 = Parameters({ 'beta': { 'three': 'two' } })
        p4 = Parameters({ 'beta': { 'four': '${alpha:${beta:three}}' } })
        n1 = Parameters({ 'name': 'node1' })
        r1 = {'alpha': {'one': 1, 'two': 2}, 'beta': {'three': 'one', 'four': 1}, 'name': 'node1'}
        r2 = {'alpha': {'one': 1, 'two': 2}, 'beta': {'three': 'two', 'four': 2}, 'name': 'node2'}
        n1.merge(p1)
        n1.merge(p4)
        n1.merge(p2)
        n1.interpolate()
        n2 = Parameters({ 'name': 'node2' })
        n2.merge(p1)
        n2.merge(p4)
        n2.merge(p3)
        n2.interpolate()
        self.assertEqual(n1.as_dict(), r1)
        self.assertEqual(n2.as_dict(), r2)

if __name__ == '__main__':
    unittest.main()
