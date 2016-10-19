# -*- coding: utf-8 -*-
'''
测试用例加载测试
'''
#2015/03/27    eeelin 创建

import unittest

from testbase.loader import TestLoader
from testbase import datadrive

class TestLoaderTest(unittest.TestCase):
    '''测试用例加载测试
    '''
    def test_load_testcase(self):
        '''测试加载一个用例
        '''
        from test.sampletest.hellotest import HelloTest
        test = HelloTest()
        data = test.dumps()
        test2 = TestLoader().load(data)
        self.assertEqual(type(test2), HelloTest)
        
    def test_load_datadrive(self):
        '''测试数据驱动用例
        '''
        from test.sampletest.datatest import DataTest
        tests = TestLoader().load_from_name("test.sampletest.datatest.DataTest")
        self.assertEqual(len(tests), 3)
        self.assertEqual(type(tests[0]), datadrive.DataDriveTestCase)
        self.assertEqual(type(tests[0].testcase), DataTest)
        
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
    '''项目级别测试驱动测试加载用例
    '''  

    def setUp(self):
        from testbase import loader
        from testbase import conf
        new_settiongs = SettingWarpper(loader.settings)
        loader.settings = new_settiongs
        conf.settings = new_settiongs
        
        from testbase import data
        reload(data)

    def tearDown(self):
        from testbase import loader
        from testbase import conf
        loader.settings = loader.settings.real_settings
        conf.settings = loader.settings
        from testbase import data
        reload(data)
        
    def test_load_testcase(self):
        '''测试加载一个用例
        '''
        from test.sampletest.hellotest import HelloTest
        tests = TestLoader().load_from_name("test.sampletest.hellotest.HelloTest")
        self.assertEqual(len(tests), 3)
        self.assertEqual(type(tests[0]), datadrive.GlobalDataDriveTestCase)
        self.assertEqual(type(tests[0].testcase), HelloTest)