# -*- coding: utf-8 -*-
'''
模块描述
'''
#2012-11-20  allenpan  - Created
#2013-01-15  aaronlai  - 已经没有htmlcontrols和htmlcontrols2模块，修改测试用例
#2013-01-15  aaronlnai - 空构造函数抛出TypeError
import testbase
import tuia.webcontrols as web
from testbase import logger
import time
from pyqq.account import QQAccount
from testbase.datadrive import DataDrive

class HelloTest(testbase.TestCase):
    '''测试示例
    '''
    owner = "allenpan&eeelin"
    status = testbase.TestCase.EnumStatus.Ready
    timeout = 1
    priority = testbase.TestCase.EnumPriority.Normal
    
    def runTest(self):
        #-----------------------------
        self.startStep("测试webcontrols.WebElement构造函数")
        #-----------------------------        
        try:
            web.WebElement()
        except TypeError:
            pass
        except:
            self.fail("空构造函数没有抛出TypeError")
        
        #-----------------------------
        self.startStep("测试webcontrols.WebPage构造函数")
        #-----------------------------
        try:
            web.WebPage()
        except TypeError:
            pass
        except:
            self.fail("空构造函数没有抛出TypeError")
            
        logger.info("QTA日志", extra=dict(attachments={"qq.tlg":"xxxxxxxxx.tlg", "qta.log": "yyyyyyyyyyyy.log"}))
        
class TimeoutTest(testbase.TestCase):
    '''超时示例
    '''
    owner = "eeelin"
    status = testbase.TestCase.EnumStatus.Ready
    timeout = 0.1
    priority = testbase.TestCase.EnumPriority.Normal
    
    def runTest(self):
        time.sleep(7)
        
        
class ResourceNotReadyTest(testbase.TestCase):
    '''资源申请失败示例
    '''
    owner = "eeelin"
    status = testbase.TestCase.EnumStatus.Ready
    timeout = 0.1
    priority = testbase.TestCase.EnumPriority.Normal
    
    def runTest(self):
        acc = QQAccount.acquire({'groupName':"eeelin"})
        acc = QQAccount.acquire({'groupName':"eeelin"})
        
        
class RawInputTest(testbase.TestCase):
    '''模拟RawInput
    '''
    owner = "eeelin"
    status = testbase.TestCase.EnumStatus.Ready
    timeout = 0.1
    priority = testbase.TestCase.EnumPriority.Normal
    
    def runTest(self):
        print raw_input('xxxxxxxxx')
        
        
@DataDrive(it for it in range(10))
class DataTest(testbase.TestCase):
    '''模拟RawInput
    '''
    owner = "eeelin"
    status = testbase.TestCase.EnumStatus.Ready
    timeout = 1
    priority = testbase.TestCase.EnumPriority.Normal
    
    def runTest(self):
        if self.casedata / 2 == 0:
            raise RuntimeError("XX")
        print self.casedata
        
# def debug_run( target=None ):
#     '''调试执行当前脚本的全部用例
#     '''    
#     from testbase.loader import TestLoader
#     from testbase.runner import TestRunner
#     from testbase.report import StreamTestReport
#     tests = TestLoader().load("__main__")
#     filtered_tests = []
#     if isinstance(target, basestring):
#         names = target.split()
#         for it in tests:
#             if it.test_name in names:
#                 filtered_tests.append(it)
#     
#     elif isinstance(target, type):
#         for it in tests:
#             if type(it) == target:
#                 filtered_tests.append(it)
#     else:
#         filtered_tests = tests
# 
#     runner = TestRunner(StreamTestReport(output_testresult=True, output_summary=True))
#     runner.run(filtered_tests)
    
    
    
if __name__ == '__main__':
    #DataTest().debug_run()
    from testbase.testcase import debug_run_all
    HelloTest().debug_run()
    #debug_run_all()
    #debug_run()
    #debug_run("RawInputTest")
    
    
    