开发新的扩展
==========

QTAF的扩展允许用户扩展QTAF命令行工具的功能。通过实现扩展，用户能定制化测试执行和资源管理的方式，也能定制自定义的测试报告的格式，方便第三方的系统或平台开发对QTA测试用例的执行的支持。

=========
扩展点
=========

目前支持扩展的功能有：

* qta-manage
 * runtest命令
 * runplan命令

* 每个项目的manage.py
 * runtest命令
 * runplan命令

以上的命令都支持用户自定义测试执行器(TestRunner)、测试报告(TestReport)和测试资源管理后端(TestResourceManagerBackend)


====
实现扩展
====

QTAF的扩展使用Python setuptools提供的 `Entry point机制`_。QTAF定义了三个Entry points:

.. _Entry point机制: http://setuptools.readthedocs.io/en/latest/pkg_resources.html#entry-points

 * qtaf.runner：测试执行器类型扩展点，对应接口 “:class:`testbase.runner.BaseTestRunner`”，更多请参考“:ref:`CustomTestRunner`”
 * qtaf.report：测试报告类型扩展点，对应接口 “:class:`testbase.report.ITestReport`”，更多请参考“:ref:`CustomTestReport`”
 * qtaf.resmgr_backend：资源管理后端扩展点，对应接口 “:class:`testbase.resource.IResourceManagerBackend`”，更多请参考“:ref:`CustomResmgrBackend`”

下面以测试执行器为例子，定义一个名字为foo的测试执行器::

    # foo.py
    import argparse
    from testbase.runner import BaseTestRunner
    class FooTestRunner(BaseTestRunner):

        def run_all_tests(self, tests ):
            tests.sort(lambda x,y: cmp(x.owner, y.owner)) #按用户排序执行
            for test in tests:
                self.run_test(test)

        @classmethod
        def get_parser(cls):
            '''获取命令行参数解析器（如果实现）

            :returns: 解析器对象
            :rtype: argparse.ArgumentParser
            '''
            return argparse.ArgumentParser()

        @classmethod
        def parse_args(cls, args_string, report, resmgr_backend):
            '''通过命令行参数构造对象
            
            :returns: 测试报告
            :rtype: cls
            '''
            return cls(report, resmgr_backend)



以上就实现了一个定制化的测试执行器，测试用例会按照用户名字排序执行。代码实现后，还需要打包和声明Entry point::

    # setup.py

    from setuptools import setup, find_packages

    setup(
        version="1.0.0",
        name="qtaf-ext-foo",
        py_modules=["foo"],
        include_package_data=True,
        package_data={'':['*.txt', '*.TXT'], },
        entry_points={
            'qtaf.runner': ['foo = foo:FooTestRuner'],  
        },
    )      

然后是打包和安装，如果是在开发调试，可以这样执行::

    $ python setup.py develop

如果是正式打包和安装::

    $ python setup.py install


如果安装成功，在执行qta-manage run是可以指定此类型的runner::

    $ qta-manage run foo-1.0.0.tar.gz run footest --runner-type foo


=======
关于扩展包命名的规范
=======

请按照包格式::

    qtaf-ext-<your name>



