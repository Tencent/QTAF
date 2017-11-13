# -*- coding: UTF8 -*-
#
# Tencent is pleased to support the open source community by making QTA available.
# Copyright (C) 2016THL A29 Limited, a Tencent company. All rights reserved.
# Licensed under the BSD 3-Clause License (the "License"); you may not use this 
# file except in compliance with the License. You may obtain a copy of the License at
# 
# https://opensource.org/licenses/BSD-3-Clause
# 
# Unless required by applicable law or agreed to in writing, software distributed 
# under the License is distributed on an "AS IS" basis, WITHOUT WARRANTIES OR CONDITIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.
#
"""用于访问支持IAccessible接口的控件

"""
#2012/12/27 pear    创建
#2013/03/14 pear    使用InvokeTypes方法获取属性，将更具有兼容性

import win32com.client
import win32con
import win32gui
import ctypes
import comtypes
from comtypes.client import GetModule
GetModule('oleacc.dll') 
from comtypes.gen.Accessibility import IAccessible
from comtypes.automation import VARIANT

class EnumAccessibleObjectRole(object):
    '''Accessible Object的角色
    '''
    ROLE_SYSTEM_TITLEBAR = 0x1
    ROLE_SYSTEM_MENUBAR = 0x2
    ROLE_SYSTEM_SCROLLBAR = 0x3
    ROLE_SYSTEM_GRIP = 0x4
    ROLE_SYSTEM_SOUND = 0x5
    ROLE_SYSTEM_CURSOR = 0x6
    ROLE_SYSTEM_CARET = 0x7
    ROLE_SYSTEM_ALERT = 0x8
    ROLE_SYSTEM_WINDOW = 0x9
    ROLE_SYSTEM_CLIENT = 0xa
    ROLE_SYSTEM_MENUPOPUP = 0xb
    ROLE_SYSTEM_MENUITEM = 0xc
    ROLE_SYSTEM_TOOLTIP = 0xd
    ROLE_SYSTEM_APPLICATION = 0xe
    ROLE_SYSTEM_DOCUMENT = 0xf
    ROLE_SYSTEM_PANE = 0x10
    ROLE_SYSTEM_CHART = 0x11
    ROLE_SYSTEM_DIALOG = 0x12
    ROLE_SYSTEM_BORDER = 0x13
    ROLE_SYSTEM_GROUPING = 0x14
    ROLE_SYSTEM_SEPARATOR = 0x15
    ROLE_SYSTEM_TOOLBAR = 0x16
    ROLE_SYSTEM_STATUSBAR = 0x17
    ROLE_SYSTEM_TABLE = 0x18
    ROLE_SYSTEM_COLUMNHEADER = 0x19
    ROLE_SYSTEM_ROWHEADER = 0x1a
    ROLE_SYSTEM_COLUMN = 0x1b
    ROLE_SYSTEM_ROW = 0x1c
    ROLE_SYSTEM_CELL = 0x1d
    ROLE_SYSTEM_LINK = 0x1e
    ROLE_SYSTEM_HELPBALLOON = 0x1f
    ROLE_SYSTEM_CHARACTER = 0x20
    ROLE_SYSTEM_LIST = 0x21
    ROLE_SYSTEM_LISTITEM = 0x22
    ROLE_SYSTEM_OUTLINE = 0x23
    ROLE_SYSTEM_OUTLINEITEM = 0x24
    ROLE_SYSTEM_PAGETAB = 0x25
    ROLE_SYSTEM_PROPERTYPAGE = 0x26
    ROLE_SYSTEM_INDICATOR = 0x27
    ROLE_SYSTEM_GRAPHIC = 0x28
    ROLE_SYSTEM_STATICTEXT = 0x29
    ROLE_SYSTEM_TEXT = 0x2a
    ROLE_SYSTEM_PUSHBUTTON = 0x2b
    ROLE_SYSTEM_CHECKBUTTON = 0x2c
    ROLE_SYSTEM_RADIOBUTTON = 0x2d
    ROLE_SYSTEM_COMBOBOX = 0x2e
    ROLE_SYSTEM_DROPLIST = 0x2f
    ROLE_SYSTEM_PROGRESSBAR = 0x30
    ROLE_SYSTEM_DIAL = 0x31
    ROLE_SYSTEM_HOTKEYFIELD = 0x32
    ROLE_SYSTEM_SLIDER = 0x33
    ROLE_SYSTEM_SPINBUTTON = 0x34
    ROLE_SYSTEM_DIAGRAM = 0x35
    ROLE_SYSTEM_ANIMATION = 0x36
    ROLE_SYSTEM_EQUATION = 0x37
    ROLE_SYSTEM_BUTTONDROPDOWN = 0x38
    ROLE_SYSTEM_BUTTONMENU = 0x39
    ROLE_SYSTEM_BUTTONDROPDOWNGRID = 0x3a
    ROLE_SYSTEM_WHITESPACE = 0x3b
    ROLE_SYSTEM_PAGETABLIST = 0x3c
    ROLE_SYSTEM_CLOCK = 0x3d
    ROLE_SYSTEM_SPLITBUTTON = 0x3e
    ROLE_SYSTEM_IPADDRESS = 0x3f
    ROLE_SYSTEM_OUTLINEBUTTON = 0x40

class EnumAccessibleObjectState(object):
    '''Accessible Object的状态
           
    '''
    STATE_SYSTEM_UNAVAILABLE = 0x00000001  # Disabled
    STATE_SYSTEM_SELECTED = 0x00000002
    STATE_SYSTEM_FOCUSED = 0x00000004
    STATE_SYSTEM_PRESSED = 0x00000008
    STATE_SYSTEM_CHECKED = 0x00000010
    STATE_SYSTEM_MIXED = 0x00000020  # 3-state checkbox or toolbar button
    STATE_SYSTEM_INDETERMINATE = STATE_SYSTEM_MIXED
    STATE_SYSTEM_READONLY = 0x00000040
    STATE_SYSTEM_HOTTRACKED = 0x00000080
    STATE_SYSTEM_DEFAULT = 0x00000100
    STATE_SYSTEM_EXPANDED = 0x00000200
    STATE_SYSTEM_COLLAPSED = 0x00000400
    STATE_SYSTEM_BUSY = 0x00000800
    STATE_SYSTEM_FLOATING = 0x00001000  # Children "owned" not "contained" by parent
    STATE_SYSTEM_MARQUEED = 0x00002000
    STATE_SYSTEM_ANIMATED = 0x00004000
    STATE_SYSTEM_INVISIBLE = 0x00008000
    STATE_SYSTEM_OFFSCREEN = 0x00010000
    STATE_SYSTEM_SIZEABLE = 0x00020000
    STATE_SYSTEM_MOVEABLE = 0x00040000
    STATE_SYSTEM_SELFVOICING = 0x00080000
    STATE_SYSTEM_FOCUSABLE = 0x00100000
    STATE_SYSTEM_SELECTABLE = 0x00200000
    STATE_SYSTEM_LINKED = 0x00400000
    STATE_SYSTEM_TRAVERSED = 0x00800000
    STATE_SYSTEM_MULTISELECTABLE = 0x01000000  # Supports multiple selection
    STATE_SYSTEM_EXTSELECTABLE = 0x02000000  # Supports extended selection
    STATE_SYSTEM_ALERT_LOW = 0x04000000  # This information is of low priority
    STATE_SYSTEM_HASSUBMENU = STATE_SYSTEM_ALERT_LOW
    STATE_SYSTEM_ALERT_MEDIUM = 0x08000000  # This information is of medium priority
    STATE_SYSTEM_ALERT_HIGH = 0x10000000  # This information is of high priority
    STATE_SYSTEM_PROTECTED = 0x20000000  # access to this is restricted
    STATE_SYSTEM_VALID = 0x3FFFFFFF
    STATE_SYSTEM_HASPOPUP = 0x40000000

class _AccessibleObjectWrapper_win32com(object):
    """使用win32com模块实现IAccessible接口的包裹类
    
    """
    #2013/11/12 pear    新增
    def __init__(self, acc_disp):
        self._acc_disp = acc_disp
        self._childID = win32con.CHILDID_SELF

    @property
    def accFocus(self):
        child = self._acc_disp._oleobj_.InvokeTypes(-5011, 0, 2, (12, 0), ())
        if isinstance(child, int) or isinstance(child, long):
            return child
        elif isinstance(child, win32com.client.DispatchBaseClass):
            return _AccessibleObjectWrapper_win32com(child)
        else:
            return None
        
    @property
    def accName(self):
        name = self._acc_disp._oleobj_.InvokeTypes(-5003, 0, 2, (8, 0), ((12, 17),), self._childID)
        if name:
            return name.encode('utf8')
        return None
        
    @property
    def accRole(self):
        return self._acc_disp._oleobj_.InvokeTypes(-5006, 0, 2, (12, 0), ((12, 17),), self._childID)
        
    @property
    def accDescription(self):
        desc = self._acc_disp._oleobj_.InvokeTypes(-5005, 0, 2, (8, 0), ((12, 17),), self._childID)
        if desc:
            return desc.encode('utf8')
        return None
        
    @property
    def accState(self):
        return self._acc_disp._oleobj_.InvokeTypes(-5007, 0, 2, (12, 0), ((12, 17),), self._childID)
    
    @property
    def accValue(self):
        val = self._acc_disp._oleobj_.InvokeTypes(-5004, 0, 2, (8, 0), ((12, 17),), self._childID)
        if val:
            return val.encode('utf8')
        return None
    
    @property
    def accParent(self):
        ret = self._acc_disp._oleobj_.InvokeTypes(-5000, 
                                                  0, 
                                                  2, 
                                                  (9, 0), 
                                                  ())
        if ret is not None:
            ret = _AccessibleObjectWrapper_win32com(win32com.client.Dispatch(ret, u'accParent', None))
        return ret
    
class _AccessibleObjectWrapper_comtypes(object):
    """使用comtypes模块实现IAccessible接口的包裹类
    
    """
    #2013/11/12 pear    新增
    def __init__(self, acc_disp):
        """Constructor
        :type acc_disp: comtypes.gen.Accessibility.IAccessible or
                        int( for window handle) or
                        tuple((x,y), for location point )
        :param acc_disp: acc_disp指定类型的实例
        :raise: TypeError
        """
        if isinstance(acc_disp, int):
            self._acc_disp = self._accessible_object_from_window(acc_disp)
        elif isinstance(acc_disp, tuple):
            self._acc_disp = self._accessible_object_from_point(acc_disp)
        elif isinstance(acc_disp, IAccessible):
            self._acc_disp = acc_disp
        else:
            raise TypeError("acc_disp must be ctypes.POINTER(IAccessible) or int or tuple")
        
        self._childID = win32con.CHILDID_SELF

    def _accessible_object_from_window(self, hwnd):
        """返回句柄指定的AccessibleObject
        
        :type hwnd: int
        :param hwnd: 句柄
        :raises: ValueError
        :rtype: comtypes.gen.Accessibility.IAccessible
        """
        if not win32gui.IsWindow(hwnd):
            raise ValueError("window(%s) is not valid!" % hwnd)
        
        OBJID_WINDOW = 0
        OBJID_CLIENT = -4
        if (win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE) & win32con.WS_CHILDWINDOW) > 0:
            objID = OBJID_CLIENT
        else:
            objID = OBJID_WINDOW
        accObj = ctypes.POINTER(IAccessible)()
        ctypes.oledll.oleacc.AccessibleObjectFromWindow(hwnd, 
                                                        objID,
                                                        ctypes.byref(IAccessible._iid_), 
                                                        ctypes.byref(accObj))
        return accObj
    
    def _accessible_object_from_point(self, pt):
        """返回坐标对应的AccessibleObject
        
        :type pt: tuple
        :param pt: (x,y)，相对于桌面的坐标
        :raises: ValueError
        :rtype: comtypes.gen.Accessibility.IAccessible
        """
        accObj = ctypes.POINTER(IAccessible)()
        varChild = VARIANT()
        
        x,y = pt
        hr = ctypes.oledll.oleacc.AccessibleObjectFromPoint( ctypes.wintypes.POINT(x,y),
                                                        ctypes.byref(accObj),
                                                        ctypes.byref(varChild))
        if hr != 0 or varChild.value is None:
            raise ValueError("Can not fetch Accessible Object from point(%s,%s)" % (x,y))
        
        if varChild.value == win32con.CHILDID_SELF:
            return accObj
        else:
            return accObj.accChild(varChild)
        
    @property
    def accFocus(self):
        child = self._acc_disp.accFocus
        
        if isinstance(child, int) or isinstance(child, long):
            return child
        elif isinstance(child, IAccessible):
            return _AccessibleObjectWrapper_comtypes(child.QueryInterface(IAccessible))
        else:
            return None
        
    @property
    def accName(self):
        try:
            name = self._acc_disp.accName(self._childID)
            if name:
                return name.encode('utf8')
            return None
        except comtypes.COMError:
            return None
        
    @property
    def accRole(self):
        try:
            return self._acc_disp.accRole(self._childID)
        except comtypes.COMError:
            return None
        
        return self._acc_disp.accRole(self._childID)
        
    @property
    def accDescription(self):
        try:
            desc = self._acc_disp.accDescription(self._childID)
            if desc:
                return desc.encode('utf8')
            return None
        except comtypes.COMError:
            return None
        
    @property
    def accState(self):
        return self._acc_disp.accState(self._childID)
    
    @property
    def accValue(self):
        try:
            val = self._acc_disp.accValue(self._childID)
            if val:
                return val.encode('utf8')
            return None
        except comtypes.COMError:
            return None
        
    @property
    def accParent(self):
        ret = self._acc_disp.accParent
        if ret:
            return _AccessibleObjectWrapper_comtypes(ret.QueryInterface(IAccessible))
        return ret
    
class AccessibleObject(object):
    """支持IAccessible接口的对象（控件）的包裹类
    
    """
    #===========================================================================
    #从GF控件中获取出来的AccessibleObject是pyidispatch，是pythoncom中定义的对象类型，
    #而win32控件和web控件的AccessibleObject都是使用了ctypes模块调用系统api函数得到的对象，
    #它的类型是ctypes.Struct。ctypes模块可以使用pythoncom(26).dll的导出函数PyObjectFromIUnknown
    #将IAccessible（ctypes.Struct类型）转换为PyIDispatch类型实例，但转换后的实例在调用IAccessible接口
    #方法时，在某些对象下（更多体现在web元素）时会抛出异常，而ctypes.Struct类型实例则正常调用。
    #故无法统一使用pythoncom方式，只能采用了两种模块来封装IAccessible接口。
    #===========================================================================
    def __init__(self, acc_disp):
        """ Constructor
        
        :type acc_disp: win32com.client.dynamic.CDispatch or
                        win32com.client.DispatchBaseClass or
                        comtypes.gen.Accessibility.IAccessible or
                        int( for window handle) or
                        tuple((x,y), for location point ) or
                        AccessibleObject
        :param acc_disp: acc_disp指定类型的实例
        :raise: TypeError
        """
        #2013/03/14 pear    修改类型判断
        #2013/11/12 pear    增加使用ctypes模块封装IAccessible，以支持win32和web类型的控件。
        if isinstance(acc_disp, win32com.client.dynamic.CDispatch) or\
           isinstance(acc_disp, win32com.client.DispatchBaseClass):
            self._acc_disp = _AccessibleObjectWrapper_win32com(acc_disp)
        elif isinstance(acc_disp, ctypes.c_void_p) or\
             isinstance(acc_disp, int) or\
             isinstance(acc_disp, tuple) :
            self._acc_disp = _AccessibleObjectWrapper_comtypes(acc_disp)
        elif isinstance(acc_disp, _AccessibleObjectWrapper_win32com) or\
             isinstance(acc_disp, _AccessibleObjectWrapper_comtypes):
            self._acc_disp = acc_disp
        elif isinstance(acc_disp, AccessibleObject):
            self._acc_disp = acc_disp._acc_disp
        else:
            raise TypeError("参数必须是以下类型：win32com.client.dynamic.CDispatch or \
                                          win32com.client.DispatchBaseClass or\
                                          comtypes.gen.Accessibility.IAccessible or\
                                          int(window handle) or\
                                          tuple((x,y)) or\
                                          AccessibleObject, but real type is %s" % type(acc_disp))
        

    @property
    def accFocus(self):
        """获取具有焦点的控件
        
        :rtype: int or AccessibleObject or None
        :return: 如果返回为0代表具有焦点的控件是其本身，
                                             返回类型为整数，则代表其获得焦点的子控件的控件ID；
                                             返回类型为AccessibleObject，则代表其获得焦点的子控件实例；
                                             返回为None，代表未实现此接口。  
        """
        #2013/03/06 pear    修改实现
        #2013/03/14 pear    应QQ测试人员需要，先回滚回以前的代码，支持QQ1.90sp3的冒烟测试，待下周一版本发布后再修改回来
        #2013/03/26 pear    返回正确的类型
        childFocus = self._acc_disp.accFocus
        if isinstance(childFocus, int) or isinstance(childFocus, long):
            return childFocus
        elif isinstance(childFocus, _AccessibleObjectWrapper_win32com) or\
             isinstance(childFocus, _AccessibleObjectWrapper_comtypes):
            return AccessibleObject(childFocus)
        else:
            return None 
        
    @property
    def accName(self):
        """获取名称
        
        :rtype: string
        """
        return self._acc_disp.accName
        
    @property
    def accRole(self):
        """获取角色
        
        :rtype: EnumAccessibleObjectRole
        """
        return self._acc_disp.accRole
        
    @property
    def accDescription(self):
        """获取描述
        
        :rtype: string
        """
        return self._acc_disp.accDescription
        
    @property
    def accState(self):
        """获取状态值
        
        :rtype: EnumAccessibleObjectState
        """
        return self._acc_disp.accState
    
    @property
    def accValue(self):
        """获取值
        
        :rtype: string
        """
        return self._acc_disp.accValue
    
    @property
    def accParent(self):
        """获取父控件
        
        :rtype: AccessibleObject
        """
        parent = self._acc_disp.accParent
        if parent:
            return AccessibleObject(parent)
        return parent
            
if __name__ == '__main__':
    pass
    