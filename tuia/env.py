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
测试环境模块
'''

import warnings

warnings.warn("`tuia.env` will be removed in the future", DeprecationWarning)

class EnumEnvType(object):
    '''测试机运行环境的类型
    Local代表本机，Lab代表测试任务执行机
    '''
    Local, Lab = ('Local', 'Lab')

run_env = EnumEnvType.Local