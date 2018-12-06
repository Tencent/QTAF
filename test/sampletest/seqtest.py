# -*- coding: utf-8 -*-
'''
按照顺序执行用例（伪实现）
'''

from testbase import TestCase
from testbase.testcase import RepeatTestCaseRunner

class TestA(TestCase):
    '''测试示例
    '''
    timeout = 1
    owner = "foo"
    status = TestCase.EnumStatus.Ready
    priority = TestCase.EnumPriority.Normal
    
    def run_test(self):
        pass
    
class TestB(TestCase):
    '''测试示例
    '''
    timeout = 1
    owner = "foo"
    status = TestCase.EnumStatus.Ready
    priority = TestCase.EnumPriority.Normal
    case_runner = RepeatTestCaseRunner()
    repeat = 4
    
    def run_test(self):
        pass
    
class TestC(TestCase):
    '''测试示例
    '''
    timeout = 1
    owner = "foo"
    status = TestCase.EnumStatus.Ready
    priority = TestCase.EnumPriority.Normal
    
    def run_test(self):
        pass
    
__qtaf_seq_tests__ = [TestA, TestB, TestC]
    
if __name__ == '__main__':
    
    from testbase.testcase import debug_run_all
    debug_run_all()
    
