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
'''配置接口

一、配置格式
配置文件名默认为settings.py，可以通过环境变量指定用户配置文件的路径
qtaf相关配置的环境变量为：
QTAF_EXLIB_PATH: 指定exlib的路径，exlib下放置对应的qtaf、qt4s、installed_libs.txt等文件
QTAF_INSTALLED_LIBS: 指定已经安装的库的列表，以分号分隔，例如qt4s，用来代替不使用installed_libs.txt的场景
QTAF_SETTINGS_MODULE: 指定用户自定义的配置文件的路径，最后加载，会覆盖已经存在的配置

配置变量名必须符合pyton变量名规范，且统一使用大写，且不可以以"__"开头

如：
CONFIG_OPTION = True
DEBUG = True
RUNNER_THREAD_CNT = 5
BANNER = "hello"

二、使用示例：
from testbase.conf import settings
print(settings.CONFIG_OPTION)

注意 settings的值都是只读的，不可以修改，如果尝试修改会导致异常

三、配置优先级
配置存在2个优先级，当存在名字冲突时，使用高优先级的配置的值。优先级自低到高分别为：
1、QTAF配置                     固定为：test_proj/exlib/qtaf.egg/qtaf_settings.py
2、lib配置                      已经配置在test_proj/exlib/installed_libs.txt的包中的settings模块
3、用户自定义配置          固定为：test_proj/settings.py
'''

import imp
import os
import sys
import traceback

import qtaf_settings

from testbase import logger
from testbase.exlib import ExLibManager

_DEFAULT_SETTINSG_MODULE = "settings"


class _Settings(object):
    '''配置读取接口
    '''

    def __init__(self):
        self.__keys = set()
        self.__sealed = False
        self.__loaded = False

    def _load(self):
        '''加载配置
        :returns: Settings - 设置读取接口
        '''
        # get PROJECT_MODE from user settings
        default_mode = getattr(qtaf_settings, 'PROJECT_MODE', None)
        try:
            pre_settings = self._load_proj_settings_module("testbase.conf.pre_settings")
            mode = getattr(pre_settings, "PROJECT_MODE", default_mode)
        except ImportError as e:
            pre_settings = None
            if os.path.isfile(__file__):
                mode = "standard"
            else:
                mode = "standalone"

        if mode == "standard":  # library mode
            proj_root = getattr(pre_settings, "PROJECT_ROOT", os.getcwd())
            installed_apps = getattr(pre_settings, "INSTALLED_APPS", getattr(qtaf_settings, 'INSTALLED_APPS', []))

        else:  # egg mode
            proj_root = self._get_standalone_project_root(pre_settings)
            installed_apps = ExLibManager(proj_root).list_names()

        # load settings from qtaf
        self._load_setting_from_module(qtaf_settings)

        # load settings from installed apps
        for appname in installed_apps:
            modname = "%s.settings" % appname
            try:
                __import__(modname)
            except:
                stack = traceback.format_exc()
                logger.warn("[WARN]load library settings module \"%s\" failed:\n%s" % (modname, stack))
            else:
                self._load_setting_from_module(sys.modules[modname])

        # load settings from user settings
        try:
            proj_settings = self._load_proj_settings_module("testbase.conf.settings")
        except ImportError as e:
            if e.args[0] not in ["No module named settings", "No module named 'settings'"]:
                # project settings found and there was an error
                stack = traceback.format_exc()
                logger.warn("[WARN]load project settings failed:\n%s" % stack)
        else:
            self._load_setting_from_module(proj_settings)

        # trying to set project root automatically
        setattr(self, "PROJECT_ROOT", proj_root)
        setattr(self, "INSTALLED_APPS", installed_apps)

    def _load_proj_settings_module(self, import_name):
        '''加载项目配置文件
        '''
        user_settings = os.environ.get("QTAF_SETTINGS_MODULE", None)
        if user_settings:
            parts = user_settings.split('.')
            parts_temp = parts[:]
            dir_path = None
            while parts_temp:
                if dir_path:
                    fd, dir_path, desc = imp.find_module(parts_temp[0], [dir_path])
                else:
                    fd, dir_path, desc = imp.find_module(parts_temp[0])
                del parts_temp[0]
        else:
            fd, dir_path, desc = imp.find_module(_DEFAULT_SETTINSG_MODULE)
        return imp.load_module(import_name, fd, dir_path, desc)

    def _load_setting_from_module(self, module):
        '''从模块中加载设置
        '''
        for name in dir(module):
            if name.startswith('__'):
                continue
            if name.islower():
                continue
            self.__keys.add(name)
            setattr(self, name, getattr(module, name))

    def _get_standalone_project_root(self, pre_settings):
        '''获取独立模式下的项目的根目录
        '''
        proj_root = getattr(pre_settings, "PROJECT_ROOT", None)
        if proj_root:
            return proj_root
        if os.path.isfile(__file__):  # 没使用qtaf.egg包
            cwd = os.getcwd()
            # 使用外链或拷贝文件的方式
            dst_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
            if cwd.find(dst_path) >= 0:
                return os.path.abspath(dst_path)

            # eclipse调试使用工程引用的方式
            if 'PYTHONPATH' not in os.environ:
                return cwd
            py_paths = os.environ['PYTHONPATH']
            paths = py_paths.split(";")
            if len(paths) > 2:
                dst_path = paths[1]
            if cwd.find(dst_path) >= 0:
                return dst_path

            # 非预期的情况，返回当前工作目录
            return cwd
        else:  # 使用的egg包，qtaf.egg包在exlib目录中
            exlib_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
            proj_root = os.path.abspath(os.path.join(exlib_dir, '..'))
            return proj_root

    def get(self, name, *default_value):
        '''获取配置
        '''
        if len(default_value) > 1:
            raise TypeError("get expected at most 3 arguments, got %s" % (len(default_value) + 2))
        if default_value:
            return getattr(self, name, default_value[0])
        else:
            return getattr(self, name)

    def __ensure_loaded(self):
        if not self.__loaded:
            self.__loaded = True
            self._load()
            self.__sealed = True

    def __setattr__(self, name, value):
        if not name.startswith('_Settings__') and self.__sealed:
            raise RuntimeError("尝试动态修改配置项\"%s\"" % name)
        else:
            super(_Settings, self).__setattr__(name, value)

    def __getattribute__(self, name):
        try:
            return super(_Settings, self).__getattribute__(name)
        except AttributeError:
            self.__ensure_loaded()
            return super(_Settings, self).__getattribute__(name)

    def __iter__(self):
        self.__ensure_loaded()
        return self.__keys.__iter__()

    def __contain__(self, key):
        self.__ensure_loaded()
        return key in self.__keys


settings = _Settings()


class _InnerSettings(object):
    """inner settings for a SettingsMixin class
    """

    def __init__(self, defined_class):
        self.__tailer_names = {}
        self.__visited_settings_class = set()
        self.__allowed_prefix = set()
        self.__sealed = False
        self.__load_settings(defined_class)
        self.__sealed = True

    def __load_settings(self, defined_class):
        classes = [defined_class]
        base_classes = [defined_class.__bases__]
        visited_classes = set()
        while classes:
            temp_cls = classes[0]
            if not base_classes:
                if hasattr(temp_cls, "Settings"):
                    self.__allowed_prefix.add(temp_cls.__name__.upper())
                    self.__load_class_settings(temp_cls)
                visited_classes.add(temp_cls)
                classes.pop(0)
            else:
                if temp_cls in visited_classes:
                    base_classes = []
                else:
                    classes = list(temp_cls.__bases__) + classes
                    base_classes = list(classes[0].__bases__)

    def __load_class_settings(self, cls):
        prefix = cls.__name__.upper() + "_"
        class_path = cls.__module__ + "." + cls.__name__
        inner_settings_cls = getattr(cls, "Settings")
        if inner_settings_cls in self.__visited_settings_class:
            return

        self.__visited_settings_class.add(inner_settings_cls)
        for key in dir(inner_settings_cls):
            if key.startswith(prefix) and key.isupper():
                if key in settings:
                    value = settings.get(key)
                else:
                    value = getattr(inner_settings_cls, key)
                setattr(self, key, value)

                # handle legacy
                tailor_name = key[len(prefix):]
                if tailor_name in self.__tailer_names:
                    for base_prefix in self.__tailer_names[tailor_name][:]:
                        base_name = base_prefix + tailor_name
                        setattr(self, base_name, value)
                        self.__tailer_names[tailor_name].append(prefix)
                else:
                    self.__tailer_names[tailor_name] = [prefix]

            elif not key.startswith("_"):
                for item in self.__allowed_prefix:
                    if key.startswith(item):
                        tailor_name = key[len(item) + 1:]
                        break
                else:
                    tailor_name = key.upper()
                err_msg = "%s's Settings item `%s` must start with %s like %s%s" % (class_path, key, prefix, prefix, tailor_name)
                raise RuntimeError(err_msg)

    def __setattr__(self, name, value):
        if not name.startswith('_InnerSettings__') and self.__sealed:
            raise RuntimeError("dynamicly modifying value is not allowed.")
        super(_InnerSettings, self).__setattr__(name, value)

    def __getattribute__(self, name):
        try:
            return super(_InnerSettings, self).__getattribute__(name)
        except AttributeError:
            if name in settings:
                return settings.get(name)
            else:
                raise


class SettingsMixin(object):
    """a mixin class coordinate with qtaf settings
    """

    @property
    def settings(self):
        cls = type(self)
        settings_key = "_%s_settings" % cls.__name__
        if not hasattr(cls, settings_key):
            if not hasattr(cls, "Settings"):
                raise RuntimeError("no inner class Settings defined")
            inner_settings = _InnerSettings(cls)
            setattr(cls, settings_key, inner_settings)
        return getattr(cls, settings_key)
