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
QTAF配置文件
'''
# -----------------------------------
# 调试模式开关
# -----------------------------------
DEBUG = False
 
# -----------------------------------
# 全局数据驱动配置
# -----------------------------------
DATA_DRIVE = False
DATA_SOURCE = 'test/data/server.py'

# -----------------------------------
# 项目配置
# -----------------------------------
PROJECT_NAME = 'qtaf'
PROJECT_MODE = 'standalone' #choices: standard/standalone
PROJECT_ROOT = None#os.path.dirname(__file__)
INSTALLED_APPS = []


# -----------------------------------
# Assert 
# -----------------------------------
QTAF_REWRITE_ASSERT = True

