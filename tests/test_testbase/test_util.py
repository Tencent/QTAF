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
'''util test
'''

import unittest

import six

from testbase import util


class UtilTest(unittest.TestCase):

    def test_smart_binary(self):
        s = u'11111\udce444444'
        result = util.smart_binary(s)
        if six.PY3:
            self.assertEqual(result, b"'11111\\udce444444'")
        else:
            self.assertEqual(result, '11111\xed\xb3\xa444444')
