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


class _Constant(object):

    def __init__(self, displayname):
        self._repr = displayname

    __str__ = __repr__ = lambda self: self._repr

MODE_NODEINFO = _Constant('NODEINFO')
MODE_NODEAPPS = _Constant('NODEAPPS')
MODE_INVENTORY = _Constant('INVENTORY')
