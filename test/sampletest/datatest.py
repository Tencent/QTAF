# -*- coding: utf-8 -*-
'''
数据驱动测试用例
'''

import testbase
from testbase import datadrive
from testbase import context

@datadrive.DataDrive(
    {
    'TEST1':1,
    'TEST2':2,
    'TEST3':3,
    }
    )
class DataTest(testbase.TestCase):
    '''数据驱动测试用例
    '''
    owner = "foo"
    status = testbase.TestCase.EnumStatus.Ready
    timeout = 0.1
    priority = testbase.TestCase.EnumPriority.Normal
    def runTest(self):
        self.logInfo(str(self.casedata))
        
@datadrive.DataDrive([0])
class SingleDataTest(testbase.TestCase):
    '''数据驱动测试用例
    '''
    owner = "foo"
    status = testbase.TestCase.EnumStatus.Ready
    timeout = 0.1
    priority = testbase.TestCase.EnumPriority.Normal
    def runTest(self):
        self.logInfo(str(self.casedata))
    
    
@datadrive.DataDrive(["A", "V", "XX"])
class ArrayDataTest(testbase.TestCase):
    '''数据驱动测试用例
    '''
    owner = "foo"
    status = testbase.TestCase.EnumStatus.Ready
    timeout = 0.1
    priority = testbase.TestCase.EnumPriority.Normal
    def runTest(self):
        self.logInfo(str(self.casedata))
        
        
class ProjDataTest(testbase.TestCase):
    '''项目级别数据驱动测试用例
    '''
    owner = "foo"
    status = testbase.TestCase.EnumStatus.Ready
    timeout = 0.1
    priority = testbase.TestCase.EnumPriority.Normal
    def runTest(self):
        self.logInfo(str(context.current_testcase().casedata)) 
        self.logInfo(str(self.casedata))
 
if __name__ == '__main__':
    #执行全部的数据驱动用例
    #DataTest().run()
    #DataTest(3).run()
    ProjDataTest().run()
