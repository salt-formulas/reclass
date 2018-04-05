#
# -*- coding: utf-8 -*-
#
# This file is part of reclass (http://github.com/madduck/reclass)
#
# Copyright © 2007–14 martin f. krafft <madduck@madduck.net>
# Released under the terms of the Artistic Licence 2.0
#
import importlib


class StorageBackendLoader(object):

    def __init__(self, storage_name):
        self._name = 'reclass.storage.' + storage_name
        try:
            self._module = importlib.import_module(self._name)
        except ImportError:
            raise NotImplementedError

    def load(self, klassname='ExternalNodeStorage'):
        klass = getattr(self._module, klassname, None)
        if klass is None:
            raise AttributeError('Storage backend class {0} does not export '
                                 '"{1}"'.format(self._name, klassname))
        return klass

    def path_mangler(self, name='path_mangler'):
        function = getattr(self._module, name, None)
        if function is None:
            raise AttributeError('Storage backend class {0} does not export "{1}"'.format(self._name, name))
        return function
