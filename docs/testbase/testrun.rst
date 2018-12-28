执行测试
============

命令行执行测试
----------------------

.. warning:: **在执行用例前，我们需要在命令行先cd到工程的根目录（即包含manage.py的那个目录）。**

本节主要介绍如何批量执行所有的测试用例并生成对应的测试报告。命令行执行用例都是基于runtest命令实现的。因此，所有执行
用例相关的命令行是以python manage.py runtest开头，查看命令行帮助，可以执行::

   $ python manage.py runtest -h  
   
===============
指定用例集
===============

命令行执行用例跟qta平台上一样，是通过用例集来加载目标用例集合的，一个用例集是一个用句点分隔的字符串，
句点分隔的条目，每部分都可以是python的模块路径，最后一部分可以是用例名。多个用例集使用空格隔开。

例如::

   $ python manage.py runtest zoo.test foo bar # 执行zoo.test、foo、bar三个用例集
   $ python manage.py runtest zoo.test.HelloTest # 执行zoo.test模块下HelloTest用例
   $ python manage.py runtest zoo.test # 执行zoo.test模块下所有用例，包括HelloTest等用例
   $ python manage.py runtest zoo # 执行zoo模块下所有用例，包括test等子模块下的所有用例

使用\\--excluded-name选项，可以排除用例集合，接受多个排除用例集合，例如::

   $ python manage.py runtest zoo --excluded zoo.test # 执行zoo模块下所有用例，但是排除zoo.test
   $ python manage.py runtest zoo --excluded zoo.xxxx --excluded zoo.oooo #排除zoo.xxxx和zoo.oooo

====================
指定工作目录
====================

使用-w或\\--working-dir可以指定执行用例的工作目录，相关的输出文件也会放到工作目录::

   $ python manage.py runtest -w foo zoo
   $ python manage.py runtest --working-dir foo zoo

如果没有指定工作目录，会通过os.getcwd()获取，所以通常来说，就是manage.py所在的目录。

指定工作目录可以是绝对路径，也可以是相对路径。如果是相对路径，则相对于当前工作路径而言。

=====================
指定用例优先级
=====================

使用\\--priority可以根据优先级过滤用例，多个\\--priority选项可以指定多个优先级，
可选的用例优先级为：BVT、High、Normal、Low，例如::

   $ python manage.py runtest zoo --priority BVT --priority Normal
   
如果不指定优先级，所有优先级的用例都可以被执行。
   
====================
指定用例状态
====================

使用\\--status可以根据用例状态过滤用例，多个\\--status选项可以指定多个状态，
可选的用例状态为：Design、Implement、Ready、Review、Suspend，例如::

   $ python manage.py runtest zoo --status Design --status Ready
   
如果不指定状态，除Suspend以外的所有状态的用例都可以被执行。

====================
指定用例作者
====================

使用\\--owner可以根据用例作者过滤用例，多个\\--owner选项可以指定多个owner，例如::

   $ python manage.py runtest zoo --owner guying
   
====================
指定用例标签
====================

使用\\--tag和\\--excluded-tag可以根据用例标签过滤用例，多个\\--tag可以指定多个标签，
多个\\--excluded-tag可以排除多个标签，例如::

   $ python manage.py runtest zoo --tag foo --excluded-tag bar
   
==========================
指定测试报告类型
==========================

测试报告类型的选项：

* \\--report-type，报告类型，可以是xml、json、empty、stream、online，默认是stream。

* \\--report-args，传递给测试报告对象的命令行参数，**需要使用双引号引用起来，并且尾部至少需要保留一个空格**，具体支持的参数可以通过帮助信息查看。

* \\--report-args-help，打印指定报告类型的命令行参数帮助信息。

如果我们想要查看某个测试报告类型所支持的参数，可以使用命令行来打印::

   $ python manage.py --report-args-help stream
   usage: runtest <test ...> --report-type <report-type> [--report-args "<report-args>"]

   optional arguments:
     -h, --help          show this help message and exit
     --no-output-result  don't output detail result of test cases
     --no-summary        don't output summary information
   

**xml类型**，会生成xml格式的报告文件，输出到工作目录下，可以用浏览器打开TestReport.xml查看报告内容，
windows下会自动通过IE打开。无命令行参数。

**json类型**，会生成json格式的报告文件，输出到stdout或指定文件路径。命令行参数如下：

* \\--title，测试报告的标题；

* \\--output/-o，输出文件名称，会将对应文件输出到当前工作目录，必填参数。

**empty类型**，将不输出报告内容。无命令行参数。

**stream类型**，将报告内容输出到stdout，与调试用例时debug_run输出的信息一致。命令行参数如下：

* \\--no-output-result，指定后，用例执行的中间内容将不会输出到报告；

* \\--no-summary，指定后，将不输出用例执行统计结果。

例如::

   $ python manage.py runtest --report-args-help stream
   $ python manage.py runtest zoo --report-type stream --report-args "--no-output-result --no-summary"
   $ python manage.py runtest zoo --report-type xml -w test_result
   
==========================
指定资源管理后端
==========================

可以通过\\--resmgr-backend-type指定资源管理后端的类型，目前仅支持local，可以满足绝大部分的项目测试需求。

例如::

   $ python manage.py runtest zoo --resmgr-backend-type local
   
=====================
指定用例执行器
=====================

测试用例执行器相关的选项：

* \\--runner-type，用例执行器TestRunner的类型，目前支持multithread,multiprocess,basic。

* \\--runner-args，传递给TestRunner的命令行参数，**需要使用双引号引用起来，并且尾部至少需要保留一个空格**，具体的参数信息可以通过帮助信息查看。

* \\--runner-args-help，打印指定类型的TestRunner的命令行参数信息。

如果我们想要某个执行器类型支持的参数，可以通过下面命令打印::

   $ python manage.py runtest --runner-args-help basic
   usage: runtest <test ...> --runner-type <runner-type> [--runner-args "<runner-args>"]

   optional arguments:
     -h, --help         show this help message and exit
     --retries RETRIES  retry count while test case failed

**multithread类型**，使用多线程来并发执行用例。命令行参数如下：

* \\--retries，用例失败后的最大重试次数，默认为0，不重试。

* \\--concurrency，用例执行的并发数，默认为0，使用当前cpu核数作为并发数。

**multiprocess类型**，使用多进程来并发执行用例。命令行参数如下：

* \\--retries，用例失败后的最大重试次数，默认为0，不重试。

* \\--concurrency，用例执行的并发数，默认为0，使用当前cpu核数作为并发数。

**basic类型**，只能以单个串行方式执行用例，适合调试单个用例的场景。命令行参数如下：

* \\--retries，用例失败后的最大重试次数，默认为0，不重试。


自定义代码执行测试
-------------------------

上面内容都是通过manage.py runtest来执行测试用例，如果想要自己定制执行用例过程，可以通过QTA的接口来执行测试用例。

如果用户想要自己去实现更多的自定义扩展，可以参考“:doc:`extension`” 。

====================
选择报告类型
====================

查看当前支持的所有报告类型，可以通过下面代码打印::

   from testbase.report import report_types
   print(report_types.keys())

根据支持的类型，先获取到对应报告类型的class，然后实例化一个报告对象传递给TestRunner，用于存储执行结果::

   from testbase.report import report_types
   report_type = report_types['xml']
   report = report_type() # 根据实际类型，可以在构造时传入对应的参数
   
自定义测试报告需要实现接口类“:class:`testbase.report.ITestReport`”和“:class:`testbase.report.ITestResultFactory`”。

由于测试结果本身由测试报告类生成和管理，用户也可以同时自定义新的测试结果类型，基于“:class:`testbase.testresult.TestResultBase`”实现。

更多测试报告相关的内容，请参考接口文档《:doc:`./api/report`》。
      
================================
选择资源管理后端类型
================================

查看当前支持的所有资源管理后端类型，可以通过下面代码打印::

   from testbase.resource import resmgr_backend_types
   print(resmgr_backend_types.keys())
   
根据支持的类型，先获取到对应资源管理后端类型的class，然后实例化一个对象传递给TestRunner，用于管理资源::

   from testbase.resource import resmgr_backend_types
   resmgr_backend_type = resmgr_backend_types["local"]
   resmgr_backend = resmgr_backend_type() # 根据实际类型，可以在构造时传入对应的参数
  
资源管理是提高测试效率和保障测试通过率的重要部分，框架支持用户自己扩展资源管理后端，可以参考“:ref:`CustomResmgrBackend`”。
  
更多关于资源管理相关的内容，请参考文档《:doc:`resource`》或接口文档“:doc:`./api/resource`”。

=====================
选择执行器类型
=====================

查看当前支持的所有资源管理后端类型，可以通过下面代码打印::

   from testbase.runner import runner_types
   print(runner_types.keys())
   
根据支持的类型，先获取到对应TestRunner类型的class，然后实例化一个对象用于执行测试用例。

结合上面的测试报告类型和资源管理后端类型的选择，我们可以如下实现一个输出xml报告的执行逻辑::

   from testbase.resource import resmgr_backend_types
   from testbase.report import report_types
   from testbase.runner import runner_types
   
   resmgr_backend = resmgr_backend_types["local"]()
   report = report_types["xml"]()
   runner_type = runner_types["multithread"]
   runner = runner_type(report, retries=1, resmgr_backend=resmgr_backend) # 根据实际类型，可以在构造时传入对应的参数
   runner.run("zoo.test")

自定义测试执行器可以以“:class:`testbase.runner.BaseTestRunner`”为基类。

更多TestRunner相关的内容，请参考接口文档《:doc:`./api/runner`》。

=====================
指定测试用例集
=====================

TestRunner指定测试用例的方法也很灵活，可以是字符串::

   runner.run("zootest.cat.feed")

如果存在多个用例集，可以用空格间隔::

   runner.run("zootest.cat.feed zootest.dog")

也可以使用列表::

   runner.run(["zootest.cat.feed", "zootest.dog"])

也可以直接指定“ :class:`testbase.testcase.TestCase`”对象列表::

    from testbase.loader import TestLoader
    tests = TestLoader().load("zootest")
    runner.run(test)

使用“:class:`testbase.runner.TestCaseSettings`”可以充分利用框架支持的所有特性来过滤用例，
包括name、owner、priority、status和tag，例如::

    from testbase.runner import TestCaseSettings
    from testbase.testcase import TestCase
    runner.run(TestCaseSettings(
        names=["zootest"],
        status=[TestCase.EnumStatus.Ready]
    ))


TestRunner也支持执行“:class:`testbase.plan.TestPlan`”对象，详情请参考“:doc:`testplan`”或接口文档“:doc:`./api/runner`”。

