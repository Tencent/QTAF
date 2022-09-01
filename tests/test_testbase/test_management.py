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
"""testcase for management
"""

import codecs
import multiprocessing
import os
import shlex
import shutil
import unittest
import sys

from testbase.testcase import TestCase
from testbase.management import RunTest, DiscoverTests, RunScript, ManagementTools
from testbase.types import runner_types, report_types
from testbase.util import get_time_str
from testbase.test import modify_settings


class RuntestTest(unittest.TestCase):
    """ """

    def test_args_parsing(self):
        cmdline = "-w working_dir xxxx oooo.test".split()
        args = RunTest.parser.parse_args(cmdline)
        self.assertEqual(args.working_dir, "working_dir")
        self.assertEqual(args.tests, ["xxxx", "oooo.test"])

        cmdline = (
            "--status Ready --status Design --priority BVT --priority High --priority Normal"
            " --tag xxx --tag ooo --excluded-tag aaa --excluded-tag bbb"
            " --owner apple --owner banana xxxx".split()
        )
        args = RunTest.parser.parse_args(cmdline)
        self.assertEqual(args.status, ["Ready", "Design"])
        self.assertEqual(args.priorities, ["BVT", "High", "Normal"])
        self.assertEqual(args.tags, ["xxx", "ooo"])
        self.assertEqual(args.excluded_tags, ["aaa", "bbb"])
        self.assertEqual(args.owners, ["apple", "banana"])
        self.assertEqual(args.tests, ["xxxx"])

    def test_config_file(self):
        cmdline = "-w working_dir xxxx oooo.test --config-file test.json".split()
        args = RunTest.parser.parse_args(cmdline)
        self.assertEqual(args.working_dir, "working_dir")
        self.assertEqual(args.tests, ["xxxx", "oooo.test"])
        self.assertEqual(args.config_file, "test.json")

    def test_report_args_parsing(self):
        cmdline = (
            'xxxx --report-type stream --report-args "--no-output-result --no-summary"'
        )
        cmdline = shlex.split(cmdline)
        args = RunTest.parser.parse_args(cmdline)
        report_type = report_types[args.report_type]
        report_type.parse_args(shlex.split(args.report_args))

        output_file = "json_report.json"
        cmdline = 'xxxx --report-type json --report-args "--output %s"' % output_file
        cmdline = shlex.split(cmdline)
        args = RunTest.parser.parse_args(cmdline)
        report_type = report_types[args.report_type]
        report_type.parse_args(shlex.split(args.report_args))
        if os.path.exists(output_file):
            os.remove(output_file)

    def test_runner_args_parsing(self):
        test_pairs = [
            ('xxxx --runner-type basic --runner-args "--retries 3"', 1),
            (
                'xxxx --runner-type multithread --runner-args "--retries 3 --concurrency 0"',
                multiprocessing.cpu_count(),
            ),
            (
                'xxxx --runner-type multiprocess --runner-args "--retries 3 --concurrency 3"',
                3,
            ),
        ]
        for cmdline, concurrency in test_pairs:
            args = RunTest.parser.parse_args(shlex.split(cmdline))
            runner_type = runner_types[args.runner_type]
            runner = runner_type.parse_args(
                shlex.split(args.runner_args), None, None, "random"
            )
            self.assertEqual(getattr(runner, "concurrency", 1), concurrency)

    def test_failed_returncode(self):
        working_dir = "test_online_report_%s" % get_time_str()
        cmdline = "--report-type html tests.sampletest.hellotest.FailedCase"
        cmdline += " -w " + working_dir
        self.addCleanup(shutil.rmtree, working_dir, ignore_errors=True)
        args = RunTest.parser.parse_args(cmdline.split())
        return_code = RunTest().execute(args)
        self.assertEqual(return_code, 1)

    def test_failed_exit_code(self):
        working_dir = "test_online_report_%s" % get_time_str()
        cmdline = "runtest --report-type html tests.sampletest.hellotest.FailedCase"
        cmdline += " -w " + working_dir
        self.addCleanup(shutil.rmtree, working_dir, ignore_errors=True)
        sys.argv = ["qtaf"]
        sys.argv.extend(cmdline.split())
        exitcode = ManagementTools().run()
        self.assertEqual(exitcode, 1)

    def test_success_returncode(self):
        working_dir = "test_online_report_%s" % get_time_str()
        cmdline = "--report-type html tests.sampletest.hellotest.PassedCase"
        cmdline += " -w " + working_dir
        self.addCleanup(shutil.rmtree, working_dir, ignore_errors=True)
        args = RunTest.parser.parse_args(cmdline.split())
        proc = multiprocessing.Process(target=RunTest().execute, args=(args,))
        proc.start()
        proc.join()
        self.assertEqual(proc.exitcode, 0)

    def test_config_file_success(self):
        working_dir = "test_online_report_%s" % get_time_str()
        cmdline = "runtest --report-type html tests.sampletest.hellotest.FailedCase --config-file tests/sampletest/test.json"
        cmdline += " -w " + working_dir
        self.addCleanup(shutil.rmtree, working_dir, ignore_errors=True)
        sys.argv = ["qtaf"]
        sys.argv.extend(cmdline.split())
        exitcode = ManagementTools().run()
        self.assertEqual(exitcode, 0)

    def test_config_file_with_dict(self):
        with modify_settings(QTAF_PARAM_MODE=True):
            working_dir = "test_online_report_%s" % get_time_str()
            cmdline = "runtest --report-type html --config-file tests/sampletest/test_dict.json"
            cmdline += " -w " + working_dir
            self.addCleanup(shutil.rmtree, working_dir, ignore_errors=True)
            sys.argv = ["qtaf"]
            sys.argv.extend(cmdline.split())
            exitcode = ManagementTools().run()
            self.assertEqual(exitcode, 0)

    def test_config_file_with_global_parameters(self):
        with modify_settings(QTAF_PARAM_MODE=True):
            working_dir = "test_online_report_%s" % get_time_str()
            cmdline = (
                "runtest --config-file tests/sampletest/test_global_parameters.json"
            )
            cmdline += " -w " + working_dir
            self.addCleanup(shutil.rmtree, working_dir, ignore_errors=True)
            sys.argv = ["qtaf"]
            sys.argv.extend(cmdline.split())
            exitcode = ManagementTools().run()
            self.assertEqual(exitcode, 0)


class DiscoverTest(unittest.TestCase):
    """discover command test"""

    def test_discover(self):
        file_name = "discovertest_%s.txt" % get_time_str()
        cmdline = "--excluded-tag test --priority High --status Ready --owner xxx "
        cmdline += "--output-file %s tests.sampletest.hellotest " % file_name
        cmdline += "tests.sampletest.tagtest tests.sampletest.loaderr"

        args = DiscoverTests.parser.parse_args(cmdline.split())
        self.assertEqual(args.priorities, [TestCase.EnumPriority.High])
        self.assertEqual(args.status, [TestCase.EnumStatus.Ready])
        self.assertEqual(args.excluded_tags, ["test"])
        self.assertEqual(args.owners, ["xxx"])
        self.assertEqual(args.output_type, "stream")
        self.assertEqual(args.output_file, file_name)

        DiscoverTests().execute(args)
        self.assertTrue(os.path.exists(file_name))
        self.addCleanup(os.remove, file_name)
        with codecs.open(file_name, "r", encoding="utf-8") as fd:
            content = fd.read()

        self.assertTrue(content.find("tests.sampletest.tagtest.TagTest2, reason") >= 0)
        self.assertTrue(content.find("tests.sampletest.hellotest.PassedCase") >= 0)
        self.assertTrue(
            content.find('cannot load test "tests.sampletest.loaderr"') >= 0
        )

    def test_discover_show(self):
        file_name = "discovertest_%s.txt" % get_time_str()
        cmdline = (
            "--excluded-tag test --owner xxx --output-file %s --show error " % file_name
        )
        cmdline += "tests.sampletest.hellotest tests.sampletest.tagtest tests.sampletest.loaderr"
        args = DiscoverTests.parser.parse_args(cmdline.split())
        DiscoverTests().execute(args)
        self.assertTrue(os.path.exists(file_name))
        self.addCleanup(os.remove, file_name)
        with codecs.open(file_name, "r", encoding="utf-8") as fd:
            content = fd.read()
        self.assertTrue(content.find("filtered test") == -1)
        self.assertTrue(content.find("normal test") == -1)
        self.assertTrue(content.find("error test") >= 0)
        self.assertTrue(
            content.find('cannot load test "tests.sampletest.loaderr"') >= 0
        )


class RunScriptTest(unittest.TestCase):
    def test_invalid_script(self):
        cmdline = "tests/test_tuia"
        args = RunScript.parser.parse_args(cmdline.split())
        try:
            RunScript().execute(args)
        except SystemExit as e:
            self.assertEqual(e.code, 1)

        cur_dir = os.path.dirname(os.path.abspath(__file__))
        cmdline = os.path.join(cur_dir, "__init__.py")
        args = RunScript.parser.parse_args(cmdline.split())
        try:
            RunScript().execute(args)
        except SystemExit as e:
            self.assertEqual(e.code, 1)


if __name__ == "__main__":
    unittest.main()
