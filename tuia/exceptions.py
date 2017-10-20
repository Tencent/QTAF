# -*- coding: utf-8 -*-
'''
异常模块定义
'''
#2012/03/16 aaronlai    初稿，创建

class ControlNotFoundError(Exception):
    '''控件没有找到
    '''
    pass

class ControlAmbiguousError(Exception):
    '''找到多个控件
    '''
    pass

class ControlExpiredError(Exception):
    '''控件失效错误
    '''
    pass

class TimeoutError(Exception):
    '''超时异常
    '''
    pass