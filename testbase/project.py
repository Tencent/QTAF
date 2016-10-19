# -*- coding: utf-8 -*-
'''测试项目接口
'''

#2015/04/28 eeelin 新建

import os
import codecs
import datetime
import zipfile
import getpass
import zipimport 
import shutil
import xml.dom.minidom as dom
from testbase.conf import settings

INITPY_CONTENT = """# -*- coding: utf-8 -*-
'''%(Doc)s
'''
#%(Date)s QTAF自动生成
"""

SETTINGS_CONTENT = """# -*- coding: utf-8 -*-
'''测试项目配置文件
'''
#%(Date)s QTAF自动生成

PROJECT_NAME = "%(ProjectName)s"
"""

RUNNER_CONTENT = """# -*- coding: utf-8 -*-
'''本地执行使用的Runner
'''
#%(Date)s QTAF自动生成

import sys
import os

proj_root = os.path.dirname(os.path.dirname(__file__))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)
exlib_dir = os.path.join(proj_root, 'exlib') 
for filename in os.listdir(exlib_dir):
    if filename.endswith('.egg'):
        lib_path = os.path.join(exlib_dir, filename)
        if os.path.isfile(lib_path) and lib_path not in sys.path:
            sys.path.insert(0, lib_path)

import getopt
from testbase.testcase import TestCase
from testbase.loader import TestLoader
from testbase import report
from testbase import runner

USAGE = '''\
用法: testrunner.py [选项] 测试用例

测试用例：
    指定测试用例集，多个测试用例集用空格隔开，如"qqtest.mainpanel qqtest.login.LoginTest"

选项：
  -h               显示本帮助信息
  -w  WorkingDir   设置工作目录。默认的工作目录是当前目录. 测试结果文件为TestReport.xml
  -p  Priorities   指定测试用例优先级，以“/”隔开. 如“High/Low”.  
  -s  Status       指定测试用例状态，以"/"隔开，如“Implement/Ready”
  -o  ReportType   指定测试报告类型，目前支持的类型有xml、stream和online. 默认为stream
  -r  RunnerType   指定用例执行方式，目前支持的类型有normal、threading和multiprocessing. 默认为normal
  -l  parallel     指定并发执行的数目，仅当类型为threading和multiprocessing的执行方式有效，默认为5
  -n  retries      指定用例失败重跑次数，默认为0，也就是不重跑

例子:
  testrunner.py -p High/Low qqtest.mainpanel qqtest.login.LoginTest
       
        运行qqtest.mainpanel模块和qqtest.login.LoginTest类下，作者为allenpan或eeelin，优先级为High和Low的测试用例.
  
'''

def print_usage():
    '''输出帮助文档
    '''
    enc = sys.stdout.encoding
    if enc is None:
        msg = USAGE
    else:
        msg = USAGE.decode('utf8').encode(enc)
    print msg
    
def program_main():
    '''主过程
    '''
    argv = sys.argv
    working_dir = os.getcwd()
    priorities = [TestCase.EnumPriority.Low, 
                  TestCase.EnumPriority.Normal, 
                  TestCase.EnumPriority.High, 
                  TestCase.EnumPriority.BVT]
    status = [TestCase.EnumStatus.Design, 
              TestCase.EnumStatus.Implement, 
              TestCase.EnumStatus.Review, 
              TestCase.EnumStatus.Ready]
    report_type = 'stream'
    runner_type = 'normal'
    parallel = 5
    retries = 0
    
    try:
        options, args = getopt.getopt(argv[1:], 'hw:p:s:o:r:l:n:')
        for opt, value in options:
            if opt in ('-h'):
                print_usage()
                sys.exit(0)
            if opt in ('-w'):
                os.chdir(value)
                working_dir = value
            if opt in ('-p'):
                priorities = value.split('/')
            if opt in ('-s'):
                status = value.split('/')
            if opt in ('-o'):
                report_type = value.lower()
            if opt in ('-r'):
                runner_type = value.lower()
            if opt in ('-l'):
                parallel = int(value)
            if opt in ('-n'):
                retries = int(value)
                
        if len(args) == 0:
            print_usage()
            sys.exit(0)
        else:
            testnames = args

    except getopt.error:
        print_usage()
        sys.exit(0)
    
    os.chdir(working_dir)

    test_conf = runner.TestCaseSettings(testnames, priorities=priorities, status=status)
    
    if report_type == 'xml':
        report_inst = report.XMLTestReport()
    elif report_type == 'stream':
        report_inst = report.StreamTestReport()
    elif report_type == 'online':
        report_inst = report.OnlineTestReport("调试报告")
    else:
        raise ValueError("非法的报告类型:" + str(report_type))
    
    if runner_type == 'normal':
        runner_inst = runner.TestRunner(report_inst, retries)
    elif runner_type == 'threading':
        runner_inst = runner.ThreadingTestRunner(report_inst, parallel, retries)
    elif runner_type == 'multiprocessing':
        runner_inst = runner.MultiProcessTestRunner(report_inst, parallel, retries)
    else:
        raise ValueError("非法的执行方式类型:" + str(runner_type))
    
    runner_inst.run(test_conf)
    if isinstance(report_inst, report.OnlineTestReport):
        print report_inst.url
    
if __name__ == '__main__':
    try:
        program_main()
    except SystemExit:
        pass
    except:
        import traceback
        enc = sys.stderr.encoding
        if enc is None:
            sys.stderr.write(traceback.format_exc())
        else:
            sys.stderr.write(traceback.format_exc().decode('utf8').encode(enc))
        
"""

TESTCASE_CONTENT = """# -*- coding: utf-8 -*-
'''示例测试用例
'''
#%(Date)s QTAF自动生成

from %(ProjectName)slib.testcase import %(ProjectNameCapUp)sTestCase

class HelloTest(%(ProjectNameCapUp)sTestCase):
    '''示例测试用例
    '''
    owner = "%(UserName)s"
    timeout = 5
    priority = %(ProjectNameCapUp)sTestCase.EnumPriority.High
    status = %(ProjectNameCapUp)sTestCase.EnumStatus.Design
    
    def run_test(self):
        self.log_info("hello testcase")
        self.assert_equal(True, True)
    
if __name__ == '__main__':
    HelloTest().debug_run()

"""

TESTLIB_CONTENT = """# -*- coding: utf-8 -*-
'''示例测试用例
'''
#%(Date)s QTAF自动生成

from testbase import testcase

class %(ProjectNameCapUp)sTestCase(testcase.TestCase):
    '''%(ProjectName)s测试用例基类
    '''
    pass
"""

MANAGE_CONTENT = """# -*- coding: utf-8 -*-
'''
项目管理和辅助工具
'''
#%(Date)s QTAF自动生成

import sys
import os

proj_root = os.path.realpath(os.path.dirname(__file__))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)
exlib_dir = os.path.join(proj_root, 'exlib') 
for filename in os.listdir(exlib_dir):
    if filename.endswith('.egg'):
        lib_path = os.path.join(exlib_dir, filename)
        if os.path.isfile(lib_path) and lib_path not in sys.path:
            sys.path.insert(0, lib_path)
            
from testbase.management import ManagementTools

if __name__ == '__main__':    
    ManagementTools().run()
"""

ECLIPSE_PROJ_CONTENT = """<?xml version="1.0" encoding="UTF-8"?>
<projectDescription>
    <name>%(ProjectName)stestproj</name>
    <comment></comment>
    <projects>
    </projects>
    <buildSpec>
        <buildCommand>
            <name>org.python.pydev.PyDevBuilder</name>
            <arguments>
            </arguments>
        </buildCommand>
    </buildSpec>
    <natures>
        <nature>org.python.pydev.pythonNature</nature>
    </natures>
</projectDescription>
"""

PYDEV_CONF_CONTENT = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<?eclipse-pydev version="1.0"?><pydev_project>
<pydev_property name="org.python.pydev.PYTHON_PROJECT_INTERPRETER">Default</pydev_property>
<pydev_property name="org.python.pydev.PYTHON_PROJECT_VERSION">python 2.7</pydev_property>
<pydev_pathproperty name="org.python.pydev.PROJECT_SOURCE_PATH">
<path>/${PROJECT_DIR_NAME}</path>
<path>/${PROJECT_DIR_NAME}/exlib/%(EggName)s</path>
</pydev_pathproperty>
</pydev_project>
"""

def _get_project_root():
    '''获取当前项目的根目录
    '''
    if os.path.isfile(__file__): #没使用egg包
        return os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
    else: #使用的egg包
        qtaf_top_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
        return os.path.realpath(os.path.join(qtaf_top_dir, '..', '..'))
    
class TestProject(object):
    '''测试项目
    '''
    def __init__(self, root, name, readonly=True ):
        '''构造函数
        :param root: 项目根目录
        :type root: string
        :param name: 项目名称
        :type name: string
        :param readonly: 是否只读
        :type readonly: boolean
        '''
        self._root = root
        self._name = name.lower()
        self._readonly = readonly
        if os.path.isfile(__file__):
            raise RuntimeError("should run in egg mode")
        self._egg_path = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
        
    @property
    def name(self):
        '''测试项目名称
        '''    
        return self._name
    
    @property
    def path(self):
        '''测试项目根目录
        '''
        return self._root
    
    @property
    def qtaf_version(self):
        '''使用的QTAF的版本
        '''
        importer = zipimport.zipimporter(os.path.join(self.path, 'exlib', 'qtaf.egg', 'testbase'))
        m = importer.load_module("version")
        return m.version
            
    def upgrade_qtaf(self, egg_path ):
        '''更新QTAF
        :param egg_path: 新的QTAF.egg包
        :type egg_path: string
        '''
        exlib_dir = os.path.join(self.path, 'exlib')
        for name in os.listdir(exlib_dir):
            if name.startswith('qtaf-') and name.endswith('.egg'):
                os.remove(os.path.join(exlib_dir, name))        
        self._copy_qtaf_egg(exlib_dir)
        self._update_pydev_conffile(os.path.basename(egg_path))
        
    def initialize(self):
        '''初始化测试项目，创建测试项目标准目录结构
        '''
        if self._readonly:
            raise RuntimeError("read only")
    
        if not os.path.isdir(self.path):
            os.makedirs(self.path)
            
#         bin_dir = os.path.join(self.path, 'bin')
#         if not os.path.isdir(bin_dir):
#             os.mkdir(bin_dir)
            
        lib_dir = os.path.join(self.path, '%slib' % self.name)
        if not os.path.isdir(lib_dir):
            os.mkdir(lib_dir)
            self._create_initpy(lib_dir, "测试lib")
            self._create_sample_lib(lib_dir)
            
        case_dir = os.path.join(self.path, '%stest' % self.name)
        if not os.path.isdir(case_dir):
            os.mkdir(case_dir)
            self._create_initpy(case_dir, "测试用例")
            self._create_sample_test(case_dir)
            
#         run_dir = os.path.join(self.path, 'runner')
#         if not os.path.isdir(run_dir):
#             os.mkdir(run_dir)
#             self._create_testrunner(run_dir)
            
        exlib_dir = os.path.join(self.path, 'exlib')
        if not os.path.isdir(exlib_dir):
            os.mkdir(exlib_dir)
            self._copy_qtaf_egg(exlib_dir)
            
        self._create_settingspy()
        self._create_managepy()
        self._create_eclipse_projfile()
        self._create_pydev_conffile()
        
    def _create_initpy(self, dir_path, doc ):
        '''创建一个__init__.py
        '''
        with codecs.open(os.path.join(dir_path, '__init__.py'), 'w') as fd:
            fd.write(INITPY_CONTENT % {"Doc":doc, "Date":datetime.date.today().strftime('%Y/%m/%d')})
            
    def _create_settingspy(self):
        '''创建settings.py文件
        '''
        with codecs.open(os.path.join(self.path, 'settings.py'), 'w') as fd:
            fd.write(SETTINGS_CONTENT % {"Date":datetime.date.today().strftime('%Y/%m/%d'),
                                         "ProjectName":self.name})
        
    def _create_managepy(self):
        '''创建manage.py文件
        '''
        with codecs.open(os.path.join(self.path, 'manage.py'), 'w') as fd:
            fd.write(MANAGE_CONTENT % {"Date":datetime.date.today().strftime('%Y/%m/%d')})
        
    def _create_sample_test(self, dir_path ):
        '''创建示例测试用例
        '''
        with codecs.open(os.path.join(dir_path, 'hello.py'), 'w') as fd:
            fd.write(TESTCASE_CONTENT % {"Date":datetime.date.today().strftime('%Y/%m/%d'),
                                         "ProjectName":self.name,
                                         "ProjectNameCapUp":self.name[0].upper()+self.name[1:],
                                         "UserName":getpass.getuser()})
            
    def _create_sample_lib(self, dir_path ):
        '''创建示例lib
        '''
        with codecs.open(os.path.join(dir_path, 'testcase.py'), 'w') as fd:
            fd.write(TESTLIB_CONTENT % {"Date":datetime.date.today().strftime('%Y/%m/%d'),
                                         "ProjectName":self.name,
                                         "ProjectNameCapUp":self.name[0].upper()+self.name[1:]})
    
#     def _create_testrunner(self, dir_path ):
#         '''创建testrunner.py
#         '''
#         with codecs.open(os.path.join(dir_path, 'testrunner.py'), 'w') as fd:
#             fd.write(RUNNER_CONTENT % {"Date":datetime.date.today().strftime('%Y/%m/%d'),
#                                        "TestName":self.name+"test"})
    
        
    def _copy_qtaf_egg(self, dir_path ):
        '''拷贝QTAF egg包
        '''
        shutil.copy(self._egg_path, dir_path)
        with zipfile.ZipFile(self._egg_path) as zfile:
            try:
                zfile.getinfo("doc/qtaf.chm") #chm可能不存在
            except KeyError:
                return
            else:
                with open(os.path.join(dir_path, "qtaf.chm"), 'wb') as fd:
                    fd.write(zfile.read("doc/qtaf.chm"))
        
    def _create_eclipse_projfile(self):
        '''创建eclispe项目文件
        '''
        with codecs.open(os.path.join(self.path, '.project'), 'w') as fd:
            fd.write(ECLIPSE_PROJ_CONTENT % {"ProjectName":self.name})
    
    def _create_pydev_conffile(self):
        '''创建pydev配置文件
        '''
        with codecs.open(os.path.join(self.path, '.pydevproject'), 'w') as fd:
            fd.write(PYDEV_CONF_CONTENT % {"EggName":os.path.basename(self._egg_path)})
            
    def _update_pydev_conffile(self, egg_name ):
        '''更新pydev配置文件中的Egg名称
        '''
        with open(os.path.join(self.path, '.pydevproject'), 'r') as fd:
            doc = dom.parse(fd)
            nodes = doc.getElementsByTagName('pydev_pathproperty')
            if len(nodes) == 0:
                propsnode = doc.createElement("pydev_pathproperty")
                propsnode.setAttribute("name", "org.python.pydev.PROJECT_SOURCE_PATH")                
            else:
                propsnode = nodes[0]
                for pathnode in propsnode.getElementsByTagName("path"):
                    rc = []
                    for node in pathnode.childNodes:
                        if node.nodeType == node.TEXT_NODE:
                            rc.append(node.data)
                    path = ''.join(rc)
                    if path.endswith('.egg') and 'qtaf-' in path:
                        propsnode.removeChild(pathnode)
                        break            
            pathnode = doc.createElement("path")
            pathnode.appendChild(doc.createTextNode("/${PROJECT_DIR_NAME}/exlib/%s"%egg_name))
            propsnode.appendChild(pathnode)
                    
        with codecs.open(os.path.join(self.path, '.pydevproject'), 'w', 'utf8') as fd:
            fd.write(doc.toxml(encoding='UTF-8'))

def current_project():
    '''返回当前测试项目
    '''    
    return TestProject(_get_project_root(), settings.PROJECT_NAME)
    