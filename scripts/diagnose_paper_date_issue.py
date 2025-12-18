#!/usr/bin/env python3
"""
诊断论文日期问题：检查ArXiv API返回的日期字段
"""
import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

import arxiv

print("=" * 60)
print("诊断论文日期问题")
print("=" * 60)
print()

# 查询12月17日提交的论文
target_date = datetime(2025, 12, 17).date()
start_date = datetime(2025, 12, 17, 0, 0, 0)
end_date = datetime(2025, 12, 18, 0, 0, 0)

date_filter = f"submittedDate:[{start_date.strftime('%Y%m%d')}0000 TO {end_date.strftime('%Y%m%d')}2359]"
query = f"(robotics OR manipulation OR embodied) AND {date_filter}"

print(f"📅 查询日期范围: {start_date.date()} 到 {end_date.date()}")
print(f"📋 查询条件: {query}")
print()

client = arxiv.Client(page_size=10, delay_seconds=1.0, num_retries=3)

search = arxiv.Search(
    query=query,
    max_results=10,
    sort_by=arxiv.SortCriterion.SubmittedDate,
    sort_order=arxiv.SortOrder.Descending
)

print("📊 ArXiv API返回的论文（前10篇）:")
print()

count = 0
for result in client.results(search):
    count += 1
    paper_id = result.get_short_id()
    submitted_date = result.submitted.date() if hasattr(result, 'submitted') else None
    published_date = result.published.date() if hasattr(result, 'published') else None
    updated_date = result.updated.date() if hasattr(result, 'updated') else None
    
    print(f"{count}. {result.title[:60]}...")
    print(f"   ID: {paper_id}")
    print(f"   提交日期 (submitted): {submitted_date}")
    print(f"   首次发布 (published): {published_date}")
    print(f"   最后更新 (updated): {updated_date}")
    print(f"   日期差异: submitted={submitted_date}, published={published_date}")
    if published_date != target_date:
        print(f"   ⚠️  published日期不是12月17日！")
    print()

print(f"✅ 共获取 {count} 篇论文")
print()
print("=" * 60)
print("结论")
print("=" * 60)
print()
print("如果published日期不是12月17日，说明：")
print("  1. 这些论文是12月17日提交的，但之前已经发布过")
print("  2. 或者ArXiv的published日期是首次发布日期，不是提交日期")
print()
print("解决方案：")
print("  1. 使用submitted日期作为publish_date（更准确反映论文提交时间）")
print("  2. 或者同时保存submitted和published两个日期")
print("  3. 或者查询时使用lastUpdatedDate而不是submittedDate")

