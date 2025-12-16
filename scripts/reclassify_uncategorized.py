#!/usr/bin/env python3
"""
尝试重新分类未分类的论文，无法分类的则删除
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import get_session, Paper
import sys
import os
# 导入分类函数
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.reclassify_all_papers import classify_paper_by_keywords
import logging

logging.basicConfig(
    format='[%(asctime)s %(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO
)

def reclassify_uncategorized():
    """尝试重新分类未分类的论文"""
    session = get_session()
    
    try:
        # 查询未分类的论文
        uncategorized = session.query(Paper).filter(Paper.category == 'Uncategorized').all()
        count = len(uncategorized)
        
        if count == 0:
            logging.info("没有未分类的论文")
            return
        
        logging.info(f"找到 {count} 篇未分类论文，尝试重新分类...")
        
        reclassified = 0
        deleted = 0
        
        for paper in uncategorized:
            # 尝试重新分类
            matched_tags = classify_paper_by_keywords(paper)
            
            if matched_tags and len(matched_tags) > 0 and matched_tags[0] != 'Uncategorized':
                # 成功分类，使用第一个匹配的标签
                classified_tag = matched_tags[0]
                paper.category = classified_tag
                session.add(paper)
                reclassified += 1
                logging.info(f"✅ 重新分类: {paper.title[:60]}... -> {classified_tag}")
            else:
                # 无法分类，删除
                session.delete(paper)
                deleted += 1
                logging.info(f"❌ 无法分类，已删除: {paper.title[:60]}...")
        
        session.commit()
        logging.info(f"\n✅ 完成!")
        logging.info(f"  重新分类: {reclassified} 篇")
        logging.info(f"  删除: {deleted} 篇")
        
    except Exception as e:
        session.rollback()
        logging.error(f"处理失败: {e}")
        import traceback
        logging.error(traceback.format_exc())
        raise
    finally:
        session.close()

if __name__ == "__main__":
    reclassify_uncategorized()

