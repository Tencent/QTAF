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

from testbase.testcase import TestCase
from testbase import datadrive
import unittest

class DatadriveTest(unittest.TestCase):

    def test_load_dict_data(self):

        data = {
            "x": {"value":"x", "xxx":{"owner": "eeelin"}},
            "y": {"value":2, "xxx":{"priority": TestCase.EnumPriority.Low}}
        }
        @datadrive.DataDrive(data)
        class Demo(TestCase):
            owner = "xxx"
            timeout = 1
            priority = TestCase.EnumPriority.BVT
            status = TestCase.EnumStatus.Design
            def run_test(self):
                pass

        tests = datadrive.load_datadrive_tests(Demo)
        self.assertEqual(len(tests), 2)
        for test in tests:
            self.assertEqual(test.casedata, data[test.casedataname])
            
    def test_load_list_data(self):

        data = ["xxx", 1111]
        @datadrive.DataDrive(data)
        class Demo(TestCase):
            owner = "xxx"
            timeout = 1
            priority = TestCase.EnumPriority.BVT
            status = TestCase.EnumStatus.Design
            def run_test(self):
                pass

        tests = datadrive.load_datadrive_tests(Demo)
        self.assertEqual(len(tests), 2)
        self.assertEqual(tests[0].casedata, data[0])
        self.assertEqual(tests[1].casedata, data[1])


    def test_set_attrs(self):
        data = [
            {"value":"x", "__attrs__":{"owner": "eeelin"}},
            {"value":2, "__attrs__":{"priority": TestCase.EnumPriority.Low}}
        ]
        @datadrive.DataDrive(data)
        class Demo(TestCase):
            owner = "xxx"
            timeout = 1
            priority = TestCase.EnumPriority.BVT
            status = TestCase.EnumStatus.Design
            def run_test(self):
                pass

        tests = datadrive.load_datadrive_tests(Demo)
        self.assertEqual(len(tests), 2)
        self.assertEqual(tests[0].owner, "eeelin")
        self.assertEqual(tests[0].priority, TestCase.EnumPriority.BVT)
        self.assertEqual(tests[1].owner, "xxx")
        self.assertEqual(tests[1].priority, TestCase.EnumPriority.Low)

    def test_set_attrs_tags(self):
        class Base(TestCase):
            tags = "base"
        
        data = [
            {"value":"x", "__attrs__":{"tags": "eeelin"}},
            {"value":"x", "__attrs__":{"tags": ("fff","xxx")}},
        ]
        @datadrive.DataDrive(data)
        class Demo(Base):
            owner = "xxx"
            timeout = 1
            priority = TestCase.EnumPriority.BVT
            status = TestCase.EnumStatus.Design
            tags = "base2"
            def run_test(self):
                pass
        tests = datadrive.load_datadrive_tests(Demo)
        self.assertEqual(len(tests), 2)
        self.assertEqual(tests[0].tags, set(["base", "eeelin"]))
        self.assertEqual(tests[1].tags, set(["base", "fff", "xxx"]))

    def test_set_attrs_doc(self):
        data = [
            {"value":"x", "__attrs__":{"__doc__": "doc"}},
            {"value":"x", "__attrs__":{"xxxx": ("fff","xxx")}},
        ]
        @datadrive.DataDrive(data)
        class Demo(TestCase):
            """base"""
            owner = "xxx"
            timeout = 1
            priority = TestCase.EnumPriority.BVT
            status = TestCase.EnumStatus.Design
            tags = "base2"
            def run_test(self):
                pass
        tests = datadrive.load_datadrive_tests(Demo)
        self.assertEqual(len(tests), 2)
        self.assertEqual(tests[0].test_doc, "doc")
        self.assertEqual(tests[1].test_doc, "base")