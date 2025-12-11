#!/usr/bin/env python3
"""
清理新闻数据库 - 删除非具身相关的新闻
"""
import logging
from news_models import get_news_session, News, init_news_db
from embodied_news_keywords import is_embodied_related

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s %(levelname)s] %(message)s',
    datefmt='%m/%d/%Y %H:%M:%S'
)
logger = logging.getLogger(__name__)


def clean_non_embodied_news():
    """
    清理非具身相关的新闻
    """
    logger.info("=" * 60)
    logger.info("开始清理非具身相关的新闻")
    logger.info("=" * 60)
    
    # 确保数据库已初始化
    try:
        init_news_db()
    except Exception as e:
        logger.warning(f"数据库初始化警告: {e}")
    
    session = get_news_session()
    
    try:
        # 获取所有新闻
        all_news = session.query(News).all()
        total_count = len(all_news)
        logger.info(f"数据库中共有 {total_count} 条新闻")
        
        if total_count == 0:
            logger.info("数据库为空，无需清理")
            return
        
        # 检查每条新闻是否与具身相关
        non_embodied_count = 0
        embodied_count = 0
        deleted_ids = []
        
        for news in all_news:
            # 组合标题和描述进行判断
            text = ""
            if news.title:
                text += news.title + " "
            if news.description:
                text += news.description
            
            # 判断是否与具身相关
            if not is_embodied_related(text, strict=False):
                non_embodied_count += 1
                deleted_ids.append(news.id)
            else:
                embodied_count += 1
        
        logger.info(f"具身相关新闻: {embodied_count} 条")
        logger.info(f"非具身相关新闻: {non_embodied_count} 条")
        
        # 删除非具身相关的新闻
        if deleted_ids:
            deleted = session.query(News).filter(News.id.in_(deleted_ids)).delete(synchronize_session=False)
            session.commit()
            logger.info(f"✅ 成功删除 {deleted} 条非具身相关的新闻")
        else:
            logger.info("✅ 所有新闻都是具身相关的，无需删除")
        
        # 显示清理后的统计
        remaining = session.query(News).count()
        logger.info(f"清理后剩余新闻: {remaining} 条")
        
    except Exception as e:
        logger.error(f"清理新闻失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        session.rollback()
    finally:
        session.close()
    
    logger.info("=" * 60)
    logger.info("新闻清理完成")
    logger.info("=" * 60)


if __name__ == "__main__":
    clean_non_embodied_news()
