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
用于QPlus App窗口的Web自动化实现
'''
#2012-02-22    beyondli    创建
#2012-05-11    beyondli    将copy_libcef从_webkit移动到此

import os
import win32gui

import _webkit
from _webkit import MeanDriver
from ..util import Keyboard
from ctypes import *

from _webkit import inspector_new

INVALID_HANDLE_VALUE = 0xFFFFFFFF
TH32CS_SNAPPROCESS = 0x00000002

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
                ('szExeFile', c_wchar*260)]

def getProcessInfo(pid = 0, process_name = ''):
    '''
        获取进程信息
    '''
    if not pid and not process_name:
        raise Exception('必须指定pid或进程名')

    hSnapShot = windll.kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, pid)
    if hSnapShot == INVALID_HANDLE_VALUE:
        return False
    pe = PROCESSENTRY32()
    pe.dwSize = sizeof(PROCESSENTRY32)
        
    bResult = windll.kernel32.Process32FirstW(hSnapShot, byref(pe))
    if not bResult: 
        print 'err', windll.kernel32.GetLastError()
        return None
    while bResult:
        item = {'pid': pe.th32ProcessID,
                'ppid': pe.th32ParentProcessID,
                'nThreads': pe.cntThreads,
                'pName': pe.szExeFile}
        if pid:
            if pid == pe.th32ProcessID:
                return item
        else:
            if pe.szExeFile == process_name:
                return item
        
        bResult = windll.kernel32.Process32NextW(hSnapShot, byref(pe))
    return None

def getProcessFilePath(pid = 0, process_name = ''):
    if not pid and not process_name:
        raise Exception('必须指定pid或进程名')
    if not pid:
        pinfo = getProcessInfo(process_name = process_name)
        if not pinfo:
            return u''
        pid = pinfo['pid']
    hProcess = windll.kernel32.OpenProcess(0x001F0FFF, 0, pid)
    if not hProcess:
        return u''
    psapi = WinDLL('psapi.dll')
    buff = create_unicode_buffer(260)
    ret = psapi.GetModuleFileNameExW(hProcess, 0, buff, 260)
    if not ret:
        return u''
    return buff.value

class LANGANDCODEPAGE(Structure):#定义语言代码结构体
    _fields_ = [('wLanguage', c_ushort), ('wCodePage', c_ushort)]

    
def getFileVersion(file_path):
    '''
    获取文件版本
    '''
    if not isinstance(file_path, unicode):
        file_path = file_path.decode('utf8')
    if not os.path.exists(file_path):
        raise Exception('文件%s不存在' % file_path)
    Version = WinDLL("version.dll")#加载DLL模块
    GetFileVersionInfoSize = Version.GetFileVersionInfoSizeW#获取函数地址
    GetFileVersionInfo = Version.GetFileVersionInfoW
    VerQueryValue = Version.VerQueryValueW
    
    size = GetFileVersionInfoSize(file_path, None)
    if not size:
        #raise Exception('GetFileVersionInfoSize failed: %s' % file_path)
        return None
    pBuf = create_string_buffer(size)#建立缓冲区，用于存放版本信息
    ret = GetFileVersionInfo(file_path, None, size, pBuf)
    if not ret:
        print 'GetFileVersionInfo failed'
        return None
    pLangue = POINTER(LANGANDCODEPAGE)()#建立LANGANDCODEPAGE类型的空指针
    len = c_uint(0)
    ret = VerQueryValue(pBuf, u"\\VarFileInfo\\Translation", byref(pLangue), byref(len))
    if not ret:
        print 'VerQueryValue failed'
        return None
    #获取语言代码
    
    name = u"\\StringFileInfo\\%04x%04x\\" % (pLangue.contents.wLanguage, pLangue.contents.wCodePage)
    #构造要查询的字符串
    #print name
    result =[]
    p = POINTER(c_wchar*256)()#建立宽字符串类型的指针
    for item in ('FileDescription', 'FileVersion'):
        VerQueryValue(pBuf, name+item, byref(p), byref(len))
        result.append(p.contents.value)
    return result

def copy_libcef():
    '''
    判断libcef是否是修改后的版本，目前QTA运行时有时没有拷贝，这里会判断一下
    暂时使用，如果QTA可以正常拷贝，就不使用该函数
    '''
    #2012-04-14    rambutan  创建
    #2012-05-11    beyondli    从_webkit移动到此    
    import os, re, time, shutil
    from ctypes import WinDLL
    
    from _webkit import basepath, PEINFO_DLL
    
    #peinfo = WinDLL(os.path.dirname(os.path.abspath(__file__)) + r'\PeInfo.dll')
    peinfo = WinDLL(os.path.join(basepath, PEINFO_DLL)) ############################ --- 注意:cherry略修改
    
    qplus_path = getProcessFilePath(process_name = 'QPlus.exe')
    if not qplus_path:
        raise Exception('QPlus.exe未运行')
    
    qplus_path = os.path.dirname(qplus_path)
    #print qplus_path
    if qplus_path.endswith('QPlus'):
        #标准版  
        libcef_path = os.environ['AppData'] + r'\Tencent\QPlus'
        qplus_dirs = []
        for p in os.listdir(libcef_path):
            path1 = libcef_path + '\\' + p
            if os.path.isdir(path1):
                pattern = re.compile(r'^\d{1}\.\d+\.\d+\.\d+$')
                match = pattern.search(p)
                if match:
                    qplus_dirs.append(p)
        #print qplus_dirs
        if len(qplus_dirs) == 0:
            raise Exception('QPlus 未安装')
        elif len(qplus_dirs) == 1:
            libcef_path += '\\' + qplus_dirs[0] + r'\Bin\libcef.dll'
        else:
            #存在多个QPlus目录，选择版本号最大的
            max_i = 0
            max_n = 0
            for i in range(len(qplus_dirs)):
                p = qplus_dirs[i]
                p = p.replace('.', '')
                p = int(p)
                if p > max_n:
                    max_i = i
                    max_n = p
            libcef_path += '\\' + qplus_dirs[max_i] + r'\Bin\libcef.dll'
    elif qplus_path.endswith('Bin'):
        #Q+Lite
        libcef_path = qplus_path + r'\libcef.dll'
    else:
        raise Exception('未处理')
    #print libcef_path
    if os.path.exists(libcef_path):    
        result = peinfo.VerifySignature(libcef_path.decode('utf8'))
        #print result
        if not result: return True  #没有数字签名的是我们修改后的版本
        i = 0
        while i < 3:
            try:
                os.remove(libcef_path)
            except:
                if os.path.exists(libcef_path): #文件被进程占用
                    os.system('taskkill /im QPlusApp.exe /F')
                    os.system('taskkill /im QQExternalEx.exe /F')#Q+Lite中的名字
                    time.sleep(0.2)
                i += 1
    src_path = ur'\\tencent.com\tfs\跨部门项目\SNG-Test\QTA\QPlusWebkit\libcef\libcef.dll'
    i = 3
    while i > 0:
        try:
            shutil.copy(src_path, libcef_path)
            break
        except:
            i -= 1
            if i == 0:
                raise Exception('从地址%s拷贝libcef.dll失败' % src_path)
    raise Exception('未拷贝测试版本的libcef.dll，现在已拷贝，请重新运行测试用例')

def getTestStubPath(qplus_ver):
    '''
    根据不同的Q+版本取相应的测试桩
    '''
    base_path = ur'\\tencent.com\tfs\跨部门项目\SNG-Test\QTA\QPlusWebkit'
    stub_path = ''
    if os.path.exists(qplus_ver):
        #Q+或QQ的安装目录
        version_found = False
        file_list = []
        if qplus_ver.endswith('QPlus'):
            #Q+独立版
            file_list = ['QPlus.exe', 'QPlusDesktop.exe']
        elif qplus_ver.endswith('QQ'):
            #QQ打包版
            qplus_ver = os.path.join(qplus_ver, 'Bin') #在Bin目录中查找
            file_list = ['QPlus.exe', 'webapp.dll']
            
        for file in file_list:
            file_path = os.path.join(qplus_ver, file)
            if os.path.exists(file_path):
                version = getFileVersion(file_path)
                if not version:
                    continue
                version = version[1]
                import re
                pattern = re.compile(r'\d+\.\d+\.\d+(\.\d+){0,1}')
                if not pattern.match(version):
                    print version
                    continue
                versions = version.split('.')
                if versions[0] == '0' and versions[1] == '0':
                    #错误的版本信息
                    continue
                qplus_ver = versions[0] + '.' + versions[1]
                version_found = True
                break
        if not version_found:
            raise Exception('查找版本信息失败：%s' % qplus_ver)  
    if qplus_ver in ['3.6', '3.7', '3.8', '3.9']:
        stub_path = r'libcef\QPlus%s\libcef.dll' % qplus_ver
    elif qplus_ver in ['4.0', '4.1', '4.2']:
        stub_path = r'cefspy\cefspy%s.0.dll' % qplus_ver
    else:
        raise Exception('不支持的Q+版本：%s' % qplus_ver)
    return os.path.join(base_path, stub_path)

class WebPage(_webkit.WebPage):
    '''用于QPlus App的WebPage实现'''
    #2012-02-22    beyondli    创建
    #2012-02-29    beyondli    添加了findInWindow方法，并对构造函数做了相应修改
    def __init__(self, driver, locator = ''):
        '''构造函数
        @type driver: CefInspector
        @param driver: 连接页面的CefInspector实例
        '''
        #copy_libcef()   #拷贝libcef.dll，如果已经是修改版本则不会拷贝
        super(WebPage, self).__init__(driver, locator)
        self._hwnd = driver._hWnd

    @classmethod
    def findByHWnd(cls, hwnd):
        if hasattr(hwnd, 'HWnd'):
            hwnd = hwnd.HWnd
        elif not isinstance(hwnd, int):
            raise ValueError("Must assign a window or handle.")
        #driver = MeanDriver(inspector.CefInspector, hwnd)
        driver = inspector_new.CefInspector(hwnd)
        return WebPage(driver)

    @property
    def BrowserType(self):
        '''获取承载页面的浏览器的名称及版本
        @rtype: str
        @return: 浏览器的名称及版本
        '''
        return "QPlus App"

    @property
    def HWnd(self):
        '''返回page所在的窗口句柄
        '''
        #2013/12/25 pear    新建
        return self._hwnd
    
    def activate(self):
        '''激活承载页面的窗口'''
        print 'activate', '%X' % self._hwnd
        try:
            win32gui.SetActiveWindow(self._hwnd)
            win32gui.ShowWindow(self._hwnd, 9)
            win32gui.BringWindowToTop(self._hwnd)
            win32gui.SetForegroundWindow(self._hwnd)
            win32gui.ShowWindow(self._hwnd, 1)
        except win32gui.error:
            print win32gui.error
            print '[WARNING]WebPage.activate() maybe failed: %s' % self
            pass

    def close(self):
        '''关闭承载页面的窗口'''
        if self._locator:
            return
        super(WebPage, self).close()
        self.activate()
        Keyboard.inputKeys("%{F4}")

class WebElement(_webkit.WebElement):
    '''用于QPlus App的WebElement实现'''
    #2012-02-22    beyondli    创建
    pass

if __name__ == "__main__":
    qplus_path = getProcessFilePath(process_name = 'QPlus.exe') 
    pass
