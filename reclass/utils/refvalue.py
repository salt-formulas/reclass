#
# -*- coding: utf-8 -*-
#
# This file is part of reclass (http://github.com/madduck/reclass)
#
# Copyright © 2007–14 martin f. krafft <madduck@madduck.net>
# Released under the terms of the Artistic Licence 2.0
#

import pyparsing as pp
from lxml import etree

import re

from reclass.utils.dictpath import DictPath
from reclass.defaults import PARAMETER_INTERPOLATION_SENTINELS, \
        PARAMETER_INTERPOLATION_DELIMITER
from reclass.errors import IncompleteInterpolationError, \
        UndefinedVariableError

_SENTINELS = [re.escape(s) for s in PARAMETER_INTERPOLATION_SENTINELS]
_RE = '(.+?)(?={0}|$)'.format(_SENTINELS[0])

_STR = 'STR'
_REF = 'REF'

class RefValue(object):
    '''
    Isolates references in string values

    RefValue can be used to isolate and eventually expand references to other
    parameters in strings. Those references can then be iterated and rendered
    in the context of a dictionary to resolve those references.

    RefValue always gets constructed from a string, because templating
    — essentially this is what's going on — is necessarily always about
    strings. Therefore, generally, the rendered value of a RefValue instance
    will also be a string.

    Nevertheless, as this might not be desirable, RefValue will return the
    referenced variable without casting it to a string, if the templated
    string contains nothing but the reference itself.

    For instance:

      mydict = {'favcolour': 'yellow', 'answer': 42, 'list': [1,2,3]}
      RefValue('My favourite colour is ${favolour}').render(mydict)
      → 'My favourite colour is yellow'      # a string

      RefValue('The answer is ${answer}').render(mydict)
      → 'The answer is 42'                   # a string

      RefValue('${answer}').render(mydict)
      → 42                                   # an int

      RefValue('${list}').render(mydict)
      → [1,2,3]                              # an list

    The markers used to identify references are set in reclass.defaults, as is
    the default delimiter.
    '''

    def __init__(self, string, delim=PARAMETER_INTERPOLATION_DELIMITER):
        self._delim = delim
        self._tokens = []
        self._refs = []
        self._parse(string)

    def _parse(self, string):
        # order of checking is important here, the nested ${} check then the regex
        scanner = pp.ZeroOrMore(pp.MatchFirst([
                                pp.nestedExpr(opener=PARAMETER_INTERPOLATION_SENTINELS[0], closer=PARAMETER_INTERPOLATION_SENTINELS[1]).setResultsName(_REF),
                                pp.Regex(_RE).setResultsName(_STR, listAllMatches=True)
                  ]))
        result = scanner.leaveWhitespace().parseString(string)
        xml = etree.fromstring(result.asXML())
        self._parseXML(xml)
        self._assembleRefs(self._tokens)

    def _parseXML(self, elements):
        self._tokens = []
        for el in elements:
            if (el.tag == _STR):
                self._tokens.append((_STR, el.text))
            elif (el.tag == _REF):
                self._tokens.append((_REF, self._parseRefXML(el)))
            else:
                self._tokens.append(('???', '???'))

    def _parseRefXML(self, elements):
        result = []
        for el in elements:
            if (len(el) == 0):
                result.append((_STR, el.text))
            else:
                result.append((_REF, self._parseRefXML(el)))
        return result

    def _assembleRefs(self, tokens, first=True):
        string = ''
        retNone = False
        for token in tokens:
            if token[0] == _STR:
                string += token[1]
            elif token[0] == _REF:
                s = self._assembleRefs(token[1], first=False)
                if s != None:
                    self._refs.append(s)
                if not first:
                   retNone = True
        if retNone:
            string = None
        return string

    def _resolve(self, ref, context):
        path = DictPath(self._delim, ref)
        try:
            return path.get_value(context)
        except KeyError as e:
            raise UndefinedVariableError(ref)

    def has_references(self):
        return len(self._refs) > 0

    def get_references(self):
        return self._refs

    def _assemble(self, tokens, resolver):
        # Preserve type if only one token
        if len(tokens) == 1:
            if tokens[0][0] == _STR:
                return tokens[0][1]
            elif tokens[0][0] == _REF:
                return resolver(self._assemble(tokens[0][1], resolver))
        # Multiple tokens
        string = ''
        for token in tokens:
            if token[0] == _STR:
                string += token[1]
            elif token[0] == _REF:
                string += str(resolver(self._assemble(token[1], resolver)))
        return string

    def render(self, context):
        resolver = lambda s: self._resolve(s, context)
        return self._assemble(self._tokens, resolver)

    def __repr__(self):
        do_not_resolve = lambda s: s.join(PARAMETER_INTERPOLATION_SENTINELS)
        return 'RefValue(%r, %r)' % (self._assemble(self._tokens, do_not_resolve),
                                     self._delim)
