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
"""
测试套基类模块
"""
from __future__ import absolute_import

import collections
import threading
import re
import traceback

import six

from testbase.testcase import ITestCaseRunner, TestCase, TestCaseRunner
from testbase.testresult import StreamResult, TestResultCollection
from testbase.util import ThreadGroupLocal, ThreadGroupScope


class SeqTestCaseRunner(ITestCaseRunner):
    """顺序执行的用例的执行器"""

    def run(self, testsuite, testresult_factory):
        """执行一个顺序执行的测试用例套

        :param testsuite: 执行的测试用例套
        :type testsuite: SeqTestSuite
        :param testresult_factory: 测试结果工厂
        :type testresult_factory: ITestResultFactory

        :return TestResult/TestResultCollection - 测试结果
        """
        passed = True
        results = []
        for it in testsuite:
            runner = getattr(it, "case_runner", TestCaseRunner())
            case_result = runner.run(it, testresult_factory)
            passed &= case_result.passed
            results.append(case_result)
            if not passed:
                break
        return TestResultCollection(results, passed)


class TestSuiteBase(object):
    """测试套基类"""

    @property
    def suite_class_name(self):
        """测试套类名称"""
        cls = type(self)
        if cls.__module__ == "__main__":
            type_name = cls.__name__
        else:
            type_name = cls.__module__ + "." + cls.__name__
        return type_name

    def dumps(self):
        """序列化"""
        raise NotImplementedError()

    def loads(self, buf):
        """反序列化"""
        raise NotImplementedError()


class SeqTestSuite(TestSuiteBase):
    """顺序执行的测试用例套"""

    case_runner = SeqTestCaseRunner()

    def __init__(self, testcases):
        """构造函数

        :param testcases: 测试用例列表
        :type testcases: list
        :param name: 测试用例名
        :type name: string
        """
        self._testcases = testcases
        self._resmgr = None
        self.__share_data_mgr = None

    def __iter__(self):
        for it in self._testcases:
            yield it

    def __len__(self):
        return len(self._testcases)

    def __repr__(self):
        return "<SeqTestSuite module:%s>" % self.test_class_name

    @property
    def test_class_name(self):
        """返回测试用例名字（不同测试用例的名字不同）

        :rtype: str
        """
        cls = type(self._testcases[0])
        return cls.__module__

    @property
    def test_name(self):
        """返回测试用例实例的名字

        :rtype: str
        """
        cls = type(self._testcases[0])
        return cls.__module__

    @property
    def test_doc(self):
        """测试用例说明

        :rtype: str
        """
        cls = type(self._testcases[0])
        desc = cls.__module__.__doc__
        if isinstance(desc, six.text_type):
            desc = re.sub("^\s*", "", desc)
            desc = re.sub("\s*$", "", desc)
        return desc

    @property
    def test_result(self):
        """将最后一个执行的用例结果，作为Suite的结果"""
        result = None
        for testcae in self._testcases:
            if testcae.test_result:
                result = testcae.test_result
            else:
                break
        return result

    @property
    def test_resmgr(self):
        """资源管理器"""
        return self._resmgr

    @test_resmgr.setter
    def test_resmgr(self, resmgr):
        self._resmgr = resmgr
        for it in self._testcases:
            it.test_resmgr = resmgr

    @property
    def share_data_mgr(self):
        """共享数据管理器"""
        return self.__share_data_mgr

    @share_data_mgr.setter
    def share_data_mgr(self, share_data_mgr):
        self.__share_data_mgr = share_data_mgr
        for it in self._testcases:
            it._share_data_mgr = share_data_mgr

    def dumps(self):
        """序列化"""
        from testbase import serialization

        return [serialization.dumps(it) for it in self._testcases]

    def loads(self, buf):
        """反序列化"""
        from testbase import serialization

        self._testcases = [serialization.loads(it) for it in buf]


class TestSuiteCaseRunner(ITestCaseRunner):
    """测试用例套执行器（支持串/并行执行用例）"""

    def __init__(self, exec_mode, stop_on_failure=True, concurrency=1):
        self._exec_mode = exec_mode
        self._stop_on_failure = stop_on_failure
        self._concurrency = concurrency

    def _log_testsuite_error(self, testsuite, testresult, message):
        """记录测试用例套执行错误"""
        with ThreadGroupScope("%s:%s" % (testsuite.test_name, id(self))):

            ThreadGroupLocal().testcase = testsuite
            ThreadGroupLocal().testresult = testresult
            testresult.error(message)

    def _run_test(self, testsuite, test, testresult_factory, testresult):
        """执行测试用例"""
        testresult.begin_step(test.test_name)
        testsuite.current_stage = test.test_name
        runner = getattr(test, "case_runner", TestCaseRunner())
        case_result = runner.run(test, testresult_factory)
        if not case_result.passed:
            self._log_testsuite_error(
                testsuite, testresult, "TestCase %s run failed" % test.test_name
            )
        return case_result

    def sequential_run(
        self, testsuite, testresult_factory, testresult, stop_on_failure
    ):
        """顺序执行用例

        :param testsuite: 执行的测试用例套
        :type testsuite: SeqTestSuite
        :param testresult_factory: 测试结果工厂
        :type testresult_factory: ITestResultFactory
        :param stop_on_failure: 是否遇到失败用例停止执行
        :type stop_on_failure: bool

        :return TestResult/TestResultCollection - 测试结果
        """
        passed = True
        results = []
        for it in testsuite:
            case_result = self._run_test(testsuite, it, testresult_factory, testresult)
            passed &= case_result.passed
            results.append(case_result)
            if not passed and stop_on_failure:
                break
        return TestResultCollection(results, passed)

    def _run_test_from_queue(
        self,
        testsuite,
        tests_queue,
        testresult_factory,
        testresult,
        lock,
        test_result_dict,
    ):
        """从队列中不断取用例并执行

        :param tests_queue: 测试用例队列
        :type tests_queue: deque
        :param testresult_factory: 测试结果工厂
        :type testresult_factory: ITestResultFactory
        :param lock: 线程锁
        :type lock: threading.Lock
        :param test_result_dict: 测试结果字典
        :type test_result_dict: dict
        """
        while len(tests_queue) > 0:
            with lock:
                if len(tests_queue) <= 0:
                    break
                test = tests_queue.pop()
            case_result = self._run_test(
                testsuite, test, testresult_factory, testresult
            )
            with lock:
                test_result_dict.append(case_result)

    def parallel_run(self, testsuite, testresult_factory, testresult, concurrency):
        """并行执行用例

        :param testsuite: 执行的测试用例套
        :type testsuite: SeqTestSuite
        :param testresult_factory: 测试结果工厂
        :type testresult_factory: ITestResultFactory
        :param concurrency: 并发数
        :type concurrency: int

        :return TestResult/TestResultCollection - 测试结果
        """
        tests_queue = collections.deque([it for it in testsuite])
        results = []
        threads = []
        lock = threading.Lock()
        for _ in range(concurrency):
            thread = threading.Thread(
                target=self._run_test_from_queue,
                args=(
                    testsuite,
                    tests_queue,
                    testresult_factory,
                    testresult,
                    lock,
                    results,
                ),
            )
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()
        passed = True
        for result in results:
            if not result.passed:
                passed = False
                break
        return TestResultCollection(results, passed)

    def run(self, testsuite, testresult_factory):
        """执行一个顺序执行的测试用例套

        :param testsuite: 执行的测试用例套
        :type testsuite: SeqTestSuite
        :param testresult_factory: 测试结果工厂
        :type testresult_factory: ITestResultFactory

        :return TestResult/TestResultCollection - 测试结果
        """
        if not isinstance(testsuite, TestSuite):
            raise ValueError("Invalid testsuite type: %s" % type(testsuite))
        testresult = testresult_factory.create(testsuite)
        testresult.begin_test(testsuite)
        testresult.begin_step("pre_test")
        testsuite.init_test(testresult)
        result = TestResultCollection([], False)
        try:
            testsuite.pre_test()
        except:
            self._log_testsuite_error(
                testsuite,
                testresult,
                "pre_test run failed: \n%s" % traceback.format_exc(),
            )
        else:
            if self._exec_mode == TestSuite.EnumExecMode.Sequential:
                result = self.sequential_run(
                    testsuite,
                    testresult_factory,
                    testresult,
                    stop_on_failure=self._stop_on_failure,
                )
            elif self._exec_mode == TestSuite.EnumExecMode.Parallel:
                result = self.parallel_run(
                    testsuite,
                    testresult_factory,
                    testresult,
                    concurrency=self._concurrency,
                )
            else:
                raise ValueError("Invalid exec mode: %s" % self._exec_mode)

        testresult.begin_step("post_test")
        try:
            testsuite.post_test()
        except:
            self._log_testsuite_error(
                testsuite,
                testresult,
                "post_test run failed: \n%s" % traceback.format_exc(),
            )
        testresult.end_test()
        testsuite.end_test(result)
        return result


class TestSuite(TestSuiteBase):
    """测试套"""

    EnumPriority = TestCase.EnumPriority
    EnumStatus = TestCase.EnumStatus

    class EnumExecMode(object):
        Parallel = "parallel"
        Sequential = "sequential"

    testcases = []
    testcase_filter = {}
    exec_mode = EnumExecMode.Sequential
    stop_on_failure = True
    concurrency = 1

    def __init__(self, testcases):
        self.case_runner = TestSuiteCaseRunner(
            self.exec_mode,
            stop_on_failure=self.stop_on_failure,
            concurrency=self.concurrency,
        )
        self.__testcases = testcases
        self.__testresult = None
        self.__testresults = None
        self.__current_stage = ""

    def __iter__(self):
        for it in self.__testcases:
            yield it

    def __len__(self):
        return len(self.__testcases)

    @property
    def test_name(self):
        """测试套名字

        :return: str
        """
        return self.suite_class_name

    @property
    def test_doc(self):
        """测试套描述

        :return: str
        """
        return self.__class__.__doc__.strip()

    @property
    def test_result(self):
        """测试套结果

        :return: TestResult
        """
        return self.__testresult

    @property
    def test_results(self):
        """测试用例结果

        :return: TestResultCollection
        """
        return self.__testresults

    @property
    def current_stage(self):
        return self.__current_stage

    @current_stage.setter
    def current_stage(self, value):
        self.__current_stage = value

    @classmethod
    def filter(cls, testcase):
        if not cls.testcase_filter:
            return False
        priority_list = cls.testcase_filter.get("priorities", [])
        if (
            priority_list
            and isinstance(priority_list, list)
            and testcase.priority not in priority_list
        ):
            return True
        status_list = cls.testcase_filter.get("statuses", [])
        if (
            status_list
            and isinstance(status_list, list)
            and testcase.status not in status_list
        ):
            return True
        owner_list = cls.testcase_filter.get("owners", [])
        if (
            owner_list
            and isinstance(owner_list, list)
            and testcase.owner not in owner_list
        ):
            return True
        tag_list = cls.testcase_filter.get("tags", [])
        if (
            tag_list
            and isinstance(tag_list, list)
            and set(tag_list).isdisjoint(testcase.tags)
        ):
            return True
        exclude_tag_list = cls.testcase_filter.get("exclude_tags", [])
        if (
            exclude_tag_list
            and isinstance(exclude_tag_list, list)
            and not set(exclude_tag_list).isdisjoint(testcase.tags)
        ):
            return True
        return False

    def add_share_data(self, name, value, level=0):
        """添加共享数据

        :type name: string
        :param name: 需要共享的数据名称
        :param value: 需要共享的数据内容
        """
        if self.share_data_mgr:
            self.share_data_mgr.set(name, value, level)

    def get_share_data(self, name):
        """从内存中获取存储的全局数据，给当前用例使用"""
        if self.share_data_mgr:
            return self.share_data_mgr.get(name)

    def remove_share_data(self, name):
        """从内存中移除存储的共享数据"""
        if self.share_data_mgr:
            return self.share_data_mgr.remove(name)

    def get_extra_fail_record(self):
        """当错误发生时，获取需要额外添加的日志记录和附件信息

        :return: dict,dict - 日志记录，附件信息
        """
        return {}, {}

    def get_test_extra_properties(self):
        return {}

    def init_test(self, testresult):
        """初始化测试套。慎用此函数，尽量将初始化放到pre_test里。

        :param testresult: 测试结果
        :type testresult: TestResult
        """
        self.__testresult = testresult

    def pre_test(self):
        pass

    def post_test(self):
        pass

    def end_test(self, testresults):
        self.__testresults = testresults

    def dumps(self):
        """序列化"""
        from testbase import serialization

        return [serialization.dumps(it) for it in self.__testcases]

    def loads(self, buf):
        """反序列化"""
        from testbase import serialization

        self.__testcases = [serialization.loads(it) for it in buf]

    def debug_run(self):
        """本地调试测试套"""
        from testbase.runner import TestRunner
        from testbase.report import EmptyTestReport

        tests = [self]
        report = EmptyTestReport(lambda tc: StreamResult())
        runner = TestRunner(report)
        return runner.run(tests)
