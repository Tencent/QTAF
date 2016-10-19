# -*- coding: utf-8 -*-
'''
测试用例序列化和反序列化
'''
#2015/03/31 eeelin 新建
#2016/01/27 eeelin 对测试数据进行pickle化处理，方式出现不可以序列化的对象

import sys
import pickle
from testbase.testcase import TestSuite


class _EmptyClass(object):
    pass

def dumps( testcase ):
    """序列化测试用例
    
    :param testcase: 测试用例
    :type testcase: TestCase
    """
    if isinstance(testcase, TestSuite):
        return {
            'id': testcase.suite_class_name,
            'data': pickle.dumps(testcase.dumps())
        }
    else:
        return {
            'id': testcase.test_class_name,
            'data': pickle.dumps(testcase.casedata),
            'dname': testcase.casedataname,
        }

def loads( buf ):
    """反序列化测试用例
    
    :param buf: 测试用例序列化数据
    :type buf: dict
    :returns: TestCase
    """
    testname = buf['id']
    items = testname.split('.')
    classname = items[-1]
    modulename = '.'.join(items[0:-1])
    __import__(modulename)
    module = sys.modules[modulename]
    testclass = getattr(module, classname)
    data = pickle.loads(buf['data'])
    if issubclass(testclass, TestSuite):
        obj = _EmptyClass()
        obj.__class__ = testclass
        obj.loads(data)
        return obj
    else:
        return testclass(data, buf['dname'])
