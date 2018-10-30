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
共用类模块
'''

import copy
import copy_reg
import operator
import os, sys
import re
import threading
import time
import traceback
import zipfile
import inspect
from tuia.exceptions import TimeoutError


class Timeout(object):
    '''TimeOut类，实现超时重试逻辑
    '''
    def __init__(self, timeout=10, interval=0.5):
        '''Constructor
        
        :param timeout: 超时秒数，默认是10
        :param interval: 重试时间间隔秒数，默认是0.5
        '''
        self.timeout=float(timeout)
        self.interval=float(interval)
        
    def retry(self,
        func,
        args,
        exceptions=(),
        resultmatcher=None,
        nothrow=False):
        """多次尝试调用函数，成功则并返回调用结果，超时则根据选项决定抛出TimeOutError异常。
        
        :param func: 尝试调用的函数
        :type args: dict或tuple
        :param args: func函数的参数
        :type exceptions: tuple类型，tuple元素是异常类定义，如QPathError, 而不是异常实例，如QPathError()
        :param exceptions: 调用func时抛出这些异常，则重试。
                                                                        如果是空列表(),则不捕获异常。
        :type resultmatcher: 函数指针类型 
        :param resultmatcher: 函数指针，用于验证第1个参数func的返回值。
                                                                                默认值为None，表示不验证func的返回值，直接返回。
                                                                               其函数原型为: 
                                  def result_match(ret):  # 参数ret为func的返回值
                                      pass                                                                                             
                                                                               当result_match返回True时，直接返回，否则继续retry。
        :type  nothrow:bool
        :param nothrow:如果为True，则不抛出TimeOutError异常
        :return: 返回成功调用func的结果
        """         
        start = time.time()
        waited = 0.0
        try_count = 0
        ret=None
        while True:
            try:
                try_count += 1
                if dict == type(args):
                    ret = func(**args)
                elif tuple == type(args):
                    ret = func(*args)
                else:
                    raise TypeError("args type %s is not a dict or tuple" % type(args))
                
                if resultmatcher == None or resultmatcher(ret)==True:
                    return ret
            except exceptions:
                pass
            
            waited = time.time() - start
            if waited < self.timeout:
                time.sleep(min(self.interval, self.timeout - waited))
            elif try_count ==1 :
                continue
            else:
                if nothrow:
                    return ret
                else:
                    raise TimeoutError("在%d秒里尝试了%d次" % (self.timeout, try_count))
    
    def waitObjectProperty(self, obj, property_name, waited_value, regularMatch=False):
        '''通过比较obj.property_name和waited_value，等待属性值出现。 
                             如果属性值obj.property_name是字符类型则waited_value做为正则表达式进行比较。
                             比较成功则返回，超时则抛出TimeoutError异常。
                             
        :param obj: 对象
        :param property_name: 要等待的obj对象的属性名
        :param waited_value: 要比较的的属性值，支持多层属性
        :param regularMatch: 参数 property_name和waited_value是否采用正则表达式的比较。
                                                                            默认为不采用（False）正则，而是采用恒等比较
        '''
        start = time.time()
        waited = 0.0
        try_count = 0
        isstr = isinstance(waited_value, basestring)
        while True:
            objtmp = obj    #增加多层属性支持
            pro_names = property_name.split('.')
            for i in range(len(pro_names)):
                propvalue = getattr(objtmp, pro_names[i])
                objtmp = propvalue
                
            if isstr and regularMatch:      #简化原逻辑
                if None != re.search(waited_value, propvalue):
                    return
            else:
                if waited_value == propvalue: 
                    return
            try_count +=1
            waited = time.time() - start
            if waited < self.timeout:
                time.sleep(min(self.interval, self.timeout - waited))
            else:
                raise TimeoutError("对象属性值比较超时（%d秒%d次）：期望值:%s，实际值:%s，" 
                                   % (self.timeout, try_count, waited_value, propvalue))

    def check(self, func, expect ):
        '''多次检查func的返回值是否符合expect设定的期望值，如果设定时间内满足，则返回True，否则返回False
        
        :param func: 尝试调用的函数
        :param expect: 设定的期望值
        :returns bool - 检查是否符合预期
        '''
        start = time.time()
        waited = 0.0
        while True:
            if expect == func():
                return True
            waited = time.time() - start
            if waited < self.timeout:
                time.sleep(min(self.interval, self.timeout - waited))
            else:
                return False
             
        
class Singleton(type):
    """单实例元类，用于某个类需要实现单例模式。
    使用方式示例如下::
          
          class MyClass(object):
              __metaclass__ = Singleton
              def __init__(self, *args, **kwargs):
                  pass
    
    """
    _instances = {}
    def __init__(cls, name, bases, dic):
        super(Singleton, cls).__init__(name, bases, dic)
        cls._instances = {}
        
    def __call__(self, *args, **kwargs):
        if self not in self._instances:
            self._instances[self] = super(Singleton, self).__call__(*args, **kwargs)          
        return self._instances[self]
    
    
class EggArchive(object):
    '''Egg包
    '''
    def __init__(self, egg_path ):
        '''构造函数
        
        :param egg_path: egg包路径
        :type egg_path: str
        '''
        self._egg_path = egg_path
        
    def get(self, relpath ):
        '''提取文件
        '''
        #EGG包都存放在项目根目录的sites文件夹下，以此推导出项目根目录
        dstpath = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', '..', 'res', os.path.basename(self._egg_path)))
        if not os.path.isdir(dstpath):
            os.makedirs(dstpath)
        dstfile = os.path.join(dstpath, relpath)
        zfile = zipfile.ZipFile(self._egg_path)
        if sys.platform == 'win32':
            ziprelpath = '/'.join(relpath.split('\\'))
        else:
            ziprelpath = relpath
        if os.path.exists(dstfile):
            return dstfile
        print 'extracting %s ...' % ziprelpath
        zfile.extract(ziprelpath, dstpath)
        return dstfile
    
class LazyInit(object):
    '''实现延迟初始化
    
    使用方式示例::
    
        class _Win32Window(object)
            def click(self):
                #......
        class Control(object):
            def __init__(self, locator):
                self._locator = locator
                self._initobj = LazyInit(self, '_initobj', self._init_window)
            def _init_window(self):
                return _Win32Window(self._locator)
            def click(self):
                return self._initobj.click()
                
        ctrl = Control("/Name=xxx)
        ctrl.click()  # <-- call _init_window
        ctrl.click()
    
    '''
    def __init__(self, obj, propname, init_func):
        '''构造函数
        '''
        self.__obj = obj
        self.__propname = propname
        self.__init_func = init_func
        
    def __getattr__(self, attrname ):
        obj = self.__init_func()
        setattr(self.__obj, self.__propname, obj)
        attr = getattr(obj, attrname)
        del self.__obj
        del self.__propname
        del self.__init_func
        return attr
    
    def __setattr__(self, attrname, value):
        if attrname in ['_LazyInit__obj', '_LazyInit__propname', '_LazyInit__init_func']:
            return super(LazyInit, self).__setattr__(attrname, value)
        obj = self.__init_func()
        setattr(self.__obj, self.__propname, obj)
        setattr(obj, attrname, value)
        del self.__obj
        del self.__propname
        del self.__init_func
        
        
class ThreadGroupLocal(object):
    '''使用线程组本地存储的元类
    
    - 当配合ThreadGroupScope使用，类似threading.local()提供的TLS变种，一个线程和其子孙线程共享一个存储
    详细使用方式请参考ThreadGroupScope类
    
    - 当不在ThreadGroupScope中使用时，行为和threading.local()一致
    '''
    def __init__(self):
        curr_thread = threading.current_thread()
#         if not hasattr(curr_thread, 'qtaf_group'):
#             raise RuntimeError("current thread is not in any QTAF thread group scope")
#         self.__data = curr_thread.qtaf_local
        if hasattr(curr_thread, 'qtaf_group'):
            self.__data = curr_thread.qtaf_local
        else:
            if not hasattr(curr_thread, 'qtaf_local_outofscope'):
                curr_thread.qtaf_local_outofscope = {}
            self.__data = curr_thread.qtaf_local_outofscope
            
    def __setattr__(self, name, value ):
        if name.startswith('_ThreadGroupLocal__'):
            super(ThreadGroupLocal,self).__setattr__(name, value)
        else:
            self.__data[name] = value
        
    def __getattr__(self, name):
        if name.startswith('_ThreadGroupLocal__'):
            return super(ThreadGroupLocal,self).__getattr__(name)
        else:
            try:
                return self.__data[name]
            except KeyError:
                raise AttributeError("'ThreadGroupLocal' object has no attribute '%s'" % (name))

class ThreadGroupScope(object):
    '''指定线程组作用域，进入这个作用域的线程，以及在其作用域内创建的线程都同属于一个线程组
    
    使用示例如下::
    
        def _thread_proc():
            ThreadGroupLocal().counter +=1
            
        with ThreadGroupScope("test_group"):
            ThreadGroupLocal().counter = 0
            t = threading.Thread(target=_thread_proc)
            t.start()
            t.join()
            t = threading.Thread(target=_thread_proc)
            t.start()
            t.join()
            assert ThreadGroupLocal().counter == 2
        
    '''
    def __init__(self, name ):
        '''构造函数
        
        :param name: 线程组名称，全局唯一
        :type name: string
        '''      
        self._name = name
        
    def __enter__(self):
        curr_thread = threading.current_thread()
        if hasattr(curr_thread, 'qtaf_local'):
            raise RuntimeError("ThreadGroupScope cannot be nested")
        curr_thread.qtaf_local = {}
        curr_thread.qtaf_group = self._name
    
    def __exit__(self, *exc_info ):
        del threading.current_thread().qtaf_local
        del threading.current_thread().qtaf_group
    
    @staticmethod
    def current_scope():
        '''返回当前线程所在的线程组作用域，如果不存在于任务线程组作用域，则返回None
        '''
        curr_thread = threading.current_thread()
        if hasattr(curr_thread, 'qtaf_group'):
            return curr_thread.qtaf_group
 
_origin_thread_start_func = threading.Thread.start   

def _thread_start_func(self, *args, **kwargs):
    '''用于劫持threading.Thread.start函数
    '''
    curr_thread = threading.current_thread()
    if hasattr(curr_thread, 'qtaf_group'):
        self.qtaf_group = curr_thread.qtaf_group
        self.qtaf_local = curr_thread.qtaf_local
    return _origin_thread_start_func(self, *args, **kwargs)
    
threading.Thread.start = _thread_start_func



def ForbidOverloadMethods( func_name_list ):
    '''生成metaclass用于指定基类禁止子类重载函数
    '''
    class _metaclass(type):
        def __init__(cls, name, bases, dic):
            if len(bases) == 1 and bases[0] == object:
                super(_metaclass, cls).__init__(name, bases, dic)
            else:
                for it in func_name_list:
                    if it in dic.keys():
                        raise RuntimeError("不允许%s重载函数: %s" % (cls.__name__, it))
                super(_metaclass, cls).__init__(name, bases, dic)
                
    return _metaclass


class classproperty(object):
    '''类属性修饰器
    '''
    def __init__(self, getter ):
        self.getter = getter
    def __get__(self, instance, owner):
        return self.getter(owner)
    
def _to_unicode( s ):
    '''将任意字符串转换为unicode编码
    '''
    if not isinstance(s, (str,unicode)):
        raise RuntimeError("data must be basestring type instead of <%s>" % s.__class__.__name__)
    if isinstance(s,unicode):
        return s
    else:
        try:
            return s.decode('utf8')
        except UnicodeDecodeError: # data 可能是gbk编码
            try:
                return s.decode('gbk')
            except UnicodeDecodeError: # data 可能是gbk和utf8混合编码
                return repr(s)
            
def _to_utf8( s ):
    '''将任意字符串转换为UTF-8编码
    '''
    if not isinstance(s, (str,unicode)):
        raise RuntimeError("data must be basestring type instead of <%s>" % s.__class__.__name__)
    if isinstance(s,unicode):
        return s.encode('utf8')
    else:
        try:
            return s.decode('utf8').encode('utf8')
        except UnicodeDecodeError: # data 可能是gbk编码
            try:
                return s.decode('gbk').encode('utf8')
            except UnicodeDecodeError: # data 可能是gbk和utf8混合编码，repr返回
                return repr(s)

def get_thread_traceback(thread):
    '''获取用例线程的当前的堆栈
    
    :param thread: 要获取堆栈的线程
    :type thread: Thread
    '''
    for thread_id, stack in sys._current_frames().items():
        if thread_id != thread.ident:
            continue
        tb = "Traceback ( thread-%d possibly hold at ):\n" % thread_id
        for filename, lineno, name, line in traceback.extract_stack(stack):
            tb += '  File: "%s", line %d, in %s\n' % (filename, lineno, name)
            if line:
                tb += "    %s\n" % (line.strip())
        return tb
    else:
        raise RuntimeError("thread not found")
    
def get_method_defined_class(method):
    method_name = method.__name__
    need_prefix = False
    if method_name.startswith("__"):
        if method_name != "__init__":
            need_prefix = True
    if getattr(method, "__self__", None):    
        classes = [method.__self__.__class__]
    else:
        #unbound method
        if hasattr(method, "im_class"):
            classes = [method.im_class]
        else:
            classes = [getattr(method, "__class__", object)]
    while classes:
        c = classes.pop()
        if c == object:
            if len(classes) > 0:
                continue
        if need_prefix:
            target_name = "_" + c.__name__ + method_name
        else:
            target_name = method_name
        if target_name in c.__dict__:
            return c
        else:
            classes = list(c.__bases__) + classes
    raise RuntimeError("cannot find implement class for method: %s" % method)

def get_last_frame_stack(back_count=2):
    frame = inspect.currentframe()
    for _ in range(back_count):
        frame = frame.f_back
    stack = "".join(traceback.format_stack(frame, 1))
    return stack

empty = object()


def new_method_proxy(func):
    def inner(self, *args):
        if self._wrapped is empty:
            self._setup()
        return func(self._wrapped, *args)
    return inner


class LazyBase(object):
    """base class of lazy inited object
    """

    # Avoid infinite recursion for __init__.
    _wrapped = None

    def __init__(self):
        self._wrapped = empty

    __getattr__ = new_method_proxy(getattr)

    def __setattr__(self, name, value):
        if name == "_wrapped":
            # Avoid infinite recursion for setattr.
            self.__dict__["_wrapped"] = value
        else:
            if self._wrapped is empty:
                self._setup()
            setattr(self._wrapped, name, value)

    def __delattr__(self, name):
        if name == "_wrapped":
            raise TypeError("can't delete _wrapped.")
        if self._wrapped is empty:
            self._setup()
        delattr(self._wrapped, name)

    def _setup(self):
        """to be overridden by subclasses.
        """
        raise NotImplementedError('subclasses of LazyInit must provide a _setup() method')

    #avoid __reduce__ failure cause __class__ method is messed.
    def __getstate__(self):
        if self._wrapped is empty:
            self._setup()
        return self._wrapped.__dict__

    # Python 3.3 will call __reduce__ when pickling; this method is needed
    # to serialize and deserialize correctly.
    @classmethod
    def __newobj__(cls, *args):
        return cls.__new__(cls, *args)

    def __reduce_ex__(self, proto):
        if proto >= 2:
            return (self.__newobj__, (self.__class__,), self.__getstate__())
        else:
            return (copy_reg._reconstructor, (self.__class__, object, None), self.__getstate__())

    def __deepcopy__(self, memo):
        if self._wrapped is empty:
            # We have to use type(self), not self.__class__, because the
            # latter is proxied.
            result = type(self)()
            memo[id(self)] = result
            return result
        return copy.deepcopy(self._wrapped, memo)

    if sys.version_info[0]==3:#py3
        __bytes__ = new_method_proxy(bytes)
        __str__ = new_method_proxy(str)
        __bool__ = new_method_proxy(bool)
    else:
        __str__ = new_method_proxy(str)
        __unicode__ = new_method_proxy(unicode)
        __nonzero__ = new_method_proxy(bool)

    # Introspection support
    __dir__ = new_method_proxy(dir)

    # Need to pretend to be the wrapped class, for the sake of objects that
    # care about this (especially in equality tests)
    __class__ = property(new_method_proxy(operator.attrgetter("__class__")))
    __eq__ = new_method_proxy(operator.eq)
    __ne__ = new_method_proxy(operator.ne)
    __hash__ = new_method_proxy(hash)

    # Dictionary methods support
    __getitem__ = new_method_proxy(operator.getitem)
    __setitem__ = new_method_proxy(operator.setitem)
    __delitem__ = new_method_proxy(operator.delitem)

    __len__ = new_method_proxy(len)
    __contains__ = new_method_proxy(operator.contains)

# Workaround for http://bugs.python.org/issue12370
_super = super

class LazyObject(LazyBase):
    """A lazy object initialized from any function.
    """
    def __init__(self, func):
        """
        :param func:init function for lazy object with no extra argument
        :type  func:function or object with __call__
        """
        self.__dict__['_setupfunc'] = func
        _super(LazyObject, self).__init__()

    def _setup(self):
        self._wrapped = self._setupfunc()

    #representation for debugging before object is caculated.
    def __repr__(self):
        if self._wrapped is empty:
            repr_attr = self._setupfunc
        else:
            repr_attr = self._wrapped
        return '<%s: %r>' % (type(self).__name__, repr_attr)

    def __deepcopy__(self, memo):
        if self._wrapped is empty:
            #__class__ is proxied,using LazyObject instead.
            result = LazyObject(self._setupfunc)
            memo[id(self)] = result
            return result
        return copy.deepcopy(self._wrapped, memo)
    

if __name__ == "__main__":
    pass
    