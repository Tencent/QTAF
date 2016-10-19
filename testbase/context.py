# -*- coding: utf-8 -*-
'''
测试用例执行时上下文
'''
#2015/03/31 eeelin 新建

from testbase.util import ThreadGroupLocal

def current_testcase():
    '''当前正在执行的用例
    
    :returns: TestCase
    '''
    return getattr(ThreadGroupLocal(), 'testcase', None)

def current_testresult():
    '''当前正在执行的用例对应的测试结果
    
    :returns: TestResult
    '''
    return getattr(ThreadGroupLocal(), 'testresult', None)