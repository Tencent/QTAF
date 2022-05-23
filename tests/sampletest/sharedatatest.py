# -*- coding: utf-8 -*-
'''
参数测试用例
'''

import testbase
import time


class AddShareDataTest(testbase.TestCase):
    '''参数测试用例
    '''
    owner = "foo"
    status = testbase.TestCase.EnumStatus.Ready
    timeout = 0.1
    priority = testbase.TestCase.EnumPriority.Normal

    def runTest(self):
        self.add_share_data('test1', 100),
        self.add_share_data('test2', {'a': 'b', 'b': 123, 'c': [1, 2, 3]})

class GetShareDataTest(testbase.TestCase):
    '''参数测试用例
    '''
    owner = "foo"
    status = testbase.TestCase.EnumStatus.Ready
    timeout = 1
    priority = testbase.TestCase.EnumPriority.Normal

    def runTest(self):
        time.sleep(0.5)
        test1 = self.get_share_data('test1')
        test2 = self.get_share_data('test2')
        self.assert_equal('assert test1', test1, 100)
        self.assert_equal('assert test2', test2, {'a': 'b', 'b': 123, 'c': [1, 2, 3]})


class RemoveShareDataTest(testbase.TestCase):
    '''参数测试用例
    '''
    owner = "foo"
    status = testbase.TestCase.EnumStatus.Ready
    timeout = 0.1
    priority = testbase.TestCase.EnumPriority.Normal

    def runTest(self):
        self.remove_share_data('test1')
