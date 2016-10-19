# -*- coding: utf-8 -*-
'''
IE模块
'''
#10/12/01 aaronlai    created
#10/12/02 aaronlai    实现IEApp的MainWindow属性、Version属性和quit方法、IEWindow类的TagControls属性、Url属性和close方法等
#10/12/07 aaronlai    更改ieapp.py为ie.py、移动TagControl类定义到__init__.py文件中
#10/12/08 aaronlai    修改IEApp.__findIEWindows函数
#10/12/30 allenpan    添加IEApp.killAll()
#11/01/07 aaronlai    更新IEWindow.Url属性
#11/01/09 allenpan    用SHDocVw的IE的COM接口重新设计此模块
#11/02/12 allenpan    基于window窗口重构此模块

import os
import re
import subprocess
import time
from tuia.app import App
from tuia.qpath import QPath
from tuia.util import Timeout

import win32api
from win32com.client import Dispatch
import win32con
import win32event
import win32gui
import win32process

import tuia.wincontrols as win32
from tuia.webcontrols import WebPage


class IEWindow(win32.Window):
    '''IE窗口
    '''
    #11/02/14 allenpan    创建
    #11/02/23 allenpan    更改IEWindow超时时间
    #11/03/03 allenpan    调高IEWindow超时到25秒，并将IEWindow里的控件查找时间是此时间保持一致
    #13/03/12 andylfang   由于10.14.38网段的虚拟机访问某些网页，会出来长时间延迟，所以把超时时间修改为120秒
     
    _timeout = Timeout(120, 1)
    def __init__(self, locator):
        '''初始化
        
        :type locator: str或 QPath
        :param locator: 如果是QPath，则用QPath定位，如果是str,则找到当前网页地址包含locator的IE窗口 
        ''' 
        if isinstance(locator, QPath):
            win32.Window.__init__(self, locator = locator)
        elif isinstance(locator, str):
            import re
            qpstr="|classname='IEFrame' && visible='True'|classname='WorkerW' && visible='True'\
            |classname='ReBarWindow32'|maxdepth='5' && classname='Edit' && caption~='%s'" % re.escape(locator)
            old_timeout = win32.Control._timeout
            win32.Control._timeout = self._timeout
            addr_edit = win32.Control(locator=QPath(qpstr))
            win32.Control._timeout = old_timeout
            win32.Window.__init__(self, root = addr_edit.TopLevelWindow)
        else:
            raise TypeError('参数locator=%s, 不是str或QPath' % locator)#ValueError('参数locator=%s, 不是str或QPath' % locator)
    
    @property
    def WebPage(self):
        '''返回WebPage
        
        :rtype: WebPage
        :return: 返回Html文档
        '''
        #12/11/19 andylfang   创建
        
        iever = IEApp.getVersion()
        iever = int(iever.split('.')[0])
        if iever < 6:
            raise RuntimeError("不支持IE%s" %iever)
        elif iever == 6: # ie6
            qp = QPath("/classname='Shell DocObject View' && visible='True'/classname='Internet Explorer_Server'")
        elif iever ==7 :
            qp = QPath("/classname='TabWindowClass' && visible='True'/maxdepth='3' && classname='Internet Explorer_Server'")
        else:
            qp = QPath("/classname='Frame Tab' && visible='True'/maxdepth='3' && classname='Internet Explorer_Server'")
        old_timeout = win32.Control._timeout
        win32.Control._timeout = self._timeout   
        ie_embed_wnd = win32.Control(root=self, locator=qp)
        win32.Control._timeout = old_timeout
        return WebPage(ie_embed_wnd)
        
    @property 
    def Url(self):
        '''返回当前的URL地址
        '''
        qpstr = "/classname='WorkerW' && visible='True' /classname='ReBarWindow32' \
        /classname~='(Address|ComboBox)'/maxdepth='3' && classname='Edit'"
        addr_edit =  win32.Control(root=self, locator=QPath(qpstr))
        return addr_edit.Caption
    
class IEApp(App):
    '''
    IE应用程序
    
    IEApp是基于IE窗口的概念性应用程序，一个IEApp实例不一定对应一个IE进程。对IE6来说，
    一个IE窗口对应一个IE进程，但对IE7以上则是几个IE进程对应一个IE窗口。因此在实例胡IEApp时，
    是根据IE窗口当前的URL来定位IE窗口，从而实例化IEApp。
    '''
    #11/02/14 allenpan    重构
    
    def __init__(self, locator):
        '''构造函数
        
        :param locator: 查找IE窗口的URL地址中包含locator字符串的IEApp。
        :type locator: str
        '''
        self._iewnd = IEWindow(locator)        
        App.__init__(self)
        
    @staticmethod
    def go(url):
        #11/09/02 jonliang    创建（无法解决URL跳转问题，暂不返回IEApp实例）
        os.system("start iexplore.exe %s"%url)
        
    @staticmethod
    def open_url(url):
        '''打开一个url，返回进程id
        '''
        
        ie_path = IEApp.get_path()
        # -e可以实现以新进程的方式打开ie
        pid =  win32process.CreateProcess(None, '%s -e %s '%(ie_path, url), None, None, 0,
                                        win32con.CREATE_NEW_CONSOLE, None, None, win32process.STARTUPINFO() )[2]
        handle = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION, False, pid)
        win32event.WaitForInputIdle(handle, 10000)
        return pid
        
    @staticmethod
    def getVersion():
        """获取注册表中的IE版本
        """
        hkey = win32con.HKEY_LOCAL_MACHINE
        subkey = r'SOFTWARE\Microsoft\Internet Explorer'
        hkey = win32api.RegOpenKey(hkey, subkey)
        ver = win32api.RegQueryValueEx(hkey, 'Version')[0]
        win32api.RegCloseKey(hkey)
        return ver
    
    @staticmethod
    def get_path():
        '''获取注册表中IE安装位置
        '''
        hkey = win32con.HKEY_LOCAL_MACHINE
        subkey = r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\IEXPLORE.EXE'
        hkey = win32api.RegOpenKey(hkey, subkey)
        return win32api.RegEnumValue(hkey, 0)[1]
    
    @staticmethod
    def searh_ie_window(url): 
        '''查找ie进程查找到就退出，现在无法解决url对应的标签不在IE最前面的问题
        '''
        import win32com.client
        wmi = win32com.client.GetObject('winmgmts:')
        for p in wmi.InstancesOf('win32_process'):
            #找到第一个就退出
            if p.CommandLine and p.CommandLine.find('SCODEF') == -1 and not p.CommandLine.lower().find('iexplore.exe') == -1:
                ie_winow = IEWindow_QT4W(p.ProcessId)
                # IE url中可能存在“/#/”这样的无用字段，固用“/”代替
                ie_url = ie_winow.Url.replace('%3A',':').replace('%2F','/').replace('%23','#').replace('/#/','/')
                if re.match('.*%s.*'%url, ie_url):
                    return ie_winow
        else:
            raise RuntimeError('%s对应的ie窗口不存在'%url)
    
    @staticmethod
    def killAll():
        '''kill掉所有IE进程
        '''
        #2011/11/23 aaronlai    有些xp系统没有taskkill.exe文件
#        import os
#        os.popen('taskkill /IM iexplore.exe /F')
        from winlib.process import ProcessFactory
        ProcessFactory.getProcesses('iexplore.exe').terminate()
#    def open(self, url):
#        '打开url地址'
#        self._ieapp.Navigate(url) 
        
    def _disableWarnOnClose(self):
        '''在关闭多个选项时禁止弹出警告框
        '''
        #11/11/24 rayechen 将原来的RegOpenKeyEx改为使用RegCreateKey，若存在则打开，不存在则创建
        hkey = win32con.HKEY_CURRENT_USER
        subkey = r'Software\Microsoft\Internet Explorer\TabbedBrowsing'
        name = 'WarnOnClose'
        key = win32api.RegCreateKey(hkey, subkey)
        win32api.RegSetValueEx(key, name, 0, win32con.REG_DWORD, 0)
        win32api.RegCloseKey(key)
    
    def quit(self):
        '''关闭主窗口
        '''
        #11/03/15 allenpan    在ie6关闭时判断是否有弹出窗口
        #11/03/17 aaronlai    修改ie6以上浏览器的等待时间
        #11/03/25 allenpan    IE7以上直接Kill，因为用WM_ENDSESSION，IE会重新连之前的网址
        #11/11/21 aaronlai    在ie8下，通过ie的pid杀进程，会残留进程。
        iever = IEApp.getVersion()
        iever = int(iever.split('.')[0])
        if iever <= 6: # ie6
            if not self._iewnd.close():
                self._iewnd.PopupWindow.close()
                self._iewnd.close()
        else:
            try:
                #在关闭多个选项时禁止弹出警告框
                self._disableWarnOnClose()
#                win32api.PostMessage(self._iewnd.HWnd, win32con.WM_ENDSESSION, 0, 1)
                win32gui.PostMessage(self._iewnd.HWnd, win32con.WM_CLOSE, 0, 0)
#                subprocess.Popen('taskkill /F /PID %d' % self._iewnd.ProcessId).wait()
                self._iewnd.waitForInvalid(10)
            except win32api.error as e:
#                import traceback
#                traceback.print_exc()
                if e[0] == 1400: #无效窗口, IE7以上是一个进程可能会有多个窗口
                    pass
        App.quit(self)
    
    def _check_ready(self):
        #12/11/19 andylfang   把htmlcontrols修改为webcontrols
        if self._iewnd.Enabled == False: 
            popupwin = self._iewnd.PopupWindow
            if popupwin is not None:
                popupwin.close()
        #if self._iewnd.HtmlDocument.State == html.HtmlDocument.EnumPageState.COMPLETE:
        if self._iewnd.WebPage.ReadyState=='complete':
            #self._iewnd.WebPage.release()
            return True
        else:
            #self._iewnd.WebPage.release()
            return False
    
    def waitForReady(self, timeout=10):
        '''等待页面完成
        '''
        #11/03/15 allenpan    添加弹出窗口判断
        Timeout(timeout, 0.5).retry(self._check_ready, (), (), lambda x: x==True)
            
    @property
    def Url(self):
        '''返回当前IE浏览的网站地址
        '''
        return self._iewnd.Url 

try:
    from qt4w.browser.browser import IBrowser
    from tuia.webview.iewebview import IEWebView
    
    class IEWindow_QT4W(win32.Window):
        '''IE窗口 qt4w使用
        '''
        def __init__(self, process_id):
            '''初始化，进程id
            
            :params process_id: 窗口进程id
            :type process_id: int
            '''
            qpstr="|classname='IEFrame' && visible='True'|classname='WorkerW' && visible='True'\
            |classname='ReBarWindow32' |classname='Address Band Root' |maxdepth='3' && classname='Edit' && ProcessId='%d'"%process_id
            old_timeout = win32.Control._timeout
            win32.Control._timeout = self._timeout
            addr_edit = win32.Control(locator=QPath(qpstr))
            win32gui.SetForegroundWindow(addr_edit.TopLevelWindow.HWnd) #激活ie窗口，并显示在最前端
            win32.Control._timeout = old_timeout
            win32.Window.__init__(self, root = addr_edit.TopLevelWindow)
            #实现窗口最大化的逻辑
            time.sleep(0.005) #优化最大化的视觉效果
            win32gui.ShowWindow(addr_edit.TopLevelWindow.HWnd, win32con.SW_MAXIMIZE)
        
        @property
        def ie_window(self):
            '''获取Internet Explorer_Server对应的ie窗口
            '''
            iever = IEApp.getVersion()
            iever = int(iever.split('.')[0])
            if iever < 6:
                raise RuntimeError("不支持IE%s" %iever)
            elif iever == 6: # ie6
                qp = QPath("/classname='Shell DocObject View' && visible='True'/classname='Internet Explorer_Server'")
            elif iever ==7 :
                qp = QPath("/classname='TabWindowClass' && visible='True'/maxdepth='3' && classname='Internet Explorer_Server'")
            else:
                qp = QPath("/classname='Frame Tab' && visible='True'/maxdepth='3' && classname='Internet Explorer_Server'")
            old_timeout = win32.Control._timeout
            win32.Control._timeout = self._timeout   
            ie_window = win32.Control(root=self, locator=qp)
            win32.Control._timeout = old_timeout
            return ie_window
            
        @property
        def webview(self):
            '''返回WebView
            
            :rtype: IEWebView
            :return: IEWebView，用于实例化对应的WebPage
            '''
            return IEWebView(self.ie_window)
        
        @property 
        def Url(self):
            '''返回当前的URL地址
            '''
            qpstr = "/classname='WorkerW' && visible='True' /classname='ReBarWindow32' \
            /classname~='(Address|ComboBox)'/maxdepth='3' && classname='Edit'"
            addr_edit =  win32.Control(root=self, locator=QPath(qpstr))
            return addr_edit.Caption
    
    class IEBrowser(IBrowser):
        '''IE浏览器
        '''
        def open_url(self, url, page_cls=None):
            '''打开一个url，返回对应的webpage实例类
            
            :params url: url
            :type url: str
            :params page_cls: page实例类
            :type page_cls: class
            '''
            process_id = IEApp.open_url(url)
            return self._get_page_cls(process_id, page_cls)
        
        def find_by_url(self, url, page_cls=None):
            '''通过url查找页面，支持正则匹配
            '''
            ie_window = IEApp.searh_ie_window(url)
            return self._get_page_cls(ie_window, page_cls)
        
        def _get_page_cls(self, process_id_or_window, page_cls=None):
            '''获取具体的webpage实例类
            '''
            if isinstance(process_id_or_window, int):
                webview = IEWindow_QT4W(process_id_or_window).webview
            else:
                webview = process_id_or_window.webview
            if page_cls:
                return page_cls(webview)
            return webview
except:
    pass

if __name__ == "__main__":
    pass