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
"""
管理和辅助工具
"""

import argparse 
import inspect
import logging
import os
import traceback
import sys
import shlex
import six

from testbase import project
from testbase.conf import settings
from testbase.version import version
from testbase.exlib import ExLibManager
from testbase.dist import DistGenerator, VirtuelEnv
from testbase.testcase import TestCasePriority, TestCaseStatus
from testbase.runner import TestCaseSettings, runner_types
from testbase.report import report_types
from testbase.resource import resmgr_backend_types


class ArgumentParser(object):
    """参数解析
    """
    USAGE = """Usage: %(ProgramName)s subcommand [options] [args]

Options:
  -h, --help            show this help message and exit

Type '%(ProgramName)s help <subcommand>' for help on a specific subcommand.

Available subcommands:

%(SubcmdList)s
    
"""

    def __init__(self, subcmd_classes ):
        """构造函数
        """
        self.subcmd_classes = subcmd_classes
        self.prog = os.path.basename(sys.argv[0])
        
    def print_help(self):
        """打印帮助文档
        """
        logging.info( self.USAGE % {"ProgramName": self.prog, 
                                 "SubcmdList": "\n".join([ '\t%s'%it.name for it in self.subcmd_classes])})
        
    def parse_args(self, args ):
        """解析参数
        """
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
#         """增加一个子命令
#         """
#         parser.prog = "%s help" % self.prog
#         self._subcmd_parser_dict[subcmd] = parser
        
    def get_subcommand(self, name ):
        """获取子命令
        """
        for it in self.subcmd_classes:
            if it.name == name:
                return it()


class Command(object):
    """一个命令
    """
    name = None
    parser = None
    
    def execute(self, args):
        """执行过程
        """
        raise NotImplementedError()


class Help(Command):
    """帮助命令
    """   
    name = 'help'
    parser = argparse.ArgumentParser("Display subcommand usage")
    parser.add_argument('subcommand', nargs='?', help="target subcommand to display")

    def execute(self, args):
        """执行过程
        """
        if args.subcommand == None:
            self.main_parser.print_help()
        else:
            subcmd = self.main_parser.get_subcommand(args.subcommand)
            subcmd.parser.print_help()


class RunScript(Command):
    """执行一个脚本
    """
    name = 'runscript'
    parser = argparse.ArgumentParser("Run python script")
    parser.add_argument('script_path', help="target script to run")
    
    def execute(self, args):
        """执行过程
        """
        import runpy
        runpy.run_path(args.script_path, run_name='__main__')


class RunTest(Command):
    """批量执行测试用例
    """
    name = 'runtest'
    parser = argparse.ArgumentParser("Run QTA testcases")
    parser.add_argument("tests", metavar="TEST", nargs='*', help="testcase set to executive, eg: zoo.xxx.HelloTest")
    parser.add_argument('-w', '--working-dir', default=None, help="working directory to store all result files", dest="working_dir")
    parser.add_argument('--priority', help="run test cases with specific priority, accept multiple options", 
                        dest="priorities", action="append",
                        choices=[TestCasePriority.BVT,TestCasePriority.High,TestCasePriority.Normal,TestCasePriority.Low])
    parser.add_argument('--status', default=None, help="run test cases with specific status, accept multiple options", 
                        dest="status", action="append",
                        choices=[TestCaseStatus.Design,TestCaseStatus.Implement,TestCaseStatus.Ready,TestCaseStatus.Review,TestCaseStatus.Suspend])
    parser.add_argument("--excluded-name", help="exclude test cases with specific name prefix , accept multiple options",
                        action="append", dest="excluded_names", metavar="EXCLUDED_NAME")
    parser.add_argument("--owner", help="run test cases with specific owner, accept multiple options",
                        action="append", dest="owners", metavar="OWNER")
    parser.add_argument("--tag", help="run test cases with specific tag, accept multiple options", 
                        action="append", dest="tags", metavar="TAG")
    parser.add_argument("--excluded-tag", help="exclude test cases with specific name tag, accept multiple options",
                        action="append", dest="excluded_tags", metavar="EXCLUDED_TAG")
    
    parser.add_argument("--report-type", help="report type", choices=report_types.keys(), default="stream")
    parser.add_argument("--report-args", help="additional arguments for specific report", default="")
    parser.add_argument("--report-args-help", help="show help information for specific report arguemnts", choices=report_types.keys())
  
    parser.add_argument("--resmgr-backend-type", help="test resource manager backend type", choices=resmgr_backend_types.keys(), default="local")
    
    parser.add_argument("--runner-type", help="test runner type", choices=runner_types.keys(), default="basic")
    parser.add_argument("--runner-args", help="additional arguments for specific runner", default="")
    parser.add_argument("--runner-args-help", help="show help information for specific runner arguemnts", choices=runner_types.keys())
     

    def execute(self, args):
        """执行过程
        """
        if args.report_args_help:
            report_types[args.report_args_help].get_parser().print_help()
            return
        if args.runner_args_help:
            runner_types[args.runner_args_help].get_parser().print_help()
            return
        if not args.tests:
            print("no test set specified")
            exit(1)
        
        from testbase.testcase import TestCase
        
        if args.working_dir is None:
            args.working_dir = os.getcwd()
            
        priorities = args.priorities or [TestCase.EnumPriority.Low, 
                                          TestCase.EnumPriority.Normal, 
                                          TestCase.EnumPriority.High, 
                                          TestCase.EnumPriority.BVT]
            
        status = args.status or [TestCase.EnumStatus.Design, 
                                  TestCase.EnumStatus.Implement, 
                                  TestCase.EnumStatus.Review, 
                                  TestCase.EnumStatus.Ready]

        test_conf = TestCaseSettings(names=args.tests,
                                    excluded_names=args.excluded_names,
                                    priorities=priorities, 
                                    status=status,
                                    owners=args.owners,
                                    tags=args.tags,
                                    excluded_tags=args.excluded_tags)
    
        report_type = report_types[args.report_type]
        if args.report_type == 'xml':
            class VerboseXMLTestReport(report_types[args.report_type]):
                def log_test_result(self, testcase, testresult ):
                    print ("run test case: %s(pass?:%s)" % (testcase.test_name, testresult.passed))
                    super(VerboseXMLTestReport, self).log_test_result(testcase, testresult)
            report_type = VerboseXMLTestReport
            
        elif args.report_type == 'online':
            class VerboseOnlineTestReport(report_types[args.report_type]):
                def log_test_result(self, testcase, testresult ):
                    print ("run test case: %s(pass?:%s)" % (testcase.test_name, testresult.passed))
                    super(VerboseOnlineTestReport, self).log_test_result(testcase, testresult)
                def begin_report(self):
                    super(VerboseOnlineTestReport,self).begin_report()
                    with open(os.path.join(os.getcwd(),"report_url.txt"),"w") as fd:
                        fd.write(self.url)
            report_type = VerboseOnlineTestReport
            
        report_inst = report_type.parse_args(shlex.split(args.report_args))        
        resmgr_backend = resmgr_backend_types[args.resmgr_backend_type]()
        
        runner_type = runner_types[args.runner_type]
        runner = runner_type.parse_args(shlex.split(args.runner_args), report_inst, resmgr_backend)
        
        prev_dir = os.getcwd()
        os.chdir(args.working_dir)
        runner.run(test_conf)
        os.chdir(prev_dir)
        if args.report_type == 'online':
            if sys.platform == "win32":
                print("opening online report url:%s" % report_inst.url)
                os.system("start %s" % report_inst.url)
            else:
                print("online report generated: %s" % report_inst.url)
                
        elif args.report_type == 'xml':
            if sys.platform == "win32":
                print("opening XML report with IE...")
                report_xml = os.path.abspath(os.path.join(args.working_dir, "TestReport.xml"))
                os.system("start iexplore %s" % report_xml)
            else:
                print("XML report generated: %s" % os.path.abspath("TestReport.xml"))

class RunPlan(Command):
    """执行测试计划
    """
    name = "runplan"
    parser = argparse.ArgumentParser("Run QTA test plan")
    parser.add_argument("--report-type", help="report type", choices=report_types.keys(), default="stream")
    parser.add_argument("--report-args", help="additional arguments for specific report", default="")
    parser.add_argument("--report-args-help", help="show help information for specific report arguemnts", choices=report_types.keys())
  
    parser.add_argument("--runner-type", help="test runner type", choices=runner_types.keys(), default="basic")
    parser.add_argument("--runner-args", help="additional arguments for specific runner", default="")
    parser.add_argument("--runner-args-help", help="show help information for specific runner arguemnts", choices=runner_types.keys())

    parser.add_argument("--resmgr-backend-type", help="test resource manager backend type", choices=resmgr_backend_types.keys(), default="local")

    parser.add_argument("plan", help="designate a test plan to run")

    def execute(self, args):
        """执行过程
        """
        if args.report_args_help:
            report_types[args.report_args_help].get_parser().print_help()
            return
        if args.runner_args_help:
            runner_types[args.runner_args_help].get_parser().print_help()
            return
            
        report_type = report_types[args.report_type]
        report = report_type.parse_args(shlex.split(args.report_args))

        resmgr_backend = resmgr_backend_types[args.resmgr_backend_type]()

        runner_type = runner_types[args.runner_type]
        runner = runner_type.parse_args(shlex.split(args.runner_args), report, resmgr_backend)

        planname = args.plan
        planmodulename, planclsname = planname.rsplit(".", 1)
        __import__(planmodulename)
        planmod = sys.modules[planmodulename]
        plancls = getattr(planmod, planclsname)
        runner.run(plancls())

class InstallLib(Command):
    """安装扩展库
    """
    name = 'installlib'
    parser = argparse.ArgumentParser("Install extend library")
    parser.add_argument("egg_path", help="egg file path")
    
    def execute(self, args):
        """执行过程
        """
        ExLibManager(settings.PROJECT_ROOT).install(args.egg_path)


class CreateProject(Command):
    """创建测试项目
    """   
    name = 'createproject'
    parser = argparse.ArgumentParser("Create new QTA project")
    parser.add_argument('name', help="project name")
    parser.add_argument('--dest', default=None, help="target path to create project")
    #parser.add_argument('--mode', default="standalone", help="project mode: standard or standalone")
    
    def execute(self, args):
        """执行过程
        """
        if args.dest is None:
            dest = os.getcwd()
        else:
            dest = args.dest
        if os.path.isfile(__file__):
            mode = project.EnumProjectMode.Standard
        else:
            mode = project.EnumProjectMode.Standalone
        proj_path = os.path.join(dest, args.name.lower()+'testproj')
        print('create %s mode test project: %s' % (mode, proj_path))
        project.create_project(proj_path, args.name, mode)


class UpgradeProject(Command):
    """升级测试项目
    """
    name = 'upgradeproject'
    parser = argparse.ArgumentParser("Upgrade QTA project")
    parser.add_argument('proj_path', help="target path to upgrade project")
    
    def execute(self, args):
        """执行过程
        """
        if os.path.isfile(__file__):
            logging.error("should run in egg mode")
            sys.exit(1)
            
        qtaf_path = os.path.dirname(os.path.abspath(__file__))
        project.update_project_qtaf(args.proj_path, qtaf_path)


class Shell(Command):
    """Python Shell
    """
    name = 'shell'
    parser = argparse.ArgumentParser("open python shell")
    
    def execute(self, args):
        """执行过程
        """
        try:
            import readline # optional, will allow Up/Down/History in the console
        except ImportError:
            pass
        import code
        varables = globals().copy()
        varables.update(locals())
        shell = code.InteractiveConsole(varables)
        shell.interact()


class Distribute(Command):
    """Generate distribution packages
    """
    name = 'dist'
    parser = argparse.ArgumentParser("Generate distribution packages")
    parser.add_argument("--version", help="assign distribution version", default="1.0.0")
    parser.add_argument("--exclude-resources", action="store_true", help="do not package resource data in package", default=False)

    def execute(self, args):
        DistGenerator(args.version).run(args.exclude_resources)


class RunTestDistPackage(Command):
    """Run tests in distribution package
    """
    name = "runtest"
    parser = argparse.ArgumentParser("Run tests in distribution package")
    parser.add_argument("--recreate-venv", action="store_true", help="force recreate virtualenv")
    parser.add_argument("--venv", help="designate virtualenv path manually")

    parser.add_argument("--priority", help="run test cases with specific priority, accept multiple options", 
                        choices=[TestCasePriority.BVT, TestCasePriority.High, TestCasePriority.Normal, TestCasePriority.Low],
                        action="append", dest="priorities")
    parser.add_argument("--status", help="run test cases with specific status, accept multiple options",
                        choices=[TestCaseStatus.Design, TestCaseStatus.Implement, TestCaseStatus.Ready, TestCaseStatus.Review, TestCaseStatus.Suspend],
                        action="append", dest="status")
    parser.add_argument("--owner", help="run test cases with specific owner, accept multiple options", action="append", dest="owners")
    parser.add_argument("--excluded-name", help="exclude test cases with specific name prefix , accept multiple options", action="append", dest="excluded_names")
    parser.add_argument("--tag", help="run test cases with specific tag, accept multiple options", action="append", dest="tags")
    parser.add_argument("--excluded-tag", help="exclude test cases with specific name tag , accept multiple options", action="append", dest="excluded_tags")
    
    parser.add_argument("--report-type", help="report type", choices=report_types.keys(), default="stream")
    parser.add_argument("--report-args", help="additional arguments for specific report", default="")
    parser.add_argument("--report-args-help", help="show help information for specific report arguemnts", choices=report_types.keys())
  
    parser.add_argument("--runner-type", help="test runner type", choices=runner_types.keys(), default="basic")
    parser.add_argument("--runner-args", help="additional arguments for specific runner", default="")
    parser.add_argument("--runner-args-help", help="show help information for specific runner arguemnts", choices=runner_types.keys())

    parser.add_argument("--resmgr-backend-type", help="test resource manager backend type", choices=resmgr_backend_types.keys(), default="local")

    parser.add_argument("--disable-run-on-child", help="do not create child process to run", action="store_true")

    parser.add_argument("package", help="QTA sdist package")
    parser.add_argument("tests", nargs='*', help="designate test names to run")

    def execute(self, args):
        if args.report_args_help:
            report_types[args.report_args_help].get_parser().print_help()
            return
        if args.runner_args_help:
            runner_types[args.runner_args_help].get_parser().print_help()
            return

        venv = VirtuelEnv(
            args.package, 
            args.venv,
            args.recreate_venv)
        venv.activate()

        report_type = report_types[args.report_type]
        report = report_type.parse_args(shlex.split(args.report_args))

        resmgr_backend = resmgr_backend_types[args.resmgr_backend_type]()

        runner_type = runner_types[args.runner_type]
        runner_args = args.runner_args + " " # incase user input has no space
        runner = runner_type.parse_args(shlex.split(runner_args), report, resmgr_backend)

        test = TestCaseSettings(
                args.tests, 
                args.excluded_names, 
                args.priorities, 
                args.status, 
                args.owners,
                args.tags,
                args.excluded_tags)

        runner.run(test)

class RunPlanDistPackage(Command):
    """Run test plan in distribution package
    """
    name = "runplan"
    parser = argparse.ArgumentParser("Run test plan in distribution package")
    parser.add_argument("--recreate-venv", action="store_true", help="force recreate virtualenv")
    parser.add_argument("--venv", help="designate virtualenv path manually")

    parser.add_argument("--report-type", help="report type", choices=report_types.keys(), default="stream")
    parser.add_argument("--report-args", help="additional arguments for specific report", default="")
    parser.add_argument("--report-args-help", help="show help information for specific report arguemnts", choices=report_types.keys())
  
    parser.add_argument("--runner-type", help="test runner type", choices=runner_types.keys(), default="basic")
    parser.add_argument("--runner-args", help="additional arguments for specific runner", default="")
    parser.add_argument("--runner-args-help", help="show help information for specific runner arguemnts", choices=runner_types.keys())

    parser.add_argument("--resmgr-backend-type", help="test resource manager backend type", choices=resmgr_backend_types.keys(), default="local")

    parser.add_argument("--disable-run-on-child", help="do not create child process to run", action="store_true")

    parser.add_argument("package", help="QTA sdist package")
    parser.add_argument("plan", help="designate a test plan to run")

    def execute(self, args):
        if args.report_args_help:
            report_types[args.report_args_help].get_parser().print_help()
            return
        if args.runner_args_help:
            runner_types[args.runner_args_help].get_parser().print_help()
            return

        venv = VirtuelEnv(
            args.package, 
            args.venv,
            args.recreate_venv)
        venv.activate()

        report_type = report_types[args.report_type]
        report = report_type.parse_args(shlex.split(args.report_args))

        resmgr_backend = resmgr_backend_types[args.resmgr_backend_type]()

        runner_type = runner_types[args.runner_type]
        runner = runner_type.parse_args(shlex.split(args.runner_args), report, resmgr_backend)

        planname = args.plan
        planmodulename, planclsname = planname.rsplit(".", 1)
        __import__(planmodulename)
        planmod = sys.modules[planmodulename]
        plancls = getattr(planmod, planclsname)
        runner.run(plancls())

class ManagementToolsConsole(object):
    """管理工具交互模式
    """
    prompt = "QTA> "
    
    def __init__(self, argparser ):
        self._argparser = argparser
        
    def cmdloop(self):
        print("""QTAF %(qtaf_version)s (test project: %(proj_root)s [%(proj_mode)s mode])\n""" % {
            'qtaf_version': version,
            'proj_root': settings.PROJECT_ROOT,
            'proj_mode': settings.PROJECT_MODE,
        })
        if six.PY3:
            raw_input_func = input
        else:
            raw_input_func = raw_input
        while 1:
            line = raw_input_func(self.prompt)
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
                print("command exit")
            except:
                traceback.print_exc()


class ManagementTools(object):
    """管理工具类入口
    """
    excluded_command_types = [CreateProject, UpgradeProject, RunTestDistPackage, RunPlanDistPackage]
    
    def __init__(self):
        if settings.PROJECT_MODE == project.EnumProjectMode.Standard:
            self.excluded_command_types.append(InstallLib)
        
    def _load_cmds(self):
        """加载全部的命令
        """            
        cmds = []
        cmds += self._load_cmd_from_module(sys.modules[__name__])
        cmds += self._load_app_cmds()
        return cmds
        
    def _load_cmd_from_module(self, mod ):
        """加载一个模块里面的全部命令
        """
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
        
        if six.PY3:
            cmp_func = lambda x,y: x>y
        else:
            cmp_func = cmp
        cmds.sort(lambda x,y:cmp_func(x.name, y.name))    
        return cmds
    
    def _load_app_cmds(self):
        """从应用lib中加载命令
        """
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
        """执行入口
        """
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
    """qta-manage工具入口
    """
    logging.root.addHandler(logging.StreamHandler())
    logging.root.level = logging.INFO
    use_egg = not os.path.isfile(__file__)
    if use_egg:
        cmds = [CreateProject, UpgradeProject, RunTestDistPackage, RunPlanDistPackage, Help]
    else:
        cmds = [CreateProject, RunTestDistPackage, RunPlanDistPackage, Help]
    argparser = ArgumentParser(cmds)
    subcmd, args = argparser.parse_args(sys.argv[1:])
    subcmd.execute(args)
