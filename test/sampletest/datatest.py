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
    owner = "organse"
    status = testbase.TestCase.EnumStatus.Ready
    timeout = 0.1
    priority = testbase.TestCase.EnumPriority.Normal
    def runTest(self):
        self.logInfo(str(self.casedata))
        
@datadrive.DataDrive([0])
class SingleDataTest(testbase.TestCase):
    '''数据驱动测试用例
    '''
    owner = "organse"
    status = testbase.TestCase.EnumStatus.Ready
    timeout = 0.1
    priority = testbase.TestCase.EnumPriority.Normal
    def runTest(self):
        self.logInfo(str(self.casedata))
    
    
@datadrive.DataDrive(["A", "V", "XX"])
class ArrayDataTest(testbase.TestCase):
    '''数据驱动测试用例
    '''
    owner = "organse"
    status = testbase.TestCase.EnumStatus.Ready
    timeout = 0.1
    priority = testbase.TestCase.EnumPriority.Normal
    def runTest(self):
        self.logInfo(str(self.casedata))
        
        
class ProjDataTest(testbase.TestCase):
    '''项目级别数据驱动测试用例
    '''
    owner = "organse"
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