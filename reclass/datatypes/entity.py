#
# -*- coding: utf-8 -*-
#
# This file is part of reclass (http://github.com/madduck/reclass)
#
# Copyright © 2007–14 martin f. krafft <madduck@madduck.net>
# Released under the terms of the Artistic Licence 2.0
#
from classes import Classes
from applications import Applications
from parameters import Parameters

class Entity(object):
    '''
    A collection of Classes, Parameters, and Applications, mainly as a wrapper
    for merging. The name and uri of an Entity will be updated to the name and
    uri of the Entity that is being merged.
    '''
    def __init__(self, classes=None, applications=None, parameters=None,
                 exports=None, uri=None, name=None, environment=None):
        if classes is None: classes = Classes()
        self._set_classes(classes)
        if applications is None: applications = Applications()
        self._set_applications(applications)
        if parameters is None: parameters = Parameters()
        if exports is None: exports = Parameters()
        self._set_parameters(parameters)
        self._set_exports(exports)
        self._uri = uri or ''
        self._name = name or ''
        self._environment = environment or ''

    name = property(lambda s: s._name)
    short_name = property(lambda s: s._short_name)
    uri = property(lambda s: s._uri)
    environment = property(lambda s: s._environment)
    classes = property(lambda s: s._classes)
    applications = property(lambda s: s._applications)
    parameters = property(lambda s: s._parameters)
    exports = property(lambda s: s._exports)

    def _set_classes(self, classes):
        if not isinstance(classes, Classes):
            raise TypeError('Entity.classes cannot be set to '\
                            'instance of type %s' % type(classes))
        self._classes = classes

    def _set_applications(self, applications):
        if not isinstance(applications, Applications):
            raise TypeError('Entity.applications cannot be set to '\
                            'instance of type %s' % type(applications))
        self._applications = applications

    def _set_parameters(self, parameters):
        if not isinstance(parameters, Parameters):
            raise TypeError('Entity.parameters cannot be set to '\
                            'instance of type %s' % type(parameters))
        self._parameters = parameters

    def _set_exports(self, exports):
        if not isinstance(exports, Parameters):
            raise TypeError('Entity.exports cannot be set to '\
                            'instance of type %s' % type(exports))
        self._exports = exports

    def merge(self, other):
        self._classes.merge_unique(other._classes)
        self._applications.merge_unique(other._applications)
        self._parameters.merge(other._parameters)
        self._exports.merge(other._exports)
        self._name = other.name
        self._uri = other.uri
        self._environment = other.environment

    def merge_parameters(self, params):
        self._parameters.merge(params)

    def interpolate(self, nodename, exports):
        exports.overwrite({ nodename: self._exports._base })
        self._parameters.interpolate(exports=exports._base)
        self._exports.interpolate_from_external(self._parameters)
        exports.interpolate_from_external(self._parameters)

    def __eq__(self, other):
        return isinstance(other, type(self)) \
                and self._applications == other._applications \
                and self._classes == other._classes \
                and self._parameters == other._parameters \
                and self._exports == other._exports \
                and self._name == other._name \
                and self._uri == other._uri

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return "%s(%r, %r, %r, %r, uri=%r, name=%r)" % (self.__class__.__name__,
                                                    self.classes,
                                                    self.applications,
                                                    self.parameters,
                                                    self.exports,
                                                    self.uri,
                                                    self.name)

    def as_dict(self):
        return {'classes': self._classes.as_list(),
                'applications': self._applications.as_list(),
                'parameters': self._parameters.as_dict(),
                'exports': self._exports.as_dict(),
                'environment': self._environment
               }
