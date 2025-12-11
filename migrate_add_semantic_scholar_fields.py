#!/usr/bin/env python3
"""
数据库迁移脚本：添加Semantic Scholar相关字段
"""
from sqlalchemy import text
from models import get_engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_database():
    """执行数据库迁移"""
    engine = get_engine()
    
    try:
        with engine.connect() as conn:
            # 检查字段是否已存在
            result = conn.execute(text("PRAGMA table_info(papers)"))
            columns = [row[1] for row in result]
            
            # 需要添加的字段
            new_columns = {
                'citation_count': 'INTEGER DEFAULT 0',
                'influential_citation_count': 'INTEGER DEFAULT 0',
                'author_affiliations': 'TEXT',
                'venue': 'VARCHAR(255)',
                'publication_year': 'INTEGER',
                'semantic_scholar_updated_at': 'DATETIME'
            }
            
            # 添加不存在的字段
            for col_name, col_type in new_columns.items():
                if col_name not in columns:
                    logger.info(f"添加字段: {col_name}")
                    conn.execute(text(f"ALTER TABLE papers ADD COLUMN {col_name} {col_type}"))
                    conn.commit()
                    logger.info(f"✅ 字段 {col_name} 添加成功")
                else:
                    logger.info(f"字段 {col_name} 已存在，跳过")
            
            logger.info("✅ 数据库迁移完成！")
            
    except Exception as e:
        logger.error(f"数据库迁移失败: {e}")
        raise

if __name__ == '__main__':
    print("=" * 60)
    print("数据库迁移：添加Semantic Scholar字段")
    print("=" * 60)
    migrate_database()


