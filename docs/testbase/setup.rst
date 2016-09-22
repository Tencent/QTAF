使用前准备
=====

=============
安装Python和相关工具
=============

Python目前要求为Python 2.7版本，如果是Windows系统，推荐使用ActivePython打包的版本

.. note:: 如果使用的是64版本的Windows，也请安装32版本的Python，目前的QTA相关支持库仅支持32位版本。
    
最新的Mac OSX内置的Python已经为2.7版本，一般无需配置。

如果在Windows或Mac下进行测试脚本开发，推荐使用Eclipse+Pydev

=======
构建QTAF包
=======

QTAF推荐的使用方式是打包为Egg包，可以执行以下命令生成egg包::

    python setup.py bdist_egg
    
执行成功后会在dist目录下生成对应的egg包。
   
   
