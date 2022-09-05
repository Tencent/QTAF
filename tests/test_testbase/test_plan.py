# -*- coding: utf-8 -*-

import unittest
from testbase.report import StreamTestReport


class PlanTest(unittest.TestCase):
    def test_debug_run(self):
        from tests.sampletestplan.hello import HelloTestPlan

        report = HelloTestPlan().debug_run()
        self.assertIsInstance(report, StreamTestReport)
