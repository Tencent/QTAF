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
'''测试框架类库
testcase -- 定义测试用例基类TestCase
testresult -- 测试用例结果输出模块
'''
#2012/10/10 pear    __version__是python模块较通用的用法
#2012/10/11 pear    去除__version__，模块里暂不管理版本号
from testcase import TestCase, TestCaseStatus, TestCasePriority
from testbase.version import version