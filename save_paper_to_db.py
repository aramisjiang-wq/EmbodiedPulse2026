"""
将抓取的论文保存到数据库
核心原则：确保没有重复论文（基于ID和标题相似度）
"""
from models import get_session, Paper
from datetime import datetime
import logging
import json
from utils import is_duplicate_title
from taxonomy import normalize_category
from scripts.reclassify_all_papers import classify_paper_by_keywords

logger = logging.getLogger(__name__)

def save_paper_to_db(paper_data, category, enable_title_dedup=True, fetch_semantic_scholar=False):
    """
    保存论文到数据库（强制去重）
    
    去重策略（按优先级）：
    1. ID去重：如果论文ID已存在，更新记录（不创建新记录）
    2. 标题相似度去重：如果标题相似度>=0.85，跳过（可选，默认启用）
    
    Args:
        paper_data: 包含论文信息的字典
        category: 论文类别
        enable_title_dedup: 是否启用标题相似度去重（默认True）
        fetch_semantic_scholar: 是否从Semantic Scholar获取补充数据（默认False）
    
    Returns:
        tuple: (success: bool, action: str)
            - success: 是否成功
            - action: 'created'（新建）、'updated'（更新）、'skipped'（跳过，重复）
    """
    session = get_session()
    try:
        paper_id = paper_data.get('id') or paper_data.get('paper_key')
        if not paper_id:
            logger.warning("论文ID为空，跳过保存")
            return False, 'skipped'
        normalized_category = normalize_category(category)
        
        title = paper_data.get('title', '').strip()
        if not title:
            logger.warning(f"论文标题为空 (ID: {paper_id})，跳过保存")
            return False, 'skipped'
        
        # 策略1: ID去重（数据库主键约束，最高优先级）
        existing = session.query(Paper).filter_by(id=paper_id).first()
        
        if existing:
            # 论文ID已存在，更新记录（不创建新记录）
            logger.debug(f"论文ID已存在，更新记录: {paper_id}")
            
            # 如果现有记录是Uncategorized，尝试重新分类
            if existing.category == 'Uncategorized' or not existing.category:
                # 尝试获取摘要（如果缺失）
                abstract = existing.abstract or paper_data.get('abstract', '')
                if not abstract and paper_id:
                    try:
                        import arxiv
                        client = arxiv.Client(page_size=1, delay_seconds=0.5, num_retries=2)
                        search = arxiv.Search(id_list=[paper_id])
                        results = list(client.results(search))
                        if results:
                            abstract = results[0].summary.replace("\n", " ")
                            existing.abstract = abstract
                            logger.info(f"为已存在论文获取摘要: {paper_id}")
                    except Exception as e:
                        logger.debug(f"无法获取摘要 {paper_id}: {e}")
                
                # 尝试重新分类
                temp_paper = Paper(
                    id=paper_id,
                    title=existing.title or title,
                    authors=existing.authors or paper_data.get('authors', ''),
                    abstract=abstract or '',
                    pdf_url=existing.pdf_url or paper_data.get('pdf_url', ''),
                    code_url=existing.code_url or paper_data.get('code_url')
                )
                matched_tags = classify_paper_by_keywords(temp_paper)
                if matched_tags and len(matched_tags) > 0 and matched_tags[0] != 'Uncategorized':
                    existing.category = matched_tags[0]
                    logger.info(f"重新分类已存在论文: {existing.title[:50]}... -> {matched_tags[0]}")
                else:
                    # 无法分类，删除该记录
                    logger.info(f"无法分类已存在论文，删除: {existing.title[:50]}... (ID: {paper_id})")
                    session.delete(existing)
                    session.commit()
                    return False, 'skipped'
            
            # 更新现有记录
            existing.title = title or existing.title
            existing.authors = paper_data.get('authors', existing.authors)
            existing.pdf_url = paper_data.get('pdf_url', existing.pdf_url)
            existing.code_url = paper_data.get('code_url', existing.code_url)
            # 如果类别不同，更新类别（允许一篇论文属于多个类别）
            if normalized_category and existing.category != normalized_category:
                # 注意：这里只更新类别，不创建重复记录
                existing.category = normalized_category
            existing.updated_at = datetime.now()
            
            if paper_data.get('date'):
                try:
                    existing.publish_date = datetime.strptime(paper_data['date'], '%Y-%m-%d').date()
                except Exception as e:
                    logger.warning(f"解析日期失败: {e}")
            
            # 如果启用Semantic Scholar，获取补充数据
            if fetch_semantic_scholar:
                update_semantic_scholar_data(existing, paper_id, session)
            
            session.commit()
            return True, 'updated'
        
        # 策略2: 标题相似度去重（可选，默认启用）
        if enable_title_dedup:
            # 获取所有已有标题
            existing_titles = [p.title for p in session.query(Paper.title).all() if p.title]
            
            if existing_titles and is_duplicate_title(title, existing_titles, threshold=0.85):
                logger.info(f"跳过重复论文（标题相似）: {title[:50]}... (ID: {paper_id})")
                return False, 'skipped'
        
        # 如果类别是Uncategorized，尝试自动分类
        if normalized_category == 'Uncategorized' or not normalized_category:
            # 如果没有摘要，尝试从ArXiv API获取
            abstract = paper_data.get('abstract', '')
            if not abstract and paper_id:
                try:
                    import arxiv
                    client = arxiv.Client(page_size=1, delay_seconds=0.5, num_retries=2)
                    search = arxiv.Search(id_list=[paper_id])
                    results = list(client.results(search))
                    if results:
                        abstract = results[0].summary.replace("\n", " ")
                        logger.info(f"从ArXiv API获取摘要: {paper_id} ({len(abstract)} 字符)")
                        # 更新paper_data以便保存
                        paper_data['abstract'] = abstract
                except Exception as e:
                    logger.warning(f"无法从ArXiv API获取摘要 {paper_id}: {e}")
            
            # 创建临时Paper对象用于分类
            temp_paper = Paper(
                id=paper_id,
                title=title,
                authors=paper_data.get('authors', ''),
                abstract=abstract or '',  # 确保是字符串
                pdf_url=paper_data.get('pdf_url', ''),
                code_url=paper_data.get('code_url')
            )
            # 尝试分类
            matched_tags = classify_paper_by_keywords(temp_paper)
            if matched_tags and len(matched_tags) > 0 and matched_tags[0] != 'Uncategorized':
                normalized_category = matched_tags[0]
                logger.info(f"自动分类成功: {title[:50]}... -> {normalized_category}")
            else:
                # 无法分类，直接跳过（不保存到数据库）
                logger.info(f"无法分类，跳过保存: {title[:50]}... (ID: {paper_id})")
                return False, 'skipped'
        
        # 确保有摘要（如果之前从ArXiv API获取了）
        final_abstract = paper_data.get('abstract', '')
        
        # 创建新记录（此时 normalized_category 一定不是 Uncategorized）
        paper = Paper(
            id=paper_id,
            title=title,
            authors=paper_data.get('authors', ''),
            abstract=final_abstract,
            pdf_url=paper_data.get('pdf_url', ''),
            code_url=paper_data.get('code_url'),
            category=normalized_category
        )
        if paper_data.get('date'):
            try:
                paper.publish_date = datetime.strptime(paper_data['date'], '%Y-%m-%d').date()
            except Exception as e:
                logger.warning(f"解析日期失败: {e}")
        
        # 如果启用Semantic Scholar，获取补充数据
        if fetch_semantic_scholar:
            update_semantic_scholar_data(paper, paper_id, session)
        
        session.add(paper)
        session.commit()
        logger.debug(f"新建论文记录: {paper_id} - {title[:50]}...")
        return True, 'created'
        
    except Exception as e:
        session.rollback()
        logger.error(f"保存论文到数据库失败 (ID: {paper_id}): {e}")
        return False, 'error'
    finally:
        session.close()


def update_semantic_scholar_data(paper, arxiv_id, session):
    """
    从Semantic Scholar获取补充数据并更新论文记录
    
    Args:
        paper: Paper对象
        arxiv_id: ArXiv论文ID
        session: 数据库会话
    """
    try:
        from semantic_scholar_client import get_paper_supplement_data
        
        supplement_data = get_paper_supplement_data(arxiv_id)
        
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
            logger.debug(f"更新Semantic Scholar数据: {arxiv_id} - 引用数: {paper.citation_count}")
        else:
            logger.debug(f"未获取到Semantic Scholar数据: {arxiv_id}")
            
    except Exception as e:
        logger.warning(f"获取Semantic Scholar数据失败 (ID: {arxiv_id}): {e}")
        # 不抛出异常，允许论文保存继续

