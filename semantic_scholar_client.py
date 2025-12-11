#!/usr/bin/env python3
"""
Semantic Scholar API 客户端
用于获取论文的被引用数量、机构信息、发表信息等补充数据
"""
import requests
import time
import logging
from typing import Optional, Dict, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API配置
BASE_URL = "https://api.semanticscholar.org/graph/v1"
RATE_LIMIT_DELAY = 0.1  # 100ms延迟，避免超过速率限制（100 requests/5min）
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # 重试延迟（秒）


def get_paper_metadata(arxiv_id: str, retry_count: int = 0) -> Optional[Dict]:
    """
    通过ArXiv ID获取Semantic Scholar论文元数据
    
    Args:
        arxiv_id: ArXiv论文ID（不含版本号，如：2504.13120）
        retry_count: 当前重试次数
    
    Returns:
        包含论文元数据的字典，如果失败则返回None
    """
    # 移除版本号（如果有）
    if 'v' in arxiv_id:
        arxiv_id = arxiv_id.split('v')[0]
    
    url = f"{BASE_URL}/paper/arXiv:{arxiv_id}"
    params = {
        'fields': 'title,authors,citationCount,influentialCitationCount,venue,year,abstract,publicationDate'
    }
    
    try:
        # 添加延迟以避免速率限制
        if retry_count == 0:
            time.sleep(RATE_LIMIT_DELAY)
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            logger.debug(f"成功获取论文 {arxiv_id} 的Semantic Scholar数据")
            return data
        elif response.status_code == 404:
            logger.debug(f"论文 {arxiv_id} 在Semantic Scholar中不存在")
            return None
        elif response.status_code == 429:
            # 速率限制，等待后重试
            if retry_count < MAX_RETRIES:
                wait_time = RETRY_DELAY * (retry_count + 1)
                logger.warning(f"速率限制，等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
                return get_paper_metadata(arxiv_id, retry_count + 1)
            else:
                logger.error(f"论文 {arxiv_id} 达到最大重试次数，跳过")
                return None
        else:
            logger.warning(f"获取论文 {arxiv_id} 失败，状态码: {response.status_code}")
            return None
            
    except requests.exceptions.Timeout:
        logger.warning(f"获取论文 {arxiv_id} 超时")
        if retry_count < MAX_RETRIES:
            time.sleep(RETRY_DELAY)
            return get_paper_metadata(arxiv_id, retry_count + 1)
        return None
    except Exception as e:
        logger.error(f"获取论文 {arxiv_id} 的Semantic Scholar数据失败: {e}")
        return None


def extract_author_affiliations(authors: List[Dict]) -> List[str]:
    """
    从作者列表中提取机构信息
    
    Args:
        authors: Semantic Scholar返回的作者列表
    
    Returns:
        机构名称列表（去重）
    """
    affiliations = set()
    
    for author in authors:
        if 'affiliations' in author and author['affiliations']:
            for aff in author['affiliations']:
                if aff:
                    affiliations.add(aff)
    
    return sorted(list(affiliations))


def parse_semantic_scholar_data(data: Dict, arxiv_id: str) -> Dict:
    """
    解析Semantic Scholar返回的数据，提取所需字段
    
    Args:
        data: Semantic Scholar API返回的数据
        arxiv_id: ArXiv论文ID
    
    Returns:
        包含解析后数据的字典
    """
    result = {
        'citation_count': data.get('citationCount', 0) or 0,
        'influential_citation_count': data.get('influentialCitationCount', 0) or 0,
        'venue': data.get('venue', '') or '',
        'publication_year': data.get('year', None),
        'author_affiliations': []
    }
    
    # 提取作者机构信息
    if 'authors' in data and data['authors']:
        affiliations = extract_author_affiliations(data['authors'])
        result['author_affiliations'] = affiliations
    
    return result


def get_paper_supplement_data(arxiv_id: str) -> Optional[Dict]:
    """
    获取论文的补充数据（被引用数量、机构信息等）
    
    Args:
        arxiv_id: ArXiv论文ID
    
    Returns:
        包含补充数据的字典，如果失败则返回None
    """
    metadata = get_paper_metadata(arxiv_id)
    
    if not metadata:
        return None
    
    return parse_semantic_scholar_data(metadata, arxiv_id)


if __name__ == '__main__':
    # 测试
    test_id = '2504.13120'
    print(f"测试获取论文 {test_id} 的Semantic Scholar数据...")
    result = get_paper_supplement_data(test_id)
    
    if result:
        print("✅ 成功获取数据:")
        print(f"  被引用数: {result['citation_count']}")
        print(f"  高影响力引用: {result['influential_citation_count']}")
        print(f"  发表场所: {result['venue']}")
        print(f"  发表年份: {result['publication_year']}")
        print(f"  机构: {', '.join(result['author_affiliations'][:3])}...")
    else:
        print("❌ 获取数据失败")


