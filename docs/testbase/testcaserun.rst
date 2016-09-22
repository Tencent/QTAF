执行测试用例
======

对于测试用例的执行，QTA也提供了一定的扩展能力。

====
重复执行
====

比如需要让一个测试用例重复执行多次::

   from testbase.testcase import TestCase, RepeatTestCaseRunner
   
   class RepeatTest(TestCase):
       '''测试示例
       '''
       owner = "eeelin"
       status = TestCase.EnumStatus.Ready
       timeout = 1
       priority = TestCase.EnumPriority.Normal
       case_runner = RepeatTestCaseRunner()
       repeat = 2
       
       def runTest(self):
           self.logInfo('第%s次测试执行'%self.iteration)
   
   
   if __name__ == '__main__':
       HelloTest().debug_run()
       
这个用例和一般用例的区别是：

   * 增加repeat属性，用于指定要重复执行的次数
   
   * case_runner属性，指定了一个“:class:`testbase.testcase.RepeatTestCaseRunner`”实例
   
直接执行以上代码，输出为::
   
   ============================================================
   测试用例:RepeatTest 所有者:eeelin 优先级:Normal 超时:1分钟
   ============================================================
   INFO: 第0次测试执行
   ============================================================
   测试用例开始时间: 2015-07-16 20:17:11
   测试用例结束时间: 2015-07-16 20:17:11
   测试用例执行时间: 00:00:0.00
   测试用例步骤结果:  1:通过
   测试用例最终结果: 通过
   ============================================================
   ============================================================
   测试用例:RepeatTest 所有者:eeelin 优先级:Normal 超时:1分钟
   ============================================================
   INFO: 第1次测试执行
   ============================================================
   测试用例开始时间: 2015-07-16 20:17:11
   测试用例结束时间: 2015-07-16 20:17:11
   测试用例执行时间: 00:00:0.00
   测试用例步骤结果:  1:通过
   测试用例最终结果: 通过
   ============================================================
   
可以看到测试用例被执行了两次，而且每次执行的时候，用例成员变量iteration都会增加1。

======
控制执行顺序
======

对于一些极端的情况下，需要控制测试用例的执行顺序。比如执行测试用例A、B、C需要按照一定先A、后B、再C的顺序来执行。

.. warning:: QTA不推荐测试用例之间存在依赖关系，这样对于用例的可读性和后续的维护都会带来麻烦，所以不推荐控制用例按照顺序来执行。


例如下面一个控制执行顺序的例子::

   from testbase import TestCase
   from testbase.testcase import RepeatTestCaseRunner
   
   class TestA(TestCase):
       '''测试示例
       '''
       timeout = 1
       owner = "eeelin"
       status = TestCase.EnumStatus.Ready
       priority = TestCase.EnumPriority.Normal
       
       def run_test(self):
           pass
       
   class TestB(TestCase):
       '''测试示例
       '''
       timeout = 1
       owner = "eeelin"
       status = TestCase.EnumStatus.Ready
       priority = TestCase.EnumPriority.Normal
       case_runner = RepeatTestCaseRunner()
       repeat = 2
   
       def run_test(self):
           pass
       
   class TestC(TestCase):
       '''测试示例
       '''
       timeout = 1
       owner = "eeelin"
       status = TestCase.EnumStatus.Ready
       priority = TestCase.EnumPriority.Normal
       
       def run_test(self):
           pass
       
   __qtaf_seq_tests__ = [TestA, TestB, TestC]
   
   if __name__ == '__main__':    
       from testbase.testcase import debug_run_all
       debug_run_all()


以上用例和普通的用例完全一致，不一样的地方是在模块中定义了变量qtaf_seq_tests ，这个变量就是用来指定测试用例的执行顺序。需要注意的是，如果要指定测试用例按照顺序执行，这些用例的实现都必须放在同一个代码文件中，这样限制的目的是为了提高代码的可读性。

以上的例子的执行结果如下::

   ============================================================
   测试用例:TestA 所有者:eeelin 优先级:Normal 超时:1分钟
   ============================================================
   ============================================================
   测试用例开始时间: 2015-07-16 20:24:46
   测试用例结束时间: 2015-07-16 20:24:46
   测试用例执行时间: 00:00:0.00
   测试用例步骤结果:  1:通过
   测试用例最终结果: 通过
   ============================================================
   ============================================================
   测试用例:TestB 所有者:eeelin 优先级:Normal 超时:1分钟
   ============================================================
   ============================================================
   测试用例开始时间: 2015-07-16 20:24:46
   测试用例结束时间: 2015-07-16 20:24:46
   测试用例执行时间: 00:00:0.00
   测试用例步骤结果:  1:通过
   测试用例最终结果: 通过
   ============================================================
   ============================================================
   测试用例:TestB 所有者:eeelin 优先级:Normal 超时:1分钟
   ============================================================
   ============================================================
   测试用例开始时间: 2015-07-16 20:24:46
   测试用例结束时间: 2015-07-16 20:24:46
   测试用例执行时间: 00:00:0.00
   测试用例步骤结果:  1:通过
   测试用例最终结果: 通过
   ============================================================
   ============================================================
   测试用例:TestC 所有者:eeelin 优先级:Normal 超时:1分钟
   ============================================================
   ============================================================
   测试用例开始时间: 2015-07-16 20:24:46
   测试用例结束时间: 2015-07-16 20:24:46
   测试用例执行时间: 00:00:0.00
   测试用例步骤结果:  1:通过
   测试用例最终结果: 通过
   ============================================================
       
=======
自定义执行方式
=======

对于一般的测试用例的执行，QTA是按照下面的流程处理的：

   1. 获取尝试测试用例对应的case_runner静态变量，如果不存在，则设置case_runner为一个“:class:`testbase.testcase.TestCaseRunner`”实例

   2. 使用case_runner去执行对应的用例
   
因此，每个测试用例都可以通过指定这个case_runner来重载用例的执行逻辑。前面的重复执行用例的例子，就是通过“:class:`testbase.testcase.RepeatTestCaseRunner`”来实现的。

测试用例指定的case_runner要符合一定的接口规范，这个接口就是“:class:`testbase.testcase.ITestCaseRunner`”，其定义如下::

   class ITestCaseRunner(object):

      def run(self, testcase, testresult_factory ):
         """执行一个用例
         
         :param testcase: 测试用例
         :type testcase: TestCase
         :param testresult_factory: 测试结果对象工厂
         :type testresult_factory: ITestResultFactory
         :rtype: TestResult/TestResultCollection
         """
         pass
        
下面以一个例子来示例如果重载case_runner来指定一个测试用例执行的时候重复执行多次，也就是实现一个我们自己的版本的RepeatTestCaseRunner::

   from testbase.testresult import TestResultCollection
   from testbase.testcase import ITestCaseRunner, TestCaseRunner
   
   class RepeatTestCaseRunner(ITestCaseRunner):
   
       def run(self, testcase, testresult_factory ):
           passed = True
           results = []
           for _ in range(testcase.repeat):
               result = TestCaseRunner().run(testcase, testresult_factory)
               results.append(result)
               passed &= result.passed
               if not passed: #有一次执行不通过则中止执行
                   break
           return TestResultCollection(results, passed)
   