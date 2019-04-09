执行测试
============

命令行执行测试
----------------------

.. warning:: **在执行用例前，我们需要在命令行先cd到工程的根目录（即包含manage.py的那个目录）。**

本节主要介绍如何批量执行所有的测试用例并生成对应的测试报告。命令行执行用例都是基于runtest命令实现的。因此，所有执行
用例相关的命令行是以python manage.py runtest开头，查看命令行帮助，可以执行::

   $ python manage.py runtest -h  
   
.. _specify_test: 
  
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

使用--excluded-name选项，可以排除用例集合，接受多个排除用例集合，例如::

   $ python manage.py runtest zoo --excluded-name zoo.test # 执行zoo模块下所有用例，但是排除zoo.test
   $ python manage.py runtest zoo --excluded-name zoo.xxxx --excluded-name zoo.oooo #排除zoo.xxxx和zoo.oooo

====================
指定工作目录
====================

使用-w或--working-dir可以指定执行用例的工作目录，相关的输出文件也会放到工作目录::

   $ python manage.py runtest -w foo zoo
   $ python manage.py runtest --working-dir foo zoo

如果没有指定工作目录，会通过os.getcwd()获取，所以通常来说，就是manage.py所在的目录。

指定工作目录可以是绝对路径，也可以是相对路径。如果是相对路径，则相对于当前工作路径而言。

.. _specify_priority:

=====================
指定用例优先级
=====================

使用--priority可以根据优先级过滤用例，多个--priority选项可以指定多个优先级，
可选的用例优先级为：BVT、High、Normal、Low，例如::

   $ python manage.py runtest zoo --priority BVT --priority Normal
   
如果不指定优先级，所有优先级的用例都可以被执行。

.. _specify_status:

====================
指定用例状态
====================

使用--status可以根据用例状态过滤用例，多个--status选项可以指定多个状态，
可选的用例状态为：Design、Implement、Ready、Review、Suspend，例如::

   $ python manage.py runtest zoo --status Design --status Ready
   
如果不指定状态，除Suspend以外的所有状态的用例都可以被执行。

.. _specify_owner:

====================
指定用例作者
====================

使用--owner可以根据用例作者过滤用例，多个--owner选项可以指定多个owner，例如::

   $ python manage.py runtest zoo --owner foo

.. _specify_tag:
   
====================
指定用例标签
====================

使用--tag和--excluded-tag可以根据用例标签过滤用例，多个--tag可以指定多个标签，
多个--excluded-tag可以排除多个标签，例如::

   $ python manage.py runtest zoo --tag foo --excluded-tag bar
   
==========================
指定测试报告类型
==========================

测试报告类型的选项：

* --report-type，报告类型，可以是xml、json、empty、stream、html，默认是stream。

* --report-args，传递给测试报告对象的命令行参数，**需要使用双引号引用起来，并且尾部至少需要保留一个空格**，具体支持的参数可以通过帮助信息查看。

* --report-args-help，打印指定报告类型的命令行参数帮助信息。

如果我们想要查看某个测试报告类型所支持的参数，可以使用命令行来打印::

   $ python manage.py runtest --report-args-help stream
   usage: runtest <test ...> --report-type <report-type> [--report-args "<report-args>"]

   optional arguments:
     -h, --help          show this help message and exit
     --no-output-result  don't output detail result of test cases
     --no-summary        don't output summary information
   

**xml类型**，会生成xml格式的报告文件，输出到工作目录下，可以用浏览器打开TestReport.xml查看报告内容，
windows下会自动通过IE打开。无命令行参数。

**json类型**，会生成json格式的报告文件，输出到stdout或指定文件路径。命令行参数如下：

* --title，测试报告的标题；

* --output/-o，输出文件名称，会将对应文件输出到当前工作目录，必填参数。

**empty类型**，将不输出报告内容。无命令行参数。

**stream类型**，将报告内容输出到stdout，与调试用例时debug_run输出的信息一致。命令行参数如下：

* --no-output-result，指定后，用例执行的中间内容将不会输出到报告；

* --no-summary，指定后，将不输出用例执行统计结果。

**html类型**，会生成js和html文件，使用浏览器打开工作目录下的qta-report.html即可查看，命令行参数如下：

* --title，测试报告的标题；

例如::

   $ python manage.py runtest --report-args-help stream
   $ python manage.py runtest zoo --report-type stream --report-args "--no-output-result --no-summary"
   $ python manage.py runtest zoo --report-type xml -w test_result
   $ python manage.py runtest zoo --report-type html -w test_result --report-args "--title zootest"
   
==========================
指定资源管理后端
==========================

可以通过--resmgr-backend-type指定资源管理后端的类型，目前仅支持local，可以满足绝大部分的项目测试需求。

例如::

   $ python manage.py runtest zoo --resmgr-backend-type local
   
.. _TestRunnerRunParam:
   
=====================
指定用例执行器
=====================

测试用例执行器相关的选项：

* --runner-type，用例执行器TestRunner的类型，目前支持multithread,multiprocess,basic。

* --runner-args，传递给TestRunner的命令行参数，**需要使用双引号引用起来，并且尾部至少需要保留一个空格**，具体的参数信息可以通过帮助信息查看。

* --runner-args-help，打印指定类型的TestRunner的命令行参数信息。

如果我们想要某个执行器类型支持的参数，可以通过下面命令打印::

   $ python manage.py runtest --runner-args-help basic
   usage: runtest <test ...> --runner-type <runner-type> [--runner-args "<runner-args>"]

   optional arguments:
     -h, --help         show this help message and exit
     --retries RETRIES  retry count while test case failed

**multithread类型**，使用多线程来并发执行用例。命令行参数如下：

* --retries，用例失败后的最大重试次数，默认为0，不重试。

* --concurrency，用例执行的并发数，默认为0，使用当前cpu核数作为并发数。

**multiprocess类型**，使用多进程来并发执行用例。命令行参数如下：

* --retries，用例失败后的最大重试次数，默认为0，不重试。

* --concurrency，用例执行的并发数，默认为0，使用当前cpu核数作为并发数。

**basic类型**，只能以单个串行方式执行用例，适合调试单个用例的场景。命令行参数如下：

* --retries，用例失败后的最大重试次数，默认为0，不重试。


自定义代码执行测试
-------------------------

上面内容都是通过manage.py runtest来执行测试用例，如果想要自己定制执行用例过程，可以通过QTA的接口来执行测试用例。

如果用户想要自己去实现更多的自定义扩展，可以参考“:doc:`extension`” 。

====================
选择报告类型
====================

查看当前支持的所有报告类型，可以通过下面代码打印::

   from testbase.types import report_types
   print(report_types.keys())

根据支持的类型，先获取到对应报告类型的class，然后实例化一个报告对象传递给TestRunner，用于存储执行结果::

   from testbase.types import report_types
   report_type = report_types['xml']
   report = report_type() # 根据实际类型，可以在构造时传入对应的参数
   
自定义测试报告需要实现接口类“:class:`testbase.report.ITestReport`”和“:class:`testbase.report.ITestResultFactory`”。

由于测试结果本身由测试报告类生成和管理，用户也可以同时自定义新的测试结果类型，基于“:class:`testbase.testresult.TestResultBase`”实现。

更多测试报告相关的内容，请参考接口文档《:doc:`./api/report`》。
      
================================
选择资源管理后端类型
================================

查看当前支持的所有资源管理后端类型，可以通过下面代码打印::

   from testbase.types import resmgr_backend_types
   print(resmgr_backend_types.keys())
   
根据支持的类型，先获取到对应资源管理后端类型的class，然后实例化一个对象传递给TestRunner，用于管理资源::

   from testbase.types import resmgr_backend_types
   resmgr_backend_type = resmgr_backend_types["local"]
   resmgr_backend = resmgr_backend_type() # 根据实际类型，可以在构造时传入对应的参数
  
资源管理是提高测试效率和保障测试通过率的重要部分，框架支持用户自己扩展资源管理后端，可以参考“:ref:`CustomResmgrBackend`”。
  
更多关于资源管理相关的内容，请参考文档《:doc:`resource`》或接口文档“:doc:`./api/resource`”。

=====================
选择执行器类型
=====================

查看当前支持的所有资源管理后端类型，可以通过下面代码打印::

   from testbase.types import runner_types
   print(runner_types.keys())
   
根据支持的类型，先获取到对应TestRunner类型的class，然后实例化一个对象用于执行测试用例。

结合上面的测试报告类型和资源管理后端类型的选择，我们可以如下实现一个输出xml报告的执行逻辑::

   from testbase.types import report_types, runner_types, resmgr_backend_types
   
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

扩展测试报告和测试执行器
------------------------------

.. _CustomTestReport:

==================
扩展测试报告
==================

扩展测试报告的步骤如下：

创建一个自己的python库工程，实现一个类，该类继承自“:class:`testbase.report.ITestReport`”，
根据自己业务的实际情况，实现ITestReport对应的方法即可。

一个简单的报告类型可以实现为，

fooreport.py::

    from testbase.report import ITestReport, ITestResultFactory, report_usage
    from testbase.testresult import TestResultBase
    
    class FooTestResult(TestResultBase):
        """a demo test result class
        """
        def handle_test_begin(self, testcase):
            '''处理一个测试用例执行的开始
            
            :param testcase: 测试用例
            :type testcase: TestCase
            '''
            print("%s began to run" % testcase)
                
        def handle_test_end(self, passed ):
            '''处理一个测试用例执行的结束
            
            :param passed: 测试用例是否通过
            :type passed: boolean
            '''
            print("testcase ended with passed=%s" % passed)
            
        def handle_step_begin(self, msg ):
            '''处理一个测试步骤的开始
            
            :param msg: 测试步骤名称
            :type msg: string
            '''
            print("testcase step began: %s" % msg)
            
        def handle_step_end(self, passed ):
            '''处理一个测试步骤的结束
            
            :param passed: 测试步骤是否通过
            :type passed: boolean
            '''
            print("testcase step ended with passed=%s" % passed)
        
        def handle_log_record(self, level, msg, record, attachments ):
            '''处理一个日志记录
            
            :param level: 日志级别，参考EnumLogLevel
            :type level: string
            :param msg: 日志消息
            :type msg: string
            :param record: 日志记录
            :type record: dict
            :param attachments: 附件
            :type attachments: dict
            '''
            print("[%s]%s\nrecord=%s\nattachments=%s" % (level, msg, record, attachments))
            
    class FooTestResultFactory(ITestResultFactory):
        """a demo test result factory
        """
        def create(self, testcase):
            return FooTestResult()
    
    class FooTestReport(ITestReport):
        """a demo test report class
        """
        def begin_report(self):
            print("test begin")
            
        def end_report(self):
            print("test end")
            
        def log_test_result(self, testcase, testresult ):
            '''记录一个测试结果
    
            :param testcase: 测试用例
            :type testcase: TestCase
            :param testresult: 测试结果
            :type testresult: TestResult
            '''
            print("test case %s is over with result passed=%s" % (testcase, testresult.passed))
            
        def log_record(self, level, tag, msg, record):
            '''增加一个记录
    
            :param level: 日志级别
            :param msg: 日志消息
            :param tag: 日志标签
            :param record: 日志记录信息
            :type level: string
            :type tag: string
            :type msg: string
            :type record: dict
            '''
            print("[log record]:%s" % msg)
            
        def log_loaded_tests(self, loader, testcases):
            '''记录加载成功的用例
    
            :param loader: 用例加载器
            :type loader: TestLoader
            :param testcases: 测试用例列表
            :type testcases: list
            '''
            print("load %s cases ok" % len(testcases))
            errors = loader.get_last_errors()
            for item in errors:
                error = errors[item]
                self.log_load_error(loader, item, error)
            
        def log_filtered_test(self, loader, testcase, reason):
            '''记录一个被过滤的测试用例
    
            :param loader: 用例加载器
            :type loader: TestLoader
            :param testcase: 测试用例
            :type testcase: TestCase
            :param reason: 过滤原因
            :type reason: str
            '''
            print("test case %s is skipped for: %s" % (testcase, reason))
            
        def log_load_error(self, loader, name, error):
            '''记录一个加载失败的用例或用例集
    
            :param loader: 用例加载器
            :type loader: TestLoader
            :param name: 名称
            :type name: str
            :param error: 错误信息
            :type error: str
            '''
            print("log test case %s error: %s" % (name, error))
    
        def log_test_target(self, test_target):
            '''记录被测对象
    
            :param test_target: 被测对象详情
            :type test_target: any
            '''
            pass
    
        def log_resource(self, res_type, resource):
            '''记录测试使用的资源
    
            :param res_type: 资源类型
            :type res_type: str
            :param resource: 资源详情
            :type resource: dict
            '''
            pass
        
        def get_testresult_factory(self):
            '''获取对应的TestResult工厂
    
            :returns ITestResultFactory
            '''
            return FooTestResultFactory()
        
        @classmethod
        def get_parser(cls):
            parser = argparse.ArgumentParser(usage=report_usage)
            return parser
        
        @classmethod
        def parse_args(cls, args_string):
            return cls()
        
实现好了测试报告类，在当前python库的setup.py中需要添加对应的entry point，例如

setup.py::

    from setuptools import setup

    setup(name="qta-ext-fooreport",
          version="1.0.0",
          py_modules=["fooreport"],
          entry_points={
              'qta.report' : [
                  'foo = fooreport:FooTestReport',
              ],
          }
    )

上面我们在entry point "qta.report"新增了一个条目foo，指定为fooreport模块下的FooTestReport类型。

接下来是打包和安装，如果是在开发调试，可以这样执行::

    $ python setup.py develop

如果是正式打包和安装::

    $ python setup.py install


如果安装成功，在执行qta-manage run是可以指定此类型的测试报告::

    $ qta-manage run foo-1.0.0.tar.gz run footest --report-type foo
    
或者在工程根目录下执行::

    $ python manage.py runtest footest --report-type foo

.. _CustomTestRunner:

==================
扩展测试执行器
==================

扩展一个测试执行器的步骤如下:

创建一个自己的python库工程，实现一个类，该类继承自“:class:`testbase.runner.BaseTestRunner`”，
根据自己业务的实际情况，重载BaseTestRunner对应的方法即可。

一个简单的测试执行器类型可以实现为，

foorunner.py::

    import argparse
    
    from testbase.runner import BaseTestRunner, runner_usage
    from testbase.testcase import TestCaseRunner
    
    class FooTestRunner(BaseTestRunner):
        """a demo test case runner
        """
        def __init__(self, report, retries=0, resmgr_backend=None):
            self._retries = retries
            self._runner = TestCaseRunner()
            super(FooTestRunner, self).__init__(report, resmgr_backend)
    
        def run_test(self, test):
            test.test_resmgr = self._resmgr
            for _ in range(self._retries + 1):
                test_result = self._runner.run(test, self.report.get_testresult_factory())
                self.report.log_test_result(test, test_result)
                if test_result.passed:
                    break
            return test_result.passed
    
        @classmethod
        def get_parser(cls):
            '''获取命令行参数解析器（如果实现）
    
            :returns: 解析器对象
            :rtype: argparse.ArgumentParser
            '''
            parser = argparse.ArgumentParser(usage=runner_usage)
            parser.add_argument("--retries", type=int, default=0, help="retry count while test case failed")
            return parser
    
        @classmethod
        def parse_args(cls, args_string, report, resmgr_backend):
            '''通过命令行参数构造对象
            
            :returns: 测试报告
            :rtype: cls
            '''
            args = cls.get_parser().parse_args(args_string)
            return cls(report, args.retries, resmgr_backend)

实现好了测试执行器类，在当前python库的setup.py中需要添加对应的entry point，例如

setup.py::

    from setuptools import setup

    setup(name="qta-ext-foorunner",
          version="1.0.0",
          py_modules=["foorunner"],
          entry_points={
              'qta.runner' : [
                  'foo = foorunner:FooTestRunner',
              ],
          }
    )
    
上面我们在entry point "qta.runner"新增了一个条目foo，指定为foorunner模块下的FooTestRunner类型。

接下来是打包和安装，如果是在开发调试，可以这样执行::

    $ python setup.py develop

如果是正式打包和安装::

    $ python setup.py install


如果安装成功，在执行qta-manage run是可以指定此类型的runner::

    $ qta-manage run foo-1.0.0.tar.gz run footest --runner-type foo
    
或者在工程根目录下执行::

    $ python manage.py runtest footest --runner-type foo

=====================================
使用扩展的测试报告和执行器
=====================================

我们同样可以在自定义代码执行测试中，使用扩展的报告类型和执行器类型。

在扩展插件安装到python库目录之后，可以通过下面方法使用扩展的测试报告和执行器::

    from testbase import runner
    from testbase import report
    test_report = report.report_types["foo"]
    test_runner = runner.runner_types["foo"](test_report, 0)
    test_runner.run("footest")

