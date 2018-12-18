#
# -*- coding: utf-8 -*-
#
# This file is part of reclass (http://github.com/madduck/reclass)
#
# Copyright © 2007–14 martin f. krafft <madduck@madduck.net>
# Released under the terms of the Artistic Licence 2.0
#
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import copy

from six import iteritems

from reclass.settings import Settings
from reclass.datatypes import Parameters
from reclass.utils.parameterdict import ParameterDict
from reclass.utils.parameterlist import ParameterList
from reclass.values.value import Value
from reclass.values.valuelist import ValueList
from reclass.values.scaitem import ScaItem
from reclass.errors import ChangedConstantError, InfiniteRecursionError, InterpolationError, ResolveError, ResolveErrorList, TypeMergeError
import unittest

try:
    import unittest.mock as mock
except ImportError:
    import mock

SIMPLE = {'one': 1, 'two': 2, 'three': 3}
SETTINGS = Settings()

class MockDevice(object):
    def __init__(self):
        self._text = ''

    def write(self, s):
        self._text += s
        return

    def text(self):
        return self._text

class TestParameters(unittest.TestCase):

    def _construct_mocked_params(self, iterable=None, settings=SETTINGS):
        p = Parameters(iterable, settings, '')
        self._base = base = p._base
        p._base = mock.MagicMock(spec_set=ParameterDict, wraps=base)
        p._base.__repr__ = mock.MagicMock(autospec=dict.__repr__,
                                          return_value=repr(base))
        p._base.__getitem__.side_effect = base.__getitem__
        p._base.__setitem__.side_effect = base.__setitem__
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
        self.assertEqual('%r' % p, '%s(%r)' % (p.__class__.__name__, {}))
        b.__repr__.assert_called_once_with()

    def test_repr(self):
        p, b = self._construct_mocked_params(SIMPLE)
        b.__repr__.return_value = repr(SIMPLE)
        self.assertEqual('%r' % p, '%s(%r)' % (p.__class__.__name__, SIMPLE))
        b.__repr__.assert_called_once_with()

    def test_equal_empty(self):
        p1, b1 = self._construct_mocked_params()
        p2, b2 = self._construct_mocked_params()
        b1.__eq__.return_value = True
        self.assertEqual(p1, p2)
        b1.__eq__.assert_called_once_with(b2)

    def test_equal_default_delimiter(self):
        p1, b1 = self._construct_mocked_params(SIMPLE)
        p2, b2 = self._construct_mocked_params(SIMPLE, SETTINGS)
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
        settings1 = Settings({'delimiter': ':'})
        settings2 = Settings({'delimiter': '%'})
        p1, b1 = self._construct_mocked_params(settings=settings1)
        p2, b2 = self._construct_mocked_params(settings=settings2)
        b1.__eq__.return_value = False
        self.assertNotEqual(p1, p2)
        b1.__eq__.assert_called_once_with(b2)

    def test_unequal_types(self):
        p1, b1 = self._construct_mocked_params()
        self.assertNotEqual(p1, None)
        self.assertEqual(b1.__eq__.call_count, 0)

    def test_construct_wrong_type(self):
        with self.assertRaises(TypeError) as e:
            self._construct_mocked_params(str('wrong type'))
        self.assertIn(str(e.exception), [ "Cannot merge <type 'str'> objects into Parameters",    # python 2
                                          "Cannot merge <class 'str'> objects into Parameters" ])  # python 3

    def test_merge_wrong_type(self):
        p, b = self._construct_mocked_params()
        with self.assertRaises(TypeError) as e:
            p.merge(str('wrong type'))
        self.assertIn(str(e.exception), [ "Cannot merge <type 'str'> objects into Parameters",    # python 2
                                          "Cannot merge <class 'str'> objects into Parameters"])   # python 3

    def test_get_dict(self):
        p, b = self._construct_mocked_params(SIMPLE)
        p.initialise_interpolation()
        self.assertDictEqual(p.as_dict(), SIMPLE)

    def test_merge_scalars(self):
        p1, b1 = self._construct_mocked_params(SIMPLE)
        mergee = {'five':5,'four':4,'None':None,'tuple':(1,2,3)}
        p2, b2 = self._construct_mocked_params(mergee)
        p1.merge(p2)
        self.assertEqual(b1.get.call_count, 4)
        self.assertEqual(b1.__setitem__.call_count, 4)

    def test_stray_occurrence_overwrites_during_interpolation(self):
        p1 = Parameters({'r' : mock.sentinel.ref, 'b': '${r}'}, SETTINGS, '')
        p2 = Parameters({'b' : mock.sentinel.goal}, SETTINGS, '')
        p1.merge(p2)
        p1.interpolate()
        self.assertEqual(p1.as_dict()['b'], mock.sentinel.goal)


class TestParametersNoMock(unittest.TestCase):

    def test_merge_scalars(self):
        p = Parameters(SIMPLE, SETTINGS, '')
        mergee = {'five':5,'four':4,'None':None,'tuple':(1,2,3)}
        p.merge(mergee)
        p.initialise_interpolation()
        goal = SIMPLE.copy()
        goal.update(mergee)
        self.assertDictEqual(p.as_dict(), goal)

    def test_merge_scalars_overwrite(self):
        p = Parameters(SIMPLE, SETTINGS, '')
        mergee = {'two':5,'four':4,'three':None,'one':(1,2,3)}
        p.merge(mergee)
        p.initialise_interpolation()
        goal = SIMPLE.copy()
        goal.update(mergee)
        self.assertDictEqual(p.as_dict(), goal)

    def test_merge_lists(self):
        l1 = [1,2,3]
        l2 = [2,3,4]
        p1 = Parameters(dict(list=l1[:]), SETTINGS, '')
        p2 = Parameters(dict(list=l2), SETTINGS, '')
        p1.merge(p2)
        p1.initialise_interpolation()
        self.assertListEqual(p1.as_dict()['list'], l1+l2)

    def test_merge_list_into_scalar(self):
        l = ['foo', 1, 2]
        p1 = Parameters(dict(key=l[0]), SETTINGS, '')
        p2 = Parameters(dict(key=l[1:]), SETTINGS, '')
        with self.assertRaises(TypeMergeError) as e:
            p1.merge(p2)
            p1.interpolate()
        self.assertEqual(e.exception.message, "-> \n   Cannot merge list over scalar, at key, in ; ")

    def test_merge_list_into_scalar_allow(self):
        settings = Settings({'allow_list_over_scalar': True})
        l = ['foo', 1, 2]
        p1 = Parameters(dict(key=l[0]), settings, '')
        p2 = Parameters(dict(key=l[1:]), settings, '')
        p1.merge(p2)
        p1.interpolate()
        self.assertListEqual(p1.as_dict()['key'], l)

    def test_merge_scalar_over_list(self):
        l = ['foo', 1, 2]
        p1 = Parameters(dict(key=l[:2]), SETTINGS, '')
        p2 = Parameters(dict(key=l[2]), SETTINGS, '')
        with self.assertRaises(TypeMergeError) as e:
            p1.merge(p2)
            p1.interpolate()
        self.assertEqual(e.exception.message, "-> \n   Cannot merge scalar over list, at key, in ; ")

    def test_merge_scalar_over_list_allow(self):
        l = ['foo', 1, 2]
        settings = Settings({'allow_scalar_over_list': True})
        p1 = Parameters(dict(key=l[:2]), settings, '')
        p2 = Parameters(dict(key=l[2]), settings, '')
        p1.merge(p2)
        p1.interpolate()
        self.assertEqual(p1.as_dict()['key'], l[2])

    def test_merge_none_over_list(self):
        l = ['foo', 1, 2]
        settings = Settings({'allow_none_override': False})
        p1 = Parameters(dict(key=l[:2]), settings, '')
        p2 = Parameters(dict(key=None), settings, '')
        with self.assertRaises(TypeMergeError) as e:
            p1.merge(p2)
            p1.interpolate()
        self.assertEqual(e.exception.message, "-> \n   Cannot merge scalar over list, at key, in ; ")

    def test_merge_none_over_list_allow(self):
        l = ['foo', 1, 2]
        settings = Settings({'allow_none_override': True})
        p1 = Parameters(dict(key=l[:2]), settings, '')
        p2 = Parameters(dict(key=None), settings, '')
        p1.merge(p2)
        p1.interpolate()
        self.assertEqual(p1.as_dict()['key'], None)

    def test_merge_dict_over_scalar(self):
        d = { 'one': 1, 'two': 2 }
        p1 = Parameters({ 'a': 1 }, SETTINGS, '')
        p2 = Parameters({ 'a': d }, SETTINGS, '')
        with self.assertRaises(TypeMergeError) as e:
            p1.merge(p2)
            p1.interpolate()
        self.assertEqual(e.exception.message, "-> \n   Cannot merge dictionary over scalar, at a, in ; ")

    def test_merge_dict_over_scalar_allow(self):
        settings = Settings({'allow_dict_over_scalar': True})
        d = { 'one': 1, 'two': 2 }
        p1 = Parameters({ 'a': 1 }, settings, '')
        p2 = Parameters({ 'a': d }, settings, '')
        p1.merge(p2)
        p1.interpolate()
        self.assertEqual(p1.as_dict(), { 'a': d })

    def test_merge_scalar_over_dict(self):
        d = { 'one': 1, 'two': 2}
        p1 = Parameters({ 'a': d }, SETTINGS, '')
        p2 = Parameters({ 'a': 1 }, SETTINGS, '')
        with self.assertRaises(TypeMergeError) as e:
            p1.merge(p2)
            p1.interpolate()
        self.assertEqual(e.exception.message, "-> \n   Cannot merge scalar over dictionary, at a, in ; ")

    def test_merge_scalar_over_dict_allow(self):
        d = { 'one': 1, 'two': 2}
        settings = Settings({'allow_scalar_over_dict': True})
        p1 = Parameters({ 'a': d }, settings, '')
        p2 = Parameters({ 'a': 1 }, settings, '')
        p1.merge(p2)
        p1.interpolate()
        self.assertEqual(p1.as_dict(), { 'a': 1})

    def test_merge_none_over_dict(self):
        p1 = Parameters(dict(key=SIMPLE), SETTINGS, '')
        p2 = Parameters(dict(key=None), SETTINGS, '')
        with self.assertRaises(TypeMergeError) as e:
            p1.merge(p2)
            p1.interpolate()
        self.assertEqual(e.exception.message, "-> \n   Cannot merge scalar over dictionary, at key, in ; ")

    def test_merge_none_over_dict_allow(self):
        settings = Settings({'allow_none_override': True})
        p1 = Parameters(dict(key=SIMPLE), settings, '')
        p2 = Parameters(dict(key=None), settings, '')
        p1.merge(p2)
        p1.interpolate()
        self.assertEqual(p1.as_dict()['key'], None)

    def test_merge_list_over_dict(self):
        p1 = Parameters({}, SETTINGS, '')
        p2 = Parameters({'one': { 'a': { 'b': 'c' } } }, SETTINGS, 'second')
        p3 = Parameters({'one': { 'a': [ 'b' ] } }, SETTINGS, 'third')
        with self.assertRaises(TypeMergeError) as e:
            p1.merge(p2)
            p1.merge(p3)
            p1.interpolate()
        self.assertEqual(e.exception.message, "-> \n   Cannot merge list over dictionary, at one:a, in second; third")

    # def test_merge_bare_dict_over_dict(self):
        # settings = Settings({'allow_bare_override': True})
        # p1 = Parameters(dict(key=SIMPLE), settings, '')
        # p2 = Parameters(dict(key=dict()), settings, '')
        # p1.merge(p2)
        # p1.initialise_interpolation()
        # self.assertEqual(p1.as_dict()['key'], {})

    # def test_merge_bare_list_over_list(self):
        # l = ['foo', 1, 2]
        # settings = Settings({'allow_bare_override': True})
        # p1 = Parameters(dict(key=l), settings, '')
        # p2 = Parameters(dict(key=list()), settings, '')
        # p1.merge(p2)
        # p1.initialise_interpolation()
        # self.assertEqual(p1.as_dict()['key'], [])

    def test_merge_dicts(self):
        mergee = {'five':5,'four':4,'None':None,'tuple':(1,2,3)}
        p = Parameters(dict(dict=SIMPLE), SETTINGS, '')
        p2 = Parameters(dict(dict=mergee), SETTINGS, '')
        p.merge(p2)
        p.initialise_interpolation()
        goal = SIMPLE.copy()
        goal.update(mergee)
        self.assertDictEqual(p.as_dict(), dict(dict=goal))

    def test_merge_dicts_overwrite(self):
        mergee = {'two':5,'four':4,'three':None,'one':(1,2,3)}
        p = Parameters(dict(dict=SIMPLE), SETTINGS, '')
        p2 = Parameters(dict(dict=mergee), SETTINGS, '')
        p.merge(p2)
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
        p = Parameters(dict(dict=base), SETTINGS, '')
        p2 = Parameters(dict(dict=mergee), SETTINGS, '')
        p.merge(p2)
        p.interpolate()
        self.assertDictEqual(p.as_dict(), dict(dict=goal))

    def test_interpolate_single(self):
        v = 42
        d = {'foo': 'bar'.join(SETTINGS.reference_sentinels),
             'bar': v}
        p = Parameters(d, SETTINGS, '')
        p.interpolate()
        self.assertEqual(p.as_dict()['foo'], v)

    def test_interpolate_multiple(self):
        v = '42'
        d = {'foo': 'bar'.join(SETTINGS.reference_sentinels) + 'meep'.join(SETTINGS.reference_sentinels),
             'bar': v[0],
             'meep': v[1]}
        p = Parameters(d, SETTINGS, '')
        p.interpolate()
        self.assertEqual(p.as_dict()['foo'], v)

    def test_interpolate_multilevel(self):
        v = 42
        d = {'foo': 'bar'.join(SETTINGS.reference_sentinels),
             'bar': 'meep'.join(SETTINGS.reference_sentinels),
             'meep': v}
        p = Parameters(d, SETTINGS, '')
        p.interpolate()
        self.assertEqual(p.as_dict()['foo'], v)

    def test_interpolate_list(self):
        l = [41, 42, 43]
        d = {'foo': 'bar'.join(SETTINGS.reference_sentinels),
             'bar': l}
        p = Parameters(d, SETTINGS, '')
        p.interpolate()
        self.assertEqual(p.as_dict()['foo'], l)

    def test_interpolate_infrecursion(self):
        v = 42
        d = {'foo': 'bar'.join(SETTINGS.reference_sentinels),
             'bar': 'foo'.join(SETTINGS.reference_sentinels)}
        p = Parameters(d, SETTINGS, '')
        with self.assertRaises(InfiniteRecursionError) as e:
            p.interpolate()
        # interpolation can start with foo or bar
        self.assertIn(e.exception.message, [ "-> \n   Infinite recursion: ${foo}, at bar",
                                             "-> \n   Infinite recursion: ${bar}, at foo"])

    def test_nested_references(self):
        d = {'a': '${${z}}', 'b': 2, 'z': 'b'}
        r = {'a': 2, 'b': 2, 'z': 'b'}
        p = Parameters(d, SETTINGS, '')
        p.interpolate()
        self.assertEqual(p.as_dict(), r)

    def test_nested_deep_references(self):
        d = {'one': { 'a': 1, 'b': '${one:${one:c}}', 'c': 'a' } }
        r = {'one': { 'a': 1, 'b': 1, 'c': 'a'} }
        p = Parameters(d, SETTINGS, '')
        p.interpolate()
        self.assertEqual(p.as_dict(), r)

    def test_stray_occurrence_overwrites_during_interpolation(self):
        p1 = Parameters({'r' : 1, 'b': '${r}'}, SETTINGS, '')
        p2 = Parameters({'b' : 2}, SETTINGS, '')
        p1.merge(p2)
        p1.interpolate()
        self.assertEqual(p1.as_dict()['b'], 2)

    def test_referenced_dict_deep_overwrite(self):
        p1 = Parameters({'alpha': {'one': {'a': 1, 'b': 2} } }, SETTINGS, '')
        p2 = Parameters({'beta': '${alpha}'}, SETTINGS, '')
        p3 = Parameters({'alpha': {'one': {'c': 3, 'd': 4} },
                         'beta':  {'one': {'a': 99} } }, SETTINGS, '')
        r = {'alpha': {'one': {'a':1, 'b': 2, 'c': 3, 'd':4} },
             'beta': {'one': {'a':99, 'b': 2, 'c': 3, 'd':4} } }
        p1.merge(p2)
        p1.merge(p3)
        p1.interpolate()
        self.assertEqual(p1.as_dict(), r)

    def test_complex_reference_overwriting(self):
        p1 = Parameters({'one': 'abc_123_${two}_${three}', 'two': 'XYZ', 'four': 4}, SETTINGS, '')
        p2 = Parameters({'one': 'QWERTY_${three}_${four}', 'three': '999'}, SETTINGS, '')
        r = {'one': 'QWERTY_999_4', 'two': 'XYZ', 'three': '999', 'four': 4}
        p1.merge(p2)
        p1.interpolate()
        self.assertEqual(p1.as_dict(), r)

    def test_nested_reference_with_overwriting(self):
        p1 = Parameters({'one': {'a': 1, 'b': 2, 'z': 'a'},
                         'two': '${one:${one:z}}' }, SETTINGS, '')
        p2 = Parameters({'one': {'z': 'b'} }, SETTINGS, '')
        r = {'one': {'a': 1, 'b':2, 'z': 'b'}, 'two': 2}
        p1.merge(p2)
        p1.interpolate()
        self.assertEqual(p1.as_dict(), r)

    def test_merge_referenced_lists(self):
        p1 = Parameters({'one': [ 1, 2, 3 ], 'two': [ 4, 5, 6 ], 'three': '${one}'}, SETTINGS, '')
        p2 = Parameters({'three': '${two}'}, SETTINGS, '')
        r = {'one': [ 1, 2, 3 ], 'two': [ 4, 5, 6], 'three': [ 1, 2, 3, 4, 5, 6 ]}
        p1.merge(p2)
        p1.interpolate()
        self.assertEqual(p1.as_dict(), r)

    def test_merge_referenced_dicts(self):
        p1 = Parameters({'one': {'a': 1, 'b': 2}, 'two': {'c': 3, 'd': 4}, 'three': '${one}'}, SETTINGS, '')
        p2 = Parameters({'three': '${two}'}, SETTINGS, '')
        r = {'one': {'a': 1, 'b': 2}, 'two': {'c': 3, 'd': 4}, 'three': {'a': 1, 'b': 2, 'c': 3, 'd': 4}}
        p1.merge(p2)
        p1.interpolate()
        self.assertEqual(p1.as_dict(), r)

    def test_deep_refs_in_referenced_dicts(self):
        p = Parameters({'A': '${C:a}', 'B': {'a': 1, 'b': 2}, 'C': '${B}'}, SETTINGS, '')
        r = {'A': 1, 'B': {'a': 1, 'b': 2}, 'C': {'a': 1, 'b': 2}}
        p.interpolate()
        self.assertEqual(p.as_dict(), r)

    def test_overwrite_none(self):
        p1 = Parameters({'A': None, 'B': None, 'C': None, 'D': None, 'E': None, 'F': None}, SETTINGS, '')
        p2 = Parameters({'A': 'abc', 'B': [1, 2, 3], 'C': {'a': 'aaa', 'b': 'bbb'}, 'D': '${A}', 'E': '${B}', 'F': '${C}'}, SETTINGS, '')
        r = {'A': 'abc', 'B': [1, 2, 3], 'C': {'a': 'aaa', 'b': 'bbb'}, 'D': 'abc', 'E': [1, 2, 3], 'F': {'a': 'aaa', 'b': 'bbb'}}
        p1.merge(p2)
        p1.interpolate()
        self.assertEqual(p1.as_dict(), r)

    def test_overwrite_dict(self):
        p1 = Parameters({'a': { 'one': 1, 'two': 2 }}, SETTINGS, '')
        p2 = Parameters({'~a': { 'three': 3, 'four': 4 }}, SETTINGS, '')
        r = {'a': { 'three': 3, 'four': 4 }}
        p1.merge(p2)
        p1.interpolate()
        self.assertEqual(p1.as_dict(), r)

    def test_overwrite_list(self):
        p1 = Parameters({'a': [1, 2]}, SETTINGS, '')
        p2 = Parameters({'~a': [3, 4]}, SETTINGS, '')
        r = {'a': [3, 4]}
        p1.merge(p2)
        p1.interpolate()
        self.assertEqual(p1.as_dict(), r)

    def test_interpolate_escaping(self):
        v = 'bar'.join(SETTINGS.reference_sentinels)
        d = {'foo': SETTINGS.escape_character + 'bar'.join(SETTINGS.reference_sentinels),
             'bar': 'unused'}
        p = Parameters(d, SETTINGS, '')
        p.initialise_interpolation()
        self.assertEqual(p.as_dict()['foo'], v)

    def test_interpolate_double_escaping(self):
        v = SETTINGS.escape_character + 'meep'
        d = {'foo': SETTINGS.escape_character + SETTINGS.escape_character + 'bar'.join(SETTINGS.reference_sentinels),
             'bar': 'meep'}
        p = Parameters(d, SETTINGS, '')
        p.interpolate()
        self.assertEqual(p.as_dict()['foo'], v)

    def test_interpolate_escaping_backwards_compatibility(self):
        """In all following cases, escaping should not happen and the escape character
        needs to be printed as-is, to ensure backwards compatibility to older versions."""
        v = ' '.join([
            # Escape character followed by unescapable character
            '1', SETTINGS.escape_character,
            # Escape character followed by escape character
            '2', SETTINGS.escape_character + SETTINGS.escape_character,
            # Escape character followed by interpolation end sentinel
            '3', SETTINGS.escape_character + SETTINGS.reference_sentinels[1],
            # Escape character at the end of the string
            '4', SETTINGS.escape_character
            ])
        d = {'foo': v}
        p = Parameters(d, SETTINGS, '')
        p.initialise_interpolation()
        self.assertEqual(p.as_dict()['foo'], v)

    def test_escape_close_in_ref(self):
        p1 = Parameters({'one}': 1, 'two': '${one\\}}'}, SETTINGS, '')
        r = {'one}': 1, 'two': 1}
        p1.interpolate()
        self.assertEqual(p1.as_dict(), r)

    def test_double_escape_in_ref(self):
        d = {'one\\': 1, 'two': '${one\\\\}'}
        p1 = Parameters(d, SETTINGS, '')
        r = {'one\\': 1, 'two': 1}
        p1.interpolate()
        self.assertEqual(p1.as_dict(), r)

    def test_merging_for_multiple_nodes(self):
        p1 = Parameters({ 'alpha': { 'one': 111 }}, SETTINGS, '')
        p2 = Parameters({ 'beta': {'two': '${alpha:one}' }}, SETTINGS, '')
        p3 = Parameters({ 'beta': {'two': 222 }}, SETTINGS, '')
        n1 = Parameters({ 'name': 'node1'}, SETTINGS, '')
        r1 = { 'alpha': { 'one': 111 }, 'beta': { 'two': 111 }, 'name': 'node1' }
        r2 = { 'alpha': { 'one': 111 }, 'beta': { 'two': 222 }, 'name': 'node2' }
        n1.merge(p1)
        n1.merge(p2)
        n1.interpolate()
        n2 = Parameters({'name': 'node2'}, SETTINGS, '')
        n2.merge(p1)
        n2.merge(p2)
        n2.merge(p3)
        n2.interpolate()
        self.assertEqual(n1.as_dict(), r1)
        self.assertEqual(n2.as_dict(), r2)

    def test_list_merging_for_multiple_nodes(self):
        p1 = Parameters({ 'alpha': { 'one': [1, 2] }}, SETTINGS, '')
        p2 = Parameters({ 'beta': {'two': '${alpha:one}' }}, SETTINGS, '')
        p3 = Parameters({ 'beta': {'two': [3] }}, SETTINGS, '')
        n1 = Parameters({ 'name': 'node1'}, SETTINGS, '')
        r1 = { 'alpha': { 'one': [1, 2] }, 'beta': { 'two': [1, 2] }, 'name': 'node1' }
        r2 = { 'alpha': { 'one': [1, 2] }, 'beta': { 'two': [1, 2, 3] }, 'name': 'node2' }
        n1.merge(p1)
        n1.merge(p2)
        n1.interpolate()
        n2 = Parameters({'name': 'node2'}, SETTINGS, '')
        n2.merge(p1)
        n2.merge(p2)
        n2.merge(p3)
        n2.interpolate()
        self.assertEqual(n1.as_dict(), r1)
        self.assertEqual(n2.as_dict(), r2)

    def test_dict_merging_for_multiple_nodes(self):
        p1 = Parameters({ 'alpha': { 'one': { 'a': 'aa', 'b': 'bb' }}}, SETTINGS, '')
        p2 = Parameters({ 'beta': {'two': '${alpha:one}' }}, SETTINGS, '')
        p3 = Parameters({ 'beta': {'two': {'c': 'cc' }}}, SETTINGS, '')
        n1 = Parameters({ 'name': 'node1'}, SETTINGS, '')
        r1 = { 'alpha': { 'one': {'a': 'aa', 'b': 'bb'} }, 'beta': { 'two': {'a': 'aa', 'b': 'bb'} }, 'name': 'node1' }
        r2 = { 'alpha': { 'one': {'a': 'aa', 'b': 'bb'} }, 'beta': { 'two': {'a': 'aa', 'b': 'bb', 'c': 'cc'} }, 'name': 'node2' }
        n1.merge(p1)
        n1.merge(p2)
        n1.interpolate()
        n2 = Parameters({'name': 'node2'}, SETTINGS, '')
        n2.merge(p1)
        n2.merge(p2)
        n2.merge(p3)
        n2.interpolate()
        self.assertEqual(n1.as_dict(), r1)
        self.assertEqual(n2.as_dict(), r2)

    def test_list_merging_with_refs_for_multiple_nodes(self):
        p1 = Parameters({ 'alpha': { 'one': [1, 2], 'two': [3, 4] }}, SETTINGS, '')
        p2 = Parameters({ 'beta': { 'three': '${alpha:one}' }}, SETTINGS, '')
        p3 = Parameters({ 'beta': { 'three': '${alpha:two}' }}, SETTINGS, '')
        p4 = Parameters({ 'beta': { 'three': '${alpha:one}' }}, SETTINGS, '')
        n1 = Parameters({ 'name': 'node1' }, SETTINGS, '')
        r1 = {'alpha': {'one': [1, 2], 'two': [3, 4]}, 'beta': {'three': [1, 2]}, 'name': 'node1'}
        r2 = {'alpha': {'one': [1, 2], 'two': [3, 4]}, 'beta': {'three': [1, 2, 3, 4, 1, 2]}, 'name': 'node2'}
        n2 = Parameters({ 'name': 'node2' }, SETTINGS, '')
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
        p1 = Parameters({ 'alpha': { 'one': 1, 'two': 2 } }, SETTINGS, '')
        p2 = Parameters({ 'beta': { 'three': 'one' } }, SETTINGS, '')
        p3 = Parameters({ 'beta': { 'three': 'two' } }, SETTINGS, '')
        p4 = Parameters({ 'beta': { 'four': '${alpha:${beta:three}}' } }, SETTINGS, '')
        n1 = Parameters({ 'name': 'node1' }, SETTINGS, '')
        r1 = {'alpha': {'one': 1, 'two': 2}, 'beta': {'three': 'one', 'four': 1}, 'name': 'node1'}
        r2 = {'alpha': {'one': 1, 'two': 2}, 'beta': {'three': 'two', 'four': 2}, 'name': 'node2'}
        n1.merge(p1)
        n1.merge(p4)
        n1.merge(p2)
        n1.interpolate()
        n2 = Parameters({ 'name': 'node2' }, SETTINGS, '')
        n2.merge(p1)
        n2.merge(p4)
        n2.merge(p3)
        n2.interpolate()
        self.assertEqual(n1.as_dict(), r1)
        self.assertEqual(n2.as_dict(), r2)

    def test_nested_refs_error_message(self):
        # beta is missing, oops
        p1 = Parameters({'alpha': {'one': 1, 'two': 2}, 'gamma': '${alpha:${beta}}'}, SETTINGS, '')
        with self.assertRaises(InterpolationError) as error:
            p1.interpolate()
        self.assertEqual(error.exception.message, "-> \n   Bad references, at gamma\n      ${beta}")

    def test_multiple_resolve_errors(self):
        p1 = Parameters({'alpha': '${gamma}', 'beta': '${gamma}'}, SETTINGS, '')
        with self.assertRaises(ResolveErrorList) as error:
            p1.interpolate()
        # interpolation can start with either alpha or beta
        self.assertIn(error.exception.message, [ "-> \n   Cannot resolve ${gamma}, at alpha\n   Cannot resolve ${gamma}, at beta",
                                                    "-> \n   Cannot resolve ${gamma}, at beta\n   Cannot resolve ${gamma}, at alpha"])

    def test_force_single_resolve_error(self):
        settings = copy.deepcopy(SETTINGS)
        settings.group_errors = False
        p1 = Parameters({'alpha': '${gamma}', 'beta': '${gamma}'}, settings, '')
        with self.assertRaises(ResolveError) as error:
            p1.interpolate()
        # interpolation can start with either alpha or beta
        self.assertIn(error.exception.message, [ "-> \n   Cannot resolve ${gamma}, at alpha",
                                                 "-> \n   Cannot resolve ${gamma}, at beta"])

    def test_ignore_overwriten_missing_reference(self):
        settings = copy.deepcopy(SETTINGS)
        settings.ignore_overwritten_missing_references = True
        p1 = Parameters({'alpha': '${beta}'}, settings, '')
        p2 = Parameters({'alpha': '${gamma}'}, settings, '')
        p3 = Parameters({'gamma': 3}, settings, '')
        r1 = {'alpha': 3, 'gamma': 3}
        p1.merge(p2)
        p1.merge(p3)
        err1 = "[WARNING] Reference '${beta}' undefined\n"
        with mock.patch('sys.stderr', new=MockDevice()) as std_err:
            p1.interpolate()
        self.assertEqual(p1.as_dict(), r1)
        self.assertEqual(std_err.text(), err1)

    def test_ignore_overwriten_missing_reference_last_value(self):
        # an error should be raised if the last reference to be merged
        # is missing even if ignore_overwritten_missing_references is true
        settings = copy.deepcopy(SETTINGS)
        settings.ignore_overwritten_missing_references = True
        p1 = Parameters({'alpha': '${gamma}'}, settings, '')
        p2 = Parameters({'alpha': '${beta}'}, settings, '')
        p3 = Parameters({'gamma': 3}, settings, '')
        p1.merge(p2)
        p1.merge(p3)
        with self.assertRaises(InterpolationError) as error:
            p1.interpolate()
        self.assertEqual(error.exception.message, "-> \n   Cannot resolve ${beta}, at alpha")

    def test_ignore_overwriten_missing_reference_dict(self):
        # setting ignore_overwritten_missing_references to true should
        # not change the behaviour for dicts
        settings = copy.deepcopy(SETTINGS)
        settings.ignore_overwritten_missing_references = True
        p1 = Parameters({'alpha': '${beta}'}, settings, '')
        p2 = Parameters({'alpha': '${gamma}'}, settings, '')
        p3 = Parameters({'gamma': {'one': 1, 'two': 2}}, settings, '')
        err1 = "[WARNING] Reference '${beta}' undefined\n"
        p1.merge(p2)
        p1.merge(p3)
        with self.assertRaises(InterpolationError) as error, mock.patch('sys.stderr', new=MockDevice()) as std_err:
            p1.interpolate()
        self.assertEqual(error.exception.message, "-> \n   Cannot resolve ${beta}, at alpha")
        self.assertEqual(std_err.text(), err1)

    def test_escaped_string_in_ref_dict_1(self):
        # test with escaped string in first dict to be merged
        p1 = Parameters({'a': { 'one': '${a_ref}' }, 'b': { 'two': '\${not_a_ref}' }, 'c': '${b}', 'a_ref': 123}, SETTINGS, '')
        p2 = Parameters({'c': '${a}'}, SETTINGS, '')
        r = { 'a': { 'one': 123 }, 'b': { 'two': '${not_a_ref}' }, 'c': { 'one': 123, 'two': '${not_a_ref}' }, 'a_ref': 123}
        p1.merge(p2)
        p1.interpolate()
        self.assertEqual(p1.as_dict(), r)

    def test_escaped_string_in_ref_dict_2(self):
        # test with escaped string in second dict to be merged
        p1 = Parameters({'a': { 'one': '${a_ref}' }, 'b': { 'two': '\${not_a_ref}' }, 'c': '${a}', 'a_ref': 123}, SETTINGS, '')
        p2 = Parameters({'c': '${b}'}, SETTINGS, '')
        r = { 'a': { 'one': 123 }, 'b': { 'two': '${not_a_ref}' }, 'c': { 'one': 123, 'two': '${not_a_ref}' }, 'a_ref': 123}
        p1.merge(p2)
        p1.interpolate()
        self.assertEqual(p1.as_dict(), r)

    def test_complex_overwrites_1(self):
        # find a better name for this test
        p1 = Parameters({ 'test': { 'dict': { 'a': '${values:one}', 'b': '${values:two}' } },
                          'values': { 'one': 1, 'two': 2, 'three': { 'x': 'X', 'y': 'Y' } } }, SETTINGS, '')
        p2 = Parameters({ 'test': { 'dict': { 'c': '${values:two}' } } }, SETTINGS, '')
        p3 = Parameters({ 'test': { 'dict': { '~b': '${values:three}' } } }, SETTINGS, '')
        r = {'test': {'dict': {'a': 1, 'b': {'x': 'X', 'y': 'Y'}, 'c': 2}}, 'values': {'one': 1, 'three': {'x': 'X', 'y': 'Y'}, 'two': 2} }
        p2.merge(p3)
        p1.merge(p2)
        p1.interpolate()
        self.assertEqual(p1.as_dict(), r)

    def test_escaped_string_overwrites(self):
        p1 = Parameters({ 'test': '\${not_a_ref}' }, SETTINGS, '')
        p2 = Parameters({ 'test': '\${also_not_a_ref}' }, SETTINGS, '')
        r = { 'test': '${also_not_a_ref}' }
        p1.merge(p2)
        p1.interpolate()
        self.assertEqual(p1.as_dict(), r)

    def test_escaped_string_in_ref_dict_overwrite(self):
        p1 = Parameters({'a': { 'one': '\${not_a_ref}' }, 'b': { 'two': '\${also_not_a_ref}' }}, SETTINGS, '')
        p2 = Parameters({'c': '${a}'}, SETTINGS, '')
        p3 = Parameters({'c': '${b}'}, SETTINGS, '')
        p4 = Parameters({'c': { 'one': '\${again_not_a_ref}' } }, SETTINGS, '')
        r = {'a': {'one': '${not_a_ref}'}, 'b': {'two': '${also_not_a_ref}'}, 'c': {'one': '${again_not_a_ref}', 'two': '${also_not_a_ref}'}}
        p1.merge(p2)
        p1.merge(p3)
        p1.merge(p4)
        p1.interpolate()
        self.assertEqual(p1.as_dict(), r)

    def test_strict_constant_parameter(self):
        p1 = Parameters({'one': { 'a': 1} }, SETTINGS, 'first')
        p2 = Parameters({'one': { '=a': 2} }, SETTINGS, 'second')
        p3 = Parameters({'one': { 'a': 3} }, SETTINGS, 'third')
        with self.assertRaises(ChangedConstantError) as e:
            p1.merge(p2)
            p1.merge(p3)
            p1.interpolate()
        self.assertEqual(e.exception.message, "-> \n   Attempt to change constant value, at one:a, in second; third")

    def test_constant_parameter(self):
        settings = Settings({'strict_constant_parameters': False})
        p1 = Parameters({'one': { 'a': 1} }, settings, 'first')
        p2 = Parameters({'one': { '=a': 2} }, settings, 'second')
        p3 = Parameters({'one': { 'a': 3} }, settings, 'third')
        r = {'one': { 'a': 2 } }
        p1.merge(p2)
        p1.merge(p3)
        p1.interpolate()
        self.assertEqual(p1.as_dict(), r)

    def test_interpolated_list_type(self):
        p1 = Parameters({'a': [ 1, 2, 3 ]}, SETTINGS, 'first')
        r = {'a': [ 1, 2, 3 ]}
        self.assertIs(type(p1.as_dict()['a']), ParameterList)
        p1.interpolate()
        self.assertIs(type(p1.as_dict()['a']), list)
        self.assertEqual(p1.as_dict(), r)

    def test_interpolated_dict_type(self):
        p1 = Parameters({'a': { 'one': 1, 'two': 2, 'three': 3 }}, SETTINGS, 'first')
        r = {'a': { 'one': 1, 'two': 2, 'three': 3 }}
        self.assertIs(type(p1.as_dict()['a']), ParameterDict)
        p1.interpolate()
        self.assertIs(type(p1.as_dict()['a']), dict)
        self.assertEqual(p1.as_dict(), r)

    def test_merged_interpolated_list_type(self):
        p1 = Parameters({'a': [ 1, 2, 3 ]}, SETTINGS, 'first')
        p2 = Parameters({'a': [ 4, 5, 6 ]}, SETTINGS, 'second')
        r = {'a': [ 1, 2, 3, 4, 5, 6 ]}
        self.assertIs(type(p1.as_dict()['a']), ParameterList)
        self.assertIs(type(p2.as_dict()['a']), ParameterList)
        p1.merge(p2)
        self.assertIs(type(p1.as_dict()['a']), ValueList)
        p1.interpolate()
        self.assertIs(type(p1.as_dict()['a']), list)
        self.assertEqual(p1.as_dict(), r)

    def test_merged_interpolated_dict_type(self):
        p1 = Parameters({'a': { 'one': 1, 'two': 2, 'three': 3 }}, SETTINGS, 'first')
        p2 = Parameters({'a': { 'four': 4, 'five': 5, 'six': 6 }}, SETTINGS, 'second')
        r = {'a': { 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6}}
        self.assertIs(type(p1.as_dict()['a']), ParameterDict)
        self.assertIs(type(p2.as_dict()['a']), ParameterDict)
        p1.merge(p2)
        self.assertIs(type(p1.as_dict()['a']), ParameterDict)
        p1.interpolate()
        self.assertIs(type(p1.as_dict()['a']), dict)
        self.assertEqual(p1.as_dict(), r)


if __name__ == '__main__':
    unittest.main()
