# -*-  coding: UTF-8  -*- -*- -*-
'''
Web自动化公共接口
'''
#2012-03-06    beyondli    创建

try:
    from qt4w import XPath
    from qt4w.webcontrols import WebElement,WebPage,FrameElement
except:
    from _autoweb import WebPage as BaseWebPage
    from _autoweb import WebElement as BaseWebElement
    from _autoweb import FrameElement
    from _autoweb import BrowserEnum
    from _autoweb import XPath
    from _autoweb import BrowserEnum
    
    import accessible
            
    __all__ = ["WebPage", "WebElement", "FrameElement", "BrowserEnum", "XPath"]
    
    class WebPage(BaseWebPage):
        '''封装Web自动化所需的页面相关的逻辑
        '''
        #2012-03-06    beyondli    创建
        def __init__(self, page):
            '''构造函数
            
            :type page: WebPage 或 Window
            :param page: 作为新实例基础的WebPage对象，或包含页面的Window对象
            '''
            super(WebPage, self).__init__(page)
    
        @staticmethod
        def openUrl(url, browser_type):
            '''用对应浏览器打开指定的URL，用这个新页面初始化WebPage实例
            
            :type url: str
            :param url: 要打开的URL
            :type browser_type: BrowserEnum
            :param browser_type: 要使用的浏览器，None表示系统默认浏览器（暂未实现）
            :rtype：WebPage
            :return: 新打开的页面
            '''
            return super(WebPage, WebPage).openUrl(url, browser_type)
    
        @staticmethod
        def findByUrl(url, browser_type):
            '''在已打开页面中查找与指定URL匹配的页面，用该页面初始化WebPage实例
            
            :type url: str
            :param url: 要匹配的URL
            :type browser_type: BrowserEnum
            :param browser_type: 要使用的浏览器，None表示系统默认浏览器（暂未实现）
            :rtype：WebPage
            :return: 匹配到的页面
            '''
            return super(WebPage, WebPage).findByUrl(url, browser_type)
    
        def updateLocator(self, items={}):
            '''更新locator集合
            
            :type items: dict
            :param items: 新定义的locator的集合
            '''
            return super(WebPage, self).updateLocator(items)
    
        @property
        def Controls(self):
            '''获取页面中当前已定义的控件
            
            :rtype: dict
            :return: 包含当前页面已定义控件的集合
            '''
            return super(WebPage, self).Controls
    
        @property
        def Url(self):
            '''获取页面的当前URL
            
            :rtype: str
            :return: 页面的当前URL
            '''
            return super(WebPage, self).Url
    
        @property
        def AccessibleObject(self):
            """返回AccessibleObject
            
            :rtype: tuia.accessible.AccessibleObject
            """
            #2013/10/22 aaronlai    created
            accObj = super(WebPage, self).AccessibleObject
            return accessible.AccessibleObject(accObj)
        
        @property
        def Title(self):
            '''获取页面的当前标题
            
            :rtype: str
            :return: 页面的当前标题
            '''
            return super(WebPage, self).Title
    
        @property
        def ReadyState(self):
            '''获取页面的当前状态
            
            :rtype: int
            :return: 页面的当前状态
            '''
            return super(WebPage, self).ReadyState
    
        @property
        def BrowserType(self):
            '''获取承载页面的浏览器的名称及版本
            
            :rtype: str
            :return: 浏览器的名称及版本
            '''
            return super(WebPage, self).BrowserType
    
        def activate(self):
            '''激活承载页面的窗口
            '''
            return super(WebPage, self).activate()
    
        def close(self):
            '''关闭承载页面的窗口
            '''
            return super(WebPage, self).close()
    
        def release(self):
            '''释放占用的资源
            '''
            return super(WebPage, self).release()
    
        def scroll(self, toX, toY):
            '''按指定的偏移量滚动页面
            
            :type toX: int
            :param toX: 横向滚动的偏移，负值向左，正值向右
            :type toY: int
            :param toY: 纵向滚动的偏移，负值向上，正值向下
            '''
            return super(WebPage, self).scroll(toX, toY)
    
        def execScript(self, script):
            '''在页面中执行脚本代码
            
            :type script: str
            :param script: 要执行的脚本代码
            :rtype: bool
            :return: True=成功；False=失败
            '''
            return super(WebPage, self).execScript(script)
    
        def waitForReady(self, timeout=60):
            '''等待页面加载完成
            
            :type timeout: int或float
            :param timeout: 最长等待的秒数
            '''
            return super(WebPage, self).waitForReady(timeout)
    
        def getElement(self, locator):
            '''在页面中查找元素，返回第一个匹配的元素
            
            :type locator: str或XPath
            :param locator: 作为查找条件的XPath
            :rtype: WebElement
            :return: 查找到的元素
            '''
            return super(WebPage, self).getElement(locator)
    
        def getElements(self, locator):
            '''在页面中查找元素，返回包含所有匹配的元素的列表
            
            :type locator: str或XPath
            :param locator: 作为查找条件的XPath
            :rtype: list<WebElement>
            :return: 查找到的元素的列表
            '''
            return super(WebPage, self).getElements(locator)
        
        def navigate(self, url):
            '''导航至指定URL
            
            @type url: str
            @param url: 指定导航的URL
            '''
            return super(WebPage, self).navigate(url)
    
    
    class WebElement(BaseWebElement):
        '''封装Web自动化所需的页面元素相关的逻辑
        '''
        #2012-03-06    beyondli    创建
        def __init__(self, root, locator):
            '''构造函数
            
            :type root: WebElement或WebPage
            :param root: 根据locator定位的基准元素
            :type locator: XPath或str
            :param locator: 描述元素的定位符
            '''
            super(WebElement, self).__init__(root, locator)
    
        @property
        def Page(self):
            '''包含当前元素的WebPage对象
            
            :rtype: WebPage
            :return: 包含当前元素的WebPage对象
            '''
            return super(WebElement, self).Page
    
        @property
        def AccessibleObject(self):
            """返回AccessibleObject
            
            :rtype: tuia.accessible.AccessibleObject
            :attention: 
                Not all Web Element objects support Active Accessibility. 
                Here is the list of the HTML elements that are accessible elements:
                please see MSDN about Accessible HTML Elements.
                <a/>,
                <applet/>,  
                <area/>, 
                <button>/,
                <embed/>,  
                <frame/>, 
                <img/>, 
                <input type='button'/>, 
                <input type='reset'/>,
                <input type='submit'/>,
                <input type='checkbox'/>, 
                <input type='image'/>, 
                <input type='password'/>, 
                <input type='radio'/>,
                <input type='text'/>.
                <marquee/>,  <-- 仅适用于MSIE3以后内核
                <object/>, 
                <panel/>
                <select/>, 
                <table/>,
                <textarea/> 
                <textrange/>,
                <td/>, 
                <th/>, 
                <window/>
                
                About Techniques for Web Content Accessibility, please see:
                    HTML Techniques for Web Content Accessibility Guidelines 1.0
                    url: http://www.w3.org/TR/WCAG10-HTML-TECHS
                    HTML Techniques for Web Content Accessibility Guidelines 2.0
                    url: http://www.w3.org/TR/WCAG20-TECHS
                
            """
            #2013/10/22 aaronlai    created
            accObj = super(WebElement, self).AccessibleObject
            return accessible.AccessibleObject(accObj)
        
        @property
        def Attributes(self):
            '''当前元素的属性集合
            
            :rtype: WebElementAttributes
            :return: 元素的属性集合
            '''
            return super(WebElement, self).Attributes
    
        @property
        def Styles(self):
            '''当前元素的样式集合
            
            :rtype: WebElementStyles
            :return: 元素的样式集合
            '''
            return super(WebElement, self).Styles
    
        @property
        def BoundingRect(self):
            '''当前元素在屏幕上的位置和大小
            
            :rtype: Rect
            :return: 元素在屏幕上的位置和大小
            '''
            return super(WebElement, self).BoundingRect
    
        @property
        def Displayed(self):
            '''当前元素是否显示
            
            :rtype: bool
            :return: 元素是否显示
            '''
            return super(WebElement, self).Displayed
    
    
        @property
        def Focused(self):
            '''当前元素是否具有焦点
            
            :rtype: bool
            :return: 元素是否具有焦点
            '''
            return super(WebElement, self).Focused
    
    
        @property
        def InnerText(self):
            '''当前元素所包含的文本
            
            :rtype: str
            :return: 元素所包含的文本
            '''
            return super(WebElement, self).InnerText
    
        @InnerText.setter
        def InnerText(self, text):
            super(WebElement, self.__class__).InnerText.fset(self, text)
        
        @property
        def InnerHtml(self):
            '''当前元素所包含的HTML
            
            :rtype: str
            :return: 元素所包含的HTML
            '''
            return super(WebElement, self).InnerHtml
    
        @InnerHtml.setter
        def InnerHtml(self, html):
            super(WebElement, self.__class__).InnerHtml.fset(self, html)
    
        def exist(self):
            '''检查元素是否有效
            
            :rtype: bool
            :return: 定位成功为True，不成功为False
            '''
            try:
                self._obj
                return True
            except:
                return False
    
        def scroll(self, toX, toY):
            '''按指定的偏移量滚动元素
            
            :type toX: int
            :param toX: 横向滚动的偏移，负值向左，正值向右
            :type toY: int
            :param toY: 纵向滚动的偏移，负值向上，正值向下
            '''
            return super(WebElement, self).scroll(toX, toY)
    
        def getElement(self, locator):
            '''在当前元素的子孙中查找元素，返回第一个匹配的元素
            
            :type locator: str或XPath
            :param locator: 作为查找条件的XPath
            :rtype: WebElement
            :return: 查找到的元素
            '''
            return super(WebElement, self).getElement(locator)
    
        def getElements(self, locator):
            '''在当前元素的子孙中查找元素，返回所有匹配的元素的列表
            
            :type locator: str或XPath
            :param locator: 作为查找条件的XPath
            :rtype: list<WebElement>
            :return: 查找到的元素的列表
            '''
            return super(WebElement, self).getElements(locator)
    
        def waitForAttribute(self, name, value, timeout=5, interval=0.5):
            '''暂停程序执行，直到当前元素的指定属性变为特定值
            
            :type name: str
            :param name: 等待的属性名称
            :type value: obj
            :param value: 等待的属性值，无论何类型都先转为str再处理
            :type timeout: int或float
            :param timeout: 最多等待的秒数
            :type interval: int或float
            :param interval: 查询间隔的秒数
            '''
            return super(WebElement, self).waitForAttribute(name, value, timeout, interval)
    
        def waitForStyle(self, name, value, timeout=5, interval=0.5):
            '''暂停程序执行，直到当前元素的指定样式变为特定值
            
            :type name: str
            :param name: 等待的样式名称
            :type value: obj
            :param value: 等待的样式值，无论何类型都先转为str再处理
            :type timeout: int或float
            :param timeout: 最多等待的秒数
            :type interval: int或float
            :param interval: 查询间隔的秒数
            '''
            return super(WebElement, self).waitForStyle(name, value, timeout, interval)
    
        def waitForText(self, value, timeout=5, interval=0.5):
            '''暂停程序执行，直到当前元素的InnerText变为特定值
            
            :type value: str
            :param value: 等待的文本值
            :type timeout: int或float
            :param timeout: 最多等待的秒数
            :type interval: int或float
            :param interval: 查询间隔的秒数
            '''
            return super(WebElement, self).waitForText(value, timeout, interval)
    
        def click(self, xOffset=None, yOffset=None):
            '''鼠标左键单击
            
            :type xOffset: int
            :param xOffset: 距离控件区域左上角的横向偏移。
            :type yOffset: int
            :param yOffset: 距离控件区域左上角的纵向偏移。
            '''
            return super(WebElement, self).click(xOffset, yOffset)
    
        def doubleClick(self, xOffset=None, yOffset=None):
            '''鼠标左键双击
            
            :type xOffset: int
            :param xOffset: 距离控件区域左上角的横向偏移。
            :type yOffset: int
            :param yOffset: 距离控件区域左上角的纵向偏移。
            '''
            return super(WebElement, self).doubleClick(xOffset, yOffset)
    
        def rightClick(self, xOffset=None, yOffset=None):
            '''鼠标右键单击
            
            :type xOffset: int
            :param xOffset: 距离控件区域左上角的横向偏移。
            :type yOffset: int
            :param yOffset: 距离控件区域左上角的纵向偏移。
            '''
            return super(WebElement, self).rightClick(xOffset, yOffset)
    
        def hover(self, xOffset=None, yOffset=None):
            '''鼠标悬停
            
            :type xOffset: int
            :param xOffset: 距离控件区域左上角的横向偏移。
            :type yOffset: int
            :param yOffset: 距离控件区域左上角的纵向偏移。
            '''
            return super(WebElement, self).hover(xOffset, yOffset)
    
        def drag(self, toX=None, toY=None):
            '''拖放到指定位置
            
            :type toX: int
            :param toX: 拖放终点距离起点的横向偏移。
            :type toY: int
            :param toY: 拖放终点距离起点的纵向偏移。
            '''
            return super(WebElement, self).drag(toX, toY)
        
        def sendKeys(self, keys):
            '''发送按键命令
            
            :type keys: str
            :param keys: 要发送的按键
            '''
            return super(WebElement, self).sendKeys(keys)
    
        def setFocus(self):
            '''设控件为焦点
            '''
            return super(WebElement, self).setFocus()
    
    
    if __name__ == "__main__":
        import time
    
        class QunLoginPage(WebPage):
            def __init__(self, page):
                super(QunLoginPage, self).__init__(page)
                self.updateLocator({
                    'FRAME1'    : {'type':FrameElement, 'root':self,
                                   'locator':XPath("//iframe")},
                    '普通登录'   : {'type':WebElement, 'root':"@FRAME1",
                                   'locator':XPath("//div[@id='web_login']")},
                    '切换登录模式': {'type':WebElement, 'root':"@FRAME1",
                                   'locator':XPath("//div[@id='switch']//a")},
                    '用户名'     : {'type':WebElement, 'root':"@FRAME1",
                                   'locator':XPath("//input[@id='u']")},
                    '密码'       : {'type':WebElement, 'root':"@FRAME1",
                                   'locator':XPath("//input[@id='p']")},
                    '登录按钮'   : {'type':WebElement, 'root':"@FRAME1",
                                   'locator':XPath("//input[@id='login_button']")},
                    '登录按钮2'  : {'type':WebElement, 'root':'@FRAME1',
                                   'locator':XPath("//iframe//input[@id='loginbtn']")},
                })
    
        class QunSpacePage(WebPage):
            def __init__(self, param):
                if isinstance(param, WebPage):
                    page = param
                else:
                    page = WebPage.openUrl("qun.qq.com", param)
                super(QunSpacePage, self).__init__(page)
                self.updateLocator({
                    '退出'   : {'type':WebElement, 'root':self,
                               'locator':XPath("//A[@title='退出']")},
                    '确定按钮': {'type':WebElement, 'root':self,
                               'locator':XPath("//button[text()='确定']")},
                })
    
        browsers = [BrowserEnum.Chrome,
                    #BrowserEnum.IE,
                    ]
        for browser in browsers:
            page = QunSpacePage(browser)
            if not page.Controls['退出'].exist():
                page = QunLoginPage(page)
                page.Controls['登录按钮2'].hover()
                if not page.Controls['普通登录'].Displayed:
                    page.Controls['切换登录模式'].drag(100, 100)
                    page.Controls['切换登录模式'].click()
                page.Controls['用户名'].Attributes['value'] = 'lc_crazy2000@163.com'
                print "Username is : ", page.Controls['用户名'].Attributes['value']
                page.Controls['密码'].sendKeys('letscan')
            print "Color is : ", page.Controls['登录按钮'].Styles['font-family']
            page.Controls['登录按钮'].click()
            page = QunSpacePage(page)
            page.waitForReady()

        print page
        el = page.getElements("//div[@class='helpArea']//a")
        for e in el:
            e.hover()
        page.Controls['退出'].click()
        page.Controls['确定按钮'].click()

        time.sleep(3) # 此处演示用，正式脚本应避免使用sleep()，而使用wait系列方法
        page.close()
