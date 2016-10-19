使用前准备
=====

=============
安装Python和相关工具
=============

Python目前要求为Python 2.7版本，如果是Windows系统，推荐使用ActivePython打包的版本::

    \\tencent.com\tfs\跨部门项目\SNG-Test\QTA\工具\python\2.7

.. note:: 如果使用的是64版本的Windows，也请安装32版本的Python，目前的QTA相关支持库仅支持32位版本。
    
最新的Mac OSX内置的Python已经为2.7版本，一般无需配置。

如果使用的是TLinux，可以使用以下的预编译好的二进制包::

   \\tencent.com\tfs\跨部门项目\SNG-Test\QTA\常用工具\tlinux\python2.7-tlinux.tar.gz
   \\tencent.com\tfs\跨部门项目\SNG-Test\QTA\常用工具\tlinux\python27.sh

安装方法如下::
   
   $ cd /usr/local
   $ tar zxvf python2.7-tlinux.tar.gz
   $ ln -s python2.7 python
   $ cp python27.sh /etc/profile.d/
   $ logout
  
.. note:: 更多QTA相关的开发工具和辅助工具，请访问：http://qta.oa.com/intro

如果在Windows或Mac下进行测试脚本开发，推荐安装QTA打包的eclipse集成开发环境::
   
   #Windows
   \\tencent.com\tfs\跨部门项目\SNG-Test\QTA\工具\IDE\QTA_IDE-win32-x86-1.0.0_beta.zip
   
   #Mac
   \\tencent.com\tfs\跨部门项目\SNG-Test\QTA\工具\IDE\QTA_IDE-macosx-x64-1.0.0_beta.zip
    

由于Eclipse依赖Java 7，如果没有安装则需要安装::

   #Windows
   \\tencent.com\tfs\跨部门项目\SNG-Test\QTA\工具\IDE\jdk-7u71-windows-i586.exe
   
   #Mac
   \\tencent.com\tfs\跨部门项目\SNG-Test\QTA\工具\IDE\jdk-7u71-macosx-x64.dmg
       
=======
获取QTAF包
=======

目前Testbase是打包在QTAF.egg中，在使用前需要选择对应的QTAF Egg包。

QTAF Egg的发布目录为::

   \\tencent.com\tfs\跨部门项目\SNG-Test\QTA\QTAF\dist\qtaf
   
对于每个版本号的QTAF，会存在多个类型，目前主要类型有:

======== ===================================================================
类型     说明
======== ===================================================================
testbase 只包含testbase模块
all      除了testbase模块外，还有tuia等支持UI自动化的模块
open     开源版本，包含testbase、tuia等模块，但是移除掉一些QTA测试平台相关的接口
======== ===================================================================

可以跟进具体测试的需要选择对应的版本：

   * 如果是UI自动化测试，一般选择all类型的版本
   
   * 对于后台测试的，可以选择testbase类型的版本
   
   
