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

from reclass import datatypes
import yaml
import os
from reclass.errors import NotFoundError

_SafeLoader = yaml.CSafeLoader if yaml.__with_libyaml__ else yaml.SafeLoader

class YamlData(object):

    @classmethod
    def from_file(cls, path):
        ''' Initialise yaml data from a local file '''
        abs_path = os.path.abspath(path)
        if not os.path.isfile(abs_path):
            raise NotFoundError('No such file: %s' % abs_path)
        if not os.access(abs_path, os.R_OK):
            raise NotFoundError('Cannot open: %s' % abs_path)
        y = cls('yaml_fs://{0}'.format(abs_path))
        with open(abs_path) as fp:
            data = yaml.load(fp, Loader=_SafeLoader)
            if data is not None:
                y._data = data
        return y

    @classmethod
    def from_string(cls, string, uri):
        ''' Initialise yaml data from a string '''
        y = cls(uri)
        data = yaml.load(string, Loader=_SafeLoader)
        if data is not None:
            y._data = data
        return y

    def __init__(self, uri):
        self._uri = uri
        self._data = dict()

    uri = property(lambda self: self._uri)

    def get_data(self):
        return self._data

    def set_absolute_names(self, name, names):
        new_names = []
        for n in names:
            if n[0] == '.':
                dots = self.count_dots(n)
                levels_up = (dots * (-1))
                parent = '.'.join(name.split('.')[0:levels_up])
                if parent == '':
                    n = n[dots:]
                else:
                    n = parent + n[dots - 1:]
            new_names.append(n)
        return new_names

    def yield_dots(self, value):
        try:
            idx = value.index('.')
        except ValueError:
            return
        if idx == 0:
            yield '.'
            for dot in self.yield_dots(value[1:]):
                yield dot

    def count_dots(self, value):
        return len(list(self.yield_dots(value)))

    def get_entity(self, name, pathname, settings):
        classes = self._data.get('classes')
        if classes is None:
            classes = []
        classes = self.set_absolute_names(name, classes)
        classes = datatypes.Classes(classes)

        applications = self._data.get('applications')
        if applications is None:
            applications = []
        applications = datatypes.Applications(applications)

        parameters = self._data.get('parameters')
        if parameters is None:
            parameters = {}
        parameters = datatypes.Parameters(parameters, settings, self._uri)

        exports = self._data.get('exports')
        if exports is None:
            exports = {}
        exports = datatypes.Exports(exports, settings, self._uri)

        env = self._data.get('environment', None)

        return datatypes.Entity(settings, classes=classes, applications=applications, parameters=parameters,
                                exports=exports, name=name, pathname=pathname, environment=env, uri=self.uri)

    def __str__(self):
        return '<{0} {1}, {2}>'.format(self.__class__.__name__, self._uri,
                                       self._data)

    def __repr__(self):
        return '<{0} {1}, {2}>'.format(self.__class__.__name__, self._uri,
                                       self._data.keys())
