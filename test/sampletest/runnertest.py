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
'''test case for runner test
'''

from testbase import TestCase

class SuccTest(TestCase):
    '''测试示例
    '''
    timeout = 1
    owner = "olive"
    status = TestCase.EnumStatus.Ready
    priority = TestCase.EnumPriority.Normal
    expect_passed = True
    
    def run_test(self):
        pass
    
class ErrLogTest(TestCase):
    '''测试示例
    '''
    timeout = 1
    owner = "olive"
    status = TestCase.EnumStatus.Ready
    priority = TestCase.EnumPriority.Normal
    expect_passed = False
    
    def run_test(self):
        self.test_result.error("error")
        
        
class FailedTest(TestCase):
    '''测试示例
    '''
    timeout = 1
    owner = "olive"
    status = TestCase.EnumStatus.Ready
    priority = TestCase.EnumPriority.Normal
    expect_passed = False
    
    def run_test(self):
        self.fail("error")
    
class ExceptTest(TestCase):
    '''测试示例
    '''
    timeout = 1
    owner = "olive"
    status = TestCase.EnumStatus.Ready
    priority = TestCase.EnumPriority.Normal
    expect_passed = False
    
    def run_test(self):
        raise RuntimeError("fault")

    