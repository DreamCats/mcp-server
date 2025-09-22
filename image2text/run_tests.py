#!/usr/bin/env python3
"""
测试运行器
用于运行所有单元测试
"""

import sys
import pytest


def run_tests():
    """运行所有测试"""
    print("开始运行image2text MCP服务器测试...")

    # 运行测试
    exit_code = pytest.main([
        "tests/",
        "-v",  # 详细输出
        "--tb=short",  # 简短的错误回溯
    ])

    return exit_code


if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)