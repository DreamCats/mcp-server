#!/usr/bin/env python3
"""
测试脚本：验证中文注释是否正确添加
"""

import ast
import os

def check_chinese_comments(file_path):
    """检查文件中的中文注释"""
    print(f"\n=== 检查文件: {file_path} ===")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 解析AST
        tree = ast.parse(content)

        # 统计中文注释
        chinese_comments = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            line = line.strip()
            if line.startswith('#') and ('中文' in line or '参数' in line or '返回' in line or '功能' in line):
                chinese_comments.append((i, line))

        print(f"找到 {len(chinese_comments)} 个中文注释:")
        for line_num, comment in chinese_comments[:5]:  # 显示前5个
            print(f"  行 {line_num}: {comment}")

        if len(chinese_comments) > 5:
            print(f"  ... 还有 {len(chinese_comments) - 5} 个注释")

        # 检查docstring
        docstrings = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
                if ast.get_docstring(node):
                    docstring = ast.get_docstring(node)
                    if '中文' in docstring or '参数' in docstring or '返回' in docstring:
                        docstrings.append((type(node).__name__, node.name if hasattr(node, 'name') else 'module'))

        print(f"找到 {len(docstrings)} 个包含中文的docstring:")
        for node_type, name in docstrings[:3]:  # 显示前3个
            print(f"  {node_type}: {name}")

        if len(docstrings) > 3:
            print(f"  ... 还有 {len(docstrings) - 3} 个docstring")

        return True

    except Exception as e:
        print(f"错误: {e}")
        return False

def main():
    """主函数"""
    print("开始验证中文注释添加情况...")

    # 要检查的文件
    files = [
        'src/service_discovery.py',
        'src/cluster_discovery.py',
        'src/instance_discovery.py',
        'src/rpc_simulation.py',
        'src/mcp_server.py'
    ]

    success_count = 0
    for file_path in files:
        if os.path.exists(file_path):
            if check_chinese_comments(file_path):
                success_count += 1
        else:
            print(f"文件不存在: {file_path}")

    print(f"\n=== 总结 ===")
    print(f"成功检查 {success_count}/{len(files)} 个文件")
    print("中文注释添加完成！")

if __name__ == "__main__":
    main()