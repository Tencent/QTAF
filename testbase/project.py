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
"""测试项目接口
"""

from __future__ import unicode_literals

import os
import datetime
import zipfile
import getpass
import shutil
import xml.dom.minidom as dom

from testbase.util import codecs_open

INITPY_CONTENT = """# -*- coding: utf-8 -*-
'''%(Doc)s
'''
#%(Date)s QTAF自动生成
"""

SETTINGS_CONTENT_STANDALONE = """# -*- coding: utf-8 -*-
'''测试项目配置文件
'''
#%(Date)s QTAF自动生成

PROJECT_NAME = "%(ProjectName)s"
PROJECT_MODE = "standalone"
"""

SETTINGS_CONTENT_STANDARD = """# -*- coding: utf-8 -*-
'''测试项目配置文件
'''
#%(Date)s QTAF自动生成

import os

PROJECT_NAME = "%(ProjectName)s"
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT_MODE = "standard"
INSTALLED_APPS = []
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

PROJ_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJ_ROOT not in sys.path:
    sys.path.insert(0, PROJ_ROOT)
EXLIB_DIR = os.path.join(PROJ_ROOT, 'exlib')
if os.path.isdir(EXLIB_DIR):
    for filename in os.listdir(EXLIB_DIR):
        if filename.endswith('.egg'):
            lib_path = os.path.join(EXLIB_DIR, filename)
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

PYDEV_CONF_CONTENT_STANDALONE = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<?eclipse-pydev version="1.0"?><pydev_project>
<pydev_property name="org.python.pydev.PYTHON_PROJECT_INTERPRETER">Default</pydev_property>
<pydev_property name="org.python.pydev.PYTHON_PROJECT_VERSION">python 2.7</pydev_property>
<pydev_pathproperty name="org.python.pydev.PROJECT_SOURCE_PATH">
<path>/${PROJECT_DIR_NAME}</path>
<path>/${PROJECT_DIR_NAME}/exlib/%(EggName)s</path>
</pydev_pathproperty>
</pydev_project>
"""

PYDEV_CONF_CONTENT_STANDARD = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<?eclipse-pydev version="1.0"?><pydev_project>
<pydev_property name="org.python.pydev.PYTHON_PROJECT_INTERPRETER">Default</pydev_property>
<pydev_property name="org.python.pydev.PYTHON_PROJECT_VERSION">python 2.7</pydev_property>
<pydev_pathproperty name="org.python.pydev.PROJECT_SOURCE_PATH">
<path>/${PROJECT_DIR_NAME}</path>
</pydev_pathproperty>
</pydev_project>
"""


class EnumProjectMode(object):
    """测试项目运行模式
    """

    Standard = "standard"  # Python标准模式，QTAF和扩展库安装到Python Libs中
    Standalone = "standalone"  # 独立模式，QTAF和扩展库安装到测试项目的exlib目录中


def _create_initpy(dir_path, doc):
    """创建一个__init__.py
        """
    with codecs_open(os.path.join(dir_path, "__init__.py"), "wb") as fd:
        fd.write(
            (
                INITPY_CONTENT
                % {"Doc": doc, "Date": datetime.date.today().strftime("%Y/%m/%d")}
            ).encode("utf8")
        )


def _create_settingspy(proj_path, proj_name, mode):
    """创建settings.py文件
    """
    if mode == EnumProjectMode.Standalone:
        content = SETTINGS_CONTENT_STANDALONE
    else:
        content = SETTINGS_CONTENT_STANDARD
    with codecs_open(os.path.join(proj_path, "settings.py"), "wb") as fd:
        fd.write(
            (
                content
                % {
                    "Date": datetime.date.today().strftime("%Y/%m/%d"),
                    "ProjectName": proj_name,
                }
            ).encode("utf8")
        )


def _create_managepy(proj_path):
    """创建manage.py文件
    """
    with codecs_open(os.path.join(proj_path, "manage.py"), "wb") as fd:
        fd.write(
            (
                MANAGE_CONTENT % {"Date": datetime.date.today().strftime("%Y/%m/%d")}
            ).encode("utf8")
        )


def _create_sample_test(dir_path, proj_name):
    """创建示例测试用例
    """
    with codecs_open(os.path.join(dir_path, "hello.py"), "wb") as fd:
        fd.write(
            (
                TESTCASE_CONTENT
                % {
                    "Date": datetime.date.today().strftime("%Y/%m/%d"),
                    "ProjectName": proj_name,
                    "ProjectNameCapUp": proj_name[0].upper() + proj_name[1:],
                    "UserName": getpass.getuser(),
                }
            ).encode("utf8")
        )


def _create_sample_lib(dir_path, proj_name):
    """创建示例lib
    """
    with codecs_open(os.path.join(dir_path, "testcase.py"), "wb") as fd:
        fd.write(
            (
                TESTLIB_CONTENT
                % {
                    "Date": datetime.date.today().strftime("%Y/%m/%d"),
                    "ProjectName": proj_name,
                    "ProjectNameCapUp": proj_name[0].upper() + proj_name[1:],
                }
            ).encode("utf8")
        )


def _copy_qtaf_egg(egg_path, dir_path):
    """拷贝QTAF egg包
    """
    shutil.copy(egg_path, dir_path)
    with zipfile.ZipFile(egg_path) as zfile:
        try:
            zfile.getinfo("doc/qtaf.chm")  # chm可能不存在
        except KeyError:
            return
        else:
            with codecs_open(os.path.join(dir_path, "qtaf.chm"), "wb") as fd:
                fd.write(zfile.read("doc/qtaf.chm"))


def _create_eclipse_projfile(proj_path, proj_name):
    """创建eclispe项目文件
    """
    with codecs_open(os.path.join(proj_path, ".project"), "wb") as fd:
        fd.write((ECLIPSE_PROJ_CONTENT % {"ProjectName": proj_name}).encode("utf8"))


def _create_pydev_conffile(proj_path, mode):
    """创建pydev配置文件
    """
    with codecs_open(os.path.join(proj_path, ".pydevproject"), "wb") as fd:
        if mode == EnumProjectMode.Standalone:
            qtaf_egg_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), ".."
            )
            qtaf_egg_path = os.path.abspath(qtaf_egg_path)
            fd.write(
                (
                    PYDEV_CONF_CONTENT_STANDALONE
                    % {"EggName": os.path.basename(qtaf_egg_path)}
                ).encode("utf8")
            )
        else:
            fd.write(PYDEV_CONF_CONTENT_STANDARD.encode("utf8"))


def _update_pydev_conffile(proj_path, egg_name):
    """更新pydev配置文件中的Egg名称
    """
    with codecs_open(
        os.path.join(proj_path, ".pydevproject"), "r", encoding="utf-8"
    ) as fd:
        doc = dom.parse(fd)
        nodes = doc.getElementsByTagName("pydev_pathproperty")
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
                path = "".join(rc)
                if path.endswith(".egg") and "qtaf-" in path:
                    propsnode.removeChild(pathnode)
                    break
        pathnode = doc.createElement("path")
        pathnode.appendChild(
            doc.createTextNode("/${PROJECT_DIR_NAME}/exlib/%s" % egg_name)
        )
        propsnode.appendChild(pathnode)

    with codecs_open(os.path.join(proj_path, ".pydevproject"), "wb", "utf8") as fd:
        fd.write(doc.toxml(encoding="UTF-8"))


def create_project(dest_path, proj_name, mode):
    """创建项目
    """
    if not os.path.isdir(dest_path):
        os.makedirs(dest_path)

    lib_dir = os.path.join(dest_path, "%slib" % proj_name)
    if not os.path.isdir(lib_dir):
        os.mkdir(lib_dir)
        _create_initpy(lib_dir, "测试lib")
        _create_sample_lib(lib_dir, proj_name)

    case_dir = os.path.join(dest_path, "%stest" % proj_name)
    if not os.path.isdir(case_dir):
        os.mkdir(case_dir)
        _create_initpy(case_dir, "测试用例")
        _create_sample_test(case_dir, proj_name)

    res_dir = os.path.join(dest_path, "resources")
    if not os.path.isdir(res_dir):
        os.mkdir(res_dir)

    if mode == EnumProjectMode.Standalone:
        exlib_dir = os.path.join(dest_path, "exlib")
        if not os.path.isdir(exlib_dir):
            os.mkdir(exlib_dir)
            qtaf_egg_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), ".."
            )
            qtaf_egg_path = os.path.abspath(qtaf_egg_path)
            _copy_qtaf_egg(qtaf_egg_path, exlib_dir)

    _create_settingspy(dest_path, proj_name, mode)
    _create_managepy(dest_path)
    _create_eclipse_projfile(dest_path, proj_name)
    _create_pydev_conffile(dest_path, mode)


def update_project_qtaf(proj_path, qtaf_egg_path):
    """升级项目的QTAF
    """
    exlib_dir = os.path.join(proj_path, "exlib")
    for name in os.listdir(exlib_dir):
        if name.startswith("qtaf-") and name.endswith(".egg"):
            os.remove(os.path.join(exlib_dir, name))
    _copy_qtaf_egg(qtaf_egg_path, exlib_dir)
    _update_pydev_conffile(proj_path, os.path.basename(qtaf_egg_path))


class Project(object):
    """一个项目（废弃接口，存在是为了兼容）
    """

    def __init__(self, root):
        self._root = root

    @property
    def path(self):
        return self._root


def current_project():
    """获取当前项目（废弃接口，存在是为了兼容）
    """
    from testbase.conf import settings

    return Project(settings.PROJECT_ROOT)
