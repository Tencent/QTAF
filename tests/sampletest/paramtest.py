# -*- coding: utf-8 -*-
'''
参数测试用例
'''

import testbase


class ParamTestWithoutAddParams(testbase.TestCase):
    '''参数测试用例
    '''
    owner = "foo"
    status = testbase.TestCase.EnumStatus.Ready
    timeout = 0.1
    priority = testbase.TestCase.EnumPriority.Normal

    def runTest(self):
        self.assert_('不存在test', 'test' not in self.__dict__)
        self.assert_('不存在test1', 'test1' not in self.__dict__)

class ParamTest(testbase.TestCase):
    '''参数测试用例
    '''
    owner = "foo"
    status = testbase.TestCase.EnumStatus.Ready
    timeout = 0.1
    priority = testbase.TestCase.EnumPriority.Normal

    def add_params(self):
        self.add_param("test", int, default=100)
        self.add_param("test1", int, default=100)

    def runTest(self):
        self.assert_('存在test', 'test' in self.__dict__)
        self.assert_('存在test1', 'test1' in self.__dict__)

        self.assert_equal('断言test', self.test, 100)
        self.assert_equal('断言test1', self.test1, 100)

class ParamOverWriteTest(testbase.TestCase):
    '''参数测试用例
    '''
    owner = "foo"
    status = testbase.TestCase.EnumStatus.Ready
    timeout = 0.1
    priority = testbase.TestCase.EnumPriority.Normal

    def add_params(self):
        self.add_param("test", int, default=100)
        self.add_param("test1", int, default=100)

    def runTest(self):
        self.assert_('存在test', 'test' in self.__dict__)
        self.assert_('存在test1', 'test1' in self.__dict__)

        self.assert_equal('断言test', self.test, 200)
        self.assert_equal('断言test1', self.test1, 400)




if __name__ == '__main__':
    ParamTest().run()
