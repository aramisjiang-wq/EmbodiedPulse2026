#!/usr/bin/env python3
"""
保存招聘信息到数据库
使用独立的招聘信息数据库
"""
from typing import List
from jobs_models import get_jobs_session, Job
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def save_job_to_db(job_data: dict) -> tuple:
    """
    保存招聘信息到数据库
    
    Args:
        job_data: 招聘信息字典
    
    Returns:
        (是否成功, 状态信息) - 状态: 'created', 'updated', 'skipped', 'error'
    """
    session = get_jobs_session()
    
    try:
        link = job_data.get('link')
        source_date = job_data.get('source_date')
        title = job_data.get('title', '')
        
        # 去重策略：基于链接+日期，如果没有链接则使用标题+日期
        if link:
            existing = session.query(Job).filter(
                Job.link == link,
                Job.source_date == source_date
            ).first()
        else:
            existing = session.query(Job).filter(
                Job.title == title,
                Job.source_date == source_date
            ).first()
        
        if existing:
            # 更新现有记录
            existing.title = job_data.get('title', existing.title)
            existing.description = job_data.get('description', existing.description)
            existing.link = job_data.get('link', existing.link)
            existing.update_date = job_data.get('update_date', existing.update_date)
            existing.company = job_data.get('company', existing.company)
            existing.location = job_data.get('location', existing.location)
            existing.job_type = job_data.get('job_type', existing.job_type)
            existing.updated_at = datetime.now()
            session.commit()
            return True, 'updated'
        
        # 创建新记录
        job = Job(
            title=job_data.get('title', ''),
            description=job_data.get('description'),
            link=job_data.get('link'),
            update_date=job_data.get('update_date'),
            source_date=job_data.get('source_date'),
            company=job_data.get('company'),
            location=job_data.get('location'),
            job_type=job_data.get('job_type')
        )
        
        session.add(job)
        session.commit()
        return True, 'created'
    
    except Exception as e:
        session.rollback()
        logger.error(f"保存招聘信息失败: {e}")
        return False, 'error'
    
    finally:
        session.close()


def batch_save_jobs(jobs_list: List[dict]) -> dict:
    """
    批量保存招聘信息
    
    Args:
        jobs_list: 招聘信息列表
    
    Returns:
        统计信息: {'total': 总数, 'created': 新建, 'updated': 更新, 'skipped': 跳过, 'error': 错误}
    """
    stats = {
        'total': len(jobs_list),
        'created': 0,
        'updated': 0,
        'skipped': 0,
        'error': 0
    }
    
    for job_data in jobs_list:
        success, status = save_job_to_db(job_data)
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
    
    test_job = {
        'title': '测试公司 - 测试职位 - 全职',
        'description': '测试描述',
        'link': 'https://example.com/job',
        'update_date': '2025.12.9',
        'source_date': '2025.12.9',
        'company': '测试公司',
        'location': '上海',
        'job_type': '全职'
    }
    
    success, status = save_job_to_db(test_job)
    print(f"保存结果: {success}, 状态: {status}")

