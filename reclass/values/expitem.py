#
# -*- coding: utf-8 -*-
#
# This file is part of reclass
#

import copy
import pyparsing as pp

from item import Item
from reclass.utils.dictpath import DictPath
from reclass.errors import ExpressionError, UndefinedVariableError

_VAR = 'VAR'
_TEST = 'TEST'
_VALUE = 'VALUE'

_IF = 'IF'
_EQUAL = '=='
_NOT_EQUAL = '!='

class ExpItem(Item):

    def _get_parser():

        def _variable(string, location, tokens):
            token = tokens[0]
            tokens[0] = (_VAR, token)

        def _test(string, location, tokens):
            token = tokens[0]
            tokens[0] = (_TEST, token)

        def _if(string, location, tokens):
            token = tokens[0]
            tokens[0] = (_IF, token)

        _EXCLUDES = '?!='
        _END_IF = '?'

        white_space = pp.White().suppress()
        end = pp.StringEnd()
        operator = (pp.Literal(_EQUAL) | pp.Literal(_NOT_EQUAL)).setParseAction(_test)
        end_if = pp.Literal(_END_IF).setParseAction(_if)
        not_operator = ~pp.Literal(_EQUAL) + ~pp.Literal(_NOT_EQUAL) + ~pp.Literal(_END_IF)
        variable = not_operator + pp.Word(pp.printables).setParseAction(_variable)
        item = (operator | end_if | variable) + (white_space | end)
        expr = pp.Optional(white_space) + pp.OneOrMore(item)
        return expr

    _parser = _get_parser()

    def __init__(self, item, delimiter):
        self._delimiter = delimiter
        self._type = None
        self._refs = []
        self._expr = []
        self._parse_expression(item.render(None, None))

    def _parse_expression(self, expr):
        try:
            self._expr = ExpItem._parser.parseString(expr).asList()
        except pp.ParseException as e:
            raise ParseError(e.msg, e.line, e.col, e.lineno)

        if len(self._expr) == 1 and self._expr[0][0] == _VAR:
            self._type = _VALUE
            return
        elif len(self._expr) == 5 and self._expr[0][0] == _VAR and self._expr[1][0] == _TEST and self._expr[2][0] == _VAR and self._expr[3][0] == _IF and self._expr[4][0] == _VAR:
            self._type = _TEST
            export, parameter, value = self._get_vars(self._expr[0][1], None, None, None)
            export, parameter, value = self._get_vars(self._expr[2][1], export, parameter, value)
            if parameter != None:
                path = DictPath(self._delimiter, parameter).drop_first()
                self._ref.append(str(path))
            return
        raise ExpressionError('Failed to parse %s' % str(self))

    def contents(self):
        return self._expr

    def has_exports(self):
        return True

    def has_references(self):
        return len(self._refs) > 0

    def get_references(self):
        return self._refs

    def _resolve(self, path, dictionary):
        try:
            return path.get_value(dictionary)
        except KeyError as e:
            raise UndefinedVariableError(str(path))

    def _value_expression(self, exports):
        results = {}
        path = DictPath(self._delimiter, self._expr[0][1]).drop_first()
        for node, items in exports.iteritems():
            if path.exists_in(items):
                results[node] = copy.deepcopy(self._resolve(path, items))
        return results

    def _if_expression(self, context, exports):
        export_path = None
        parameter_path = None
        parameter_value = None
        test = None
        value_path = DictPath(self._delimiter, self._expr[4][1])

        if self._expr[1][1] == _EQUAL:
            test = _EQUAL
        elif self._expr[1][1] == _NOT_EQUAL:
            test = _NOT_EQUAL

        export_path, parameter_path, parameter_value = self._get_vars(self._expr[0][1], export_path, parameter_path, parameter_value)
        export_path, parameter_path, parameter_value = self._get_vars(self._expr[2][1], export_path, parameter_path, parameter_value)

        if parameter_path != None:
            parameter_path.drop_first()
            parameter_value = str(self._resolve(parameter, context))

        if export_path is None or parameter_value is None or test is None or value_path is None:
            ExpressionError('Failed to render %s' % str(self))

        export_path.drop_first()
        value_path.drop_first()

        results = {}
        for node, items in exports.iteritems():
            if export_path.exists_in(items):
                export_value = str(self._resolve(export_path, items))
                test_passed = False
                if test == _EQUAL and export_value == parameter_value:
                    test_passed = True
                elif test == _NOT_EQUAL and export_value != parameter_value:
                    test_passed = True
                if test_passed:
                    results[node] = copy.deepcopy(self._resolve(value_path, items))
        return results

    def _get_vars(self, var, export, parameter, value):
        if isinstance(var, str):
            path = DictPath(self._delimiter, var)
            if path.path[0] == 'exports':
                export = path
            elif path.path[0] == 'SELF':
                parameter = path
            else:
                value = var
        else:
            value = var
        return export, parameter, value

    def render(self, context, exports):
        if self._type == _VALUE:
            return self._value_expression(exports)
        elif self._type == _TEST:
            return self._if_expression(context, exports)
        raise ExpressionError('Failed to render %s' % str(self))

    def __str__(self):
        return ' '.join(str(j) for i,j in self._expr)

    def __repr__(self):
        return 'ExpItem(%r)' % self._expr
