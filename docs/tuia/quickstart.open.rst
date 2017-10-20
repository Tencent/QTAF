快速入门
====

在编写UI自动化测试之前，您需要先准备好以下的工具和开发环境：
   
   * Python运行环境
   * QTAF(`testbase <http://qta-testbase.readthedocs.io/zh/latest/>`_ & `tuia <http://qta-tuia.readthedocs.io/zh/latest/>`_)
   * 一个适用于对应平台QTA测试驱动器，如QT4A
   
在开始之前，您需要先创建一个QTA测试自动化项目，并掌握基本的测试用例组织形式和设计方法，详情请参考《`QTA Testbase文档 <http://qta-testbase.readthedocs.io/zh/latest/>`_》。

.. note:: 为了简单，下文示例代码使用QTA的一个驱动器————QT4X，QT4X是一个示例的QTA测试驱动器，支持对“QT4X SUT UI框架”实现的应用的自动化测试。“QT4X SUT UI框架”其实并不是一个真正的UI应用框架，而只是用于QTA驱动器的测试和学习目的设计，基于Python的XML etree实现的“伪”框架。实际使用时，可以针对测试的平台选择对应的驱动器进行替换。


--------
准备一个测试项目
--------
可以使用QTAF包创建一个空测试项目，比如::
   
   $ qta-manage createproject foo

创建成功后，安装对应平台的“测试驱动器”::

   $ pip install qt4x

-------
封装一个App
-------

对于QTA，一个App表示一个被测的应用。我们在测试项目的foolib目录下创建一个新的Python模块“fooapp.py”::

   from qt4x.app import App
   
   class FooApp(App):
   
      ENTRY = "qt4x_sut.demo"
      PORT  = 16000
      
.. note:: 由于平台的差异，各个QTA的驱动器封装App的方式略不同，具体需要参考对应驱动器的文档。对于QT4X，这里“ENTRY”指定的是一个Python的模块名，标识被测应用代码的入口；而“PORT”指定的是测试桩RPC服务的监听端口。


----------
封装一个Window
----------

对于QTA，一个Window表示被测应用的一个用户界面。一般来说，QTA的Window的概念和被测平台都能找到对应的概念，比如Android的Activity、iOS的Window、Win32平台上的窗口。
QTA的窗口的封装是为了告知QTA框架以下的信息：
   * 如果找到一个窗口
   * 窗口内的UI元素的布局信息
   
因此，在封装窗口的时候，我们需要获取被测应用界面的窗口和对应的布局信息，这就需要利用对应平台下的UI布局查看工具：

========  ======  ========================================
平台      驱动器       UI查看工具
========  ======  ========================================
Android    QT4A     AndroidUISpy
iOS        QT4i     iOSUISpy
Win32      QT4C     QTAInspect
Web        QT4W     可以在具体平台上的工具内部调起相关工具
========  ======  ========================================

对于QT4X，我们的UI窗口是由一个XML定义的，具体可以查看“qt4x_sut.demo”模块定义的窗口布局XML，比如主窗口布局如下::

   MAIN_LAYOUT = """<Window>
       <TitleBar name="title" text="Text editor"/>
       <MenuBar name="menu" >
           <Menu text="File" >
               <MenuItem value="Open file" />
               <MenuItem value="Save file" />
           </Menu>
           <Menu text="Help">
               <MenuItem value="Help" />
               <MenuItem value="About">
                   <Buttom name="about_btn"/>
               </MenuItem>
           </Menu>
       </MenuBar>
       <TextEdit name="editor" text="input here..." />
   </Window>"""
   
被测应用在创建时注册了主窗口::
   
   class TextEditorApp(App):
       '''text editor app
       '''
       def on_created(self):
           self.register_window("Main", MAIN_LAYOUT)
            ...
            
可以看到注册的窗口标识符为“Main”，因此我们封装对应的窗口::

   from qt4x.app import Window
   
   class MainWindow(Window):
       """main window
       """
       NAME = "Main"

.. note:: 由于平台的差异，各个QTA的驱动器封装Window的方式略不同，甚至一些平台下的类名字都不同，具体需要参考对应驱动器的文档。对于QT4X SUT的UI框架，一个窗口可以通过其注册时的标识符唯一确定，所以QT4X要求窗口封装的时候需要指定这个“标识符”，也就是“NAME”属性

------
指定窗口布局
------

以上的窗口的封装只是告诉测试框架如何找到这个窗口，还需要指定这个窗口的布局。所谓窗口的布局，即是一个窗口中的UI元素的信息，包括：

   * 名称————便于后面使用这个UI元素
   * UI元素类型————指定这个UI元素可以被如何使用
   * UI元素的定位器————如何定位此UI元素

QTA框架通过在窗口类的updateLocator接口来设置窗口的布局信息，比如对应上面的窗口，我们封装一个UI元素的布局::

   from qt4x.controls import Button, Window
   from qt4x.qpath import QPath
   
   class MainWindow(Window):
       """main window
       """
       NAME = "Main"
       
       def __init__(self, app):
           super(MainWindow, self).__init__(app)
           self.update_locator({
               "About Button": {"type": Button, "root": self, "locator": QPath("/name='menu' /name='about_btn' && MaxDepth=4 ")}
           })

这里是重载了窗口的构造函数，并追加调用updateLocator接口来设置窗口布局。

.. note:: 虽然在各个平台下的都是通过updateLocator来设置窗口布局，但是由于各个平台下的Window类的构造函数的参数可能不同，重装构造函数时需要注意。

从updateLocator的调用参数看，窗口布局是一个Python的dict结构：

   * 字典的键就是UI元素的“名称”，主要用于后面使用这个UI元素时所谓索引，一般这个名称建议是一个可读性较好且和被测应用的功能业务相关的名字；
   * 字典的值也是一个Python的字典，标识UI元素的属性，字典包括一下内容：
   
      * type： 标识UI元素元素的类型，对应一个Python类
      * locator：UI元素元素的定位器
      * root：UI元素元素定位查找时的使用的根节点UI元素
      
.. note:: UI元素属性的type和root的属性有可能不是必填属性，具体请参考对应平台的驱动器的接口
      
在上面的简单的例子中，我们定义了一个“About Button”的按钮（Button）UI元素。这里存在两个问题，一是，在实际的UI布局的封装的时候，该如何为一个UI元素指定一个准确的UI元素类型呢？
QTA框架对UI元素的类型并不做任何校验和检查的，也就是说，如果指定了一个UI元素类型为Button，则这个UI元素就可以当作一个Button来使用，即使这个UI元素实际上并不是一个Button，而是一个InputUI元素也是可以在QTA框架中当作Button来使用（当然，最终执行的结果会导致异常）。
因此，选择一个UI元素的类型就是看需要对这个UI元素进行哪些操作，一般来说，QTA各个平台下的基础UI元素类型在名字上都会尽量和对应的UI框架的UI元素类名一致，但也不排除有例外的情况。在选择UI元素的类型时，可以查看QTA各个平台的驱动器的UI元素类定义对应的Python模块：

========  ======  ========================================
平台      驱动器       Python模块
========  ======  ========================================
Android    QT4A     qt4a.andrcontrols
iOS        QT4i     qt4i.icontrols
Win32      QT4C     tuia.wincontrols
Web        QT4W     qt4w.webcontrols
Demo       QT4X     qt4x.controls
========  ======  ========================================

UI元素定位的第二个问题就是如何设计“UI元素的定位器”。由于在目前已知的所有的UI框架中，UI元素的组织结构都是树状的，包括我们这里使用的QT4X使用的XML结构也是树状的。
因此，QTA的UI元素的定位的本质就是在树状的结构中准确找到指定的节点，为此，QTA框架需要有两个参数：
   
      * 起始查找节点，也就是前面U元素属性的“root”参数就是用于指定UI树查找的根节点
      * UI元素定位器
      
UI树查找的根节点很容易理解，来看看UI元素的定位器。QTA框架使用了多种类型的UI元素的定位器：

   * QPath：QTA最主要的UI元素定位
   * XPath：主要用于Web UI元素的定位，XPath有W3C定义（https://www.w3.org/TR/xpath/）
   * str：各个平台下意义不同，一般是QPath或XPath的一种简便形式
   
由于XPath W3C是标准定义的语言，这里就不再熬述。
而QPath是QTA框架定义的一种简单的UI定位语言，以上面的QPath的例子::

   QPath("/name='menu' /name='about_btn' && MaxDepth=4 ")

以上的QPath查找控件的过程如下：

   1. 从根节点（窗口容器）开始查找其直接孩子节点，如果节点对应的UI元素的属性存在name属性且取值为menu，则执行第二级查找
   2. 开始第二级查找，以第一次查找的结果对象的UI元素为根，查找深度小于或等于4的全部孩子节点对应的UI元素，如果其属性存在name属性且取值为about_btn，则就是要定位的目标UI元素
   
以上只是简单的例子，更多关于QPath的语法和使用方法说明，可以参考《:doc:`./uilocator`》。
      








