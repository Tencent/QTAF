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
#2010/11/10 banana    重新整理本模块
#2010/11/16 banana    使TextLog是Thread-safe的
#2010/12/16 banana    增加logInfo方法
#2011/06/02 persimmon    增加XmlResultHandler类的CurrentClassName属性
#2011/06/29 persimmon    将判断log是否属于运行当前用例的线程的逻辑放到BaseHandler的emit方法中
#2013/05/10 tangor   add platform detect
#2013/07/21 pear  增加平台检测，支持linux系统使用
#2014/11/21 olive    更好支持非Windows系统
#2015/01/26 olive    支持在测试报告中展示附件
#2015/01/26 olive    测试用例超时时，测试报告中展示对应的错误类型
#2015/03/27 olive    重构

import sys
import traceback
import time
import xml.dom.minidom as dom
import xml.parsers.expat as xmlexpat
import xml.sax.saxutils as saxutils
import types
import socket
import threading
import codecs
import os
import locale

from testbase import context

try:
    from testbase.platform import report as _reportitf
except ImportError:
    _reportitf = None
    
os_encoding = locale.getdefaultlocale()[1]

class EnumLogLevel(object):
    '''日志级别
    '''
    DEBUG = 10
    INFO = 20
    Environment = 21  #测试环境相关信息， device/devices表示使用的设备、machine表示执行的机器
    ENVIRONMENT = Environment
    
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

def _to_unicode( s ):
    '''将任意字符串转换为unicode编码
    '''
    if isinstance(str, unicode):
        return s
    try:
        return s.decode('utf8')
    except UnicodeDecodeError:
        return s.decode(os_encoding)
    
def _to_utf8( s ):
    '''将任意字符串转换为UTF-8编码
    '''
    if isinstance(str, unicode):
        return s.encode('utf-8')
    try:
        return s.decode('utf8').encode('utf8')
    except UnicodeDecodeError:
        return s.decode(os_encoding).encode('utf8')
    
def _to_utf8_by_lines( s ):
    '''将任意字符串转换为UTF-8编码
    '''
    lines = []
    for line in s.split('\n'):
        lines.append(_to_utf8(line))
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
        self.__error_level = None
        
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
        return reduce(lambda x,y: x and y, self.__steps_passed)
    
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
        if isinstance(msg, unicode):
            msg = msg.encode('utf8')
        with self.__lock:
            if not self.__accept_result:
                return
            if level >= EnumLogLevel.ERROR:
                self.__steps_passed[self.__curr_step] = False
                if level > self.__error_level:
                    self.__error_level = level
                if level == EnumLogLevel.TESTTIMEOUT:
                    extra_record, extra_attachments = self._get_extra_fail_record_safe() #超时时调用这个可能会卡死，所以要这样处理
                    record.update(extra_record)
                    attachments.update(extra_attachments)    
                else:
                    try:
                        extra_record, extra_attachments = context.current_testcase().get_extra_fail_record()
                        record.update(extra_record)
                        attachments.update(extra_attachments)
                    except:
                        self.handle_log_record(EnumLogLevel.ERROR, '测试失败时获取测试用例上下文失败', 
                                          {'traceback':traceback.format_exc()}, {})
            self.handle_log_record(level, msg, record, attachments)
        
    def _get_extra_fail_record_safe(self):
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
        t.join(10)
        extra_record, extra_attachments = {}, {}
        if t.is_alive():
            self.handle_log_record(EnumLogLevel.ERROR, '测试失败时获取测试用例上下文超时',  {}, {})
        else:
            if errors:
                self.handle_log_record(EnumLogLevel.ERROR, '测试失败时获取测试用例上下文失败', 
                                      {'traceback':errors[0]}, {})
            else:
                extra_record, extra_attachments = outputs[0]
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
    #11/04/04 banana    创建
    #15/03/30 olive      修改自StreamHandler
    
    _seperator1 = "-" * 40 + "\n"
    _seperator2 = "=" * 60 + "\n"
    
    def __init__(self, stream=sys.stdout):
        '''构造函数
        
        :param stream: 流对象
        :type stream: file
        '''
        super(StreamResult, self).__init__()
        self._stream = stream
        if stream.encoding and stream.encoding != 'utf8':
            if stream.encoding.lower().startswith('ansi'): #fix Linux下可能出现编码为ANSI*的情况
                self._write = self._stream.write
            else:
                self._write = lambda x: self._stream.write(x.decode('utf8').encode(stream.encoding))
        else:
            self._write = self._stream.write
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
        self._write("测试用例:%s 所有者:%s 优先级:%s 超时:%s分钟\n" % 
                    (testcase.test_name, owner, priority, timeout))
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
        #2012/10/23 pear    修改显示的异常信息
        self._write("%s: %s\n" % (levelname[level], msg))
        
        if level == EnumLogLevel.ASSERT:
            if record.has_key("actual"):
                self._write("   实际值：%s\n" % record["actual"])
            if record.has_key("expect"):
                self._write("   期望值：%s\n" % record["expect"])    
            if record.has_key("code_location"):
                self._write(_to_utf8('  File "%s", line %s, in %s\n' % record["code_location"]))
            
        if record.has_key("traceback"):
            self._write(_to_utf8_by_lines("%s\n" % record["traceback"]))
            
        for name in attachments:
            file_path = attachments[name]
            if os.path.exists(_to_unicode(file_path)):
                file_path = os.path.realpath(file_path)
            self._write("   %s：%s\n" % (name, _to_utf8(file_path)))

class XmlResult(TestResultBase):
    '''xml格式的测试用例结果
    '''
    #11/04/04 banana    创建
    #11/06/02 persimmon    增加XmlResultHandler类的CurrentClassName属性
    #2012/05/31 pear    open的参数不支持utf8编码，需修改为gbk
    #2013/04/01 pear    增加对检查点失败情况下的自动分析功能
    #2015/03/30 olive      从XmlResultHandler修改
    
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
        
    def _decode(self, data):
        #2011/05/23 pear    可能的编码错误
        #2013/01/10 pear    若出现编码错误，则通过repr转换
        if data and isinstance(data, basestring):
            if not isinstance(data, types.UnicodeType):
                try:
                    return data.decode('utf8')
                except UnicodeDecodeError: # data 可能是gbk编码
                    pass
                try:
                    return data.decode('gbk')
                except UnicodeDecodeError: # data 可能是gbk编码
                    return repr(data)
        return data
        
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
        self._testnode.setAttribute("name", _to_unicode(saxutils.escape(testcase.test_name)))
        self._testnode.setAttribute("owner", _to_unicode(saxutils.escape(owner)))
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
            with codecs.open(self._file_path.decode('utf8'), 'w') as fd:
                fd.write(self.toxml())
        
    def handle_step_begin(self, msg ):
        '''处理一个测试步骤的开始
        
        :param msg: 测试步骤名称
        :type msg: string
        '''
        self._stepnode = self._xmldoc.createElement("STEP")
        self._stepnode.setAttribute('title', self._decode(msg))
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
        #2011/06/13 pear    增加对crashfiles属性的处理
        #2012/02/24 pear    添加对异常类型的处理
        #2012/05/16 pear    优化在测试报告显示的异常信息，取完整的最后一行
        #2012/05/17 pear    callstack如果找不到raise，则默认最后一行
        #2012/10/22 pear    获取堆栈信息；去除异常原因信息字符串中左右两边的空格和换行符
        #2012/10/23 pear    修改显示的异常信息
        #2012/10/23 pear    若脚本不通过，则提示"检查点不通过"
        #2013/06/21 pear    对用户传入的expect的值进行有效性检查，看能否被xml解释
        #2013/08/27 pear    对实际值进行有效性检查，看能否被xml解释
        #2013/08/28 pear    qtfa(rambutan)需要期望值存在非正常字符时也不抛异常
        #2015/01/26 olive      优化用例超时时的报告展示
        #2015/01/26 olive      报告展示错误类型增加优先级
        #2016/01/26 olive      支持非str类型的消息
        if not isinstance(msg, basestring):
            msg = str(msg)
        
        if level == EnumLogLevel.ASSERT and record.has_key("code_location"):
            msg += ' [File "%s", line %s, in %s]' % record["code_location"]
            
        #由于目前的报告系统仅支持部分级别的标签，所以这里先做转换
        if level >= EnumLogLevel.ERROR:
            tagname = levelname[EnumLogLevel.ERROR]
        elif level == EnumLogLevel.Environment:
            tagname = levelname[EnumLogLevel.INFO]
        else:
            tagname = levelname[level]
            
        infonode = self._xmldoc.createElement(tagname)
        textnode = self._xmldoc.createTextNode(self._decode(msg))
        infonode.appendChild(textnode)
        self._stepnode.appendChild(infonode)
        
        if level == EnumLogLevel.ASSERT:
            if record.has_key("actual"):
                node = self._xmldoc.createElement("ACTUAL")
                #2013/08/27 pear 这里对self.record.actual进行格式化，加入a标签（其实，可使用能被xml解释接受的任一合法标签），
                #                    是为了使dom.parseString函数在解释self.record.expect时，不会抛异常。
                #2014/05/14 pear 若actual是unicode类型，需要catch此异常，并显示出来
                try:
                    if isinstance(record["actual"], basestring):
                        dom.parseString("<a>%s</a>" % record["actual"])
                    acttxt = self._decode(record["actual"])
                except xmlexpat.ExpatError:
                    acttxt = self._decode(repr(record["actual"]))
                except UnicodeEncodeError:
                    acttxt = self._decode(repr(record["actual"]))
                    
                node.appendChild(self._xmldoc.createTextNode(acttxt))
                infonode.appendChild(node)
                
            if record.has_key("expect"):   
                node = self._xmldoc.createElement("EXPECT")
                try:
                    if isinstance(record["expect"], basestring):
                        #2013/06/27 pear 这里对self.record.expect进行格式化，加入a标签（其实，可使用能被xml解释接受的任一合法标签），
                        #                    是为了使dom.parseString函数在解释self.record.expect时，不会抛异常。
                        dom.parseString("<a>%s</a>" % record["expect"])
                    exptxt = self._decode(str(record["expect"]))
                except xmlexpat.ExpatError:
                    exptxt = self._decode(repr(record["expect"]))
                except UnicodeEncodeError:
                    exptxt = self._decode(repr(record["expect"]))
                node.appendChild(self._xmldoc.createTextNode(exptxt))
                infonode.appendChild(node)

        if record.has_key("traceback"):
            excnode = self._xmldoc.createElement('EXCEPT')
            excnode.appendChild(self._xmldoc.createTextNode(self._decode(record["traceback"])))
            infonode.appendChild(excnode)

        for name in attachments:
            file_path = attachments[name]
            attnode = self._xmldoc.createElement('ATTACHMENT')
            attnode.setAttribute('filepath', self._decode(file_path))
            attnode.appendChild(self._xmldoc.createTextNode(self._decode(name)))
            infonode.appendChild(attnode)
                                
    def toxml(self):
        '''返回xml文本
        
        :returns string - xml文本
        '''
        return self._xmldoc.toprettyxml(indent="    ", newl="\n", encoding='utf-8')

if _reportitf:
    class OnlineResult(XmlResult):
        '''存储在测试报告服务器上的测试用例结果
        '''
        
        def __init__(self, reportid, storage, update_xml=True ):
            '''构造函数
            
            :param reportid: 测试报告ID
            :type reportid: string
            :param storage: 网络文件存储接口
            :type storage: NFStorage
            :param update_xml: 是否上传XML文件
            :type update_xml: boolean
            '''
            super(OnlineResult, self).__init__()
            self._reportid = reportid
            self._nfs = storage
            
            self._exp_info = None
            self._exp_priority = 0
            self._devices_used = set()
            self._machine = socket.gethostname()
            self._update_xml = update_xml
            self._extra = {}
            
        @property
        def storage(self):
            '''网络文件存储接口
            
            :returns: NFStorage - 网络文件存储接口
            '''
            return self._nfs
        
        @property
        def extra(self):
            '''用例附件信息
            
            :returns: dict
            '''
            return self._extra
        
        def handle_test_end(self, passed ):
            '''处理一个测试用例执行的结束
            
            :param passed: 测试用例是否通过
            :type passed: boolean
            '''
            super(OnlineResult, self).handle_test_end(passed)        
            xml_data = self.toxml()
            if self._update_xml:
                casename = self.testcase.test_class_name
                if len(casename) > 32:
                    casename = casename[0:10] + '___' + casename[-10:-1]
                xml_filepath = '%s_%s.xml'%(casename, time.time())
                with codecs.open(xml_filepath, 'w') as fd:
                    fd.write(xml_data)
                self._nfs.upload(xml_filepath)
            req = dict( name=self.testcase.test_name, 
                        path=self.testcase.test_name,
                        author=self.testcase.owner, 
                        result={True:0,False:1}[passed], 
                        iteration="1",
                        machine_id=self._machine, 
                        priority=self.testcase.priority, 
                        timeout=self.testcase.timeout, 
                        description=self.testcase.test_doc, 
                        started_time=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.begin_time)), 
                        finished_time=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.end_time)),
                        log_content=xml_data, 
                        log_dir=self._nfs.url, 
                        reason=self._exp_info, 
                        callstack=None, 
                        machine=','.join([str(it) for it in self._devices_used]))
            req.update(self._extra)
            _reportitf.upload_testcase(self._reportid, **req)
    
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
            if level > EnumLogLevel.ERROR:
                if self._exp_priority <= 3 and level == EnumLogLevel.APPCRASH:
                    self._exp_info, self._exp_priority = "Crash", 3
                        
                if self._exp_priority <= 2 and level == EnumLogLevel.TESTTIMEOUT:
                    self._exp_info, self._exp_priority = "用例执行超时", 2
                      
                if self._exp_priority <= 1 and level == EnumLogLevel.ASSERT:
                    self._exp_info, self._exp_priority = "检查点不通过", 1
                        
                if self._exp_priority <= 1 and record.has_key("traceback"):
                    if not self._exp_info: #优先记录第一个异常，第一个异常往往比较大可能是问题的原因
                        self._exp_info, self._exp_priority = record["traceback"].split('\n')[-2], 1
               
            if level == EnumLogLevel.Environment:
                if record.has_key('device'):
                    self._devices_used.add(record["device"])
                if record.has_key('devices'):
                    self._devices_used |= set(record["devices"])
                if record.has_key('machine'):
                    self._machine = record["machine"]
    
            for name in attachments:
                file_path = attachments[name]
                if os.path.isfile(_to_unicode(file_path)):
                    attachments[name] = self._nfs.upload(file_path)
    
            super(OnlineResult, self).handle_log_record(level, msg, record, attachments)
    
    
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
    
    
