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
'''testcase test
'''

from testbase.loader import TestLoader
from testbase.testcase import TestCase
import unittest

TestLoader.__test__ = False # for nauseated Nose

class TestCaseTest(unittest.TestCase):
    
    def test_property(self):
        test = TestLoader().load("test.sampletest.hellotest.HelloTest")[0]
        self.assertEqual(test.test_class_name, "test.sampletest.hellotest.HelloTest")
        self.assertEqual(test.test_name, "test.sampletest.hellotest.HelloTest")
        self.assertEqual(test.casedata, None)
        self.assertEqual(test.test_doc, '测试示例')

        
    def test_datadrive(self):
        test = TestLoader().load("test.sampletest.datatest.SingleDataTest")[0]
        self.assertEqual(test.test_class_name, "test.sampletest.datatest.SingleDataTest")
        self.assertEqual(test.test_name, "test.sampletest.datatest.SingleDataTest/0")
        self.assertEqual(test.casedata, 0)

    def test_extra_info(self):
        test = TestLoader().load("test.sampletest.hellotest.ExtraInfoTest")[0]
        self.assertIn("dev_owner", test.test_extra_info)
    
    def test_forbidden_overload_init(self):
        with self.assertRaises(RuntimeError):
            class Error(TestCase):
                def __init__(self):
                    pass

    def test_tags(self):
        class Hello(TestCase):
            """tag test"""
            owner = "xxx"
            timeout = 1
            priority = TestCase.EnumPriority.BVT
            status = TestCase.EnumStatus.Design
            tags = "test", "ok"
            def run_test(self):
                pass
        self.assertEqual(Hello.tags, set(("test", "ok")))

    def test_tags_str(self):
        class Hello(TestCase):
            """tag test"""
            owner = "xxx"
            timeout = 1
            priority = TestCase.EnumPriority.BVT
            status = TestCase.EnumStatus.Design
            tags = "test"
            def run_test(self):
                pass
        self.assertEqual(Hello.tags, set(("test",)))


    def test_tags_inhert(self):
        class Base(TestCase):
            tags = "base"

        class Hello(Base):
            """tag test"""
            owner = "xxx"
            timeout = 1
            priority = TestCase.EnumPriority.BVT
            status = TestCase.EnumStatus.Design
            tags = "test"
            def run_test(self):
                pass
        self.assertEqual(Hello.tags, set(("test", "base")))

    def test_tags_inhert_from_module(self):
        test = TestLoader().load("test.sampletest.tagtest.TagTest")[0]
        self.assertEqual(test.tags, set(("test","mod")))
        
    def test_run(self):
        class Hello(TestCase):
            """tag test"""
            owner = "xxx"
            timeout = 1
            priority = TestCase.EnumPriority.BVT
            status = TestCase.EnumStatus.Design
            def init_test(self, testresult):
                self.steps = ["init_test"]
            def pre_test(self):
                self.steps.append("pre_test")
            def run_test(self):
                self.steps.append("run_test")
            def post_test(self):
                self.steps.append("post_test")
            def clean_test(self):
                self.steps.append("clean_test")
        hello = Hello()
        hello.debug_run()
        self.assertEqual(hello.steps, ["init_test", "pre_test", "run_test", "post_test", "clean_test"])

    def test_run_inhert(self):
        class Base(TestCase):
            def init_test(self, testresult):
                self.steps = ["init_test"]
            def pre_test(self):
                self.steps.append("pre_test")
            def post_test(self):
                self.steps.append("post_test")
            def clean_test(self):
                self.steps.append("clean_test")

        class Hello(Base):
            """tag test"""
            owner = "xxx"
            timeout = 1
            priority = TestCase.EnumPriority.BVT
            status = TestCase.EnumStatus.Design
            def run_test(self):
                self.steps.append("run_test")
        hello = Hello()
        hello.debug_run()
        self.assertEqual(hello.steps, ["init_test", "pre_test", "run_test", "post_test", "clean_test"])

    def test_run_style_priority(self):
        class Base(TestCase):
            def init_test(self, testresult):
                self.steps = ["init_test"]
            def pre_test(self):
                self.steps.append("pre_test")
            def post_test(self):
                self.steps.append("post_test")
            def clean_test(self):
                self.steps.append("clean_test")

        class Hello(Base):
            """tag test"""
            owner = "xxx"
            timeout = 1
            priority = TestCase.EnumPriority.BVT
            status = TestCase.EnumStatus.Design
            def runTest(self):
                self.steps.append("runTest")
            def run_test(self):
                self.steps.append("run_test")
        hello = Hello()
        report = hello.debug_run()
        self.assertEqual(report.passed, False)


    def test_run_style_priority_old(self):
        class Base(TestCase):
            def init_test(self, testresult):
                self.steps = ["init_test"]
            def pre_test(self):
                self.steps.append("pre_test")
            def post_test(self):
                self.steps.append("post_test")
            def clean_test(self):
                self.steps.append("clean_test")

        class Hello(Base):
            """tag test"""
            owner = "xxx"
            timeout = 1
            priority = TestCase.EnumPriority.BVT
            status = TestCase.EnumStatus.Design
            def runTest(self):
                self.steps.append("runTest")
        hello = Hello()
        hello.debug_run()
        self.assertEqual(hello.steps, ["init_test", "pre_test", "runTest", "post_test", "clean_test"])
        
    def test_wait_for(self):
        class WaitForEqualTest(TestCase):
            """wait for equal test ok"""
            owner = "xxx"
            timeout = 1
            priority = TestCase.EnumPriority.BVT
            status = TestCase.EnumStatus.Design
            def run_test(self):
                self.wait_for_equal("xxxx", self, "timeout", 1, 1, 0.2)
                
        class WaitForEqualFailureTest(WaitForEqualTest):
            """wait for equal test failure
            """
            def run_test(self):
                self.wait_for_equal("xxxx", self, "timeout", 2, 1, 0.2)
                
        class WaitForMatchTest(WaitForEqualTest):
            """wait for match ok
            """
            def run_test(self):
                self.wait_for_match("xxxx", self, "owner", "x*", 1, 0.2)
                
        class WaitForMatchFailureTest(WaitForEqualTest):
            """wait for match failure
            """
            def run_test(self):
                self.wait_for_match("xxxx", self, "owner", "xxxxx*", 1, 0.2)
                
        case = WaitForEqualTest()
        case.debug_run()
        self.assertEqual(case.test_result.passed, True, "等待成功，但是用例失败")
        
        case = WaitForEqualFailureTest()
        case.debug_run()
        self.assertEqual(case.test_result.passed, False, "等待失败，用例没有失败")
        
        case = WaitForMatchTest()
        case.debug_run()
        self.assertEqual(case.test_result.passed, True, "等待成功，但是用例失败")
        
        case = WaitForMatchFailureTest()
        case.debug_run()
        self.assertEqual(case.test_result.passed, False, "等待成功，但是用例失败")