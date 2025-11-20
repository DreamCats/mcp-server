#!/usr/bin/env python3
"""
测试运行器

运行所有测试并生成测试报告
"""

import pytest
import sys
import os

def run_tests():
    """运行所有测试"""
    # 获取当前脚本目录
    test_dir = os.path.dirname(os.path.abspath(__file__))

    # 测试参数
    args = [
        test_dir,
        "-v",  # 详细输出
        "--tb=short",  # 简短的traceback格式
        "--strict-markers",  # 严格检查markers
        "--disable-warnings",  # 禁用警告
        "-p", "no:cacheprovider",  # 禁用缓存
    ]

    # 运行测试
    exit_code = pytest.main(args)

    return exit_code

if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)