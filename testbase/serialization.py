# -*- coding: utf-8 -*-
#
# Tencent is pleased to support the open source community by making QTA available.
# Copyright (C) 2016THL A29 Limited, a Tencent company. All rights reserved.
# Licensed under the BSD 3-Clause License (the "License"); you may not use this
# file except in compliance with the License. You may obtain a copy of the License at
#
# https://opensource.org/licenses/BSD-3-Clause
#
# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" basis, WITHOUT WARRANTIES OR CONDITIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.
#
'''
测试用例序列化和反序列化
'''

import sys
import pickle
from testbase.testcase import TestSuite


class _EmptyClass(object):
    pass


def dumps(testcase):
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


def loads(buf):
    """反序列化测试用例
    
    :param buf: 测试用例序列化数据
    :type buf: dict
    :returns: TestCase
    """
    testname = buf['id']
    items = testname.split('.')
    classname = items[-1]
    modulename = '.'.join(items[0:-1])
    if not modulename:  # main module
        modulename = "__main__"
    else:
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
        attrs = None
        if isinstance(data, dict) and "__attrs__" in data:
            attrs = data.get("__attrs__")
        return testclass(data, buf['dname'], attrs)
