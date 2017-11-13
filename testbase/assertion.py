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
请勿使用！此模块正在建设中

测试用例验证函数
方案一::

    verify("验证变量x是否为True", By.True_(x))  
    verify("验证obj.getX()==123", By.Equal(obj.getX, 123))
    verify("验证xx里是否匹配正则表达式QQ\d+", By.Match(xx, "QQ\d+"))
    verify("验证0<yy<5", By.Function(yy, lambda yy: yy>0 and yy<10))
    verify("验证10秒内obj.getX()==123", By.Wait(By.Equal(obj.getX, 123), 10))

方案二::

    verifyTrue("检查actual的值是否为True",actual)
    verifyTrueWait("验证3秒内obj.getTrue(x1,x2)的值是否为True",obj.getTrue,{'x1':1,'x2':2},3,1)
    verifyEqual("检查b==c",b,c)
    verifyEqualWait("验证10秒内obj.getplus(b,c)的值等于3",a.getplus,{'x1':b,'x2':c},3,10,1)
    verifyMatch("验证'abcd'里是否匹配正则表达式'^a'","abcd","^a")
    verifyMatchWait("验证10秒内obj.getstr()返回的字符串是否匹配正则表达式'^a'",obj.getstr,{},"^a")
    verifyCompareFunc("检查0<d<5",d,lambda x:x>0 and x<5)
    verifyCompareFuncWait("验证10秒内obj.getplus(b,c)的值大于等于3",obj.getplus,{'x1':b,'x2':c},lambda x:x>=4)
    verifyPropertyWait("验证10秒内obj.Top的值等于10",obj,'Top',10)
    
'''
#2012/06/18 banana 创建接口
#2012/06/18 strawberry  接口实现
#2013/05/17 pear 去掉不必要的import
import re
import time
import types
import logger

       
#def assert_(msg, compare_object):
#    """断言。如果不通过，则抛出AssertionError。此方法会中断测试用例执行。
#    如果需要不中断用例，请使用verify函数。
#    """
#    raise NotImplementedError()

def isFunType(obj):
    '''判断obj是否为函数对象和lambda对象
    '''
    return isinstance(obj,types.MethodType) or isinstance(obj,types.LambdaType)

class By(object):
    class CompareBase(object):
        def compare(self):
            '''
            
            :rtype: boolean'''
            raise NotImplementedError("please implement in subclass")
        
        @property
        def Actual(self):
            return self._act
            
        @property
        def Expect(self):
            return self._exp
        
    class Equal(CompareBase):
        '''等值判断类
        '''
        def __init__(self,act,exp):
            self._actemp = act
            self._exptemp = exp 
            
        def compare(self):
            '''检查实际值和期望值是否相等，相等返回True,不等则返回False
            
               :return: True or False
            '''
            if isFunType(self._exptemp):
                self._exp = self._exptemp()
            else:
                self._exp = self._exptemp
            if isFunType(self._actemp):
                self._act = self._actemp()
            else:
                self._act = self._actemp
            if self._exp != self._act: 
                return False
            else:
                return True
   
    class Match(CompareBase):
        '''字符串模式匹配类
        '''
        def __init__(self,act,regexp):
            self._actemp = act
            self._exp = regexp
              
        def compare(self):
            '''检查Actual和Expect是否匹配，匹配返回True,否则返回False
            
               :return: True or False
            '''
            if isFunType(self._exptemp):
                self._act = self._actemp()
            else:
                self._act = self._actemp
            if re.search(self._exp, self._act):
                return True
            else:
                return False
        
    class True_(CompareBase):
        '''布尔值比较类
        '''
        def __init__(self,act):
            self._actemp = act
            self._exp = True 
             
        def compare(self):
            '''检查变量Actual的值是否为True
            
               :return: True or False
            '''
            if isFunType(self._actemp):
                self._act = self._actemp()
            else:
                self._act = self._actemp
            return self._act
        
    class CompareFunc(CompareBase):
        '''自定义函数比较类
        
           :param exp:用户指定的期望值
        '''
        def __init__(self,act,match_func):
            self._actemp = act
            self._exp = True 
            self._comparefunc = match_func
        
        @property
        def Actual(self):
            if isFunType(self._actemp):
                return self._comparefunc(self._actemp())
            else:
                return self._comparefunc(self._actemp)        
        
        def compare(self):
            '''获取自定义比较函数的执行结果
            
               :return: True or False
            '''
            if isFunType(self._actemp):
                self._act = self._comparefunc(self._actemp())
            else:
                self._act = self._comparefunc(self._actemp)  
            return self._act==self._exp
        
    class Wait(CompareBase):
        '''等待函数比较类
        '''
        def __init__(self,compareobject,timeout=10,interval=0.5):
            self._compareobject = compareobject
            self._timeout = timeout 
            self._interval = interval
            
        def compare(self):
            '''函数对象的比较结果为True则立即返回True，超时则返回False。
            
               :return: True or False
            '''
            start = time.time()
            waited = 0.0
            try_count = 0
            while True:
                result = self._compareobject.compare()
                if result==True:
                    self._act = self._compareobject.Actual
                    self._exp = self._compareobject.Expect
                    return True
                try_count +=1
                waited = time.time() - start
                if waited < self._timeout:
                    time.sleep(min(self._interval, self._timeout - waited))
                else:
                    self._act = self._compareobject.Actual
                    self._exp = self._compareobject.Expect
                    return False
        
def verify(msg,compare_object):
    '''测试验证，如果不通过，则会Log一个Error的错误，但不会抛出Exception,用例继续执行 
    
    :param compare_object: 比较对象
    :type compare_object: By.CompareBase
    '''
    if compare_object.compare() != True: 
        logger.error(msg, extra={'actual':compare_object.Actual, 'expect':compare_object.Expect})
        return False
    else:
        return True
    
def _getObjProperty(obj,prop_name):
    '''获取对象多层属性值
    '''
    objtmp = obj
    pro_names = prop_name.split('.')
    for i in range(len(pro_names)):
        propvalue = getattr(objtmp, pro_names[i])
        objtmp = propvalue
    return propvalue

def _getFuncResult(func,args):
    '''对函数对象和参数进行类型检查，调用函数对象获取结果
    '''
    if not isinstance(func,types.MethodType) and not isinstance(func,types.LambdaType):
        raise TypeError("func type %s is not a MethodType or LambdaType" % type(func))
    if dict == type(args):
        actret = func(**args)
    elif tuple == type(args):
        actret = func(*args)
    else:
        actret = func(args)
    return actret

def _waitForCompareResult(func,args,compareobj,timeout=10,interval=0.5):
    ''' 等待获取比较结果
    
       :param actualfunc: 获取实际值的函数对象
       :param actargs: 获取实际值的函数的参数
       :param compareobj: 变量或者判断实际值是否符合预期条件的函数对象
       :return comparefunc: True or False
       :param timeout: 超时秒数
       :param interval: 重试间隔秒数
       :return type: tuple,(True,try_count,actual,expect)
    '''
    start = time.time()
    waited = 0.0
    try_count = 0
    while True:
        try_count +=1
        actret = _getFuncResult(func,args)
        if isinstance(compareobj,types.MethodType) or isinstance(compareobj,types.LambdaType):
            expret = _getFuncResult(compareobj,actret)
            if expret == True:
                return True,try_count,actret,expret
        else:
            expret = compareobj
            if actret == expret:
                return True,try_count,actret,expret
        waited = time.time() - start
        if waited < timeout:
            time.sleep(min(interval, timeout - waited))
        else:
            return False,try_count,actret,expret

def verifyTrue(message,actual):
    '''检查变量actual的值是否为True
    '''
    if not isinstance(actual,bool):
        raise TypeError("actual type %s is not a bool" % type(actual))
    if actual != True:
        logger.error(message, extra={'actual':actual, 'expect':True})
        return False
    return True

def verifyTrueWait(message,actualfunc,actargs,timeout=10,interval=0.5):
    '''每隔interval检查actualfunc返回的值是否为True，如果在timeout时间内都不相等，则测试用例失败
    
       :param message: 失败时的输出信息
       :param actualfunc: 获取实际值的函数对象
       :param actargs: 获取实际值的函数的参数
       :param timeout: 超时秒数
       :param interval: 重试间隔秒数
    '''
    result = _waitForCompareResult(actualfunc,actargs,True,timeout,interval)
    if result[0]==False:
        logger.error("%s[Timeout:在%d秒内尝试了%d次]" % (message,timeout,result[1]), extra={'actual':result[2], 'expect':True})

     
def verifyEqual(message,actual,expect):
    '''检查实际值和期望值是否相等，不等则测试用例失败
    
       :param message: 检查信息
       :param actual: 实际值
       :param expect: 期望值
       :return: True or False
    '''
    if actual != expect:
        logger.error(message, extra={'actual':actual, 'expect':expect})
        return False
    return True
        
def verifyEqualWait(message,actualfunc,actargs,expect,timeout=10,interval=0.5):
    '''每隔interval检查实际值和期望值是否相等，如果在timeout时间内都不相等，则测试用例失败

       :param message: 失败时的输出信息
       :param actualfunc: 获取实际值的函数对象
       :param actargs: 获取实际值的函数的参数
       :param expect: 期望值
       :param timeout: 超时秒数
       :param interval: 重试间隔秒数
    '''
    result = _waitForCompareResult(actualfunc,actargs,expect,timeout,interval)
    if result[0]==False:
        logger.error("%s[Timeout:在%d秒内尝试了%d次]" % (message,timeout,result[1]), extra={'actual':result[2], 'expect':expect})


def verifyMatch(message,actual,regexpect):
    '''检查actual和regexpect是否模式匹配，不匹配则记录一个检查失败
    
        :type message: string
        :param message: 失败时记录的消息
        :type actual: string
        :param actual: 需要匹配的字符串
        :type regexpect: string
        :param regexpect: 要匹配的正则表达式 
    '''
    if re.search(regexpect, actual):
        return True
    else:
        logger.error(message, extra={'actual':actual, 'expect':regexpect})
    return False

def verifyMatchWait(message,actualfunc,actargs,regexpect,timeout=10,interval=0.5):
    '''每隔interval检查actualfunc返回值是否和正则表达式regexpect是否匹配，如果在timeout时间内都不相等，则测试用例失败

       :param message: 失败时的输出信息
       :param actualfunc: 获取实际值的函数对象
       :param actargs: 获取实际值的函数的参数
       :param regexpect: 需要匹配的正则表达式
       :param timeout: 超时秒数
       :param interval: 重试间隔秒数
       :return: True or False
    '''
    compareobj = lambda x:re.search(regexpect, x)!=None
    result = _waitForCompareResult(actualfunc,actargs,compareobj,timeout,interval)
    if result[0]==False:
        logger.error("%s[Timeout:在%d秒内尝试了%d次]" % (message,timeout,result[1]), extra={'actual':result[2], 'expect':regexpect})


def verifyCompareFunc(message,actual,comparefunc):
    '''检查传入actual后调用comparefunc的返回值是否为True，为False则测试用例失败
    
        :param actual: 实际值
        :type actual: tuple or dict or 任意一个变量
        :param comparefunc: 判断实际值是否符合预期条件的函数对象
        :return comparefunc: True
    '''
    actret = _getFuncResult(comparefunc,actual)
    if actret != True:
        logger.error(message, extra={'actual':actret, 'expect':True})
        return False
    return True

def verifyCompareFuncWait(message,actualfunc,actargs,comparefunc,timeout=10,interval=0.5):
    '''每隔interval将actualfunc返回值传入到comparefunc，检查其返回值是否为True，如果在timeout时间内都不为True，则测试用例失败
    
       :param message: 失败时的输出信息
       :param actualfunc: 获取实际值的函数对象
       :param actargs: 获取实际值的函数的参数
       :param comparefunc: 判断实际值是否符合预期条件的函数对象
       :return comparefunc: True
       :param timeout: 超时秒数
       :param interval: 重试间隔秒数
    '''
    result = _waitForCompareResult(actualfunc,actargs,comparefunc,timeout,interval)
    if result[0]==False:
        logger.error("%s[Timeout:在%d秒内尝试了%d次]" % (message,timeout,result[1]), extra={'actual':result[2], 'expect':True})

def verifyPropertyWait(message,obj,prop_name,expect,timeout=10,interval=0.5):
    '''每隔interval检查obj.prop_name是否和expected相等，如果在timeout时间内都不相等，则测试用例失败
    
       :param message: 失败时的输出信息
       :param obj: 需要检查的对象
       :type prop_name: string 
       :param prop_name: 需要检查的对象的属性名，支持多层属性
       :param expect: 期望的对象属性值
       :param timeout: 超时秒数
       :param interval: 重试间隔秒数
    '''
    result = _waitForCompareResult(_getObjProperty,{'obj':obj,'prop_name':prop_name},expect,timeout,interval)
    if result[0]==False:
        logger.error("%s[Timeout:在%d秒内尝试了%d次]" % (message,timeout,result[1]), extra={'actual':result[2], 'expect':expect})

        
if __name__ == '__main__':
    pass  
