# -*- coding: utf-8 -*-
'''Tuia：Tencent UI Automation

Tuia是UI engine层，封装了鼠标键盘操作，还有window，GF和html的UI操作。
'''
#2012/10/10 aaronlai    __version__是python模块较通用的用法
#2012/10/11 aaronlai    去除__version__，模块里暂不管理版本号
#2012/11/28 aaronlai    增加安全限制
#2015/10/28 eeelin      准备开源，不做安全检查

# def __isInTencentDomain():
#     """判断tuia是否在tencent域下运行
#     """
#     #2012/11/28 aaronlai    创建
#     import win32api,win32con
#     szSafeDomain = [0x74, 0x65, 0x6e, 0x63, 0x65, 0x6e, 0x74, 0x2e, 0x63, 0x6f, 0x6d]
#     dnsDomain = win32api.GetComputerNameEx(win32con.ComputerNameDnsDomain)
#     if len(szSafeDomain) == len(dnsDomain):
#         isAllMatch = True
#         cnt = len(dnsDomain)
#         for i in range(cnt):
#             c = dnsDomain[i]
#             if ord(c) != szSafeDomain[i]:
#                 isAllMatch = False
#                 break
#         return isAllMatch 
#     return False
# 
# def __hasKeyDataInRegister():
#     """当在注册表中有指定注册数据时，也认为是可信环境
#     """
#     #2012/11/28 aaronlai    创建
#     import win32api,win32con
#     #"CLSID\{2AF508C7-3D2C-4A91-81B4-21B8BC82660B}"
#     szSafetyRegKey = [
#             0x43, 0x4c, 0x53, 0x49, 0x44, 0x5c, 0x7b, 0x32, 0x41, 0x46,
#             0x35, 0x30, 0x38, 0x43, 0x37, 0x2d, 0x33, 0x44, 0x32, 0x43, 
#             0x2d, 0x34, 0x41, 0x39, 0x31, 0x2d, 0x38, 0x31, 0x42, 0x34, 
#             0x2d, 0x32, 0x31, 0x42, 0x38, 0x42, 0x43, 0x38, 0x32, 0x36, 
#             0x36, 0x30, 0x42, 0x7d, 0x00]
#     reg_path = ""
#     for c in szSafetyRegKey:
#         reg_path = reg_path + chr(c)
#     try:
#         win32api.RegOpenKeyEx(win32con.HKEY_CLASSES_ROOT, reg_path, 0, win32con.KEY_READ)
#         return True
#     except:
#         return False
#         
# def __isInSafeEnv():
#     """判读此包是否在安全环境下运行
#     @attention: 安全环境包括tencent域或者已注册安全key
#     """
#     #2012/11/28 aaronlai    创建
#     return __isInTencentDomain or __hasKeyDataInRegister()
# 
# 
# if not __isInSafeEnv():
#     raise RuntimeError("Auto Testing is stop while it runs in an unsafe environment!")
