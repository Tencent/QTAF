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
'''runner test
'''
import unittest

from testbase import runner
from testbase import report
from testbase import testresult


class TestResult(testresult.TestResultBase):

    __test__ = False  # for nauseated Nose

    def __init__(self):
        super(TestResult, self).__init__()
        self.logs = []

    def handle_test_begin(self, testcase):
        self.logs.append(["handle_test_begin", testcase])

    def handle_test_end(self, passed):
        self.logs.append(["handle_test_end", passed])

    def handle_step_begin(self, msg):
        self.logs.append(["handle_step_begin", msg])

    def handle_step_end(self, passed):
        self.logs.append(["handle_step_end", passed])

    def handle_log_record(self, level, msg, record, attachments):
        self.logs.append(["handle_log_record", level, msg, record, attachments])


class TestResultFactory(report.ITestResultFactory):

    __test__ = False  # for nauseated Nose

    def create(self, testcase):
        return TestResult()

    def dumps(self):
        pass

    def loads(self, buf):
        pass


class TestReport(report.ITestReport):

    __test__ = False  # for nauseated Nose

    def __init__(self):
        self.logs = []

    def begin_report(self):
        self.logs.append(["begin_report"])

    def end_report(self):
        self.logs.append(["end_report"])

    def log_test_result(self, testcase, testresult):
        self.logs.append(["log_test_result", testcase, testresult])

    def log_record(self, level, tag, msg, record):
        self.logs.append(["log_record", level, tag, msg, record])

    def get_testresult_factory(self):
        return TestResultFactory()

    def log_loaded_tests(self, loader, testcases):
        self.logs.append(["log_loaded_tests", loader, testcases])

    def log_filtered_test(self, loader, testcase, reason):
        self.logs.append(["log_filtered_test", loader, testcase, reason])
    
    def log_ignored_test(self, testcase, reason):
        self.logs.append(["log_ignored_test", testcase, reason])

    def log_load_error(self, loader, name, error):
        self.logs.append(["log_load_error", loader, name, error])

    def log_test_target(self, test_target):
        self.logs.append(["log_test_target", test_target])

    def log_resource(self, res_type, resource):
        self.logs.append(["log_resource", res_type, resource])


class RunnerTest(unittest.TestCase):

    def _run_runner_test(self, report, r):
        r.run("tests.sampletest.runnertest")
        self.assertEqual(report.logs[0][0], "begin_report")
        self.assertEqual(report.logs[-1][0], "end_report")
        testresults = {}
        for it in report.logs:
            if it[0] == 'log_test_result':
                testresults[it[1]] = it[2]

        for tc, testresult in testresults.items():
            self.assertEqual(tc, testresult.testcase)
            self.assertEqual(tc.expect_passed, testresult.passed, msg=str(tc))

    def test_run(self):
        report = TestReport()
        r = runner.TestRunner(report)
        self._run_runner_test(report, r)

    def test_run_threading(self):
        report = TestReport()
        r = runner.ThreadingTestRunner(report, 2)
        self._run_runner_test(report, r)

    def test_retry(self):
        report = TestReport()
        r = runner.TestRunner(report, retries=1)
        r.run("tests.sampletest.runnertest")
        testresults = {}
        for it in report.logs:
            if it[0] == 'log_test_result':
                testresults.setdefault(it[1], [])
                testresults[it[1]].append(it[2])
        for tc, testresult in testresults.items():
            if tc.expect_passed:
                self.assertEqual(len(testresult), 1)
            else:
                self.assertEqual(len(testresult), 2)

    def test_seq_and_repeat_test(self):
        report = TestReport()
        r = runner.TestRunner(report)
        r.run("tests.sampletest.seqtest")
        results = []
        for it in report.logs:
            if it[0] == 'log_test_result':
                results.append(type(it[1]).__name__)
        self.assertEqual(results, ["TestA"] + ["TestB"] * 4 + ["TestC"])

    def test_run_multiprocessing(self):
        # To fix the Windows forking system it's necessary to point __main__ to
        # the module we want to execute in the forked process
        # https://stackoverflow.com/questions/33128681/how-to-unit-test-code-that-uses-python-multiprocessing
        import sys
        old_main = sys.modules["__main__"]
        old_main_file = sys.modules["__main__"].__file__
        sys.modules["__main__"] = sys.modules[__name__]
        sys.modules["__main__"].__file__ = sys.modules[__name__].__file__

        #-----------------
        # real test logic begin

        report = TestReport()
        r = runner.MultiProcessTestRunner(report, 2)
        self._run_runner_test(report, r)

        # real test logic end
        #------------------

        sys.modules["__main__"] = old_main
        sys.modules["__main__"].__file__ = old_main_file

    def test_run_plan(self):
        import uuid
        from tests.sampletestplan.hello import HelloTestPlan
        report = TestReport()
        r = runner.TestRunner(report)
        r.run(HelloTestPlan())
        ops = []
        for it in report.logs:
            if it[0] == "log_test_target":
                ops.append(it[0])
            elif it[0] == "log_loaded_tests":
                ops.append(it[0])
            elif it[0] == "log_record" and it[2] == 'plan':
                ops.append(it[3])
        self.assertEqual(ops, [ "test_setup", "log_test_target",
                "resource_setup-node-%s" % uuid.getnode(),
                "resource_setup-hello-1",
                "resource_setup-hello-2",
                "log_loaded_tests",
                "resource_teardown-hello-1",
                "resource_teardown-hello-2",
                "resource_teardown-node-%s" % uuid.getnode(),
                "test_teardown"])

    def test_run_testcasesettings(self):
        report = TestReport()
        r = runner.TestRunner(report)
        r.run(runner.TestCaseSettings(["tests.sampletest"], tags=["mod"], excluded_tags=["test2"]))
        tcs = []
        for it in report.logs:
            if it[0] == 'log_test_result':
                tcs.append(it[1])
        self.assertEqual(len(tcs), 1)
        tc = tcs[0]
        from tests.sampletest.tagtest import TagTest
        self.assertIsInstance(tc, TagTest)

    def test_add_share_data(self):
        runner_types = [runner.TestRunner, runner.ThreadingTestRunner, runner.MultiProcessTestRunner]
        for runner_type in runner_types:
            if runner_type == runner.MultiProcessTestRunner:
                import sys
                old_main = sys.modules["__main__"]
                old_main_file = sys.modules["__main__"].__file__
                sys.modules["__main__"] = sys.modules[__name__]
                sys.modules["__main__"].__file__ = sys.modules[__name__].__file__

            share_data = {
                'test1': 100,
                'test2': {'a': 'b', 'b': 123, 'c': [1, 2, 3]}
            }
            report = TestReport()
            r = runner_type(report)
            r.run(runner.TestCaseSettings(["tests.sampletest.sharedatatest.AddShareDataTest"]))
            test1 = r.get_share_data('test1')
            self.assertEqual(test1, share_data['test1'])
            test2 = r.get_share_data('test2')
            self.assertEqual(test2, share_data['test2'])

            if runner_type == runner.MultiProcessTestRunner:
                sys.modules["__main__"] = old_main
                sys.modules["__main__"].__file__ = old_main_file

    def test_get_share_data(self):
        runner_types = [runner.TestRunner, runner.ThreadingTestRunner, runner.MultiProcessTestRunner]
        for runner_type in runner_types:
            if runner_type == runner.MultiProcessTestRunner:
                import sys
                old_main = sys.modules["__main__"]
                old_main_file = sys.modules["__main__"].__file__
                sys.modules["__main__"] = sys.modules[__name__]
                sys.modules["__main__"].__file__ = sys.modules[__name__].__file__

            share_data = {
                'test1': 100,
                'test2': {'a': 'b', 'b': 123, 'c': [1, 2, 3]}
            }
            report = TestReport()
            r = runner_type(report)
            r.load_share_data(share_data)
            r.run(runner.TestCaseSettings(["tests.sampletest.sharedatatest.GetShareDataTest"]))
            testresults = {}
            for it in report.logs:
                if it[0] == 'log_test_result':
                    testresults[it[1]] = it[2]

            for tc, testresult in testresults.items():
                self.assertEqual(True, testresult.passed, msg=str(tc))

            if runner_type == runner.MultiProcessTestRunner:
                sys.modules["__main__"] = old_main
                sys.modules["__main__"].__file__ = old_main_file

    def test_remove_share_data(self):
        runner_types = [runner.TestRunner, runner.ThreadingTestRunner, runner.MultiProcessTestRunner]
        for runner_type in runner_types:
            if runner_type == runner.MultiProcessTestRunner:
                import sys
                old_main = sys.modules["__main__"]
                old_main_file = sys.modules["__main__"].__file__
                sys.modules["__main__"] = sys.modules[__name__]
                sys.modules["__main__"].__file__ = sys.modules[__name__].__file__

            share_data = {
                'test1': 100,
                'test2': {'a': 'b', 'b': 123, 'c': [1, 2, 3]}
            }
            report = TestReport()
            r = runner_type(report)
            r.load_share_data(share_data)
            r.run(runner.TestCaseSettings(["tests.sampletest.sharedatatest.RemoveShareDataTest"]))
            share_data_mgr = r._share_data_mgr
            self.assertNotIn('test1', share_data_mgr.data)
            self.assertIn('test2', share_data_mgr.data)

            if runner_type == runner.MultiProcessTestRunner:
                sys.modules["__main__"] = old_main
                sys.modules["__main__"].__file__ = old_main_file


    def test_execute_type(self):
        runner_types = [runner.TestRunner, runner.ThreadingTestRunner, runner.MultiProcessTestRunner]
        for runner_type in runner_types:
            if runner_type == runner.MultiProcessTestRunner:
                import sys
                old_main = sys.modules["__main__"]
                old_main_file = sys.modules["__main__"].__file__
                sys.modules["__main__"] = sys.modules[__name__]
                sys.modules["__main__"].__file__ = sys.modules[__name__].__file__

            report = TestReport()
            r = runner_type(report, execute_type="sequential")
            r.run(runner.TestCaseSettings(["tests.sampletest.sharedatatest.AddShareDataTest", "tests.sampletest.sharedatatest.GetShareDataTest"]))
            testresults = {}
            for it in report.logs:
                if it[0] == 'log_test_result':
                    testresults[it[1]] = it[2]

            for tc, testresult in testresults.items():
                self.assertEqual(True, testresult.passed, msg=str(tc))

            if runner_type == runner.MultiProcessTestRunner:
                sys.modules["__main__"] = old_main
                sys.modules["__main__"].__file__ = old_main_file
    
    def test_stop_on_failure(self):
        runner_types = [runner.TestRunner, runner.ThreadingTestRunner, runner.MultiProcessTestRunner]

        for runner_type in runner_types:
            if runner_type == runner.MultiProcessTestRunner:
                import sys
                old_main = sys.modules["__main__"]
                old_main_file = sys.modules["__main__"].__file__
                sys.modules["__main__"] = sys.modules[__name__]
                sys.modules["__main__"].__file__ = sys.modules[__name__].__file__
            
            report = TestReport()
            r = runner_type(report, execute_type="random")
            r.run(runner.TestCaseSettings(["tests.sampletest.stoponfailuretest.FirstFailureTest", "tests.sampletest.stoponfailuretest.SecondFailureTest"]))
            for it in report.logs:
                print(it[0])

if __name__ == "__main__":
    unittest.main()
