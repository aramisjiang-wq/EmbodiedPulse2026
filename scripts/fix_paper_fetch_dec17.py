#!/usr/bin/env python3
"""
专门抓取12月17日的论文
"""
import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("抓取2025年12月17日的论文")
print("=" * 60)
print()

try:
    from daily_arxiv import load_config, demo
    
    config = load_config('config.yaml')
    config['max_results'] = 200  # 增加抓取数量
    config['update_paper_links'] = False
    config['enable_dedup'] = True
    config['enable_incremental'] = True
    config['days_back'] = 1  # 只抓取最近1天（12月17日）
    config['fetch_semantic_scholar'] = True
    config['publish_gitpage'] = False
    config['publish_wechat'] = False
    
    print(f"📅 抓取日期范围: 2025-12-17 (最近1天)")
    print(f"📊 关键词数量: {len(config.get('kv', {}))}")
    print()
    
    demo(**config)
    
    print()
    print("=" * 60)
    print("✅ 抓取完成，检查结果...")
    print("=" * 60)
    print()
    
    # 检查结果
    from models import get_session, Paper
    
    session = get_session()
    target_date = datetime(2025, 12, 17).date()
    papers_1217 = session.query(Paper).filter(Paper.publish_date == target_date).count()
    
    print(f"📊 数据库中12月17日的论文数: {papers_1217} 篇")
    
    if papers_1217 > 0:
        print(f"\n📋 论文列表（前10篇）:")
        papers_list = session.query(Paper).filter(
            Paper.publish_date == target_date
        ).order_by(Paper.created_at.desc()).limit(10).all()
        for i, paper in enumerate(papers_list, 1):
            print(f"   {i}. {paper.title[:60]}...")
            print(f"      分类: {paper.category}")
            print(f"      创建时间: {paper.created_at}")
    else:
        print("\n⚠️  没有找到12月17日的论文")
        print("   可能的原因：")
        print("   1. ArXiv API没有返回12月17日的论文")
        print("   2. 论文被去重逻辑过滤了")
        print("   3. 分类关键词不匹配")
    
    session.close()
    
except Exception as e:
    print(f"❌ 抓取失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

