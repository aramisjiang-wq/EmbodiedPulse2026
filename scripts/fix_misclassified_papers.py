#!/usr/bin/env python3
"""
修复误分类的论文
使用改进的分类算法重新分类被错误分类的论文
"""
import sys
import os
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from models import get_session, Paper
from taxonomy import normalize_category, UNCATEGORIZED_KEY
from scripts.improved_classifier import classify_paper_by_keywords_improved
import logging

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def fix_misclassified_papers():
    """修复误分类的论文"""
    session = get_session()
    
    try:
        # 查找被错误分类为"Learning/Imitation Learning"的论文
        # 这些论文可能不包含imitation learning相关关键词
        il_papers = session.query(Paper).filter(
            Paper.category == 'Learning/Imitation Learning'
        ).all()
        
        logger.info(f"找到 {len(il_papers)} 篇被分类为'Learning/Imitation Learning'的论文")
        logger.info("开始检查并修复误分类...")
        logger.info("=" * 60)
        
        fixed_count = 0
        kept_count = 0
        
        for i, paper in enumerate(il_papers, 1):
            try:
                # 检查是否真的包含imitation learning关键词
                text = (paper.title + ' ' + (paper.abstract or '')).lower()
                has_il_keywords = any(kw in text for kw in [
                    'imitation learning', 'behavioral cloning', 'learning from demonstration',
                    'demonstration learning', 'behavior cloning', 'lfd',
                    'inverse reinforcement', 'learning from human', 'expert demonstration',
                    'learning from data', 'demonstration data'
                ])
                
                if not has_il_keywords:
                    # 使用改进的分类算法重新分类
                    new_tags = classify_paper_by_keywords_improved(paper)
                    if new_tags and new_tags[0] != 'Learning/Imitation Learning':
                        new_category = normalize_category(new_tags[0])
                        old_category = paper.category
                        paper.category = new_category
                        paper.updated_at = datetime.now()
                        fixed_count += 1
                        logger.info(f"[{i}/{len(il_papers)}] ✅ 修复: {paper.title[:50]}...")
                        logger.info(f"     {old_category} → {new_category}")
                    else:
                        kept_count += 1
                        logger.debug(f"[{i}/{len(il_papers)}] 保持: {paper.title[:50]}...")
                else:
                    kept_count += 1
                    logger.debug(f"[{i}/{len(il_papers)}] 保持: {paper.title[:50]}... (包含IL关键词)")
                
                # 每10篇提交一次
                if i % 10 == 0:
                    session.commit()
                    logger.info(f"已处理 {i}/{len(il_papers)} 篇...")
            
            except Exception as e:
                logger.error(f"处理论文失败 {paper.id}: {e}")
                continue
        
        session.commit()
        session.close()
        
        logger.info("=" * 60)
        logger.info(f"修复完成！")
        logger.info(f"✅ 修复: {fixed_count} 篇")
        logger.info(f"📌 保持: {kept_count} 篇")
        
    except Exception as e:
        logger.error(f"修复过程失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        session.rollback()
        session.close()

if __name__ == '__main__':
    fix_misclassified_papers()

