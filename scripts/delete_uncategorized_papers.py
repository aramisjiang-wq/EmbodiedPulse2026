#!/usr/bin/env python3
"""
删除未分类的论文
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import get_session, Paper
import logging

logging.basicConfig(
    format='[%(asctime)s %(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO
)

def delete_uncategorized_papers():
    """删除所有未分类的论文"""
    session = get_session()
    
    try:
        # 查询未分类的论文
        uncategorized = session.query(Paper).filter(Paper.category == 'Uncategorized').all()
        count = len(uncategorized)
        
        if count == 0:
            logging.info("没有未分类的论文需要删除")
            return
        
        logging.info(f"找到 {count} 篇未分类论文，准备删除...")
        
        # 显示前5篇论文的标题（用于确认）
        logging.info("\n前5篇论文标题（用于确认）：")
        for i, paper in enumerate(uncategorized[:5], 1):
            logging.info(f"  {i}. {paper.title[:80]}...")
        if count > 5:
            logging.info(f"  ... 还有 {count - 5} 篇")
        
        # 删除所有未分类的论文
        for paper in uncategorized:
            session.delete(paper)
        
        session.commit()
        logging.info(f"\n✅ 成功删除 {count} 篇未分类论文")
        
    except Exception as e:
        session.rollback()
        logging.error(f"删除失败: {e}")
        import traceback
        logging.error(traceback.format_exc())
        raise
    finally:
        session.close()

if __name__ == "__main__":
    delete_uncategorized_papers()

