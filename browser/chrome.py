# -*- coding: UTF-8 -*-

'''ChromeBrowser的接口实现
'''

# 2016/01/05  guyingzhao 创建文件
# 2016/02/25  cesarzheng 修改加入参数page_cls

import re
from tuia.qpath import QPath
from tuia.wincontrols import Window

import win32api
import win32event
import win32gui

from qt4w.browser.browser import IBrowser
from tuia.webview.chromewebview import ChromeWebView


class ChromeBrowser(IBrowser):
    '''Chrome浏览器
    '''
    def __init__(self, port=9200):
        self._port = port
        self._main_wnd = None
        self._pid = 0
    
    def get_chrome_window(self, pid):
        '''通过pid查找对应的chrome窗口
        '''
        qp_str = QPath(r"/ClassName='Chrome_WidgetWin_1'&&ProcessId='%d'&&Visible='True' /ClassName='Chrome_RenderWidgetHostHWND' && Instance='0' " % pid)
        return Window(locator=qp_str)
    
    def open_url(self, url, page_cls=None):
        import win32process, win32con
        while is_port_occupied(self._port):  # 如果端口被占用，则查找下一个可用端口
            self._port += 1
        exe_path = ChromeBrowser.get_browser_path()
        temp_dir = r'C:\Users\Administrator\AppData\Local\Temp\Chrome_%d' % self._port
        params = "--remote-debugging-port=%d --disable-session-crashed-bubble --disable-translate --user-data-dir=%s" % (self._port, temp_dir)
        cmd = ' '.join([exe_path, params, url])
        _, _, pid, _ = win32process.CreateProcess(None, cmd, None, None, 0, 0, None, None, win32process.STARTUPINFO())
        handle = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION, False, pid)
        win32event.WaitForInputIdle(handle, 10000)
        self._pid = pid
        print 'chrome进程为%d' % pid  # 加上此句话查看chrome是否成功打开了
        page_wnd = self.get_chrome_window(pid)
        self._webview = ChromeWebView(page_wnd, url, self._pid, self._port)
        return self.get_page_cls(self._webview, page_cls)
   
    def find_by_url(self, url, page_cls=None):
        webview = self.search_chrome_webview(url)
        return self.get_page_cls(webview, page_cls)
     
    def get_page_cls(self, webview, page_cls=None):
        '''得到具体页面类
        '''
        if page_cls:
            return page_cls(webview)
        return webview
    
    @staticmethod
    def get_browser_path():
        '''获取chorme.exe的路径
        '''
        import _winreg
        sub_key = "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Google Chrome"
        try:
            hkey = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, sub_key)
            install_dir, _ = _winreg.QueryValueEx(hkey, "InstallLocation")
            _winreg.CloseKey(hkey)
        except WindowsError:
            hkey = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, sub_key)
            install_dir, _ = _winreg.QueryValueEx(hkey, "InstallLocation")
        return install_dir + "\\chrome.exe"
    
    def search_chrome_webview(self, url):
        '''根据url查找chrome对应的webview类
        
        returns ChromeWebView: ChromeWebView类
        '''
        import win32com.client
        wmi = win32com.client.GetObject('winmgmts:')
        for p in wmi.InstancesOf('win32_process'):
            if not p.CommandLine:
                continue
            if p.CommandLine.startswith('"%s"' % self.get_browser_path()):
                chrome_window = self.get_chrome_window(p.ProcessId)
                self._webview = ChromeWebView(chrome_window, url, p.ProcessId)
                if re.match('.*%s.*' % url, self.Url):
                    win32gui.SetForegroundWindow(chrome_window.TopLevelWindow.HWnd)
                    return self._webview
                raise RuntimeError('当前标签页不在窗口最前端！')
        else:
            raise RuntimeError('%s对应的chrome进程不存在' % url)
    
    @staticmethod
    def killall():
        '''杀掉所有chrome进程
        '''
        from winlib.process import ProcessFactory
        ProcessFactory.getProcesses('chrome.exe').terminate()
        
    @property
    def Url(self):
        return self._webview.eval_script(None, 'location.href')
 
def is_port_occupied(port):
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
    
def get_next_avail_port(port):
    cur_port = port
    while is_port_occupied(cur_port):
        cur_port += 1
    return cur_port
    
if __name__ == '__main__':
    pass
