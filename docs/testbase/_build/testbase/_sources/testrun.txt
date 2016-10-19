执行测试
====

本节主要介绍如果批量执行所有的测试用例并生成对应的测试报告。

========
批量执行测试用例
========

当测试用例编写完成，大部分情况下，我们需要全量来执行我们的测试用例，这里我们就可以使用manage.py工具::

   $ python manage.py runtest zootest.cat.feed
   
执行完成后，可以看到当前目录下生成以下文件::

   2016/02/03  08:59               450 zootest.cat.feed.FeedFishTest.xml
   2016/02/03  08:59               420 zootest.cat.feed.FeedAppleTest.xml
   2016/02/03  08:59               412 zootest.cat.feed.FeedAppleTest.xml
   2016/02/03  08:59               709 TestReport.xml
   2016/02/03  08:59             4,646 TestReport.xsl
   2016/02/03  08:59             5,697 TestResult.xsl
   
直接双击TestReport.xml用浏览器打开就可以看到测试报告。

========
指定测试报告类型
========

刚刚执行生成的报告是xml类型的，可以通过-o选项控制测试报告的类型，比如::

   $ python manage.py runtest -o online zootest.cat.feed

执行后输出一个在线报告的链接，例如::
   
   http://qta.oa.com/report/v2/base/qta/get/report/9273512
   
也可以修改为流输出式的测试报告::

   $ python manage.py runtest -o stream zootest.cat.feed

执行后输出::

   Test Cases runs at:2016-02-03 09:02:48.
   filter 0 testcases
   load 3 testcases
   run test case: zootest.cat.feed.FeedFishTest(pass?:True)
   run test case: zootest.cat.feed.FeedMouseTest(pass?:True)
   run test case: zootest.cat.feed.FeedAppleTest(pass?:True)
   Test Cases ends at:2016-02-03 09:02:48.
   Total execution time is :0:00:00

====
并发执行
====

当测试比较多时，可以考虑通过并发的方式执行测试用例。testrunner内置两种并发方式：多线程和多进程。

使用多线程的方式并发::

   $ python manage.py runtest -o stream -l threading -n 2 zootest.cat.feed

这里我们使用2个线程并发去执行全部用例。也可以使用多进程并发::

   $ python manage.py runtest -o stream -l multiprocessing -n 2 zootest.cat.feed

======
指定测试用例
======

当只需要指定部分用例进行执行时，testrunner也支持选择过滤测试用例。

通过用例名指定测试用例，比如指定多个用例模块::

   $ python manage.py runtest -o stream zootest.cat zootest.dog

测试用例名可以是一个包、模块或者类的名字，其参数TestLoader接受的参数是一样的。

也可以通过用例优先级过滤，比如只执行优先级为High和BVT的用例::

   $ python manage.py runtest -o stream -p High/BVT zootest

也可以通过用例状态进行过滤，比如只执行Ready状态的用例::
   
   $ python manage.py runtest -o stream -s Ready zootest

=======
自定义测试执行
=======

上面的执行都是通过manage.py来测试用例，如果需要扩展测试用例执行的过程，增加一些测试步骤，也可以通过QTA的接口来执行测试用例。

等价于上面的runtest命令的代码的实现::

   from testbase.runner import TestRunner
   from testbase.report import XMLTestReport
   
   report = XMLTestReport()
   runner = TestRunner(report)
   runner.run("zootest.cat.feed")
   
如果要多线程执行::

   runner = ThreadingTestRunner(report)

如果要使用Stream报告::

   report = StreamTestReport()
   
通过使用不同类型的TestRunner和TestReport，可以定制测试执行的方式或测试报告的格式，更多的类型和使用方法，请参考接口文档《:doc:`./api/runner`》和《:doc:`./api/report`》




