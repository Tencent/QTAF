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
'''
扩展库管理（仅独立模式使用）
'''

import os
import zipfile
import shutil
import logging
import codecs
import xml.dom.minidom as dom

class ExLibManager(object):
    '''扩展库管理器
    '''
    def __init__(self, proj_root ):
        self._top_dir = proj_root
        self._installed_libs = os.path.join(self._top_dir, 'exlib', 'installed_libs.txt')
    
    def _get_egg_name(self, egg_path ):
        '''获取egg包名称
        '''
        with zipfile.ZipFile(egg_path, 'r') as egg:
            with egg.open('EGG-INFO/PKG-INFO', 'r') as fd:
                for line in fd.readlines():
                    if line.startswith('Name:'):
                        return line.split(':')[1].strip()

    def install(self, egg_path ):
        '''安装
        '''
        #获取全部的顶级package
        toplv_pkgs = []
        with zipfile.ZipFile(egg_path, 'r') as egg:
            for f in egg.filelist:
                items = f.filename.split('/')
                if len(items) == 2 and items[1].lower() == '__init__.py':
                    toplv_pkgs.append(items[0])
        
        exlib_dir = os.path.join(self._top_dir, 'exlib')
        if not os.path.isdir(exlib_dir):
            os.makedirs(exlib_dir)
        
        #移除老的包
        egg_name = self._get_egg_name(egg_path)
        egg_paths_remove = []
        if egg_name:
            for file_name in os.listdir(exlib_dir):
                if not file_name.lower().endswith('.egg'):
                    continue
                file_path = os.path.join(exlib_dir, file_name)
                if not os.path.isfile(file_path):
                    continue
                if egg_name == self._get_egg_name(file_path):
                    os.remove(file_path)
                    egg_paths_remove.append(file_path)
        
        #拷贝包
        shutil.copy(egg_path, exlib_dir)
        
        #记录到installed_libs.txt
        installed_pkgs = self.list_names()
        for pkg in toplv_pkgs[:]:
            if pkg in installed_pkgs:
                toplv_pkgs.remove(pkg)
        if toplv_pkgs:
            with open(self._installed_libs, 'a+') as fd:
                for pkg in toplv_pkgs:
                    fd.write(pkg+'\n')
                    
        self._update_pydev_conf(egg_path, egg_paths_remove)
                    
    def _update_pydev_conf(self, egg_path, egg_paths_remove):
        '''修改pydev配置
        '''
        egg_names_remove = []
        for it in egg_paths_remove:
            egg_names_remove.append(os.path.basename(it).lower())
        egg_name = os.path.basename(egg_path)
        
#         if len(egg_names_remove) == 1 and egg_names_remove[0] == egg_name:
#             return
        
        pydev_path = os.path.join(self._top_dir, '.pydevproject')
        if not os.path.isfile(pydev_path):
            logging.warn('pydev configure file not found')
            return
        doc = dom.parse(pydev_path)
        for propnode in doc.getElementsByTagName('pydev_pathproperty'):
            if propnode.getAttribute('name') == 'org.python.pydev.PROJECT_SOURCE_PATH':
                break
        else:
            propnode = doc.createElement('pydev_pathproperty')
            propnode.setAttribute('name', 'org.python.pydev.PROJECT_SOURCE_PATH')
            projnodes = doc.getElementsByTagName('pydev_project')
            if not projnodes:
                logging.warn('pydev configure file corrupted')
                return
            projnodes[0].AppendChild(propnode)
        

        for pathnode in propnode.getElementsByTagName('path'):
            file_path =  pathnode.childNodes[0].data
            name = file_path[file_path.rfind('/')+1:]
            if name.lower() in egg_names_remove:
                propnode.removeChild(pathnode)
                
        pathnode = doc.createElement('path')
        print(egg_name)
        pathnode.appendChild(doc.createTextNode('/${PROJECT_DIR_NAME}/exlib/%s'%egg_name))
        propnode.appendChild(pathnode)
        with codecs.open(pydev_path, 'w', 'utf8') as fd:
            fd.write(doc.toxml(encoding='UTF-8'))
        
                    
    def list_names(self):
        '''获取全部的扩展包的名字
        '''
        if not os.path.isfile(self._installed_libs):
            return []
        names = []
        with open(self._installed_libs, 'r') as fd:
            for libname in fd.readlines():
                libname = libname.strip('\r\n ')
                if not libname:
                    continue
                names.append(libname)
        return names