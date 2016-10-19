# -*- coding: utf-8 -*-
'''
控件基类模块
'''
#10/11/04 allenpan    用Keyboard.inputKeys代替Keyboard.sendKeys
#10/11/11 aaronlai    从控件类中分离出控件定位功能
#10/11/15 aaronlai    定义异常类ControlNotFoundError和ControlAmbiguousError
#10/11/26 aaronlai    修改Control类的rightClick、doubleClick方法，增加Control.mouseOver方法
#10/11/30 aaronlai    修改Control.mouseOver为hover名
#10/12/02 aaronlai    增加Control.waitForValue函数的参数
#10/12/13 allenpan    增加ControlContainer类
#12/02/14 jonliang    增加_getClickXY方法，以方便子类调用；暂时屏蔽_click方法

from util import Timeout
from mouse import Mouse, MouseFlag, MouseClickType
from keyboard import Keyboard
from tuia.exceptions import ControlAmbiguousError, ControlNotFoundError, TimeoutError
#__all__=['Control']
    
#===============================================================================
# 异常类定义
#===============================================================================
#class ControlNotFoundError(Exception):
#    "控件没有找到"
#    pass
#
#class ControlAmbiguousError(Exception):
#    "找到多个控件"
#    pass 
    
#===============================================================================
# 基础控件类定义
#===============================================================================
class Control(object):
    '''
    控件基类
    '''
    #11/02/23 allenpan    将_timeout作为静态变量
    
    _timeout=Timeout(5,0.5) #控件查找timeout时间 
    def __init__(self):
        pass
    
    @property
    def Children(self):
        '''返回此控件的子控件。需要在子类中实现。
        '''
        raise NotImplementedError("请在%s类中实Children属性" % type(self))
    
#     @staticmethod
#     def exist(locator, root=None, timeout=10, interval=0.5):
#         '''在timeout时间内检查控件，返回找到的控件个数。
#         
#         :type locator: QPath
#         :param locator: 查找方式
#         :param root: 开始查找的父控件
#         :param timeout: 控件查找超时时间
#         :param interval: 查找间隔 
#         :return: 找到的控件个数
#         '''
#         #11/01/17 allenpan    添加此函数
#         
#         import util
#         ctrls = []
#         try: 
#             ctrls = util.Timeout(timeout, interval).retry(locator.search, (root,), (), lambda x: len(x) != 0)
#         except TimeoutError:
#             pass
#         return len(ctrls)
#     
#     @classmethod
#     def exist2(cls, *args, **kwargs):
#         #11/11/23 jonliang    添加此函数
#         #11/11/23 jonliang    考虑了一下还是增加timeout和interval参数
#         #12/04/12 jonliang    去掉timeout与interval参数
#         '''在timeout时间内检查控件是否存在，返回True or False
#         
#         :param kwargs: 可变参数。代表控件类实例化所需的参数，比如说通过MainPanel类调用该函数，则参数传入qqapp实例
#         :param args: 可变参数。代表控件类实例化所需的参数，比如说通过MainPanel类调用该函数，则参数传入qqapp实例
#         :return: 该类型控件是否存在，True or False
#         :attention: 如果通过某个类的QPATH能找到多个符合条件的控件，会抛出ControlAmbiguousError，
#                                                     这表明该控件类的QPATH定义是不准确的
#         '''
#         return cls(*args, **kwargs).exist()
    
    def _click(self, mouseFlag, clickType, xOffset, yOffset):
        '''点击控件
        
        :type mouseFlag: tuia.mouse.MouseFlag
        :param mouseFlag: 鼠标按钮
        :type clickType: tuia.mouse.MouseClickType 
        :param clickType: 鼠标动作
        :type xOffset: int
        :param xOffset: 距离控件区域左上角的偏移。
                                                               默认值为None，代表控件区域x轴上的中点；
                                                               如果为负值，代表距离控件区域右边的绝对值偏移；
        :type yOffset: int
        :param yOffset: 距离控件区域左上角的偏移。
                                                               默认值为None，代表控件区域y轴上的中点；
                                                              如果为负值，代表距离控件区域上边的绝对值偏移；
        '''
        #2011/08/22 aaronlai    增加xOffset,yOffset参数
        if not self.BoundingRect:
            return
        (l, t, r, b) = self.BoundingRect.All
        if xOffset is None:
            x = (l+r)/2
        else:
            if xOffset < 0:
                x = r + xOffset
            else:
                x = l + xOffset
        if yOffset is None:
            y = (t+b)/2
        else:
            if yOffset < 0:
                y = b + yOffset
            else:
                y = t + yOffset        
        Mouse.click(x,y, mouseFlag, clickType)
        
    def click(self, mouseFlag=MouseFlag.LeftButton, 
                    clickType=MouseClickType.SingleClick,
                    xOffset=None, yOffset=None):
        '''点击控件
        
        :type mouseFlag: tuia.mouse.MouseFlag
        :param mouseFlag: 鼠标按钮
        :type clickType: tuia.mouse.MouseClickType 
        :param clickType: 鼠标动作
        :type xOffset: int
        :param xOffset: 距离控件区域左上角的偏移。默认值为None，代表控件区域x轴上的中点。 如果为负值，代表距离控件区域右上角的x轴上的绝对值偏移。
        :type yOffset: int
        :param yOffset: 距离控件区域左上角的偏移。 默认值为None，代表控件区域y轴上的中点。如果为负值，代表距离控件区域右上角的y轴上的绝对值偏移。
        '''
        #2011/08/22 aaronlai    增加xOffset,yOffset参数
        x, y = self._getClickXY(xOffset, yOffset)
        Mouse.click(x,y, mouseFlag, clickType)
        
    def _getClickXY(self, xOffset, yOffset):
        '''通过指定的偏移值确定具体要点击的x,y坐标
        '''
        if not self.BoundingRect:
            return
        (l, t, r, b) = self.BoundingRect.All
        if xOffset is None:
            x = (l+r)/2
        else:
            if xOffset < 0:
                x = r + xOffset
            else:
                x = l + xOffset
        if yOffset is None:
            y = (t+b)/2
        else:
            if yOffset < 0:
                y = b + yOffset
            else:
                y = t + yOffset
        return x, y       
    
    def doubleClick(self, xOffset=None, yOffset=None):
        """左键双击，参数参考click函数
        """
        self.click(MouseFlag.LeftButton, MouseClickType.DoubleClick, xOffset, yOffset)
    
    def hover(self):
        """鼠标移动到该控件上
        """
        if not self.BoundingRect:
            return
#        (l, t, r, b) = (self.BoundingRect.Left, 
#                        self.BoundingRect.Top,
#                        self.BoundingRect.Right,
#                        self.BoundingRect.Bottom
#                        )

        x, y = self.BoundingRect.Center.All
        Mouse.move(x, y)
        
    def rightClick(self, xOffset=None, yOffset=None):
        """右键双击，参数参考click函数
        """
        self.click(MouseFlag.RightButton, xOffset=xOffset, yOffset=yOffset)
    
       
#    def leftClick(self):
#        #2011/1/25  xandywang  添加 
#        self.click(MouseFlag.LeftButton)
        
    def drag(self, toX, toY):
        '''拖拽控件到指定位置
        '''
        if not self.BoundingRect:
            return
        (l, t, r, b) = (self.BoundingRect.Left, 
                        self.BoundingRect.Top,
                        self.BoundingRect.Right,
                        self.BoundingRect.Bottom
                        )
        x, y = (l+r)/2, (t+b)/2
        Mouse.drag(x, y, toX, toY)
    
    def sendKeys(self, keys):
        '''发送按键命令
        '''
        self.setFocus()
        Keyboard.inputKeys(keys)

    def setFocus(self):
        '''设控件为焦点
        '''
        raise NotImplementedError('please implement in sub class')
    
    def waitForValue(self, prop_name, prop_value, timeout=10, interval=0.5, regularMatch=False):
        """等待控件属性值出现, 如果属性为字符串类型，则使用正则匹配
        
        :param prop_name: 属性名字
        :param prop_value: 等待出现的属性值
        :param timeout: 超时秒数, 默认为10
        :param interval: 等待间隔，默认为0.5
        :param regularMatch: 参数 property_name和waited_value是否采用正则表达式的比较。默认为不采用（False）正则，而是采用恒等比较。
        """
        Timeout(timeout, interval).waitObjectProperty(self, prop_name, prop_value, regularMatch)
    
    @property
    def BoundingRect(self):
        """返回窗口大小。未实现！
        """
        raise NotImplementedError("please implement in sub class")
    
    def equal(self, other):
        '''判断两个对象是否相同。未实现!
        
        :type other: Control
        :param other: 本对象实例
        '''
        #2014/08/21 aaronlai    创建
        raise NotImplementedError("please implement in sub class")
        
    def __eq__(self, other):
        """重载对象恒等操作符(==)
        """
        #2014/08/20 aaronlai    创建
        return self.equal(other)
    
    def __ne__(self, other):
        """重载对象不等操作符(!=)
        """
        return (not self.equal(other))
    
class ControlContainer(object):
    '''控件集合接口
    
    当一个类继承本接口，并设置Locator属性后，该类可以使用Controls属于获取控件。如
    
    >>>class SysSettingWin(gf.GFWindow, ControlContainer)
            def __init__(self):
                locators={'基本设置Tab': {'type':gf.Button, 'root':self, 'locator'='Finger_Btn'},
                          '常规页': {'type':gf.Control, 'root':self, 'locator'='PageBasicGeneral'},
                          '退出程序单选框': {'type':gf.RadioBox, 'root':'@常规页','locator'=QPath("/name='ExitPrograme_RI' && maxdepth='10'")}}
                self.updateLocator(locators)
                                 
    则SysSettingWin().Controls['基本设置Tab']返回设置窗口上基本设置Tab的gf.Button实例,
    而SysSettingWin().Controls['退出程序单选框']，返回设置窗口的常规页下的退出程序单选框实例。
    其中'root'='@常规页'中的'@常规页'表示参数'root'的值不是这个字符串，而是key'常规页'指定的控件。
    '''
    
    def __init__(self):
        self._locators = {}
    
    def __findctrl_recur(self, ctrlkey):
        #12/04/11    jonliang    修改子控件名错误时的异常提示
        
        if not (ctrlkey in self._locators.keys()):
            raise NameError("%s没有名为'%s'的子控件！" % (type(self), ctrlkey))
        params = self._locators[ctrlkey].copy()
        ctrltype = params['type']
        del params['type']
        for key in params:
            value = params[key]
            if isinstance(value, basestring) and value.startswith('@'):
                params[key] = self.__findctrl_recur(value[1:])
        return ctrltype(**params)
        
        
    def __getitem__(self, index):
        '''获取index指定控件
        
        :type index: string
        :param index: 控件索引，如'查找按钮'  
        '''
        return self.__findctrl_recur(index)
    
    def clearLocator(self):
        '''清空控件定位参数
        '''
        self._locators = {}
    
    def hasControlKey(self, control_key):
        '''是否包含控件control_key
        
        :rtype: boolean
        '''
        #11/07/01 allenpan    添加此函数
        return self._locators.has_key(control_key)
    
    def updateLocator(self, locators):
        '''更新控件定位参数
        
        :type locators: dict
        :param locators: 定位参数，格式是 {'控件名':{'type':控件类, 控件类的参数dict列表}, ...}
        '''
        self._locators.update(locators)    
     
    def isChildCtrlExist(self, childctrlname):
        '''判断指定名字的子控件是否存在
        
        :param childctrlname: 指定的子控件名称
        :type childctrlname: str
        :rtype: boolean
        '''
        #12/04/12    jonliang    创建
        return self.Controls[childctrlname].exist()
    
    @property
    def Controls(self):
        '''返回控件集合。使用如foo.Controls['最小化按钮']的形式获取控件
        '''
        return self
        
        
        
    
            
if __name__ == "__main__":
    pass
