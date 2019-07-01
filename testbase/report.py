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
import socket
import os
import shutil
import json
import getpass
import locale
import argparse
import xml.dom.minidom as dom
import xml.sax.saxutils as saxutils

from datetime import datetime

from testbase import logger
from testbase import testresult
from testbase.testresult import EnumLogLevel
from testbase.util import smart_text, smart_binary, to_pretty_xml, ensure_binary_stream, \
    codecs_open, get_os_version, get_inner_resource
from testbase.version import version

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

    def log_test_result(self, testcase, testresult):
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

    def is_passed(self):
        '''报告中所有用例是否都通过

        :return: boolean
        '''
        pass

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


class TestReportBase(ITestReport):
    '''TestReport基类
    '''

    def __init__(self):
        '''构造函数
        '''
        self._cases_passed = {}

    def log_test_result(self, testcase, testresult):
        '''记录一个测试结果

        :param testcase: 测试用例
        :type testcase: TestCase
        :param testresult: 测试结果
        :type testresult: TestResult
        '''
        self._cases_passed[testcase.test_name] = testresult.passed

    def is_passed(self):
        '''报告中是否所有用例都通过，兼容已有EmptyTestReport，若用例数为0，也认为不通过
        
        :return: boolean
        '''
        return all(self._cases_passed.values()) and len(self._cases_passed) > 0


class ITestResultFactory(object):
    '''TestResult工厂接口
    '''

    def create(self, testcase):
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

    def __init__(self, result_factory_func=None):
        '''构造函数
        :param result_factory_func: TestResult工厂函数
        :type result_factory_func: Function
        '''
        self._result_factory_func = result_factory_func

    def create(self, testcase):
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


class EmptyTestReport(TestReportBase):
    '''不输出测试报告
    '''

    def __init__(self, result_factory_func=None):
        '''构造函数
        :param result_factory_func: TestResult工厂函数
        :type result_factory_func: callable
        '''
        super(EmptyTestReport, self).__init__()
        self._result_factory_func = result_factory_func

    def get_testresult_factory(self):
        '''获取对应的TestResult工厂
        :returns ITestResultFactory
        '''
        return EmptyTestResultFactory(self._result_factory_func)

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

    def __init__(self, stream):
        '''构造函数
        :param stream: 指定要输出的流设备
        :type stream: file
        '''
        self._stream = stream

    def create(self, testcase):
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
            raise ValueError("invalid fd: %s" % fileno)


class StreamTestReport(TestReportBase):
    '''流形式的测试报告
    '''

    def __init__(self, stream=sys.stdout, error_stream=sys.stderr, output_testresult=False, output_summary=True):
        '''构造函数
        :param stream: 指定要输出的流设备
        :type stream: file
        :param output_testresult: 是否输出测试用例执行的日志
        :type output_testresult: boolean
        :param output_summary: 是否输出执行汇总信息
        :type output_summary: boolean
        '''
        super(StreamTestReport, self).__init__()
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
        # self._write("Total execution time is :%s\n" % str(end_time-self._start_time).split('.')[0])

        if self._output_summary:
            self._write("\n" + "="*60 + "\n")
            self._write("SUMMARY:\n\n")
            self._write(" Totals: %s\t%0.4fs\n\n" % (len(self._failed_testresults) + len(self._passed_testresults),
                                                     (end_time - self._start_time).total_seconds()))

            self._write(" Passed: %s\n" % len(self._passed_testresults))
            for it in self._passed_testresults:
                self._write(" \t%s\t%0.4fs\n" % (it.testcase.test_name,
                                                 it.end_time - it.begin_time))
            self._write("\n")

            self._write(" Failed: %s\n" % len(self._failed_testresults))
            for it in self._failed_testresults:
                self._write_err(" \t%s\t%0.4fs\n" % (it.testcase.test_name,
                                                     it.end_time - it.begin_time))

    def log_test_result(self, testcase, testresult):
        '''记录一个测试结果
        :param testcase: 测试用例
        :type testcase: TestCase
        :param testresult: 测试结果
        :type testresult: TestResult
        '''
        super(StreamTestReport, self).log_test_result(testcase, testresult)
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


class XMLTestResultFactory(ITestResultFactory):
    '''XML形式TestResult工厂
    '''

    def create(self, testcase):
        '''创建TestResult对象
        :param testcase: 测试用例
        :type testcase: TestCase
        :return TestResult
        '''
        return testresult.XmlResult(testcase)


class XMLTestReport(TestReportBase):
    '''XML形式的测试报告
    '''

    def __init__(self):
        '''构造函数
        '''
        super(XMLTestReport, self).__init__()
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
        os_ver = get_os_version()
        envxml = dom.parseString(xmltpl % (hostname, os_ver))
        self._runrstnode.appendChild(envxml.childNodes[0])

    def end_report(self):
        '''结束测试执行
        :param passed: 测试是否通过
        :type passed: boolean
        '''
        time_end = datetime.now()
        timexml = "<RunTime><StartTime>%s</StartTime><EndTime>%s</EndTime><Duration>%s</Duration></RunTime>"
        timexml = timexml % (self._time_start.strftime("%Y-%m-%d %H:%M:%S"), time_end.strftime("%Y-%m-%d %H:%M:%S"), str(time_end - self._time_start).split('.')[0])
        timenodes = dom.parseString(timexml)
        self._runrstnode.appendChild(timenodes.childNodes[0])

        xmldata = to_pretty_xml(self._xmldoc)
        with codecs_open('TestReport.xml', 'wb') as fd:
            fd.write(xmldata)
        test_repor_xsl = get_inner_resource("qta_statics", "TestReport.xsl")
        shutil.copy(test_repor_xsl, os.getcwd())
        test_result_xsl = get_inner_resource("qta_statics", "TestResult.xsl")
        shutil.copy(test_result_xsl, os.getcwd())

    def log_test_result(self, testcase, testresult):
        '''记录一个测试结果
        :param testcase: 测试用例
        :type testcase: TestCase
        :param testresult: 测试结果
        :type testresult: XmlResult
        '''
        super(XMLTestReport, self).log_test_result(testcase, testresult)
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
                with codecs_open(logfile, 'wb') as fd:
                    fd.write(smart_binary(record['error']))

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
        with codecs_open(log_file, 'wb') as fd:
            fd.write(smart_binary(error))

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

    def create(self, testcase):
        '''创建TestResult对象
        :param testcase: 测试用例
        :type testcase: TestCase
        :return TestResult
        '''
        return testresult.JSONResult(testcase)


class JSONTestReportBase(TestReportBase):
    '''JSON格式的测试报告基类
    '''

    def __init__(self, title="调试测试"):
        '''构造函数

        :param title: 报告标题
        :type title: str
        '''
        super(JSONTestReportBase, self).__init__()
        self._logs = []
        self._filtered_tests = []
        self._load_errors = []
        self._passed_tests = {}
        self._failed_tests = {}
        self._data = {
            "version": "1.0",
            "summary": {
                "tool": "QTA",
                "title": title,
                "environment" : {}
            },
            "logs": self._logs,
            "filtered_tests": self._filtered_tests,
            "load_errors": self._load_errors,
            "passed_tests" : self._passed_tests,
            "failed_tests" : self._failed_tests
        }
        self._testcase_names = set()
        self._testcase_total_run = 0

    def begin_report(self):
        '''开始测试执行
        '''
        self._data["summary"]["start_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._data["summary"]["environment"]["hostname"] = socket.gethostname()
        self._data["summary"]["environment"]["os"] = get_os_version()
        self._data["summary"]["environment"]["qtaf_version"] = version
        python_version = "%s.%s.%s[%s]" % (sys.version_info[0],
                                           sys.version_info[1],
                                           sys.version_info[2],
                                           sys.platform)
        self._data["summary"]["environment"]["python_version"] = python_version

    def end_report(self):
        '''结束测试执行
        :param passed: 测试是否通过
        :type passed: boolean
        '''
        self._data["summary"]["testcase_total_run"] = self._testcase_total_run
        self._data["summary"]["testcase_total_count"] = len(self._cases_passed)
        self._data["summary"]["testcase_passed"] = len(self._passed_tests)
        self._data["summary"]["succeed"] = self.is_passed()
        self._data["summary"]["end_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def get_default_test_info(self, test_case, test_result):
        test_result_data = test_result.get_data()
        test_info = {"description": test_case.test_doc,
                     "owner": test_case.owner,
                     "priority": test_case.priority,
                     "status": test_case.status,
                     "timeout": test_case.timeout,
                     "failed_info": "",
                     "start_time" : test_result_data["start_time"],
                     "end_time" : test_result_data["end_time"],
                     "records" : []}
        return test_info

    def log_test_result(self, testcase, testresult):
        '''记录一个测试结果
        :param testcase: 测试用例
        :type testcase: TestCase
        :param testresult: 测试结果
        :type testresult: TestResult
        '''
        super(JSONTestReportBase, self).log_test_result(testcase, testresult)
        self._testcase_total_run += 1

        test_name = testcase.test_name
        if test_name in self._failed_tests:
            test_info = self._failed_tests.pop(test_name)
        else:
            test_info = self.get_default_test_info(testcase, testresult)
        test_info["records"].append(testresult.get_file())

        if testresult.passed:
            self._passed_tests[test_name] = test_info
        else:
            test_info["failed_info"] = testresult.get_data()["failed_info"]
            self._failed_tests[test_name] = test_info

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


class JSONTestReport(JSONTestReportBase):
    '''JSON格式的测试报告
    '''

    def __init__(self, fd, title="调试测试"):
        '''构造函数

        :param fd: 输出流
        :type fd: file object
        :param title: 报告标题
        :type title: str
        '''
        self._fd = fd
        super(JSONTestReport, self).__init__(title)

    def end_report(self):
        '''结束测试执行
        '''
        super(JSONTestReport, self).end_report()
        json.dump(self._data, self._fd)

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
        parser.add_argument("--title", help="report title", default="Debug test report")
        parser.add_argument("-o", "--output", help="output file name", required=True)
        return parser

    @classmethod
    def parse_args(cls, args_string):
        '''通过命令行参数构造对象
        
        :returns: 测试报告
        :rtype: cls
        '''
        args = cls.get_parser().parse_args(args_string)
        fd = codecs_open(args.output, 'w', encoding="utf-8")
        return cls(fd, title=args.title)


class HtmlTestReport(JSONTestReportBase):
    """html test report
    """

    def __init__(self, title="调试测试", displays=["failed", "error"]):
        super(HtmlTestReport, self).__init__(title=title)
        self._data["displays"] = displays

    def get_testresult_factory(self):
        '''获取对应的TestResult工厂
        :returns ITestResultFactory
        '''
        return HtmlTestResultFactory()

    def end_report(self):
        super(HtmlTestReport, self).end_report()
        data = json.dumps(self._data)
        content = "var qta_report_data = %s" % data
        with codecs_open("qta-report.js", "w", encoding="utf-8") as fd:
            fd.write(content)

        qta_report_html = get_inner_resource("qta_statics", "qta-report.html")
        shutil.copy(qta_report_html, os.getcwd())

    @classmethod
    def get_parser(cls):
        '''获取命令行参数解析器（如果实现）

        :returns: 解析器对象
        :rtype: argparse.ArgumentParser
        '''
        parser = argparse.ArgumentParser(usage=report_usage)
        parser.add_argument("--title", help="report title", default="Debug test report")
        parser.add_argument("--display", action="append", choices=["all", "failed", "passed", "filtered", "error"], dest="displays",
                            default=[], help="default test result types to display when opening the report, multiple options accepted")
        return parser

    @classmethod
    def parse_args(cls, args_string):
        '''通过命令行参数构造对象
        
        :returns: 测试报告
        :rtype: cls
        '''
        args = cls.get_parser().parse_args(args_string)
        displays = args.displays or ["failed", "error"]
        return cls(title=args.title, displays=displays)


class HtmlTestResultFactory(ITestResultFactory):
    """html test result factory
    """

    def create(self, testcase):
        return testresult.HtmlResult(testcase)



class TestListOutputBase(object):
    """base class of test case list output
    """

    def __init__(self, output_file):
        if output_file is None:
            self._fd = None
            self._close_fd = False
            self._output_func = logger.info
        else:
            self._fd = codecs_open(output_file, "w")
            self._close_fd = True
            self._output_func = lambda x: self._fd.write(x + "\n")

    def output_normal_tests(self, normal_tests):
        raise NotImplementedError

    def output_filtered_tests(self, filtered_tests):
        raise NotImplementedError

    def output_error_tests(self, error_tests):
        raise NotImplementedError

    def end_output(self):
        if self._close_fd:
            self._fd.close()


class StreamTestListOutput(TestListOutputBase):
    """stream output
    """

    def output_normal_tests(self, normal_tests):
        self._output_func("\n======================")
        self._output_func("%s normal tests:" % len(normal_tests))
        self._output_func("======================")
        for test in normal_tests:
            test_info = self.stream_format_test(test)
            self._output_func(test_info)

    def output_filtered_tests(self, filtered_tests):
        self._output_func("\n======================")
        self._output_func("%s filtered tests:" % len(filtered_tests))
        self._output_func("======================")
        for test, reason in filtered_tests:
            test_info = self.stream_format_test(test) + ", reason:" + reason
            self._output_func(test_info)

    def output_error_tests(self, error_tests):
        self._output_func("\n======================")
        self._output_func("%s error tests:" % len(error_tests))
        self._output_func("======================")
        for test_name, error in error_tests:
            test_info = "cannot load test \"%s\"" % test_name + ", error:\n" + error
            self._output_func(test_info)

    def stream_format_test(self, test):
        desc = ("%s/%s" % (test.priority, test.status))
        test_info = "%-12s " % desc
        test_info += "timeout=%-3s " % test.timeout
        test_info += "%-10s " % test.owner
        test_info += "%s" % test.test_name
        return test_info


class LineTestListOutput(TestListOutputBase):
    """output test list as single line
    """

    def output_normal_tests(self, normal_tests):
        self._output_func("normal test set:\n")
        content = " ".join(map(lambda x: x.test_name, normal_tests))
        self._output_func(content)

    def output_filtered_tests(self, filtered_tests):
        self._output_func("filtered test set:\n")
        content = " ".join(map(lambda x: x[0].test_name, filtered_tests))
        self._output_func(content)

    def output_error_tests(self, error_tests):
        self._output_func("error test set:\n")
        for test_name, error in error_tests:
            test_info = "\"%s\"" % test_name + ", error:\n" + error
            self._output_func(test_info)


test_list_types = {"stream" : StreamTestListOutput,
                   "line" : LineTestListOutput}

