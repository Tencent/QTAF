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
"""重试机制实现
"""

import time
    
class _RetryItem(object):
    """
    """
    def __init__(self, iteration, timestamps=None):
        self.__iteration = iteration
        self.__ts = timestamps

    @property
    def iteration(self):
        return self.__iteration
    
    @property
    def ts(self):
        return self.__ts
    
    def __str__(self):
        return "<%s iter=%s, ts=%s>" % (self.__class__.__name__, self.__iteration, self.__ts)
            
    
class _RetryWithTimeout(object):
    """retry mechanism with timeout
    """
    def __init__(self,interval=5, timeout=60, raise_error=True):
        self.interval = interval
        self.timeout = timeout
        self.raise_error = raise_error
        self.__start_time = None
        self.__count = 0
    
    def __iter__(self):
        return self
    
    def next(self):
        if self.__start_time == None:
            self.__count += 1
            self.__start_time = time.time()
            return _RetryItem(self.__count, self.__start_time)
        else:
            time.sleep(self.interval)
            ts = time.time()
            if ts - self.__start_time < self.timeout:
                self.__count += 1
                return _RetryItem(self.__count, ts)
            else:
                if self.raise_error:
                    raise RetryLimitExcceeded("Procedure retried %s times in %ss" % (self.__count, self.timeout))
                else:
                    raise StopIteration
                
    __next__ = next
        
        
class _RetryWithCount(object):
    """retry mechanism with count
    """
    def __init__(self, limit=3, interval=0,raise_error=True):
        self.limit = limit
        self.raise_error = raise_error
        self.interval = interval
        self.__count = 0
        
    def __iter__(self):
        return self
    
    def next(self):
        self.__count += 1
        if self.__count <= self.limit:
            if self.__count !=1 and self.interval:
                time.sleep(self.interval)
            return _RetryItem(self.__count, time.time())
        if self.raise_error:
            raise RetryLimitExcceeded("Procedure retried for %s times with interval=%ss" % (self.limit, self.interval))
        else:
            raise StopIteration
        
    __next__ = next

        
class RetryLimitExcceeded(Exception):
    """maxmium retry limit excceeded error
    """
    pass

 
class Retry(object):
    """retry mechanism with timeout or limit
    """
    def __init__(self, timeout=10, limit=None, interval=0.5, raise_error=True):
        if limit:
            self._retry = _RetryWithCount(limit=limit, interval=interval, raise_error=raise_error)
        else:
            self._retry = _RetryWithTimeout(timeout=timeout, interval=interval, raise_error=raise_error)
        
    def __iter__(self):
        return self._retry.__iter__()
    
    def call(self, callee, *args, **kwargs):
        if not hasattr(callee, "__call__"):
            raise ValueError("callee must be a function instance")
        for _ in self:
            r = callee(*args, **kwargs)
            if r:
                return r
