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
"""logger test
"""

import sys
import logging
import unittest
from testbase import logger
if sys.version_info < (3, 3):
    from imp import reload
else:
    from importlib import reload

class TestHandler(logging.Handler):
    def __init__(self, *args, **kwargs):
        super(logging.Handler, self).__init__(*args, **kwargs)
        self.messages = []

    def emit(self, record):
        self.messages.append(self.format(record))

    def format(self, record):
        return self.formatter.format(record)

class LoggerTest(unittest.TestCase):


    def test_set_formatter(self):
        try:
            handler = TestHandler()
            logger._stream_handler = handler

            logger.set_formatter('[%(message)s]')
            logger.info('www')
            last = handler.messages[-1]

            self.assertIn(b'[www]', last)
        finally:
            reload(logger)

    def test_set_log_level(self):
        try:
            handler = TestHandler()
            logger._stream_handler = handler

            logger.set_level(logging.ERROR)
            logger.info('www')

            self.assertTrue(len(handler.messages) == 0)
        finally:
            reload(logger)

if __name__ == '__main__':
    unittest.main()
