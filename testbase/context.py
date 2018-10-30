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
测试用例执行时上下文
'''

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

def current_testcase_local():
    return ThreadGroupLocal()