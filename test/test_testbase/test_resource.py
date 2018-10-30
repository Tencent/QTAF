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

import unittest, os, shutil
from testbase import resource
from testbase.conf import settings

def _create_testfile():
    res_dir = os.path.join(settings.PROJECT_ROOT,'resources')
    if not os.path.isdir(res_dir):
        os.mkdir(res_dir)
    os.path.join(res_dir,'test_dir')
    if not os.path.isdir(res_dir):
        os.mkdir(res_dir)
    local_file = os.path.join(res_dir,'a.txt')
    link_file = os.path.join(res_dir,'test.txt.link')
    with open(local_file,'w') as f:
        f.write('abc')
    with open(link_file,'w') as f:
        f.write('http://file.sng.com/browse/qta/user_resources/test.txt')
    return local_file,link_file[:-5],res_dir

def _copy_testfile(src):
    base_dir = os.path.join(settings.PROJECT_ROOT,'base_test')
    if not os.path.isdir(base_dir):
        os.mkdir(base_dir)
    res_dir = os.path.join(base_dir,'resources')
    if os.path.isdir(res_dir):
        shutil.rmtree(res_dir)
    shutil.copytree(src, res_dir)
    return base_dir

def _rm_testfile():
    rm_root=[]
    for root, _, _ in os.walk(settings.PROJECT_ROOT):
        if root.endswith('resources'):
            rm_root.append(root)
    for it in rm_root:
        try:
            print it
            shutil.rmtree(it)
        except:
            pass
    
    
      

class TestResManager(unittest.TestCase):
    def setUp(self):
        _rm_testfile()
        
      
    def test_get_file(self):
        local_file,link_file, res_dir = _create_testfile()
        self.addCleanup(_rm_testfile)
        fm = resource.TestResourceManager(resource.LocalResourceManagerBackend()).create_session()
        self.assertEqual(local_file, fm.get_file('a.txt'))
        self.assertEqual(link_file, fm.get_file('test.txt'))
        self.assertEqual(local_file, resource.get_file('a.txt'))
        self.assertEqual(link_file, resource.get_file('test.txt'))
         
    def test_path_compatibility(self):
        local_file,link_file, res_dir = _create_testfile()
        self.addCleanup(_rm_testfile)
        fm = resource.TestResourceManager(resource.LocalResourceManagerBackend()).create_session()
        self.assertEqual(local_file, fm.get_file('\\a.txt'))
        self.assertEqual(local_file, fm.get_file('/a.txt'))
        self.assertEqual(link_file, fm.get_file('\\test.txt'))
        self.assertEqual(link_file, fm.get_file('/test.txt'))
        self.assertEqual(local_file, resource.get_file('\\a.txt'))
        self.assertEqual(local_file, resource.get_file('/a.txt'))
        self.assertEqual(link_file, resource.get_file('\\test.txt'))
        self.assertEqual(link_file, resource.get_file('/test.txt'))
     
    def test_list_dir(self):
        _,_, res_dir = _create_testfile()
        self.addCleanup(_rm_testfile)
        fm = resource.TestResourceManager(resource.LocalResourceManagerBackend()).create_session()
        paths =[]
        from testbase.util import _to_unicode
        for it in os.listdir(res_dir):
            paths.append(_to_unicode(os.path.join(res_dir,it)))
        self.assertEqual(paths,fm.list_dir(''))
        self.assertEqual(paths,resource.list_dir(''))
         
    def test_nofile_raise(self):
        fm = resource.TestResourceManager(resource.LocalResourceManagerBackend()).create_session()
        self.assertRaisesRegexp(Exception, "文件不存在",fm.get_file,'a.txt')
        self.assertRaisesRegexp(Exception, "文件不存在",resource.get_file,'a.txt')
        self.assertRaisesRegexp(Exception, "目录不存在",fm.list_dir,'')
        self.assertRaisesRegexp(Exception, "目录不存在",resource.list_dir,'')
                 
    def test_duplicated_raise(self):
        _, _, res_dir=_create_testfile()
        _copy_testfile(res_dir)
        self.addCleanup(_rm_testfile)
        fm = resource.TestResourceManager(resource.LocalResourceManagerBackend()).create_session()
        self.assertRaisesRegexp(Exception, "存在多个",fm.get_file,'a.txt')
        self.assertRaisesRegexp(Exception, "存在多个",fm.list_dir,'')
        self.assertRaisesRegexp(Exception, "存在多个",resource.get_file,'a.txt')
        self.assertRaisesRegexp(Exception, "存在多个",resource.list_dir,'')
        
        
        
        
if __name__ == '__main__':
    unittest.main()
