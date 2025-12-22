#!/usr/bin/env python3
"""
测试Semantic Scholar数据更新功能
用于诊断问题
"""
import sys
import logging
from models import get_session, Paper
from semantic_scholar_client import get_paper_supplement_data
import json

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s %(levelname)s] %(message)s',
    datefmt='%m/%d/%Y %H:%M:%S'
)
logger = logging.getLogger(__name__)

def test_semantic_scholar_update():
    """测试Semantic Scholar更新功能"""
    session = get_session()
    
    try:
        # 查找一篇论文进行测试
        paper = session.query(Paper).filter(
            Paper.semantic_scholar_updated_at == None
        ).first()
        
        if not paper:
            # 如果没有未更新的，找一篇已更新的查看数据
            paper = session.query(Paper).first()
            logger.info(f"未找到未更新的论文，使用已有论文进行测试: {paper.id}")
        else:
            logger.info(f"找到未更新的论文: {paper.id}")
        
        if not paper:
            logger.error("数据库中没有论文数据")
            return
        
        logger.info("=" * 60)
        logger.info(f"测试论文: {paper.id}")
        logger.info(f"标题: {paper.title[:80]}...")
        logger.info(f"当前引用数: {paper.citation_count}")
        logger.info(f"当前期刊: {paper.venue}")
        logger.info(f"当前机构信息: {paper.author_affiliations}")
        logger.info("=" * 60)
        
        # 调用API获取数据
        logger.info("正在调用Semantic Scholar API...")
        supplement_data = get_paper_supplement_data(paper.id)
        
        if supplement_data:
            logger.info("✅ 成功获取Semantic Scholar数据:")
            logger.info(f"  引用数: {supplement_data.get('citation_count', 0)}")
            logger.info(f"  高影响力引用: {supplement_data.get('influential_citation_count', 0)}")
            logger.info(f"  期刊: {supplement_data.get('venue', 'N/A')}")
            logger.info(f"  发表年份: {supplement_data.get('publication_year', 'N/A')}")
            logger.info(f"  机构数量: {len(supplement_data.get('author_affiliations', []))}")
            
            affiliations = supplement_data.get('author_affiliations', [])
            if affiliations:
                logger.info(f"  机构列表: {', '.join(affiliations[:5])}")
            
            # 更新数据库
            logger.info("\n正在更新数据库...")
            paper.citation_count = supplement_data.get('citation_count', 0) or 0
            paper.influential_citation_count = supplement_data.get('influential_citation_count', 0) or 0
            paper.venue = supplement_data.get('venue', '') or ''
            paper.publication_year = supplement_data.get('publication_year')
            
            if affiliations:
                paper.author_affiliations = json.dumps(affiliations, ensure_ascii=False)
            
            from datetime import datetime
            paper.semantic_scholar_updated_at = datetime.now()
            
            session.commit()
            logger.info("✅ 数据库更新成功")
            
            # 验证更新
            session.refresh(paper)
            logger.info("\n更新后的数据:")
            logger.info(f"  引用数: {paper.citation_count}")
            logger.info(f"  高影响力引用: {paper.influential_citation_count}")
            logger.info(f"  期刊: {paper.venue}")
            logger.info(f"  发表年份: {paper.publication_year}")
            logger.info(f"  机构信息: {paper.author_affiliations}")
            logger.info(f"  更新时间: {paper.semantic_scholar_updated_at}")
        else:
            logger.warning("❌ 未能获取Semantic Scholar数据")
            logger.warning("可能的原因:")
            logger.warning("  1. 论文不在Semantic Scholar数据库中")
            logger.warning("  2. API调用失败")
            logger.warning("  3. 网络问题")
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        session.rollback()
    finally:
        session.close()

if __name__ == '__main__':
    test_semantic_scholar_update()

