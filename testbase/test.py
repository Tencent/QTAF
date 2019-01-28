# -*- coding: utf-8 -*-
#
# Tencent is pleased to support the open source community by making QTA available.
# Copyright (C) 2016THL A29 Limited, a Tencent company. All rights reserved.
# Licensed under the BSD 3-Clause License (the "License"); you may not use this
# file except in compliance with the License. You may obtain a copy of the License at
#
# https://opensource.org/licenses/BSD-3-Clause
#
# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" basis, WITHOUT WARRANTIES OR CONDITIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.
#
"""a module for unittest
"""
import os
import threading

from testbase.conf import settings


class _NotExistedItem(object):
    pass


class modify_settings(object):
    """temporarily modify settings
    """

    def __init__(self, **kwargs):
        self.new_conf = kwargs
        self.old_conf = {}

    def __enter__(self):
        settings._Settings__ensure_loaded()  # ensure loaded
        settings._Settings__sealed = False
        for key in self.new_conf:
            self.old_conf[key] = getattr(settings, key, _NotExistedItem())
            if isinstance(self.old_conf[key], _NotExistedItem):
                settings._Settings__keys.add(key)
            setattr(settings, key, self.new_conf[key])

    def __exit__(self, *args):
        for key in self.old_conf:
            old_value = self.old_conf[key]
            if isinstance(old_value, _NotExistedItem):
                delattr(settings, key)
                settings._Settings__keys.remove(key)
            else:
                setattr(settings, key, old_value)
        settings._Settings__sealed = True


class modify_environ(object):
    """temporarily modify envrion
    """

    def __init__(self, **kwargs):
        self.new_conf = kwargs
        self.old_conf = {}

    def __enter__(self):
        for key in self.new_conf:
            self.old_conf[key] = os.environ.get(key, _NotExistedItem())
            os.environ[key] = self.new_conf[key]

    def __exit__(self, *args):
        for key in self.old_conf:
            old_value = self.old_conf[key]
            if isinstance(old_value, _NotExistedItem):
                del os.environ[key]
            else:
                os.environ[key] = old_value


class modify_attributes(object):
    """temporarily modify attributes
    """
    _lock = threading.Lock()

    def __init__(self, target, key_values):
        self._target = target
        self._old_values = {}
        self._new_values = key_values
        for key in key_values.keys():
            self._old_values[key] = getattr(target, key)

    def __enter__(self):
        self._lock.acquire()
        for key in self._new_values:
            setattr(self._target, key, self._new_values[key])

    def __exit__(self, *args):
        try:
            for key in self._old_values:
                setattr(self._target, key, self._old_values[key])
        finally:
            self._lock.release()
