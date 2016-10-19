# -*-  coding: UTF-8  -*-
'''
用于360安全浏览器(chromium内核)的Web自动化实现
'''
#2013-11-05    miawu    创建

import os
import time
import win32gui
import win32api
import win32con

from tuia import qpath
import _webkit
from _webkit import inspector_new
from ..util import Keyboard
from chrome import getNextPort, portOccupied


class WebPage(_webkit.WebPage):
    '''用于360安全浏览器(chromium内核)的WebPage实现'''
    #2013-11-05    miawu    创建

    def __init__(self, driver, locator=''):
        '''构造函数
        @type driver: ChromeInspector
        @param driver: 连接页面的ChromeInspector实例
        '''
        super(WebPage, self).__init__(driver, locator)
        self._pid = driver.getPid()
        self._phwnd = self._get_parent_hwnd()
        self._hwnd = self._get_hwnd()
        self._create_time = time.clock() #用来防止一打开即关闭的情况

    def _get_parent_hwnd(self):
        ''' 
        根据pid查找承载当前页面的浏览器窗口
        '''
        qp = qpath.QPath("/ClassName~='360se'&& processid='%d'" %self._pid)
        result = qp.search()
        if len(result) >= 1:
            return result[0].HWnd
        else:
            raise Exception('查找浏览器顶层窗口失败,进程id: %d' %self._pid)

    def _get_hwnd(self):
        '''
        根据pid查找当前的页面窗口句柄
        '''
        qp = qpath.QPath("/ClassName~='360se'/ClassName='SeWnd'\
        /ClassName~='Chrome_WidgetWin_'/ClassName~='Chrome_WidgetWin_'\
        /ClassName='Chrome_RenderWidgetHostHWND' && Visible='True' \
        && processid='%d'" %self._pid)
        result = qp.search()
        if len(result) >= 1:
            return result[0].HWnd
        else:
            raise Exception('查找浏览器页面窗口失败,进程id: %d' %self._pid)
    
    def _getPageNum(self):
        '''
        查找同一个浏览器窗口下有多少个页面，这些页面的进程ID与浏览器窗口一致；
        '''
        qp = qpath.QPath("/ClassName~='360se'/ClassName='SeWnd'\
                /ClassName~='Chrome_WidgetWin_'/ClassName~='Chrome_WidgetWin_'\
                /ClassName='Chrome_RenderWidgetHostHWND' \
                 && processid='%d'" %self._pid)
        return len(qp.search())

    @staticmethod
    def _get_browser_path():
        import sys, os
        if sys.getwindowsversion()[0] >= 6:
            # Vista/Win7支持这个环境变量
            path = os.getenv("APPDATA")
        else:
            # XP下则是位于这个路径
            path = os.getenv("USERPROFILE")
            path = os.path.join(path, r"\Application Data")
        path = os.path.join(path, r"360se6\Application\360se.exe")
        if not os.path.exists(path):
            import ctypes
            buff = ctypes.create_string_buffer(256)
            ctypes.memset(buff, 0, 256)
            if ctypes.windll.kernel32.GetWindowsDirectoryA(buff, 256):
                buff[3] = chr(0)
                buff = buff.value
            else:
                buff = 'C:\\'
            return buff + r'Program Files\360se6\Application\360se.exe'
        return path

    @staticmethod
    def _get_disk_cache_path():
        path = WebPage._get_browser_path()[:-9]
        path += "test_cache"
        return path

    @staticmethod
    def _clear_disk_cache():
        import os, shutil
        path = WebPage._get_disk_cache_path()
        if not os.path.isdir(path):
            return
        shutil.rmtree(path)
        
    @property
    def BrowserType(self):
        '''获取承载页面的浏览器的名称及版本
        @rtype: str
        @return: 浏览器的名称及版本
        '''
        return "QiHu 360se"

    @staticmethod
    def openUrl(url):
        '''用对应浏览器打开指定的URL，用这个新页面初始化WebPage实例
        @type url: str
        @param url: 要打开的URL
        @rtype：WebPage
        @return: 新打开的页面
        '''
        path = WebPage._get_browser_path()
        cmdline = [path, url]
        port = 9200
        port = getNextPort(port)
        if not port:
            raise Exception('未找到当前可用的端口号')

        cmdline.append("--remote-debugging-port=%d" % port)
        cmdline.append("--user-data-dir=remote-profile_%d" % port) # 2013/4/18 shadowyang 注释掉该行，访问https页面会打不开
        cmdline.append('--disk-cache-dir="%s"' % WebPage._get_disk_cache_path())
        cmd = ' '.join(cmdline)

        if not os.path.exists(path):
            raise RuntimeError('%s不存在' % path)
        import win32process, win32event
        processinfo = win32process.CreateProcess(None, cmd, None, None, 0, 0, None, None, win32process.STARTUPINFO())
        win32event.WaitForInputIdle(processinfo[0], 10000)
        processid = processinfo[2]

        while True:
            qp = qpath.QPath("/ClassName='SeWnd'/ClassName~='Chrome_WidgetWin_'\
            /ClassName~='Chrome_WidgetWin_' && Visible='True' && processid='%d'" %processid)
            if(qp.search() > 0): break

        inspector = inspector_new.ChromeInspector(port, url)
        return WebPage(inspector)

    @staticmethod
    def findByUrl(url):
        '''在已打开页面中查找与指定URL匹配的页面，用该页面初始化WebPage实例
        @type url: str
        @param url: 要匹配的URL
        @rtype：WebPage
        @return: 匹配到的页面
        '''
        if "://" not in url:
            url = "http://" + url

        for port in range(9200, 9210): #一般来说不会用到这么多的端口
            occupied = portOccupied(port)
            if occupied:
                try:
                    inspector = inspector_new.ChromeInspector(port, url)
                    return WebPage(inspector)
                except Exception, e:    pass
        raise Exception('查找URL失败')

    @property
    def HWnd(self):
        '''返回page所在的窗口句柄
        '''
        #2013/12/25 aaronlai    新建
        return self._phwnd
    
    def activate(self):
        '''激活承载页面的窗口'''
        try:
            win32gui.SetForegroundWindow(self._phwnd)
        except win32gui.error:
            print '[WARNING]WebPage.activate() maybe failed: %s' % win32gui.error
            pass

    def _closeBrowser(self):
        '''关闭承载页面的浏览器窗口'''
        win32api.PostMessage(self._phwnd,win32con.WM_CLOSE,0,0)
        time.sleep(1)
        ret = win32gui.IsWindow(self._phwnd)
        if not ret: 
            return True
        os.popen("taskkill /F /PID %s" %self._pid)
        return True
        
        
    def close(self):
        '''关闭承载页面的窗口'''
        if self._locator:   return
        super(WebPage, self).close()
        pageNum = self._getPageNum()
        if pageNum <= 1:                    #如果只有一个页面，直接关掉浏览器窗口
            return  self._closeBrowser()
        else:
            self.activate()
            Keyboard.inputKeys("^w")    # 此处w必须小写，大写相当于Ctrl+Shift+W
            for i in range(10):
                ret = win32gui.IsWindow(self._hwnd)
                if not ret:
                    return True
                else:
                    if i % 3 == 2:
                        Keyboard.inputKeys("^{w}")
                time.sleep(1)               # 等待浏览器进程完全退出
        
class WebElement(_webkit.WebElement):
    '''用于360安全浏览器（Chromium内核）的WebElement实现'''
    #2013-11-05    miawu    创建，本类从_webkit.WebElement派生
    pass

if __name__ == "__main__":
    pass
