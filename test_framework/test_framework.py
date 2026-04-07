"""Test Framework for methodology-v2"""
import time
from typing import List, Dict
from enum import Enum

class TestStatus(Enum):
    PASS = "pass"
    FAIL = "fail"

class AgentTest:
    def __init__(self, name: str):
        self.name = name
        self.results = []
    
    def assert_equals(self, actual, expected, msg=""):
        start = time.time()
        status = TestStatus.PASS if actual == expected else TestStatus.FAIL
        self.results.append({"name": msg or self.name, "status": status.value, "duration": time.time()-start})
    
    def assert_contains(self, text, substring, msg=""):
        start = time.time()
        status = TestStatus.PASS if substring in text else TestStatus.FAIL
        self.results.append({"name": msg or self.name, "status": status.value, "duration": time.time()-start})

class TestSuite:
    def __init__(self):
        self.tests = []
    
    def add_test(self, test):
        self.tests.append(test)
    
    def run(self):
        passed = failed = 0
        for test in self.tests:
            for r in test.results:
                if r["status"] == "pass": passed += 1
                else: failed += 1
        return {"passed": passed, "failed": failed, "total": passed+failed}

if __name__ == "__main__":
    t = AgentTest("math")
    t.assert_equals("4", "4")
    t.assert_equals("hello", "world")
    s = TestSuite()
    s.add_test(t)
    print(s.run())
