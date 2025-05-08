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
"""util test
"""

import threading
import time
import unittest
import sys

import six

from testbase import util
from testbase.test import modify_settings


class UtilTest(unittest.TestCase):
    def test_smart_binary(self):
        s = u"11111\udce444444"
        result = util.smart_binary(s)
        if six.PY3:
            self.assertEqual(result, b"'11111\\udce444444'")
        else:
            self.assertEqual(result, "11111\xed\xb3\xa444444")

    def test_timeout_lock(self):
        if sys.version_info[0] == 2:
            return
        timeout = 5
        lock1 = util.TimeoutLock(timeout)
        time0 = time.time()
        with lock1:
            pass
        time_cost = time.time() - time0
        self.assertLess(time_cost, 0.1)
        def lock_thread():
            with lock1:
                print('lock1 acquired in thread')
                time.sleep(2)

        t = threading.Thread(target=lock_thread)
        t.daemon = True
        t.start()
        time.sleep(0.1)
        time0 = time.time()
        with lock1:
            print('lock1 acquired')
            time_cost = time.time() - time0
            self.assertGreater(time_cost, 1.5)

    def test_timeout_lock_deadlock(self):
        if sys.version_info[0] == 2:
            return
        timeout = 5
        lock1 = util.TimeoutLock(timeout)
        lock2 = threading.RLock()
        def lock_thread():
            with lock1:
                print('lock1 acquired in thread')
                time.sleep(1)
                with lock2:
                    print('lock2 acquired in thread')
        t = threading.Thread(target=lock_thread)
        t.daemon = True
        t.start()
        time.sleep(0.1)
        time0 = time.time()
        with lock2:
            print('lock2 acquired')
            time.sleep(1)
            with lock1:
                print('lock1 acquired')
        time_cost = time.time() - time0
        self.assertGreater(time_cost, timeout + 1)
        self.assertLess(time_cost, timeout + 1.5)

    def test_get_last_frame_stack(self):
        def func_wrapper():
            return util.get_last_frame_stack(2)
        stack = func_wrapper()
        assert "func_wrapper" in stack
        with modify_settings(QTAF_STACK_FILTERS=["func_wrapper"]):
            stack = func_wrapper()
            assert "func_wrapper" not in stack
