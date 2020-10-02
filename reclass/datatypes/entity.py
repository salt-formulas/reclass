#
# -*- coding: utf-8 -*-
#
# This file is part of reclass (http://github.com/madduck/reclass)
#
# Copyright © 2007–14 martin f. krafft <madduck@madduck.net>
# Released under the terms of the Artistic Licence 2.0
#
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

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
    def __init__(self, settings, classes=None, applications=None,
                 parameters=None, exports=None, uri=None, name=None,
                 pathname=None, environment=None):
        self._uri = '' if uri is None else uri
        self._name = '' if name is None else name
        self._pathname = '' if pathname is None else pathname
        self._classes = self._set_field(classes, Classes)
        self._applications = self._set_field(applications, Applications)
        pars = [None, settings, uri]
        self._parameters = self._set_field(parameters, Parameters, pars)
        self._exports = self._set_field(exports, Exports, pars)
        self._environment = environment

    name = property(lambda s: s._name)
    uri = property(lambda s: s._uri)
    pathname = property(lambda s: s._pathname)
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

    def _set_field(self, received_value, expected_type, parameters=None):
        if parameters is None:
            parameters = []
        if received_value is None:
            return expected_type(*parameters)
        if not isinstance(received_value, expected_type):
            raise TypeError('Entity.%s cannot be set to instance of type %s' %
                            (type(expected_type), type(received_value)))
        return received_value

    def merge(self, other):
        self._classes.merge_unique(other.classes)
        self._applications.merge_unique(other.applications)
        self._parameters.merge(other.parameters)
        self._exports.merge(other.exports)
        self._name = other.name
        self._uri = other.uri
        self._parameters._uri = other.uri
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
                and self._applications == other.applications \
                and self._classes == other.classes \
                and self._parameters == other.parameters \
                and self._exports == other.exports \
                and self._name == other.name \
                and self._uri == other.uri

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return "%s(%r, %r, %r, %r, uri=%r, name=%r, pathname=%r, environment=%r)" % (
                   self.__class__.__name__, self.classes, self.applications,
                   self.parameters, self.exports, self.uri, self.name,
                   self.pathname, self.environment)

    def as_dict(self):
        return {'classes': self._classes.as_list(),
                'applications': self._applications.as_list(),
                'parameters': self._parameters.as_dict(),
                'exports': self._exports.as_dict(),
                'environment': self._environment
               }
