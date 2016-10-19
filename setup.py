# -*- coding: utf-8 -*-
"""
发布流程
------------
1. 修改版本:
    修改文件的VERSION，并上库

2. build chm:  进入doc目录，运行"make.bat chm"
    
3. build egg: 
    * 运行："python setup.py bdist_qtaf"
    可以使用--target指定生成的目标类型，比如
    * 生成最简目标类型的egg包，运行"python setup.py bdist_qtaf --target testbase"
    * 生成最全目标类型的egg包，运行"python setup.py bdist_qtaf --target all"
    可以通过修改EXCLUDE_SOURCES_PACKAGES、PREDEF_PACKAGES_BLACKLIST来控制是否打包对应模块的代码文件
    注意：pyc文件不能在不同python版本之间兼容。

4. 打基线：将trunk打tag，用版本号当tag名字

5. 给相关项目更新QTAF包
    5.1. 部门外的使用不包含源文件的egg包，部门内的可以先使用含有源文件的egg包
    5.1. 安装qtaf：将py安装到“site”目录，将脚本安装到“scripts”目录
        "easy_install -m -d site -s scripts path_to_qtaf_egg"
    5.2. 将安装到site和scripts目录的文件上库
    
"""
# 2012/11/07 allenpan   移到本文件到最外层
# 2012/11/14 allenpan   setup文件基本改造完成
# 2013/01/15 aaronlai   版本号叠加，从2.4开始
# 2013/04/02 aaronlai   testrunner增加对使用egg的项目的支持，版本号递增1
# 2013/04/16 aaronlai   对tuia.gfcontrols.Menu.forceAppear函数的参数作了改造，版本递增
# 2013/07/25 aaronlai   添加document,window对象的属性检测，保证获取的对象的相关属性是可用的
# 2013/07/31 aaronlai   改动了iedriver 的__release__，解决了死循环的bug
# 2013/10/11 aaronlai   修复 raw_unicode_escape 对"\uXXXX"前面带有“\”的字符串解码错误
# 2013/11/12 aaronlai   增加使用ctypes模块封装IAccessible，以支持win32和web类型的控件。
#                       testbase.testcase新增测试环境变量
# 2013/11/13 aaronlai   增加对360浏览器的支持
# 2013/12/09 pillarzou  增加测试资源文件统一管理(testbase.resource.FileResourceMgr)
# 2013/12/12 aaronlai   增加对360浏览器支持时，缺少一个文件
# 2014/02/26 aaronlai   webcontrols.WebPage新增navigate方法
# 2014/02/26 aaronlai   cef改造
# 2014/03/04 aaronlai   修改accessible模块
# 2014/03/19 aaronlai   修改注入模块
# 2014/03/27 aaronlai   tuia.keyboard模块修改，新增clear方法
# 2014/04/21 aaronlai   增加对已存在chromespy进程的判断
# 2014/04/30 aaronlai   修正frame url信息带","时，查找失败问题
# 2014/05/04 aaronlai   增加对搜索iframe下元素失败时的重试
# 2014/06/04 aaronlai   新增有focused, screenwidth, screenheight等特性
# 2014/06/24 aaronlai   数据驱动支持用例命名
# 2014/07/02 aaronlai   64位环境下，修改获取32位chrome的路径问题
# 2014/07/18 aaronlai   修改_tif的缓存问题
# 2014/08/20 eeelin     新增pyqq
# 2014/08/25 eeelin     新增--target参数表示要生成的目标类型
# 2014/10/30 natusmewei 无py文件打包时加入pypredef文件
# 2015/03/19 eeelin     增加打包qtaf_settings.py
# 2015/05/04 eeelin     代码重构，默认打包带上py文件

import os
import sys
from setuptools import setup, find_packages
from setuptools.command import bdist_egg
from setuptools import Command
from distutils import log
import pypredef

NAME        = "qtaf"

try:
    import _qtaf_version_stub
    VERSION = _qtaf_version_stub.VERSION
except ImportError:
    VERSION     = "5.0.50"

EXCLUDE_ALL_SOURCE = True
EXCLUDE_SOURCES_PACKAGES  = ["pyqq"] #只打包pyc文件的包名，但是会生成对应的pyperdef文件用于支持代码提示
PREDEF_PACKAGES_BLACKLIST = ["pyqq.protocol", r"pyqq.mqlib"] #不需要生成pypredef文件的包名黑名单
FORCE_BUILD_ALL_PREDEFS = True

def get_open_target_modules():
    testbase_exd_names = ["_rscitf", "resource"]
    tuia_ind_names = ["__init__", "testcase", "app", "qpath", "qpathparser", "exceptions", "util", "env", "wintypes"]
    base_dir = os.path.realpath(os.path.dirname(__file__))
    py_modules = []
    
    testbase_dir = os.path.join(base_dir, "testbase")
    for file_name in os.listdir(testbase_dir):
        file_path = os.path.join(testbase_dir, file_name)
        if not file_name.endswith(".py"):
            continue
        name = file_name[:-3]
        if name in testbase_exd_names:
            continue
        if os.path.isfile(file_path):
            #print "++++++++++","testbase.%s"%name
            py_modules.append("testbase.%s"%name)
            
    tuia_dir = os.path.join(base_dir, "tuia")
    for file_name in os.listdir(tuia_dir):
        file_path = os.path.join(tuia_dir, file_name)
        if not file_name.endswith(".py"):
            continue
        name = file_name[:-3]
        if name not in tuia_ind_names:
            continue
        if os.path.isfile(file_path):
            #print "++++++++++","tuia.%s"%name
            py_modules.append("tuia.%s"%name)
    return py_modules
    

TARGET_PACKAGES_DICT = {
    "testbase"  : ["browser", "testbase", "tuia", "winlib"],
    "all"       : ["browser", "testbase", "tuia", "winlib", "pyqq"],
    "open"      : ["tuia/_autoweb"],
}

TARGET_MODULES_DICT = {
    "testbase"  : ["qtaf_settings", "__main__", "drunentry"],
    "all"       : ["qtaf_settings", "__main__", "drunentry"],
    "open"      : ["qtaf_settings", "__main__"] + get_open_target_modules()
}

TARGET_DATA_FILES_DICT = {
    "testbase"  : [],#[("doc", ["doc/qtaf.chm"])],
    "all"       : [],#[("doc", ["doc/qtaf.chm"])],
    "open"      : []
}


    
    

class bdist_qtaf(Command):
    '''扩展bdist_egg的功能
    '''
    description = "create an \"QTAF egg\" distribution"
    
    user_options = [
        ('target=', None,
            "target type of QTAF distribution, could be \"testbase\" or \"all\" (default: all)"),
    ]
    
    boolean_options = []
          
    def initialize_options (self):
        '''增加target参数
        '''
        self.target = 'all'
    
    def finalize_options(self):
        pass
    
    def _list_sub_pkgs(self, packages):
        '''返回包含pkgs和pkgs子包的list
        '''
        pkgs = packages[:]
        for pkg in packages:
            subpkgs = find_packages(pkg)
            for subpkg in subpkgs:
                pkgs.append("%s.%s" % (pkg, subpkg))
        return pkgs

    def _write_version_file(self, bdist_dir):
        '''写入QTAF版本到testbase.version中
        '''
        version_file = os.path.join(bdist_dir, 'testbase', 'version.py')
        with open(version_file, 'w') as fd:
            fd.write("version=\"%s\"\n"%VERSION)
                    
    def run(self):
        '''执行过程
        '''
        packages = TARGET_PACKAGES_DICT.get(self.target, None)
        if packages is None:
            raise RuntimeError("invalid target: \"%s\"" % self.target)
    
        self.distribution.py_modules = TARGET_MODULES_DICT.get(self.target, None)
        self.distribution.data_files = TARGET_DATA_FILES_DICT.get(self.target, None)
        
        self.distribution.packages = self._list_sub_pkgs(packages)
        
        pypredef_packages = []
        if not FORCE_BUILD_ALL_PREDEFS:
            if EXCLUDE_SOURCES_PACKAGES:
                for package in EXCLUDE_SOURCES_PACKAGES:
                    for it in packages:
                        if package.startswith(it):
                            pypredef_packages.append(package)
                            break
        else:
            for package in packages:
                print package
                pypredef_packages.append(package)
        
        for idx, it in enumerate(pypredef_packages):
            pypredef_packages[idx] = it.replace('/', '.')
            
        if pypredef_packages:
            log.info("build .pypredef files from source")
            dst_path = os.path.join(os.getcwd(), 'pypredef')
            self.distribution.data_files += pypredef.build(os.getcwd(), 
                                                           dst_path, 
                                                           pypredef_packages, 
                                                           PREDEF_PACKAGES_BLACKLIST)
                
                
        cmd = self.reinitialize_command("bdist_egg", keep_temp=True, exclude_source_files=EXCLUDE_ALL_SOURCE)
        self.run_command("bdist_egg")
        
        self._write_version_file(cmd.bdist_dir)
        
        if EXCLUDE_SOURCES_PACKAGES:
            log.info("Removing .py files from temporary directory")
            for package in EXCLUDE_SOURCES_PACKAGES:
                filename_perfix = os.path.join(cmd.bdist_dir, package.replace('.', os.path.sep))
                if os.path.isdir(filename_perfix):
                    for base,_,files in os.walk(filename_perfix):
                        for name in files:
                            if name.endswith('.py'):
                                path = os.path.join(base,name)
                                log.debug("Deleting %s", path)
                                os.unlink(path)
                elif os.path.isfile(filename_perfix+'.py'):
                    filepath = filename_perfix+'.py'
                    log.debug("Deleting %s", filepath)
                    os.unlink(filepath)
                    
        # Make the archive, again.
        os.remove(cmd.egg_output)
        filename = '%s-%s-%s-py%s.egg' % (NAME, VERSION, self.target, sys.version[:3])
        egg_output = os.path.join(cmd.dist_dir, filename)
        bdist_egg.make_zipfile(egg_output, cmd.bdist_dir, verbose=cmd.verbose,
                          dry_run=cmd.dry_run, mode=cmd.gen_header())
        bdist_egg.remove_tree(cmd.bdist_dir, dry_run=cmd.dry_run)
        

if __name__ == "__main__":
        
    setup(
      version=VERSION,
      name=NAME,
      cmdclass = {"bdist_qtaf": bdist_qtaf},
      include_package_data=True,
      package_data={'':['*.lib', '*.txt', '*.chm', '*.ini', '*.pyd', '*.tlb', '*.exe', '*.html', '*.dll', '*.dylib'], },
      author="Tencent",
      author_email="t_DBASIC_PQC_QTA@tencent.com",
      license="Copyright(c)2010-2015 Tencent All Rights Reserved. ",
      url="http://km.oa.com/group/QTA",
      requires=["PIL", "comtypes"],
        )
