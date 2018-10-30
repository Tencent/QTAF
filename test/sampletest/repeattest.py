# -*- coding: utf-8 -*-
'''
一个用例重复执行
'''

from testbase import TestCase
from testbase.testcase import RepeatTestCaseRunner

class RepeatTest(TestCase):
    '''测试示例
    '''
    owner = "foo"
    status = TestCase.EnumStatus.Ready
    timeout = 1
    priority = TestCase.EnumPriority.Normal
    case_runner = RepeatTestCaseRunner()
    repeat = 5
    
    def runTest(self):
        self.logInfo('第%s次测试执行'%self.iteration)
        
if __name__ == '__main__':
    RepeatTest().run()
