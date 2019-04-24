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
打包
"""

import os
import sys
import re
import shutil
import zipfile
import pkg_resources
import subprocess
import six

from testbase import resource
from testbase.conf import settings
from testbase.util import codecs_open

SETUP_PY_TEMPLATE = """
from setuptools import setup, find_packages

setup(
    version="%(version)s",
    name="%(name)s",
    packages=find_packages(),
    py_modules=["settings"],
    include_package_data = True,
    install_requires=%(requirements)s,
    entry_points={'console_scripts': ['qta-manage-venv = testbase.management:qta_manage_main'], },
)
"""


SETUP_PY_TEMPLATE_INCLUDE_RESOURCE = """
import os
import re
from setuptools import setup, find_packages, Command
    
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def find_all_file_patterns( resource_dir ):
    file_patterns = []
    rel_prefix = "." + os.path.sep
    for dirpath, dirnames, filenames in os.walk(resource_dir):
        if filenames:
            relpath = os.path.relpath(dirpath, resource_dir)
            pattern = os.path.join(relpath, "*")
            pattern = "resources" + os.path.sep + pattern.lstrip(rel_prefix)
            file_patterns.append(pattern)
    return file_patterns

def find_resource_packages_data():
    '''Collect files in 'resources' directory in package as package data
    '''
    packages_data = {}
    
    for dirpath, dirnames, _ in os.walk(BASE_DIR):
        for dirname in list(dirnames):
            if dirname == 'resources':
                if not os.path.isfile(os.path.join(dirpath, "__init__.py")):
                    continue
                resource_dir = os.path.join(dirpath, dirname)
                relpath = os.path.relpath(dirpath, BASE_DIR)
                package_name = ".".join(relpath.split(os.path.sep))
                packages_data[package_name] = find_all_file_patterns(resource_dir)

            if not os.path.isfile(os.path.join(dirpath, dirname, "__init__.py")):
                dirnames.remove(dirname)  # not a package
                continue
    return packages_data

def find_resource_data_files():
    '''Collect files in top level 'resources' directory as data_files
    '''
    import site
    if hasattr(site, "getsitepackages"):
        install_prefix = os.path.join(site.getsitepackages()[0], "resources")
    else:
        # Work around for virtuelenv bug: https://github.com/pypa/virtualenv/issues/355
        install_prefix = os.path.join(".", "lib", "site-packages", "resources")
    data_files = []
    resource_dir = os.path.join(BASE_DIR, "resources")
    for dirpath, dirnames, filenames in os.walk(resource_dir):
        dirrelpath = os.path.relpath(dirpath, resource_dir)
        filelist = [
            os.path.join("resources", dirrelpath, filename)
            for filename in filenames
        ]
        data_files.append((
            os.path.join(install_prefix, dirrelpath),
            filelist
        ))
    return data_files

class sdist_qta(Command):
    user_options = []
    boolean_options = []
    sub_commands = (("sdist_qta_resource", None),)
          
    def initialize_options (self):
        pass
    
    def finalize_options(self):
        pass

    def run(self):
        sdist = self.reinitialize_command("sdist")
        sdist.sub_commands = self.sub_commands
        self.run_command("sdist")
        
class sdist_qta_resource(Command):
    user_options = []
    boolean_options = []
        
    def initialize_options (self):
        pass
    
    def finalize_options(self):
        pass

    def run(self):
        sdist = self.get_finalized_command("sdist")
        src_root = os.getcwd()
        for dirpath, _, filenames in os.walk(src_root):
            relpath = os.path.relpath(dirpath, src_root)
            if "resources" in relpath.split(os.path.sep):
                for filename in filenames:
                    sdist.filelist.append(os.path.join(relpath, filename))
setup(
    version="%(version)s",
    name="%(name)s",
    # We want to bulid sdist with package datas without a MANIFEST.in
    # Work around for https://stackoverflow.com/questions/7522250/how-to-include-package-data-with-setuptools-distribute
    cmdclass={"sdist_qta": sdist_qta,
              "sdist_qta_resource": sdist_qta_resource},
    packages=find_packages(),
    py_modules=["settings"],
    package_data=find_resource_packages_data(),
    data_files=find_resource_data_files(),
    include_package_data = True,
    install_requires=%(requirements)s,
    entry_points={'console_scripts': ['qta-manage-venv = testbase.management:qta_manage_main'], },
)
"""


class DistGenerator(object):
    """Build dist packages"""

    def __init__(self, version):
        self._version = version

    def run(self, exclude_resources):
        self._generate_sdist(exclude_resources=exclude_resources)

    def _merge_requirements(self):
        """Merge exlib & requirements.txt"""
        exlib = os.path.join(settings.PROJECT_ROOT, 'exlib')
        egg_pattern = re.compile(r"(?P<name>[a-zA-Z0-9_]+)(\-(?P<version>[0-9a-zA-Z_\.]+)|)(\-.*|)\.egg$")
        reqs_dict = {}

        req_txt = os.path.join(settings.PROJECT_ROOT, "requirements.txt")
        if os.path.isfile(req_txt):
            with codecs_open(req_txt, 'r', encoding="utf-8") as fd:
                for it in pkg_resources.parse_requirements(fd.read()):
                    reqs_dict[it.name] = str(it)

        elif os.path.isdir(exlib):
            for filename in os.listdir(exlib):
                if not filename.endswith(".egg"):
                    continue
                result = egg_pattern.match(filename)
                if not result:
                    continue
                name, version = result.group('name'), result.group('version')
                if version:
                    reqs_dict[name] = "%s==%s" % (name, version)
                else:
                    reqs_dict[name] = name

        if 'qtaf' not in reqs_dict:
            reqs_dict["qtaf"] = "qtaf"
        return list(reqs_dict.values())

    def _generate_sdist(self, exclude_resources):
        """Call setuptools to generate source dist"""
        reqs = self._merge_requirements()
        setup_py = os.path.join(settings.PROJECT_ROOT, "setup.py")
        if exclude_resources:
            template = SETUP_PY_TEMPLATE
            cmd = "sdist"
        else:
            template = SETUP_PY_TEMPLATE_INCLUDE_RESOURCE
            cmd = "sdist_qta"

        with codecs_open(setup_py, "w", encoding="utf-8") as fd:
            fd.write(template % dict(
                version=self._version,
                name=settings.PROJECT_NAME,
                requirements=repr(reqs),
            ))

        subprocess.call(["python", "setup.py", cmd], cwd=settings.PROJECT_ROOT)
        os.remove(setup_py)

    def _generate_resource_pkg(self):
        filename = "%s-%s-resource.zip" % (settings.PROJECT_NAME, self._version)
        filepath = os.path.join(settings.PROJECT_ROOT, "dist", filename)
        with zipfile.ZipFile(filepath, "w") as zf:
            for res_path in resource.iter_resource_paths():
                for dirpath, _, filenames in os.walk(res_path):
                    for filename in filenames:
                        src = os.path.join(dirpath, filename)
                        zf.write(src, os.path.relpath(src, res_path))

class VirtuelEnv(object):
    """virtual env for QTA test project
    """

    VENV_ENV_NAME = "QTAF_VENV"

    def __init__(self, dist_pkg_path, path=None, recreate=False):
        self._dist_pkg_path = dist_pkg_path
        self._venv = path
        self._recreate_venv = recreate

    def activate(self):
        """activate virtuelenv on current processs

        Logic:
            1. Call from 'qta-manage', then create virtualenv
            2. Activate it
            3. Set OS environ 'QTAF_VENV'
            4. Create child process, replace 'qta-manage' with 'qta-manage-venv'
                (1) Call from 'qta-manage-venv'
                (2) OS environ 'QTAF_VENV' detected, ignore virtualenv creation code
        """
        
        if self.VENV_ENV_NAME in os.environ: # already in our venv
            return

        try:
            import virtualenv
        except ImportError:
            raise RuntimeError("Python package 'virtualenv' need to be not installed.")

        if self._venv:
            venv_path = self._venv
        else:
            venv_path = os.path.basename(self._dist_pkg_path)
            if venv_path.endswith(".zip"):
                venv_path = venv_path.rsplit(".", 1)[0]
            elif venv_path.endswith(".tar.gz"):
                venv_path = venv_path.rsplit(".", 2)[0]
            venv_path = venv_path + '_venv'
        if (not os.path.isdir(venv_path)) or self._recreate_venv:
            if os.path.isdir(venv_path):
                shutil.rmtree(venv_path)
            virtualenv.create_environment(venv_path, site_packages=True)
            created = True
        else:
            created = False
        _, _, _, bin_dir = virtualenv.path_locations(venv_path)
        activation_script = os.path.join(bin_dir, 'activate_this.py')
        with open(activation_script, "r") as fd:
            exec(fd.read(), dict(__file__=activation_script))
        if created:
            subprocess.call(["pip", "install", self._dist_pkg_path], close_fds=True)

        os.environ[self.VENV_ENV_NAME] = "1"
        argv = list(sys.argv)
        argv[0] = "qta-manage-venv"
        subprocess.call(argv, close_fds=True)
        sys.exit(0)
