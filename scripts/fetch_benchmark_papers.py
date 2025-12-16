#!/usr/bin/env python3
"""
为基准分类补齐论文
目标：100篇
检索词：embodied benchmark
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import arxiv
import logging
from datetime import datetime, timedelta
from models import get_session, Paper
from scripts.reclassify_all_papers import classify_paper_by_keywords
import time

logging.basicConfig(
    format='[%(asctime)s %(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO
)

def fetch_benchmark_papers(target_count=100):
    """
    为基准分类抓取论文
    """
    session = get_session()
    
    # 检查当前数量
    current_count = session.query(Paper).filter(
        Paper.category == 'Benchmark/Benchmark'
    ).count()
    
    logging.info("="*60)
    logging.info(f"基准分类当前论文数: {current_count} 篇")
    logging.info(f"目标: {target_count} 篇")
    logging.info(f"需要补齐: {target_count - current_count} 篇")
    logging.info("="*60)
    
    if current_count >= target_count:
        logging.info("✅ 已达标，无需补充")
        session.close()
        return
    
    need_count = target_count - current_count
    
    # 检索词：embodied benchmark
    query = "(ti:embodied benchmark OR abs:embodied benchmark) OR ((ti:embodied OR abs:embodied) AND (ti:benchmark OR abs:benchmark))"
    
    logging.info(f"\n开始抓取论文...")
    logging.info(f"查询: {query}")
    
    try:
        # 使用ArXiv Client API
        client = arxiv.Client(
            page_size=100,
            delay_seconds=2.0,
            num_retries=3
        )
        
        search = arxiv.Search(
            query=query,
            max_results=500,  # 抓取更多以确保有足够的新论文
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending
        )
        
        added_count = 0
        skipped_count = 0
        
        for result in client.results(search):
            if added_count >= need_count:
                break
            
            arxiv_id = result.entry_id.split('/abs/')[-1].split('v')[0]
            
            # 检查是否已存在
            existing = session.query(Paper).filter_by(id=arxiv_id).first()
            if existing:
                # 如果已存在但分类不是基准，检查是否需要更新
                if existing.category != 'Benchmark/Benchmark':
                    # 重新分类
                    new_tags = classify_paper_by_keywords(existing)
                    if 'Benchmark/Benchmark' in new_tags:
                        existing.category = 'Benchmark/Benchmark'
                        existing.updated_at = datetime.now()
                        session.commit()
                        added_count += 1
                        logging.info(f"  ✓ 更新分类: {arxiv_id} -> Benchmark/Benchmark")
                skipped_count += 1
                continue
            
            # 创建新论文
            paper = Paper(
                id=arxiv_id,
                title=result.title,
                authors=', '.join([author.name for author in result.authors]),
                abstract=result.summary,
                publish_date=result.published.date(),
                pdf_url=result.pdf_url,
                category='Benchmark/Benchmark',  # 直接分类为基准
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            session.add(paper)
            added_count += 1
            
            if added_count % 10 == 0:
                session.commit()
                logging.info(f"  已添加 {added_count}/{need_count} 篇...")
        
        # 提交剩余
        session.commit()
        
        logging.info("="*60)
        logging.info(f"✅ 完成!")
        logging.info(f"  新增: {added_count} 篇")
        logging.info(f"  跳过: {skipped_count} 篇（已存在）")
        
        # 验证最终数量
        final_count = session.query(Paper).filter(
            Paper.category == 'Benchmark/Benchmark'
        ).count()
        logging.info(f"  基准分类最终数量: {final_count} 篇")
        logging.info("="*60)
        
    except Exception as e:
        session.rollback()
        logging.error(f"❌ 抓取失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    fetch_benchmark_papers(target_count=100)

