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

    def __init__(self, mapping=None, delimiter=None):
        if delimiter is None:
            delimiter = Parameters.DEFAULT_PATH_DELIMITER
        self._delimiter = delimiter
        self._base = {}
        self._unrendered = None
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

    def _wrap_container(self, container, key, value):
        if isinstance(value, dict):
            self._wrap_dict(value)
        elif isinstance(value, list):
            self._wrap_list(value)
        elif not isinstance(value, (Value, ValueList)):
            container[key] = Value(value, self._delimiter)

    def _wrap_list(self, item_list):
        for n, value in enumerate(item_list):
            self._wrap_container(item_list, n, value)

    def _wrap_dict(self, dictionary):
        for key, value in dictionary.iteritems():
            self._wrap_container(dictionary, key, value)

    def _update_value(self, cur, new, path):
        if cur is None:
            return new

        values = cur
        if isinstance(cur, (dict, list)):
            values = ValueList(Value(cur))
        elif isinstance(cur, Value):
            values = ValueList(cur)

        if isinstance(new, (dict, list)):
           new = Value(new)

        if isinstance(new, Value):
            values.append(new)
        elif isinstance(new, ValueList):
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

        self._unrendered = None
        if isinstance(other, dict):
            wrapped = copy.deepcopy(other)
            self._wrap_dict(wrapped)
            self._base = self._merge_recurse(self._base, wrapped,
                                             DictPath(self.delimiter), initmerge)

        elif isinstance(other, self.__class__):
            self._base = self._merge_recurse(self._base, other._base,
                                             DictPath(self.delimiter), initmerge)

        else:
            raise TypeError('Cannot merge %s objects into %s' % (type(other),
                            self.__class__.__name__))

    def render_simple(self, options=None):
        if options is None:
            options = MergeOptions()
        self._unrendered = {}
        self._render_simple_dict(self._base, DictPath(self.delimiter), options)

    def _render_simple_container(self, container, key, value, path, options):
            if isinstance(value, ValueList):
                if value.is_complex():
                    self._unrendered[path.new_subpath(key)] = True
                    return
                else:
                    value = value.merge(options)
            if isinstance(value, Value) and value.is_container():
                value = value.contents()
            if isinstance(value, dict):
                self._render_simple_dict(value, path.new_subpath(key), options)
                container[key] = value
            elif isinstance(value, list):
                self._render_simple_list(value, path.new_subpath(key), options)
                container[key] = value
            elif isinstance(value, Value):
                if value.is_complex():
                    self._unrendered[path.new_subpath(key)] = True
                else:
                    container[key] = value.render(None, None, options)

    def _render_simple_dict(self, dictionary, path, options):
        for key, value in dictionary.iteritems():
            self._render_simple_container(dictionary, key, value, path, options)

    def _render_simple_list(self, item_list, path, options):
        for n, value in enumerate(item_list):
            self._render_simple_container(item_list, n, value, path, options)

    def _ensure_render_simple(self, options):
        if self._unrendered is None:
            self.render_simple(options)

    def interpolate_from_external(self, external, options=None):
        if self._unrendered is None:
            options = MergeOptions()
        self._ensure_render_simple(options)
        external._ensure_render_simple(options)
        while len(self._unrendered) > 0:
            path, v = self._unrendered.iteritems().next()
            value = path.get_value(self._base)
            external._interpolate_references(path, value, None, options)
            new = value.render(external._base, options)
            path.set_value(self._base, new)
            del self._unrendered[path]

    def interpolate(self, exports=None, options=None):
        if options is None:
            options = MergeOptions()
        self._ensure_render_simple(options)
        while len(self._unrendered) > 0:
            # we could use a view here, but this is simple enough:
            # _interpolate_inner removes references from the refs hash after
            # processing them, so we cannot just iterate the dict
            path, v = self._unrendered.iteritems().next()
            self._interpolate_inner(path, exports, options)

    def _interpolate_inner(self, path, exports, options):
        value = path.get_value(self._base)
        if not isinstance(value, (Value, ValueList)):
            # references to lists and dicts are only deepcopied when merged
            # together so it's possible a value with references in a referenced
            # list or dict has already been visited by _interpolate_inner
            del self._unrendered[path]
            return
        self._unrendered[path] = False
        self._interpolate_references(path, value, exports, options)
        new = self._interpolate_render_value(path, value, exports, options)
        path.set_value(self._base, new)
        del self._unrendered[path]

    def _interpolate_render_value(self, path, value, exports, options):
        try:
            new = value.render(self._base, exports, options)
        except UndefinedVariableError as e:
            raise UndefinedVariableError(e.var, path)

        if isinstance(new, dict):
            self._render_simple_dict(new, path, options)
        elif isinstance(new, list):
            self._render_simple_list(new, path, options)
        return new

    def _interpolate_references(self, path, value, exports, options):
        all_refs = False
        while not all_refs:
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
                        self._interpolate_inner(path_from_ref, exports, options)
                else:
                    # ensure ancestor keys are already dereferenced
                    ancestor = DictPath(self.delimiter)
                    for k in path_from_ref.key_parts():
                        ancestor = ancestor.new_subpath(k)
                        if ancestor in self._unrendered:
                            self._interpolate_inner(ancestor, exports, options)
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
