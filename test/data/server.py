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
测试数据文件
'''

WTLOGIN = {
    'HOST': 'wtlogin.qq.com',
    'PORT': 80
}

SSO = [
    {
        'HOST': '114.12.12.30',
        'PORT': 8080
    },
    {
        'HOST': '114.12.12.31',
        'PORT': 8080
    },
    {
        'HOST': '114.12.12.32',
        'PORT': 8080
    },   
]

DATASET = [
    {
        'SSO': it,
        'WTLOGIN': WTLOGIN,
    }
    for it in SSO
]


DEFAULT_KEY = 0


