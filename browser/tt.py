# -*- coding: utf-8 -*-
'''
TT程序模块
'''
#10/12/01 aaronlai    created
#10/12/07 aaronlai    移动TagControl类定义到__init__.py文件中
#10/12/08 aaronlai    实现本模块各接口功能
#11/01/10 allenpan    重构此模块
#11/02/12 allenpan    基于浏览器窗口重构此模块

import win32api
import win32con

from tuia.app import App
import tuia.wincontrols as win32
from tuia.qpath import QPath 
from tuia.webcontrols import WebPage

class TTWindow(win32.Window):
    '''TT浏览器窗口
    '''
    
    def __init__(self):
        qp = QPath("/classname~='TTFrameWnd' && visible='True'")
        win32.Window.__init__(self, locator = qp)
    
    @property
    def Url(self):
        '''当前访问的网址
        '''
        qp = QPath("/ClassName='ComboBox' && MaxDepth='2' && Instance='0'/ClassName='Edit'")
        edit = win32.Control(locator=qp, root=self)
        return edit.Text 
    
    @property
    def WebPage(self):
        '''返回WebPage
        
        :rtype: WebPage
        :return: 返回TTWindow下的Html文档
        '''
        #12/11/19 andylfang   把htmlcontrols修改为webcontrols
        qp = QPath("/classname='TT_WebCtrl' && visible='True'/maxdepth='3' && classname='Internet Explorer_Server'")
        ie_embed_wnd = win32.Window(locator=qp)
        return WebPage(ie_embed_wnd)
        
    
class TTApp(App):
    '''TT 浏览器应用程序
    '''
    
    def __init__(self):
        '''构造函数，找到当前的TT浏览器
        '''
        self._ttwnd = TTWindow()
        App.__init__(self)
    
    @property
    def Url(self):
        '''返回浏览器当前浏览的网址
        '''
        return self._ttwnd.Url 
    
    @staticmethod
    def getInstallDir():
        '''获取安装路径，如未安装TT返回None
        '''
        import pywintypes
        try:
            hkey = win32con.HKEY_LOCAL_MACHINE
            subkey = r'SOFTWARE\Tencent\TTraveler'
            hkey = win32api.RegOpenKey(hkey, subkey)
            dir = win32api.RegQueryValueEx(hkey, 'Install')[0]
            win32api.RegCloseKey(hkey)
            return dir
        except pywintypes.error:
            return None
    
#    @staticmethod
#    def killAll():
#        'kill掉所有TT进程'
#        import os
#        os.popen('taskkill /IM TTraveler.exe /F')
        
    def quit(self):
        '''退出TT
        
        由于TT没有正确响应WM_ENDSESSION消息，所以直接kill掉进程
        '''
        import os
        os.popen('taskkill /IM TTraveler.exe /F')
        App.quit(self)
    
    def waitForReady(self, timeout=10):
        '''等待页面完成
        '''
        #12/11/19 andylfang   把htmlcontrols修改为webcontrols
        self._ttwnd.WebPage.waitForReady(timeout)
        #self._ttwnd.HtmlDocument.waitForValue('State', html.HtmlDocument.EnumPageState.COMPLETE, timeout, 0.5)
        
if __name__ == "__main__": 
    tt = TTApp()
    tt.waitForReady()
    
    