# -*- coding: utf-8 -*-
'''
file.test.sng.local文件服务器接口
'''
#12/06/29    jonliang    创建
#13/12/03    pillarzou   增加测试资源文件管理
#15/04/08    pillarzou   上传文件时分段读取内容

import os
import httplib
import urllib
import json
import types
import traceback

from testbase.conf import settings

class FileSystemError(Exception):
    '''文件操作异常
    '''
    pass

class FileSystem(object):
    '''文件管理
    
          通过构造函数传入一个目录描述符可得到一个目录路径的映射，用户使用get_file传入一个相对路径即可得到一个完整的文件路径。
    '''
    _host = settings.QTAF_FILE_HOST
    _root = "/data/cfs/qta/"
    _qfm_script = 'http://%s/wsgi/qfm-interface.py' % _host
    _downloaded_files = []
    
    def __init__(self, dir_descriptor=""):
        '''Contructor
        
        :type dir_descriptor: string
        :param dir_descriptor: 目录描述符，支持多级目录描述，如"测试资源"，"测试资源\QQ"
        '''
        if isinstance(dir_descriptor, unicode):
            dir_descriptor = dir_descriptor.encode('utf8')
        self._dir_descriptor = self._adjust_path(dir_descriptor)
            
    def __del__(self):
        for filename in self._downloaded_files:
            if os.path.isfile(filename):
                os.remove(filename)
        del self._downloaded_files[:]
        
    def get_url(self, remote_file):
        '''获取文件的URL
        '''
        (_path,_filename) = os.path.split(remote_file)
        return "http://" + self._host + self._root + self._joinHostPath(remote_file)    
        
    def get_file(self, remote_file):
        '''获取文件
        
        :param remote_file:文件相对路径
        :param savepath:存放到本地的绝对路径
        :return:返回下载到本地的文件绝对路径
        ''' 
        (_path,_filename) = os.path.split(remote_file)
        _remote_file_url = "http://" + self._host + self._root + self._joinHostPath(remote_file)       
        import tempfile
        local_file = os.path.join(tempfile.gettempdir(), _filename)
        if os.path.exists(local_file):
            os.remove(local_file)
        urllib.urlretrieve(_remote_file_url, local_file)
        self._downloaded_files.append(local_file)
        return local_file
        
    def put_file(self, local_file, remote_path):
        '''上传文件
        
        :param local_file:本地文件绝对路径
        :param remote_path:上传到服务器的相对路径
        '''                
        if isinstance(local_file, types.UnicodeType):
            local_file = local_file.encode('utf8')
        if isinstance(remote_path, types.UnicodeType):
            remote_path = remote_path.encode('utf8')
        params = {"path":self._joinHostPath(remote_path)}
        files = {"file":local_file}
        
        #重试3次
        result = None
        error_msg = ''
        for _ in range(3):
            try:
                conn = httplib.HTTPConnection(self._host)
                conn.request("POST", self._qfm_script + "/uploadfile", *self._encode_multipart_data(params, files))
                response = conn.getresponse().read()
                conn.close()
                if not response:
                    raise RuntimeError("请求返回空")
                result = json.loads(response)
                if result == None:
                    raise RuntimeError("请求返回None")
                if result['retval'] != 0:
                    raise RuntimeError("请求返回错误：retval=%s" %  result['retval'] )
                return
            except:
                error_msg = traceback.format_exc()
                
        if not result:
            raise FileSystemError('上传文件失败：%s\n'% error_msg)
        
    def put_directory(self, local_dir, remote_path):
        '''上传目录
        
        :param local_file:本地目录绝对路径
        :param remote_path:上传到服务器的相对路径
        '''   
        if isinstance(local_dir, types.UnicodeType):
            local_dir = local_dir.encode('utf8')
        if isinstance(remote_path, types.UnicodeType):
            remote_path = remote_path.encode('utf8')
        if not os.path.exists(local_dir):
            raise FileSystemError('本地目录不存在')
        for dirpath, _, filenames in os.walk(local_dir):
            for fn in filenames:
                lfile = os.path.join(dirpath, fn).decode('gbk').encode('utf8')
                rpath = remote_path+dirpath[len(local_dir):].decode('gbk').encode('utf8')
                self.put_file(lfile, rpath)
        
    def remove_file(self, remote_file):
        '''删除文件
        
        :param remote_file:文件相对路径
        '''
        params = {"path":self._joinHostPath(remote_file)}
        params = urllib.urlencode(params)
        conn = httplib.HTTPConnection(self._host)
        conn.request("POST", self._qfm_script + "/rmfile", params)
        response = conn.getresponse().read()
        conn.close()
        result = json.loads(response)
        if result['retval'] != 0:
            raise FileSystemError('删除文件失败：返回%s'%result)
    
    def create_directory(self, remote_path):
        '''创建目录
        
        :param remote_path:目录相对路径
        '''  
        params = {"path":self._joinHostPath(remote_path)}
        params = urllib.urlencode(params)
        conn = httplib.HTTPConnection(self._host)
        conn.request("POST", self._qfm_script + "/mkdir", params)
        response = conn.getresponse().read()
        conn.close()
        result = json.loads(response)
        if result['retval'] != 0:
            raise FileSystemError('创建目录失败：返回%s'%result)
    
    def remove_directory(self, remote_path):
        '''删除目录
        
        :param remote_path:目录相对路径
        '''
        params = {"path":self._joinHostPath(remote_path)}
        params = urllib.urlencode(params)
        conn = httplib.HTTPConnection(self._host)
        conn.request("POST", self._qfm_script + "/rmdir", params)
        response = conn.getresponse().read()
        conn.close()
        result = json.loads(response)
        if result['retval'] != 0:
            raise FileSystemError('删除目录失败：返回%s'%result)
        
    def listdir(self, remote_path):
        '''获取目录/文件列表
        
        :param remote_path:目录相对路径
        '''
        params = {"path":self._joinHostPath(remote_path)}
        params = urllib.urlencode(params)
        conn = httplib.HTTPConnection(self._host)
        conn.request("POST", self._qfm_script + "/listdir", params)
        response = conn.getresponse().read()
        conn.close()
        result = eval(response)
        if result['retval'] != 0:
            raise FileSystemError('获取目录失败：返回%s'%result)
        return result['data'] 
        
    def isdir(self, remote_path):
        '''判断路径是否为目录
        
        :param remote_path:目录相对路径
        '''
        params = {"path":self._joinHostPath(remote_path)}
        params = urllib.urlencode(params)
        conn = httplib.HTTPConnection(self._host)
        conn.request("POST", self._qfm_script + "/isdir", params)
        response = conn.getresponse().read()
        conn.close()
        result = json.loads(response)
        if result['retval'] != 0:
            return False
        else:
            return True
        
    def isfile(self, remote_path):
        '''判断路径是否为文件
        
        :param remote_path:目录相对路径
        '''
        params = {"path":self._joinHostPath(remote_path)}
        params = urllib.urlencode(params)
        conn = httplib.HTTPConnection(self._host)
        conn.request("POST", self._qfm_script + "/isfile", params)
        response = conn.getresponse().read()
        conn.close()
        result = json.loads(response)
        if result['retval'] != 0:
            return False
        else:
            return True
        
    def exists(self, remote_path):
        '''判断路径是否存在
        
        :param remote_path:目录相对路径
        '''
        params = {"path":self._joinHostPath(remote_path)}
        params = urllib.urlencode(params)
        conn = httplib.HTTPConnection(self._host)
        conn.request("POST", self._qfm_script + "/exists", params)
        response = conn.getresponse().read()
        conn.close()
        result = json.loads(response)
        if result['retval'] != 0:
            return False
        else:
            return True
    
    def _joinHostPath(self, path1, path2=""):
        path1 = self._adjust_path(path1)
        path2 = self._adjust_path(path2)
        hostpath = self._dir_descriptor + '/' + path1 + '/' + path2
        hostpath = hostpath.replace('//', '/')
        if len(hostpath) > 1:    
            if hostpath[0] == '/':
                hostpath = hostpath[1:]
            if hostpath[-1] == '/':
                hostpath = hostpath[0:-1]
        if hostpath == '/':
            hostpath = ''
        return hostpath     
        
    def _adjust_path(self, path):
        '''转换成"a\b\c"的路径形式
        '''
        path = path.strip()
        return path.replace('\\', '/')
    
    def _encode_multipart_data(self, params, files):
        import mimetools
        import mimetypes  
        boundary = mimetools.choose_boundary()
        def get_content_type(filename):
            return mimetypes.guess_type(filename)[0] or 'application/octet-stream'    
        def encode_field(field_name):
            return('--' + boundary,
                    'Content-Disposition: form-data; name="%s"' % field_name,
                    '', str(params[field_name]))    
        def encode_file(field_name):
            def read_file_content(filename):
                chunk_size = 1024*1024
                file_content = ''
                f = open(filename.decode('utf8'), 'rb')
                while True:
                    chunk_data = f.read(chunk_size)
                    if not chunk_data:
                        break
                    file_content += chunk_data
                f.close()
                return file_content
                    
            filename = files [field_name]
            return('--' + boundary,
                    'Content-Disposition: form-data; name="%s"; filename="%s"' % (field_name, filename),
                    'Content-Type: %s' % get_content_type(filename),
                    '', read_file_content(filename))  
              
        lines = []
        for name in params:
            lines.extend(encode_field (name))
        for name in files:
            lines.extend(encode_file (name))
        lines.extend(('--%s--' % boundary, ''))
        body = '\r\n'.join(lines)    
        headers = {'content-type': 'multipart/form-data; boundary=' + boundary,
                   'content-length': str(len(body))}    
        return body, headers

if __name__ == '__main__':
    FileSystem('').put_file(__file__, '/中午')