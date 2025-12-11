#!/usr/bin/env python3
"""
RSS新闻客户端
从多个RSS源获取具身智能相关新闻
"""
import feedparser
import requests
import logging
from typing import List, Dict, Optional
from datetime import datetime
import re
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

logger = logging.getLogger(__name__)

# 导入扩展的关键词配置
from embodied_news_keywords import (
    ALL_EMBODIED_KEYWORDS,
    RSS_FILTER_KEYWORDS,
    is_embodied_related,
    COMPANY_NAMES
)

# 使用扩展的关键词列表
EMBODIED_AI_KEYWORDS = ALL_EMBODIED_KEYWORDS

# RSS源列表（按稳定性排序，最稳定的在前）
RSS_FEEDS = [
    # 机器之心（已验证可用）
    {
        'name': '机器之心',
        'url': 'https://www.jiqizhixin.com/rss',
        'category': '科技媒体'
    },
    # ArXiv RSS（机器人相关，使用HTTP避免SSL问题）
    {
        'name': 'ArXiv Robotics',
        'url': 'http://arxiv.org/rss/cs.RO',
        'category': '学术'
    },
    # ArXiv RSS（AI相关）
    {
        'name': 'ArXiv AI',
        'url': 'http://arxiv.org/rss/cs.AI',
        'category': '学术'
    },
    # ArXiv RSS（机器学习相关）
    {
        'name': 'ArXiv Machine Learning',
        'url': 'http://arxiv.org/rss/cs.LG',
        'category': '学术'
    },
    # 国内科技媒体RSS（使用HTTP或更稳定的源）
    {
        'name': '36氪',
        'url': 'http://www.36kr.com/feed',
        'category': '科技媒体'
    },
    {
        'name': '虎嗅网',
        'url': 'http://www.huxiu.com/rss/0.xml',
        'category': '科技媒体'
    },
    {
        'name': '极客公园',
        'url': 'http://www.geekpark.net/rss',
        'category': '科技媒体'
    },
    # 国外科技媒体（使用HTTP避免SSL问题）
    {
        'name': 'IEEE Spectrum',
        'url': 'http://spectrum.ieee.org/rss/blog/automaton/topic/robotics/fulltext',
        'category': '科技媒体'
    },
    {
        'name': 'MIT Technology Review',
        'url': 'http://www.technologyreview.com/topic/artificial-intelligence/rss/',
        'category': '科技媒体'
    }
]


def is_embodied_ai_related(title: str, description: str = '', strict: bool = False) -> bool:
    """
    判断新闻是否与具身智能相关（使用扩展的关键词配置）
    
    Args:
        title: 新闻标题
        description: 新闻描述
        strict: 是否严格模式（True=必须包含关键词，False=宽松模式）
    
    Returns:
        是否相关
    """
    text = (title + ' ' + description).lower()
    
    # 使用扩展的关键词判断函数
    if strict:
        # 严格模式：必须包含核心关键词
        return is_embodied_related(text, strict=True)
    
    # 宽松模式：包含关键词，或者标题/描述足够长（可能是相关新闻）
    # 对于学术论文（ArXiv），放宽限制
    if 'arxiv' in text or 'cs.ro' in text or 'cs.ai' in text or 'cs.lg' in text:
        # ArXiv论文，只要标题包含robot/robotics/ai/ml等关键词就认为相关
        broad_keywords = ['robot', 'robotics', 'ai', 'machine learning', 'ml', 'neural', 'deep learning', 'embodied', '具身']
        for keyword in broad_keywords:
            if keyword.lower() in text:
                return True
    
    # 检查是否包含关键词（使用扩展的关键词列表）
    return is_embodied_related(text, strict=False)


def parse_published_date(date_str: str) -> Optional[datetime]:
    """
    解析RSS日期字符串
    
    Args:
        date_str: RSS日期字符串
    
    Returns:
        datetime对象或None
    """
    if not date_str:
        return None
    
    try:
        # feedparser会自动解析标准格式
        if hasattr(date_str, 'timetuple'):
            return datetime(*date_str.timetuple()[:6])
        # 如果是字符串，尝试解析
        parsed = feedparser._parse_date(date_str)
        if parsed:
            return datetime(*parsed[:6])
    except:
        pass
    
    return None


def fetch_news_from_rss(feed_url: str, feed_name: str = '', max_items: int = 50) -> List[Dict]:
    """
    从RSS源获取新闻
    
    Args:
        feed_url: RSS源URL
        feed_name: RSS源名称
        max_items: 最多获取数量
    
    Returns:
        新闻列表
    """
    news_list = []
    
    try:
        logger.info(f"正在从 {feed_name or feed_url} 获取RSS...")
        
        # 尝试使用不同的方法解析RSS，处理SSL问题
        feed = None
        
        # 方法1: 直接使用feedparser（默认）
        try:
            feed = feedparser.parse(feed_url)
        except Exception as e1:
            logger.warning(f"方法1失败: {e1}")
            
            # 方法2: 使用requests库，禁用SSL验证（仅用于测试）
            try:
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                response = requests.get(feed_url, verify=False, timeout=30, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                if response.status_code == 200:
                    feed = feedparser.parse(response.content)
            except Exception as e2:
                logger.warning(f"方法2失败: {e2}")
                
                # 方法3: 使用urllib，创建不验证SSL的context
                try:
                    import ssl
                    import urllib.request
                    ssl_context = ssl.create_default_context()
                    ssl_context.check_hostname = False
                    ssl_context.verify_mode = ssl.CERT_NONE
                    
                    req = urllib.request.Request(feed_url, headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    })
                    with urllib.request.urlopen(req, context=ssl_context, timeout=30) as response:
                        content = response.read()
                        feed = feedparser.parse(content)
                except Exception as e3:
                    logger.error(f"所有方法都失败: {e3}")
                    return []
        
        if feed is None:
            logger.warning(f"无法获取RSS源 {feed_name or feed_url}")
            return []
        
        if feed.bozo and feed.bozo_exception:
            logger.warning(f"RSS解析警告: {feed.bozo_exception}")
        
        if not feed.entries:
            logger.warning(f"RSS源 {feed_name or feed_url} 没有条目")
            return []
        
        # 增加处理数量，确保获取足够新闻
        entries_to_process = feed.entries[:max_items * 2]  # 处理更多条目，因为会过滤
        
        for entry in entries_to_process:
            title = entry.get('title', '')
            description = entry.get('description', '') or entry.get('summary', '')
            link = entry.get('link', '')
            
            # 对于机器之心等科技媒体，使用更严格的过滤（避免误匹配）
            # 对于学术源（ArXiv），使用更严格的过滤
            is_academic = 'arxiv' in feed_url.lower() or 'cs.' in feed_url.lower()
            
            # 判断是否保留（统一使用优化后的过滤逻辑）
            should_keep = False
            if is_academic:
                # 学术源：使用关键词过滤（宽松模式，因为ArXiv论文标题通常更明确）
                should_keep = is_embodied_ai_related(title, description, strict=False)
            else:
                # 科技媒体：使用更严格的过滤（避免误匹配通用AI新闻和非机器人新闻）
                # 优先检查标题，如果标题没有核心词，即使描述有也不匹配（特殊情况除外）
                title_lower = title.lower()
                full_text = (title + ' ' + description).lower()
                
                # 检查标题是否包含核心词
                from embodied_news_keywords import CORE_EMBODIED_KEYWORDS, ROBOTICS_KEYWORDS, COMPANY_NAMES
                title_core_keywords = [
                    'robot', 'robotics', 'robotic', 'humanoid', 'manipulator', 'gripper',
                    'embodied', 'embodied ai', 'embodied intelligence',
                    '机器人', '具身', '具身智能', '具身ai', '人形机器人', '机械臂', '抓取'
                ]
                title_has_core = any(kw in title_lower for kw in title_core_keywords)
                title_has_company = any(company.lower() in title_lower for company in COMPANY_NAMES)
                
                # 检查是否是新闻聚合类或商业大会类
                news_aggregation_keywords = [
                    '8点', '8点1氪', '早报', '晚报', '日报', '周报',
                    '热点', '要闻', '资讯', 'news', 'daily', 'weekly',
                ]
                business_event_keywords = [
                    '大会', 'conference', 'forum', '论坛', '会议',
                    '商业', 'business', 'wise', '创新大会',
                ]
                is_aggregation = any(kw in title_lower for kw in news_aggregation_keywords)
                is_business_event = any(kw in title_lower for kw in business_event_keywords)
                
                # 如果是新闻聚合或商业大会，且标题没有核心词，不匹配
                if (is_aggregation or is_business_event) and not title_has_core and not title_has_company:
                    should_keep = False
                else:
                    # 先检查是否有明显的排除词（如：高铁、迪士尼、规划等）
                    from embodied_news_keywords import RSS_EXCLUDE_KEYWORDS
                    has_exclude = any(kw.lower() in full_text for kw in RSS_EXCLUDE_KEYWORDS)
                    
                    if has_exclude:
                        # 如果有排除词，必须明确包含机器人核心词才保留
                        robot_core = ['robot', 'robotics', '机器人', 'embodied', '具身', 'humanoid', '人形']
                        if not any(kw in full_text for kw in robot_core):
                            should_keep = False
                        else:
                            # 即使有机器人核心词，也要通过完整的匹配检查
                            should_keep = is_embodied_related(full_text, strict=False)
                    else:
                        # 使用优化后的关键词匹配（要求必须有机器人/具身核心词）
                        should_keep = is_embodied_related(full_text, strict=False)
            
            if should_keep:
                # 解析发布时间
                published_at = None
                
                # 优先使用published字段（包含时区信息）
                if hasattr(entry, 'published') and entry.published:
                    try:
                        # 手动解析RSS日期字符串（格式：Tue, 09 Dec 2025 12:02:00 +0800）
                        import re
                        from datetime import timedelta
                        
                        date_str = entry.published
                        # 尝试解析时区偏移量（+0800 或 -0500）
                        timezone_match = re.search(r'([+-])(\d{2})(\d{2})$', date_str)
                        if timezone_match:
                            sign = timezone_match.group(1)
                            hours = int(timezone_match.group(2))
                            minutes = int(timezone_match.group(3))
                            offset_hours = hours + minutes / 60.0
                            if sign == '-':
                                offset_hours = -offset_hours
                            
                            # 解析日期部分（去掉时区信息）
                            date_part = re.sub(r'\s*[+-]\d{4}$', '', date_str)
                            # 使用feedparser解析日期
                            parsed_time = entry.published_parsed if hasattr(entry, 'published_parsed') else None
                            
                            # 优先使用parsedate_tz，因为它能正确处理时区
                            try:
                                from email.utils import parsedate_tz
                                parsed = parsedate_tz(date_str)
                                if parsed:
                                    # parsedate_tz返回 (year, month, day, hour, minute, second, weekday, yearday, isdst, tzoffset)
                                    # parsed[:6] 已经是本地时间（考虑了时区）
                                    # tzoffset是秒数偏移（正数表示UTC+，负数表示UTC-）
                                    # 对于 +0800，tzoffset = 28800秒
                                    # 本地时间 = UTC时间 + tzoffset
                                    # 所以：UTC时间 = 本地时间 - tzoffset
                                    # 但parsed[:6]已经是本地时间了，所以直接使用
                                    dt = datetime(*parsed[:6])
                                    # 直接使用本地时间，不需要转换
                                    published_at = dt
                            except:
                                # 如果parsedate_tz失败（如36氪的非标准格式），使用published_parsed + 时区偏移
                                if parsed_time:
                                    # published_parsed是UTC时间，需要加上时区偏移得到本地时间
                                    utc_dt = datetime(*parsed_time[:6])
                                    # 计算本地时间（UTC时间 + 时区偏移）
                                    published_at = utc_dt + timedelta(hours=offset_hours)
                                else:
                                    # 如果也没有published_parsed，尝试手动解析（针对36氪格式：2025-12-09 16:20:34  +0800）
                                    try:
                                        import re
                                        # 匹配格式：YYYY-MM-DD HH:MM:SS +HHMM
                                        match = re.match(r'(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2}):(\d{2})\s+([+-])(\d{2})(\d{2})', date_str)
                                        if match:
                                            year, month, day, hour, minute, second = map(int, match.groups()[:6])
                                            sign, tz_hour, tz_min = match.groups()[6:]
                                            tz_offset = int(tz_hour) + int(tz_min) / 60.0
                                            if sign == '-':
                                                tz_offset = -tz_offset
                                            # 这是本地时间，直接使用
                                            published_at = datetime(year, month, day, hour, minute, second)
                                    except:
                                        pass
                        else:
                            # 没有时区信息，直接使用published_parsed（假设是UTC）
                            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                                # 假设是UTC时间，转换为北京时间（UTC+8）
                                utc_dt = datetime(*entry.published_parsed[:6])
                                published_at = utc_dt + timedelta(hours=8)
                    except Exception as e:
                        logger.debug(f"解析published字段失败: {e}, 尝试使用published_parsed")
                        # 如果解析失败，尝试使用published_parsed（假设是UTC，转换为北京时间）
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            try:
                                from datetime import timedelta
                                utc_dt = datetime(*entry.published_parsed[:6])
                                # 假设是UTC时间，转换为北京时间（UTC+8）
                                published_at = utc_dt + timedelta(hours=8)
                            except:
                                pass
                elif hasattr(entry, 'published_parsed') and entry.published_parsed:
                    try:
                        # published_parsed是UTC时间，转换为北京时间（UTC+8）
                        from datetime import timedelta
                        utc_dt = datetime(*entry.published_parsed[:6])
                        published_at = utc_dt + timedelta(hours=8)
                    except:
                        pass
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    try:
                        # updated_parsed也是UTC时间，转换为北京时间（UTC+8）
                        from datetime import timedelta
                        utc_dt = datetime(*entry.updated_parsed[:6])
                        published_at = utc_dt + timedelta(hours=8)
                    except:
                        pass
                
                # 如果没有发布时间，使用当前时间
                if not published_at:
                    published_at = datetime.now()
                # 注意：即使时间戳看起来旧，也保留原始发布时间
                # 因为前端会显示原始发布时间，而不是抓取时间
                
                # 只保留24小时内的新闻
                from datetime import timedelta
                twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
                if published_at < twenty_four_hours_ago:
                    continue  # 跳过24小时前的新闻
                
                # 提取图片
                image_url = ''
                if hasattr(entry, 'media_content') and entry.media_content:
                    image_url = entry.media_content[0].get('url', '')
                elif hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
                    image_url = entry.media_thumbnail[0].get('url', '')
                elif hasattr(entry, 'image') and entry.image:
                    image_url = entry.image.get('href', '')
                
                # 提取作者
                author = ''
                if hasattr(entry, 'author'):
                    author = entry.author
                elif hasattr(entry, 'authors') and entry.authors:
                    author = entry.authors[0].get('name', '')
                
                # 提取平台名称
                platform = feed_name or ''
                if not platform and hasattr(feed.feed, 'title'):
                    platform = feed.feed.title
                
                news_item = {
                    'title': title,
                    'description': description,
                    'link': link,
                    'source': 'rss',
                    'platform': platform,
                    'published_at': published_at,
                    'image_url': image_url,
                    'author': author,
                    'tags': []
                }
                news_list.append(news_item)
        
        logger.info(f"从 {feed_name or feed_url} 获取到 {len(news_list)} 条相关新闻")
        return news_list
    
    except Exception as e:
        logger.error(f"从 {feed_name or feed_url} 获取RSS失败: {e}")
        return []


def fetch_all_news(max_per_feed: int = 50, max_workers: int = 5) -> List[Dict]:
    """
    从所有RSS源获取具身智能相关新闻（并发优化）
    
    Args:
        max_per_feed: 每个RSS源最多获取的数量
        max_workers: 并发线程数（默认5，避免过多请求）
    
    Returns:
        新闻列表
    """
    all_news = []
    news_lock = threading.Lock()  # 线程锁，保护all_news列表
    
    def fetch_single_feed(feed_config):
        """单个RSS源的抓取函数（用于并发）"""
        feed_url = feed_config.get('url', '')
        feed_name = feed_config.get('name', '')
        
        if not feed_url:
            return []
        
        try:
            news = fetch_news_from_rss(feed_url, feed_name, max_items=max_per_feed)
            return news
        except Exception as e:
            logger.error(f"从 {feed_name} 获取新闻异常: {e}")
            return []
    
    # 使用线程池并发抓取（提高效率）
    logger.info(f"开始并发抓取 {len(RSS_FEEDS)} 个RSS源（并发数: {max_workers}）...")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_feed = {
            executor.submit(fetch_single_feed, feed_config): feed_config
            for feed_config in RSS_FEEDS
        }
        
        # 收集结果
        for future in as_completed(future_to_feed):
            feed_config = future_to_feed[future]
            try:
                news = future.result()
                with news_lock:
                    all_news.extend(news)
            except Exception as e:
                feed_name = feed_config.get('name', 'unknown')
                logger.error(f"从 {feed_name} 获取新闻失败: {e}")
    
    # 去重（基于标题和链接）- 优化：使用字典提高去重效率
    seen = {}
    unique_news = []
    for news in all_news:
        # 使用链接作为主键（更可靠）
        link = news['link'].strip().lower()
        title = news['title'].lower().strip()
        
        # 如果链接已存在，跳过
        if link in seen:
            continue
        
        # 如果标题完全相同，也跳过（可能是同一新闻的不同链接）
        if title in seen.values():
            continue
        
        seen[link] = title
        unique_news.append(news)
    
    logger.info(f"总共获取到 {len(unique_news)} 条具身智能相关新闻（去重后，原始: {len(all_news)}）")
    return unique_news


if __name__ == "__main__":
    # 测试
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("测试RSS新闻客户端")
    print("=" * 60)
    
    news = fetch_all_news(max_per_feed=10)
    
    print(f"\n获取到 {len(news)} 条新闻:\n")
    for i, item in enumerate(news[:10], 1):
        print(f"{i}. [{item['platform']}] {item['title'][:60]}")
        if item['link']:
            print(f"   链接: {item['link'][:60]}...")
        if item['published_at']:
            print(f"   时间: {item['published_at']}")
        print()

