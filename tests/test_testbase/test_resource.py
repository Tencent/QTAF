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

import os
import shutil
import six
import sys
import unittest

from testbase import resource
from testbase.conf import settings
from testbase.test import modify_environ
from testbase.util import smart_text, codecs_open

suffix = "%s%s" % (sys.version_info[0], sys.version_info[1])
root_dir = os.path.join(settings.PROJECT_ROOT, 'resources')
test_dir_name = 'test_dir_%s' % suffix
test_file_name = "a_%s.txt" % suffix


def _create_local_testfile():
    test_dir = os.path.join(root_dir, test_dir_name)
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)
    with codecs_open(os.path.join(test_dir, "foo.txt"), mode="w") as fd:
        fd.write("foo")
    local_file = os.path.join(root_dir, 'a_%s.txt' % suffix)
    with codecs_open(local_file, 'w', encoding="utf-8") as f:
        f.write('abc')

    return local_file, root_dir




dup_test_dir = "base_test_%s" % sys.version_info[0]


def _copy_testfile(src):
    base_dir = os.path.join(settings.PROJECT_ROOT, dup_test_dir)
    if not os.path.isdir(base_dir):
        os.mkdir(base_dir)
    res_dir = os.path.join(base_dir, 'resources')
    if os.path.isdir(res_dir):
        shutil.rmtree(res_dir)
    shutil.copytree(src, res_dir)
    return base_dir


class TestResManager(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if six.PY2:
            cls.assertRaisesRegex = cls.assertRaisesRegexp

        cls.local_file, cls.local_dir = _create_local_testfile()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(os.path.join(root_dir, test_dir_name), True)
        os.remove(cls.local_file)

    def test_get_local_file(self):
        fm = resource.TestResourceManager(resource.LocalResourceManagerBackend()).create_session()
        self.assertEqual(self.local_file, fm.get_file(test_file_name))
        self.assertEqual(self.local_file, resource.get_file(test_file_name))

        paths = []
        for it in os.listdir(os.path.join(self.local_dir, test_dir_name)):
            paths.append(smart_text(os.path.join(self.local_dir, test_dir_name, it)))
        list_result = fm.list_dir(test_dir_name)
        self.assertEqual(paths, list_result)
        list_result = resource.list_dir(test_dir_name)
        self.assertEqual(paths, list_result)


    def test_nofile_raise(self):
        fm = resource.TestResourceManager(resource.LocalResourceManagerBackend()).create_session()
        self.assertRaisesRegex(Exception, "文件不存在", fm.get_file, 'a_xxx.txt')
        self.assertRaisesRegex(Exception, "文件不存在", resource.get_file, 'a_xxx.txt')
        self.assertRaisesRegex(Exception, "目录不存在", fm.list_dir, 'xxx_xxx')
        self.assertRaisesRegex(Exception, "目录不存在", resource.list_dir, 'xxx_xxx')

    def test_duplicated_raise(self):
        _, local_dir = _create_local_testfile()
        dup_dir = _copy_testfile(local_dir)
        self.addCleanup(shutil.rmtree, dup_dir, True)
        fm = resource.TestResourceManager(resource.LocalResourceManagerBackend()).create_session()
        self.assertRaisesRegex(Exception, "存在多个", fm.get_file, test_file_name)
        self.assertRaisesRegex(Exception, "存在多个", fm.list_dir, test_dir_name)
        self.assertRaisesRegex(Exception, "存在多个", resource.get_file, test_file_name)
        self.assertRaisesRegex(Exception, "存在多个", resource.list_dir, test_dir_name)

    def test_unregisted_restype(self):
        rm = resource.TestResourceManager(resource.LocalResourceManagerBackend()).create_session()
        with self.assertRaises(ValueError):
            rm.acquire_resource("xxx")
        with self.assertRaises(ValueError):
            rm.release_resource("xxx", 12)

    def test_walk_dir(self):
        dir_path_set = set()
        dir_names_set = set()
        file_names_set = set()
        for dir_path, dir_names, file_names in resource.walk("/"):
            dir_path_set.add(os.path.basename(dir_path))
            for dir_name in dir_names:
                dir_names_set.add(dir_name)
            for file_name in file_names:
                file_names_set.add(file_name)
        self.assertTrue(test_dir_name in dir_path_set)
        self.assertTrue(test_dir_name in dir_names_set)
        self.assertTrue(test_file_name in file_names_set)

    def test_testcase_resources(self):
        from tests.sampletest.hellotest import ResmgrTest
        result = ResmgrTest().debug_run()
        self.assertTrue(result.is_passed())


if __name__ == '__main__':
    unittest.main(defaultTest="TestResManager.test_get_local_file")
