#
# -*- coding: utf-8 -*-
#
# This file is part of reclass (http://github.com/madduck/reclass)
#
# Copyright © 2007–14 martin f. krafft <madduck@madduck.net>
# Released under the terms of the Artistic Licence 2.0
#

import copy
import sys
import types
from collections import namedtuple
from reclass.defaults import *
from reclass.utils.dictpath import DictPath
from reclass.values.mergeoptions import MergeOptions
from reclass.values.value import Value
from reclass.values.valuelist import ValueList
from reclass.errors import InfiniteRecursionError, UndefinedVariableError, InterpolationError

class Parameters(object):
    '''
    A class to hold nested dictionaries with the following specialities:

      1. "merging" a dictionary (the "new" dictionary) into the current
         Parameters causes a recursive walk of the new dict, during which

         - scalars (incl. tuples) are replaced with the value from the new
           dictionary;
         - lists are extended, not replaced;
         - dictionaries are updated (using dict.update), not replaced;

      2. "interpolating" a dictionary means that values within the dictionary
         can reference other values in the same dictionary. Those references
         are collected during merging and then resolved during interpolation,
         which avoids having to walk the dictionary twice. If a referenced
         value contains references itself, those are resolved first, in
         topological order. Therefore, deep references work. Cyclical
         references cause an error.

    To support these specialities, this class only exposes very limited
    functionality and does not try to be a really mapping object.
    '''
    DEFAULT_PATH_DELIMITER = PARAMETER_INTERPOLATION_DELIMITER
    DICT_KEY_OVERRIDE_PREFIX = PARAMETER_DICT_KEY_OVERRIDE_PREFIX

    def __init__(self, mapping=None, delimiter=None, options=None):
        if delimiter is None:
            delimiter = Parameters.DEFAULT_PATH_DELIMITER
        if options is None:
            options = MergeOptions()
        self._delimiter = delimiter
        self._base = {}
        self._unrendered = None
        self._escapes_handled = {}
        self._has_inv_query = False
        self._options = options
        if mapping is not None:
            # we initialise by merging
            self._keep_overrides = True
            self.merge(mapping)
            self._keep_overrides = False

    delimiter = property(lambda self: self._delimiter)

    def __len__(self):
        return len(self._base)

    def __repr__(self):
        return '%s(%r, %r)' % (self.__class__.__name__, self._base,
                               self._delimiter)

    def __eq__(self, other):
        return isinstance(other, type(self)) \
                and self._base == other._base \
                and self._delimiter == other._delimiter

    def __ne__(self, other):
        return not self.__eq__(other)

    def has_inv_query(self):
        return self._has_inv_query

    def as_dict(self):
        return self._base.copy()

    def _wrap_value(self, value):
        if isinstance(value, dict):
            return self._wrap_dict(value)
        elif isinstance(value, list):
            return self._wrap_list(value)
        elif isinstance(value, (Value, ValueList)):
            return value
        else:
            return Value(value, self._delimiter)

    def _wrap_list(self, source):
        return [ self._wrap_value(v) for v in source ]

    def _wrap_dict(self, source):
        return { k: self._wrap_value(v) for k, v in source.iteritems() }

    def _update_value(self, cur, new, path):
        if isinstance(cur, Value):
            values = ValueList(cur)
        elif isinstance(cur, ValueList):
            values = cur
        else:
            values = ValueList(Value(cur))

        if isinstance(new, Value):
            values.append(new)
        elif isinstance(new, ValueList):
            values.extend(new)
        else:
            values.append(Value(new))

        return values

    def _merge_dict(self, cur, new, path):
        """Merge a dictionary with another dictionary.

        Iterate over keys in new. If this is not an initialization merge and
        the key begins with PARAMETER_DICT_KEY_OVERRIDE_PREFIX, override the
        value of the key in cur. Otherwise deeply merge the contents of the key
        in cur with the contents of the key in _merge_recurse over the item.

        Args:
            cur (dict): Current dictionary
            new (dict): Dictionary to be merged
            path (string): Merging path from recursion
            initmerge (bool): True if called as part of entity init

        Returns:
            dict: a merged dictionary

        """

        ret = cur
        ovrprfx = Parameters.DICT_KEY_OVERRIDE_PREFIX
        for key, newvalue in new.iteritems():
            if key.startswith(ovrprfx) and not self._keep_overrides:
                ret[key.lstrip(ovrprfx)] = newvalue
            else:
                ret[key] = self._merge_recurse(ret.get(key), newvalue, path.new_subpath(key))
        return ret

    def _merge_recurse(self, cur, new, path=None):
        """Merge a parameter with another parameter.

        Iterate over keys in new. Call _merge_dict, _extend_list, or
        _update_scalar depending on type. Pass along whether this is an
        initialization merge.

        Args:
            cur (dict): Current dictionary
            new (dict): Dictionary to be merged
            path (string): Merging path from recursion
            initmerge (bool): True if called as part of entity init, defaults
                to False

        Returns:
            dict: a merged dictionary

        """


        if cur is None:
            return new
        elif isinstance(new, dict) and isinstance(cur, dict):
            return self._merge_dict(cur, new, path)
        else:
            return self._update_value(cur, new, path)

    def merge(self, other):
        """Merge function (public edition).

        Call _merge_recurse on self with either another Parameter object or a
        dict (for initialization). Set initmerge if it's a dict.

        Args:
            other (dict or Parameter): Thing to merge with self._base

        Returns:
            None: Nothing

        """

        self._unrendered = None
        if isinstance(other, dict):
            wrapped = self._wrap_dict(other)
        elif isinstance(other, self.__class__):
            wrapped = self._wrap_dict(other._base)
        else:
            raise TypeError('Cannot merge %s objects into %s' % (type(other),
                            self.__class__.__name__))
        self._base = self._merge_recurse(self._base, wrapped, DictPath(self._delimiter))

    def _render_simple_container(self, container, key, value, path):
            if isinstance(value, ValueList):
                if value.is_complex():
                    self._unrendered[path.new_subpath(key)] = True
                    if value.has_inv_query():
                        self._has_inv_query = True
                    return
                else:
                    value = value.merge(self._options)
            if isinstance(value, Value) and value.is_container():
                value = value.contents()
            if isinstance(value, dict):
                self._render_simple_dict(value, path.new_subpath(key))
                container[key] = value
            elif isinstance(value, list):
                self._render_simple_list(value, path.new_subpath(key))
                container[key] = value
            elif isinstance(value, Value):
                if value.is_complex():
                    self._unrendered[path.new_subpath(key)] = True
                    if value.has_inv_query():
                        self._has_inv_query = True
                else:
                    container[key] = value.render(None, None, self._options)

    def _render_simple_dict(self, dictionary, path):
        for key, value in dictionary.iteritems():
            self._render_simple_container(dictionary, key, value, path)

    def _render_simple_list(self, item_list, path):
        for n, value in enumerate(item_list):
            self._render_simple_container(item_list, n, value, path)

    def interpolate(self, inventory=None):
        self._initialise_interpolate()
        while len(self._unrendered) > 0:
            # we could use a view here, but this is simple enough:
            # _interpolate_inner removes references from the refs hash after
            # processing them, so we cannot just iterate the dict
            path, v = self._unrendered.iteritems().next()
            self._interpolate_inner(path, inventory)

    def initialise_interpolation(self):
        self._unrendered = None
        self._initialise_interpolate()

    def _initialise_interpolate(self):
        if self._unrendered is None:
            self._unrendered = {}
            self._has_inv_query = False
            self._render_simple_dict(self._base, DictPath(self._delimiter))

    def _interpolate_inner(self, path, inventory):
        value = path.get_value(self._base)
        if not isinstance(value, (Value, ValueList)):
            # references to lists and dicts are only deepcopied when merged
            # together so it's possible a value with references in a referenced
            # list or dict has already been visited by _interpolate_inner
            del self._unrendered[path]
            return
        self._unrendered[path] = False
        self._interpolate_references(path, value, inventory)
        new = self._interpolate_render_value(path, value, inventory)
        path.set_value(self._base, new)
        del self._unrendered[path]

    def _interpolate_render_value(self, path, value, inventory):
        try:
            new = value.render(self._base, inventory, self._options)
        except UndefinedVariableError as e:
            raise UndefinedVariableError(e.var, path)

        if isinstance(new, dict):
            self._render_simple_dict(new, path)
        elif isinstance(new, list):
            self._render_simple_list(new, path)
        return new

    def _interpolate_references(self, path, value, inventory):
        all_refs = False
        while not all_refs:
            for ref in value.get_references():
                path_from_ref = DictPath(self._delimiter, ref)

                if path_from_ref in self._unrendered:
                    if self._unrendered[path_from_ref] is False:
                        # every call to _interpolate_inner replaces the value of
                        # self._unrendered[path] with False
                        # Therefore, if we encounter False instead of True,
                        # it means that we have already processed it and are now
                        # faced with a cyclical reference.
                        raise InfiniteRecursionError(path, ref)
                    else:
                        self._interpolate_inner(path_from_ref, inventory)
                else:
                    # ensure ancestor keys are already dereferenced
                    ancestor = DictPath(self._delimiter)
                    for k in path_from_ref.key_parts():
                        ancestor = ancestor.new_subpath(k)
                        if ancestor in self._unrendered:
                            self._interpolate_inner(ancestor, inventory)
            if value.allRefs():
                all_refs = True
            else:
                # not all references in the value could be calculated previously so
                # try recalculating references with current context and recursively
                # call _interpolate_inner if the number of references has increased
                # Otherwise raise an error
                old = len(value.get_references())
                value.assembleRefs(self._base)
                if old == len(value.get_references()):
                    raise InterpolationError('Bad reference count, path:' + repr(path))
