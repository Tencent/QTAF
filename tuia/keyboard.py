# -*- coding: utf-8 -*-
'''键盘输入模块
'''
#10/11/04 allenpan    重构整个模块并加入窗口消息方式输入键盘消息
#11/01/07 allenpan    修改Keyboard.inputKeys和postKeys的编码问题
#11/01/27 aaronlai    增加1个虚键'APPS'
#11/02/12 aaronlai    增加1个虚键'CAPS'
#11/06/09 rayechen    修改Keyborad类支持选择使用某种Key类
#14/03/20 pillarzou    增加一个MODIFIER，win键

import time
import ctypes
import win32con
import win32api

_SHIFT = {'~' : '`', '!' : '1', '@' : '2','#' : '3', '$' : '4','%' : '5','^' : '6','&' : '7','*' : '8','(' : '9',')' : '0','_' : '-','+' : '=',
    '{' : '[','}' : ']','|' : '\\',':' : ';','"' : "'",'<' : ',','>' : '.','?' : '/'}

_MODIFIERS = [
    win32con.VK_SHIFT, 
    win32con.VK_CONTROL, 
    win32con.VK_MENU,
    win32con.VK_LWIN,
    win32con.VK_RWIN,
]

_MODIFIER_KEY_MAP = {
    '+': win32con.VK_SHIFT,
    '^': win32con.VK_CONTROL,
    '%': win32con.VK_MENU,                     
}

#ESCAPEDS= '+%^{}'

#2011/05/10 aaronlai    加入Win键
#2011/06/20 aaronlai    加入截屏键
_CODES = {
    'F1':112, 'F2':113, 'F3':114, 'F4':115, 'F5':116, 'F6':117, 
    'F7':118, 'F8':119, 'F9':120, 'F10':121, 'F11':122, 'F12':123,
    'BKSP':8, 'TAB':9, 'ENTER':13, 'ESC':27, 'END':35, 'HOME':36,'INSERT':45, 'DEL':46, 
    'SPACE':32,'PGUP':33,'PGDN':34,'LEFT':37,'UP':38,'RIGHT':39,'DOWN':40,'PRINT':44,
    'SHIFT':16, 'CTRL':17, 'MENU':18, 'ALT':18,
    'APPS':93, 'CAPS':20, 'WIN':91, 'LWIN': 91, 'RWIN':92,
    }

def _scan2vkey(scan):
    #2011/07/28 aaronlai    VkKeyScanW接受的是tchar类型，需把scan转成tchar类型
    return 0xff & ctypes.windll.user32.VkKeyScanW(ctypes.c_wchar("%c" % scan))
    #return 0xff & ctypes.windll.user32.VkKeyScanW(scan)
        
class _KeyboardEvent(object):
        KEYEVENTF_EXTENDEDKEY = 1
        KEYEVENTF_KEYUP  = 2
        KEYEVENTF_UNICODE     = 4
        KEYEVENTF_SCANCODE    = 8
        

class _MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ('dx', ctypes.c_long),
        ('dy', ctypes.c_long),
        ('mouseData', ctypes.c_ulong),
        ('dwFlags', ctypes.c_ulong),
        ('time', ctypes.c_ulong),
        ('dwExtraInfo', ctypes.c_ulong),
    ]

class _HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ('uMsg', ctypes.c_ulong),
        ('wParamL', ctypes.c_ushort),
        ('wParamH', ctypes.c_ushort),
    ]

class _KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ('wVk', ctypes.c_ushort),
        ('wScan', ctypes.c_ushort),
        ('dwFlags', ctypes.c_ulong),
        ('time', ctypes.c_ulong),
        ('dwExtraInfo', ctypes.c_ulong),
    ]

class _UNION_INPUT_STRUCTS(ctypes.Union):
    "The C Union type representing a single Event of any type"
    _fields_ = [
        ('mi', _MOUSEINPUT),
        ('ki', _KEYBDINPUT),
        ('hi', _HARDWAREINPUT),
    ]

class _INPUT(ctypes.Structure):
    _fields_ = [
        ('type', ctypes.c_ulong),
        ('_', _UNION_INPUT_STRUCTS),
    ]



class KeyInputError(Exception):
    '''键盘输入错误
    '''
    pass

        
class Key(object):
    '''一个按键
    '''

    def __init__(self, key):
        '''Constructor
        
        :type key: number or charactor
        :param key: 按键 
        '''
        self._flag = 0
        self._modifiers = []
        if isinstance(key, basestring):
            self._scan = ord(key)
            if self._scan < 256: #ASCII code
                self._vk = _scan2vkey(self._scan)
                if key.isupper() or key in _SHIFT: #按下shift键
                    self._modifiers.append(Key(_MODIFIER_KEY_MAP['+']))
            else: #unicode
                self._vk = 0
                self._flag |= _KeyboardEvent.KEYEVENTF_UNICODE
        elif isinstance(key, int): #virtual Key
            self._vk = key
            self._scan = ctypes.windll.user32.MapVirtualKeyW(self._vk, 0)
            if self._isExtendedKey(self._vk):
                self._flag |= _KeyboardEvent.KEYEVENTF_EXTENDEDKEY
        else:
            raise KeyInputError('Key is not a number or string')
        
        # 若是以下虚拟键则需要同步
        # 暂只对最主要的SHIFT、CTRL、ALT键进行同步
        self._SyncVKeys = [win32con.VK_SHIFT, win32con.VK_LSHIFT, win32con.VK_RSHIFT,
         win32con.VK_CONTROL, win32con.VK_LCONTROL, win32con.VK_RCONTROL,
         win32con.VK_MENU, win32con.VK_LMENU, win32con.VK_RMENU]
    
    def appendModifierKey(self, key):
        '''Modifier Key comes with the key
        
        :type key: Key
        :param key: Ctrl, Shift or Atl Key 
        '''
        self._modifiers.append(key)

    def _isExtendedKey(self, vkey):
        if ((vkey >= 33 and vkey <= 46) or 
            (vkey >= 91 and vkey <= 93) ):
            return True
        else:
            return False
        
    def _inputKey(self, up):
        inp = _INPUT()
        inp.type = 1
        inp._.ki.wVk = self._vk
        inp._.ki.wScan = self._scan
        inp._.ki.dwFlags |= self._flag
        if up:
            inp._.ki.dwFlags |= _KeyboardEvent.KEYEVENTF_KEYUP
        ctypes.windll.user32.SendInput(1,ctypes.byref(inp),ctypes.sizeof(_INPUT))
        
    
    def inputKey(self):
        '''键盘模拟输入按键
        '''
        for mkey in self._modifiers:
            mkey._inputKey(up=False)
        
        self._inputKey(up=False)
        self._inputKey(up=True)
        for mkey in self._modifiers:
            mkey._inputKey(up=True)
            
    def _postKey(self, hwnd, up):
        """给某个窗口发送按钮"""
        #2011/04/28 aaronlai    创建
        if up:
            ctypes.windll.user32.PostMessageW(hwnd, win32con.WM_KEYUP, self._vk, self._scan <<16 | 0xc0000001)
        else:
            ctypes.windll.user32.PostMessageW(hwnd, win32con.WM_KEYDOWN, self._vk, self._scan<<16 | 1)
        time.sleep(0.01) #必须加，否则有些控件响应不了，会产生问题
        
    def postKey(self, hwnd):
        '''将按键消息发到hwnd
        '''
        #2011/03/17 aaronlai    修改keydown和keyup的发送顺序
        #2011/04/28 aaronlai    修改实现
        #2014/04/14 aaronlai    bug fix：Keyboard.postKey(hwnd, '3:20')，实际结果为:"3;20"
        for mkey in self._modifiers:
            mkey._inputKey(up=False)
            time.sleep(0.01) #必须加，否则下面实际寄送的键盘按键消息可能比这个消息更快到达目标窗口

        if self._scan < 256:
            self._postKey(hwnd, up=False)
            self._postKey(hwnd, up=True)
        else:
            ctypes.windll.user32.PostMessageW(hwnd, win32con.WM_CHAR, self._scan, 1)
        
        for mkey in self._modifiers:
            mkey._inputKey(up=True)
    
    def _isPressed(self):
        """该键是否被按下
        """
        if (win32api.GetAsyncKeyState(self._vk) & 0x8000) == 0:
            return False
        else:
            return True
        
    def _isToggled(self):
        """该键是否被开启，如CAps Lock或Num Lock等
        """
        if(win32api.GetKeyState(self._vk) & 1):
            return True
        else:
            return False
    
class Keyboard(object):
    '''键盘输入类，实现了两种键盘输入方式。
    
    一类方法使用模拟键盘输入的方式。
    另一类方法使用Windows消息的机制将字符串直接发送的窗口。
    
    键盘输入类支持以下字符的输入。
    1、特殊字符：^, +, %,  {, }
        '^'表示Control键，同'{CTRL}'。'+'表示Shift键，同'{SHIFT}'。'%'表示Alt键，同'{ALT}'。
        '^', '+', '%'可以单独或同时使用，如'^a'表示CTRL+a，’^%a'表示CTRL+ALT+a。
        {}： 大括号用来输入特殊字符本身和虚键，如‘{+}’输入加号，'{F1}'输入F1虚键，'{}}'表示输入'}'字符。 
    2、ASCII字符：除了特殊字符需要｛｝来转义，其他ASCII码字符直接输入，
    3、Unicode字符：直接输入，如"测试"。
    4、虚键：
        {F1}, {F2},...{F12}
        {Tab},{CAPS},{ESC},{BKSP},{HOME},{INSERT},{DEL},{END},{ENTER}
        {PGUP},{PGDN},{LEFT},{RIGHT},{UP},{DOWN},{CTRL},{SHIFT},{ALT},{APPS}..
           注意：当使用联合键时，注意此类的问题,inputKeys('^W')和inputKeys('%w')，字母'w'的大小写产生的效果可能不一样
    '''
    #11/06/09 rayechen    新增selectKeyClass函数并修改_parse_keys函数以支持选择使用不同的Key类
    #2012/05/09 aaronlai    注释中增加注意事项
    _keyclass = Key
    _pressedkey = None
    
    @staticmethod
    def selectKeyClass(newkeyclass):
        oldkeyclass = Keyboard._keyclass
        Keyboard._keyclass = newkeyclass
        return oldkeyclass
    
    @staticmethod
    def _parse_keys(keystring):        
        keys = []
        modifiers = []
        index = 0
        while index < len(keystring):
            c = keystring[index]
            index += 1
                
            # Escape or named key
            if c == "{":
                end_pos = keystring.find("}", index)
                if end_pos == -1:
                    raise KeyInputError('`}` not found')
                elif end_pos == index and keystring[end_pos+1] == '}': #{}}
                        index +=2
                        code = '}'
                else: 
                    code = keystring[index:end_pos]
                    index = end_pos + 1
                    
                if code in _CODES.keys():
                    key = _CODES[code]
                elif len(code) == 1:
                    key = code
                else:
                    raise KeyInputError("Code '%s' is not supported" % code)
            
            # unmatched "}"
            elif c == '}':
                raise KeyInputError('`}` should be preceeded by `{`')
            
            elif c in _MODIFIER_KEY_MAP.keys():
                key = _MODIFIER_KEY_MAP[c]
       
            # so it is a normal character
            else:
                key = c
            if key in _MODIFIERS :
                modifiers.append(key)
            else:
                akey = Keyboard._keyclass(key)
                for mkey in modifiers:
                    akey.appendModifierKey(Keyboard._keyclass(mkey))
                modifiers = []
                keys.append(akey)
        for akey in modifiers:
            keys.append(Keyboard._keyclass(akey))
            
        return keys
    
    @staticmethod
    def inputKeys(keys, interval=0.01):
        '''模拟键盘输入字符串
        
        :type keys: utf-8 str or unicode
        :param keys: 键盘输入字符串,可输入组合键，如"{CTRL}{MENU}a"
        :type interval: number
        :param interval: 输入的字符和字符之间的暂停间隔。
        '''

        if not isinstance(keys, unicode):
            keys = keys.decode('utf-8')
        keys = Keyboard._parse_keys(keys)
    
        for k in keys:
            k.inputKey()
            time.sleep(interval)
            
   
    @staticmethod
    def postKeys(hwnd, keys, interval=0.01):
        '''将字符串以窗口消息的方式发送到指定win32窗口。
        
        :type hwnd: number
        :param hwnd: windows窗口句柄 
        :type keys: utf8 str 或者 unicode
        :param keys: 键盘输入字符串
        :type interval: number
        :param interval: 输入的字符和字符之间的暂停间隔。
        '''
        if not isinstance(keys, unicode):
            keys = keys.decode('utf-8')
        keys = Keyboard._parse_keys(keys)
    
        for k in keys:
            k.postKey(hwnd)
            time.sleep(interval)
            
    @staticmethod
    def pressKey(key):
        """按下某个键
        """
        #2011/02/23 aaronlai    created
        #2014/03/20 pillarzou   modify
        if Keyboard._pressedkey:
            raise ValueError("尚有按键未释放,请先对按键进行释放,未释放的按键为: %s"%Keyboard._pressedkey)
            
        if not isinstance(key, unicode):
            key = key.decode('utf-8')
        keys = Keyboard._parse_keys(key)
        if len(keys) != 1:
            raise ValueError("输入参数错误,只支持输入一个键,key: %s"%key)  
        keys[0]._inputKey(up=False)
        Keyboard._pressedkey = key
                
    @staticmethod
    def releaseKey(key=None):
        """释放上一个被按下的键
        """
        #2011/02/23 aaronlai    created
        #2014/03/20 pillarzou   modify
        #后续改成不带参数的，将释放上一个按键，暂时兼容下现有的使用方式
        if not Keyboard._pressedkey:
            raise Exception("没有可释放的按键")
        
        key = Keyboard._pressedkey                
        if not isinstance(key, unicode):
            key = key.decode('utf-8')
        keys = Keyboard._parse_keys(key)
        if len(keys) != 1:
            raise ValueError("输入参数错误,只支持输入一个键,key: %s"%key)  
        keys[0]._inputKey(up=True)      
        Keyboard._pressedkey = None  
        
    @staticmethod
    def isPressed(key):
        """是否被按下
        """
        #2011/04/20 aaronlai    创建
        if not isinstance(key, unicode):
            key = key.decode('utf-8')
        keys = Keyboard._parse_keys(key)
        if len(keys) != 1:
            raise ValueError("输入参数错误,只支持输入一个键,key: %s"%key)  
        return keys[0]._isPressed()
    
    @staticmethod
    def clear():
        """释放被按下的按键
        """
        #2014/03/19 pillarzou    创建
        if Keyboard._pressedkey:
            Keyboard.releaseKey()

    @staticmethod
    def isTroggled(key):
        #2011/04/20 aaronlai    创建
        """是否开启，如Caps Lock或Num Lock等
        """
        if not isinstance(key, unicode):
            key = key.decode('utf-8')
        keys = Keyboard._parse_keys(key)
        if len(keys) != 1:
            raise ValueError("输入参数错误,只支持输入一个键,key: %s"%key)  
        return keys[0]._isToggled()
    
if __name__ == "__main__":
    pass
