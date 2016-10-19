# -*- coding: utf-8 -*-
'''
QPlusApp进程各窗口基本控件
'''
#2012/04/30    rayechen    created

import tuia.control as control
import tuia.wincontrols as wincontrols
import util
import _tif
from mouse import Mouse, MouseFlag, MouseClickType

import types
import pythoncom

#===============================================================================
# 相关类定义
#===============================================================================
class _LongControlID(object):
    def __init__(self, longID):
        self._longID = longID
        
    @property
    def Str(self):
        return self._longID

#===============================================================================
# 控件类定义
#===============================================================================
class Control(control.Control):
    """基础控件类
    
    :type root: qpappcontrols.Control or wincontrols.Control
    :param root: 开始查找的QPApp控件或包含QPApp控件的win32control.Window；
    :type locator: qpath.QPath or 控件的名字(字符串类型) or qpappcontrols._LongControlID
    :param locator: 查询类的实例, 如果是None，则将root作为此窗口；或者是控件的名字；或者是控件的长ID。
    :attention: 参数root和locator不能同时为None
    """
    # 2012/04/30  rayechen  创建
    def __init__(self, root=None, locator=None):
        #2012/10/10   rayechen  因QPlusApp组件纳入tif管理，修改为使用IQPAppSvr接口
        if locator is None and root is None:
            raise RuntimeError("传入参数locator和root不能同时为None!")
        
        control.Control.__init__(self)
        
        # 若是在Windows控件下面查找
        if isinstance(root, wincontrols.Control):
            pid = root.ProcessId
            if not pid or not root.Valid: 
                raise RuntimeError("The root window is Not Valid or its process has Exited!" % pid)
        
        if isinstance(root, Control):
            self._qpappentry = root._qpappentry
            self._hwnd = root.HWnd
            self._longID = root._LongID  # 此处先赋值，之后根据locator或longID再改
        elif isinstance(root, wincontrols.Control):
            self._hwnd = root.HWnd
            
            import win32process
            pid = win32process.GetWindowThreadProcessId(self._hwnd)[1]        
            self._qpappentry = _tif.TestObjectMgr(pid).queryObject('IQPAppSvr')
            self._longID = '0'  # 此处先赋值，之后根据locator或longID再改
        
        if locator is not None:           
            if isinstance(locator, basestring):# 若locator是name
                # root必须是QPAppControl
                if isinstance(root, Control):
                    #self._longID = _find_by_name(self, locator)
                    if type(locator) != types.UnicodeType:
                        ucname = unicode(locator, 'utf8')
                    try:                 
                        self._longID = self._qpappentry.GetDescendantCtrlLongIDByName(self.HWnd, self._LongID, ucname)
                    except pythoncom.com_error:
                        raise control.ControlNotFoundError("没有找到Name属性值为%s的子控件"%locator)
                else:
                    raise RuntimeError("root type %s is not supported when locator is name" % type(root))
            elif isinstance(locator, _LongControlID): # 若locator是LongID（初始化自己的场景）
                self._longID = locator.Str
                return
            else:  # 若locator非字符串（默认为其是QPath对象）    
                try:
                    kwargs = {'root':root}
                    # 调用locator（QPath对象）的search方法在root下对locator中保存的条件进行匹配查找
                    foundctrls =  self._timeout.retry(locator.search, kwargs, (), self.__validCtrlNum)
                except util.TimeoutError, erro:
                    raise control.ControlNotFoundError("<%s>中的%s查找超时：%s" % (locator,locator.getErrorPath(), erro))
                
                nctrl = len(foundctrls)
                if (nctrl>1):
                    raise control.ControlAmbiguousError("<%s>找到%d个控件" % (locator, nctrl))
                
                self._qpappentry = foundctrls[0]._qpappentry
                self._hwnd = foundctrls[0]._hwnd
                self._longID = foundctrls[0]._longID
                
    def __validCtrlNum(self, ctrls):
        return (len(ctrls) > 0)
    
    @property
    def Children(self):
        cnt = self._qpappentry.GetCtrlChildrenNum(self._hwnd, self._longID)
        children = []
        try:
            # 返回本控件的一级子控件
            for i in range(cnt):
                subctrlLongID = self._qpappentry.GetSubCtrlLongIDByIndex(self._hwnd, self._longID, i)
                children.append(Control(root=self, locator=_LongControlID(subctrlLongID)))
        except pythoncom.com_error: #遇到com_error，可能是控件的子节点减少，直接退出即可
            pass
        return children
        
    @property
    def BoundingRect(self):
        """返回窗口大小
        
        :rtype: util.Rectangle
        :return: util.Rectangle实例，如果不能获取到GF控件的窗口大小，则返回None
        """
        rect = self._qpappentry.GetCtrlPropValue(self._hwnd, self._longID, "rect")
        if rect:
            import win32gui
            wndLeft, wndTop, _, _ = win32gui.GetWindowRect(self._hwnd)
            left = rect[0] + wndLeft
            top = rect[1] + wndTop
            right = rect[2] + wndLeft
            bottom = rect[3] + wndTop
            return util.Rectangle((left, top, right, bottom))
        return None
    
    @property
    def Name(self):
        name = self._qpappentry.GetCtrlPropValue(self._hwnd, self._longID, "name")
        if name != None:
            return name.encode('utf8')
        else:
            return ""
    
    @property
    def Text(self):
        text = self._qpappentry.GetCtrlPropValue(self._hwnd, self._longID, "text")
        if text != None:
            return text.encode('utf8')
        else:
            return ""
        
    @property
    def Visible(self):
        try:
            return not self._qpappentry.GetCtrlPropValue(self._hwnd, self._longID, "hidden")
        except AttributeError, pythoncom.com_error:
            return False
    
    @property
    def HWnd(self):
        return self._hwnd
    
    @property
    def Parent(self):
        parentLongID = self._qpappentry.GetParentLongID(self._hwnd, self._longID)
        if parentLongID == None or parentLongID == '':
            return None
        else:
            return Control(root=self, locator=_LongControlID(parentLongID))
    
    @property
    def _LongID(self):
        '''控件的唯一标识
        
        :attention: _LongID对于不同版本Q+可能会变更，因此请不要在代码中使用具体的_LongID值
        '''
        return self._longID
    
    @property 
    def ProcessId(self):
        return wincontrols.Control(root=self._hwnd).ProcessId
    
    @property
    def ThreadId(self):
        return wincontrols.Control(root=self._hwnd).ThreadId
    
    @property
    def ToolTip(self):
        tooltip = self._qpappentry.GetCtrlPropValue(self._hwnd, self._longID, "tipText")
        if tooltip != None:
            return tooltip.encode('utf8')
        else:
            return ""
    
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
        x, y = self._getClickXY(xOffset, yOffset)
        self.hover(xOffset, yOffset)
        Mouse.postClick(self._hwnd, x, y, mouseFlag, clickType)
        import tuia.util
        tuia.util.MsgSyncer(self._hwnd).wait()
        
    def hover(self, xOffset=None, yOffset=None):
        """鼠标悬停
        """        
        if not self.BoundingRect:
                raise RuntimeError("空间区域为空!")

        if xOffset != None and yOffset != None:
            x, y = self._getClickXY(xOffset, yOffset)
        else:
            x, y = self.BoundingRect.Center.All
        
        hwnd = self.HWnd

        Mouse.postMove(hwnd, x, y)
        import tuia.util
        tuia.util.MsgSyncer(hwnd).wait()
        
        #增加等待
        import time
        time.sleep(0.5)
    
    def getDescendantByName(self, name):
        '''根据名字获取某子孙控件
        '''
        return Control(root=self, locator=unicode(name))

class Button(Control):
    '''按钮
    '''
    # 2012/04/30  rayechen  创建
    @property
    def ImagePath(self):
        '''图像路径
        '''
        raise RuntimeError("Button暂不支持ImagePath属性，若有需求请尽快联系rayechen")
        imagePath = self._qpappentry.GetCtrlPropValue(self._hwnd, self._longID, "imagePath")
        if imagePath != None:
            return imagePath.encode('utf8')
        else:
            return ""
        
class PushButton(Button):
    '''可按按钮
    '''
    # 2012/04/30  rayechen  创建
    @property
    def PushState(self):
        '''按钮按下状态
        '''
        state = self._qpappentry.GetCtrlPropValue(self._hwnd, self._longID, "pushstate")
        return 0!=state
        
class ComboButton(Control):
    '''复合按钮
    '''
    # 2012/04/30  rayechen  创建
    @property
    def MainButton(self):
        '''主按钮
        '''
        subCtrlLongID = self._qpappentry.GetSubCtrlLongIDByIndex(self._hwnd, self._longID, 0)
        return Button(root = self, locator=_LongControlID(subCtrlLongID))
    
    @property
    def MenuButton(self):
        '''菜单按钮
        '''
        subCtrlLongID = self._qpappentry.GetSubCtrlLongIDByIndex(self._hwnd, self._longID, 1)
        return Button(root = self, locator=_LongControlID(subCtrlLongID))
    
    
class QPAppWindow(Control, control.ControlContainer):
    ''''窗口
    '''
    # 2012/04/30  rayechen  创建    
    def __init__(self, root=None, locator=None):
        '''Constructor。没有使用super
        '''
        Control.__init__(self, root=root, locator=locator)
        self._winHandle = self.HWnd
        control.ControlContainer.__init__(self)
        locators = {
            '最小化按钮' : {'type':Button, 'root':self, 'locator':'最小化'},
            '最大化按钮' : {'type':Button, 'root':self, 'locator':'最大化'},
            '关闭按钮'   : {'type':Button, 'root':self, 'locator':'关闭'},
            '全屏按钮'   : {'type':Button, 'root':self, 'locator':'全屏'}
        }
        self.updateLocator(locators)
    
    @property
    def Window(self):
        """返回wincontrols.Window对象
        """
        return wincontrols.Window(root=self._winHandle)
    
    def close(self):
        '''关闭窗口
        '''
        import tuia.util
        msg_syncer = tuia.util.MsgSyncer(self.HWnd)
        
        if self.hasControlKey('关闭按钮'):
            btn = self.Controls['关闭按钮']            
            btn.click()
        else:
            self.Window.close()
        self.waitForInvalid()
        
        #窗口关闭的时候会有其他消息发给其他窗口，会造成诸如menu消失的问题。用一个同步来处理
        msg_syncer.wait()
        
    def waitForInvalid(self, timeout=10.0):
        '''等待窗口失效
        
        :type timeout: float 
        :param timeout: 超时秒数
        '''
        try:
            if self.Window.Valid == False: return
            self.Window._wait_for_disabled_or_invisible(timeout)
#            self.Window.waitForInvalid(timeout)
        except pythoncom.com_error: #[allenpan]com对象调用失败，表示窗口已经被销毁
            pass
        
    def waitForInvisible(self, timeout=10.0):
        '''等待窗口消失
        
        :type timeout: float 
        :param timeout: 超时秒数
        '''
        try:
            if self.Window.Visible == False: return
            self.Window.waitForInvisible(timeout)
        except pythoncom.com_error: 
            pass

if __name__ == "__main__":
    pass
