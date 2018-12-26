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
"""unittest for module testbase.report
"""

import unittest, six, time, json, os

from xml.dom import minidom
from testbase import runner
from testbase import report
from testbase.util import smart_text, codecs_open


class TestReportTest(unittest.TestCase):
    def setUp(self):
        if six.PY3:
            self.assertRegexpMatches = self.assertRegex
    
    def test_stream_report(self):
        test_pairs = [("HelloTest", "ASSERT"),
                      ("TimeoutTest", "TESTTIMEOUT"),
                      ("CrashTest", "APPCRASH"),
                      ("QT4iTest", "CRITICAL"),]
        for test_name, reason in test_pairs:
            test_report = report.report_types["stream"](output_testresult=True)
            test_runner = runner.runner_types["basic"](test_report)
            test_name = "test.sampletest.hellotest.%s" % test_name
            print("#### stream report test for test: " + test_name + "###")
            test_runner.run(test_name)
            test_result = test_report._failed_testresults[0]
            self.assertEqual(test_result.failed_reason, reason)
            
    def test_xml_report(self):
        def _clean_files():
            items = os.listdir(os.getcwd())
            for item in items:
                if item.endswith(".xml") or item.endswith(".xsl"):
                    os.remove(os.path.join(os.getcwd(), item))
        self.addCleanup(_clean_files)
        
        test_pairs = [("HelloTest", "断言失败"),
                    ("TimeoutTest", "用例执行超时"),
                    ("CrashTest", "App Crash"),
                    ("QT4iTest", "run_test执行失败"),]
        
        for test_name, reason in test_pairs:
            test_report = report.report_types["xml"]()
            test_runner = runner.runner_types["basic"](test_report)
            test_name = "test.sampletest.hellotest.%s" % test_name
            print("xml report test for test: " + test_name)
            test_runner.run(test_name)
            report_path = os.path.join(os.getcwd(), "TestReport.xml")
            report_xml = minidom.parse(report_path)
            test_results = report_xml.getElementsByTagName("TestResult")
            self.assertEqual(len(test_results), 1)
            attrs = test_results[0].attributes
            self.assertEqual(attrs["name"].value, test_name)
            self.assertEqual(attrs["result"].value, "False")
            result_path = os.path.join(os.getcwd(), attrs["log"].value)
            result_xml = minidom.parse(result_path)
            error_nodes = result_xml.getElementsByTagName("ERROR")
            self.assertEqual(len(error_nodes), 1)
            failed_reason = smart_text(error_nodes[0].childNodes[0].nodeValue)
            self.assertRegexpMatches(failed_reason, reason)
            
    def test_json_report(self):        
        test_pairs = [("HelloTest", "断言失败"),
                    ("TimeoutTest", "用例执行超时"),
                    ("CrashTest", "App Crash"),
                    ("QT4iTest", "run_test执行失败"),]
        for test_name, reason in test_pairs:
            time_str = time.strftime("%Y%m%d_%H%M%S", time.localtime(time.time()))
            test_report_name = "%s_%s.json" % (time_str, test_name)
            with codecs_open(test_report_name, "w", encoding="utf-8") as fd:
                test_report = report.report_types["json"](fd=fd)
                test_runner = runner.runner_types["basic"](test_report)
                test_name = "test.sampletest.hellotest.%s" % test_name
                print("json report test for test: " + test_name)
                test_runner.run(test_name)
            with codecs_open(test_report_name, "r", encoding="utf-8") as fd:
                self.addCleanup(os.remove, test_report_name)
                content = fd.read()
                report_json = json.loads(content)
                self.assertEqual(report_json["loaded_testcases"][0]["name"], test_name)
                test_results = report_json["results"]
                self.assertEqual(len(test_results), 1)
                self.assertEqual(test_results[0]["succeed"], False)
                failed_step = test_results[0]["steps"][-1]
                self.assertEqual(failed_step["succeed"], False)
                actual_reson = smart_text(failed_step["logs"][0]["message"])
                self.assertRegexpMatches(actual_reson, reason)
