# -*- coding: utf-8 -*-

import os
import time

from testbase.testcase import TestCase
from testbase.testsuite import TestSuite

class HelloTest(TestCase):
    """测试示例"""

    owner = "foo"
    status = TestCase.EnumStatus.Ready
    timeout = 1
    priority = TestCase.EnumPriority.Normal

    def run_test(self):
        # -----------------------------
        self.startStep("测试")
        # -----------------------------
        with open("1.txt") as fp:
            self.assert_("Check file content", fp.read() == "123456")
        time.sleep(2)

        # -----------------------------
        self.startStep("Check share data")
        # -----------------------------
        value = self.get_share_data("suite")
        self.assert_equal("Check share data", value, "add_share_data")


class HelloTestSuite(TestSuite):
    """HelloTestSuite"""

    owner = "root"
    timeout = 5
    priority = TestSuite.EnumPriority.High
    status = TestSuite.EnumStatus.Design
    testcases = ["sampletest.hellotest.HelloTest", HelloTest]
    exec_mode = TestSuite.EnumExecMode.Sequential
    stop_on_failure = True

    def pre_test(self):
        print("This is pre_test")
        with open("1.txt", "w") as fp:
            fp.write("123456")
        self.add_share_data("suite", "add_share_data")

    def post_test(self):
        print("This is post_test")
        os.remove("1.txt")


class HelloTestSuitePreTestFail(HelloTestSuite):

    testcases = [HelloTest]

    def pre_test(self):
        super(HelloTestSuitePreTestFail, self).pre_test()
        raise RuntimeError("This is pre_test fail")


class HelloTestSuitePostTestFail(HelloTestSuite):

    testcases = [HelloTest]

    def post_test(self):
        super(HelloTestSuitePostTestFail, self).post_test()
        raise RuntimeError("This is post_test fail")


class HelloTestSuiteParallel(HelloTestSuite):
    testcases = [HelloTest, HelloTest, HelloTest, HelloTest]
    exec_mode = TestSuite.EnumExecMode.Parallel
    concurrency = 2


class HelloTestSuiteFilter(HelloTestSuite):
    testcases = ["sampletest.hellotest.HelloTest", "sampletest.hellotest.HelloTest2", HelloTest]
    testcase_filter = {
        "priorities": [TestCase.EnumPriority.Normal],
        "statuses": [TestCase.EnumStatus.Ready],
    }
