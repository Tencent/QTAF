# -*- coding: utf-8
'''TIF 对象管理
'''
#2011/09/16 allenpan 创建

#import logging
import win32api
import win32con
import win32gui
import win32process
import ctypes
import threading
import pywintypes
import locale
import os
from win32com.client import Dispatch

class TestObjectMgr(object):
    '''TIF的TestObjectManger对象。
    内部创建并缓存相关进程的TestInterfaceFramework.TestObjectManager的COM对象。
    '''
    #2011/09/19 allenpan 创建
    
    _fail_pids = set() #注入失败的pid缓存
    _test_object_mgr_itfs = {} #进程的tom对象缓存
    _tif_dll = "tif.dll"
    _tif_init_event = 'TIF_INIT_DONE'
    _detoured_openprocess = None
    def __init__(self, pid):
        '''constructor
        
        :param pid: 进程ID 
        '''
        #2013/09/23 aaronlai    在注入dll后，assist window不一定及时创建完毕，需使用retry
        #2013/12/18 aaronlai    注册tom可能会因QQ进程阻塞而导致测试进程阻塞，故修改为SendMessageTimeout方式
        #2014/03/19 aaronlai    先判断目标进程是否能让tif.dll注入成功
        #2014/07/09 aaronlai    根据进程id和线程id来对tom进行cache
        import qpath
        import util
        
        self._pid = pid
        tid = threading.currentThread().ident
        if (pid,tid) in self._fail_pids:
            raise ValueError("PID:%d 不支持注入!" % pid)
        elif (pid,tid) in self._test_object_mgr_itfs:
            self._tom = self._test_object_mgr_itfs[(pid,tid)]
        else:
            if not self._isInjectedEnable():
                self._fail_pids.add((pid,tid))
                raise ValueError("PID:%d 不支持注入!" % pid)

            if not self._isTifInjected():
                if not self._injectTifDll():
                    self._fail_pids.add((pid,tid))
                    tif_path = os.path.join(self._getTifDllPath(), self._tif_dll)
                    # 将tif_path转为utf8编码
                    os_encoding = locale.getdefaultlocale(None)[1]
                    tif_path = tif_path.decode(os_encoding).encode('utf-8')
    
                    err_msg = '注入%s到进程%d失败' %(tif_path, self._pid)
                    raise RuntimeError(err_msg)

            wnds = util.Timeout(2,0.1).retry(lambda:qpath.QPath("/classname='AssistWnd' && processid='%d'" % pid).search(None),
                                              (), 
                                              {}, 
                                              lambda x: len(x)>0)
            if len(wnds) != 1:
                raise RuntimeError("fail to locate Assist Wnd")
            hwnd = wnds[0].HWnd
            ret, _ = win32gui.SendMessageTimeout(hwnd, win32con.WM_USER+1, 0, 0, win32con.SMTO_ABORTIFHUNG, 10000)
            if ret==0:
                raise Exception("failed to register TestObjectManger!")
            
            tom = Dispatch('TestInterfaceFramework.TestObjectManage')
            if pid != tom.getProcessId():
                raise RuntimeError("cannot find TestObjectManger object.")
            self._tom = tom
            self._test_object_mgr_itfs[(pid,tid)] = tom

#     def __del__(self):
#         """析构函数，释放缓存的数据
#         """
#         #2013/07/29 aaronlai    created
#         #2013/07/31 aaronlai    不清除_detoured_openprocess
#         #2014/07/09 aaronlai    去掉析构，是缓存功能生效
#         TestObjectMgr._fail_pids = set()
#         TestObjectMgr._test_object_mgr_itfs = {}

    @staticmethod
    def clearCache():
        TestObjectMgr._fail_pids = set()
        TestObjectMgr._test_object_mgr_itfs = {}
        
    def _getModuleNames(self):
        '''获取目标进程内加载的module name
        '''
        #2014/03/19 aaronlai    created
        handle = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION|win32con.PROCESS_VM_READ, 0, self._pid)
        modules = []
        try:
            modules = win32process.EnumProcessModules(handle)
        except pywintypes.error as e:
            if e[0] == 299:
                #===============================================================
                # http://msdn.microsoft.com/en-us/windows/desktop/ms682631.aspx
                # if this function is called from a 32-bit application running on WOW64,
                # it can only enumerate the modules of a 32-bit process. If the process is
                # 64-bit process, this function fails and the last error code is ERROR_PARTIAL_COPY(299).
                #===============================================================
                win32api.CloseHandle(handle)
                return []
            
        moduleNames = []
        for module in modules:
            try:
                modulename = win32process.GetModuleFileNameEx(handle, module)
                moduleNames.append(modulename)
            except win32process.error:
                continue
            
        win32api.CloseHandle(handle)
        
        return moduleNames
        
    def queryObject(self, name):
        ''' 获取名字为name的TestObject
        
        :return: 返回注册到TestObject
        :rtype: Dispatch
        '''
        return self._tom.queryObject(name)
    
    def _isInjectedEnable(self):
        '''判断目标进程是否可注入tif.dll
        '''
        #2014/03/19 aaronlai    created
        moduleNames = self._getModuleNames()
        flag = 0x0
        for modulename in moduleNames:
            if modulename.upper().endswith('COMMON.DLL'):
                flag = flag | 0x1
            elif modulename.upper().endswith('GF.DLL'):
                flag = flag | 0x2
            if flag == 0x3:
                break;
        
        if flag == 0x3:
            return True
        else:
            return False
        
    def _isTifInjected(self):
        '''if tif dll injected
        '''
        moduleNames = self._getModuleNames()
        for modulename in moduleNames:
            if modulename.upper().endswith(self._tif_dll.upper()):
                return True
        return False
    
    def _getTifDllPath(self):
        '''得到tif.dll的所在路径
        '''
        #2014/03/19 aaronlai    创建。采用此方式，用于解决bug:http://tapd.oa.com/v3/10028971/bugtrace/bugs/view?bug_id=1010028971049314173
        
        moduleNames = self._getModuleNames()
        for modulename in moduleNames:
            if modulename.upper().endswith('COMMON.DLL'):
                return modulename.rpartition('\\')[0]
        return None    
        
#    @staticmethod
#    def _getInjectPath(pid):
#        h = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION|win32con.PROCESS_VM_READ, 0, pid)
#        pidpath = win32process.GetModuleFileNameEx(h, None)
#        dpath = pidpath.rpartition('\\')[0]
#        return dpath
    
    def _getTimerWnd(self):
        '''获取QQ的Timer Window，若Timer Window还未创建前就注入测试桩，那么注入会失败
        '''
        hTargetWnd = 0
        hwnd = win32gui.FindWindowEx(win32con.HWND_MESSAGE, 0, None, "Timer Helper Window")
        while win32gui.IsWindow(hwnd):
            pid = win32process.GetWindowThreadProcessId(hwnd)[1]
            if pid == self._pid:
                hTargetWnd = hwnd
                break
            hwnd = win32gui.FindWindowEx(win32con.HWND_MESSAGE, hwnd, None, "Timer Helper Window")
        return hTargetWnd
    
    def _injectTifDll(self):
        '''注入tif.dll
        '''
        # 2011.12.30   rayechen   修改为全路径注入
        # 2012.04.17   aaronlai     在Timer Window出现后再注入tif.dll才能成功
        # 2012.07.31   rayechen   等到向Timer Window发送WM_NULL成功后才注入
        # 2012.09.17   aaronlai   增加Timeout值，见单9431978
        # 2013.08.23   aaronlai   bug fix:48909040
        import win32event
        import win32gui
        import util
        hTimerWnd = util.Timeout(5,0.1).retry(self._getTimerWnd, (), {}, lambda x: win32gui.IsWindow(x))
        win32gui.SendMessageTimeout(hTimerWnd, win32con.WM_NULL, 0, 0, win32con.SMTO_NORMAL, 10000)
        event = win32event.CreateEvent(None, True, False, self._tif_init_event)
        win32event.ResetEvent(event)    
        tif_path = os.path.join(self._getTifDllPath(), self._tif_dll)
        self._remote_inject_dll(self._pid, tif_path)
        ret = win32event.WaitForSingleObject(event, 10000)
        win32api.CloseHandle(event)
        if ret == win32con.WAIT_TIMEOUT:
            return False
        return True
    
    @staticmethod
    def clear():
        #2012/06/18    rayechen   创建
        TestObjectMgr._fail_pids.clear()
        TestObjectMgr._test_object_mgr_itfs = {}
    
    def _remote_inject_dll(self, process_id, dll_path):
        '''在process_id进程中远程注入dll_path的DLL
        '''
        #12/04/17 aaronlai    因Q盾3.3会在QQ登录前拦截OpenProcess，改用替换的OpenProcess。(原本此函数在tuia.util模块中定义。)
        #14/03/03 aaronlai    修改提示语
        os_encoding = locale.getdefaultlocale(None)[1]
        dll_path = dll_path.decode('utf-8').encode(os_encoding)
        
        nbytes = len(dll_path)
        dllpath = str(dll_path)
        if TestObjectMgr._detoured_openprocess is None:
            hproc = ctypes.windll.kernel32.OpenProcess(win32con.PROCESS_ALL_ACCESS, False, process_id)
        else:
            hproc = TestObjectMgr._detoured_openprocess(win32con.PROCESS_ALL_ACCESS, False, process_id)
            if hproc==-1:
                raise Exception('OpenProcess被Q盾拦截，请确认qdaclutil.dll文件是否已加入Q盾后台拦截白名单')
        dllname = ctypes.windll.kernel32.VirtualAllocEx(hproc, None, nbytes, 
                                win32con.MEM_RESERVE|win32con.MEM_COMMIT, win32con.PAGE_READWRITE)
        ctypes.windll.kernel32.WriteProcessMemory(hproc, dllname, dllpath, len(dllpath), None)
        hknl = ctypes.windll.kernel32.GetModuleHandleA("kernel32.dll")
        ldlib_addr = ctypes.windll.kernel32.GetProcAddress(hknl , "LoadLibraryA")
        ctypes.windll.kernel32.CreateRemoteThread(hproc, None, None, 
                    ldlib_addr, dllname, None, None)
        ctypes.windll.kernel32.VirtualFreeEx(hproc, dllname, nbytes, win32con.MEM_RELEASE)
        ctypes.windll.kernel32.CloseHandle(hknl)
        ctypes.windll.kernel32.CloseHandle(hproc)
    
    @staticmethod
    def _detour_openprocess(newfuncptr):
        """传入自定义的OpenProcess以替代相应的系统api
        
        """
        #2013/04/17 aaronlai    创建
        TestObjectMgr._detoured_openprocess = newfuncptr
        
class UtilEntry(object):
    '''
    对应TIF内部实现的UtilEntry对象
    '''
    #2011/12/19 rayechen 创建
    class eFileInfoTypeInDB:
        E_FILE_INFO_TYPE_CREATE_TIME = 0  #文件创建时间
        E_FILE_INFO_TYPE_MODIFY_TIME = 1  #文件修改时间
        
    def __init__(self, pid):
        self._tom = TestObjectMgr(pid)
        self._utilentry = self._tom.queryObject('TIFUtilEntry')
        pass

    def isFileInDBExist(self, dbpath, filePathInDB):
        '''判断DB文件中的某个文件是否存在
        
        :param dbpath: DB文件路径
        :param filePathInDB: 所指定的DB复合文档中某文件的路径
        :return: bool{True:存在；False:不存在}
        '''
        return self._utilentry.IsFileInDBExist(dbpath, filePathInDB)
    
    def getFileCreateTime(self, dbpath, filePathInDB):
        '''获取DB文件中某个文件的创建时间
        
        :param dbpath: DB文件路径
        :param filePathInDB: 所指定的DB复合文档中某文件的路径
        :return: str{相关值}
        '''
        return self._utilentry.GetFileInfoInDB(dbpath, filePathInDB, UtilEntry.eFileInfoTypeInDB.E_FILE_INFO_TYPE_CREATE_TIME)
    
    def getFileModifyTime(self, dbpath, filePathInDB):
        '''获取DB文件中某个文件的修改时间
        
        :param dbpath: DB文件路径
        :param filePathInDB: 所指定的DB复合文档中某文件的路径
        :return: str{相关值}
        '''
        return self._utilentry.GetFileInfoInDB(dbpath, filePathInDB, UtilEntry.eFileInfoTypeInDB.E_FILE_INFO_TYPE_MODIFY_TIME)
    
    def deleteFileInDB(self, dbpath, filePathInDB):
        '''删除DB文件中的某个文件
        
        :param dbpath: DB文件路径
        :param filePathInDB: 所指定的DB复合文档中某文件的路径
        :return: bool{True:删除成功；False:删除失败}
        '''
        return self._utilentry.DeleteFileInDB(dbpath, filePathInDB)
    
    def SetSCBit(self, idx, val):
        '''
        '''
        #2014/06/25 aaronlai    created
        #查询RichServerCtrlBit时，需增加Client端的临时偏移转换值10000（旧的ServerCtrlBit都是小于10000的）
        if idx < 10000:
            idx = idx + 10000
        return self._utilentry.SetSCBit(idx, val)
     
if __name__ == '__main__':
    pass
