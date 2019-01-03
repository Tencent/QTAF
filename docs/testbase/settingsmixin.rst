使用SettingsMixin
===================

SettingsMixin是一个混合类，用于方便地跟用户定义的类进行复合，在定义配置项的时候，
将定义放到lib层，而不是孤立地放在settings.py或配置模块中，再人工进行关联。

=========
定义配置项
=========

一个简单的使用例子如下::

   from qt4s.service import Channel
   from qt4s.conn2 import HttpConn
   from testbase.conf import SettingsMixin
   
   class MyChannel(Channel, SettingsMixin):
       """define a pseudo channel
       """
       class Settings(object):
           MYCHANNEL_URL = "http://www.xxxx.com"
           
       def __init__(self):
           self._conn = HttpConn()
           
       def get(self, uri, params):
           return self._conn.get(self.settings.MYCHANNEL_URL + uri, params)
           
MyChannel多重继承了Channel和SettingsMixin，SettingsMixin要求类的内部定义一个Settings类，
这个类定义配置项的规则如下：

* 配置项必须以当前类的名字大写+下划线开头，例如这里的"MYCHANNEL_"；
* 配置项的每个字母都必须大写；
* 访问配置项，使用self.settings访问，例如self.settings.MYCHANNEL_URL

==========
重载配置项
==========

重载配置项，分为两种情况

------------
派生类重载
------------

如果某个SettingsMixin类被继承，那么子类可以访问父类所拥有的配置项，并且可以重载父类的配置项，但是这里重载的方式比较特殊。

因为SettingsMixin要求当前类下必须定义一个嵌套Settings类，并且配置项必须以类名加下划线开头，因此，子类要重载父类的配置项，
通过定义相同后缀的配置项来实现，如下面的DUMMY_A和DUMMYCHILD_A，它们的后缀名都是"A"，这样才会生效。

一个具体的例子如下::

    from testbase.conf import SettingsMixin

    class Dummy(SettingsMixin):
        class Settings(object):
            DUMMY_A = 0
            
        def print_a(self):
            print("DUMMY_A=%s" % self.settings.DUMMY_A)
            
    class DummyChild(Dummy):
        class Settings(object):
            DUMMYCHILD_A = 2
    
    dummy = Dummy()
    assert dummy.settings.DUMMY_A == 0
    dummy.print_a()
    # DUMMY_A = 0
            
    child = DummyChild()
    assert child.settings.DUMMY_A == 2
    assert child.settings.DUMMYCHILD_A == 2
    child.print_a()
    # DUMMY_A = 2
    
如上，我们看到，在覆盖掉父类的配置项后，在父类的方法中访问的配置项也一样会被重载，这样可以复用父类的一些配置项，并根据需要进行重载。

------------
全局配置项重载
------------

SettingsMixin定义的配置项还可以被全局配置项重载，并且全局配置项的优先级最高。我们仍然用上面的Dummy和DummyChild来说明问题。

settings.py::

    DUMMYCHILD_A = 3
    
xxxxcase.py::

    dummy = Dummy()
    assert dummy.settings.DUMMY_A == 0
    dummy.print_a()
    # DUMMY_A = 0
            
    child = DummyChild()
    assert child.settings.DUMMY_A == 3
    assert child.settings.DUMMYCHILD_A == 3
    child.print_a()
    # DUMMY_A = 3
    
可以看到，即使子类重载了DUMMY_A的值为2，但是仍然可以在settings.py中已更高的优先级将其修改。

.. warning:: **框架在SettingsMixin定义的某个配置项被子类重载后，是不允许再在settings.py中去重载该配置项的**，
    即：如果我们在settings.py中添加DUMMY_A = 5，框架会提示错误，要求用户去重载DUMMYCHILD_A，而不是DUMMY_A。
    这样可以防止使用配置项在派生类之间冲突，并且简化配置项的设置。

