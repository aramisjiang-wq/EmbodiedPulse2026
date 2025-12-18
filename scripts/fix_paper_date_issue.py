#!/usr/bin/env python3
"""
修复论文日期问题：将12月17日创建的论文的publish_date更新为12月17日
"""
import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

from models import get_session, Paper

print("=" * 60)
print("修复论文日期问题")
print("=" * 60)
print()

session = get_session()

# 找出12月17日创建的论文，但publish_date不是12月17日的
target_date = datetime(2025, 12, 17).date()
dec17_start = datetime(2025, 12, 17, 0, 0, 0)
dec17_end = datetime(2025, 12, 18, 0, 0, 0)

papers_to_fix = session.query(Paper).filter(
    Paper.created_at >= dec17_start,
    Paper.created_at < dec17_end,
    Paper.publish_date != target_date
).all()

print(f"📊 找到 {len(papers_to_fix)} 篇需要修复的论文")
print()

if len(papers_to_fix) > 0:
    print("开始修复...")
    fixed_count = 0
    
    for paper in papers_to_fix:
        old_date = paper.publish_date
        paper.publish_date = target_date
        fixed_count += 1
        
        if fixed_count <= 5:
            print(f"  修复: {paper.title[:50]}...")
            print(f"    旧日期: {old_date} -> 新日期: {target_date}")
    
    session.commit()
    print()
    print(f"✅ 已修复 {fixed_count} 篇论文的日期")
else:
    print("✅ 没有需要修复的论文")

# 验证修复结果
papers_1217 = session.query(Paper).filter(Paper.publish_date == target_date).count()
print()
print(f"📊 修复后，12月17日的论文数: {papers_1217} 篇")

session.close()

