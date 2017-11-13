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
'''log模块
'''

import logging
import sys
import traceback
from testbase import context

#2012/07/20 pear    去掉basicConfig，因为会重复打印stream log
#2012/06/10 persimmon    给logging系统做基本配置
#2015/03/30 olive      TestResult和logging模块解耦
#2016/06/27 durian  如果TestResult为空，则输出到控制台


_streamhandler=logging.StreamHandler(sys.stdout)
class TestResultBridge(logging.Handler):
    '''中转log信息到TestResult
    '''
    def emit(self, log_record):
        '''Log Handle 必须实现此函数
        '''
        testresult = context.current_testresult()
        if testresult is None:
            _streamhandler.emit(log_record)
            return
        record = {}
        if log_record.exc_info:
            record['traceback'] = ''.join(traceback.format_tb(log_record.exc_info[2])) + '%s: %s' %(
                                   log_record.exc_info[0].__name__, log_record.exc_info[1])
        testresult.log_record(log_record.levelno, log_record.msg, record)
        
_LOGGER_NAME = "QTA_LOGGER"
_logger = logging.getLogger(_LOGGER_NAME)
_logger.setLevel(logging.DEBUG)
_logger.addHandler(TestResultBridge())

        
def critical(msg, *args, **kwargs):
    _logger.error(msg, *args, **kwargs)
 
fatal = critical

def error(msg, *args, **kwargs):
    '''Log a message with severity 'ERROR' on the root logger.
    '''
    _logger.error(msg, *args, **kwargs)

def exception(msg, *args):
    '''Log a message with severity 'ERROR' on the root logger,with exception information.
    '''
    _logger.exception(msg, *args)

def warning(msg, *args, **kwargs):
    '''Log a message with severity 'WARNING' on the root logger.
    '''
    _logger.warning(msg, *args, **kwargs)

warn = warning

def info(msg, *args, **kwargs):
    '''Log a message with severity 'INFO' on the root logger.
    '''
    _logger.info(msg, *args, **kwargs)

def debug(msg, *args, **kwargs):
    '''Log a message with severity 'DEBUG' on the root logger.
    '''
    _logger.debug(msg, *args, **kwargs)

def log(level, msg, *args, **kwargs):
    '''Log 'msg % args' with the integer severity 'level' on the root logger.
    '''
#    print len(root.handlers)
    _logger.log(level, msg, *args, **kwargs)
    
def addHandler(hdlr):
    '''Add the specified handler to this logger.
    '''
    _logger.addHandler(hdlr)
    
def removeHandler(hdlr):
    '''Remove the specified handler from this logger.
    '''
    _logger.removeHandler(hdlr)
    