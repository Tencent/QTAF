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
'''conf test
'''

from testbase.conf import settings, SettingsMixin
from testbase.test import modify_settings
import unittest


class SettingTest(unittest.TestCase):
    
    def test_get(self):
        '''get settings
        '''
        self.assertEqual(settings.DEBUG, False)
        self.assertEqual(settings.get('DEBUG'), False)
        self.assertEqual(settings.get('NOT_EXIST', False), False)
        
    def test_set(self):
        '''set settings failed
        '''
        self.assertRaises(RuntimeError, setattr, settings, 'DEBUG', False)
        
    def test_contain(self):
        '''test settings in op
        '''
        self.assertEqual("DEBUG" in settings, True, "DEBUG should have been in settings")
        self.assertEqual("IMPOSSIBLE" in settings, False, "IMPOSSIBLE is unexpected in settings")
        
    def test_iteration(self):
        self.assertEqual("DEBUG" in list(settings), True, "DEBUG should have been in list(settings)")

class Dummy(SettingsMixin):
    class Settings(object):
        DUMMY_A = 0
            
class Dummy2(SettingsMixin):
    class Settings(object):
        B = 1
        
class Dummy3(SettingsMixin):
    class Settings(object):
        Dummy3_A = 4
        
class DummyChild(Dummy):
    class Settings(object):
        DUMMYCHILD_A = 2
        
class DummyChild2(Dummy):
    class Settings(object):
        DUMMY_A = 1
        
class DummyChild3(Dummy):
    class Settings(object):
        DUMMYCHILD3_B = -1

class SettingsMixinTest(unittest.TestCase):
    """test case for settings mixin class
    """
    def test_get(self):
        self.reset_class_settings(Dummy)
        dummy = Dummy()
        self.assertEqual(dummy.settings.DUMMY_A, 0)
        self.assertRaises(AttributeError, getattr, dummy.settings, "B")
        
        with modify_settings(GLOBAL_X="xxxx", DUMMY_A=100):
            self.reset_class_settings(Dummy)
            self.assertEqual(dummy.settings.GLOBAL_X, "xxxx")
            self.assertEqual(dummy.settings.DUMMY_A, 100)
        
    def test_set(self):
        self.reset_class_settings(Dummy)
        dummy = Dummy()
        self.assertRaises(RuntimeError, setattr, dummy.settings, "C", 2)
        
    def test_declare(self):
        self.assertRaises(RuntimeError, getattr, Dummy2(), "settings")
        self.assertRaises(RuntimeError, getattr, Dummy3(), "settings")
        self.assertRaises(RuntimeError, getattr, Dummy3(), "settings")
        
    def test_deriving(self):
        self.reset_class_settings(DummyChild)
        child = DummyChild()
        self.assertEqual(child.settings.DUMMY_A, 2)
        self.assertEqual(child.settings.DUMMYCHILD_A, 2)
        
        with modify_settings(DUMMY_A=3):
            self.reset_class_settings(Dummy)
            dummy = Dummy()
            self.assertEqual(dummy.settings.DUMMY_A, 3)
            
            self.reset_class_settings(DummyChild)
            child = DummyChild()
            self.assertRaises(RuntimeError, getattr, child, "settings")
            
        with modify_settings(DUMMYCHILD_A=4):
            self.reset_class_settings(DummyChild)
            self.assertEqual(child.settings.DUMMY_A, 4)
            self.assertEqual(child.settings.DUMMYCHILD_A, 4)
            
        self.assertRaises(RuntimeError, getattr, DummyChild2(), "settings")
        
        child = DummyChild3()
        self.assertEqual(child.settings.DUMMYCHILD3_B, -1)
        self.assertRaises(AttributeError, getattr, child.settings, "DUMMYCHILD3_A")
            
    def reset_class_settings(self, cls):
        settings_key = "_%s_settings" % cls.__name__
        if hasattr(cls, settings_key):
            delattr(cls, settings_key)
        
if __name__ == "__main__":
    unittest.main(defaultTest="SettingsMixinTest.test_deriving")