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
"""
测试用例加载
"""
from __future__ import absolute_import

import imp
import pkgutil
import os
import sys
import traceback
import types

from collections import OrderedDict

import six

from testbase import datadrive
from testbase.testcase import TestCase
from testbase.testsuite import SeqTestSuite, TestSuite
from testbase.conf import settings
from testbase.util import smart_text


class TestLoader(object):
    """测试用例加载器"""

    def __init__(self, filter_func=None):
        """构造函数
        :param filter: 用例过滤函数，函数原型为 filter_func(testcase_obj)，返回None/False表示不过滤此用例
        :type filter: callable
        """
        self._filter = filter_func
        self._module_errs = {}
        self._filtered_tests = {}

    def get_last_errors(self):
        """返回最后一次load调用时加载失败的全部模块和对应错误信息

        :returns dict: 模块和对应的错误信息
        """
        return self._module_errs

    def get_filtered_tests(self):
        """返回最后一次load调用时被过滤掉的测试用例"""
        return list(self._filtered_tests.keys())

    def get_filtered_tests_with_reason(self):
        """返回最后一次load调用时被过滤掉的测试用例和过滤原因"""
        return self._filtered_tests

    def load(self, testname):
        """通过名字加载测试用例

        :param name: 用例或用例名称
        :type name: string/list

        :returns list - 测试用例对象列表
        """

        if isinstance(testname, list):
            testnames = testname
        else:
            testnames = [testname]

        self._module_errs = {}
        testcases = []

        for testname in testnames:
            parameters = {}
            exclude_data_keys = None

            if isinstance(testname, dict):
                parameters = testname.get("parameters", {})
                exclude_data_keys = testname.get("exclude_data_keys")
                testname = testname.get("name")
            testname = smart_text(testname)
            if settings.DATA_DRIVE:
                self._dataset = TestDataLoader().load()
            if "/" in testname:
                testname, data_key = testname.split("/", 1)
            else:
                data_key = None

            obj = self._load(testname)

            if isinstance(obj, types.ModuleType):
                if hasattr(obj, "__path__"):
                    testcases += self._load_from_package(
                        obj, data_key, exclude_data_keys, parameters
                    )
                else:
                    testcases += self._load_from_module(
                        obj, data_key, exclude_data_keys, parameters
                    )
            elif isinstance(obj, type):
                if issubclass(obj, TestCase):
                    testcases += self._load_from_class(
                        obj, data_key, exclude_data_keys, parameters
                    )
                elif issubclass(obj, TestSuite):
                    if not self._filter_testcase(obj):
                        tests = self._load_from_testsuite(
                            obj, data_key, exclude_data_keys, parameters
                        )
                        testcases.append(
                            obj(tests)
                        )  # append testsuite to testcase list

        # 过滤掉重复的用例
        testcase_dict = OrderedDict()
        for testcase in testcases:
            testcase_dict[testcase.test_name] = testcase

        return list(testcase_dict.values())

    def _load(self, testname):
        """加载对应的对象

        :param name: 用例或用例集名称
        :type name: string
        :returns - Type/ModuleType
        """
        parts = testname.split(".")
        module = None
        i = 0
        while i < len(parts):
            i += 1
            modulename = ".".join(parts[:i])
            try:
                module = __import__(modulename)  # __import__得到的是最外层模块的object
            except Exception as ex:  # pylint: disable=broad-except
                self._module_errs[modulename] = traceback.format_exc()
                return
            else:
                for name in parts[1:i]:
                    module = getattr(module, name)
                if not hasattr(module, "__path__"):
                    # file module
                    break

        obj = module
        if i == len(parts):  # 为一个包或模块
            return obj
        elif i < len(parts) - 1:
            self._module_errs[testname] = "ImportError: No module named %s" % ".".join(
                parts[: i + 1]
            )
            return

        classname = parts[-1]
        if classname == "SeqTestSuiteTest":  # 为顺序测试套
            return obj

        elif hasattr(module, classname):  # 为一个类
            try:
                testclass = getattr(module, classname)
                if not self._is_testcase_class(
                    testclass
                ) and not self._is_testsuite_class(testclass):
                    raise TypeError("%s不是一个有效的测试用例(套)" % testname)
            except Exception:  # pylint: disable=broad-except
                self._module_errs[testname] = traceback.format_exc()
                return
            else:
                return testclass

        else:  # 触发异常
            self._module_errs[
                testname
            ] = "ImportError: No testcase named %s in module %s" % (
                classname,
                module.__name__,
            )

    def _is_testcase_class(self, obj):
        """是否为测试用例类

        :returns bool - 是否为用例类
        """
        return (
            isinstance(obj, type)
            and issubclass(obj, TestCase)
            and hasattr(obj, "runTest")
            and getattr(obj, "priority", None)
        )

    def _is_testsuite_class(self, obj):
        """是否是测试用例套类

        :returns bool - 是否为用例套类
        """
        return (
            isinstance(obj, type)
            and issubclass(obj, TestSuite)
            and obj is not TestSuite
        )

    def _walk_package_error(self, modulename):
        """walk_packages错误回调"""
        self._module_errs[modulename] = traceback.format_exc()

    def _load_from_package(
        self,
        pkg,
        data_key=None,
        exclude_data_key=None,
        attrs=None,
        ignore_testsuite=False,
    ):
        """从一个python包加载测试用例

        :param pkg: Python包
        :type pkg: ModuleType
        :returns list - 测试用例对象列表
        """
        tests = []
        for _, modulename, ispkg in pkgutil.walk_packages(
            pkg.__path__, pkg.__name__ + ".", onerror=self._walk_package_error
        ):
            if ispkg:
                continue
            try:
                __import__(modulename)
                tests += self._load_from_module(
                    sys.modules[modulename],
                    data_key,
                    exclude_data_key=exclude_data_key,
                    attrs=None,
                    ignore_testsuite=ignore_testsuite,
                )
            except Exception:  # pylint: disable=broad-except
                self._module_errs[modulename] = traceback.format_exc()
        return tests

    def _load_from_module(
        self,
        mod,
        data_key=None,
        exclude_data_key=None,
        attrs=None,
        ignore_testsuite=False,
    ):
        """从一个python模块加载测试用例

        :param mod: Python模块
        :type mod: ModuleType
        :returns list - 测试用例对象列表
        """
        tests = []
        for name in dir(mod):
            obj = getattr(mod, name)
            if self._is_testcase_class(obj):
                tests += self._load_from_class(
                    obj, data_key, exclude_data_key=exclude_data_key, attrs=attrs
                )
            elif self._is_testsuite_class(obj) and not ignore_testsuite:
                if not self._filter_testcase(obj):
                    testcases = self._load_from_testsuite(
                        obj, data_key, exclude_data_key=exclude_data_key, attrs=attrs
                    )
                    tests.append(obj(testcases))

        if hasattr(mod, "__qtaf_seq_tests__"):  # 测试用例需要顺序执行
            seqdef = mod.__qtaf_seq_tests__
            if not isinstance(seqdef, list):
                raise TypeError("__qtaf_seq_tests__必须为list类型")
            if len(seqdef) == 0:
                raise ValueError("__qtaf_seq_tests__必须至少包含一个测试用例")
            for it in seqdef:
                if type(it) != type(TestCase) or not issubclass(it, TestCase):
                    raise TypeError("__qtaf_seq_tests__的元素必须为测试用例类")
            test_dict = {}
            for test in tests:
                if type(test) in test_dict:
                    test_dict[type(test)].append(test)
                else:
                    test_dict[type(test)] = [
                        test,
                    ]
            for it in seqdef:
                if it not in test_dict:
                    raise RuntimeError("__qtaf_seq_tests__中的测试用例'%s'已被过滤" % it.__name__)
            tests_list = []
            for it in seqdef:
                tests_list += test_dict[it]
            tests = [SeqTestSuite(tests_list)]
        return tests

    def _load_from_testsuite(
        self, cls, data_key=None, exclude_data_key=None, attrs=None
    ):
        """从测试用例套类加载测试用例"""
        tests = []
        for test in cls.testcases:
            if isinstance(test, str):
                test = self._load(test)
            if not isinstance(test, type):
                if hasattr(test, "__path__"):
                    tests += self._load_from_package(
                        test,
                        data_key,
                        exclude_data_key=exclude_data_key,
                        attrs=attrs,
                        ignore_testsuite=True,
                    )
                else:
                    tests += self._load_from_module(
                        test,
                        data_key,
                        exclude_data_key=exclude_data_key,
                        attrs=attrs,
                        ignore_testsuite=True,
                    )
            else:
                tests += self._load_from_class(
                    test, data_key, exclude_data_key=exclude_data_key, attrs=attrs
                )

        return [it for it in tests if not cls.filter(it)]

    def _filter_testcase(self, test):
        if not self._filter:
            return False
        filter_reason = self._filter(test)
        if filter_reason:
            self._filtered_tests[test] = filter_reason
            return True
        else:
            return False

    def _load_from_class(self, cls, data_key=None, exclude_data_key=None, attrs=None):
        """加载用例类

        :param cls: Python类
        :type cls: Type
        :returns list - 测试用例对象列表
        """
        if exclude_data_key is None:
            exclude_data_key = []
        exclude_data_key = [smart_text(i) for i in exclude_data_key]

        tests = []
        if datadrive.is_datadrive(cls) or settings.DATA_DRIVE:
            try:
                tests = datadrive.load_datadrive_tests(cls, data_key, attrs)
            except ValueError:
                self._module_errs[
                    "%s.%s/%s" % (cls.__module__, cls.__name__, data_key)
                ] = traceback.format_exc()
            else:
                if len(tests) == 0:
                    tests = [cls(attrs=attrs)]
        else:
            tests = [cls(attrs=attrs)]

        return [it for it in tests if not self._filter_testcase(it)]


class TestDataLoader(object):
    """测试数据加载器"""

    MODULE_NAME = "testbase.loader.testdata"

    def _load_dataset_module_from_file(self):
        """从文件中加载数据模块"""
        if self.MODULE_NAME in sys.modules:
            return sys.modules[self.MODULE_NAME]

        if os.path.isfile(__file__):
            qtaf_top_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), ".."
            )
            top_dir = qtaf_top_dir
        else:  # 使用的egg包
            qtaf_top_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), ".."
            )
            top_dir = os.path.join(qtaf_top_dir, "..", "..")
        top_dir = os.path.abspath(top_dir)

        py_path = os.path.join(top_dir, settings.DATA_SOURCE)
        if not os.path.isfile(py_path):
            raise RuntimeError('指定的数据源文件"%s"不存在' % py_path)

        module_name = os.path.basename(py_path)
        module_name = module_name[0 : module_name.rfind(".")]

        fd, pathname, desc = imp.find_module(
            module_name, [os.path.dirname(py_path), top_dir]
        )
        module = imp.load_module(self.MODULE_NAME, fd, pathname, desc)
        return module

    def _load_dataset_module_from_name(self):
        """根据模块名加载模块"""
        __import__(settings.DATA_SOURCE)
        return sys.modules[settings.DATA_SOURCE]

    def _load_dataset(self):
        """加载数据"""
        if not settings.DATA_SOURCE:
            raise RuntimeError("DATA_DRIVE=True，但未指定的数据源文件")

        if isinstance(settings.DATA_SOURCE, six.string_types):
            if settings.DATA_SOURCE.endswith(".py"):
                module = self._load_dataset_module_from_file()
            else:
                module = self._load_dataset_module_from_name()
            if not hasattr(module, "DATASET"):
                raise RuntimeError('数据源文件"%s"没有定义模块变量"DATASET"' % module)
            return module.DATASET

        else:
            return settings.DATA_SOURCE

    def load(self):
        """从数据源加载测试数据
        :returns list - 测试数据集
        """
        dataset = self._load_dataset()
        if isinstance(dataset, list) or isinstance(dataset, tuple):
            dataset_dict = OrderedDict()  # keep ordered
            for idx, it in enumerate(dataset):
                dataset_dict[str(idx)] = it
            dataset = dataset_dict
        elif isinstance(dataset, dict):
            pass
        else:
            raise ValueError("DATASET必须为list/tuple/dict类型")
        if len(dataset) == 0:
            raise ValueError("DATASET不可以为空")
        return dataset
