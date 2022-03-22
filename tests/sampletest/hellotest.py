# -*- coding: utf-8 -*-
'''
模块描述
'''

import os
import sys
import threading
import time
import testbase
from testbase import logger
from testbase import context
from testbase.datadrive import DataDrive
from testbase.testresult import EnumLogLevel
from testbase.util import codecs_open

def _some_thread():
    logger.info('非测试线程打log, tid=%s' % threading.current_thread().ident)

class HelloTest(testbase.TestCase):
    '''测试示例
    '''
    owner = "foo"
    status = testbase.TestCase.EnumStatus.Ready
    timeout = 1
    priority = testbase.TestCase.EnumPriority.Normal

    def run_test(self):
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
    timeout = 0.01
    priority = testbase.TestCase.EnumPriority.Normal

    def run_test(self):
        time.sleep(2)

class CrashTest(testbase.TestCase):
    '''发生Crash
    '''
    owner = "foo"
    status = testbase.TestCase.EnumStatus.Ready
    timeout = 1
    priority = testbase.TestCase.EnumPriority.Normal

    def run_test(self):
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

    def init_test(self, testresult):
        super(QT4iTest,self).initTest(testresult)
        self._apps = []

    def run_test(self):
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

    def run_test(self):
        pass

class ResmgrTest(testbase.TestCase):
    '''资源管理相关接口测试
    '''
    owner = "foo"
    status = testbase.TestCase.EnumStatus.Ready
    timeout = 1
    priority = testbase.TestCase.EnumPriority.Normal
    dev_owner = "foo"

    def pre_test(self):
        from testbase.conf import settings
        self.resource_root = os.path.join(settings.PROJECT_ROOT,'resources')
        if not os.path.isdir(self.resource_root):
            os.mkdir(self.resource_root)
        self.file_name = "a_%s%s_resmgr.txt" % (sys.version_info[0], sys.version_info[1])
        self.link_file_name = "readme_%s%s.txt.link" % (sys.version_info[0], sys.version_info[1])
        with codecs_open(os.path.join(self.resource_root, self.file_name), 'w', encoding="utf-8") as f:
            f.write('abc')
        with codecs_open(os.path.join(self.resource_root, self.link_file_name), 'w', encoding="utf-8") as f:
            f.write(os.path.join(self.resource_root, self.file_name))

    def _test_getfile(self, resmgr):
        with codecs_open(resmgr.get_file(self.file_name), encoding="utf-8") as f:
            print(f.read())

        with codecs_open(resmgr.get_file(self.link_file_name[:-5]), encoding="utf-8") as f:
            print(f.read())

    def run_test(self):
        import testbase.resource as rs
        self._test_getfile(self.test_resources)
        self._test_getfile(rs)

    def post_test(self):
        for file_name in [self.file_name, self.link_file_name]:
            os.remove(os.path.join(self.resource_root, file_name))

@DataDrive({"中国":"中国", "xxx":"xxx"})
class DataDriveCase(testbase.TestCase):
    '''xxx
    '''
    owner='xxx'
    timeout=5
    priority=testbase.TestCase.EnumPriority.High
    status=testbase.TestCase.EnumStatus.Ready

    def run_test(self):
        pass

class FailedCase(testbase.TestCase):
    '''xxx
    '''
    owner = 'xxx'
    timeout = 5
    priority = testbase.TestCase.EnumPriority.High
    status = testbase.TestCase.EnumStatus.Ready

    def run_test(self):
        self.assert_equal("assert failed", False, True)

class PassedCase(testbase.TestCase):
    '''xxx
    '''
    owner = 'xxx'
    timeout = 5
    priority = testbase.TestCase.EnumPriority.High
    status = testbase.TestCase.EnumStatus.Ready

    def run_test(self):
        self.assert_equal("assert success", True, True)

class TestProperty(object):
    pass

def test_func():
    return True

class ExtraPropertyTestBase(testbase.TestCase):
    base_property_str = '123'
    base_property_int = 123
    base_property_type = TestProperty
    base_property_class = TestProperty()
    base_property_func_value = test_func()
    base_property_bool = True
    base_property_dict = {'a': 'a1_test'}

class ExtraPropertyTest(ExtraPropertyTestBase):
    '''测试extra property的用例
    '''
    owner = "foo"
    status = testbase.TestCase.EnumStatus.Ready
    timeout = 1
    priority = testbase.TestCase.EnumPriority.Normal
    property_str = '123'
    property_int = 123
    property_type = TestProperty
    property_class = TestProperty()
    property_func_value = test_func()
    property_bool = True
    property_dict = {'b': 'b1_test'}

    def run_test(self):
        self.run_property_str = '123'
        self.run_property_int = 123
        self.run_property_type = TestProperty
        self.run_property_class = TestProperty()

    @property
    def property_variable(self):
        return self.base_property_dict['b']

    @property
    def property_variable2(self):
        return self.property_dict['b']

    @property
    def property_exception(self):
        raise RuntimeError

if __name__ == '__main__':
#     HelloTest().run()
#     x = CrashTest().debug_run()
    ResmgrTest().debug_run()
#     TimeoutTest().debug_run()
