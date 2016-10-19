创建和修改测试项目
=========

对于QTA，一个测试自动化项目指的是针具体产品的特定测试的自动化用例和支持库的集合。在测试项目的支持库中，Testbase是必不可少的基础库，因为Testbase提供了测试项目的基本的管理的支持。

======
创建测试项目
======

创建测试项目需要使用QTAF Egg，在终端下执行::

   $ python qtaf.egg createproject foo
   
执行成功后，可以看到当前目录下生成一下结构的文件::

   /footestproj/
               /exlib/
                     /qtaf.chm
                     /qtaf.egg
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

.. note:: 一般来说，测试项目会由QTA的管理员负责创建

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
 
 * exlib，存放测试项目依赖的是搜索Egg包，这里面中至少会存在一个QTAF Egg。
 
 * 项目配置文件，即settings.py
 
 * 项目辅助脚本，即manage.py

======
升级QTAF
======

测试项目创建后，如果需要升级使用的QTAF Egg的版本::

   $ python qtaf-new.egg upgradeproject footestproj

最后一个参数为测试项目所在的文件路径。上面的脚本其实是拷贝并替换qtaf-new.egg到exlib目录中，同时修改.pydevproject中的相关配置


========
安装依赖的Egg
========

对于测试项目依赖的Egg，可以直接放置到exlib目录中，但是如果是在Eclipse中，还需要修改测试项目对应的PYTHONPATH配置。manage.py提供了一个命令可以自动完成拷贝和配置的动作::

   $ python manage.py installlib other.egg
   
