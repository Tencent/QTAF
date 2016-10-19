# -*- coding: utf-8 -*-
'''cef3的webview实现
'''

#2016/01/05  guyingzhao   创建文件
#2016/01/26  guyingzhao   完善实现
#2016/03/18  guyingzhao   支持非qq产品，并且以qpath查找辅助窗口，防止不同进程干扰
#2016/07/13  guyingzhao   修复返回时反斜杠转义错误和优化编码格式

import re


from qt4w import XPath
from qt4w.webcontrols import WebPage, WebElement
from qt4w.webdriver.webkitwebdriver import WebDriverBase
from qt4w.util import encode_wrap

from testbase import logger
from tuia.util import Timeout,Process
from tuia.webview.base import WebViewBase
from tuia.qpath import QPath
from tuia.gfcontrols import Control
from tuia import wincontrols
from tuia.util import remote_inject_dll
from tuia.mouse import MouseFlag, MouseClickType

class Cef3WebView(WebViewBase):
    '''QQ内部的cef3内嵌页面
    '''
    
    class _Msg(object):
        '''WebKit消息定义
        '''
        GET_RENDERPID_CLIENTID = 1  # 获取跨进程WebKit对应的渲染进程ID和ClientID
        
    def __init__(self, root=None, locator=None, timeout=10,offscreen_win=None):
        self._window = Control(root, locator)
        if offscreen_win==None:
            offscreen_win=wincontrols.Control(root=self._window.HWnd)
        super(Cef3WebView, self).__init__(self._window,WebDriverBase(self),offscreen_win)
        Timeout().retry(lambda x:x._window.ProcessId, (self,), RuntimeError, lambda x:x!=4294967295) 
        self._window.Value = [self._Msg.GET_RENDERPID_CLIENTID]
        if not self._window.Value:
            raise RuntimeError("获取渲染进程pid和client id失败")
        self._render_pid = self._window.Value[0]
        self._client_id = self._window.Value[1]
        self._inspector = self._install_cef_hook()
        self._frameMap = {}  # 缓存frameId，通过获取的frameTree的hash变化来更新此表
        self._frameTree = ''  # 保存framTree字符串，用于判断frame变化
    
    def _install_cef_hook(self):
        '''获取内部实现接口对象
        '''
        import os, win32con, win32com.client, win32api, win32gui
        qp=QPath("/ClassName='QQCefSpyWnd'&&ProcessId='%d'" % self._render_pid)
        wins=qp.search()
        pyhwnd=None
        if wins:
            pyhwnd=wins[0].HWnd
        if not pyhwnd:
            # 尚未注入，需要注入qqcefspy.dll
            exe_path=os.path.dirname(Process(self._render_pid).ProcessPath)
            dll_path = os.path.join(exe_path,'qqcefspy.dll')
            if not os.path.exists(dll_path):
                raise RuntimeError('没有找到测试桩文件%s' % dll_path.encode('utf8'))
            remote_inject_dll(self._render_pid, dll_path)
            timeout = 10000
            import win32event
            from ctypes import windll
            event_name = 'CefSpyWnd_CreateEvent_%X' % self._render_pid
            try:
                hEvent = win32event.OpenEvent(0, False, event_name)
            except:
                hEvent = win32event.CreateEvent(None, False, False, event_name)
            # print type(hEvent)
            # ret = windll.kernel32.WaitForSingleObject(hEvent.handle, timeout)
            ret = win32event.WaitForSingleObject(hEvent.handle, timeout)
            if ret == 0xFFFFFFFF:
                raise RuntimeError('WaitForSingleObject failed') 
            elif ret == 0x00000102:
                raise RuntimeError('qqcefspy.dll注入超时')
            wins=qp.search()
            if wins:
                pyhwnd=wins[0].HWnd
            if not pyhwnd:
                raise RuntimeError('未找到辅助测试窗口')
        
        # windll.user32.SendMessageW(assist_wnd.HWnd, win32con.WM_USER + 101, None, None)
        win32gui.SendMessage(pyhwnd, win32con.WM_USER + 101, None, None)
        inspector = win32com.client.Dispatch('qqcefspy.QQCefInspector')
        inspector.InstallHook(self._client_id)
        return inspector
    
    def _get_frame_id(self, frame_xpaths):
        '''获取指定xpath的frame id
        '''
        if not frame_xpaths:
            return ''
        elif len(frame_xpaths)>1:
            raise RuntimeError("当前不支持frame xpath长度大于2的情况")

        frame_id = None
        if self._frameMap.get(str(frame_xpaths)):
            return self._frameMap.get(str(frame_xpaths))
        else:
            results=re.search('"\w+"|\'\w+\']',frame_xpaths[0])
            if results:
                frame_name=results.group(0)[1:-1]
            else:
                raise RuntimeError("无法获取frame：%s的名字" % frame_xpaths)
            frame_id=Timeout(10,1).retry(self._find_frame,(frame_name,),(),lambda x:x<>None)
            self._frameMap[str(frame_xpaths)] = frame_id
            return frame_id
        
    def _find_frame(self,frame_name):
        '''查找frame的id
        '''
        def _handle_single_frame(single_frame,match_name):
            if single_frame['frame']['name']==match_name:
                return single_frame['frame']['id']
            else:
                return None
        import json  
        frameTree_str = self._inspector.GetFrameTree(self._client_id)
        frame_tree = json.loads(frameTree_str.encode('utf8')) 
        sub_frame=frame_tree
        while 1:
            frame_id=_handle_single_frame(sub_frame, frame_name)
            if frame_id:
                return frame_id
            else:
                if sub_frame.has_key('childFrames'):
                    index=0
                    child_frames=sub_frame.get('childFrames')
                    frame_count=len(child_frames)
                    for frame in child_frames:
                        frame_id=_handle_single_frame(frame, frame_name)
                        if frame_id:
                            return frame_id
                    else:
                        if index<frame_count:
                            sub_frame=child_frames[index]
                            index+=1
                        else:
                            break
                else:
                    break
        #logger.warning(("frame: %s not found in frame tree:\n %s" % (frame_name,frame_tree))
    
    @encode_wrap
    def eval_script(self, frame_xpaths, script):
        '''执行注入的js代码
        '''
        frame_id = self._get_frame_id(frame_xpaths)
#         print script
        script = script.replace('\\', r'\\')
        script = script.replace('"', r'\"')
        script = script.replace('\r', r'\r')
        script = script.replace('\n', r'\n')
        script = r'''(function(){
            try{
                var result = eval("%s");
                if(result != undefined){
                    return 'S'+result.toString();
                }else{
                    return 'Sundefined';
                }
            }catch(e){
                var retVal = 'E['+e.name + ']' + e.message;//toString()
                retVal += '\n' + e.stack;
                return retVal;
            }
        })();''' % script  # 2016/1/26 shadowyang 不能返回对象，否则会报错
        
        result = self._inspector.EvalScript(self._client_id, script, frame_id)
        result=result.replace('\\\\','\\')
        result=result.decode('raw_unicode_escape')
        if result.startswith('S"'):
            result=result[2:-2]
        else:
            raise RuntimeError("js return error:%s" % result)
        return self._handle_result(result, frame_xpaths)
        
if __name__ == '__main__':
    pass