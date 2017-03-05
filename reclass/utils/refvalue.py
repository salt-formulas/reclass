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
        self._allRefs = False
        self._parse(string)

    def _getParser():

        def _push(description, string, location, tokens):
            RefValue._stack.append((description, tokens))

        def _string(string, location, tokens):
            _push(_STR, string, location, tokens)

        def _reference(string, location, tokens):
            _push(_REF, string, location, tokens)

        string = (pp.Literal('\\\\').setParseAction(pp.replaceWith('\\')) |
                  pp.Literal('\\$').setParseAction(pp.replaceWith('$')) |
                  pp.White() |
                  pp.Word(pp.printables, excludeChars='\\$')).setParseAction(_string)

        refString = (pp.Literal('\\\\').setParseAction(pp.replaceWith('\\')) |
                     pp.Literal('\\$').setParseAction(pp.replaceWith('$')) |
                     pp.Literal('\\{').setParseAction(pp.replaceWith('{')) |
                     pp.Literal('\\}').setParseAction(pp.replaceWith('}')) |
                     pp.White() |
                     pp.Word(pp.printables, excludeChars='\\${}')).setParseAction(_string)

        refItem = pp.Forward()
        refItems = pp.OneOrMore(refItem)
        reference = (pp.Literal('${').suppress() + pp.Group(refItems) + pp.Literal('}').suppress()).setParseAction(_reference)
        refItem << (reference | refString)

        item = reference | string
        line = pp.OneOrMore(item) + pp.StringEnd()
        return line

    _stack = []
    _parser = _getParser()

    def _tokenise(self, items, stack):
        result = []
        for n, i in reversed(list(enumerate(items))):
            t = stack.pop()[0]
            if (t == _REF):
               result.insert(0, (_REF, self._tokenise(i, stack) ))
            else:
               result.insert(0, (_STR, i))
        return result

    def _parse(self, string):
        del RefValue._stack[:]
        result = RefValue._parser.leaveWhitespace().parseString(string)
        self._tokens = self._tokenise(result, RefValue._stack)
        self.assembleRefs()

    def _assembleRefs(self, tokens, resolver, first=True):
        for token in tokens:
            if token[0] == _REF:
                self._assembleRefs(token[1], resolver, False)
                try:
                    s = self._assemble(token[1], resolver)
                    self._refs.append(s)
                except UndefinedVariableError as e:
                    self._allRefs = False
                    pass

    def assembleRefs(self, context={}):
        resolver = lambda s: self._resolve(s, context)
        self._refs = []
        self._allRefs = True
        self._assembleRefs(self._tokens, resolver, True)

    def assembledAllRefs(self):
        return self._allRefs

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
