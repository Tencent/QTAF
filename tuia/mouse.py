# -*- coding: utf-8 -*-
"""
鼠标操作模块
"""
#10/09/14 allenpan    创建
#10/11/02 aaronlai    添加Mouse.sendClick函数   
#10/11/04 allenpan    修改sendClick方法，使用绝对坐标
#10/12/12 aaronlai    修改Mouse.sendClick方法
#10/12/14 aaronlai    修改Mouse.sendClick方法
#10/12/15 aaronlai    修改Mouse.sendClick方法
#11/01/11 aaronlai    增加Mouse.sendNCClick方法
#11/01/13 aaronlai    修改Mouse.drag方法
#11/03/09 dadalin     修改Mouse.sendClick方法
#11/03/23 dadalin     修改Mouse.sendClick方法，支持CTRL/SHIFT

import win32api
import win32con
import win32gui
import time

class MouseFlag(object):
    '''鼠标按键枚举类
    '''
    LeftButton, MiddleButton, RightButton=range(3)

class MouseClickType(object):
    '''鼠标点击枚举类
    '''
    SingleClick, DoubleClick = range(2)    

class MouseCursorType(object):
    '''鼠标图标枚举类型
    '''
    Arrow, Hand, Busy, Cross, No, Help, IBeam = range(7) 
    
_cursor_flags = { 
                 0:win32con.IDC_ARROW,
                 1:win32con.IDC_HAND,
                 2:win32con.IDC_WAIT,
                 3:win32con.IDC_CROSS,
                 4:win32con.IDC_NO,
                 5:win32con.IDC_HELP,
                 6:win32con.IDC_IBEAM,
                 }
    
_mouse_msg={
    MouseFlag.LeftButton: [win32con.MOUSEEVENTF_LEFTDOWN, win32con.MOUSEEVENTF_LEFTUP],
    MouseFlag.MiddleButton: [win32con.MOUSEEVENTF_MIDDLEDOWN, win32con.MOUSEEVENTF_MIDDLEUP],
    MouseFlag.RightButton: [win32con.MOUSEEVENTF_RIGHTDOWN, win32con.MOUSEEVENTF_RIGHTUP]
    }

_mouse_msg_param={
    MouseFlag.LeftButton: [win32con.WM_LBUTTONDOWN, win32con.WM_LBUTTONUP, 1, win32con.WM_LBUTTONDBLCLK], 
    MouseFlag.MiddleButton:  [win32con.WM_MBUTTONDOWN, win32con.WM_MBUTTONUP, 16, win32con.WM_RBUTTONDBLCLK],
    MouseFlag.RightButton: [win32con.WM_RBUTTONDOWN, win32con.WM_RBUTTONUP, 2, win32con.WM_MBUTTONDBLCLK]
    }

_mouse_ncmsg_param={
    MouseFlag.LeftButton: [win32con.WM_NCLBUTTONDOWN, win32con.WM_LBUTTONUP, 1, win32con.WM_NCLBUTTONDBLCLK], 
    }


class Mouse(object):
    '''鼠标操作静态类
    '''
    
    _last_click_time = time.time()
    
    @staticmethod
    def click(x, y, flag=MouseFlag.LeftButton, 
              clicktype=MouseClickType.SingleClick):
        """鼠标点击(x,y)点
        
        :param x: 屏幕x坐标
        :type x: int  
        :param y: 屏幕y坐标
        :type y: int
        :param mouseFlag: 鼠标按钮
        :type mouseFlag: tuia.mouse.MouseFlag
        :param clickType: 鼠标动作,如双击还是单击
        :type clickType: tuia.mouse.MouseClickType
        """
        
        
        #2011/02/25 aaronlai    LButtomDown与LButtonUp之间等待0.1秒
        #2011/12/28 benjamin    优化单击和双击逻辑
        win32api.SetCursorPos((x,y))
        win32api.mouse_event(_mouse_msg[flag][0] | _mouse_msg[flag][1],0,0,0,0)
        if clicktype != MouseClickType.SingleClick:
            time.sleep(0.1)
            win32api.mouse_event(_mouse_msg[flag][0] | _mouse_msg[flag][1],0,0,0,0)
    
    @staticmethod
    def _clickSlowly(x,y,flag=MouseFlag.LeftButton, interval=0.1):
        """模拟鼠标缓慢点击，在鼠标键按下和释放之间存在一个interval的时间间隔
        """
        #2011/03/04 aaronlai    created
        win32api.SetCursorPos((x,y))
        win32api.mouse_event(_mouse_msg[flag][0],0,0,0,0)
        if interval:
            time.sleep(interval)
        win32api.mouse_event(_mouse_msg[flag][1],0,0,0,0)
        
    @staticmethod
    def sendClick(hwnd, x, y, flag=MouseFlag.LeftButton, 
                  clicktype=MouseClickType.SingleClick):
        """在目标窗口通过SendMessage方式产生鼠标点击的动作
        
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
        """
        #11/02/16 allenpan    创建
        
#        sleep_time = (win32gui.GetDoubleClickTime() / 1000.0 + 0.05) -  (time.time() - Mouse._last_click_time)
#        if sleep_time > 0 :
#            time.sleep(sleep_time)
        keystate = 0
        if win32api.GetAsyncKeyState(win32con.VK_CONTROL) & 0x8000 != 0:
            keystate = keystate | win32con.MK_CONTROL
        if win32api.GetAsyncKeyState(win32con.VK_SHIFT) & 0x8000 != 0:
            keystate = keystate | win32con.MK_SHIFT
        win32api.SetCursorPos((x,y))
        #2012/05/11 aaronlai    增加sleep 0.2秒，用于解决qplusapi测试的点击无效的问题，临时解决方案
        #问题查明，SetCursorPos以Post Message发送WM_MOUSEMOVE消息给目标窗口，
        #而WM_LBUTTONDOWN等消息是以Send Message方式被发送给目标窗口，因此，WM_LBUTTONDOWN等消息可能会比
        #WM_MOUSEMOVE消息优先被目标窗口收到并处理。这种情况下，会产生问题。QPlusAPI冒烟测试中出现此类情况。
        #比较好的方案是需要像gf的postClick那样加入同步，实现代码在Qplus3.7。
        time.sleep(0.2)
        c_x, c_y = win32gui.ScreenToClient(hwnd, (x, y))
        if clicktype == MouseClickType.SingleClick:
            try:
                win32gui.SendMessageTimeout(hwnd, _mouse_msg_param[flag][0], _mouse_msg_param[flag][2] | keystate, (c_y << 16) | c_x, 0, 1000)
            except win32gui.error as e:
                if e[0] == 1400: #无效窗口句柄，有些窗口post第一个消息后就会消失
                    pass
                elif e[0] == 1460: #timeout
                    win32gui.SendMessageTimeout(hwnd, win32con.WM_NULL, 0, 0, 0, 30000) #发送NULL确认上个消息已处理
                else:
                    raise e
            try:
                win32gui.SendMessageTimeout(hwnd, _mouse_msg_param[flag][1], 0 | keystate, (c_y << 16) | (c_x) , 0, 1000)
            except win32gui.error as e:
                if e[0] == 1400: #无效窗口句柄，有些窗口post第一个消息后就会消失
                    pass
                elif e[0] == 1460:#timeout
                    win32gui.SendMessageTimeout(hwnd, win32con.WM_NULL, 0, 0, 0, 30000)#发送NULL确认上个消息已处理
                else:
                    raise e 
        else:
            win32gui.SendMessage(hwnd, _mouse_msg_param[flag][0], _mouse_msg_param[flag][2] | keystate, (c_y << 16) | c_x)
            win32gui.SendMessage(hwnd, _mouse_msg_param[flag][1], 0 | keystate, (c_y << 16) | (c_x) )
#            time.sleep(0.1)
            win32gui.SendMessage(hwnd, _mouse_msg_param[flag][3], _mouse_msg_param[flag][2] | keystate, (c_y << 16) | c_x)
            win32gui.SendMessage(hwnd, _mouse_msg_param[flag][1], 0 | keystate, (c_y << 16) | (c_x) )
#        Mouse._last_click_time = time.time()
        
    @staticmethod
    def postClick(hwnd, x, y, flag=MouseFlag.LeftButton, 
                  clicktype=MouseClickType.SingleClick):
        """在目标窗口通过PostMessage的方式产生鼠标点击的动作
        
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
        """
        #11/02/16 allenpan    截获无效窗口句柄错误
        #2011/02/25 aaronlai    LButtomDown与LButtonUp之间等待0.1秒
        #11/03/09 dadalin    保证与上次鼠标操作间间隔GetDoubleClickTime()，防止短间隔两次鼠标单击被GF认为鼠标双击
        #11/03/23 dadalin    增加判断CTRL和SHIFT键按下状态
        #11/03/25 allenpan    更名为postclick
        #11/11/11 allenpan    由于GF的Menu处理消息有问题，需要RButtonDown消息之前发一个NULL消息来workaround
        
        sleep_time = (win32gui.GetDoubleClickTime() / 1000.0 + 0.05) -  (time.time() - Mouse._last_click_time)
        if sleep_time > 0 :
            time.sleep(sleep_time)
        keystate = 0
        if win32api.GetAsyncKeyState(win32con.VK_CONTROL) & 0x8000 != 0:
            keystate = keystate | win32con.MK_CONTROL
        if win32api.GetAsyncKeyState(win32con.VK_SHIFT) & 0x8000 != 0:
            keystate = keystate | win32con.MK_SHIFT
        win32api.SetCursorPos((x,y))
        c_x, c_y = win32gui.ScreenToClient(hwnd, (x, y))
        if clicktype == MouseClickType.SingleClick:
            try:
                win32gui.PostMessage(hwnd, win32con.WM_NULL, 0 , 0) #by allenpan
                win32gui.PostMessage(hwnd, _mouse_msg_param[flag][0], _mouse_msg_param[flag][2] | keystate, (c_y << 16) | c_x)
                win32gui.PostMessage(hwnd, _mouse_msg_param[flag][1], 0 | keystate, (c_y << 16) | (c_x) )
            except win32gui.error as e:
                if e[0] == 1400: #无效窗口句柄，有些窗口post第一个消息后就会消失
                    pass
                else:
                    raise e
        else:
            win32gui.PostMessage(hwnd, _mouse_msg_param[flag][0], _mouse_msg_param[flag][2] | keystate, (c_y << 16) | c_x)
            win32gui.PostMessage(hwnd, _mouse_msg_param[flag][1], 0 | keystate, (c_y << 16) | (c_x) )
            time.sleep(0.1)
            win32gui.PostMessage(hwnd, _mouse_msg_param[flag][3], _mouse_msg_param[flag][2] | keystate, (c_y << 16) | c_x)
            win32gui.PostMessage(hwnd, _mouse_msg_param[flag][1], 0 | keystate, (c_y << 16) | (c_x) )
        Mouse._last_click_time = time.time()
        
        
#    @staticmethod
#    def _sendClickSlowly(hwnd, x, y, flag=MouseFlag.LeftButton, interval=0.1):
#        """在目标窗口通过发消息的方式产生鼠标点击的动作，
#                             但在鼠标键按下和释放之间存在一个interval的时间间隔
#        """
#        #2011/03/04 aaronlai    created
#        win32api.SetCursorPos((x,y))
#        c_x, c_y = win32gui.ScreenToClient(hwnd, (x, y))
#        win32gui.SendMessage(hwnd, win32con.WM_NCHITTEST, 0, (c_y << 16) | c_x)
#        try:
#            win32gui.PostMessage(hwnd, _mouse_msg_param[flag][0], _mouse_msg_param[flag][2], (c_y << 16) | c_x)
#            if interval:
#                time.sleep(interval)
#            win32gui.PostMessage(hwnd, _mouse_msg_param[flag][1], 0, (c_y << 16) | (c_x) )
#        except win32gui.error as e:
#            if e[0] == 1400: #无效窗口句柄，有些窗口post第一个消息后就会消失
#                pass
#            else:
#                raise e
            
    @staticmethod
    def sendNCClick(hwnd, x, y, flag=MouseFlag.LeftButton, 
                  clicktype=MouseClickType.SingleClick):
        """在目标窗口的Non-Client区域通过发消息的方式产生鼠标点击的动作
        
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
        """
        win32api.SetCursorPos((x,y))
        c_x, c_y = win32gui.ScreenToClient(hwnd, (x, y))
        uHitTestResult = win32gui.SendMessage(hwnd, win32con.WM_NCHITTEST, 0, (c_y << 16) | c_x)
        if clicktype == MouseClickType.SingleClick:
            win32gui.PostMessage(hwnd, _mouse_ncmsg_param[flag][0], uHitTestResult, (c_y << 16) | c_x)
            win32gui.PostMessage(hwnd, _mouse_msg_param[flag][1], 0, (c_y << 16) | (c_x) )
        else:
            win32gui.PostMessage(hwnd, _mouse_ncmsg_param[flag][0], uHitTestResult, (c_y << 16) | c_x)
            win32gui.PostMessage(hwnd, _mouse_ncmsg_param[flag][1], 0, (c_y << 16) | (c_x) )
            time.sleep(0.1)
            win32gui.PostMessage(hwnd, _mouse_ncmsg_param[flag][3], uHitTestResult, (c_y << 16) | c_x)
            win32gui.PostMessage(hwnd, _mouse_ncmsg_param[flag][1], 0, (c_y << 16) | (c_x) )
            
    @staticmethod
    def drag(fromX, fromY, toX, toY, flag=MouseFlag.LeftButton, intervaltime=1):
        """鼠标从(fromX, fromX)拖拽到(toX, toY)
        
        :param fromX: 屏幕x坐标
        :type fromX: 整数  
        :param fromY: 屏幕y坐标
        :type fromY: 整数
        :param toX: 屏幕x坐标
        :type toX: 整数  
        :param toY: 屏幕y坐标
        :type toY: 整数
        :param flag: 鼠标键类型 
        :type flag: 枚举类型, MouseFlag.LeftButton|MouseFlag.MiddleButton|MouseFlag.RightButton
        """
        #2011/05/04 aaronlai    修改实现
        win32api.SetCursorPos((fromX,fromY))
        time.sleep(0.1)
        win32api.mouse_event(_mouse_msg[flag][0],0,0,0,0)
        time.sleep(intervaltime)
        win32api.SetCursorPos((toX,toY))
        time.sleep(0.1)
        win32api.mouse_event(_mouse_msg[flag][1],0,0,0,0)
    
    @staticmethod
    def press(x, y, flag=MouseFlag.LeftButton):
        """在某个位置按下鼠标键
        
        :param x: 屏幕x坐标
        :type x: 整数  
        :param y: 屏幕y坐标
        :type y: 整数
        :param flag: 鼠标键类型 
        :type flag: 枚举类型, MouseFlag.LeftButton|MouseFlag.MiddleButton|MouseFlag.RightButton
        """ 
        #2011/04/20 aaronlai    创建
        #2011/05/04 aaronlai    修改实现
        win32api.SetCursorPos((x,y))
        time.sleep(0.1)
        win32api.mouse_event(_mouse_msg[flag][0],0,0,0,0)
        
    @staticmethod
    def release(x, y, flag=MouseFlag.LeftButton):
        """在某个位置释放鼠标键，与press配对使用
        
        :param x: 屏幕x坐标
        :type x: 整数  
        :param y: 屏幕y坐标
        :type y: 整数
        :param flag: 鼠标键类型 
        :type flag: 枚举类型, MouseFlag.LeftButton|MouseFlag.MiddleButton|MouseFlag.RightButton
        """ 
        #2011/04/20 aaronlai    创建
        win32api.SetCursorPos((x,y))
        time.sleep(0.1)
        win32api.mouse_event(_mouse_msg[flag][1],0,0,0,0)
        
    @staticmethod
    def postMove(hwnd, toX, toY):
        #2011/04/13 aaronlai    创建
        #2012/04/12 aaronlai    去掉下划线，改为共有方法
        win32api.SetCursorPos((toX,toY))
        c_x, c_y = win32gui.ScreenToClient(hwnd, (toX, toY))
        keystate = 0
        if win32api.GetAsyncKeyState(win32con.VK_CONTROL) & 0x8000 != 0:
            keystate = keystate | win32con.MK_CONTROL
        if win32api.GetAsyncKeyState(win32con.VK_SHIFT) & 0x8000 != 0:
            keystate = keystate | win32con.MK_SHIFT
        win32gui.PostMessage(hwnd, win32con.WM_MOUSEMOVE, keystate, (c_y << 16) | c_x)
        
    @staticmethod
    def sendMove(hwnd, toX, toY):
        #2012/04/12 aaronlai    创建
        win32api.SetCursorPos((toX,toY))
        c_x, c_y = win32gui.ScreenToClient(hwnd, (toX, toY))
        keystate = 0
        if win32api.GetAsyncKeyState(win32con.VK_CONTROL) & 0x8000 != 0:
            keystate = keystate | win32con.MK_CONTROL
        if win32api.GetAsyncKeyState(win32con.VK_SHIFT) & 0x8000 != 0:
            keystate = keystate | win32con.MK_SHIFT
        win32gui.SendMessage(hwnd, win32con.WM_MOUSEMOVE, keystate, (c_y << 16) | c_x)
    
    @staticmethod
    def move(toX, toY):
        """鼠标移动到(tox,toy)
        
        :param x: 屏幕x坐标
        :type x: int  
        :param y: 屏幕y坐标
        :type y: int
        """
        win32api.SetCursorPos((toX,toY))
    
    @staticmethod
    def getPosition():
        '''当前Mouse的位置
        '''
        x,y = win32api.GetCursorPos()
        return (x,y)
        
    @staticmethod
    def getCursorType():
        """返回当前鼠标图标类型
        
        :rtype: MouseCursorType
        """
        hcursor = win32gui.GetCursorInfo()[1]
        for key, flag in _cursor_flags.items():
            if win32gui.LoadCursor(0, flag) == hcursor:
                return key
        return None 
                    
    @staticmethod
    def scroll(bForward=False):
        '''鼠标滚动
        bForward: True则向前滚动，False则向后滚动。默认是False。
        '''
        if(bForward==True):
            win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL,0,0,120)
        else:
            win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL,0,0,-120)

                                                              
if __name__ == "__main__":
    pass