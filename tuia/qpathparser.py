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
QPath解析器

QPath是一个用于定位各个平台的UI控件（除Web控件）的查询语言。

 - QPath语法定义如下::

    QPath ::= Seperator QPath Seperator UIObjectLocator
    UIObjectLocator ::= UIObjectProperty PropertyConnector UIObjectLocator
    UIObjectProperty ::= UIProperty 
                        | RelationProperty 
                        | IndexProperty
                        | UITypeProperty 
    UIProperty ::= PropertyName Operator Literal
    RelationProperty ::= MaxDepthIdentifier EqualOperator Literal
    IndexProperty ::= InstanceIdentifier EqualOperator Literal
    UITypeProperty ::= UITypeIdentifier EqualOperator StringLiteral
    MaxDepthIdentifier := "MaxDepth"
    InstanceIdentifier ::= "Instance"
    UITypeIdentifier := "UIType"
    Operator ::= EqualOperator | MatchOperator
    PropertyConnector ::= "&&"
    Seperator ::= "/"
    EqualOperator ::= "="  #精确匹配
    MatchOperator ::= "~="  #使用正则进行模糊匹配
    PropertyName  ::= "[a-zA-Z_]*"
    Literal := StringLiteral
              | IntegerLiteral
              | BooleanLiteral
    StringLiteral ::= "\"[a-zA-Z_]*\""
    IntegerLiteral ::= "[0-9]*"
    BooleanLiteral := "True" | "False" | "true" | "false"


 - 需要注意的是，QPath的属性名都是大小写无关的。

 - 简单举例如下::
 
    / ClassName='TxGuiFoundation' && Caption~='QQ\d+' / name='mainpanel'


'''
from __future__ import absolute_import

import six
import types

try:
    from .ply import lex, yacc
    from .ply.lex import TOKEN
except ImportError:
    from ply import lex, yacc
    from ply.lex import TOKEN


class QPathSyntaxError(Exception):
    '''QPath语法错误
    '''

    def __init__(self, qpath_string, err_msg, lexpos):
        '''Constructor
        
        :param qpath_string: QPath字符串
        :type qpath_string: str
        :parma err_msg: 错误信息
        :type err_msg: str
        :param lexpos: 错误对应的词法位置
        :type lexpos: int
        '''
        self.qpath_string = qpath_string
        self.msg = err_msg
        self.lexpos = lexpos

    def __str__(self):
        return '%s\n  %s\n  %s^' % (self.msg, self.qpath_string, ' ' * self.lexpos)


class QPathLexer(object):
    '''QPath词法解析器
    '''

    tokens = ['SEPERATOR',
              'EQUAL',
              'MATCH',
              'AND',
              'BOOL_CONST',
              'STRING_LITERAL',
              'INT_CONST_DEC',
              'INT_CONST_OCT',
              'INT_CONST_HEX',
              'PROPERTY',
              'MINUS']

    t_ignore = "\t "
    t_EQUAL = r'='
    t_MATCH = r'~='
    t_AND = r'(&&)|(&)'
    t_MINUS = r'-'
    t_SEPERATOR = '/'

    bad_match = r'~[^=*]'

    t_PROPERTY = r'[a-zA-Z_][0-9a-zA-Z_]*'

    boolean_constant = '(True)|(False)|(true)|(false)'

    decimal_constant = '(0)|([1-9][0-9]*)'
    octal_constant = '0[0-7]+'
    hex_prefix = '0[xX]'
    hex_digits = '[0-9a-fA-F]+'
    hex_constant = hex_prefix + hex_digits

    bad_octal_constant = '0[0-7]*[89]'

    # simple_escape = r"""([a-zA-Z._~!=&\^\-\\?'"])"""
    # decimal_escape = r"""(\d+)"""
    # hex_escape = r"""(x[0-9a-fA-F]+)"""
    # bad_escape = r"""([\\][^a-zA-Z._~^!=&\^\-\\?'"x0-7])"""
    # escape_sequence = r"""(\\("""+simple_escape+'|'+decimal_escape+'|'+hex_escape+'))'

    escape_sequence_1 = r'''(?<=\\)"'''
    escape_sequence_2 = r"""(?<=\\)'"""

    string_char_1 = r"""([^"]|""" + escape_sequence_1 + ')'
    string_literal_1 = '"' + string_char_1 + '*"'
    # bad_string_literal_1 = '"'+string_char_1+'*'+bad_escape+string_char_1+'*"'

    string_char_2 = r"""([^']|""" + escape_sequence_2 + ')'
    string_literal_2 = "'" + string_char_2 + "*'"
    # bad_string_literal_2 = "'"+string_char_2+'*'+bad_escape+string_char_2+"*'"

    string_literal = '(' + string_literal_1 + ')|(' + string_literal_2 + ')'
    # bad_string_literal = '('+bad_string_literal_1+')|('+bad_string_literal_2+')'

    @TOKEN(boolean_constant)
    def t_BOOL_CONST(self, t):
        if t.value.lower() == 'true':
            t.value = True
        else:
            t.value = False
        return t

    @TOKEN(hex_constant)
    def t_INT_CONST_HEX(self, t):
        t.value = int(t.value, 16)
        return t

    @TOKEN(octal_constant)
    def t_INT_CONST_OCT(self, t):
        t.value = int(t.value, 8)
        return t

    @TOKEN(decimal_constant)
    def t_INT_CONST_DEC(self, t):
        t.value = int(t.value)
        return t

    @TOKEN(string_literal)
    def t_STRING_LITERAL(self, t):
        col = t.value[0]
        value = t.value[1:-1].replace("\\%s" % col, col)
        t.value = value
        return t

#     @TOKEN(bad_string_literal)
#     def t_BAD_STRING_LITERAL(self, t):
#         self._error("字符串包含非法的转移字符", t)

    @TOKEN(bad_match)
    def t_BAD_MATCH(self, t):
        self._error("'~'后只能连接'='", t)

    def t_error(self, t):
        msg = '存在非法字符: %s' % repr(t.value[0])
        self._error(msg, t)

    def _error(self, msg, t):
        '''错误通知
        '''
        raise QPathSyntaxError(self._qpath_string, msg, t.lexpos)

    def input(self, qpath_string):  # @ReservedAssignment
        '''词法分析输入
        
        :param qpath_string: QPath字符串
        :type qpath_string: str
        '''
        self._qpath_string = qpath_string
        self._lexer = lex.lex(object=self)
        self._lexer.input(qpath_string)
        return self

    def token(self):
        '''解析并返回一个Token
        '''
        t = self._lexer.token()
        return t


class PropertyName(object):
    '''QPath属性名
    '''

    def __init__(self, value, lexpos):
        '''Constructor
        
        :param value: 属性名字符串
        :type value: str
        :param lexpos: 对应的词法位置
        :type lexpos: int
        '''
        self.value = value
        self.lexpos = lexpos

    def __str__(self):
        return '<PropertyName value:%s lexpos:%s>' % (self.value, self.lexpos)


class Literal(object):
    '''QPath属性常量值
    '''

    def __init__(self, value, lexpos):
        '''Constructor
        
        :param value: 属性值常量
        :type value: str/int/bool
        :param lexpos: 对应的词法位置
        :type lexpos: int
        '''
        self.value = value
        self.lexpos = lexpos

    def __str__(self):
        return '<Literal value:%s lexpos:%s>' % (repr(self.value), self.lexpos)


class Operator(object):
    '''QPath操作符
    '''

    def __init__(self, value, lexpos):
        '''Constructor
        
        :param value: 属性操作符
        :type value: str
        :param lexpos: 对应的词法位置
        :type lexpos: int
        '''
        self.value = value
        self.lexpos = lexpos

    def __str__(self):
        return '<Operator value:%s lexpos:%s>' % (repr(self.value), self.lexpos)


class UIObjectProperty(object):
    '''QPath属性
    '''

    def __init__(self, name, operator, value):
        '''Constructor
        
        :param name: 属性名
        :type name: PropertName
        :param operator: 属性操作符
        :type operator: Operator
        :param value: 属性值
        :type value: Literal
        '''
        self.name = name
        self.operator = operator
        self.value = value
        self.lexpos = self.name.lexpos

    def __str__(self):
        return "<UIObjectProperty %s>" % (self.format())

    def format(self):
        '''格式化字符串
        
        :returns: str
        '''
        return '%s%s%s' % (self.name.value, self.operator.value, repr(self.value.value))


class UIObjectLocator(object):
    '''QPath Locator
    '''

    def __init__(self, properties):
        '''Constructor
        
        :param properties: 属性字典
        :type properties: dict
        '''
        self._prop_dict = {}
        for it in properties:
            self._prop_dict[it.name.value.upper()] = it
        self.lexpos = properties[0].lexpos

    def append(self, prop):
        '''增加一个属性
        
        :param prop: 属性
        :type prop: UIObjectProperty
        '''
        self._prop_dict[prop.name.value.upper()] = prop

    def dumps(self):
        '''序列化
        
        :returns: list
        '''
        d = {}
        for name in self:
            prop = self[name]
            d[prop.name.value] = [prop.operator.value, prop.value.value]
        return d

    def format(self):
        '''格式化字符串
        
        :returns: str
        '''
        return ' & '.join([it.format() for it in self._prop_dict.values()])

    def __str__(self):
        return '<UIObjectLocator "%s">' % self.format()

    def __getitem__(self, name):
        return self._prop_dict.get(name.upper())

    def __delitem__(self, name):
        del self._prop_dict[name.upper()]

    def __setitem__(self, name, val):
        self._prop_dict[name.upper()] = val

    def __contains__(self, name):
        return name.upper() in self._prop_dict

    def __iter__(self):
        return self._prop_dict.__iter__()


class QPathParser(object):
    '''QPath语法解析器
    
    QPath解析器解析QPath后会生成两个结构:
    
    1. QPath结构列表：每一个UIObjectLocator用一个字典表示
    其中字典的键值为属性名，对应的值为一个长度为2的列表，第一个元素为操作符号，
    目前为字符串'='或'~='，第二个元素为属性值
    
    2. QPath词法位置信息：和解析后的结构对应，每一个UIObjectLocator用一个字典表示
    其中字典的键值为属性名，对应的指为一个长度为3的列表，第一个元素为属性名的
    词法位置，第二个元素为操作符的词法位置，第三个元素为属性值的词法位置
    
    比如以下的QPath::
    
        / ClassName="TxGuiFoundation" && Caption1~='QQ\d+' && Instance=-1 / UIType='GF' && name='mainpanel' && MaxDepth=10
    
    解析后得到的结构列表为::
    
        [{'Caption1': ['~=', 'QQ\\d+'],
          'ClassName': ['=', 'TxGuiFoundation'],
          'Instance': ['=', -1]},
         {'MaxDepth': ['=', 10], 
          'UIType': ['=', 'GF'], 
          'name': ['=', 'mainpanel']}]

    解析后得到的词法位置信息表为::
    
        [{'CAPTION1': [33, 41, 43],
          'CLASSNAME': [2, 11, 12],
          'INSTANCE': [54, 62, 63]},
         {'MAXDEPTH': [103, 111, 112], 
          'NAME': [83, 87, 88], 
          'UITYPE': [68, 74, 75]}]
    
    使用方法示例::
    
        qp ="""/ ClassName="TxGuiFoundation" && Caption1~='QQ\d+' && Instance='-1' / UIType='GF' && name='mainpanel' && MaxDepth='10'"""
        parser = QPathParser()
        qpath_struct, lex_info = parser.parse(qp)
    '''

    INT_TYPE_PROPNAMES = ['INSTANCE', 'MAXDEPTH']

    class _NullStream(object):
        '''模拟空设备
        '''

        def write(self, *_):
            pass

    def __init__(self, verbose=False):
        '''构造函数
        
        :param verbose: 是否有log提示
        :type verbose: boolean
        '''
        if verbose:
            self._logger = None
        else:
            self._logger = yacc.PlyLogger(self._NullStream())

    def parse(self, qpath_string):
        '''返回解析后的结果
        
        :param qpath_string: QPath字符串
        :type qpath_string: string
        :returns: list, list - 解析后结构, 词法位置信息
        '''
        self._last_locator = None
        qpath_string = qpath_string.strip()
        self._lexer = QPathLexer()
        self.tokens = self._lexer.tokens
        self._parser = yacc.yacc(module=self, debuglog=self._logger, errorlog=self._logger, write_tables=0)
        self._qpath_string = qpath_string
        parsed_structs = []
        lex_structs = []
        for locator in self._parser.parse(qpath_string, self._lexer):
            parsed_structs.append(locator.dumps())
            lex_struct = {}
            for propname in locator:
                prop = locator[propname]
                lex_struct[prop.name.value] = [prop.name.lexpos, prop.operator.lexpos, prop.value.lexpos]
            lex_structs.append(lex_struct)
        return parsed_structs, lex_structs

    def _error(self, msg, p, pos):
        '''提示错误
        '''
        raise QPathSyntaxError(self._qpath_string, msg, pos)

    # 以下为YACC语法构造函数
    def p_qpath(self, p):
        '''qpath : SEPERATOR qpath_content
        '''
        p[0] = p[2]

    def p_qpath_content(self, p):
        '''qpath_content : 
                         | object_locator
                         | qpath_content SEPERATOR object_locator
        '''
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[1].append(p[3])
            p[0] = p[1]

    def p_object_locator(self, p):
        '''object_locator : prop
                          | object_locator AND prop
        '''
        if len(p) == 2:
            p[0] = UIObjectLocator([p[1]])
        else:
            p[0] = p[1]
            p[0].append(p[3])

    def p_prop(self, p):
        '''prop : prop_name operator prop_value
        '''
        if p[1].value.upper() in self.INT_TYPE_PROPNAMES:
            if p[2].value == '~=':
                self._error('"%s"属性不可以使用"~="操作符' % (p[1].value), p[2], p[2].lexpos)
            if not isinstance(p[3].value, int):
                try:
                    p[3].value = int(p[3].value)
                except ValueError:
                    self._error('"%s"属性值不可为"%s"类型，必须为int类型' % (p[1].value, type(p[3].value)), p[3], p[3].lexpos)
            if p[1].value.upper() == 'MAXDEPTH':
                if p[3].value <= 0:
                    self._error("MaxDepth属性值必须>0", p[3], p[3].lexpos)

        elif p[2].value == '~=':
            if not isinstance(p[3].value, six.string_types):
                self._error('操作符"~="不可以连接"%s"类型的属性' % (type(p[3].value)), p[2], p[2].lexpos)

        p[0] = UIObjectProperty(p[1], p[2], p[3])

    def p_prop_name(self, p):
        '''prop_name : PROPERTY
        '''
        p[0] = PropertyName(p[1], p.lexpos(1))

    def p_operator(self, p):
        '''operator : EQUAL
                    | MATCH
        '''
        p[0] = Operator(p[1], p.lexpos(1))

    def p_prop_value(self, p):
        '''prop_value : STRING_LITERAL
                      | BOOL_CONST
                      | int_const
        '''
#         if isinstance(p[1], types.StringTypes) and len(p[1]) == 0:
#             self._error("属性值不可为空", p, p.lexpos(1))
        if isinstance(p[1], Literal):
            p[0] = p[1]
        else:
            p[0] = Literal(p[1], p.lexpos(1))

    def p_int_const(self, p):
        '''int_const : INT_CONST_DEC
                     | INT_CONST_OCT
                     | INT_CONST_HEX
                     | MINUS int_const
        '''
        if len(p) == 2:
            p[0] = Literal(p[1], p.lexpos(1))
        else:
            p[0] = Literal(-p[2].value, p.lexpos(1))

    def p_error(self, p):
        '''处理错误
        '''
        if p is None:
            self._error("不完整的QPath", p, len(self._qpath_string))
        lexpos = p.lexpos
        if not isinstance(lexpos, types.IntType):  # 不是Token
            lexpos = p.lexpos(1)
        self._error("QPath语法错误", p, lexpos)


if __name__ == '__main__':

    q = QPathParser().parse("/classname='UIATableCell' && label~='XXX.*群，\\d，ZZZ.*\:.+，.*\\d\:\\d' && visible=true")
    x = "/classname='UIATableCell' && label~='XXX.*群，\\d.*\\,' && visible=true"

    QPathParser().parse('/class="\\d\\""')

    QPathParser().parse("/class='\\d\:\"\\'xxx'")
