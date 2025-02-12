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
"""imp兼容库
"""

import importlib.util
import itertools
import sys


def find_module(module_name, path_list=None):
    # 查找模块的规范
    spec = None
    if not path_list:
        spec = importlib.util.find_spec(module_name)
    else:
        _path_list = []
        for path in path_list:
            if isinstance(path, list):
                _path_list.extend(path)
            else:
                _path_list.append(path)
        for path in _path_list:
            sys.path.insert(0, path)
            spec = importlib.util.find_spec(module_name)
            sys.path.pop(0)
            if spec:
                break

    if spec is None:
        raise ImportError("Module %s not found" % module_name)

    # 获取模块的文件路径
    module_file = spec.origin
    module_path = spec.submodule_search_locations if hasattr(spec, 'submodule_search_locations') else None

    # description 是一个元组，包含模块类型和其他信息
    description = (spec.loader, module_file, spec)

    return (module_file, module_path, description)


def load_module(name, file, path, description):
    # load_module传入的name参数是给模块命名用的，不需要实际存在，所以这里没有使用
    # 从描述中获取加载器
    loader = description[0]
    # 使用 loader 加载模块
    module = loader.load_module()
    return module
