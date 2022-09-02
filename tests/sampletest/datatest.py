# -*- coding: utf-8 -*-
"""
数据驱动测试用例
"""

import testbase
from testbase import datadrive
from testbase import context


@datadrive.DataDrive(
    {
        "TEST1": 1,
        "TEST2": 2,
        "TEST3": 3,
    }
)
class DataTest(testbase.TestCase):
    """数据驱动测试用例"""

    owner = "foo"
    status = testbase.TestCase.EnumStatus.Ready
    timeout = 0.1
    priority = testbase.TestCase.EnumPriority.Normal

    def runTest(self): # pylint: disable=invalid-name
        self.logInfo(str(self.casedata))


@datadrive.DataDrive([0])
class SingleDataTest(testbase.TestCase):
    """数据驱动测试用例"""

    owner = "foo"
    status = testbase.TestCase.EnumStatus.Ready
    timeout = 0.1
    priority = testbase.TestCase.EnumPriority.Normal

    def runTest(self): # pylint: disable=invalid-name
        self.logInfo(str(self.casedata))


@datadrive.DataDrive([])
class EmptyDataTest(testbase.TestCase):
    """数据驱动测试用例"""

    owner = "foo"
    status = testbase.TestCase.EnumStatus.Ready
    timeout = 0.1
    priority = testbase.TestCase.EnumPriority.Normal

    def runTest(self): # pylint: disable=invalid-name
        self.logInfo(str(self.casedata))


@datadrive.DataDrive(["A", "V", "XX", 0])
class ArrayDataTest(testbase.TestCase):
    """数据驱动测试用例"""

    owner = "foo"
    status = testbase.TestCase.EnumStatus.Ready
    timeout = 0.1
    priority = testbase.TestCase.EnumPriority.Normal

    def runTest(self): # pylint: disable=invalid-name
        self.logInfo(str(self.casedata))


class ProjDataTest(testbase.TestCase):
    """项目级别数据驱动测试用例"""

    owner = "foo"
    status = testbase.TestCase.EnumStatus.Ready
    timeout = 0.1
    priority = testbase.TestCase.EnumPriority.Normal

    def runTest(self): # pylint: disable=invalid-name
        self.logInfo(str(context.current_testcase().casedata))
        self.logInfo(str(self.casedata))


bad_names = [
    "foo test",
    "a&b",
    "2*2",
    "5-1",
    "foo|bar",
    "ok?",
    "about<xxx>",
    "10/2",
    "go~",
    "a=1",
    "a(good)",
    "b[bad]",
]

bad_drive_data = dict(zip(bad_names, bad_names))


@datadrive.DataDrive(bad_drive_data)
class BadCharCaseTest(testbase.TestCase):
    """bad char test"""

    owner = "foo"
    timeout = 1
    priority = testbase.TestCase.EnumPriority.High
    status = testbase.TestCase.EnumStatus.Ready

    def run_test(self):
        self.log_info('bad char test\'s case name is "%s"' % self.test_name)


if __name__ == "__main__":
    #     DataTest().run()
    #     DataTest(3).run()
    ProjDataTest().run()
