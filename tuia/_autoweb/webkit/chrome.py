# -*-  coding: UTF-8  -*-
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
'''
用于Chrome浏览器的Web自动化实现
'''
#2012-02-14    beyondli    创建
#2012-02-22    beyondli    主要实现转移到_webkit中作为基类，各类改为从_webkit中的相应类派生

import os
from urllib2 import urlopen, Request
import json
import time
import win32gui

from tuia import qpath
import _webkit
from _webkit import inspector_new, LazyDriver
from ..util import Keyboard

def portOccupied(port):
    '''
    端口是否被占用
    '''
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('localhost', port))
        sock.close()
        return False
    except:
        return True

def getNextPort(port):
    '''
    获取从port开始的可用本地端口
    '''
    while port < 65536:
        if portOccupied(port):
            port += 1
        else:
            return port
    return 0 #表示获取失败

class WebPage(_webkit.WebPage):
    '''用于Chrome浏览器的WebPage实现'''
    #2012-02-14    beyondli    创建
    #2012-02-21    beyondli    初步实现了除activate和findByUrl外的全部方法
    #2012-02-22    beyondli    主要实现转移到_webkit中作为基类，本类改为从_webkit.WebPage派生
    #2012-05-17    beyondli    Chrome 19窗口结构变化，修改取句柄算法
    #2012-08-14    rambutan  使用Chrome测试桩

    def __init__(self, driver, locator=''):
        '''构造函数
        @type driver: ChromeInspector
        @param driver: 连接页面的ChromeInspector实例
        '''
        super(WebPage, self).__init__(driver, locator)
        self._pid = driver.getPid()      #在定位窗口时需要使用到窗口进程ID
        self._phwnd = self._get_parent_hwnd()
        self._hwnd = self._get_hwnd()
        self._page_hwnd = self._get_page_hwnd()
        self._create_time = time.clock() #用来防止一打开即关闭的情况

    @staticmethod
    def _find_window_has_child(window_desc, child_desc, parent_hwnd=0, start_hwnd=0):
        '''查找包含指定子窗口的窗口
        @type window: tuple(str, str)
        @param window: 要查找的窗口的classname和title
        @type child: tuple(str, str)
        @param child: 要包含的子窗口的classname和title
        @rtype: int
        @return: 要查找的窗口的classname和title
        '''
        h = start_hwnd
        hp = parent_hwnd
        hc = 0
        while True:
            h = win32gui.FindWindowEx(hp, h, window_desc[0], window_desc[1])
            if h == 0:
                return 0
            hc = win32gui.FindWindowEx(h, 0, child_desc[0], child_desc[1])
            if hc != 0:
                return h

    def _get_parent_hwnd(self):
        '''根据pid查找承载当前页面的浏览器窗口的句柄'''
        #2014/02/21 carambola   为了兼容不同版本的chrome窗口结构不一致的情况，需要遍历各个版本的窗口路径
         
        search_paths = []
        search_paths.append("/ClassName~='Chrome_WidgetWin_'\
        /ClassName='Chrome_OmniboxView'&& processid='%d'" %self._pid)
        search_paths.append("/ClassName~='Chrome_WidgetWin_1'\
        /ClassName='Chrome_WidgetWin_0'&& processid='%d'" %self._pid)
        search_paths.append("/ClassName~='Chrome_WidgetWin_1'\
        /ClassName='Static'&& processid='%d'" %self._pid)
        search_paths.append("/ClassName~='Chrome_WidgetWin_1'\
        /ClassName='Chrome_RenderWidgetHostHWND'&& processid='%d'" %self._pid)
        
        for path in search_paths:
            result = qpath.QPath(path).search()
            if len(result) >= 1:
                return result[0].Parent.HWnd
             
        raise Exception('查找浏览器顶层窗口失败,进程id: %d' %self._pid)
        '''
        #该注释代码为历史遗留代码，暂时不用用到，所以注释掉
        t = time.time()
        while time.time() - t < 10:
            h = self._find_window_has_child(("Chrome_WidgetWin_0", None), ("Chrome_WidgetWin_0", None))
            if h:
                break
            time.sleep(0.1)
        if not h:
            raise Exception("Browser window not found")
        return h
        '''

    def _get_hwnd(self):
        '''根据pid查找当前页面的句柄,该句柄的作用只是在_get_rect为了取得页面窗口的绝对坐标,用于计算元素的绝对坐标'''
        #2014/02/21 carambola   为了兼容不同版本的chrome窗口结构不一致的情况，需要遍历各个版本的窗口路径
        
        search_paths = []   
        search_paths.append("/ClassName~='Chrome_WidgetWin_1'/ClassName='Static'&& processid='%d'" %self._pid)
        search_paths.append("/ClassName~='Chrome_WidgetWin_'/ClassName~='Chrome_WidgetWin_'\
            /ClassName='Chrome_RenderWidgetHostHWND' && Visible='True'&& processid='%d'" %self._pid)
        search_paths.append("/ClassName~='Chrome_WidgetWin_'\
            /ClassName='Chrome_RenderWidgetHostHWND' && Visible='True'&& processid='%d'" %self._pid)
            
        for path in search_paths:
            result = qpath.QPath(path).search()
            if len(result) >= 1:
                return result[0].HWnd
        raise Exception('查找浏览器页面窗口失败,进程id: %d' %self._pid)

        '''
            #该注释代码为历史遗留代码，暂时不用用到，所以注释掉
            hp = self._phwnd
            hp = self._find_window_has_child(("Chrome_WidgetWin_0", None), ("Chrome_RenderWidgetHostHWND", None), hp)
            h = win32gui.FindWindowEx(hp, 0, "Chrome_RenderWidgetHostHWND", None)
            return h
         '''

    def _get_page_hwnd(self):
        '''根据pid查找页面的窗口句柄'''
        #2014/03/12 carambola   创建，为了兼容不同版本的chrome窗口结构不一致的情况，需要遍历各个版本的窗口路径
        #旧版本页面作为一个独立的窗口
        '''
        path ="/ClassName~='Chrome_WidgetWin_'/ClassName~='Chrome_WidgetWin_'\
            /ClassName='Chrome_RenderWidgetHostHWND' && Visible='True'&& processid='%d'" %self._pid
        result = qpath.QPath(path).search()
        if len(result) >= 1:
            return result[0].HWnd
        '''
        
        search_paths = []
        search_paths.append("/ClassName~='Chrome_WidgetWin_'\
        /ClassName='Chrome_OmniboxView'&& processid='%d'" %self._pid)
        search_paths.append("/ClassName~='Chrome_WidgetWin_1'\
        /ClassName='Chrome_WidgetWin_0'&& processid='%d'" %self._pid)
        search_paths.append("/ClassName~='Chrome_WidgetWin_1'\
        /ClassName='Static'&& processid='%d'" %self._pid)
        search_paths.append("/ClassName~='Chrome_WidgetWin_1'\
        /ClassName='Chrome_RenderWidgetHostHWND'&& processid='%d'" %self._pid)
        
        for path in search_paths:
            result = qpath.QPath(path).search()
            if len(result) >= 1:
                return result[0].Parent.HWnd
             
        raise Exception('查找浏览器顶层窗口失败,进程id: %d' %self._pid)
        
        
        #新版本页面窗口跟浏览器最顶层窗口是同一个窗口
        path = "/ClassName~='Chrome_WidgetWin_1'/ClassName='Static'&& processid='%d'" %self._pid
        result = qpath.QPath(path).search()
        if len(result) >= 1:
            return result[0].Parent.HWnd
             
        raise Exception('查找页面所在窗口失败,进程id: %d' %self._pid)
    
    @staticmethod
    def _get_browser_path():
        import sys, os
        if sys.getwindowsversion()[0] >= 6:
            # Vista/Win7支持这个环境变量
            path = os.getenv("LOCALAPPDATA")
        else:
            # XP下则是位于这个路径
            path = os.getenv("USERPROFILE")
            path = os.path.join(path, r"Local Settings\Application Data")
        path = os.path.join(path, r"Google\Chrome\Application\chrome.exe")
        if not os.path.exists(path):
            import ctypes
            buff = ctypes.create_string_buffer(256)
            ctypes.memset(buff, 0, 256)
            if ctypes.windll.kernel32.GetWindowsDirectoryA(buff, 256):
                buff[3] = chr(0)
                buff = buff.value
            else:
                buff = 'C:\\'
                
            path = buff + r'Program Files\Google\Chrome\Application\chrome.exe';
            if not os.path.exists(path):
                path = buff + r'Program Files (x86)\Google\Chrome\Application\chrome.exe';

        return path

    @staticmethod
    def _get_page_list():
        try:
            req = Request(url='http://localhost:9200/json',
                          headers={'User-Agent': 'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)'})
            ret = urlopen(req).read()
            data = json.loads(ret)
        except IOError:
            raise IOError("Cannot connect to browser.")
        return data

    @staticmethod
    def _get_disk_cache_path():
        path = WebPage._get_browser_path()[:-10]
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
        return "Google Chrome"

    @staticmethod
    def openUrl(url):
        '''用对应浏览器打开指定的URL，用这个新页面初始化WebPage实例
        @type url: str
        @param url: 要打开的URL
        @rtype：WebPage
        @return: 新打开的页面
        '''
        #2012/12/6 rambutan 改为CreateProcess创建进程，Popen方式与Staf有冲突
        path = WebPage._get_browser_path()
        cmdline = [path, url]
        port = 9200
		
        #2014/4/21 rambutan 检测是否存有一个chrome & chromespy实例
        processid = 0;
        try:
            processid = inspector_new.getPidByPort(port);
        except:
            pass;

        #2014/4/21 tangor 如果存在原有spy进程，则使用原port
        if processid <= 0:
            port = getNextPort(port)
            if not port:
                raise Exception('未找到当前可用的端口号')

        cmdline.append("--remote-debugging-port=%d" % port)
        #cmdline.append("--user-data-dir=remote-profile_%d" % port) # 2013/4/18 rambutan 注释掉该行，访问https页面会打不开
        cmdline.append('--disk-cache-dir="%s"' % WebPage._get_disk_cache_path())
        cmd = ' '.join(cmdline)

        if not os.path.exists(path):
            raise RuntimeError('%s不存在' % path)
        import win32process, win32event
        processinfo = win32process.CreateProcess(None, cmd, None, None, 0, 0, None, None, win32process.STARTUPINFO())
        win32event.WaitForInputIdle(processinfo[0], 10000)
        processid = processinfo[2]
        
        while True:
            qp = qpath.QPath("/ClassName~='Chrome_WidgetWin_'\
            /ClassName~='Chrome_WidgetWin_' && processid='%d'" %processid )
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
        t0 = time.time()

        #while time.time() - t0 < 10:   #去掉超时，避免还没遍历完端口就超时退出；
        for port in range(9200, 9210): #一般来说不会用到这么多的端口
            occupied = portOccupied(port)
            if occupied:
                try:
                    inspector = inspector_new.ChromeInspector(port, url)
                    return WebPage(inspector)
                except Exception, e: pass
                    #raise e
                    #if time.time() - t0 >= 10:
                    #    raise e
                    
            #time.sleep(0.5)
        raise Exception('查找URL超时')

    @property
    def HWnd(self):
        '''返回page所在的窗口句柄
        '''
        #2013/12/25 pear    新建
        #2013/03/12 carambola       页面所在窗口句柄存储在_page_hwnd
        return self._page_hwnd
    
    def activate(self):
        '''激活承载页面的窗口'''
        try:
            win32gui.SetForegroundWindow(self._phwnd)
        except win32gui.error:
            print '[WARNING]WebPage.activate() maybe failed: %s' % self
            pass
        # TODO:
        # 首先激活外框窗口
        # Ctrl+Tab切换

    def close(self):
        '''关闭承载页面的窗口'''
#        time_spend = time.clock() - self._create_time
#        if time_spend < 1: #从类创建到关闭强制需要1秒钟时间
#            time.sleep(1 - time_spend)
        if self._locator:
            return
        super(WebPage, self).close()
        self.activate()
        Keyboard.inputKeys("^w")    # 此处w必须小写，大写相当于Ctrl+Shift+W
        for i in range(10):
            ret = win32gui.IsWindow(self._hwnd)
            if not ret:
                return True
            else:
                if i % 3 == 2:
                    #再按一次Ctrl + w
                    Keyboard.inputKeys("^w")
            time.sleep(1)               # 等待浏览器进程完全退出
        #time.sleep(2)
    
    def navigate(self, url):
        ''' 页面跳转 ，navigate会自动等待页面跳转完成'''
        #2014/03/12 carambola    新建
        if "://" not in url :
            url = "http://" + url
            
        self._driver.navigate(url)
    

class WebElement(_webkit.WebElement):
    '''用于Chrome浏览器的WebElement实现'''
    #2012-02-14    beyondli    创建
    #2012-02-21    beyondli    初步实现了全部方法
    #2012-02-22    beyondli    主要实现转移到_webkit中作为基类，本类改为从_webkit.WebElement派生
    pass

if __name__ == "__main__":
    pass
