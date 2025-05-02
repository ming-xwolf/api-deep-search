#!/usr/bin/env python
"""
运行API Deep Search项目的所有单元测试
"""

import unittest
import sys
import os

if __name__ == "__main__":
    # 添加项目根目录到Python路径
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    
    # 发现并运行所有测试用例
    test_suite = unittest.defaultTestLoader.discover("tests", pattern="test_*.py")
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # 根据测试结果设置退出码
    sys.exit(not result.wasSuccessful()) 