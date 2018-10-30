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
"""test cases for retry mechanism
"""


import time
import unittest

from testbase.retry import Retry, RetryLimitExcceeded
    

class TestRetry(unittest.TestCase):
    """test retry with invalid calllee
    """
    def test_retry_with_timeout(self):
        def dummy(toggle_time,start_ts):
            if time.time() - start_ts > toggle_time:
                return True
        
        interval = 1
        timeout = 5
        retry = Retry(interval=interval, timeout=timeout)
        self.assertRaises(ValueError, retry.call, None)
         
        start_time = time.time()
        try:
            retry.call(dummy, timeout+1, start_time)
        except RetryLimitExcceeded:
            time_cost = time.time() - start_time
            self.assertGreaterEqual(time_cost, 5, "actual timeout=%s is less than specified timeout=%s" % (time_cost, timeout))
        else:
            self.fail("no RetryLimitExcceeded raised")
         
        start_time = time.time()
        count = 0
        retry = Retry(interval=interval, timeout=timeout)
        for retry_item in retry:
            count += 1
            self.assertEqual(count, retry_item.iteration, "iteration does not match")
            if dummy(2, start_time):
                time_cost = time.time() - start_time
                self.assertGreaterEqual(time_cost, 2, "actual interval=%s is less than specified interval=%s" % (time_cost/float(count), interval))
                break
        else:
            self.fail("unexpected timeout")
            
            
    def test_retry_with_count(self):
        def dummy(param):
            param[0] += 1
            if param[0] > 2:
                return True            
        
        retry = Retry(limit=1)
        self.assertRaises(ValueError, retry.call, None)
             
        x = [0]
        try:
            retry.call(dummy, x)
        except RetryLimitExcceeded:
            pass
        else:
            self.fail("no RetryLimitExcceeded was raised")

        x = [0]
        retry = Retry(limit=3)
        try:
            retry.call(dummy, x)
        except RetryLimitExcceeded:
            self.fail("RetryLimitExcceeded was raised")
            
        x = [0]
        retry = Retry(limit=3, interval=None)
        retry_count = 0 
        start_time = time.time()
        for retry_item in retry:
            retry_count +=1
            self.assertEqual(retry_count, retry_item.iteration, "iteration does not match")
            if dummy(x):
                self.assertEqual(retry_count, 3, "iteration does not match")
                break
        time_cost = time.time() - start_time
        self.assertLess(time_cost, 0.05, "interval is unexpected")
            
        x = [-5]
        limit=3
        retry = Retry(limit=limit, interval=0.5, raise_error=False)
        start_time = time.time()
        retry.call(dummy, x)
        time_cost = time.time() - start_time
        self.assertGreaterEqual(time_cost, (limit-1)*0.5, "interval has no effect.")
        

if __name__ == "__main__":
    defaultTest="TestRetry.test_retry_with_count"
    defaultTest=None
    unittest.main(defaultTest=defaultTest)
