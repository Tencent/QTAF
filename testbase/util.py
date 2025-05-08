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
"""
共用类模块
"""

import binascii
import codecs
import importlib
import inspect
import io
import locale
import os
import re
import sys
import threading
import time
import traceback

from inspect import isclass, getmro, types
from xml.dom.minidom import Node
from datetime import datetime

import pkg_resources
import six

from tuia.exceptions import TimeoutError

default_locale = locale.getdefaultlocale()
if default_locale:
    default_encoding = default_locale[1] or "utf-8"
else:
    default_encoding = "utf-8"  # pylint: disable=invalid-name

file_encoding = sys.getfilesystemencoding()
file_encoding_lower = file_encoding.lower()
for special_encoding in ["ansi", "ascii"]:
    if file_encoding_lower.find(special_encoding) >= 0:
        file_encoding = "utf-8"  # pylint: disable=invalid-name
        break
file_encoding = file_encoding or "utf-8"


class Timeout(object):
    """TimeOut类，实现超时重试逻辑"""

    def __init__(self, timeout=10, interval=0.5):
        """Constructor

        :param timeout: 超时秒数，默认是10
        :param interval: 重试时间间隔秒数，默认是0.5
        """
        self.timeout = float(timeout)
        self.interval = float(interval)

    def retry(self, func, args, exceptions=(), resultmatcher=None, nothrow=False):
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
        :rtype : any
        """
        start = time.time()
        waited = 0.0
        try_count = 0
        ret = None
        while True:
            try:
                try_count += 1
                if dict == type(args):
                    ret = func(**args)
                elif tuple == type(args):
                    ret = func(*args)
                else:
                    raise TypeError("args type %s is not a dict or tuple" % type(args))

                if resultmatcher is None or resultmatcher(ret):
                    return ret
            except exceptions:
                pass

            waited = time.time() - start
            if waited < self.timeout:
                time.sleep(min(self.interval, self.timeout - waited))
            elif try_count == 1:
                continue
            else:
                if nothrow:
                    return ret
                else:
                    raise TimeoutError("在%d秒里尝试了%d次" % (self.timeout, try_count))

    def waitObjectProperty(
        self, obj, property_name, waited_value, regularMatch=False
    ):  # pylint: disable=invalid-name
        """通过比较obj.property_name和waited_value，等待属性值出现。
                             如果属性值obj.property_name是字符类型则waited_value做为正则表达式进行比较。
                             比较成功则返回，超时则抛出TimeoutError异常。

        :param obj: 对象
        :param property_name: 要等待的obj对象的属性名
        :param waited_value: 要比较的的属性值，支持多层属性
        :param regularMatch: 参数 property_name和waited_value是否采用正则表达式的比较。
                                                                            默认为不采用（False）正则，而是采用恒等比较
        """
        start = time.time()
        waited = 0.0
        try_count = 0
        isstr = isinstance(waited_value, six.string_types)
        while True:
            objtmp = obj  # 增加多层属性支持
            pro_names = property_name.split(".")
            for i in range(len(pro_names)):
                propvalue = getattr(objtmp, pro_names[i])
                objtmp = propvalue

            if isstr and regularMatch:  # 简化原逻辑
                if None != re.search(waited_value, propvalue):
                    return
            else:
                if waited_value == propvalue:
                    return
            try_count += 1
            waited = time.time() - start
            if waited < self.timeout:
                time.sleep(min(self.interval, self.timeout - waited))
            else:
                raise TimeoutError(
                    "对象属性值比较超时（%d秒%d次）：期望值:%s，实际值:%s，"
                    % (self.timeout, try_count, waited_value, propvalue)
                )

    def check(self, func, expect):
        """多次检查func的返回值是否符合expect设定的期望值，如果设定时间内满足，则返回True，否则返回False

        :param func: 尝试调用的函数
        :param expect: 设定的期望值

        :returns bool - 检查是否符合预期
        """
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
    import six
    class MyClass(with_metaclass(Singleton, object)):
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


class LazyInit(object):
    """实现延迟初始化

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

    """

    def __init__(self, obj, propname, init_func):
        """构造函数"""
        self.__obj = obj
        self.__propname = propname
        self.__init_func = init_func

    def __getattr__(self, attrname):
        obj = self.__init_func()
        setattr(self.__obj, self.__propname, obj)
        attr = getattr(obj, attrname)
        del self.__obj
        del self.__propname
        del self.__init_func
        return attr

    def __setattr__(self, attrname, value):
        if attrname in [
            "_LazyInit__obj",
            "_LazyInit__propname",
            "_LazyInit__init_func",
        ]:
            return super(LazyInit, self).__setattr__(attrname, value)
        obj = self.__init_func()
        setattr(self.__obj, self.__propname, obj)
        setattr(obj, attrname, value)
        del self.__obj
        del self.__propname
        del self.__init_func


class ShareDataManager(object):
    def __init__(self, lock=threading.Lock(), data=None):
        self._data = data
        if self._data is None:
            self._data = {}
        self._lock = lock

    @property
    def data(self):
        return self._data

    def get(self, key):
        self._lock.acquire()
        data = self._data.get(key)
        self._lock.release()
        if not data:
            raise KeyError("No such key %s exists" % key)
        return data.get("value", None)

    def set(self, key, value, level=0):
        self._lock.acquire()
        self._data[key] = {"value": value, "level": level}
        self._lock.release()

    def pop(self, key):
        try:
            self._lock.acquire()
            data = self._data.pop(key)
        except KeyError:
            raise KeyError("No such key %s exists" % key)
        finally:
            self._lock.release()
        return data.get("value", None)

    def remove(self, key):
        try:
            self._lock.acquire()
            self._data.pop(key)
        except KeyError:
            raise KeyError("No such key %s exists" % key)
        finally:
            self._lock.release()


class ThreadGroupLocal(object):
    """使用线程组本地存储的元类

    - 当配合ThreadGroupScope使用，类似threading.local()提供的TLS变种，一个线程和其子孙线程共享一个存储
    详细使用方式请参考ThreadGroupScope类

    - 当不在ThreadGroupScope中使用时，行为和threading.local()一致

    """

    def __init__(self):
        curr_thread = threading.current_thread()
        #         if not hasattr(curr_thread, 'qtaf_group'):
        #             raise RuntimeError("current thread is not in any QTAF thread group scope")
        #         self.__data = curr_thread.qtaf_local
        if hasattr(curr_thread, "qtaf_group"):
            self.__data = curr_thread.qtaf_local
        else:
            if not hasattr(curr_thread, "qtaf_local_outofscope"):
                curr_thread.qtaf_local_outofscope = {}
            self.__data = curr_thread.qtaf_local_outofscope

    def __setattr__(self, name, value):
        if name.startswith("_ThreadGroupLocal__"):
            super(ThreadGroupLocal, self).__setattr__(name, value)
        else:
            self.__data[name] = value

    def __getattr__(self, name):
        if name.startswith("_ThreadGroupLocal__"):
            return super(ThreadGroupLocal, self).__getattr__(name)
        else:
            try:
                return self.__data[name]
            except KeyError:
                raise AttributeError(
                    "'ThreadGroupLocal' object has no attribute '%s'" % (name)
                )


class ThreadGroupScope(object):
    """指定线程组作用域，进入这个作用域的线程，以及在其作用域内创建的线程都同属于一个线程组

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

    """

    def __init__(self, name):
        """构造函数

        :param name: 线程组名称，全局唯一
        :type name: string
        """
        self._name = name

    def __enter__(self):
        curr_thread = threading.current_thread()
        if hasattr(curr_thread, "qtaf_local"):
            raise RuntimeError("ThreadGroupScope cannot be nested")
        curr_thread.qtaf_local = {}
        curr_thread.qtaf_group = self._name

    def __exit__(self, *exc_info):
        del threading.current_thread().qtaf_local
        del threading.current_thread().qtaf_group

    @staticmethod
    def current_scope():
        """返回当前线程所在的线程组作用域，如果不存在于任务线程组作用域，则返回None"""
        curr_thread = threading.current_thread()
        if hasattr(curr_thread, "qtaf_group"):
            return curr_thread.qtaf_group


class TimeoutLock(object):
    """Lock with timeout"""

    def __init__(self, timeout=None):
        self._timeout = timeout
        self._lock = threading.RLock()

    def acquire(self, blocking=True, timeout=-1):
        if timeout <= 0:
            timeout = self._timeout
        return self._lock.acquire(blocking, timeout)

    def release(self):
        try:
            self._lock.release()
        except RuntimeError:
            pass

    def __enter__(self):
        acquired = self.acquire()
        return acquired

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


_origin_thread_start_func = threading.Thread.start


def _thread_start_func(self, *args, **kwargs):
    """用于劫持threading.Thread.start函数"""
    curr_thread = threading.current_thread()
    if hasattr(curr_thread, "qtaf_group"):
        self.qtaf_group = curr_thread.qtaf_group
        self.qtaf_local = curr_thread.qtaf_local
    return _origin_thread_start_func(self, *args, **kwargs)


threading.Thread.start = _thread_start_func


def ForbidOverloadMethods(func_name_list):  # pylint: disable=invalid-name
    """生成metaclass用于指定基类禁止子类重载函数"""

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


class classproperty(object):  # pylint: disable=invalid-name
    """类属性修饰器"""

    def __init__(self, getter):
        self.getter = getter

    def __get__(self, instance, owner):
        return self.getter(owner)


def smart_text(s, decoding=None):
    """convert any text or binary to text
    py2 text: utf-8 bytes
    py3 text: unicode
    """
    if not isinstance(s, (six.string_types, six.binary_type)):
        raise RuntimeError("string or binary type didn't match with %r" % s)
    if six.PY3:
        if isinstance(s, six.text_type):
            return s
        else:
            try:
                return s.decode("utf8")
            except UnicodeDecodeError:  # other encoding
                try:
                    if decoding is None:
                        decoding = default_encoding
                    return s.decode(decoding)
                except UnicodeDecodeError:  # mixed encoding
                    return repr(s)
    else:
        return smart_binary(s, decoding=decoding)  # py2


def smart_binary(s, encoding="utf8", decoding=None):
    """convert any text or binary to binary of specified encoding"""
    if not isinstance(s, (six.string_types, six.binary_type)):
        raise RuntimeError("string or binary type didn't match with %r" % s)
    if isinstance(s, six.text_type):
        try:
            return s.encode(encoding)
        except UnicodeEncodeError:
            if six.PY3:
                return bytes(repr(s), encoding)
            else:
                return bytes(repr(s))

    assert type(s) == six.binary_type
    try:
        return s.decode("utf8").encode(encoding)  # other encoding
    except UnicodeError:
        try:
            if decoding is None:
                decoding = default_encoding
            return s.decode(decoding).encode(encoding)
        except UnicodeError:  # data mixed encoding
            if six.PY3:
                return bytes(repr(s), encoding)
            else:
                return bytes(repr(s))


def smart_bytes(data):
    if not isinstance(data, (six.string_types, six.binary_type)):
        raise ValueError("data=%r does not match string or bytes type" % data)
    if isinstance(data, six.text_type):
        return smart_binary(data)
    else:
        return data


def smart_to_hex(s, encoding="utf8", decoding=None):
    s = smart_binary(s, encoding=encoding, decoding=decoding)
    binary_s = binascii.hexlify(s)
    return smart_text(binary_s)


def smart_from_hex(s):
    s = smart_binary(s)
    binary_s = binascii.unhexlify(s)
    return smart_text(binary_s)


def smart_bytify(obj, encoding="utf-8", decoding=None):
    """recursively convert objects from string types to binary"""
    if isinstance(obj, dict):
        dic = {}
        for key, value in obj.items():
            dic[smart_bytify(key, encoding, decoding)] = smart_bytify(
                value, encoding, decoding
            )
        return dic
    elif isinstance(obj, list):
        ls = []
        for element in obj:
            ls.append(smart_bytify(element, encoding, decoding))
        return ls
    elif isinstance(obj, six.string_types):
        return smart_binary(obj, encoding, decoding)
    else:
        return obj


def smart_strfy(obj, decoding=None):
    """recursively convert objects from binary to text"""
    if isinstance(obj, dict):
        dic = {}
        for key, value in obj.items():
            dic[smart_strfy(key, decoding)] = smart_strfy(value, decoding)
        return dic
    elif isinstance(obj, list):
        ls = []
        for element in obj:
            ls.append(smart_strfy(element, decoding))
        return ls
    elif isinstance(obj, six.string_types):
        return smart_text(obj, decoding)
    else:
        return obj


def get_thread_traceback(thread):
    """获取用例线程的当前的堆栈

    :param thread: 要获取堆栈的线程
    :type thread: Thread
    """
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
        # unbound method
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
    from testbase.conf import settings
    filter_funcs = []
    if hasattr(settings, "QTAF_STACK_FILTERS"):
        filter_funcs = settings.QTAF_STACK_FILTERS
    frame = inspect.currentframe()
    i = 0
    while i < back_count:
        frame = frame.f_back
        if frame.f_code.co_name in filter_funcs:
            continue
        i += 1
    stack = "".join(traceback.format_stack(frame, 1))
    return stack


def to_pretty_xml(doc, encoding="utf-8"):
    """we need to ensure each line to be binary type"""

    class _XMLWriter(codecs.StreamWriter):
        """an inner writer to give writer a chance to handle each line"""

        def write(self, data):
            data = smart_binary(data)
            self.stream.write(data)

    buff = io.BytesIO()
    indent = "    "
    newl = "\n"
    writer = _XMLWriter(buff)
    if doc.nodeType == Node.DOCUMENT_NODE:  # document node needs encoding
        doc.writexml(writer, "", indent, newl, encoding)
    else:
        doc.writexml(writer, "", indent, newl)
    return writer.stream.getvalue()


def ensure_binary_stream(stream, encoding="utf-8"):
    if six.PY3:
        stream_type = type(stream)
        if issubclass(stream_type, io.IOBase):
            if not hasattr(stream, "mode"):
                raise ValueError("stream=%r does not have attribute mode" % stream)
            if "b" in stream.mode:
                new_stream = stream
            else:
                new_stream = stream.buffer
        else:  # making our effort to adapt to the abnormal stream
            orig_stream_write_func = stream.write

            def _binary_write(s):
                s = smart_text(s)
                if not isinstance(s, bytes):
                    s = s.encode(encoding)
                orig_stream_write_func(s)

            stream.write = _binary_write
            new_stream = stream
    else:
        if getattr(stream, "encoding", None):
            if not stream.encoding.lower().startswith("ansi"):  # linux ascii
                encoding = stream.encoding
        new_stream = stream
    return new_stream, encoding


def codecs_open(filename, mode="rb", encoding=None, errors="strict", buffering=1):
    filename = smart_binary(filename, encoding=file_encoding)
    return codecs.open(
        filename, mode=mode, encoding=encoding, errors=errors, buffering=buffering
    )


def path_exists(filename):
    filename = smart_binary(filename, encoding=file_encoding)
    return os.path.exists(filename)


def get_os_version():
    if sys.platform == "win32":
        with os.popen("ver") as pipe:
            osver = smart_text(pipe.read())
    else:
        osver = smart_text(str(os.uname()))  # @UndefinedVariable
    return osver


if six.PY3:
    maketrans_func = str.maketrans
else:
    import string

    maketrans_func = string.maketrans

BAD_FILE_CHARS = r'\/*?:<>"|~#'
BAD_VAR_CHAR = BAD_FILE_CHARS + "()[]+-=& "
TRANS = maketrans_func(BAD_VAR_CHAR, "_" * len(BAD_VAR_CHAR))
BAD_VAR_CHAR_SET = set(BAD_VAR_CHAR)


def translate_bad_char(input_string):
    if six.PY2:
        translated_string = smart_binary(input_string).translate(TRANS)
        translated_string = re.sub(
            r"[^\x00-\x7f]", "", translated_string
        )  # Replace non-ascii chars
    else:
        translated_string = smart_text(input_string).translate(TRANS)
    return translated_string


def has_bad_char(input_string):
    if set(input_string) & BAD_VAR_CHAR_SET:
        return True
    else:
        return False


def get_time_str():
    now = datetime.now()
    time_str = now.strftime("%Y%m%d_%H%M%S%f")[:-3]
    return time_str


def get_inner_resource(resource_module, resource_name):
    if not os.path.isfile(__file__):  # using egg
        file_path = pkg_resources.resource_filename(resource_module, resource_name)
    else:
        mod = importlib.import_module(resource_module)
        mod_path = mod.__path__[0]
        file_path = os.path.join(mod_path, resource_name)
    if not path_exists(file_path):
        raise RuntimeError("resource path: %s not existed." % file_path)
    return file_path


def get_attribute_from_string(object_path):
    parts = object_path.split(".")
    parts_len = len(parts)
    mod = None
    for index in range(parts_len):
        mod_path = ".".join(parts[: index + 1])
        try:
            mod = importlib.import_module(mod_path)
        except ImportError:
            break
    value = mod
    for new_index in range(index, parts_len):
        try:
            value = getattr(value, parts[new_index])
        except AttributeError:
            raise AttributeError(
                '%s has no attribute or submodule named "%s"'
                % (value, parts[new_index])
            )
    return value


def getmembers(object, predicate=None):
    """Return all members of an object as (name, value) pairs sorted by name.
    Optionally, only return members that satisfy a given predicate."""
    if isclass(object):
        mro = (object,) + getmro(object)
    else:
        mro = ()
    results = []
    processed = set()
    names = dir(object)
    # :dd any DynamicClassAttributes to the list of names if object is a class;
    # this may result in duplicate entries if, for example, a virtual
    # attribute with the same name as a DynamicClassAttribute exists
    try:
        for base in object.__bases__:
            for k, v in base.__dict__.items():
                if isinstance(v, types.DynamicClassAttribute):
                    names.append(k)
    except Exception:  # pylint: disable=broad-except
        pass
    for key in names:
        # First try to get the value via getattr.  Some descriptors don't
        # like calling their __get__ (see bug #1785), so fall back to
        # looking in the __dict__.
        try:
            value = getattr(object, key)
            # handle the duplicate key
            if key in processed:
                raise AttributeError
        except AttributeError:
            for base in mro:
                if key in base.__dict__:
                    value = base.__dict__[key]
                    break
            else:
                # could be a (currently) missing slot member, or a buggy
                # __dir__; discard and move on
                continue
        except Exception:  # pylint: disable=broad-except
            continue
        if not predicate or predicate(value):
            results.append((key, value))
        processed.add(key)
    results.sort(key=lambda pair: pair[0])
    return results


if __name__ == "__main__":
    pass
