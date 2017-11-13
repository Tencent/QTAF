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
模块描述
'''
#2012-11-20  banana  - Created
#2013-01-15  pear  - 已经没有htmlcontrols和htmlcontrols2模块，修改测试用例
#2013-01-15  aaronlnai - 空构造函数抛出TypeError
import testbase
from testbase import logger
from testbase import context
import time
import threading
from testbase.testresult import EnumLogLevel

def _some_thread():
    logger.info('非测试线程打log, tid=%s' % threading.current_thread().ident)
    
class HelloTest(testbase.TestCase):
    '''测试示例
    '''
    owner = "banana"
    status = testbase.TestCase.EnumStatus.Ready
    timeout = 1
    priority = testbase.TestCase.EnumPriority.Normal
    
    def runTest(self):
        #-----------------------------
        self.startStep("测试")
        #-----------------------------
        self.assert_equal('断言失败', False, True)
        
    
    def get_extra_record(self):
        return {
            'screenshots':{
                'PC截图': __file__,
                '设备723982ef8截图':__file__,
            }
        }
        
class TimeoutTest(testbase.TestCase):
    '''超时示例
    '''
    owner = "olive"
    status = testbase.TestCase.EnumStatus.Ready
    timeout = 0.1
    priority = testbase.TestCase.EnumPriority.Normal
    
    def runTest(self):
        time.sleep(7)
        
class CrashTest(testbase.TestCase):
    '''发生Crash
    '''
    owner = "olive"
    status = testbase.TestCase.EnumStatus.Ready
    timeout = 0.1
    priority = testbase.TestCase.EnumPriority.Normal
    
    def runTest(self):
        context.current_testresult().log_record(EnumLogLevel.APPCRASH, "App Crash", attachments={'QQ12e6.dmp':__file__, 'QQ12e6.txt':__file__})
                
    
class App(object):
    def __init__(self, name):
        self._name = name
    @property
    def name(self):
        return self._name
    def get_creenshot(self):
        return __file__
    
    
class QT4iTest(testbase.TestCase):
    '''QT4i测试用例
    '''
    owner = "olive"
    status = testbase.TestCase.EnumStatus.Ready
    timeout = 0.1
    priority = testbase.TestCase.EnumPriority.Normal
    
    def initTest(self, testresult):
        super(QT4iTest,self).initTest(testresult)
        self._apps = []
        
    def runTest(self):
        self._apps.append(App("A"))
        self._apps.append(App("B"))
        raise RuntimeError("XXX")
    
    def get_extra_fail_record(self):
        attachments = {}
        for app in self._apps:
            attachments[app.name+'的截图'] = app.get_creenshot()
        return {},attachments
    

class ExtraInfoTest(testbase.TestCase):
    '''带test_extra_info_def的用例
    '''
    owner = "olive"
    status = testbase.TestCase.EnumStatus.Ready
    timeout = 1
    priority = testbase.TestCase.EnumPriority.Normal
    dev_owner = "olive"
    
    test_extra_info_def = [
        ("dev_owner", "开发负责人")
    ]
    
    def runTest(self):
        pass
    
if __name__ == '__main__':
#     HelloTest().run()
#     CrashTest().debug_run()
    QT4iTest().debug_run()