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
'''QTAF执行入口
'''

#2015/04/28 olive 新建

import sys
import os
import logging
import argparse

from testbase.management import ArgumentParser, Help, Command
from testbase import project

class CreateProject(Command):
    '''创建测试项目
    '''   
    name = 'createproject'
    parser = argparse.ArgumentParser("Create new QTA project")
    parser.add_argument('name', help="project name")
    parser.add_argument('--dest', default=None, help="target path to create project")
    
    def execute(self, args):
        '''执行过程
        '''
        if os.path.isfile(__file__):
            logging.error("should run in egg mode")
            sys.exit(1)
        if args.dest is None:
            dest = os.getcwd()
        else:
            dest = args.dest
        project.TestProject(os.path.join(dest, args.name.lower()+'testproj'), args.name, False).initialize()
    
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
            
        qtaf_path = os.path.dirname(__file__)
        target = project.TestProject(args.proj_path, '', False)
        target.upgrade_qtaf(qtaf_path)

if __name__ == '__main__':
    logging.root.addHandler(logging.StreamHandler())
    logging.root.level = logging.INFO
    argparser = ArgumentParser([CreateProject, UpgradeProject, Help])
    subcmd, args = argparser.parse_args(sys.argv[1:])
    subcmd.execute(args)