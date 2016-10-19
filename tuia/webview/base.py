# -*- coding: UTF-8 -*-

'''PC端WebView基类
'''

# 2016/1/13 shadowyang 创建

from tuia.mouse import Mouse, MouseFlag, MouseClickType
from tuia.qpath import QPath

import win32gui, win32con

from qt4w.webview.webview import IWebView
from tuia.filedialog import FileDialog


class WebViewBase(IWebView):
    '''PC端WebView基类
    '''
    def __init__(self,window,webdriver,offscreen_win=None):
        self._window=window
        self._offscreen_win=offscreen_win
        self._webdriver=webdriver
        self._parent_wnd=win32gui.GetParent(self._window.HWnd)
        #如果获取的父窗口是空
        if self._parent_wnd==0:
            self._parent_wnd=self._window.HWnd
        self._browser_type='not defined'
        
    def __getattr__(self, attr):
        '''转发给WebDriver实现
        '''
        return getattr(self._webdriver, attr)
        
    @property
    def browser_type(self):
        return self._browser_type
    
    @browser_type.setter
    def browser_type(self,type_name):
        self._browser_type=type_name
    
    def _handle_result(self, result, frame_xpaths):
        '''处理执行JavaScript的结果
        
        :param result: 要处理的数据
        :type  result: string
        :param frame_xpaths: 执行js所在frame的xpath
        :type  frame_xpaths: list
        '''
        from qt4w.util import JavaScriptError
        if result[0] == 'S': return result[1:]
        elif result[0] == 'E':
            raise JavaScriptError(frame_xpaths, result[1:])
        else:
            raise ValueError('执行JavaScript返回结果错误：%r' % result)
    
    def _inner_click(self,flag,click_type,x_offset,y_offset,):
        self.activate()
        new_x,new_y=win32gui.ClientToScreen(self._window.HWnd,(int(x_offset),int(y_offset)))
        if self._offscreen_win:
            new_x+=self._window.BoundingRect.Left-self._offscreen_win.BoundingRect.Left
            new_y+=self._window.BoundingRect.Top-self._offscreen_win.BoundingRect.Top
        Mouse.click(new_x, new_y, flag, click_type)
        
    def click(self, x_offset, y_offset):        
        self._inner_click(MouseFlag.LeftButton,MouseClickType.SingleClick,x_offset, y_offset)
        
    def double_click(self, x_offset, y_offset):
        self._inner_click(MouseFlag.LeftButton,MouseClickType.DoubleClick,x_offset, y_offset)
    
    def right_click(self, x_offset, y_offset):
        self._inner_click(MouseFlag.RightButton,MouseClickType.SingleClick,x_offset, y_offset)
    
    def long_click(self, x_offset, y_offset, duration=1):
        raise NotImplementedError
        
    def hover(self, x_offset, y_offset):
        self.activate()
        new_x,new_y=win32gui.ClientToScreen(self._window.HWnd,(int(x_offset),int(y_offset)))
        if self._offscreen_win:
            new_x+=self._window.BoundingRect.Left-self._offscreen_win.BoundingRect.Left
            new_y+=self._window.BoundingRect.Top-self._offscreen_win.BoundingRect.Top
        Mouse.move(new_x,new_y)
    
    def scroll(self, backward=True):
        self._window.scroll(backward)
        
    def send_keys(self,keys):
        self._window.sendKeys(keys)
        
    def activate(self, is_true=True):
        '''激活当前窗口
        
        :param is_true: 是否激活，默认为True
        :type  is_true: bool
        '''
        win32gui.SetWindowPos(self._parent_wnd,win32con.HWND_TOPMOST,0,0,0,0,win32con.SWP_NOSIZE|win32con.SWP_NOMOVE)
    
    @property
    def rect(self):
        '''当前可见窗口的坐标信息
        '''
        return win32gui.GetClientRect(self._window.HWnd)
    
    def upload_file(self, file_path):
        file_dialog = UploadFileDialog(self._window.ProcessId)
        file_dialog.upload_file(file_path)

class UploadFileDialog(FileDialog):
    '''上传文件对话框，目前ie、chrome封装是一样的，故放在这里，后面如果有不同，
    '''
    def __init__(self, process_id):
        '''通过进程id查找文件窗口
        '''
        qp = QPath('|classname~="32770" && ProcessId="%s"'%process_id)
        super(UploadFileDialog, self).__init__(qp)
        import tuia.wincontrols as win32
        self.updateLocator({
            '文件名展示框' : { 'type':win32.Control, 'root':self, 
                        'locator':QPath('/ClassName="ComboBoxEx32" && Visible="True" /ClassName="ComboBox" && Visible="True"') },
            '文件名' : { 'type':win32.Control, 'root':'@文件名展示框', 'locator':QPath('/ClassName="Edit" && Visible="True"') },
            
            '打开按钮' : { 'type':win32.Control, 'root':self, 'locator':QPath('/ClassName="Button" && Text="打开(&O)"') }
        })
        
    def upload_file(self, file_path):
        '''上传文件
        '''
        self.Controls['文件名'].Text = file_path
        self.Controls['打开按钮'].click()