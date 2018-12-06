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
测试结果模块

参考logging模块的设计，使用示例如下::

    result = TestResult()
    result.add_handler(StreamResultHandler())
    result.begin_test()
    result.start_step('a step')
    result.info('test')
    result.end_test()

其中result.info接口可以传record扩展信息，比如::

    result.error('', '异常发生', traceback=traceback.format_exc())
        
同logger一样，TestResult对象保证对所有的ITestResultHandler的调用都是线程安全的，可以通过实现
ITestResultHandler来实现一个新的Handler，详细请参考ITestResultHandler接口

'''

import codecs
import sys
import traceback
import time
import xml.dom.minidom as dom
import xml.parsers.expat as xmlexpat
import xml.sax.saxutils as saxutils
import socket
import threading
import os
import locale
import json
import six

from testbase import context
from testbase.util import smart_text, get_thread_traceback, get_method_defined_class, \
to_pretty_xml, smart_binary, ensure_binary_stream

    
os_encoding = locale.getdefaultlocale()[1]

class EnumLogLevel(object):
    '''日志级别
    '''
    DEBUG = 10
    INFO = 20
    Environment = 21  #测试环境相关信息， device/devices表示使用的设备、machine表示执行的机器
    ENVIRONMENT = Environment
    RESOURCE = 22
    
    WARNING = 30
    ERROR = 40
    ASSERT = 41 #断言失败，actual/expect/code_location
    CRITICAL = 60
    APPCRASH = 61 #测试目标Crash
    TESTTIMEOUT = 62 #测试执行超时
    RESNOTREADY = 69 #当前资源不能满足测试执行的要求

levelname = {}
for name in EnumLogLevel.__dict__:
    value = EnumLogLevel.__dict__[name]
    if isinstance(value, int):
        levelname[value] = name
    
def _convert_timelength(sec):
    h = int(sec / 3600)
    sec -= h * 3600
    m = int(sec / 60)
    sec -= m * 60
    return (h, m, sec)

def smart_text_by_lines( s ):
    '''将任意字符串转换为UTF-8编码
    '''
    lines = []
    for line in s.split('\n'):
        lines.append(smart_text(line))
    return '\n'.join(lines)

class TestResultBase(object):
    '''测试结果基类
    
    此类的职责如下：
    1、提供测试结果基本接口
    2、保证线程安全
    2、测试是否通过之逻辑判断
    '''
    def __init__(self):
        '''构造函数
        '''
        self.__lock = threading.RLock()
        self.__steps_passed = [True] #预设置一个，以防用例中没调用startStep
        self.__curr_step = 0
        self.__accept_result = False
        self.__testcase = None
        self.__begin_time = None
        self.__end_time = None
        self.__error_level = 0
        
    @property
    def testcase(self):
        '''对应的测试用例
        :returns: TestCase
        '''
        return self.__testcase
        
    @property
    def passed(self):
        '''测试是否通过
        
        :returns: True or False
        '''
        if six.PY3:
            import functools
            reduce_func = functools.reduce
        else:
            reduce_func = reduce
        return reduce_func(lambda x,y: x and y, self.__steps_passed)
    
    @property
    def failed_reason(self):
        '''用例测试不通过的错误原因
        
        :returns: str
        '''
        if self.__error_level:
            return levelname.get(self.__error_level, 'unknown')
        else:
            return ''
        
    @property
    def begin_time(self):
        '''测试用例开始时间
        
        :returns: float
        '''
        return self.__begin_time
    
    @property
    def end_time(self):
        '''测试用例结束时间
        
        :returns: float
        '''
        return self.__end_time
        
    def begin_test(self, testcase ):
        '''开始执行测试用例
        
        :param testcase: 测试用例
        :type testcase: TestCase
        '''
        with self.__lock:
            if self.__accept_result:
                raise RuntimeError("此时不可调用begin_test")
            self.__accept_result = True
            self.__begin_time = time.time()
            self.handle_test_begin(testcase)
            self.__testcase = testcase
        
    def end_test(self):
        '''结束执行测试用例
        '''
        with self.__lock:
            if not self.__accept_result:
                raise RuntimeError("此时不可调用end_test")
            self.handle_step_end(self.__steps_passed[self.__curr_step])
            self.__end_time = time.time()
            self.handle_test_end(self.passed) #防止没有一个步骤
            self.__accept_result = False
    
    def begin_step(self, msg ):
        '''开始一个测试步骤
        
        :param msg: 测试步骤名称
        :type msg: string
        '''
        with self.__lock:
            if not self.__accept_result:
                raise RuntimeError("此时不可调用begin_step")
            if len(self.__steps_passed) != 1:
                self.handle_step_end(self.__steps_passed[self.__curr_step])
            self.__steps_passed.append(True)
            self.__curr_step += 1
            self.handle_step_begin(msg)
    
    def log_record(self, level, msg, record=None, attachments=None ):
        '''处理一个日志记录
        
        :param level: 日志级别，参考EnumLogLevel
        :type level: string
        :param msg: 日志消息
        :type msg: string
        :param record: 日志记录
        :type record: dict
        :param attachments: 附件
        :type attachments: dict
        '''
        if record is None:
            record = {}
        if attachments is None:
            attachments = {}
        if not isinstance(msg, six.string_types):
            raise ValueError("msg='%r'必须是string类型" % msg)
        msg = smart_text(msg)
        if level >= EnumLogLevel.ERROR:
                self.__steps_passed[self.__curr_step] = False
                if level > self.__error_level:
                    self.__error_level = level
                extra_record, extra_attachments = self._get_extra_fail_record_safe()
                record.update(extra_record)
                attachments.update(extra_attachments)
                
        with self.__lock:
            if not self.__accept_result:
                return
            self.handle_log_record(level, msg, record, attachments)
        
    def _get_extra_fail_record_safe(self,timeout=300):
        '''使用线程调用测试用例的get_extra_fail_record
        '''
        def _run(outputs, errors):
            try:
                outputs.append(context.current_testcase().get_extra_fail_record())
            except:
                errors.append(traceback.format_exc())
                
                
        errors = []
        outputs = []
        t = threading.Thread(target=_run, args=(outputs, errors))
        t.daemon = True
        t.start()
        t.join(timeout)
        extra_record, extra_attachments = {}, {}
        with self.__lock:
            if t.is_alive():
                stack=get_thread_traceback(t)
                self.handle_log_record(EnumLogLevel.ERROR, '测试失败时获取其他额外错误信息超过了指定时间：%ds' % timeout,
                                       {'traceback':stack}, 
                                       {})
            else:
                if errors:
                    self.handle_log_record(EnumLogLevel.ERROR, '测试失败时获取其他额外错误信息失败', 
                                          {'traceback':errors[0]}, {})
                else:
                    record_info = outputs[0]
                    if isinstance(record_info, (tuple,list)) and len(record_info) == 2:
                        extra_record, extra_attachments = record_info
                    else:
                        cls = get_method_defined_class(self.testcase.get_extra_fail_record)
                        if cls.__module__ == '__main__':
                            class_path = cls.__name__
                        else:
                            class_path = "%s.%s" % (cls.__module__,cls.__name__)
                        raise RuntimeError("%s.get_extra_fail_record must return a 2 elements tuple" % class_path)
        return extra_record, extra_attachments

    def debug(self, msg, record=None, attachments=None):
        '''处理一个DEBUG日志
        '''
        self.log_record(EnumLogLevel.DEBUG, msg, record, attachments)
    
    def info(self, msg,  record=None, attachments=None):
        '''处理一个INFO日志
        '''
        self.log_record(EnumLogLevel.INFO, msg, record, attachments)
    
    def warning(self, msg,  record=None, attachments=None):
        '''处理一个WARNING日志
        '''
        self.log_record(EnumLogLevel.WARNING, msg, record, attachments)
    
    def error(self, msg,  record=None, attachments=None):
        '''处理一个ERROR日志
        '''
        self.log_record(EnumLogLevel.ERROR, msg, record, attachments)
    
    def exception(self, msg,  record=None, attachments=None):
        '''处理一个DEBUG日志
        '''
        if record is None:
            record = {}
        record['traceback'] = traceback.format_exc()
        self.log_record(EnumLogLevel.CRITICAL, msg, record, attachments)
                
    def handle_test_begin(self, testcase ):
        '''处理一个测试用例执行的开始
        
        :param testcase: 测试用例
        :type testcase: TestCase
        '''
        pass
            
    def handle_test_end(self, passed ):
        '''处理一个测试用例执行的结束
        
        :param passed: 测试用例是否通过
        :type passed: boolean
        '''
        pass
        
    def handle_step_begin(self, msg ):
        '''处理一个测试步骤的开始
        
        :param msg: 测试步骤名称
        :type msg: string
        '''
        pass
        
    def handle_step_end(self, passed ):
        '''处理一个测试步骤的结束
        
        :param passed: 测试步骤是否通过
        :type passed: boolean
        '''
        pass
    
    def handle_log_record(self, level, msg, record, attachments ):
        '''处理一个日志记录
        
        :param level: 日志级别，参考EnumLogLevel
        :type level: string
        :param msg: 日志消息
        :type msg: string
        :param record: 日志记录
        :type record: dict
        :param attachments: 附件
        :type attachments: dict
        '''
        pass
    

class EmptyResult(TestResultBase):
    '''不输出
    '''
    pass

class StreamResult(TestResultBase):
    '''测试用例stream输出
    '''
    
    _seperator1 = "-" * 40 + "\n"
    _seperator2 = "=" * 60 + "\n"
    
    def __init__(self, stream=sys.stdout):
        '''构造函数
        
        :param stream: 流对象
        :type stream: file
        '''
        super(StreamResult, self).__init__()
        self._stream, encoding = ensure_binary_stream(stream)
        self._write = lambda x: self._stream.write(smart_binary(x, encoding=encoding))
        self._step_results = []
        
    def handle_test_begin(self, testcase ):
        '''处理一个测试用例执行的开始
        
        :param testcase: 测试用例
        :type testcase: TestCase
        '''
        self._write(self._seperator2)
        owner = getattr(testcase, 'owner', None)
        priority = getattr(testcase, 'priority', None)
        timeout = getattr(testcase, 'timeout', None)
        begin_msg = u"测试用例:%s 所有者:%s 优先级:%s 超时:%s分钟\n" % (testcase.test_name, owner, priority, timeout)
        self._write(begin_msg)
        self._write(self._seperator2)
    
    def handle_test_end(self, passed ):
        '''处理一个测试用例执行的结束
        
        :param passed: 测试用例是否通过
        :type passed: boolean
        '''
        self._write(self._seperator2)
        self._write("测试用例开始时间: %s\n" % time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.begin_time)))
        self._write("测试用例结束时间: %s\n" % time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.end_time)))
        self._write("测试用例执行时间: %02d:%02d:%02.2f\n" %  _convert_timelength(self.end_time - self.begin_time))
        
        rsttxts = {True:'通过', False:'失败'}
        steptxt = ''
        for i, ipassed in enumerate(self._step_results):
            steptxt += " %s:%s" % (i+1, rsttxts[ipassed])
        self._write("测试用例步骤结果: %s\n" % steptxt)
        self._write("测试用例最终结果: %s\n" % rsttxts[passed])
        self._write(self._seperator2)

    def handle_step_begin(self, msg ):
        '''处理一个测试步骤的开始
        
        :param msg: 测试步骤名称
        :type msg: string
        '''
        if not isinstance(msg, six.string_types):
            raise ValueError("msg='%r'必须是string类型" % msg)
        
        self._write(self._seperator1)
        self._write("步骤%s: %s\n" % (len(self._step_results) + 1, msg))
    
    def handle_step_end(self, passed ):
        '''处理一个测试步骤的结束
        
        :param passed: 测试步骤是否通过
        :type passed: boolean
        '''
        self._step_results.append(passed)
    
    def handle_log_record(self, level, msg, record, attachments ):
        '''处理一个日志记录
        
        :param level: 日志级别，参考EnumLogLevel
        :type level: string
        :param msg: 日志消息
        :type msg: string
        :param record: 日志记录
        :type record: dict
        :param attachments: 附件
        :type attachments: dict
        '''
        self._write("%s: %s\n" % (levelname[level], msg))
        
        if level == EnumLogLevel.ASSERT:
            if "actual" in record:
                actual=record["actual"]
                self._write(u"   实际值：%s%s\n" % (actual.__class__,actual))
            if "expect" in record:
                expect=record["expect"]
                self._write(u"   期望值：%s%s\n" % (expect.__class__,expect))
            if "code_location" in record:
                self._write(smart_text('  File "%s", line %s, in %s\n' % record["code_location"]))
            
        if "traceback" in record:
            self._write(smart_text_by_lines("%s\n" % record["traceback"]))
            
        for name in attachments:
            file_path = smart_text(attachments[name])
            if os.path.exists(file_path):
                file_path = os.path.abspath(file_path)
            self._write("   %s:%s\n" % (smart_text(name), file_path))

class XmlResult(TestResultBase):
    '''xml格式的测试用例结果
    '''
    
    def __init__(self, file_path=None ):
        '''构造函数
        
        :param file_path: XML文件路径
        :type file_path: string
        '''
        super(XmlResult, self).__init__()
        self._xmldoc = dom.Document()
        self._file_path = file_path
    
    @property
    def file_path(self):
        '''xml文件路径
        
        :returns: str
        '''
        return self._file_path
        
    def handle_test_begin(self, testcase ):
        '''处理一个测试用例执行的开始
        
        :param testcase: 测试用例
        :type testcase: TestCase
        '''
        self._xmldoc.appendChild(self._xmldoc.createProcessingInstruction("xml-stylesheet", 'type="text/xsl" href="TestResult.xsl"'))
        owner = getattr(testcase, 'owner', None)
        priority = getattr(testcase, 'priority', None)
        timeout = getattr(testcase, 'timeout', None)
        self._testnode = self._xmldoc.createElement('TEST')
        self._testnode.setAttribute("name", smart_text(saxutils.escape(testcase.test_name)))
        self._testnode.setAttribute("owner", smart_text(saxutils.escape(str(owner))))
        self._testnode.setAttribute("priority", str(priority))
        self._testnode.setAttribute("timeout", str(timeout))
        self._testnode.setAttribute('begintime', time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.begin_time)))
        self._xmldoc.appendChild(self._testnode)
        
        self.begin_step('测试用例初始步骤')
    
    def handle_test_end(self, passed ):
        '''处理一个测试用例执行的结束
        
        :param passed: 测试用例是否通过
        :type passed: boolean
        '''
        self._testnode.setAttribute('result', str(passed))
        self._testnode.setAttribute('endtime', time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.end_time)))
        self._testnode.setAttribute('duration', "%02d:%02d:%02.2f\n" %  _convert_timelength(self.end_time- self.begin_time))
        if self._file_path:
            with codecs.open(smart_text(self._file_path), 'w', encoding="utf-8") as fd:
                fd.write(self.toxml())
        
    def handle_step_begin(self, msg ):
        '''处理一个测试步骤的开始
        
        :param msg: 测试步骤名称
        :type msg: string
        '''
        if not isinstance(msg, six.string_types):
            raise ValueError("msg='%r'必须是string类型" % msg)
        self._stepnode = self._xmldoc.createElement("STEP")
        self._stepnode.setAttribute('title', smart_text(msg))
        self._stepnode.setAttribute('time', time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())))
        self._testnode.appendChild(self._stepnode)
        
    def handle_step_end(self, passed ):
        '''处理一个测试步骤的结束
        
        :param passed: 测试步骤是否通过
        :type passed: boolean
        '''
        self._stepnode.setAttribute('result', str(passed))
    
    def handle_log_record(self, level, msg, record, attachments ):
        '''处理一个日志记录
        
        :param level: 日志级别，参考EnumLogLevel
        :type level: string
        :param msg: 日志消息
        :type msg: string
        :param record: 日志记录
        :type record: dict
        :param attachments: 附件
        :type attachments: dict
        '''
        if not isinstance(msg, six.string_types):
            msg = str(msg)
            
        #由于目前的报告系统仅支持部分级别的标签，所以这里先做转换
        if level >= EnumLogLevel.ERROR:
            tagname = levelname[EnumLogLevel.ERROR]
        elif level == EnumLogLevel.Environment or level == EnumLogLevel.RESOURCE:
            tagname = levelname[EnumLogLevel.INFO]
        else:
            tagname = levelname[level]
            
        infonode = self._xmldoc.createElement(tagname)
        textnode = self._xmldoc.createTextNode(smart_text(msg))
        infonode.appendChild(textnode)
        self._stepnode.appendChild(infonode)
        
        if level == EnumLogLevel.ASSERT:
            if "actual" in record:
                node = self._xmldoc.createElement("ACTUAL")
                try:
                    actual=record["actual"]
                    if isinstance(actual, six.string_types):
                        actual = smart_text(actual)
                        dom.parseString("<a>%s</a>" % actual)
                    acttxt = "%s%s" % (actual.__class__,actual)
                except xmlexpat.ExpatError:
                    acttxt = "%s%s" % (actual.__class__,repr(actual))
                except UnicodeEncodeError:
                    acttxt = "%s%s" % (actual.__class__,repr(actual))
                    
                node.appendChild(self._xmldoc.createTextNode(acttxt))
                infonode.appendChild(node)
                
            if "expect" in record:   
                node = self._xmldoc.createElement("EXPECT")
                try:
                    expect=record["expect"]
                    if isinstance(expect, six.string_types):
                        expect = smart_text(expect)
                        dom.parseString("<a>%s</a>" % expect)
                    exptxt = "%s%s" % (expect.__class__,expect)
                except xmlexpat.ExpatError:
                    exptxt = "%s%s" % (expect.__class__,repr(expect))
                except UnicodeEncodeError:
                    exptxt = "%s%s" % (expect.__class__,repr(expect))
                node.appendChild(self._xmldoc.createTextNode(exptxt))
                infonode.appendChild(node)

        if "traceback" in record:
            excnode = self._xmldoc.createElement('EXCEPT')
            excnode.appendChild(self._xmldoc.createTextNode(smart_text(record["traceback"])))
            infonode.appendChild(excnode)

        for name in attachments:
            file_path = attachments[name]
            attnode = self._xmldoc.createElement('ATTACHMENT')
            attnode.setAttribute('filepath', smart_text(file_path))
            attnode.appendChild(self._xmldoc.createTextNode(smart_text(name)))
            infonode.appendChild(attnode)
                                
    def toxml(self):
        '''返回xml文本
        
        :returns string - xml文本
        '''
        return to_pretty_xml(self._xmldoc)
                
class JSONResult(TestResultBase):
    '''JSON格式的结果
    '''
    def __init__(self, testcase):
        super(JSONResult, self).__init__()
        self._steps = []
        self._data = {
            "testcase": testcase.test_name,
            "description": testcase.test_doc,
            "owner": testcase.owner,
            "priority": testcase.priority,
            "status": testcase.status,
            "steps": self._steps
        }
        
    def get_data(self):
        return self._data
    
    def handle_test_begin(self, testcase ):
        '''处理一个测试用例执行的开始
        
        :param testcase: 测试用例
        :type testcase: TestCase
        '''
        self.begin_step("测试用例初始化步骤")

    def handle_test_end(self, passed ):
        '''处理一个测试用例执行的结束
        
        :param passed: 测试用例是否通过
        :type passed: boolean
        '''
        self._data["succeed"] = passed
        self._data["start_time"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.begin_time)), 
        self._data["end_time"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.begin_time)), 

    def handle_step_begin(self, msg ):
        '''处理一个测试步骤的开始
        
        :param msg: 测试步骤名称
        :type msg: string
        '''
        self._steps.append({
            "name": msg,
            "start_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), 
            "logs": []
        })
        
    def handle_step_end(self, passed ):
        '''处理一个测试步骤的结束
        
        :param passed: 测试步骤是否通过
        :type passed: boolean
        '''
        curr_step = self._steps[-1]
        curr_step["succeed"] = passed
        curr_step["end_time"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), 

    def handle_log_record(self, level, msg, record, attachments ):
        '''处理一个日志记录
        
        :param level: 日志级别，参考EnumLogLevel
        :type level: string
        :param msg: 日志消息
        :type msg: string
        :param record: 日志记录
        :type record: dict
        :param attachments: 附件
        :type attachments: dict
        '''
        curr_step = self._steps[-1]
        curr_step["logs"].append({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "level": level,
            "message": msg,
            "record": record,
            "attachments": attachments
        })



class TestResultCollection(list):
    '''测试结果集合
    '''
    def __init__(self, results, passed ):
        '''构造函数
        
        :param results: 测试结果列表
        :type results: list
        :param passed: 测试是否通过
        :type passed: boolean
        '''
        super(TestResultCollection, self).__init__(results)
        self.__passed = passed
        
    @property
    def passed(self):
        '''测试是否通过
        
        :returns: boolean
        '''
        return self.__passed
