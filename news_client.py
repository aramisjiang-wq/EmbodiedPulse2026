#!/usr/bin/env python3
"""
新闻API客户端
使用Orz.ai API获取具身智能相关新闻
"""
import requests
import logging
from typing import List, Dict, Optional
from datetime import datetime
import re
import urllib3

logger = logging.getLogger(__name__)

# Orz.ai API配置
ORZ_API_BASE = "https://orz.ai/api/v1/dailynews"

# 导入扩展的关键词配置
from embodied_news_keywords import (
    ALL_EMBODIED_KEYWORDS,
    is_embodied_related
)

# 使用扩展的关键词列表
EMBODIED_AI_KEYWORDS = ALL_EMBODIED_KEYWORDS

# 优先使用的平台（技术相关）
PREFERRED_PLATFORMS = [
    'github',      # 开源项目、编程语言
    'hackernews',  # 科技新闻、创业、编程
    'tskr',        # 36氪，科技创业、商业资讯
    'juejin',      # 掘金，编程、技术文章
    'stackoverflow', # 编程问答、技术讨论
    'vtex'         # V2EX，技术、编程、创意
]


def is_embodied_ai_related(title: str, description: str = '') -> bool:
    """
    判断新闻是否与具身智能相关（使用扩展的关键词配置）
    
    Args:
        title: 新闻标题
        description: 新闻描述
    
    Returns:
        是否相关
    """
    text = (title + ' ' + description).lower()
    # 使用扩展的关键词判断函数
    return is_embodied_related(text, strict=False)


def fetch_news_from_platform(platform: str, limit: int = 50) -> List[Dict]:
    """
    从指定平台获取新闻
    
    Args:
        platform: 平台名称
        limit: 获取数量限制
    
    Returns:
        新闻列表
    """
    url = f"{ORZ_API_BASE}/?platform={platform}"
    
    try:
        headers = {
            'User-Agent': 'Embodied-AI-Daily/1.0',
            'Accept': 'application/json'
        }
        
        logger.info(f"正在从 {platform} 获取新闻...")
        
        # 尝试禁用SSL验证（仅用于解决SSL问题）
        try:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            response = requests.get(url, headers=headers, timeout=30, verify=False)
        except Exception as e:
            logger.warning(f"禁用SSL验证后仍失败: {e}")
            # 回退到正常请求
            response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # 解析返回数据
            news_list = []
            items = data.get('data', []) or data.get('items', []) or []
            
            for item in items[:limit]:
                title = item.get('title', '') or item.get('name', '')
                description = item.get('description', '') or item.get('summary', '') or ''
                link = item.get('link', '') or item.get('url', '') or item.get('href', '')
                
                # 只保留与具身智能相关的新闻
                if is_embodied_ai_related(title, description):
                    news_item = {
                        'title': title,
                        'description': description,
                        'link': link,
                        'source': platform,
                        'platform': platform,
                        'published_at': item.get('published_at') or item.get('time') or item.get('date'),
                        'image_url': item.get('image') or item.get('image_url') or '',
                        'author': item.get('author', ''),
                        'tags': []
                    }
                    news_list.append(news_item)
            
            logger.info(f"从 {platform} 获取到 {len(news_list)} 条相关新闻")
            return news_list
        else:
            logger.warning(f"从 {platform} 获取新闻失败: HTTP {response.status_code}")
            return []
    
    except requests.exceptions.Timeout:
        logger.warning(f"从 {platform} 获取新闻超时")
        return []
    except requests.exceptions.RequestException as e:
        logger.warning(f"从 {platform} 获取新闻失败: {e}")
        return []
    except Exception as e:
        logger.error(f"从 {platform} 解析新闻失败: {e}")
        return []


def fetch_all_news(max_per_platform: int = 20) -> List[Dict]:
    """
    从所有平台获取具身智能相关新闻
    
    Args:
        max_per_platform: 每个平台最多获取的数量
    
    Returns:
        新闻列表
    """
    all_news = []
    
    # 优先从技术相关平台获取
    for platform in PREFERRED_PLATFORMS:
        try:
            news = fetch_news_from_platform(platform, limit=max_per_platform)
            all_news.extend(news)
        except Exception as e:
            logger.error(f"从 {platform} 获取新闻异常: {e}")
            continue
    
    logger.info(f"总共获取到 {len(all_news)} 条具身智能相关新闻")
    return all_news


if __name__ == "__main__":
    # 测试
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("测试新闻API客户端")
    print("=" * 60)
    
    news = fetch_all_news(max_per_platform=10)
    
    print(f"\n获取到 {len(news)} 条新闻:\n")
    for i, item in enumerate(news[:10], 1):
        print(f"{i}. [{item['platform']}] {item['title'][:60]}")
        if item['link']:
            print(f"   链接: {item['link'][:60]}...")
        print()

