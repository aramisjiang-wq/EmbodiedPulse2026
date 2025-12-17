#!/usr/bin/env python3
"""
全量抓取论文脚本
使用宽泛的关键词查询，抓取所有相关领域的论文
用于补充关键词抓取可能遗漏的论文
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import arxiv
import logging
from datetime import datetime, timedelta
from models import get_session, Paper
from save_paper_to_db import save_paper_to_db
from taxonomy import normalize_category

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def fetch_full_papers(days_back=3, max_results_per_query=100):
    """
    全量抓取论文（使用宽泛的关键词查询）
    
    Args:
        days_back: 抓取最近N天的论文（默认3天）
        max_results_per_query: 每个查询的最大结果数（默认100）
    """
    logger.info("=" * 60)
    logger.info("开始全量抓取论文（宽泛关键词查询）")
    logger.info("=" * 60)
    
    # 宽泛的关键词查询（覆盖所有具身智能相关领域）
    broad_queries = [
        # 机器人相关
        '(robot OR robotics OR robotic OR "robot learning" OR "robotic system")',
        # 具身智能相关
        '(embodied OR "embodied AI" OR "embodied agent" OR "embodied intelligence")',
        # 操作相关
        '(manipulation OR grasping OR "pick and place" OR "object manipulation")',
        # 感知相关
        '(perception OR "computer vision" OR "visual perception" OR "3d perception")',
        # 学习相关
        '("reinforcement learning" OR "imitation learning" OR "robot learning")',
        # 规划相关
        '(planning OR navigation OR "path planning" OR "task planning")',
    ]
    
    # 计算日期范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    date_filter = f"submittedDate:[{start_date.strftime('%Y%m%d')}0000 TO {end_date.strftime('%Y%m%d')}2359]"
    
    logger.info(f"查询日期范围: {start_date.date()} 到 {end_date.date()} (最近{days_back}天)")
    logger.info(f"查询数量: {len(broad_queries)} 个宽泛查询")
    logger.info("")
    
    # 使用ArXiv Client
    client = arxiv.Client(
        page_size=100,
        delay_seconds=1.5,
        num_retries=3
    )
    
    all_papers = {}  # 使用字典去重（key: paper_id）
    total_fetched = 0
    
    for i, query in enumerate(broad_queries, 1):
        try:
            # 构建完整查询（添加日期过滤）
            full_query = f"({query}) AND {date_filter}"
            
            logger.info(f"[{i}/{len(broad_queries)}] 查询: {query[:50]}...")
            
            search = arxiv.Search(
                query=full_query,
                max_results=max_results_per_query,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )
            
            results = list(client.results(search))
            logger.info(f"  获取到 {len(results)} 篇论文")
            
            # 处理结果
            for result in results:
                paper_id = result.get_short_id()
                if paper_id not in all_papers:
                    all_papers[paper_id] = result
                    total_fetched += 1
            
            logger.info(f"  累计唯一论文: {len(all_papers)} 篇")
            logger.info("")
            
        except Exception as e:
            logger.error(f"查询失败: {e}")
            continue
    
    logger.info("=" * 60)
    logger.info(f"全量抓取完成，共获取 {len(all_papers)} 篇唯一论文")
    logger.info("=" * 60)
    logger.info("")
    
    # 保存到数据库
    if all_papers:
        logger.info("开始保存到数据库...")
        session = get_session()
        saved_count = 0
        skipped_count = 0
        
        for i, (paper_id, result) in enumerate(all_papers.items(), 1):
            try:
                # 构建论文数据
                paper_data = {
                    'id': paper_id,
                    'title': result.title,
                    'authors': ', '.join([author.name for author in result.authors]),
                    'abstract': result.summary.replace('\n', ' '),
                    'pdf_url': result.pdf_url,
                    'code_url': None,
                    'date': result.published.date().strftime('%Y-%m-%d'),
                }
                
                # 使用自动分类（Uncategorized，让save_paper_to_db自动分类）
                category = 'Uncategorized'
                
                # 保存到数据库（启用去重和自动分类）
                success, action = save_paper_to_db(
                    paper_data,
                    category,
                    enable_title_dedup=True,
                    fetch_semantic_scholar=False  # 全量抓取时不获取Semantic Scholar数据，加快速度
                )
                
                if success:
                    saved_count += 1
                elif action == 'skipped':
                    skipped_count += 1
                
                # 每50篇输出一次进度
                if i % 50 == 0:
                    logger.info(f"  已处理 {i}/{len(all_papers)} 篇... (保存: {saved_count}, 跳过: {skipped_count})")
            
            except Exception as e:
                logger.error(f"保存论文失败 {paper_id}: {e}")
                continue
        
        session.close()
        
        logger.info("")
        logger.info("=" * 60)
        logger.info(f"保存完成！")
        logger.info(f"  ✅ 新增: {saved_count} 篇")
        logger.info(f"  ⏭️  跳过: {skipped_count} 篇（重复）")
        logger.info("=" * 60)
    else:
        logger.info("没有找到新论文")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='全量抓取论文（宽泛关键词查询）')
    parser.add_argument('--days', type=int, default=3, help='抓取最近N天的论文（默认3天）')
    parser.add_argument('--max-results', type=int, default=100, help='每个查询的最大结果数（默认100）')
    
    args = parser.parse_args()
    
    fetch_full_papers(days_back=args.days, max_results_per_query=args.max_results)

