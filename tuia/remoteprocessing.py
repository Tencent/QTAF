# -*- coding: utf-8 -*-
'''
多机协作模块
'''

#11/08/05    jonliang    创建
#11/08/15    jonliang    去掉误添加的注释
#11/08/16    jonliang    Process类增加timeout参数，修改join方法，增加terminate方法
#11/10/09    jonliang    修正join方法，优化一些原来的逻辑
#12/02/27    aaronlai    修改import包的位置
#12/03/30    jonliang    子进程的返回结果先判断能不能被pickle
#12/05/09    jonliang    内部变量名使用双下划线;修改了异常类型;修改SVN更新方式
#14/10/29    eeelin      优化错误提示
#14/11/04    eeelin      协作机支持unpickle客户端的__main__模块的对象
#14/11/21    eeelin      兼容egg包的情况

import os, sys

if not os.path.isfile(__file__): #egg包的情况
    QTAPATH = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
else:
    QTAPATH = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))

import time
import traceback
import imp
import pickle
from multiprocessing.connection import Client, Listener
import multiprocessing as multiprocessing

import testbase.logger as logger


class Process(object):
    '''
    Process对象代表需要在协作机上运行的一个任务，这个类的部分接口与 multiprocessing.Process类相似
    
    Process类初始化的参数定义：
        address指定协作机的IP
        target指定需要在协作机上运行的函数
        args指定需要在协作机上运行的函数的参数，以元组(tuple)的方式传入
        kwargs指定需要在协作机上运行的函数的参数，以字典(dict)的方式传入。kwargs一般不需要使用
        timeout指定函数在协作机上执行的最大时间
        
    初始化得到Process对象后，使用start()方法可启动该任务，join([timeout])方法可等待该任务执行完毕或者等待最长timeout时间。
    is_alive()方法可以判断协作机上的任务是否已经执行完毕，而getReturnValue可以得到在协作机上运行的函数的返回值
    
    例子：
    
def login_qq_remote()
    qqacc = QQAccountRes.request()
    qqapp = QQApp()
    test.loginQQ(qqapp, qqacc)

rp = remoteprocessing.Process(address='10.6.253.126', target=login_qq_remote, args=())
rp.start()
rp.join(600)
if rp.is_alive():        #如果协作机任务在600秒内没有执行完毕
    raise
else:
    ret = rp.getReturnValue()    #这里login_qq_remote函数没有返回值,会得到None
    
    
    更具体的例子可参考qqtest.hello模块的ContactMessage2Sync 和 ContactMessage2Async
    '''
    
    
    def __init__(self, address, target=None, args=(), kwargs={}, timeout=30):
        ''' 
                       
        :param target: 需要远程机器执行的函数
        :type target: function
        :param args: 远程执行函数的args参数
        :type args: tuple
        :param kwargs: 远程执行函数的kwargs参数
        :type kwargs: dict
        :param timeout: 远程执行函数的总超时时间，单位为分钟
        :type timeout: int
        '''
        #11/08/16    jonliang    Process类增加timeout参数
        #11/08/18    jonliang    修改实例化Client类时传入的错误类型
        #12/05/10    jonliang    返回结果是否缓存拆分成两个内部变量以及去掉一些不必要的注释
        #12/06/29    jonliang    使用更标准的方法hook异常
        self.__target = target
        self.__args = args
        self.__kwargs = kwargs
        self.__timeout = timeout*60
        
        self.__isstarted  = False
        self.__isalive = True
        self.__isresultcached = False
        self.__retval = None
        
        if address == 'localhost':
            import socket
            self.address = socket.gethostbyname(socket.gethostname())
        else:
            self.address = address
                                
        try:
            self.cliconn = Client((self.address, 7226))
        except IOError as e:     #hook标准异常，使用更明确的错误信息提示用户
            if e[0] == 10060:
                raise RemoteConnectionError('协作机--%s连接超时！请检查网络策略或协作机是否正常' %self.address)
            if e[0] == 10061:
                raise RemoteConnectionError('协作机--%s连接失败！请检查网络策略或协作机是否正常' %self.address)
            elif e[0] == 10054:
                raise RemoteConnectionError('协作机--%s正在执行其它任务！'%self.address)
            else:
                raise
        
    def __sendmsg( self, msg ):
        '''发送消息到协作机
        '''
        self.cliconn.send(msg)
        ret, result = self.cliconn.recv() 
        if ret == True:
            return result
        else:
            errtype, msg = result
            if errtype == 0: #已知错误类型
                raise RemoteExecutionError("协作机任务执行异常：%s"%msg)
            else: #其他错误类型
                raise RemoteExecutionError("协作机任务执行异常：\n%s"%msg)
        
    def start(self):
        '''远程任务启动函数
        '''
        #2013/04/19 jonliang    先等待协作机开始执行函数
        self.__isstarted = True
        target = (self.__target, self.__args, self.__kwargs)
        self.__sendmsg((EnumMsgId.EXECUTE_FUNC, pickle.dumps(target), self.__get_main_module_relpath()))
        self.starttime = time.time()
        
    def __get_main_module_relpath(self):
        '''获取__main__模块的相对路径
        '''
        #获取__main__文件路径
        main_path = getattr(sys.modules['__main__'], '__file__', None)
        if not main_path and sys.argv[0] not in ('', '-c'):
            main_path = sys.argv[0]
        if not main_path:
            return
        
        #推算出__main__文件对应的相对路径
        if os.path.isfile(__file__): #非egg包的情况
            qtapath = QTAPATH
        else: #egg包
            #EGG包都存放在项目根目录的sites或exlib文件夹下，以此推导出项目根目录
            qtapath = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        return os.path.relpath(main_path, qtapath)

    def join(self, timeout=None):
        '''阻塞等待协作机的任务进程执行完毕，或者到达timeout时间。可以多次 join 同一个任务进程
        
        :param timeout: 等待的最长时间。当timeout为None时，则会一直等待直到协作机的任务进程执行完毕
        :type timeout: int. 单位为秒
        '''
        #11/08/16    jonliang    修改
        #11/08/17    jonliang    缓存已执行完毕的结果
        #11/10/09    jonliang    修正状态更新的错误
        if not self.__isstarted:
            raise SyntaxError('请先调用start方法启动协作机任务')
        
        if self.__isalive:
            joinstarttime = time.time()
            self.__timeout = self.__timeout - (joinstarttime-self.starttime)  #更新总超时时间
            if timeout is None:
                timeout = self.__timeout      #如果timeout参数为None,则最多等待总超时时间
            elif timeout < self.__timeout:
                logger.warning('join方法指定的等待时间已超过协作机任务的剩余执行时间')

            self.__isalive = self.__sendmsg((EnumMsgId.JOIN_REMOTE,timeout))           
            if not self.__isalive:
                self.__retval = self.__getret()   #提前把运行结果缓存到本地
                self.__isresultcached = True
                return
                       
            usedtime = time.time()-joinstarttime
            if usedtime > self.__timeout:
                raise RemoteExecutionError("协作机任务执行超时")
            else:
                self.__timeout -= usedtime
            
            
    def is_alive(self):
        '''判断协作机上的任务进程是否还存活
        '''
        if not self.__isstarted:
            raise SyntaxError('请先调用start方法启动协作机任务')
        
        if self.__isalive:
            self.__isalive = self.__sendmsg((EnumMsgId.IS_ALIVE,))
        return self.__isalive
    
    
    def terminate(self):
        '''强制终止协作机任务进程，使用该方法后，不能再调用本类的其它方法
        '''
        if not self.__isstarted:
            raise SyntaxError('请先调用start方法启动协作机任务')
        
        if self.is_alive():
            self.cliconn.send((EnumMsgId.KILL_PROCESS,))
        else:
            logger.debug('协作机的任务进程已退出，不需要强制终止')
            
                  
    def getReturnValue(self):
        '''获取协作机执行执行函数的返回值
        
        :attention: 该函数为非阻塞。如果函数仍在执行，则返回None
        '''
        if not self.__isstarted:
            raise SyntaxError('请先调用start方法启动协作机任务')
        
        if self.is_alive():
            return None
        if not self.__isresultcached:
            self.__retval = self.__getret()
        return self.__retval
    
                  
    def __getret(self):
        '''获取远程执行函数的返回值,内部使用
        '''
        #12/05/10    jonliang    去掉异常处理
        ret, result = self.__sendmsg((EnumMsgId.GET_RESULT,))
        if ret == True:
            return result
        else:
            raise RemoteExecutionError("协作机执行函数 %s时发生异常：\n%s" % (self.__target.__name__, result) )
        
        
def _start_server():
    '''启动协作程序
    
    note: 即本函数应该在协作机上执行
    '''
    #11/08/16    jonliang    修改SVN代码更新，接受任务后先更新代码
    #11/08/17    jonliang    修改处理join请求以后不退出循环的错误逻辑
    #11/10/09    jonliang    修改退出循环的时机
    #12/05/09    jonliang    增加异常捕获的注释
    #12/06/18    jonliang    增加对ImportError的捕获
    #12/08/14    jonliang    增加对IOError 10054的捕获
    #13/07/08    jonliang    跟在send之后的recv是阻塞等待的，直接退出该连接，以解决连接结束逻辑没有退出的问题
    #13/07/22    jonliang    改为在整个长连接过程中捕获异常
    
    import socket
    localip = socket.gethostbyname(socket.gethostname())
    address = (localip, 7226)
    listener = Listener(address)

    try:    
        while True:
            conn = listener.accept()
            print 'connection accepted from', listener.last_accepted, time.strftime("%Y-%m-%d %H:%M:%S")
            _svn_update(QTAPATH)
            finished = False
            while not finished:
                time.sleep(0.05)
                try:
                    datalist = conn.recv()
                    result = None
                    
                    if datalist[0] == EnumMsgId.EXECUTE_FUNC:
                        jq = multiprocessing.Queue()
                        subprocess = multiprocessing.Process(target=_execute, args=(jq, datalist[1], datalist[2]))
                        subprocess.start()
                        result = True
    
                    elif datalist[0] == EnumMsgId.JOIN_REMOTE:
                        subprocess.join(datalist[1])
                        result = subprocess.is_alive()
                            
                    elif datalist[0] == EnumMsgId.IS_ALIVE:
                        result = subprocess.is_alive()
                                             
                    elif datalist[0] == EnumMsgId.GET_RESULT:
                        if jq.empty():
                            raise RuntimeError('Queue is empty')
                            
                        elif jq.full():
                            raise RuntimeError('Queue is empty')
                        else:
                            ret = jq.get_nowait()
                            result = ret  #ret is a tuple
                        finished = True
                        
                    elif datalist[0] == EnumMsgId.KILL_PROCESS:
                        if subprocess.is_alive():
                            subprocess.terminate()
                        finished = True
                        
                    else:
                        raise RuntimeError("非法的MsgId：%s" % datalist[0])
                    
                    conn.send((True,result))
                        
                        
                except EOFError:    #主动机结束连接
                    finished = True
                    
                except AttributeError:  #如果协作机上没有要执行的函数，则pickle会抛该异常
                    conn.send((False, (0,"协作机代码中没有找到要执行的函数")))
                    finished = True
                    
                except ImportError: #如果协作机上没有要执行函数所在的模块，则pickle会抛该异常
                    conn.send((False, (0,"协作机代码中没有找到要执行的函数所在的模块")))
                    finished = True
   
                except:
                    conn.send((False, (1,traceback.format_exc())))
                    finished = True
                        
            conn.close()

            
    except KeyboardInterrupt:
        listener.close()
          

def _load_main_module( main_mod_refpath ):
    '''加载并替换原来的__main__模块
    '''
    if not main_mod_refpath:
        return
    main_path = os.path.realpath(os.path.join(QTAPATH, main_mod_refpath ))
    main_name = os.path.splitext(os.path.basename(main_path))[0]       
    if main_name == '__init__':
        main_name = os.path.basename(os.path.dirname(main_path))
    if main_path is None:
        dirs = None
    elif os.path.basename(main_path).startswith('__init__.py'):
        dirs = [os.path.dirname(os.path.dirname(main_path))]
    else:
        dirs = [os.path.dirname(main_path)]

    assert main_name not in sys.modules, main_name
    fd, path_name, etc = imp.find_module(main_name, dirs)
    
    #将客户端代码的__main__模块的目录加入PATH中
    sys.path.append(dirs[0])
    
    try:
        # 不可以使用"imp.load_module('__main__', ...)"的方式来加载
        # 会导致'if __name__ == "__main__"'的分支被执行
        main_module = imp.load_module(
            '__client_main__', fd, path_name, etc
            )
    finally:
        if fd:
            fd.close()

    sys.modules['__main__'] = main_module
    main_module.__name__ = '__main__'
    
    # 使得原本的sys.modules['__main__']的对象在pickle的时候不出现异常
    for obj in main_module.__dict__.values():
        try:
            if obj.__module__ == '__client_main__':
                obj.__module__ = '__main__'
        except Exception:
            pass
               
    
def _execute(q, target_buf, main_mod_refpath ):
    '''传给子进程执行的包裹函数，内部会call从主机 pickle的函数并获取其返回值，最后释放在协作机上申请的所有帐号资源
    '''
    #12/03/30 jonliang    先判断结果能不能被pickle
    #12/05/10 jonliang    去掉释放帐号的操作，tuia不依赖其它包
    try:        
        _load_main_module(main_mod_refpath)
        target_func, args, kwargs = pickle.loads(target_buf)
        retval = target_func(*args, **kwargs)
        f = open('remoteprocessing.tmp', 'w+')
        pickle.dump(retval, f)  #先判断一下结果能不能被pickle
        f.close()
        os.remove('remoteprocessing.tmp')
        q.put((True, retval))
    except:
        q.put((False, traceback.format_exc()))
    return True


class RemoteConnectionError(Exception):
    '''主动机和协作机连接出现异常
    '''
    pass


class RemoteExecutionError(Exception):
    '''协作机执行任务函数时出现异常
    '''
    pass


class EnumMsgId(object):
    '''主动机和协作机通信标志位
    '''
    
    EXECUTE_FUNC = 0x0000
    JOIN_REMOTE = 0x0001
    IS_ALIVE = 0x0002
    GET_RESULT = 0x0003
    KILL_PROCESS = 0x0004

def _svn_update(script_dir):
    #12/05/09 jonliang    改用svnupdate.exe进行更新
    #12/05/10 jonliang    修改一处参数错误
    #12/06/29 jonliang    修改svnupdate.exe的路径
    parentdir = os.path.abspath(os.path.join(script_dir, "../"))
    svnlogdir = os.path.join(parentdir,'remoteprocessing_svn_logs')
    if not os.path.exists(svnlogdir):
        os.mkdir(svnlogdir)
    svnlogpath = "%s\\%s.log" % (svnlogdir,time.strftime("%Y_%m_%d_%H_%M_%S"))
    cmd_str = r'"\\tencent.com\tfs\跨部门项目\SNG-Test\QTA\常用工具\svnupdate\svnupdate.exe" %s %s' %(script_dir, svnlogpath)
    os.system(cmd_str.decode('utf8').encode('gbk'))
    

if __name__ == '__main__':
    _start_server()