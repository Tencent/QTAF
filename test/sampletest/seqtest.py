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
    
    
# class SequenceTest(object):
#     '''顺序执行的用例
#     '''    
#     def __init__(self, test_classes ):
#         '''构造函数
#         :param test_classes: 测试用例类列表
#         :type test_classes: list
#         '''
#         self._test_classes = test_classes
#         self._testcase_class = None
#                 
#     def __call__(self, testcase_class ):
#         '''修饰器
#         :param testcase_class: 要修饰的测试用例
#         :type testcase_class: TestCase
#         '''
#         self._testcase_class = testcase_class
#         testcase_class.case_runner = SeqTestCaseRunner()
#         testcase_class.sequence = self._test_classes
#         timeout = 0
#         for it in self._test_classes:
#             it.owner = testcase_class.owner
#             it.status = testcase_class.status
#             it.priority = testcase_class.priority
#             it.test_class_name = property(fget=self.get_test_class_name)
#             
#             timeout += it.timeout
#             it.controller = testcase_class
#         testcase_class.timeout = timeout
#         return testcase_class
#         
#     def get_test_class_name(self, name ):
#         return self._testcase_class().test_class_name
#         
# @SequenceTest([TestA, TestB, TestC])
# class SeqTest(TestCase):
#     '''按照顺序执行的用例
#     '''
#     owner = "foo"
#     status = TestCase.EnumStatus.Ready
#     priority = TestCase.EnumPriority.Normal
#     
#     def __iter__(self):
#         for it in self.sequence:
#             testcase = it()
# #             print testcase.test_class_name
# #             print testcase.test_name
#             yield testcase
#     
    
__qtaf_seq_tests__ = [TestA, TestB, TestC]
    
if __name__ == '__main__':
    
    from testbase.testcase import debug_run_all
    debug_run_all()
    
    #print SeqTest.timeout
    #print TestC.owner
    
