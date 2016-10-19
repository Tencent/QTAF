# -*- coding: utf-8
'''应用程序基类模块
'''
#10/11/19 allenpan    implement quitAll()
#10/11/22 allenpan    修改quit()
#10/12/21 aaronlai    修改App.quit函数
#11/01/08 allenpan    重构App

#PROCESS_TERMINATE = 1


class App(object):
    '''应用程序基类
    '''
    _totalapps = [] #所有打开的应用程序
    def __init__(self):
        '''构造函数，将self加入到应用程序列表中
        '''
        App._totalapps.append(self)
        
    def quit(self):
        '''请在子类中实现，并调用此方法通知程序退出
        '''
        if self in App._totalapps:
            App._totalapps.remove(self)
    
    @staticmethod
    def quitAll():
        '''退出所有应用程序
        '''
        apps = App._totalapps[:]
        for app in apps:
            app.quit()
            
    @staticmethod
    def clearAll():
        '''清除所有程序记录
        '''
        #11/02/14 allenpan 添加
        
        del App._totalapps[:]
        
    @staticmethod
    def killAll():
        '''结束所有记录的进程
        '''
        #12/01/05 allenpan 添加
        from util import Process
        for app in App._totalapps:
            Process(app.ProcessId).terminate()
        del App._totalapps[:]
        
        
    

if __name__ == "__main__":
    pass