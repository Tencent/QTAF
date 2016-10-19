# -*- coding: utf-8 -*-
'''
GF控件模块
'''
#10/11/04 allenpan    用消息方式发送鼠标键盘消息
#10/11/11 aaronlai    从控件类中分离出控件定位功能、修改Control.BoundingRect的返回类型
#10/11/12 aaronlai    修改Control.__init__和注释
#10/11/15 aaronlai    在Control.__init__判断查找返回的控件、修改ListHeader.BoundingRect属性和ListSubItem.BoundingRect属性
#10/11/16 aaronlai    在Control.__init__抛出控件查找结果的异常、增加GFWindow类
#10/11/18 aaronlai    修改ListSubItem.click和ListHeader.click方法的参数名
#10/11/25 aaronlai    增加Control.GFWin、去除Menu.__init__
#10/11/26 aaronlai    修改PasswordBox类的clear和setPassword函数，防止死循环
#10/12/02 aaronlai    修改Control.GFWin属性为Control.GFWindow
#10/12/14 allenpan    GFWindow继承ControlContainer，并加入最小化，最小化和关闭按钮
#10/12/15 aaronlai    修改Control.click方法，实现MenuItem.SubMenu方法
#10/12/20 allenpan    增加RadioButton类
#10/12/20 aaronlai    增加IE类、_DetouredTextItem、DetouredTextItems类
#                     增加GFWindow.DetouredTextItems属性和Control.DetouredText属性
#10/12/21 allenpan    修改Menu使可以无需QPath定位；MenuItem.SubMenu的实现使用IGFAccessbile接口
#10/12/21 aaronlai    增加RichStatic类，删除_DetouredTextItem、DetouredTextItems类
#10/12/22 allenpan    增加ListView和ListCtrl的支持
#10/12/23 wingyipye   增加ComboButton
#10/12/29 aaronlai    修改GFWindow._DetouredTextItems属性
#10/12/30 aaronlai    增加Control.Type属性，修改ComboBox的属性
#10/12/31 allenpan    encode gf.Control.ToolTip as utf8
#11/01/04 aaronlai    取出Control.click方法里的bringForeground方法的调用，更改_ButtonState为ButtonState
#11/01/08 aaronlai    增加TreeView控件
#11/01/12 aaronlai    增加ScrollBar类，修改ListView、ListViewItem等系列控件的方法
#11/01/13 aaronlai    增加Scroll.backward和forward方法、增加ComboBox.Style属性
#11/01/17 aaronlai    修改ListViewSubItem.Text的bug、修改MenuItem的方法
#11/03/17 dadalin     增加Calendar类
#11/03/18 dadalin     增加Flash类
#11/03/22 joyhu       修改Control.__init__
#11/06/09 rayechen    新增_QQKey类，修改Control类的sendKeys方法
#11/08/18 aaronlai    增加TabButton类
#11/12/12 aaronlai    用_tif.TestObjectMgr代替HummerHelper
#11/09/20 rayechen    新增Slider类
#13/03/06 pillarzou   Button类新增获取face的方法

import win32con
import win32gui
import ctypes
import types
import pythoncom
import datetime
import time
from win32com.client.dynamic import CDispatch

import control
from mouse import Mouse, MouseFlag, MouseClickType
from keyboard import Keyboard, Key
import wincontrols
import util
from testbase.util import LazyInit, Timeout
import _tif
import accessible
from tuia.exceptions import ControlAmbiguousError, ControlNotFoundError, ControlExpiredError, TimeoutError

# class static_or_member_method(object):
#     '''构建一个同时支持静态函数方式和成员函数方式调用的函数
#     '''
#     def __init__(self, member_handler, static_handler ):
#         self.member_handler = member_handler
#         self.static_handler = static_handler
#         
#     def __get__(self, obj, cls):
#         if obj is None:
#             return self.static_handler
#         else:
#             return self.member_handler.__get__(obj,cls)
        
#===============================================================================
# 全局私有函数定义
#===============================================================================
def _find_by_name(gfcontrol, name):
    #2011/04/20 aaronlai    name为中文情况下的查找，需修改编码
    #2011/11/23 jonliang    修改使用的异常类型
    #2011/11/24 jonliang    修正编码
    if type(name) != types.UnicodeType:
        ucname = unicode(name,'utf8')
    try:
        return gfcontrol._gfacc.getDescendantByName(ucname)
    except pythoncom.com_error:
        raise ControlNotFoundError("没有找到Name属性为%s的子控件"%name)
#===============================================================================
# Key继承类定义
#===============================================================================
class _QQKey(Key):
    """向QQ发送的Key类
    
    该类与Key类的区别在于：被发送消息的窗口所在进程被注入了一个模块，以便可以处理自Post消息
    和Event对象进行进程间同步，使用此种方式保证所Post的消息已被对方消息循环取到并被处理
    """
    #11/06/09 rayechen    新增_QQKey类
    #2014/04/15 aaronlai    bug fix：Keyboard.postKey(hwnd, '3:20')，实际结果为:"3;20"
    def postKey(self, hwnd):
        '''将按键消息发到hwnd
        '''
        #处理所有
        for mkey in self._modifiers:
            mkey._inputKey(up=False)
            time.sleep(0.01) #必须加，否则下面实际寄送的键盘按键消息可能比这个消息更快到达目标窗口

        if self._scan < 256:
            self._postKey(hwnd, up=False)
            self._postKey(hwnd, up=True)
        else:
            ctypes.windll.user32.PostMessageW(hwnd, win32con.WM_CHAR, self._scan, 1)
        
        #进行同步
        import tuia.util
        tuia.util.MsgSyncer(hwnd).wait()
        
        for mkey in self._modifiers:
            mkey._inputKey(up=True)

#===============================================================================
# 控件类定义
#===============================================================================
class _GFAcc(object):
    '''
    GF接口访问类
    '''
    #15/02/04 pillarzou 新建
    
    def __init__(self, gfacc):
        '''构造函数
        :param gfacc: gf的com访问接口
        :type gfacc: com实例
        '''
        self._gfacc = gfacc
        
    def __getattr__(self, attrname):
        return getattr(self._gfacc, attrname)
    
    def empty_invoke(self):
        '''空调用
        '''
        pass
    
    def equal(self, other):
        #2014/08/20 aaronlai    创建
        if not isinstance(other, Control):
            return False
        if self.ProcessId != other.ProcessId:
            return False
        return self._gfacc == other._gfacc
            
    @property
    def BoundingRect(self):
        rect = self._gfacc.getLocation()
        if rect:
            return util.Rectangle(rect)
        return None
        
    @property
    def Children(self):
        cnt = self._gfacc.childCount
        children = []
        try:
            for idx in range(cnt):
                children.append(Control(root=self._gfacc.getChildByIndex(idx)))
        except pythoncom.com_error: #遇到com_error，可能是控件的子节点减少，直接退出即可
            pass
        return children
    
    @property
    def Config(self):
        return self._gfacc.config
    
    @property
    def Enabled(self):
        return self._gfacc.isEnabled
    
    @property
    def GFWindow(self):
        #2011/02/24 aaronlai    捕获异常
        #2012/05/09 aaronlai    修正捕获的异常
        if isinstance(self, GFWindow):
            return self
        else:
            try:
                return GFWindow(root=wincontrols.Window(root=self.HWnd))
            except ControlNotFoundError:
                return None
            except pythoncom.com_error:
                return None
        
    @property
    def HWnd(self):        
        return self._gfacc.hwnd
    
    @property
    def Name(self):
        #2011/05/11 aaronlai    修改返回值的编码
        name = self._gfacc.name        
        if name != None:
            return name.encode('utf8')
        else:
            return ""
    
    @property
    def Parent(self):
        parent = self._gfacc.parent 
        if parent == None:
            return None
        else:
            return Control(root=parent)   
    
    @property 
    def ProcessId(self):
        hwnd = self._gfacc.hwnd
        return wincontrols.Control(root=hwnd).ProcessId    
    
    @property
    def Text(self):
        text = self._gfacc.text
        if text != None:
            return text.encode('utf8')
        else:
            return ""
    
    @property
    def Valid(self):
        try:
            return self._gfacc.isValid
        except AttributeError: #allenpan: 遇到AttributeError是因为对象已不存在
            return False
    
    @property
    def Value(self):        
        return self._gfacc.value
    
    @Value.setter
    def Value(self, value):
        if isinstance(value, str):
            self._gfacc.value = value.decode('utf8')
        else:            
            self._gfacc.value = value
    
    @property
    def Visible(self):
        """是否可见
        """
        #2011/05/17 aaronlai    修改返回值
        try:
            return self._gfacc.isVisible
        except AttributeError, pythoncom.com_error:
            return False
    
    @property
    def Focus(self):
        """是否具有焦点
        """
        #2011/03/21 aaronlai    created
        return self._gfacc.isFocus
    
    @property
    def ThreadId(self):
        hwnd = self._gfacc.hwnd
        return wincontrols.Control(root=hwnd).ThreadId
    
    @property
    def ToolTip(self):
        tooltip = self._gfacc.toolTip
        if tooltip != None:
            return tooltip.encode('utf8')
        else:
            return ""
        
    @property
    def AccessibleObject(self):
        #2012/12/26 aaronlai    create
        #2013/01/21 aaronlai    修改实现:如果控件不支持IAccessible接口，那么在调用getAccessibleObject就会抛异常，
        #                       用例将执行不了，因此，需要catch异常，改为返回None，由脚本根据返回值决定用例是否执行。
        try:
            acc_disp = self._gfacc.getAccessibleObject()
            if acc_disp:
                return accessible.AccessibleObject(acc_disp)
        except pythoncom.com_error:
            pass
        return None
    
    @property
    def Type(self):
        return self._gfacc.type
                
    def setFocus(self):
        #2014/08/07 aaronlai    判断控件是否有效，是否已具有焦点
        if self.Valid and not self.Focus:
            wincontrols.Window(root=self.HWnd).setFocus()
            self._gfacc.setFocus()
    
    def getDescendantByName(self, name):
        return Control(root=self._gfacc.getDescendantByName(unicode(name)))
    
    
class Control(control.Control):
    '''
    GF控件基类，包装IGFAccessible接口
    '''
    def __init__(self, root=None, locator=None):
        """ Constructor
        
        :type root: gfcontrols.Control or wincontrols.Control
        :param root: 开始查找的GF控件或包含GF的win32control.Window；
        :type locator: qpath.QPath or GF的名字(字符串类型)
        :param locator: 查询类的实例, 如果是None，则将root作为此窗口；或者是GF的名字。
        :attention: 参数root和locator不能同时为None
        """        
        control.Control.__init__(self)
        
        if locator is None and root is None:
            raise RuntimeError("传入参数locator和root不能同时为None!")        
        self._root = root
        self._locator = locator
        self._gfacc = LazyInit(self, '_gfacc', self._init_gfacc_obj)
                   
    def _init_gfacc_obj(self):
        '''初始化gf访问接口
        '''
        #2011/02/24 aaronlai    在注入前，增加对进程是否存在的判断
        #2011/03/16 aaronlai    因root.ProcessId返回值修改而修改
        #2011/03/29 aaronlai    增加对root是否有效的判断
        #2011/06/07 aaronlai    丰富异常信息展示
        #2011/09/02 jonliang    修改一处异常的显示内容
        #2011/11/24 jonliang    修改retry过滤的异常类型
        #2012/03/13 jonliang    修改retry过滤的异常类型
        #2012/03/22 aaronlai    兼容root为win32控件类型且locator为GFWindow的QPath类型的情况
        if isinstance(self._root, wincontrols.Control):            
            pid = self._root.ProcessId
            if not pid or not self._root.Valid: 
                raise ControlExpiredError("父控件/父窗口已经失效，查找中止！")
            if self._locator is None:
                gfentry = _tif.TestObjectMgr(pid).queryObject('GFEntry')
                try:
                    self._root = Control(root=gfentry.getGFObjectFromWindow(self._root.HWnd))
                except pythoncom.com_error:
                    raise ControlExpiredError("父控件/父窗口已经失效，查找中止！")
                except AttributeError:
                    raise ControlExpiredError("父控件/父窗口已经失效，查找中止！")
            
        if self._locator is None:
            if isinstance(self._root, Control):                
                self._root.empty_invoke() #触发_init_gfacc_obj函数调用，以便得到_GFAcc接口
                gfacc = self._root._gfacc                
            elif isinstance(self._root, CDispatch):
                gfacc = _GFAcc(self._root)
            else:
                raise TypeError("root应为gfcontrols.Control类型或者CDispatch类型，实际类型为：%s" % type(self._root))
        else:
#            self._timeout = util.Timeout(5,0.5) #控件查找timeout时间 
            if isinstance(self._locator, basestring):
                if isinstance(self._root, Control):
                    kwargs = {'gfcontrol':self._root, 'name': self._locator}
                    try:
                        foundctrl = self._timeout.retry(_find_by_name, kwargs, (ControlNotFoundError))
                        foundctrl.empty_invoke() #触发_init_gfacc_obj函数调用，以便得到_GFAcc接口
                        gfacc = foundctrl._gfacc
                    except TimeoutError:
                        raise ControlNotFoundError("找不到name为%s的GF子控件！" % self._locator)
                else:
                    raise TypeError("root应为gfcontrols.Control类型，实际类型为：%s" % type(self._root))
            else:
                try:
                    kwargs = {'root':self._root}
                    foundctrls =  self._timeout.retry(self._locator.search, kwargs, (), self.__validCtrlNum)
                except TimeoutError, erro:
                    raise ControlNotFoundError("<%s>中的%s查找超时：%s" % (self._locator,self._locator.getErrorPath(),erro))                
                nctrl = len(foundctrls)
                if (nctrl>1):
                    raise ControlAmbiguousError("<%s>找到%d个控件" % (self._locator, nctrl))
                foundctrls[0].empty_invoke() #触发_init_gfacc_obj函数调用，以便得到_GFAcc接口
                gfacc = foundctrls[0]._gfacc
        return gfacc
    
    def empty_invoke(self):
        '''空调用
        '''
        return self._gfacc.empty_invoke()
    
    def __str__(self):
        """重载__str__，用于返回控件的一些属性信息
        
        """
        #2013/01/05 aaronlai    创建
        #2013/01/14 aaronlai    转换编码
        fmt_str = "Type=%s; Name=%s; Config=%s;" % (self._gfacc.Type,
                                                self._gfacc.Name,
                                                self._gfacc.Config)
        return fmt_str.encode('utf8')
    
    def __validCtrlNum(self, ctrls):
        return (len(ctrls) > 0)
    
    def equal(self, other):
        '''判断两个对象是否相同。
        
        :type other: Control
        :param other: 本对象实例
        '''
        return self._gfacc.equal(other)
            
    @property
    def BoundingRect(self):
        """返回窗口大小
        
        :rtype: util.Rectangle
        :return: util.Rectangle实例，如果不能获取到GF控件的窗口大小，则返回None
        """
        return self._gfacc.BoundingRect
        
    @property
    def Children(self):
        return self._gfacc.Children
    
    @property
    def Config(self):
        return self._gfacc.Config
    
    @property
    def Enabled(self):
        return self._gfacc.Enabled
    
    @property
    def GFWindow(self):
        return self._gfacc.GFWindow
        
    @property
    def HWnd(self):
        return self._gfacc.HWnd
    
    @property
    def Name(self):
        return self._gfacc.Name
    
    @property
    def Parent(self):
        return self._gfacc.Parent
    
    @property 
    def ProcessId(self):
        return self._gfacc.ProcessId
    
    @property
    def Text(self):
        return self._gfacc.Text
    
    @property
    def Valid(self):
        return self._gfacc.Valid
    
    @property
    def Value(self):
        return self._gfacc.Value
    
    @Value.setter
    def Value(self, value):
        self._gfacc.Value = value
    
    @property
    def Visible(self):
        """是否可见
        """
        return self._gfacc.Visible
    
    @property
    def Focus(self):
        """是否具有焦点
        """
        #2011/03/21 aaronlai    created
        return self._gfacc.Focus
    
    @property
    def ThreadId(self):
        return self._gfacc.ThreadId
    
    @property
    def ToolTip(self):
        '''返回tooltip
        '''
        return self._gfacc.ToolTip
        
    @property
    def AccessibleObject(self):
        '''返回GF对应的IAccessible接口
        
        :rtype：accessible.AccessibleObject
        :return: GF控件对应的IAccessible接口
        '''
        return self._gfacc.AccessibleObject
    
    @property
    def Type(self):
        """返回控件类型
        """
        return self._gfacc.Type
        
    def click(self, mouseFlag=MouseFlag.LeftButton, 
                    clickType=MouseClickType.SingleClick,
                    xOffset=None, yOffset=None):
        """点击控件
        
        :type mouseFlag: tuia.mouse.MouseFlag
        :param mouseFlag: 鼠标按钮
        :type clickType: tuia.mouse.MouseClickType 
        :param clickType: 鼠标动作
        :type xOffset: int
        :param xOffset: 距离控件区域左上角的偏移。
                                                               默认值为None，代表控件区域x轴上的中点；
                                                               如果为负值，代表距离控件区域右上角的x轴上的绝对值偏移；
        :type yOffset: int
        :param yOffset: 距离控件区域左上角的偏移。
                                                               默认值为None，代表控件区域y轴上的中点；
                                                              如果为负值，代表距离控件区域右上角的y轴上的绝对值偏移；
        """
        #2011/02/14 aaronlai    修改实现
        #2011/03/30 allenpan    发送SETFOCUS消息，gf的menu需要监听这个消息
        #2011/03/31 allenpan    用回postClick，并加上消息同步机制
        #2011/08/22 aaronlai    增加xOffset,yOffset参数
        #2012/02/14 jonliang    获取点击位置的逻辑统一调用_getClickXY方法
        #2012/03/16 rayechen   修改hover位置
        #2012/03/27 jonliang    修正错误的hover位置
        #2012/07/17 jonliang    click之前先hover可能会引起其他行为，去掉hover（eeelin协议测试发现），仅在ComboButton的click里进行hover操作
        x, y = self._getClickXY(xOffset, yOffset)
        hwnd = self.HWnd
        Mouse.postClick(hwnd, x, y, mouseFlag, clickType)
        import tuia.util
        tuia.util.MsgSyncer(hwnd).wait()
        
    def hover(self, xOffset=None, yOffset=None):
        """鼠标悬停
        """
        #2011/04/11 aaronlai    创建
        #2011/04/13 aaronlai    修改Mouse.move为_postMove
        #2012/02/10 rayechen  【临时方案】增加等待，若不等待则可能造成click无效
        #2011/03/16 rayechen  修改为兼容Offset
        #2012/04/12 aaronlai    修改_postMove为postMove
        if not self.BoundingRect:
            raise RuntimeError("BoundingRect为空！")

        if xOffset != None and yOffset != None:
            x, y = self._getClickXY(xOffset, yOffset)
        else:
            x, y = self.BoundingRect.Center.All
        
        hwnd = self.HWnd
        
#        Mouse.move(x, y)
        Mouse.postMove(hwnd, x, y)
        import tuia.util
        tuia.util.MsgSyncer(hwnd).wait()
        
        #增加等待
        import time
        time.sleep(0.5)
        
    def sendKeys(self, keys, interval=0.01):
        '''设置此控件具有输入焦点，并通过post message方式实现键盘输入
        
        :type keys: string
        :param keys: 输入的键值，参考tuia.keyboard.Keyboard类说明
        :type interval: int
        :param interval: 输入的每个键之间的间隔时间，默认值为0.01秒     
        '''
        #11/03/31 allenpan    添加消息同步机制
        #11/06/09 rayechen    使用_QQKey类postKey的同步特性替代之前的消息同步语句
        #12/11/18 aaronlai    增加参数"间隔时间"
        #14/08/07 aaronlai    判断控件是否有效，是否已具有焦点
        if not self.Valid:
            raise Exception("control is not valid, please create new instance!")
        self.setFocus()
        hwnd = self.HWnd
        
        oldkeyclass = Keyboard.selectKeyClass(_QQKey)
        Keyboard.postKeys(hwnd, keys, interval)
        Keyboard.selectKeyClass(oldkeyclass)
    
    def setFocus(self):
        '''设置控件焦点'''
        self._gfacc.setFocus()
    
    def getDescendantByName(self, name):
        'return the gf control by its name'
        return self._gfacc.getDescendantByName(name)
    
    def exist(self):
        '''判断控件是否存在
        '''  
        if isinstance(self._root, wincontrols.Control):
            pid = self._root.ProcessId
            if not pid or not self._root.Valid: 
                return False
            
        if self._locator is None:
            if isinstance(self._root, Control) or isinstance(self._root, wincontrols.Control):
                return self._root.exist()
            elif isinstance(self._root, CDispatch):
                return True            
            else:
                raise TypeError("root应为gfcontrols.Control/wincontrols.Control类型，实际类型为：%s" % type(self._root))
        else:
            if isinstance(self._locator, basestring):
                if isinstance(self._root, Control):
                    try:
                        foundctrl = _find_by_name(self._root, self._locator)
                        foundctrl.empty_invoke()
                        return (foundctrl._gfacc is not None)
                    except ControlNotFoundError:
                        return False
            else:
                if isinstance(self._root, Control):
                    if not self._root.exist():
                        return False
                foundctrls =  self._locator.search(root=self._root)           
                nctrl = len(foundctrls)
                if (nctrl>1):
                    raise ControlAmbiguousError("<%s>找到%d个控件" % (self._locator, nctrl))
                if (nctrl<1):
                    return False
                else:
                    return True
    
    #exist = static_or_member_method(_exist, control.Control.exist)
    
    def wait_for_exist(self, timeout, interval):
        '''等待控件存在
        '''
        Timeout(timeout, interval).retry(self.exist, (), (), lambda x:x==True)
        
    def waitForExist(self, timeout, interval):
        '''等待控件存在
        '''
        Timeout(timeout, interval).retry(self.exist, (), (), lambda x:x==True)
    
    def wait_for_invalid(self, timeout=10.0, interval=0.5 ):
        '''等待控件失效
        '''
        Timeout(timeout, interval).retry(self.exist, (), (), lambda x:x==False)
        
    def waitForInvalid(self, timeout=10.0, interval=0.5 ):
        '''等待控件失效
        '''
        Timeout(timeout, interval).retry(self.exist, (), (), lambda x:x==False) 
        
class Button(Control):
    '''
    Button 控件
    '''
    class _ButtonMsg(object):
        GETSTATE = 1
        ISGRAY = 2
        GETFACE = 3
    
    class EnumButtonState(object):
        """枚举Button状态
        """
        #2011/03/17 aaronlai    在Button类中定义
        #2011/04/27 jinghuang   类名大写
        GBS_UNKNOWN = 0 # 未知
        GBS_NORMAL = 1 # 正常
        GBS_HIGHLIGHT = 2 # 高亮
        GBS_PUSHED = 3 # 按下
        
    @property
    def State(self):
        """Button的状态
        
        :rtype: Button.EnumButtonState
        """
        #2011/08/22 aaronlai    修改实现
        self.Value = [Button._ButtonMsg.GETSTATE]
        return self.Value
    
    @property
    def Gray(self):
        """Button是否灰显
        """
        #2011/08/22 aaronlai    创建
        self.Value = [Button._ButtonMsg.ISGRAY]
        return self.Value
    
    @property
    def Face(self):
        """Button第几面（对双面Button有效）
        
        :rtype: 双面button的face只有0和1两个值，返回0或1
        """
        #2013/03/01 pillarzou    创建
        self.Value = [Button._ButtonMsg.GETFACE]
        return self.Value

class ComboButton(Button):
    '''
    ComboButton 控件
    '''
    class EnumComboButtonState(object):
        """枚举ComboButton状态
        """
        #2011/09/13 aaronlai    created
        GCBS_UNKNOWN = 0 # 未知
        GCBS_NORMAL = 1 # 正常
        GCBS_HIGHLIGHT = 2 # 高亮
        GCBS_PUSHED = 3 # 按下
        GCBS_ARWPUSHED = 4 # 按下
        
    @property
    def State(self):
        """ComboButton的状态
        
        :rtype: ComboButton.EnumComboButtonState
        """
        #2011/09/13 aaronlai    created
        return self.Value
        
    def dropMenu(self):
        #11/11/15 jonliang    改用Control.click
        self.click(xOffset=-5, yOffset=5)
        
    def click(self, mouseFlag=MouseFlag.LeftButton, 
                    clickType=MouseClickType.SingleClick,
                    xOffset=None, yOffset=None):
        '''由于combobutton的点击需要较长的鼠标停留时间，所以click前先hover
        '''
        #2012/07/17    jonliang    创建
        
        self.hover(xOffset, yOffset)
        Button.click(self, mouseFlag, clickType, xOffset, yOffset)

class CheckBox(Control):
    '''Checkbox控件
    '''
    
    @property
    def Checked(self):
        '返回勾选是否状态'
        return self.Value
    
    @Checked.setter
    def Checked(self, status):
        '''设置勾选状态
        
        :status: True为勾选，False为不勾选
                    直接设置，有可能不能触发其它控件，也有可能导致阻塞 
        '''
        #2011/03/25 aaronlai    QQInject内部有个阻塞式的方法调用，需更改直接赋状态值
        #2011/09/13 aaronlai    加上判断，如果不可操作，则直接返回
        if not self.Enabled:
            return
        if self.Value != status:
            self.click()

class _ComboBoxMsg(object):
    """ComboBox消息
    """
    GCB_GETCURSEL = 1
    GCB_GETCOUNT = 2
    GCB_SETCURSEL = 3
    GCB_SETTEXT = 4
    GCB_GETSTYLE = 5
    GCB_GETIMAGE = 6
    GCB_GETSEL_START = 7
    GCB_GETSEL_END = 8
    GCB_GETDEFAULTTEXT = 9
    GCB_GETHWND = 10
    
class ComboBox(Control):
    '''
    ComboBox控件
    '''
    class EnumCbxStyle(object):
        #2011/03/23 aaronlai    修改Style
        UNKNOWNTYPE = 0 # 未知风格 
        DROPDOWN = 1 # 可编辑
        DROPDOWNLIST = 2 # 不可编辑
    
    @property 
    def Count(self):
        '''返回ComboBox的项目数
        '''
        self.Value = [_ComboBoxMsg.GCB_GETCOUNT]
        return self.Value

    @property
    def Image(self):
        """获取图片文件名，如果存在的话
        """
        self.Value = [_ComboBoxMsg.GCB_GETIMAGE]
        return self.Value
    
    @property
    def SelectedIndex(self):
        '''返回当选选中的索引值
        '''
        self.Value = [_ComboBoxMsg.GCB_GETCURSEL]
        return self.Value

    @SelectedIndex.setter
    def SelectedIndex(self, index):
        '''设置当前选中索引值
        '''
        self.Value = [_ComboBoxMsg.GCB_SETCURSEL, int(index)]
        
    @property
    def SelectedText(self):
        """获取选中的文本
        """
        #2011/03/23 aaronlai    创建
        return self.Text
    
    @SelectedText.setter
    def SelectedText(self, text):
        """设置文本值(注:使用Text.setter可能不会触发其它逻辑操作)
        """
        #2011/03/23 aaronlai    创建
        #2012/01/05 aaronlai    修改提示语
        idx = self.SelectedIndex
        cnt = self.Count
        isFound = False
        for i in range(cnt):
            self.SelectedIndex = i
            if text == self.SelectedText:
                isFound = True
                break
        if not isFound:
            self.SelectedIndex = idx
            if self.Style != ComboBox.EnumCbxStyle.DROPDOWN: #如果不可编辑，且输入text找不到，则抛异常
                raise ValueError("不能选择，因为ComboBox不存在该选项%s!" % text)
    
    @property 
    def Text(self):
        return super(ComboBox, self).Text
    
    @Text.setter
    def Text(self, text):
        '''设置ComboBox文字
        '''
        #2011/02/16 aaronlai    指定编码
        #2011/03/23 aaronlai    加入Style判断
        if text == self.Text:
            return
        if self.Style != ComboBox.EnumCbxStyle.DROPDOWN:
            raise RuntimeError("设置值失败，ComboBox必须可编辑!")
        if type(text) == types.UnicodeType:
            self.Value = [_ComboBoxMsg.GCB_SETTEXT, text]
        else:
            self.Value = [_ComboBoxMsg.GCB_SETTEXT, unicode(text,'utf8')]
        
    @property
    def DefaultText(self):
        """返回缺省文字
        """
        #2011/03/04 aaronlai    created
        #2011/03/29 aaronlai    修改返回值编码
        self.Value = [_ComboBoxMsg.GCB_GETDEFAULTTEXT]
        text = self.Value
        if text:
            text = text.encode('utf8')
        return text            
#        self.Value = [_ComboBoxMsg.GCB_GETDEFAULTTEXT]
#        return self.Value
        
    @property
    def Style(self):
        """返回组合框的风格类型
        
        :rtype: ComboBox.EnumCbxStyle
        """
        self.Value = [_ComboBoxMsg.GCB_GETSTYLE]
        return self.Value 
    
    @property
    def SelectedRange(self):
        """返回选中文本的下标范围
        """
        if self.Style != ComboBox.EnumCbxStyle.DROPDOWN:
            raise RuntimeError("设置值失败，ComboBox必须可编辑!")
        self.Value = [_ComboBoxMsg.GCB_GETSEL_START]
        nStart = self.Value 
        self.Value = [_ComboBoxMsg.GCB_GETSEL_END]
        nEnd = self.Value
        return (nStart, nEnd)
    
    @property
    def HWnd(self):
        #2011/04/28 aaronlai    重载HWnd，请使用最新QQInject
        #2011/05/04 aaronlai    修改没有返回值的问题
        #2011/05/10 aaronlai    注释
        #2011/05/20 aaronlai    重新使用，以观效果
        self.Value = [_ComboBoxMsg.GCB_GETHWND]
        hwnd = self.Value
        if hwnd:
            return hwnd
        else:
            return super(ComboBox,self).HWnd
    
#    @property
#    def _RealHWnd(self):
#        self.Value = [_ComboBoxMsg.GCB_GETHWND]
#        return self.Value 
    
#    def sendKeys(self, keys):
#        '''键盘输入(重载基类函数）
#        '''
#        #11/05/10 aaronlai    创建
#        hwnd = self._RealHWnd
#        if hwnd:
#            self.setFocus()
#            Keyboard.postKeys(hwnd, keys)
#        else:
#            super(ComboBox,self).sendKeys(keys)
#            
#    def click(self, mouseFlag=MouseFlag.LeftButton, 
#                    clickType=MouseClickType.SingleClick):
#        """点击控件(重载基类函数）
#        """
#        #11/05/10 aaronlai    创建
#        if self._RealHWnd:
#            if not self.BoundingRect:
#                raise RuntimeError("BoundingRect为空！")
#            x, y = self.BoundingRect.Center.All
#            self.hover()
#            Mouse.postClick(self._RealHWnd, x, y, mouseFlag, clickType)
#        else:
#            super(ComboBox,self).click(mouseFlag, clickType)
 
class IE(Control):
    """IE控件
    """
    @property
    def Url(self):
        return self.Value


#===============================================================================
# Begin
#ListCtrl已实现支持，但因为没有看到QQ使用ListCtrl控件，所以暂时屏蔽掉ListCtrl控件
#2012/01/18 aaronlai    ListCtrl在QQCRM（BizQQ）中有用到，故重新提供使用
#===============================================================================
class _ListCtrlMsg(object):
    '''GFListCtrl消息定义
    '''
    GLC_GETHEADERCOUNT  =1  #获取header数  
    GLC_GETITEMCOUNT    =2  #获取listitem数  
    GLC_GETHEADERTEXT   =3  #获取指定列的header的文字  
    GLC_GETSUBITEMVALUE =4  #获取指定(行数，列数）subitem的文字  
    GLC_GETHEADERHEIGHT =5  #获取header高度 
    GLC_GETHEADERWIDTH  =6  #获取指定列header宽度 
    GLC_GETITEMHEIGHT   =7  #获取指定行高度  
    GLC_GETSCROLLINFO   =8  #获取滚动条信息
    GLC_GETPURECLIENTRECT = 9 #获取listctrl纯client rect的大小
    
class ListCtrlHeaderItem(object):
    '''
    ListCtrl的Header的一项
    '''
    def __init__(self, list_ctrl, header_index):
        self._list_ctrl = list_ctrl
        self._col = header_index
        
    @property
    def BoundingRect(self):
        """返回Header的位置
        
        :rtype: util.Rectangle
        :return: util.Rectangle的实例"""
        listloc = self._list_ctrl.BoundingRect
        xoff = 0
        for col in range(self._col):
            xoff += ListCtrlHeaderItem(self._list_ctrl, col).Width
        left = listloc.Left + xoff
        right = left + self.Width
        top = listloc.Top
        bottom = top + self._list_ctrl.HeaderHeight
        return util.Rectangle((left, top, right, bottom))
    
    @property
    def Text(self):
        '''返回HeaderItem文字
        '''
        self._list_ctrl.Value=[_ListCtrlMsg.GLC_GETHEADERTEXT, self._col]
        text = self._list_ctrl.Value
        return text
    
    @property
    def Width(self):
        '''返回HeaderItem宽度
        '''
        self._list_ctrl.Value = [_ListCtrlMsg.GLC_GETHEADERWIDTH, self._col]
        width = self._list_ctrl.Value
        return width
    
    def click(self, mouseFlag=MouseFlag.LeftButton, 
                    clickType=MouseClickType.SingleClick):
        if not self.BoundingRect:
            raise RuntimeError("BoundingRect为空！")
        self._list_ctrl.GFWindow.Window.bringForeground()
        (l, t, r, b) = self.BoundingRect.All
        x = (l+r)/2
        y = (t+b)/2
        Mouse.click(x, y, mouseFlag, clickType)
    
class ListCtrlSubItem(object):
    '''
    ListCtrl一行的一项
    '''
    
    def __init__(self, list_ctrl, index_listitem, index_subitem):
        self._list_ctrl = list_ctrl
        self._row = index_listitem
        self._col = index_subitem
    
    @property
    def Text(self):
        '''返回该项文字
        '''
        self._list_ctrl.Value=[_ListCtrlMsg.GLC_GETSUBITEMVALUE, self._row, self._col]
        return self._list_ctrl.Value
        
    @property
    def Width(self):
        self._list_ctrl.Value = [_ListCtrlMsg.GLC_GETHEADERWIDTH, self._col]
        return self._list_ctrl.Value
    
    @property
    def BoundingRect(self):
        rowRect = self._list_ctrl.Items[self._row].BoundingRect
        top = rowRect.Top
        bottom = rowRect.Bottom
        totalWidthBefore = 0
        col = 0
        while col < self._col:
            totalWidthBefore = totalWidthBefore + self._list_ctrl.HeaderItems[col].Width
            col = col + 1
        left = rowRect.Left + totalWidthBefore
        right = left + self.Width
        return util.Rectangle((left,top,right,bottom))
    
    @property
    def Visible(self):
        """该子项是否可见
        """
        #2012/01/18 aaronlai    created
        rowItem = self._list_ctrl.Items[self._row]
        if not rowItem.Visible:
            return False
        if self.BoundingRect.Center.X > self._list_ctrl.BoundingRect.Right or\
           self.BoundingRect.Center.X < self._list_ctrl.BoundingRect.Left:
            return False
        else:
            return True
        
    def click(self, mouseFlag=MouseFlag.LeftButton, 
                    clickType=MouseClickType.SingleClick):
        if not self.BoundingRect:
            raise RuntimeError("BoundingRect为空！")
        self._list_ctrl.GFWindow.Window.bringForeground()
        (l, t, r, b) = self.BoundingRect.All
        x = (l+r)/2
        y = (t+b)/2
        Mouse.click(x, y, mouseFlag, clickType)
        
    def ensureVisible(self):
        """确保该子项可见
        """
        #2012/01/18 aaronlai    created
        rowItem = self._list_ctrl.Items[self._row]
        if not rowItem.Visible:
            rowItem.ensureVisible()
        if not self.Visible:
            self._list_ctrl.GFWindow.Window.bringForeground()
            hScrollBar = self._list_ctrl.HorizontalScrollBar
            if hScrollBar:
                if self.BoundingRect.Center.X > self._list_ctrl.BoundingRect.Right:
                    while hScrollBar.forward():
                        if self.BoundingRect.Right <= self._list_ctrl.BoundingRect.Right:
                            return True
                elif self.BoundingRect.Center.X < self._list_ctrl.BoundingRect.Left:
                    while hScrollBar.backward():
                        if self.BoundingRect.Left >= self._list_ctrl.BoundingRect.Left:
                            return True
                return False
            return True
        

class ListCtrlItem(object):
    '''
    ListCtrl的每一行
    '''
    def __init__(self, list_ctrl, index_listitem):
        self._row = index_listitem
        self._list_ctrl = list_ctrl
    
    @property
    def SubItems(self):
        '''返回ListCtrlItem的所有子项ListCtrlSubItem
        '''
        self._list_ctrl.Value = [_ListCtrlMsg.GLC_GETHEADERCOUNT]
        colnum = self._list_ctrl.Value
        subitems = []
        for col in range(colnum):
            subitem = ListCtrlSubItem(self._list_ctrl, self._row, col)
            subitems.append(subitem)
        return subitems
    
    @property
    def Height(self):
        """ListItem的高
        """
        #12/01/16 aaronlai    创建
        self._list_ctrl.Value = [_ListCtrlMsg.GLC_GETITEMHEIGHT]
        return self._list_ctrl.Value
    
    @property
    def Width(self):
        """ListItem的总宽度，可能大于ListView的宽度
        """
        totalWidth = 0
        for subItem in self.SubItems:
            totalWidth += subItem.Width
        return totalWidth
    
    @property
    def BoundingRect(self):
        parentRect = self._list_ctrl.BoundingRect
        left = parentRect.Left
        hScrollbar = self._list_ctrl.HorizontalScrollBar
        if hScrollbar:
            left = left - hScrollbar.Position
        top = parentRect.Top + self._list_ctrl.HeaderHeight + self._row * self.Height
        vScrollbar = self._list_ctrl.VerticalScrollBar
        if vScrollbar:
            top = top - vScrollbar.Position
        right = left + self.Width
        bottom = top + self.Height
        return util.Rectangle((left,top,right,bottom))
    
    @property
    def Visible(self):
        """该项是否可见
        """
        #2012/01/18 aaronlai    created
        if self.BoundingRect.Center.Y > self._list_ctrl.BoundingRect.Bottom or\
           self.BoundingRect.Center.X < self._list_ctrl.BoundingRect.Top:
            return False
        else:
            return True
        
    def ensureVisible(self):
        """确保该项可见
        """
        #2012/01/18 aaronlai    created
        #2013/01/16 aaronlai    因ScrollBar接口更改，修改实现方式
        if not self.Visible:
            vScrollBar = self._list_ctrl.VerticalScrollBar
            if vScrollBar:
                self._list_ctrl.GFWindow.Window.bringForeground()
                if self.BoundingRect.Center.Y > self._list_ctrl.BoundingRect.Bottom:
                    while vScrollBar.forward():
                        if self.BoundingRect.Center.Y <= self._list_ctrl.BoundingRect.Bottom:
                            return True
                elif self.BoundingRect.Center.Y < self._list_ctrl.BoundingRect.Top:
                    while vScrollBar.backward():
                        if self.BoundingRect.Center.Y >= self._list_ctrl.BoundingRect.Top:
                            return True
                return False
            return True
        
class _ScrollBarSnapshot(object):
    def __init__(self, sbinfo, rc, hwnd):
        self.sbinfo = sbinfo
        self.rc = rc
        self.hwnd = hwnd
        
    @property
    def BoundingRect(self):
        return util.Rectangle(self.rc)
    
    def backward(self):
        """向后滚动一步
        """
        y = self.BoundingRect.Top + 8
        x = self.BoundingRect.Left + 8
        Mouse.click(x,y)
#        Mouse.sendClick(self.hwnd, x, y)
        
    def forward(self):
        """向前滚动一步
        """
        y = self.BoundingRect.Bottom - 8
        x = self.BoundingRect.Right - 8
        Mouse.click(x,y)
    
    @property
    def MiniPos(self):
        return self.sbinfo[0]
    
    @property
    def MaxPos(self):
        return self.sbinfo[1]
    
    @property
    def Position(self):
        return self.sbinfo[2]
    
    @property
    def Page(self):
        return self.sbinfo[3]
    
class ListCtrl(Control):
    '''
    GF ListCtrl 控件类型
    '''

    @property
    def HeaderHeight(self):
        '''返回Header高度
        '''
        self.Value = [_ListCtrlMsg.GLC_GETHEADERHEIGHT]
        header_height = self.Value
        return header_height
    
    @property
    def HeaderItems(self):
        '''返回Header的全部ListCtrlHeaderItem
        '''
        self.Value = [_ListCtrlMsg.GLC_GETHEADERCOUNT]
        headercnt = self.Value
        headers = []
        for col in range(headercnt):
            header = ListCtrlHeaderItem(self, col)
            headers.append(header)
        return headers
    
    @property
    def Items(self):
        '''返回ListCtrl的全部ListCtrlItem
        '''
        self.Value = [_ListCtrlMsg.GLC_GETITEMCOUNT]
        itemcnt = self.Value
        items = []
        for row in range(itemcnt):
            item = ListCtrlItem(self, row)
            items.append(item)
        return items
    
    @property
    def VerticalScrollBar(self):
        """返回ListView的垂直滚动条控件，如果存在的话
        """
        rc = self.BoundingRect.All
        self.Value = [_ListCtrlMsg.GLC_GETSCROLLINFO]
        info = self.Value
        w = rc[2] - rc[0]
        self.Value = [_ListCtrlMsg.GLC_GETPURECLIENTRECT]
        cx,cy = self.Value
        if w-cx <= 10: #有垂直滚动条
            left = self.BoundingRect.Left + cx
            top = self.BoundingRect.Top
            right = self.BoundingRect.Right
            bottom = self.BoundingRect.Bottom + self.HeaderHeight + cy
            return _ScrollBarSnapshot((info[5:9]),(left,top,right,bottom), self.HWnd)
        return None
        
    @property
    def HorizontalScrollBar(self):
        """返回ListView的水平滚动条控件，如果存在的话
        """
        rc = self.BoundingRect.All
        self.Value = [_ListCtrlMsg.GLC_GETSCROLLINFO]
        info = self.Value
        h = rc[3] - rc[1]
        self.Value = [_ListCtrlMsg.GLC_GETPURECLIENTRECT]
        cx,cy = self.Value
        if h-cy-self.HeaderHeight >= 10: #有水平滚动条
            left = self.BoundingRect.Left
            top = self.BoundingRect.Top + self.HeaderHeight + cy
            bottom = self.BoundingRect.Bottom
            right = left + cx
            return _ScrollBarSnapshot((info[0:4]),(left,top,right,bottom), self.HWnd)
        return None
    
    @property
    def TotalItemHeight(self):
        """返回ListView的所有行的总高度
        """
        totalHeight = 0
        for item in self.Items:
            totalHeight += item.Height
        return totalHeight
#===============================================================================
# End
#===============================================================================

class _ListViewMsg(object):
    '''GFListCtrl消息定义
    '''
    GLV_GETHEADERCOUNT=1    #获取header数
    GLV_GETITEMCOUNT=2        #获取listitem数
    GLV_GETHEADERTEXT=3        #获取指定列的header的文字 （未实现
    GLV_GETSUBITEMVALUE=4    #[obsolete]获取指定(行数，列数）subitem的文字 
    GLV_GETHEADERHEIGHT=5    #获取header高度
    GLV_GETHEADERWIDTH=6        #获取指定列header宽度
    GLV_GETITEMHEIGHT=7        #获取指定行高度
    GLV_GETSUBITEM_TEXT=8    #获取指定（行，列）subitem的文字
    GLV_GETSUBITEM_IMGPATH=9  #获取指定（行，列）subitem的图片路径
    GLV_GETSUBITEM_INNERCTRL=10 #获取指定（行，列）subitem的内部控件
    GLV_GETITEMSTATE = 11 # 获取子项的状态

class ListViewHeaderItem(object):
    '''
    ListView的Header里的每一项
    '''
    def __init__(self, list_ctrl, header_index):
        self._list_ctrl = list_ctrl
        self._col = header_index
    
    @property
    def Text(self):
        '''返回该列Header文字
        '''
        #2011/08/15 aaronlai    实现
        self._list_ctrl.Value = [_ListViewMsg.GLV_GETHEADERTEXT, self._col]
        txt = self._list_ctrl.Value
        if txt:
            txt = txt.encode('utf8')
        return txt
    
    @property
    def Width(self):
        '''返回该列Header宽度
        '''
        self._list_ctrl.Value = [_ListViewMsg.GLV_GETHEADERWIDTH, self._col]
        width = self._list_ctrl.Value
        return width
    
class ListViewSubItem(object):
    '''
    ListCtrl一行的一项
    '''
    
    def __init__(self, list_ctrl, index_listitem, index_subitem):
        self._list_ctrl = list_ctrl
        self._row = index_listitem
        self._col = index_subitem
    
    @property
    def BoundingRect(self):
        """获取此控件的区域
        
        :rtype: tuia.util.Rectangle
        """
        #2013/01/16 aaronlai    修改计算方式
        # QQ1.90版本后，消息管理器的滚动条只有当鼠标移到上面才会出现
        self._list_ctrl.hover()
        parentRect = self._list_ctrl.BoundingRect
        rowRect = self._list_ctrl.Items[self._row].BoundingRect
        top = rowRect.Top
        bottom = rowRect.Bottom
        totalWidthBefore = 0
        col = 0
        while col < self._col:
            totalWidthBefore = totalWidthBefore + self._list_ctrl.HeaderItems[col].Width
            col = col + 1
        
        hScrollbar = self._list_ctrl.HorizontalScrollBar
        if hScrollbar is None:
            left = rowRect.Left + totalWidthBefore
        else:
            totalItemWidth = self._list_ctrl.Items[self._row].Width
            curPos = hScrollbar.Position
            left = rowRect.Left + totalWidthBefore\
                  - int(curPos * (totalItemWidth-parentRect.Width))
        right = left + self.Width
        return util.Rectangle((left,top,right,bottom))
    
    @property
    def Column(self):
        """第几列(从0开始)
        """
        #2011/03/22 aaronlai    created
        return self._col
    
    @property
    def Height(self):
        #2011/01/20 aaronlai    增加返回值
        self._list_ctrl.Value=[_ListViewMsg.GLV_GETITEMHEIGHT, self._row, self._col]
        return self._list_ctrl.Value
    
    @property
    def ImagePath(self):
        '''返回该项的图片路径
        '''
        self._list_ctrl.Value=[_ListViewMsg.GLV_GETSUBITEM_IMGPATH, self._row, self._col]
        return self._list_ctrl.Value
                
    @property
    def InnerControl(self):
        '''返回该项内嵌控件
        '''
        self._list_ctrl.Value=[_ListViewMsg.GLV_GETSUBITEM_INNERCTRL, self._row, self._col]
        innerfrm = None
        if self._list_ctrl.Value:
            innerfrm = Control(root=self._list_ctrl.Value)
        return innerfrm
    
    @property
    def Text(self):
        '''返回文字
        '''
        #11/01/12 allenpan 将Text编码为utf-8
        self._list_ctrl.Value=[_ListViewMsg.GLV_GETSUBITEM_TEXT, self._row, self._col]
        text = self._list_ctrl.Value
        if text != None:
            return text.encode('utf-8')
        else:
            return ""
    
    @property
    def Visible(self):
        """该子项是否可见
        """
        #2011/02/14 aaronlai    created
        rowItem = ListViewItem(self._list_ctrl, self._row)
        if not rowItem.Visible:
            return False
        if self.BoundingRect.Right > self._list_ctrl.BoundingRect.Right or\
           self.BoundingRect.Left < self._list_ctrl.BoundingRect.Left:
            return False
        else:
            return True
        
    @property
    def Width(self):
        self._list_ctrl.Value = [_ListViewMsg.GLV_GETHEADERWIDTH, self._col]
        return self._list_ctrl.Value
    
    def click(self, mouseFlag=MouseFlag.LeftButton, 
                    clickType=MouseClickType.SingleClick):
        '''点击控件
        
        :type mouseFlag: tuia.mouse.MouseFlag
        :param mouseFlag: 鼠标按钮
        :type clickType: tuia.mouse.MouseClickType 
        :param clickType: 鼠标动作
        '''
        if not self.BoundingRect:
            raise RuntimeError("BoundingRect为空！")
        if not self.Visible:
            self.ensureVisible()
        (l, t, r, b) = self.BoundingRect.All
        x, y = (l+r)/2, (t+b)/2
        Mouse.sendClick(self._list_ctrl.HWnd, x, y, mouseFlag, clickType)
        
    def ensureVisible(self):
        """确保该子项可见
        """
        #2011/02/14 aaronlai    created
        #2013/01/16 aaronlai    因ScrollBar接口变更修改实现方式
        rowItem = ListViewItem(self._list_ctrl, self._row)
        if not rowItem.Visible:
            rowItem.ensureVisible()
        if self.Visible:
            return True
        else:
            hScrollBar = self._list_ctrl.HorizontalScrollBar
            if hScrollBar:
                if self.BoundingRect.Right > self._list_ctrl.BoundingRect.Right:
                    while hScrollBar.forward():
                        if self.BoundingRect.Right <= self._list_ctrl.BoundingRect.Right:
                            return True
                elif self.BoundingRect.Left < self._list_ctrl.BoundingRect.Left:
                    while hScrollBar.backward():
                        if self.BoundingRect.Left >= self._list_ctrl.BoundingRect.Left:
                            return True
                return False
            return True
    
class ListViewItem(control.Control):
    """ListCtrl的每一行
    """
    #11/04/02 allenpan    更改为control.Control继承
    
    LVIS_SELECTED = 0x2
    
    def __init__(self, list_ctrl, index_listitem):
        self._row = index_listitem
        self._list_ctrl = list_ctrl
    
    def setFocus(self):
        self._list_ctrl.setFocus()
        
    @property
    def BoundingRect(self):
        """返回此空间的区域
        
        :rtype: tuia.util.Rectangle
        """
        #2013/01/16 aaronlai    修改计算方式
        # QQ1.90版本后，消息管理器的滚动条只有当鼠标移到上面才会出现
        self._list_ctrl.hover()
        parentRect = self._list_ctrl.BoundingRect
        left = parentRect.Left
        right = parentRect.Right
        vScrollbar = self._list_ctrl.VerticalScrollBar
        if vScrollbar is None:
            top = parentRect.Top + self._list_ctrl.HeaderHeight + self._row * self.Height
        else:
            totalItemHeight = self._list_ctrl.TotalItemHeight
            curPos = vScrollbar.Position
            
            top = parentRect.Top + self._list_ctrl.HeaderHeight\
                  + self._row * self.Height\
                  - int((totalItemHeight-parentRect.Height) * curPos)
        bottom = top + self.Height
        return util.Rectangle((left,top,right,bottom))
    
    @property
    def Height(self):
        """ListViewItem高度
        """
        #11/01/20 aaronlai     created
        maxHeight = 0
        for subItem in self.SubItems:
            if subItem.Height > maxHeight:
                maxHeight = subItem.Height
        return maxHeight
    
    @property
    def Row(self):
        """第几行(从0开始)
        """
        #2011/03/22 aaronlai    created
        return self._row
    
    @property
    def Selected(self):
        """是否被选中
        """
        if (self._State & ListViewItem.LVIS_SELECTED) > 0:
            return True
        return False
        
    @property
    def _State(self):
        """返回项状态
        """
        #2011/03/29 aaronlai    修改实现的bug
        self._list_ctrl.Value = [_ListViewMsg.GLV_GETITEMSTATE, self._row]
        return self._list_ctrl.Value
        
    @property
    def SubItems(self):
        '''返回ListViewItem的所有子项
        
        :rtype: list of ListViewSubItem
        :return: 返回ListViewItem的所有子项
        '''
        self._list_ctrl.Value = [_ListViewMsg.GLV_GETHEADERCOUNT]
        colnum = self._list_ctrl.Value
        subitems = []
        for col in range(colnum):
            subitem = ListViewSubItem(self._list_ctrl, self._row, col)
            subitems.append(subitem)
        return subitems
        
    @property
    def Visible(self):
        """此控件是否在可见视图内
        """
        #2011/02/14 aaronlai    created
        if self.BoundingRect.Bottom > self._list_ctrl.BoundingRect.Bottom or\
           self.BoundingRect.Top < self._list_ctrl.BoundingRect.Top:
            return False
        else:
            return True
    
    @property
    def Width(self):
        """ListViewItem的总宽度，可能大于ListView的宽度
        """
        totalWidth = 0
        for subItem in self.SubItems:
            totalWidth += subItem.Width
        return totalWidth
       
    def click(self, mouseFlag=MouseFlag.LeftButton, 
                    clickType=MouseClickType.SingleClick,
                    xOffset=None,
                    yOffset=None):
        """点击控件
        
        :type mouseFlag: tuia.mouse.MouseFlag
        :param mouseFlag: 鼠标按钮
        :type clickType: tuia.mouse.MouseClickType 
        :param clickType: 鼠标动作
        """
        #2011/02/14 aaronlai    加入是否可见的判断
        #2011/04/02 allenpan    使用postClick并加上消息同步
        #2012/02/17 jonliang    增加offset参数
        x, y = self._getClickXY(xOffset, yOffset)
        Mouse.postClick(self._list_ctrl.HWnd, x, y, mouseFlag, clickType)
        util.MsgSyncer(self._list_ctrl.HWnd).wait()                
        
    def ensureVisible(self):
        """通过滚动，使此控件在可见视图内
        """
        #2011/02/14 aaronlai    created
        #2011/03/29 aaronlai    修改实现
        if self.Visible:
            return True
        else:
            # QQ1.90版本后，消息管理器的滚动条只有当鼠标移到上面才会出现
            self._list_ctrl.hover()
            vScrollBar = self._list_ctrl.VerticalScrollBar
            if vScrollBar:
                if self.BoundingRect.Center.Y > self._list_ctrl.BoundingRect.Bottom:
                    while vScrollBar.forward():
                        if self.BoundingRect.Center.Y <= self._list_ctrl.BoundingRect.Bottom:
                            return True
                elif self.BoundingRect.Center.Y < self._list_ctrl.BoundingRect.Top:
                    while vScrollBar.backward():
                        if self.BoundingRect.Center.Y >= self._list_ctrl.BoundingRect.Top:
                            return True
                return False
            return True
            
    def __getitem__(self, key):
        """根据key返回ListViewItem
        
        :type key: int
        :param key: 索引
        """
        #2011/03/22 aaronlai    created
        if isinstance(key, int):
            self._list_ctrl.Value = [_ListViewMsg.GLV_GETHEADERCOUNT]
            colnum = self._list_ctrl.Value
            if key >= colnum or key < 0:
                raise IndexError("key超出下标范围!")
            return ListViewSubItem(self._list_ctrl, self._row, key)
        raise TypeError("只支持整数类型索引")
            
class ListView(Control):
    '''GF LisView 控件类型
    
    使用如listview.Items[0].SubItems[2].Text返回第0行第2列项的文字
    '''

    @property
    def HeaderHeight(self):
        '''返回Header高度
        '''
        if self.HeaderCtrl is None:
            return 0
        self.Value = [_ListViewMsg.GLV_GETHEADERHEIGHT]
        header_height = self.Value
        return header_height
    
#    @property
#    def ItemHeight(self):
#        '返回ListItem高度'
#        self.Value = [_ListViewMsg.GLV_GETITEMHEIGHT]
#        itemheight =self.Value 
#        return itemheight
    
    @property
    def HeaderItems(self):
        '''返回LisView 的全部ListViewHeaderItem
        '''
        #2012/01/16 aaronlai    更名为Headers
        if self.HeaderCtrl is None:
            return []
        self.Value = [_ListViewMsg.GLV_GETHEADERCOUNT]
        headercnt = self.Value
        headers = []
        for col in range(headercnt):
            header = ListViewHeaderItem(self, col)
            headers.append(header)
        return headers
    
    @property
    def Items(self):
        '''返回LisView 的全部ListItem
        '''
        self.Value = [_ListViewMsg.GLV_GETITEMCOUNT]
        itemcnt = self.Value
        items = []
        for row in range(itemcnt):
            item = ListViewItem(self, row)
            items.append(item)
        return items
    
    @property
    def VerticalScrollBar(self):
        """返回ListView的垂直滚动条控件，如果存在的话
        """
        from qpath import QPath
        ctrls = QPath("/Config='vertscrollbar' && Visible='True' && MaxDepth='3'").search(self)
        if len(ctrls) == 1:
            return ScrollBar(root=ctrls[0])
        return None
    
    @property
    def HorizontalScrollBar(self):
        """返回ListView的水平滚动条控件，如果存在的话
        """
        from qpath import QPath
        ctrls = QPath("/Config='horzscrollbar' && Visible='True' && MaxDepth='3'").search(self)
        if len(ctrls) == 1:
            return ScrollBar(root=ctrls[0])
        return None
    
    @property
    def HeaderCtrl(self):
        """返回ListView的Header控件，如果存在的话
        """
        #2011/03/17 aaronlai    修改返回值
        from tuia.qpath import QPath
        ctrls = QPath("/Config='headerctrl' && Visible='True' && MaxDepth='3'").search(self)
        if len(ctrls) == 1:
            return Control(root=ctrls[0])
        return None
    
    @property
    def TotalItemHeight(self):
        """返回ListView的所有行的总高度
        """
        totalHeight = 0
        for item in self.Items:
            totalHeight += item.Height
        return totalHeight

    def __getitem__(self, key):
        """根据key返回MenuItem
        
        :type key: int
        :param key: 索引
        """
        #2011/03/22 aaronlai    created
        if isinstance(key, int):
            self.Value = [_ListViewMsg.GLV_GETITEMCOUNT]
            itemcnt = self.Value
            if key >= itemcnt or key < 0:
                raise IndexError("key超出下标范围!")
            return ListViewItem(self, key)
        raise TypeError("只支持整数类型索引")
    
class WebKitCtrl(Control):
    '''
    IGFWebKitCtrl 进程内WebKit控件
    WebKitCtrl不再使用，请使用qqlib.qqcontrols.WebKit
    '''
    #12/11/14    rayechen     创建
    #14/02/22 aaronlai    统一使用webkit控件
    def __init__(self, root=None, locator=None):
        raise Exception("WebKitCtrl不再使用，请使用qqlib.qqcontrols.WebKit") 
    
#    class _Msg(object):
#        '''IGFWebKitCtrl消息定义
#        '''
#        WEBKIT_GET_CEFBROWSER=1    # 获取进程内WebKit实例的CefBrowser指针
#    
#    @property
#    def CefBrowser(self):
#        ''' CefBrowser指针
#        
#        :returns: int
#        '''
#        self.Value = [WebKitCtrl._Msg.WEBKIT_GET_CEFBROWSER]
#        return self.Value
    
class OPWebKitCtrl(Control):
    '''
    IGFOPWebKitCtrl 跨进程WebKit控件
    OPWebKitCtrl不再使用，请使用qqlib.qqcontrols.WebKit
    '''
    #12/11/13    rayechen     创建
    #14/02/22 aaronlai    统一使用webkit控件
    def __init__(self, root=None, locator=None):
        raise Exception("OPWebKitCtrl不再使用，请使用qqlib.qqcontrols.WebKit") 
    
#    class _Msg(object):
#        '''IGFOPWebKitCtrl消息定义
#        '''
#        OPWEBKIT_GET_RENDERPID_CLIENTID=1    # 获取跨进程WebKit对应的渲染进程ID和ClientID
#    
#    @property
#    def ProcessID(self):
#        ''' 渲染进程ID
#        
#        :returns: int
#        '''
#        self.Value = [OPWebKitCtrl._Msg.OPWEBKIT_GET_RENDERPID_CLIENTID]
#        return self.Value[0]
#    
#    @property
#    def ClientID(self):
#        ''' 渲染进程WebKit实例ID
#         
#        :returns: int
#        '''
#        self.Value = [OPWebKitCtrl._Msg.OPWEBKIT_GET_RENDERPID_CLIENTID]
#        return self.Value[1]

    
class PasswordBox(Control):
    '''
    PasswordBox 控件
    '''
    @property
    def PasswordLength(self):
        '''返回密码长度
        '''
        return self.Value
    
#    @property
#    def RealCtrl(self):
#        """获取密码框中的真控件
#        
#        :return: 返回wincontrols.Control
#        """
#        #2012/12/11 aaronlai    创建，临时方案
#        from qpath import QPath
#        parentHWnd = self.HWnd
#        parentCtrl = wincontrols.Control(root=parentHWnd)
#        realEdtCtrl = wincontrols.Control(locator=QPath("/ClassName='Edit'&&MaxDepth='3'"),
#                                          root=parentCtrl)
#        return realEdtCtrl
    
    def clear(self):
        '''清空密码
        '''
        #2011/02/18 aaronlai    有时清空一次会失败，加入retry
        #2012/12/11 aaronlai    修改为真控件设置焦点
        #2012/12/12 aaronlai    还是模拟鼠标点击吧，为啥跨进程SetFocus总是不稳定
        #2013/01/31 aaronlai    保证bringForeground成功，不再使用RealCtrl进行模拟点击。
        retry = 3
        import time
        while retry > 0:
            pwdlen = self.PasswordLength
            delkeys = "{BKSP}" * (pwdlen+2) #+2是第一个字母输入有时有错的workaround
            self.setFocus()
            Keyboard.inputKeys(delkeys)
            if self.PasswordLength == 0:
                break
            retry = retry - 1
            time.sleep(0.5)
        self.waitForValue('PasswordLength', 0)
    
    def _getPasswordLen(self, pwd):
        """获取密码的实际长度
        """
        #2011/01/27 aaronlai    created
        import re
        specialKeyList = ['{{}','{}}','{%}','{\^}','{\+}' ]
        pwdLen = len(pwd)
        for pattern in specialKeyList:
            pwdLen = pwdLen - len(re.findall(pattern, pwd)) * 2
        return pwdLen
        
    def setPassword(self, pwd):
        '''设置密码
        '''
        #2011/01/25 aaronlai    针对密码有时会输错而进行尝试
        #2011/01/27 aaronlai    修改密码的实际长度
        #2011/02/24 aaronlai    如果多次输入密码错误，抛出异常
        #2012/04/12 rayechen    密码输入修改为使用keybd_event方式
        #2012/04/17 rayechen    密码输入修改回SendInput方式（keybd_event方式不支持汉字输入）
        #2012/10/31 aaronlai    修改设置窗口为前端的方式，但SwitchToThisWindow这个函数需要观察下效果
        #2012/12/11 aaronlai    修改设置窗口前端和设置焦点的方式，临时方案
        #2012/12/12 aaronlai    临时方案：还是模拟鼠标点击吧，为啥跨进程SetFocus总是不稳定
        #2013/01/31 aaronlai    保证bringForeground成功，不再使用RealCtrl进行模拟点击。
        #                       见单：http://tapd.oa.com/v3/10028971/bugtrace/bugs/view?bug_id=1010028971009665807
        #                             http://tapd.oa.com/v3/10028971/bugtrace/bugs/view?bug_id=1010028971009599285
        retry = 3
        import time
        pwdLen = self._getPasswordLen(pwd)
        while retry > 0:
            self.GFWindow.Window.bringForeground()
#            wincontrols.Window(root=self.HWnd).bringForeground()
            self.clear()
            self.setFocus()
            Keyboard.inputKeys('a{BKSP}{BKSP}' + pwd, 0.1) #第一个字母不能输入的workaround
            time.sleep(0.5)
            if self.PasswordLength == pwdLen:
                return
            retry = retry - 1
            time.sleep(0.5)
        raise RuntimeError("密码输入尝试多次后仍错误!")
        

class RadioButton(Control):
    '''RadioButton控件
    '''
    @property
    def Checked(self):
        '''返回选中状态
        
        :rtype: bool
        '''
        return self.Value
    
    @Checked.setter
    def Checked(self, status):
        '''设置选中状态
        
        :type status: bool
        :param status: True为勾选，False为不勾选 
        '''
        self.Value = status

class _RichStaticExMsg(object):
    RSE_GETITEMCOUNT = 1
    RSE_GETITEMTYPE = 2
    RSE_GETITEMTEXT = 3
    RSE_GETITEMRECT = 4
    
class RichStaticItem(object):
    """RichStatic子项
    """
    class EnumItemType(object):
        """子项类型
        """
        IMAGE = 0
        TEXT = 1
        LINK = 2
        
    def __init__(self, rs, index):
        self._rs = rs
        self._itemIndex = index
        
    @property
    def Text(self):        
        """显示的文本，如果是Image,则是图片文件名
        """
        #11/03/02 allenpan    编码为utf8
        self._rs.Value = [_RichStaticExMsg.RSE_GETITEMTEXT, self._itemIndex]
        txt =  self._rs.Value
        if txt is not None:
            txt = txt.encode('utf8')
        return txt
    
    @property
    def BoundingRect(self):
        """item 区域
        """
        self._rs.Value = [_RichStaticExMsg.RSE_GETITEMRECT, self._itemIndex]
        return util.Rectangle(self._rs.Value)
    
    @property
    def ItemType(self):
        """item 类型
        
        :rtype: RichStaticItem.EnumItemType
        """
        self._rs.Value = [_RichStaticExMsg.RSE_GETITEMTYPE, self._itemIndex]
        return self._rs.Value
    
    def click(self, mouseFlag=MouseFlag.LeftButton, 
                    clickType=MouseClickType.SingleClick):
        """点击控件
        
        :type mouseFlag: tuia.mouse.MouseFlag
        :param mouseFlag: 鼠标按钮
        :type clickType: tuia.mouse.MouseClickType 
        :param clickType: 鼠标动作
        """
        #2011/03/01 aaronlai    created
        if not self.BoundingRect:
            raise RuntimeError("BoundingRect为空！")
        x, y = self.BoundingRect.Center.All
        Mouse.sendClick(self._rs.HWnd, x, y, mouseFlag, clickType)
        
class RichStatic(Control):
    """RichStatic控件
    """
    #2011/02/28 aaronlai    去除Text
    @property
    def ItemCount(self):
        """获取子项个数
        """
        self.Value = [_RichStaticExMsg.RSE_GETITEMCOUNT]
        return self.Value
        
    @property
    def Items(self):
        """返回RichStaticItem的子项列表
        """
        items = []
        n = self.ItemCount
        for i in range(n):
            items.append(RichStaticItem(self, i))
        return items
    
    def __getitem__(self, key):
        """根据key返回对应的RichStaticItem
        
        :type key: String or int 
        :param key: 索引或文字
        """
        #11/02/23 allenpan    decode key
        #11/03/02 allenpan    remove decode key
        
        if isinstance(key, int):
            cnt = len(self.Items)
            if key >= cnt:
                raise IndexError("key超出下标范围!")
            return self.Items[key]
        if isinstance(key, basestring):
            for item in self.Items:
                if item.Text == key:
                    return item
            raise IndexError("没有找到<%s>链接" %key)
    
class _ScrollBarMsg(object):
    '''GFScrollBar消息定义
    '''
    #2013/01/04 aaronlai    增加消息Id-设置滚动条的位置
    
    GSB_GETMINPOS=1     #获取最小滚动位置
    GSB_GETMAXPOS=2     #获取最大滚动位置
    GSB_GETPAGEPOS=3    #获取每页大小
    GSB_GETSTYLE=4      #获取滚动类型（水平or垂直）
    GSB_GETCURPOS=5     #获取当前滚动位置
    GSB_GETSTEPSIZE=6   #获取滚动步长
    GSB_SETSCROLLPOS=7  #设置滚动条的位置
    
class ScrollBar(Control):
    VERTICAL_SCROLLBAR = 1 # 垂直滚动条
    HORIZONTAL_SCROLLBAR = 2 # 水平滚动条
    """滚动条
    """
    #2013/01/16 aaronlai    去掉MaxPos、MiniPos、StepSize和PageSize属性
    @property
    def Style(self):
        """水平 or 垂直
        
        :rtype: int
        :return: ScrollBar.VERTICAL_SCROLLBAR or ScrollBar.HORIZONTAL_SCROLLBAR
        """
        self.Value = [_ScrollBarMsg.GSB_GETSTYLE]
        return self.Value
    
    @property
    def Position(self):
        """当前滚动位置
        
        :rtype: float
        :return: 返回当前位置，值区间为[0,1]
                 0 - 代表当前滚动位置为最左端（垂直滚动条为最顶端）
                 1 - 代表当前滚动位置为最右端（垂直滚动条为最底端）
        """
        #2013/01/16 aaronlai    修改返回的值
        self.Value = [_ScrollBarMsg.GSB_GETCURPOS]
        value = self.Value
        if value is not None:
            self.Value = [_ScrollBarMsg.GSB_GETMINPOS]
            minPos = self.Value
            self.Value = [_ScrollBarMsg.GSB_GETMAXPOS]
            maxPos = self.Value
            self.Value = [_ScrollBarMsg.GSB_GETPAGEPOS]
            pageSize = self.Value
            return ((value - minPos) * 1.0) / (maxPos - minPos - pageSize)
        return None 
    
    @Position.setter
    def Position(self, pos):
        """设置滚动条位置
        
        :type pos: float
        :param pos: 预设置的滚动条的位置，值区间为[0,1]
                    0 - 代表当前滚动位置为最左端（垂直滚动条为最顶端）
                    1 - 代表当前滚动位置为最右端（垂直滚动条为最底端）
        """
        #2013/01/16 aaronlai    创建
        if pos >= 0.0 and pos <= 1.0:
            self.Value = [_ScrollBarMsg.GSB_GETMINPOS]
            minPos = self.Value
            self.Value = [_ScrollBarMsg.GSB_GETMAXPOS]
            maxPos = self.Value
            self.Value = [_ScrollBarMsg.GSB_GETPAGEPOS]
            pageSize = self.Value
            
            abs_pos = int(minPos + pos * (maxPos - minPos - pageSize))
            self.Value = [_ScrollBarMsg.GSB_SETSCROLLPOS, abs_pos]
        else:
            raise ValueError("传入的值不在滚动范围内!")
        
    def backward(self):
        """向左端（垂直滚动条为顶端）方向滚动一步
        
        :rtype: bool
        :return: 当不能再继续滚动时，返回False
        """
        #2012/03/06 aaronlai    修改click的实现
        #2012/04/18 aaronlai    取消offset的hardcode
        #2013/01/16 aaronlai    滚动前判断，返回滚动操作是否成功
        if self.Position == 0.0:
            return False
        if self.Style == ScrollBar.VERTICAL_SCROLLBAR:
            offset = self.BoundingRect.Width / 2
        else:
            offset = self.BoundingRect.Height / 2
        super(ScrollBar,self).click(xOffset=offset, yOffset=offset)
        return True

    def forward(self):
        """向右端（垂直滚动条为底端）方向滚动一步
        
        :rtype: bool
        :return: 当不能再继续滚动时，返回False
        """
        #2012/03/06 aaronlai    修改click的实现
        #2012/04/18 aaronlai    取消offset的hardcode
        #2013/01/16 aaronlai    滚动前判断，返回滚动操作是否成功
        if self.Position == 1.0:
            return False
        if self.Style == ScrollBar.VERTICAL_SCROLLBAR:
            offset = 0 - self.BoundingRect.Width / 2
        else:
            offset = 0 - self.BoundingRect.Height / 2
        super(ScrollBar,self).click(xOffset=offset, yOffset=offset)
        return True
    
class Slider(Control):
    '''
    Slider 控件
    '''
    #2011/09/19 rayechen 创建
    
    class _SliderMsg(object):
        '''GFSlider消息定义
        '''
        GSLD_GETFOREGROUND=1         #获取滑动条前景图片路径
        GSLD_GETDRAGBACKGROUND=2  #获取滑动条拖动条的背景图片路径
        GSLD_GETVERTICAL=3              #获取滑动条是否竖向
        GSLD_GETDRAGPOS=4              #获取滑动条拖动条的位置
        GSLD_GETPOS=5                     #获取滑动条位置
        GSLD_GETRANGE=6                  #获取滑动条总范围
        
    @property
    def Foreground(self):
        """滑动条(Slider)前景
        
        :rtype: str
        :return: 滑动条(Slider)前景图像路径
        """
        self.Value = [Slider._SliderMsg.GSLD_GETFOREGROUND]
        return self.Value
    
    @property
    def DragBackground(self):
        """拖动条背景
        
        :rtype: str
        :return: 拖动条背景图像路径
        """
        self.Value = [Slider._SliderMsg.GSLD_GETDRAGBACKGROUND]
        return self.Value
    
    @property
    def Vertical(self):
        """是否竖向
        
        :rtype: bool
        :return: 是否竖向滚动条
        """
        self.Value = [Slider._SliderMsg.GSLD_GETVERTICAL]
        return self.Value
    
    @property
    def DragPos(self):
        """拖动条的位置
        
        :rtype: int
        :return: 滚动条的位置
        """
        self.Value = [Slider._SliderMsg.GSLD_GETDRAGPOS]
        return self.Value
  
    @property
    def Pos(self):
        """滑动条(Slider)前景的位置
        
        :rtype: int
        :return: 滑动条(Slider)前景的位置
        """
        self.Value = [Slider._SliderMsg.GSLD_GETPOS]
        return self.Value
    
    @property
    def Range(self):
        """拖动条的范围
        
        :rtype: (int, int)
        :return: 拖动条的范围
        """
        self.Value = [Slider._SliderMsg.GSLD_GETRANGE]
        return self.Value
  
class TabButton(Control):
    '''
    TabButton 控件
    '''
    class EnumTabButtonState(object):
        """枚举TabButton状态
        """
        UNKNOWN = 0
        UNPUSHEDNORMAL = 1
        UNPUSHEDHIGHLIGHT = 2
        UNPUSHEDPUSHED = 3
        PUSHEDNORMAL = 4
        PUSHEDHIGHLIGHT = 5
        PUSHEDPUSHED = 6
        MAX = 255
        
    @property
    def State(self):
        """TabButton
        
        :rtype: TabButton.EnumTabButtonState
        """
        return self.Value
    
class _TextMsg(object):      
    """Text消息定义
    """
    REC_TESTMSG = 0
    REC_GETDEFAULTTEXT = 1
    REC_PUTTEXT = 2
    REC_GETREADONLY = 3
    
class TextBox(Control):
    '''
    TextBox控件
    '''
    @property 
    def Text(self):
        return super(TextBox,self).Text
    
    @Text.setter
    def Text(self, text):
        '''设置ComboBox文字
        '''
        #2011/02/16 aaronlai    指定编码
        #2011/03/04 aaronlai    修改实现
        if type(text) == types.UnicodeType:
            self.Value = [_TextMsg.REC_PUTTEXT, text]
        else:
            self.Value = [_TextMsg.REC_PUTTEXT, unicode(text,'utf8')]
            
    @property
    def DefaultText(self):
        """返回缺省文字(IAFRichEditCtrl)
        """
        #2011/03/04 aaronlai    created
        #2011/03/14 aaronlai    修改返回值的编码
        self.Value = [_TextMsg.REC_GETDEFAULTTEXT]
        text = self.Value
        if text != None:
            return text.encode('utf8')
        else:
            return ""
        
    @property
    def ReadOnly(self):
        """是否只读
        
        :rtype: bool
        """
        #2013/01/28 aaronlai    增加获取只读属性
        self.Value = [_TextMsg.REC_GETREADONLY]
        return self.Value
    
class _TreeItemMsg(object):
    TITEM2_ISEXPANDED = 1
    TITEM2_GETIMAGE = 2
    TITEM2_ISGRAY = 3
    TITEM2_SELECT = 4
    TITEM2_MULTISELECT = 5
    TITEM2_EXPAND = 6
    TITEM2_COLLAPSE = 7
    TITEM2_GETSTATE = 8
    TITEM2_GETITEMDATA_BUDDYFOLDERTREE = 9      #2012/06/20  rayechen  新增
 
class TreeViewItem(Control):
    """TreeView的子项
    """
    #2011/03/03 aaronlai    created
    @property
    def Expanded(self):
        """是否展开
        """
        self.Value = [_TreeItemMsg.TITEM2_ISEXPANDED]
        return self.Value
    
    def expand(self):
        """展开该子项
        """
        #2011/03/04 aaronlai    在expand前先select，否则有问题
        if not self.Expanded:
            self.select()
            self.Value = [_TreeItemMsg.TITEM2_EXPAND]
            return self.Value
    
    @property
    def Image(self):
        """获取子项的图片文件名
        """
        self.Value = [_TreeItemMsg.TITEM2_GETIMAGE]
        return self.Value
    
    @property
    def Selected(self):
        """是否被选中
        """
        self.Value = [_TreeItemMsg.TITEM2_GETSTATE]
        return ((self.Value & 4) > 0)
    
    @property
    def Items(self):
        """返回该子项直接孩子列表
        
        :rtype: list of TreeViewItem
        """
        items = []
        for item in self.Children:
            items.append(TreeViewItem(root=item))
        return items
    
    def select(self):
        """选中某子项
        """
        self.Value = [_TreeItemMsg.TITEM2_SELECT]
        return self.Value
    
    def multiSelect(self):
        """多选某子项
        """
        self.Value = [_TreeItemMsg.TITEM2_MULTISELECT]
        return self.Value
    
    def collapse(self):
        """折叠某子项
        """
        if self.Expanded:
            self.Value = [_TreeItemMsg.TITEM2_COLLAPSE]
            return self.Value
    
class TreeView(Control):
    """IGFTreeCtrl2/选择联系人模块的左边树形控件 or 消息管理器的左边树形控件
    """
    @property
    def Items(self):
        """
        
        :rtype: list
        :return: list of TreeViewItem
        """
        items = []
        for item in self.Children:
            itemType = item.Type
            if itemType and itemType.startswith("IGFTreeItem"):
                items.append(TreeViewItem(root=item))
        return items
    
class _GFWindowMsg(object):
        """
        """
        #12/03/12 rayechen   创建
        TGFWin_SMALLICON = 0;
        
class GFWindow(Control, control.ControlContainer):
    """GF窗口
    """
    #11/01/13 allenpan    添加waitForInvalid函数
    #11/01/13 allenpan    添加close函数
    #13/03/14 aaronlai    增加检查GFWindow下的控件是否支持IAccessible接口的功能
    _listeners = []
    def __init__(self, root=None, locator=None):
        '''Constructor。没有使用super
        '''
        Control.__init__(self, root=root, locator =locator)
        #self._winHandle = self.HWnd
        control.ControlContainer.__init__(self)
        locators = {
            '最小化按钮' : {'type':Button, 'root':self, 'locator':'minimizebutton'},
            '最大化按钮' : {'type':Button, 'root':self, 'locator':'maximizebutton'},
            '关闭按钮'   : {'type':Button, 'root':self, 'locator':'closebutton'}
        }
        self.updateLocator(locators)
        self._notifyListener()
        
    def _notifyListener(self, notifier=None):
        if len(self._listeners) > 0:
            if notifier is None:
                notifier = self
            for listener in self._listeners:
                listener.update(notifier)
        
    @staticmethod
    def addListener(listener):
        """添加监听者
        
        :type listener: qqlib.listener.BaseListener
        :param listener: 监听者
        """
        GFWindow._listeners.append(listener)
        
    @staticmethod
    def clearListener():
        """清空监听者
        
        """
        del GFWindow._listeners[:]
        GFWindow._listeners = []
        
    @property
    def Caption(self):
        """返回窗口标题
        """
        #11/02/11 aaronlai    新增属性
        return self.Window.Caption
    
    @property
    def SmallIcon(self):
        """返回标题栏小图标路径
        """
        #12/03/12 rayechen   创建
        self.Value = [_GFWindowMsg.TGFWin_SMALLICON];
        return self.Value;
    
    @property
    def Window(self):
        """返回wincontrols.Window
        """
        #11/02/16 aaronlai    修改参数
        return wincontrols.Window(root=self.HWnd)
    
    def close(self):
        '''关闭GF窗口
        '''
        #11/6/20 allenpan    加上消息同步
        #11/07/01 allenpan    当没有关闭按钮时（如Menu）用window的close
        #12/11/09 aaronlai    在点击关闭按钮前，需等待该按钮状态可点击，见bug单：9530948
        import tuia.util
        msg_syncer = tuia.util.MsgSyncer(self.HWnd)
        
        if self.hasControlKey('关闭按钮'):
            btn = self.Controls['关闭按钮']
            btn.waitForValue("Enabled", True)
            btn.click()
        else:
            self.Window.close()
        self.waitForInvalid()
        
        #窗口关闭的时候会有其他消息发给其他窗口，会造成诸如menu消失的问题。用一个同步来处理
        msg_syncer.wait()
    
    def waitForInvalid(self, timeout=10.0, interval=0.5):
        '''等待窗口失效
        
        :type timeout: float 
        :param timeout: 超时秒数
        '''
        #2011/11/21 aaronlai    当完成关闭窗口操作后出现对话框时，会导致失败
        if not self.exist():
            return
        try:
            if self.Valid == False: return
            self.Window._wait_for_disabled_or_invisible(timeout, interval)
#            self.Window.waitForInvalid(timeout)
        except pythoncom.com_error: #[allenpan]com对象调用失败，表示窗口已经被销毁
            pass
        
    def waitForInvisible(self, timeout=10.0):
        '''等待窗口消失
        
        :type timeout: float 
        :param timeout: 超时秒数
        '''
        #2011/02/22 aaronlai    created
        try:
            if self.Visible == False: return
            self.Window.waitForInvisible(timeout)
        except pythoncom.com_error: 
            pass
    
    @property
    def Valid(self):
        """窗口是否有效
        """
        #2011/02/16 aaronlai    覆盖基类的Valid属性
        return self.Window.Valid
    
    @property
    def Visible(self):
        """窗口是否可见
        """
        #2011/02/16 aaronlai    覆盖基类的Visible属性
        #2011/02/22 aaronlai    增加Valid属性的判断
        if not self.Valid:
            return False
        return self.Window.Visible
    
    @property
    def _DetouredTextItems(self):
        """获取截获的文本
        """

        if self._gfacc.detouredText is None:
            return None
        
        items = []
        sortList = []
        for item in self._gfacc.detouredText:
            rc = item[1:5]
            newItem = list(item)
            newItem[1] = self.BoundingRect.Left+rc[0]
            newItem[2] = self.BoundingRect.Top+rc[1]
            newItem[3] = self.BoundingRect.Left+rc[0]+rc[2]
            newItem[4] = self.BoundingRect.Top+rc[1]+rc[3]
            sortList.append((item[5],newItem))
        sortList.sort()
        for item in sortList:
            items.append(item[1])
        return items
    
class _MenuItemExMsg(object):
    GMI_GETSUBMENU = 1
    GMI_GETIMAGEPATH = 2
    GMI_GETCHECK = 3
    GMI_GET_DEL_IMAGEPATH = 4
    GMI_GET_DEL_HIGHLIGHT_IMAGEPATH = 5
    
class MenuItemDelButton(object):
    '''
    菜单项上的右侧删除按钮（非真GF按钮）类
    '''
    #12/03/16    rayechen    创建
    def __init__(self, menuItem):
        self._menuItem = menuItem
        
        # 注：以下值根据GF代码得来
        self._interval = 5     # 本删除按钮右侧到菜单项右侧的间隔
        self._width   = 12    # 本删除按钮宽度
        self._height  = 12    # 本删除按钮高度
        
    @property
    def ImagePath(self):
        '''返回正常图像路径
        '''
        self._menuItem.Value=[_MenuItemExMsg.GMI_GET_DEL_IMAGEPATH]
        return self._menuItem.Value
    
    @property
    def HighLightImagePath(self):
        '''返回高亮图像路径
        '''
        self._menuItem.Value=[_MenuItemExMsg.GMI_GET_DEL_HIGHLIGHT_IMAGEPATH]
        return self._menuItem.Value
    
    @property
    def BoundingRect(self):
        '''返回RECT(相对屏幕左上角)
        '''
        rcMenuItem = self._menuItem.BoundingRect

        # 使用大小位置信息与菜单项的BoundingRect信息进行计算
        right = rcMenuItem.Right - self._interval
        left = right - self._width
        top = rcMenuItem.Top + (rcMenuItem.Height - self._height)/2
        bottom = top + self._height
        return util.Rectangle((left, top, right, bottom))
    
    @property
    def Offset(self):
        # 计算相对于该菜单项左上角的偏移
        rcMenuItem = self._menuItem.BoundingRect
        delImageCenter = self.BoundingRect.Center
        x = delImageCenter.X - rcMenuItem.Left
        y = delImageCenter.Y - rcMenuItem.Top
        return (x, y)
    
    def hover(self):
        """悬停
        """
        x, y = self.Offset
        self._menuItem.hover(x, y)
        
    def click(self):
        """点击
        """
        x, y = self.Offset
        # 调用菜单项的click方法进行点击
        self._menuItem.click(xOffset = x, yOffset = y)
    
class MenuItem(Control):
    '''菜单项控件。不要直接实例化这个类，而通过Menu.MenuItems来获取。
    ''' 
    @property
    def Checked(self):
        """返回该子项是否被勾选
        """
        self.Value=[_MenuItemExMsg.GMI_GETCHECK]
        return self.Value
    
    @property
    def ImagePath(self):
        '''返回菜单项左边的图像路径
        '''
        self.Value=[_MenuItemExMsg.GMI_GETIMAGEPATH]
        return self.Value
    
    @property
    def DelBtn(self):
        '''返回删除按钮类
        '''
        return MenuItemDelButton(self)
    
    @property
    def SubMenu(self):
        """鼠标移动到该子项上，产生子菜单，并返回该子菜单
        
        :rtype: Menu
        """
        if not self.BoundingRect:
            raise RuntimeError("BoundingRect为空！")
        x, y = self.BoundingRect.Center.All
        Mouse.sendClick(self.HWnd, x, y)
#        self.click()
        self.Value=[_MenuItemExMsg.GMI_GETSUBMENU]
        menu = Menu(root=self.Value)
        menu.waitForValue('Visible', True)
        return menu
    
    def click(self, mouseFlag=MouseFlag.LeftButton, 
                    clickType=MouseClickType.SingleClick,
                    xOffset=None,
                    yOffset=None):
        """点击控件
        
        :type mouseFlag: tuia.mouse.MouseFlag
        :param mouseFlag: 鼠标按钮
        :type clickType: tuia.mouse.MouseClickType 
        :param clickType: 鼠标动作
        """
        #2011/02/22 aaronlai    创建
        #2011/02/24 aaronlai    修改实现
        #2011/04/27 allenpan    移动gfwin变量位置，避免异常
        #2011/10/13 jonliang    增加调试信息
        #2011/11/08 rayechen  去除等待菜单消失
        #2012/02/17 jonliang    增加offset参数
        try:
            super(MenuItem,self).click(mouseFlag, clickType, xOffset, yOffset)
        except:
            import testbase.logger as logger
            logger.info("isWindow: %d"%win32gui.IsWindow(self.HWnd))
            raise
            
class Menu(GFWindow):
    '''
            菜单控件
    '''
    
    class _LazyTXMenuWindow(object):
        pass
    
    #2011/02/22 aaronlai    继承GFWindow
    def __init__(self, root=None, locator=None):
        '''Constructor，当root和locator都是None时找到当前的唯一显示的菜单
        
        :param root: root控件
        :param locator: 定位参数 
        '''
        #2011/04/18 aaronlai    优化查找窗口的速度
        if root==None and locator==None:
            root = self._LazyTXMenuWindow()
        super(Menu, self).__init__(root, locator)
        
    def _init_gfacc_obj(self):
        '''初始化gf访问接口
        '''
        if isinstance(self._root, self._LazyTXMenuWindow):
            hwnd = Menu._timeout.retry(self.__findTXMenuWindow,(),(),lambda x: x != None)
            self._root = wincontrols.Control(root=hwnd)
        gfacc = super(Menu, self)._init_gfacc_obj()
        self.clearLocator()
        return gfacc
    
    def exist(self):
        '''控件存在性检查
        '''
        if isinstance(self._root, self._LazyTXMenuWindow):
            return self.__findTXMenuWindow() != None
        else:
            return super(Menu, self).exist()
        
    def __findTXMenuWindow(self):
        #2011/06/17 aaronlai    增加menu窗口的判断
        hwnds = []
        win32gui.EnumWindows(Menu.__enum_childwin_callback, hwnds)
        menuWnds = []
        for hwnd in hwnds:
            if 'TXMenuWindow' == wincontrols.Window(root=hwnd).Caption:
                menuWnds.append(hwnd)
        if not menuWnds:
            return None
        menuCount = len(menuWnds)
        if menuCount > 1:
            raise RuntimeError("找到%d个MenuWindow" % menuCount)
        return menuWnds[0]
    
    @staticmethod
    def closeAllMenuWindow():
        """关闭所有的menu窗口
        """
        #2011/06/23 aaronlai    创建
        hwnds = []
        win32gui.EnumWindows(Menu.__enum_childwin_callback, hwnds)
        for hwnd in hwnds:
            menuWnd = wincontrols.Window(root=hwnd)
            if 'TXMenuWindow' == menuWnd.Caption:
                menuWnd.close()
        
    @staticmethod
    def __enum_childwin_callback(hwnd, hwnds):
        if hwnd and win32gui.IsWindowVisible(hwnd):
            hwnds.append(hwnd)
    
    def __iter__(self):
        cnt = self._gfacc.childCount
        for i in range(cnt):
            yield MenuItem(self._gfacc.getChildByIndex(i))
            
    def __getitem__(self, key):
        '''根据key返回MenuItem
        
        :key: 菜单索引或菜单文字
        '''
        #2011/04/18 aaronlai    优化定位item的速度
        return self._getMenuItem(key)
#        if isinstance(key, int):
#            cnt = self._gfacc.childCount
#            if key >= cnt:
#                raise IndexError("key超出下标范围!")
#            return MenuItem(root=self._gfacc.getChildByIndex(key))
#        if isinstance(key, basestring):
#            for item in self:
#                if item.Text == key:
#                    return item
#            raise IndexError("cannot find menu item of text %s" %key)
       
    @property
    def MenuItems(self):
        '''获取MenuItem。通过MenuItems[菜单项索引]或MenuItems[菜单项文字]返回MenuItem实例。
        '''
        return self

    def _getMenuItem(self, key):
        """从接口获取menuitem，需较新的QQInject支持
        """
        #2011/04/15 aaronlai    创建
        #2011/04/18 aaronlai    修改
        #2011/05/17 aaronlai    加入timeout机制
        #2011/06/22 aaronlai    异常信息增加key信息
        #2011/06/28 aaronlai    IndexError中修改key的编码
        #2012/04/20 jonliang    str菜单项不存在时并不会抛IndexError异常
        MENU_GETITEM = 1
        self._timeout.retry(lambda: self._gfacc.childCount > 0, (), (), lambda x: x == True)
        
        if isinstance(key, int):
            cnt = self._gfacc.childCount
            if key >= cnt:
                raise IndexError("key(%d)超出下标范围!" % key)
        if isinstance(key, basestring):
            key = key.decode('utf8')
        
        self.Value = [MENU_GETITEM,key]
        gfacc = self.Value
        if gfacc:
            return MenuItem(root=gfacc)
        else:
            return None
    
    @staticmethod
    def forceAppear(menu_owner, flag):
        '''强制指定进程的Menu在失去焦点的情况下也不要消失
        
        :param menu_owner: 菜单的所有者，可以传入进程ID或者app实例
        :param flag: True的时候强制不消失，False时取消强制
        '''
        #2011/10/20 allenpan 创建
        #2013/03/29 jonliang 修改app参数名，支持传入进程ID或者app实例
        from app import App
        if isinstance(menu_owner, App):
            process_id = menu_owner.ProcessId
        elif isinstance(menu_owner, int):
            process_id = menu_owner
        else:
            raise TypeError("menu_owner参数请传入进程ID或者app实例.")
        menuhk = _tif.TestObjectMgr(process_id).queryObject('IGFMenuHook')
        
#        hummerhelper = _HummerHelper.getHummerHelperItf(qqapp.ProcessId)
#        menuhk = hummerhelper.QueryObject("IGFMenuHook")
        if flag == True:
            menuhk.blockActiveApp()
            menuhk.blockFocus()
        else:
            menuhk.revoke()
        
class BubbleTip(GFWindow):
    '''气泡GF控件
    '''
    #11/01/13 allenpan    创建此类
    #11/03/04 aaronlai    Text属性已实现
    #12/02/02 aaronlai    去除对caption的依赖
    def __init__(self):
        from tuia.qpath import QPath
        qp = QPath("/classname='TXGuiFoundation' && visible='True'/UIType='GF' && config='BubbleTip'")
        GFWindow.__init__(self, locator=qp)
    
#    @property
#    def Text(self):
#        '返回文字'
#        
#        return "BubbleTip的文字暂时还不能提供"


class Calendar(Control):
    '''日历控件
    '''
    #11/03/17 dadalin 创建
    
    @property
    def Date(self):
        '''获取选择的日期
        
        :rtype: datetime.date
        :return: 选择的日期
        '''
        dt = self.Value
        ls = dt.split('-')
        return datetime.date(int(ls[0]), int(ls[1]), int(ls[2]))

    @Date.setter
    def Date(self, dt):
        '''设置选择的日期
        
        :param dt:  datetime.date, 设置的日期
        '''
        sdt = str(dt.year)+'-'+str(dt.month)+'-'+str(dt.day)
        self.Value = sdt
        
class Flash(Control):
    '''Flash控件
    
    通过Text属性获取FLASH地址
    '''
    #11/03/18 dadalin 创建
    pass

class PwdEdit(Control):
    '''
    PwdEdit
    '''
    @property 
    def Text(self):
        return super(PwdEdit, self).Text
    
    @Text.setter
    def Text(self, text):
        '''设置密码
        '''
        #2015/05/13 pillarzou    新建

        if text == self.Text:
            return
        if type(text) == types.UnicodeType:
            self.Value = text
        else:
            self.Value = unicode(text,'utf8')
  
if __name__ == "__main__":
    pass