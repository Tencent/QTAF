# -*- coding: utf-8 -*-


import testbase

__qtaf_tags__ = "mod"

class TagTest(testbase.TestCase):
    '''测试示例
    '''
    owner = "foo"
    status = testbase.TestCase.EnumStatus.Ready
    timeout = 1
    priority = testbase.TestCase.EnumPriority.Normal
    tags = "test"

    def runTest(self):
        #-----------------------------
        self.startStep("测试")
        #-----------------------------
        self.assert_equal('断言失败', False, True)

class TagTest2(testbase.TestCase):
    '''测试示例
    '''
    owner = "foo"
    status = testbase.TestCase.EnumStatus.Ready
    timeout = 1
    priority = testbase.TestCase.EnumPriority.Normal
    tags = "test2"

    def runTest(self):
        #-----------------------------
        self.startStep("测试")
        #-----------------------------
        self.assert_equal('断言失败', False, True)
