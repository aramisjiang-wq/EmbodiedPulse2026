"""
工具函数：智能去重、相似度计算等
"""
import re
from difflib import SequenceMatcher
from datetime import datetime, timedelta
from typing import List, Dict, Optional

def calculate_title_similarity(title1: str, title2: str) -> float:
    """
    计算两个标题的相似度
    
    Args:
        title1: 标题1
        title2: 标题2
    
    Returns:
        相似度分数 (0-1)，1表示完全相同
    """
    # 标准化标题：转小写、移除标点、移除多余空格
    def normalize(title: str) -> str:
        # 转小写
        title = title.lower()
        # 移除标点符号
        title = re.sub(r'[^\w\s]', '', title)
        # 移除多余空格
        title = ' '.join(title.split())
        return title
    
    norm1 = normalize(title1)
    norm2 = normalize(title2)
    
    # 使用 SequenceMatcher 计算相似度
    similarity = SequenceMatcher(None, norm1, norm2).ratio()
    return similarity

def is_duplicate_title(new_title: str, existing_titles: List[str], threshold: float = 0.85) -> bool:
    """
    检查新标题是否与已有标题重复
    
    Args:
        new_title: 新标题
        existing_titles: 已有标题列表
        threshold: 相似度阈值，超过此值认为是重复（默认0.85）
    
    Returns:
        True表示重复，False表示不重复
    """
    for existing_title in existing_titles:
        similarity = calculate_title_similarity(new_title, existing_title)
        if similarity >= threshold:
            return True
    return False

def get_latest_paper_date(category: Optional[str] = None) -> Optional[datetime]:
    """
    获取数据库中指定类别的最新论文日期（用于增量更新）
    
    Args:
        category: 论文类别，None表示所有类别
    
    Returns:
        最新论文的发布日期，如果没有论文则返回None
    """
    try:
        from models import get_session, Paper
        from sqlalchemy import func
        
        session = get_session()
        try:
            query = session.query(func.max(Paper.publish_date))
            if category:
                query = query.filter(Paper.category == category)
            
            result = query.scalar()
            if result:
                # 如果是date对象，转换为datetime
                if isinstance(result, datetime):
                    return result
                else:
                    return datetime.combine(result, datetime.min.time())
            return None
        finally:
            session.close()
    except Exception as e:
        print(f"获取最新论文日期失败: {e}")
        return None

def should_fetch_paper(paper_date: datetime, category: Optional[str] = None, days_back: int = 7) -> bool:
    """
    判断是否应该抓取这篇论文（增量更新逻辑）
    
    修复说明：
    - 原逻辑：如果论文日期 <= 最新日期，就跳过（有问题，因为可能某些类别还没抓取）
    - 新逻辑：只检查时间范围（days_back），不检查日期比较（因为去重机制已经处理了）
    
    Args:
        paper_date: 论文发布日期
        category: 论文类别（保留参数，但不再使用类别日期比较）
        days_back: 只抓取最近N天的论文（默认7天）
    
    Returns:
        True表示应该抓取，False表示跳过
    """
    # 只抓取最近N天的论文
    cutoff_date = datetime.now() - timedelta(days=days_back)
    if paper_date < cutoff_date:
        return False
    
    # 注意：不再检查"论文日期 <= 最新日期"的逻辑
    # 原因：
    # 1. 不同类别的论文可能在不同日期被抓取
    # 2. 某些日期的论文可能在之前的抓取中被跳过
    # 3. 去重机制（ID和标题相似度）已经足够处理重复问题
    # 4. 只依赖日期比较会导致漏抓论文
    
    return True

def extract_keywords_from_title(title: str) -> List[str]:
    """
    从标题中提取关键词（用于智能分类）
    
    Args:
        title: 论文标题
    
    Returns:
        关键词列表
    """
    # 简单的关键词提取（可以根据需要扩展）
    keywords = []
    title_lower = title.lower()
    
    # 定义关键词映射
    keyword_map = {
        'perception': ['perception', 'visual', 'scene', 'understanding'],
        'vlm': ['vision language', 'multimodal', 'visual-language'],
        'planning': ['planning', 'path', 'trajectory', 'motion planning'],
        'rl/il': ['reinforcement learning', 'imitation learning', 'rl', 'policy'],
        'manipulation': ['manipulation', 'grasping', 'grasp'],
        'locomotion': ['locomotion', 'walking', 'navigation', 'mobile'],
        'dexterous': ['dexterous', 'dexterity', 'fine manipulation'],
        'vla': ['vision language action', 'vla', 'embodied agent'],
        'humanoid': ['humanoid', 'bipedal', 'humanoid robot']
    }
    
    for category, keywords_list in keyword_map.items():
        if any(kw in title_lower for kw in keywords_list):
            keywords.append(category)
    
    return keywords

