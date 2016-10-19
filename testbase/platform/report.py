# -*- coding: UTF-8 -*-
'''在线测试报告使用接口'
'''

#2015/03/30 eeelin 新建
#2015/07/29 eeelin 增加新接口

import urllib
import urllib2
import json

from testbase.conf import settings

if settings.DEBUG:
    SITE_ENDPOINT = "http://exp.imd.com/report/v2"
    SITE_URL = SITE_ENDPOINT + "/cgi"
else:
    SITE_ENDPOINT = "http://testing.sng.local/report/v2"
    SITE_URL = SITE_ENDPOINT + "/cgi"

#CGI调用默认超时时间
timeout = 30

__opener = None

def __call_cgi( path, reqdict ):
    """调用CGI接口
    """
    global __opener
    for k in reqdict:
        v = reqdict[k]
        if isinstance(v, unicode):
            reqdict[k] = v.encode('utf8')
    params = urllib.urlencode(reqdict)        
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    req = urllib2.Request( SITE_URL + path, params, headers)
    if __opener is None:
        proxy_handler = urllib2.ProxyHandler({})
        proxy_auth_handler = urllib2.HTTPBasicAuthHandler()
        __opener = urllib2.build_opener(proxy_handler, proxy_auth_handler)
    jsondata = __opener.open(req, timeout=timeout).read()
    rsp = json.loads(jsondata)
    
    if rsp['result'] == "error":
        raise RuntimeError("调用上报报告CGI接口\"%s\"返回失败: %s" %(path, rsp['message'].encode('utf8')))
    else:
        return rsp['result']
    
def create_report( taskname, reporttype, product, version, testtype, creator, build="", protocol="", stream="", mailto="", mailcc="",
                   installerpath=None, maillist_whenfail=None, jobid=None, machine_type=None,
                   svn_proj_url=None, ref_report_id=None, **extra ):
    """创建一份测试报告
    
    :parma taskname: 测试报告名 
    :type taskname: string
    :param reporttype: 测试报告类型，平台中定义的报告类型的key，如果找不到该key会提示失败
    :type reporttype: string
    :param product: 测试产品名，找不到该产品会新建
    :type product: string
    :param version: 测试产品版本，找不到该版本会新建
    :type version: string
    :param testtype: 测试类型，找不到该测试类型会新建
    :type testtype: string
    :param creator: 创建人
    :type creator: string
    :param mailto: 测试报告收件人列表，可以为空
    :type mailto: string
    :param mailcc: 测试报告抄送人列表，可以为空
    :type mailcc: string             
    :returns string - 测试报告ID
    :param installerpath: 安装包路径，可以为空
    :type installerpath: string    
    :param maillist_whenfail: 任务异常是通知人
    :type maillist_whenfail: string
    :param jobid: DRun任务ID,
    :type jobid: string
    :param svn_proj_url: 对应SVN路径，用例重跑使用，可以不填
    :type svn_proj_url: string
    :param machine_type: 使用的机器类型，用例重跑使用，可以不填
    :type machine_type: string
    :param ref_report_id: 参考报告ID，性能对比测试报告使用
    :type ref_report_id: string
    :param extra: 额外参数
    :type extra: dict
    :returns string: 报告ID
    """    
    reqdict = {
               "taskname": taskname, 
               "reporttype":reporttype, 
               "product":product, 
               "version":version, 
               "stream":stream,
               "testtype":testtype, 
               "creator": creator, 
               "build":build, 
               "protocol":protocol, 
               "mailto": mailto, 
               "mailcc":mailcc}
    if installerpath is not None:
        reqdict['installerpath'] = installerpath
    if maillist_whenfail is not None:
        reqdict['maillist_whenfail'] = maillist_whenfail
    if jobid is not None:
        reqdict['jobid'] = jobid
    if machine_type is not None:
        reqdict['machine_type'] = machine_type
    if svn_proj_url is not None:
        reqdict['svn_proj_url'] = svn_proj_url
    if ref_report_id is not None:
        reqdict['ref_report_id'] = ref_report_id
    reqdict.update(extra)
    result = __call_cgi('/uploadreport', reqdict)
    return result['report_id']
    
def finish_report( reportid, endtime="", mail=True, when_pass="", when_fail="", info="", is_normal=1):
    """关闭一份测试报告，测试报告不可以再修改
    
    :param reportid: 测试报告ID
    :type reportid: string
    :param endtime: 测试结束时间，如果为空，则默认为当前时间
    :type endtime: string
    :param mail: 是否发送邮件，已废弃，改用when_pass和when_fail
    :type mail: boolean
    :param when_pass: 报告通过时的通知方式，json串，{"email":0, "rtx":1, "sms":1, "weixin":0}, 1表示需要该通知方式，0表示不需要，下同
    :type when_pass: string
    :param when_fail：报告不通过时的通知方式，json串，{"email":0, "rtx":1, "sms":1, "weixin":0}
    :type when_fail: string
    :param is_normal: 任务是否正常结束
    :type is_normal: int
    
    """
    reqdict = {"report_id": reportid, 
               "endtime": endtime, 
               "mail": mail and 1 or 0, 
               "when_pass" : when_pass, 
               "when_fail":when_fail, 
               "info":info, 
               "is_normal":is_normal}
    __call_cgi('/testcomplete', reqdict)
     
def upload_testcase( reportid, name, path, author, result, iteration="1",
                     machine_id=None, priority=None, timeout=None, description=None,
                     started_time=None, finished_time=None, log_content=None, log_dir=None,
                     reason=None, callstack=None, perf_result=None, machine=None, **kwargs):
    """上传一个测试用例结果
    
    :param reportid: 该测试用于属于的报告ID
    :type reportid: string
    :param name: 测试用例名
    :type name: string
    :param path: 测试用例全路径，系统根据该字段来标识用例的唯一性
    :type path: string
    :param author: 用例作者
    :type author: string
    :param iteration: 测试执行的迭代次数，该迭代用于多条数据驱动的测试
    :type iteration: string
    :param result: 测试结果该字段可以为空，表明本次请求为用例注册。1为不通过，0为通过
    :type result: int
            
    :param machine_id: 执行改用例的机器标识符,
    :type machine_id: string
    :param priority: 用例优先级
    :type priority: string
    :param timeout: 用例超时时间
    :type timeout: string
    :param description: 用例描述
    :type description: string
    :param started_time: 用例开始时间
    :type started_time: string
    :param finished_time: 用例结束时间
    :type finisihed_time: string
    :param log_content: 用例日志xml记录
    :type log_content: string
    :param log_dir: 用例附件文件路径
    :type log_dir: string
    :param reason: 用例失败原因
    :type reason: string
    :param callstack: 用例失败是的堆栈回溯信息
    :type callstack: string
    :param perf_result: 性能日志，性能测试使用
    :type perf_result: string
    :param machine: 使用的设备列表的标识符，多个设备用','间隔
    :type machine: string  
    :returns string - 用例ID
    
    :param kwargs: 扩展参数
    :type kwargs: dict
    
    """
    reqdict = {"report_id": reportid, 
               "name":name, 
               "path":path, 
               "author":author, 
               "iteration":iteration, 
               "result":result}
    
    for it in ['machine_id', 'priority', 'timeout', 'description',
               'started_time', 'finished_time', 'log_content', 'log_dir',
               'reason', 'callstack', 'perf_result', 'machine']:
        if locals()[it] != None:
            reqdict[it] = locals()[it]
    
    reqdict.update(kwargs)
    
    print reqdict
    
    result = __call_cgi('/uploadcase', reqdict)
    return result['case_result_id']

def upload_log( reportid, machine, log, log_type, level=0 ):
    """上传日志
    
    :param reportid: 该测试用于属于的报告ID
    :type reportid: string
    :param machine: log上传的机器，字符串类型则会被当作机器名，int类型则会被当作机器ID
    :type machine: string/int
    :param log: log信息
    :type log: string
    :param log_type: log类型：0为环境log，1为运行时log，后续可扩展，例如性能log等
    :type log_type: int
    :param level: log的级别： 0为debug，1为info，2为warn，3为error，4为fatal
    :type level: int       
    """
    log = log.strip()
    if not log:
        raise ValueError("log cannot be null.")
    if isinstance(machine, int):
        isname = 0
    else:
        isname = 1
    reqdict = {"report_id": reportid, 
               "machine":machine, 
               "log":log, 
               "type":log_type, 
               "level":level, 
               "isname": isname}
    __call_cgi('/uploadlog', reqdict) 
        

# def upload_crash( reportid, machine, dir_path, count ):
#     """上传产品Crash信息
#     
#     :param reportid: 该测试用于属于的报告ID
#     :type reportid: string
#     """
#     reqdict = {"report_id": reportid, 
#                "machine":machine,
#                "dir":dir_path, 
#                "count":count}
#     __call_cgi('/uploadcrash', reqdict)
    
def upload_total_testcase_count( reportid, count ):
    """上传测试用例总数
    
    :param reportid: 该测试用于属于的报告ID
    :type reportid: string
    :param count: 用例总数
    :type count: int
    """
    reqdict = {"report_id": reportid, 
               "case_num":count,}
    __call_cgi('/uploadcasenum', reqdict)


def upload_filtered_testcase( reportid, name, path, author, reason ):
    """上传被过滤的测试用例、
    
    :param reportid: 该测试用于属于的报告ID
    :type reportid: string
    :param reason: reason
    :type reason: string
    """
    reqdict = {"report_id": reportid, 
           "name":name, 
           "path":path, 
           "author":author, 
           "iteration":"1", 
           "result":2,
           "reason":reason}
    result = __call_cgi('/uploadcase', reqdict)
    return result['case_result_id']
    
def upload_error_testname( reportid, testname, error, callstack):
    """上报加载失败的模块
    
    :param reportid: 该测试用于属于的报告ID
    :type reportid: string
    :param testname: 模块名
    :type testname: string
    :param error: 错误原因
    :type error: string
    :param callstack: 堆栈信息
    :type callstack: string
    """
    reqdict = {"report_id": reportid, 
           "name":testname, 
           "path":testname, 
           "author":"unknown", 
           "iteration":"1", 
           "result":3,
           "reason":error,
           "callstack":callstack}
    result = __call_cgi('/uploadcase', reqdict)
    return result['case_result_id']
    
def get_url( reportid ):
    """获取报告的URL
    """
    return SITE_ENDPOINT + "/base/qta/get/report/%s" % reportid

if __name__ == '__main__':
    
    import socket
    reportid = create_report('测试报告调试', 'QTA', 'QQ', '1.2.3.4', '个人测试', 
                  'eeelin', '0.0', '12000', 'eeelin', 'eeelin;eeelin')
    
    print reportid
    
    #upload_crash(reportid, socket.gethostname(), r'\\tencent.com\tfs', 2)
    
    upload_log(reportid, socket.gethostname(), 
               "&nbsp;&nbsp;&nbsp;<a class=\"file-link\" href=\"%s\" style=\"text-decoration: underline;\">%s</a>" % ('http://xxx.com/log', 'DRun.log'),
               log_type=1, level=3)
    
    for it in ['hello.xxx', 'hello.yyy']:
        print upload_testcase(reportid, it, it,
                        'eeelin', 0, 1, socket.gethostname(), 
                        'High', 10, '测试用例hello', 
                        '2015-03-20 12:12:12', '2015-03-20 12:12:18', 
                        '', r'\\tencent.com\tfs', '', '')
    
    finish_report(reportid, is_normal=1)
    
    
    
