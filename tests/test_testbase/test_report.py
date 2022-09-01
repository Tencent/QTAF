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

import argparse
import json
import os
import shutil
import six
import sys
import traceback
import unittest

from xml.dom import minidom
from testbase.test import modify_attributes
from testbase.types import runner_types, report_types
from testbase.util import smart_text, codecs_open, get_time_str

suffix = "%s%s" % (sys.version_info[0], sys.version_info[1])


class TestReportBase(unittest.TestCase):
    """base class of report test"""

    def setUp(self):
        if six.PY3:
            self.assertRegexpMatches = self.assertRegex


class StreamReportTest(TestReportBase):
    """test stream report"""

    def test_stream_report(self):
        test_pairs = [
            ("HelloTest", "ASSERT"),
            ("TimeoutTest", "TESTTIMEOUT"),
            ("CrashTest", "APPCRASH"),
            ("QT4iTest", "CRITICAL"),
        ]
        for test_name, reason in test_pairs:
            test_report = report_types["stream"](output_testresult=True)
            test_runner = runner_types["basic"](test_report)
            test_name = "tests.sampletest.hellotest.%s" % test_name
            print("#### stream report test for test: " + test_name + "###")
            test_runner.run(test_name)
            test_result = test_report._failed_testresults[0]
            self.assertEqual(test_result.failed_reason, reason)


class XmlReportTest(TestReportBase):
    """xml report test"""

    def test_xml_report(self):
        test_pairs = [
            ("HelloTest", "断言失败"),
            ("TimeoutTest", "用例执行超时"),
            ("CrashTest", "App Crash"),
            ("QT4iTest", "run_test执行失败"),
        ]

        old_cwd = os.getcwd()
        for test_name, reason in test_pairs:
            try:
                test_report = report_types["xml"]()
                test_runner = runner_types["basic"](test_report)
                test_name = "tests.sampletest.hellotest.%s" % test_name
                working_dir = test_name + "_" + get_time_str()
                os.makedirs(working_dir)
                os.chdir(working_dir)
                self.addCleanup(shutil.rmtree, working_dir, True)
                print("xml report test for test: %s" % test_name)
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

    def test_xml_report_with_extra_properties(self):
        test_pairs = [
            ("HelloTest", "断言失败"),
            ("TimeoutTest", "用例执行超时"),
            ("CrashTest", "App Crash"),
            ("QT4iTest", "run_test执行失败"),
        ]

        old_cwd = os.getcwd()
        try:
            test_report = report_types["xml"]()
            test_runner = runner_types["basic"](test_report)
            test_name = "tests.sampletest.hellotest.ExtraPropertyTest"
            working_dir = test_name + "_" + get_time_str()
            os.makedirs(working_dir)
            os.chdir(working_dir)
            self.addCleanup(shutil.rmtree, working_dir, True)
            print("xml report test for test: %s" % test_name)
            test_runner.run(test_name)
            report_path = os.path.join(os.getcwd(), "TestReport.xml")
            xml_report = minidom.parse(report_path)
            test_results = xml_report.getElementsByTagName("TestResult")
            self.assertEqual(len(test_results), 1)
            attrs = test_results[0].attributes
            self.assertEqual(attrs["name"].value, test_name)
            self.assertEqual(attrs["result"].value, "True")
            result_path = os.path.join(os.getcwd(), attrs["log"].value)
            result_xml = minidom.parse(result_path)
            test_nodes = result_xml.getElementsByTagName("TEST")
            self.assertEqual(len(test_nodes), 1)
            attrs = test_nodes[0].attributes
            self.assertEqual(attrs["base_property_str"].value, "123")
            self.assertEqual(attrs["base_property_int"].value, "123")
            self.assertEqual(attrs["base_property_func_value"].value, "True")
            self.assertEqual(attrs["base_property_bool"].value, "True")
            self.assertEqual(attrs["property_str"].value, "123")
            self.assertEqual(attrs["property_int"].value, "123")
            self.assertEqual(attrs["property_func_value"].value, "True")
            self.assertEqual(attrs["property_bool"].value, "True")
            self.assertEqual(attrs["property_variable2"].value, "b1_test")
        finally:
            os.chdir(old_cwd)


class JsonReportTest(TestReportBase):
    """json report test"""

    def test_json_report_content(self):
        test_pairs = [
            ("HelloTest", "断言失败"),
            ("TimeoutTest", "用例执行超时"),
            ("CrashTest", "App Crash"),
            ("QT4iTest", "run_test执行失败"),
        ]

        old_cwd = os.getcwd()
        for test_name, reason in test_pairs:
            try:
                time_str = get_time_str()
                working_dir = test_name + "_" + time_str
                os.makedirs(working_dir)
                os.chdir(working_dir)
                self.addCleanup(shutil.rmtree, working_dir, True)

                test_report_name = "%s_%s.json" % (time_str, test_name)
                with codecs_open(test_report_name, "w", encoding="utf-8") as fd:
                    test_report = report_types["json"](fd=fd)
                    test_runner = runner_types["basic"](test_report)
                    test_name = "tests.sampletest.hellotest.%s" % test_name
                    print("json report test for test: " + test_name)
                    test_runner.run(test_name)
                with codecs_open(test_report_name, "r", encoding="utf-8") as fd:
                    content = fd.read()
                    report_json = json.loads(content)
                    failed_test_names = list(report_json["failed_tests"].keys())
                    self.assertEqual(failed_test_names[0], test_name)
                    failed_tests = report_json["failed_tests"]
                    self.assertEqual(len(failed_tests), 1)
                    with codecs_open(
                        failed_tests[test_name]["records"][0], "r", encoding="utf-8"
                    ) as fd2:
                        content = fd2.read()
                        result_json = json.loads(content)
                        self.assertEqual(result_json["succeed"], False)
                        failed_step = result_json["steps"][-1]
                        self.assertEqual(failed_step["succeed"], False)
                        actual_reson = smart_text(failed_step["logs"][0]["message"])
                        self.assertRegexpMatches(actual_reson, reason)
            finally:
                os.chdir(old_cwd)

    def test_json_report_retry(self):
        old_cwd = os.getcwd()
        try:
            test_name = "tests.sampletest.hellotest.HelloTest tests.sampletest.hellotest.TimeoutTest"
            time_str = get_time_str()
            working_dir = test_name + "_" + time_str
            os.makedirs(working_dir)
            os.chdir(working_dir)
            self.addCleanup(shutil.rmtree, working_dir, True)

            test_report_name = "test_json_report_%s.json" % time_str
            retry_count = 2
            with codecs_open(test_report_name, "w", encoding="utf-8") as fd:
                test_report = report_types["json"](fd=fd, title="test_json_report")
                test_runner = runner_types["multithread"](
                    test_report, retries=retry_count
                )
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


class HtmlReportTest(TestReportBase):
    """html report test"""

    def test_html_report_content(self):
        test_pairs = [
            ("HelloTest", "断言失败"),
            ("TimeoutTest", "用例执行超时"),
            ("CrashTest", "App Crash"),
            ("QT4iTest", "run_test执行失败"),
        ]

        old_cwd = os.getcwd()
        for test_name, reason in test_pairs:
            try:
                working_dir = test_name + "_" + get_time_str()
                os.makedirs(working_dir)
                os.chdir(working_dir)
                self.addCleanup(shutil.rmtree, working_dir, True)

                test_report = report_types["html"](title="test html report")
                test_runner = runner_types["basic"](test_report)
                test_name = "tests.sampletest.hellotest.%s" % test_name
                print("html report test for test: " + test_name)
                test_runner.run(test_name)
                html_report_file = os.path.join(os.getcwd(), "qta-report.js")
                with codecs_open(html_report_file, encoding="utf-8") as fd:
                    content = fd.read()
                    index = content.find("{")
                    qta_report_data = content[index:]
                    qta_report = json.loads(qta_report_data)
                    failed_test_names = list(qta_report["failed_tests"].keys())
                    self.assertEqual(failed_test_names[0], test_name)
                    failed_tests = qta_report["failed_tests"]
                    self.assertEqual(len(failed_tests), 1)
                    with codecs_open(
                        failed_tests[test_name]["records"][0], "r", encoding="utf-8"
                    ) as fd2:
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

    def test_html_report_datadrive(self):
        old_cwd = os.getcwd()
        try:
            test_name = "DataDriveCase"
            working_dir = test_name + "_" + get_time_str()
            os.makedirs(working_dir)
            os.chdir(working_dir)
            self.addCleanup(shutil.rmtree, working_dir, True)

            test_report = report_types["html"](title="test html report")
            test_runner = runner_types["basic"](test_report)
            test_name = "tests.sampletest.hellotest." + test_name
            test_runner.run(test_name)

            with codecs_open("qta-report.js", encoding="utf-8") as fd:
                content = fd.read()
                index = content.find("{")
                qta_report_data = content[index:]
                qta_report = json.loads(qta_report_data)
                self.assertEqual(qta_report["summary"]["testcase_total_run"], 2)
                passed_tests = qta_report["passed_tests"]
                for item in ["中国", "xxx"]:
                    is_ok = any((lambda x: item in x, passed_tests.keys()))
                    self.assertTrue(is_ok)
                self.assertEqual(len(passed_tests), 2)

                for test_name in passed_tests:
                    with codecs_open(
                        passed_tests[test_name]["records"][0], "r", encoding="utf-8"
                    ) as fd2:
                        content = fd2.read()
                        index = content.find("{")
                        result_json_data = content[index:]
                        result_json = json.loads(result_json_data)
                        self.assertEqual(result_json["succeed"], True)
        finally:
            os.chdir(old_cwd)


class RuntestReportTest(TestReportBase):
    """runtest report test"""

    def test_runtest_return_code(self):
        from testbase.management import RunTest

        test_cases = list(
            map(
                lambda x: "tests.sampletest.hellotest." + x,
                [
                    "PassedCase",
                    "FailedCase",
                    "PassedCase",
                ],
            )
        )
        report_pairs = [
            ("stream", ""),
            ("json", "-o xxxx.json"),
            ("html", ""),
            ("xml", ""),
        ]
        context = modify_attributes(os, {"system": lambda _: None})
        for report_type, report_args in report_pairs:
            args = argparse.Namespace()
            args.tests = test_cases
            args.working_dir = "runtest_%s" % get_time_str()
            self.addCleanup(shutil.rmtree, args.working_dir, True)
            args.report_type = report_type
            args.report_args = report_args
            args.report_args_help = None
            args.runner_type = "basic"
            args.runner_args = ""
            args.runner_args_help = None
            args.priorities = None
            args.status = None
            args.owners = None
            args.excluded_names = None
            args.tags = None
            args.excluded_tags = None
            args.resmgr_backend_type = "local"
            args.execute_type = "random"
            args.share_data = None
            args.global_parameters = None
            args.config_file = None

            with context:
                self.assertEqual(RunTest().execute(args), 1)

            args.working_dir = "runtest_%s" % get_time_str()
            self.addCleanup(shutil.rmtree, args.working_dir, True)
            args.tests = test_cases[:1]

            with context:
                self.assertEqual(RunTest().execute(args), None)


if __name__ == "__main__":
    unittest.main()
