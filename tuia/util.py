# -*- coding: utf-8 -*
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

import warnings

warnings.warn(
    "`tuia.util` is depressed, please use `qt4c.util` instead", DeprecationWarning
)
try:
    from qt4c.util import *  # pylint: disable=wildcard-import
except ImportError:
    pass

from testbase.util import Timeout  # pylint: disable=unused-import
from tuia.exceptions import TimeoutError  # pylint: disable=unused-import
