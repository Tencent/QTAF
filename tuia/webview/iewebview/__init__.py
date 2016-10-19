# -*- coding: UTF-8 -*-

'''IE WebView实现
'''

# 2015/11/6 shadowyang 创建

import time
import logging
import win32gui
import win32process

from iedriver import IEDriver
from qt4w.util import JavaScriptError
from tuia.webview.base import WebViewBase
from tuia.mouse import Mouse, MouseFlag, MouseClickType

class IEWebView(WebViewBase):
    '''IE WebView实现
    '''
    def __init__(self, ie_window_or_hwnd):
        '''初始化
        
        :params ie_window_or_hwnd: ie窗口或句柄
        :type ie_window_or_hwnd: Control or int
        '''
        if isinstance(ie_window_or_hwnd, int):  # 句柄需要转化为对应的窗口，句柄是IEFrame的句柄
            process_id = win32process.GetWindowThreadProcessId(ie_window_or_hwnd)[1]
            from browser.ie import IEWindow_QT4W
            ie_window = IEWindow_QT4W(process_id).ie_window
        else:
            ie_window = ie_window_or_hwnd
        from qt4w.webdriver import iewebdriver
        self._webdriver = iewebdriver.IEWebDriver(self)
        self._browser_type = 'ie'
        self._ie_window = ie_window
        self._driver = IEDriver(self._ie_window.HWnd)
        super(IEWebView, self).__init__(ie_window, self._webdriver)
        
    def _get_frame_window_by_xpath(self, frame_xpaths):
        '''根据xpath查找对应的frameIHTMLWindow对象
        '''
        if len(frame_xpaths) == 0: return None
        else:
            parent_frame_win = self._get_frame_window_by_xpath(frame_xpaths[:-1])
            frame_id, url = self._webdriver._get_frame_info(frame_xpaths)
            # print frame_id, url
            return self._driver.get_frame_window(parent_frame_win, frame_id, url)
    
    def eval_script(self, frame_xpaths, script, use_eval=True):
        '''在指定frame中执行JavaScript，并返回执行结果
        
        :param frame_xpaths: frame元素的XPATH路径，如果是顶层页面，怎传入“[]”
        :type frame_xpaths:  list
        :param script:       要执行的JavaScript语句
        :type script:        string
        '''
        import pywintypes
        from iedriver import IEDriverError
        frame_win = None
        retry_count = 3
        for i in range(retry_count):
            try:
                # print 'xxx', frame_xpaths
                if frame_xpaths:
                    frame_win = self._get_frame_window_by_xpath(frame_xpaths)
                result = self._driver.eval_script(frame_win, script, use_eval)
                break
            except (pywintypes.com_error, IEDriverError), e:
                if i >= retry_count - 1:
                    raise e
                logging.exception('eval script error')
                time.sleep(1)
                self._driver._init_com_obj()  # 重新初始化COM对象
        if result == None: return
        return self._handle_result(result, frame_xpaths)
    
    def highlight(self, elem_xpaths):
        '''使元素高亮
        
        :param elem_xpaths: 元素的XPATH路径
        :type elem_xpaths:  list
        '''
        try:
            return self._webdriver.highlight(elem_xpaths)
        except JavaScriptError, e:
            # IE下可能会出现setAttribute时拒绝访问的错误，此时需要重新创建DIV
            logging.warn('highlight error: %s' % e)
            self.eval_script(elem_xpaths[:-1], 'qt4w_driver_lib.initHighlightDiv();')
            return self._webdriver.highlight(elem_xpaths)
        
    # 因为ie在使用Mouse.postClick情况下，需要发送先发送两次WM_LBUTTONDOWN，然后发送WM_LBUTTONUP才能点击生效，
    # 为了不修改tuia的内容，所以这里使用全局的鼠标点击实现，但是这种情况下，如果页面被遮挡，点击仍然会失败
    def inner_click(self, flag, click_type, x_offset, y_offset):
        new_x, new_y = win32gui.ClientToScreen(self._window.HWnd, (int(x_offset), int(y_offset)))
        Mouse.click(new_x, new_y, flag, click_type)
    
    def click(self, x_offset, y_offset):
        self.inner_click(MouseFlag.LeftButton, MouseClickType.SingleClick, x_offset, y_offset)
        
    def double_click(self, x_offset, y_offset):
        self.inner_click(MouseFlag.LeftButton, MouseClickType.DoubleClick, x_offset, y_offset)
    
    def right_click(self, x_offset, y_offset):
        self.inner_click(MouseFlag.RightButton, MouseClickType.SingleClick, x_offset, y_offset)
        
    
if __name__ == '__main__':
    pass
    
