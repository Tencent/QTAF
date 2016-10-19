# -*- coding: utf-8 -*-
'''
DRun使用接口
'''

#2015/06/23 eeelin 新建


import socket
import os
import getpass
import uuid

def get_runid():
    '''获取当前的RunID
    
    :returns: string/NoneType
    '''
    runid = os.environ.get('DRUN_RUNID', None) 
    if runid is None:
        return os.environ.get('QTA_DRUNID', None) #DRun2
    else:
        return runid
    
def get_nodeid():
    '''获取当前的节点的ID
    
    :returns: string
    '''
    nodeid = os.environ.get('DRUN_NODEID', None)
    if nodeid:
        return nodeid
    else: #生成一个临时的ID
        return '%s@%s/%s' % (getpass.getuser(), socket.gethostname(), hex(uuid.getnode())[2:-1])

if __name__ == '__main__':
    print get_runid()
    print get_nodeid()

