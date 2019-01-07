开发新的扩展
==============

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


========
实现扩展
========

QTAF的扩展使用Python setuptools提供的 `Entry point机制`_。QTAF定义了三个Entry points:

.. _Entry point机制: http://setuptools.readthedocs.io/en/latest/pkg_resources.html#entry-points

 * qtaf.runner：测试执行器类型扩展点，对应接口 “:class:`testbase.runner.BaseTestRunner`”，更多请参考“:ref:`CustomTestRunner`”
 * qtaf.report：测试报告类型扩展点，对应接口 “:class:`testbase.report.ITestReport`”，更多请参考“:ref:`CustomTestReport`”
 * qtaf.resmgr_backend：资源管理后端扩展点，对应接口 “:class:`testbase.resource.IResourceManagerBackend`”，更多请参考“:ref:`CustomResmgrBackend`”


=======================
关于扩展包命名的规范
=======================

请按照包格式::

    qtaf-ext-<your name>



