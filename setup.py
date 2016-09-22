# -*- coding: utf-8 -*-
"""
打包脚本
"""

# 2015/09/02 eeelin 新建

import os
from setuptools import setup, find_packages

NAME        = "qtaf"
VERSION     = "5.0.88"
BASE_DIR    = os.path.dirname(os.path.realpath(__file__))

def get_requirements():
    '''获取依赖包
    
    :returns: list
    '''
    reqs = []
    req_file = os.path.join(BASE_DIR, "requirements.txt")
    if os.path.isfile(req_file):
        with open(req_file, 'r') as fd:
            for line in fd.readlines():
                line = line.strip()
                if line:
                    reqs.append(line)
    return reqs
    
if __name__ == "__main__":
    
    setup(
      version=VERSION,
      name=NAME,
      packages=find_packages(),
      py_modules=["__main__", "qtaf_settings"],
      package_data={'':['*.lib', '*.txt', '*.TXT', '*.exe', '*.lib'], },
      data_files=[(".", ["requirements.txt", "LICENSE.TXT"])],
      author="Tencent",
      license="Copyright(c)2010-2016 Tencent All Rights Reserved. ",
      requires=get_requirements(),   
      )
