#-*- coding: utf-8 -*-
'''从SVN的Workspace同步代码
'''

#2017/10/20 eeelin 新建

import os
import re
import traceback
import sys
import locale
import shutil

os_encoding = locale.getdefaultlocale()[1]

SVN_WORKSPACE_PATH = "D:\\dist\\qtaf5"
BLACKLIST_DIRNAME = r"(\.svn)|(_build)|(pyqq)"
BLACKLIST_FILENAME = r".*\.pyc"

BASEDIR = os.path.realpath(os.path.dirname(__file__))
BLACKLIST_DEL_PATHS = [os.path.join(BASEDIR,'.git'), __file__]

def printf( s ):
    if sys.stdout.encoding:
        sys.stdout.write(s.decode('utf8').encode(sys.stdout.encoding))
    else:
        sys.stdout.write(s)
        
def input( s ):
    if sys.stdout.encoding:
        s = s.decode('utf8').encode(sys.stdout.encoding)
    return raw_input(s)

def pause():
    if sys.platform == 'win32':
        os.system('pause')
    else:
        os.system('read -p 按任意键继续')
        
    
def main():
    if not SVN_WORKSPACE_PATH:
        raise RuntimeError("SVN_WORKSPACE_PATH not set!")
        
    bl_dirname = re.compile(BLACKLIST_DIRNAME)
    bl_filename = re.compile(BLACKLIST_FILENAME)
    
    dst_root = os.path.realpath(os.path.dirname(__file__))
    
    for dirpath, dirnames, filenames in os.walk(SVN_WORKSPACE_PATH):
        relpath = os.path.relpath(dirpath, SVN_WORKSPACE_PATH)
        dstdirpath = os.path.join(dst_root, relpath)
        new_created_dir = False
        if not os.path.exists(dstdirpath):
            print("mkdir %s" % dstdirpath)
            os.makedirs(dstdirpath)
            new_created_dir = True
                
        for it in list(dirnames):
            if bl_dirname.match(it):
                dirnames.remove(it)
        for filename in filenames:
            if bl_filename.match(filename):
                continue
            src = os.path.join(dirpath, filename)

            print("copy %s -> %s" % (src, relpath) )
            shutil.copy(src, os.path.join(dstdirpath, filename))
            
        if not new_created_dir:
            dst_items = set(os.listdir(dstdirpath))
            src_items = set(dirnames + filenames)
            del_items = dst_items - src_items
            for it in del_items:
                del_path = os.path.realpath(os.path.join(dstdirpath, it))
                if del_path in BLACKLIST_DEL_PATHS:
                    continue
                if os.path.isfile(del_path):
                    print("rm %s" % del_path)
                    os.remove(del_path)
                else:
                    print("rmdir %s" % del_path)
                    shutil.rmtree(del_path)
        
   
if __name__ == '__main__':
    try:
        main()
    except:
        printf(traceback.format_exc())
        
