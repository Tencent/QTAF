# -*-  coding: UTF-8  -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
__modified__ = '2011.12.30'
__description__ = '3.x 仅用于辅助独立执行时对弹出提示框的支持(中文输入输出仅使用UTF-8字符编码)'
__version__ = 301
__author__ = 'tommyzhang(张勇军)'
# -*- -*- -*- -*- -*- -*-
import time
import locale
import win32ext
# -*-
RuntimeDefaultEncoding = 'UTF-8'
LocalCode, LocalEncoding = locale.getdefaultlocale()
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-


class __BaseWindow__:
    '''@desc: (辅助类)简易封装顶层Win32Window(仅限顶层窗口)'''
    
    Timeout = 5
    Timestep = 0.2
    
    def __init__(self, classname=None, windowtext=None, processid=None, index=1, timeout=Timeout, timestep=Timestep):
        '''
        @param: classname   <str>        win32 classname  (注意：支持正则表达式，特殊字符请注意)
                windowtext  <str>        win32 windowtext (注意：支持正则表达式，特殊字符请注意，例如Q+可以匹配Q+和QQ)
                processid   <int>        win32 进程ID - 辅助定位特定进程的子窗口
                index       <int>        按启动先后排序的下标，默认为1，起始值为1
                timeout     <int|float>  定位时的超时值
                timestep    <int|float>  定位轮询间隔时间值
        '''
        self.classname = classname
        self.windowtext = windowtext
        self.processid = processid
        self.index = index
        self.timeout = timeout
        self.timestep = timestep
        self.handle = None
        self.__locate__(self.timeout, self.timestep)
    
    def __locate__(self, timeout=Timeout, timestep=Timestep):
        begin = time.time()
        while (time.time() - begin <= timeout or timeout <= 0):
            handles = win32ext.Handle.get_top_windows(classname=self.classname, windowtext=self.windowtext, processid=self.processid)
            if self.index <= len(handles):
                self.handle = handles[self.index - 1]
                return True
            if timeout <= 0 : break
            time.sleep(timestep)
        return False
        #raise Exception('Win32Window not found')
    
    def exist(self):
        '''@desc: 是否存在'''
        try:
            if self.handle and win32ext.Handle.is_valid(self.handle):return True
            return self.__locate__(self.timeout, self.timestep)
        except:pass
        return False
    
    def active(self):
        '''@desc: 激活'''
        if self.exist():win32ext.Handle.active(self.handle);time.sleep(0.5)
    
    def close(self):
        '''@desc: 关闭'''
        if self.exist():win32ext.Handle.close(self.handle)
    
    def max(self):
        '''@desc: 最大化'''
        if self.exist():win32ext.Handle.set_style(self.handle, 1)
    
    def min(self):
        '''@desc: 最小化'''
        if self.exist():win32ext.Handle.set_style(self.handle, 2)
    
    def restore(self):
        '''@desc: 复位'''
        if self.exist():win32ext.Handle.set_style(self.handle, 7)
    
    def get_rect(self):
        '''
        @desc: 获取窗口的坐标以及高宽
        @return：<dict>
        '''
        if self.exist():
            left, top, right, bottom = win32ext.Handle.get_windowrect(self.handle)
            return {'left':left, 'top':top, 'right':right, 'bottom':bottom, 'width':right - left, 'height':bottom - top}
    
    def get_text(self):
        if self.exist():return win32ext.Handle.get_windowtext(self.handle)
    
    def set_text(self, text):
        if text != None : text = text.decode(RuntimeDefaultEncoding)
        if self.exist() : win32ext.Handle.set_windowtext(self.handle, text)
    
    def set_focus(self):
        if self.exist():win32ext.Handle.set_focus(self.handle)
    
    def click(self, x=None, y=None, key=0, dbl=False, locus=True):
        '''
        @desc: 鼠标点击，默认鼠标点击中央。
        @param: x     in<int>  X坐标(相对窗口)
                y     in<int>  Y坐标(相对窗口)
                key   in<int>  默认 = Left = 0; Right = 1; Middle = 2
                dbl   in<bool> 是否双击
                locus in<bool> 启动轨迹
        '''
        if self.exist():
            self.active()
            left, top, right, bottom = win32ext.Handle.get_windowrect(self.handle)
            x, y = left + (right - left) / 2, top + (bottom - top) / 2
            win32ext.Mouse.evt_click(pos=(x, y), locus=locus, key=key, dbl=dbl)

# -*- -*- -*- -*- -*- -*-

class __BaseTipWindow__(__BaseWindow__):
    
    Timeout = 5
    Timestep = 0.2
    
    def __init__(self, classname=None, windowtext=None, processid=None, index=1, timeout=Timeout, timestep=Timestep):
        __BaseWindow__.__init__(self, classname, windowtext, processid, index, timeout, timestep)
        self.handle_btnok = None
        self.handle_btncancel = None
        self.handle_tip = None
        self.handle_message = None
        self.handle_edit = None
        self.handle_icon = None
        self.__locate_childs__()
    
    def __locate_childs__(self):
        self.childs = win32ext.Handle.get_childs(self.handle)
        for handle in self.childs:
            classname = win32ext.Handle.get_classname(handle)
            windowtext = win32ext.Handle.get_windowtext(handle)
            if 'Button' == classname and ('确定' == windowtext or 'ok' == windowtext):
                self.handle_btnok = handle
            if 'Button' == classname and ('取消' == windowtext or 'cancel' == windowtext):
                self.handle_btncancel = handle
            if 'Static' == classname and '脚本提示:' == windowtext:
                self.handle_tip = handle
            if 'Static' == classname and len(windowtext) > 0:
                self.handle_message = handle
            if 'Edit' == classname:
                self.handle_edit = handle
            if 'Static' == classname and '' == windowtext:
                self.handle_icon = handle


# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-


class IEAlert(__BaseTipWindow__):
    '''@desc: (辅助类)对应alert弹出的提示框，请使用HtmlWindow.get_alert_window获取。'''
    
    Timeout = 5
    Timestep = 0.2
    
    def __init__(self, processid=None, index=1, timeout=Timeout, timestep=Timestep):
        '''
        @param: processid   <int>        win32 进程ID - 辅助定位特定进程的子窗口
                index       <int>        按启动先后排序的下标，默认为1，起始值为1
                timeout     <int|float>  定位时的超时值
                timestep    <int|float>  定位轮询间隔时间值
        '''
        self.classname = '#32770'.decode(RuntimeDefaultEncoding)
        self.windowtext = '^来自网页的消息$'.decode(RuntimeDefaultEncoding)
        self.processid = processid
        self.index = index
        self.timeout = timeout
        self.timestep = timestep
        __BaseTipWindow__.__init__(self, self.classname, self.windowtext, self.processid, self.index, self.timeout, self.timestep)
    
    def get_msg(self):
        '''@desc: 获取文本信息'''
        if self.exist() and self.handle_message:
            return win32ext.Handle.get_windowtext(self.handle_message).encode(RuntimeDefaultEncoding)
    
    def click_ok(self):
        '''@desc: 点击确定按钮'''
        if self.exist() and self.handle_btnok:
            self.active()
            left, top, right, bottom = win32ext.Handle.get_windowrect(self.handle_btnok)
            x, y = left + (right - left) / 2, top + (bottom - top) / 2
            win32ext.Mouse.evt_click(pos=(x, y), locus=True, key=0, dbl=False)

# -*- -*- -*- -*- -*- -*-

class IEConfirm(__BaseTipWindow__):
    '''@desc: (辅助类)对应confirm弹出的提示框，请使用HtmlWindow.get_confirm_window获取。'''
    
    Timeout = 5
    Timestep = 0.2
    
    def __init__(self, processid=None, index=1, timeout=Timeout, timestep=Timestep):
        self.classname = '#32770'.decode(RuntimeDefaultEncoding)
        self.windowtext = '^来自网页的消息$'.decode(RuntimeDefaultEncoding)
        self.processid = processid
        self.index = index
        self.timeout = timeout
        self.timestep = timestep
        __BaseTipWindow__.__init__(self, self.classname, self.windowtext, self.processid, self.index, self.timeout, self.timestep)
    
    def get_msg(self):
        '''@desc: 获取文本信息'''
        if self.exist() and self.handle_message:
            return win32ext.Handle.get_windowtext(self.handle_message).encode(RuntimeDefaultEncoding)
    
    def click_ok(self):
        '''@desc: 点击确定按钮'''
        if self.exist() and self.handle_btnok:
            self.active()
            left, top, right, bottom = win32ext.Handle.get_windowrect(self.handle_btnok)
            x, y = left + (right - left) / 2, top + (bottom - top) / 2
            win32ext.Mouse.evt_click(pos=(x, y), locus=True, key=0, dbl=False)
    
    def click_cancel(self):
        '''@desc: 点击取消按钮'''
        if self.exist() and self.handle_btncancel:
            self.active()
            left, top, right, bottom = win32ext.Handle.get_windowrect(self.handle_btncancel)
            x, y = left + (right - left) / 2, top + (bottom - top) / 2
            win32ext.Mouse.evt_click(pos=(x, y), locus=True, key=0, dbl=False)

# -*- -*- -*- -*- -*- -*-

class IEPrompt(__BaseTipWindow__):
    '''@desc: (辅助类)对应prompt弹出的提示框，请使用HtmlWindow.get_prompt_window获取'''
    
    Timeout = 5
    Timestep = 0.2
    
    def __init__(self, processid=None, index=1, timeout=Timeout, timestep=Timestep):
        self.classname = '#32770'.decode(RuntimeDefaultEncoding)
        self.windowtext = '^.+ 需要某些信息$|^Explorer 用户提示$'.decode(RuntimeDefaultEncoding)
        self.processid = processid
        self.index = index
        self.timeout = timeout
        self.timestep = timestep
        __BaseTipWindow__.__init__(self, self.classname, self.windowtext, self.processid, self.index, self.timeout, self.timestep)
    
    def get_msg(self):
        '''@desc: 获取文本信息'''
        if self.exist() and self.handle_message:
            return win32ext.Handle.get_windowtext(self.handle_message).encode(RuntimeDefaultEncoding)
    
    def click_ok(self):
        '''@desc: 点击确定按钮'''
        if self.exist() and self.handle_btnok:
            self.active()
            left, top, right, bottom = win32ext.Handle.get_windowrect(self.handle_btnok)
            x, y = left + (right - left) / 2, top + (bottom - top) / 2
            win32ext.Mouse.evt_click(pos=(x, y), locus=True, key=0, dbl=False)
    
    def click_cancel(self):
        '''@desc: 点击取消按钮'''
        if self.exist() and self.handle_btncancel:
            self.active()
            left, top, right, bottom = win32ext.Handle.get_windowrect(self.handle_btncancel)
            x, y = left + (right - left) / 2, top + (bottom - top) / 2
            win32ext.Mouse.evt_click(pos=(x, y), locus=True, key=0, dbl=False)
    
    def click_edit(self):
        '''@desc: 点击编辑框'''
        if self.exist() and self.handle_edit:
            self.active()
            left, top, right, bottom = win32ext.Handle.get_windowrect(self.handle_edit)
            x, y = left + (right - left) / 2, top + (bottom - top) / 2
            x, y = left + (right - left) / 2, top + (bottom - top) / 2
            win32ext.Mouse.evt_click(pos=(x, y), locus=True, key=0, dbl=False)
    
    def get_edit_text(self):
        '''@desc: 获取编辑框内的文本内容'''
        if self.exist() and self.handle_edit:
            return win32ext.Handle.get_windowtext(self.handle_edit).encode(RuntimeDefaultEncoding)
    
    def clean_edit_text(self):
        '''@desc: 清除编辑框内的文本内容'''
        if self.exist() and self.handle_edit:
            self.click_edit()
            win32ext.Handle.set_windowtext(self.handle_edit, '')
    
    def set_edit_text(self, text):
        '''@desc: 设置编辑框内的文本内容'''
        if self.exist() and self.handle_edit:
            self.clean_edit_text()
            win32ext.Handle.set_windowtext(self.handle_edit, text.decode(RuntimeDefaultEncoding))
