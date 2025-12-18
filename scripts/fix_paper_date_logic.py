#!/usr/bin/env python3
"""
修复论文日期逻辑：使用submitted日期作为publish_date（更准确反映论文提交时间）
"""
import sys
import os

# 添加项目根目录到Python路径
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

print("=" * 60)
print("修复论文日期逻辑")
print("=" * 60)
print()

# 检查daily_arxiv.py中的日期逻辑
daily_arxiv_path = os.path.join(project_root, 'daily_arxiv.py')

with open(daily_arxiv_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 查找使用published.date()的地方
if "result.published.date()" in content:
    print("⚠️  发现使用 result.published.date() 作为日期")
    print("   问题：published是首次发布日期，可能早于提交日期")
    print()
    print("📝 建议修复：")
    print("   1. 使用 result.submitted.date() 作为publish_date（更准确）")
    print("   2. 或者同时保存submitted和published两个日期")
    print()
    
    # 查找具体位置
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        if 'publish_time' in line and 'result.published.date()' in line:
            print(f"   位置: daily_arxiv.py 第 {i} 行")
            print(f"   代码: {line.strip()}")
            print()

print("=" * 60)
print("修复方案")
print("=" * 60)
print()
print("需要修改 daily_arxiv.py 中的日期逻辑：")
print("  将 publish_time = result.published.date()")
print("  改为 publish_time = result.submitted.date()")
print()
print("这样publish_date会更准确地反映论文的提交日期（即用户在ArXiv上看到的新论文日期）")
print()

