# -*- coding: utf-8 -*-

import testbase

class InitTest(testbase.TestCase):
    """QT4i测试用例"""

    owner = "foo"
    status = testbase.TestCase.EnumStatus.Ready
    timeout = 0.1
    priority = testbase.TestCase.EnumPriority.Normal

    def run_test(self):
        pass