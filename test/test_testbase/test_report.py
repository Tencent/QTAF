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

import json
import os
import shutil
import six
import sys
import traceback
import unittest

from xml.dom import minidom
from testbase import runner
from testbase import report
from testbase.util import smart_text, codecs_open, get_time_str

suffix = "%s%s" % (sys.version_info[0], sys.version_info[1])

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
        test_pairs = [("HelloTest", "断言失败"),
                    ("TimeoutTest", "用例执行超时"),
                    ("CrashTest", "App Crash"),
                    ("QT4iTest", "run_test执行失败"),]
        
        old_cwd = os.getcwd()
        for test_name, reason in test_pairs:
            try:
                test_report = report.report_types["xml"]()
                test_runner = runner.runner_types["basic"](test_report)
                test_name = "test.sampletest.hellotest.%s" % test_name
                working_dir = test_name + "_" + get_time_str()
                os.makedirs(working_dir)
                os.chdir(working_dir)
                self.addCleanup(shutil.rmtree, working_dir, True)
                print("xml report test for test: %s, wokring dir=%s" % (test_name, working_dir))
                test_runner.run(test_name)
                report_path = os.path.join(os.getcwd(), "TestReport.xml")
                xml_report = minidom.parse(report_path)
                test_results = xml_report.getElementsByTagName("TestResult")
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
            finally:
                os.chdir(old_cwd)
            
    def test_json_report(self):
        test_pairs = [("HelloTest", "断言失败"),
                    ("TimeoutTest", "用例执行超时"),
                    ("CrashTest", "App Crash"),
                    ("QT4iTest", "run_test执行失败")]
        
        old_cwd = os.getcwd()
        try:
            for test_name, reason in test_pairs:
                time_str = get_time_str()
                working_dir = test_name + "_" + time_str
                os.makedirs(working_dir)
                os.chdir(working_dir)
                self.addCleanup(shutil.rmtree, working_dir, True)
                
                test_report_name = "%s_%s.json" % (time_str, test_name)
                with codecs_open(test_report_name, "w", encoding="utf-8") as fd:
                    test_report = report.report_types["json"](fd=fd)
                    test_runner = runner.runner_types["basic"](test_report)
                    test_name = "test.sampletest.hellotest.%s" % test_name
                    print("json report test for test: " + test_name)
                    test_runner.run(test_name)
                with codecs_open(test_report_name, "r", encoding="utf-8") as fd:
                    content = fd.read()
                    report_json = json.loads(content)
                    self.assertEqual(report_json["loaded_testcases"][0]["name"], test_name)
                    test_results = report_json["results"]
                    self.assertEqual(len(test_results), 1)
                    with codecs_open(test_results[test_name][0], "r", encoding="utf-8") as fd2:
                        content = fd2.read()
                        result_json = json.loads(content)
                        self.assertEqual(result_json["succeed"], False)
                        failed_step = result_json["steps"][-1]
                        self.assertEqual(failed_step["succeed"], False)
                        actual_reson = smart_text(failed_step["logs"][0]["message"])
                        self.assertRegexpMatches(actual_reson, reason)
        finally:
            os.chdir(old_cwd)
            
        try:
            test_name = "test.sampletest.hellotest.HelloTest test.sampletest.hellotest.TimeoutTest"
            time_str = get_time_str()
            working_dir = test_name + "_" + time_str
            os.makedirs(working_dir)
            os.chdir(working_dir)
            self.addCleanup(shutil.rmtree, working_dir, True)
            
            test_report_name = "test_json_report_%s.json" % time_str
            retry_count = 2
            with codecs_open(test_report_name, "w", encoding="utf-8") as fd:
                test_report = report.report_types["json"](fd=fd, title="test_json_report")
                test_runner = runner.runner_types["multithread"](test_report, retries=retry_count)
                test_runner.run(test_name)
            with codecs_open(test_report_name, "r", encoding="utf-8") as fd:
                content = fd.read()
                report_json = json.loads(content)
                summary = report_json["summary"]
                self.assertEqual(summary["testcase_total_run"], (retry_count + 1) * 2)
                self.assertEqual(summary["testcase_total_count"], 2)
                self.assertTrue("hostname" in summary["environment"])
                self.assertTrue("os" in summary["environment"])
                self.assertTrue("qtaf_version" in summary["environment"])
                self.assertTrue("python_version" in summary["environment"])
        finally:
            os.chdir(old_cwd)
            
    def test_html_report(self):
        test_pairs = [("HelloTest", "断言失败"),
                    ("TimeoutTest", "用例执行超时"),
                    ("CrashTest", "App Crash"),
                    ("QT4iTest", "run_test执行失败"),]
        
        old_cwd = os.getcwd()
        for test_name, reason in test_pairs:
            try:
                working_dir = test_name + "_" + get_time_str()
                os.makedirs(working_dir)
                os.chdir(working_dir)
                self.addCleanup(shutil.rmtree, working_dir, True)
                
                test_report = report.report_types["html"](title="test html report")
                test_runner = runner.runner_types["basic"](test_report)
                test_name = "test.sampletest.hellotest.%s" % test_name
                print("html report test for test: " + test_name)
                test_runner.run(test_name)
                html_report_file = os.path.join(os.getcwd(), "qta-report.js")
                with codecs_open(html_report_file, encoding="utf-8") as fd:
                    content = fd.read()
                    index = content.find("{")
                    qta_report_data = content[index:]
                    qta_report = json.loads(qta_report_data)
                    self.assertEqual(qta_report["loaded_testcases"][0]["name"], test_name)
                    test_results = qta_report["results"]
                    self.assertEqual(len(test_results), 1)
                    with codecs_open(test_results[test_name][0], "r", encoding="utf-8") as fd2:
                        content = fd2.read()
                        index = content.find("{")
                        result_json_data = content[index:]
                        result_json = json.loads(result_json_data)
                        self.assertEqual(result_json["succeed"], False)
                        failed_step = result_json["steps"][-1]
                        self.assertEqual(failed_step["succeed"], False)
                        actual_reson = smart_text(failed_step["logs"][0]["message"])
                        self.assertRegexpMatches(actual_reson, reason)
                
            finally:
                os.chdir(old_cwd)
                
        try:
            test_name = "DataDriveCase"
            working_dir = test_name + "_" + get_time_str()
            os.makedirs(working_dir)
            os.chdir(working_dir)
            self.addCleanup(shutil.rmtree, working_dir, True)
            
            test_report = report.report_types["html"](title="test html report")
            test_runner = runner.runner_types["basic"](test_report)
            test_name = "test.sampletest.hellotest." + test_name
            test_runner.run(test_name)
            
            with codecs_open("qta-report.js", encoding="utf-8") as fd:
                content = fd.read()
                index = content.find("{")
                qta_report_data = content[index:]
                qta_report = json.loads(qta_report_data)
                self.assertEqual(len(qta_report["loaded_testcases"]), 2)
                for item in ["中国", "xxx"]:
                    is_ok = map(lambda x: item in smart_text(x["name"]), qta_report["loaded_testcases"])
                    self.assertTrue(any(is_ok))
                test_results = qta_report["results"]
                self.assertEqual(len(test_results), 2)
                
                for test_name in map(lambda x: x["name"], qta_report["loaded_testcases"]):
                    with codecs_open(test_results[test_name][0], "r", encoding="utf-8") as fd2:
                        content = fd2.read()
                        index = content.find("{")
                        result_json_data = content[index:]
                        result_json = json.loads(result_json_data)
                        self.assertEqual(result_json["succeed"], True)
        finally:
            os.chdir(old_cwd)

