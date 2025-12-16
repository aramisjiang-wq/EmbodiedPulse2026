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
import time

logging.basicConfig(
    format='[%(asctime)s %(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO
)

# 机器人相关的广泛查询
QUERIES = [
    "cat:cs.RO",  # Robotics类别
    "cat:cs.CV AND robot",
    "cat:cs.LG AND robot",
    "cat:cs.AI AND (robot OR embodied)",
]

def fetch_papers_by_date(start_date, end_date):
    """
    抓取指定日期范围的论文
    """
    session = get_session()
    all_papers = {}
    
    logging.info(f"抓取日期: {start_date} 到 {end_date}")
    logging.info("="*60)
    
    for query in QUERIES:
        logging.info(f"\n查询: {query}")
        
        # 构建日期过滤
        date_filter = f"submittedDate:[{start_date.strftime('%Y%m%d')}0000 TO {end_date.strftime('%Y%m%d')}2359]"
        full_query = f"{query} AND {date_filter}"
        
        try:
            search = arxiv.Search(
                query=full_query,
                max_results=1000,
                sort_by=arxiv.SortCriterion.SubmittedDate
            )
            
            count = 0
            for result in search.results():
                arxiv_id = result.entry_id.split('/abs/')[-1].split('v')[0]
                
                if arxiv_id not in all_papers:
                    # 检查是否已存在
                    existing = session.query(Paper).filter_by(id=arxiv_id).first()
                    if not existing:
                        all_papers[arxiv_id] = result
                        count += 1
            
            logging.info(f"  找到 {count} 篇新论文")
            time.sleep(3)
            
        except Exception as e:
            logging.error(f"  查询失败: {e}")
            continue
    
    logging.info(f"\n总共找到 {len(all_papers)} 篇唯一的新论文")
    
    # 保存到数据库
    logging.info("\n开始保存到数据库...")
    new_count = 0
    
    for arxiv_id, result in all_papers.items():
        try:
            paper = Paper(
                id=arxiv_id,
                title=result.title,
                authors=', '.join([author.name for author in result.authors]),
                abstract=result.summary,
                publish_date=result.published.date(),
                pdf_url=result.pdf_url,
                category='Uncategorized',
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            session.add(paper)
            new_count += 1
            
            if new_count % 100 == 0:
                session.commit()
                logging.info(f"  已保存 {new_count} 篇")
                
        except Exception as e:
            logging.error(f"  保存失败 {arxiv_id}: {e}")
            continue
    
    session.commit()
    session.close()
    
    logging.info(f"\n✅ 完成！新增 {new_count} 篇论文")
    return new_count


if __name__ == "__main__":
    # 抓取12月13-15日
    start = datetime(2025, 12, 13)
    end = datetime(2025, 12, 15)
    
    fetch_papers_by_date(start, end)
