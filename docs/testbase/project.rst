创建和修改测试项目
=========

对于QTA，一个测试自动化项目指的是针具体产品的特定测试的自动化用例和支持库的集合。在测试项目的支持库中，Testbase是必不可少的基础库，因为Testbase提供了测试项目的基本的管理的支持。

======
创建测试项目
======

在安装好QTAF后，可以在终端中执行一下命令::

    $ qta-manage createproject footestproj
   
执行成功后，可以看到当前目录下生成一下结构的文件::

   /footestproj/
               /foolib/
                      /__init__.py
                      /testcase.py
               /footest/
                       /__init__.py
                       /hello.py
               /.project
               /.pydevproject
               /settings.py
               /manage.py


==============
导入测试项目到Eclipse
==============

如果在Windows/Mac上，可以使用QTA IDE（eclispe）导入以上项目:

 * File -> Import... 打开Import对话框
 * 选择源类型：General/Existing Projects into Workspace
 * 通过Select root directory选择创建的QTA项目的根路径
 * 看到Projects窗口显示footestproj，选择并点击Finish完成导入
   
======
测试项目结构
======

对于测试项目，一般包括一下的模块:

 * 测试用例，比如foo项目中的footest包，这里存储所有的测试用例的脚本。
 
 * 测试业务库，比如foo项目中的foolib包，这里存放所有测试业务Lib层的代码。
 
 * 项目配置文件，即settings.py
 
 * 项目辅助脚本，即manage.py



