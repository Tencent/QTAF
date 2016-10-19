# -*- coding: utf-8 -*-

'''
QQ中libcef的内嵌页面
'''

import win32gui
import tuia.gfcontrols as gf
from tuia.util import Rectangle
import _webkit
from _webkit import inspector_new

class WebPage(_webkit.WebPage):
    '''QQ Webkit的实现类
    '''
    #2012/10/08 shadowyang 创建
    
    def __init__(self, driver, locator = ''):
        '''构造函数
                
        :param driver: 底层测试桩的实现
        :type  driver: QQCefInspector
            
        :param locator: 如果是内嵌frame，指定该frame的XPath
        :type  locator: string
        '''
        super(WebPage, self).__init__(driver, locator)
        self._container = None 
        
    @property
    def container(self):
        '''WebPage所在的容器
        
        :returns: WebKit - WebPage所在的容器实例
        '''
        return self._container
    
    @container.setter
    def container(self, gfctrl):
        '''设置WebPage所在的容器
                
        :param gfctrl: 容器实例
        :type  gfctrl: WebKit
        '''
        self._container = gfctrl
            
    @classmethod
    def findByHWnd(cls, gfwebkit):
        '''通过WebkitCtrl实例获取WebPage实例
                
        :param gfwebkit: WebPage所在的容器
        :type  gfwebkit: qqlib.qqcontrols.WebKit
        
        :returns: WebPage - 创建WebPage实例
        :raises:  TypeError
        '''
        #2013/08/08 aaronlai    修改类型判断，使之能兼容AFWebKitCtrl，临时方案，后续再重构Webkit这一块
        #2013/08/08 aaronlai    修改函数参数，明确意义
        #2014/06/18 aaronlai    判定pid是否正确
        if hasattr(gfwebkit, 'ClientID'):
            pid = gfwebkit.ProcessID #渲染进程ID
            client_id = gfwebkit.ClientID #要操作的webkit实例的clientID
            if pid == 4294967295:
                raise Exception("正在加载页面，请稍后...")
        elif hasattr(gfwebkit, 'CefBrowser'):
            #进程内渲染
            pid = gfwebkit.ProcessId
            client_id = gfwebkit.CefBrowser
        else:
            raise TypeError('参数为WebKit类型')
        
        driver = _webkit.WrappedDriver(inspector_new.QQCefInspector, pid, client_id)
        #print driver
        page = WebPage(driver)
        page.container = gfwebkit #设置GF容器
        driver.Callback = page.checkValid #设置回调，用于检查页面有效性
        return page
    
    def _get_rect(self):
        '''获取页面在屏幕上的绝对位置
            
        :returns: Rectangle - 页面在屏幕上的绝对位置
        '''
        return self._container.BoundingRect
    
    @property
    def BrowserType(self):
        '''获取承载页面的浏览器的名称及版本
        
        :return: string - 浏览器的名称及版本
        '''
        return "QQ Webkit"
    
    @property
    def HWnd(self):
        '''返回page所在的窗口句柄
        '''
        #2013/12/25 aaronlai    新建
        return self._container.HWnd
    
    def activate(self):
        '''激活承载页面的窗口
        
        :raises: RuntimeError
        '''
        if not self._container:
            raise RuntimeError('未设置父层GF容器')
        hwnd = self._container.HWnd

        try:
            win32gui.SetActiveWindow(hwnd)
            win32gui.ShowWindow(hwnd, 9)
            win32gui.BringWindowToTop(hwnd)
            win32gui.SetForegroundWindow(hwnd)
            win32gui.ShowWindow(hwnd, 1)
        except win32gui.error:
            print '[WARNING]WebPage.activate() maybe failed: ', win32gui.error
    
    def close(self):
        '''由于QQ使用的是内嵌页面，因此这里只释放底层inspector对象
        '''
        if self._locator:
            return
        super(WebPage, self).close()
    
    def checkValid(self):
        '''检查页面有效性'''
        #2012/11/21 shadowyang 添加
        if not self._container.Valid:
            raise RuntimeError('页面已销毁')

class WebElement(_webkit.WebElement):
    '''
        用于QQ Webkit的WebElement实现
    '''
    pass
