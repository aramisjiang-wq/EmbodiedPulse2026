#!/usr/bin/env python3
"""
批量更新已有论文的Semantic Scholar数据
"""
import logging
import time
from models import get_session, Paper
from semantic_scholar_client import get_paper_supplement_data
import json
from datetime import datetime

logging.basicConfig(
    format='[%(asctime)s %(levelname)s] %(message)s',
    datefmt='%m/%d/%Y %H:%M:%S',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def update_all_papers(limit=None, skip_existing=True, status=None, status_lock=None):
    """
    批量更新所有论文的Semantic Scholar数据
    
    Args:
        limit: 限制更新的论文数量（None表示全部）
        skip_existing: 是否跳过已有Semantic Scholar数据的论文
        status: 用于更新状态的字典（可选）
        status_lock: 用于线程安全更新的锁（可选）
    """
    session = get_session()
    
    try:
        # 查询需要更新的论文
        query = session.query(Paper)
        
        if skip_existing:
            # 只更新没有Semantic Scholar数据的论文
            query = query.filter(
                (Paper.citation_count == None) | 
                (Paper.citation_count == 0) |
                (Paper.semantic_scholar_updated_at == None)
            )
        
        # 按发布日期倒序排序，优先更新最新论文
        query = query.order_by(Paper.publish_date.desc())
        
        if limit:
            query = query.limit(limit)
        
        papers = query.all()
        total = len(papers)
        
        logger.info(f"找到 {total} 篇需要更新的论文")
        
        # 更新状态
        if status is not None:
            if status_lock:
                with status_lock:
                    status['total'] = total
                    status['progress'] = 0
                    status['message'] = f'找到 {total} 篇需要更新的论文'
                    status['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            else:
                status['total'] = total
                status['progress'] = 0
                status['message'] = f'找到 {total} 篇需要更新的论文'
                status['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if total == 0:
            logger.info("没有需要更新的论文")
            if status is not None:
                if status_lock:
                    with status_lock:
                        status['message'] = '没有需要更新的论文'
                        status['running'] = False
                        status['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                else:
                    status['message'] = '没有需要更新的论文'
                    status['running'] = False
                    status['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            return
        
        success_count = 0
        fail_count = 0
        
        for idx, paper in enumerate(papers, 1):
            try:
                logger.info(f"[{idx}/{total}] 更新论文: {paper.id} - {paper.title[:50]}...")
                
                # 更新状态
                if status is not None:
                    if status_lock:
                        with status_lock:
                            status['progress'] = idx
                            status['current_paper'] = paper.id
                            status['message'] = f'正在更新: {paper.title[:50]}... ({idx}/{total})'
                            status['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        status['progress'] = idx
                        status['current_paper'] = paper.id
                        status['message'] = f'正在更新: {paper.title[:50]}... ({idx}/{total})'
                        status['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
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
        
        # 更新最终状态
        final_message = f'更新完成！成功: {success_count}, 失败: {fail_count}'
        logger.info("=" * 60)
        logger.info(final_message)
        logger.info("=" * 60)
        
        if status is not None:
            if status_lock:
                with status_lock:
                    status['message'] = final_message
                    status['progress'] = total
                    status['current_paper'] = ''
                    status['running'] = False
                    status['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            else:
                status['message'] = final_message
                status['progress'] = total
                status['current_paper'] = ''
                status['running'] = False
                status['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
    except Exception as e:
        error_msg = f"批量更新失败: {e}"
        logger.error(error_msg)
        session.rollback()
        
        # 更新错误状态
        if status is not None:
            if status_lock:
                with status_lock:
                    status['message'] = error_msg
                    status['running'] = False
                    status['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            else:
                status['message'] = error_msg
                status['running'] = False
                status['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    finally:
        session.close()


def update_category_papers(category, limit=None):
    """
    更新指定类别的论文
    
    Args:
        category: 论文类别
        limit: 限制更新的论文数量
    """
    session = get_session()
    
    try:
        query = session.query(Paper).filter(Paper.category == category)
        
        if limit:
            query = query.limit(limit)
        
        papers = query.all()
        total = len(papers)
        
        logger.info(f"找到 {total} 篇 {category} 类别的论文")
        
        for idx, paper in enumerate(papers, 1):
            try:
                logger.info(f"[{idx}/{total}] 更新: {paper.id}")
                supplement_data = get_paper_supplement_data(paper.id)
                
                if supplement_data:
                    paper.citation_count = supplement_data.get('citation_count', 0) or 0
                    paper.influential_citation_count = supplement_data.get('influential_citation_count', 0) or 0
                    paper.venue = supplement_data.get('venue', '') or ''
                    paper.publication_year = supplement_data.get('publication_year')
                    
                    affiliations = supplement_data.get('author_affiliations', [])
                    if affiliations:
                        paper.author_affiliations = json.dumps(affiliations, ensure_ascii=False)
                    
                    paper.semantic_scholar_updated_at = datetime.now()
                    session.commit()
                    logger.info(f"  ✅ 成功")
                
                if idx < total:
                    time.sleep(0.15)
                    
            except Exception as e:
                logger.error(f"  ❌ 失败: {e}")
                session.rollback()
        
    finally:
        session.close()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='批量更新论文的Semantic Scholar数据')
    parser.add_argument('--limit', type=int, help='限制更新的论文数量')
    parser.add_argument('--category', type=str, help='只更新指定类别的论文')
    parser.add_argument('--skip-existing', action='store_true', default=True, help='跳过已有数据的论文')
    parser.add_argument('--no-skip', action='store_false', dest='skip_existing', help='不跳过已有数据的论文（强制更新）')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("批量更新Semantic Scholar数据")
    print("=" * 60)
    
    if args.category:
        update_category_papers(args.category, args.limit)
    else:
        update_all_papers(limit=args.limit, skip_existing=args.skip_existing)

