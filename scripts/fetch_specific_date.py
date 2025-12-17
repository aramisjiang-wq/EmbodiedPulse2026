#!/usr/bin/env python3
"""
专门抓取指定日期的论文（用于测试）
用法: python3 scripts/fetch_specific_date.py --date 2025-12-16
"""
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import argparse
from daily_arxiv import load_config, demo
from models import get_session, Paper
from sqlalchemy import func

def fetch_papers_for_date(target_date_str):
    """
    抓取指定日期的论文
    
    Args:
        target_date_str: 日期字符串，格式：YYYY-MM-DD
    """
    print("=" * 60)
    print(f"开始抓取 {target_date_str} 的论文...")
    print("=" * 60)
    
    # 解析目标日期
    try:
        target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
    except ValueError:
        print(f"❌ 日期格式错误，请使用 YYYY-MM-DD 格式，例如：2025-12-16")
        return
    
    print(f"📅 目标日期: {target_date}")
    print(f"📅 今天是: {datetime.now().date()}")
    
    # 检查数据库中是否已有该日期的论文
    session = get_session()
    existing_papers = session.query(Paper).filter(
        func.date(Paper.publish_date) == target_date
    ).all()
    print(f"📊 数据库中已有 {len(existing_papers)} 篇 {target_date} 的论文")
    
    if len(existing_papers) > 0:
        print("\n已有论文列表（前5篇）：")
        for i, paper in enumerate(existing_papers[:5], 1):
            print(f"  {i}. {paper.title[:60]}...")
            print(f"     提交日期: {paper.publish_date}, 创建时间: {paper.created_at}")
    
    session.close()
    
    # 加载配置
    config = load_config('config.yaml')
    config['max_results'] = 200  # 增加抓取数量，确保不遗漏
    config['update_paper_links'] = False
    config['enable_dedup'] = True
    config['enable_incremental'] = True
    
    # 计算日期范围：目标日期前后各1天，确保能抓到
    start_date = target_date - timedelta(days=1)
    end_date = target_date + timedelta(days=1)
    days_back = (datetime.now().date() - start_date).days + 1
    
    config['days_back'] = days_back
    config['fetch_semantic_scholar'] = True
    config['publish_gitpage'] = False
    config['publish_wechat'] = False
    
    print(f"\n📊 抓取配置:")
    print(f"  日期范围: {start_date} 到 {end_date}")
    print(f"  days_back: {days_back} 天")
    print(f"  max_results: {config['max_results']}")
    
    # 修改 daily_arxiv.py 的日期过滤逻辑（临时）
    # 我们需要在查询中添加更精确的日期过滤
    print(f"\n🔍 开始从ArXiv API抓取...")
    
    try:
        # 调用demo函数进行抓取
        demo(**config)
        
        # 抓取完成后，再次检查数据库
        print("\n" + "=" * 60)
        print("抓取完成，检查结果...")
        print("=" * 60)
        
        session = get_session()
        new_papers = session.query(Paper).filter(
            func.date(Paper.publish_date) == target_date
        ).all()
        
        print(f"📊 数据库中现在有 {len(new_papers)} 篇 {target_date} 的论文")
        
        if len(new_papers) > len(existing_papers):
            added_count = len(new_papers) - len(existing_papers)
            print(f"✅ 成功新增 {added_count} 篇论文！")
            
            print("\n新增论文列表：")
            for i, paper in enumerate(new_papers[len(existing_papers):], 1):
                print(f"  {i}. {paper.title[:60]}...")
                print(f"     提交日期: {paper.publish_date}, 创建时间: {paper.created_at}")
                print(f"     URL: {paper.url}")
        else:
            print("⚠️  没有新增论文")
            print("\n可能的原因：")
            print("1. ArXiv API在目标日期没有返回新论文")
            print("2. 论文的提交日期（submittedDate）和发布日期（publish_date）不同")
            print("3. 论文可能在其他日期提交，但显示为12月16日")
        
        # 检查最近创建的论文（可能是12月16日提交的）
        print("\n" + "=" * 60)
        print("检查最近创建的论文（可能是目标日期提交的）...")
        print("=" * 60)
        
        recent_papers = session.query(Paper).filter(
            Paper.created_at >= datetime.now() - timedelta(hours=1)
        ).order_by(Paper.created_at.desc()).limit(10).all()
        
        if recent_papers:
            print(f"📊 最近1小时内创建的论文: {len(recent_papers)} 篇")
            for i, paper in enumerate(recent_papers, 1):
                print(f"  {i}. {paper.title[:60]}...")
                print(f"     提交日期: {paper.publish_date}, 创建时间: {paper.created_at}")
        else:
            print("⚠️  最近1小时内没有创建新论文")
        
        session.close()
        
        print("\n" + "=" * 60)
        print("✅ 抓取任务完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 抓取失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    parser = argparse.ArgumentParser(description='抓取指定日期的论文')
    parser.add_argument('--date', type=str, required=True, 
                       help='目标日期，格式：YYYY-MM-DD，例如：2025-12-16')
    args = parser.parse_args()
    
    fetch_papers_for_date(args.date)

if __name__ == '__main__':
    main()

