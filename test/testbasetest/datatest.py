# -*- coding: utf-8 -*-
'''
项目级数据模块测试
'''
#2015/03/27    eeelin 创建

import unittest
import threading

from testbase.data import data, dataset, TestData
from testbase.util import ThreadGroupScope

class TestDataTest(unittest.TestCase):
    '''测试数据测试
    '''
    def test_use_data(self):
        '''一般使用
        '''
        self.assertEqual(data['SSO'], {'HOST': '114.12.12.30', 'PORT': 8080})
        
    def test_use_set(self):
        '''数据集使用
        '''
        self.assertEqual(dataset[0]['SSO'], {'HOST': '114.12.12.30', 'PORT': 8080})
        
    def _test_child_thread(self, port ):
        '''测试线程子线程
        '''
        self.assertEqual(data['SSO'], {'HOST': '114.12.12.30', 'PORT': port})
        
    def _test_thread(self, testname, port):
        '''测试线程
        '''
        with ThreadGroupScope(testname):
            TestData().update({'SSO':{'HOST': '114.12.12.30', 'PORT': port}})
            self.assertEqual(data['SSO'], {'HOST': '114.12.12.30', 'PORT': port})
            t = threading.Thread(target=self._test_child_thread, args=(port,))
            t.start()
            t.join()
            
    def test_testcase_thread_local(self):
        '''多用例线程隔离
        '''
        t1 = threading.Thread(target=self._test_thread, args=('test1', 1))
        t2 = threading.Thread(target=self._test_thread, args=('test2', 2))
        t3 = threading.Thread(target=self._test_thread, args=('test3', 3))
        t1.start()
        t2.start()
        t3.start()
        t1.join()
        t2.join()
        t3.join()
        
        
        