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
用于各种Webkit内核浏览器的Web自动化实现的基类，目前支持Chrome和QPlus
'''
#2012-02-22    banana    创建
#2012-03-07    banana    增加了LazyDriver类
#2012-03-08    banana    _wait方法从WebPage移动到WebElement
#2012-04-10    cherry  在顶部加入自解压部分，banana回来上班后请梳理这个导包逻辑

'''
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
import sys, os, time, shutil, zipfile
WebkitLibPath = os.path.join(os.getenv('APPDATA'), 'webkitlib')
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-

class __prepare:
    def __init__(self):
        self.tag_time = 1335569812.66
        self.cur_path = os.path.dirname(os.path.realpath(__file__))
        self.lib_name = 'webkit.lib'
        self.lib_path = os.path.join(self.cur_path, self.lib_name)
        self.tmp_path = os.getenv('TEMP')
        self.tmp_paths = []
        self.out_path = WebkitLibPath
        if self.check_need_decompress():
            print "~~yeah~~"
            self.revise_lib_path()
            self.revise_lib()
            self.clean_tmp_paths()
        self.import_exist_lib()
    
    def check_need_decompress(self):
        if not os.path.exists(self.out_path)               : return True
        if len(os.listdir(self.out_path)) == 0             : return True
        if os.path.getmtime(self.out_path) < self.tag_time : return True
        return False
    
    def revise_lib_path(self):
        _root, _path = os.path.splitdrive(self.cur_path)
        tag_path = _root + '\\'
        paths = _path.strip('\\').split('\\')
        for item in paths:
            tag_path = os.path.join(tag_path, item)
            if zipfile.is_zipfile(tag_path) or (os.path.isfile(tag_path) and 'exe' == os.path.splitext(tag_path)[1].lower()):
                tmp_path = os.path.join(self.tmp_path, 'TEMP%s' % str(int(time.time())))
                zp = zipfile.ZipFile(tag_path, mode="r", compression=zipfile.ZIP_DEFLATED)
                zp.extractall(tmp_path)
                zp.close()
                tag_path = tmp_path
                self.tmp_paths.append(tmp_path)
        self.lib_path = os.path.join(tag_path, self.lib_name)
    
    def revise_lib(self):
        if not os.path.exists(self.out_path) : os.mkdir(self.out_path)
        tag_path1 = os.path.join(self.out_path, self.lib_name)
        shutil.copy(self.lib_path, tag_path1)
        # -*- for PeInfo.dll
        dll_path = os.path.join(os.path.dirname(self.lib_path), 'PeInfo.dll')
        tag_path2 = os.path.join(self.out_path, 'PeInfo.dll')
        shutil.copy(dll_path, tag_path2)
    
    def import_exist_lib(self):
        global inspector
        tag_path = os.path.join(self.out_path, self.lib_name)
        try:
            tag_py_path = os.path.join(tag_path, 'py26')
            sys.path.append(tag_path)
            sys.path.append(tag_py_path)
            import inspector
        except ImportError:
            tag_py_path = os.path.join(tag_path, 'py27')
            sys.path.append(tag_path)
            sys.path.append(tag_py_path)
            import inspector
    
    def clean_tmp_paths(self):
        for path in self.tmp_paths:
            if os.path.exists(path):shutil.rmtree(path)


# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
#__prepare()
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
'''

import time
import win32gui
from datetime import datetime
from ctypes import *
from ... import base
from ...util import (Rect, XPath, Mouse, Keyboard,
                     LazyDict, WebElementAttributes, WebElementStyles)


import os, sys, zipfile
import copy

from tuia.accessible import AccessibleObject, EnumAccessibleObjectRole
import tuia.wincontrols as wincontrols
from tuia.mouse import MouseFlag, MouseClickType

WEBKIT_LIB = "webkit.lib"
filelist = [WEBKIT_LIB, 'chromespy.exe']
extlist = [".zip", ".exe", '.egg']
basepath = os.path.dirname(__file__)

zipped = False
pos = -1
for ext in extlist:
    pos = basepath.lower().find(ext.lower())
    if pos >= 0:
        pos += len(ext)
        pakpath = basepath[:pos] #取压缩包路径
        if os.path.isfile(pakpath):
            #只有是压缩包文件才会解压
            zipped = True
            break

if zipped:
    tmp = os.path.join(os.getenv('TEMP'), 'autoweb')
    pak = basepath[:pos]
    zp = zipfile.ZipFile(pak, mode="r", compression=zipfile.ZIP_DEFLATED)
    for f in filelist:
        zp.extract(os.path.join(basepath[pos+1:], f).replace("\\", "/"), tmp)
    zp.close()
    basepath = os.path.join(tmp, basepath[pos+1:])

libpath = os.path.join(basepath, WEBKIT_LIB)
sys.path.append(libpath)
#sys.path.append(os.path.join(libpath, "py26"))
#sys.path.append(os.path.join(libpath, "py27"))
sys.path.append(os.path.join(libpath, "py2%s" % sys.version_info[1]))

import inspector_new

LOGGING_LEVEL = 0

class WebPage(base.IWebPage):
    '''用于各种Webkit内核浏览器的WebPage实现'''
    #2012-02-22    banana    创建
    #2012-02-27    banana    添加了__str__方法
    #2012-03-08    banana    优化了getElement方法的效率
    #2012-03-08    banana    优化了_get_control方法的效率
    #2012-03-08    banana    添加了getFramePage方法
    def __init__(self, driver, locator = ''):
        '''构造函数
        @type driver: WebkitInspector
        @param driver: 连接页面的WebkitInspector实例
        @type frame_xpath: XPath
        @param frame_xpath: 当前WebPage所在frame的xpath路径 
        '''
        
        if locator:
            if not isinstance(locator, XPath):
                locator = XPath(locator)
        else:
            locator = XPath('')
        self._locator = locator
        if self._locator:
            self._locators = self._locator.break_frames()
        else:
            self._locators = []
        self._page = self
        self._controls = {}
        self.Controls = LazyDict(self._get_control)
        self._driver = driver

    def __del__(self):
        '''析构函数'''
        if not self._fid:
            self._driver.close()
            pass
#    '''
    def _get_loc(self, root, loc):
        if isinstance(root, basestring) and root[0] == "@":
            item = self._controls[root[1:]]
            root, loc = self._get_loc(item["root"], item["locator"] + loc)
        if not hasattr(root, 'getElement'):
            raise Exception("Cannot find the control：%s" % str(item))
        return root, loc

    def _get_control(self, name):
        item = self._controls[name]
        root = item['root']
        loc = item['locator']
        root, loc = self._get_loc(root, loc)
        return root.getElement(loc)

    def _get_rect(self):
        ret = win32gui.GetWindowRect(self._hwnd)
        return Rect(ret[0], ret[1], ret[2] - ret[0], ret[3] - ret[1])
    
    def _execute(self, cmd):
        tmpl = '''
            webkit_inspector.result = null;
            webkit_inspector.command = function(){%s;};
            webkit_inspector.result = webkit_inspector.command();
        '''
        ret = self._driver.evalScript(self._locators, tmpl % cmd)
        return ret

    def updateLocator(self, items={}):
        '''更新locator集合
        @type items: dict
        @param items: 新定义的locator的集合
        '''
        self._controls.update(items)
        
    @property
    def Url(self):
        '''获取页面的当前URL
        @rtype: str
        @return: 页面的当前URL
        '''
        cmd = "return document.URL;"
        return self._execute(cmd)

    @property
    def ActiveElementOuterHTML(self):
        '''当前元素的outerhtml
        @rtype: str
        @return: 当前元素的outerhtml
        '''
        cmd = "return document.activeElement.outerHTML;"
        html = self._execute(cmd)
        return html;
        
    @property
    def Title(self):
        '''获取页面的当前标题
        @rtype: str
        @return: 页面的当前标题
        '''
        cmd = "return document.title;"
        title = self._execute(cmd)
        if isinstance(title, unicode):
            title = title.encode('utf8')
        return title

    @property
    def ReadyState(self):
        '''获取页面的当前状态
        @rtype: int
        @return: 页面的当前状态
        '''
        cmd = "return document.readyState;"
        return self._execute(cmd)
    
    def _getAccessibleObject(self):
        boundingrect = self._get_rect()
        x = int((boundingrect.Left + boundingrect.Right)/2)
        y = int((boundingrect.Top + boundingrect.Bottom)/2)
        pt = (x,y)
        try:
            ao = AccessibleObject(pt)
        except ValueError:
            return None
        while ao:
            if ao.accRole == EnumAccessibleObjectRole.ROLE_SYSTEM_DOCUMENT:
                return ao
            ao = ao.accParent
        return None
    
    @property
    def AccessibleObject(self):
        """返回AccessibleObject
        
        :rtype: tuia.accessible.AccessibleObject
        :attention: webkit的accessible的获取是通过坐标点来获取的，故需要保证目标元素总在系统桌面的最前端
        """
        #2013/10/22 pear    created
        self.activate()
        if self.__module__.find("qqcef") != -1:
            self._container.setFocus()
            for i in range(10):
                ao = self._getAccessibleObject()
                if ao:
                    return ao
                else:
                    Keyboard.inputKeys("{TAB}")
                    time.sleep(1)
            
        return self._getAccessibleObject()
        
    @property
    def HWnd(self):
        '''返回page所在的窗口句柄
        '''
        return None
    
    def activate(self):
        '''激活承载页面的窗口'''
        pass

    def close(self):
        '''关闭承载页面的窗口'''
        self.release()

    def release(self):
        '''释放占用的资源，这里仅断开与driver的连接'''
        self._driver.close()

    def scroll(self, toX, toY):
        '''按指定的偏移量滚动页面
        @type toX: int
        @param toX: 横向滚动的偏移，负值向左，正值向右
        @type toY: int
        @param toY: 纵向滚动的偏移，负值向上，正值向下
        '''
        cmd = '''
            window.scrollTo(%s, %s)
        ''' % (toX, toY)
        return self._execute(cmd)

    def execScript(self, script):
        '''在页面中执行脚本代码
        @type script: str
        @param script: 要执行的脚本代码
        @rtype: bool
        @return: True=成功；False=失败
        '''
        self._driver.evalScript(self._locators, script)
        return True
#        try:
#            self._driver.evalScript(self._locators, script)
#        except Exception as e:
#            print 'EvalScript error', e
#            return False
#        return True

    def waitForReady(self, timeout = 60):
        '''等待页面加载完成
        @type timeout: int或float
        @param timeout: 最长等待的时间
        '''
        ret = self._driver.waitForReady(self._locators, timeout)
        return ret

    def getElement(self, locator):
        '''在页面中查找元素，返回第一个匹配的元素
        @type locator: str或XPath
        @param locator: 查找条件，可以是XPath或元素ID
        @rtype: WebElement
        @return: 查找到的元素
        '''
        return WebElement(self, locator)
    #"""
    def getElements(self, locator):
        '''在页面中查找元素，返回包含所有匹配的元素的列表
        @type locator: str或XPath
        @param locator: 查找条件，可以是XPath或元素Tag、Name
        @rtype: list<WebElement>
        @return: 查找到的元素的列表
        '''
        locators = XPath(locator).break_frames()
        locators[-1] = "(%s)" % locators[-1]
        locator = "".join(locators)
        def get_elem(index):
            loc = XPath('%s[%d]' % (locator, index + 1))
            return self.getElement(loc)
        
        num = self._driver.getNodeListLength(locators)
        ret = LazyDict(get_elem, lister=lambda:xrange(num))
#        try:
#            #elem = self.getElement(locator)
#            num = self._driver.getNodeListLength(locators)
#            ret = LazyDict(get_elem, lister=lambda:xrange(num))
#        except:
#            ret = []
        return ret
    """
    def getElements(self, locator):
        '''在页面中查找元素，返回包含所有匹配的元素的列表
        @type locator: str或XPath
        @param locator: 查找条件，可以是XPath或元素Tag、Name
        @rtype: list<WebElement>
        @return: 查找到的元素的列表
        '''
        locators = XPath(locator).break_frames()
        locators[-1] = "(%s)" % locators[-1]
        locator = "".join(locators)
        cnt = 1
        ret = []
        self._driver.start()
        while True:
            loc = XPath('%s[%d]' % (locator, cnt))
            try:
                elem = self.getElement(loc)
            except:
                break
            if not isinstance(elem, WebElement):
                break
            ret.append(elem)
            cnt += 1
        self._driver.end()
        return ret
    #""" 
    def getFramePage(self, locator):
        '''在页面中查找Frame或IFrame，返回该Frame或IFrame所包含的页面
        @type locator: str或XPath
        @param locator: 查找条件，可以是XPath或元素Tag、Name
        @rtype: WebPage
        @return: 查找到的Frame或IFrame所包含的页面
        '''
        if not isinstance(locator, XPath):
            locator = XPath(locator)
        if not locator.Nodetest in ["iframe", "frame"]:
            raise Exception(locator+'不是一个Frame元素')
        return self.__class__(self._driver, self._locator+locator)
        
    def __str__(self):
        return '<%s: "%s">' % (self.__class__.__name__, (self.Title or self.Url))
    
    def checkValid(self):
        '''
        检查页面是否存在，由子类实现
        '''
        #2012/11/21 rambutan 添加
        pass
    
    def navigate(self, url):
        '''导航至指定URL
        @type url: str
        @param url: 指定导航的URL
        '''
        if "://" not in url :
            url = "http://" + url
            
        script = r"window.location = '%s'" %url
        self.execScript(script)


class WebElement(base.IWebElement):
    '''用于Webkit内核浏览器的WebElement实现'''
    #2012-02-14    banana    创建
    #2012-02-21    banana    初步实现了全部方法
    #2012-02-27    banana    添加了__str__方法
    def __init__(self, root, locator):
        '''构造函数
        @type root: WebElement或WebPage
        @param root: 根据locator定位的基准元素
        @type locator: XPath或str
        @param locator: 描述元素的定位符
        '''
        # _locator: 传入的参数locator，相对于root的XPath
        # _frame:   _locator的前半部分，所在frame相对于root的XPath
        # _xpath:   _locator的后半部分，相对于所在frame的XPath

        if not isinstance(locator, XPath):
            locator = XPath(locator)
        self._root = root
        self._locator = XPath(root._locator + locator)
        self._locators = self._locator.break_frames()#当前元素的完整xpath路径列表
        
        self._page = root._page
        self._driver = root._driver

        if not self._wait(lambda: self._driver.nodeExist(self._locators)):
            raise Exception('WebElement not found: "%s"' % self._locator)
        self._attrs = WebElementAttributes(self._getattr, self._setattr, self._listattr)
        self._styles = WebElementStyles(self._getstyle)
    #'''
    
    def _execute(self, cmd):
        return self._root._execute(cmd)
        
#    def _parse_frames(self):
#        locators = self._root._locators
#        for loc in locators:
#            if loc is not locators[-1] and loc.Nodetest in ["iframe", "frame"]:
#                fid = self._driver.getFrameIdByXPath(loc, fid)
#                continue
#            if not self._wait(lambda: self._driver.nodeExist(loc, fid)):
#                raise Exception('WebElement not found: "%s"' % self._locator)
#        return fid, self._locator[:-len(loc)], loc

    def _wait(self, func, timeout=5, interval=0.5):
        if timeout < 5:
            timeout = 5
        if interval < 0.5:
            interval = 0.5
        start = time.time()
        while True:
            waited = time.time() - start
            if waited > timeout or func():
                break
            time.sleep(interval)
        return waited <= timeout
        
    def _getstyle(self, name):
        # TODO: 处理color的返回值
        ret = self._driver.getStyle(self._locators, name.lower())
        return ret

    def _getattr(self, name):
        if name in ["value", "checked"]:
            ret = self._driver.getProperty(self._locators, name)
        else:
            ret = self._driver.getAttribute(self._locators, name)
        return ret

    def _setattr(self, name, value):
        self.highlight()
        if name in ["value", "checked"]:
            ret = self._driver.setProperty(self._locators, name, value)
        else:
            ret = self._driver.setAttribute(self._locators, name, value)
        return ret

    def _listattr(self):
        return ['id', 'name', 'class']
    
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
        return self._attrs

    @property
    def Styles(self):
        '''当前元素的样式集合
        @rtype: WebElementStyles
        @return: 元素的样式集合
        '''
        return self._styles

    @property
    def BoundingRect(self):
        '''当前元素在屏幕上的位置和大小
        @rtype: Rect
        @return: 元素在屏幕上的位置和大小
        '''
        m_rect = self._driver.getElementRect(self._locators, False)
        f_rect = self._page._get_rect()
#        if len(self._locators) > 1:
#            f_rect = WebElement(self._root, self._frame).BoundingRect
        x = m_rect[0] + f_rect.Left
        y = m_rect[1] + f_rect.Top
        w = m_rect[2]
        h = m_rect[3]
        #print m_rect
        return Rect(x, y, w, h)

    def _getAccessibleObject(self):
        x = int(self.BoundingRect.Left + self.BoundingRect.Width/2)
        y = int(self.BoundingRect.Top + self.BoundingRect.Height/2)
        pt = (x,y)
        try:
            return AccessibleObject(pt)
        except ValueError:
            return None
        
    @property
    def AccessibleObject(self):
        """返回AccessibleObject
        
        :attention: 1 Not all IHTMLElement objects support Active Accessibility. 
                    Here is the list of the HTML elements that are also accessible elements:
                    A, AREA, BUTTON, FRAME, IMG,  MARQUEE, OBJECT, APPLET, EMBED, SELECT, 
                    TABLE, TD, TH, TEXTAREA, INPUT type=BUTTON, INPUT type=RESET, INPUT type=SUBMIT, 
                    INPUT type=checkbox, INPUT type=image, INPUT type=password, INPUT type=radio, INPUT type=TEXT.
                    2 webkit的accessible的获取是通过坐标点来获取的，故需要保证目标元素总在系统桌面的最前端
        :rtype: tuia.accessible.AccessibleObject
        """
        #2013/10/22 pear    created
        self._page.activate()
        if self.__module__.find("qqcef") != -1:
            for i in range(10):
                ao = self._page.AccessibleObject
                if ao:
                    break
                else:
                    Keyboard.inputKeys("{TAB}")
                    time.sleep(1)
        
        return self._getAccessibleObject()
        
    @property
    def Displayed(self):
        '''当前元素是否显示
        @rtype: bool
        @return: 元素是否显示
        '''
        return self.Styles['display'] != 'none'

    @property
    def InnerText(self):
        '''当前元素所包含的文本
        @rtype: str
        @return: 元素所包含的文本
        '''
        ret = self._driver.getProperty(self._locators, 'innerText')
        return ret

    @InnerText.setter
    def InnerText(self, text):
        self.highlight()
        self._driver.setProperty(self._locators, 'innerText', text)

    @property
    def InnerHtml(self):
        '''当前元素所包含的HTML
        @rtype: str
        @return: 元素所包含的HTML
        '''
        ret = self._driver.getProperty(self._locators, 'innerHTML')
        return ret

    @InnerHtml.setter
    def InnerHtml(self, html):
        self.highlight()
        self._driver.setProperty(self._locators, 'innerHTML', html)

    @property
    def Focused(self):
        outerHTML = self._driver.getProperty(self._locators, 'outerHTML')
        return outerHTML == self._page.ActiveElementOuterHTML;
        
        
    def scroll(self, toX, toY):
        '''按指定的偏移量滚动元素
        @type toX: int
        @param toX: 横向滚动的偏移，负值向左，正值向右
        @type toY: int
        @param toY: 纵向滚动的偏移，负值向上，正值向下
        '''
        # TODO: 此种方法无法滚动
        ret = self._driver.setProperty(self._locators, 'scrollLeft', toX)
        ret = ret and self._driver.setProperty(self._locators, 'scrollTop', toY)
        return ret

    def getElement(self, locator):
        '''在当前元素的子孙中查找元素，返回第一个匹配的元素
        @type locator: str或XPath
        @param locator: 查找条件，可以是XPath或元素ID
        @rtype: WebElement
        @return: 查找到的元素
        '''
        locator = XPath(self._locator + locator)
        return self._root.getElement(locator)

    def getElements(self, locator):
        '''在当前元素的子孙中查找元素，返回所有匹配的元素的列表
        @type locator: str或XPath
        @param locator: 查找条件，可以是XPath或元素Tag、Name
        @rtype: list<WebElement>
        @return: 查找到的元素的列表
        '''
        locator = XPath(self._locator + locator)
        return self._root.getElements(locator)

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
        return self._wait((lambda: self.Attributes[name] == value), timeout, interval)

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
        return self._wait((lambda: self.Styles[name] == value), timeout, interval)

    def waitForText(self, value, timeout=10, interval=0.5):
        '''暂停程序执行，直到当前元素的InnerText变为特定值
        @type value: str
        @param value: 等待的文本值
        @type timeout: int或float
        @param timeout: 最多等待的秒数
        @type interval: int或float
        @param interval: 查询间隔的秒数
        '''
        return self._wait((lambda: self.InnerText == value), timeout, interval)

    def highlight(self):
        self._page.activate()
        self._driver.highlight(self._locators)
        time.sleep(0.5)
        self._page.activate()

    def _get_cursor_pos(self, xOffset=None, yOffset=None):

        self.highlight()
        rect = self.BoundingRect
        if xOffset is None:
            xOffset = rect.Width / 2
        if yOffset is None:
            yOffset = rect.Height / 2
        x = int(rect.Left + xOffset)
        y = int(rect.Top + yOffset)
        return x, y

    def _exClick(self, hwnd, (x,y), flag=MouseFlag.LeftButton, 
                  clicktype=MouseClickType.SingleClick):
        """点击操作实现的加强版，确保点击操作实现
        
        :param hwnd: 目标窗口句柄
        :type hwnd: 整数
        :param x: 屏幕x坐标
        :type x: 整数  
        :param y: 屏幕y坐标
        :type y: 整数
        :param flag: 鼠标键类型 
        :type flag: 枚举类型, MouseFlag.LeftButton|MouseFlag.MiddleButton|MouseFlag.RightButton
        :param clicktype: 鼠标键点击方式
        :type clicktype: 枚举类型, MouseClickType.SingleClick | MouseClickType.DoubleClick
        :raise: ValueError, hwnd句柄无效
        """
        #2013/12/25 pear    新建
        if hwnd is None:
            Mouse.click(x, y, flag, clicktype)
            return
        if not win32gui.IsWindow(hwnd):
            raise ValueError("句柄(%s)无效!" % hwnd)
        ptWnd = win32gui.WindowFromPoint((x,y))
        if (ptWnd == hwnd):
            Mouse.click(x, y, flag, clicktype)
        else:
            wincontrols.Control(root=hwnd).TopLevelWindow.bringForeground()
            ptWnd = win32gui.WindowFromPoint((x,y))
            if (ptWnd == hwnd):
                Mouse.click(x, y, flag, clicktype)
            else:
                #Mouse.postClick(ptWnd, x, y, flag, clicktype)
                #Mouse.click(x, y, flag, clicktype)
                Mouse.postClick(hwnd, x, y, flag, clicktype)

    
    def _exHover(self, hwnd, (x,y)):
        """悬停实现的加强版，确保悬停效果
        
        :param hwnd: 目标窗口句柄
        :type hwnd: 整数
        :param x: 屏幕x坐标
        :type x: 整数  
        :param y: 屏幕y坐标
        :type y: 整数
        :raise: ValueError, hwnd句柄无效
        """
        #2013/12/25 pear    新建
        if hwnd is None:
            Mouse.click(x, y)
        if not win32gui.IsWindow(hwnd):
            raise ValueError("句柄(%s)无效!" % hwnd)
        ptWnd = win32gui.WindowFromPoint((x,y))
        if (ptWnd == hwnd):
            Mouse.move(x, y)
        else:
            wincontrols.Control(root=hwnd).TopLevelWindow.bringForeground()
            ptWnd = win32gui.WindowFromPoint((x,y))
            if (ptWnd == hwnd):
                Mouse.move(x, y)
            else:
                print 'post move'
                Mouse.postMove(hwnd, x, y)
    
    def click(self, xOffset=None, yOffset=None):
        '''鼠标左键单击
        @type xOffset: int
        @param xOffset: 距离控件区域左上角的横向偏移。
        @type yOffset: int
        @param yOffset: 距离控件区域左上角的纵向偏移。
        '''
        #2013/12/24 pear    修改点击实现
        x, y = self._get_cursor_pos(xOffset, yOffset)
        self._exClick(self._page.HWnd, (x,y))

    def doubleClick(self, xOffset=None, yOffset=None):
        '''鼠标左键双击
        @type xOffset: int
        @param xOffset: 距离控件区域左上角的横向偏移。
        @type yOffset: int
        @param yOffset: 距离控件区域左上角的纵向偏移。
        '''
        #2013/12/24 pear    修改点击实现
        x, y = self._get_cursor_pos(xOffset, yOffset)
        self._exClick(self._page.HWnd, (x,y), clicktype=MouseClickType.DoubleClick)
        
    def rightClick(self, xOffset=None, yOffset=None):
        '''鼠标右键单击
        @type xOffset: int
        @param xOffset: 距离控件区域左上角的横向偏移。
        @type yOffset: int
        @param yOffset: 距离控件区域左上角的纵向偏移。
        '''
        #2013/12/24 pear    修改点击实现
        x, y = self._get_cursor_pos(xOffset, yOffset)
        self._exClick(self._page.HWnd, (x,y), flag=MouseFlag.RightButton)

    def hover(self, xOffset=None, yOffset=None):
        '''鼠标悬停
        @type xOffset: int
        @param xOffset: 距离控件区域左上角的横向偏移。
        @type yOffset: int
        @param yOffset: 距离控件区域左上角的纵向偏移。
        '''
        #2013/12/24 pear    修改悬停实现
        x, y = self._get_cursor_pos(xOffset, yOffset)
        self._exHover(self._page.HWnd, (x, y))

    def drag(self, toX, toY):
        '''拖放到指定位置
        @type toX: int:
        @param toX: 拖放终点的屏幕坐标。
        @type toY: int:
        @param toY: 拖放终点的屏幕坐标。
        '''
        x, y = self._get_cursor_pos()
        Mouse.drag(x, y, toX, toY)

    def sendKeys(self, keys):
        '''发送按键命令
        @type keys: str
        @param keys: 要发送的按键
        '''
        self.click()
        Keyboard.inputKeys(keys, interval=0.1)

    def setFocus(self):
        '''设控件为焦点'''
        self._page.activate()
        self._driver.getProperty(self._locators, 'focus()')

    def __str__(self):
        return '<%s: "%s">' % (self.__class__.__name__, self._locator)

class MeanDriver(object):
    '''统一管理，对同一hwnd只创建一次的driver'''
    #2012-04-13    banana    创建
    drivers = {}

    def __init__(self, drvcls, *args, **kwargs):
        self._hwnd = args[0]
        self._drvcls = drvcls
        self._args = args
        self._kwargs = kwargs
        self._driver = None

    @property
    def driver(self):
        if (self._hwnd not in MeanDriver.drivers or
            not MeanDriver.drivers[self._hwnd][0]._running):
            driver = self._drvcls(*self._args, **self._kwargs)
            MeanDriver.drivers[self._hwnd] = [driver, 0]
        if not (self._driver and self._driver._running):
            self._driver = MeanDriver.drivers[self._hwnd][0]
            MeanDriver.drivers[self._hwnd][1] += 1
        return self._driver

    @driver.setter
    def driver(self, value):
        self._driver = value

    def __getattr__(self, name):
        def func(*args, **kwargs):
            life = 3
            while life > 0:
#                t0 = datetime.now()
                try:
                    work = getattr(self.driver, name)
                    ret = work(*args, **kwargs)
                    return ret
                except (AttributeError, ValueError):
                    raise
                except:
                    life -= 1
                    if life <= 0:
                        raise
                    time.sleep(1)
                finally:
                    pass
#                    print (datetime.now() - t0),
#                    print name, args, kwargs
        return func

    def start(self):
        pass

    def end(self):
        pass

    def close(self):
        drvinfo = MeanDriver.drivers[self._hwnd]
        if drvinfo[1] > 0:
            drvinfo[1] -= 1
        if drvinfo[1] == 0:
            self.driver.close()
            self.driver = None
            del MeanDriver.drivers[self._hwnd]
            pass

class LazyDriver(object):
    '''只在需要时创建连接的driver'''
    #2012-03-07    banana    创建
    def __init__(self, drvcls, *args, **kwargs):
        '''构造函数
        @type drvcls: callable
        @param drvcls: 获取实际driver的类或方法
        '''
        self._drvcls = drvcls
        self._args = args
        self._kwargs = kwargs
        self._hwnd = args[0]
        if "hwnd" in kwargs:
            self._hwnd = kwargs["hwnd"]
        self.success = 0
        self.failed = 0
        self.driver = None
        self.ref = 0

    def __getattr__(self, name):
        def func(*args, **kwargs):
            life = 3
            while life > 0:
#                t0 = datetime.now()
                try:
                    if not self.driver:
                        self.driver = self._drvcls(*self._args, **self._kwargs)
#                        print "@@@@ ", (datetime.now() - t0)
                    self.success += 1
                    work = getattr(self.driver, name)
                    ret = work(*args, **kwargs)
                    return ret
                except AttributeError:
                    raise
                except Exception as e:
                    if self.ref and self.driver:
                        self.close()
                    if not self.driver:
                        self.failed += 1
                        life += 0.8
                    life -= 1
#                    print e
                    if life <= 0:
                        raise
                    time.sleep(0.1)
                finally:
#                    print self.success, self.failed
                    if self.ref <= 0:
                        self.close()
#                    print (datetime.now() - t0),
#                    print name, args, kwargs,
#                    print "=====", self.ref, "======"
        return func

    def start(self):
        #self.ref += 1
        pass

    def end(self):
        if self.ref > 0:
            self.ref -= 1
            pass
        if self.ref <= 0:
            self.close()
            pass

    def close(self):
        if self.driver:
            self.driver.close()
            self.driver = None

class WrappedDriver(object):
    '''包裹Driver，用于在调用前进行有效性检查'''
    #2012/11/21 rambutan 添加
    
    def __init__(self, drvcls, *args, **kwargs):
        '''
        @type drvcls: callable
        @param drvcls: 获取实际driver的类或方法
        '''
        self._driver = drvcls(*args, **kwargs) #创建真正的driver实例
        self._callback = None
    
    @property
    def Callback(self):
        '''调用方法前的回调'''
        return self._callback
    
    @Callback.setter
    def Callback(self, callback):
        '''设置回调'''
        self._callback = callback
        
    def __getattr__(self, name):
        def func(*args, **kwargs):
            if self._callback:
                self._callback()
            real_func = getattr(self._driver, name)
            return real_func(*args, **kwargs)
        return func
    
if __name__ == "__main__":
    pass
