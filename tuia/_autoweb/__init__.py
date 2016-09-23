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
Web自动化适配层
'''
#2012-02-14    banana    创建
#2012-02-29    banana    初步完成WebPage与浏览器实现的整合
import time

import base
from util import (XPath, XPathParser, LazyDict)

import ie
import webkit.chrome as chrome
import webkit.cef as qplus
import webkit.qqcef as qq
import webkit.qihu360se as qihu360se

__all__ = ["WebPage", "WebElement", "FrameElement", "BrowserEnum", "XPath"]

class BrowserEnum(object):
    '''支持的浏览器类型枚举'''
    #2012-02-29    banana    创建
    IE = "msie"
    Firefox = "firefox"
    Chrome = "chrome"
    QPlus = "qplus"
    QQ = "qq"
    QiHu360Se = "qihu360se"

_classname_to_browser = {
    "Internet Explorer_Server": BrowserEnum.IE,
    "Chrome_RenderWidgetHostHWND": BrowserEnum.Chrome,
    "CefBrowserWindow": BrowserEnum.QPlus,
    "MozillaWindowClass": BrowserEnum.Firefox,
    "TXGuiFoundation": BrowserEnum.QQ
    }

_browser_type_to_browser = {
    BrowserEnum.IE: ie,
    BrowserEnum.Chrome: chrome,
    BrowserEnum.QPlus: qplus,
    BrowserEnum.Firefox: "firefox",
    BrowserEnum.QQ: qq,
    BrowserEnum.QiHu360Se: qihu360se
    }

class WebBase(object):
    '''WebPage与WebElement通用的属性与方法'''
    #2012-03-15    banana    创建
    def __init__(self):
        '''构造函数'''
        self._locators = {}
        self._controls = LazyDict(self._get_control, lister=self._locators.keys)

    def _get_loc(self, root, loc):
        if isinstance(root, basestring) and root[0] == "@":
            item = self._locators.get(root[1:])
            if not item:
                raise ValueError('Invalid root: %s' % root)
            root, loc = self._get_loc(item["root"], item["locator"] + loc)
        if not hasattr(root, 'getElement'):
            raise Exception("Cannot find the control：%s in %s" % (str(loc), str(root)))
        return root, loc

    def _get_control(self, name):
        item = self._locators[name]
        if 'instance' in item:
            return item['instance']
        root = item['root']
        loc = item['locator']
        cls = item['type']
        root, loc = self._get_loc(root, loc)
        instance = cls(root, loc)
        item['instance'] = instance
        return instance

    def updateLocator(self, items={}):
        '''更新locator集合
        @type items: dict
        @param items: 新定义的locator的集合
        '''
        return self._locators.update(items)

    @property
    def Controls(self):
        '''获取页面中当前已定义的控件
        @rtype: dict
        @return: 包含当前页面已定义控件的集合
        '''
        return self._controls

    def getElement(self, locator):
        '''在页面中查找元素，返回第一个匹配的元素
        @type locator: str或XPath
        @param locator: 作为查找条件的XPath
        @rtype: WebElement
        @return: 查找到的元素
        '''
        return WebElement(self, locator)

    def getElements(self, locator):
        '''在页面中查找元素，返回包含所有匹配的元素的列表
        @type locator: str或XPath
        @param locator: 作为查找条件的XPath
        @rtype: list<WebElement>
        @return: 查找到的元素的列表
        '''
        return self._obj.getElements(locator)
#        locators = XPath(locator).break_frames()
#        locators[-1] = "(%s)" % locators[-1]
#        locator = "".join(locators)
#        cnt = 1
#        ret = []
#        while True:
#            loc = XPath('%s[%d]' % (locator, cnt))
#            try:
#                elem = self.getElement(loc)
#            except:
#                break
#            if not isinstance(elem, WebElement) or not elem.exist():
#                break
#            ret.append(elem)
#            cnt += 1
#        return ret


class WebPage(WebBase):
    '''封装Web自动化所需的页面相关的逻辑，对应于具体浏览器的派生类需要实现这些接口'''
    #2012-02-14    banana    创建
    #2012-02-29    banana    新增findByHWnd方法
    def __init__(self, page):
        '''构造函数
        @type page: WebPage 或 Window
        @param page: 作为新实例基础的WebPage对象，或包含页面的Window对象
        '''
        super(WebPage, self).__init__()
        if isinstance(page, base.IWebPage):
            self._obj = page
        elif isinstance(page, WebPage):
            self._obj = page._obj
        elif isinstance(page, int) or hasattr(page, "HWnd"):
            self._obj = self._get_page_by_hwnd(page)
        else:
            raise ValueError("Need a WebPage or Window object!")
        self._page = self

    def __str__(self):
        return '<%s: "%s" in %s>' % (self.__class__.__name__, (self.Title or self.Url), self.BrowserType)

    @staticmethod
    def _get_browser_type(hwnd):
        '''根据hwnd对应的窗口类型判断浏览器类型
        @type hwnd: int
        @param hwnd: 承载页面的窗口句柄
        @rtype：BrowserEnum
        @return: 浏览器类型
        '''
        import ctypes
        GetClassName = ctypes.windll.user32.GetClassNameW
        buf = ctypes.create_unicode_buffer(1024)
        try:
            GetClassName(hwnd, buf, 1024)
            ret = _classname_to_browser[buf.value]
        except:
            return None
        return ret

    def _get_page_by_hwnd(self, hwnd):
        '''在指定的窗口中查找页面，用该页面初始化WebPage实例
        @type hwnd: Window或int
        @param hwnd: Window对象或其句柄
        @rtype：WebPage
        @return: 匹配到的页面
        '''
        #2012/11/14 rambutan 增加对QQWebkit控件的支持
        if hasattr(hwnd, 'HWnd'):
            hwnd_old = hwnd
            hwnd = hwnd.HWnd
        elif not isinstance(hwnd, int):
            raise ValueError("Must assign a window or handle.")
        browser_type = self._get_browser_type(hwnd)
        if browser_type not in _browser_type_to_browser:
            raise ValueError("The browser [%s] is not supported." % browser_type)
        browser = _browser_type_to_browser[browser_type]
        try:
            page = browser.WebPage.findByHWnd(hwnd_old) #如果是gf.Control类型，则优先传入该类型参数
        except TypeError:
            page = browser.WebPage.findByHWnd(hwnd)
        return page

    @staticmethod
    def _clear_disk_cache(browser_type=None):
        '''清除指定浏览器的缓存
        @type browser_type: BrowserEnum
        @param browser_type: 要清除缓存的浏览器，None表示系统默认浏览器（暂未实现）
        '''
        if not browser_type:
            raise ValueError("暂不支持调用系统默认浏览器，请指定浏览器类型。")
        if browser_type not in _browser_type_to_browser:
            raise ValueError("不支持指定的浏览器。")
        browser = _browser_type_to_browser[browser_type]
        browser.WebPage._clear_disk_cache()

    @staticmethod
    def openUrl(url, browser_type=None):
        '''用对应浏览器打开指定的URL，用这个新页面初始化WebPage实例
        @type url: str
        @param url: 要打开的URL
        @type browser_type: BrowserEnum
        @param browser_type: 要使用的浏览器，None表示系统默认浏览器（暂未实现）
        @rtype：WebPage
        @return: 新打开的页面
        '''
        if not browser_type:
            raise ValueError("暂不支持调用系统默认浏览器，请指定浏览器类型。")
        if browser_type not in _browser_type_to_browser:
            raise ValueError("不支持指定的浏览器。")
        browser = _browser_type_to_browser[browser_type]
        page = browser.WebPage.openUrl(url)
        return WebPage(page)

    @staticmethod
    def findByUrl(url, browser_type=None):
        '''在已打开页面中查找与指定URL匹配的页面，用该页面初始化WebPage实例
        @type url: str
        @param url: 要匹配的URL
        @type browser_type: BrowserEnum
        @param browser_type: 要使用的浏览器，None表示系统默认浏览器（暂未实现）
        @rtype：WebPage
        @return: 匹配到的页面
        '''
        if not browser_type:
            raise ValueError("暂不支持调用系统默认浏览器，请指定浏览器类型。")
        if browser_type not in _browser_type_to_browser:
            raise ValueError("不支持指定的浏览器。")
        browser = _browser_type_to_browser[browser_type]
        page = browser.WebPage.findByUrl(url)
        if not page:
            return None
        return WebPage(page)

    @property
    def AccessibleObject(self):
        """返回AccessibleObject
        
        """
        #2013/10/22 pear    created
        return self._obj.AccessibleObject
    
    @property
    def Url(self):
        '''获取页面的当前URL
        @rtype: str
        @return: 页面的当前URL
        '''
        return self._obj.Url

    @property
    def Title(self):
        '''获取页面的当前标题
        @rtype: str
        @return: 页面的当前标题
        '''
        return self._obj.Title

    @property
    def ReadyState(self):
        '''获取页面的当前状态
        @rtype: int
        @return: 页面的当前状态
        '''
        return self._obj.ReadyState

    @property
    def ScreenWidth(self):
        return self._obj.ScreenWidth;
    @property
    def ScreenHeight(self):
        return self._obj.ScreenHeight;



    @property
    def BrowserType(self):
        '''获取承载页面的浏览器的名称及版本
        @rtype: str
        @return: 浏览器的名称及版本
        '''
        return str(self._obj.BrowserType)

    @property
    def Dialog(self):
        try:
            return WebDialog(self._obj)
        except:
            return None

    def activate(self):
        '''激活承载页面的窗口'''
        return self._obj.activate()

    def close(self):
        '''关闭承载页面的窗口'''
        return self._obj.close()

    def release(self):
        '''释放占用的资源'''
        return self._obj.release()

    def scroll(self, toX, toY):
        '''按指定的偏移量滚动页面
        @type toX: int
        @param toX: 横向滚动的偏移，负值向左，正值向右
        @type toY: int
        @param toY: 纵向滚动的偏移，负值向上，正值向下
        '''
        return self._obj.scroll(toX, toY)

    def execScript(self, script):
        '''在页面中执行脚本代码
        @type script: str
        @param script: 要执行的脚本代码
        @rtype: bool
        @return: True=成功；False=失败
        '''
        return self._obj.execScript(script)

    def waitForReady(self, timeout=60):
        '''等待页面加载完成
        @type timeout: int或float
        @param timeout: 最长等待的秒数
        '''
        return self._obj.waitForReady(timeout)
    
    def maximize(self):
        '''浏览器最大化（只支持ie系列）'''
        if self.BrowserType.lower().find("msie") == -1:
            raise Exception("目前还不支持非IE浏览器的窗口最大化。")
        return self._obj.max()

    def navigate(self, url):
        '''
        @desc: 导航至指定URL
        @type url: str
        @param url: 指定导航的URL
        '''
        return self._obj.navigate(url)
        

class WebElement(WebBase):
    '''封装Web自动化所需的页面元素相关的逻辑，对应于具体浏览器的派生类需要实现这些接口'''
    #2012-02-14    banana    创建
    #2012-03-08    banana    实现
    def __init__(self, root, locator):
        '''构造函数
        @type root: WebElement或WebPage
        @param root: 根据locator定位的基准元素
        @type locator: XPath或str
        @param locator: 描述元素的定位符
        '''
        super(WebElement, self).__init__()
        if not (isinstance(root, WebPage) or isinstance(root, WebElement)):
            raise ValueError("Invalid 'root' parameter.")
        self._root = root
        self._locator = locator
        self._page = root._page
        self._objele = None

    @property
    def _obj(self):
        if not self._objele:
            ele = self._root._obj.getElement(self._locator)
            if not isinstance(ele, base.IWebElement):
                raise Exception('WebElement not found: "%s" in %s'
                                % (self._locator, self._root))
            self._objele = ele
        return self._objele

    def __str__(self):
        return '<%s: "%s" in %s>' % (self.__class__.__name__, self._locator, self._root)

    @property
    def Page(self):
        '''包含当前元素的WebPage对象
        @rtype: WebPage
        @return: 包含当前元素的WebPage对象
        '''
        return self._page

    @property
    def Attributes(self):
        '''当前元素的属性集合
        @rtype: WebElementAttributes
        @return: 元素的属性集合
        '''
        return self._obj.Attributes

    @property
    def AccessibleObject(self):
        """返回AccessibleObject
        
        :rtype: tuia.accessible.AccessibleObject
        """
        #2013/10/22 pear    created
        return self._obj.AccessibleObject
    
    @property
    def Styles(self):
        '''当前元素的样式集合
        @rtype: WebElementStyles
        @return: 元素的样式集合
        '''
        return self._obj.Styles

    @property
    def BoundingRect(self):
        '''当前元素在屏幕上的位置和大小
        @rtype: Rect
        @return: 元素在屏幕上的位置和大小
        '''
        return self._obj.BoundingRect

    @property
    def Displayed(self):
        '''当前元素是否显示
        @rtype: bool
        @return: 元素是否显示
        '''
        return self._obj.Displayed

    @property
    def Focused(self):
        '''当前元素是否具有焦点
        @rtype: bool
        @return: 元素是否具有焦点
        '''
        return self._obj.Focused

    @property
    def InnerText(self):
        '''当前元素所包含的文本
        @rtype: str
        @return: 元素所包含的文本
        '''
        return self._obj.InnerText

    @InnerText.setter
    def InnerText(self, text):
        self._obj.InnerText = text

    @property
    def InnerHtml(self):
        '''当前元素所包含的HTML
        @rtype: str
        @return: 元素所包含的HTML
        '''
        return self._obj.InnerHtml

    @InnerHtml.setter
    def InnerHtml(self, html):
        self._obj.InnerHtml = html

    def exist(self):
        '''检查元素是否有效
        @rtype: bool
        @return: 定位成功为True，不成功为False
        '''
        try:
            self._root._obj.getElement(self._locator).InnerHtml
            return True
        except:
            return False

    def scroll(self, toX, toY): #未经测试
        '''按指定的偏移量滚动元素
        @type toX: int
        @param toX: 横向滚动的偏移，负值向左，正值向右
        @type toY: int
        @param toY: 纵向滚动的偏移，负值向上，正值向下
        '''
        return self._obj.scroll(toX, toY)

    def waitForAttribute(self, name, value, timeout=10, interval=0.5):
        '''暂停程序执行，直到当前元素的指定属性变为特定值
        @type name: str
        @param name: 等待的属性名称
        @type value: obj
        @param value: 等待的属性值，无论何类型都先转为str再处理
        @type timeout: int或float
        @param timeout: 最多等待的秒数
        @type interval: int或float
        @param interval: 查询间隔的秒数
        '''
        return self._obj.waitForAttribute(name, value, timeout, interval)

    def waitForStyle(self, name, value, timeout=10, interval=0.5):
        '''暂停程序执行，直到当前元素的指定样式变为特定值
        @type name: str
        @param name: 等待的样式名称
        @type value: obj
        @param value: 等待的样式值，无论何类型都先转为str再处理
        @type timeout: int或float
        @param timeout: 最多等待的秒数
        @type interval: int或float
        @param interval: 查询间隔的秒数
        '''
        return self._obj.waitForStyle(name, value, timeout, interval)

    def waitForText(self, value, timeout=10, interval=0.5): #未经测试
        '''暂停程序执行，直到当前元素的InnerText变为特定值
        @type value: str
        @param value: 等待的文本值
        @type timeout: int或float
        @param timeout: 最多等待的秒数
        @type interval: int或float
        @param interval: 查询间隔的秒数
        '''
        return self._obj.waitForText(value, timeout, interval)

    def click(self, xOffset=None, yOffset=None):
        '''鼠标左键单击
        @type xOffset: int
        @param xOffset: 距离控件区域左上角的横向偏移。
        @type yOffset: int
        @param yOffset: 距离控件区域左上角的纵向偏移。
        '''
        time.sleep(0.1)
        return self._obj.click(xOffset, yOffset)

    def doubleClick(self, xOffset=None, yOffset=None): #未经测试
        '''鼠标左键双击
        @type xOffset: int
        @param xOffset: 距离控件区域左上角的横向偏移。
        @type yOffset: int
        @param yOffset: 距离控件区域左上角的纵向偏移。
        '''
        return self._obj.doubleClick(xOffset, yOffset)

    def rightClick(self, xOffset=None, yOffset=None): #未经测试
        '''鼠标右键单击
        @type xOffset: int
        @param xOffset: 距离控件区域左上角的横向偏移。
        @type yOffset: int
        @param yOffset: 距离控件区域左上角的纵向偏移。
        '''
        return self._obj.rightClick(xOffset, yOffset)

    def hover(self, xOffset=None, yOffset=None):
        '''鼠标悬停
        @type xOffset: int
        @param xOffset: 距离控件区域左上角的横向偏移。
        @type yOffset: int
        @param yOffset: 距离控件区域左上角的纵向偏移。
        '''
        return self._obj.hover(xOffset, yOffset)

    def drag(self, toX=None, toY=None):
        '''拖放到指定位置
        @type toX: int
        @param toX: 拖放终点距离起点的横向偏移。
        @type toY: int
        @param toY: 拖放终点距离起点的纵向偏移。
        '''
        return self._obj.drag(toX, toY)

    def sendKeys(self, keys):
        '''发送按键命令
        @type keys: str
        @param keys: 要发送的按键
        '''
        return self._obj.sendKeys(keys)

    def setFocus(self):
        '''设控件为焦点'''
        return self._obj.setFocus()


class FrameElement(WebElement):
    '''对应于HTMLFrame元素和HTMLIFrame元素的WebElement派生类'''
    #2012-03-08    banana    创建
    def __init__(self, root, locator):
        loc = XPathParser.parse_for_frames(locator)[-1]
        if not ('/iframe' in loc or '/frame' in loc):
            raise ValueError("Not a Frame nor IFrame: '%s'" % locator)
        super(FrameElement, self).__init__(root, locator)
        self._frame_page = None

    @property
    def FramePage(self):
        if self._frame_page is None:
            if not isinstance(self._obj, base.IWebElement):
                raise ValueError("Invalid WebElement.")
            page = self._obj.Page.getFramePage(self._locator)
            self._frame_page = WebPage(page)
        return self._frame_page


if __name__ == "__main__":
    pass
