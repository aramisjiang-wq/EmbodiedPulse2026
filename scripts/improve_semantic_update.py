#!/usr/bin/env python3
"""
改进的Semantic Scholar更新脚本
支持增量更新（更新已有数据的论文）
"""
import logging
import time
from models import get_session, Paper
from semantic_scholar_client import get_paper_supplement_data
import json
from datetime import datetime, timedelta

logging.basicConfig(
    format='[%(asctime)s %(levelname)s] %(message)s',
    datefmt='%m/%d/%Y %H:%M:%S',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def update_recent_papers(days=30, limit=None):
    """
    更新最近N天的论文（增量更新）
    
    Args:
        days: 更新最近N天的论文（默认30天）
        limit: 限制更新的论文数量（None表示全部）
    """
    session = get_session()
    
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # 查询最近N天的论文（无论是否已有Semantic Scholar数据）
        query = session.query(Paper).filter(
            Paper.publish_date >= cutoff_date.date()
        ).order_by(Paper.publish_date.desc())
        
        if limit:
            query = query.limit(limit)
        
        papers = query.all()
        total = len(papers)
        
        logger.info(f"找到 {total} 篇最近{days}天的论文（将进行增量更新）")
        
        if total == 0:
            logger.info("没有需要更新的论文")
            return
        
        success_count = 0
        fail_count = 0
        skipped_count = 0
        
        for idx, paper in enumerate(papers, 1):
            try:
                # 检查是否需要更新（如果数据超过7天，需要更新）
                needs_update = True
                if paper.semantic_scholar_updated_at:
                    days_since_update = (datetime.now() - paper.semantic_scholar_updated_at).days
                    if days_since_update < 7:
                        skipped_count += 1
                        needs_update = False
                        logger.debug(f"[{idx}/{total}] 跳过（7天内已更新）: {paper.id}")
                
                if not needs_update:
                    continue
                
                logger.info(f"[{idx}/{total}] 更新论文: {paper.id} - {paper.title[:50]}...")
                
                supplement_data = get_paper_supplement_data(paper.id)
                
                if supplement_data:
                    paper.citation_count = supplement_data.get('citation_count', 0) or 0
                    paper.influential_citation_count = supplement_data.get('influential_citation_count', 0) or 0
                    paper.venue = supplement_data.get('venue', '') or ''
                    paper.publication_year = supplement_data.get('publication_year')
                    
                    # 保存机构信息为JSON字符串
                    affiliations = supplement_data.get('author_affiliations', [])
                    if affiliations:
                        paper.author_affiliations = json.dumps(affiliations, ensure_ascii=False)
                    
                    paper.semantic_scholar_updated_at = datetime.now()
                    
                    session.commit()
                    success_count += 1
                    logger.info(f"  ✅ 成功: 引用数={paper.citation_count}, 机构数={len(affiliations)}")
                else:
                    fail_count += 1
                    logger.warning(f"  ⚠️  未获取到数据")
                
                # 添加延迟以避免速率限制
                if idx < total:
                    time.sleep(0.15)  # 150ms延迟，确保不超过速率限制
                    
            except Exception as e:
                fail_count += 1
                logger.error(f"  ❌ 更新失败: {e}")
                session.rollback()
                continue
        
        logger.info("=" * 60)
        logger.info(f"更新完成！成功: {success_count}, 失败: {fail_count}, 跳过: {skipped_count}")
        
    except Exception as e:
        logger.error(f"批量更新失败: {e}")
        session.rollback()
    finally:
        session.close()


def update_all_papers_incremental(limit=None, skip_recent=True):
    """
    增量更新所有论文的Semantic Scholar数据
    
    Args:
        limit: 限制更新的论文数量（None表示全部）
        skip_recent: 是否跳过最近7天已更新的论文
    """
    session = get_session()
    
    try:
        # 查询需要更新的论文
        query = session.query(Paper)
        
        if skip_recent:
            # 跳过最近7天已更新的论文
            cutoff_date = datetime.now() - timedelta(days=7)
            query = query.filter(
                (Paper.semantic_scholar_updated_at == None) |
                (Paper.semantic_scholar_updated_at < cutoff_date)
            )
        
        # 按发布日期倒序排序，优先更新最新论文
        query = query.order_by(Paper.publish_date.desc())
        
        if limit:
            query = query.limit(limit)
        
        papers = query.all()
        total = len(papers)
        
        logger.info(f"找到 {total} 篇需要更新的论文（增量更新）")
        
        if total == 0:
            logger.info("没有需要更新的论文")
            return
        
        success_count = 0
        fail_count = 0
        
        for idx, paper in enumerate(papers, 1):
            try:
                logger.info(f"[{idx}/{total}] 更新论文: {paper.id} - {paper.title[:50]}...")
                
                supplement_data = get_paper_supplement_data(paper.id)
                
                if supplement_data:
                    paper.citation_count = supplement_data.get('citation_count', 0) or 0
                    paper.influential_citation_count = supplement_data.get('influential_citation_count', 0) or 0
                    paper.venue = supplement_data.get('venue', '') or ''
                    paper.publication_year = supplement_data.get('publication_year')
                    
                    # 保存机构信息为JSON字符串
                    affiliations = supplement_data.get('author_affiliations', [])
                    if affiliations:
                        paper.author_affiliations = json.dumps(affiliations, ensure_ascii=False)
                    
                    paper.semantic_scholar_updated_at = datetime.now()
                    
                    session.commit()
                    success_count += 1
                    logger.info(f"  ✅ 成功: 引用数={paper.citation_count}, 机构数={len(affiliations)}")
                else:
                    fail_count += 1
                    logger.warning(f"  ⚠️  未获取到数据")
                
                # 添加延迟以避免速率限制
                if idx < total:
                    time.sleep(0.15)  # 150ms延迟，确保不超过速率限制
                    
            except Exception as e:
                fail_count += 1
                logger.error(f"  ❌ 更新失败: {e}")
                session.rollback()
                continue
        
        logger.info("=" * 60)
        logger.info(f"更新完成！成功: {success_count}, 失败: {fail_count}")
        
    except Exception as e:
        logger.error(f"批量更新失败: {e}")
        session.rollback()
    finally:
        session.close()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='改进的Semantic Scholar数据更新（支持增量更新）')
    parser.add_argument('--recent', type=int, help='更新最近N天的论文（增量更新）')
    parser.add_argument('--limit', type=int, help='限制更新的论文数量')
    parser.add_argument('--all', action='store_true', help='更新所有论文（增量更新）')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("改进的Semantic Scholar数据更新（支持增量更新）")
    print("=" * 60)
    
    if args.recent:
        update_recent_papers(days=args.recent, limit=args.limit)
    elif args.all:
        update_all_papers_incremental(limit=args.limit, skip_recent=True)
    else:
        # 默认：更新最近30天的论文
        update_recent_papers(days=30, limit=args.limit)

