#
# -*- coding: utf-8 -*-
#
# This file is part of reclass (http://github.com/madduck/reclass)
#
# Copyright © 2007–14 martin f. krafft <madduck@madduck.net>
# Released under the terms of the Artistic Licence 2.0
#

import pyparsing as pp

from reclass.settings import Settings
from reclass.values.value import Value
from reclass.errors import ResolveError, ParseError
import unittest

SETTINGS = Settings()

def _var(s):
    return '%s%s%s' % (SETTINGS.reference_sentinels[0], s,
                       SETTINGS.reference_sentinels[1])

CONTEXT = {'favcolour':'yellow',
           'motd':{'greeting':'Servus!',
                   'colour':'${favcolour}'
                  },
           'int':1,
           'list':[1,2,3],
           'dict':{1:2,3:4},
           'bool':True
          }

def _poor_mans_template(s, var, value):
    return s.replace(_var(var), value)

class TestValue(unittest.TestCase):

    def test_simple_string(self):
        s = 'my cat likes to hide in boxes'
        tv = Value(s, SETTINGS, '')
        self.assertFalse(tv.has_references())
        self.assertEquals(tv.render(CONTEXT, None), s)

    def _test_solo_ref(self, key):
        s = _var(key)
        tv = Value(s, SETTINGS, '')
        res = tv.render(CONTEXT, None)
        self.assertTrue(tv.has_references())
        self.assertEqual(res, CONTEXT[key])

    def test_solo_ref_string(self):
        self._test_solo_ref('favcolour')

    def test_solo_ref_int(self):
        self._test_solo_ref('int')

    def test_solo_ref_list(self):
        self._test_solo_ref('list')

    def test_solo_ref_dict(self):
        self._test_solo_ref('dict')

    def test_solo_ref_bool(self):
        self._test_solo_ref('bool')

    def test_single_subst_bothends(self):
        s = 'I like ' + _var('favcolour') + ' and I like it'
        tv = Value(s, SETTINGS, '')
        self.assertTrue(tv.has_references())
        self.assertEqual(tv.render(CONTEXT, None),
                         _poor_mans_template(s, 'favcolour',
                                             CONTEXT['favcolour']))

    def test_single_subst_start(self):
        s = _var('favcolour') + ' is my favourite colour'
        tv = Value(s, SETTINGS, '')
        self.assertTrue(tv.has_references())
        self.assertEqual(tv.render(CONTEXT, None),
                         _poor_mans_template(s, 'favcolour',
                                             CONTEXT['favcolour']))

    def test_single_subst_end(self):
        s = 'I like ' + _var('favcolour')
        tv = Value(s, SETTINGS, '')
        self.assertTrue(tv.has_references())
        self.assertEqual(tv.render(CONTEXT, None),
                         _poor_mans_template(s, 'favcolour',
                                             CONTEXT['favcolour']))

    def test_deep_subst_solo(self):
        motd = SETTINGS.delimiter.join(('motd', 'greeting'))
        s = _var(motd)
        tv = Value(s, SETTINGS, '')
        self.assertTrue(tv.has_references())
        self.assertEqual(tv.render(CONTEXT, None),
                         _poor_mans_template(s, motd,
                                             CONTEXT['motd']['greeting']))

    def test_multiple_subst(self):
        greet = SETTINGS.delimiter.join(('motd', 'greeting'))
        s = _var(greet) + ' I like ' + _var('favcolour') + '!'
        tv = Value(s, SETTINGS, '')
        self.assertTrue(tv.has_references())
        want = _poor_mans_template(s, greet, CONTEXT['motd']['greeting'])
        want = _poor_mans_template(want, 'favcolour', CONTEXT['favcolour'])
        self.assertEqual(tv.render(CONTEXT, None), want)

    def test_multiple_subst_flush(self):
        greet = SETTINGS.delimiter.join(('motd', 'greeting'))
        s = _var(greet) + ' I like ' + _var('favcolour')
        tv = Value(s, SETTINGS, '')
        self.assertTrue(tv.has_references())
        want = _poor_mans_template(s, greet, CONTEXT['motd']['greeting'])
        want = _poor_mans_template(want, 'favcolour', CONTEXT['favcolour'])
        self.assertEqual(tv.render(CONTEXT, None), want)

    def test_undefined_variable(self):
        s = _var('no_such_variable')
        tv = Value(s, SETTINGS, '')
        with self.assertRaises(ResolveError):
            tv.render(CONTEXT, None)

    def test_incomplete_variable(self):
        s = SETTINGS.reference_sentinels[0] + 'incomplete'
        with self.assertRaises(ParseError):
            tv = Value(s, SETTINGS, '')

if __name__ == '__main__':
    unittest.main()
