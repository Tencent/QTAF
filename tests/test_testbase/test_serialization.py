# -*- coding: utf-8 -*-
"""test serialization
"""

import unittest

from testbase.testcase import TestCase
from testbase.testsuite import SeqTestSuite, TestSuite
from testbase import serialization, datadrive

drive_data = [
    0,
    {
        "data": 1,
        "__attrs__": {
            "owner": "bar",
            "timeout": 5,
            "priority": TestCase.EnumPriority.BVT,
            "status": TestCase.EnumStatus.Implement,
            "tags": ("a", "b", "c"),
            "__doc__": "demo",
        },
    },
]


@datadrive.DataDrive(drive_data)
class FooTest(TestCase):
    """foo test"""

    owner = "foo"
    timeout = 1
    priority = TestCase.EnumPriority.High
    status = TestCase.EnumStatus.Ready

    def run_test(self):
        pass


class SerializationTest(unittest.TestCase):
    def test_normal_serialization(self):
        from tests.sampletest.hellotest import HelloTest

        hello = HelloTest()
        data = serialization.dumps(hello)
        deserialized_case = serialization.loads(data)
        self.assertEqual(type(deserialized_case), HelloTest)
        for attr in ["owner", "timeout", "priority", "status", "tags", "test_doc"]:
            self.assertEqual(getattr(deserialized_case, attr), getattr(hello, attr))

    def test_datadrive_serialization(self):
        tests = datadrive.load_datadrive_tests(FooTest, 1)
        self.assertEqual(len(tests), 1)
        test = tests[0]
        deserialized_test = serialization.loads(serialization.dumps(test))
        self.assertEqual(deserialized_test.owner, "bar")
        self.assertEqual(deserialized_test.timeout, 5)
        self.assertEqual(deserialized_test.priority, TestCase.EnumPriority.BVT)
        self.assertEqual(deserialized_test.status, TestCase.EnumStatus.Implement)
        self.assertEqual(deserialized_test.tags, set(["a", "b", "c"]))
        self.assertEqual(deserialized_test.test_doc, "demo")

    def test_serialize_seq_testsuite(self):
        from tests.sampletest.hellotest import HelloTest, TimeoutTest

        foo_test = datadrive.load_datadrive_tests(FooTest, 1)[0]
        testsuite = SeqTestSuite([HelloTest(), TimeoutTest(), foo_test])
        data = serialization.dumps(testsuite)
        deserialized_testsuite = serialization.loads(data)
        self.assertEqual(len(deserialized_testsuite), len(testsuite))
        for deserialized_test, test in zip(deserialized_testsuite, testsuite):
            self.assertEqual(type(deserialized_test), type(test))
            for attr in ["owner", "timeout", "priority", "status", "tags", "test_doc"]:
                self.assertEqual(getattr(deserialized_test, attr), getattr(test, attr))

    def test_serialize_testsuite(self):
        foo_test = datadrive.load_datadrive_tests(FooTest, 1)[0]
        testsuite = TestSuite([foo_test])
        data = serialization.dumps(testsuite)
        deserialized_testsuite = serialization.loads(data)
        self.assertEqual(len(deserialized_testsuite), len(testsuite))


if __name__ == "__main__":
    unittest.main(defaultTest="SerializationTest.test_serialize_testsuite")
