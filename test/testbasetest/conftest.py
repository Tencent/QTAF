# -*- coding: utf-8 -*-
'''conf test
'''
#2015/03/27 eeelin created

from testbase.conf import settings
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
        

