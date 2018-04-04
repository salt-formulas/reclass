#
# -*- coding: utf-8 -*-
#
# This file is part of reclass
#

import pyparsing as pp

from .compitem import CompItem
from .invitem import InvItem
from .refitem import RefItem
from .scaitem import ScaItem

from reclass.errors import ParseError
from reclass.values.parser_funcs import STR, REF, INV

class Parser(object):

    def parse(self, value, settings):
        self._settings = settings
        dollars = value.count('$')
        if dollars == 0:
            # speed up: only use pyparsing if there is a $ in the string
            return ScaItem(value, self._settings)
        elif dollars == 1:
            # speed up: try a simple reference
            try:
                tokens = self._settings.simple_ref_parser.leaveWhitespace().parseString(value).asList()
            except pp.ParseException:
                # fall back on the full parser
                try:
                    tokens = self._settings.ref_parser.leaveWhitespace().parseString(value).asList()
                except pp.ParseException as e:
                    raise ParseError(e.msg, e.line, e.col, e.lineno)
        else:
            # use the full parser
            try:
                tokens = self._settings.ref_parser.leaveWhitespace().parseString(value).asList()
            except pp.ParseException as e:
                raise ParseError(e.msg, e.line, e.col, e.lineno)

        items = self._create_items(tokens)
        if len(items) == 1:
            return items[0]
        else:
            return CompItem(items, self._settings)

    _create_dict = { STR: (lambda s, v: ScaItem(v, s._settings)),
                     REF: (lambda s, v: s._create_ref(v)),
                     INV: (lambda s, v: s._create_inv(v)) }

    def _create_items(self, tokens):
        return [ self._create_dict[t](self, v) for t, v in tokens ]

    def _create_ref(self, tokens):
        items = [ self._create_dict[t](self, v) for t, v in tokens ]
        return RefItem(items, self._settings)

    def _create_inv(self, tokens):
        items = [ ScaItem(v, self._settings) for t, v in tokens ]
        if len(items) == 1:
            return InvItem(items[0], self._settings)
        else:
            return InvItem(CompItem(items), self._settings)
