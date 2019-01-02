#-*- coding: UTF-8 -*-
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
"""unit tests entry
"""
import argparse
import importlib
import pkgutil
import os
import re
import sys
import traceback
import unittest

test_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(test_dir))
sys.path.insert(0, test_dir)
loader = unittest.TestLoader()

def load_case(case_path):
    parts = case_path.split(".")
    temp_parts = parts[:]
    
    mod = None
    while temp_parts:
        try:
            mod_name = ".".join(temp_parts)
            mod = importlib.import_module(mod_name)
            break
        except:
            temp_parts.pop()
    if not mod:
        raise RuntimeError("case path=%s cannot be imported." % case_path)
        
    case_name = ".".join(parts[len(temp_parts):])
    test_suites = []
    if case_name:
        test_suites.append(loader.loadTestsFromName(case_name, mod))
    else:
        if hasattr(mod, "__path__"):
            for _, mod_name, _ in pkgutil.walk_packages(mod.__path__):
                mod_name = mod.__name__ + "." + mod_name
                sub_mod = importlib.import_module(mod_name)
                test_suites.append(loader.loadTestsFromModule(sub_mod))
        else:
            test_suites.append(loader.loadTestsFromModule(mod))
    return test_suites

def load_cases(tests):
    test_suite = unittest.TestSuite()
    for test in tests:
        test_suite.addTests(load_case(test))
    return test_suite

def main(verbosity, tests):
    if not tests:
        tests = ['test_testbase', 'test_tuia']
    test_suite = load_cases(tests)
    runner = unittest.TextTestRunner(verbosity=10 + verbosity)
    raise SystemExit(not runner.run(test_suite).wasSuccessful())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", metavar='v', nargs="*", dest="verbosity",
                        help="verbose level for result output")
    parser.add_argument("tests", metavar='TEST', nargs="*", 
                        help="a python style module path for testcase set, eg: hello.MyTestCase")
    args = parser.parse_args(sys.argv[1:])
    if args.verbosity:
        verbosity = len(args.verbosity)
    else:
        verbosity = 0
    main(verbosity, args.tests)