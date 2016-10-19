# -*- coding: utf-8 -*-
'''
资源管理模块

包括：协作机管理及测试资源文件管理
'''
#12/06/29    jonliang    创建
#13/12/03    pillar      增加测试资源文件管理

import _rscitf as rscitf
import testbase.logger as logger
import os

#---------------------------------------------------------
# 协作机管理
#---------------------------------------------------------

class RemoteProcessMachine(object):
    '''协作机管理类，包括协作机的申请和释放，协作机本身信息
    
            使用方法: 申请协作机: m = RemoteProcessMachine.request()
                                     释放协作机: del m
                                     执行函数:   tuia.remoteprocessing.Process(address=m.IP, target=login_qq_remote)
    '''
    
    def __init__(self, ip):
        self.__ip = ip
        self._rscId = 0
        
    @property
    def IP(self):
        '''协作机的IP
        '''
        return self.__ip

    @staticmethod
    def request(features={'machine_type':'QQ'}):
        #12/11/09    jonliang    log中增加成功申请的协作机IP
        '''申请一台协作机。目前仅支持按协作机类型申请
        '''
        resource_id, resource_property_dict = rscitf.ApplyRes(attrDic=features, groupName='remoteprocess_machines', resType='10')
        if not resource_property_dict.has_key('ip'):
            raise ResourceError('该资源没有IP属性，协作机资源必须具有IP属性.')
        m = RemoteProcessMachine(ip=resource_property_dict['ip'])
        m._rscId = resource_id
        logger.info('成功申请协作机: %s\n'% m.IP)
        return m
    
    def __del__(self):
        '''Destructor，释放申请的资源
        '''
        #12/07/10    jonliang    增加协作机信息的打印
        
        logger.info('正在释放协作机: %s\n'% self.IP)
        if self._rscId != 0:
            rscitf.ReleaseRes([self._rscId])
    

class ResourceError(Exception):
    '''机器异常
    '''
    pass

#---------------------------------------------------------
# 测试资源文件管理
#---------------------------------------------------------   
class FileResourceMgr(object):
    '''测试文件资源管理类
    
          通过构造函数传入一个目录描述符可得到一个目录路径的映射，用户使用get_file传入一个相对路径即可得到一个完整的文件路径。
    '''
    _root = r"\\tencent.com\tfs\跨部门项目\SNG-Test\QTA"
    
    def __init__(self, dir_descriptor):
        '''Contructor
        
        :type dir_descriptor: string
        :param dir_descriptor: 目录描述符，支持多级目录描述，如"测试资源"，"测试资源\QQ"
        '''
        self._path_mapping = os.path.join(self._root, dir_descriptor)        
        
    def get_file(self, path):
        '''获取文件
        
        :param path:相对路径
        :return:返回绝对路径
        '''
        path = self._adjust_path(path)      
        return os.path.join(self._path_mapping, path)
    
    def _adjust_path(self, path):
        '''转换成"a\b\c"的路径形式
        '''
        return path.replace('/', '\\')
        

if __name__ == "__main__":
    #m = RemoteProcessMachine.request()
    filemgr = FileResourceMgr("测试资源")
    print filemgr.get_file(r"测试文件\test.txt")
    
    filemgr = FileResourceMgr("TIF")
    print filemgr.get_file(r"cip\发布基线库\01_Hummer\QQ2.00\9050_FinalRelease_sign_perf\tif.dll")
        