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
from reclass.utils.mergeoptions import MergeOptions
from reclass.utils.dictpath import DictPath
from reclass.utils.value import Value
from reclass.utils.values import Values
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

    def __init__(self, mapping=None, delimiter=None):
        if delimiter is None:
            delimiter = Parameters.DEFAULT_PATH_DELIMITER
        self._delimiter = delimiter
        self._base = {}
        self._unrendered = {}
        self._escapes_handled = {}
        if mapping is not None:
            # we initialise by merging, otherwise the list of references might
            # not be updated
            self.merge(mapping, initmerge=True)

    delimiter = property(lambda self: self._delimiter)

    def __len__(self):
        return len(self._base)

    def __repr__(self):
        return '%s(%r, %r)' % (self.__class__.__name__, self._base,
                               self.delimiter)

    def __eq__(self, other):
        return isinstance(other, type(self)) \
                and self._base == other._base \
                and self._delimiter == other._delimiter

    def __ne__(self, other):
        return not self.__eq__(other)

    def as_dict(self):
        return self._base.copy()

    def _itemise_list(self, item_list):
        for n, value in enumerate(item_list):
            if isinstance(value, dict):
                self._itemise_dict(value)
            elif isinstance(value, list):
                self._itemise_list(value)
            elif not isinstance(value, (Value, Values)):
                item_list[n] = Value(value, self._delimiter)

    def _itemise_dict(self, dictionary):
        for key, value in dictionary.iteritems():
            if isinstance(value, dict):
                self._itemise_dict(value)
            elif isinstance(value, list):
                self._itemise_list(value)
                dictionary[key] = Value(value, self._delimiter)
            elif not isinstance(value, (Value, Values)):
                dictionary[key] = Value(value, self._delimiter)

    def _update_value(self, cur, new, path):
        if cur is None:
            return new

        values = cur
        if isinstance(cur, (dict, list)):
            values = Values(Value(cur))
        elif isinstance(cur, Value):
            values = Values(cur)

        if isinstance(new, (dict, list)):
           new = Value(new)

        if isinstance(new, Value):
            values.append(new)
        elif isinstance(new, Values):
            values.extend(new)
        else:
            raise TypeError('Can not merge %r into %r' % (new, cur))

        return values

    def _merge_dict(self, cur, new, path, initmerge):
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

        if isinstance(cur, dict):
            ret = cur
        else:
            # nothing sensible to do
            raise TypeError('Cannot merge dict into {0} '
                            'objects'.format(type(cur)))

        if self.delimiter is None:
            # a delimiter of None indicates that there is no value
            # processing to be done, and since there is no current
            # value, we do not need to walk the new dictionary:
            ret.update(new)
            return ret

        ovrprfx = Parameters.DICT_KEY_OVERRIDE_PREFIX

        for key, newvalue in new.iteritems():
            if key.startswith(ovrprfx) and not initmerge:
                ret[key.lstrip(ovrprfx)] = newvalue
            else:
                ret[key] = self._merge_recurse(ret.get(key), newvalue,
                                            path.new_subpath(key), initmerge)
        return ret

    def _merge_recurse(self, cur, new, path=None, initmerge=False):
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


        if isinstance(new, dict) and (cur is None or isinstance(cur, (dict))):
            if cur is None:
                cur = {}
            return self._merge_dict(cur, new, path, initmerge)

        else:
            return self._update_value(cur, new, path)

    def merge(self, other, initmerge=False):
        """Merge function (public edition).

        Call _merge_recurse on self with either another Parameter object or a
        dict (for initialization). Set initmerge if it's a dict.

        Args:
            other (dict or Parameter): Thing to merge with self._base

        Returns:
            None: Nothing

        """

        if isinstance(other, dict):
            itemised_other = copy.deepcopy(other)
            self._itemise_dict(itemised_other)
            self._base = self._merge_recurse(self._base, itemised_other,
                                             DictPath(self.delimiter), initmerge)

        elif isinstance(other, self.__class__):
            self._base = self._merge_recurse(self._base, other._base,
                                             DictPath(self.delimiter), initmerge)

        else:
            raise TypeError('Cannot merge %s objects into %s' % (type(other),
                            self.__class__.__name__))

    def has_unresolved_refs(self):
        return len(self._unrendered) > 0

    def resolve_simple(self, options=None):
        if options is None:
            options = MergeOptions()
        self._resolve_simple_recurse_dict(self._base, DictPath(self.delimiter), options)

    def _resolve_simple_recurse_dict(self, dictionary, path, options):
        for key, value in dictionary.iteritems():
            if isinstance(value, Values):
                if value.has_references():
                    self._unrendered[path.new_subpath(key)] = True
                    continue
                else:
                    value = value.merge(options)
            if isinstance(value, Value) and value.is_container():
                value = value.contents()

            if isinstance(value, dict):
                self._resolve_simple_recurse_dict(value, path.new_subpath(key), options)
                dictionary[key] = value
            elif isinstance(value, list):
                self._resolve_simple_recurse_list(value, path.new_subpath(key), options)
                dictionary[key] = value
            elif isinstance(value, Value):
                if value.has_references():
                    self._unrendered[path.new_subpath(key)] = True
                else:
                    dictionary[key] = value.render({}, options)

    def _resolve_simple_recurse_list(self, item_list, path, options):
        for n, value in enumerate(item_list):
            if isinstance(value, Values):
                if value.has_references():
                    self._unrendered[path.new_subpath(n)] = True
                    continue
                else:
                    value = value.merge(options)
            if isinstance(value, Value) and value.is_container():
                value = value.contents()

            if isinstance(value, dict):
                self._resolve_simple_recurse_dict(value, path.new_subpath(n), options)
                item_list[n] = value
            elif isinstance(value, list):
                self._resolve_simple_recurse_list(value, path.new_subpath(n), options)
                item_list[n] = value
            elif isinstance(value, Value):
                if value.has_references():
                    self._unrendered[path.new_subpath(n)] = True
                else:
                    item_list[n] = value.render({}, options)

    def interpolate(self, options=None):
        if options is None:
            options = MergeOptions()
        self._unrendered = {}
        self.resolve_simple(options)
        while self.has_unresolved_refs():
            # we could use a view here, but this is simple enough:
            # _interpolate_inner removes references from the refs hash after
            # processing them, so we cannot just iterate the dict
            path, value = self._unrendered.iteritems().next()
            self._interpolate_inner(path, path.get_value(self._base), options)

    def _interpolate_inner(self, path, value, options):
        self._unrendered[path] = False  # mark as seen
        for ref in value.get_references():
            path_from_ref = DictPath(self.delimiter, ref)

            if path_from_ref in self._unrendered:
                if self._unrendered[path_from_ref] is False:
                    # every call to _interpolate_inner replaces the value of
                    # self._unrendered[path] with False
                    # Therefore, if we encounter False instead of True,
                    # it means that we have already processed it and are now
                    # faced with a cyclical reference.
                    raise InfiniteRecursionError(path, ref)
                else:
                    value_inner = path_from_ref.get_value(self._base)
                    self._interpolate_inner(path_from_ref, value_inner, options)

        if value.allRefs():
            # all references have been deferenced so render value
            try:
                new = value.render(self._base, options)
                if isinstance(new, dict):
                    self._resolve_simple_recurse_dict(new, path, options)
                    path.set_value(self._base, copy.deepcopy(new))
                elif isinstance(new, list):
                    self._resolve_simple_recurse_list(new, path, options)
                    path.set_value(self._base, copy.deepcopy(new))
                else:
                    path.set_value(self._base, new)

                # remove the reference from the unrendered list
                del self._unrendered[path]
            except UndefinedVariableError as e:
                raise UndefinedVariableError(e.var, path)
        else:
            # not all references in the value could be calculated previously so
            # try recalculating references with current context and recursively
            # call _interpolate_inner if the number of references has increased
            # Otherwise raise an error
            old = len(value.get_references())
            value.assembleRefs(self._base)
            if old != len(value.get_references()):
                self._interpolate_inner(path, value, options)
            else:
                raise InterpolationError('Bad reference count, path:' + repr(path))
