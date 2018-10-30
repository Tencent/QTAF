测试资源管理
==============

在测试执行过程中，需要使用或依赖一些资源（文件、设备等），为此，框架提供了统一的测试资源的管理和使用接口，以及新增测试资源的扩展接口。

目前的测试资源分为两类：
 * 文件资源
 * 非文件资源

================
文件资源的存储
================

若要使用文件资源管理器去测试文件资源，需要一定的规则来存放测试文件资源。

------------------------
一般测试文件资源存放方式
------------------------

每个QTA测试项目的目录中新增一个目录“resources”（新创建项目自带，老项目可以手动创建）::

    /footestproj/
               footest/
               foolib/
               exlib/
               resources/
               settings.py
               manage.py


用户将需要使用的文件资源都存放在此目录下，文件资源的组织自由，可以也推荐用户按需要创建多级目录，比如::

    /footestproj/
               footest/
               foolib/
               exlib/
               resources/
                         test.txt
                         video/
                               foo.mp4
                         audio/
                               foo.mp3
               settings.py
               manage.py


-----------------------
文件定位搜索逻辑
-----------------------

有部分QTA项目涉及到外链代码有资源文件访问的情况，所以资源文件读取会搜索当前工程目录所有“resources”目录去寻找资源::

    /footestproj/
               footest/
               foolib/
               exlib/
               resources/
                         test.txt
                         video/
                               foo.mp4
                         audio/
                               foo.mp3
               mqlib/
                     resources/
                               qq.jpeg
               settings.py
               manage.py

不过，这种情况下要保证所有的“resources”目录下不能同名（相对路径相同）的文件资源。


-----------------------
外链文件资源
-----------------------

对于比较大的文件资源，SVN等代码管理系统的限制，导致没法存放在代码库中的时候，可以通过软链接的方式存放，具体的方法是在resources目录中创建一个文本文件，后缀名为“.lnk”。比如下面的的例子::

    /footestproj/
               footest/
               foolib/
               exlib/
               resources/
                         test.txt              
                         video/
                               bigfile.mp4.lnk #软链接文件
                               foo.mp4
                         audio/
                               foo.mp3
               settings.py
               manage.py

                  
bingfile.mp4.lnk是一个文本文件，其内容为文件正在的路径，比如可以是一个HTTP下载路径

    http://foo.com/xx/xxx/bigfile.mp4

也可以是一个本地绝对路径::

    /data/foo/xx/bigfile.mp4


-----------------------
资源路径格式
-----------------------

由于操作系统的差异，路径的分隔符可能是“/”或“\”，以上的接口不区分操作系统，且两种分隔符都同时支持。
比如下面的两个路径是等价的，在Windows/Mac/Linux上都能同时使用::

    video/foo.mp4
    video\foo.mp4


==================
文件资源的使用接口
==================

目前提供两个操作文件资源的方法：
    * get_file:获取指定文件对象，传入参数为上文描述规则的相对路径，返回的是文件对象的绝对路径。
    * list_dir:列举指定目录下文件对象（包括文件夹），传入参数为上文描述规则的相对路径，返回的是一个包含该路径下所有文件对象的绝对路径的list。
用户如果需要在测试用例中使用特定的文件资源的时候，可以通过访问TestCase基类提供的方法::

   from testbase.testcase import TestCase

   class HelloTest(TestCase):
       '''文件资源测试用例
       '''
       owner = "foo"
       status = TestCase.EnumStatus.Ready
       priority = TestCase.EnumPriority.Normal
       timeout = 1
   
       def run_test(self):
           #---------------------------
           self.start_step("测试文件资源管理接口")
           #---------------------------
           paths = self.test_resources.list_dir("video")
           print paths
           
           mp4_filepath = self.test_resources.get_file("video/foo.mp4")
           self.assert_equal("文件存在", os.path.isfile(mp4_filepath), True)

           bigfile_path = self.test_resource.get_file("video/bigfile.mp4.lnk")
           self.assert_equal("文件存在", os.path.isfile(bigfile_path ), True)
      

在lib层中可以直接使用文件管理的接口来实现相应的逻辑，如下::

    from testbase import resource
    def get_test_video_path():
        return resource.get_file("video/foo.mp4")



================
非文件资源的使用
================

非文件资源指除了文件形态外的其他资源类型，比如执行用例的设备、使用的终端设备、测试帐号等都属于此类。非文件资源管理主要用于解决可能导致的资源使用冲突，对于并行执行测试用例的场景尤其必要。

测试资源一般只允许在测试用例，和文件资源一样，也通过test_resources接口（类型为：“:class:`testbase.resource.Session`”）使用::

   from testbase.testcase import TestCase

   class HelloTest(TestCase):
       '''非文件资源测试用例
       '''
       owner = "foo"
       status = TestCase.EnumStatus.Ready
       priority = TestCase.EnumPriority.Normal
       timeout = 1
   
       def run_test(self):
           acc = self.test_resources.acquire_resource("account")
           app = FooApp()
           app.login(acc["username"], acc["password"])

acquire_resource如果申请成功会返回一个资源的dict，其中除了必要的id、res_group（分组）属性外，还有其他资源自定义的属性。

acquire_resource接口还提供两个可选参数：
    * res_group: 指定资源的分组
    * condition: 指定匹配的资源的属性的字典

比如可以这样使用::

   class HelloTest(TestCase):
       '''非文件资源测试用例
       '''
       ...
       def run_test(self):
           acc = self.test_resources.acquire_resource("account", res_group="foo", condition={"vip": True})
           ...
    

如果申请资源失败，则会导致异常。有两种情况会导致申请资源失败:
    * 指定条件的资源不存在
    * 指定条件的资源存在，但是目前都被占用。对于这种情况，会产生一个RESNOTREADY级别的日志

一般来说资源的使用不需要显式释放，测试用例执行完成或超时时，测试框架会负责回收。如果用户需要手动释放资源，则可以通过release_resource接口::

   class HelloTest(TestCase):
       '''非文件资源测试用例
       '''
       ...
       def run_test(self):
           acc = self.test_resources.acquire_resource("account")
           self.test_resource.release_resource("account", acc["id"])


如果需要的话，在lib层中可以直接使用非文件管理的接口来实现相应的逻辑，如下::

    from testbase import resource
    
    def get_special_resource():
        return resource.acquire_resource("account", res_group="special")
    


.. _RegisterResType:

================
注册测试资源类型
================

上面的资源使用的接口的前提是有对应的注册好的资源，比如上面的测试帐号资源，需要通过“:class:`testbase.resource.LocalResourceManagerBackend`”接口注册一个以“:class:`testbase.resource.LocalResourceHandler`”为基类的Handler。

比如我们用一个本地的CSV文件来管理测试资源::

    import csv
    from testbase.testcase import TestCase
    from testbase.resource import LocalResourceManagerBackend, LocalCSVResourceHandler
    
    LocalResourceManagerBackend.register_resource_type(
        "account", 
        LocalCSVResourceHandler("/path/to/account.csv"))


    class HelloTest(TestCase):
        '''非文件资源测试用例
        '''
        owner = "foo"
        status = TestCase.EnumStatus.Ready
        priority = TestCase.EnumPriority.Normal
        timeout = 1

        def run_test(self):
        acc = self.test_resources.acquire_resource("account")
        app = FooApp()
        app.login(acc["username"], acc["password"])


如果需要，也可以通过以“:class:`testbase.resource.LocalResourceHandler`”为基类自定义一个资源类型，比如对于Android手机设备，设备资源是通过ADB工具动态查询得到的，则可以这样实现::

    from testbase.resource import LocalResourceManagerBackend, LocalResourceHandler

    class AndroidResourceHandler(LocalResourceHandler):
        def iter_resource(self, res_type, res_group=None, condition=None):
            for it in ADBClient().list_device():
                yield {"id": it["serialno"], "host":"localhost", "serialno":it["serialno"]}


.. _CustomResmgrBackend:

================
扩展资源管理后端
================

上面的资源管理都是基于内置的“:class:`testbase.resource.LocalResourceManagerBackend`”资源管理后端，一般来说能满足本地单机执行测试的要求，但如果对于支持QTA自动化测试的平台，在执行多机分布式执行测试的情况时，则可能需要扩展对应的资源管理后端。

用户如果要实现测试资源管理后端，需要实现接口类“:class:`testbase.resource.IResourceManagerBackend`”

资源管理后端也可以以QTAF的扩展的形式实现，更多细节请参考“:doc:`extension`”。