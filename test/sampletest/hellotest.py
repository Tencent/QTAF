# -*- coding: utf-8 -*-
'''
模块描述
'''

import testbase
from testbase import logger
from testbase import context
import time
import threading
from testbase.testresult import EnumLogLevel

def _some_thread():
    logger.info('非测试线程打log, tid=%s' % threading.current_thread().ident)

def _create_sampefile():
    import os
    from testbase.conf import settings
    res_dir = os.path.join(settings.PROJECT_ROOT,'resources')
    if not os.path.isdir(res_dir):
        os.mkdir(res_dir)
    with open(os.path.join(res_dir,'a.txt'),'w') as f:
        f.write('abc')
    with open(os.path.join(res_dir,'readme.txt.link'),'w') as f:
        f.write('/dist/qt4c/readme.txt')

def _test_getfile(resmgr):
    with open(resmgr.get_file('a.txt')) as f:
        print f.read()
    
    with open(resmgr.get_file('readme.txt')) as f:
            print f.read()
    
        
    
class HelloTest(testbase.TestCase):
    '''测试示例
    '''
    owner = "foo"
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
    owner = "foo"
    status = testbase.TestCase.EnumStatus.Ready
    timeout = 0.1
    priority = testbase.TestCase.EnumPriority.Normal
    
    def runTest(self):
        time.sleep(7)
        
class CrashTest(testbase.TestCase):
    '''发生Crash
    '''
    owner = "foo"
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
    owner = "foo"
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
    owner = "foo"
    status = testbase.TestCase.EnumStatus.Ready
    timeout = 1
    priority = testbase.TestCase.EnumPriority.Normal
    dev_owner = "foo"
    
    test_extra_info_def = [
        ("dev_owner", "开发负责人")
    ]
    
    def runTest(self):
        pass

class ResmgrTest(testbase.TestCase):
    '''资源管理相关接口测试
    '''
    owner = "foo"
    status = testbase.TestCase.EnumStatus.Ready
    timeout = 1
    priority = testbase.TestCase.EnumPriority.Normal
    dev_owner = "foo"
    _create_sampefile()
    
    def runTest(self):
        import testbase.resource as rs
        _test_getfile(self.test_resources)
        _test_getfile(rs)
            
    
if __name__ == '__main__':
#     HelloTest().run()
#     CrashTest().debug_run()
    ResmgrTest().debug_run()
