QPath语法和使用
==========

QPath是QTA UI自动化框架中最主要的定位UI元素的语言。

========
QPath的语法
========

QPath的完整的语法定义如下::

   QPath ::= Seperator QPath Seperator UIObjectLocator
    UIObjectLocator ::= UIObjectProperty PropertyConnector UIObjectLocator
    UIObjectProperty ::= UIProperty 
                        | RelationProperty 
                        | IndexProperty
                        | UITypeProperty 
    UIProperty ::= PropertyName Operator Literal
    RelationProperty ::= MaxDepthIdentifier EqualOperator Literal
    IndexProperty ::= InstanceIdentifier EqualOperator Literal
    UITypeProperty ::= UITypeIdentifier EqualOperator StringLiteral
    MaxDepthIdentifier := "MaxDepth"
    InstanceIdentifier ::= "Instance"
    UITypeIdentifier := "UIType"
    Operator ::= EqualOperator | MatchOperator
    PropertyConnector ::= "&&" | "&"
    Seperator ::= "/"
    EqualOperator ::= "="  #精确匹配
    MatchOperator ::= "~="  #使用正则进行模糊匹配
    PropertyName  ::= "[a-zA-Z_]*"
    Literal := StringLiteral
              | IntegerLiteral
              | BooleanLiteral
    StringLiteral ::= "\"[a-zA-Z_]*\""
    IntegerLiteral ::= "[0-9]*"
    BooleanLiteral := "True" | "False" | "true" | "false"

需要注意的是：

   * QPath的属性名（PropertyName）都是不区分大小写

以下是一个最简单的QPath的例子::

   / Id='MainPanel'

QPath通过“/”来连接多个UI对象定位器（UIObjectLocator），比如::

   / Id='MainPanel' / Id='LogoutButton'
   
一个UI对象定位器也可以存在多个属性，使用“&”或者“&&”连接，比如::

   / Id='MainPanel' & className='Window' / Id='LogoutButton' && Visiable='True'
   
如果属性值本身是布尔或者数值类型，也可以不使用字符串标识，比如下面的QPath和之前的QPath是等价的::

   / Id='MainPanel' & className='Window' / Id='LogoutButton' && Visiable=True
   
QPath也支持对属性进行正则匹配，可以使用“~=”::

   / Id~='MainP.*' / Id='LogoutButton'
   

============
QPath和UI元素查找
============

QPath的语义是描述如何去定位一个或者多个UI元素。因为在所有的UI框架中，UI元素的组织形式都是树状的，
因此QPath描述的也就是如何在一个UI树里面去定位一个或者多个UI元素。
QPath在树查找的过程，就是从根节点开始，一层一层增加树的深度去查找UI元素，QPath的间隔符“/”就是为了区分层次，比如下面的QPath::

   / Id='MainPanel' & className='Window' / Id='LogoutButton' && Visiable='True'
   
有两层的查找。
在每一层的查找过程中，QPath通过属性匹配的方式来筛选UI元素。在一些情况下，如果UI元素不存在QPath中定义的属性，则认为不匹配。
QPath在一层深度中查找到一个或者多个UI元素，则这些UI元素都会作为根，依次查找下一层的UI元素；如果在一层深度的UI元素查找中未能找到任何匹配的UI元素，则查找失败，即这个QPath不匹配任何的UI元素。

==========
QPath的特殊属性
==========

一般来说，QPath的查找都是匹配UI元素的属性，但QPath也定义了一些特殊的属性，

----------
MaxDepth属性
----------
MaxDepth属性用于控制一次搜索的最大深度。一般情况下，一个QPath有多少个UIObjectLocator则有会匹配到同样深度的子UI元素，但是对于UI元素层次比较深的UI元素，QPath会变得很长。
比如下面的例子::

   / ClassName='TxGuiFoundation' && Caption~='QQ\d+'
   / ClassName='TxGuiFoundation'
   / ClassName='TxGuiFoundation'
   / ClassName='TxGuiFoundation'
   / ClassName='TxGuiFoundation'
   / ClassName='TxGuiFoundation'
   / ClassName='TxGuiFoundation'
   / ClassName='GF' && name='mainpanel'

为解决这个问题，QPath使用关系属性（RelationProperty）来指定一次搜索的深度，比如上面很冗余的QPath在很多情况下都可以修改为::

   / ClassName='TxGuiFoundation' && Caption~='QQ\d+'
   / name='mainpanel'&& MaxDepth='7'

注意MaxDepth是从当前深度算起，也就是说MaxDepth='1'时和没有指定MaxDepth是一样的，也就是说MaxDepth默认为1。

----------
Instance属性
----------

当一个QPath搜索的结果中包含多个匹配的UI元素时，可以使用索引属性（IndexProperty）来唯一指定一个UI元素，比如假设以上的QPath搜索得到了多个UI元素，需要指定返回第一个匹配的UI元素，则可以写为::

   / ClassName='TxGuiFoundation' && Caption~='QQ\d+'
   / name='mainpanel'&&MaxDepth='7'&&Instance='0'

注意索引是从0开始计算的，支持负数索引。

.. note:: 当QPath找到多个UI元素的时候其排序本身并没有标准的定义，一般来说和树遍历的方式有关，具体的平台可能都存在差异，而且由于指定Instance本身并不是很好维护的方式，所以要尽量避免使用。

--------
UIType属性
--------

当UI界面混合使用多种类型的UI控件时，可以通过UIType指定控件的类型，如果不指定UIType，则继承上一层搜索时指定的UIType，对于只有一种控件类型的平台，可以指定一个默认UIType，用户可以不用在QPath显式指定UIType。比如以下一个使用UIType的例子::

   / ClassName='TxGuiFoundation' && Caption~='QQ\d+'
   / UIType='GF'&&name='main'
   / name='mainpanel'

在这里，UIType默认为“Win32”，因此在第一层搜索的搜索时候，只搜索控件类型为Win32的控件；但在第二层搜索的时候，UIType指定为“GF”，则第二层和第三层的搜索都只搜索控件类型为GF的控件。


===========
QPath简便写法汇总
===========

在一些平台上，可以使用字符串类型来标识一个等价意义的QPath，特汇总如下。

-------------
QT4C的字符串类型定位器
-------------

在QT4C中字符串类型的定位器等价于在UI元素树查找对应Name属性值匹配的元素，比如字符串::

   "Hello"
   
等价于下面的“伪”QPath::

   QPath('/Name="Hello"' && MaxDepth=∞')

-------------
QT4i的字符串类型定位器
-------------

在QT4i中字符串类型的定位器等价于在UI元素树查找对应Name属性值匹配的元素，比如字符串::

   "Hello"
   
等价于下面的“伪”QPath::

   QPath('/Name="Hello"' && MaxDepth=∞')

============
QPath兼容性问题汇总
============

由于历史原因，QTA的各个UI自动化的驱动器在QPath和UI元素查找的实现上略有差异，特汇总如下。

---------------
QT4A的首级Id无限深度查找
---------------

对于QT4A的QPath，如果QPath的第一层的Selector只有一个Id的属性，则在搜索UI元素的时候遍历的深度为无限。比如下面的QPath::

   QPath('/Id="Hello"')
   
在QT4A中等价于下面的“伪”QPath::

   QPath('/Id="Hello"' && MaxDepth=∞')
   
因为不存在值为“无限”的数值，所以上面的QPath其实是不合法的。

   
---------------
QT4A的Instance属性
---------------
对于QT4A的QPath，如果Instance的取值类型为字符串，则Instance的值表示的是第N个元素（从1开始计算）；
如果Instance的取值类型为数值，则Instance的值表示的是第N-1元素（从0开始计算）。
比如下面的QPath::

   QPath('/Id="Hello" && Instance="1" ')
   
和下面的QPath是等价的::

   QPath('/Id="Hello" && Instance=0 ')

一般来说，在QT4A中推荐使用第二种用法；第二种用法和其他平台的驱动器的与语义是一致的。






