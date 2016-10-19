# -*- coding: utf-8 -*-
'''测试框架类库
testcase -- 定义测试用例基类TestCase
testresult -- 测试用例结果输出模块
'''
#2012/10/10 aaronlai    __version__是python模块较通用的用法
#2012/10/11 aaronlai    去除__version__，模块里暂不管理版本号
from testcase import TestCase, TestCaseStatus, TestCasePriority
from testbase.version import version