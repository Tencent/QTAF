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
测试用例基类模块
'''
from __future__ import absolute_import

import os
import sys
import re
import threading
import traceback
import collections
import types
import six

from testbase.assertion import AssertionRewriter
from testbase.util import Singleton, ThreadGroupLocal, ThreadGroupScope, smart_text, get_last_frame_stack
from testbase.testresult import EnumLogLevel, TestResultCollection
from testbase.conf import settings
from testbase.retry import Retry


# 后续需专门花时间去除TestCaseStatus和TestCasePriority这两个类
class TestCaseStatus(object):
    '''测试用例状态

    :attention: 此类将会被移除，请使用TestCase.EnumStatus
    '''
    Design, Implement, Review, Ready, Suspend = ('Design', 'Implement', 'Review', 'Ready', 'Suspend')


class TestCasePriority(object):
    '''测试用例优先级

    :attention: 此类将会被移除，请使用TestCase.EnumPriority
    '''
    BVT, High, Normal, Low = ('BVT', 'High', 'Normal', 'Low')


class Environ(six.with_metaclass(Singleton, dict)):
    """测试环境类

用法说明：
它是一个继承了字典类型的单实例类。使用时，需先实例化该类，如：
from testbase.testcase import Environ
env = Environ()
env保存了用例运行时的一些测试环境变量。

测试环境变量分为3个部分：

1、在测试执行时，env则存储了由测试计划定义的用例环境变量，使用方法如下::

    from testbase.testcase import Environ
    env = Environ()
    print(env_
    # 输出
    env = {
        'ASSERTTEST':'True',  #注意：这里key是全字母大写
    }

2、测试用例基类testbase.testcase.TestCase的构造函数中也实例化了Environ类（变量名为environ)，
并且，保存了当时执行用例类的类名和类说明，使用方法如下::

    #todo: 执行用例中使用evniron，用于打印用例名称和用例说明
    from testbase.testcase import TestCase
    class YourTest(TestCase):
        def runTest(self):
            print(self.environ['TestName'])
            print(self.environ['TestDoc'])

3、Environ还可以用于设置自定义的环境变量，使用方法如下::

    from testbase.testcase import Environ
    env = Environ()
    env['YourEnvKey'] = "EnvValue"
    print(env['YourEnvKey'])

    """

    def __init__(self):
        """构造函数。判断系统环境变量中是否存在由测试计划中传入的环境变量，有则加载。

        """
        super(Environ, self).__init__()
        for key in os.environ.keys():
            if key.startswith("QTAF_") and key[5:]:
                self[key[5:]] = os.environ[key]


class TestCaseType(type):
    '''测试用例元类型
    '''
    forbid_overload_methods = ["__init__"]

    def __new__(cls, name, bases, attrs):
        super_new = super(TestCaseType, cls).__new__
        parents = [b for b in bases if isinstance(b, TestCaseType)]
        # ensure only apply for subclass of TestCase
        if not parents:
            return super_new(cls, name, bases, attrs)

        for it in cls.forbid_overload_methods:
            if it in attrs.keys():
                raise RuntimeError("不允许%s重载函数: %s" % (cls.__name__, it))

        base_tags_set = set()
        tags = attrs.pop("tags") if "tags" in attrs else set()
        if isinstance(tags, six.string_types):
            tags = [tags]
        tags_set = set(tags)
        for b in bases:
            print(b)
            if issubclass(b, TestCase) and hasattr(b, "tags"):
                base_tags_set |= b.tags
        if "__module__" in attrs:
            mod = sys.modules[attrs["__module__"]]
            if hasattr(mod, "__qtaf_tags__"):
                mod_tags = mod.__qtaf_tags__
                if isinstance(mod_tags, six.string_types):
                    mod_tags = [mod_tags]
                base_tags_set |= set(mod_tags)
        tags_set |= base_tags_set

        attrs["tags"] = tags_set
        attrs["base_tags"] = base_tags_set
        return super_new(cls, name, bases, attrs)


@six.add_metaclass(TestCaseType)
class TestCase(object):
    '''测试用例基类

            所有测试用例都最终从此基类继承。测试用例的测试脚本主要实现在"runTest()"中，

           而当用例需要初始化和清理测试环境时则分别重写"preTest()"和"postTest()"函数。
    '''
    test_extra_info_def = []  # 自定义字段

    class EnumStatus(object):
        '''测试用例状态枚举类

        :attention: 如果因为特殊原因需要暂时屏蔽某个用例的任务执行（比如有功能缺陷从而导致执行失败），
                                                     则可以先置为该字段为Suspend,等到可用的时候再将该字段置为Ready

        '''
        Design, Implement, Review, Ready, Suspend = (TestCaseStatus.Design,
                                                     TestCaseStatus.Implement,
                                                     TestCaseStatus.Review,
                                                     TestCaseStatus.Ready,
                                                     TestCaseStatus.Suspend)

    class EnumPriority(object):
        '''测试用例优先级枚举类
        '''
        BVT, High, Normal, Low = (TestCasePriority.BVT,
                                  TestCasePriority.High,
                                  TestCasePriority.Normal,
                                  TestCasePriority.Low)

    owner = None
    priority = None
    status = None
    timeout = None

    ATTRIB_OVERWRITE_WHITELIST = ["priority", "status", "owner", "timeout", "tags", "__doc__"]

    def __init__(self, testdata=None, testdataname=None, attrs=None):
        '''构造函数

        :param testdata: 测试数据
        :type testdata: object
        :param testdataname: 测试数据标识
        :type testdataname: str
        :param attrs: 重载的测试用例属性
        :type attrs: dict
        '''
        self.__casedata = testdata
        self.__testdataname = testdataname
        self.__environ = Environ()
        self.__testresult = None
        self.__resmgr_session = None
        self.__resmgr = None
        self.__test_doc = None

        if attrs:
            for k, v in attrs.items():
                if k in self.ATTRIB_OVERWRITE_WHITELIST:
                    if k == "__doc__":
                        self.__test_doc = v
                    elif k == "tags":
                        if isinstance(v, six.string_types):
                            v = [v]
                        self.tags = self.base_tags | set(v)
                    else:
                        setattr(self, k, v)

    @property
    def casedata(self):
        '''测试数据

        :rtype: list
        '''
        return self.__casedata

    @property
    def casedataname(self):
        '''测试数据标识

        :rtype: str
        '''
        return self.__testdataname

    @property
    def environ(self):
        '''环境变量

        :rtype: Environ
        '''
        return self.__environ

    @property
    def test_result(self):
        '''对应的测试结果

        :rtype: TestResult
        '''
        return self.__testresult

    @property
    def test_dir(self):
        '''测试用例执行的临时目录

        :rtype: str
        '''
        return os.path.abspath(os.getcwd())

    @property
    def test_class_name(self):
        '''返回测试用例名字（不同测试用例的名字不同）

        :rtype: str
        '''
        cls = type(self)
        if cls.__module__ == '__main__':
            type_name = smart_text(cls.__name__)
        else:
            type_name = smart_text(cls.__module__ + '.' + cls.__name__)
        return type_name

    @property
    def test_name(self):
        '''返回测试用例实例的名字

        :rtype: str
        '''
        if self.casedataname is not None:
            casedataname = smart_text(self.casedataname)
            return '%s/%s' % (self.test_class_name, casedataname)
        else:
            return self.test_class_name

    @property
    def test_doc(self):
        '''测试用例说明

        :rtype: str
        '''
        if self.__test_doc:
            return self.__test_doc
        desc = self.__class__.__doc__
#        if desc:
#            desc = cgi.escape(desc)
        if isinstance(desc, six.text_type):
            desc = re.sub('^\s*', '', desc)
            desc = re.sub('\s*$', '', desc)
        return desc

    @property
    def test_extra_info(self):
        '''测试用例额外信息
        '''
        info = {}
        for name, _ in self.test_extra_info_def:
            info[name] = getattr(self, name, None)
        return info

    @property
    def test_resmgr(self):
        '''资源管理器
        '''
        return self.__resmgr

    @test_resmgr.setter
    def test_resmgr(self, resmgr):
        self.__resmgr = resmgr

    @property
    def test_resources(self):
        '''资源管理使用接口
        '''
        if not self.__resmgr_session:
            self.__resmgr_session = self.__resmgr.create_session(self)
        return self.__resmgr_session

    def init_test(self, testresult):
        '''初始化测试用例。慎用此函数，尽量将初始化放到preTest里。

        :param testresult: 测试结果
        :type testresult: TestResult
        '''
        self.__testresult = testresult

    def pre_test(self):
        '''测试环境初始化
        '''
        pass

    def run_test(self):
        '''运行测试用例
        '''
        raise NotImplementedError("请在%s类中实现runTest方法" % type(self))

    def post_test(self):
        '''测试环境清理
        '''
        pass

    def clean_test(self):
        '''测试用例反初始化。慎用此函数，尽量将清理放到postTest里。
        '''
        if self.__resmgr_session:
            self.test_resources.destroy()

    def start_step(self, stepinfo):
        '''开始执行一个测试步骤

        :param stepinfo: 步骤描述
        :type stepinfo: str
        '''
        if not isinstance(stepinfo, six.text_type):
            stepinfo = str(stepinfo)
        self.__testresult.begin_step(stepinfo)

    def log_info(self, info):
        '''Log一条信息

        :type info: string
        :param info: 要Log的信息
        '''
        if not isinstance(info, six.text_type):
            info = str(info)
        self.__testresult.info(info)

    def fail(self, message):
        '''测试用例失败

        :type message: string
        :param message: 要Log的信息
        '''
        if not isinstance(message, six.text_type):
            message = str(message)
        self.__testresult.error(message)

    def __record_assert_failed(self, message, actual, expect):
        '''记录Assert失败信息

        :param message: 提示信息
        :type message: string
        :param actual: 实际值
        :type actual: string
        :param expect: 期望值
        :type expect: string
        '''
        # 得到上一个函数调用帧所在的文件路径，行号，函数名
        stack = get_last_frame_stack(3)
        msg = "检查点不通过\n%s%s\n期望值：%s%s\n实际值：%s%s" % (smart_text(stack), smart_text(message),
                                                    expect.__class__, expect,
                                                    actual.__class__, actual)
        self.__testresult.log_record(EnumLogLevel.ASSERT, msg)

    def _log_assert_failed(self, message, back_count=2):
        """记录断言失败的信息
        """
        stack = get_last_frame_stack(back_count)
        msg = "检查点不通过\n%s%s\n" % (smart_text(stack), smart_text(message))
        self.__testresult.log_record(EnumLogLevel.ASSERT, msg)
        if not settings.get("QTAF_ASSERT_CONTINUE", True):
            raise RuntimeError("testcase assert failed:%s" % message)

    def assert_(self, message, value):
        """测试断言，如果value的值不为真，则用例失败，输出对应信息

        :param message:断言失败时的提示消息
        :type  message: str
        :param value:用于判断的值
        :type  value: bool或
        """
        if not value:
            self._log_assert_failed(message, 3)

    def assert_equal(self, message, actual, expect=True):
        '''检查实际值和期望值是否相等，不能则测试用例失败

       :param message: 检查信息
       :param actual: 实际值
       :param expect: 期望值(默认：True)
       :return: True or False
        '''
        if isinstance(actual, six.string_types):
            actual = smart_text(actual)
        if isinstance(expect, six.string_types):
            expect = smart_text(expect)
        if expect != actual:
            self.__record_assert_failed(message, actual, expect)
            return False
        else:
            return True

    def assert_match(self, message, actual, expect):
        '''检查actual和expect是否模式匹配，不匹配则记录一个检查失败

        :type message: string
        :param message: 失败时记录的消息
        :type actual: string
        :param actual: 需要匹配的字符串
        :type expect: string
        :param expect: 要匹配的正则表达式
        :return: 匹配成果
        '''
        if isinstance(actual, six.string_types):
            actual = smart_text(actual)
        if isinstance(expect, six.string_types):
            expect = smart_text(expect)
        if re.search(expect, actual):
            return True
        else:
            self.__record_assert_failed(message, actual, expect)
            return False

    def wait_for_equal(self, message, obj, prop_name, expected, timeout=10, interval=0.5):
        '''每隔interval检查obj.prop_name是否和expected相等，如果在timeout时间内都不相等，则测试用例失败

        :param message: 失败时的输出信息
        :param obj: 需要检查的对象
        :type prop_name: string
        :param prop_name: 需要检查的对象的属性名，支持多层属性
        :param expected: 期望的obj.prop_name值
        :param timeout: 超时秒数
        :param interval: 重试间隔秒数
        :return: True or False
        '''
        for _ in Retry(timeout=timeout, interval=interval, raise_error=False):
            actual = getattr(obj, prop_name)
            if actual == expected:
                return True
        else:
            self.__record_assert_failed(message, getattr(obj, prop_name), expected)
            return False

    def wait_for_match(self, message, obj, prop_name, expected, timeout=10, interval=0.5):
        '''每隔interval检查obj.prop_name是否和正则表达式expected是否匹配，如果在timeout时间内都不相等，则测试用例失败

        :param message: 失败时的输出信息
        :param obj: 需要检查的对象
        :type prop_name: string
        :param prop_name: 需要检查的对象的属性名, obj.prop_name返回字符串
        :param expected: 需要匹配的正则表达式
        :param timeout: 超时秒数
        :param interval: 重试间隔秒数
        :return: True or False
        '''
        for _ in Retry(timeout=timeout, interval=interval, raise_error=False):
            actual = getattr(obj, prop_name)
            if re.match(expected, actual, re.I):
                return True
        else:
            self.__record_assert_failed(message, getattr(obj, prop_name), expected)
            return False

    def get_extra_fail_record(self):
        '''当错误发生时，获取需要额外添加的日志记录和附件信息

        :rtype: dict,dict - 日志记录，附件信息
        '''
        return {}, {}

    def debug_run(self):
        '''本地调试测试用例
        '''
        from testbase import datadrive
        from testbase.runner import TestRunner
        from testbase.report import StreamTestReport, EmptyTestReport
        from testbase.testresult import StreamResult

        test_cls = type(self)
        if datadrive.is_datadrive(test_cls) or settings.DATA_DRIVE:  # datadrvie
            if self.casedataname is not None:
                tests = datadrive.load_datadrive_tests(test_cls, self.casedataname)
                report = EmptyTestReport(lambda tc: StreamResult())
            else:
                tests = datadrive.load_datadrive_tests(test_cls)
                report = StreamTestReport(output_testresult=True, output_summary=True)
        else:
            tests = [self]
            report = EmptyTestReport(lambda tc: StreamResult())
        runner = TestRunner(report)
        return runner.run(tests)

    def debug_run_one(self, name=None):
        '''本地调试测试用例，给数据驱动的用例使用，只执行一个用例

        :param name: 测试数据名称，如果不指定，执行第一个数据的用例
        '''
        from testbase import datadrive
        from testbase.runner import TestRunner
        from testbase.report import EmptyTestReport
        from testbase.testresult import StreamResult

        test_cls = type(self)
        if not datadrive.is_datadrive(test_cls) and not settings.DATA_DRIVE:  # non-datadrive
            raise RuntimeError("非数据驱动用例，请使用debug_run进行调试")
        if name:
            tests = datadrive.load_datadrive_tests(test_cls, name)
        else:
            tests = datadrive.load_datadrive_tests(test_cls)
            tests = tests[:1]
        runner = TestRunner(EmptyTestReport(lambda tc: StreamResult()))
        return runner.run(tests)

    #----------------------------------------------------
    #    以下为兼容老的代码风格的接口，新代码请勿再使用
    #----------------------------------------------------

    def run(self):
        '''本地调试测试用例
        '''
        self.debug_run()

        sys.stderr.write('============================================================\n')
        sys.stderr.write('注意：TestCase.run接口准备废弃，建议改用为.debug_run接口，例如：\n')
        sys.stderr.write('if __name__ == \'__main__\'\n')
        sys.stderr.write('    %s().debug_run()\n' % type(self).__name__)
        sys.stderr.write('============================================================\n')

    initTest = init_test
    preTest = pre_test
    runTest = run_test
    postTest = post_test
    cleanTest = clean_test
    startStep = start_step

    assertEqual = assert_equal
    assertMatch = assert_match
    waitForEqual = wait_for_equal
    waitForMatch = wait_for_match

    TestClassName = test_class_name
    TestName = test_name
    TestDoc = test_doc

    logInfo = log_info


class ITestCaseRunner(object):
    '''测试用例执行器接口定义
    '''

    def run(self, testcase, testresult_factory):
        '''执行一个测试用例

        :param testcase: 执行的测试用例
        :type testcase: TestCase
        :param testresult_factory: 测试结果工厂
        :type testresult_factory: ITestResultFactory

        :return TestResult/TestResultCollection - 测试结果
        '''
        raise NotImplementedError()


class TestCaseRunner(ITestCaseRunner):
    '''负责执行一个测试用例

    如果一个测试用例没有指定case_runner类变量，则默认都使用TestCaseRunner来执行这个用例。
    测试用例可以自定义和TestCaseRunner接口兼容的runner类，并设置case_runner类变量来实现
    自定义一个测试用例的执行逻辑，以下是TestCaseRunner的接口定义
    '''

    CLEANUP_TIMEOUT = 300

    def __init__(self):
        '''构造函数
        '''
        self._lock = threading.Lock()
        self._stop_run = False
        self._error = None

    def _rewrite_assert(self, cls):
        if not settings.get("QTAF_REWRITE_ASSERT", True) or cls == TestCase:
            return
        rewriter = AssertionRewriter()
        for key in dir(cls):
            item = getattr(cls, key)
            if isinstance(item, (types.MethodType, types.FunctionType)):
                rewriter.rewrite(item)

    def _walk_bases(self, test_case):
        '''遍历所有基类，进行相应的处理
        '''
        cur_cls = type(test_case)
        self._single_methods_mapping(cur_cls)
        self._rewrite_assert(cur_cls)
        bases = set(cur_cls.__bases__)
        while bases:
            new_bases = set()
            for base_cls in bases:
                self._single_methods_mapping(base_cls)
                self._rewrite_assert(cur_cls)
                new_bases = new_bases.union(set(base_cls.__bases__))
            bases = new_bases

    def _single_methods_mapping(self, cls_type):
        '''针对单个类进行方法映射
        '''
        if object == cls_type:
            return
        case_mothods = [
            ("initTest", "init_test"),
            ("preTest", "pre_test"),
            ("runTest", "run_test"),
            ("postTest", "post_test"),
            ("cleanTest", "clean_test")
        ]
        cls_dict = cls_type.__dict__
        for pairs in case_mothods:
            if pairs[0] in cls_dict and not pairs[1] in cls_dict:
                setattr(cls_type, pairs[1], cls_dict[pairs[0]])
                self._testresult.warning("严重警告：类型%s应当定义方法%s，方法%s已被废弃，请勿使用" % (cls_type.__name__, pairs[1], pairs[0]))
            elif pairs[0] not in cls_dict and pairs[1] in cls_dict:
                setattr(cls_type, pairs[0], cls_dict[pairs[1]])
            elif pairs[0] in cls_dict and pairs[1] in cls_dict:
                if cls_dict[pairs[0]] != cls_dict[pairs[1]]:
                    raise RuntimeError('类型%s不允许同时独立定义"%s"和"%s"' % (cls_type, pairs[0], pairs[1]))

    def _check_testcase(self, testcase):
        '''检查测试用例

        :param testcase: 测试用例
        :type testcase: TestCase
        :returns boolean, string - 检测是否通过，错误消息
        '''
        attrnames = ['owner', 'priority', 'status', 'timeout']
        tcattrs = {}
        for attr in attrnames:
            attrvalue = getattr(self._testcase, attr)
            if isinstance(attrvalue, six.text_type):
                if attrvalue.strip(" ") == "":
                    attrvalue = None
            tcattrs[attr] = attrvalue
        tcattrs['testname'] = self._testcase.test_name
        if None in tcattrs.values():
            raise RuntimeError("测试用例需要设置以下类属性：%s" % attrnames)
        if not self._testcase.test_doc:
            raise RuntimeError("测试用例的描述不能为空，请加上描述！")

        self._walk_bases(testcase)

    def _thread_run(self):
        '''测试用例线程过程
        '''
        #                     函数时发生了死锁，故注释掉。观察一段时间，看修改是否会影响测试。
        try:
            try:
                self._check_testcase(self._testcase)
            except RuntimeError as e:
                self._testresult.error(e.args[0])
                return

            while True:
                with self._lock:
                    if len(self._subtasks) == 0 or self._stop_run:
                        break
                    it = self._subtasks.popleft()

                if isinstance(it, str):
                    try:
                        if it in ['init_test', 'initTest']:
                            getattr(self._testcase, it)(self._testresult)
                        else:
                            getattr(self._testcase, it)()
                    except:
                        self._testresult.exception('%s执行失败' % it)
                else:
                    it()

        except:
            self._error = traceback.format_exc()

    def _thread_cleanup(self):
        '''清理线程
        '''
        try:
            while True:
                with self._lock:
                    if len(self._subtasks) == 0:
                        break
                    it = self._subtasks.popleft()
                    if it in ['initTest', 'preTest', 'runTest', 'init_test', 'pre_test', 'run_test']:
                        continue

                if isinstance(it, str):
                    try:
                        getattr(self._testcase, it)()
                    except:
                        self._testresult.exception('用例超时时%s执行失败' % it)
                else:
                    it()
        except:
            self._error = traceback.format_exc()

    def setup(self, testcase, testresult):
        '''测试执行初始化

        :param testcase: 执行的测试用例
        :type testcase: TestCase
        :param testresult: 测试用例结果
        :type testresult: TestResult
        '''
        pass

    def teardown(self, testcase, testresult):
        '''测试执行清理

        :param testcase: 执行的测试用例
        :type testcase: TestCase
        :param testresult: 测试用例结果
        :type testresult: TestResult
        '''
        pass

    def run(self, testcase, testresult_factory):
        '''执行一个测试用例

        :param testcase: 执行的测试用例
        :type testcase: TestCase
        :param testresult_factory: 测试结果工厂
        :type testresult_factory: ITestResultFactory
        :rtype: TestResult/TestResultCollection - 测试结果
        '''
        #                       临时方案是disable gc后kill掉程序，在enable gc。后续这里
        #                        需要重新考虑已独立进程来执行测试用例。

        self._stop_run = False
        self._testcase = testcase
        self._testresult = testresult_factory.create(testcase)
        self._subtasks = collections.deque(['init_test', 'pre_test', 'run_test', 'post_test', 'clean_test'])

        with ThreadGroupScope('%s:%s' % (self._testcase.test_name, id(self))):

            ThreadGroupLocal().testcase = self._testcase
            ThreadGroupLocal().testresult = self._testresult

            self._testresult.begin_test(self._testcase)

            self.setup(self._testcase, self._testresult)

            if isinstance(self._testcase.timeout, int) or isinstance(self._testcase.timeout, float):
                timeout = self._testcase.timeout * 60
            else:
                timeout = 60

            test_thread = threading.Thread(target=self._thread_run)
            test_thread.daemon = True
            test_thread.start()
            test_thread.join(timeout)
            if test_thread.is_alive():
                self._stop_run = True
                try:
                    thread_traceback = self._get_current_traceback(test_thread)
                except:
                    self._testresult.log_record(EnumLogLevel.TESTTIMEOUT, '测试用例执行超时')
                else:
                    self._testresult.log_record(EnumLogLevel.TESTTIMEOUT, '测试用例执行超时，抓取测试线程当前堆栈',
                                                dict(traceback=thread_traceback))

                # 启动线程执行可能未执行的postTest和cleanTest
                cleanup_thread = threading.Thread(target=self._thread_cleanup)
                cleanup_thread.daemon = True
                cleanup_thread.start()
                cleanup_thread.join(self.CLEANUP_TIMEOUT)
                if cleanup_thread.is_alive():
                    try:
                        thread_traceback = self._get_current_traceback(cleanup_thread)
                    except:
                        self._testresult.log_record(EnumLogLevel.TESTTIMEOUT, '测试用例执行超时时清理超时')
                    else:
                        self._testresult.log_record(EnumLogLevel.TESTTIMEOUT, '测试用例执行超时时清理超时，抓取清理线程当前堆栈',
                                                    dict(traceback=thread_traceback))
                else:
                    if self._error:
                        raise RuntimeError("用例执行线程异常：\n%s" % smart_text(self._error))
            else:
                if self._error:
                    raise RuntimeError("用例执行线程异常：\n%s" % smart_text(self._error))

            self.teardown(self._testcase, self._testresult)

            self._testresult.end_test()

        # gc.enable()
        # gc.collect()
        return self._testresult

    def _get_current_traceback(self, thread):
        '''获取用例线程的当前的堆栈

        :param thread: 要获取堆栈的线程
        :type thread: Thread
        '''
        for thread_id, stack in sys._current_frames().items():
            if thread_id != thread.ident:
                continue
            tb = "Traceback ( thread-%d possibly hold at ):\n" % thread_id
            for filename, lineno, name, line in traceback.extract_stack(stack):
                tb += '  File: "%s", line %d, in %s\n' % (filename, lineno, name)
                if line:
                    tb += "    %s\n" % (line.strip())
            return tb
        else:
            raise RuntimeError("thread not found")


class RepeatTestCaseRunner(ITestCaseRunner):
    '''重复执行的用例执行器

    可以通过设置测试用例的类属性为此runner实例来实现指定测试用例
    执行多次。测试用例执行时可以访问成员变量iteration来判断当前是
    第几次执行。

    使用示例如下::

        class HelloRepeatTest(TestCase):
            '示例用例'
            case_runner = RepeatTestCaseRunner()
            owner = "foo"
            timeout = 1
            status = TestCase.EnumStatus.Ready
            priority = TestCase.EnumPriority.Normal

            def run_test(self):
                self.log_info("第%s次执行测试"%self.iteration)

    '''

    def __init__(self, case_runner_class=None):
        '''指定执行一个用例的CaseRunner类，不指定则为TestCaseRunner类
        '''
        if case_runner_class is None:
            case_runner_class = TestCaseRunner
        self._case_runner_class = case_runner_class

    def run(self, testcase, testresult_factory):
        '''执行一个测试用例

        :param testcase: 执行的测试用例
        :type testcase: TestCase
        :param testresult_factory: 测试结果工厂
        :type testresult_factory: ITestResultFactory

        :returns : 测试结果
        :rtype TestResult/TestResultCollection - 测试结果
        '''
        passed = True
        if not hasattr(testcase, "repeat"):
            passed = False
            err_msg = "使用RepeatTestCaseRunner的测试用例需要设置类属性：repeat"
        elif testcase.repeat <= 0:
            passed = False
            err_msg = "使用RepeatTestCaseRunner的测试用例的类属性'repeat'必须大于0"
        if not passed:
            with ThreadGroupScope('%s:%s' % (testcase.test_name, id(self))):
                result = testresult_factory.create(testcase)
                ThreadGroupLocal().testcase = testcase
                ThreadGroupLocal().testresult = result
                result.begin_test(testcase)
                result.error(err_msg)
                result.end_test()
                return result

        passed = True
        results = []
        for i in range(testcase.repeat):
            testcase.iteration = i
            case_result = self._case_runner_class().run(testcase, testresult_factory)
            passed &= case_result.passed
            results.append(case_result)
            if not passed:
                break
        return TestResultCollection(results, passed)


class SeqTestCaseRunner(ITestCaseRunner):
    '''顺序执行的用例的执行器
    '''

    def run(self, testsuite, testresult_factory):
        '''执行一个顺序执行的测试用例套

        :param testsuite: 执行的测试用例套
        :type testsuite: SeqTestSuite
        :param testresult_factory: 测试结果工厂
        :type testresult_factory: ITestResultFactory

        :return TestResult/TestResultCollection - 测试结果
        '''
        passed = True
        results = []
        for it in testsuite:
            runner = getattr(it, 'case_runner', TestCaseRunner())
            case_result = runner.run(it, testresult_factory)
            passed &= case_result.passed
            results.append(case_result)
            if not passed:
                break
        return TestResultCollection(results, passed)


class TestSuite(object):
    '''测试用例套
    '''

    @property
    def suite_class_name(self):
        '''测试套类名称
        '''
        cls = type(self)
        if cls.__module__ == '__main__':
            type_name = cls.__name__
        else:
            type_name = (cls.__module__ + '.' + cls.__name__)
        return type_name

    def dumps(self):
        '''序列化
        '''
        raise NotImplementedError()

    def loads(self, buf):
        '''反序列化
        '''
        raise NotImplementedError()


class SeqTestSuite(TestSuite):
    '''顺序执行的测试用例套
    '''
    case_runner = SeqTestCaseRunner()

    def __init__(self, testcases):
        '''构造函数

        :param testcases: 测试用例列表
        :type testcases: list
        :param name: 测试用例名
        :type name: string
        '''
        self._testcases = testcases
        self._resmgr = None

    def __iter__(self):
        for it in self._testcases:
            yield it

    def __len__(self):
        return len(self._testcases)

    def __repr__(self):
        return '<SeqTestSuite module:%s>' % self.test_class_name

    @property
    def test_class_name(self):
        '''返回测试用例名字（不同测试用例的名字不同）

        :rtype: str
        '''
        cls = type(self._testcases[0])
        return cls.__module__

    @property
    def test_name(self):
        '''返回测试用例实例的名字

        :rtype: str
        '''
        cls = type(self._testcases[0])
        return cls.__module__

    @property
    def test_doc(self):
        '''测试用例说明

        :rtype: str
        '''
        cls = type(self._testcases[0])
        desc = cls.__module__.__doc__
        if isinstance(desc, six.text_type):
            desc = re.sub('^\s*', '', desc)
            desc = re.sub('\s*$', '', desc)
        return desc

    @property
    def test_result(self):
        '''将最后一个执行的用例结果，作为Suite的结果
        '''
        result = None
        for testcae in self._testcases:
            if testcae.test_result:
                result = testcae.test_result
            else:
                break
        return result

    @property
    def test_resmgr(self):
        '''资源管理器
        '''
        return self._resmgr

    @test_resmgr.setter
    def test_resmgr(self, resmgr):
        self._resmgr = resmgr
        for it in self._testcases:
            it.test_resmgr = resmgr

    def dumps(self):
        '''序列化
        '''
        from testbase import serialization
        return [serialization.dumps(it) for it in self._testcases]

    def loads(self, buf):
        '''反序列化
        '''
        from testbase import serialization
        self._testcases = [serialization.loads(it) for it in buf]


def debug_run_all():
    '''调试执行当前脚本的全部用例
    '''
    from testbase.loader import TestLoader
    from testbase.runner import TestRunner
    from testbase.report import StreamTestReport
    tests = TestLoader().load("__main__")
    runner = TestRunner(StreamTestReport(output_testresult=True, output_summary=True))
    runner.run(tests)
