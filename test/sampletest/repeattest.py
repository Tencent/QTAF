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
一个用例重复执行
'''

from testbase import TestCase
from testbase.testcase import RepeatTestCaseRunner

class RepeatTest(TestCase):
    '''测试示例
    '''
    owner = "olive"
    status = TestCase.EnumStatus.Ready
    timeout = 1
    priority = TestCase.EnumPriority.Normal
    case_runner = RepeatTestCaseRunner()
    repeat = 5
    
    def runTest(self):
        self.logInfo('第%s次测试执行'%self.iteration)
        
if __name__ == '__main__':
    RepeatTest().run()