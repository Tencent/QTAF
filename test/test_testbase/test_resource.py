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
'''runner test
'''

import unittest, os, shutil, six
from testbase import resource
from testbase.conf import settings
from testbase.test import modify_environ
from testbase.util import smart_text, codecs_open

def _create_local_testfile():
    res_dir = os.path.join(settings.PROJECT_ROOT,'resources')
    os.makedirs(os.path.join(res_dir,'test_dir'))
    local_file = os.path.join(res_dir,'a.txt')
    with codecs_open(local_file, 'w', encoding="utf-8") as f:
        f.write('abc')
    
    return local_file, res_dir


def _copy_testfile(src):
    base_dir = os.path.join(settings.PROJECT_ROOT,'base_test')
    if not os.path.isdir(base_dir):
        os.mkdir(base_dir)
    res_dir = os.path.join(base_dir,'resources')
    if os.path.isdir(res_dir):
        shutil.rmtree(res_dir)
    shutil.copytree(src, res_dir)
    return base_dir

class TestResManager(unittest.TestCase):
    def setUp(self):
        if six.PY2:
            self.assertRaisesRegex = self.assertRaisesRegexp
    
    def tearDown(self):
        proj_root = settings.PROJECT_ROOT
        shutil.rmtree(os.path.join(proj_root, "resources"), ignore_errors=True)
        shutil.rmtree(os.path.join(proj_root, "base_test"), ignore_errors=True)
        
    def test_get_local_file(self):
        local_file, local_dir = _create_local_testfile()
        fm = resource.TestResourceManager(resource.LocalResourceManagerBackend()).create_session()
        self.assertEqual(local_file, fm.get_file('a.txt'))
        self.assertEqual(local_file, resource.get_file('a.txt'))
        
        paths =[]
        for it in os.listdir(local_dir):
            paths.append(smart_text(os.path.join(local_dir,it)))
        self.assertEqual(paths,fm.list_dir(''))
        self.assertEqual(paths,resource.list_dir(''))
  
         
    def test_nofile_raise(self):
        fm = resource.TestResourceManager(resource.LocalResourceManagerBackend()).create_session()
        self.assertRaisesRegex(Exception, "文件不存在",fm.get_file,'a.txt')
        self.assertRaisesRegex(Exception, "文件不存在",resource.get_file,'a.txt')
        self.assertRaisesRegex(Exception, "目录不存在",fm.list_dir,'')
        self.assertRaisesRegex(Exception, "目录不存在",resource.list_dir,'')
                 
    def test_duplicated_raise(self):
        _, local_dir=_create_local_testfile()
        _copy_testfile(local_dir)
        fm = resource.TestResourceManager(resource.LocalResourceManagerBackend()).create_session()
        self.assertRaisesRegex(Exception, "存在多个",fm.get_file,'a.txt')
        self.assertRaisesRegex(Exception, "存在多个",fm.list_dir,'')
        self.assertRaisesRegex(Exception, "存在多个",resource.get_file,'a.txt')
        self.assertRaisesRegex(Exception, "存在多个",resource.list_dir,'')
        
    def test_unregisted_restype(self):
        rm = resource.TestResourceManager(resource.LocalResourceManagerBackend()).create_session()
        with self.assertRaises(ValueError):
            rm.acquire_resource("xxx")      
        with self.assertRaises(ValueError):
            rm.release_resource("xxx", 12)
        
if __name__ == '__main__':
    unittest.main(defaultTest="TestResManager.test_get_local_file")
