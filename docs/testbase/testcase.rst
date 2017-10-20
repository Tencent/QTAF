设计测试用例
======

========
最简单的测试用例
========

下面我们来编写第一个QTA测试用例，在测试项目中新建一个hello.py::

   from testbase.testcase import TestCase

   class HelloTest(TestCase):
       '''第一个测试用例
       '''
       owner = "eeelin"
       status = TestCase.EnumStatus.Ready
       priority = TestCase.EnumPriority.Normal
       timeout = 1
   
       def run_test(self):
           #---------------------------
           self.start_step("第一个测试步骤")
           #---------------------------
           self.log_info("hello")
           
           
可以看到，这个最简单的测试用例包括以下主要的部分：

   * 一个测试用例就是一个Python类，类的名称就是测试用例名，类的DocString就是测试用例的简要说明文档。注意DocString对于QTA测试用例而言是必要的，否则会导致执行用例失败。
   
   * 测试用例类包括四个必要的属性：
   
      * owner，测试用例负责人，必要属性。
      
      * status，测试用例状态，必要属性。目前测试用例有五种状态：Design、Implement、Review、Ready、Suspend。
      
      * priority，测试用例优先级，必要属性。目前测试用例有四种优先级：BVT、High、Normal和Low。
      
      * timeout，测试用例超时时间，必要属性，单位为分钟。超时时间用于指定测试用例执行的最长时间，如果测试用例执行超过此时间，执行器会停止用例执行，并认为用例执行超时，测试不通过。一般来说，不建议这个时间设置得太长，如果用例需要比较长的执行时间，可以考虑拆分为多个测试用例。
  
  * run_test函数：这个是测试逻辑的代码，每个测试用例只有一个唯一的run_test函数；但每个测试用例可以划分为多个测试步骤，测试步骤以start_step函数调用来分隔。
  
以上的测试用例并没有任何测试逻辑，只是调用接口打印一行日志。

.. note:: 由于历史的原因，QTA很多接口的函数有两种代码风格的版本，比如上面的run_test、log_info，就有对应的mixedCase的版本runTest、logInfo。一般情况下，建议和测试项目已有的代码使用一致的风格的接口，如果是新项目，推荐使用lower_with_under风格的接口。

====
调试执行
====

测试用例编写后，需要进行调试执行。需要在hello.py中增加以下的代码::

   if __name__ == '__main__':
      HelloTest().debug_run()

如果使用的是IDE，在eclipse中，通过“CTRL + F11”快捷键执行当前hello.py脚本，可以看到输出如下::
 
   ============================================================
   测试用例:HelloTest 所有者:eeelin 优先级:Normal 超时:1分钟
   ============================================================
   ----------------------------------------
   步骤1: 第一个测试步骤
   INFO: hello
   ============================================================
   测试用例开始时间: 2015-04-27 12:51:59
   测试用例结束时间: 2015-04-27 12:51:59
   测试用例执行时间: 00:00:0.00
   测试用例步骤结果:  1:通过
   测试用例最终结果: 通过
   ============================================================
    
如果没有使用IDE，可以通过manage.py执行单个用例::

   $ python manage.py runscript footest/hello.py

   
在命令行窗口可以看到一样的执行输出::  

   ============================================================
   测试用例:HelloTest 所有者:eeelin 优先级:Normal 超时:1分钟
   ============================================================
   ----------------------------------------
   步骤1: 第一个测试步骤
   INFO: hello
   ============================================================
   测试用例开始时间: 2015-04-27 12:51:59
   测试用例结束时间: 2015-04-27 12:51:59
   测试用例执行时间: 00:00:0.00
   测试用例步骤结果:  1:通过
   测试用例最终结果: 通过
   ============================================================
      
====
测试断言
====

上面的测试代码没有任何测试的逻辑，并不算是一个完整的测试用例。下面我们通过一个例子来介绍QTA的两个测试检查接口。

假设我们需要测试一个字符串拼接的函数::

   def string_combine(a,b):
      return a+b
      
测试用例的代码如下::

   from testbase.testcase import TestCase

   class StrCombineTest(TestCase):
       '''测试字符串拼接接口
       '''
       owner = "eeelin"
       status = TestCase.EnumStatus.Ready
       priority = TestCase.EnumPriority.Normal
       timeout = 1
   
       def run_test(self):
           #---------------------------
           self.start_step("测试字符串拼接")
           #---------------------------
           result = string_combine("xxX", "yy")
           self.assert_equal("检查string_combine调用结果", result, "xxXyy")
      
以上的代码执行结果如下::

   ============================================================
   测试用例:StrCombineTest 所有者:eeelin 优先级:Normal 超时:1分钟
   ============================================================
   ----------------------------------------
   步骤1: 测试字符串拼接
   ============================================================
   测试用例开始时间: 2016-02-02 14:10:21
   测试用例结束时间: 2016-02-02 14:10:21
   测试用例执行时间: 00:00:0.00
   测试用例步骤结果:  1:通过
   测试用例最终结果: 通过
   ============================================================
   
可以看到结果是测试通过的，但是如果string_combine实现有问题，比如我们新定义一个string_combine2::

   def string_combine2(a,b):
      return a+'b'
      
以为以上的实现是有问题，执行结果必然是不通过的::

   ============================================================
   测试用例:StrCombineTest 所有者:eeelin 优先级:Normal 超时:1分钟
   ============================================================
   ----------------------------------------
   步骤1: 测试字符串拼接
   ASSERT: 检查string_combine2调用结果
      实际值：xxXb
      期望值：xxXyy
     File "D:\workspace\qtaf5\test\hellotest.py", line 87, in run_test
   ============================================================
   测试用例开始时间: 2016-02-02 14:11:45
   测试用例结束时间: 2016-02-02 14:11:45
   测试用例执行时间: 00:00:0.00
   测试用例步骤结果:  1:失败
   测试用例最终结果: 失败
   ============================================================
   
可以看到除了测试不通过外，测试结果还显示了断言失败的详细信息，包括预期值、实际值和对应的代码行。

这个就是QTA提供的测试断言的函数接口，其详细的定义如下::

    def assert_equal(self, message, actual, expect=True):
        '''检查实际值和期望值是否相等，不同则测试用例失败
        
       :param message: 检查信息
       :param actual: 实际值
       :param expect: 期望值(默认：True)
       :return: True or False
        '''

除了这个，QTA还提供另一个版本的断言函数::

    def assert_match(self, message, actual, expect):
        '''检查actual和expect是否模式匹配，不匹配则记录一个检查失败
        
        :type message: string
        :param message: 失败时记录的消息
        :type actual: string
        :param actual: 需要匹配的字符串
        :type expect: string
        :param expect: 要匹配的正则表达式 
        :return: True or False
        '''
assert_match和assert_equal的区别是，assert_match使用的是正则匹配而不是严格匹配，比如::

   self.assert_equal("严格匹配断言", "XXX", "X*")
   
以上的断言是不通过的，但是对于下面的正则断言是通过的::

   self.assert_match("正则匹配断言", "XXX", "X*")
   
assert_match和assert_equal相比，还有一个区别就是，assert_match只支持字符串或字符串兼容的类型的值的检查；但是assert_equal可以支持大部分类型的值的检查。

=====
忙等待检查
=====

以上的两个断言的检查的接口，都是检查某个时刻的被测系统的状态。但是对于一些系统，特别是UI，如果仅仅调用assert_equal和assert_match接口去检查当前的状态其实是不恰当的。

例如，一个表单的UI界面，如果点击“提交”后，我们需要检查“提交”按钮变为不可点击的状态，测试用例可能是这样的::

   form.controls['提交按钮'].click()
   self.assert_equal("检查“提交”按钮变为不可点击的状态", form.controls['提交按钮'].enable, False)
   
上面的测试用例，存在一个问题，就是点击“提交”之后，“提交”按钮的状态的更新并不是同步的，可能由于被测系统响应慢了一点点，就会导致测试检查不通过，所以上面的测试用例代码段应该修改为::

   form.controls['提交按钮'].click()
   start = time.time()
   while time.time()-start > 2:
      if not form.controls['提交按钮'].enable:
         break
      else:
         time.sleep(0.2)
   else:
      raise RuntimeError("等待超过2秒还是可以点击")
      
以上的测试代码是在2秒之内，多次去检查“提交”按钮的状态是否符合预期。通过这样的“平滑”的方式，就可以避免由于被测系统状态同步问题而导致测试不稳定。

但是上面的测试代码还是相当复杂的，因此QTA测试用例提供了两个接口来帮忙解决这类问题::

    def wait_for_equal(self, message, obj, prop_name, expected, timeout=10, interval=0.5):
        '''每隔interval检查obj.prop_name是否和expected相等，如果在timeout时间内都不相等，则测试用例失败

        :param message: 失败时的输出信息
        :param obj: 需要检查的对象
        :type prop_name: string 
        :param prop_name: 需要检查的对象的属性名，支持多层属性
        :param expected: 期望的obj.prop_name值
        :param timeout: 超时秒数
        :param interval: 重试间隔秒数
        :return: True or False
        '''
        
    def wait_for_match(self, message, obj, prop_name, expected, timeout=10, interval=0.5):
        '''每隔interval检查obj.prop_name是否和正则表达式expected是否匹配，如果在timeout时间内都不相等，则测试用例失败

        :param message: 失败时的输出信息
        :param obj: 需要检查的对象
        :type prop_name: string 
        :param prop_name: 需要检查的对象的属性名, obj.prop_name返回字符串
        :param expected: 需要匹配的正则表达式
        :param timeout: 超时秒数
        :param interval: 重试间隔秒数
        :return: True or False
        '''
        
这两个其实就是assert_equal和assert_match的忙等待检查版本，通过wait_for系列的接口，上面的测试代码就可以简化为::

   form.controls['提交按钮'].click()
   self.wait_for_equal("检查提交按钮变为不可点击", form.controls['提交按钮'], "enable", False,
                       timeout=2, interval=0.2)


======
测试执行控制
======

QTA测试用例的代码的执行控制逻辑和一般Python的代码是类似的，所以除了执行过程中出现Python异常或用例执行超时，测试用例会一直执行。而且，即使是assert_和wait_for_系列的接口失败了，也会继续执行，比如下面的例子::

   class CtrlTest(TestCase):
       '''流程控制测试
       '''
       owner = "eeelin"
       status = TestCase.EnumStatus.Ready
       priority = TestCase.EnumPriority.Normal
       timeout = 1
   
       def run_test(self):
           #---------------------------
           self.start_step("断言失败")
           #---------------------------
           self.assert_equal("检查断言", True, False)
           
           #---------------------------
           self.start_step("第二个步骤")
           #---------------------------
           self.log_info("hello")

上面的第一个测试步骤中，有一个断言是必然失败的，但是第二个测试步骤还是会被正常执行::

   ============================================================
   测试用例:CtrlTest 所有者:eeelin 优先级:Normal 超时:1分钟
   ============================================================
   ----------------------------------------
   步骤1: 断言失败
   ASSERT: 检查断言
      实际值：True
      期望值：False
     File "D:\workspace\qtaf5\test\hellotest.py", line 86, in run_test
   ----------------------------------------
   步骤2: 第二个步骤
   INFO: hello
   ============================================================
   测试用例开始时间: 2016-02-02 15:27:29
   测试用例结束时间: 2016-02-02 15:27:29
   测试用例执行时间: 00:00:0.00
   测试用例步骤结果:  1:失败 2:通过
   测试用例最终结果: 失败
   ============================================================

.. note:: 对于断言失败的执行逻辑处理，这个是QTA测试框架和其他一般测试框架比较大的差异点，设计测试用例是需要注意。

       
==========
测试环境初始化和清理
==========
        
在前面的例子中，我们在测试用例类的run_test实现了测试的主要逻辑，这里我们引入两个新的接口pre_test和post_test。

假设我们的用例需要临时配置一个本地host域名，示例代码如下::

   from testbase.testcase import TestCase
   
   class EnvTest1(TestCase):
       '''环境构造测试
       '''
       owner = "eeelin"
       status = TestCase.EnumStatus.Ready
       priority = TestCase.EnumPriority.Normal
       timeout = 1
   
       def run_test(self):
   
           _add_host("www.qq.com", "11.11.12.12")
   
           # main test logic here
           # ...
                     
           _del_host("www.qq.com", "11.11.12.12")
      
以上的代码在逻辑，在用例正常执行完成的情况下是完全正确的，但是这里存在一个问题，就是当run_test测试过程中，由于测试目标bug或者脚本问题导致run_test异常终止，则可能导致host配置没有删除，则可能影响到后面的测试用例。如何解决这个问题呢？QTA为此提供了post_test接口。
   
下面是使用post_test接口的新版本的测试用例代码::

   from testbase.testcase import TestCase
   
   class EnvTest2(TestCase):
       '''环境构造测试
       '''
       owner = "eeelin"
       status = TestCase.EnumStatus.Ready
       priority = TestCase.EnumPriority.Normal
       timeout = 1
   
       def run_test(self):
   
           _add_host("www.qq.com", "11.11.12.12")
   
           # main test logic 
           # ...
             
       def post_test(self):
           super(EnvTest2, self).post_test()        
           _del_host("www.qq.com", "11.11.12.12")
   

QTA执行用例的接口是先执行run_test，然后执行post_test；而且即使测试用例执行run_test中发生异常，仍会执行post_test，这样就保证了测试环境的清理操作。

.. note:: 虽然使用post_test可以保证清理环境，但是还是要注意清理环境的逻辑要尽量简单，否则清理环境时发生异常，也会导致清理动作未完成。

和post_test对应，QTA还提供了pre_test接口，从名字上看以看出，pre_test的作用主要是用于测试环境的构造和初始化，下面是使用pre_test的例子::

   class EnvTest3(TestCase):
       '''环境构造测试
       '''
       owner = "eeelin"
       status = TestCase.EnumStatus.Ready
       priority = TestCase.EnumPriority.Normal
       timeout = 1
       
       def pre_test(self):
           _add_host("www.qq.com", "11.11.12.12")
           super(EnvTest3, self).pre_test()
       
       def run_test(self):
           # main test logic
           # ...
           pass
       
       def post_test(self):
           super(EnvTest3, self).post_test()
           _del_host("www.qq.com", "11.11.12.12")

QTA会依照以下顺序执行测试用例的三个接口:

   * pre_test
   
   * run_test
   
   * post_test
   
且任意一个接口执行异常，QTA仍然会执行下一个接口。

.. note:: 由于历史原因，QTA还提供另一套代码风格的接口preTest、runTest和postTest，建议测试用例编写时选择测试项目存量代码统一的代码风格，如果是新的测试项目还是建议使用lower_with_under的代码风格。

.. warning:: 在一个测试用例中仅支持一套代码风格的接口，QTA选择接口的代码风格是基于run_test/runTest选择的风格为主，也就是说如果用例定义了runTest，则只会执行preTest和postTest，但不会执行pre_test和post_test。当run_test和runTest两个接口都存在的时候，QTA优先选择run_test接口来执行。


pre_test这个接口的一个作用是可以提高测试用例代码的复用，比如以下的例子::

   from testbase.testcase import TestCase

   class EnvTestBase(TestCase):
       
       def pre_test(self):
           super(EnvTestBase, self).post_test()    
           _add_host("www.qq.com", "11.11.12.12")
   
       def post_test(self):
           super(EnvTestBase, self).post_test()        
           _del_host("www.qq.com", "11.11.12.12")
   
   class EnvTest4(EnvTestBase):
       '''环境构造测试
       '''
       owner = "eeelin"
       status = TestCase.EnumStatus.Ready
       priority = TestCase.EnumPriority.Normal
       timeout = 1
   
       def run_test(self):
           # code 1
           pass
            
   class EnvTest5(EnvTestBase):
       '''环境构造测试
       '''
       owner = "eeelin"
       status = TestCase.EnumStatus.Ready
       priority = TestCase.EnumPriority.Normal
       timeout = 1
   
       def run_test(self):
           # code 2
           pass
           
可以看到EnvTest4和EnvTest5的基类都是为EnvTestBase，也就是他们本身会继承基类的pre_test和post_test的实现，因此也会进行环境的初始化和清理的动作。

.. note:: 可以看到EnvTestBase的pre_test和post_test方法都调用的super接口，对于Python语言的含义表示的是调用基类的方法，虽然不是必定需要的，但是大部分情况下还是推荐这样做；因为这样做可以保证基类的初始化和清理的接口会被执行。
