# -*- coding: utf-8 -*-
'''
测试环境模块
'''
#11/07/20 jonliang    创建


class EnumEnvType(object):
    '''测试机运行环境的类型
    Local代表本机，Lab代表测试任务执行机
    '''
    Local, Lab = ('Local', 'Lab')

run_env = EnumEnvType.Local