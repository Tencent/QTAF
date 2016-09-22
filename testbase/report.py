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
'''测试报告
'''

#2015/03/27 olive 新建
#2015/04/20 olive XML结果增加XLS文件生成
#2015/05/25 olive Product新增stream参数

import sys
import codecs
import cgi
import socket
import os
import shutil
import json
import getpass
import string
import locale
import xml.dom.minidom as dom
import xml.sax.saxutils as saxutils
from datetime import datetime

from testbase import testresult
from testbase.testresult import EnumLogLevel

try:
    from testbase.platform import report as _reportitf
    from testbase.platform import fs as _fsitf
except ImportError:
    _reportitf = _fsitf = None
    
    
os_encoding = locale.getdefaultlocale()[1]

class ITestReport(object):
    '''测试报告接口
    '''
    def begin_report(self):
        '''开始测试执行
        '''
        pass
    
    def end_report(self):
        '''结束测试执行
        :param passed: 测试是否通过
        :type passed: boolean
        '''
        pass
        
    def log_test_result(self, testcase, testresult ):
        '''记录一个测试结果
        :param testcase: 测试用例
        :type testcase: TestCase
        :param testresult: 测试结果
        :type testresult: TestResult
        '''
        pass
    
    def log_record(self, level, tag, msg, record):
        '''增加一个记录
        :param level: 日志级别
        :param msg: 日志消息
        :param tag: 日志标签
        :param record: 日志记录信息
        :type level: string
        :type tag: string
        :type msg: string
        :type record: dict
        '''
        pass
    
    def get_testresult_factory(self):
        '''获取对应的TestResult工厂
        :returns ITestResultFactory
        '''
        raise NotImplementedError()
    
    def debug(self, tag, msg, record=None):
        '''记录一个DEBUG日志
        :param msg: 日志消息
        :param tag: 日志标签
        :param record: 日志记录信息
        :type tag: string
        :type msg: string
        :type record: dict
        '''
        if record is None:
            record = {}
        self.log_record(EnumLogLevel.DEBUG, tag, msg, record)
        
    def info(self, tag, msg, record=None):
        '''记录一个INFO日志
        :param msg: 日志消息
        :param tag: 日志标签
        :param record: 日志记录信息
        :type tag: string
        :type msg: string
        :type record: dict
        '''
        if record is None:
            record = {}
        self.log_record(EnumLogLevel.INFO, tag, msg, record)
        
    def warning(self, tag, msg, record=None):
        '''记录一个WARN日志
        :param msg: 日志消息
        :param tag: 日志标签
        :param record: 日志记录信息
        :type tag: string
        :type msg: string
        :type record: dict
        '''
        if record is None:
            record = {}
        self.log_record(EnumLogLevel.WARNING, tag, msg, record)
        
    def error(self, tag, msg, record=None):
        '''记录一个ERROR日志
        :param msg: 日志消息
        :param tag: 日志标签
        :param record: 日志记录信息
        :type tag: string
        :type msg: string
        :type record: dict
        '''
        if record is None:
            record = {}
        self.log_record(EnumLogLevel.ERROR, tag, msg, record)
        
    def critical(self, tag, msg, record=None):
        '''记录一个CRITICAL日志
        :param msg: 日志消息
        :param tag: 日志标签
        :param record: 日志记录信息
        :type tag: string
        :type msg: string
        :type record: dict
        '''
        if record is None:
            record = {}
        self.log_record(EnumLogLevel.CRITICAL, tag, msg, record)
        
class ITestResultFactory(object):
    '''TestResult工厂接口
    '''
    def create(self, testcase ):
        '''创建TestResult对象
        :param testcase: 测试用例
        :type testcase: TestCase
        :return TestResult
        '''
        raise NotImplementedError()
    
    def dumps(self):
        '''序列化
        :return picklable object
        '''
        pass
    
    def loads(self, buf):
        '''反序列化
        :param buf: dumps返回的序列化后的数据
        :type buf: object
        '''
        pass
        
class EmptyTestResultFactory(ITestResultFactory):
    '''测试结果工厂
    '''
    def __init__(self, result_factory_func=None ):
        '''构造函数
        :param result_factory_func: TestResult工厂函数
        :type result_factory_func: Function
        '''
        self._result_factory_func = result_factory_func
        
    def create(self, testcase ):
        '''创建TestResult对象
        :param testcase: 测试用例
        :type testcase: TestCase
        :return TestResult
        '''
        if self._result_factory_func is None:
            return testresult.EmptyResult()
        else:
            return self._result_factory_func(testcase)
        
    def dumps(self):
        '''序列化
        :return picklable object
        '''
        return self._result_factory_func
    
    def loads(self, buf):
        '''反序列化
        :param buf: dumps返回的序列化后的数据
        :type buf: object
        '''
        self._result_factory_func = buf
        
class EmptyTestReport(ITestReport):
    '''不输出测试报告
    '''
    def __init__(self, result_factory_func=None ):
        '''构造函数
        :param result_factory_func: TestResult工厂函数
        :type result_factory_func: callable
        '''
        self._result_factory_func = result_factory_func
    
    def get_testresult_factory(self):
        '''获取对应的TestResult工厂
        :returns ITestResultFactory
        '''
        return EmptyTestResultFactory(self._result_factory_func)

class StreamTestResultFactory(ITestResultFactory):
    '''流形式TestResult工厂
    '''
    def __init__(self, stream ):
        '''构造函数
        :param stream: 指定要输出的流设备
        :type stream: file
        '''
        self._stream = stream
        
    def create(self, testcase ):
        '''创建TestResult对象
        :param testcase: 测试用例
        :type testcase: TestCase
        :return TestResult
        '''
        return testresult.StreamResult(self._stream)
    
    def dumps(self):
        '''序列化
        :return picklable object
        '''
        fileno = self._stream.fileno()
        if fileno not in [0, 1]:
            raise ValueError("不支持的流对象: %s" % self._stream)
        return fileno
    
    def loads(self, buf):
        '''反序列化
        :param buf: dumps返回的序列化后的数据
        :type buf: object
        '''
        fileno = buf
        if fileno == 1:
            self._stream = sys.stdout
        elif fileno == 2:
            self._stream = sys.stderr
        else:
            raise ValueError("invalid fd: %s" % fileno )
    
class StreamTestReport(ITestReport):
    '''流形式的测试报告
    '''
    def __init__(self, stream=sys.stdout, output_testresult=False ):
        '''构造函数
        :param stream: 指定要输出的流设备
        :type stream: file
        :param output_testresult: 是否输出测试用例执行的日志
        :type output_testresult: boolean
        '''
        self._stream = stream
        self._output_testresult = output_testresult
        if stream.encoding and stream.encoding != 'utf8':
            self._write = lambda x: self._stream.write(x.decode('utf8').encode(stream.encoding))
        else:
            self._write = self._stream.write
            
    def begin_report(self):
        '''开始测试执行
        '''
        self._start_time = datetime.now()
        self._write("Test Cases runs at:%s.\n" % self._start_time.strftime("%Y-%m-%d %H:%M:%S"))
    
    def end_report(self):
        '''结束测试执行
        :param passed: 测试是否通过
        :type passed: boolean
        '''
        end_time = datetime.now()
        self._write("Test Cases ends at:%s.\n" % end_time.strftime("%Y-%m-%d %H:%M:%S"))
        self._write("Total execution time is :%s\n" % str(end_time-self._start_time).split('.')[0])
    
    def log_test_result(self, testcase, testresult ):
        '''记录一个测试结果
        :param testcase: 测试用例
        :type testcase: TestCase
        :param testresult: 测试结果
        :type testresult: TestResult
        '''
        self._write("run test case: %s(pass?:%s)\n" % (testcase.test_name, testresult.passed))
                    
    def log_record(self, level, tag, msg, record={}):
        '''增加一个记录
        :param level: 日志级别
        :param msg: 日志消息
        :param tag: 日志标签
        :param record: 日志记录信息
        :type level: string
        :type tag: string
        :type msg: string
        :type record: dict
        '''
        self._write("%s\n" % (msg))
    
    def get_testresult_factory(self):
        '''获取对应的TestResult工厂
        :returns ITestResultFactory
        '''
        if self._output_testresult:
            return StreamTestResultFactory(self._stream)
        else:
            return EmptyTestResultFactory()
        
REPORT_XSL = """<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:template match="/RunResult">
<html>
    <head>
    <style>
    *{
    font-size:12px; 
    font-family: '宋体' , 'Courier New', Arial, 'Arial Unicode MS', '';
    }
    .title
    {
    font-size:14px;
    font-weight: bold;
    margin: 20px auto 5px auto;
    }
    table{
    border:solid 1px #0099CC;
    border-collapse:collapse;
    margin: 0px auto;
    }
    td
    {
    border:solid 1px #0099CC;
    padding: 6px 6px;
    }
    .td_Title
    {
    color:#FFF;
    font-weight: bold;
    background-color:#66CCFF;
    }
    .tr_pass
    {
    background-color:#B3E8B8;
    }
    .tr_fail
    {
    background-color:#F5BCBD;
    }
    .success
    {
    color:#0000FF;
    }
    .fail
    {
    color:#FF0000;
    }
    .exception
    {
    color:#00AA00;
    }
    
    </style>
    </head>
    <body>
    <div class='title'>
        <td>测试报告链接：</td>
        <td><a><xsl:attribute name="href"><xsl:value-of select="TestReportLink/Url"/></xsl:attribute>点击这里</a></td>
    </div>
    <div class='title'>测试运行环境：</div>
    <table>
        <tr>
            <td class='td_Title'>主机名</td>
            <td><xsl:value-of select="TestEnv/PC"/></td>
        </tr>
        <tr>
            <td class='td_Title'>操作系统</td>
            <td><xsl:value-of select="TestEnv/OS"/></td>
        </tr>
    </table>
    <div class='title'>测试运行时间:</div>
    <table>
        <tr>
            <td class='td_Title'>Run开始时间</td>
            <td><xsl:value-of select="RunTime/StartTime"/></td>
        </tr>
        <tr>
            <td class='td_Title'>Run结束时间</td>
            <td><xsl:value-of select="RunTime/EndTime"/></td>
        </tr>
        <tr>
            <td class='td_Title'>Run执行时间</td>
            <td><xsl:value-of select="RunTime/Duration"/></td>
        </tr>
    </table>
    <div class='title'>测试用例汇总：</div>
    <table>
    <tr>
        <td class='td_Title'>用例总数</td>
        <td class='td_Title'>通过用例数</td>
        <td class='td_Title'>失败用例数</td>
    </tr>
    <tr>
        <td>
        <xsl:value-of select="count(TestResult)"/>
        </td>
        <td>
        <xsl:value-of select="count(TestResult[@result='True'])"/>
        </td>
        <td>
        <xsl:value-of select="count(TestResult[@result='False'])"/>
        </td>
    </tr>
    </table>
    <div class='title'>加载失败模块：</div>
    <table>
    <tr>
    <td class='td_Title'>模块名</td>
    <td class='td_Title'>失败Log</td>
    </tr>
    <tr>
    <xsl:for-each select="LoadFailure/Module">
        <tr>
        <td><xsl:value-of select="@name"/></td>
        <td><a><xsl:attribute name="href">
                <xsl:value-of select="@log"/>
            </xsl:attribute>
            Log
        </a></td>
        </tr>
    </xsl:for-each>
    </tr>
    </table>
    <div class='title'>测试用例详细信息：</div>
    <table>
    <tr>
    <td class='td_Title'>测试结果</td>
    <td class='td_Title'>测试用例</td>
    <td class='td_Title'>负责人</td>
    <td class='td_Title'>用例描述</td>
    <td class='td_Title'>用例状态</td>
    <td class='td_Title'>用例Log</td>
    </tr>
    <xsl:for-each select="TestResult">
    <xsl:if test="@result='False'">
        <tr class='tr_fail'>
            <td>失败</td>
            <td><xsl:value-of select="@name"/></td>
            <td><xsl:value-of select="@owner"/></td>
            <td><xsl:value-of select="."/></td>
            <td><xsl:value-of select="@status"/></td>
            <td><a><xsl:attribute name="href">
                    <xsl:value-of select="@log"/>
                    </xsl:attribute>
                    Log
            </a></td>
        </tr>
    </xsl:if>
    <xsl:if test="@result='True'">
        <tr class='tr_pass'>
            <td>通过</td>
            <td><xsl:value-of select="@name"/></td>
            <td><xsl:value-of select="@owner"/></td>
            <td><xsl:value-of select="."/></td>
            <td><xsl:value-of select="@status"/></td>
            <td><a><xsl:attribute name="href">
                    <xsl:value-of select="@log"/>
                    </xsl:attribute>
                    Log
            </a></td>
        </tr>
    </xsl:if>
    </xsl:for-each>
    </table>
    </body>
</html>
</xsl:template>
</xsl:stylesheet>"""

RESULT_XLS = """<?xml version="1.0" encoding="utf-8"?><!-- DWXMLSource="tmp/qqtest.hello.HelloW.xml" --><!DOCTYPE xsl:stylesheet  [
    <!ENTITY nbsp   "&#160;">
    <!ENTITY copy   "&#169;">
    <!ENTITY reg    "&#174;">
    <!ENTITY trade  "&#8482;">
    <!ENTITY mdash  "&#8212;">
    <!ENTITY ldquo  "&#8220;">
    <!ENTITY rdquo  "&#8221;"> 
    <!ENTITY pound  "&#163;">
    <!ENTITY yen    "&#165;">
    <!ENTITY euro   "&#8364;">
]>

<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:strip-space elements="*"/>
<xsl:template match="/TEST">
<html>
    <head>
    <style>
    *{
    font-size:12px; 
    font-family: '宋体' , 'Courier New', Arial, 'Arial Unicode MS', '';
    }
    .title
    {
    font-size:14px;
    font-weight: bold;
    margin: 20px auto 5px auto;
    }
    .subtable{
    border:solid 1px #0099CC;
    border-collapse:collapse;
    margin: 0px auto auto 0px;
    }
    .subtable td
    {
    border:solid 1px #0099CC;
    padding: 6px 6px;
    }
    .td_title
    {
    color:#FFF;
    font-weight: bold;
    background-color:#66CCFF;
    }
    .tr_pass
    {
    background-color:#B3E8B8;
    }
    .tr_fail
    {
    background-color:#F5BCBD;
    }
    .suc_step_title
    {
    background-color:#B3E8B8;
    padding:2px 2px
    }
    
.STYLE1 {font-size: 16px}
.STYLE3 {font-size: 14px; color:#666666;}
.STYLE4 {color: #999999}
.STYLE5 {
    color: #FF0000;
    font-weight: bold;
}
.STYLE6 {
    color: #FF9900;
    font-weight: bold;
}
</style>
    </head>
    <body>
    <div>
    <table class="subtable">
        <tr>
            <td class='td_title'>用例名字：</td>
            <td><xsl:value-of select="@name"/></td>
            <td class='td_title'>运行结果：</td>
            <td>
            <span>
                <xsl:attribute name="style">
                <xsl:if test="@result='True'">color: #00FF00</xsl:if>
                <xsl:if test="@result='False'">color: #FF0000</xsl:if>
                </xsl:attribute>
                <xsl:apply-templates select="@result"/>
            </span>
            </td>
        </tr>
        <tr>
            <td class='td_title'>开始时间：</td>
            <td><xsl:value-of select="@begintime"/></td>
            <td class='td_title'>负责人：</td>
            <td><xsl:value-of select="@owner"/></td>
        </tr>
        <tr>
            <td class='td_title'>结束时间：</td>
            <td><xsl:value-of select="@endtime"/></td>
            <td class='td_title'>优先级：</td>
            <td><xsl:value-of select="@priority"/></td>
        </tr>
        <tr>
            <td class="td_title">运行时间：</td>
            <td><xsl:value-of select="@duration"/></td>
            <td class='td_title'>用例超时：</td>
            <td><xsl:value-of select="@timeout"/>分钟</td>
        </tr>
        
    </table>
    </div> 

    <xsl:apply-templates/>
    </body>
</html>
</xsl:template>

<xsl:template match="@result">
    <xsl:if test=".='True'">通过</xsl:if>
    <xsl:if test=".='False'">失败</xsl:if>
</xsl:template>

<xsl:template match="STEP">
<hr />
<div>
<xsl:if test="@result='True'">
<xsl:attribute name="style">
    padding:2px 2px; background-color:#B3E8B8
</xsl:attribute>
</xsl:if>
<xsl:if test="@result='False'">
<xsl:attribute name="style">
    padding:2px 2px; background-color:#F5BCBD
</xsl:attribute>
</xsl:if>

<table border="0">
  <tr>
    <td><span class="STYLE1">步骤：</span></td>
    <td><span class="STYLE1"><xsl:value-of select="@title"/></span></td>
    <td><span class="STYLE1">&nbsp;<xsl:value-of select="@time"/></span></td>
    <td><span class="STYLE1">&nbsp;
    <xsl:apply-templates select="@result"/>
    </span></td>
  </tr>
</table>
</div>
<hr />
<table>
    <xsl:apply-templates/>
</table>
</xsl:template>
<xsl:template match="DEBUG">
    <tr>
    <td valign="top"><strong>DEBUG:</strong></td>
    <td><xsl:value-of select="text()"/></td>
  </tr>
</xsl:template>
<xsl:template match="INFO">
    <tr>
      <!--<td valign="top"><span class="STYLE4">12:12:11</span></td> -->
    <td valign="top"><strong>INFO:</strong></td>
    <td><xsl:value-of select="text()"/></td>
  </tr>
</xsl:template>
<xsl:template match="WARNING">
  <tr>
      <!--<td valign="top"><span class="STYLE4">12:12:11</span></td> -->
    <td valign="top"><span class="STYLE6">WARNING:</span></td>
    <td><xsl:value-of select="text()"/></td>
  </tr>
</xsl:template>
<xsl:template match="ERROR">
<tr>
      <!--<td valign="top"><span class="STYLE4">12:12:11</span></td> -->
    <td valign="top"><span class="STYLE5">ERROR:</span></td>
    <td><xsl:value-of select="text()"/>
        <pre>
            <xsl:value-of select="EXCEPT/text()"/>
        </pre>
        <table border="0">
            <xsl:apply-templates select="EXPECT"/>
            <xsl:apply-templates select="ACTUAL"/>
        </table>
        <xsl:for-each select="ATTACHMENT">
            <a>
                <xsl:attribute name="href">
                    <xsl:value-of select="@filepath"/>
                </xsl:attribute>
                [<xsl:value-of select="text()"/>]
            </a>
        </xsl:for-each>
    </td>
  </tr>
</xsl:template>
<xsl:template match="EXPECT">
    <tr>
    <td>&nbsp;&nbsp;期望值：</td>
    <td><xsl:value-of select="text()"/></td>
      </tr>
</xsl:template>
<xsl:template match="ACTUAL">
    <tr>
    <td>&nbsp;&nbsp;实际值：</td>
    <td><xsl:value-of select="text()"/></td>
      </tr>
</xsl:template>
</xsl:stylesheet>"""

class XMLTestResultFactory(ITestResultFactory):
    '''XML形式TestResult工厂
    '''
    BAD_CHARS = r'\/*?:<>"|~'
    TRANS = string.maketrans(BAD_CHARS, '='*len(BAD_CHARS))
                    
    def create(self, testcase ):
        '''创建TestResult对象
        :param testcase: 测试用例
        :type testcase: TestCase
        :return TestResult
        '''
        filename = '%s.xml' % testcase.test_name.translate(self.TRANS)
        return testresult.XmlResult(filename)

class XMLTestReport(ITestReport):
    '''XML形式的测试报告
    '''
    def __init__(self):
        '''构造函数
        '''
        self._xmldoc = dom.Document()
        self._xmldoc.appendChild(self._xmldoc.createProcessingInstruction("xml-stylesheet", 'type="text/xsl" href="TestReport.xsl"'))
        self._runrstnode = self._xmldoc.createElement("RunResult")
        self._xmldoc.appendChild(self._runrstnode)
        self._result_factory = XMLTestResultFactory()
        
    def begin_report(self):
        '''开始测试执行
        '''
        self._time_start = datetime.now()
        
        xmltpl = "<TestEnv><PC>%s</PC><OS>%s</OS></TestEnv>"
        hostname = socket.gethostname()
        if sys.platform == 'win32':
            osver = os.popen("ver").read().decode('gbk').encode('utf-8')
        else:
            osver = os.uname()  # @UndefinedVariable
        envxml = dom.parseString(xmltpl % (hostname, osver))
        self._runrstnode.appendChild(envxml.childNodes[0])
        
    def end_report(self):
        '''结束测试执行
        :param passed: 测试是否通过
        :type passed: boolean
        '''
        time_end = datetime.now()
        timexml = "<RunTime><StartTime>%s</StartTime><EndTime>%s</EndTime><Duration>%s</Duration></RunTime>"
        timexml = timexml % (self._time_start.strftime("%Y-%m-%d %H:%M:%S"), time_end.strftime("%Y-%m-%d %H:%M:%S"), str(time_end-self._time_start).split('.')[0] )
        timenodes = dom.parseString(timexml)
        self._runrstnode.appendChild(timenodes.childNodes[0])
        
        xmldata = self._xmldoc.toprettyxml(indent="    ", 
                                           newl="\n", 
                                           encoding='utf-8')
        with codecs.open('TestReport.xml', 'w') as fd:
            fd.write(xmldata)
        with codecs.open('TestReport.xsl', 'w') as fd:
            fd.write(REPORT_XSL)
        with codecs.open('TestResult.xsl', 'w') as fd:
            fd.write(RESULT_XLS)   
    
    def log_test_result(self, testcase, testresult ):
        '''记录一个测试结果
        :param testcase: 测试用例
        :type testcase: TestCase
        :param testresult: 测试结果
        :type testresult: XmlResult
        '''
        casemark = cgi.escape(testcase.test_doc)
        nodestr = """<TestResult result="%s" log="%s" status="%s">%s</TestResult>
        """ % (testresult.passed, testresult.file_path, testcase.status, casemark)
        doc2 = dom.parseString(nodestr)
        resultNode = doc2.childNodes[0]
        resultNode.setAttribute("name", _to_unicode(saxutils.escape(testcase.test_name)))
        resultNode.setAttribute("owner", _to_unicode(saxutils.escape(testcase.owner)))
        self._runrstnode.appendChild(resultNode)
    
    def log_record(self, level, tag, msg, record={}):
        '''增加一个记录
        :param level: 日志级别
        :param msg: 日志消息
        :param tag: 日志标签
        :param record: 日志记录信息
        :type level: string
        :type tag: string
        :type msg: string
        :type record: dict
        '''        
        if tag == 'LOADER' and level == EnumLogLevel.ERROR:
            if record.has_key('testname') and record.has_key('traceback'):
                testname = record['testname']
                mdfailsnode = self._xmldoc.createElement("LoadFailure")
                self._runrstnode.appendChild(mdfailsnode)
                logfile = '%s.log' % testname
                xmltpl = """<Module name="%s" log="%s"/>""" % (testname, logfile)
                mdfailsnode.appendChild(dom.parseString(xmltpl).childNodes[0])
                with open(logfile, 'w') as fd:
                    fd.write(record['traceback'])
                
    def get_testresult_factory(self):
        '''获取对应的TestResult工厂
        :returns ITestResultFactory
        '''
        return self._result_factory
    
if _fsitf and _reportitf:
    
    class Product(object):
        '''产品配置
        '''
        def __init__(self, name, path='', version='0.0', build='0.0', protocol='', stream=''):
            '''构造函数
            :param name: 产品名称，如QQ
            :param path: 产品安装包路径
            :param version: 产品主版本号
            :param build: 产品build号
            :param protocol: 产品协议号
            :param stream: 产品流号
            '''
            self.name = name
            self.version = version
            self.build = build
            self.protocol = protocol
            self.path = path
            self.stream = stream
            
    class Notification(object):
        '''结果通知配置
        '''
        class Item(object):
            def __init__(self, mail=False, sms=False, rtx=False, weixin=False):
                '''构造函数
                :param mail: 是否邮件通知
                :param sms: 是否短信通知
                :param rtx: 是否RTX通知
                :param weixin: 是否微信通知
                '''
                self.mail = mail
                self.sms = sms
                self.rtx = rtx
                self.weixin = weixin
                
            def dumps(self):
                d = {}
                for key in self.__dict__:
                    if getattr(self, key):
                        d[key] = 1
                    else:
                        d[key] = 0
                return json.dumps(d)
            
        def __init__(self, when_success=None, when_failed=None, receivers=None, critical_receivers=None):
            if when_success is None:
                when_success = self.Item()
            if when_failed is None:
                when_failed = self.Item()
            if receivers is None:
                receivers = getpass.getuser()
            if critical_receivers is None:
                critical_receivers = getpass.getuser()
            self.when_success = when_success
            self.when_failed = when_failed
            self.receivers = receivers
            self.critical_receivers = critical_receivers
            
    class NFS(object):
        '''网络文件系统配置
        '''
        _DEFAULT_TFS_ROOT = r"\\FS-GK10A\SNG-Test$\QTA\TestResults"
        
        def __init__(self, backend='cfs', tfs_root=_DEFAULT_TFS_ROOT ):
            '''构造函数
            :param backend: 后端存储系统，cfs或者tfs
            :param tfs_root: 要指定的使用TFS的路径
            '''
            self.backend = backend
            self.tfs_root = tfs_root
            
        def dumps(self):
            '''序列化
            '''
            return {
                "backend": self.backend,
                "tfs_root": self.tfs_root
            }
            
        def loads(self, buf ):
            '''反序列化
            '''
            self.backend = buf['backend']
            self.tfs_root = buf['tfs_root']
            
    class NFStorage(object):
        '''网络文件存储接口
        '''
        @property
        def url(self):
            '''对应的URL路径
            :returns string
            '''
            raise NotImplementedError()
            
        def upload(self, local_file, dstdir=None ):
            '''上传文件
            :param local_file: 本地文件
            :type local_file: string
            :param dstdir: 远程目录
            :type dstdir: string
            :returns string: 上传后引用的路径
            '''
            raise NotImplementedError()
        
        def child(self, name ):
            '''返回孩子节点（子目录）
            :returns NFStorage
            '''
            raise NotImplementedError()
                
        def dumps(self):
            '''序列化
            :return picklable object
            '''
            raise NotImplementedError()
        
        def loads(self, buf):
            '''反序列化
            :param buf: dumps返回的序列化后的数据
            :type buf: object
            '''
            raise NotImplementedError()
        
    def _to_unicode( s ):
        '''将任意字符串转换为unicode编码
        '''
        if isinstance(str, unicode):
            return s
        try:
            return s.decode('utf8')
        except UnicodeDecodeError:
            return s.decode(os_encoding)
        
    class TFSStorage(object):
        '''基于TFS的文件存储
        '''
        def __init__(self, dirname, root ):
            self._dirname = dirname
            self._root = root
            self._path = self.join(root, dirname).decode('utf8')
            if not os.path.isdir(self._path):
                os.makedirs(self._path)
    
        @property
        def url(self):
            '''对应的URL路径
            :returns string
            '''
            return self._path.encode('utf8')
            
        def join(self, *path_items):
            '''连接路径
            '''
            if sys.platform == 'win32':
                return os.path.join(*path_items)
            else:
                return '\\'.join(path_items)
                    
        def upload(self, local_file, dstdir=None ):
            '''上传文件
            :param local_file: 本地文件
            :type local_file: string
            :param dstdir: 远程目录
            :type dstdir: string
            :returns string: 上传后引用的路径
            '''
            local_file = _to_unicode(local_file)
            if dstdir != None:
                dstdir = _to_unicode(dstdir)
                
            if dstdir:
                dstpath = self.join(self._path, dstdir)
            else:
                dstpath = self._path
        
            if sys.platform == 'win32':
                self._try_makedirs(dstpath)
                shutil.copy(local_file, dstpath)
            else:
                self._copy_on_mac(local_file, dstpath)
            ref_url = self.join(dstpath, os.path.basename(local_file))
            return ref_url.encode('utf8')
            
        def _copy_on_mac(self, local_file, dstpath):
            '''在mac上复制文件到TFS
            '''
            idx = dstpath.find('SNG-Test$') + len('SNG-Test$')
            dstpath = '/Volumes/SNG-Test$' + dstpath[idx:].replace('\\', '/')
            if not os.path.isdir(dstpath):
                os.makedirs(dstpath)
            shutil.copy(local_file, dstpath)
            
        def _try_makedirs(self, dstpath ):
            '''在TFS上创建文件夹路径
            由于TFS有时候会导致Error 123错误，这里增加重试
            '''
            for _ in range(3):
                if not os.path.isdir(dstpath):
                    try:
                        os.makedirs(dstpath)
                        return
                    except WindowsError, e:
                        if e.args[0] == 123:
                            continue
                        else:
                            raise
                        
        def child(self, name ):
            '''返回孩子节点（子目录）
            '''
            return TFSStorage( self._dirname + os.path.sep + name, self._root)
        
        def dumps(self):
            '''序列化
            :return picklable object
            '''
            return self._dirname, self._root
        
        def loads(self, buf):
            '''反序列化
            :param buf: dumps返回的序列化后的数据
            :type buf: object
            '''
            self._dirname, self._root = buf
            self._path = self.join(self._root, self._dirname).decode('utf8')
        
    class CFSStorage(object):
        '''基于CFS的文件存储
        '''
        def __init__(self, dirname ):
            self._dirname = dirname
            self._rootfs = _fsitf.FileSystem('TestResults\\%s'%dirname)
        
        @property
        def url(self):
            '''对应的URL路径
            :returns string
            '''
            return 'http://%s%sTestResults/%s' % (_fsitf.FileSystem._host, _fsitf.FileSystem._root, self._dirname.replace('\\','/'))
        
        def upload(self, localfile, dstdir=None ):
            '''上传文件
            :param local_file: 本地文件
            :type local_file: string
            :param dstdir: 远程目录
            :type dstdir: string
            :returns string: 上传后引用的路径
            '''
            localfile = _to_unicode(localfile).encode('utf8')
            if dstdir != None:
                dstdir = _to_unicode(dstdir).encode('utf8')
            if dstdir:
                dstpath = '\\' + dstdir
            else:
                dstpath = '\\'
            self._rootfs.put_file(localfile, dstpath)
            return self._rootfs.get_url(dstpath+'\\'+os.path.basename(localfile))
        
        def child(self, name ):
            '''返回孩子节点（子目录）
            '''
            return CFSStorage( self._dirname + '\\' + name )
        
        def dumps(self):
            '''序列化
            :return picklable object
            '''
            return self._dirname
        
        def loads(self, buf):
            '''反序列化
            :param buf: dumps返回的序列化后的数据
            :type buf: object
            '''
            self._dirname = buf
            self._rootfs = _fsitf.FileSystem('TestResults\\%s'%self._dirname)
            
    class OnlineTestResultFactory(ITestResultFactory):
        '''存储在测试报告服务器上的测试用例结果工厂
        '''
        class EmptyClass(object):
            pass
        
        def __init__(self, reportid, storage, upload_xmlresult ):
            '''构造函数
            :param reportid: 测试报告ID
            :type reportid: string
            :param storage: NFS存储接口
            :type storage: NFStorage
            :param upload_xmlresult: 是否上传xml测试结果文件
            :type upload_xmlresult: boolean
            '''
            self._reportid = reportid
            self._storage = storage
            self._upload_xmlresult = upload_xmlresult
        
        def create(self, testcase ):
            '''创建TestResult对象
            :param testcase: 测试用例
            :type testcase: TestCase
            :return TestResult
            '''
            return testresult.OnlineResult(self._reportid, 
                                           self._storage.child(socket.gethostname()),
                                           self._upload_xmlresult)
                
        def dumps(self):
            '''序列化
            :return picklable object
            '''
            return self._reportid, type(self._storage), self._storage.dumps(), self._upload_xmlresult
        
        def loads(self, buf):
            '''反序列化
            :param buf: dumps返回的序列化后的数据
            :type buf: object
            '''
            self._reportid = buf[0]
            storage_type = buf[1]
            self._storage = self.EmptyClass()
            self._storage.__class__ = storage_type
            self._storage.loads(buf[2])
            self._upload_xmlresult = buf[3]
            
    class OnlineTestReport(ITestReport):
        '''上传报告服务器的测试报告
        '''
        class EmptyClass(object):
            pass
        
        def __init__(self, name, testtype='个人测试', product=None, notification=None, nfs=None, creator=None, taskid=None, ref_report=None, upload_xmlresult=True, extra=None ):
            '''构造函数
            :param name: 报告名称
            :type name: string
            :param product: 产品信息配置
            :type product: Product
            :param notification: 通知方式配置
            :type notification: Notification
            :param nfs: 网络文件系统配置
            :type nfs: NFS
            :param creator: 创建者，默认为本机用户名
            :type creator: string
            :param taskid: 对应的任务ID
            :type taskid: string
            :param ref_report: 参考测试报告，性能对比测试使用
            :type ref_report: OnlineTestReport
            :param upload_xmlresult: 是否上传XML测试结果文件
            :type upload_xmlresult: boolean
            :param extra: 自定义参数配置
            :type extra: dict
            '''
            if product is None:
                product = Product('Unknown')
            if notification is None:
                notification = Notification()
            if nfs is None:
                nfs = NFS()
            if creator is None:
                creator = getpass.getuser()
            
            self._name = name
            self._product = product
            self._notification = notification
            self._nfs = nfs
            self._creator = creator
            self._ref_report = ref_report
            self._testtype = testtype
            self._taskid = taskid
            self._storage = None
            self._reportid = None
            self._upload_xmlresult = upload_xmlresult
            if extra == None:
                extra = {}
            self._extra = extra
            
        @property
        def storage(self):
            '''测试报告存储接口
            '''
            return self._storage
        
        def begin_report(self):
            '''创建报告
            '''
            req = dict(
                 taskname=self._name, 
                 reporttype='QTA', 
                 product=self._product.name, 
                 version=self._product.version, 
                 testtype=self._testtype, 
                 creator=self._creator, 
                 build=self._product.build, 
                 protocol=self._product.protocol, 
                 mailto=self._notification.receivers, 
                 mailcc='', 
                 installerpath=self._product.path, 
                 maillist_whenfail=self._notification.critical_receivers, 
                 jobid=self._taskid)
            if self._product.stream:
                req['stream'] = self._product.stream
            if self._ref_report:
                req['ref_report_id']=self._ref_report._reportid
            req.update(self._extra)     
            self._reportid = _reportitf.create_report(**req)            
            task_dirname = '%s\\%s\\%s\\%s' % (self._product.name, 
                                              self._testtype, 
                                              datetime.now().strftime("%Y_%m_%d"), 
                                              self._reportid)
            if self._nfs.backend.lower() == 'cfs':
                self._storage = CFSStorage(task_dirname)
            elif self._nfs.backend.lower() == 'tfs':
                if sys.platform != 'win32':
                    raise ValueError("TFS backend is not supported on %s platform" % sys.platform )
                self._storage = TFSStorage(task_dirname, self._nfs.tfs_root)
            else:
                raise ValueError("unsupported NFS backend: '%s'" % self._nfs.backend )
            
            #print 'report created', self.url
            
        def end_report(self):
            '''结束测试执行
            :param passed: 测试是否通过
            :type passed: boolean
            '''
            _reportitf.finish_report(self._reportid, 
                                     when_pass=self._notification.when_success.dumps(), 
                                     when_fail=self._notification.when_failed.dumps(), 
                                     is_normal=1)
                
        def log_record(self, level, tag, msg, record={}):
            '''增加一个记录
            :param level: 日志级别
            :param msg: 日志消息
            :param tag: 日志标签
            :param record: 日志记录信息
            :type level: string
            :type tag: string
            :type msg: string
            :type record: dict
            '''
            if tag == 'Environment' and record.has_key("machine"):
                machineid = record["machine"]
                del record["machine"]
                _reportitf.upload_log(self._reportid, machineid, json.dumps(record), log_type=0, level=1)
            elif tag == 'Environment' and record.has_key("device"):
                _reportitf.upload_log(self._reportid, socket.gethostname(), json.dumps(record), log_type=2, level=1)
            elif tag == 'Loader' and record.has_key("testcases"):
                _reportitf.upload_total_testcase_count(self._reportid, len(record['testcases']))  
            elif tag == 'Loader' and record.has_key("filtered_testcases"):
                for tc, reason in record["filtered_testcases"]:
                    _reportitf.upload_filtered_testcase(self._reportid, tc.test_name, tc.test_name, tc.owner, reason)
            elif tag == 'Loader' and record.has_key("error_testname") and record.has_key("error"):
                error = record["error"]
                lines = error.split('\n')
                error_summary = 'unknown'
                for line in reversed(lines):
                    if line:
                        error_summary = line
                        break
                _reportitf.upload_error_testname(self._reportid, record["error_testname"], error_summary, error)
            else:
                if isinstance(msg, unicode): #msg是用户输入的，需要兼容unicode或UTF8字符串
                    msg = msg.encode('utf8')
                if record.has_key("link_file"):
                    url = self._storage.upload(record["link_file"])
                    log_data = "&nbsp;&nbsp;&nbsp;<a class=\"file-link\" href=\"%s\" style=\"text-decoration: underline;\">%s</a>" % (url, msg)
                else:
                    log_data = msg
                _reportitf.upload_log(self._reportid, tag, log_data, log_type=1, level=3)
                    
        def get_testresult_factory(self):
            '''获取对应的TestResult工厂
            :returns ITestResultFactory
            '''
            return OnlineTestResultFactory(self._reportid, self._storage, self._upload_xmlresult)
        
        @property
        def url(self):
            '''报告的URL路径
            '''
            return _reportitf.get_url(self._reportid)
        
        def dumps(self):
            '''序列化
            '''
            return {
                "reportid": self._reportid,
                "storage": self._storage.dumps(),
                "storage_backend": self._nfs.backend,
                "upload_xmlresult": self._upload_xmlresult,
                "nfs": self._nfs.dumps(),
            }
        
        def loads(self, buf ):
            '''反序列化
            :param buf: 序列化后的数据
            :type buf: picklable object
            '''
            self._reportid = buf["reportid"]
            if buf["storage_backend"] == 'cfs':
                storage_class = CFSStorage
            else:
                storage_class = TFSStorage
            self._storage = self.EmptyClass()
            self._storage.__class__ = storage_class
            self._storage.loads(buf["storage"])
            self._upload_xmlresult = buf["upload_xmlresult"]
            if buf.has_key('nfs'):
                self._nfs = self.EmptyClass()
                self._nfs.__class__ = NFS
                self._nfs.loads(buf['nfs'])
