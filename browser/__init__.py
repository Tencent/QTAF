## -*- coding: utf-8 -*-
'''浏览器类库
'''
#10/12/02 aaronlai    created
#10/12/08 aaronlai    添加BrowserHelper等类
#11/01/04 aaronlai    更新BrowserHelper.newBrowserByClick方法
#11/01/07 aaronlai    更新BrowserHelper.newBrowserByClick方法
#11/01/09 allenpan    删除此模块所有code
#11/01/10 allenpan    添加获取默认浏览器

class EnumBrowserType(object):
    IE, TT, FireFox = "iexplore", "TTraveler", "firefox"

def _get_default_browser1():
    '''获取xp下的默认浏览器
    '''
    import win32con, win32api
    hkey = win32con.HKEY_CLASSES_ROOT
    subkey = r'http\shell\open\command'
    hkey = win32api.RegOpenKey(hkey, subkey)
    brwcmd = win32api.RegQueryValue(hkey, None)
    win32api.RegCloseKey(hkey)
    if -1 != brwcmd.lower().find(EnumBrowserType.IE):
        return EnumBrowserType.IE
    if -1 != brwcmd.find(EnumBrowserType.TT):
        return EnumBrowserType.TT
    
    if -1 != brwcmd.find(EnumBrowserType.FireFox):
        return EnumBrowserType.FireFox
    
    raise RuntimeError('未支持浏览器:%s' % brwcmd)#Exception('浏览器:%s，还未支持' % brwcmd)

def _get_default_browser2():
    '''获取vista或以上的默认浏览器
    '''
    import win32con, win32api, pywintypes
    hkey = win32con.HKEY_CURRENT_USER
    subkey = r'Software\Microsoft\Windows\Shell\Associations\UrlAssociations\http\UserChoice'
    win32api.RegOpenCurrentUser()
    brwchoice = 'IE.HTTP'
    try:
        hkey = win32api.RegOpenKey(hkey, subkey)
        brwchoice = win32api.RegQueryValueEx(hkey, 'ProgId')[0]
        win32api.RegCloseKey(hkey)
    except pywintypes.error: #[allenpan]subkey没有设过，因此默认是IE
        return EnumBrowserType.IE
    brwmap = {'FirefoxURL': EnumBrowserType.FireFox, 
              'IE.HTTP': EnumBrowserType.IE, 
              'TTraveler.HTTP':EnumBrowserType.TT}
    if brwchoice not in brwmap.keys():
        raise RuntimeError("未支持浏览器%s" % brwchoice)#Exception("浏览器%s还未支持" % brwchoice)
    return brwmap[brwchoice]
    
def get_default_browser():
    '''获取默认浏览器类型
    
    :rtype: EnumBrowserType
    '''
    import sys
    winver = sys.getwindowsversion()
    if winver[0]<=5 : #xp or below
        return _get_default_browser1()
    elif winver[0] >=6: # vista or above
        return _get_default_browser2()

if __name__ == '__main__':
    pass
