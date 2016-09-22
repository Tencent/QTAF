# -*-  coding: UTF-8  -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
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
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
__all__ = ['SendKeys', 'win32ext', 'iedriver', 'ietips']
import sys, os, time, shutil, zipfile, comtypes
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-

class __init__:
    def __init__(self):
        self.tag_time = 1362056628.29
        self.cur_path = os.path.dirname(os.path.realpath(__file__))
        self.lib_name = 'ielib.lib'
        self.lib_path = os.path.join(self.cur_path, self.lib_name)
        self.tmp_path = os.getenv('TEMP')
        self.tmp_paths = []
        self.out_path = os.path.join(os.getenv('APPDATA'), 'ielib')
        if self.check_need_decompress() : self.revise_lib_path();self.import_lib();self.write_pver(self.get_python_ver());self.clean_tmp_paths()
        else                            : self.import_exist_lib()
    
    def check_need_decompress(self):
        if not os.path.exists(self.out_path)               : return True
        if len(os.listdir(self.out_path)) == 0             : return True
        if self.read_pver() != self.get_python_ver()    : return True
        if os.path.getmtime(self.out_path) > self.tag_time : return False
        return True
    
    def revise_lib_path(self):
        shutil.rmtree(self.out_path, ignore_errors=True)
        _root, _path = os.path.splitdrive(self.cur_path)
        tag_path = _root + '\\'
        paths = _path.strip('\\').split('\\')
        for item in paths:
            tag_path = os.path.join(tag_path, item)
            if zipfile.is_zipfile(tag_path) or (os.path.isfile(tag_path) and os.path.splitext(tag_path)[1].lower()) in ['exe', 'egg']:
                tmp_path = os.path.join(self.tmp_path, 'TEMP%s' % str(int(time.time())))
                zp = zipfile.ZipFile(tag_path, mode="r", compression=zipfile.ZIP_DEFLATED)
                zp.extractall(tmp_path)
                zp.close()
                tag_path = tmp_path
                self.tmp_paths.append(tmp_path)
        self.lib_path = os.path.join(tag_path, self.lib_name)        
        
    def write_pver(self, version):
        '''写入解压时所用python版本号
        '''
        with open(os.path.join(self.out_path, 'pver'), 'w') as f:
            f.write(version)
            
    def read_pver(self):
        '''读取解压时所用python版本号
        '''
        version = '0.0.0'
        pver_path = os.path.join(self.out_path, 'pver')
        if not os.path.exists(pver_path):
            return '0.0.0'
        with open(os.path.join(self.out_path, 'pver'), 'r') as f:
            version = f.read()
        return version
    
    def get_python_ver(self):
        return '%s.%s.%s'%(sys.version_info[0], sys.version_info[1], sys.version_info[2])
    
    def import_lib(self):
        global SendKeys, win32ext, iedriver, ietips
        sys.path.append(self.lib_path)
        import ielibinitialize, SendKeys, win32ext, iedriver, ietips
        
        # try    : import ielibinitialize, SendKeys, win32ext, iedriver, ietips
        # except : raise Exception('Error: ielib init failed')
    
    def import_exist_lib(self):
        global SendKeys, win32ext, iedriver, ietips
        sys.path.append(self.out_path)
        import SendKeys, win32ext, iedriver, ietips
    
    def clean_tmp_paths(self):
        for path in self.tmp_paths:
            if os.path.exists(path):shutil.rmtree(path)


# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
__init__()
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
