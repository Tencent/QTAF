# -*- coding: utf-8 -*-

from testbase.plan import TestPlan
from testbase.resource import LocalResourceHandler, LocalResourceManagerBackend

class HelloResourceHandler(LocalResourceHandler):
    def iter_resource(self, res_type, res_group=None,condition=None):
        for i in range(2):
            yield {"id": i+1}

LocalResourceManagerBackend.register_resource_type("hello", HelloResourceHandler())

class HelloTestPlan(TestPlan):
    tests = "test.sampletest.runnertest"
    test_target_args = {}

    def test_setup(self, report):
        report.info("plan", "test_setup")

    def test_teardown(self, report):
        report.info("plan", "test_teardown")

    def resource_setup(self, report, res_type, resource):
        report.info("plan", "resource_setup-%s-%s" % (res_type, resource["id"]))

    def resource_teardown(self, report, res_type, resource):
        report.info("plan", "resource_teardown-%s-%s" % (res_type, resource["id"]))

if __name__ == '__main__':
    HelloTestPlan().debug_run()