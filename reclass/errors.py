#
# -*- coding: utf-8 -*-
#
# This file is part of reclass (http://github.com/madduck/reclass)
#
# Copyright © 2007–14 martin f. krafft <madduck@madduck.net>
# Released under the terms of the Artistic Licence 2.0
#

import posix, sys
import traceback

from reclass.defaults import REFERENCE_SENTINELS, EXPORT_SENTINELS

class ReclassException(Exception):

    def __init__(self, rc=posix.EX_SOFTWARE, msg=None):
        super(ReclassException, self).__init__()
        self._rc = rc
        self._msg = msg
        self._previous_traceback = traceback.format_exc()
        self._full_traceback = False

    message = property(lambda self: self._get_message())
    rc = property(lambda self: self._rc)

    def __str__(self):
        return self.message + '\n' + super(ReclassException, self).__str__()

    def _get_message(self):
        if self._msg:
            return self._msg
        else:
            return 'No error message provided.'

    def exit_with_message(self, out=sys.stderr):
        if self._full_traceback:
            t, v, tb = sys.exc_info()
            print >>out, 'Full Traceback:'
            for l in traceback.format_tb(tb):
                print >>out, l,
            print >>out
        if self._previous_traceback:
            print >>out, self._previous_traceback
        print >>out, self.message
        print >>out
        sys.exit(self.rc)


class PermissionError(ReclassException):

    def __init__(self, msg, rc=posix.EX_NOPERM):
        super(PermissionError, self).__init__(rc=rc, msg=msg)


class InvocationError(ReclassException):

    def __init__(self, msg, rc=posix.EX_USAGE):
        super(InvocationError, self).__init__(rc=rc, msg=msg)


class ConfigError(ReclassException):

    def __init__(self, msg, rc=posix.EX_CONFIG):
        super(ConfigError, self).__init__(rc=rc, msg=msg)


class DuplicateUriError(ConfigError):

    def __init__(self, nodes_uri, classes_uri):
        super(DuplicateUriError, self).__init__(msg=None)
        self._nodes_uri = nodes_uri
        self._classes_uri = classes_uri

    def _get_message(self):
        return "The inventory URIs must not be the same " \
               "for nodes and classes: {0}".format(self._nodes_uri)


class UriOverlapError(ConfigError):

    def __init__(self, nodes_uri, classes_uri):
        super(UriOverlapError, self).__init__(msg=None)
        self._nodes_uri = nodes_uri
        self._classes_uri = classes_uri

    def _get_message(self):
        msg = "The URIs for the nodes and classes inventories must not " \
              "overlap, but {0} and {1} do."
        return msg.format(self._nodes_uri, self._classes_uri)


class NotFoundError(ReclassException):

    def __init__(self, msg, rc=posix.EX_IOERR):
        super(NotFoundError, self).__init__(rc=rc, msg=msg)


class NodeNotFound(NotFoundError):

    def __init__(self, storage, nodename, uri):
        super(NodeNotFound, self).__init__(msg=None)
        self._storage = storage
        self._name = nodename
        self._uri = uri

    def _get_message(self):
        msg = "Node '{0}' not found under {1}://{2}"
        return msg.format(self._name, self._storage, self._uri)


class ClassNotFound(NotFoundError):

    def __init__(self, storage, classname, uri, nodename=None):
        super(ClassNotFound, self).__init__(msg=None)
        self._storage = storage
        self._name = classname
        self._uri = uri
        self._nodename = nodename

    def _get_message(self):
        if self._nodename:
            msg = "Class '{0}' (in ancestry of node '{1}') not found " \
                  "under {2}://{3}"
        else:
            msg = "Class '{0}' not found under {2}://{3}"
        return msg.format(self._name, self._nodename, self._storage, self._uri)

    def set_nodename(self, nodename):
        self._nodename = nodename


class InterpolationError(ReclassException):

    def __init__(self, msg, rc=posix.EX_DATAERR, nodename=''):
        super(InterpolationError, self).__init__(rc=rc, msg=msg)
        self.nodename = nodename
        self.uri = None
        self.context = None

    def _get_message(self):
        msg = '=> {0}\n'.format(self.nodename)
        msg += self._render_error_message(self._get_error_message(), 1)
        msg = msg[:-1]
        return msg

    def _render_error_message(self, message_list, indent):
        msg = ''
        for l in message_list:
            if isinstance(l, list):
                msg += self._render_error_message(l, indent + 1)
            else:
                msg += (' ' * indent * 3) + l + '\n'
        return msg

    def _add_context_and_uri(self):
        msg = ''
        if self.context:
            msg += ', at %s' % self.context
        if self.uri:
            msg += ', in %s' % self.uri
        return msg


class ResolveError(InterpolationError):

    def __init__(self, reference, uri=None, context=None):
        super(ResolveError, self).__init__(msg=None)
        self.reference = reference

    def _get_error_message(self):
        msg = 'Cannot resolve {0}'.format(self.reference.join(REFERENCE_SENTINELS)) + self._add_context_and_uri()
        return [ msg ]


class InvQueryError(InterpolationError):

    def __init__(self, query, resolveError, uri=None, context = None):
        super(InvQueryError, self).__init__(msg=None)
        self.query = query
        self.resolveError = resolveError
        self._traceback = self.resolveError._traceback

    def _get_error_message(self):
        msg1 = 'Failed inv query {0}'.format(self.query.join(EXPORT_SENTINELS)) + self._add_context_and_uri()
        msg2 = [ '--> {0}'.format(self.resolveError.nodename) ]
        msg2.extend(self.resolveError._get_error_message())
        return [ msg1, msg2 ]


class ParseError(InterpolationError):

    def __init__(self, msg, line, col, lineno, rc=posix.EX_DATAERR):
        super(ParseError, self).__init__(rc=rc, msg=None)
        self._err = msg
        self._line = line
        self._col = col
        self._lineno = lineno

    def _get_error_message(self):
        msg = [ 'Parse error: {0}'.format(self._line.join(EXPORT_SENTINELS)) + self._add_context_and_uri() ]
        msg.append('{0} at char {1}'.format(self._err, self._col - 1))


class InfiniteRecursionError(InterpolationError):

    def __init__(self, path, ref):
        super(InfiniteRecursionError, self).__init__(msg=None)
        self._path = path
        self._ref = ref.join(REFERENCE_SENTINELS)

    def _get_error_message(self):
        msg = "Infinite recursion while resolving {0} at {1}"
        return [ msg.format(self._ref, self._path) ]


class BadReferencesError(InterpolationError):

    def __init__(self, refs, path):
        super(BadReferencesError, self).__init__(msg=None)
        self._path = path
        self._refs = [ r.join(REFERENCE_SENTINELS) for r in refs ]

    def _get_error_message(self):
        msg = 'Bad references: {0} for path: {1}'
        return [ msg.format(", ".join(self._refs), self._path) ]


class ExpressionError(InterpolationError):

    def __init__(self, msg, rc=posix.EX_DATAERR):
        super(ExpressionError, self).__init__(rc=rc, msg=None)
        self._error_msg = msg

    def _get_error_message(self):
        msg = [ 'Expression error: {0}'.format(self._error_msg) + self._add_context_and_uri() ]
        return msg


class MappingError(ReclassException):

    def __init__(self, msg, rc=posix.EX_DATAERR):
        super(MappingError, self).__init__(rc=rc, msg=msg)


class MappingFormatError(MappingError):

    def __init__(self, msg):
        super(MappingFormatError, self).__init__(msg)


class NameError(ReclassException):

    def __init__(self, msg, rc=posix.EX_DATAERR):
        super(NameError, self).__init__(rc=rc, msg=msg)


class InvalidClassnameError(NameError):

    def __init__(self, invalid_character, classname):
        super(InvalidClassnameError, self).__init__(msg=None)
        self._char = invalid_character
        self._classname = classname

    def _get_message(self):
        msg = "Invalid character '{0}' in class name '{1}'."
        return msg.format(self._char, self._classname)


class DuplicateNodeNameError(NameError):

    def __init__(self, storage, name, uri1, uri2):
        super(DuplicateNodeNameError, self).__init__(msg=None)
        self._storage = storage
        self._name = name
        self._uris = (uri1, uri2)

    def _get_message(self):
        msg = "{0}: Definition of node '{1}' in '{2}' collides with " \
              "definition in '{3}'. Nodes can only be defined once " \
              "per inventory."
        return msg.format(self._storage, self._name, self._uris[1], self._uris[0])
