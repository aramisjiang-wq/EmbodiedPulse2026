#!/usr/bin/env python3
"""
检查并清理未分类论文，以及查询指定日期的论文
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import get_session, Paper
from datetime import datetime, date
from sqlalchemy import func

def check_uncategorized():
    """检查未分类论文数量"""
    session = get_session()
    try:
        uncategorized = session.query(Paper).filter(
            Paper.category == 'Uncategorized'
        ).all()
        
        print(f"\n📊 未分类论文统计:")
        print(f"   总数: {len(uncategorized)} 篇")
        
        if len(uncategorized) > 0:
            print(f"\n   前10篇未分类论文:")
            for i, paper in enumerate(uncategorized[:10], 1):
                print(f"   {i}. [{paper.id}] {paper.title[:80]}...")
        
        return uncategorized
    finally:
        session.close()

def delete_uncategorized():
    """删除所有未分类论文"""
    session = get_session()
    try:
        uncategorized = session.query(Paper).filter(
            Paper.category == 'Uncategorized'
        ).all()
        
        count = len(uncategorized)
        if count == 0:
            print("\n✅ 没有未分类论文需要删除")
            return 0
        
        print(f"\n⚠️  准备删除 {count} 篇未分类论文...")
        
        for paper in uncategorized:
            session.delete(paper)
        
        session.commit()
        print(f"✅ 已删除 {count} 篇未分类论文")
        
        return count
    except Exception as e:
        session.rollback()
        print(f"❌ 删除失败: {e}")
        return 0
    finally:
        session.close()

def check_papers_by_date(start_date, end_date):
    """检查指定日期范围的论文"""
    session = get_session()
    try:
        papers = session.query(Paper).filter(
            Paper.publish_date >= start_date,
            Paper.publish_date <= end_date
        ).order_by(Paper.publish_date.desc()).all()
        
        print(f"\n📅 {start_date} 至 {end_date} 的论文:")
        print(f"   总数: {len(papers)} 篇")
        
        if len(papers) > 0:
            # 按日期分组统计
            date_counts = {}
            for paper in papers:
                date_str = paper.publish_date.strftime('%Y-%m-%d') if paper.publish_date else 'Unknown'
                date_counts[date_str] = date_counts.get(date_str, 0) + 1
            
            print(f"\n   按日期分布:")
            for date_str in sorted(date_counts.keys()):
                print(f"   {date_str}: {date_counts[date_str]} 篇")
            
            print(f"\n   前20篇论文:")
            for i, paper in enumerate(papers[:20], 1):
                date_str = paper.publish_date.strftime('%Y-%m-%d') if paper.publish_date else 'Unknown'
                print(f"   {i}. [{date_str}] [{paper.id}] {paper.title[:70]}...")
                print(f"      类别: {paper.category}")
        else:
            print("   ❌ 该日期范围内没有论文")
        
        return papers
    finally:
        session.close()

def main():
    print("=" * 60)
    print("未分类论文检查和清理工具")
    print("=" * 60)
    
    # 1. 检查未分类论文
    uncategorized = check_uncategorized()
    
    # 2. 询问是否删除
    if len(uncategorized) > 0:
        response = input(f"\n是否删除这 {len(uncategorized)} 篇未分类论文？(yes/no): ")
        if response.lower() in ['yes', 'y']:
            deleted = delete_uncategorized()
            if deleted > 0:
                print(f"\n✅ 已删除 {deleted} 篇未分类论文")
        else:
            print("\n⏭️  跳过删除操作")
    
    # 3. 检查2025年12月13-15日的论文
    print("\n" + "=" * 60)
    print("检查2025年12月13-15日的论文")
    print("=" * 60)
    
    start_date = date(2025, 12, 13)
    end_date = date(2025, 12, 15)
    papers = check_papers_by_date(start_date, end_date)
    
    print("\n" + "=" * 60)
    print("✅ 检查完成")
    print("=" * 60)

if __name__ == "__main__":
    main()

