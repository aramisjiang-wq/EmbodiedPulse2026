#!/usr/bin/env python3
"""
批量修复新闻时间戳
从RSS源重新获取正确的发布时间并更新数据库
"""
import feedparser
from email.utils import parsedate_tz
from datetime import datetime
from news_models import get_news_session, News
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# RSS源列表（与rss_news_client.py保持一致）
RSS_FEEDS = [
    {
        'name': '机器之心',
        'url': 'https://www.jiqizhixin.com/rss',
        'domain': 'jiqizhixin.com'
    },
    {
        'name': '极客公园',
        'url': 'https://www.geekpark.net/rss',
        'domain': 'geekpark.net'
    },
    {
        'name': '36氪',
        'url': 'https://36kr.com/feed',
        'domain': '36kr.com'
    },
    {
        'name': 'ArXiv Robotics',
        'url': 'http://arxiv.org/rss/cs.RO',
        'domain': 'arxiv.org'
    },
    {
        'name': 'ArXiv AI',
        'url': 'http://arxiv.org/rss/cs.AI',
        'domain': 'arxiv.org'
    },
    {
        'name': 'ArXiv Machine Learning',
        'url': 'http://arxiv.org/rss/cs.LG',
        'domain': 'arxiv.org'
    },
    {
        'name': 'The Robot Report',
        'url': 'https://www.therobotreport.com/feed/',
        'domain': 'therobotreport.com'
    },
    {
        'name': 'Robotics Business Review',
        'url': 'https://www.roboticsbusinessreview.com/feed/',
        'domain': 'roboticsbusinessreview.com'
    },
    {
        'name': 'MIT Technology Review',
        'url': 'https://www.technologyreview.com/feed/',
        'domain': 'technologyreview.com'
    },
    {
        'name': 'IEEE Spectrum',
        'url': 'https://spectrum.ieee.org/rss',
        'domain': 'ieee.org'
    }
]

def get_domain_from_url(url):
    """从URL中提取域名"""
    if not url:
        return None
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc
        # 移除www.前缀
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except:
        return None

def fetch_correct_timestamp_from_rss(news_item):
    """从RSS源获取正确的发布时间"""
    if not news_item.link:
        return None
    
    domain = get_domain_from_url(news_item.link)
    if not domain:
        return None
    
    # 找到对应的RSS源
    rss_feed = None
    for feed in RSS_FEEDS:
        if feed['domain'] in domain:
            rss_feed = feed
            break
    
    if not rss_feed:
        logger.warning(f"未找到RSS源: {domain}")
        return None
    
    try:
        logger.info(f"从 {rss_feed['name']} 获取新闻时间...")
        feed = feedparser.parse(rss_feed['url'])
        
        # 查找匹配的新闻条目
        for entry in feed.entries:
            entry_link = entry.get('link', '')
            # 比较链接（可能需要规范化）
            if entry_link == news_item.link or entry_link in news_item.link or news_item.link in entry_link:
                date_str = entry.get('published', '')
                if date_str:
                    parsed = parsedate_tz(date_str)
                    if parsed:
                        correct_time = datetime(*parsed[:6])
                        logger.info(f"  找到正确时间: {correct_time}")
                        return correct_time
        logger.warning(f"  未在RSS中找到匹配的新闻: {news_item.link}")
    except Exception as e:
        logger.error(f"获取RSS数据失败: {e}")
    
    return None

def fix_all_news_timestamps():
    """修复所有新闻的时间戳"""
    session = get_news_session()
    
    try:
        # 获取所有新闻
        all_news = session.query(News).all()
        total = len(all_news)
        logger.info(f"开始修复 {total} 条新闻的时间戳...")
        
        fixed_count = 0
        skipped_count = 0
        error_count = 0
        
        for i, news in enumerate(all_news, 1):
            try:
                # 检查是否需要修复
                # 如果发布时间和创建时间相同或非常接近（可能是错误的时间）
                if news.published_at and news.created_at:
                    time_diff = abs((news.published_at - news.created_at).total_seconds())
                    # 如果时间差小于10秒，可能是错误的时间
                    if time_diff < 10:
                        logger.info(f"[{i}/{total}] 修复: {news.title[:50]}...")
                        correct_time = fetch_correct_timestamp_from_rss(news)
                        if correct_time:
                            news.published_at = correct_time
                            session.commit()
                            fixed_count += 1
                            logger.info(f"  ✅ 已更新为: {correct_time}")
                        else:
                            skipped_count += 1
                            logger.warning(f"  ⚠️  无法获取正确时间，跳过")
                    else:
                        skipped_count += 1
                        logger.debug(f"[{i}/{total}] 跳过（时间正常）: {news.title[:50]}...")
                else:
                    # 如果没有发布时间，尝试获取
                    logger.info(f"[{i}/{total}] 添加时间: {news.title[:50]}...")
                    correct_time = fetch_correct_timestamp_from_rss(news)
                    if correct_time:
                        news.published_at = correct_time
                        session.commit()
                        fixed_count += 1
                        logger.info(f"  ✅ 已添加: {correct_time}")
                    else:
                        skipped_count += 1
                        logger.warning(f"  ⚠️  无法获取时间，跳过")
                
                # 避免请求过快
                time.sleep(0.5)
                
            except Exception as e:
                error_count += 1
                logger.error(f"[{i}/{total}] 处理失败: {e}")
                continue
        
        logger.info("=" * 60)
        logger.info(f"修复完成！")
        logger.info(f"总计: {total} 条")
        logger.info(f"修复: {fixed_count} 条")
        logger.info(f"跳过: {skipped_count} 条")
        logger.info(f"错误: {error_count} 条")
        
    finally:
        session.close()

if __name__ == '__main__':
    fix_all_news_timestamps()







