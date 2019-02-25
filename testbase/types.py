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
"""qtaf related types
"""

import pkg_resources
import traceback

from testbase import runner, report, resource, logger

RUNNER_ENTRY_POINT = "qtaf.runner"
REPORT_ENTRY_POINT = "qtaf.report"
RESMGR_BACKEND_ENTRY_POINT = "qtaf.resmgr_backend"

runner_types = {}
report_types = {}
resmgr_backend_types = {}

def __init_runner_types():
    global runner_types
    if runner_types:
        return
    runner_types["basic"] = runner.TestRunner
    runner_types["multithread"] = runner.ThreadingTestRunner
    runner_types["multiprocess"] = runner.MultiProcessTestRunner
    for ep in pkg_resources.iter_entry_points(RUNNER_ENTRY_POINT):
        if ep.name not in runner_types:
            try:
                runner_types[ep.name] = ep.load()
            except:
                stack = traceback.format_exc()
                logger.warn("load TestRunner type for %s failed:\n%s" % (ep.name, stack))


def __init_report_types():
    global report_types
    if report_types:
        return
    report_types.update({
        "empty"  : report.EmptyTestReport,
        "stream" : report.StreamTestReport,
        "xml"    : report.XMLTestReport,
        "json"   : report.JSONTestReport,
        "html"   : report.HtmlTestReport,
    })

    # Register other `ITestReport` implementations from entry points
    for ep in pkg_resources.iter_entry_points(REPORT_ENTRY_POINT):
        if ep.name not in report_types:
            try:
                report_types[ep.name] = ep.load()
            except:
                stack = traceback.format_exc()
                logger.warn("load ITestReport entry point for %s failed:\n%s" % (ep.name, stack))


def __init_resmgr_backend_types():
    global resmgr_backend_types
    if resmgr_backend_types:
        return
    resmgr_backend_types["local"] = resource.LocalResourceManagerBackend
    for ep in pkg_resources.iter_entry_points(RESMGR_BACKEND_ENTRY_POINT):
        if ep.name not in resmgr_backend_types:
            resmgr_backend_types[ep.name] = ep.load()


__init_runner_types()
del __init_runner_types

__init_report_types()
del __init_report_types

__init_resmgr_backend_types()
del __init_resmgr_backend_types

