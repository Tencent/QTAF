# -*- coding: utf-8 -*-
'''testcase test
'''
#2017/11/13 eeelin created

from testbase.loader import TestLoader
import unittest


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
    