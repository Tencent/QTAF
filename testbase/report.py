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

import sys
import codecs
import socket
import os
import shutil
import json
import getpass
import locale
import argparse
import pkg_resources
import six
import xml.dom.minidom as dom
import xml.sax.saxutils as saxutils

from datetime import datetime

from testbase import testresult
from testbase.testresult import EnumLogLevel
from testbase.util import smart_text, smart_binary, to_pretty_xml, ensure_binary_stream
    
REPORT_ENTRY_POINT = "qtaf.report"
report_types = {}
os_encoding = locale.getdefaultlocale()[1]
report_usage = 'runtest <test ...> --report-type <report-type> [--report-args "<report-args>"]'
        
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

    def log_loaded_tests(self, loader, testcases):
        '''记录加载成功的用例

        :param loader: 用例加载器
        :type loader: TestLoader
        :param testcases: 测试用例列表
        :type testcases: list
        '''
        pass

    def log_filtered_test(self, loader, testcase, reason):
        '''记录一个被过滤的测试用例

        :param loader: 用例加载器
        :type loader: TestLoader
        :param testcase: 测试用例
        :type testcase: TestCase
        :param reason: 过滤原因
        :type reason: str
        '''
        pass

    def log_load_error(self, loader, name, error):
        '''记录一个加载失败的用例或用例集

        :param loader: 用例加载器
        :type loader: TestLoader
        :param name: 名称
        :type name: str
        :param error: 错误信息
        :type error: str
        '''
        pass

    def log_test_target(self, test_target):
        '''记录被测对象

        :param test_target: 被测对象详情
        :type test_target: any
        '''
        pass

    def log_resource(self, res_type, resource):
        '''记录测试使用的资源

        :param res_type: 资源类型
        :type res_type: str
        :param resource: 资源详情
        :type resource: dict
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

    @classmethod
    def get_parser(cls):
        '''获取命令行参数解析器（如果实现）

        :returns: 解析器对象
        :rtype: argparse.ArgumentParser
        '''
        raise NotImplementedError()

    @classmethod
    def parse_args(cls, args_string):
        '''通过命令行参数构造对象
        
        :returns: 测试报告
        :rtype: cls
        '''
        raise NotImplementedError()
        
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
        self._is_passed = True
    
    def get_testresult_factory(self):
        '''获取对应的TestResult工厂
        :returns ITestResultFactory
        '''
        return EmptyTestResultFactory(self._result_factory_func)

    def log_test_result(self, testcase, testresult ):
        '''记录一个测试结果

        :param testcase: 测试用例
        :type testcase: TestCase
        :param testresult: 测试结果
        :type testresult: TestResult
        '''
        if not testresult.passed:
            self._is_passed = False
    
    @property
    def passed(self):
        '''测试是否通过
        '''
        return self._is_passed

    @classmethod
    def get_parser(cls):
        '''获取命令行参数解析器（如果实现）

        :returns: 解析器对象
        :rtype: argparse.ArgumentParser
        '''
        return argparse.ArgumentParser(usage=report_usage)

    @classmethod
    def parse_args(cls, args_string):
        '''通过命令行参数构造对象
        
        :returns: 测试报告
        :rtype: cls
        '''
        return EmptyTestReport()

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
        self._stream, encoding = ensure_binary_stream(stream)
        self._err_stream, _ = ensure_binary_stream(error_stream)
        self._write = lambda x: self._stream.write(smart_binary(x, encoding=encoding))
        self._write_err = lambda x: self._err_stream.write(smart_binary(x, encoding=encoding))
                    
        self._output_testresult = output_testresult
        self._output_summary = output_summary
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
    
    def log_filtered_test(self, loader, testcase, reason):
        '''记录一个被过滤的测试用例
        :param loader: 用例加载器
        :type loader: TestLoader
        :param testcase: 测试用例
        :type testcase: TestCase
        :param reason: 过滤原因
        :type reason: str
        '''
        self._write("filtered test case: %s (reason: %s)\n" % (testcase.test_name, reason))

    def log_load_error(self, loader, name, error):
        '''记录一个加载失败的用例或用例集
        :param loader: 用例加载器
        :type loader: TestLoader
        :param name: 名称
        :type name: str
        :param error: 错误信息
        :type error: str
        '''
        line = ""
        for line in reversed(error.split("\n")):
            if line.strip():
                break
        self._write_err("load test failed: %s (error: %s)\n" % (name, line))

    def get_testresult_factory(self):
        '''获取对应的TestResult工厂
        :returns ITestResultFactory
        '''
        if self._output_testresult:
            return StreamTestResultFactory(self._stream)
        else:
            return EmptyTestResultFactory()
        
    @classmethod
    def get_parser(cls):
        '''获取命令行参数解析器（如果实现）

        :returns: 解析器对象
        :rtype: argparse.ArgumentParser
        '''
        parser = argparse.ArgumentParser(usage=report_usage)
        parser.add_argument("--no-output-result", action="store_true", help="don't output detail result of test cases")
        parser.add_argument("--no-summary", action="store_true", help="don't output summary information")
        return parser

    @classmethod
    def parse_args(cls, args_string):
        '''通过命令行参数构造对象
        
        :returns: 测试报告
        :rtype: cls
        '''
        args = cls.get_parser().parse_args(args_string)
        return cls(
            output_testresult=not args.no_output_result,
            output_summary=not args.no_summary)


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
    <xsl:for-each select="LoadTestError">
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

<xsl:template name="break_lines">
  <xsl:param name="text" select="string(.)"/>
  <xsl:choose>
    <xsl:when test="contains($text, '&#xa;')">
      <xsl:value-of select="substring-before($text, '&#xa;')"/>
      <br/>
      <xsl:call-template name="break_lines">
        <xsl:with-param 
          name="text" 
          select="substring-after($text, '&#xa;')"
        />
      </xsl:call-template>
    </xsl:when>
    <xsl:otherwise>
      <xsl:value-of select="$text"/>
    </xsl:otherwise>
  </xsl:choose>
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
    <td>
        <xsl:call-template name="break_lines" />
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

if six.PY3:
    maketrans_func = str.maketrans
else:
    import string
    maketrans_func = string.maketrans

class XMLTestResultFactory(ITestResultFactory):
    '''XML形式TestResult工厂
    '''
    BAD_CHARS = r'\/*?:<>"|~'
    TRANS = maketrans_func(BAD_CHARS, '='*len(BAD_CHARS))
                    
    def create(self, testcase ):
        '''创建TestResult对象
        :param testcase: 测试用例
        :type testcase: TestCase
        :return TestResult
        '''
        time_str=datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        if six.PY2:
            translated_name = smart_binary(testcase.test_name).translate(self.TRANS)
        else:
            translated_name = smart_text(testcase.test_name).translate(self.TRANS)
        filename = '%s_%s.xml' % (translated_name, time_str)
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
            with os.popen("ver") as pipe:
                osver = smart_binary(pipe.read()) # dom parse needs utf-8
        else:
            osver = smart_binary(str(os.uname()))  # @UndefinedVariable
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
        
        xmldata = to_pretty_xml(self._xmldoc)
        with codecs.open('TestReport.xml', 'w', encoding="utf-8") as fd:
            fd.write(xmldata)
        with codecs.open('TestReport.xsl', 'w', encoding="utf-8") as fd:
            fd.write(smart_text(REPORT_XSL))
        with codecs.open('TestResult.xsl', 'w', encoding="utf-8") as fd:
            fd.write(smart_text(RESULT_XLS))   
    
    def log_test_result(self, testcase, testresult ):
        '''记录一个测试结果
        :param testcase: 测试用例
        :type testcase: TestCase
        :param testresult: 测试结果
        :type testresult: XmlResult
        '''
        casemark = saxutils.escape(testcase.test_doc)
        nodestr = """<TestResult result="%s" log="%s" status="%s">%s</TestResult>
        """ % (testresult.passed, testresult.file_path, testcase.status, casemark)
        doc2 = dom.parseString(smart_binary(nodestr))
        resultNode = doc2.childNodes[0]
        resultNode.setAttribute("name", smart_text(saxutils.escape(testcase.test_name)))
        resultNode.setAttribute("owner", smart_text(saxutils.escape(testcase.owner)))
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
            if 'error_testname' in record and 'error' in record:
                testname = record['error_testname']
                mdfailsnode = self._xmldoc.createElement("LoadFailure")
                self._runrstnode.appendChild(mdfailsnode)
                logfile = '%s.log' % testname
                xmltpl = """<Module name="%s" log="%s"/>""" % (testname, logfile)
                mdfailsnode.appendChild(dom.parseString(xmltpl).childNodes[0])
                with open(logfile, 'w') as fd:
                    fd.write(record['error'])
                
    def log_filtered_test(self, loader, testcase, reason):
        '''记录一个被过滤的测试用例
        :param loader: 用例加载器
        :type loader: TestLoader
        :param testcase: 测试用例
        :type testcase: TestCase
        :param reason: 过滤原因
        :type reason: str
        '''
        nodestr = """<FilterTest name="%s" reason="%s"></FilterTest>
        """ % (
            smart_text(saxutils.escape(testcase.test_name)),
            smart_text(saxutils.escape(reason))
        )
        doc2 = dom.parseString(nodestr)
        filterNode = doc2.childNodes[0]
        self._runrstnode.appendChild(filterNode)

    def log_load_error(self, loader, name, error):
        '''记录一个加载失败的用例或用例集
        :param loader: 用例加载器
        :type loader: TestLoader
        :param name: 名称
        :type name: str
        :param error: 错误信息
        :type error: str
        '''
        log_file = "%s.log" % name
        nodestr = """<LoadTestError name="%s" log="%s"></LoadTestError>
        """ % (
            smart_text(saxutils.escape(name)),
            log_file,
        )
        doc2 = dom.parseString(nodestr)
        errNode = doc2.childNodes[0]
        self._runrstnode.appendChild(errNode)
        with open(log_file, 'w') as fd:
            fd.write(error)

    def get_testresult_factory(self):
        '''获取对应的TestResult工厂
        :returns ITestResultFactory
        '''
        return self._result_factory
    
    @classmethod
    def get_parser(cls):
        '''获取命令行参数解析器（如果实现）

        :returns: 解析器对象
        :rtype: argparse.ArgumentParser
        '''
        return argparse.ArgumentParser(usage=report_usage)

    @classmethod
    def parse_args(cls, args_string):
        '''通过命令行参数构造对象
        
        :returns: 测试报告
        :rtype: cls
        '''
        return cls()

class JSONTestResultFactory(ITestResultFactory):
    '''JSON形式TestResult工厂
    '''
                    
    def create(self, testcase ):
        '''创建TestResult对象
        :param testcase: 测试用例
        :type testcase: TestCase
        :return TestResult
        '''
        return testresult.JSONResult(testcase)

class JSONTestReport(ITestReport):
    '''JSON格式的测试报告
    '''
    def __init__(self, name="调试测试报告", fd=None ):
        '''构造函数

        :param name: 报告名
        :type name: str
        :param fd: 输出流
        :type fd: file object
        '''
        if fd is None:
            self._fd = sys.stdout
        else:
            self._fd = fd
        self._results = []
        self._logs = []
        self._filtered_tests = []
        self._load_errors = []
        self._testcases = []
        self._data = {
            "version": "1.0",
            "summary": {
                "tool": "QTA",
                "name": name,
            },
            "results": self._results,
            "logs": self._logs,
            "filtered_tests": self._filtered_tests,
            "load_errors": self._load_errors,
            "loaded_testcases": self._testcases
        }
        self._testcase_total = 0
        self._testcase_passed = 0

    def begin_report(self):
        '''开始测试执行
        '''
        self._data["summary"]["start_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def end_report(self):
        '''结束测试执行
        :param passed: 测试是否通过
        :type passed: boolean
        '''
        self._data["summary"]["testcase_total"] = self._testcase_total
        self._data["summary"]["testcase_passed"] = self._testcase_passed
        self._data["summary"]["succeed"] = self._testcase_passed == self._testcase_total
        self._data["summary"]["end_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        json.dump(self._data, self._fd)
        
    def log_test_result(self, testcase, testresult ):
        '''记录一个测试结果
        :param testcase: 测试用例
        :type testcase: TestCase
        :param testresult: 测试结果
        :type testresult: TestResult
        '''
        self._testcase_total += 1
        if testresult.passed:
            self._testcase_passed += 1
        self._results.append(testresult.get_data())
    
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
        self._logs.append({
            "level": level,
            "tag": tag,
            "message": msg,
            "record": record
        })

    def log_loaded_tests(self, loader, testcases):
        '''记录加载成功的用例

        :param loader: 用例加载器
        :type loader: TestLoader
        :param testcases: 测试用例列表
        :type testcases: list
        '''
        self._testcases += [
            {"name": testcase.test_name} 
            for testcase in testcases
        ]

    def log_filtered_test(self, loader, testcase, reason):
        '''记录一个被过滤的测试用例
        :param loader: 用例加载器
        :type loader: TestLoader
        :param testcase: 测试用例
        :type testcase: TestCase
        :param reason: 过滤原因
        :type reason: str
        '''
        self._filtered_tests.append({
            "name": testcase.test_name,
            "reason": reason
        })

    def log_load_error(self, loader, name, error):
        '''记录一个加载失败的用例或用例集
        :param loader: 用例加载器
        :type loader: TestLoader
        :param name: 名称
        :type name: str
        :param error: 错误信息
        :type error: str
        '''
        self._load_errors.append({
            "name": name,
            "error": error
        })
    
    def get_testresult_factory(self):
        '''获取对应的TestResult工厂
        :returns ITestResultFactory
        '''
        return JSONTestResultFactory()

    @classmethod
    def get_parser(cls):
        '''获取命令行参数解析器（如果实现）

        :returns: 解析器对象
        :rtype: argparse.ArgumentParser
        '''
        parser = argparse.ArgumentParser(usage=report_usage)
        parser.add_argument("--name", help="report title", default="Debug test report")
        parser.add_argument("-o", "--output", help="output file path, can be stdout & stderr", default="stdout")
        return parser

    @classmethod
    def parse_args(cls, args_string):
        '''通过命令行参数构造对象
        
        :returns: 测试报告
        :rtype: cls
        '''
        args = cls.get_parser().parse_args(args_string)
        if args.output == 'stdout':
            fd = sys.stdout
        elif args.output == 'stderr':
            fd = sys.stderr
        else:
            fd = open(args.output, 'w')
        return cls(
            name=args.name,
            fd=fd)


def __init_report_types():
    global report_types
    if report_types:
        return
    report_types.update({
        "empty":  EmptyTestReport,
        "stream": StreamTestReport,
        "xml":    XMLTestReport,
        "json":   JSONTestReport,
    })

    # Register other `ITestReport` implementiations from entry points 
    for ep in pkg_resources.iter_entry_points(REPORT_ENTRY_POINT):
        if ep.name not in report_types:
            report_types[ep.name] = ep.load()

__init_report_types()
del __init_report_types
