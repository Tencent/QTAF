# -*-  coding: UTF-8  -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
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
__modified__ = '2012.12.19'
__description__ = '3.x'
__version__ = '3.5.2.2'
__author__ = 'cherry(张勇军)'
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
import os, re, sys, time, types, locale, win32com.client
try:
    from comtypes import IServiceProvider, COMError
    from comtypes.gen.Accessibility import IAccessible
    from tuia.accessible import AccessibleObject
except ImportError:
    pass
        
sys.path.append(os.path.realpath('webcontrol'))
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
# -*-
try    : from ..base import IWebPage
except : from   base import IWebPage
try    : from ..base import IWebElement
except : from   base import IWebElement
try    : from ..util import WebElementAttributes, WebElementStyles
except : from   util import WebElementAttributes, WebElementStyles
# -*-
from ielib import SendKeys
from ielib import win32ext
from ielib import iedriver
from ielib import ietips  # 此tips扩展仅辅助使用，建议使用tuia。
from tuia.keyboard import Keyboard

RuntimeDefaultEncoding = 'UTF-8'
LocalCode, LocalEncoding = locale.getdefaultlocale()
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-


# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- Util

class Util:
    
    Timeout = 3
    Timestep = 0.2
    
    @classmethod
    def clear_internet_temporary_files(cls):
        '''@desc: 清除IE临时文件'''
        os.system("RunDll32.exe InetCpl.cpl,ClearMyTracksByProcess 8")
    
    @classmethod
    def clear_internet_cookies(cls):
        '''@desc: 清除IE cookies'''
        os.system("RunDll32.exe InetCpl.cpl,ClearMyTracksByProcess 2")
    
    @classmethod
    def clear_internet_history(cls):
        '''@desc: 清除IE历史记录 history'''
        os.system("RunDll32.exe InetCpl.cpl,ClearMyTracksByProcess 1")
    
    @classmethod
    def clear_internet_formdata(cls):
        '''@desc: 清除IE表单数据 Form Data'''
        os.system("RunDll32.exe InetCpl.cpl,ClearMyTracksByProcess 16")
    
    @classmethod
    def clear_internet_passwords(cls):
        '''@desc: 清除IE记录密码 Passwords'''
        os.system("RunDll32.exe InetCpl.cpl,ClearMyTracksByProcess 32")
    
    @classmethod
    def clear_internet_all_cache(cls):
        '''@desc: 清除IE全部缓存'''
        os.system("RunDll32.exe InetCpl.cpl,ClearMyTracksByProcess 255")
    
    @classmethod
    def clear_internet_all_cache2(cls):
        '''@desc: 清除IE全部缓存(Also delete files and settings stored by add-ons)'''
        os.system("RunDll32.exe InetCpl.cpl,ClearMyTracksByProcess 4351")
    
    @classmethod
    def add_trusted_sites(cls, url_string):
        '''@desc: 添加IE可信站点'''
        win32ext.IERegistry.add_trusted_sites(url_string)
    
    @classmethod
    def del_trusted_sites(cls, url_string):
        '''@desc: 删除IE可信站点'''
        win32ext.IERegistry.del_trusted_sites(url_string)
    
    @classmethod
    def taskkill_all_ie(cls):
        '''@desc: 清杀IE全部进程'''
        os.popen("taskkill /F /IM iexplore.exe")
    
    @classmethod
    def get_processes(cls):
        '''@desc: 获取系统当前进程列表'''
        return [(process.Properties_('ProcessId').Value, process.Properties_('Name').Value) for process in win32com.client.GetObject('winmgmts:').InstancesOf('Win32_Process')]
    
    @classmethod
    def process_exists_byname(cls, process_name):
        '''@desc: 通过进程名查询进程是否存在'''
        objs = win32com.client.GetObject('winmgmts:').ExecQuery('select * from Win32_Process where Name="%s"' % process_name)
        return len(objs) > 0
    
    @classmethod
    def process_exists_bypid(cls, process_id):
        '''@desc: 通过进程ID查询进程是否存在'''
        processes = cls.get_processes()
        for pid, name in processes:
            if pid == int(process_id) : return True
        return False
    
    @classmethod
    def waitForProcessIdNotExists(cls, process_id, timeout=Timeout, timestep=Timestep):
        begin = time.time()
        while time.time() - begin <= timeout:
            if not cls.process_exists_bypid(process_id) : return True
            time.sleep(timestep)
        return not cls.process_exists_bypid(process_id)

# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- XPath

class XPath(str):
    '''@desc: XPath类'''
    def __init__(self, obj):str.__init__(self)

# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- WebElements

class WebElements(dict):
    '''@desc: WebElements类'''
    
    def __getitem__(self, key):
        if self.has_key(key):
            data = self.get(key)
            if type(data) == types.DictType:
#                if data.has_key('instance'):
#                    instance = data.get('instance')
#                    instance.__locate__()
#                    return instance
                instance = self.__constructor__(data)
#                data.update({'instance':instance})
                return instance
        raise KeyError(key)
    
    def __constructor__(self, params):
        cls = params.get('class') or params.get('type') or WebElement
        if type(cls) == types.TypeType:
            root = params.get('root')
            locator = params.get('locator')
            if isinstance(root, basestring):
                root = re.sub('^@', '', root)
                root = self[root]
            if type(root) == types.InstanceType or root is None or locator != None:
                return cls(root=root, locator=locator)
        raise Exception('structural error: %s' % params)

# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- WebElementAttributes
'''
class WebElementAttributes(object):
    def __init__(self, getitem, setitem, getitems):
        self.getitem, self.setitem, self.getitems = getitem, setitem, getitems
    
    def __str__(self):return self.getitems()
    
    def __getitem__(self, key):return self.getitem(key)
    
    def __setitem__(self, key, value):self.setitem(key, value)
'''
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- WebElementStyles
'''
class WebElementStyles(object):
    def __init__(self, getitem, setitem, getitems):
        self.getitem, self.setitem, self.getitems = getitem, setitem, getitems
    
    def __str__(self):return self.getitems()
    
    def __getitem__(self, key):return self.getitem(key)
    
    def __setitem__(self, key, value):self.setitem(key, value)
'''
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- WebPageScroll

class WebPageScroll(object):
    '''@desc: 页面的滚动条'''
    def __init__(self, page):self.page = page

    @property
    def ScrollInfo(self):
        '''@desc: 获取页面滚动条信息'''
        return eval(self.page.driver.get_current_window_scrollInfo(self.page.xpaths))
    
    @property
    def ScrollTop(self):
        '''@desc: 获取页面纵向滚动条信息'''
        return self.ScrollInfo['scrollTop']
    
    @ScrollTop.setter
    def ScrollTop(self, value=0):
        '''
        @desc: 设置页面纵向滚动条位置
        @param : value in<int> 滚动条偏移像素值
        '''
        self.page.driver.set_current_window_scrollTop(self.page.xpaths, value)
    
    @property
    def ScrollLeft(self):
        '''@desc: 获取页面横向滚动条信息'''
        return self.ScrollInfo['scrollLeft']
    
    @ScrollLeft.setter
    def ScrollLeft(self, value=0):
        '''
        @desc: 设置页面横向滚动条位置
        @param : value in<int> 滚动条偏移像素值
        '''
        self.page.driver.set_current_window_scrollLeft(self.page.xpaths, value)

# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- WebPage

class WebPage(IWebPage):
    '''@desc: (主要类)WebPage类'''
    
    Timeout = 10
    Timestep = 0.2
    
    def __init__(self, HWnd):
        self.driver, self.xpaths = None, ''
        if isinstance(HWnd, int) : self.driver = iedriver.IEDrivers.get(HWnd)
        if hasattr(HWnd, 'HWnd') : self.driver = iedriver.IEDrivers.get(HWnd.HWnd)
        if self.driver is None or not isinstance(self.driver, iedriver.IEDriver):raise Exception('is not a valid WebPage.')
        self.__init_element_cls_mapping__()
        self.Controls = self.Elements = WebElements()
    
    def updateLocator(self, items={}):
        '''
        @desc: 附加子控件集
        # 示例
        #self.updateLocator({
            #'某按钮1':{'type':WebElement,  root=WebPage或WebElement, locator=XPath("//from[@id='login']//button[@id='someBtn']")    },
            #'某按钮2':{'type':WebElement,  root=WebPage或WebElement, locator=XPath("//from[@id='login']//button[@id='someSubmit']") },
            #'某按钮3':{'class':WebElement, root=WebPage或WebElement, locator=XPath("//from[@id='login']//button[@id='someReset']")  },
        #})
        '''
        self.Controls.update(items)
    
    def __init_element_cls_mapping__(self):
        self.element_cls_mapping = {
            'default'   : WebElement,
            'frame'     : FrameElement,
            'iframe'    : FrameElement,
            # 'input'     : {
            #               'submit'    : HtmlInputSubmit,
            #               'password'  : HtmlInputPassword,
            #               'checkbox'  : HtmlInputCheckbox,
            #               'radio'     : HtmlInputRadio,
            #               'text'      : HtmlInputText,
            #               'file'      : HtmlInputFile,
            #              },
            # 'select'    : HtmlSelect,
            # 'button'    : HtmlButton
        }
    
    def __get_element_cls__(self, ele):
        cls = self.element_cls_mapping.get(ele.nodeName.lower())
        # if 'input' == ele.nodeName.lower() and type(cls) == types.DictType : cls = cls.get(ele.type.lower())
        if cls is None : cls = self.element_cls_mapping.get('default')
        return cls
    
    # -*- -*- -*-
    
    @classmethod
    def _clear_disk_cache(cls):
        Util.clear_internet_all_cache2()
    
    @classmethod
    def openUrl(cls, url='about:blank'):
        '''
        @desc:   (类方法)以本机安装的IE(6|7|8|9|10)打开url页面，并返回WebPage实例对象。
        @param:  url in<str> - url地址
        @return: object<WebPage>
        '''
        driver = iedriver.IEDrivers.open_url_by_ie(url)
        return cls(driver.ies_handle)
    
    @classmethod
    def findByHWnd(cls, HWnd):return cls(HWnd)
    
    @classmethod
    def findByUrl(cls, url, onlyIE=True, index=1, timeout=None, timestep=None):
        '''
        @desc:       (类方法)查找匹配url的页面(支持正则)，并返回WebPage实例对象。
        @param: 
            url      in<str>         - 页面的url(支持正则)
            onlyIE   in<bool>        - True=仅搜索IE浏览器；False=全面搜索，含内嵌IE；
            index    in<int>         - 多个相同页面时，匹配第几个。默认=1(按启动时间先后排序)
            timeout  in<int|float>   - 默认查找5秒后超时
            timestep in<int|float>   - 在超时期间，间隔多少秒查找一次(建议大于0.2秒，查找密度太高消耗CPU资源多)
        @return:     object<WebPage>
        '''
        if url != None:
            timeout = timeout or cls.Timeout
            timestep = timestep or cls.Timestep
            url = url.decode(RuntimeDefaultEncoding)
            driver = iedriver.IEDrivers.find(url, None, onlyIE, index, timeout, timestep)
            if driver:return cls(driver.ies_handle)
    
    @classmethod
    def findByTitle(cls, title, onlyIE=True, index=1, timeout=None, timestep=None):
        '''
        @desc:       (类方法)查找匹配title的页面(支持正则)，并返回WebPage实例对象。
        @param: 
            title    in<str>         - 页面的title(支持正则)
            onlyIE   in<bool>        - True=仅搜索IE浏览器；False=全面搜索，含内嵌IE；
            index    in<int>         - 多个相同页面时，匹配第几个。默认=1(按启动时间先后排序)
            timeout  in<int|float>   - 默认查找5秒后超时
            timestep in<int|float>   - 在超时期间，间隔多少秒查找一次(建议大于0.2秒，查找密度太高消耗CPU资源多)
        @return:     object<WebPage>
        '''
        if title != None:
            timeout = timeout or cls.Timeout
            timestep = timestep or cls.Timestep
            title = title.decode(RuntimeDefaultEncoding)
            driver = iedriver.IEDrivers.find(None, title, onlyIE, index, timeout, timestep)
            if driver:return cls(driver.ies_handle)
    
    def getFramePage(self, locator):
        '''@desc: 获取IFrame|Frame内的WebPage实例对象。'''
        return FrameElement(self, locator).FramePage

    # -*- -*- -*-
    
    def __getattribute__(self, name):
        if name in ['Url', 'Title', 'ReadyState', 'Scroll', 'navigate', 'back', 'forward', 'reload', 'waitForReady', 'execScript']:
            driver = object.__getattribute__(self, 'driver')
            xpaths = object.__getattribute__(self, 'xpaths')
            # -*- -*- -*-
            if name in ['Url', 'Title', 'ReadyState'] and (xpaths == None or len(xpaths) == 0):
                if name == 'Url'        : return object.__getattribute__(self, '_TopUrl')
                if name == 'Title'      : return object.__getattribute__(self, '_TopTitle')
                if name == 'ReadyState' : return object.__getattribute__(self, '_TopReadyState')
            # -*- -*- -*-
            if bool(driver) : driver.cross_in_by_xpaths(xpaths)
        return object.__getattribute__(self, name)
    
    # -*- -*- -*-
    
    @property
    def _IEFPID(self):
        '''
        @desc: 获取"IEFrame"的进程ID(用于IE8以上版本的多进程模型)
        @return: <int>
        '''
        return self.driver.ief_processID
    
    @property
    def _IESPID(self):
        '''
        @desc: 获取"Internet Explorer_Server"的进程ID
        @return: <int>
        '''
        return self.driver.ies_processID
    
    @property
    def _IEFRect(self):
        '''
        @desc: 获取"Internet Explorer_Server"控件所在Win32Window的坐标以及高宽
        @return: <dict>
        '''
        return self.driver.get_ief_rect()
    
    @property
    def _IESRect(self):
        '''
        @desc: 获取"Internet Explorer_Server"控件的坐标以及高宽
        @return: <dict>
        '''
        return self.driver.get_ies_rect()
    
    @property
    def HWnd(self):
        return self.driver.ies_handle
    
    @property
    def BoundingRect(self):
        '''
        @desc: 获取"Internet Explorer_Server"控件的坐标以及高宽
        @return: <dict>
        '''
        return self.driver.get_ies_rect()
    
    @property
    def AccessibleObject(self):
        """返回AccessibleObject
        
        :rtype: tuia.accessible.AccessibleObject
        """
        #2013/10/22 pear    created
        self.driver.__init_top_com_objs__()
        isp = self.driver.com_objs['doc2'].QueryInterface(IServiceProvider)
        ia = isp.QueryService(IAccessible._iid_, IAccessible)
        self.release()
        if ia:
            return AccessibleObject(ia)
        return None    
    
    # -*- -*- -*-
    
    @property
    def _TopUrl(self):
        '''
        @desc: 获取 top 页面的 url (为了高性能获取顶层页面数据)
        @return: <str|None>
        '''
        result = self.driver.get_top_url()
        return result.encode(RuntimeDefaultEncoding)
    
    @property
    def _TopTitle(self):
        '''
        @desc: 获取 top 页面的 title (为了高性能获取顶层页面数据)
        @return: <str|None>
        '''
        result = self.driver.get_top_title()
        return result.encode(RuntimeDefaultEncoding)
    
    @property
    def _TopReadyState(self):
        '''
        @desc: 获取 top 页面 Document.readyState 加载状态 (为了高性能获取顶层页面数据)
        @return: <str|None>
        '''
        result = self.driver.get_top_readyState()
        return result.encode(RuntimeDefaultEncoding)
    
    @property
    def Url(self):
        '''
        @desc: 获取当前页面的URL
        @return: <str>
        '''
        self.waitForReady()
        url = self.driver.doc2.url
        if url : return url.encode(RuntimeDefaultEncoding)
    
    @property
    def Title(self):
        '''
        @desc: 获取当前页面HTML的Title
        @return: <str>
        '''
        self.waitForReady()
        title = self.driver.doc2.title
        if title : return title.encode(RuntimeDefaultEncoding)
    
    @property
    def ReadyState(self):
        '''
        @desc: 获取 Current Document加载状态
        @return: <str>
        '''
        readyState = self.driver.doc2.readyState
        return readyState.encode(RuntimeDefaultEncoding)
    
    @property
    def BrowserType(self):
        '''
        @desc: 获取当前浏览器类型和版本信息（注意IE9后的版本可以切换内核）
        @return: <str>
        '''
        
        self.waitForReady()
        userAgent = self.driver.win2.navigator.userAgent
        if userAgent.find("Gecko") >= 0:
            return "MSIE11";
        return re.search('MSIE\s(\d+|\.)+(?=;)', userAgent).group().encode(RuntimeDefaultEncoding)
        
        #self.waitForReady()
        #userAgent = self.driver.win2.navigator.userAgent
        #return re.search('MSIE\s(\d+|\.)+(?=;)', userAgent).group().encode(RuntimeDefaultEncoding)
    
    @property
    def Scroll(self):
        '''@desc: 获取页面滚动条'''
        if not hasattr(self, 'WebPageScroll'):self.WebPageScroll = WebPageScroll(self)
        return self.WebPageScroll
    

    @property
    def ScreenWidth(self):
        return self.driver.doc2.parentWindow.screen.width;

    @property
    def ScreenHeight(self):
        return self.driver.doc2.parentWindow.screen.height;


    # -*- -*- -*- 辅助接口操作
    
    def exist(self):
        '''
        @desc: 当前页面是否有效的存在于Win32
        @return: <bool>
        '''
        return win32ext.Handle.is_valid(self.driver.ies_handle)
    
    def activate(self):
        '''@desc: 激活容纳页面的Win32Window窗口'''
        win32ext.IEHandle.active(self.driver.ief_handle, self.driver.ies_handle)
        time.sleep(0.2)
    
    def navigate(self, url):
        '''
        @desc: 导航至指定URL
        @param:url in<str>
        '''
        if "://" not in url :
            url = "http://" + url

        self.driver.win2.navigate(url)
    
    def back(self):
        '''@desc: 浏览记录回退(如果有记录，等效于浏览器工具栏上的后退按钮)'''
        self.driver.win2.history.back()
    
    def forward(self):
        '''@desc: 浏览记录前进(如果有记录，等效于浏览器工具栏上的前进按钮)'''
        self.driver.win2.history.forward()
    
    def reload(self):
        '''@desc: 刷新页面(等效于按F5刷新浏览器请求的网页)'''
        self.driver.win2.location.reload(True)
    
    def max(self):
        '''@desc: 容纳页面的Win32Window窗口最大化'''
        win32ext.Handle.set_style(self.driver.ief_handle, 1)
        time.sleep(0.2)
    
    def min(self):
        '''@desc: 容纳页面的Win32Window窗口最小化'''
        win32ext.Handle.set_style(self.driver.ief_handle, 2)
        time.sleep(0.2)
    
    def restore(self):
        '''@desc: 容纳页面的Win32Window窗口复位'''
        win32ext.Handle.set_style(self.driver.ief_handle, 7)
        time.sleep(0.2)
    
    def close(self):
        '''
        @desc: 关闭当前页面或释放资源
        #      此接口有两处应用，一处是关闭浏览器，另外一处非主动关闭时的释放资源。
        '''
        #2014/01/06 pear    修改关闭页面的方式，activate函数和快捷键方式有时失效
        self.driver.release()
#        self.activate()
#        SendKeys.SendKeys('^{w}')
        scriptClosePage = """
            window.opener=null;
            window.open('','_self');
            window.close();
        """
        self.execScript(scriptClosePage)
        
        time.sleep(1)
        # if not Util.waitForProcessIdNotExists(self.driver.ies_processID):os.popen("taskkill /F /PID %s /T" % self.driver.ies_processID)
        if not Util.waitForProcessIdNotExists(self.driver.ies_processID):os.popen("taskkill /F /PID %s" % self.driver.ies_processID)
        time.sleep(2)
    
    def release(self):
        '''@desc: 释放资源'''
        self.driver.release()
    
    # -*- -*- -*-
    
    def waitForLoading(self, timeout=15, timestep=Timestep):
        '''
        @desc: 等待页面再次导航，状态变为loading，不可操作。
        '''
        start = time.time()
        while time.time() - start < timeout: 
            if 'loading' == self.ReadyState : break
            time.sleep(timestep)
        return 'loading' == self.ReadyState
    
    def waitForReady(self, timeout=60, timestep=Timestep):
        '''
        @desc: 等待页面加载就绪(默认60秒)
        @param: 
            timeout  in<int|float> 等待超时秒
            timestep in<int|float> 轮询步骤秒
        @return: bool
        '''
        self.waitForLoading(0.5)
        start = time.time()
        while time.time() - start < timeout: 
            if 'complete' == self.ReadyState : break
            time.sleep(timestep)
        return 'complete' == self.ReadyState
    
    def execScript(self, script, encoding=RuntimeDefaultEncoding):
        '''
        @desc: 注入JavaScript(代码会驻留，不能捕获异常，如异常则返回False。如要捕获异常请用JavaScript的try语句块输出至特定的DOM内)
        @param:
            script   in<str> JavaScript String
            encoding in<str> 传入JavaScript的字符编码
        @return: <bool> True=成功；False=失败；
        '''
        return self.driver.inject(script.decode(encoding))
    
    def getElement(self, xpaths, timeout=None, timestep=None, auto_mapping=True):
        '''
        @desc: 单一Element元素XPath选择器
        @param : 
            xpaths       in <XPath|str|list>  - 需要定位的WebElement对象的XPaths。
                                              - 例0(腾讯首页新闻链接)：XPath("//a[text()='新闻']")
                                              - 例1(腾讯首页新闻链接)："//a[text()='新闻']"
                                              - 例2(群空间的登录按钮)："//iframe[@id='loginFrameEmbed']//iframe[@id='xui']//input[@id='loginbtn']"
                                              - 例3(群空间的登录按钮)：["//iframe[@id='loginFrameEmbed']", "//iframe[@id='xui']", "//input[@id='loginbtn']"]
            timeout      in <int|float>       - 超时值
            timestep     in <int|float>       - 循环查找间隔时间
            auto_mapping in <bool>            - 是否自动映射，返回高级对象。关闭则直接返回COM对象。
        '''
        xpaths = self.xpaths + xpaths
        timeout = timeout or self.Timeout
        timestep = timestep or self.Timestep
        ele = self.driver.xpath_select(xpaths=xpaths, timeout=timeout, timestep=timestep)
        if ele:
            if auto_mapping:return self.__get_element_cls__(ele)(root=self, locator=xpaths)
            return ele

    def getElements(self, xpaths, timeout=None, timestep=None, auto_mapping=True):
        '''
        @desc: WebElement元素列表集XPath选择器(集合各元素按页面加载顺序排序)
        @param : 
            xpaths       in <XPath|str|list>  - 需要定位的WebElement对象的XPaths。
                                              - 例0(腾讯首页新闻链接)：XPath("//a[text()='新闻']")
                                              - 例1(腾讯首页新闻链接)："//a[text()='新闻']"
                                              - 例2(群空间的登录按钮)："//iframe[@id='loginFrameEmbed']//iframe[@id='xui']//input[@id='loginbtn']"
                                              - 例3(群空间的登录按钮)：["//iframe[@id='loginFrameEmbed']", "//iframe[@id='xui']", "//input[@id='loginbtn']"]
            timeout      in <int|float>       - 超时值
            timestep     in <int|float>       - 循环查找间隔时间
            auto_mapping in <bool>            - 是否自动映射，返回高级对象。关闭则直接返回COM对象。
        '''
        xpaths = self.xpaths + xpaths
        timeout = timeout or self.Timeout
        timestep = timestep or self.Timestep
        eles = []
        results = self.driver.xpath_select_list(xpaths=xpaths, timeout=timeout, timestep=timestep)
        if len(results) > 0:
            for (ele, expaths) in results:
                if auto_mapping:eles.append(self.__get_element_cls__(ele)(root=self, locator=expaths))
        return eles
    
    # -*- -*- -*- 辅助提示框
    
    def get_alert_window(self, timeout=None, timestep=None):
        '''
        @desc: 有则返回Alert实例对象，无则返回None。支持IE8以及后续版本
        @param: timeout  <int|float> 延迟直到有alert出现的，延迟超时值
                timestep <int|float> 每间隔多少时间检测一次alert
        @return: <IEAlert>|<None>
        '''
        timeout = timeout or self.Timeout
        timestep = timestep or self.Timestep
        obj = ietips.IEAlert(processid=self.driver.ies_processID, index=1, timeout=timeout, timestep=timestep)
        if obj.exist():return obj
    
    def get_confirm_window(self, timeout=None, timestep=None):
        '''
        @desc: 有则返回Alert实例对象，无则返回None。支持IE8以及后续版本
        @param: timeout  <int|float> 延迟直到有alert出现的，延迟超时值
                timestep <int|float> 每间隔多少时间检测一次alert
        @return: <Confirm>|<None>
        '''
        timeout = timeout or self.Timeout
        timestep = timestep or self.Timestep
        obj = ietips.IEConfirm(processid=self.driver.ies_processID, index=1, timeout=timeout, timestep=timestep)
        if obj.exist():return obj
    
    def get_prompt_window(self, timeout=None, timestep=None):
        '''
        @desc: 有则返回Prompt实例对象，无则返回None。支持IE8以及后续版本
        @param: timeout  <int|float> 延迟直到有alert出现的，延迟超时值
                timestep <int|float> 每间隔多少时间检测一次alert
        @return: <Prompt>|<None>
        '''
        timeout = timeout or self.Timeout
        timestep = timestep or self.Timestep
        obj = ietips.IEPrompt(processid=self.driver.ies_processID, index=1, timeout=timeout, timestep=timestep)
        if obj.exist():return obj
    
    # -*- -*- -*- 辅助鼠标
    
    def _get_ies_center_pos(self, x=None, y=None):
        '''
        @desc: 获取(Internet Explorer_Server控件)的中心点坐标
        @param : 
            x in<int> - 如果x=None则计算x的中心点，否则不计算。
            y in<int> - 如果y=None则计算y的中心点，否则不计算。
        @return: (x<int>, y<int>)
        '''
        ies_rect = self._IESRect
        if x == None : x = ies_rect.get('width') / 2
        if y == None : y = ies_rect.get('height') / 2
        return x, y
    
    def mouse_move(self, x=None, y=None, locus=True):
        '''
        @desc: 鼠标移动
        @param : 
            x     in<int>  X坐标(相对页面，默认=None则视为页面中央)
            y     in<int>  Y坐标(相对页面，默认=None则视为页面中央)
            locus in<bool> 启动轨迹
        '''
        self.activate()
        x, y = self._get_ies_center_pos(x, y)
        win32ext.Mouse.evt_moveIn(handle=self.driver.ies_handle, pos=(x, y), locus=locus)
    
    def mouse_click(self, x=None, y=None, locus=True, key=0, dbl=False):
        '''
        @desc: 点击页面
        @param : 
            x     in<int>  - X坐标(相对页面，默认=None则视为页面中央)
            y     in<int>  - Y坐标(相对页面，默认=None则视为页面中央)
            locus in<bool> - 启动轨迹
            key   in<int>  - 默认 = Left = 0; Right = 1; Middle = 2
            dbl   in<bool> - 是否双击
        '''
        self.activate()
        x, y = self._get_ies_center_pos(x, y)
        win32ext.Mouse.evt_clickIn(handle=self.driver.ies_handle, pos=(x, y), locus=locus, key=key, dbl=dbl)
    
    def mouse_drag(self, x=None, y=None, key=0, locus=True):
        '''
        @desc: 鼠标左键按下(不释放)。默认鼠标按下(不释放)于页面的中央，否则按照传入的坐标按下(不释放)(相对页面)。与MouseDrop配合使用，实现拖拽。
        @param : 
            x     in<int>  X坐标(相对页面，默认=None则视为页面中央)
            y     in<int>  Y坐标(相对页面，默认=None则视为页面中央)
            key   in<int>  默认 = Left = 0; Right = 1; Middle = 2
            locus in<bool> 启动轨迹
        '''
        self.activate()
        x, y = self._get_ies_center_pos(x, y)
        win32ext.Mouse.evt_dragIn(handle=self.driver.ies_handle, pos=(x, y), locus=locus, key=key)
    
    def mouse_drop(self, x=None, y=None, key=0, locus=True):
        '''
        @desc: 鼠标左键释放。默认鼠标释放于页面的中央，否则按照传入的坐标释放(相对页面)。与MouseDrag配合使用，实现拖拽。
        @param : 
            x     in<int>  X坐标(相对页面，默认=None则视为页面中央)
            y     in<int>  Y坐标(相对页面，默认=None则视为页面中央)
            key   in<int>  默认 = Left = 0; Right = 1; Middle = 2
            locus in<bool> 启动轨迹
        '''
        self.activate()
        x, y = self._get_ies_center_pos(x, y)
        win32ext.Mouse.evt_dropIn(handle=self.driver.ies_handle, pos=(x, y), locus=locus, key=key)
    
    def mouse_wheel(self, x=None, y=None, locus=True, step=0):
        '''
        @desc: 鼠标滚轮滚动(会先移动鼠标)。
        @param : 
            x     in<int>  X坐标(相对页面，默认=None则视为页面中央)
            y     in<int>  Y坐标(相对页面，默认=None则视为页面中央)
            locus in<bool> 启动轨迹
            step  in<int>  滚轮轮机数量，正值为向前滚动，负值为向后滚动。(滚动一格所产生的距离)
        '''
        self.activate()
        x, y = self._get_ies_center_pos(x, y)
        win32ext.Mouse.evt_moveIn(handle=self.driver.ies_handle, pos=(x, y), locus=locus)
        win32ext.Mouse.evt_wheelIn(handle=self.driver.ies_handle, step=step)

# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-    

class WebElement(IWebElement):
    '''@desc: (主要类)WebElement类 '''
    
    Timeout = 5
    Timestep = 0.2
    
    def __init__(self, root=None, locator=None):
        '''
        @desc: 构造
        @param: root    in<int|object>     - 父对象：WebPage实例对象; 或包含Internet Explorer_Server句柄HWnd的实例对象(如：SomeObject.HWnd); 或直接是句柄。
                locator in<XPath|str|list> - 定位对象的XPaths，XPaths会自动组合延续父root对象的XPaths。
                                           - 例0(腾讯首页新闻链接)：XPath("//a[text()='新闻']")
                                           - 例1(腾讯首页新闻链接)："//a[text()='新闻']"
                                           - 例2(群空间的登录按钮)："//iframe[@id='loginFrameEmbed']//iframe[@id='xui']//input[@id='loginbtn']"
                                           - 例3(群空间的登录按钮)：["//iframe[@id='loginFrameEmbed']", "//iframe[@id='xui']", "//input[@id='loginbtn']"]
        '''
        self.page, self.root, self.xpaths, self.ele = None, root, locator, None
        # -*-
        if hasattr(self.root, 'HWnd')        : self.root = WebPage(root.HWnd)
        if isinstance(self.root, int)        : self.root = WebPage(root)
        if isinstance(self.root, WebPage)    : self.page = self.root
        if isinstance(self.root, WebElement) : self.page = self.root.page
        # -*-
        self.xpaths = self.root.xpaths + self.xpaths
        if self.ele == None : self.__locate__()
        # -*-
        self.Controls = self.Elements = WebElements()
    
    def updateLocator(self, items={}):
        '''
        @desc: 附加子控件集
        # 示例
        #self.updateLocator({
            #'某按钮1':{'type':WebElement,  root=WebPage或WebElement, locator=XPath("//from[@id='login']//button[@id='someBtn']")    },
            #'某按钮2':{'type':WebElement,  root=WebPage或WebElement, locator=XPath("//from[@id='login']//button[@id='someSubmit']") },
            #'某按钮3':{'class':WebElement, root=WebPage或WebElement, locator=XPath("//from[@id='login']//button[@id='someReset']")  },
        #})
        '''
        self.Controls.update(items)
    
    @property
    def Page(self):return self.page
    
    def __locate__(self):
        # try    : self.ele.nodeName;return True
        # except : pass
        self.ele = self.page.getElement(self.xpaths, self.Timeout, self.Timestep, auto_mapping=False)
        if self.ele : return True
        raise Exception('is not a valid WebElement. - %s' % str(self.xpaths))
    
    def exist(self, timeout=None, timestep=None):
        '''
        @desc: 对象是否存在
        @param : 
            timeout  <int|float> 延迟直到对象存在的，延迟超时值
            timestep <int|float> 每间隔多少时间检测一次
        '''
        self.Timeout = timeout or self.Timeout
        self.Timestep = timestep or self.Timestep
        try    : return self.__locate__()
        except : return False
    
    def __getattribute__(self, name):
        locate = object.__getattribute__(self, '__locate__')
        member = object.__getattribute__(self, name)
        if name in [
           'BoundingRect',
           'NodeName',
           'Attributes',
           'Styles',
           'OuterHTML',
           'InnerHtml',
           'InnerText',
           'Displayed',
           'Focused',
           'Hidden',
           'Value',
           'DefaultChecked',
           'Checked',
           'Options',
           'SelectedIndex',
           'SelectedOption',
           'SelectedText',
           'SelectedValue']:
            # print name
            locate()
        
        if callable(member) and type(member) == types.MethodType and not bool(re.match('^_.*$', name)) and name not in ['__locate__', 'exist']:
            # print name
            locate()
        return member
    
    # -*- -*- -*-
    
    def _getAttributes(self):
        '''@desc: 获取元素全部显式声明的属性'''
        result = self.page.driver.get_ele_attributes(self.xpaths, self.ele)
        return eval(result).keys()
    
    def _getAttribute(self, name):
        '''
        @desc: 获取元素的属性
        @param:
            name in<name> - 属性名
        '''
        name = name.decode(RuntimeDefaultEncoding)
        # -*-
        # 注意：如果textarea本身被赋予了value属性，那么这里永远读取不到，但可以用_getAttributes获取到。
        if name.lower() == 'value' and self.ele.nodeName == 'TEXTAREA' : return self.InnerText
        # -*-
        result = self.page.driver.get_ele_attribute(self.xpaths, self.ele, name)
        if isinstance(result, basestring):result = result.encode(RuntimeDefaultEncoding)
        return result
    
    def _setAttribute(self, name, value):
        '''
        @desc: 设置元素的属性
        @param: 
            name  in<str> - 属性名
            value in<str> - 属性值
        '''
        name = name.decode(RuntimeDefaultEncoding)
        if isinstance(value, basestring) : value = value.decode(RuntimeDefaultEncoding)
        self.page.driver.set_ele_attribute(self.xpaths, self.ele, name, value)
    
    def _getCurrentStyles(self):
        '''
        @desc: 获取元素当前样式属性值
        '''
        result = self.page.driver.get_ele_currentStyles(self.xpaths, self.ele)
        return result.encode(RuntimeDefaultEncoding)
    
    def _getCurrentStyle(self, style_name):
        '''
        @desc: 获取元素当前样式某属性值
        @param:
            style_name in<str> - 样式名(例如：display; color; ......)
        '''
        result = self.page.driver.get_ele_currentStyle(self.xpaths, self.ele, style_name.decode(RuntimeDefaultEncoding))
        if isinstance(result, basestring):result = result.encode(RuntimeDefaultEncoding)
        return result
    
    def _setStyle(self, name, value):
        '''
        @desc: 设置元素的样式
        @param: 
            name  in<str> - 样式名
            value in<str> - 样式值
        '''
        name = name.decode(RuntimeDefaultEncoding)
        value = value.decode(RuntimeDefaultEncoding)
        self.page.driver.set_ele_style(self.xpaths, self.ele, name, value)
    
    # -*- -*- -*-
    @property
    def AccessibleObject(self):
        """返回AccessibleObject
        
        :rtype: tuia.accessible.AccessibleObject
        :attention: Not all IHTMLElement objects support Active Accessibility. 
                    Here is the list of the HTML elements that are also accessible elements:
                    A, AREA, BUTTON, FRAME, IMG,  MARQUEE, OBJECT, APPLET, EMBED, SELECT, 
                    TABLE, TD, TH, TEXTAREA, INPUT type=BUTTON, INPUT type=RESET, INPUT type=SUBMIT, 
                    INPUT type=checkbox, INPUT type=image, INPUT type=password, INPUT type=radio, INPUT type=TEXT.
        """
        #2013/10/22 pear    created
        isp = self.ele.QueryInterface(IServiceProvider)
        try:
            ia = isp.QueryService(IAccessible._iid_, IAccessible)
            if ia:
                return AccessibleObject(ia)
            return None
        except COMError as e:
            if e[0] == -2147467262:
                raise Exception("Web element(%s) can not support IAccessible" % self.xpaths)
            raise e
        
    
    @property
    def BoundingRect(self):
        '''
        @desc: 获取元素动态的屏幕坐标
        @return: <dict>
        '''
        page_rect = self.page.BoundingRect
        ele_rect = self.page.driver.get_ele_rect(self.xpaths, self.ele, autoview=True, highlight=1)
        ele_rect['top'] += page_rect['top']
        ele_rect['bottom'] += page_rect['top']
        ele_rect['left'] += page_rect['left']
        ele_rect['right'] += page_rect['left']
        return ele_rect
    
    @property
    def NodeName(self):
        '''@desc: 获取该对象的nodeName，也等效于tagName，命名从W3C规范以nodeName为准。'''
        return self.ele.nodeName.encode(RuntimeDefaultEncoding)
    
    @property
    def Attributes(self):
        '''@desc: 获取当前元素的属性集'''
        if not hasattr(self, 'attributes'):self.attributes = WebElementAttributes(self._getAttribute, self._setAttribute, self._getAttributes)
        return self.attributes
    
    @property
    def Styles(self):
        '''@desc: 获取当前元素的样式集'''
        if not hasattr(self, 'styles'):self.styles = WebElementStyles(self._getCurrentStyle, self._setStyle, self._getCurrentStyles)
        return self.styles
    
    @property
    def OuterHTML(self):
        '''@desc: 获取元素的HTML，包含子孙。(注意：经过浏览器解析后的数据，浏览器会略有调整。如果要精准检测请使用HTTP协议测试)'''
        result = None
        try    : result = self.ele.outerHTML
        except : pass
        if result : return result.encode(RuntimeDefaultEncoding)
    
    @property
    def InnerHtml(self):
        '''@desc: 获取元素所包含的HTML，不包含自己。(注意：经过浏览器解析后的数据，浏览器会略有调整。如果要精准检测请使用HTTP协议测试)'''
        result = None
        try    : result = self.page.driver.get_ele_innerHTML(self.xpaths, self.ele)
        except : pass
        if result : return result.encode(RuntimeDefaultEncoding)
    
    @InnerHtml.setter
    def InnerHtml(self, html):
        '''@desc: 设置元素的子HTML'''
        self.ele.innerHTML = html.decode(RuntimeDefaultEncoding)
    
    @property
    def InnerText(self):
        '''@desc: 获取元素内的所有文本。(注意：经过浏览器解析后的数据，浏览器会略有调整。如果要精准检测请使用HTTP协议测试)'''
        result = None
        try    : result = self.ele.innerText
        except : pass
        if result : return result.encode(RuntimeDefaultEncoding)
    
    @InnerText.setter
    def InnerText(self, text):
        '''@desc: 设置元素的子文本'''
        self.ele.innerText = text.decode(RuntimeDefaultEncoding)
    
    @property
    def Displayed(self):
        '''@desc: 是否显示'''
        if self._getCurrentStyle('display') != 'none' : return True
        return False
    
    @property
    def Focused(self):
        '''@desc: 是否具有焦点'''
        if self.ele.outerHTML == self.page.driver.doc2.activeElement.outerHTML  : return True
        return False

    @property
    def Hidden(self):
        '''@desc: 是否隐藏域'''
        result = self.page.driver.ele_is_hidden(self.xpaths, self.ele)
        return result
    
    # -*- -*- -*-
    
    def focus(self):
        '''@desc: 赋予焦点'''
        self.page.driver.do_ele_event(self.xpaths, self.ele, 'focus')
    
    def setFocus(self):
        self.focus()
    
    def blur(self):
        '''@desc: 移开焦点'''
        self.page.driver.do_ele_event(self.xpaths, self.ele, 'blur')
    
    # -*- -*- -*-
    
    def highlight(self):
        '''@desc: 高亮对象'''
        self.page.activate()
        return self.page.driver.get_ele_rect(self.xpaths, self.ele, autoview=True, highlight=1)
    
    def getElement(self, locator, timeout=None, timestep=None, auto_mapping=True):
        '''在当前元素的子孙中查找元素'''  # 注意集合的子集合
        timeout = timeout or self.Timeout
        timestep = timestep or self.Timestep
        return self.page.getElement(self.xpaths + locator, timeout, timestep, auto_mapping)

    def getElements(self, locator, timeout=None, timestep=None, auto_mapping=True):
        '''在当前元素的子孙中查找元素集'''  # 注意集合的子集合
        timeout = timeout or self.Timeout
        timestep = timestep or self.Timestep
        return self.page.getElements(self.xpaths + locator, timeout, timestep, auto_mapping)

    def waitForAttribute(self, name, value, timeout=10, interval=0.5):
        '''暂停程序执行，直到当前元素的指定属性变为特定值'''
        begin = time.time()
        while True:
            if self.Attributes[name] == value : return True
            if time.time() - begin > timeout  : break
            time.sleep(interval)
        return False

    def waitForStyle(self, name, value, timeout=10, interval=0.5):
        '''暂停程序执行，直到当前元素的指定样式变为特定值'''
        begin = time.time()
        while True:
            if self.Styles[name] == value : return True
            if time.time() - begin > timeout  : break
            time.sleep(interval)
        return False

    def waitForText(self, value, timeout=10, interval=0.5):
        '''暂停程序执行，直到当前元素的InnerText变为特定值'''
        begin = time.time()
        while True:
            if self.InnerText == value : return True
            if time.time() - begin > timeout  : break
            time.sleep(interval)
        return False
    
    # -*- -*- -*-
    
    def _get_ele_center_pos(self, x=None, y=None):
        '''@desc: 获取相对于元素的中心点XY坐标'''
        rect = self.BoundingRect
        if x == None : x = rect.get('left') + rect.get('width') / 2
        else         : x = rect.get('left') + x
        if y == None : y = rect.get('top') + rect.get('height') / 2
        else         : y = rect.get('top') + y
        return x, y
    
    def _mouse_click(self, x=None, y=None, key=0, dbl=False, locus=True):
        '''
        @desc: 鼠标点击。默认鼠标点击元素的中央，否则按照传入的坐标点击(相对元素)
        @param : 
            x     in<int>  相对元素的X坐标
            y     in<int>  相对元素的Y坐标
            key   in<int>  默认 = Left = 0; Right = 1; Middle = 2
            dbl   in<bool> 是否双击
            locus in<bool> 启动轨迹
        '''
        self.page.activate()
        x, y = self._get_ele_center_pos(x, y)
        # win32ext.Mouse.msg_click(handle=self.page.driver.ies_handle, pos=(x, y), msg='Post', locus=locus, key=key, dbl=dbl)
        win32ext.Mouse.evt_click(pos=(x, y), locus=locus, key=key, dbl=dbl)
    
    def _mouse_move(self, x=None, y=None, locus=True):
        '''
        @desc: 鼠标移动。默认鼠标移动至元素的中央，否则按照传入的坐标点击(相对元素)
        @param : 
            x     in<int>  相对元素的X坐标
            y     in<int>  相对元素的Y坐标
            locus in<bool> 启动轨迹
        '''
        self.page.activate()
        x, y = self._get_ele_center_pos(x, y)
        # win32ext.Mouse.msg_move(handle=self.page.driver.ies_handle, pos=(x, y), msg='Post', locus=locus)
        win32ext.Mouse.evt_move(pos=(x, y), locus=locus)
    
    def _mouse_drag(self, x=None, y=None, key=0, locus=True):
        '''
        @desc: 鼠标左键按下(不释放)。默认鼠标按下(不释放)于元素的中央，否则按照传入的坐标按下(不释放)(相对元素)。与_mouse_drop配合使用，实现拖拽。
        @param : 
            x     <int>  相对元素的X坐标
            y     <int>  相对元素的Y坐标
            key   <int>  默认 = Left = 0; Right = 1; Middle = 2
            locus <bool> 启动轨迹
        '''
        self.page.activate()
        x, y = self._get_ele_center_pos(x, y)
        # win32ext.Mouse.msg_drag(handle=self.page.driver.ies_handle, pos=(x, y), msg='Post', locus=locus, key=key)
        win32ext.Mouse.evt_drag(pos=(x, y), locus=locus, key=key)
    
    def _mouse_drop(self, x=None, y=None, key=0, locus=True):
        '''
        @desc: 鼠标左键释放。默认鼠标释放于元素的中央，否则按照传入的坐标释放(相对元素)。与_mouse_drag配合使用，实现拖拽。
        @param : 
            x     <int>  相对元素的X坐标
            y     <int>  相对元素的Y坐标
            key   <int>  默认 = Left = 0; Right = 1; Middle = 2
            locus <bool> 启动轨迹
        '''
        self.page.activate()
        x, y = self._get_ele_center_pos(x, y)
        # win32ext.Mouse.msg_drop(handle=self.page.driver.ies_handle, pos=(x, y), msg='Post', locus=locus, key=key)
        win32ext.Mouse.evt_drop(pos=(x, y), locus=locus, key=key)
        
    def _mouse_wheel(self, step=0):
        '''
        @desc: 鼠标滚轮滚动，需要先点击与悬停于元素上方。
        @param : 
            step   <int>   滚轮轮机数量，正值为向前滚动，负值为向后滚动。(滚动一格所产生的距离)
        '''
        self._mouse_move()
        self.focus()
        # win32ext.Mouse.msg_wheel(handle=self.page.driver.ies_handle, step=step, msg='Post')
        win32ext.Mouse.evt_wheel(step=step)
    
    # -*- -*- -*-
    
    def click(self, x=None, y=None):
        '''@desc: 鼠标左键单击'''
        self._mouse_click(x, y)
    
    def hover(self, x=None, y=None):
        '''@desc: 鼠标悬停'''
        self._mouse_move(x, y)
    
    def doubleClick(self, x=None, y=None):
        '''@desc: 鼠标右键单击'''
        self._mouse_click(x, y, dbl=True)
    
    def rightClick(self, x=None, y=None):
        '''@desc: 鼠标左键双击'''
        self._mouse_click(x, y, key=1)
    
    def drag(self, x=None, y=None):
        self._mouse_drag()
        self._mouse_drop(x, y)
    
    # def drag(self, x=None, y=None):
    #    '''@desc: 拖'''
    #    self._mouse_drag(x, y)
    
    # def drop(self, x=None, y=None):
    #    '''@desc: 拽'''
    #    self._mouse_drop(x, y)
    
    def sendKeys(self, keys):
        '''
        @desc: 发送按键
        @param : 
            keys      in<str>(UTF-8) 需要按键的字符串，如果是中文请注意编码为UTF-8，并isChinese=True
            #去掉该参数 isChinese in<bool>       默认=False; True=中文
        '''
        self.page.activate()
        self.click()
        
        #直接调用tuia.Keyboard支持sendKeys即可
        Keyboard.inputKeys(keys, interval=0.1)
        
        '''
        #以下方式，需要额外一个参数，并且中文的方式直接采用了粘贴复制的方式，会无法支持例如{ENTER}的写法
        if isChinese : SendKeys.SendChinese(keys.decode('UTF-8'))
        else         : SendKeys.SendKeys(keys)
        '''
    
    # -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- for form and input # 对外封装时请注意
    
    def submit_form(self):
        '''
        @desc: 提交按钮所在的表单。触发onsubmit处理函数，通过后则提交，否则不提交(例如验证函数必须执行通过)
             : 当表单中有submit类型的按钮的name='submit'，则会引发IE的异常，不能提交。
        '''
        if self.ele.nodeName.lower() == 'form' : self.page.driver.do_ele_event(self.xpaths, self.ele, 'submit')
        else                                   : self.page.driver.do_ele_event(self.xpaths, self.ele.form, 'submit')
    
    @property
    def Value(self):
        return self.ele.value.encode(RuntimeDefaultEncoding)
        # return self.Attributes['value']
    
    @Value.setter
    def Value(self, value):
        '''@desc: 填写文本'''
        self._mouse_click()
        self.ele.value = value.decode(RuntimeDefaultEncoding)
        # self.Attributes['value'] = value
        self.page.driver.do_ele_event(self.xpaths, self.ele, 'change')

    def select(self):
        '''@desc: 选取文本框中的全部文本'''
        self._mouse_click()
        self.ele.Select()

    def clean(self):
        '''@desc: 清除文本'''
        self._mouse_click()
        self.ele.select()
        self.Attributes['value'] = ''
        self.page.driver.do_ele_event(self.xpaths, self.ele, 'change')
    
    @property
    def DefaultChecked(self):
        '''@desc: 默认选中'''
        return self.Attributes['defaultChecked']
    
    @property
    def Checked(self):
        '''@desc: 是否选中'''
        return self.Attributes['checked']
    
    @Checked.setter
    def Checked(self, value=True):
        '''@desc: 选中(True|False)'''
        self._mouse_move()
        self.Attributes['checked'] = value

    @property
    def Options(self):
        '''
        @desc: 获取options数据集
        @return:
            [(<int>index, <str>text, <str>value),...]
        @sample:
            for (index, text, value) in WIEComboBox('...').GetOptions():
                print '索引: %s; 文本: %s; 值: %s' % (index, text, value)
        '''
        options = []
        for item in self.ele.options:
            options.append((
                item.index,
                item.text.encode(RuntimeDefaultEncoding),
                item.value.encode(RuntimeDefaultEncoding)
            ))
        return options
    
    @property
    def SelectedIndex(self):
        return self.ele.selectedIndex
    
    @SelectedIndex.setter
    def SelectedIndex(self, index):
        self._mouse_click()
        self.ele.selectedIndex = int(index)
        self._mouse_click()
    
    @property
    def SelectedOption(self):
        '''
        @desc: 获取当前选中的option数据
        @return:
            <int>index, <str>text, <str>value
        '''
        options = self.Options
        for opt_index, opt_text, opt_value in options:
            if self.SelectedIndex == opt_index:
                return opt_index, opt_text, opt_value
    
    @property
    def SelectedText(self):
        return self.SelectedOption[1]
    
    @SelectedText.setter
    def SelectedText(self, text=None):
        '''
        @desc: 选择指定文本的项目(第一个完全匹配项目优先)
        @sample:
            Select('...').select_byText('男性')
        '''
        if text:
            text = text.decode(RuntimeDefaultEncoding)
            options = self.Options
            for opt_index, opt_text, opt_value in options:
                if opt_text == text:
                    self.SelectedIndex = opt_index
                    break
    
    @property
    def SelectedValue(self):
        return self.SelectedOption[2]
    
    @SelectedValue.setter
    def SelectedValue(self, value=None):
        '''
        @desc: 选择指定值的项目(第一个完全匹配项目优先)
        @sample:
            Select('...').select_byValue('1')
        '''
        if value:
            value = value.decode(RuntimeDefaultEncoding)
            options = self.Options
            for opt_index, opt_text, opt_value in options:
                if opt_value == value:
                    self.SelectedIndex = opt_index
                    break

# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-

class FrameElement(WebElement):
    '''@desc: 继承于<WebElement>，代表 <iframe>兼容 <frame> 元素'''
    
    def __init__(self, root=None, locator=None):
        WebElement.__init__(self, root=root, locator=locator)
    
    @property
    def FramePage(self):
        '''@desc: 获取IFrame|Frame内的WebPage实例对象。'''
        if not hasattr(self, '_frame_page'):self._frame_page = WebPage(self.page.driver.ies_handle)
        self._frame_page.xpaths = self.xpaths
        return self._frame_page

# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-


if __name__ == '__main__':
    
    
    """
    # WebQQ 登录脚本示例
    class LoginAndLoout(WebPage):
        def __init__(self, HWnd=None):
            WebPage.__init__(self, HWnd=HWnd)
            self.updateLocator({
                '左边栏QQ'     : {'type':WebElement, 'root':self, 'locator':XPath("//div[@id = 'leftBar']//div[@title = 'QQ']")},
                'EQQ面板登录'  : {'type':WebElement, 'root':self, 'locator':XPath("//DIV[@class='window_content']//DIV[@id='loginIcon']")},
                '开始菜单按钮' : {'type':WebElement, 'root':self, 'locator':XPath("//A[@title='点击这里开始']")},
                '开始菜单登录' : {'type':WebElement, 'root':self, 'locator':XPath("//DIV[@id='startMenuSelfNick']")},
                '登录窗口'     : {'type':FrameElement, 'root':self, 'locator':XPath("//div[@class = 'ui_boxy']//iframe[@id='ifram_login']")},
                '帐号输入'     : {'type':WebElement, 'root':'@登录窗口', 'locator':XPath("//input[@id = 'u']")},
                '密码输入'     : {'type':WebElement, 'root':'@登录窗口', 'locator':XPath("//input[@id = 'p']")},
                '登录按钮'     : {'type':WebElement, 'root':'@登录窗口', 'locator':XPath("//input[@id = 'login_button']")},
                '检查点'       : {'type':WebElement, 'root':self, 'locator':XPath("//DIV[@class='window_content']//div[@class='EQQ_myNick']")},
                '注销'         : {'type':WebElement, 'root':self, 'locator':XPath("//A[@title='注销当前用户']")},
                '注销确认'     : {'type':WebElement, 'root':self, 'locator':XPath("//A[@class='ui_button window_button window_ok']")},
                '关闭EQQ'      : {'type':WebElement, 'root':self, 'locator':XPath("//A[@class='ui_button window_action_button window_close']")},
            })
        
        def doLogin(self, uid, pwd):
            self.Controls['帐号输入'].Value = ''
            self.Controls['帐号输入'].sendKeys('^(a)'+uid)
            self.Controls['密码输入'].Value = ''
            self.Controls['密码输入'].sendKeys(pwd)
            self.Controls['登录按钮'].click()
    
    # -*- 脚本 -*-
    page = WebPage.openUrl('http://web.qq.com')
    page.mouse_move()
    page.waitForReady()
    doc = LoginAndLoout(page)
    doc.Controls['左边栏QQ'].click()
    doc.doLogin('1002000505', 'tencent@123')
    """
    
    
    '''
    # QQ的手机充值内嵌页面，请先从QQ面板上打开该充值APP
    class RechargePage(WebPage):
        #11/9/28 cherry 创建
        def __init__(self, HWnd=None):
            WebPage.__init__(self, HWnd=HWnd)
            self.updateLocator({
                '充话费'       : {'type':WebElement, 'root':self, 'locator':XPath("//LI[@id='mobile']")},
                '充网游'       : {'type':WebElement, 'root':self, 'locator':XPath("//LI[@id='game']")},
                '充Q币'        : {'type':WebElement, 'root':self, 'locator':XPath("//LI[@id='service']")},
                '买彩票'       : {'type':WebElement, 'root':self, 'locator':XPath("//LI[@id='lottery']")},
                # -*-
                '话费子页'     : {'type':FrameElement, 'root':self, 'locator':XPath('//IFRAME[@id="mobileIframe"]')},
                '手机号码'     : {'type':WebElement, 'root':'@话费子页', 'locator':XPath('//INPUT[@id="txtMobileNum"]')},
                # -*-
                '充值记录'     : {'type':WebElement, 'root':'@话费子页', 'locator':XPath('//a[text()="充值记录"]')},
                '在线查询进度' : {'type':WebElement, 'root':'@话费子页', 'locator':XPath('//a[text()="在线查询进度"]')},
                '话费充值流程' : {'type':WebElement, 'root':'@话费子页', 'locator':XPath('//a[text()="话费充值流程"]')},
                '联系客服'     : {'type':WebElement, 'root':'@话费子页', 'locator':XPath('//a[text()="联系客服"]')},
            })
    
    page = WebPage.findByUrl('http://virtual.paipai.com/chong/appbox.+')
    rechargePage = RechargePage(page)
    ele = rechargePage.Controls['充值记录']
    ele.hover()
    '''
    
    for i in xrange(3):
        page = WebPage.openUrl("http://www.qq.com/")
        page.waitForReady()
        page.getElement("//a[@id='onekey']").click()
        page.waitForReady()
        print page.getElement("//body").InnerHtml
        page.getElement("//iframe[@id='login_frame']//input[@id='u']")
