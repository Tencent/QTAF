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
'''数据驱动模块

使用介绍：
1、在TestCase类前面加入@DataDrive装饰器，参数为测试数据列表或者字典::

    @datadrive.DataDrive([1,2,3])
    class Test(tc.TestCase):
        def runTest(self):
            pass
    
    @datadrive.DataDrive(
        {
        'TEST1':1,
        'TEST2':2,
        'TEST3':3,
        }
        )
    class Test(tc.TestCase):
        def runTest(self):
            pass
        
在测试报告中展示用例名字时，若参数为列表的，则在用例后面增加一个索引序号，若参数为字典的，则在用例后面增加上key的名字：

    - 列表显示为::
    
        Test#1
        Test#2
        Test#3
        
    - 字典显示为::

        Test#TEST1
        Test#TEST2
        Test#TEST3

2、可以在runTest里通过self.casedata使用测试数据::

    def runTest(self):
        print self.casedata
    
3、运行及调试方法和原来一样::

    MyTest().run()
        

    完整的例子如下::
    
    # -*- coding: utf-8 -*-
    
    import testbase.testcase as tc
    import testbase.datadrive as datadrive
    
    @datadrive.DataDrive([1,2,3])
    class MyTest(tc.TestCase):
        """test
        """
        
        owner = 'organse'
        priority = tc.TestCase.EnumPriority.High
        status = tc.TestCase.EnumStatus.Ready
        timeout = 5       
        
        def runTest(self):
            print 'runTest, casedata:', self.casedata
              
            
    if __name__ == '__main__':
        MyTest().run()
        
'''

#12/11/26    organse    创建
#14/06/23    organse    支持字典数据
#14/10/30    olive       testbase重构修改，TestCase移除execute方法
#14/10/31    olive       bugfix：appointRunAt会影响全部的每个数据驱动用例实例设置的数据
#15/03/25    olive       重构
#16/11/22    durian   给DataDrive增加__len__方法

import types
from testbase.testcase import TestCase

class DataDrive(object):
    '''数据驱动类修饰器，标识一个测试用例类使用数据驱动
    '''    
    def __init__(self, case_datas ):
        '''构造函数
        
        :param case_datas: 数据驱动测试数据集
        :type case_datas: list/tuple/dict
        '''
        self._case_datas = case_datas
                
    def __call__(self, testcase_class ):
        '''修饰器
        
        :param testcase_class: 要修饰的测试用例
        :type testcase_class: TestCase
        '''
        if not issubclass(testcase_class, TestCase):
            raise TypeError('数据驱动使用错误，只能对testcase类使用')
        testcase_class.__qtaf_datadrive__ = self
        return testcase_class
    
    def __iter__(self):
        '''遍历全部的数据名
        '''
        if isinstance(self._case_datas, types.GeneratorType):
            self._case_datas = list(self._case_datas)
        if isinstance(self._case_datas, list) or isinstance(self._case_datas, tuple):
            for it in range(len(self._case_datas)):
                yield it
        else:
            for it in self._case_datas:
                yield it
                
    def __getitem__(self, name):
        '''获取对应名称的数据
        '''
        return self._case_datas[name]
    
    def __len__(self):
        return len(self._case_datas)
        
def is_datadrive( obj ):
    '''是否为数据驱动用例
    
    :param obj: 测试用例或测试用例类
    :type obj: TestCase/type
    :returns boolean
    '''
    return hasattr(obj, '__qtaf_datadrive__')

def get_datadrive( obj ):
    '''获取对应用例的数据驱动
    
    :param obj: 测试用例或测试用例类
    :type obj: TestCase/type
    :returns DataDrive
    '''
    return obj.__qtaf_datadrive__
