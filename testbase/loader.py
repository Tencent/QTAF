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
import six
'''
测试用例加载
'''

import types
import sys
import pkgutil
import os
import imp
import traceback

from testbase.testcase import TestCase, SeqTestSuite
from testbase.conf import settings
from testbase.util import smart_text
from testbase import datadrive

class TestLoader(object):
    '''测试用例加载器
    '''
    def __init__(self, filter_func=None ):
        '''构造函数
        :param filter: 用例过滤函数，函数原型为 filter_func(testcase_obj)，返回None/False表示不过滤此用例
        :type filter: callable
        '''
        self._filter = filter_func
        self._module_errs = {}
        self._filtered_tests = {}
            
    def get_last_errors(self):
        '''返回最后一次load调用时加载失败的全部模块和对应错误信息
        
        :returns dict: 模块和对应的错误信息
        '''
        return self._module_errs
                    
    def get_filtered_tests(self):
        '''返回最后一次load调用时被过滤掉的测试用例
        '''
        return list(self._filtered_tests.keys())
    
    def get_filtered_tests_with_reason(self):
        '''返回最后一次load调用时被过滤掉的测试用例和过滤原因
        '''
        return self._filtered_tests
                    
    def load(self, testname ):
        '''通过名字加载测试用例
        
        :param name: 用例或用例名称
        :type name: string/list
        :returns list - 测试用例对象列表
        '''

        if isinstance(testname, list):
            testnames = testname
        else:
            testnames = [testname]

        self._module_errs = {}
        testcases = []

        for testname in testnames:
            testname = smart_text(testname)
            if settings.DATA_DRIVE:
                self._dataset = TestDataLoader().load()
            if '/' in testname:
                testname, datakeyname = testname.split('/', 1)
            else:
                datakeyname = None 
                
            obj = self._load(testname)
            
            if isinstance(obj, types.ModuleType):
                if hasattr(obj, '__path__'):
                    testcases += self._load_from_package(obj)
                else:
                    testcases += self._load_from_module(obj)
            elif isinstance(obj, type):
                testcases += self._load_from_class(obj)
        
        #过滤掉重复的用例
        testcase_dict = {}
        for testcase in testcases:
            if datakeyname and smart_text(testcase.casedataname) != datakeyname:
                continue
            testcase_dict[testcase.test_name] = testcase
            
        return list(testcase_dict.values())

    def _load(self, testname ):
        '''加载对应的对象
        
        :param name: 用例或用例集名称
        :type name: string
        :returns - Type/ModuleType
        '''
        parts = testname.split('.')
        module = None
        parts_imp = parts[:]
        while parts_imp:
            try:
                modulename = '.'.join(parts_imp)
                __import__(modulename)   #__import__得到的是最外层模块的object
                module = sys.modules[modulename]
                break
            except ImportError:
                del parts_imp[-1]
            except:
                del parts_imp[-1]
                break
            
        obj = module
        
        if parts_imp == parts: #为一个包或模块
            return obj
        
        elif parts_imp == parts[0:-1] and hasattr(module, parts[-1]): #为一个类
            try:
                testclass = getattr(module, parts[-1])
                if not self._is_testcase_class(testclass):
                    raise TypeError("%s不是一个有效的测试用例"%testname)      
            except:
                self._module_errs[testname] = traceback.format_exc()
                return
            else:
                return testclass


        else: #触发异常
            if parts_imp:
                modulename = '.'.join(parts_imp)
                modulename += '.'
            else:
                modulename = ''
            modulename += parts[len(parts_imp)]
            try:
                __import__(modulename)
            except:
                self._module_errs[modulename] = traceback.format_exc()
    
    def _is_testcase_class(self, obj ):
        '''是否为测试用例类
        
        :returns bool - 是否为用例类
        '''
        return ( isinstance(obj, type) and
              issubclass(obj, TestCase) and
              hasattr(obj, "runTest") and 
              getattr(obj, "priority", None))
        
    def _walk_package_error(self, modulename ):
        '''walk_packages错误回调
        '''
        self._module_errs[modulename] = traceback.format_exc()
        
    def _load_from_package(self, pkg ):
        '''从一个python包加载测试用例
        
        :param pkg: Python包
        :type pkg: ModuleType
        :returns list - 测试用例对象列表
        '''
        tests = []
        for _, modulename, ispkg in pkgutil.walk_packages(pkg.__path__, pkg.__name__+'.', onerror=self._walk_package_error):
            if ispkg:
                continue
            try:
                __import__(modulename)
                tests += self._load_from_module(sys.modules[modulename])
            except:
                self._module_errs[modulename] = traceback.format_exc()
        return tests
    
    def _load_from_module(self, mod):
        '''从一个python模块加载测试用例
        
        :param mod: Python模块
        :type mod: ModuleType
        :returns list - 测试用例对象列表
        '''
        tests = []
        for name in dir(mod):
            obj = getattr(mod, name)
            if self._is_testcase_class(obj):
                tests += self._load_from_class(obj)
        if hasattr(mod, '__qtaf_seq_tests__'): #测试用例需要顺序执行
            seqdef = mod.__qtaf_seq_tests__
            if not isinstance(seqdef, list):
                raise TypeError("__qtaf_seq_tests__必须为list类型")
            if len(seqdef) == 0:
                raise ValueError("__qtaf_seq_tests__必须至少包含一个测试用例")
#            modulename = mod.__name__
            for it in seqdef:
                if type(it) != type(TestCase) or not issubclass(it, TestCase):
                    raise TypeError("__qtaf_seq_tests__的元素必须为测试用例类")
#                 if it.__module__ != modulename:
#                     raise ValueError("__qtaf_seq_tests__中的测试用例类必须在当前模块中定义，'%s'不属于当前模块" % it.__name__)
            test_dict = {}
            for test in tests:
                test_dict[type(test)] = test
            for it in seqdef:
                if it not in test_dict:
                    raise RuntimeError("__qtaf_seq_tests__中的测试用例'%s'已被过滤"%it.__name__)
            tests = [SeqTestSuite([ test_dict[it] for it in seqdef])]
        return tests
    
    def _load_from_class(self, cls ):
        '''加载用例类
        
        :param cls: Python类 
        :type cls: Type
        :returns list - 测试用例对象列表
        '''
        tests = []
        if datadrive.is_datadrive(cls):
            tests = datadrive.load_datadrive_tests(cls)
        elif settings.DATA_DRIVE:
            tests = [cls(self._dataset[it], str(it)) for it in self._dataset]
        else:
            tests = [cls()]
        
        if self._filter:
            final_tests = []
            for it in tests:
                filter_reason = self._filter(it)
                if filter_reason:
                    self._filtered_tests[it] = filter_reason
                else:
                    final_tests.append(it)
            tests = final_tests 
        return tests
    
class TestDataLoader(object):
    '''测试数据加载器
    '''
    MODULE_NAME = 'testbase.loader.testdata'
    
    
    def _load_dataset_module_from_file(self):
        '''从文件中加载数据模块
        '''
        if self.MODULE_NAME in sys.modules:
            return sys.modules[self.MODULE_NAME]
        
        if os.path.isfile(__file__):
            qtaf_top_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
            top_dir = qtaf_top_dir
        else: #使用的egg包
            qtaf_top_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
            top_dir = os.path.join(qtaf_top_dir, '..', '..')
            
        py_path = os.path.join(top_dir, settings.DATA_SOURCE)
        if not os.path.isfile(py_path):
            raise RuntimeError("指定的数据源文件\"%s\"不存在"%py_path)
            
        module_name = os.path.basename(py_path)
        module_name = module_name[0:module_name.rfind('.')]
        
        fd, pathname, desc = imp.find_module(module_name, [os.path.dirname(py_path), top_dir])
        module = imp.load_module(self.MODULE_NAME, fd, pathname, desc)
        return module
             
    def _load_dataset_module_from_name(self):
        '''根据模块名加载模块
        '''
        __import__(settings.DATA_SOURCE)
        return sys.modules[settings.DATA_SOURCE]
        
    def _load_dataset(self):
        '''加载数据
        '''
        if not settings.DATA_SOURCE:
            raise RuntimeError("DATA_DRIVE=True，但未指定的数据源文件")
        
        if isinstance(settings.DATA_SOURCE, six.string_types):
            if settings.DATA_SOURCE.endswith('.py'):
                module = self._load_dataset_module_from_file()
            else:
                module = self._load_dataset_module_from_name()
            if not hasattr(module, 'DATASET'):
                raise RuntimeError("数据源文件\"%s\"没有定义模块变量\"DATASET\"" % module)         
            return module.DATASET
        
        else:
            return settings.DATA_SOURCE

    def load(self):
        '''从数据源加载测试数据
        :returns list - 测试数据集
        '''
        dataset = self._load_dataset()
        if isinstance(dataset, list) or isinstance(dataset, tuple):
            dataset_dict = {}
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
    