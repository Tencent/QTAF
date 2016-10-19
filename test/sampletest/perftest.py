# -*- coding: utf-8 -*-
'''
模块描述
'''
#2015-4-22 eeelin 新建

from testbase.testcase import TestCase, ITestCaseRunner, TestCaseRunner
from testbase.testresult import OnlineResult
from testbase.report import OnlineTestResultFactory

perf_result = r"""<?xml version='1.0' encoding='UTF-8'?>
<Perflib>
    <Results cpu_time="1219" 
             desc="测试场景3" 
             duration="199" 
             gdi_objects="5" 
             handles="11" 
             io_bytes="634" 
             io_counts="577" 
             log_url="\\fs-gk02a.tencent.com\cip$\PerfReport\QQSpeed\sngperf-PC1\QQ2013_NewVerQQShowAd\QQ5.5.10919.0[1398752980]\OpenGroupAIO\2" 
             name="opengroupaio.OpenGroupAIO.firstopengroupaio3" 
             no_response="215" 
             page_faults="12120" 
             private_bytes="1178" 
             threads="12" 
             user_objects="12" 
             working_set="-23429" />
             
    <Results cpu_time="1312" 
             desc="测试场景4" 
             duration="189" 
             gdi_objects="7" 
             handles="17" 
             io_bytes="584" 
             io_counts="564" 
             log_url="\\fs-gk02a.tencent.com\cip$\PerfReport\QQSpeed\sngperf-PC1\QQ2013_NewVerQQShowAd\QQ5.5.10919.0[1398752980]\OpenGroupAIO\2" 
             name="opengroupaio.OpenGroupAIO.firstopengroupaio4" 
             no_response="229" 
             page_faults="12210" 
             private_bytes="1182" 
             threads="4" 
             user_objects="1"
              working_set="-23420">
              
              <AnalyseFile path="\\fs-gk02a.tencent.com\cip$\PerfReport\QQSpeed\SNGPERF-PC34\QQ6.1\QQ6.1.11859.0[1405323493]\LoginQQ\4\etl.zip" priority="0" />
              <AnalyseFile path="\\fs-gk02a.tencent.com\cip$\PerfReport\QQSpeed\SNGPERF-PC34\QQ6.1\QQ6.1.11859.0[1405323493]\LoginQQ\3\etl.zip" priority="0" />
    </Results>
</Perflib>
"""




class PerfResult(object):
    '''性能测试结果（PerfLib定义）
    '''
    def to_string(self):
        return perf_result
    
class PerfTestCase(TestCase):
    """性能测试用例示例
    """
    owner = "eeelin"
    status = TestCase.EnumStatus.Ready
    timeout = 1
    priority = TestCase.EnumPriority.Normal

    def init_test(self, testresult):
        TestCase.init_test(self, testresult)
        self.perf_result = PerfResult()
        
    def run_test(self):
        self.log_info("test")
        
    def clean_test(self):
        TestCase.clean_test(self)
        if hasattr(self.test_result, 'extra'):
            self.test_result.extra['perf_result'] = self.perf_result.to_string()
        
if __name__ == '__main__':
    PerfTestCase().debug_run()