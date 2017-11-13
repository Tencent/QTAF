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
'''
管理和辅助工具
'''

#2015/10/30 olive 新建

import argparse 
import inspect
import logging
import shlex
import cmd
import sys
import os
import traceback

from testbase import project
from testbase.conf import settings
from testbase.version import version
from testbase.exlib import ExLibManager

class ArgumentParser(object):
    '''参数解析
    '''
    USAGE = """Usage: %(ProgramName)s subcommand [options] [args]

Options:
  -h, --help            show this help message and exit

Type '%(ProgramName)s help <subcommand>' for help on a specific subcommand.

Available subcommands:

%(SubcmdList)s
    
"""

    def __init__(self, subcmd_classes ):
        '''构造函数
        '''
        self.subcmd_classes = subcmd_classes
        self.prog = os.path.basename(sys.argv[0])
        
    def print_help(self):
        '''打印帮助文档
        '''
        logging.info( self.USAGE % {"ProgramName": self.prog, 
                                 "SubcmdList": "\n".join([ '\t%s'%it.name for it in self.subcmd_classes])})
        
    def parse_args(self, args ):
        '''解析参数
        '''
        if len(args) < 1:
            self.print_help()
            sys.exit(1)
            
        subcmd = args[0]
        for it in self.subcmd_classes:
            if it.name == subcmd:
                subcmd_class = it
                parser = it.parser
                break
        else:
            logging.error("invalid subcommand \"%s\"\n" % subcmd )
            sys.exit(1)
            
        ns = parser.parse_args(args[1:])
        subcmd = subcmd_class()
        subcmd.main_parser = self
        return subcmd, ns
        
#     def add_subcommand(self, subcmd, parser ):
#         '''增加一个子命令
#         '''
#         parser.prog = "%s help" % self.prog
#         self._subcmd_parser_dict[subcmd] = parser
        
    def get_subcommand(self, name ):
        '''获取子命令
        '''
        for it in self.subcmd_classes:
            if it.name == name:
                return it()
        
class Command(object):
    '''一个命令
    '''
    name = None
    parser = None
    
    def execute(self, args):
        '''执行过程
        '''
        raise NotImplementedError()

class Help(Command):
    '''帮助命令
    '''   
    name = 'help'
    parser = argparse.ArgumentParser("Display subcommand usage")
    parser.add_argument('subcommand', nargs='?', help="target subcommand to display")

    def execute(self, args):
        '''执行过程
        '''
        if args.subcommand == None:
            self.main_parser.print_help()
        else:
            subcmd = self.main_parser.get_subcommand(args.subcommand)
            subcmd.parser.print_help()
        
class RunScript(Command):
    '''执行一个脚本
    '''
    name = 'runscript'
    parser = argparse.ArgumentParser("Run python script")
    parser.add_argument('script_path', help="target script to run")
    
    def execute(self, args):
        '''执行过程
        '''
        import runpy
        runpy.run_path(args.script_path, run_name='__main__')

class RunTest(Command):
    '''批量执行测试用例
    '''
    name = 'runtest'
    parser = argparse.ArgumentParser("Run QTA testcases")
    parser.add_argument("tests", nargs='*', help="test cases to executive")
    parser.add_argument('-w', default=None, help="working directory to store all result files", dest="working_dir")
    parser.add_argument('-p', default=None, help="test case priorities filter, separate with '/'", dest="priorities")
    parser.add_argument('-s', default=None, help="test case status filter, separate with '/'", dest="status")
    parser.add_argument('-o', default='stream', help="test report type, could be xml, stream or online", dest="report_type")
    parser.add_argument('-x', default='normal', help="test runner type, could be normal, threading or multiprocessing", dest="runner_type")
    parser.add_argument('-j', default=5, help="concurrency to run test case", dest="concurrency", type=int)
    parser.add_argument('-r', default=0, help="retry count while test case failed", dest="retries")
    parser.add_argument('-v', '--verbose', default=False, action='store_true', help="verbose output", dest="verbose")
    parser.add_argument('-n', default=None, help="users split by `;` for online report to notify, used with -o online option", dest="notification")
    
    
    def execute(self, args):
        '''执行过程
        '''      
        from testbase.testcase import TestCase
        from testbase import runner, report
        
        if args.working_dir is None:
            args.working_dir = os.getcwd()
            
        if args.priorities is None:
            priorities = [TestCase.EnumPriority.Low, 
                          TestCase.EnumPriority.Normal, 
                          TestCase.EnumPriority.High, 
                          TestCase.EnumPriority.BVT]
        else:
            priorities = args.priorities.split('/')
            
        if args.status is None:
            status = [TestCase.EnumStatus.Design, 
                      TestCase.EnumStatus.Implement, 
                      TestCase.EnumStatus.Review, 
                      TestCase.EnumStatus.Ready]
        else:
            status = args.status

        test_conf = runner.TestCaseSettings(args.tests, priorities=priorities, status=status)
    
        if args.report_type == 'xml':
            class VerboseXMLTestReport(report.XMLTestReport):
                def log_test_result(self, testcase, testresult ):
                    print ("run test case: %s(pass?:%s)" % (testcase.test_name, testresult.passed))
                    super(VerboseXMLTestReport, self).log_test_result(testcase, testresult)
            report_inst = VerboseXMLTestReport()
            
        elif args.report_type == 'stream':
            report_inst = report.StreamTestReport(output_testresult=args.verbose)
            
        elif args.report_type == 'online':
            class VerboseOnlineTestReport(report.OnlineTestReport):
                def log_test_result(self, testcase, testresult ):
                    print ("run test case: %s(pass?:%s)" % (testcase.test_name, testresult.passed))
                    super(VerboseOnlineTestReport, self).log_test_result(testcase, testresult)
            receivers=args.notification
            if receivers and receivers[-1]!=";":#需要分号结尾
                receivers+=";"
            notification=report.Notification(receivers=receivers)
            report_inst = VerboseOnlineTestReport("调试报告",notification=notification)
            print "报告url: %s" % report_inst.url
            
        else:
            raise ValueError("非法的报告类型:" + str(args.report_type))
        
        if args.runner_type == 'normal':
            runner_inst = runner.TestRunner(report_inst, args.retries)
        elif args.runner_type == 'threading':
            runner_inst = runner.ThreadingTestRunner(report_inst, args.concurrency, args.retries)
        elif args.runner_type == 'multiprocessing':
            runner_inst = runner.MultiProcessTestRunner(report_inst, args.concurrency, args.retries)
        else:
            raise ValueError("非法的执行方式类型:" + str(args.runner_type))
        
        prev_dir = os.getcwd()
        os.chdir(args.working_dir)
        runner_inst.run(test_conf)
        os.chdir(prev_dir)
        if isinstance(report_inst, report.OnlineTestReport):
            if sys.platform == "win32":
                print "opening online report url:%s" % report_inst.url
                os.system("start %s" % report_inst.url)
            else:
                print "online report generated: %s" % report_inst.url
                
        elif isinstance(report_inst, report.XMLTestReport):
            if sys.platform == "win32":
                print "opening XML report with IE..."
                os.system("start iexplore %s" % os.path.realpath("TestReport.xml"))
            else:
                print "XML report generated: %s" % os.path.realpath("TestReport.xml")
                      
class InstallLib(Command):
    '''安装扩展库
    '''
    name = 'installlib'
    parser = argparse.ArgumentParser("Install extend library")
    parser.add_argument("egg_path", help="egg file path")
    
    def execute(self, args):
        '''执行过程
        '''
        ExLibManager(settings.PROJECT_ROOT).install(args.egg_path)

class CreateProject(Command):
    '''创建测试项目
    '''   
    name = 'createproject'
    parser = argparse.ArgumentParser("Create new QTA project")
    parser.add_argument('name', help="project name")
    parser.add_argument('--dest', default=None, help="target path to create project")
    #parser.add_argument('--mode', default="standalone", help="project mode: standard or standalone")
    
    def execute(self, args):
        '''执行过程
        '''
        if args.dest is None:
            dest = os.getcwd()
        else:
            dest = args.dest
        if os.path.isfile(__file__):
            mode = project.EnumProjectMode.Standard
        else:
            mode = project.EnumProjectMode.Standalone
        proj_path = os.path.join(dest, args.name.lower()+'testproj')
        print 'create %s mode test project: %s' % (mode, proj_path)
        project.create_project(proj_path, args.name, mode)
    
class UpgradeProject(Command):
    '''升级测试项目
    '''
    name = 'upgradeproject'
    parser = argparse.ArgumentParser("Upgrade QTA project")
    parser.add_argument('proj_path', help="target path to upgrade project")
    
    def execute(self, args):
        '''执行过程
        '''
        if os.path.isfile(__file__):
            logging.error("should run in egg mode")
            sys.exit(1)
            
        qtaf_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        project.update_project_qtaf(args.proj_path, qtaf_path)
        
class Shell(Command):
    '''Python Shell
    '''
    name = 'shell'
    parser = argparse.ArgumentParser("open python shell")
    
    def execute(self, args):
        '''执行过程
        '''
        try:
            import readline # optional, will allow Up/Down/History in the console
        except ImportError:
            pass
        import code
        varables = globals().copy()
        varables.update(locals())
        shell = code.InteractiveConsole(varables)
        shell.interact()
        
class ManagementToolsConsole(object):
    '''管理工具交互模式
    '''
    prompt = "QTA> "
    
    def __init__(self, argparser ):
        self._argparser = argparser
        
    def cmdloop(self):
        print """QTAF %(qtaf_version)s (test project: %(proj_root)s [%(proj_mode)s mode])\n""" % {
            'qtaf_version': version,
            'proj_root': settings.PROJECT_ROOT,
            'proj_mode': settings.PROJECT_MODE,
        }
        while 1:
            line = raw_input(self.prompt)
            args = shlex.split(line, posix="win" not in sys.platform)
            if not args:
                continue
            subcmd = args[0]
            if not self._argparser.get_subcommand(subcmd):
                sys.stderr.write("invalid command: \"%s\"\n" % subcmd )
                continue
            try:
                subcmd, ns = self._argparser.parse_args(args)
                subcmd.execute(ns)
            except SystemExit:
                print "command exit"
            except:
                traceback.print_exc()

class ManagementTools(object):
    '''管理工具类入口
    '''
    excluded_command_types = [CreateProject, UpgradeProject]
    
    def __init__(self):
        if settings.PROJECT_MODE == project.EnumProjectMode.Standard:
            self.excluded_command_types.append(InstallLib)
        
    def _load_cmds(self):
        '''加载全部的命令
        '''            
        cmds = []
        cmds += self._load_cmd_from_module(sys.modules[__name__])
        cmds += self._load_app_cmds()
        return cmds
        
    def _load_cmd_from_module(self, mod ):
        '''加载一个模块里面的全部命令
        '''
        cmds = []
        for objname in dir(mod):
            obj = getattr(mod, objname)
            if not inspect.isclass(obj):
                continue
            if obj == Command:
                continue
            if obj in self.excluded_command_types:
                continue
            if issubclass(obj, Command):
                cmds.append(obj)
                
        cmds.sort(lambda x,y:cmp(x.name, y.name))    
        return cmds
    
    def _load_app_cmds(self):
        '''从应用lib中加载命令
        '''
        cmds = []
        for libname in settings.INSTALLED_APPS:
            if not libname:
                continue
            modname = '%s.cmds' % libname
            try:
                __import__(modname)
            except ImportError:
                continue
            else:
                for cmd in self._load_cmd_from_module(sys.modules[modname]):
                    cmd.name = libname + '.' + cmd.name
                    cmds.append(cmd)
        return cmds 
        
    def run(self):
        '''执行入口
        '''
        logging.root.addHandler(logging.StreamHandler())
        logging.root.level = logging.INFO
        cmds = self._load_cmds()
        argparser = ArgumentParser(cmds)
        if len(sys.argv) > 1:
            subcmd, args = argparser.parse_args(sys.argv[1:])
            subcmd.execute(args)
        else:
            ManagementToolsConsole(argparser).cmdloop()
            
            
            
def qta_manage_main():
    '''qta-manage工具入口
    '''
    logging.root.addHandler(logging.StreamHandler())
    logging.root.level = logging.INFO
    use_egg = not os.path.isfile(__file__)
    if use_egg:
        cmds = [CreateProject, UpgradeProject, Help]
    else:
        cmds = [CreateProject, Help]
    argparser = ArgumentParser(cmds)
    subcmd, args = argparser.parse_args(sys.argv[1:])
    subcmd.execute(args)
    
