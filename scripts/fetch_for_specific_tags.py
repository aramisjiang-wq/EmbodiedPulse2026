#!/usr/bin/env python3
"""
定向抓取特定标签的论文
针对未达标的标签进行精准补充
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import arxiv
from models import get_session, Paper
from taxonomy import NEW_TAXONOMY
from datetime import datetime, timedelta
import time
import re

# 需要补充的标签和对应的ArXiv查询
TAG_QUERIES = {
    'Perception/Semantic Understanding': [
        'semantic understanding robot',
        'scene understanding robotics',
        'spatial reasoning robot',
        'language understanding embodied',
        'common sense reasoning robot'
    ],
    'Motion Control/Quadruped Robot': [
        'quadruped robot',
        'four-legged robot',
        'legged locomotion',
        'Spot robot',
        'ANYmal robot',
        'Unitree robot'
    ],
    'Decision/Chain of Thought': [
        'chain of thought robot',
        'step by step reasoning robot',
        'reasoning process robotics',
        'thought chain embodied'
    ],
    'Operation/Bimanual Manipulation': [
        'bimanual manipulation',
        'two-arm manipulation',
        'dual-arm robot',
        'bimanual coordination'
    ],
    'Motion Control/Mobile Manipulation': [
        'mobile manipulation',
        'mobile robot manipulation',
        'wheeled manipulation',
        'navigation and manipulation'
    ]
}

def classify_paper_by_keywords(paper_title, paper_abstract, target_tag):
    """
    使用关键词分类
    检索词需要在标题或摘要中出现（分别检查）
    """
    title = (paper_title or '').lower()
    abstract = (paper_abstract or '').lower()
    
    # 清理文本（移除特殊字符）
    title = re.sub(r'[^\w\s]', ' ', title)
    abstract = re.sub(r'[^\w\s]', ' ', abstract)
    
    chinese, english, keywords = NEW_TAXONOMY[target_tag]
    
    score = 0
    for keyword in keywords:
        kw_lower = keyword.lower()
        title_match = False
        abstract_match = False
        
        # 检查标题
        if title:
            if f' {kw_lower} ' in f' {title} ':
                title_match = True
                score += 3
            elif kw_lower in title:
                title_match = True
                score += 1
        
        # 检查摘要
        if abstract:
            if f' {kw_lower} ' in f' {abstract} ':
                abstract_match = True
            score += 3
            elif kw_lower in abstract:
                abstract_match = True
            score += 1
        
        # 如果标题和摘要都匹配，额外加分
        if title_match and abstract_match:
            score += 2
    
    # 如果得分够高，分类到目标标签
    if score >= 2:
        return target_tag
    
    return 'Uncategorized'

def fetch_for_tag(tag, queries, max_papers=40):
    """为特定标签抓取论文"""
    session = get_session()
    chinese, english, keywords = NEW_TAXONOMY[tag]
    
    print(f'\n{"="*80}')
    print(f'🎯 标签: {chinese} ({english})')
    print(f'   查询数: {len(queries)}')
    print(f'   目标: 补充 {max_papers} 篇')
    print(f'{"="*80}\n')
    
    added_count = 0
    classified_count = 0
    
    for query_idx, query in enumerate(queries, 1):
        if added_count >= max_papers:
            break
        
        print(f'📡 查询 {query_idx}/{len(queries)}: "{query}"')
        
        try:
            # 设置日期范围（最近1年）
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            
            search = arxiv.Search(
                query=query,
                max_results=20,
                sort_by=arxiv.SortCriterion.SubmittedDate
            )
            
            results = list(search.results())
            print(f'   找到 {len(results)} 篇论文')
            
            for result in results:
                if added_count >= max_papers:
                    break
                
                arxiv_id = result.entry_id.split('/')[-1]
                
                # 检查是否已存在
                existing = session.query(Paper).filter(Paper.id == arxiv_id).first()
                if existing:
                    continue
                
                # 分类
                category = classify_paper_by_keywords(result.title, result.summary, tag)
                
                # 创建新论文
                paper = Paper(
                    id=arxiv_id,
                    title=result.title,
                    authors=', '.join([author.name for author in result.authors]),
                    abstract=result.summary,
                    publish_date=result.published.date(),
                    pdf_url=result.pdf_url,
                    category=category,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                
                session.add(paper)
                added_count += 1
                
                if category == tag:
                    classified_count += 1
                    print(f'   ✅ [{classified_count}] {result.title[:60]}...')
                
            session.commit()
            time.sleep(3)  # API限速
            
        except Exception as e:
            print(f'   ❌ 错误: {e}')
            session.rollback()
            continue
    
    session.close()
    
    print(f'\n✅ 标签"{chinese}"完成:')
    print(f'   新增论文: {added_count}篇')
    print(f'   分类到目标: {classified_count}篇')
    
    return added_count, classified_count

def main():
    """主函数"""
    print('🚀 开始定向抓取论文...\n')
    
    total_added = 0
    total_classified = 0
    
    for tag, queries in TAG_QUERIES.items():
        added, classified = fetch_for_tag(tag, queries, max_papers=40)
        total_added += added
        total_classified += classified
    
    print(f'\n{"="*80}')
    print(f'🎉 全部完成！')
    print(f'   总新增: {total_added}篇')
    print(f'   成功分类: {total_classified}篇')
    print(f'   成功率: {total_classified*100/total_added:.1f}%' if total_added > 0 else '   成功率: N/A')
    print(f'{"="*80}')

if __name__ == '__main__':
    main()
