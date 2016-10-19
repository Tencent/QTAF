设计测试用例
======

====
测试项目
====

测试用例归属于一个测试项目，在设计测试用例之前，如果没有测试项目，请先参考《`Testbase创建和修改测试项目 <http://qta.oa.com/static/doc/testbase/project.html>`_》。


=======
第一个测试用例
=======

我们先看一个简单的UI自动化的用例::

   class QT4CHelloTest(ClientTestCase):
       '''QT4C示例测试用例
       '''
       owner = "eeelin"
       status = ClientTestCase.EnumStatus.Ready
       timeout = 1
       priority = ClientTestCase.EnumPriority.Normal
       
       def pre_test(self):
           #-----------------------------
           self.startStep("关闭当前的所有Win7文件窗口")
           #-----------------------------       
           for w in QPath("/Visible='True' && ClassName='CabinetWClass'").search():
               w.close()
            
       def run_test(self):
           #-----------------------------
           self.startStep("Win7打开文件浏览器")
           #-----------------------------       
           os.popen2('explorer')
           fw = wincontrols.Window(locator=QPath("/Classname='CabinetWClass' && Visible='True'"))
           location = wincontrols.Control(root=fw, locator=QPath('/ControlId = "0x3E9" && Classname="ToolbarWindow32" && visible="True" && MaxDepth="8"'))
           self.assert_equal("检查默认的文件路径", location.Text, '地址: 库')


这个测试用例的逻辑很简单：

 * 为排除干扰，关闭当前的所有文件浏览器窗口
 
 * 在Win7下打开一个文件浏览器窗口
 
 * 检查其默认的文件地址为：库
 
我们先看主要代码的实现run_test，在第一步通过os.popen2启动一个文件浏览器进程后，我们实例化一个窗口对象::

   fw = wincontrols.Window(locator=QPath("/Classname='CabinetWClass' && Visible='True'"))
   
可以看到这里使用一个“:class:`tuia.qpath.QPath`”实例来作为locator的参数，这个locator其实是用于唯一定位我们打开的文件浏览器主窗口。

在构造主窗口对象后，我们构造了一个控件实例对象::

   location = wincontrols.Control(
      root=fw, 
      locator=QPath('/ControlId = "0x3E9" && Classname="ToolbarWindow32" && visible="True" && MaxDepth="8"'))
   
这个控件表示的是我们打开的文件浏览器的文件路径对应的控件，可以看到这里使用两个参数:
   
   * root：表示这个控件所属的窗口容器
   
   * locator：用于在窗口内唯一定位一个控件
   
可以看到location示例是属于我们的fw窗口，所以其root为fw。

在构造location对象后，我们便可以通过其Text属性来检查::

   self.assert_equal("检查默认的文件路径", location.Text, '地址: 库')


====
定位控件
====

上面的例子中，我们使用了一个叫QPath的locator来定位控件。QPath是怎么唯一定位一个控件的呢？

对于Windows平台，其实对于其他的平台也是一样，UI元素是以树结构组织的。像Windows操作系统的文件系统，也是以树结构的形式来管理的，我们使用的文件路径比如::

   C:\Python27\Lib\ctypes
   
以上的路径就是通过间隔符号“\”来分层定位一个文件。所以，可以理解QPath其实就是一个UI元素的路径定位技术，比如我们实例化文件浏览器窗口的QPath::

   /Classname='CabinetWClass' && Visible='True'

表示的就是从根开始（对于Windows来说，桌面窗口就是所有窗口的根），搜索其直接子窗口中符合对应ClassName和Visible属性的窗口。

而我们构造location控件对象时，由于指定了root参数，则是以文件浏览器窗口为根节点开始，搜素符合条件的控件元素。
从这里可以看出，QT4C使用两步定位的方式来定位一个控件，先找到这个控件所属的窗口，然后在这个窗口中搜索这个控件。
严格来说，Windows操作系统只有窗口的概念，并没有区分控件和窗口这两个概念，而在QT4C中，“:class:`tuia.wincontrols.Window`”的意义是指控件的容器，而“:class:`tuia.wincontrols.Control`”则表示一个不可以分隔的UI元素。
因此QT4C中是使用“:class:`tuia.wincontrols.Window`”还是“:class:`tuia.wincontrols.Control`”，关键看使用者怎么理解这个UI元素的作用。

更多的控件定位的详细内容，请参考《:doc:`./uilocator`》


======
理解UI结构
======
   
上面的QT4CHelloTest用例存在两个问题：

 * 可读性差，只能依赖构造的实例的名字来猜测控件对应的用途
 
 * 维护成本高，我们在测试用例中硬编码QPath的路径，如果被测对象的UI结构调整，则需要修改每一个测试用例；而且可以看到在一个用例中，我们也多次引用了同一个QPath。
  
为解决这两个问题，我们的测试用例可以这样修改::

   from tuia.qpath import QPath
   from tuia import wincontrols

   class ExplorerFolder(wincontrols.Window):
       '''文件浏览器文件夹窗口
       '''
       LOCATOR = QPath("/Classname='CabinetWClass' && Visible='True'")
       
       def __init__(self):
           super(ExplorerFolder, self).__init__(locator=self.LOCATOR)
           self.updateLocator({
               '文件地址显示框'   :{'type':wincontrols.Control, 
                                   'root':self, 
                                   'locator': QPath('/ControlId = "0x3E9" && Classname="ToolbarWindow32" && visible="True" && MaxDepth="8"')},            
           })
           
       @staticmethod
       def closeAll():
           for w in ExplorerFolder.LOCATOR.search():
               w.close()
           
   class QT4CHelloTest(ClientTestCase):
       '''QT4C示例测试用例
       '''
       owner = "eeelin"
       status = ClientTestCase.EnumStatus.Ready
       timeout = 1
       priority = ClientTestCase.EnumPriority.Normal
       
       def pre_test(self):
           #-----------------------------
           self.startStep("关闭当前的所有Win7文件窗口")
           #-----------------------------       
           ExplorerFolder.closeAll()
   
       def run_test(self):
           #-----------------------------
           self.startStep("Win7打开文件浏览器")
           #-----------------------------       
           os.popen2('explorer')
           ef = ExplorerFolder()
           self.assert_equal("检查默认的文件路径", ef['文件地址显示框'].Text, '地址: 库')


可以看到我们封装了以个ExplorerFolder类，表示这个文件浏览器的窗口。

先看看run_test用例，和之前有较大的变化，实例化窗口对象不需要提供locator参数::

   ef = ExplorerFolder()
   
检查其子控件的属性也变得简单易懂::

   ef['文件地址显示框'].Text
   
当然这得益于对ExplorerFolder的封装。ExplorerFolder本身是“:class:`tuia.wincontrols.Window`”的子类，表示这个是一个窗口，在其调用基类构造函数的时候传递了locator参数，因此使用的时候变得简单，无需任何参数。
ExplorerFolder还在构造函数中调用了updateLocator方法，传入一个字典::

   {
      '文件地址显示框'   :{'type': wincontrols.Control, 
                          'root': self, 
                          'locator': QPath('/ControlId = "0x3E9" && Classname="ToolbarWindow32" && visible="True" && MaxDepth="8"')},            
   }
   
这个字典其实就是这个窗口的子控件的布局的描述，每个子控件的描述由四个部分组成：

   * 名称：用字符串表示这个子控件的名字，窗口对象可以通过这个名字来引用使用对应的子控件，就像我们在测试用例中使用“'文件地址显示框'”一样。
   
   * type：表示子控件的类型，下面我们会介绍
   
   * root：表示子控件定位时使用的跟节点，一般都是用self，也就是当前的窗口对象
   
   * locator：表示子控件定位时使用的路径，一般是QPath或其他类似的控件定位符号
   
通过ExplorerFolder类，可以更清晰得看到QT4C两层UI结构的意义所在。

实际上，除了Window和Control，QT4C还提供了第三层的UI结构，即是“:class:`tuia.app.App`”。比如上面的用例，我们可以增加一个ExplorerApp类并对应修改ExplorerFolder类::

   class ExplorerFolder(wincontrols.Window):
       '''文件浏览器文件夹窗口
       '''
       LOCATOR_STR = "/Classname='CabinetWClass' && Visible='True'"
       
       def __init__(self, app ):
           super(ExplorerFolder, self).__init__(locator=QPath(self.LOCATOR_STR + " && ThreadId='%s'" % app.ThreadId))
           self.updateLocator({
               '文件地址显示框'   :{'type':wincontrols.Control, 'root':self, 'locator': QPath('/ControlId = "0x3E9" && Classname="ToolbarWindow32" && visible="True" && MaxDepth="8"')},            
           })
           
   class ExplorerApp(App):
       '''文件浏览器应用
       '''
       def __init__(self):
           '''构造函数
           '''
           prev_threads = set([it.ThreadId for it in QPath(ExplorerFolder.LOCATOR_STR).search()])
           p = subprocess.Popen('explorer')
           p.wait()
           #等待explorer创建一个新的线程
           new_threads = util.Timeout().retry(self._get_threadid, (prev_threads,), (), lambda x: len(x)>0)
           assert len(new_threads) == 1
           self._threadid = new_threads.pop()
            
       def _get_threadid(self, prev_threads ):
           '''获取新建的线程的ID
           '''                  
           return set([it.ThreadId for it in QPath(ExplorerFolder.LOCATOR_STR).search()]) - prev_threads
                   
       @property
       def ThreadId(self):
           '''对应在explorer.exe进程中的线程ID
           '''
           return self._threadid
       
       def quit(self):
           ExplorerFolder(self).close()
           
       def kill(self):
           ExplorerFolder(self).close()
           
       @staticmethod
       def killAll():
           for w in QPath(ExplorerFolder.LOCATOR_STR).search():
               w.close()

对应的，测试用例可以修改为::

   class QT4CHelloTest(ClientTestCase):
       '''QT4C示例测试用例
       '''
       owner = "eeelin"
       status = ClientTestCase.EnumStatus.Ready
       timeout = 1
       priority = ClientTestCase.EnumPriority.Normal
       
       def run_test(self):
           #-----------------------------
           self.startStep("Win7打开文件浏览器")
           #-----------------------------       
           explorer = ExplorerApp()
           ef = ExplorerFolder(explorer)
           self.assert_equal("检查默认的文件路径", ef['文件地址显示框'].Text, '地址: 库')

这个用例和之前的用例有比较大的区别就是少了pre_test，原因是ExplorerApp类已经实现了对多个文件浏览器的管理的功能，所以可以不用在测试之前通过将全部窗口都关闭的方式来避免发生干扰。
QT4C的App的作用，在UI的层面上，就是用于管理多个重复窗口的情况；在操作系统的层面上讲，App可以理解为提供一个特定功能的软件，一般来说可能是对应操作系统的一个进程、一个线程、或者多个进程集合。

更多的UI结构和封装的详细内容，请参考《:doc:`./uistruct`》。


=======
控件类型和属性
=======

在指定UI布局的时候，我们可以选择对应的控件的类型，在上面的例子里面::

   {
      '文件地址显示框'   :{'type': wincontrols.Control, 
                          'root': self, 
                          'locator': QPath('/ControlId = "0x3E9" && Classname="ToolbarWindow32" && visible="True" && MaxDepth="8"')},            
   }
   
type使用的是“:class:`tuia.wincontrols.Control`”类型，我们需要如何选择控件的类型？有哪些控件的类型呢？

同时，在检查控件的属性的时候，我们使用Text属性::

   ef['文件地址显示框'].Text

但是我们需要如何知道使用哪个属性？

QT4C目前支持三种类型的控件，分别是：

   * Native控件，即Windows操作系统提供的窗口控件，接口请参考《:doc:`api/wincontrols`》
   
   * GF控件，Tencent Hummer SDK中提供的自绘控件，接口请参考《:doc:`api/gfcontrols`》
   
   * Web控件，基于QT4W提供的内嵌Web页面的控件识别能力
   
Web控件和其他的控件的使用略有不同，我们会在《:doc:`./web`》中讨论。

Native和GF是控件的实现方式的差异导致，在同种实现方式下，也会有很多不同的控件类型，比如对于Native控件，我们前面使用到的“:class:`tuia.wincontrols.Control`”表示的就是普通的控件，但如何是可以列表控件，则可以使用“:class:`tuia.wincontrols.ListView`”。
使用哪种类型的控件，关键是看使用者要如何使用这个控件，QT4C不会也无法检查选择控件类型和对应的控件是否匹配。例如，对于一个Checkbox，最基本的操作是支持“勾选”的操作，如果要实现这样的操作，则控件的类型必须指定为“:class:`tuia.gfcontrols.CheckBox`”::

   {
      '是否打开'   :{'type': gfcontrols.CheckBox, 
                     'root': self, 
                     'locator': QPath('/ControlId = "0x3E9" && MaxDepth="8"')},            
   }

指定之后可以这样使用::

   ef['是否打开'].Checked = True
   
   
   

