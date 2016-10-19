#-*- coding: UTF-8 -*-

'''
新版本inspector
'''

import os
import urllib, time
from win32com.client import Dispatch
import pywintypes
import win32gui
import win32process
import win32con
import win32api
from ctypes import *
import string
import zipfile

from tuia.util import remote_inject_dll
#from tuia.wincontrols import *
#from tuia.qpath import QPath

try:
    from __init__ import LOGGING_LEVEL
except:
    try:
        from tuia._autoweb.webkit._webkit.__init__ import LOGGING_LEVEL
    except:
        LOGGING_LEVEL = 1
#print LOGGING_LEVEL

def LOGGING(*args):
    level = args[0]
    #print level
    if LOGGING_LEVEL < level: return
    for item in args[1:]:
        
        print item,
    print
    
#def getTestStubPath(type):
#    '''
#    获取测试桩路径
#    @param type: 测试桩类型，取值为“cef”、“chrome”
#    @type  type: String
#    @return: 测试桩路径
#    '''
#    if type == 'cef':
#        return ur'\\kingsan-pc4\临时文件交换区\shadowyang\autoweb\cefspy\cefspy.dll'
#    elif type == 'chrome':
#        return ur'\\kingsan-pc4\临时文件交换区\shadowyang\autoweb\chromespy\chromespy.exe'
#    else:
#        raise Exception('参数取值错误')
#
#def copyTestStub(type):
#    '''
#    将测试桩从服务器拷贝到本地，并返回本地路径
#    '''    
#    import shutil
#    remote_path = getTestStubPath(type)
#    filename = os.path.split(remote_path)[1]
#    local_path = os.path.dirname(os.path.abspath(__file__)) + '\\' + filename
#    if os.path.exists(local_path):
#        os.remove(local_path)
#    shutil.copy(remote_path, local_path)
#    return local_path

def getQPlusInstallDir():
    '返回Q+安装目录'
    import win32api
    try:
        hkey = win32con.HKEY_CURRENT_USER
        subkey = r'SOFTWARE\Tencent\QPlus'
        hkey = win32api.RegOpenKey(hkey, subkey)
        qplusdir = win32api.RegQueryValueEx(hkey, 'Install')
        win32api.RegCloseKey(hkey)
        return qplusdir[0]
    except Exception, e:
        print e
        try:
            hkey = win32con.HKEY_LOCAL_MACHINE
            subkey = r'SOFTWARE\Tencent\QPlus'
            hkey = win32api.RegOpenKey(hkey, subkey)
            
            qplusdir = win32api.RegQueryValueEx(hkey, 'Install')
            win32api.RegCloseKey(hkey)
            return qplusdir[0]
        except:
            return None

def getPidByPort(port):
    '''根据端口号获取进程ID'''
    try:
        command ="netstat -aon|findstr 127.0.0.1:%d" %port
        portInfos = os.popen(command).readlines()         #只读取符合条件的一行即可；
        pidMap = {}
        #找到监听该端口的所有进程
        for line in portInfos:
            pid = line.split(" ")[-1]
            pidMap[pid] = pid
            
        #判断是否是浏览器进程
        for pid in pidMap:
            command ="tasklist|findstr " + pid
            procInfo = os.popen(command).readline()
            procName = procInfo.split(" ")[0]
            if procName == "chrome.exe" or procName == "360se.exe":
                return string.atoi(pid)
            
        raise Exception("get pid by port failed:　port = %d" %port)
    except Exception, e:
            raise Exception("get pid by port exception:　port = %d， errorInfo :%s" %(port,e))

def getFileVersion(filename):
    '''根据文件路径查看文件版本号'''
    try:
        info = win32api.GetFileVersionInfo(filename, "\\")
        ms = info['FileVersionMS']
        ls = info['FileVersionLS']
        version = '%d.%d.%d.%d' % (win32api.HIWORD(ms), win32api.LOWORD(ms), win32api.HIWORD(ls), win32api.LOWORD(ls))
        return version
    except:   
        return 0

class WebkitInspector(object):
    '''
    Inspector基类，封装公共部分
    '''
    
    js_base = '''
    var webkit_inspector = {
        selectNodes: function(sXPath) {  
                //alert(sXPath);
                var oXPathExpress = document.createExpression(sXPath, null);  
                var oResult = oXPathExpress.evaluate(document,  
                        XPathResult.ORDERED_NODE_ITERATOR_TYPE, null); 
                //alert(oResult);
                var aNodes = new Array();  
                if (oResult != null) {  
                    var oElement = oResult.iterateNext();  
                    while (oElement) {  
                        aNodes.push(oElement);  
                        oElement = oResult.iterateNext();  
                    }  
                }  
                if(aNodes.length == 0){
                    //alert('found node failed: '+sXPath);
                }
                return aNodes;  
            },  
        selectNode: function(sXPath) {  
                var oXPathExpress = document.createExpression(sXPath, null);  
                var oResult = oXPathExpress.evaluate(document,  
                        XPathResult.FIRST_ORDERED_NODE_TYPE, null); 
                //alert('oResult:'+oResult);
                return oResult.singleNodeValue;  
            },
        getFrameInfo: function(xpath){
                //获取指定frame信息，包括id和url
                var result = new Array();
                var node = this.selectNodes(xpath)[0];
                if(node == undefined) throw new Error('find '+xpath+' failed');
                if(node.name)
                    result.push(node.name);
                else
                    result.push(node.id);
                result.push(node.src);
                return result.toString();
            },
                    //获取元素的纵坐标 
        getTop: function(e){ 
                var offset=e.offsetTop; 
                if(e.offsetParent!=null) offset += this.getTop(e.offsetParent); 
                return offset; 
            },
            
            //获取元素的横坐标 
        getLeft: function(e){ 
                var offset=e.offsetLeft; 
                if(e.offsetParent!=null) offset += this.getLeft(e.offsetParent); 
                return offset; 
            },
            
        getElemRect: function(xpath){
                var node = this.selectNode(xpath);
                if(node == undefined) throw new Error('find '+xpath+' failed');

                var result = new Array();
                var rect = node.getBoundingClientRect();
                result.push(rect.left);
                result.push(rect.top);
                result.push(rect.width);
                result.push(rect.height);
                return result.toString();
            },
            
        bd0: document.createElement("div"),
        bd1: document.createElement("div"),
        bd2: document.createElement("div"),
        bd3: document.createElement("div"),
            
        showDiv: function(cnt){
                if(cnt % 2 != 0)
                {
                    document.body.appendChild(webkit_inspector.bd0);
                    document.body.appendChild(webkit_inspector.bd1);
                    document.body.appendChild(webkit_inspector.bd2);
                    document.body.appendChild(webkit_inspector.bd3);
                } else {
                    document.body.removeChild(webkit_inspector.bd0);
                    document.body.removeChild(webkit_inspector.bd1);
                    document.body.removeChild(webkit_inspector.bd2);
                    document.body.removeChild(webkit_inspector.bd3);
                }
                if (cnt){
                    cnt--;
                    setTimeout("webkit_inspector.showDiv(" + cnt + ")", 100);
                }
            },

        highlight: function(node){
                node.scrollIntoViewIfNeeded();
                var rect = node.getBoundingClientRect();
                var left= rect.left;
                var top = rect.top;
                var width = node.offsetWidth;
                var height = node.offsetHeight;
                //alert(''+left+','+top+','+width+','+'height');
                webkit_inspector.bd0.setAttribute("style", "border:solid 1px red;"
                    + "left:" + (left) + "px;top:" + (top) + "px;z-index:32767;"
                    + "width:" + (width) + "px;height:0px;position:fixed;");
                webkit_inspector.bd1.setAttribute("style", "border:solid 1px red;"
                    + "left:" + (left) + "px;top:" + (top) + "px;z-index:32767;"
                    + "width:0px;height:" + (height) + "px;position:fixed;");
                webkit_inspector.bd2.setAttribute("style", "border:solid 1px red;"
                    + "left:" + (left+width) + "px;top:" + (top) + "px;z-index:32767;"
                    + "width:0px;height:" + (height) + "px;position:fixed;");
                webkit_inspector.bd3.setAttribute("style", "border:solid 1px red;"
                    + "left:" + (left) + "px;top:" + (top+height) + "px;z-index:32767;"
                    + "width:" + (width) + "px;height:0px;position:fixed;");
                webkit_inspector.showDiv(3);
            }
        }
    '''
    
    def __init__(self):
        self._inspector = None
        self._frameMap = {} #缓存frameId，通过获取的frameTree的hash变化来更新此表
        self._frameTree = '' #保存framTree字符串，用于判断frame变化
        
    def _my_encode(self, text):
        '''
                    对于中文，统一处理成unicode编码
                    如“中国”，变成“\u4e2d\u56fd”
        '''
        if not isinstance(text, unicode):
            text = text.decode('utf8')
        return text.encode('raw_unicode_escape')
    
    def _my_decode(self, text):
        #raw_unicode_escape不能处理\uXXXX前面带有“\”的情况
        #return text.decode('raw_unicode_escape') 
        input = text
        end = len(input)
        pos = 0
        output = u""
        while pos < end:
            if pos <= end - 6 and input[pos] == '\\' and input[pos+1] == 'u':
                output += unichr(int(input[pos+2:pos+6], 16)) #\uXXXX转为unicode字符
                pos = pos + 6
            else:
                output += unicode(input[pos])
                pos += 1 
        return output
    
    def _xpath_encode(self, xpath):
        xpath = xpath.replace('\'', '"')
        return self._my_encode(xpath)
    
    def _xpaths_encode(self, xpath_list):
        for i in range(len(xpath_list)):
            xpath_list[i] = self._xpath_encode(xpath_list[i])
        #print xpath_list
    
    def _getFrameInfo(self, frame_xpaths):
        '''
        获取指定frame的信息，返回的是每一层frame的信息
        '''
        result = []
        self._xpaths_encode(frame_xpaths)
        for i in range(len(frame_xpaths)):
            js = '''
                webkit_inspector.result = webkit_inspector.getFrameInfo('%s');
            ''' % frame_xpaths[i]  
            result.append(self.evalScript(frame_xpaths[:i], js))
        return result
    
            
    def evalScript(self, frame_xpaths, script):
        '''
        @summary: 在指定frame中执行js
        @param frame_xpaths: 由frame的xpath路径分割得到的xpath数组
        @type  frame_xpaths: list
        @param script: 要执行的js脚本
        @type  script: string   
        '''
        frameId = self._getFrameId(frame_xpaths)
        script = self._my_encode(script)
        result = self._evalScript(script, frameId)

        flag = result[0]
        if flag != 'S' and flag != 'F':
            raise RuntimeError('EvalScript返回消息错误')
        
        result = result[1:]
        LOGGING(3, 'result', result)
        
        if flag == 'F':
            try:
                err_message = eval(result)
            except:
                result = result.replace('\n', r'\n')
                err_message = eval(result)
            if err_message['type'] == 'javascript' and \
                err_message['message'].find('webkit_inspector is not defined') >= 0:
                #注入js基础库
                self.evalScript(frame_xpaths, WebkitInspector.js_base)
                return self.evalScript(frame_xpaths, script)
            elif err_message['type'] == 'command' and \
                err_message['message'].find('Internal error: result is not an Object') >= 0:
                return self.evalScript(frame_xpaths, script)
            elif err_message['type'] == 'command' and \
                (err_message['message'] == 'Inspected frame has gone' or 
                 err_message['message'].find('Execution context with given id not found') >= 0 or
                 err_message['message'].find('Frame with given id not found') >= 0):
                #frame过期
                LOGGING(1, 'frame %s:%s has gone' % (str(frame_xpaths), frameId))

                self._frameMap = {}
                return self.evalScript(frame_xpaths, script)
            #去掉{try execpt}观察是否可能出现解码错误的问题
            err_info = u'错误类型：%s %s\n详细信息：%s' % (err_message['type'],
                                            err_message['name'],
                                            err_message['message'] + err_message['description'])
            err_info = self._my_decode(err_info).encode('utf8')
            raise RuntimeError(err_info)

        if result.endswith('\n'):
            result = result[:-1]
        #print 'result', repr(result), type(result)
        if result == 'null':
            return None
        try:
            result = eval(result)#返回的数据如果是字符串会有双引号：如："complete"
        except Exception as e:
            LOGGING(2, 'eval %s error' % result, e)
        if type(result) == str:
            result = self._my_decode(result)
            if isinstance(result, unicode):
                result = result.encode('utf8')
            return result
        else:
            return result
    
    def getFrameTree(self):
        '''
        获取frameTree
        '''
        result = self._getFrameTree()
        if not self._frameTree:
            self._frameTree = result
        else:
            if self._frameTree != result:
                #frame发生变化
                self._frameMap = {}
        #print 'frameTree', result
        return eval(result)
    
    def _getFrameTree(self):
        '''
        由子类实现
        '''
        pass
    
    def _getFrameId(self, frame_xpaths):
        '''
        获取指定frame的frameId
        '''
        if not frame_xpaths:
            return ''
        
        #2014/5/4 terisli frame match retry
        frame_id = None;
        try:
            times = 5;
            while times > 0:
                frameTree = self.getFrameTree()
                if self._frameMap.get(str(frame_xpaths)):
                    return self._frameMap[str(frame_xpaths)]
                LOGGING(3, frameTree)
                frameInfos = self._getFrameInfo(frame_xpaths)
                #print 'frameInfos', frameInfos
                for frameInfo in frameInfos:
                    if frameInfo[0] == '"':
                        frameInfo = frameInfo[1:]
                    if frameInfo[-1] == '"':
                        frameInfo = frameInfo[:-2]
                    pos = frameInfo.index(',');
                    frameName = frameInfo[0:pos];
                    frameUrl = frameInfo[pos+1:];
                    #frameInfo = frameInfo.split(',')
                    #frameName = frameInfo[0]
                    #frameUrl = frameInfo[1] #urllib.unquote(frameInfo[1]) #确定一下是否需要unquote
                    LOGGING(3, frameName, frameUrl)
                    try:
                        frameTree = self._getFrameIdHelper(frameTree, frameName, frameUrl)
                    except:
                        pass
                frame_id = frameTree['frame']['id']
                if frame_id:
				    break;
                time.sleep(1);
                times = times - 1;
        except:
            pass

        #frame_id = self._getFrameIdHelper(frameTree, frameName, frameUrl)
        frame_id = frameTree['frame']['id']
        if not frame_id:
            raise RuntimeError('查找FrameId %s 失败' % frameName)
        self._frameMap[str(frame_xpaths)] = frame_id
        
        #print self._frameMap
        return frame_id
    
    def _getFrameIdHelper(self, frame_node, name='', url=''):
        if not name and not url:
            raise RuntimeError('name和url不能同时为空')    
        frame = frame_node['frame']
#        print frame['name'] , name
#        print frame['url'], url
#        print urllib.unquote(frame['url']) , url
#        if frame['name'] == name:# and urllib.unquote(frame['url']) == url:
#            return frame['id']
#        if frame_node.has_key('childFrames'):
#            for child_frame in frame_node['childFrames']:
#                result = self._getFrameIdHelper(child_frame, name, url)
#                if result:
#                    return result
#        return ''
        if not frame_node.has_key('childFrames'):
            raise RuntimeError('查找Frame %s 出错：%s' % (name, str(frame_node)))
        for child_frame in frame_node['childFrames']:
            frame = child_frame['frame']
            if name and frame['name'] == name: #存在name时直接比较name
                return child_frame
            if frame['url'] == url:
                return child_frame
        raise RuntimeError('未找到Frame：%s' % name)
            
    
    def readyState(self, frame_xpaths):
        '''
        '''
        js = '''
        webkit_inspector.result = document.readyState;
        '''
        result = self.evalScript(frame_xpaths, js)
        #print result
        return result 
    
    def waitForReady(self, frame_xpaths, timeout=10):
        '''
        '''
        t = time.time()
        time.sleep(0.2) #等待页面开始跳转，防止过早返回
        while time.time() - t < timeout:
            state = self.readyState(frame_xpaths)
            if state == 'complete':
                return True
            time.sleep(0.5)
        return False
    
    def getElementRect(self, elem_xpaths, rav=True):
        '''
        获取元素在页面中的相对坐标
        @type rav: Bool
        @param rav: 是否是相对于当前frame的坐标
        '''
        self._xpaths_encode(elem_xpaths)
        frame_xpaths = elem_xpaths[:-1]
        elem_xpath = elem_xpaths[-1]
        
        return self._getElementRect(frame_xpaths, elem_xpath, rav)
    
    def _getElementRect(self, frame_xpaths, elem_xpath, rav):
        '''
        获取元素在页面中的相对坐标
        '''
        self._xpaths_encode(frame_xpaths)
        elem_xpath = self._xpath_encode(elem_xpath)
        
        js = '''
            webkit_inspector.result = webkit_inspector.getElemRect('%s');
        ''' % elem_xpath  
        result = self.evalScript(frame_xpaths, js)
        result = result.replace('"', '')
        #print result
        result = result.split(',')
        for i in range(len(result)):
            result[i] = float(result[i])
        if not rav and frame_xpaths:
            result1 = self._getElementRect(frame_xpaths[:-1], frame_xpaths[-1], rav)
            for i in range(2):
                result[i] += result1[i]
        return result
    
    def nodeExist(self, elem_xpaths):
        '''
        判断节点是否存在
        '''
        self._xpaths_encode(elem_xpaths)
        frame_xpaths = elem_xpaths[:-1]
        elem_xpath = elem_xpaths[-1]
        
        js = '''
            webkit_inspector.result = webkit_inspector.selectNodes('%s');
            if(webkit_inspector.result.length > 0)
                webkit_inspector.result = 1;
            else
                webkit_inspector.result = 0;
        ''' % elem_xpath
        result = self.evalScript(frame_xpaths, js)
        #result = int(result)
        #print result, type(result)
        if result:
            return True
        else:
            return False
    
    def getNodeListLength(self, elem_xpaths):
        '''
        获取节点数量
        '''
        self._xpaths_encode(elem_xpaths)
        frame_xpaths = elem_xpaths[:-1]
        elem_xpath = elem_xpaths[-1]
        
        js = '''
            webkit_inspector.result = webkit_inspector.selectNodes('%s');
            webkit_inspector.result = webkit_inspector.result.length;
        ''' % elem_xpath
        result = self.evalScript(frame_xpaths, js)
        return result
    
    def getStyle(self, elem_xpaths, style_name):
        '''
        '''
        self._xpaths_encode(elem_xpaths)
        frame_xpaths = elem_xpaths[:-1]
        elem_xpath = elem_xpaths[-1]
        
        js = '''
            webkit_inspector.node = webkit_inspector.selectNode('%s');
            if(webkit_inspector.node == undefined) throw('find %s failed');
            webkit_inspector.result = getComputedStyle(webkit_inspector.node,null).getPropertyValue('%s');
        ''' % (elem_xpath, elem_xpath, style_name)
        return self.evalScript(frame_xpaths, js)
    
    def getProperty(self, elem_xpaths, prop_name):
        '''
        获取xpath指定的节点的特定值，例如：node.innerHTML
        '''
        self._xpaths_encode(elem_xpaths)
        frame_xpaths = elem_xpaths[:-1]
        elem_xpath = elem_xpaths[-1]
        
        js = '''
            webkit_inspector.node = webkit_inspector.selectNodes('%s')[0];
            if(webkit_inspector.node == undefined) throw('find %s failed');
            webkit_inspector.result = webkit_inspector.node.%s;
        ''' % (elem_xpath, elem_xpath, prop_name)
        return self.evalScript(frame_xpaths, js)
    
    def setProperty(self, elem_xpaths, prop_name, value):
        '''
        设置xpath指定的节点的特定值，例如：node.innerHTML
        '''
        self._xpaths_encode(elem_xpaths)
        frame_xpaths = elem_xpaths[:-1]
        elem_xpath = elem_xpaths[-1]
        
        if value is None:
            value = ''
        if type(value) == str:
            value = self._my_encode(value)
            value = '\'' + value + '\''
        js = '''
            webkit_inspector.node = webkit_inspector.selectNodes('%s')[0];
            if(webkit_inspector.node == undefined) throw('find %s failed');
            webkit_inspector.result = (webkit_inspector.node.%s = %s);
        ''' % (elem_xpath, elem_xpath, prop_name, value)
        return self.evalScript(frame_xpaths, js)
    
    def getAttribute(self, elem_xpaths, attr_name):
        '''
        获取属性值
        '''
        self._xpaths_encode(elem_xpaths)
        frame_xpaths = elem_xpaths[:-1]
        elem_xpath = elem_xpaths[-1]
        
        js = '''
            webkit_inspector.node = webkit_inspector.selectNodes('%s')[0];
            if(webkit_inspector.node == undefined) throw('find %s failed');
            webkit_inspector.result = webkit_inspector.node.getAttribute('%s');
        ''' % (elem_xpath, elem_xpath, attr_name)
        return self.evalScript(frame_xpaths, js)
    
    def setAttribute(self, elem_xpaths, attr_name, value):
        '''
        设置属性值
        '''
        self._xpaths_encode(elem_xpaths)
        frame_xpaths = elem_xpaths[:-1]
        elem_xpath = elem_xpaths[-1]
        
        if type(value) == str:
            value = self._my_encode(value)
            value = '\'' + value + '\''
        js = '''
            webkit_inspector.node = webkit_inspector.selectNodes('%s')[0];
            if(webkit_inspector.node == undefined) throw('find %s failed');
            webkit_inspector.result = webkit_inspector.node.setAttribute('%s', %s);
        ''' % (elem_xpath, elem_xpath, attr_name, value)
        return self.evalScript(frame_xpaths, js)
    
    def highlight(self, elem_xpaths):    
        '''
        对由xpath指定的控件做高亮
        '''
        LOGGING(3, 'highlight', elem_xpaths)
        self._xpaths_encode(elem_xpaths)
        frame_xpaths = elem_xpaths[:-1]

        elem_xpath = elem_xpaths[-1]
        js = '''
        webkit_inspector.node = webkit_inspector.selectNode('%s');
        //alert(webkit_inspector.node);
        if(webkit_inspector.node == undefined) throw('find %s failed');
        webkit_inspector.highlight(webkit_inspector.node);
        ''' % (elem_xpath, elem_xpath)
        self.evalScript(frame_xpaths, js)
        return True
    
    def url(self, frame_xpaths):
        '''获取url'''
        self._xpaths_encode(frame_xpaths)
        js = '''
        location.href;
        '''
        return self.evalScript(frame_xpaths, js)
    
    def close(self):
        '''
        关闭当前页面
        '''
        pass
    
def findHelpWnd(hWndMain=0, pid=0, wnd_class='CefSpy'):
    '''
    查找辅助窗口句柄
    '''
    if pid:
        pid0 = pid
    elif hWndMain:
        pid0 = c_int(0)
        windll.user32.GetWindowThreadProcessId(hWndMain, byref(pid0)) #获取进程ID
        pid0 = pid0.value
        if not pid0:
            raise Exception('窗口句柄错误')
    else:
        raise Exception('hWndMain和pid不能同时为空')
    
    try:
        handle = win32gui.FindWindow(wnd_class + 'Wnd', wnd_class)
    except pywintypes.error, e:
        if e[0] == 2: #在某些版本上找不到窗口时会直接抛出异常
            return None
        else:
            raise e

    while handle:
#        print handle
#        title = win32gui.GetWindowText(handle)
#        title = title.decode('gbk')
#        print title
        pid = c_int(0)
        windll.user32.GetWindowThreadProcessId(handle, byref(pid))
        if pid.value == pid0:
            return handle
        handle = win32gui.FindWindowEx(None, handle, wnd_class + 'Wnd', wnd_class)
    #raise Exception('查找辅助窗口失败，请确认已注入cefspy.dll')
    return None

def getProcessPath(pid):
    '''
    获取窗口所在进程的目录
    '''
    buffer = create_unicode_buffer(260)
    handle = windll.kernel32.OpenProcess(0x001F0FFF, 0, pid)
    windll.psapi.GetModuleFileNameExW(handle, None, buffer, 260)
    windll.kernel32.CloseHandle(handle)
    path = buffer.value
    path = str(path);
    return os.path.split(path)[0]

class PROCESSENTRY32(Structure):
    _fields_ = [('dwSize', c_uint),
                ('cntUsage', c_uint),
                ('th32ProcessID', c_uint),
                ('th32DefaultHeapID', c_void_p),
                ('th32ModuleID', c_uint),
                ('cntThreads', c_uint),
                ('th32ParentProcessID', c_uint),
                ('pcPriClassBase', c_int),
                ('dwFlags', c_uint),
                ('szExeFile', c_wchar * 260)]
    
class THREADENTRY32(Structure):
    _fields_ = [('dwSize', c_ulong),
                ('cntUsage', c_ulong),
                ('th32ThreadID', c_ulong),
                ('th32OwnerProcessID', c_ulong),
                ('tpBasePri', c_long),
                ('tpDeltaPri', c_long),
                ('dwFlags', c_ulong)
                ]
class MODULEENTRY32(Structure):
    _fields_ = [('dwSize', c_ulong),
                ('th32ModuleID', c_ulong),
                ('th32ProcessID', c_ulong),
                ('GlblcntUsage', c_ulong),
                ('ProccntUsage', c_ulong),
                ('modBaseAddr', c_void_p),
                ('modBaseSize', c_ulong),
                ('hModule', c_ulong),
                ('szModule', c_wchar * 256),
                ('szExePath', c_wchar * 260)]

def getProcessInfo(pid=0):
    '''
    获取进程信息
    '''
    INVALID_HANDLE_VALUE = -1
    TH32CS_SNAPPROCESS = 0x00000002
    result = []
    hSnapShot = windll.kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, pid)
    if hSnapShot == INVALID_HANDLE_VALUE:
        return False
    pe = PROCESSENTRY32()
    pe.dwSize = sizeof(PROCESSENTRY32)
    
    bResult = windll.kernel32.Process32FirstW(hSnapShot, byref(pe))
    if not bResult: 
        print 'err', windll.kernel32.GetLastError()
        return False
    while bResult:
        item = {'pid': pe.th32ProcessID,
                'ppid': pe.th32ParentProcessID,
                'nThreads': pe.cntThreads,
                'pName': pe.szExeFile}
        if pid:
            if pid == pe.th32ProcessID:
                result.append(item)
        else:
            result.append(item)
        bResult = windll.kernel32.Process32NextW(hSnapShot, byref(pe))
    return result

def getModuleInfo(pid, dll_name):
    '''获取DLL信息'''
    dll_name = dll_name.lower()
    INVALID_HANDLE_VALUE = -1
    TH32CS_SNAPMODULE = 0x00000008
    hSnapShot = windll.kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPMODULE, pid)
    if hSnapShot == INVALID_HANDLE_VALUE:
        return False
    me = MODULEENTRY32()
    me.dwSize = sizeof(MODULEENTRY32)
    bResult = windll.kernel32.Module32FirstW(hSnapShot, byref(me))
    if not bResult: 
        print 'err', windll.kernel32.GetLastError()
        return False
    modBase = 0
    while bResult:
        #print modBase, modSize, me.szExePath
        if me.szModule.lower() == dll_name:
            #print me.szExePath
            modBase = me.hModule
            modSize = me.modBaseSize
            windll.kernel32.CloseHandle(hSnapShot)
            return {'modBase': modBase, 'modSize': modSize}
        bResult = windll.kernel32.Module32NextW(hSnapShot, byref(me))
    windll.kernel32.CloseHandle(hSnapShot)
    return {}

def remote_unload_dll(pid, dll_name):
    '''卸载远程进程中的模块'''
    mod_info = getModuleInfo(pid, dll_name)
    if not mod_info:
        return False
    #print 'mod: %X' % modBase
    hProcess = windll.kernel32.OpenProcess(win32con.PROCESS_ALL_ACCESS, False, pid)
    if not hProcess: return False
    hKernel = windll.kernel32.GetModuleHandleA("kernel32.dll")
    ldlib_addr = windll.kernel32.GetProcAddress(hKernel , "FreeLibrary")
    #print 'FreeLibrary', ldlib_addr
    windll.kernel32.CreateRemoteThread(hProcess, None, None,
                ldlib_addr, mod_info['modBase'], None, None)
    windll.kernel32.CloseHandle(hKernel)
    windll.kernel32.CloseHandle(hProcess)
    return True

class CefInspector(WebkitInspector):
    '''
    使用新版测试桩的版本
    '''
    def __init__(self, hWnd):
        WebkitInspector.__init__(self)
        hWndCefSpy = findHelpWnd(hWnd)
        if not hWndCefSpy:
            #注入进程
            pid = c_int(0)
            windll.user32.GetWindowThreadProcessId(hWnd, byref(pid))
            LOGGING(2, '注入进程', pid.value)
            exe_path = getProcessPath(pid.value)
            if exe_path.find('QPlus') > 0:
                dll_path = getQPlusInstallDir() + r'\cefspy.dll'
            else:
                dll_path = getProcessPath(pid.value) + r'\cefspy.dll'
            if not os.path.exists(dll_path):
                raise Exception('libcef测试桩%s不存在' % dll_path)
            remote_inject_dll(pid.value, dll_path)
            timeout = 10000
            import win32event
            event_name = 'CefSpyWnd_CreateEvent_%X' % pid.value
            try:
                hEvent = win32event.OpenEvent(0, False, event_name)
            except:
                hEvent = win32event.CreateEvent(None, False, False, event_name)
            #print type(hEvent)
            ret = windll.kernel32.WaitForSingleObject(hEvent.handle, timeout)
            if ret == 0xFFFFFFFF:
                raise Exception('WaitForSingleObject failed')
            elif ret == 0x00000102:
                raise Exception('cefspy.dll注入超时')
            #elif ret == 0x00000000:
            hWndCefSpy = findHelpWnd(hWnd)
            if not hWndCefSpy:
                raise Exception('Impossible!')
            #windll.user32.SendMessageW(hWnd, win32con.WM_USER + 0x111, None, None)
        LOGGING(2, 'REGISTER_CLASS_OBJECT')
        windll.user32.SendMessageW(hWndCefSpy, win32con.WM_USER + 101, None, None)
        self._inspector = Dispatch('cefspy.CefInspector')
        self._inspector.InstallHook(hWnd)
        self._hWnd = hWnd
        
    def _evalScript(self, script, frameId):
        '''
        封装EvalScript接口
        '''
        LOGGING(3, 'evalScript', frameId, script)
        time1 = time.clock()
        result = self._inspector.EvalScript(self._hWnd, script, frameId)
        LOGGING(3, 'evalScript:', time.clock() - time1)
        #print result
        return result 
    
    def _openDevTools(self):
        self._inspector.OpenDevTools(self._hWnd)
        
    
    def _getFrameTree(self):
        '''
        获取frameTree
        '''
        LOGGING(3, 'getFrameTree')
        time1 = time.clock()
        result = self._inspector.GetFrameTree(self._hWnd)
        LOGGING(3, 'getFrameTree', time.clock() - time1)
        return result

class QQCefInspector(WebkitInspector):
    def __init__(self, pid, client_id):
        '''
        @param pid: 渲染进程ID 
        @param cefbrowser: CefBrowser类实例指针
        '''
        WebkitInspector.__init__(self)
        self._client_id = client_id
        LOGGING(3, 'clientid=', self._client_id)
        hWndCefSpy = findHelpWnd(pid=pid, wnd_class='QQCefSpy')
        if not hWndCefSpy:
            #尚未注入
            qq_bin = getProcessPath(pid)
            qqcefspy_path = os.path.join(qq_bin, 'qqcefspy.dll')
            libcef_path = os.path.join(qq_bin, 'libcef.dll')
            if not os.path.exists(qqcefspy_path):
                raise Exception('libcef测试桩%s不存在' % qqcefspy_path)
            remote_inject_dll(pid, qqcefspy_path)
            timeout = 10000
            import win32event
            event_name = 'CefSpyWnd_CreateEvent_%X' % pid
            try:
                hEvent = win32event.OpenEvent(0, False, event_name)
            except:
                hEvent = win32event.CreateEvent(None, False, False, event_name)
            #print type(hEvent)
            ret = windll.kernel32.WaitForSingleObject(hEvent.handle, timeout)
            if ret == 0xFFFFFFFF:
                raise RuntimeError('WaitForSingleObject failed') 
            elif ret == 0x00000102:
                raise RuntimeError('qqcefspy.dll注入超时')
            hWndCefSpy = findHelpWnd(pid=pid, wnd_class='QQCefSpy')
            if not hWndCefSpy:
                raise RuntimeError('未找到辅助测试窗口')
        #print 'hWndCefSpy', hWndCefSpy
        LOGGING(2, 'REGISTER_CLASS_OBJECT')
        windll.user32.SendMessageW(hWndCefSpy, win32con.WM_USER + 101, None, None)
        self._inspector = Dispatch('qqcefspy.QQCefInspector')
        self._inspector.InstallHook(client_id)
                
    def _evalScript(self, script, frameId):
        '''
        封装EvalScript接口
        '''
        LOGGING(3, 'evalScript', frameId, script)
        time1 = time.clock()
        result = self._inspector.EvalScript(self._client_id, script, frameId)
        LOGGING(3, 'evalScript:', time.clock() - time1)
        #print result
        return result 
    
    def _openDevTools(self):
        self._inspector.OpenDevTools(self._client_id)
    
    def _getFrameTree(self):
        '''
        获取frameTree
        '''
        LOGGING(3, 'getFrameTree')
        time1 = time.clock()
        result = self._inspector.GetFrameTree(self._client_id)
        LOGGING(3, 'getFrameTree', time.clock() - time1)
        return result
        
class ChromeInspector(WebkitInspector):
    '''
    封装了Chrome测试桩的功能
    由于对于Chrome同一个远程调试端口上打开的页面，建立后一个页面会自动销毁前一个页面的inspector对象
    因此对于每次调用需要动态获取测试桩实例
    '''
    
    def __init__(self, port, url, title=''):
        WebkitInspector.__init__(self)
        self._port = port
        
        if not url.lower() == "about:blank" and not url.startswith('http://') and not url.startswith('https://') :
            url = 'http://' + url
    
        self._url = url
        self._title = title
        
        try:
            inspector_new_flag = True
            self._inspector = self._createDispatch()
            #如果存在的话， 判断当前的chromespy是否是最新的
            if not self._checkInspectorNew():
                inspector_new_flag = False
            
        except pywintypes.com_error, e:
            if e[0] == -2147024894 or e[0] == -2147221005:
                #系统找不到指定的文件。
                #无效的类字符串
                #注释掉原先注册chromespy.exe的方式，使用兼容egg包注册的方式
                '''
                stub_path = os.path.dirname(os.path.abspath(__file__)) + r'\chromespy.exe'
                if not os.path.exists(stub_path):
                    stub_path = os.path.dirname(os.path.abspath(__file__)) + r'\..\..\chromespy.exe'
                    if not os.path.exists(stub_path):
                        raise Exception('未找到chromespy.exe')
                os.system('"' + stub_path + '" -RegServer')
                self._inspector = self._createDispatch()
                '''
                inspector_new_flag = False
            else:
                raise e
        
        if not inspector_new_flag:
            inspector_path = self._getInspectorPath()
            os.system('"' + inspector_path + '" -RegServer')
            self._inspector = self._createDispatch()
            
        #print self._inspector
        self._connectPage()
        self._pid = getPidByPort(self._port)  #初始化时，通过端口号查找浏览器窗口的进程ID
    
    
    def _checkInspectorNew(self):
        #记录当前最新版本号和clsid,更新chromespy时需要更新对应项
        tag_version = "1.0.0.3"    
        chromespy_clsid_path = r"CLSID\{925577EB-0E8C-4812-9EBC-0C10A2635749}\LocalServer32" 
        try:
            #get chromespy path in the register
            regkey = win32api.RegOpenKey(win32con.HKEY_CLASSES_ROOT, chromespy_clsid_path, 0, win32con.KEY_READ)
            keyvalue = win32api.RegQueryValueEx(regkey,'')[0]
            win32api.RegCloseKey(regkey)
            
            #check the inspector is new or not
            last_inspector_path = keyvalue.strip('"\'')
            if os.path.exists(last_inspector_path):
                register_version = getFileVersion(last_inspector_path)
                if register_version < tag_version:
                    return False
                else:
                    return True
            return False
        except Exception, e:
            raise e
    
    def _getInspectorPath(self):
        #if the file is not in the egg package, just return the path
        cur_path = os.path.dirname(os.path.realpath(__file__))
        inspector_path = os.path.join(cur_path, "chromespy.exe")
        if os.path.exists(inspector_path):
            return inspector_path
        
        #decompress form the egg package
        decompress_path = os.path.join(os.getenv('APPDATA'), 'chromespy')
        chromespy_path = 'tuia/_autoweb/webkit/_webkit/chromespy.exe'
        root, path = os.path.splitdrive(cur_path)
        tag_path = root + '\\'
        paths = path.strip('\\').split('\\')
        try:
            for item in paths:
                tag_path = os.path.join(tag_path, item)
                if zipfile.is_zipfile(tag_path) or (os.path.isfile(tag_path) and os.path.splitext(tag_path)[1].lower()) in ['exe', 'egg']:
                    zp = zipfile.ZipFile(tag_path, mode="r", compression=zipfile.ZIP_DEFLATED)
                    inspector_path = zp.extract(chromespy_path,decompress_path)
                    zp.close()
                    return inspector_path
        except Exception, e:
            raise Exception('chromespy正在使用，解压缩chromespy到相关目录失败，请关闭浏览器之后重试')
    
    def _createDispatch(self):
        '''
        创建COM对象
        '''
        LOGGING(2, 'createDispatch')
        import traceback
        #
        for i in range(3):
            try:
                return Dispatch('chromespy.ChromeInspector')
            except Exception, e:
                if i == 2:
                    traceback.print_exc()
                    raise e
                time.sleep(1)
        
    
    def _connectPage(self):
        '''
        连接Chrome中的某个页面
        '''
        timeout = 10

        windll.kernel32.OutputDebugStringA('%d\n' % windll.kernel32.GetTickCount())
        try:
            self._inspector.ConnectChrome(self._port, timeout)
        except:
            raise RuntimeError('Connect to Chrome at port %d failed' % self._port)
        
        found = False
        retrytimes = 0
        #原先设置超时10s，现在改为重试3次，减少耗时；
        while retrytimes < 3:
            url_list = self._inspector.GetUrlList(self._port)
            import json, re
            url_list = json.loads(url_list)
            pattern = re.compile(self._url)
            
            for url in url_list:
                if url == self._url or pattern.match(url):
                    self._url = url
                    found = True
                    break
            if found: break
            retrytimes = retrytimes + 1
            time.sleep(1)
        if not found:
            raise RuntimeError('未匹配到URL: %s' % self._url)
        websocket_url = self._inspector.GetWebSocketUrl(self._port, self._url, self._title)
        #print websocket_url
        if not websocket_url:
            raise RuntimeError('请确认在Chrome中已经打开了被测页面: %s' % self._url)
        try:
            self._inspector.ConnectPage(self._port, websocket_url)
            return True
        except Exception, e: #切换url
            LOGGING(1, e)
            #time.sleep(0.1) #等待旧连接中断
            self._inspector = self._createDispatch()
            return self._connectPage()
        return False
    
    
    def _getInstance(self):
        if not self._inspector:
            self._inspector = self._createDispatch()
        else:
            try:
                self._inspector.Test()
            except Exception, e:
                LOGGING(1, e)
                self._inspector = self._createDispatch()
                self._connectPage()
        return self._inspector
    
    def _getFrameTree(self):
        '''
        获取frameTree
        '''
        LOGGING(3, 'getFrameTree')
        time1 = time.clock()
        result = self._getInstance().GetFrameTree(self._port)
        LOGGING(3, 'getFrameTree', time.clock() - time1)
        return result
    
    def _evalScript(self, script, frameId):
        '''
        封装EvalScript接口
        '''
        LOGGING(3, 'evalScript', frameId, script)
        time1 = time.clock()
        result = self._getInstance().EvalScript(self._port, script, frameId)
        LOGGING(3, 'evalScript:', time.clock() - time1)
        #print result
        return result 
    
    def close(self):
        '''
        '''
        try:
            self._inspector.Close(self._port)
        except: #如果实例已经无效，就没有必要再关闭了
            pass
        self._inspector = None
        
    def getPid(self):
        '''
        返回当前浏览器窗口的进程ID
        '''
        return self._pid
    
    def navigate(self, url):
        ''' 
        页面跳转 ，navigate会自动等待页面跳转完成
        '''
        #2014/03/12 miawu    新建,调用chromespy.exe提供的接口执行即可
        self._getInstance().Navigate(self._port,url)
    
if __name__ == '__main__':
    pass
