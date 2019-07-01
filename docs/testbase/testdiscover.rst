发现测试用例
===============

有时候，我们希望查看指定的条件和用例集下，最终会被执行的用例的列表，可以使用python manage.py discover命令来实现。例如::

    $ python manage.py discover footest
    $ python manage.py discover --tag test --owner foo --priority High --status BVT footest
    $ python manage.py discover --excluded-name bar --output-file xxxx.txt footest
    
除了可以指定用例集，也可以指定用例状态、优先级和标签等等，与runtest命令类似。

===============
指定用例集
===============

这里可以参考“:ref:`specify_test`”。

=====================
指定用例优先级
=====================

这里可以参考“:ref:`specify_priority`”。

**这里需要特别注意的是，discover命令默认放到normal的用例优先级是High和Normal。**
   
====================
指定用例状态
====================

这里可以参考“:ref:`specify_status`”。

**这里需要特别注意的是，discover命令默认放到normal的用例状态只有Ready。**

====================
指定用例作者
====================

这里可以参考“:ref:`specify_owner`”。
   
====================
指定用例标签
====================

这里可以参考“:ref:`specify_tag`”。

====================
指定显示的用例列表类型
====================

使用--show命令可以显示用例列表类型，支持三种类型：normal、filtered和error。

默认情况下，三种类型都会展示，如果希望指定了--show选项，会以用户指定的类型为准。可以指定多个--show选项。例如::

    $ python manage.py discover --show normal footest
    $ python manage.py discover --show normal --show error footest

====================
指定输出格式
====================

使用--output-type可以指定输出用例列表的格式，目前支持格式如下：

* stream，每个部分一行是一个用例，会详细展示用例相关的属性
* line，每个部分的用例用空格拼接为一整行，用于runtest或者测试计划

====================
指定输出文件
====================

使用--output-file可以指定用例列表的输出文件，未指定时，会将内容输出到stdout。