#
# -*- coding: utf-8 -*-
#
# This file is part of reclass
#
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import copy
import itertools as it
import operator
import pyparsing as pp

from six import iteritems
from six import string_types

from reclass.values import item, parser_funcs
from reclass.settings import Settings
from reclass.utils.dictpath import DictPath
from reclass.errors import ExpressionError, ParseError, ResolveError


# TODO: generalize expression handling.
class BaseTestExpression(object):

    known_operators = {}
    def __init__(self, delimiter):
        self._delimiter = delimiter
        self.refs = []
        self.inv_refs = []


class EqualityTest(BaseTestExpression):

    known_operators = { parser_funcs.EQUAL: operator.eq,
                        parser_funcs.NOT_EQUAL: operator.ne}

    def __init__(self, expression, delimiter):
        # expression is a list of at least three tuples, of which first element
        # is a string tag, second is subelement value; other tuples apparently
        # are not used.
        # expression[0][1] effectively contains export path and apparently must
        # be treated as such, also left hand operand in comparison
        # expression[1][1] appa holds commparison operator == or !=
        # expression[2][1] is the righhand operand
        super(EqualityTest, self).__init__(delimiter)
        # TODO: this double sommersault must be cleaned
        _ = self._get_vars(expression[2][1], *self._get_vars(expression[0][1]))
        self._export_path, self._parameter_path, self._parameter_value = _
        try:
            self._export_path.drop_first()
        except AttributeError:
            raise ExpressionError('No export')
        try:
            self._compare = self.known_operators[expression[1][1]]
        except KeyError as e:
            msg = 'Unknown test {0}'.format(expression[1][1])
            raise ExpressionError(msg, tbFlag=False)
        self.inv_refs = [self._export_path]
        if self._parameter_path is not None:
            self._parameter_path.drop_first()
            self.refs = [str(self._parameter_path)]

    def value(self, context, items):
        if self._parameter_path is not None:
            self._parameter_value = self._resolve(self._parameter_path,
                                                  context)
        if self._parameter_value is None:
            raise ExpressionError('Failed to render %s' % str(self),
                                  tbFlag=False)
        if self._export_path.exists_in(items):
            export_value = self._resolve(self._export_path, items)
            return self._compare(export_value, self._parameter_value)
        return False

    def _resolve(self, path, dictionary):
        try:
            return path.get_value(dictionary)
        except KeyError as e:
            raise ResolveError(str(path))

    def _get_vars(self, var, export=None, parameter=None, value=None):
        if isinstance(var, string_types):
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


class LogicTest(BaseTestExpression):

    known_operators = { parser_funcs.AND: operator.and_,
                        parser_funcs.OR: operator.or_}

    def __init__(self, expr, delimiter):
        super(LogicTest, self).__init__(delimiter)
        subtests = list(it.compress(expr, it.cycle([1, 1, 1, 0])))
        self._els = [EqualityTest(subtests[j:j+3], self._delimiter)
                     for j in range(0, len(subtests), 3)]
        for x in self._els:
            self.refs.extend(x.refs)
            self.inv_refs.extend(x.inv_refs)
        try:
            self._ops = [self.known_operators[x[1]] for x in expr[3::4]]
        except KeyError as e:
            msg = 'Unknown operator {0} {1}'.format(e.messsage, self._els)
            raise ExpressionError(msg, tbFlag=False)

    def value(self, context, items):
        if len(self._els) == 0:  # NOTE: possible logic error
            return True
        result = self._els[0].value(context, items)
        for op, next_el in zip(self._ops, self._els[1:]):
            result = op(result, next_el.value(context, items))
        return result


class InvItem(item.Item):

    type = item.ItemTypes.INV_QUERY

    def __init__(self, newitem, settings):
        super(InvItem, self).__init__(newitem.render(None, None), settings)
        self.needs_all_envs = False
        self.has_inv_query = True
        self.ignore_failed_render = (
                self._settings.inventory_ignore_failed_render)
        self._parse_expression(self.contents)

    def _parse_expression(self, expr):
        parser = parser_funcs.get_expression_parser()
        try:
            tokens = parser.parseString(expr).asList()
        except pp.ParseException as e:
            raise ParseError(e.msg, e.line, e.col, e.lineno)

        if len(tokens) == 2:  # options are set
            passed_opts = [x[1] for x in tokens.pop(0)]
            self.ignore_failed_render = parser_funcs.IGNORE_ERRORS in passed_opts
            self.needs_all_envs = parser_funcs.ALL_ENVS in passed_opts
        elif len(tokens) > 2:
            raise ExpressionError('Failed to parse %s' % str(tokens),
                                  tbFlag=False)
        self._expr_type = tokens[0][0]
        self._expr = list(tokens[0][1])

        if self._expr_type == parser_funcs.VALUE:
            self._value_path = DictPath(self._settings.delimiter,
                                        self._expr[0][1]).drop_first()
            self._question = LogicTest([], self._settings.delimiter)
            self.refs = []
            self.inv_refs = [self._value_path]
        elif self._expr_type == parser_funcs.TEST:
            self._value_path = DictPath(self._settings.delimiter,
                                        self._expr[0][1]).drop_first()
            self._question = LogicTest(self._expr[2:], self._settings.delimiter)
            self.refs = self._question.refs
            self.inv_refs = self._question.inv_refs
            self.inv_refs.append(self._value_path)
        elif self._expr_type == parser_funcs.LIST_TEST:
            self._value_path = None
            self._question = LogicTest(self._expr[1:], self._settings.delimiter)
            self.refs = self._question.refs
            self.inv_refs = self._question.inv_refs
        else:
            msg = 'Unknown expression type: %s'
            raise ExpressionError(msg % self._expr_type, tbFlag=False)

    @property
    def has_references(self):
        return len(self._question.refs) > 0

    def get_references(self):
        return self._question.refs

    def assembleRefs(self, context):
        return

    def get_inv_references(self):
        return self.inv_refs

    def _resolve(self, path, dictionary):
        try:
            return path.get_value(dictionary)
        except KeyError as e:
            raise ResolveError(str(path))

    def _value_expression(self, inventory):
        results = {}
        for name, node in iteritems(inventory):
            if self.needs_all_envs or node.env_matches:
                if self._value_path.exists_in(node.items):
                    answer = self._resolve(self._value_path, node.items)
                    results[name] = copy.deepcopy(answer)
        return results

    def _test_expression(self, context, inventory):
        if self._value_path is None:
            msg = 'Failed to render %s'
            raise ExpressionError(msg % str(self), tbFlag=False)

        results = {}
        for name, node  in iteritems(inventory):
            if self.needs_all_envs or node.env_matches:
                if (self._question.value(context, node.items) and
                    self._value_path.exists_in(node.items)):
                    answer = self._resolve(self._value_path, node.items)
                    results[name] = copy.deepcopy(answer)
        return results

    def _list_test_expression(self, context, inventory):
        results = []
        for name, node in iteritems(inventory):
            if self.needs_all_envs or node.env_matches:
                if self._question.value(context, node.items):
                    results.append(name)
        results.sort()
        return results

    def render(self, context, inventory):
        if self._expr_type == parser_funcs.VALUE:
            return self._value_expression(inventory)
        elif self._expr_type == parser_funcs.TEST:
            return self._test_expression(context, inventory)
        elif self._expr_type == parser_funcs.LIST_TEST:
            return self._list_test_expression(context, inventory)
        raise ExpressionError('Failed to render %s' % str(self), tbFlag=False)

    def __str__(self):
        return ' '.join(str(j) for i,j in self._expr)

    def __repr__(self):
        # had to leave it here for now as the behaviour differs from basic
        return 'InvItem(%r)' % self._expr
