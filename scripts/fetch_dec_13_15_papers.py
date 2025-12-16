#!/usr/bin/env python3
"""
抓取2025年12月13-15日的论文
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import arxiv
import logging
from datetime import datetime
from models import get_session, Paper
from scripts.reclassify_all_papers import classify_paper_by_keywords
import time

logging.basicConfig(
    format='[%(asctime)s %(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO
)

# 机器人相关的广泛查询（同时搜索标题和摘要）
QUERIES = [
    "(ti:robot OR abs:robot) OR (ti:robotic OR abs:robotic) OR (ti:robotics OR abs:robotics)",
    "(ti:embodied OR abs:embodied) OR (ti:autonomous agent OR abs:autonomous agent)",
    "(ti:manipulation OR abs:manipulation) OR (ti:grasp OR abs:grasp)",
    "(ti:perception OR abs:perception) OR (ti:vision OR abs:vision)",
    "(ti:learning OR abs:learning) AND ((ti:robot OR abs:robot) OR (ti:embodied OR abs:embodied))",
    "(ti:control OR abs:control) AND ((ti:robot OR abs:robot) OR (ti:motion OR abs:motion))",
    "(ti:planning OR abs:planning) AND ((ti:robot OR abs:robot) OR (ti:task OR abs:task))",
]

def fetch_papers_by_date_range(start_date, end_date):
    """
    抓取指定日期范围的论文
    """
    session = get_session()
    all_papers = {}
    
    logging.info("="*60)
    logging.info(f"抓取日期: {start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}")
    logging.info("="*60)
    
    for query_idx, query in enumerate(QUERIES, 1):
        logging.info(f"\n查询 {query_idx}/{len(QUERIES)}: {query[:80]}...")
        
        # 构建日期过滤
        date_filter = f"submittedDate:[{start_date.strftime('%Y%m%d')}0000 TO {end_date.strftime('%Y%m%d')}2359]"
        full_query = f"({query}) AND {date_filter}"
        
        try:
            client = arxiv.Client(
                page_size=100,
                delay_seconds=2.0,
                num_retries=3
            )
            
            search = arxiv.Search(
                query=full_query,
                max_results=500,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )
            
            count = 0
            for result in client.results(search):
                arxiv_id = result.entry_id.split('/abs/')[-1].split('v')[0]
                
                if arxiv_id not in all_papers:
                    # 检查是否已存在
                    existing = session.query(Paper).filter_by(id=arxiv_id).first()
                    if not existing:
                        all_papers[arxiv_id] = result
                        count += 1
            
            logging.info(f"  找到 {count} 篇新论文")
            time.sleep(3)  # API限流
            
        except Exception as e:
            logging.error(f"  查询失败: {e}")
            continue
    
    logging.info(f"\n总共找到 {len(all_papers)} 篇唯一的新论文")
    
    # 保存到数据库并分类
    if all_papers:
        logging.info("\n开始保存到数据库并分类...")
        new_count = 0
        updated_count = 0
        
        for arxiv_id, result in all_papers.items():
            try:
                # 创建临时Paper对象用于分类
                temp_paper = Paper(
                    id=arxiv_id,
                    title=result.title,
                    authors=', '.join([author.name for author in result.authors]),
                    abstract=result.summary,
                    publish_date=result.published.date(),
                    pdf_url=result.pdf_url
                )
                
                # 分类
                new_tags = classify_paper_by_keywords(temp_paper)
                category = new_tags[0] if new_tags else 'Uncategorized'
                
                # 创建论文记录
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
                new_count += 1
                
                if new_count % 50 == 0:
                    session.commit()
                    logging.info(f"  已保存 {new_count} 篇...")
                    
            except Exception as e:
                logging.error(f"  保存论文 {arxiv_id} 失败: {e}")
                continue
        
        session.commit()
        
        logging.info("="*60)
        logging.info(f"✅ 完成!")
        logging.info(f"  新增: {new_count} 篇")
        logging.info("="*60)
    else:
        logging.info("未找到新论文")
    
    session.close()


if __name__ == "__main__":
    # 2025年12月13-15日
    start_date = datetime(2025, 12, 13)
    end_date = datetime(2025, 12, 15)
    
    fetch_papers_by_date_range(start_date, end_date)

