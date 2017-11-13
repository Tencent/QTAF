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
    
os_encoding = locale.getdefaultlocale()[1]

def _to_unicode( s ):
    '''将任意字符串转换为unicode编码
    '''
    if isinstance(str, unicode):
        return s
    try:
        return s.decode('utf8')
    except UnicodeDecodeError:
        return s.decode(os_encoding)
        
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
    def __init__(self, stream=sys.stdout, error_stream=sys.stderr, output_testresult=False, output_summary=True ):
        '''构造函数
        :param stream: 指定要输出的流设备
        :type stream: file
        :param output_testresult: 是否输出测试用例执行的日志
        :type output_testresult: boolean
        :param output_summary: 是否输出执行汇总信息
        :type output_summary: boolean
        '''
        self._stream = stream
        self._err_stream = error_stream
        self._output_testresult = output_testresult
        self._output_summary = output_summary
        if stream.encoding and stream.encoding != 'utf8':
            self._write = lambda x: self._stream.write(x.decode('utf8').encode(stream.encoding))
            self._write_err = lambda x: self._err_stream.write(x.decode('utf8').encode(stream.encoding))
        else:
            self._write = self._stream.write
            self._write_err = self._err_stream.write
        self._passed_testresults = []
        self._failed_testresults = [] 
            
    def begin_report(self):
        '''开始测试执行
        '''
        self._start_time = datetime.now()
        self._write("Test runs at:%s.\n" % self._start_time.strftime("%Y-%m-%d %H:%M:%S"))
    
    def end_report(self):
        '''结束测试执行
        :param passed: 测试是否通过
        :type passed: boolean
        '''
        end_time = datetime.now()
        self._write("Test ends at:%s.\n" % end_time.strftime("%Y-%m-%d %H:%M:%S"))
        #self._write("Total execution time is :%s\n" % str(end_time-self._start_time).split('.')[0])
    
        if self._output_summary:
            self._write("\n" + "="*60 + "\n")
            self._write("SUMMARY:\n\n")
            self._write(" Totals: %s\t%0.4fs\n\n" % (len(self._failed_testresults) + len(self._passed_testresults),
                                                     (end_time-self._start_time).total_seconds()))
            
            self._write(" Passed: %s\n" % len(self._passed_testresults))
            for it in self._passed_testresults:
                self._write(" \t%s\t%0.4fs\n" % (it.testcase.test_name,
                                                 it.end_time-it.begin_time))
            self._write("\n")
            
            self._write(" Failed: %s\n" % len(self._failed_testresults))
            for it in self._failed_testresults:
                self._write_err(" \t%s\t%0.4fs\n" % (it.testcase.test_name,
                                                     it.end_time-it.begin_time))
            
    def log_test_result(self, testcase, testresult ):
        '''记录一个测试结果
        :param testcase: 测试用例
        :type testcase: TestCase
        :param testresult: 测试结果
        :type testresult: TestResult
        '''
        if testresult.passed:
            self._passed_testresults.append(testresult)
        else:
            self._failed_testresults.append(testresult)
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
    
