#!/usr/bin/env python3
"""
解析掘金文章中的数据集信息
从 https://juejin.cn/post/7475651131450327040 获取数据集信息
"""
import requests
from bs4 import BeautifulSoup
import re
import json
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

JUEJIN_ARTICLE_URL = "https://juejin.cn/post/7475651131450327040"


def fetch_juejin_article() -> Optional[str]:
    """
    获取掘金文章内容
    
    Returns:
        HTML内容字符串，如果失败返回None
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }
    
    try:
        logger.info(f"正在获取掘金文章: {JUEJIN_ARTICLE_URL}")
        response = requests.get(JUEJIN_ARTICLE_URL, headers=headers, timeout=30)
        
        if response.status_code == 200:
            logger.info(f"成功获取文章，大小: {len(response.text)} 字符")
            return response.text
        else:
            logger.error(f"获取文章失败: HTTP {response.status_code}")
    
    except Exception as e:
        logger.error(f"获取文章异常: {e}")
    
    return None


def parse_datasets_from_html(html_content: str) -> List[Dict]:
    """
    从HTML内容中解析数据集信息
    
    由于掘金是动态加载，这里提供一个基础解析框架
    实际可能需要手动整理或使用更高级的解析方法
    
    Args:
        html_content: HTML内容
    
    Returns:
        数据集信息列表
    """
    datasets = []
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 尝试从JSON-LD中获取基本信息
        scripts = soup.find_all('script', type='application/ld+json')
        article_info = {}
        for script in scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, list):
                    for item in data:
                        if item.get('@type') == 'BlogPosting':
                            article_info = item
                            break
            except:
                continue
        
        # 如果无法自动解析，返回示例数据结构
        # 实际使用时需要手动整理文章内容
        logger.warning("无法自动解析数据集信息，返回示例数据")
        logger.info("建议：手动整理文章中的数据集信息，然后使用 save_datasets_manually 函数")
        
    except Exception as e:
        logger.error(f"解析HTML失败: {e}")
    
    return datasets


def save_datasets_manually() -> List[Dict]:
    """
    手动整理的数据集信息
    基于文章内容手动整理的数据集列表
    
    Returns:
        数据集信息列表
    """
    # 这里需要根据实际文章内容手动整理
    # 示例数据结构
    datasets = [
        {
            'name': '示例数据集1',
            'description': '数据集描述',
            'category': '视觉',
            'link': 'https://example.com/dataset1',
            'paper_link': '',
            'source': 'juejin',
            'source_url': JUEJIN_ARTICLE_URL,
            'tags': ['视觉', '机器人']
        },
        # 添加更多数据集...
    ]
    
    return datasets


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("解析掘金文章数据集信息")
    print("=" * 60)
    
    html = fetch_juejin_article()
    if html:
        datasets = parse_datasets_from_html(html)
        print(f"\n解析到 {len(datasets)} 个数据集")
        
        if len(datasets) == 0:
            print("\n⚠️  无法自动解析，请使用 save_datasets_manually() 手动整理数据")
            print("建议：阅读文章后，手动整理数据集信息并添加到 save_datasets_manually() 函数中")







