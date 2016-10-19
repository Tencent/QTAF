# -*-  coding: UTF-8  -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
__modified__ = '2011.05 - 2012.05.30'
__description__ = '3.5.x (中文输入输出仅使用Unicode字符集)'
__author__ = 'tommyzhang(张勇军)'
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
import os, re, time, types, locale, urllib, urllib2, sqlite3, datetime
# -*-
import win32con, win32api, win32gui, win32event, win32process, win32clipboard, win32com.client
# -*-
import ctypes, ctypes.wintypes, comtypes, comtypes.client
# -*-
LocalCode, LocalEncoding = locale.getdefaultlocale()
APPDATA_IELIB_PATH = os.path.join(os.getenv('APPDATA'), 'ielib')
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-

# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- Functions

def filetime_to_local_datetime(lpFileTime):
    _filetime_null_date = datetime.datetime(1601, 1, 1, 0, 0, 0)
    lpLocalFileTime = ctypes.wintypes.FILETIME()
    lpLocalFileTime.dwSize = ctypes.sizeof(ctypes.wintypes.FILETIME)
    ctypes.windll.kernel32.FileTimeToLocalFileTime(ctypes.byref(lpFileTime), ctypes.byref(lpLocalFileTime))
    timestamp = lpLocalFileTime.dwHighDateTime
    timestamp <<= 32
    timestamp |= lpLocalFileTime.dwLowDateTime
    return _filetime_null_date + datetime.timedelta(microseconds=timestamp / 10)

# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- Structures

class IEProxy_INTERNET_PER_CONN_OPTION_VALUE(ctypes.Union): #'''@desc: Contains the value of an option in the IEProxy_INTERNET_PER_CONN_OPTION struct.'''
    _fields_ = [('dwValue', ctypes.c_ulong),
                ('pszValue', ctypes.c_char_p),
                ('ftValue', ctypes.wintypes.FILETIME)]

class IEProxy_INTERNET_PER_CONN_OPTION(ctypes.Structure): #'''@desc: Contains the value of an option in the IEProxy_INTERNET_PER_CONN_OPTION_LIST struct.'''
    _fields_ = [('dwOption', ctypes.c_ulong),
                ('Value', IEProxy_INTERNET_PER_CONN_OPTION_VALUE)]

class IEProxy_INTERNET_PER_CONN_OPTION_LIST(ctypes.Structure): #'''@desc: Contains the list of options for a particular Internet connection.'''
    _fields_ = [('dwSize', ctypes.c_ulong),
                ('pszConnection', ctypes.c_char_p),
                ('dwOptionCount', ctypes.c_ulong),
                ('dwOptionError', ctypes.c_ulong),
                ('pOptions', ctypes.POINTER(IEProxy_INTERNET_PER_CONN_OPTION))]

class ThreadEntry32(ctypes.Structure):
    _fields_ = [('dwSize', ctypes.c_ulong),
                ('cntUsage', ctypes.c_ulong),
                ('th32ThreadID', ctypes.c_ulong),
                ('th32OwnerProcessID', ctypes.c_ulong),
                ('tpBasePri', ctypes.c_long),
                ('tpDeltaPri', ctypes.c_long),
                ('dwFlags', ctypes.c_ulong)]

class ProcessEntry32(ctypes.Structure):
    _fields_ = [('dwSize', ctypes.c_ulong),
                ('cntUsage', ctypes.c_ulong),
                ('th32ProcessID', ctypes.c_ulong),
                ('th32DefaultHeapID', ctypes.c_ulong),
                ('th32ModuleID', ctypes.c_ulong),
                ('cntThreads', ctypes.c_ulong),
                ('th32ParentProcessID', ctypes.c_ulong),
                ('pcPriClassBase', ctypes.c_long),
                ('dwFlags', ctypes.c_ulong),
                ('szExeFile', ctypes.c_char * win32con.MAX_PATH)]

# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- Handle

class Handle(object):
    
    @classmethod
    def __enum_child_windows_callback__(cls, handle, args):
        parent, childs = args[0], args[1]
        if parent == win32gui.GetParent(handle):childs.append(handle)
    
    @classmethod
    def get_childs(cls, handle):
        childs = []
        try    : win32gui.EnumChildWindows(handle, cls.__enum_child_windows_callback__, (handle, childs))
        except : pass
        return childs
    
    @classmethod
    def get_parent(cls, handle):return win32gui.GetParent(handle)
    
    @classmethod
    def get_top_window(cls, handle):
        cur_handle = handle
        while cls.get_parent(cur_handle):cur_handle = cls.get_parent(cur_handle)
        return cur_handle
    
    @classmethod
    def is_valid(cls, handle):return bool(win32gui.IsWindow(handle))
    
    @classmethod
    def is_invalid(cls, handle):return not cls.is_valid(handle)
    
    @classmethod
    def is_enabled(cls, handle):return bool(win32gui.IsWindowEnabled(handle))
    
    @classmethod
    def is_visible(cls, handle):return bool(win32gui.IsWindowVisible(handle))
    
    @classmethod
    def get_windowrect(cls, handle):return win32gui.GetWindowRect(handle)
    
    @classmethod
    def get_classname(cls, handle):return win32gui.GetClassName(handle).decode(LocalEncoding)
    
    @classmethod
    def get_id(cls, handle):return win32gui.GetDlgCtrlID(handle)
    
    @classmethod
    def get_style(cls, handle):return win32gui.GetWindowLong(handle, win32con.GWL_STYLE)
    
    @classmethod
    def get_windowtext(cls, handle):
        text = win32gui.GetWindowText(handle).decode(LocalEncoding)
        if len(text) == 0:
            buf_size = win32gui.SendMessage(handle, win32con.WM_GETTEXTLENGTH, 0, 0) + 1
            buffer = win32gui.PyMakeBuffer(buf_size)
            win32gui.SendMessage(handle, win32con.WM_GETTEXT, buf_size, buffer)
            text = buffer[:buf_size - 1].decode(LocalEncoding)
        return text
    
    @classmethod
    def get_threadid(cls, handle):return win32process.GetWindowThreadProcessId(handle)[0]
    
    @classmethod
    def get_processid(cls, handle):return win32process.GetWindowThreadProcessId(handle)[1]
    
    @classmethod
    def set_focus(cls, handle):
        tag_threadid = cls.get_threadid(handle)
        cur_threadid = win32api.GetCurrentThreadId()
        win32process.AttachThreadInput(tag_threadid, cur_threadid, True)
        win32gui.SetFocus(handle)
        win32process.AttachThreadInput(tag_threadid, cur_threadid, False)
    
    @classmethod
    def set_windowtext(cls, handle, text):win32gui.SendMessage(handle, win32con.WM_SETTEXT, 0, text.encode(LocalEncoding))
    
    @classmethod
    def set_style(cls, handle, style):
        '''
        @desc: 设置窗口样式
        @param: handle <int> 窗口句柄
                style  <int> 1.最大化; 2.最小化; 3.显示; 4.隐藏; 5.设置面板始终最前端; 6.取消面板始终最前端设置; 7.回复原形状
        '''
        if style == 1 : win32gui.ShowWindow(handle, win32con.SW_SHOWMAXIMIZED)
        if style == 2 : win32gui.ShowWindow(handle, win32con.SW_MINIMIZE)
        if style == 3 : win32gui.ShowWindow(handle, win32con.SW_SHOW)
        if style == 4 : win32gui.ShowWindow(handle, win32con.SW_HIDE)
        if style == 5 : win32gui.SetWindowPos(handle, win32con.HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOSIZE | win32con.SWP_NOMOVE)
        if style == 6 : win32gui.SetWindowPos(handle, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, win32con.SWP_NOSIZE | win32con.SWP_NOMOVE)
        if style == 7 : win32gui.ShowWindow(handle, win32con.SW_RESTORE)
    
    @classmethod
    def close(cls, handle):
        try:
            win32api.PostMessage(handle, win32con.WM_CLOSE, 0, 0)
            win32api.PostMessage(handle, win32con.WM_DESTROY, 0, 0)
            win32api.PostMessage(handle, win32con.WM_QUIT, 0, 0)
            time.sleep(0.2)
        except Exception, e : pass
        return cls.is_invalid(handle)
    
    # -*- -*- -*- -*- -*-
    
    @classmethod
    def __enum_top_windows_callback__(cls, handle, args):
        if cls.is_valid(handle):
            filter, items = args[0], args[1]
            isMatch = True
            classname = cls.get_classname(handle)
            windowtext = cls.get_windowtext(handle)
            processid = cls.get_processid(handle)
            if filter['classname'] and not re.match(filter['classname'], classname)    : isMatch = False
            if filter['windowtext'] and not re.match(filter['windowtext'], windowtext) : isMatch = False
            if filter['processid'] and filter['processid'] != processid                : isMatch = False
            if isMatch                                                                 : items.append(handle)
    
    @classmethod
    def get_top_windows(cls, classname=None, windowtext=None, processid=None):
        handles = []
        filter = {'classname':classname, 'windowtext':windowtext, 'processid':processid}
        win32gui.EnumWindows(cls.__enum_top_windows_callback__, (filter, handles))
        return handles
    
    @classmethod
    def highlight(cls, rect=(0, 0, 0, 0), line_pixel=2, line_color=win32api.RGB(255, 0, 0), loop=2, timestep=0.125, dc_handle=win32gui.GetDesktopWindow()):
        left, top, right, bottom = rect
        for i in xrange(loop):
            dc = win32gui.GetWindowDC(dc_handle)
            new_pen = win32gui.CreatePen(win32con.PS_SOLID, line_pixel, line_color)
            org_pen = win32gui.SelectObject(dc, new_pen)
            org_brush = win32gui.SelectObject(dc, win32gui.GetStockObject(win32con.HOLLOW_BRUSH))
            win32gui.Rectangle(dc, left, top, right + line_pixel, bottom + line_pixel)
            win32gui.SelectObject(dc, org_pen)
            win32gui.SelectObject(dc, org_brush)
            win32gui.ReleaseDC(dc_handle, dc)
            time.sleep(timestep)
            win32gui.InvalidateRect(dc_handle, None, True)
            win32gui.UpdateWindow(dc_handle)
            win32gui.RedrawWindow(dc_handle, None, None, win32con.RDW_FRAME | win32con.RDW_INVALIDATE | win32con.RDW_UPDATENOW | win32con.RDW_ALLCHILDREN)
            time.sleep(timestep)
    
    @classmethod
    def active(cls, tag_handle):
        cur_handle = win32gui.GetForegroundWindow()
        cur_handle_tid, cur_handle_pid = win32process.GetWindowThreadProcessId(cur_handle)
        tag_handle_tid, tag_handle_pid = win32process.GetWindowThreadProcessId(tag_handle)
        if cur_handle_tid != tag_handle_tid:
            ctypes.windll.user32.AllowSetForegroundWindow(tag_handle_pid)
            ctypes.windll.user32.SetForegroundWindow(tag_handle)
        if ctypes.windll.user32.GetForegroundWindow != tag_handle : ctypes.windll.user32.SetForegroundWindow(tag_handle)
        if win32gui.IsIconic(tag_handle)                          : win32gui.ShowWindow(tag_handle, win32con.SW_RESTORE)
        if not win32gui.IsWindowVisible(tag_handle)               : win32gui.ShowWindow(tag_handle, win32con.SW_SHOW)
        ctypes.windll.user32.SetActiveWindow(tag_handle)
        ctypes.windll.user32.BringWindowToTop(tag_handle)

    @classmethod
    def get_handle_from_point_by_classname(cls, classname=None):
        handle = win32gui.WindowFromPoint(win32gui.GetCursorPos())
        if classname :
            if classname == cls.get_classname(handle):return handle
        else : return handle

# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- Thread

class Thread:
    
    TH32CS_SNAPTHREAD = 0x00000004
    
    @classmethod
    def __get_thread_times__(cls, threadID):
        lpCreationTime = ctypes.wintypes.FILETIME()
        lpCreationTime.dwSize = ctypes.sizeof(ctypes.wintypes.FILETIME)
        lpExitTime = ctypes.wintypes.FILETIME()
        lpExitTime.dwSize = ctypes.sizeof(ctypes.wintypes.FILETIME)
        lpKernelTime = ctypes.wintypes.FILETIME()
        lpKernelTime.dwSize = ctypes.sizeof(ctypes.wintypes.FILETIME)
        lpUserTime = ctypes.wintypes.FILETIME()
        lpUserTime.dwSize = ctypes.sizeof(ctypes.wintypes.FILETIME)
        hThread = ctypes.windll.kernel32.OpenThread(win32con.THREAD_QUERY_INFORMATION, False, threadID)
        ctypes.windll.kernel32.GetThreadTimes(hThread, ctypes.byref(lpCreationTime), ctypes.byref(lpExitTime), ctypes.byref(lpKernelTime), ctypes.byref(lpUserTime))
        ctypes.windll.kernel32.CloseHandle(hThread)
        return lpCreationTime, lpExitTime, lpKernelTime, lpUserTime
    
    @classmethod
    def get_creation_time_by_threadID(cls, threadID):
        lpCreationTime, lpExitTime, lpKernelTime, lpUserTime = cls.__get_thread_times__(threadID)
        return filetime_to_local_datetime(lpCreationTime)
    
    @classmethod
    def get_creation_time_by_threadHandle(cls, handle):
        threadID, processID = win32process.GetWindowThreadProcessId(handle)
        return cls.get_creation_time_by_threadID(threadID)
    
    @classmethod
    def get_threads(cls):
        threads = []
        objTE32 = ThreadEntry32()
        objTE32.dwSize = ctypes.sizeof(ThreadEntry32)
        snapshot = ctypes.windll.kernel32.CreateToolhelp32Snapshot(cls.TH32CS_SNAPTHREAD, 0)
        if ctypes.windll.kernel32.Thread32First(snapshot, ctypes.byref(objTE32)):
            while True:
                threads.append((
                    int(objTE32.th32ThreadID),
                    int(objTE32.th32OwnerProcessID),
                    cls.get_creation_time_by_threadID(objTE32.th32ThreadID)))
                if not ctypes.windll.kernel32.Thread32Next(snapshot, ctypes.byref(objTE32)):break
        ctypes.windll.kernel32.CloseHandle(snapshot)
        return threads

# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- Process

class Process:
    
    TH32CS_SNAPPROCESS = 0x00000002
    
    @classmethod
    def __get_process_times__(cls, processID):
        lpCreationTime = ctypes.wintypes.FILETIME()
        lpCreationTime.dwSize = ctypes.sizeof(ctypes.wintypes.FILETIME)
        lpExitTime = ctypes.wintypes.FILETIME()
        lpExitTime.dwSize = ctypes.sizeof(ctypes.wintypes.FILETIME)
        lpKernelTime = ctypes.wintypes.FILETIME()
        lpKernelTime.dwSize = ctypes.sizeof(ctypes.wintypes.FILETIME)
        lpUserTime = ctypes.wintypes.FILETIME()
        lpUserTime.dwSize = ctypes.sizeof(ctypes.wintypes.FILETIME)
        hProcess = ctypes.windll.kernel32.OpenProcess(win32con.PROCESS_QUERY_INFORMATION, False, processID)
        ctypes.windll.kernel32.GetProcessTimes(hProcess, ctypes.byref(lpCreationTime), ctypes.byref(lpExitTime), ctypes.byref(lpKernelTime), ctypes.byref(lpUserTime))
        ctypes.windll.kernel32.CloseHandle(hProcess)
        return lpCreationTime, lpExitTime, lpKernelTime, lpUserTime
    
    @classmethod
    def wait_for_input_idle_by_processID(cls, processID, milliseconds=win32event.INFINITE):
        hProcess = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, False, processID)
        win32event.WaitForInputIdle(hProcess, milliseconds)
        win32api.CloseHandle(hProcess)
    
    @classmethod
    def wait_for_input_idle_by_processHandle(cls, processHandle, milliseconds=win32event.INFINITE):
        win32event.WaitForInputIdle(processHandle, milliseconds)
    
    @classmethod
    def get_creation_time_by_processID(cls, processID):
        lpCreationTime, lpExitTime, lpKernelTime, lpUserTime = cls.__get_process_times__(processID)
        return filetime_to_local_datetime(lpCreationTime)
    
    @classmethod
    def get_creation_time_by_processHandle(cls, processHandle):
        threadID, processID = win32process.GetWindowThreadProcessId(processHandle)
        return cls.get_creation_time_by_processID(processID)
    
    @classmethod
    def get_processes(cls, processName=None):
        processes = []
        objPE32 = ProcessEntry32()
        objPE32.dwSize = ctypes.sizeof(ProcessEntry32)
        snapshot = ctypes.windll.kernel32.CreateToolhelp32Snapshot(cls.TH32CS_SNAPPROCESS, 0)
        if ctypes.windll.kernel32.Process32First(snapshot, ctypes.byref(objPE32)):
            while True:
                if processName is None or re.match(processName, objPE32.szExeFile):
                    processes.append((
                        str(objPE32.szExeFile),
                        int(objPE32.th32ProcessID),
                        int(objPE32.th32ParentProcessID),
                        cls.get_creation_time_by_processID(objPE32.th32ProcessID)))
                if not ctypes.windll.kernel32.Process32Next(snapshot, ctypes.byref(objPE32)):break
        ctypes.windll.kernel32.CloseHandle(snapshot)
        return processes
    
    @classmethod
    def get_parent_processID(cls, processID):
        processes = cls.get_processes()
        for _processName, _processID, _parentProcessID, _creationTime in processes:
            if processID == _processID : return _parentProcessID
    
    @classmethod
    def get_processName_by_processID(cls, processID):
        processes = cls.get_processes()
        for _processName, _processID, _parentProcessID, _creationTime in processes:
            if processID == _processID : return _processName
    
    @classmethod
    def get_processID_by_index(cls, processName=None, index=1):
        processes = cls.get_processes(processName)
        processesLen = len(processes)
        if processesLen == 0    : return
        if index > processesLen : return
        for i in xrange(processesLen - 1, 0, -1):
            for j in xrange(0, i):
                if processes[j][3] > processes[j + 1][3]:
                    processes[j], processes[j + 1] = processes[j + 1], processes[j]
        return processes[index - 1][1]
    
    @classmethod
    def exists_by_processID(cls, processID):
        processes = cls.get_processes()
        for _processName, _processID, _parentProcessID, _creationTime in processes:
            if processID == _processID : return True
        return False
    
    @classmethod
    def terminate_by_processID(cls, processID, timeout=20, timestep=0.2):
        begin = time.time()
        while (time.time() - begin <= timeout or timeout <= 0):
            if cls.exists_by_processID(processID):
                try:
                    hProcess = ctypes.windll.kernel32.OpenProcess(win32con.PROCESS_TERMINATE, False, processID)
                    ctypes.windll.kernel32.TerminateProcess(hProcess, 0)
                except Exception, e : pass
            else            : break
            if timeout <= 0 : break
            time.sleep(timestep)
        return not cls.exists_by_processID(processID)

# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- SendKeys

class SendKeys:
    
    WScriptShell = comtypes.client.CreateObject('WScript.Shell')
    
    @classmethod
    def SendKeys(cls, string):cls.WScriptShell.SendKeys(string, True)
    
    @classmethod
    def SendChinese(cls, string):
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(string)
        win32clipboard.CloseClipboard()
        cls.SendKeys('^(v)');time.sleep(0.15)
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.CloseClipboard()

# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- Mouse

class Mouse:
    
    Post = 'Post'
    Send = 'Send'
    Timestep = 0.15
    MouseKeyLeft = 0
    MouseKeyRight = 1
    MouseKeyMiddle = 2
    
    @classmethod
    def __get_locus__(cls, tag_pos, isScreenPos=False):
        ls = []
        try:
            tag_x, tag_y = tag_pos
            cur_x, cur_y = win32api.GetCursorPos()
            if tag_x == cur_x and tag_y == cur_y : return ls
            # -*-
            if isScreenPos:
                tag_x = tag_x * 65559 / win32api.GetSystemMetrics(0)
                tag_y = tag_y * 65559 / win32api.GetSystemMetrics(1)
                cur_x = cur_x * 65559 / win32api.GetSystemMetrics(0)
                cur_y = cur_y * 65559 / win32api.GetSystemMetrics(1)
            # -*-
            dx = tag_x - cur_x
            dy = tag_y - cur_y
            if abs(dx) == 0 and abs(dy) == 0 : return ls
            # -*-
            pixel = 10
            multiple = (abs(dx) or abs(dy)) / pixel
            if abs(dy) != 0 and abs(dx) > abs(dy): multiple = abs(dy) / pixel
            if abs(dx) != 0 and abs(dx) < abs(dy): multiple = abs(dx) / pixel
            #if multiple==0 : multiple=10
            # -*-
            if dx <= 0 and dy <= 0:
                while cur_x >= tag_x and cur_y >= tag_y:
                    if abs(dx) > 0 : cur_x = cur_x + dx / multiple
                    if abs(dy) > 0 : cur_y = cur_y + dy / multiple
                    if cur_x < tag_x or cur_y < tag_y : break
                    ls.append((cur_x, cur_y))
                return ls
            if dx >= 0 and dy >= 0:
                while cur_x <= tag_x and cur_y <= tag_y:
                    if abs(dx) > 0 : cur_x = cur_x + dx / multiple
                    if abs(dy) > 0 : cur_y = cur_y + dy / multiple
                    if cur_x > tag_x or cur_y > tag_y : break
                    ls.append((cur_x, cur_y))
                return ls
            if dx <= 0 and dy >= 0:
                while cur_x >= tag_x and cur_y <= tag_y:
                    if abs(dx) > 0 : cur_x = cur_x + dx / multiple
                    if abs(dy) > 0 : cur_y = cur_y + dy / multiple
                    if cur_x < tag_x or cur_y > tag_y : break
                    ls.append((cur_x, cur_y))
                return ls
            if dx >= 0 and dy <= 0:
                while cur_x <= tag_x and cur_y >= tag_y:
                    if abs(dx) > 0 : cur_x = cur_x + dx / multiple
                    if abs(dy) > 0 : cur_y = cur_y + dy / multiple
                    if cur_x > tag_x or cur_y < tag_y : break
                    ls.append((cur_x, cur_y))
                return ls
        except:return ls
    
    @classmethod
    def evt_move(cls, pos=None, locus=True, isScreenPos=True):
        '''
        @desc: 移动
        @param: pos   <typle>(x, y) 坐标
                locus <bool>        轨迹
        '''
        if type(pos) == types.TupleType and len(pos) == 2 and type(pos[0]) == types.IntType and type(pos[1]) == types.IntType:
            if locus:
                pos_lst = cls.__get_locus__(tag_pos=pos, isScreenPos=isScreenPos)
                for i, (x, y) in enumerate(pos_lst):
                    if not isScreenPos:
                        x = x * 65559 / win32api.GetSystemMetrics(0)
                        y = y * 65559 / win32api.GetSystemMetrics(1)
                    win32api.mouse_event(win32con.MOUSEEVENTF_ABSOLUTE | win32con.MOUSEEVENTF_MOVE, x, y, 0, 0)
            win32api.SetCursorPos(pos)
            time.sleep(cls.Timestep)
            return True
        return False
    
    @classmethod
    def evt_wheel(cls, step=0):
        '''
        @desc: 滚轮滚动
        @param: step <int> 数量，负向上，正向下
        '''
        if type(step) == types.IntType:
            win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, step * win32con.WHEEL_DELTA, 0)
            time.sleep(cls.Timestep)
    
    @classmethod
    def evt_click(cls, pos=None, locus=True, key=MouseKeyLeft, dbl=False):
        '''
        @desc: 点击
        @param: pos      <typle>(x, y) 坐标，移至后点击，默认当前位置
                locus    <bool>        轨迹
                key <int>              按键
                                         #左：Mouse.MouseKeyLeft = 0
                                         #右：Mouse.MouseKeyRight = 1
                                         #中：Mouse.MouseKeyMiddle = 2
                dbl  <bool>            双击
        '''
        if type(pos) == types.NoneType or cls.evt_move(pos, locus):
            if key == cls.MouseKeyLeft:
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN | win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                if dbl:
                    time.sleep(cls.Timestep)
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN | win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            if key == cls.MouseKeyRight:
                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN | win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
                if dbl:
                    time.sleep(cls.Timestep)
                    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN | win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
            if key == cls.MouseKeyMiddle:
                win32api.mouse_event(win32con.MOUSEEVENTF_MIDDLEDOWN | win32con.MOUSEEVENTF_MIDDLEUP, 0, 0, 0, 0)
                if dbl:
                    time.sleep(cls.Timestep)
                    win32api.mouse_event(win32con.MOUSEEVENTF_MIDDLEDOWN | win32con.MOUSEEVENTF_MIDDLEUP, 0, 0, 0, 0)
            time.sleep(cls.Timestep)
    
    @classmethod
    def evt_drag(cls, pos=None, locus=True, key=MouseKeyLeft):
        '''
        @desc: 按下
        @param: pos      <typle>(x, y) 坐标，移至后按下，默认当前位置
                locus    <bool>        轨迹
                key <int>              按键
                                         #左：Mouse.MouseKeyLeft = 0
                                         #右：Mouse.MouseKeyRight = 1
                                         #中：Mouse.MouseKeyMiddle = 2
        '''
        if type(pos) == types.NoneType or cls.evt_move(pos, locus):
            if key == cls.MouseKeyLeft   : win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            if key == cls.MouseKeyRight  : win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
            if key == cls.MouseKeyMiddle : win32api.mouse_event(win32con.MOUSEEVENTF_MIDDLEDOWN, 0, 0, 0, 0)
            time.sleep(cls.Timestep)
    
    @classmethod
    def evt_drop(cls, pos=None, locus=True, key=MouseKeyLeft):
        '''
        @desc: 弹起
        @param: pos      <typle>(x, y) 坐标，移至后弹起，默认当前位置
                locus    <bool>        轨迹
                key <int>              按键
                                         #左：Mouse.MouseKeyLeft = 0
                                         #右：Mouse.MouseKeyRight = 1
                                         #中：Mouse.MouseKeyMiddle = 2
        '''
        if type(pos) == types.NoneType or cls.evt_move(pos, locus):
            if key == cls.MouseKeyLeft   : win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            if key == cls.MouseKeyRight  : win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
            if key == cls.MouseKeyMiddle : win32api.mouse_event(win32con.MOUSEEVENTF_MIDDLEUP, 0, 0, 0, 0)
            time.sleep(cls.Timestep)
    
    # -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
    
    @classmethod
    def __evt_client_to_screen__(cls, handle, pos=None):
        if win32gui.IsWindow(handle):
            if type(pos) == types.NoneType:
                pos = win32api.GetCursorPos()
            else:
                pos = win32gui.ClientToScreen(handle, pos)
        return pos
    
    @classmethod
    def evt_moveIn(cls, handle, pos=None, locus=True):
        if win32gui.IsWindow(handle):
            pos = cls.__evt_client_to_screen__(handle, pos)
            return cls.evt_move(pos, locus)
    
    @classmethod
    def evt_wheelIn(cls, handle, step=0):
        if win32gui.IsWindow(handle):
            cls.evt_wheel(step)
    
    @classmethod
    def evt_clickIn(cls, handle, pos=None, locus=True, key=MouseKeyLeft, dbl=False):
        if win32gui.IsWindow(handle):
            pos = cls.__evt_client_to_screen__(handle, pos)
            cls.evt_click(pos, locus, key, dbl)
    
    @classmethod
    def evt_dragIn(cls, handle, pos=None, locus=True, key=MouseKeyLeft):
        if win32gui.IsWindow(handle):
            pos = cls.__evt_client_to_screen__(handle, pos)
            cls.evt_drag(pos, locus, key)
    
    @classmethod
    def evt_dropIn(cls, handle, pos=None, locus=True, key=MouseKeyLeft):
        if win32gui.IsWindow(handle):
            pos = cls.__evt_client_to_screen__(handle, pos)
            cls.evt_drop(pos, locus, key)
    
    # -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
    
    @classmethod
    def __get_msg_api__(cls, msg=Post):
        if msg == cls.Post : return win32api.PostMessage
        if msg == cls.Send : return win32api.SendMessage
        return win32api.PostMessage
    
    @classmethod
    def msg_moveIn(cls, handle, pos=None, msg=Post, locus=True):
        '''
        @desc: PostMessage或SendMessage移动(窗口内)
        @param: handle <int>           窗口句柄
                pos    <tuple>(x, y)   坐标
                msg    <str>Post|Send  类型
                locus  <bool>          轨迹
        '''
        if win32gui.IsWindow(handle) and type(pos) == types.TupleType and len(pos) == 2 and type(pos[0]) == types.IntType and type(pos[1]) == types.IntType:
            msg_api = cls.__get_msg_api__(msg)
            if locus:
                pos_lst = cls.__get_locus__(tag_pos=win32gui.ClientToScreen(handle, pos), isScreenPos=False)
                for i, (x, y) in enumerate(pos_lst):
                    x, y = win32gui.ScreenToClient(handle, (x, y))
                    msg_api(handle, win32con.WM_MOUSEMOVE, 0, win32api.MAKELONG(x, y))
                    win32api.SetCursorPos(win32gui.ClientToScreen(handle, (x, y)))
                    time.sleep(0.001)
            x, y = pos
            msg_api(handle, win32con.WM_MOUSEMOVE, 0, win32api.MAKELONG(x, y))
            win32api.SetCursorPos(win32gui.ClientToScreen(handle, pos))
            time.sleep(cls.Timestep)
            return True
        return False
    
    @classmethod
    def msg_wheelIn(cls, handle, step=0, msg=Post):
        '''
        @desc: PostMessage或SendMessage滚轮滚动(窗口内)
        @param: handle <int> 窗口句柄
                step   <int> 数量，负向上，正向下
                msg    <str>Post|Send  类型
        '''
        if win32gui.IsWindow(handle) and type(step) == types.IntType:
            msg_api = cls.__get_msg_api__(msg)
            msg_api(handle, win32con.WM_MOUSEWHEEL, ((step * win32con.WHEEL_DELTA) << 16) | 0, 0)
            time.sleep(cls.Timestep)
    
    @classmethod
    def msg_clickIn(cls, handle, pos=None, msg=Post, locus=True, key=MouseKeyLeft, dbl=False):
        '''
        @desc: PostMessage或SendMessage按键点击(窗口内)
        @param: handle   <int>           窗口句柄
                pos      <typle>(x, y)   坐标，移至后点击，默认当前位置
                msg      <str>Post|Send  类型
                locus    <bool>          轨迹
                key <int>                按键
                                          #左：Mouse.MouseKeyLeft = 0
                                          #右：Mouse.MouseKeyRight = 1
                                          #中：Mouse.MouseKeyMiddle = 2
                dbl  <bool>              双击
        '''
        if win32gui.IsWindow(handle):
            msg_api = cls.__get_msg_api__(msg)
            if type(pos) == types.NoneType:
                pos = win32api.GetCursorPos()
                pos = win32gui.ScreenToClient(handle, pos)
            x, y = pos
            if cls.msg_moveIn(handle, pos, msg, locus):
                if key == cls.MouseKeyLeft:
                    msg_api(handle, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, win32api.MAKELONG(x, y))
                    msg_api(handle, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, win32api.MAKELONG(x, y))
                    if dbl:
                        time.sleep(cls.Timestep)
                        msg_api(handle, win32con.WM_LBUTTONDBLCLK, win32con.MK_LBUTTON, win32api.MAKELONG(x, y))
                        msg_api(handle, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, win32api.MAKELONG(x, y))
                if key == cls.MouseKeyRight:
                    msg_api(handle, win32con.WM_RBUTTONDOWN, win32con.MK_RBUTTON, win32api.MAKELONG(x, y))
                    msg_api(handle, win32con.WM_RBUTTONUP, win32con.MK_RBUTTON, win32api.MAKELONG(x, y))
                    if dbl:
                        time.sleep(cls.Timestep)
                        msg_api(handle, win32con.WM_RBUTTONDBLCLK, win32con.MK_RBUTTON, win32api.MAKELONG(x, y))
                        msg_api(handle, win32con.WM_RBUTTONUP, win32con.MK_RBUTTON, win32api.MAKELONG(x, y))
                if key == cls.MouseKeyMiddle:
                    msg_api(handle, win32con.WM_MBUTTONDOWN, win32con.MK_MBUTTON, win32api.MAKELONG(x, y))
                    msg_api(handle, win32con.WM_MBUTTONUP, win32con.MK_MBUTTON, win32api.MAKELONG(x, y))
                    if dbl:
                        time.sleep(cls.Timestep)
                        msg_api(handle, win32con.WM_MBUTTONDBLCLK, win32con.MK_MBUTTON, win32api.MAKELONG(x, y))
                        msg_api(handle, win32con.WM_MBUTTONUP, win32con.MK_MBUTTON, win32api.MAKELONG(x, y))
                time.sleep(cls.Timestep)
    
    @classmethod
    def msg_dragIn(cls, handle, pos=None, msg=Post, locus=True, key=MouseKeyLeft):
        '''
        @desc: PostMessage或SendMessage按键按下(窗口内)
        @param: handle   <int>           窗口句柄
                pos      <typle>(x, y)   坐标，移至后按下，默认当前位置
                msg      <str>Post|Send  类型
                locus    <bool>          轨迹
                key <int>                按键
                                          #左：Mouse.MouseKeyLeft = 0
                                          #右：Mouse.MouseKeyRight = 1
                                          #中：Mouse.MouseKeyMiddle = 2
        '''
        if win32gui.IsWindow(handle):
            msg_api = cls.__get_msg_api__(msg)
            if type(pos) == types.NoneType:
                pos = win32api.GetCursorPos()
                pos = win32gui.ScreenToClient(handle, pos)
            x, y = pos
            if cls.msg_moveIn(handle, pos, msg, locus):
                if key == cls.MouseKeyLeft   : msg_api(handle, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, win32api.MAKELONG(x, y))
                if key == cls.MouseKeyRight  : msg_api(handle, win32con.WM_RBUTTONDOWN, win32con.MK_RBUTTON, win32api.MAKELONG(x, y))
                if key == cls.MouseKeyMiddle : msg_api(handle, win32con.WM_MBUTTONDOWN, win32con.MK_MBUTTON, win32api.MAKELONG(x, y))
                time.sleep(cls.Timestep)
    
    @classmethod
    def msg_dropIn(cls, handle, pos=None, msg=Post, locus=True, key=MouseKeyLeft):
        '''
        @desc: PostMessage或SendMessage按键弹起(窗口内)
        @param: handle   <int>           窗口句柄
                pos      <typle>(x, y)   坐标，移至后弹起，默认当前位置
                msg      <str>Post|Send  类型
                locus    <bool>          轨迹
                key <int>                按键
                                          #左：Mouse.MouseKeyLeft = 0
                                          #右：Mouse.MouseKeyRight = 1
                                          #中：Mouse.MouseKeyMiddle = 2
        '''
        if win32gui.IsWindow(handle):
            msg_api = cls.__get_msg_api__(msg)
            if type(pos) == types.NoneType:
                pos = win32api.GetCursorPos()
                pos = win32gui.ScreenToClient(handle, pos)
            x, y = pos
            if cls.msg_moveIn(handle, pos, msg, locus):
                if key == cls.MouseKeyLeft   : msg_api(handle, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, win32api.MAKELONG(x, y))
                if key == cls.MouseKeyRight  : msg_api(handle, win32con.WM_RBUTTONUP, win32con.MK_RBUTTON, win32api.MAKELONG(x, y))
                if key == cls.MouseKeyMiddle : msg_api(handle, win32con.WM_MBUTTONUP, win32con.MK_MBUTTON, win32api.MAKELONG(x, y))
                time.sleep(cls.Timestep)
    
    # -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
    
    @classmethod
    def __msg_screen_to_client__(cls, handle, pos=None):
        if win32gui.IsWindow(handle):
            if type(pos) == types.NoneType : pos = win32api.GetCursorPos()
            pos = win32gui.ScreenToClient(handle, pos)
            return pos
    
    @classmethod
    def msg_move(cls, handle, pos=None, msg=Post, locus=True):
        pos = cls.__msg_screen_to_client__(handle, pos)
        cls.msg_moveIn(handle, pos, msg, locus)
    
    @classmethod
    def msg_wheel(cls, handle, step=0, msg=Post):
        cls.msg_wheelIn(handle, step, msg)
    
    @classmethod
    def msg_click(cls, handle, pos=None, msg=Post, locus=True, key=MouseKeyLeft, dbl=False):
        pos = cls.__msg_screen_to_client__(handle, pos)
        cls.msg_clickIn(handle, pos, msg, locus, key, dbl)
    
    @classmethod
    def msg_drag(cls, handle, pos=None, msg=Post, locus=True, key=MouseKeyLeft):
        pos = cls.__msg_screen_to_client__(handle, pos)
        cls.msg_dragIn(handle, pos, msg, locus, key)
    
    @classmethod
    def msg_drop(cls, handle, pos=None, msg=Post, locus=True, key=MouseKeyLeft):
        pos = cls.__msg_screen_to_client__(handle, pos)
        cls.msg_dropIn(handle, pos, msg, locus, key)

# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- IEConst

class IEConst:
    
    IEF_ClassName = 'IEFrame'
    IES_ClassName = 'Internet Explorer_Server'
    IEF_ProcessID = 'IEF_ProcessID'
    IEF_Process_CreationTime = 'IEF_Process_CreationTime'
    IEF_ThreadID = 'IEF_ThreadID'
    IEF_Thread_CreationTime = 'IEF_Thread_CreationTime'
    IEF_Handle = 'IEF_Handle'
    IES_ProcessID = 'IES_ProcessID'
    IES_Process_CreationTime = 'IES_Process_CreationTime'
    IES_ThreadID = 'IES_ThreadID'
    IES_Thread_CreationTime = 'IES_Thread_CreationTime'
    IES_Handle = 'IES_Handle'

# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- IEProxy

class IEProxy:
    
    INTERNET_PER_CONN_FLAGS = 1
    PROXY_TYPE_DIRECT = 0x00000001
    PROXY_TYPE_PROXY = 0x00000002
    INTERNET_PER_CONN_PROXY_SERVER = 2
    INTERNET_PER_CONN_PROXY_BYPASS = 3
    INTERNET_OPTION_PER_CONNECTION_OPTION = 75
    INTERNET_OPTION_SETTINGS_CHANGED = 39
    INTERNET_OPTION_REFRESH = 37
    
    @classmethod
    def clean(cls):cls.set()
    
    @classmethod
    def set(cls, proxy_server=None, proxy_bypass='*.local', conn_type=None):
        conn_option_list = IEProxy_INTERNET_PER_CONN_OPTION_LIST()
        conn_option_list.dwSize = ctypes.sizeof(IEProxy_INTERNET_PER_CONN_OPTION_LIST)
        conn_option_list.pszConnection = conn_type
        if proxy_server:
            conn_option_list.dwOptionCount = 3
            conn_options_cls = IEProxy_INTERNET_PER_CONN_OPTION * 3
            conn_options_obj = conn_options_cls()
            conn_options_obj[0].dwOption = cls.INTERNET_PER_CONN_FLAGS
            conn_options_obj[0].Value.dwValue = cls.PROXY_TYPE_DIRECT | cls.PROXY_TYPE_PROXY
            conn_options_obj[1].dwOption = cls.INTERNET_PER_CONN_PROXY_SERVER
            conn_options_obj[1].Value.pszValue = proxy_server
            conn_options_obj[2].dwOption = cls.INTERNET_PER_CONN_PROXY_BYPASS
            conn_options_obj[2].Value.pszValue = proxy_bypass
        else:
            conn_option_list.dwOptionCount = 1
            conn_options_cls = IEProxy_INTERNET_PER_CONN_OPTION * 1
            conn_options_obj = conn_options_cls()
            conn_options_obj[0].dwOption = cls.INTERNET_PER_CONN_FLAGS
            conn_options_obj[0].Value.dwValue = cls.PROXY_TYPE_DIRECT
        conn_option_list.pOptions = conn_options_obj
        ctypes.windll.Wininet.InternetSetOptionA(0, cls.INTERNET_OPTION_PER_CONNECTION_OPTION, ctypes.addressof(conn_option_list), ctypes.sizeof(conn_option_list))
        ctypes.windll.Wininet.InternetSetOptionA(0, cls.INTERNET_OPTION_SETTINGS_CHANGED, 0, 0)
        ctypes.windll.Wininet.InternetSetOptionA(0, cls.INTERNET_OPTION_REFRESH, 0, 0)

# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- IERegistry

class IERegistry:
    
    IE_Registry_Trusted_Sites_Path = r'Software\Microsoft\Windows\CurrentVersion\Internet Settings\ZoneMap\Domains'
    
    @classmethod
    def get_ie_exe_path(cls):
        path = os.path.join(os.environ.get('PROGRAMFILES', r'C:\Program Files'), 'Internet Explorer', 'iexplore.exe')
        app_path_registry_path = r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\IEXPLORE.EXE'
        key = win32api.RegOpenKey(win32con.HKEY_LOCAL_MACHINE, app_path_registry_path, 0, win32con.KEY_READ)
        for item in win32api.RegEnumValue(key, 0):
            try    :
                if os.path.exists(str(item)) and os.path.isfile(str(item)) : path = str(item)
            except : pass
        win32api.RegCloseKey(key)
        return path
    
    @classmethod
    def get_ie_version(cls):
        objRegKey = win32api.RegOpenKey(win32con.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Internet Explorer', 0, win32con.KEY_READ)
        keyValue = win32api.RegQueryValueEx(objRegKey, 'Version')[0]
        win32api.RegCloseKey(objRegKey)
        return int((re.findall('^\d', keyValue) + [0])[0])
    
    @classmethod
    def add_trusted_sites(cls, urlString):
        regedit_path = cls.IE_Registry_Trusted_Sites_Path
        scheme, netloc, url, params, query, fragment = urllib2.urlparse.urlparse(urlString)
        host = None
        if url != ''    : host = '.'.join(url.split('/')[0].split('.')[-2:])
        if netloc != '' : host = '.'.join(netloc.split('.')[-2:])
        if host is None : return
        key_reader = win32api.RegOpenKey(win32con.HKEY_CURRENT_USER, regedit_path, 0, win32con.KEY_READ)
        for name, reserved, cls, last_write_time in win32api.RegEnumKeyEx(key_reader):
            if name == host : win32api.RegCloseKey(key_reader);return
        win32api.RegCloseKey(key_reader)
        key_writer = win32api.RegOpenKey(win32con.HKEY_CURRENT_USER, regedit_path, 0, win32con.KEY_WRITE)
        new_writer = win32api.RegCreateKey(key_writer, host)
        win32api.RegSetValueEx(new_writer, '*', 0, win32con.REG_DWORD, 2)
        win32api.RegCloseKey(new_writer)
        win32api.RegCloseKey(key_writer)
    
    @classmethod
    def del_trusted_sites(cls, urlString):
        regedit_path = cls.IE_Registry_Trusted_Sites_Path
        scheme, netloc, url, params, query, fragment = urllib2.urlparse.urlparse(urlString)
        host = None
        if url != ''    : host = '.'.join(url.split('/')[0].split('.')[-2:])
        if netloc != '' : host = '.'.join(netloc.split('.')[-2:])
        if host is None : return
        key_reader = win32api.RegOpenKey(win32con.HKEY_CURRENT_USER, regedit_path, 0, win32con.KEY_READ)
        key_writer = win32api.RegOpenKey(win32con.HKEY_CURRENT_USER, regedit_path, 0, win32con.KEY_WRITE)
        for name, reserved, cls, last_write_time in win32api.RegEnumKeyEx(key_reader):
            if name == host : win32api.RegDeleteKey(key_writer, host)
        win32api.RegCloseKey(key_writer)
        win32api.RegCloseKey(key_reader)
    
    @classmethod
    def setting_config_trusted_sites(cls, items=[]):
        for item in items:
            try                 : cls.add_trusted_sites(item)
            except Exception, e : print 'Warning: IERegistry.setting_config_trusted_sites "%s"' % str(e)
    
    @classmethod
    def restore_config_trusted_sites(cls, items=[]):
        for item in items:
            try                 : cls.del_trusted_sites(item)
            except Exception, e : print 'Warning: IERegistry.restore_config_trusted_sites "%s"' % str(e)

# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- IEF/IES IEHandle

class IEHandle:
    
    @classmethod
    def get_ief_from_point(cls, timeout=None, timestep=0.15):
        if timeout is None:timeout = True
        while timeout:
            handle = Handle.get_handle_from_point_by_classname(IEConst.IEF_ClassName)
            if handle:return handle
            if type(timeout)in [types.IntType, types.FloatType]:
                timeout -= timestep
                if timeout < 0:return
            time.sleep(timestep)
    
    @classmethod
    def get_ies_from_point(cls, timeout=None, timestep=0.15):
        if timeout is None:timeout = True
        while timeout:
            handle = Handle.get_handle_from_point_by_classname(IEConst.IES_ClassName)
            if handle:return handle
            if type(timeout)in [types.IntType, types.FloatType]:
                timeout -= timestep
                if timeout < 0:return
            time.sleep(timestep)
    
    @classmethod
    def ies_is_valid(cls, ies_handle):
        if Handle.is_valid(ies_handle) and Handle.get_classname(ies_handle) == IEConst.IES_ClassName : return True
        return False
    
    @classmethod
    def ies_is_invalid(cls, ies_handle):
        if Handle.is_invalid(ies_handle) or Handle.get_classname(ies_handle) != IEConst.IES_ClassName : return True
        return False
    
    @classmethod
    def __callback_get_ies_enum_child_windows__(cls, ies_handle, ies_handles):
        if win32gui.IsWindow(ies_handle) and win32gui.GetClassName(ies_handle) == IEConst.IES_ClassName : ies_handles.append(ies_handle)
    
    @classmethod
    def __callback_get_iefs_enum_windows__(cls, ief_handle, extra_args):
        if win32gui.IsWindow(ief_handle):
            ief_classname = extra_args[0]
            iefs = extra_args[1]
            if ief_classname and ief_classname != win32gui.GetClassName(ief_handle) : return
            ies_handles = []
            # -*-
            try : win32gui.EnumChildWindows(ief_handle, cls.__callback_get_ies_enum_child_windows__, ies_handles)
            except Exception, e : pass
            # -*-
            for ies_handle in ies_handles:
                ief_threadID, ief_processID = win32process.GetWindowThreadProcessId(ief_handle)
                ies_threadID, ies_processID = win32process.GetWindowThreadProcessId(ies_handle)
                iefs.append({
                    IEConst.IEF_ProcessID : ief_processID,
                    IEConst.IEF_Process_CreationTime : Process.get_creation_time_by_processID(ief_processID),
                    IEConst.IEF_ThreadID             : ief_threadID,
                    IEConst.IEF_Thread_CreationTime  : Thread.get_creation_time_by_threadID(ief_threadID),
                    IEConst.IEF_Handle               : ief_handle,
                    # -*-
                    IEConst.IES_ProcessID            : ies_processID,
                    IEConst.IES_Process_CreationTime : Process.get_creation_time_by_processID(ies_processID),
                    IEConst.IES_ThreadID             : ies_threadID,
                    IEConst.IES_Thread_CreationTime  : Thread.get_creation_time_by_threadID(ies_threadID),
                    IEConst.IES_Handle               : ies_handle
                })
    
    @classmethod
    def sort_handles_by_threadCreationTime(cls, handles):
        length = len(handles)
        for i in xrange(length - 1, 0, -1):
            for j in xrange(0, i):
                if Thread.get_creation_time_by_threadHandle(handles[j]) > Thread.get_creation_time_by_threadHandle(handles[j + 1]):
                    handles[j], handles[j + 1] = handles[j + 1], handles[j]
        return handles
    
    @classmethod
    def get_all_iefs(cls, ief_classname=None):
        iefs = []
        win32gui.EnumWindows(cls.__callback_get_iefs_enum_windows__, (ief_classname, iefs))
        length = len(iefs)
        for i in xrange(length - 1, 0, -1):
            for j in xrange(0, i):
                if iefs[j][IEConst.IES_Thread_CreationTime] > iefs[j + 1][IEConst.IES_Thread_CreationTime]:
                    iefs[j], iefs[j + 1] = iefs[j + 1], iefs[j]
        return iefs
    
    @classmethod
    def get_all_ies(cls, ief_classname=None):
        iefs = cls.get_all_iefs(ief_classname)
        ies = []
        for item in iefs:ies.append(item[IEConst.IES_Handle])
        return ies
    
    @classmethod
    def get_all_visible_iefs(cls, ief_classname=None):
        _VisibleIEFS = []
        iefs = cls.get_all_iefs(ief_classname)
        for item in iefs:
            if win32gui.IsWindowVisible(item[IEConst.IEF_Handle]) and win32gui.IsWindowVisible(item[IEConst.IES_Handle]):
                _VisibleIEFS.append(item)
        return _VisibleIEFS
    
    @classmethod
    def get_visible_ies_by_ief(cls, ief_handle):
        ies_handles = []
        if win32gui.IsWindow(ief_handle):
            try : win32gui.EnumChildWindows(ief_handle, cls.__callback_get_ies_enum_child_windows__, ies_handles)
            except Exception, e : pass
        ies_handles = cls.sort_handles_by_threadCreationTime(ies_handles)
        for ies_handle in ies_handles:
            if win32gui.IsWindowVisible(ies_handle):return ies_handle
    
    @classmethod
    def get_all_ies_by_ief(cls, ief_handle):
        ies_handles = []
        if win32gui.IsWindow(ief_handle):
            try : win32gui.EnumChildWindows(ief_handle, cls.__callback_get_ies_enum_child_windows__, ies_handles)
            except Exception, e : pass
        ies_handles = cls.sort_handles_by_threadCreationTime(ies_handles)
        return ies_handles
    
    @classmethod
    def get_iefs_by_ief(cls, ief_handle, ief_classname=None):
        all_iefs = cls.get_all_iefs(ief_classname)
        for item in all_iefs:
            if item[IEConst.IEF_Handle] == ief_handle:return item
    
    @classmethod
    def get_iefs_by_ies(cls, ies_handle, ief_classname=None):
        all_iefs = cls.get_all_iefs(ief_classname)
        for item in all_iefs:
            if item[IEConst.IES_Handle] == ies_handle:return item
    
    @classmethod
    def get_iefs_by_threadID(cls, threadID):
        all_iefs = cls.get_all_iefs()
        for item in all_iefs:
            if item[IEConst.IES_ThreadID] == threadID:return item
    
    @classmethod
    def active_ief_by_ies(cls, ies_handle):
        iefs = cls.get_iefs_by_ies(ies_handle)
        Handle.active(iefs[IEConst.IEF_Handle])
    
    @classmethod
    def active(cls, ief_handle, ies_handle):
        Handle.active(ief_handle)
        if not win32gui.IsWindowVisible(ies_handle):
            if ies_handle == cls.get_visible_ies_by_ief(ief_handle):return
            all_ies_handle = cls.get_all_ies_by_ief(ief_handle)
            if len(all_ies_handle) == 1 : return
            for i, item in enumerate(all_ies_handle):
                try    : SendKeys.SendKeys('^{TAB}');time.sleep(0.15)
                except : pass
                if ies_handle == cls.get_visible_ies_by_ief(ief_handle):return

# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- IEProcess

class IEProcess:
    
    IEDefaultUrl = 'about:blank'
    IEProcessName = 'iexplore.exe'
    IE8_INT_Version = 8
    ERROR_CreateProcessTimeout = 'Create process timeout.'
    ERROR_CreateProcessMultiple = 'Create process too much. Too uncertain object.'
    ERROR_CreateProcess = 'Create process error.'
    CreateProcessTimeout = 60
    CreateProcessTimestep = 0.2
    
    @classmethod
    def get_ie8_parent_processID(cls):return Process.get_processID_by_index(cls.IEProcessName, 1)

    @classmethod
    def get_ie_processInfo_by_index(cls, index=1, justIE=True):
        if justIE : ief_classname = IEConst.IEF_ClassName
        else      : ief_classname = None
        all_iefs = IEHandle.get_all_iefs(ief_classname=ief_classname)
        all_iefs_length = len(all_iefs)
        if all_iefs_length == 0    : return
        if index > all_iefs_length : return
        return all_iefs[index - 1]
    
    @classmethod
    def __base_create_ie_process__(cls, url=IEDefaultUrl):
        hProcess, hThread, dwProcessId, dwThreadId = win32process.CreateProcess(IERegistry.get_ie_exe_path(), ' "' + url + '"', None, None, 0, win32process.CREATE_NEW_CONSOLE, None, None, win32process.STARTUPINFO())
        Process.wait_for_input_idle_by_processHandle(hProcess, 1000 * 30)
        return hProcess, hThread, dwProcessId, dwThreadId
    
    @classmethod
    def __create_ie_process__(cls, url=IEDefaultUrl):
        try:
            hProcess, hThread, dwProcessId, dwThreadId = cls.__base_create_ie_process__(url)
            Process.wait_for_input_idle_by_processHandle(hProcess, 1000 * 60)
            for i in xrange(50):
                newIEFS = IEHandle.get_iefs_by_threadID(dwThreadId)
                if newIEFS != None : break
                time.sleep(0.1)
            Process.wait_for_input_idle_by_processID(newIEFS[IEConst.IES_ProcessID], 1000 * 60)
            return newIEFS
        except Exception, e:
            RaiseERROR_CreateProcess = Exception(cls.ERROR_CreateProcess)
            raise RaiseERROR_CreateProcess
    
    @classmethod
    def __create_ie8_process__(cls, url=IEDefaultUrl, timeout=CreateProcessTimeout, timestep=CreateProcessTimestep):
        begin = time.time()
        beforeIES = IEHandle.get_all_ies(ief_classname=IEConst.IEF_ClassName)
        hProcess, hThread, dwProcessId, dwThreadId = cls.__base_create_ie_process__(url)
        Process.wait_for_input_idle_by_processHandle(hProcess, 1000 * 60)
        while time.time() - begin <= timeout:
            lastIES = IEHandle.get_all_ies(ief_classname=IEConst.IEF_ClassName)
            newIES = list(set(lastIES) - set(beforeIES))
            if len(newIES) == 1:
                newIEFS = IEHandle.get_iefs_by_ies(ies_handle=newIES[0], ief_classname=IEConst.IEF_ClassName)
                Process.wait_for_input_idle_by_processID(newIEFS[IEConst.IES_ProcessID], 1000 * 60)
                #经过试验，0.3s内能够检测到句柄失效，如果后续有出现未检测到的情况，可以适当添加时间；
                time.sleep(0.3)
                if IEHandle.ies_is_valid(newIEFS[IEConst.IES_Handle]):
                    return newIEFS
            if len(newIES) > 1 :
                RaiseERROR_CreateProcessMultiple = Exception(cls.ERROR_CreateProcessMultiple)
                raise RaiseERROR_CreateProcessMultiple
            time.sleep(timestep)
        RaiseERROR_CreateProcessTimeout = Exception(cls.ERROR_CreateProcessTimeout)
        raise RaiseERROR_CreateProcessTimeout
    
    @classmethod
    def create_ie_process(cls, url=IEDefaultUrl, timeout=CreateProcessTimeout, timestep=CreateProcessTimestep):
        if url is None : url = cls.IEDefaultUrl
        return cls.__create_ie8_process__(url, timeout, timestep)
        #if IERegistry.get_ie_version() < cls.IE8_INT_Version : return cls.__create_ie_process__(url)
        #else                                                 : return cls.__create_ie8_process__(url, timeout, timestep)
    
    @classmethod
    def create_ie_process2(cls, url=IEDefaultUrl, timeout=CreateProcessTimeout, timestep=CreateProcessTimestep):
        begin = time.time()
        ie = win32com.client.dynamic.Dispatch("InternetExplorer.Application")
        ie.visible = 1
        ie.navigate(url)
        while time.time() - begin <= timeout:
            iefs = IEHandle.get_iefs_by_ief(ie.hwnd)
            if iefs : return iefs
            time.sleep(timestep)
        RaiseERROR_CreateProcessTimeout = Exception(cls.ERROR_CreateProcessTimeout)
        raise RaiseERROR_CreateProcessTimeout

# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- IECOM

class IECOM:
    
    JSCore = []
    try    : MSHTML = comtypes.client.GetModule(os.path.join(win32api.GetSystemDirectory(), 'mshtml.tlb'))
    except : raise Exception("Error: can't init 'mshtml.tlb'")
    try    : OLEACC = ctypes.oledll.LoadLibrary(os.path.join(win32api.GetSystemDirectory(), 'oleacc.dll'))
    except : raise Exception("Error: can't init 'oleacc.dll'")
    try    : SHDocVw = comtypes.client.GetModule(os.path.join(win32api.GetSystemDirectory(), 'shdocvw.dll'))
    except : raise Exception("Error: can't init 'shdocvw.dll'")
    try    : ServProvTLB = comtypes.client.GetModule(os.path.join(APPDATA_IELIB_PATH, 'ServProv.tlb'))
    except : raise Exception("Error: can't init 'ServProv.tlb'")
    try    : comtypes.client.CreateObject('MSScriptControl.ScriptControl')
    except : raise Exception("Error: can't init 'JSEngine'")
    
    
    @classmethod
    def __get_lresult__(cls, ies_handle):
        lresult = ctypes.c_ulong()
        ret = ctypes.windll.user32.SendMessageTimeoutA(ctypes.c_int(ies_handle), ctypes.c_int(win32api.RegisterWindowMessage('WM_HTML_GETOBJECT')), ctypes.c_int(0), ctypes.c_int(0), ctypes.c_int(win32con.SMTO_BLOCK), ctypes.c_int(10000), ctypes.byref(lresult))
        if ret == 0 : WindowsLastError = WindowsError('Last Error [%s]' % ctypes.windll.kernel32.GetLastError());raise WindowsLastError
        return lresult
    
    @classmethod
    def get_ihtmldocument2(cls, ies_handle):
        #2013.06.20 terisli support ie9
        #version = cls.__get_ieversion__();
        #if version >= 9:
        #    return cls.__get_ihtmldocument2_ie9(ies_handle);

        begin = time.time()
        while time.time() - begin < 30:
            try:
                lresult = cls.__get_lresult__(ies_handle)
                doc2 = ctypes.POINTER(cls.MSHTML.IHTMLDocument2)()
                cls.OLEACC.ObjectFromLresult(lresult, ctypes.byref(cls.MSHTML.IHTMLDocument2._iid_), 0, ctypes.byref(doc2))
                doc2.url
                doc2.readyState
                return doc2
            except:
                time.sleep(0.03)
        raise Exception('Error: IE COM ERROR')
    
    @classmethod
    def __get_ieversion__(cls):
        filename = win32api.GetSystemDirectory() + os.sep + "mshtml.dll";
        info = win32api.GetFileVersionInfo(filename, os.sep);
        version = win32api.HIWORD(info['FileVersionMS'])
        return version;
    
    @classmethod
    def __get_ihtmldocument2_ie9(cls, ies_handle):
        begin = time.time()
        import pythoncom;
        while time.time() - begin < 30:
            try:
                msg = win32gui.RegisterWindowMessage('WM_HTML_GETOBJECT')             
                ret, lresult = win32gui.SendMessageTimeout(ies_handle, msg, 0, 0, win32con.SMTO_ABORTIFHUNG, 1000)
                obj = pythoncom.ObjectFromLresult(lresult, pythoncom.IID_IDispatch, 0);
                doc2 = win32com.client.dynamic.Dispatch(obj)
                doc2.url
                doc2.readyState
                return doc2
            except:
                time.sleep(0.03)
        raise Exception('Error: IE COM ERROR')

    @classmethod
    def get_ihtmlwindow2(cls, doc2):return doc2.Script.QueryInterface(cls.MSHTML.IHTMLWindow2)
    
    @classmethod
    def get_iwebbrowser2(cls, win2):
        iServiceProvider = win2.QueryInterface(cls.ServProvTLB.IServiceProvider, cls.ServProvTLB.IServiceProvider._iid_)
        return iServiceProvider.QueryService(cls.SHDocVw.IWebBrowserApp._iid_, cls.SHDocVw.IWebBrowser2)
    
    @classmethod
    def get_engine(cls, doc2, win2):
        engine = comtypes.client.CreateObject('MSScriptControl.ScriptControl')
        engine.AllowUI = True
        engine.Language = 'JavaScript'
        engine.UseSafeSubset = True
        engine.AddObject('document', doc2, True)
        engine.AddObject('window', win2, True)
        return engine
    
    @classmethod
    def get_com_objs(cls, win2):
        browser2 = cls.get_iwebbrowser2(win2)
        doc2 = browser2.document
        win2 = browser2.document.Script.QueryInterface(cls.MSHTML.IHTMLWindow2)
        engine = cls.get_engine(doc2, win2)
        browser2.Release();browser2 = None
        return doc2, win2, engine
    
    @classmethod
    def get_jscore(cls):
        if len(cls.JSCore) > 0 : return cls.JSCore
        jscore_lib_path = os.path.join(APPDATA_IELIB_PATH, 'JSCore.lib')
        if not os.path.exists(jscore_lib_path) : raise Exception("Error: can't init 'JSCore.lib'")
        conn = sqlite3.connect(jscore_lib_path)
        cursor = conn.cursor()
        cursor.execute("select datas from JSCore")
        for line in cursor.fetchall():cls.JSCore.append(urllib.unquote(line[0].encode('UTF-8')).decode('UTF-8'))
        cursor.close()
        conn.close()
        return cls.JSCore

