# -*- coding: utf-8 -*-
'''
模块描述
'''
import testbase

class HelloTest(testbase.TestCase):
    '''测试示例
    '''
    owner = "foo"
    status = testbase.TestCase.EnumStatus.Ready
    timeout = 1
    priority = testbase.TestCase.EnumPriority.Normal
    
    def __init__(self):
        pass
    
    def runTest(self):
        #-----------------------------
        self.startStep("测试webcontrols.WebElement构造函数")
        #-----------------------------
        
        
raise RuntimeError("load error on this module")
