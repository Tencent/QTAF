#-*- coding: utf-8 -*-
'''自动打包和发布
'''

#2015/06/18 eeelin 新建

import os
import subprocess
import traceback
import sys
import locale
import shutil

os_encoding = locale.getdefaultlocale()[1]

DIST_PATH = r'\\tencent.com\tfs\跨部门项目\SNG-Test\QTA\QTAF\dist\qtaf'

TARGETS = ['all', 'testbase', 'open']

BASE_DIR = os.path.dirname(__file__)


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
        
# def build_doc():
    # if os.path.isdir(os.path.join(BASE_DIR, 'build')):
        # shutil.rmtree(os.path.join(BASE_DIR, 'build'))
    # doc_make_dir = os.path.join(BASE_DIR, "doc")
    # os.chdir(doc_make_dir)
    # retcode = subprocess.call(['make', 'chm'], shell=True)
    # if retcode != 0:
        # raise RuntimeError("编译生成qtaf.chm失败")
    # doc_dst_path = os.path.join(doc_make_dir, 'qtaf.chm')
    # if not os.path.isfile(doc_dst_path):
        # raise RuntimeError("生成qtaf.chm失败，文件存在")
    # return doc_dst_path
    
def main():
    dest_dir = DIST_PATH.decode('utf8').encode(os_encoding)
    versions = []
    for it in os.listdir(dest_dir):
        if os.path.isdir(os.path.join(dest_dir, it)):
            items = it.split('.')
            if len(items) == 3:
                versions.append([int(i) for i in items])
            elif len(items) == 2:
                items.append('0')
                versions.append([int(i) for i in items])
    
    version_tuple = sorted(versions)[-1]
    version = '.'.join([str(i) for i in version_tuple])
    
    printf('获取最新的QTAF版本：%s\n' % version)
    
    prefix, subver = version.rsplit('.', 1)
    next_version = prefix + '.' + str(int(subver)+1)
        
    input_version = input ('请输入新版本号(默认:%s)> ' % next_version )
    if input_version:
        next_version = input_version
    with open(os.path.join(BASE_DIR, '_qtaf_version_stub.py'), 'w') as fd:
        fd.write('VERSION=%s'%(repr(next_version)))
    
    
    #doc_path = build_doc()
    
    os.chdir(BASE_DIR)
    
    for target in TARGETS:
        if os.path.isdir(os.path.join(BASE_DIR, 'build')):
            shutil.rmtree(os.path.join(BASE_DIR, 'build'))
        retcode = subprocess.call(['python', 'setup.py', 'bdist_qtaf', '--target', target])
        if retcode != 0:
            raise RuntimeError("打包失败")
        egg_filename = 'qtaf-%s-%s-py2.7.egg' % (next_version, target)
        egg_filepath = os.path.join(BASE_DIR, 'dist', egg_filename)
        if not os.path.isfile(egg_filepath):
            raise RuntimeError("打包失败，没有生成egg包，%s" % egg_filepath)
        
    while 1:
        choice = input('已经生成egg包，是否发布到TFS上(Y/N)> ')
        if choice.upper() == 'N':
            break
        elif choice.upper() == 'Y':
            dist_dir = os.path.join(DIST_PATH, next_version).decode('utf8').encode(os_encoding)
            os.makedirs(dist_dir)
            for target in TARGETS: 
                egg_filename = 'qtaf-%s-%s-py2.7.egg' % (next_version, target)
                egg_filepath = os.path.join(BASE_DIR, 'dist', egg_filename)
                shutil.copy(egg_filepath, dist_dir)
            #shutil.copy(doc_path, dist_dir)
            break
        printf('请输入Y或N\n')
        
        
    printf ('成功！')
#     pause()

if __name__ == '__main__':
    try:
        main()
    except:
        printf(traceback.format_exc())
#         pause()
        
