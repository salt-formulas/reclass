#
# -*- coding: utf-8 -*-
#
# This file is part of reclass
#

import copy
import pyparsing as pp

from six import iteritems

from .item import Item
from reclass.settings import Settings
from reclass.utils.dictpath import DictPath
from reclass.errors import ExpressionError, ParseError, ResolveError

_OBJ = 'OBJ'
_TEST = 'TEST'
_LIST_TEST = 'LIST_TEST'
_LOGICAL = 'LOGICAL'
_OPTION = 'OPTION'

_VALUE = 'VALUE'
_IF = 'IF'
_AND = 'AND'
_OR = 'OR'

_EQUAL = '=='
_NOT_EQUAL = '!='

_IGNORE_ERRORS = '+IgnoreErrors'
_ALL_ENVS = '+AllEnvs'

class Element(object):

    def __init__(self, expression, delimiter):
        self._delimiter = delimiter
        self._export_path = None
        self._parameter_path = None
        self._parameter_value = None
        self._export_path, self._parameter_path, self._parameter_value = self._get_vars(expression[0][1], self._export_path, self._parameter_path, self._parameter_value)
        self._export_path, self._parameter_path, self._parameter_value = self._get_vars(expression[2][1], self._export_path, self._parameter_path, self._parameter_value)

        try:
            self._export_path.drop_first()
        except AttributeError:
            raise ExpressionError('No export')

        self._inv_refs = [ self._export_path ]
        self._test = expression[1][1]

        if self._parameter_path is not None:
            self._parameter_path.drop_first()
            self._refs = [ str(self._parameter_path) ]
        else:
            self._refs = []

    def refs(self):
        return self._refs

    def inv_refs(self):
        return self._inv_refs

    def value(self, context, items):
        if self._parameter_path is not None:
            self._parameter_value = self._resolve(self._parameter_path, context)

        if self._parameter_value is None or self._test is None:
            raise ExpressionError('Failed to render %s' % str(self), tbFlag=False)

        if self._export_path.exists_in(items):
            result = False
            export_value = self._resolve(self._export_path, items)
            if self._test == _EQUAL:
                if export_value == self._parameter_value:
                    result = True
            elif self._test == _NOT_EQUAL:
                if export_value != self._parameter_value:
                    result = True
            else:
                raise ExpressionError('Unknown test {0}'.format(self._test), tbFlag=False)
            return result
        else:
            return False

    def _resolve(self, path, dictionary):
        try:
            return path.get_value(dictionary)
        except KeyError as e:
            raise ResolveError(str(path))

    def _get_vars(self, var, export, parameter, value):
        if isinstance(var, str):
            path = DictPath(self._delimiter, var)
            if path.path[0].lower() == 'exports':
                export = path
            elif path.path[0].lower() == 'self':
                parameter = path
            elif path.path[0].lower() == 'true':
                value = True
            elif path.path[0].lower() == 'false':
                value = False
            else:
                value = var
        else:
            value = var
        return export, parameter, value


class Question(object):

    def __init__(self, expression, delimiter):
        self._elements = []
        self._operators = []
        self._delimiter = delimiter
        self._refs = []
        self._inv_refs = []
        i = 0
        while i < len(expression):
            e = Element(expression[i:], self._delimiter)
            self._elements.append(e)
            self._refs.extend(e.refs())
            self._inv_refs.extend(e.inv_refs())
            i += 3
            if i < len(expression):
                self._operators.append(expression[i][1])
                i += 1

    def refs(self):
        return self._refs

    def inv_refs(self):
        return self._inv_refs

    def value(self, context, items):
        if len(self._elements) == 0:
            return True
        elif len(self._elements) == 1:
            return self._elements[0].value(context, items)
        else:
            result = self._elements[0].value(context, items)
            for i in range(0, len(self._elements)-1):
                next_result = self._elements[i+1].value(context, items)
                if self._operators[i] == _AND:
                    result = result and next_result
                elif self._operators[i] == _OR:
                    result = result or next_result
                else:
                    raise ExpressionError('Unknown operator {0} {1}'.format(self._operators[i], self.elements), tbFlag=False)
            return result


class InvItem(Item):

    def _get_parser():

        def _object(string, location, tokens):
            token = tokens[0]
            tokens[0] = (_OBJ, token)

        def _integer(string, location, tokens):
            try:
                token = int(tokens[0])
            except ValueError:
                token = tokens[0]
            tokens[0] = (_OBJ, token)

        def _number(string, location, tokens):
            try:
                token = float(tokens[0])
            except ValueError:
                token = tokens[0]
            tokens[0] = (_OBJ, token)

        def _option(string, location, tokens):
            token = tokens[0]
            tokens[0] = (_OPTION, token)

        def _test(string, location, tokens):
            token = tokens[0]
            tokens[0] = (_TEST, token)

        def _logical(string, location, tokens):
            token = tokens[0]
            tokens[0] = (_LOGICAL, token)

        def _if(string, location, tokens):
            token = tokens[0]
            tokens[0] = (_IF, token)

        def _expr_var(string, location, tokens):
            token = tokens[0]
            tokens[0] = (_VALUE, token)

        def _expr_test(string, location, tokens):
            token = tokens[0]
            tokens[0] = (_TEST, token)

        def _expr_list_test(string, location, tokens):
            token = tokens[0]
            tokens[0] = (_LIST_TEST, token)

        white_space = pp.White().suppress()
        end = pp.StringEnd()
        ignore_errors = pp.CaselessLiteral(_IGNORE_ERRORS)
        all_envs = pp.CaselessLiteral(_ALL_ENVS)
        option = (ignore_errors | all_envs).setParseAction(_option)
        options = pp.Group(pp.ZeroOrMore(option + white_space))
        operator_test = (pp.Literal(_EQUAL) | pp.Literal(_NOT_EQUAL)).setParseAction(_test)
        operator_logical = (pp.CaselessLiteral(_AND) | pp.CaselessLiteral(_OR)).setParseAction(_logical)
        begin_if = pp.CaselessLiteral(_IF, ).setParseAction(_if)
        obj = pp.Word(pp.printables).setParseAction(_object)
        integer = pp.Word('0123456789-').setParseAction(_integer)
        number = pp.Word('0123456789-.').setParseAction(_number)
        item = integer | number | obj
        single_test = white_space + item + white_space + operator_test + white_space + item
        additional_test = white_space + operator_logical + single_test
        expr_var = pp.Group(obj + pp.Optional(white_space) + end).setParseAction(_expr_var)
        expr_test = pp.Group(obj + white_space + begin_if + single_test + pp.ZeroOrMore(additional_test) + end).setParseAction(_expr_test)
        expr_list_test = pp.Group(begin_if + single_test + pp.ZeroOrMore(additional_test) + end).setParseAction(_expr_list_test)
        expr = (expr_test | expr_var | expr_list_test)
        line = options + expr + end
        return line

    _parser = _get_parser()

    def __init__(self, item, settings):
        self.type = Item.INV_QUERY
        self._settings = settings
        self._needs_all_envs = False
        self._ignore_failed_render = self._settings.inventory_ignore_failed_render
        self._expr_text = item.render(None, None)
        self._parse_expression(self._expr_text)

    def _parse_expression(self, expr):
        try:
            tokens = InvItem._parser.parseString(expr).asList()
        except pp.ParseException as e:
            raise ParseError(e.msg, e.line, e.col, e.lineno)

        if len(tokens) == 1:
            self._expr_type = tokens[0][0]
            self._expr = list(tokens[0][1])
        elif len(tokens) == 2:
            for opt in tokens[0]:
                if opt[1] == _IGNORE_ERRORS:
                    self._ignore_failed_render = True
                elif opt[1] == _ALL_ENVS:
                    self._needs_all_envs = True
            self._expr_type = tokens[1][0]
            self._expr = list(tokens[1][1])
        else:
            raise ExpressionError('Failed to parse %s' % str(tokens), tbFlag=False)

        if self._expr_type == _VALUE:
            self._value_path = DictPath(self._settings.delimiter, self._expr[0][1]).drop_first()
            self._question = Question([], self._settings.delimiter)
            self._refs = []
            self._inv_refs = [ self._value_path ]
        elif self._expr_type == _TEST:
            self._value_path = DictPath(self._settings.delimiter, self._expr[0][1]).drop_first()
            self._question = Question(self._expr[2:], self._settings.delimiter)
            self._refs = self._question.refs()
            self._inv_refs = self._question.inv_refs()
            self._inv_refs.append(self._value_path)
        elif self._expr_type == _LIST_TEST:
            self._value_path = None
            self._question = Question(self._expr[1:], self._settings.delimiter)
            self._refs = self._question.refs()
            self._inv_refs = self._question.inv_refs()
        else:
            raise ExpressionError('Unknown expression type: %s' % self._expr_type, tbFlag=False)

    def assembleRefs(self, context):
        return

    def contents(self):
        return self._expr_text

    def has_inv_query(self):
        return True

    def has_references(self):
        return len(self._question.refs()) > 0

    def get_references(self):
        return self._question.refs()

    def get_inv_references(self):
        return self._inv_refs

    def needs_all_envs(self):
        return self._needs_all_envs

    def ignore_failed_render(self):
        return self._ignore_failed_render

    def _resolve(self, path, dictionary):
        try:
            return path.get_value(dictionary)
        except KeyError as e:
            raise ResolveError(str(path))

    def _value_expression(self, inventory):
        results = {}
        for (node, items) in iteritems(inventory):
            if self._value_path.exists_in(items):
                results[node] = copy.deepcopy(self._resolve(self._value_path, items))
        return results

    def _test_expression(self, context, inventory):
        if self._value_path is None:
            ExpressionError('Failed to render %s' % str(self), tbFlag=False)

        results = {}
        for (node, items) in iteritems(inventory):
            if self._question.value(context, items) and self._value_path.exists_in(items):
                results[node] = copy.deepcopy(self._resolve(self._value_path, items))
        return results

    def _list_test_expression(self, context, inventory):
        results = []
        for (node, items) in iteritems(inventory):
            if self._question.value(context, items):
                results.append(node)
        return results

    def render(self, context, inventory):
        if self._expr_type == _VALUE:
            return self._value_expression(inventory)
        elif self._expr_type == _TEST:
            return self._test_expression(context, inventory)
        elif self._expr_type == _LIST_TEST:
            return self._list_test_expression(context, inventory)
        raise ExpressionError('Failed to render %s' % str(self), tbFlag=False)

    def __str__(self):
        return ' '.join(str(j) for i,j in self._expr)

    def __repr__(self):
        return 'InvItem(%r)' % self._expr
