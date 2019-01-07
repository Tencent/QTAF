测试计划
========

在“:doc:`testrun`”中介绍了一种批量执行测试用例和生成对应测试报告的方法，但是在实际测试执行中，还需要一些前置和后置的动作，以及对测试资源（帐号、设备等）进行初始化和清理，而“测试计划”就是用于解决这个问题。


==============
定义测试计划
==============

测试计划都以“:class:`testbase.plan.TestPlan`”为基类::

    from testbase.plan import TestPlan

    class AndroidAppTestPlan(TestPlan):
        """Android App test plan
        """
        tests = "adtest"
        test_target_args = "http://package.com/xx.apk"

        def get_test_target(self):
            """获取被测对象详情
            """
            return {"apk": self.test_target_args",
                    "version": tool_get_apk_ver(self.test_target_args)}

        def test_setup(self, report):
            """全局初始化
            """
            install_tools("adb")

        def resource_setup(self, report, restype, resource):
            """测试资源初始化
            """
            if res_type == "android":
                adb_install(resource["serialno"], self.test_target_args)
    
    if __name__ == '__main__':
        AndroidAppTestPlan().debug_run()

.. note:: TestPlan不允许子类重载__init__方法，否则会导致对象初始化失败。

上面的代码定义了一个测试计划，包括两个必要的类成员变量：

 * tests：要执行的测试用例，接受多种类型参数，可以参考“:ref:`TestRunnerRunParam`”
 * test_target: 被测对象的参数，由用户自定义，可以是任意的Python类型，一般来说主要是字符串等

这里实现了两个接口
 
 * :meth:`testbase.plan.TestPlan.get_test_target`：用于解析被测对象参数，并返回对应的被测对象的Key-Value信息，具体的KV结构完全由用户自定义，这个方法返回的结果会提供给测试报告进行记录
 * :meth:`testbase.plan.TestPlan.test_setup`：全局初始化，会在测试执行之前处理一次
 * :meth:`testbase.plan.TestPlan.resource_setup`：资源初始化，针对每个资源都会有一次操作。这里大部分的资源由资源管理系统提供，资源的注册和新增可以通过资源管理的接口实现，详情可以参考“:ref:`RegisterResType`”；但有一种特殊的资源类型“node”会由测试执行器定义，node类型的资源表示的是当前执行测试用例的主机，因此，如果需要对当前执行测试的主机环境进行预处理，可以针对node类型的资源进行处理即可。

和初始化的接口对应的，TestPlan也同时提供的清理接口：

 * :meth:`testbase.plan.TestPlan.test_teardown`：全局清理
 * :meth:`testbase.plan.TestPlan.resource_teardown`：资源清理

如果需要也可以重载以上两个方法。

==============
调试测试计划
==============

和测试用例类似，测试计划也提供了 :meth:`testbase.plan.TestPlan.debug_run` 的方法用于调试执行。像上面的例子，在__main__分支下调用debug_run后，只要直接执行当前的脚本就可以实现调试。

默认情况下，执行测试计划会执行全部用例，且使用 :class:`testbase.report.StreamTestReport` 类型的报告和 :class:`testbase.resource.LocalResourceManagerBackend` 类型的后端，如果用户需要指定对应的后端，可以通过参数传递给debug_run方法::

    if __name__ == '__main__':
        from testbase.report import XMLReport
        from testbase.resource import LocalResourceManagerBackend
        AndroidAppTestPlan().debug_run(
            report=XMLReport(), 
            resmgr_backend=LocalResourceManagerBackend())


=====================
测试计划存放的位置
=====================

测试计划的存放位置框架没有强制的要求，建议一般是存放在“testplan”名字后缀的Python包或模块中，比如下面的项目代码结构::

    /footestproj/
               footest/
               footestplan/
                    func.py <----功能测试计划
                    perf.py <----性能测试计划
               foolib/
               exlib/
               resources/
               settings.py
               manage.py


==============
执行测试计划
==============

正式执行测试计划有两种方式，一种是通过QTAF提供的命令行工具，一种是直接调用QTAF的接口

-----------
命令行接口
-----------

qta-manage接口和每个项目的manage.py都有提供“runplan”命令用于执行一个测试计划。

如果通过qta-manage调用，可以针对已经打包（参考“:doc:`dist`”）的项目中的测试计划进行执行::

    $ qta-manage runplan footest-1.0.0.tar.gz footestplan.FooTestPlan

如果通过manage.py调用::

    $ manage.py runplan footestplan.FooTestPlan

此外，qta-manage和manage.py的runplan和runtest类似，都提供选择测试类型执行器、测试报告、资源管理类型的参数，详情可以参考“:ref:`RunDistPkg`”。

-----------
类接口
-----------

“:class:`testbase.runner.TestRunner.run`”也支持传入“:class:`testbase.plan.TestPlan`”对象::

    from testbase.runner import TestRunner
    from testbase.report import StreamTestReport
    from footestplan import FooTestPlan
    TestRunner(StreamTestReport()).run(FooTestPlan())

TestRunner其他的用法和执行用例的方式一致，详情请参考“:doc:`testrun`”。