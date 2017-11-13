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
'''loader test
'''
#2015/03/27 olive created

import unittest

from testbase.loader import TestLoader

class TestLoaderTest(unittest.TestCase):
    '''测试用例加载测试
    '''
    def test_load_testcase(self):
        '''测试加载一个用例
        '''
        tests = TestLoader().load("test.sampletest.hellotest.HelloTest")
        self.assertEqual(len(tests), 1)
        from test.sampletest.hellotest import HelloTest
        self.assertEqual(type(tests[0]), HelloTest)
        
    def test_load_datadrive(self):
        '''测试数据驱动用例
        '''
        from test.sampletest.datatest import DataTest
        tests = TestLoader().load("test.sampletest.datatest.DataTest")
        self.assertEqual(len(tests), 3)
        self.assertEqual(type(tests[0]), DataTest)
        
        
    def test_load_failed_not_found(self):
        loader = TestLoader()
        tests = loader.load("test.sampletest.notfound")
        self.assertEqual(len(tests), 0)
        errors = loader.get_last_errors()
        self.assertEqual(len(errors), 1)
        self.assertIn("test.sampletest.notfound", errors)
        self.assertIn("No module named notfound", errors.values()[0])
        
    def test_load_failed_runtime_error(self):
        loader = TestLoader()
        tests = loader.load("test.sampletest.loaderr")
        self.assertEqual(len(tests), 0)
        errors = loader.get_last_errors()
        self.assertEqual(len(errors), 1)
        self.assertIn("test.sampletest.loaderr", errors)
        self.assertIn("RuntimeError", errors.values()[0])
        
    def test_load_filter(self):
        filtered_test = 'test.sampletest.hellotest.HelloTest'
        def filter_func(test):
            if test.test_class_name == filtered_test:
                return "hello filtered"
        loader = TestLoader(filter_func)
        tests = loader.load("test.sampletest")
        testnames = [ it.test_class_name for it in tests ]
        self.assertNotIn(filtered_test, testnames)
        tests = loader.get_filtered_tests()
        self.assertEqual(len(tests), 1)
        self.assertEqual(tests[0].test_class_name, filtered_test)
        result = loader.get_filtered_tests_with_reason()
        self.assertEqual(len(tests), 1)
        self.assertEqual(result.keys()[0].test_class_name, filtered_test)
        self.assertEqual("hello filtered", result.values()[0])
        
        
class SettingWarpper(object):
    
    def __init__(self, settings):
        self.real_settings = settings
    
    def __getattribute__(self, name):
        if name.isupper():
            if name == 'DATA_DRIVE':
                return True
            else:
                return getattr(self.real_settings, name)
        else:
            return super(SettingWarpper,self).__getattribute__(name)
            
class DataDriveTestLoaderTest(unittest.TestCase):
    '''global data-drive test loader
    '''  

    def setUp(self):
        from testbase import loader
        from testbase import conf
        new_settiongs = SettingWarpper(loader.settings)
        loader.settings = new_settiongs
        conf.settings = new_settiongs
        

    def tearDown(self):
        from testbase import loader
        from testbase import conf
        loader.settings = loader.settings.real_settings
        conf.settings = loader.settings
        
    def test_load_testcase(self):
        '''load a test with global data-drive
        '''
        from test.data import server
        tests = TestLoader().load("test.sampletest.hellotest.HelloTest")
        self.assertEqual(len(tests), 3)
        casedatas = set()
        for test in tests:
            self.assertEqual(test.test_class_name, "test.sampletest.hellotest.HelloTest")
            casedatas.add(str(test.casedata))
        self.assertEqual(casedatas, set([str(it) for it in server.DATASET]))    
        