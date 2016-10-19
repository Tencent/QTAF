管理测试用例
======

从《:doc:`./testcase`》部分可以我们知道，一个测试用例，就是一个Python的测试用例类。在实际的测试项目中，会包含成百上千的测试用例，所以需要一种组织形式来管理这些测试用例。

====
组织形式
====

一个测试用例，就是一个Python的测试用例类，因此测试用例的组织其实就是Python类的组织。对于Python而言，存在三层结构的代码组织形式：包、模块和类。

Python模块即对应一个py代码文件，比如前面的hello.py就是定义一个python的模块。Python的包是一个模块的容器，Python要求包中至少定义一个__init__.py的模块，而且Python包是允许包含另一个Python包，因此可以构成一个N层次的树状结构。例如下面的代码组织形式::

   zootest\
          __init__.py
          cat\
              __init__.py
              feed.py *
              play.py
          dog\
              __init__.py
              feed.py
              play.py
            
Python以名字来唯一表示一个模块，也就是说，名字相同的模块就是同一个模块，所以模块名字必须是唯一的。使用“.”间隔的方式来唯一定位一个模块，比如上面的代码树的例子中加“*”的模块的名字如下::

   zootest.cat.feed
   
因此，对应的在feed.py里面的类的名字的唯一标识为::

   zootest.cat.feed.FeedFishTest
   zootest.cat.feed.FeedMouseTest
   zootest.cat.feed.FeedAppleTest
   
由于一个测试用例，就是一个Python的测试用例类，所以测试用例的名字也就和类的名字是一样的（数据驱动用例除外）。

.. note:: Python初学者容易忘记在包定义中增加__init__.py文件，如果没有__init__.py，则对于Python来说只是一个普通的文件夹，因此定义在里面的测试用例也无法被QTA识别出来。

======
加载测试用例
======

对于一个测试项目中大量的测试用例，我们可以使用TestLoader来加载和分析，例如下面的代码::

   from testbase.loader import TestLoader
   
   loader = TestLoader()
   for it in loader.load("zootest"):
      print it
      
上面代码是加载zootest包下面的全部测试用例，并展示其对应的测试用例名称，执行的结果如下::

   zootest.cat.feed.FeedFishTest
   zootest.cat.feed.FeedMouseTest
   zootest.cat.feed.FeedAppleTest
   zootest.cat.play.PlayBallTest
   zootest.cat.play.PlayLightTest
   zootest.dog.feed.FeedFishTest
   zootest.dog.feed.FeedMouseTest
   zootest.dog.feed.FeedAppleTest
   zootest.dog.play.PlayBallTest
   zootest.dog.play.PlayLightTest
      
TestLoader的load可以接受非顶层的包名，比如::

   for it in loader.load("zootest.cat"):
      print it
      
返回::

   zootest.cat.feed.FeedFishTest
   zootest.cat.feed.FeedMouseTest
   zootest.cat.feed.FeedAppleTest
   zootest.cat.play.PlayBallTest
   zootest.cat.play.PlayLightTest
   
也支持模块名::

   for it in loader.load("zootest.cat.feed"):
      print it
   
返回::

   zootest.cat.feed.FeedFishTest
   zootest.cat.feed.FeedMouseTest
   zootest.cat.feed.FeedAppleTest
   
甚至可以支持测试用例名::

   for it in loader.load("zootest.cat.feed.FeedFishTest"):
      print it
   
返回::

   zootest.cat.feed.FeedFishTest
   
可以看到通过不同的层次路径，我们可以控制测试用例的范围。如果通过名字控制的方式比较难筛选，也可以通过过滤函数来筛选::

   def filter( testcase ):
      if testcase.status != TestCase.EnumStatus.Ready:
         return "status is not ready"
         
   loader = TestLoader(filter)
   for it in loader.load("zootest"):
      print it
      
以上的代码可以过滤掉全部状态不是为Ready的测试用例。如果需要查询被过滤的全部测试用例，可以调用下面接口::

   filtered_records = loader.get_filtered_tests_with_reason()
   for tc in filtered_records:
      print tc.name, filtered_records[tc]
      
======
处理加载失败
======

测试用例加载过程中，可能会遇到由于测试脚本设计问题，在加载模块的时候就异常了，比如下面的py脚本::

   from testbase.testcase import TestCase
   
   raise RuntimeError("load error")
   
   class HelloTest(TestCase):
      '''测试示例
      '''
      owner = "eeelin"
      status = TestCase.EnumStatus.Ready
      timeout = 1
      priority = TestCase.EnumPriority.Normal
       
      def runTest(self):
         pass
      
      
上面的脚本加载必然失败，TestLoader会把这种错误记录下来，通过下面的方式可以查询::

   err_records = loader.get_last_errors()
   for name in err_records:
      print 'name:', name
      print 'error:', err_records[name]
         
执行的结果::

   name: hello
   error: Traceback (most recent call last):
     File "D:\workspace\qtaf5\test\hellotest.py", line 14, in <module>
       raise RuntimeError("load error")
   RuntimeError: load error


      
      
     



