#
# -*- coding: utf-8 -*-
#
# This file is part of reclass (http://github.com/madduck/reclass)
#
# Copyright © 2007–14 martin f. krafft <madduck@madduck.net>
# Released under the terms of the Artistic Licence 2.0
#
from .classes import Classes
from .applications import Applications
from .exports import Exports
from .parameters import Parameters

class Entity(object):
    '''
    A collection of Classes, Parameters, and Applications, mainly as a wrapper
    for merging. The name and uri of an Entity will be updated to the name and
    uri of the Entity that is being merged.
    '''
    def __init__(self, settings, classes=None, applications=None, parameters=None,
                 exports=None, uri=None, name=None, environment=None):
        self._uri = uri or ''
        self._name = name or ''
        if classes is None: classes = Classes()
        self._set_classes(classes)
        if applications is None: applications = Applications()
        self._set_applications(applications)
        if parameters is None: parameters = Parameters(None, settings, uri)
        if exports is None: exports = Exports(None, settings, uri)
        self._set_parameters(parameters)
        self._set_exports(exports)
        self._environment = environment

    name = property(lambda s: s._name)
    short_name = property(lambda s: s._short_name)
    uri = property(lambda s: s._uri)
    classes = property(lambda s: s._classes)
    applications = property(lambda s: s._applications)
    parameters = property(lambda s: s._parameters)
    exports = property(lambda s: s._exports)

    @property
    def environment(self):
        return self._environment

    @environment.setter
    def environment(self, value):
        self._environment = value

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
        if not isinstance(exports, Exports):
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
        if other.environment != None:
            self._environment = other.environment

    def merge_parameters(self, params):
        self._parameters.merge(params)

    def interpolate(self, inventory):
        self._parameters.interpolate(inventory)
        self.interpolate_exports()

    def initialise_interpolation(self):
        self._parameters.initialise_interpolation()
        self._exports.initialise_interpolation()

    def interpolate_exports(self):
        self.initialise_interpolation()
        self._exports.interpolate_from_external(self._parameters)

    def interpolate_single_export(self, references):
        self._exports.interpolate_single_from_external(self._parameters, references)

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
        return "%s(%r, %r, %r, %r, uri=%r, name=%r, environment=%r)" % (
                   self.__class__.__name__, self.classes, self.applications,
                   self.parameters, self.exports, self.uri, self.name,
                   self.environment)

    def as_dict(self):
        return {'classes': self._classes.as_list(),
                'applications': self._applications.as_list(),
                'parameters': self._parameters.as_dict(),
                'exports': self._exports.as_dict(),
                'environment': self._environment
               }
