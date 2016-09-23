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
定义对应于具体浏览器的Web自动化组件需要实现的接口
'''
#2012-02-14    banana    创建

class IWebPage(object):
    '''封装Web自动化所需的页面相关的逻辑，对应于具体浏览器的派生类需要实现这些接口'''
    #2012-02-14    banana    创建
    def __init__(self, hwnd):
        '''构造函数
        @type hwnd: hwnd
        @param hwnd: 承载页面的窗口的句柄
        '''
        raise NotImplementedError()

    @classmethod
    def openUrl(cls, url):
        '''用对应浏览器打开指定的URL，用这个新页面初始化WebPage实例
        @type url: str
        @param url: 要打开的URL
        @rtype：WebPage
        @return: 新打开的页面
        '''
        raise NotImplementedError()

    @classmethod
    def findByUrl(cls, url):
        '''在已打开页面中查找与指定URL匹配的页面，用该页面初始化WebPage实例
        @type url: str
        @param url: 要匹配的URL
        @rtype：WebPage
        @return: 匹配到的页面
        '''
        raise NotImplementedError()

    @classmethod
    def findByHWnd(cls, hwnd):
        '''在指定的窗口中查找页面，用该页面初始化WebPage实例
        @type hwnd: Window或int
        @param hwnd: Window对象或其句柄
        @rtype：WebPage
        @return: 匹配到的页面
        '''
        raise NotImplementedError()

    @property
    def Url(self):
        '''获取页面的当前URL
        @rtype: str
        @return: 页面的当前URL
        '''
        raise NotImplementedError()

    @property
    def Title(self):
        '''获取页面的当前标题
        @rtype: str
        @return: 页面的当前标题
        '''
        raise NotImplementedError()

    @property
    def ReadyState(self):
        '''获取页面的当前状态
        @rtype: int
        @return: 页面的当前状态
        '''
        raise NotImplementedError()

    @property
    def BrowserType(self):
        '''获取承载页面的浏览器的名称及版本
        @rtype: str
        @return: 浏览器的名称及版本
        '''
        raise NotImplementedError()

    def activate(self):
        '''激活承载页面的窗口'''
        raise NotImplementedError()

    def close(self):
        '''关闭承载页面的窗口'''
        raise NotImplementedError()

    def release(self):
        '''释放占用的资源'''
        raise NotImplementedError()

    def scroll(self, toX, toY):
        '''按指定的偏移量滚动页面
        @type toX: int
        @param toX: 横向滚动的偏移，负值向左，正值向右
        @type toY: int
        @param toY: 纵向滚动的偏移，负值向上，正值向下
        '''
        raise NotImplementedError()

    def execScript(self, script):
        '''在页面中执行脚本代码
        @type script: str
        @param script: 要执行的脚本代码
        @rtype: bool
        @return: True=成功；False=失败
        '''
        raise NotImplementedError()

    def waitForReady(self, timeout=60):
        '''等待页面加载完成
        @type timeout: int或float
        @param timeout: 最长等待的秒数
        '''
        raise NotImplementedError()

    def getElement(self, locator):
        '''在页面中查找元素，返回第一个匹配的元素
        @type locator: str或XPath
        @param locator: 查找条件，可以是XPath或元素ID
        @type within: WebElement
        @param within: 查找范围，为None则在整个页面中查找
        @rtype: WebElement
        @return: 查找到的元素
        '''
        raise NotImplementedError()

    def getElements(self, locator):
        '''在页面中查找元素，返回包含所有匹配的元素的列表
        @type locator: str或XPath
        @param locator: 查找条件，可以是XPath或元素Tag、Name
        @type within: WebElement
        @param within: 查找范围，为None则在整个页面中查找
        @rtype: list<WebElement>
        @return: 查找到的元素的列表
        '''
        raise NotImplementedError()


class IWebElement(object):
    '''封装Web自动化所需的页面元素相关的逻辑，对应于具体浏览器的派生类需要实现这些接口'''
    #2012-02-14    banana    创建
    def __init__(self, root, locator):
        '''构造函数
        @type root: WebElement或WebPage
        @param root: 根据locator定位的基准元素
        @type locator: XPath或str
        @param locator: 描述元素的定位符
        '''
        raise NotImplementedError()

    @property
    def Page(self):
        '''包含当前元素的WebPage对象
        @rtype: WebPage
        @return: 包含当前元素的WebPage对象
        '''
        raise NotImplementedError()

    @property
    def Attributes(self):
        '''当前元素的属性集合
        @rtype: WebElementAttributes
        @return: 元素的属性集合
        '''
        raise NotImplementedError()

    @property
    def Styles(self):
        '''当前元素的样式集合
        @rtype: WebElementStyles
        @return: 元素的样式集合
        '''
        raise NotImplementedError()

    @property
    def BoundingRect(self):
        '''当前元素在屏幕上的位置和大小
        @rtype: Rect
        @return: 元素在屏幕上的位置和大小
        '''
        raise NotImplementedError()

    @property
    def Displayed(self):
        '''当前元素是否显示
        @rtype: bool
        @return: 元素是否显示
        '''
        raise NotImplementedError()

    @property
    def InnerText(self):
        '''当前元素所包含的文本
        @rtype: str
        @return: 元素所包含的文本
        '''
        raise NotImplementedError()

    @property
    def InnerHtml(self):
        '''当前元素所包含的HTML
        @rtype: str
        @return: 元素所包含的HTML
        '''
        raise NotImplementedError()

    def scroll(self, toX, toY):
        '''按指定的偏移量滚动元素
        @type toX: int
        @param toX: 横向滚动的偏移，负值向左，正值向右
        @type toY: int
        @param toY: 纵向滚动的偏移，负值向上，正值向下
        '''
        raise NotImplementedError()

    def getElement(self, locator):
        '''在当前元素的子孙中查找元素，返回第一个匹配的元素
        @type locator: str或XPath
        @param locator: 查找条件，可以是XPath或元素ID
        @rtype: WebElement
        @return: 查找到的元素
        '''
        raise NotImplementedError()

    def getElements(self, locator):
        '''在当前元素的子孙中查找元素，返回所有匹配的元素的列表
        @type locator: str或XPath
        @param locator: 查找条件，可以是XPath或元素Tag、Name
        @rtype: list<WebElement>
        @return: 查找到的元素的列表
        '''
        raise NotImplementedError()

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
        raise NotImplementedError()

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
        raise NotImplementedError()

    def waitForText(self, value, timeout=10, interval=0.5):
        '''暂停程序执行，直到当前元素的InnerText变为特定值
        @type value: str
        @param value: 等待的文本值
        @type timeout: int或float
        @param timeout: 最多等待的秒数
        @type interval: int或float
        @param interval: 查询间隔的秒数
        '''
        raise NotImplementedError()

    def click(self, xOffset=None, yOffset=None):
        '''鼠标左键单击
        @type xOffset: int
        @param xOffset: 距离控件区域左上角的横向偏移。
        @type yOffset: int
        @param yOffset: 距离控件区域左上角的纵向偏移。
        '''
        raise NotImplementedError()

    def doubleClick(self, xOffset=None, yOffset=None):
        '''鼠标左键双击
        @type xOffset: int
        @param xOffset: 距离控件区域左上角的横向偏移。
        @type yOffset: int
        @param yOffset: 距离控件区域左上角的纵向偏移。
        '''
        raise NotImplementedError()

    def rightClick(self, xOffset=None, yOffset=None):
        '''鼠标右键单击
        @type xOffset: int
        @param xOffset: 距离控件区域左上角的横向偏移。
        @type yOffset: int
        @param yOffset: 距离控件区域左上角的纵向偏移。
        '''
        raise NotImplementedError()

    def hover(self, xOffset=None, yOffset=None):
        '''鼠标悬停
        @type xOffset: int
        @param xOffset: 距离控件区域左上角的横向偏移。
        @type yOffset: int
        @param yOffset: 距离控件区域左上角的纵向偏移。
        '''
        raise NotImplementedError()

    def drag(self, toX=None, toY=None):
        '''拖放到指定位置
        @type toX: int
        @param toX: 拖放终点距离起点的横向偏移。
        @type toY: int
        @param toY: 拖放终点距离起点的纵向偏移。
        '''
        raise NotImplementedError()
    
    def sendKeys(self, keys):
        '''发送按键命令
        @type keys: str
        @param keys: 要发送的按键
        '''
        raise NotImplementedError()

    def setFocus(self):
        '''设控件为焦点'''
        raise NotImplementedError()

if __name__ == "__main__":
    pass
