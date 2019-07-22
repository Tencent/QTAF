# -*- coding: UTF-8 -*-
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
"""Test plan
"""


class TestPlan(object):
    """测试计划
    """
    tests = None
    test_target_args = {}

    def get_tests(self):
        """获取测试用例定义

        :rtypes: str/list(str)/list(TestCase)/TestCaseSettings
        """
        if self.tests is None:
            raise ValueError("%s's class member tests is not specified" % type(self))
        return self.tests

    def get_test_target(self):
        """获取被测对象

        :return: 被测对象信息
        :rtypes: dict
        """
        if isinstance(self.test_target_args, dict):
            return self.test_target_args
        raise ValueError("`test_target_args` is not a dictionary, please overwrite `get_test_target` for your custom implenmentation")

    def test_setup(self, report):
        """测试初始化步骤
        """
        pass

    def test_teardown(self, report):
        """测试清理步骤
        """
        pass

    def resource_setup(self, report, restype, resource):
        """测试资源初始化
        """
        pass

    def resource_teardown(self, report, restype, resource):
        """测试资源清理
        """
        pass

    def debug_run(self, report=None, resmgr_backend=None):
        """调试执行
        """
        from testbase.runner import TestRunner
        from testbase.report import StreamTestReport
        if report is None:
            report = StreamTestReport()
        return TestRunner(report, resmgr_backend=resmgr_backend).run(self)
