# -*- coding: utf-8 -*-
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
#10/11/18 pear    created
#10/12/21 pear    增加PROCESSENTRY32结构
#13/02/28 olive      增加MODULEENTRY32
import ctypes
import win32con
import os
    
class RECT(ctypes.Structure):
    """The RECT structure defines the coordinates of the upper-left and lower-right corners of a rectangle
    """
    _fields_ = [
        ('left', ctypes.c_long),
        ('top', ctypes.c_long),
        ('right', ctypes.c_long),
        ('bottom', ctypes.c_long)]
    
class TBBUTTON(ctypes.Structure):
    """Contains information about a button in a system's traynotifybar."""
    #2013/06/20 pear    修改TBButton的结构，会根据操作系统位数修改
    _fields_ = [
        ('iBitmap', ctypes.c_int),
        ('idCommand', ctypes.c_int),
        ('fsState', ctypes.c_ubyte),
        ('fsStyle', ctypes.c_ubyte),
        ('bReserved', ctypes.c_ubyte*(6 if 'PROGRAMFILES(X86)' in os.environ else 2)),
        ('dwData', ctypes.c_ulong),
        ('iString', ctypes.c_int)]
       
class TRAYDATA(ctypes.Structure):
    """for description"""
    _fields_ = [
        ('hwnd', ctypes.c_long),
        ('uID', ctypes.c_uint),
        ('uCallbackMessage', ctypes.c_uint),
        ('Reserved', ctypes.c_ulong * 2),
        ('hIcon', ctypes.c_long)]
    
class PROCESSENTRY32(ctypes.Structure):
    """
    
    :desc: Describes an entry from a list that enumerates the processes residing in the system address space when a snapshot was taken.
    """
    _fields_ = [
        ('dwSize', ctypes.c_ulong),
        ('cntUsage', ctypes.c_ulong),
        ('th32ProcessID', ctypes.c_ulong),
        ('th32DefaultHeapID', ctypes.c_ulong),
        ('th32ModuleID', ctypes.c_ulong),
        ('cntThreads', ctypes.c_ulong),
        ('th32ParentProcessID', ctypes.c_ulong),
        ('pcPriClassBase', ctypes.c_long),
        ('dwFlags', ctypes.c_ulong),
        ('szExeFile', ctypes.c_char * win32con.MAX_PATH),
        ('th32MemoryBase', ctypes.c_ulong),
        ('th32AccessKey', ctypes.c_ulong)]
    
class APPBARDATA(ctypes.Structure):
    """App Bar Data Structure
    """
    _fields_ = [
        ('cbSize', ctypes.c_ulong),
        ('hWnd', ctypes.c_ulong),
        ('uCallbackMessage', ctypes.c_ulong),
        ('uEdge', ctypes.c_ulong),
        ('rc', RECT),
        ('lParam', ctypes.c_long)]
    
class LVITEM(ctypes.Structure):
    """
    
    :desc: Specifies or receives the attributes of a list-view item. This structure has been updated
           to support a new mask value (LVIF_INDENT) that enables item indenting. This structure supersedes the LV_ITEM structure
    """
    #2011/04/28 peach   created
    #2014/07/01 pear    补齐结构
    _fields_ = [
        ('mask', ctypes.c_uint),
        ('iItem', ctypes.c_int),
        ('iSubItem', ctypes.c_int),
        ('state', ctypes.c_uint),
        ('stateMask', ctypes.c_uint),
        ('pszText', ctypes.c_char_p),
        ('cchTextMax', ctypes.c_int),
        ('iImage', ctypes.c_int),
        ('lParam', ctypes.c_char_p),
        ('iIndent', ctypes.c_int),
        ('iGroupId', ctypes.c_int),
        ('cColumns', ctypes.c_int),
        ('puColumns', ctypes.c_uint)]
    
class LVITEM64(ctypes.Structure):
    """
    
    :desc: Specifies or receives the attributes of a list-view item. This structure has been updated
           to support a new mask value (LVIF_INDENT) that enables item indenting. This structure supersedes the LV_ITEM structure
    """
    #2014/07/01 pear    created
    _fields_ = [
        ('mask', ctypes.c_uint),
        ('iItem', ctypes.c_int),
        ('iSubItem', ctypes.c_int),
        ('state', ctypes.c_uint),
        ('stateMask', ctypes.c_uint),
        ('iPlaceholder11', ctypes.c_int),
        ('pszText', ctypes.c_char_p),
        ('iPlaceholder12', ctypes.c_int),
        ('cchTextMax', ctypes.c_int),
        ('iImage', ctypes.c_int),
        ('lParam', ctypes.c_char_p),
        ('iPlaceholder2', ctypes.c_int),
        ('iIndent', ctypes.c_int),
        ('iGroupId', ctypes.c_int),
        ('cColumns', ctypes.c_int),
        ('iPlaceholder3', ctypes.c_int),
        ('puColumns', ctypes.c_uint),
        ('iPlaceholder4', ctypes.c_int),
        ]
    
class TVITEM(ctypes.Structure):
    """
    """
    #2011/05/23 peach   created
    _fields_ = [
        ('mask', ctypes.c_uint),
        ('hItem', ctypes.c_long),
        ('state', ctypes.c_uint),
        ('stateMask', ctypes.c_uint),
        ('pszText', ctypes.c_char_p),
        ('cchTextMax', ctypes.c_int),
        ('iImage', ctypes.c_int),
        ('iSelectedImage', ctypes.c_int),
        ('cChildren', ctypes.c_int),
        ('lParam', ctypes.c_char_p)]
    
class BITMAPINFOHEADER(ctypes.Structure):
    """BITMAP Info Header
    """
    #2012/01/10 pear created
    _fields_ = [
        ('biSize', ctypes.c_uint32),
        ('biWidth', ctypes.c_long),
        ('biHeight', ctypes.c_long),
        ('biPlanes', ctypes.c_uint16),
        ('biBitCount', ctypes.c_uint16),
        ('biCompression', ctypes.c_uint32),
        ('biSizeImage', ctypes.c_uint32),
        ('biXPelsPerMeter', ctypes.c_long),
        ('biYPelsPerMeter', ctypes.c_long),
        ('biClrUsed', ctypes.c_uint32),
        ('biClrImportant', ctypes.c_uint32)
                ]

class RGBTRIPLE(ctypes.Structure):
    """RGB Define
    """
    #2012/01/10 pear created
    _fields_ = [
        ('rgbBlue', ctypes.c_byte),
        ('rgbGreen', ctypes.c_byte),
        ('rgbRed', ctypes.c_byte),
        ('rgbReserved', ctypes.c_byte),
                ]
        
class BITMAPINFO(ctypes.Structure):
    """BITMAP Info
    """
    #2012/01/10 pear created
    _fields_ = [
        ('bmiHeader', BITMAPINFOHEADER),
        ('bmciColors', RGBTRIPLE * 1)]
  
class BITMAP(ctypes.Structure):
    """BITMAP
    """
    #2012/01/10 pear created
    _fields_ = [
        ('bmType', ctypes.c_long),
        ('bmWidth', ctypes.c_long),
        ('bmHeight', ctypes.c_long),
        ('bmWidthBytes', ctypes.c_long),
        ('bmPlanes', ctypes.c_uint16),
        ('bmBitsPixel', ctypes.c_uint16),
        ('bmBits', ctypes.c_void_p)]
      
class DIBSECTION(ctypes.Structure):
    """DIB Section
    """
    #2012/01/10 pear created
    _fields_ = [
        ('dsBm', BITMAP),
        ('dsBmih', BITMAPINFOHEADER),
        ('dsBitfields', ctypes.c_uint32 * 3),
        ('dshSection', ctypes.c_void_p),
        ('dsOffset', ctypes.c_uint32)]
    
class BITMAPFILEHEADER(ctypes.Structure):
    """BITMAP File Header
    """
    #2012/01/10 pear created
    _fields_ = [
        ('bfType', ctypes.c_uint16),
        ('bfSize', ctypes.c_uint32),
        ('bfReserved1', ctypes.c_uint16),
        ('bfReserved2', ctypes.c_uint16),
        ('bfOffBits', ctypes.c_uint32)
                ]
    
class MODULEENTRY32(ctypes.Structure):
    """This structure describes an entry from a list that enumerates 
    the modules used by a specified process.
    """
    _fields_ = [
        ("dwSize",ctypes.c_long),
        ("th32ModuleID", ctypes.c_long),
        ("th32ProcessID", ctypes.c_long),
        ("GlblcntUsage", ctypes.c_long),
        ("ProccntUsage", ctypes.c_long),
        ("modBaseAddr", ctypes.c_long),
        ("modBaseSize", ctypes.c_long),
        ("szModule", ctypes.c_char*win32con.MAX_PATH),
        ("szExePath", ctypes.c_char*win32con.MAX_PATH),
        ("dwFlags", ctypes.c_long),
         ]

class THREADENTRY32(ctypes.Structure):
    """
    This structure describes an entry from a list that enumerates the threads executing in the system when a snapshot was taken. 
    """
    _fields_ = [
        ("dwSize", ctypes.c_ulong),
        ("cntUsage", ctypes.c_ulong),
        ("th32ThreadID", ctypes.c_ulong),
        ("th32OwnerProcessID", ctypes.c_ulong),
        ("tpBasePri", ctypes.c_long),
        ("tpDeltaPri", ctypes.c_long),
        ("dwFlags", ctypes.c_ulong)
    ]
