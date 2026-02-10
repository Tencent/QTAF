设计测试用例
==============

================
最简单的测试用例
================

下面我们来编写第一个QTA测试用例，在测试项目中新建一个hello.py::

        # -*- coding: utf-8 -*-
        '''示例测试用例
        '''
        #2020/07/08 QTAF自动生成

        from foolib.testcase import FooTestCase

        class HelloTest(FooTestCase):
            '''第一个测试用例
            '''
            owner = "foo"
            timeout = 5
            priority = FooTestCase.EnumPriority.High
            status = FooTestCase.EnumStatus.Design

            def run_test(self):
                self.log_info("hello testcase")
                self.assert_equal(True, True)
           
           
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

========
调试执行
========

测试用例编写后，需要进行调试执行。需要在hello.py中增加以下的代码::

   if __name__ == '__main__':
      HelloTest().debug_run()

如果使用的是IDE，在eclipse中，通过“CTRL + F11”快捷键执行当前hello.py脚本，可以看到输出如下::
 
   ============================================================
   测试用例:HelloTest 所有者:foo 优先级:Normal 超时:1分钟
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
    
如果没有使用IDE，可以通过manage.py runtest，加载指定用例集进行::

    $ python manage.py runtest footest.hello

也可以通过manage.py runscript方式执行，直接执行指定脚本::

    $ python manage.py runscript footest/hello.py

   
在命令行窗口可以看到一样的执行输出::  

   ============================================================
   测试用例:HelloTest 所有者:foo 优先级:Normal 超时:1分钟
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
      
==============
测试用例标签
==============

测试用例除了owner、timeout、status和priority之外，还有一个自定义的标签属性“tags”。测试标签的作用是，在批量执行用例的时候，用来指定或排除对应的测试用例，相关详情可以参考《:doc:`./testrun`》。

设置标签的方式十分简单::


   from foolib.testcase import TestCase

   class HelloTest(TestCase):
       '''第一个测试用例
       '''
       owner = "foo"
       status = TestCase.EnumStatus.Ready
       priority = TestCase.EnumPriority.Normal
       timeout = 1
       tags = "Demo"
   
       def run_test(self):
           #---------------------------
           self.start_step("第一个测试步骤")
           #---------------------------
           self.log_info("hello")

标签支持一个或多个，下面的例子也是正确的::

   from foolib.testcase import TestCase

   class HelloTest(TestCase):
       '''第一个测试用例
       '''
       owner = "foo"
       status = TestCase.EnumStatus.Ready
       priority = TestCase.EnumPriority.Normal
       timeout = 1
       tags = "Demo", "Help"
   
       def run_test(self):
           #---------------------------
           self.start_step("第一个测试步骤")
           #---------------------------
           self.log_info("hello")


需要注意的是，测试用例标签经过框架处理后，会变成set类型，比如上面的用例::

    assert HelloTest.tags == set(["Demo", "Help"])


======================
测试环境初始化和清理
======================
        
在前面的例子中，我们在测试用例类的run_test实现了测试的主要逻辑，这里我们引入两个新的接口pre_test和post_test。

假设我们的用例需要临时配置一个本地host域名，示例代码如下::

   from foolib.testcase import TestCase
   
   class EnvTest1(TestCase):
       '''环境构造测试
       '''
       owner = "foo"
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
       owner = "foo"
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
       owner = "foo"
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
           super(EnvTestBase, self).pre_test()    
           _add_host("www.qq.com", "11.11.12.12")
   
       def post_test(self):
           super(EnvTestBase, self).post_test()        
           _del_host("www.qq.com", "11.11.12.12")
   
   class EnvTest4(EnvTestBase):
       '''环境构造测试
       '''
       owner = "foo"
       status = TestCase.EnumStatus.Ready
       priority = TestCase.EnumPriority.Normal
       timeout = 1
   
       def run_test(self):
           # code 1
           pass
            
   class EnvTest5(EnvTestBase):
       '''环境构造测试
       '''
       owner = "foo"
       status = TestCase.EnumStatus.Ready
       priority = TestCase.EnumPriority.Normal
       timeout = 1
   
       def run_test(self):
           # code 2
           pass
           
可以看到EnvTest4和EnvTest5的基类都是为EnvTestBase，也就是他们本身会继承基类的pre_test和post_test的实现，因此也会进行环境的初始化和清理的动作。

.. note:: 可以看到EnvTestBase的pre_test和post_test方法都调用的super接口，对于Python语言的含义表示的是调用基类的方法，虽然不是必定需要的，但是大部分情况下还是推荐这样做；因为这样做可以保证基类的初始化和清理的接口会被执行。



