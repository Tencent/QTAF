测试项目打包
============

QTA内置测试项目打包的功能，方便将测试项目打包并发布给支持QTA测试执行的执行系统

========
执行打包
========

调用测试项目的manage.py::

    $ python manage.py dist --version 1.0.0

执行成功后可以看到生成文件在dist目录下::

    dist/
        foo-1.0.0.tar.gz


.. _RunDistPkg:

========
使用包
========

对于生成的包，QTA内置了执行测试的工具，可以通过调用qta-manage命令来执行测试::

    $ qta-manage runtest foo-1.0.0.tar.gz footest

qta-manage run命令提供丰富的控制参数来控制测试用例的执行范围。比如，只执行特定状态的用例::

    $ qta-manage runtest foo-1.0.0.tar.gz footest --status Ready --status BVT

除了状态外，用例优先级、负责人等都能作为过滤的选项，也能通过--exclude-name来排除特定的包或模块的用例集::

    $ qta-manage runtest foo-1.0.0.tar.gz footest --exclude-name footest.hello

QTA打包生成的包是Python的sdist标准格式，而qta-manage runtest命令是通过生成一个virtualenv来执行测试的Python代码，如果需要，用户也能控制使用的virtualenv::

    $ qta-manage runtest foo-1.0.0.tar.gz footest --venv /path/to/your/venv

qta-manage run命令，也能控制使用的测试执行器、测试报告类型和测试资源管理后端类型::

    $ qta-manage runtest foo-1.0.0.tar.gz footest --runner-type multithread --report-type json 

上面的命令行就指定使用多线程执行，并生成JSON格式的报告；更多的可选的执行器、报告类型可以通过qta-manage run的--help参数查询。
在指定特定类型的runner和report后，也能传递参数给特定类型的runner和report，例如::

    $ qta-manage runtest foo-1.0.0.tar.gz footest --runner-type multithread --runner-args "--concurrent 10"

比如上面的命令就指定多线程执行时使用10个线程。具体的runner和report类型有哪些可选参数，可以通过这样获取::

    $ qta-manage foo-1.0.0.tar.gz runtest --runner-args-help multithread
    usage: qta-manage [-h] [--retries RETRIES] [--concurrent CONCURRENT]

    optional arguments:
    -h, --help            show this help message and exit
    --retries RETRIES     retry count while test case failed
    --concurrent CONCURRENT
                            number of concurrent thread

同理，测试报告也能通过“--report-args-help”查询。


