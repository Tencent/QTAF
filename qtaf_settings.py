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
# 资源管理系统配置
# -----------------------------------
USE_RESMGR_V5 = True
RESMGR_JSONRPC_URL = 'http://resmgr.qta.oa.com/resource/'
LOG_RESOURCE_NOT_READY = True

# -----------------------------------
# PYQQ相关配置
# -----------------------------------
PYQQ_SERVER_HOST = 'tools.sng.local'
PYQQ_PSKEY_DOMAINS = [
    "qzone.qq.com",
    "qzone.com"
]

PYQQ_OSS_SERVER_LIST =  [
    ('msfwifi.3g.qq.com', 14000),
]

PYQQ_OIDB_MOCK_CLIENT_IP_LIST = [
    '14.17.22.20',
    '14.17.22.21',
    '14.17.22.22',
    '14.17.22.23',
    '14.17.22.31',
    '14.17.22.32',
    '14.17.22.33',
    '14.17.22.34',
    '14.17.22.35',
    '14.17.22.36',
    '14.17.22.37',
    '14.17.22.38',
    '14.17.22.39',
    '14.17.22.40',
    '14.17.22.41',
    '14.17.22.42',
    '14.17.22.43',
    '14.17.22.44',
    '14.17.22.45',
    '14.17.22.46',
    '14.17.22.47',
    '14.17.22.48',
    '14.17.22.49',
    '14.17.22.50',
    '14.17.22.51',
    '14.17.22.52',
    '14.17.22.53',
    '14.17.22.54',                                 
]

QTAF_REPORT_URL = "http://testing.sng.local/report/v2"
QTAF_FILE_HOST = "file.test.sng.local"