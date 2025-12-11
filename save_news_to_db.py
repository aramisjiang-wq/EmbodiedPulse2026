#!/usr/bin/env python3
"""
保存新闻信息到数据库
"""
import logging
from typing import List, Dict, Optional
from datetime import datetime
import json
from news_models import get_news_session, News

logger = logging.getLogger(__name__)


def save_news_to_db(news_data: Dict) -> tuple[bool, str]:
    """
    保存单条新闻到数据库
    
    Args:
        news_data: 新闻数据字典
    
    Returns:
        (是否成功, 状态: 'created'/'updated'/'skipped'/'error')
    """
    session = get_news_session()
    
    try:
        # 检查是否已存在（基于标题和链接）
        existing = session.query(News).filter(
            News.title == news_data.get('title', ''),
            News.link == news_data.get('link', '')
        ).first()
        
        if existing:
            # 更新现有记录
            existing.description = news_data.get('description', existing.description)
            existing.source = news_data.get('source', existing.source)
            existing.platform = news_data.get('platform', existing.platform)
            existing.image_url = news_data.get('image_url', existing.image_url)
            existing.author = news_data.get('author', existing.author)
            tags = news_data.get('tags', [])
            existing.tags = json.dumps(tags, ensure_ascii=False) if isinstance(tags, list) else tags
            existing.updated_at = datetime.now()
            session.commit()
            return True, 'updated'
        
        # 解析发布时间
        published_at = None
        if news_data.get('published_at'):
            try:
                # 尝试解析各种时间格式
                pub_time = news_data['published_at']
                if isinstance(pub_time, str):
                    # 尝试解析ISO格式（YYYY-MM-DD HH:MM:SS 或 YYYY-MM-DDTHH:MM:SS）
                    try:
                        # 标准格式：YYYY-MM-DD HH:MM:SS
                        if ' ' in pub_time and len(pub_time) == 19:
                            published_at = datetime.strptime(pub_time, '%Y-%m-%d %H:%M:%S')
                        # ISO格式：YYYY-MM-DDTHH:MM:SS
                        elif 'T' in pub_time:
                            published_at = datetime.fromisoformat(pub_time.replace('Z', '+00:00'))
                        else:
                            published_at = datetime.fromisoformat(pub_time)
                    except:
                        # 如果解析失败，尝试其他格式
                        try:
                            published_at = datetime.strptime(pub_time, '%Y-%m-%d %H:%M:%S')
                        except:
                            pass
                elif isinstance(pub_time, datetime):
                    # 直接使用datetime对象
                    published_at = pub_time
            except Exception as e:
                logger.warning(f"解析发布时间失败: {e}, 时间数据: {news_data.get('published_at')}")
                pass
        
        # 创建新记录
        tags = news_data.get('tags', [])
        news = News(
            title=news_data.get('title', ''),
            description=news_data.get('description'),
            link=news_data.get('link'),
            source=news_data.get('source', 'orz'),
            platform=news_data.get('platform', ''),
            published_at=published_at,
            image_url=news_data.get('image_url'),
            author=news_data.get('author'),
            tags=json.dumps(tags, ensure_ascii=False) if isinstance(tags, list) else None
        )
        
        session.add(news)
        session.commit()
        return True, 'created'
    
    except Exception as e:
        session.rollback()
        logger.error(f"保存新闻失败: {e}")
        return False, 'error'
    
    finally:
        session.close()


def batch_save_news(news_list: List[Dict]) -> Dict[str, int]:
    """
    批量保存新闻到数据库
    
    Args:
        news_list: 新闻数据列表
    
    Returns:
        统计信息字典
    """
    stats = {
        'total': len(news_list),
        'created': 0,
        'updated': 0,
        'skipped': 0,
        'error': 0
    }
    
    for news_data in news_list:
        success, status = save_news_to_db(news_data)
        
        if success:
            if status == 'created':
                stats['created'] += 1
            elif status == 'updated':
                stats['updated'] += 1
            elif status == 'skipped':
                stats['skipped'] += 1
        else:
            stats['error'] += 1
    
    return stats


if __name__ == "__main__":
    # 测试
    logging.basicConfig(level=logging.INFO)
    
    test_news = {
        'title': '测试新闻标题',
        'description': '测试新闻描述',
        'link': 'https://example.com/news/1',
        'source': 'test',
        'platform': 'test',
        'tags': ['测试', '新闻']
    }
    
    success, status = save_news_to_db(test_news)
    print(f"保存结果: {status}")

