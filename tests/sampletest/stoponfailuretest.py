# -*- coding: utf-8 -*-
'''
参数测试用例
'''

import testbase
import time


class FirstFailureTest(testbase.TestCase):
    """
    参数测试用例
    """
    owner = "foo"
    status = testbase.TestCase.EnumStatus.Ready
    priority = testbase.TestCase.EnumPriority.Normal
    timeout = 1

    def run_test(self):
        self.assertEqual("1", "2")

class SecondFailureTest(testbase.TestCase):
    """
    参数测试用例
    """
    owner = "foo"
    status = testbase.TestCase.EnumStatus.Ready
    priority = testbase.TestCase.EnumPriority.Normal
    timeout = 1


    def run_test(self):
        self.assertEqual("hello", "world")

