# -*- coding: utf-8 -*-
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


