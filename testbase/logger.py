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
import os

import Testcase.settings as settings
from testbase import context
from testbase.util import ensure_binary_stream, smart_binary, smart_text

_stream, _encoding = ensure_binary_stream(sys.stdout)
class PackagePathFilter(logging.Filter):
    def filter(self, record):
        pathname = record.pathname
        record.relativepath = None
        abs_sys_paths = map(os.path.abspath, sys.path)
        for path in sorted(abs_sys_paths, key=len, reverse=True):  # longer paths first
            if not path.endswith(os.sep):
                path += os.sep
            if pathname.startswith(path):
                record.relativepath = os.path.relpath(pathname, path)
                break
        return True

class _StreamFormatter(logging.Formatter):
    def format(self, record):
        _f = logging.Formatter('[%(asctime)s][%(levelname)s][%(threadName)s][%(relativepath)s:%(lineno)d][%(funcName)s] %(message)s')
        s = _f.format(record)
        return smart_binary(s, encoding=_encoding)

class _ReportFormatter(logging.Formatter):
    def format(self, record):
        _f = logging.Formatter('[%(threadName)s][%(relativepath)s:%(lineno)d][%(funcName)s] %(message)s')
        s = _f.format(record)
        return smart_binary(s, encoding=_encoding)

_stream_handler=logging.StreamHandler(_stream)
_stream_handler.terminator = b"\n"
_stream_handler.setFormatter(_StreamFormatter())
_stream_handler.addFilter(PackagePathFilter())
_stream_handler.setLevel(logging.DEBUG)

class TestResultBridge(logging.Handler):
    '''中转log信息到TestResult
    '''
    def emit(self, log_record):
        '''Log Handle 必须实现此函数
        '''
        testresult = context.current_testresult()
        if testresult is None:
            _stream_handler.emit(log_record)
            return
        record = {}
        if log_record.exc_info:
            record['traceback'] = ''.join(traceback.format_tb(log_record.exc_info[2])) + '%s: %s' %(
                                   log_record.exc_info[0].__name__, log_record.exc_info[1])
        msg = smart_text(self.format(log_record))
        testresult.log_record(log_record.levelno, msg, record)


result_handler = TestResultBridge()
result_handler.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
result_handler.setFormatter(_ReportFormatter())
result_handler.addFilter(PackagePathFilter())

_LOGGER_NAME = "QTA_LOGGER"
_logger = logging.getLogger(_LOGGER_NAME)
_logger.setLevel(logging.DEBUG)
# if settings.CONSOLE_REPORT:
#     _logger.addHandler(_stream_handler)
_logger.addHandler(result_handler)


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
    _logger.log(level, msg, *args, **kwargs)

def addHandler(hdlr):
    '''Add the specified handler to this logger.
    '''
    _logger.addHandler(hdlr)

def removeHandler(hdlr):
    '''Remove the specified handler from this logger.
    '''
    _logger.removeHandler(hdlr)
