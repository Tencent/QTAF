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
QPath测试
'''
import unittest
from tuia.qpathparser import QPathParser, QPathSyntaxError


class QPathTest(unittest.TestCase):
    
    def test_invalid_operator_in_instance(self):
        qp = "/ ClassName='TxGuiFoundation' & Caption='QQ' / Instance~=2 & name='mainpanel'"
        with self.assertRaises(QPathSyntaxError) as cm:
            QPathParser().parse(qp)
        self.assertEqual(qp.find('~='), cm.exception.lexpos)
        
    def test_invalid_operator_in_maxdepth(self):
        qp = "/ ClassName='TxGuiFoundation' & Caption='QQ' / maxdepth~=2 & name='mainpanel'"
        with self.assertRaises(QPathSyntaxError) as cm:
            QPathParser().parse(qp)
        self.assertEqual(qp.find('~='), cm.exception.lexpos)
        
    def test_invalid_value_of_instance(self):
        qp = "/ ClassName='TxGuiFoundation' & Caption='QQ' / instance='xxx' & name='mainpanel'"
        with self.assertRaises(QPathSyntaxError) as cm:
            QPathParser().parse(qp)
        #print cm.exception.msg
        self.assertEqual(qp.find('\'xxx\''), cm.exception.lexpos)
        
    def test_invalid_value_of_match_operator(self):
        qp = "/ ClassName='TxGuiFoundation' & Caption='QQ' / name~=true"
        with self.assertRaises(QPathSyntaxError) as cm:
            QPathParser().parse(qp)
        #print cm.exception.msg
        self.assertEqual(qp.find('~='), cm.exception.lexpos)
        
    def test_invalid_seperator(self):
        qp = "| ClassName='TxGuiFoundation' & Caption='QQ' | name~=true"
        with self.assertRaises(QPathSyntaxError) as cm:
            QPathParser().parse(qp)
        self.assertEqual(0, cm.exception.lexpos)
        
#     def test_empty_prop_value(self):
#         qp = "/ ClassName='TxGuiFoundation' & Caption='' / name~=true"
#         with self.assertRaises(QPathSyntaxError) as cm:
#             QPathParser().parse(qp)
#         self.assertEqual(qp.find("''"), cm.exception.lexpos)
        
    def test_maxdepth_smaller_than_zero(self):
        qp = "/ ClassName='TxGuiFoundation' & Caption='xxx' / Instance=-1 & maxdepth=0 & name='xxx'"
        with self.assertRaises(QPathSyntaxError) as cm:
            QPathParser().parse(qp)
        self.assertEqual(qp.find('0'), cm.exception.lexpos)
            
    def test_dumps(self):
        
        qp = "/ ClassName='TxGuiFoundation' & Caption='QQ' / name=true"
        data,_ = QPathParser().parse(qp)
        self.assertEqual([{'ClassName': ['=', 'TxGuiFoundation'], 'Caption': ['=', 'QQ']}, {'name': ['=', True]}],
                         data)
        
    def test_type_trans(self):
        qp = "/ A='xxx' & B=-0X2121 & C=True"
        data,_ = QPathParser().parse(qp)
        data = data[0]
        self.assertEqual(data['A'][1], 'xxx')
        self.assertEqual(data['B'][1], -0X2121)
        self.assertEqual(data['C'][1], True)
        
    def test_escape(self):
        qp = "/ A='xxx' & B='\"' & C=True"
        data,_ = QPathParser().parse(qp)
        self.assertEqual(data[0]['B'][1], '\"') 
        
        qp = "/ A='xxx' & B='\\'' & C=True"
        data,_ = QPathParser().parse(qp)
        self.assertEqual(data[0]['B'][1], "'") 
        
        qp = "/ A='xxx' & B='\d' & C=True"
        data,_ = QPathParser().parse(qp)
        self.assertEqual(data[0]['B'][1], "\d") 
        
        qp = "/ A='xxx' & B='\\d' & C=True"
        data,_ = QPathParser().parse(qp)
        self.assertEqual(data[0]['B'][1], "\\d") 
        
        
# class LocatorTest(unittest.TestCase):
#     
#     def test_as_dict(self):
#         qp = "/ ClassName='TxGuiFoundation' & Caption='QQ' / name=true"
#         locator = QPath(qp).locators[0]
#         self.assertEqual(locator['ClassName'].name.value, 'ClassName')
#         self.assertEqual(locator['classname'].name.value, 'ClassName')
#         self.assertEqual(locator['Caption'].value.value, 'QQ')       
#         self.assertTrue('CLASSNAME' in [it for it in locator])
#         self.assertTrue('CAPTION' in [it for it in locator])
#         self.assertTrue('Caption' in locator)
#         self.assertTrue('caption' in locator)
    