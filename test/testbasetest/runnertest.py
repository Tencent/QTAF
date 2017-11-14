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
#2017/11/13 olive created

from testbase import runner
from testbase import report
from testbase import testresult
import unittest

class TestResult(testresult.TestResultBase):

    def __init__(self):
        super(TestResult, self).__init__()
        self.logs = []
        
    def handle_test_begin(self, testcase ):
        self.logs.append(["handle_test_begin", testcase])
            
    def handle_test_end(self, passed ):
        self.logs.append(["handle_test_end", passed])
        
    def handle_step_begin(self, msg ):
        self.logs.append(["handle_step_begin", msg])
        
    def handle_step_end(self, passed ):
        self.logs.append(["handle_step_end", passed])
    
    def handle_log_record(self, level, msg, record, attachments ):
        self.logs.append(["handle_log_record", level, msg, record, attachments])
    
class TestResultFactory(report.ITestResultFactory):
    
    def create(self, testcase ):
        return TestResult()
    
    def dumps(self):
        pass
    
    def loads(self, buf):
        pass

class TestReport(report.ITestReport):
    
    def __init__(self):
        self.logs = []
        
    def begin_report(self):
        self.logs.append(["begin_report"])
    
    def end_report(self):
        self.logs.append(["end_report"])
        
    def log_test_result(self, testcase, testresult ):
        self.logs.append(["log_test_result", testcase, testresult])
                
    def log_record(self, level, tag, msg, record):
        self.logs.append(["log_record", level, tag, msg, record])

    def get_testresult_factory(self):
        return TestResultFactory()
        
class RunnerTest(unittest.TestCase):
    
    def test_run(self):
        report = TestReport()
        r = runner.TestRunner(report)
        self._run_runner_test(report, r)
        
    def test_run_threading(self):
        report = TestReport()
        r = runner.ThreadingTestRunner(report,2)
        self._run_runner_test(report, r)
        
    def test_run_multiprocessing(self):
        report = TestReport()
        r = runner.MultiProcessTestRunner(report,2)
        self._run_runner_test(report, r)
        
    def _run_runner_test(self, report, r):
        r.run("test.sampletest.runnertest")
        self.assertEqual(report.logs[0][0], "begin_report")
        self.assertEqual(report.logs[-1][0], "end_report")
        testresults = {}
        for it in report.logs:
            if it[0] == 'log_test_result':
                testresults[it[1]] = it[2]

        for tc, testresult in testresults.items():
            self.assertEqual(tc, testresult.testcase)
            self.assertEqual(tc.expect_passed, testresult.passed)
            
    def test_retry(self):
        report = TestReport()
        r = runner.TestRunner(report, retries=1)
        r.run("test.sampletest.runnertest")
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
        r.run("test.sampletest.seqtest")
        results = []
        for it in report.logs:
            if it[0] == 'log_test_result':
                results.append(type(it[1]).__name__)
        self.assertEqual(results, ["TestA"] + ["TestB"] * 4 +["TestC"])
        
        
        
        