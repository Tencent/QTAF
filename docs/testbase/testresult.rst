处理测试结果
======

对于一个测试用例，其测试结果包括这个测试用例的执行通过与否，和对应的日志信息。

========
测试通过与不通过
========

对于QTA，判断一个测试用例是否通过的原则：

   * 测试用例类定义有问题，比如缺少DocString或必要属性，缺少run_test接口的实现。
   
   * 如果测试用例类定义正确，则当所有测试步骤都通过时，测试用例测试通过，否则测试用例不通过”。

而判断一个测试步骤是否通过，主要看是否出现以下任意一个情况：

   * 测试断言失败，即调用assert或wait_for系列的接口检查不通过
   
   * 测试代码问题，Python代码执行异常
   
   * 测试执行过程中，QTA内置的logger有错误级别的日志
   
第一种情况在前面《:doc:`./testcase`》章节已经有介绍，对于后面的两种情况，我们看下面的例子::

   class ExceptTest(TestCase):
       '''异常测试
       '''
       owner = "foo"
       status = TestCase.EnumStatus.Ready
       priority = TestCase.EnumPriority.Normal
       timeout = 1
   
       def run_test(self):
           #---------------------------
           self.start_step("异常测试")
           #---------------------------
           raise RuntimeError("抛异常")
           
以上的用例有问题，执行比如有会有异常抛出，因此测试结果是不通过的::

   ============================================================
   测试用例:ExceptTest 所有者:foo 优先级:Normal 超时:1分钟
   ============================================================
   ----------------------------------------
   步骤1: 异常测试
   CRITICAL: run_test执行失败
   Traceback (most recent call last):
     File "D:\workspace\qtaf5\testbase\testcase.py", line 550, in _thread_run
       getattr(self._testcase, it)()
     File "D:\workspace\qtaf5\test\hellotest.py", line 86, in run_test
       raise RuntimeError("抛异常")
   RuntimeError: 抛异常
   
   ============================================================
   测试用例开始时间: 2016-02-02 15:12:03
   测试用例结束时间: 2016-02-02 15:12:03
   测试用例执行时间: 00:00:0.02
   测试用例步骤结果:  1:失败
   测试用例最终结果: 失败
   ============================================================

再看看一个测试不通过的用例的例子::

   class LogErrorTest(TestCase):
       '''异常测试
       '''
       owner = "foo"
       status = TestCase.EnumStatus.Ready
       priority = TestCase.EnumPriority.Normal
       timeout = 1
   
       def run_test(self):
           #---------------------------
           self.start_step("异常测试")
           #---------------------------
           self.fail("异常发生")
           
   if __name__ == '__main__':
       ExceptTest().debug_run()
       
上面的用例是调用日志的接口，记录一个错误的日志，因此测试也不通过::

   ============================================================
   测试用例:LogErrorTest 所有者:foo 优先级:Normal 超时:1分钟
   ============================================================
   ----------------------------------------
   步骤1: 异常测试
   ERROR: 异常发生
   ============================================================
   测试用例开始时间: 2016-02-02 15:14:19
   测试用例结束时间: 2016-02-02 15:14:19
   测试用例执行时间: 00:00:0.01
   测试用例步骤结果:  1:失败
   测试用例最终结果: 失败
   ============================================================
   
====
测试日志
====

从前面测试用例的例子可以看到，测试结果主要包括几类信息：

 * 测试用例基本信息，如名称、负责、优先级等
 
 * 测试用例执行的基本信息，比如开始时间、结束时间
 
 * 测试用例执行结果，通过或不通过

 * 各个测试步骤的日志信息，包括测试步骤的名称、测试步骤通过与否，和测试步骤执行过程中的日志、断言失败信息等
 
前面三点的信息都是固定的，第四点的信息是基于测试用例的代码而变化的，像一些特殊的日志信息，比如断言失败的日志，会由用户的assert或wait_for接口产生。但是一般来说，用户可以通过下面两个接口记录日志::

   def log_info(self, info ):
      '''Log一条信息
      
      :type info: string
      :param info: 要Log的信息  
      '''
      
   def fail(self, message):
      '''测试用例失败
      
      :type message: string
      :param message: 要Log的信息  
      '''
      
以上两个接口在《:doc:`./testcase`》章节已经有介绍，从使用上，这两个接口只能在测试用例类的方法中使用，如果需要在测试用例之外的代码，比如lib层，则可以使用QTA内置的logger::

   from testbase import logger
   logger.info("hello")
   logger.error("error")
      
上面的代码等价于在测试用例中使用log_info和fail::

   self.log_info("hello")
   self.fail("error")

QTA内置的logger的接口和Python标准库的logging的logger是完全兼容的。


======
测试结果对象
======

对于一个测试用例对象，在执行过程中都会有一个test_result属性表示此测试用例对应的测试结果，我们也可以通过这个测试结果对象的接口去记录日志信息::

   self.test_result.info("hello")
   self.test_result.error("error")

上面的代码等价于在测试用例中使用log_info和fail::

   self.log_info("hello")
   self.fail("error")
   
test_result属性返回的类型为“:class:`testbase.testresult.TestResultBase`”，更多接口可以参考接口文档。
   
test_result的日志接口，无论info、error等，其实都是调用log_record实现，比如info的接口::

    def info(self, msg,  record=None, attachments=None):
        '''处理一个INFO日志
        '''
        self.log_record(EnumLogLevel.INFO, msg, record, attachments)
        
可以看到这里其实有两个另外的参数：record和attachments。record主要是给用户传递自定义的参数给自定义的测试结果对象，这块会在《:doc:`./testrun`》中讨论。而atachments参数表示的是测试用例的附加文件信息，比如截图、Dump文件或日志文件等。

下面是使用attachments参数的例子::

   self.test_result.info("这个是一个截图", attachments={"PC截图":"desktop.png"})
   
调试执行的结果::

   INFO: 这个是一个截图
   PC截图：desktop.png
   
attachments参数是一个字典，因此也支持多个附件::

   self.test_result.info("这个是全部截图", attachments={"PC截图":"desktop.png", "手机截图":"mobile.png"})
   
在调试执行是，附件的日志信息意义其实不大，但是对于其他执行方式，如果采用不同的测试结果格式（比如xml、网页报告），测试附件会直接附加在对应的测试结果中，方便用户分析测试用例问题。这块会在《:doc:`./testrun`》中讨论，这里也不展开讨论。

=======
测试日志的级别
=======

test_result的log_record接口第一个参数就是日志级别，比如对于info接口，其对应的日志的级别就是INFO。以下是test_result目前支持的全部日志级别信息::

   class EnumLogLevel(object):
      '''日志级别
      '''
      DEBUG = 10
      INFO = 20
      Environment = 21  #测试环境相关信息， device/devices表示使用的设备、machine表示执行的机器
      ENVIRONMENT = Environment
      
      WARNING = 30
      ERROR = 40
      ASSERT = 41 #断言失败，actual/expect/code_location
      CRITICAL = 60
      APPCRASH = 61 #测试目标Crash
      TESTTIMEOUT = 62 #测试执行超时
      RESNOTREADY = 69 #当前资源不能满足测试执行的要求
      
其中，INFO/WANRING/ERROR/CRITICAL的类型都是和Python的logging模块的日志级别对应的，是一般的日志级别。除此之外，ASSERT是在断言失败的时候使用，也就是wait_for_和assert_系列结果中使用，用户不用直接使用。TESTTIMEOUT和RESNOTREADY也是内置的类型，由测试框架调用，用户一般都不用使用。用户可以使用的剩下的两个特殊的日志级：ENVIRONMENT和APPCRASH。

ENVIRONMENT用于日志环境信息，比如测试用例使用PC、手机等信息，比如::
   
   self.test_result.log_record(EnumLogLevel.ENVIRONMENT, "测试用例执行机名称", {"machine":socket.gethostname()})
   self.test_result.log_record(EnumLogLevel.ENVIRONMENT, "使用移动设备", {"device":"01342300111222"})
   self.test_result.log_record(EnumLogLevel.ENVIRONMENT, "使用移动设备", {"devices":["93284972333", "21903948324923"]})
   
APPCRASH用于记录被测对象的Crash，比如::

   self.test_result.log_record(EnumLogLevel.APPCRASH, "QQ Crash", attachments={"QQ日志": "QQ.tlg", "QQ Dump": "QQ34ef450a.dmp"})

.. note::  ENVIRONMENT和APPCRASH约定的record参数类型并不是强制的，但是如果希望日志被内置的测试结果类型更好的处理，需要按照其约定来调用。
  
=====
异常时日志
=====

测试用例执行过程中有两种可能的异常情况，用例执行超时或者用例测试代码异常。在这种情况下，QTA一般会记录当时的堆栈信息，但是如果需要在这种情况增加更多的信息，比如当时的截图、环境信息等，则可以使用测试用例类的get_extra_fail_record接口。示例代码如下::

   class EnvLogOnExceptTest(TestCase):
       '''异常时记录IP和时间
       '''
       owner = "foo"
       status = TestCase.EnumStatus.Ready
       priority = TestCase.EnumPriority.Normal
       timeout = 1
   
       def run_test(self):
           raise RuntimeError("异常")
       
       def get_extra_fail_record(self):
           record, attachments = super(EnvLogOnExceptTest, self).get_extra_fail_record()
           record['当前IP'] = socket.gethostbyname(socket.gethostname())
           attachments['当前代码文件'] = __file__
           return record, attachments

get_extra_fail_record主要是提供一个hook点，可以在日志异常信息时，让测试用例去修改record和attachments参数。上面的例子就是在record和attachments增加了两项内容。

get_extra_fail_record是在日志级别为ERROR或者以上时被执行，也就是包括：

   * self.fail、logger.error和test_result.error产生ERROR级别的日志时
   
   * self.assert_和self.wait_for_系列接口断言失败时
   
   * 测试用例执行超时时
   
   * 测试用例执行异常时




   


   
   
      

