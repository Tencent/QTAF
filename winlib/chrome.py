# -*- coding: utf-8 -*-
'''
Chrome浏览器的GUI自动化库
'''
#12/04/16 benjaminli      created

import tuia.wincontrols
import tuia.qpath
import tuia.util
import traceback
import os

from tuia.exceptions import TimeoutError

EXE_FILENAME = 'chrome.exe'

def KillAll():
    for p in tuia.util.Process.GetProcessesByName(EXE_FILENAME):
        p.terminate()

def CloseAll():
    g_MainFrameMgr.closeAll()

def GetInstallDir():
    import sys
    if sys.getwindowsversion()[0] >= 6:
        # Vista/Win7支持这个环境变量
        path = os.getenv("LOCALAPPDATA")
    else:
        # XP下则是位于这个路径
        path = os.getenv("USERPROFILE")
        path = os.path.join(path, "Local Settings", "Application Data")
    return os.path.join(path, "Google", "Chrome")

def GetExePath():
    return os.path.join(GetInstallDir(), "Application", EXE_FILENAME)

def GetCachePath():
    return os.path.join(GetInstallDir(), 'User Data', 'Default', 'Cache')

def ClearCache():
    import shutil
    print '正在清空Chrome缓存'
    CloseAll()
    pathCache = GetCachePath()
    print '删除目录：%s' % pathCache
    shutil.rmtree(pathCache, ignore_errors=True)

def CreateChrome(cmdArgs=None):
    '''
    
    :summary: 启动一个新的Chrome主窗口
    :return: 对应的MainFrame实例
    '''
    import win32process, win32event
    exePath = GetExePath()
    currentDir = os.path.dirname(exePath)
    if cmdArgs is None:
        cmdLine = exePath
    else:
        cmdLine = '"%s" "%s"' % (exePath, cmdArgs)
    hp, ht, _, _ = win32process.CreateProcess(
                 None, cmdLine, None, None, 0, 0, None, currentDir, win32process.STARTUPINFO())
    win32event.WaitForInputIdle(hp, 3000)
    ht.Close()
    hp.Close()

class WebPage(tuia.wincontrols.Window):
    '''
    
    :summary: Chrome的Web页渲染窗口（Chrome_RenderWidgetHostHWND）
    '''
    def __init__(self, hWnd):
        self._hwnd = hWnd
        self._mainFrame = None
    
    @staticmethod
    def openUrlDefault():
        '''
        
        :summary: 新开一个独立chrome窗口，并打开默认页
        '''
        CreateChrome()
        _mfList = g_MainFrameMgr.waitForMainFrame()
        return WebPage.findByTitle(_mfList[0], '')
    
    @staticmethod
    def findByTitle(mainFrame, title=''):
        '''
        
        :summary: 在指定的mainFrame中查找与网页title匹配的Tab页
        :param mainFrame: MainFrame实例
        :param title: 要匹配的title，正则表达式，不传此参数则任意标题均可匹配
        '''
        qpathPage = tuia.qpath.QPath("|ClassName~='Chrome_WidgetWin_\d' && Caption~='%s'" % title)
        wndPage = tuia.wincontrols.Window(root=mainFrame, locator=qpathPage)
        webPage = WebPage(wndPage.HWnd)
        webPage._mainFrame = mainFrame
        return webPage
    
    def getMainFrame(self):
        if self._mainFrame is None:
            self._mainFrame = MainFrame(self.Parent.HWnd)
        return self._mainFrame
    MainFrame = property(getMainFrame, doc='此Tab页所属的MainFrame')
    
    def getRenderHostHWnd(self):
        qpathHost = tuia.qpath.QPath("|ClassName='Chrome_RenderWidgetHostHWND'")
        return tuia.wincontrols.Window(root=self, locator=qpathHost).HWnd
    RenderHostHWnd = property(getRenderHostHWnd, doc='Chrome用来渲染的真实窗口')
    
    def navigate(self, url):
        '''
        
        :summary: 跳转到指定url
        '''
        self.activate()
        self.MainFrame.navigate(url)
    
    def activate(self):
        '''
        
        :summary: 激活承载页面的窗口
        :attention: 目前不支持多Tab激活，未来可能用Ctrl+Tab或父子关系变换实现
        '''
        try:
            self.MainFrame.bringForeground()
        except:
            traceback.print_exc()
    
    def close(self):
        '''
        
        :summary: 通过按Ctrl + W快捷键关闭Tab页
        '''
        import tuia.keyboard
        self.activate()
        tuia.keyboard.Keyboard.inputKeys("^W")
        try:
            g_MainFrameMgr.waitForAnyProcQuit()
            g_MainFrameMgr.refresh()
        except:
            pass

class MainFrame(tuia.wincontrols.Window):
    def __init__(self, hWnd):
        self._hwnd = hWnd
        self._urlBox = None
        super(MainFrame,self).__init__(root=hWnd)
    
    @staticmethod
    def findByTitle(title):
        '''
        
        :summary: 在已打开的所有chrome独立窗口中寻找与标题匹配的窗口
        :type title: str，正则表达式
        :param title: 要匹配的title
        '''
        qpathFrame = tuia.qpath.QPath("|ClassName~='Chrome_WidgetWin_\d' && Caption~='%s'" % title)
        return MainFrame(tuia.wincontrols.Window(locator=qpathFrame).HWnd)
    
    @staticmethod
    def findAll():
        '''
        
        :summary: 查询所有的MainFrame实例
        :return: []，列表内部的实例均为MainFrame
        :note: 因为顶层窗口有多余的Chrome_WidgetWin_0，必须先查Chrome_OmniboxView，其父窗口才是真正的MainFrame
        '''
        _mfList = []
        qpathUrlBox = tuia.qpath.QPath("|ClassName~='Chrome_WidgetWin_\d'|ClassName='Chrome_OmniboxView'")
        for _urlBox in qpathUrlBox.search():
            _mf = MainFrame(_urlBox.Parent.HWnd)
            _mf._urlBox = _urlBox
            _mfList.append(_mf)
        return _mfList
    
    def getUrlBox(self):
        if self._urlBox is None:
            qpathUrlBox = tuia.qpath.QPath("|ClassName='Chrome_OmniboxView'")
            self._urlBox = tuia.wincontrols.Window(root=self, locator=qpathUrlBox)
        return self._urlBox
    UrlBox = property(getUrlBox, doc='chrome主窗口所属的URL输入框')
    
    def navigate(self, url):
        '''
        
        :summary: 将网址输入框中的内容改为url后按回车键
        '''
        self.UrlBox.Text = url
        self.UrlBox.sendKeys('{ENTER}')

class MainFrameMgr(object):
    def __init__(self):
        self._hWndListOld = []
        self._hWndListNew = []
        self._procList = []
        self.refresh()
    
    def _isAnyProcQuit(self):
        for _proc in self._procList:
            if _proc.Live is False:
                return True
        return False
    AnyProcQuit = property(fget=_isAnyProcQuit, doc='有任意一个chrome.exe进程退出')
    
    def _getHWndListNew(self):
        self.refresh()
        return self._hWndListNew
    
    def _getProcList(self):
        self.refresh()
        return self._procList
    
    def waitForAnyProcQuit(self, timeout=3, interval=0.5):
        '''
        
        :summary: 等待任意一个chrome.exe进程退出
        :param timeout: 最多等timeout秒
        :param interval: 每interval秒检查一次是否有进程退出
        '''
        tuia.util.Timeout(timeout,interval).waitObjectProperty(self, 'AnyProcQuit', True)
    
    def waitForMainFrame(self, timeout=5, interval=0.5, count=1):
        '''
        
        :summary: 等待count个MainFrame新创建出来
        :param timeout: 最多等timeout秒
        :param interval: 每interval秒检查一次是否有进程退出
        :param count: MainFrame个数
        '''
        tuia.util.Timeout(timeout,interval).retry(self._getHWndListNew, (), (), lambda x: len(x)==count)
        _mfList = []
        for _hWnd in self._hWndListNew:
            _mfList.append(MainFrame(_hWnd))
        return _mfList
    
    def refresh(self):
        '''
        
        :summary: 更新内部维护的hWnd列表和进程列表
        :attention: 在chrome窗口或进程发生变化时，需要及时调用此方法
        '''
        _hWndListLast = self._hWndListOld
        _hWndListLast.extend(self._hWndListNew)
        self._hWndListOld = []
        self._hWndListNew = []
        for _mf in MainFrame.findAll():
            if _mf.HWnd in _hWndListLast:
                self._hWndListOld.append(_mf.HWnd)
            else:
                self._hWndListNew.append(_mf.HWnd)
        self._procList = tuia.util.Process.GetProcessesByName(EXE_FILENAME)
    
    def closeAll(self):
        '''
        
        :summary: 关闭所有的Chrome窗口
        '''
        self.refresh()
        _hWndList = self._hWndListOld
        _hWndList.extend(self._hWndListNew)
        for _hWnd in _hWndList:
            MainFrame(_hWnd).close()
        try:
            tuia.util.Timeout(3, 0.5).retry(self._getProcList, (), (), lambda x: len(x)==0)
        except TimeoutError:
            KillAll()

g_MainFrameMgr = MainFrameMgr()

if __name__ == '__main__':
    pass
    page = WebPage.openUrlDefault()
    page.navigate('testing.sng.local')
#    time.sleep(3)
#    page.close()
