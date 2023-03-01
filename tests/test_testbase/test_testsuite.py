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
"""testsuite test
"""

import time
import unittest

from testbase.loader import TestLoader
from testbase.testsuite import TestSuite, TestSuiteCaseRunner

class TestSuiteTest(unittest.TestCase):

    def test_property(self):
        test = TestLoader().load("tests.sampletest.suitetest.HelloTestSuite")[0]
        self.assertEqual(test.test_name, "tests.sampletest.suitetest.HelloTestSuite")
        self.assertEqual(test.owner, "root")
        self.assertEqual(len(test.testcases), 2)

    def test_sequential_run(self):
        test = TestLoader().load("tests.sampletest.suitetest.HelloTestSuite")[0]
        test.debug_run()
        self.assertEqual(test.test_result.passed, False)
        self.assertEqual(len(test.test_results), 1)

        test.case_runner = TestSuiteCaseRunner(
            TestSuite.EnumExecMode.Sequential,
            stop_on_failure=False
        )
        test.debug_run()
        self.assertEqual(test.test_result.passed, False)
        self.assertEqual(len(test.test_results), 2)
        self.assertEqual(test.test_results[0].passed, False)
        self.assertEqual(test.test_results[1].passed, True)

    def test_parallel_run(self):
        test = TestLoader().load("tests.sampletest.suitetest.HelloTestSuiteParallel")[0]
        time0 = time.time()
        test.debug_run()
        time_cost = time.time() - time0
        self.assertEqual(test.test_result.passed, True)
        self.assertEqual(len(test.test_results), 4)
        self.assertLess(time_cost, 7)

    def test_run_pre_test_fail(self):
        test = TestLoader().load("tests.sampletest.suitetest.HelloTestSuitePreTestFail")[0]
        test.debug_run()
        self.assertEqual(test.test_result.passed, False)
        self.assertEqual(len(test.test_results), 0)

    def test_run_post_test_fail(self):
        test = TestLoader().load("tests.sampletest.suitetest.HelloTestSuitePostTestFail")[0]
        test.debug_run()
        self.assertEqual(test.test_result.passed, False)
        self.assertEqual(len(test.test_results), 1)
        self.assertEqual(test.test_results[0].passed, True)
