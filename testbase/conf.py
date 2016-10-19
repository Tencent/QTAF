# -*- coding: utf-8 -*-
'''配置接口

一、配置格式
配置文件名默认为settings.py，可以通过环境变量指定用户配置文件的路径
qtaf相关配置的环境变量为：
QTAF_EXLIB_PATH: 指定exlib的路径，exlib下放置对应的qtaf、qt4s、installed_libs.txt等文件
QTAF_INSTALLED_LIBS: 指定已经安装的库的列表，以分号分隔，例如qt4s，用来代替不使用installed_libs.txt的场景
QTAF_SETTINGS_MODULE: 指定用户自定义的配置文件的路径，最后加载，会覆盖已经存在的配置

配置变量名必须符合pyton变量名规范，且统一使用大写，且不可以以"__"开头

如：
CONFIG_OPTION = True
DEBUG = True
RUNNER_THREAD_CNT = 5
BANNER = "hello"

二、使用示例：
from testbase.conf import settings
print settings.CONFIG_OPTION

注意 settings的值都是只读的，不可以修改，如果尝试修改会导致异常

三、配置优先级
配置存在2个优先级，当存在名字冲突时，使用高优先级的配置的值。优先级自低到高分别为：
1、QTAF配置                     固定为：test_proj/exlib/qtaf.egg/qtaf_settings.py
2、lib配置                      已经配置在test_proj/exlib/installed_libs.txt的包中的settings模块
3、用户自定义配置          固定为：test_proj/settings.py
'''

#2015/03/18 eeelin 新建
#2015/03/19 eeelin 简化代码结构
#2015/10/30 eeelin 支持加载lib的默认配置文件

import os
import sys
import imp
import qtaf_settings
from testbase.exlib import ExLibManager


class Settings(object):
    '''配置读取接口
    '''
    def __init__(self):
        self.__sealed = False
        self._load()
        self.__sealed = True
        
    def _load(self):
        '''加载配置
        :returns: Settings - 设置读取接口
        '''
        top_dir=ExLibManager.find_top_dir()
            
        #优先加载QTAF设置
        self._load_setting_from_module(qtaf_settings)
        
        #加载exlib中其他egg的配置
        for lib_settings in self._load_libs_settings():
            self._load_setting_from_module(lib_settings)
                
        #加载用户自定义设置 
        try:
            user_settings=os.environ.get("QTAF_SETTINGS_MODULE",None)
            if user_settings:
                parts=user_settings.split('.')
                parts_temp=parts[:]
                dir_path=None
                while parts_temp:
                    if dir_path:
                        fd,dir_path,desc=imp.find_module(parts_temp[0],[dir_path])
                    else:
                        fd,dir_path,desc=imp.find_module(parts_temp[0])
                    del parts_temp[0]
            else:
                name="settings"
                fd, dir_path, desc = imp.find_module(name, [top_dir])
            mod = imp.load_module("testbase.conf.settings", fd, dir_path, desc)
            self._load_setting_from_module(mod)
        except ImportError:
            pass
              
    def _load_setting_from_module(self, module ):
        '''从模块中加载设置
        '''
        for name in dir(module):
            if name.startswith('__'):
                continue
            if name.islower():
                continue
            setattr(self, name, getattr(module,name))
                    
    def _load_libs_settings(self):
        '''获取已安装的lib的配置文件
        '''
        mods = []
        for libname in ExLibManager().list_names():
                modname = '%s.settings' % libname
                try:
                    __import__(modname)
                except ImportError:
                    continue
                else:
                    mods.append(sys.modules[modname])
        return mods    

    def get(self, name, *default_value ):
        '''获取配置
        '''
        if len(default_value) > 1:
            raise TypeError("get expected at most 3 arguments, got %s"%(len(default_value)+2))
        if default_value:
            return getattr(self, name, default_value[0])
        else:
            return getattr(self, name)
        
    def __setattr__(self, name, value ):
        if not name.startswith('_Settings__') and self.__sealed:
            raise RuntimeError("尝试动态修改配置项\"%s\""%name)
        else:
            super(Settings,self).__setattr__(name, value)
                
    def __getattribute__(self, name):#加上这个是为了使pydev不显示红叉
        return super(Settings,self).__getattribute__(name)
           
    def __iter__(self):
        for name in dir(self):
            if not name.startswith('__') and name.isupper():
                yield name
                
settings = Settings()