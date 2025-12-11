#!/usr/bin/env python3
"""
抓取新闻信息
从Orz.ai API获取并保存到数据库
"""
import logging
import argparse
import os
from sqlalchemy import or_, and_
from rss_news_client import fetch_all_news as fetch_rss_news
from news_client import fetch_all_news as fetch_orz_news
from newsapi_client import fetch_news_from_newsapi
from save_news_to_db import batch_save_news
from news_models import init_news_db
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s %(levelname)s] %(message)s',
    datefmt='%m/%d/%Y %H:%M:%S'
)
logger = logging.getLogger(__name__)


def fetch_and_save_news():
    """
    抓取并保存新闻信息
    只保存24小时内的新闻
    """
    logger.info("=" * 60)
    logger.info("开始抓取新闻信息（24小时内）")
    logger.info("=" * 60)
    
    # 确保数据库已初始化
    try:
        init_news_db()
    except Exception as e:
        logger.warning(f"数据库初始化警告: {e}")
    
    # 获取新闻信息（先抓取，再清理，避免误删新抓取的新闻）
    # 优先级：RSS源 > NewsAPI.org > Orz.ai API
    # 优化：并发抓取多个源，提高效率
    news_list = []
    
    # 方案1: 尝试RSS源（最稳定，免费，并发优化）
    try:
        logger.info("尝试从RSS源获取新闻（并发抓取）...")
        # 先获取更多新闻，然后再过滤24小时内的
        # 增加每个源的获取数量，确保有足够的新新闻（优化：并发抓取）
        all_rss_news = fetch_rss_news(max_per_feed=150, max_workers=5)  # 并发抓取，提高效率
        # 再次过滤24小时内的新闻（双重保险）
        from datetime import datetime, timedelta
        twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
        filtered_news = [n for n in all_rss_news if n.get('published_at') and n['published_at'] >= twenty_four_hours_ago]
        if filtered_news:
            news_list = filtered_news
            logger.info(f"✅ 从RSS源获取到 {len(news_list)} 条24小时内的新闻（共抓取 {len(all_rss_news)} 条）")
        else:
            logger.warning(f"⚠️  RSS源获取到 {len(all_rss_news)} 条新闻，但没有24小时内的新闻")
    except Exception as e:
        logger.warning(f"RSS源获取失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    # 方案2: 如果RSS没有获取到足够数据（至少30条），尝试NewsAPI.org
    if len(news_list) < 30:
        try:
            logger.info("尝试从NewsAPI.org获取新闻...")
            # 计算需要补充的数量（目标30条）
            needed = 30 - len(news_list)
            newsapi_news = fetch_news_from_newsapi(max_results=max(needed + 20, 80))  # 增加获取数量
            if newsapi_news:
                # 过滤24小时内的新闻
                from datetime import datetime, timedelta
                twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
                newsapi_news = [n for n in newsapi_news if n.get('published_at') and n['published_at'] >= twenty_four_hours_ago]
                
                # 去重合并
                existing_links = {news['link'] for news in news_list}
                added_count = 0
                for news in newsapi_news:
                    if news['link'] not in existing_links:
                        news_list.append(news)
                        existing_links.add(news['link'])
                        added_count += 1
                        # 如果已经达到30条，可以提前停止
                        if len(news_list) >= 30:
                            break
                logger.info(f"✅ 从NewsAPI.org补充 {added_count} 条24小时内的新闻")
        except Exception as e:
            logger.warning(f"NewsAPI.org获取失败: {e}")
    
    # 方案3: 如果还是没有足够数据，尝试Orz.ai API（最后备选）
    if len(news_list) < 30:
        try:
            logger.info("尝试从Orz.ai API获取新闻...")
            # 计算需要补充的数量（目标30条）
            needed = 30 - len(news_list)
            orz_news = fetch_orz_news(max_per_platform=max(needed // 6 + 10, 30))  # 增加获取数量
            if orz_news:
                # 过滤24小时内的新闻
                from datetime import datetime, timedelta
                twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
                orz_news = [n for n in orz_news if n.get('published_at') and n['published_at'] >= twenty_four_hours_ago]
                
                # 去重合并
                existing_links = {news['link'] for news in news_list}
                added_count = 0
                for news in orz_news:
                    if news['link'] not in existing_links:
                        news_list.append(news)
                        existing_links.add(news['link'])
                        added_count += 1
                        # 如果已经达到30条，可以提前停止
                        if len(news_list) >= 30:
                            break
                logger.info(f"✅ 从Orz.ai API补充 {added_count} 条24小时内的新闻")
        except Exception as e:
            logger.warning(f"Orz.ai API获取失败: {e}")
    
    # 最终检查：确保至少有30条新闻（如果可能）
    if len(news_list) < 30:
        logger.warning(f"⚠️  仅获取到 {len(news_list)} 条新闻，少于目标30条")
    else:
        logger.info(f"✅ 成功获取 {len(news_list)} 条新闻，达到目标")
    
    # 最终过滤：再次检查新闻是否相关（确保过滤逻辑正确应用）
    from embodied_news_keywords import is_embodied_related
    filtered_news_list = []
    for news in news_list:
        text = (news.get('title', '') + ' ' + news.get('description', '')).lower()
        if is_embodied_related(text, strict=False):
            filtered_news_list.append(news)
        else:
            logger.debug(f"过滤掉不相关新闻: {news.get('title', '')[:60]}...")
    
    if len(filtered_news_list) < len(news_list):
        logger.info(f"✅ 最终过滤：从 {len(news_list)} 条过滤到 {len(filtered_news_list)} 条相关新闻")
        news_list = filtered_news_list
    
    # 最终过滤：确保所有新闻都在24小时内（三重保险）
    from datetime import datetime, timedelta
    twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
    final_news_list = []
    for news in news_list:
        published_at = news.get('published_at')
        if published_at and published_at >= twenty_four_hours_ago:
            final_news_list.append(news)
        elif not published_at:
            # 如果没有发布时间，使用当前时间（新抓取的新闻）
            news['published_at'] = datetime.now()
            final_news_list.append(news)
    
    news_list = final_news_list
    
    if not news_list:
        logger.warning("未获取到任何24小时内的新闻信息")
        return
    
    logger.info(f"获取到 {len(news_list)} 条24小时内的新闻，开始保存...")
    
    # 批量保存
    stats = batch_save_news(news_list)
    
    # 清理24小时前的旧新闻（在保存新新闻之后，避免误删新抓取的新闻）
    # 这样可以确保新抓取的新闻不会被误删，同时保持数据库整洁
    try:
        from datetime import datetime, timedelta
        from news_models import get_news_session, News
        session = get_news_session()
        cutoff_time = datetime.now() - timedelta(hours=24)
        # 删除24小时前的新闻（优先使用published_at，如果没有则使用created_at）
        deleted = session.query(News).filter(
            or_(
                and_(News.published_at.isnot(None), News.published_at < cutoff_time),
                and_(News.published_at.is_(None), News.created_at < cutoff_time)
            )
        ).delete()
        session.commit()
        session.close()
        if deleted > 0:
            logger.info(f"清理了 {deleted} 条24小时前的旧新闻")
    except Exception as e:
        logger.warning(f"清理旧新闻失败: {e}")
    
    logger.info("=" * 60)
    logger.info("新闻信息抓取完成")
    logger.info("=" * 60)
    logger.info(f"总计: {stats['total']} 条")
    logger.info(f"新建: {stats['created']} 条")
    logger.info(f"更新: {stats['updated']} 条")
    logger.info(f"跳过: {stats['skipped']} 条")
    logger.info(f"错误: {stats['error']} 条")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="抓取新闻信息")
    parser.add_argument("--yes", action="store_true", help="自动确认，不询问")
    
    args = parser.parse_args()
    
    if not args.yes:
        print("将从Orz.ai API获取新闻信息并保存到数据库")
        confirm = input("确认继续？(y/n): ")
        if confirm.lower() != 'y':
            print("已取消")
            exit(0)
    
    fetch_and_save_news()

