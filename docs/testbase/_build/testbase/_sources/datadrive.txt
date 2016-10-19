数据驱动测试
======

所谓数据驱动测试，即是将测试数据和测试用例分离，可以实现一份测试用例跑多份的测试数据，在一些业务场景的测试下可以大大提升测试用例开发和维护的成本。

========
数据驱动测试用例
========

先看一个简单的例子，小E需要设计一个针对登录的测试用例：

 * 输入“111”登录QQ，登录失败，提示非法帐号
 
 * 输入“”登录QQ，登录失败，提示非法帐号
 
 * 输入“11111111111111111”登录QQ，登录失败，提示非法帐号
 
 * 输入“$%^&#”登录QQ，登录失败，提示非法帐号

如果需要实现对应的自动化测试用例，则可能会写类似下面的代码::

   from testbase.testcase import TestCase

   class InvalidUinTest1(TestCase):
       '''非法测试号码1
       '''
       owner = "eeelin"
       status = TestCase.EnumStatus.Ready
       priority = TestCase.EnumPriority.Normal
       timeout = 1
   
       def run_test(self):
           qq = QQApp()
           login = LoginPanel(qq)
           login['uin'] = "111"
           login['passwd'] = "test123"
           login['login'].click()
           self.assertEqual(login['tips'].text, "非法帐号")
   
   class InvalidUinTest2(TestCase):
       '''非法测试号码2
       '''
       owner = "eeelin"
       status = TestCase.EnumStatus.Ready
       priority = TestCase.EnumPriority.Normal
       timeout = 1
   
       def run_test(self):
           qq = QQApp()
           login = LoginPanel(qq)
           login['uin'] = ""
           login['passwd'] = "test123"
           login['login'].click()
           self.assertEqual(login['tips'].text, "非法帐号")
   
   
   class InvalidUinTest3(TestCase):
       '''非法测试号码3
       '''
       owner = "eeelin"
       status = TestCase.EnumStatus.Ready
       priority = TestCase.EnumPriority.Normal
       timeout = 1
   
       def run_test(self):
           qq = QQApp()
           login = LoginPanel(qq)
           login['uin'] = "11111111111111111"
           login['passwd'] = "test123"
           login['login'].click()
           self.assertEqual(login['tips'].text, "非法帐号")
   
   class InvalidUinTest4(TestCase):
       '''非法测试号码4
       '''
       owner = "eeelin"
       status = TestCase.EnumStatus.Ready
       priority = TestCase.EnumPriority.Normal
       timeout = 1
   
       def run_test(self):
           qq = QQApp()
           login = LoginPanel(qq)
           login['uin'] = "$%^&#"
           login['passwd'] = "test123"
           login['login'].click()
           self.assertEqual(login['tips'].text, "非法帐号")
           
   if __name__ == '__main__':
      InvalidUinTest1().debug_run()
      InvalidUinTest2().debug_run()
      InvalidUinTest3().debug_run()
      InvalidUinTest4().debug_run()
           
从上面的代码看出，用户的逻辑基本上是类似的，每个用例几乎只有一点点的差异，特别是如果测试的场景变多了，用例维护起来更麻烦。

这里我们就可以用数据驱动用例来解决这个问题，使用数据驱动修改后的用例::

   from testbase.testcase import TestCase
   from testbase import datadrive 

   testdata = [
     "111",
     "",
     "11111111111111111",
     "$%^&#",
   ]
   
   @datadrive.DataDrive(testdata)
   class InvalidUinTest(TestCase):
       '''非法测试号码
       '''
       owner = "eeelin"
       status = TestCase.EnumStatus.Ready
       priority = TestCase.EnumPriority.Normal
       timeout = 1
   
       def run_test(self):
           qq = QQApp()
           login = LoginPanel(qq)
           login['uin'] = self.casedata
           login['passwd'] = "test123"
           login['login'].click()
           self.assertEqual(login['tips'].text, "非法帐号")
   
   if __name__ == '__main__':
       InvalidUinTest().debug_run()

如果执行以上的代码，其输出的结果是和前面四个测试用例的执行结果是一致的，但是这里却只有一个用例，这个就是数据驱动测试用例的强大之处。

上面的数据驱动测试用例和一般测试用例的主要区别在两点：

 * 测试用例类增加了修饰器“:class:`testbase.datadrive.DataDrive`”，修饰器接受一个参数来指定对应的测试数据
 
 * 测试用例通过casedata属性获取测试数据
 
====
测试数据
====

测试数据通过修饰器“:class:`testbase.datadrive.DataDrive`”指定，目前支持两个格式的数据：
   
   * list和list兼容类型
   
   * dict和dict兼容类型
   
----------
list类型测试数据
----------

上面的InvalidUinTest使用的就是list类型的测试数据，对于list类型的数据，QTA会将list的每一个元素生成对应的一个测试用例，并将该元素赋值给对应的测试用例的casedata属性。

例如测试数据为::

   @datadrive.DataDrive(["AA", 1234234, {"xx":"XX"},  True])
   class HelloDataTest(TestCase):
      pass
      
则生成的四个测试用例对应的casedata分别为::

   "AA"
   
   1234234
   
   {"xx":"XX"}
   
   True
   
----------
dict类型测试数据
----------

数据驱动也支持dict类型的测试数据，QTA会讲dict类型的所有值生成对应的一个测试用例，并将该值赋给对应的测试用例的casedata属性。

例如测试数据为::

   @datadrive.DataDrive({
      "A": "AA",
      "B": 1234234,
      "C": {"xx":"XX"},
      "D": True
   })
   class HelloDataTest(TestCase):
      pass
      
则生成的四个测试用例对应的casedata分别为::

   "AA"
   
   1234234
   
   {"xx":"XX"}
   
   True
   
但dict的键在这里似乎没什么用处？

==========
管理数据驱动测试用例
==========

QTA对于每个测试用例，都有一个唯一的名字；由于数据驱动把一个测试用例对应数据生成了多个测试用例，所以QTA对于每个数据驱动生成的用例的名字也是不一样的。

假设一个数据驱动的用例footest/cat/eat.py::

   @datadrive.DataDrive(["fish", "mouse", "apple"])
   class EatTest(TestCase):
      #这里省略相关代码
      pass
      
如果我们参考《:doc:`./testmgr`》使用TestLoader来加载这块测试用例::

   from testbase.loader import TestLoader
   loader = TestLoader()
   for it in loader.load("zootest.cat.eat"):
      print it.test_name
      
执行结果如下::

   zootest.cat.eat.EatTest/0
   zootest.cat.eat.EatTest/1
   zootest.cat.eat.EatTest/2
   
可以看到每个用例后面都有一个后缀，表示对应的list的索引值。

这个是list类型的例子，如果是dict类型::

   @datadrive.DataDrive({
      "fish": "fish",
      "mouse": "mouse",
      "apple": "apple",
   })
   class EatTest(TestCase):
      #这里省略相关代码
      pass
   
则TestLoader的执行结果如下::

   zootest.cat.eat.EatTest/fish
   zootest.cat.eat.EatTest/mouse
   zootest.cat.eat.EatTest/apple

之前的list的索引变成了dict键。

其实TestLoader也支持加载一个单独的数据驱动用例::

   from testbase.loader import TestLoader
   loader = TestLoader()
   for it in loader.load("zootest.cat.eat/fish"):
      print it.test_name

则TestLoader的执行结果如下::

   zootest.cat.eat.EatTest/fish
   
   
==========
调试数据驱动测试用例
==========

数据驱动测试用例本地调试的时候，可以和一般的测试用例一样::

   if __name__ == '__main__':
       DataHelloTest().debug_run()

但是上面的方式会执行所有的数据驱动的用例，如果需要指定测试用例使用具体某一个测试数据，对于list类型的数据可以::

   if __name__ == '__main__':
       DataHelloTest()[0].debug_run()
   
上面的例子指调试执行第一个数据驱动生成的用例。

如果是dict类型的测试数据，可以::

   if __name__ == '__main__':
       DataHelloTest()["key"].debug_run()
   
上面的例子会调试执行键为"key"对应的数据驱动生成的用例


========
全局数据驱动测试
========

数据驱动用例需要我们去修改测试用例，并为每个测试用例都增加修饰器和通过casedata访问数据，但是有没有可能在不修改测试用例的情况下，对全部的测试用例都进行数据驱动测试呢？比如对于后台测试，通过配置一份测试服务器的IP列表作为测试数据，然后对全部用例都以这份IP列表来生成对应的N个用例。答案就是全局数据驱动用例。

设置全局数据驱动需要修改项目的settings.py文件，增加下面两个配置::

   DATA_DRIVE = True
   DATA_SOURCE = 'test/data/server.py'

.. note:: settings.py配置的更多使用方法，请参考《:doc:`./settings`》

第一个配置表示打开全局数据驱动，第二个配置指定一个py文件作为数据源，如server.py::

   DATASET = [
    "11.22.11.11",
    "11.22.11.12",
    "11.22.11.13",
    "11.22.11.14",
   ]

数据py文件只需要定义一个DATASET模块变量，变量类型要求是list或者dict类型，格式和作用和前面的数据驱动用例DataDrive参数是一样的。

通过以上配置之后，本地调用debug_run调试脚本，可以看到每个用例都会被执行4次，且每次的casedata数据分别为DATASET变量定义的数据。

如果数据格式比较简单，也可以直接内嵌在settings.py中，这个时候DATA_SOURCE即表示数据源，同上面配置等价的配置如下::

   DATA_DRIVE = True
   DATA_SOURCE = [
    "11.22.11.11",
    "11.22.11.12",
    "11.22.11.13",
    "11.22.11.14",
   ]

.. note:: 当测试用例已经有修饰器DataDrive，但同时配置了全局数据驱动，这个时候全局数据驱动对于这个用例是无效的，这个用例还是只会通过DataDrive生成数据驱动测试用例。
 
