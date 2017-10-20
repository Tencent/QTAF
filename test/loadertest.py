# -*- coding: utf-8 -*-
'''
testloader test case
'''

import unittest

from testbase.loader import TestLoader

class LoaderTest(unittest.TestCase):
    
    def test_load_data_drive(self):
        
        loader = TestLoader()
        for it in loader.load("test.sampletest.hellotest/XX"):
            print it
        