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
#2017/11/13 olive created

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
    