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
Web自动化的辅助类
'''
#2012-02-14    banana    创建
#2012-02-20    cherry  加入XPathParser
from tuia.mouse import Mouse        #@UnusedImport
from tuia.keyboard import Keyboard  #@UnusedImport
import re

__all__ = ["Mouse", "Keyboard", "Rect", "XPath", "XPathParser",
           "LazyDict", "WebElementAttributes", "WebElementStyles"]
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- Rect
class Rect(object):
    '''表示矩形区域'''
    #2012-02-14    banana    创建
    #2012-02-17    banana    添加__str__()方法
    def __init__(self, left=0, top=0, width=0, height=0):
        '''构造函数
        @type left: int
        @param left: 矩形区域的左上角横向坐标
        @type top: int
        @param top: 矩形区域的左上角纵向坐标
        @type width: int
        @param width: 矩形区域的宽度
        @type height: int
        @param height: 矩形区域的高度
        '''
        self.Left = left
        self.Top = top
        self.Width = width    
        self.Height = height
    
    def __str__(self):
        tmpl = "Left = %s, Top = %s, Width = %s, Height = %s"
        return tmpl % (self.Left, self.Top, self.Width, self.Height)

# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- XPath
class XPathParser(object):
    '''@desc: XPath解析'''
    #11/05/11    cherry    创建
    
    node_tname_pattern = '\w+|\.{1,2}|\*'
    node_stmts_pattern = '\[ *.+ *\]'
    node_index_pattern = '\[ *\d+ *\]'
    
    @classmethod
    def __split__(cls, xpaths):
        xpaths = re.split('\|(?= ?/.+$)', xpaths)
        splits_pattern = '//|/'
        splits = []
        for xpath in xpaths:
            roots = re.findall(splits_pattern, xpath)
            nodes = [item.strip() for item in re.split(splits_pattern, xpath)[1:]]
            if len(roots) == len(nodes) : splits.append((roots, nodes))
        return splits
    
    @classmethod
    def __parse_node_tname__(cls, node):
        if re.match(cls.node_tname_pattern, node):
            tname = re.sub(' *' + cls.node_stmts_pattern + ' *', '', node).strip()
            tname = re.sub(' *' + cls.node_index_pattern + ' *$', '', tname).strip()
            if re.match('^%s$' % cls.node_tname_pattern, tname):
                return tname
    
    @classmethod
    def __parse_node_stmts__(cls, node):
        if re.match(cls.node_tname_pattern + cls.node_stmts_pattern, node):
            stmts = re.sub('^ *' + cls.node_tname_pattern + ' *', '', node).strip()
            stmts = re.sub(' *' + cls.node_index_pattern + ' *$', '', stmts).strip()
            if re.match('^%s$' % cls.node_stmts_pattern, stmts):
                stmts = re.sub('^\[|\]$', '', stmts).strip()
                return stmts
    
    @classmethod
    def __parse_node_index__(cls, node):
        if re.match('.* *' + cls.node_index_pattern + ' *$', node):
            index = re.sub('.*(?= *' + cls.node_index_pattern + ' *$)', '', node).strip()
            if re.match('^%s$' % cls.node_index_pattern, index):
                index = re.sub('^\[|\]$', '', index).strip()
                return int(index)
    
    @classmethod
    def __parse__(cls, node):
        node_tname = cls.__parse_node_tname__(node)
        node_stmts = cls.__parse_node_stmts__(node)
        node_index = cls.__parse_node_index__(node)
        return node_tname, node_stmts, node_index
    
    @classmethod
    def parse(cls, xpaths=None):
        parsed = []
        if isinstance(xpaths, basestring):
            splits = cls.__split__(xpaths)
            for roots, nodes in splits:
                item = []
                for i, node in enumerate(nodes):
                    node_tname, node_stmts, node_index = cls.__parse__(node)
                    item.append((roots[i], node_tname, node_stmts, node_index))
                parsed.append(item)
        return parsed
    
    @classmethod
    def parse_for_frames(cls, xpaths=None):
        # XPathParser.parse_for_frames("//ifrmae//iframe//input")
        # 输出: ['//ifrmae', '//iframe', '//input']
        parsed = []
        if isinstance(xpaths, basestring):
            base_parsed = cls.parse(xpaths)
            cur = ''
            for i, item in enumerate(base_parsed):
                if i > 0 and len(cur) > 0:cur += '|'
                for node_path, node_tname, node_stmts, node_index in item:
                    cur += '%s%s' % (node_path, node_tname)
                    if node_stmts:cur += '[%s]' % node_stmts
                    if node_index:cur += '[%s]' % node_index
                    if node_tname.upper() in ['IFRAME', 'FRAME']:
                        parsed.append(cur)
                        cur = ''
            if len(cur) > 0:parsed.append(cur)
        return parsed

class XPath(str):
    '''表示XPath'''
    #2012-02-14    banana    创建
    def __init__(self, obj):
        str.__init__(self)
        self._obj = obj
        self._censored = None

    def __str__(self):
        if not self._obj:
            return ""
        obj = self._obj
        if not obj.strip("(").startswith("/"):
            if "#" in obj:
                pos = obj.find("#")
                nodename = obj[:pos] or "*"
                nodeid = obj[pos + 1:]
                t = nodename + nodeid
                if not nodeid or '"' in t or "'" in t:
                    obj = "/" + obj
                else:
                    obj = "//%s[@id='%s']" % (nodename, nodeid)
            else:
                obj = "/" + obj
            self._obj = obj
        return obj

    def __repr__(self):
        return repr(str(self))

    @property
    def Axis(self):
        axis = None
        pos = self._censor().strip("/").find("::")
        if pos > 0:
            axis = self.strip("/")[:pos]
        return axis

    @property
    def Nodetest(self):
        p1 = self._censor().strip("/").rfind("::")
        if p1 < 0:
            p1 = self._censor().strip("/").rfind("/")
        if p1 < 0:
            p1 = 0
        p2 = self._censor().strip("/").find("[", p1)
        if p2 < 0:
            p2 = len(self._censor().strip("/"))
        nodetest = self._censor().strip("/")[p1+1:p2]
        # print nodetest
        return nodetest

    def break_steps(self):
        ret = []
        p1 = 0
        p2 = 0
        p3 = 0
        s = str(self)
        t = self._censor()
        while True:
            if s[p1] == "(":
                p2 = p1
                while p2 >= 0:
                    p2 = t.find(")", p2 + 1)
                    if t.count("(", p1 + 1, p2) == t.count(")", p1 + 1, p2):
                        break
            else:
                p2 = p1 + 2
            p3 = t.find("/", p2)
            if p3 < 0:
                break
            if s[p3 - 1] == "(":
                p3 = p3 - 1
            ret.append(XPath(s[p1:p3]))
            p1 = p3
        ret.append(XPath(s[p1:]))
        return ret

    def break_frames(self):
        steps = self.break_steps()
        ret = []
        frame = ""
        for step in steps:
            frame += step
            if step.Nodetest.lower() in ["iframe", "frame"]:
                ret.append(XPath(frame))
                frame = ""
        if frame:
            ret.append(XPath(frame))
        return ret
    
    def _censor(self):
        if self._censored is not None:
            return self._censored
        ret = str(self)
        p3 = 0
        while p3 >= 0:
            p1 = ret.find("'", p3 + 1)
            p2 = ret.find('"', p3 + 1)
            if p1 < 0 and p2 < 0:
                break
            if p2 < 0 or 0 <= p1 < p2:
                p3 = ret.find("'", p1 + 1)
                if p3 < 0:
                    break
                ret = ret[:p1 + 1] + '"' * (p3 - p1 - 1) + ret[p3:]
            elif p1 < 0 or 0 <= p2 < p1:
                p3 = ret.find('"', p2 + 1)
                if p3 < 0:
                    break
                ret = ret[:p2 + 1] + "'" * (p3 - p2 - 1) + ret[p3:]
        self._censored = ret
        return ret
        
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- WebElementAttributes
class LazyDict(object):
    '''类字典容器，本身不存储数据，只在需要时调用相应函数实现读写操作'''
    #2012-02-21    banana    创建
    def __init__(self, getter, setter=None, lister=None):
        self._getter = getter
        self._setter = setter
        self._lister = lister

    def __getitem__(self, key):
        return self._getter(key)

    def __setitem__(self, key, value):
        if not self._setter:
            raise Exception("Item cannot be set.")
        return self._setter(key, value)

    def __delitem__(self):
        raise Exception("Item cannot be deleted.")

    def __iter__(self):
        if not self._lister:
            raise Exception("Items cannot be listed.")
        keys = self._lister()
        for key in keys:
            yield self.__getitem__(key)        

    def __len__(self):
        return len(self._lister())

    def __str__(self):
        keys = self._lister()
        ret = "{"
        for key in keys:
            ret += "%s: %s, " % (repr(key), repr(self[key]))
        return ret[:-2] + "}"

class WebElementAttributes(LazyDict):
    '''供WebElement的Attributes属性使用的类字典容器'''
    #2012-02-14    banana    创建
    #2012-02-21    banana    改为从LazyDict继承
    def __delitem__(self):
        raise Exception("Attribute cannot be deleted.")

class WebElementStyles(LazyDict):
    '''供WebElement的Styles属性使用的类字典容器'''
    #2012-02-21    banana    创建
    def __setitem__(self, key, value):
        raise Exception("Style cannot be set.")

    def __delitem__(self):
        raise Exception("Style cannot be deleted.")

if __name__ == '__main__':
    # print XPathParser.parse_for_frames("//div[@class = 'ui_boxy']//iframe[@id='ifram_login']//input[@id = 'login_button']")
    #d = LazyDict((lambda(a): a), (lambda(b): b), (lambda: ['a', 'b', 'c']))
    #print d
    xpath = XPath("(//div[text='helpArea']/span[text()])[1]/a")
    xpath = XPath("div[class='container']//iframe[id='embed'](//button|//input)[value='text']")
    xpath = XPath("div//a")
    xpath = XPath("//div[@class = 'ui_boxy']//iframe[@id='ifram_login']//input[@id = 'login_button']")
    #print xpath
    xpath = XPath('//iframe[@id="ptLoginFrame"]//iframe[@id="xui"]')
    print xpath.Nodetest
    #print xpath.break_frames()
