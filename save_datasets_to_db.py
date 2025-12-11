#!/usr/bin/env python3
"""
保存数据集信息到数据库
"""
from typing import List
from datasets_models import get_datasets_session, Dataset
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)


def save_dataset_to_db(dataset_data: dict) -> tuple:
    """
    保存数据集信息到数据库
    
    Args:
        dataset_data: 数据集信息字典
    
    Returns:
        (是否成功, 状态信息) - 状态: 'created', 'updated', 'skipped', 'error'
    """
    session = get_datasets_session()
    
    try:
        name = dataset_data.get('name', '')
        link = dataset_data.get('link', '')
        
        # 去重策略：基于名称+链接
        if link:
            existing = session.query(Dataset).filter(
                Dataset.link == link
            ).first()
        else:
            existing = session.query(Dataset).filter(
                Dataset.name == name
            ).first()
        
        if existing:
            # 更新现有记录
            existing.name = dataset_data.get('name', existing.name)
            existing.description = dataset_data.get('description', existing.description)
            existing.category = dataset_data.get('category', existing.category)
            existing.publisher = dataset_data.get('publisher', existing.publisher)
            existing.publish_date = dataset_data.get('publish_date', existing.publish_date)
            existing.project_link = dataset_data.get('project_link', existing.project_link)
            existing.paper_link = dataset_data.get('paper_link', existing.paper_link)
            existing.dataset_link = dataset_data.get('dataset_link', existing.dataset_link)
            existing.scale = dataset_data.get('scale', existing.scale)
            existing.link = dataset_data.get('link', existing.link)
            existing.source = dataset_data.get('source', existing.source)
            existing.source_url = dataset_data.get('source_url', existing.source_url)
            tags = dataset_data.get('tags', [])
            existing.tags = json.dumps(tags, ensure_ascii=False) if isinstance(tags, list) else tags
            existing.updated_at = datetime.now()
            session.commit()
            return True, 'updated'
        
        # 创建新记录
        tags = dataset_data.get('tags', [])
        dataset = Dataset(
            name=dataset_data.get('name', ''),
            description=dataset_data.get('description'),
            category=dataset_data.get('category'),
            publisher=dataset_data.get('publisher'),
            publish_date=dataset_data.get('publish_date'),
            project_link=dataset_data.get('project_link'),
            paper_link=dataset_data.get('paper_link'),
            dataset_link=dataset_data.get('dataset_link'),
            scale=dataset_data.get('scale'),
            link=dataset_data.get('link'),
            source=dataset_data.get('source', 'juejin'),
            source_url=dataset_data.get('source_url'),
            tags=json.dumps(tags, ensure_ascii=False) if isinstance(tags, list) else None
        )
        
        session.add(dataset)
        session.commit()
        return True, 'created'
    
    except Exception as e:
        session.rollback()
        logger.error(f"保存数据集信息失败: {e}")
        return False, 'error'
    
    finally:
        session.close()


def batch_save_datasets(datasets_list: List[dict]) -> dict:
    """
    批量保存数据集信息
    
    Args:
        datasets_list: 数据集信息列表
    
    Returns:
        统计信息
    """
    stats = {
        'total': len(datasets_list),
        'created': 0,
        'updated': 0,
        'skipped': 0,
        'error': 0
    }
    
    for dataset_data in datasets_list:
        success, status = save_dataset_to_db(dataset_data)
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
    logging.basicConfig(level=logging.INFO)
    
    test_dataset = {
        'name': '测试数据集',
        'description': '测试描述',
        'category': '视觉',
        'link': 'https://example.com/dataset',
        'source': 'juejin',
        'source_url': 'https://juejin.cn/post/7475651131450327040',
        'tags': ['视觉', '机器人']
    }
    
    success, status = save_dataset_to_db(test_dataset)
    print(f"保存结果: {success}, 状态: {status}")

