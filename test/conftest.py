# -*- coding: utf-8 -*-
'''配置接口测试
'''

from testbase.conf import settings
import unittest


class SettingTest(unittest.TestCase):
    
    def test_get(self):
        '''测试获取配置
        '''
        self.assertEqual(settings.DEBUG, False)
        self.assertEqual(settings.get('DEBUG'), False)
        self.assertEqual(settings.get('NOT_EXIST', False), False)
        
    def test_set(self):
        self.assertRaises(RuntimeError, setattr, settings, 'DEBUG', False)
        

