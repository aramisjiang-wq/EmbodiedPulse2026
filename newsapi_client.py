#!/usr/bin/env python3
"""
NewsAPI.org客户端
作为RSS的备选方案
"""
import requests
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import os
import urllib3

logger = logging.getLogger(__name__)

# NewsAPI.org配置
NEWSAPI_BASE_URL = "https://newsapi.org/v2"
NEWSAPI_API_KEY = os.getenv('NEWSAPI_API_KEY', '359745328c4a471eb7641e120a4c330f')

# 导入扩展的关键词配置
from embodied_news_keywords import (
    ALL_EMBODIED_KEYWORDS,
    get_search_queries,
    is_embodied_related
)

# 使用扩展的关键词列表
EMBODIED_AI_KEYWORDS = ALL_EMBODIED_KEYWORDS


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


def fetch_news_from_newsapi(max_results: int = 50) -> List[Dict]:
    """
    从NewsAPI.org获取新闻
    
    Args:
        max_results: 最多获取数量
    
    Returns:
        新闻列表
    """
    if not NEWSAPI_API_KEY or NEWSAPI_API_KEY == 'your_api_key_here':
        logger.warning("NewsAPI.org API Key未配置")
        return []
    
    news_list = []
    
    try:
        # 使用扩展的搜索查询列表
        queries = get_search_queries()
        # 组合所有查询（NewsAPI支持OR查询）
        query = ' OR '.join(queries[:5])  # 限制查询长度，避免过长
        
        # 计算日期范围（最近7天）
        to_date = datetime.now()
        from_date = to_date - timedelta(days=7)
        
        url = f"{NEWSAPI_BASE_URL}/everything"
        params = {
            'q': query,
            'language': 'en,zh',
            'sortBy': 'publishedAt',
            'pageSize': min(max_results, 100),  # NewsAPI最多100条
            'from': from_date.strftime('%Y-%m-%d'),
            'to': to_date.strftime('%Y-%m-%d')
        }
        headers = {
            'X-Api-Key': NEWSAPI_API_KEY,
            'User-Agent': 'Embodied-AI-Daily/1.0'
        }
        
        logger.info("正在从NewsAPI.org获取新闻...")
        
        # 尝试禁用SSL验证（仅用于解决SSL问题）
        try:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            response = requests.get(url, params=params, headers=headers, timeout=30, verify=False)
        except Exception as e:
            logger.warning(f"禁用SSL验证后仍失败: {e}")
            # 回退到正常请求
            response = requests.get(url, params=params, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            articles = data.get('articles', [])
            
            for article in articles:
                title = article.get('title', '')
                description = article.get('description', '') or article.get('content', '')
                link = article.get('url', '')
                
                # 只保留与具身智能相关的新闻
                if is_embodied_ai_related(title, description):
                    # 解析发布时间
                    published_at = None
                    if article.get('publishedAt'):
                        try:
                            published_at = datetime.fromisoformat(article['publishedAt'].replace('Z', '+00:00'))
                        except:
                            pass
                    
                    news_item = {
                        'title': title,
                        'description': description,
                        'link': link,
                        'source': 'newsapi',
                        'platform': article.get('source', {}).get('name', 'newsapi'),
                        'published_at': published_at,
                        'image_url': article.get('urlToImage', ''),
                        'author': article.get('author', ''),
                        'tags': []
                    }
                    news_list.append(news_item)
            
            logger.info(f"从NewsAPI.org获取到 {len(news_list)} 条相关新闻")
            return news_list
        elif response.status_code == 401:
            logger.error("NewsAPI.org API Key无效")
            return []
        elif response.status_code == 429:
            logger.warning("NewsAPI.org API达到速率限制")
            return []
        else:
            logger.warning(f"从NewsAPI.org获取新闻失败: HTTP {response.status_code}")
            return []
    
    except requests.exceptions.Timeout:
        logger.warning("NewsAPI.org请求超时")
        return []
    except requests.exceptions.RequestException as e:
        logger.warning(f"NewsAPI.org请求失败: {e}")
        return []
    except Exception as e:
        logger.error(f"从NewsAPI.org解析新闻失败: {e}")
        return []


if __name__ == "__main__":
    # 测试
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("测试NewsAPI.org客户端")
    print("=" * 60)
    
    news = fetch_news_from_newsapi(max_results=10)
    
    print(f"\n获取到 {len(news)} 条新闻:\n")
    for i, item in enumerate(news[:10], 1):
        print(f"{i}. [{item['platform']}] {item['title'][:60]}")
        if item['link']:
            print(f"   链接: {item['link'][:60]}...")
        print()

