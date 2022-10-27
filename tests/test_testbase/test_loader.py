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
"""loader test
"""

import unittest

from testbase.loader import TestLoader
from testbase.test import modify_settings

TestLoader.__test__ = False  # for nauseated Nose


class TestLoaderTest(unittest.TestCase):
    loader = TestLoader()

    def test_load_testcase(self):
        """load test cases from class path"""
        tests = self.loader.load("tests.sampletest.hellotest.HelloTest")
        self.assertEqual(len(tests), 1)
        from tests.sampletest.hellotest import HelloTest

        self.assertEqual(type(tests[0]), HelloTest)

    def test_load_failed_not_found(self):
        tests = self.loader.load("tests.sampletest.notfound")
        self.assertEqual(len(tests), 0)
        errors = self.loader.get_last_errors()
        self.assertEqual(len(errors), 1)
        self.assertIn("tests.sampletest.notfound", errors)
        self.assertRegexpMatches(
            list(errors.values())[0], "No module named .*notfound.*"
        )

    def test_load_failed_runtime_error(self):
        tests = self.loader.load("tests.sampletest.loaderr")
        self.assertEqual(len(tests), 0)
        errors = self.loader.get_last_errors()
        self.assertEqual(len(errors), 1)
        self.assertIn("tests.sampletest.loaderr", errors)
        self.assertIn("RuntimeError", list(errors.values())[0])

    def test_load_filter(self):
        filtered_test = "tests.sampletest.hellotest.HelloTest"

        def filter_func(test):
            if test.test_class_name == filtered_test:
                return "hello filtered"

        loader = TestLoader(filter_func)
        tests = loader.load("tests.sampletest")
        testnames = [it.test_class_name for it in tests]
        self.assertNotIn(filtered_test, testnames)
        tests = loader.get_filtered_tests()
        self.assertEqual(len(tests), 1)
        self.assertEqual(tests[0].test_class_name, filtered_test)
        result = loader.get_filtered_tests_with_reason()
        self.assertEqual(len(tests), 1)
        self.assertEqual(list(result.keys())[0].test_class_name, filtered_test)
        self.assertEqual("hello filtered", list(result.values())[0])

    def test_load_testcasedict(self):
        testcases = [
            {
                "name": "tests.sampletest.paramtest.ParamTest",
                "parameters": {"test": 200, "test1": 400},
            }
        ]
        with modify_settings(QTAF_PARAM_MODE=True):
            tests = self.loader.load(testcases)
            self.assertEqual(len(tests), 1)
            self.assertEqual(tests[0].test, 200)


class LoadDataDriveReversibleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.loader = TestLoader()

    def test_dict_data_reversible(self):
        """load test cases from dict data and can be reverted loaded"""
        from tests.sampletest.datatest import DataTest

        tests = self.loader.load("tests.sampletest.datatest.DataTest")
        self.assertEqual(len(tests), 3)
        self.assertEqual(type(tests[0]), DataTest)

        test_set = " ".join(map(lambda x: x.test_name, tests)).split()
        loader = TestLoader()
        new_tests = loader.load(test_set)
        self.assertEqual(len(new_tests), len(tests))

    def test_list_data_reversible(self):
        from tests.sampletest.datatest import ArrayDataTest

        tests = self.loader.load("tests.sampletest.datatest.ArrayDataTest")
        self.assertEqual(len(tests), 4)
        self.assertEqual(type(tests[0]), ArrayDataTest)

        test_set = " ".join(map(lambda x: x.test_name, tests)).split()
        loader = TestLoader()
        new_tests = loader.load(test_set)
        self.assertEqual(len(new_tests), len(tests))

    def test_empty_data_reversible(self):
        from tests.sampletest.datatest import EmptyDataTest

        tests = self.loader.load("tests.sampletest.datatest.EmptyDataTest")
        self.assertEqual(len(tests), 1)
        self.assertEqual(type(tests[0]), EmptyDataTest)

    def test_global_data_reversible(self):
        from tests.data import server

        with modify_settings(DATA_DRIVE=True, DATA_SOURCE="tests/data/server.py"):
            tests = TestLoader().load("tests.sampletest.hellotest.HelloTest")
            self.assertEqual(len(tests), 3)
            casedata = set()
            for test in tests:
                self.assertEqual(
                    test.test_class_name, "tests.sampletest.hellotest.HelloTest"
                )
                casedata.add(str(test.casedata))
            self.assertEqual(casedata, set([str(it) for it in server.DATASET]))

            test_set = " ".join(map(lambda x: x.test_name, tests)).split()
            loader = TestLoader()
            new_tests = loader.load(test_set)
            self.assertEqual(len(new_tests), len(tests))

    def test_bad_name_reversible(self):
        from tests.sampletest.datatest import BadCharCaseTest, bad_drive_data

        tests = self.loader.load("tests.sampletest.datatest.BadCharCaseTest")
        self.assertEqual(len(tests), len(bad_drive_data))
        self.assertEqual(type(tests[0]), BadCharCaseTest)

        test_set = " ".join(map(lambda x: x.test_name, tests)).split()
        loader = TestLoader()
        new_tests = loader.load(test_set)
        self.assertEqual(len(new_tests), len(tests))


if __name__ == "__main__":
    #     unittest.main(defaultTest="LoadDataDriveReversibleTest")
    unittest.main()
