# -*- coding: utf-8 -*-
'''
管理和辅助工具
'''

#2015/10/30 eeelin 新建

import argparse 
import inspect
import logging
import sys
import os

from testbase import project
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
        return subcmd_class(), ns
        
    def add_subcommand(self, subcmd, parser ):
        '''增加一个子命令
        '''
        parser.prog = "%s help" % self.prog
        self._subcmd_parser_dict[subcmd] = parser
        
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
    parser.add_argument('subcommand', help="target subcommand to display")
    
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
    parser.add_argument('-j', default=5, help="concurrency to run test case", dest="concurrency")
    parser.add_argument('-r', default=0, help="retry count while test case failed", dest="retries")
              
    def execute(self, args):
        '''执行过程
        '''      
        from testbase.testcase import TestCase
        from testbase.conf import settings
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
            status = args.status.split('/')

        test_conf = runner.TestCaseSettings(args.tests, priorities=priorities, status=status)
    
        if args.report_type == 'xml':
            report_inst = report.XMLTestReport()
        elif args.report_type == 'stream':
            report_inst = report.StreamTestReport()
        elif args.report_type == 'online':
            # 对应报告平台中的产品名称
            product = report.Product(settings.get('PRODUCT_NAME', 'Unknown'))
            report_inst = report.OnlineTestReport("本地调试", product=product)
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
            print report_inst.url
          
class InstallLib(Command):
    '''安装扩展库
    '''
    name = 'installlib'
    parser = argparse.ArgumentParser("Install extend library")
    parser.add_argument("egg_path", help="egg file path")
    
    def execute(self, args):
        '''执行过程
        '''
        ExLibManager().install(args.egg_path)
        
class ManagementTools(object):
    '''管理工具类入口
    '''
    def _load_cmds(self):
        '''加载全部的命令
        '''            
        cmds = []
        from testbase import management
        cmds += self._load_cmd_from_module(management)
        cmds += self._load_libs_cmds()
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
            if issubclass(obj, Command):
                cmds.append(obj)
                
        cmds.sort(lambda x,y:cmp(x.name, y.name))    
        return cmds
    
    def _load_libs_cmds(self):
        '''从lib中加载命令
        '''
        cmds = []
        for libname in ExLibManager().list_names():
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
        argparser = ArgumentParser(self._load_cmds())
        subcmd, args = argparser.parse_args(sys.argv[1:])
        subcmd.execute(args)
        
