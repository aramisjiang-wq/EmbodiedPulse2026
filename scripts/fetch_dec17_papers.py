#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全地抓取2025年12月17日发布的论文
包含完整的错误处理、日志记录和进度显示
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from daily_arxiv import load_config, demo, get_daily_papers
from models import get_session, Paper
from save_paper_to_db import save_paper_to_db
from taxonomy import normalize_category

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s %(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 目标日期
TARGET_DATE = datetime(2025, 12, 17).date()


def fetch_papers_for_date(target_date, max_results_per_category=100):
    """
    安全地抓取指定日期的论文
    
    Args:
        target_date: 目标日期（date对象）
        max_results_per_category: 每个类别最多抓取的论文数
    
    Returns:
        dict: 抓取结果统计
    """
    logger.info("=" * 60)
    logger.info(f"开始抓取 {target_date} 发布的论文")
    logger.info("=" * 60)
    
    # 加载配置
    try:
        config = load_config('config.yaml')
        keywords = config.get('kv', {})
        logger.info(f"加载了 {len(keywords)} 个论文类别")
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}")
        return {'success': False, 'error': str(e)}
    
    # 统计信息
    stats = {
        'total_categories': len(keywords),
        'processed_categories': 0,
        'success_categories': 0,
        'failed_categories': 0,
        'total_papers': 0,
        'new_papers': 0,
        'updated_papers': 0,
        'errors': []
    }
    
    session = get_session()
    
    try:
        # 遍历每个类别
        for category, query in keywords.items():
            stats['processed_categories'] += 1
            category_display = normalize_category(category)
            
            logger.info(f"\n[{stats['processed_categories']}/{stats['total_categories']}] "
                       f"处理类别: {category_display}")
            
            try:
                # 抓取论文（使用 submittedDate 而不是 publishedDate）
                # 扩大日期范围，确保不遗漏（前后各1天）
                start_date = target_date - timedelta(days=1)
                end_date = target_date + timedelta(days=1)
                
                papers = get_daily_papers(
                    topic=category,
                    query=query,
                    max_results=max_results_per_category,
                    days_back=3  # 扩大范围到3天
                )
                
                if not papers:
                    logger.warning(f"  未找到论文")
                    continue
                
                # 过滤出目标日期的论文
                target_papers = []
                for date_str, paper_list in papers.items():
                    try:
                        paper_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                        if paper_date == target_date:
                            target_papers.extend(paper_list)
                    except (ValueError, TypeError):
                        # 如果日期格式不对，检查论文的 submitted 日期
                        for paper in paper_list:
                            if hasattr(paper, 'submitted') and paper.submitted:
                                paper_date = paper.submitted.date()
                                if paper_date == target_date:
                                    target_papers.append(paper)
                
                if not target_papers:
                    logger.info(f"  未找到 {target_date} 的论文（找到 {sum(len(p) for p in papers.values())} 篇其他日期的论文）")
                    continue
                
                logger.info(f"  找到 {len(target_papers)} 篇 {target_date} 的论文")
                
                # 保存论文到数据库
                new_count = 0
                updated_count = 0
                
                for paper in target_papers:
                    try:
                        # 检查是否已存在
                        arxiv_id = paper.get('id', '').replace('http://arxiv.org/abs/', '').replace('https://arxiv.org/abs/', '')
                        if not arxiv_id:
                            continue
                        
                        existing = session.query(Paper).filter_by(arxiv_id=arxiv_id).first()
                        
                        if existing:
                            # 更新现有论文
                            result = save_paper_to_db(paper, category, session=session, update_existing=True)
                            if result:
                                updated_count += 1
                        else:
                            # 创建新论文
                            result = save_paper_to_db(paper, category, session=session)
                            if result:
                                new_count += 1
                        
                        stats['total_papers'] += 1
                        
                    except Exception as e:
                        logger.error(f"  保存论文失败 ({paper.get('id', 'unknown')}): {e}")
                        stats['errors'].append(f"{category}: {str(e)}")
                        continue
                
                # 提交事务
                try:
                    session.commit()
                    logger.info(f"  ✅ 成功: 新增 {new_count} 篇，更新 {updated_count} 篇")
                    stats['success_categories'] += 1
                    stats['new_papers'] += new_count
                    stats['updated_papers'] += updated_count
                except Exception as e:
                    session.rollback()
                    logger.error(f"  ❌ 提交失败: {e}")
                    stats['failed_categories'] += 1
                    stats['errors'].append(f"{category}: 提交失败 - {str(e)}")
                
            except Exception as e:
                logger.error(f"  ❌ 处理类别 {category} 失败: {e}")
                import traceback
                traceback.print_exc()
                stats['failed_categories'] += 1
                stats['errors'].append(f"{category}: {str(e)}")
                session.rollback()
                continue
        
        # 最终统计
        logger.info("\n" + "=" * 60)
        logger.info("抓取完成统计:")
        logger.info(f"  总类别数: {stats['total_categories']}")
        logger.info(f"  成功类别: {stats['success_categories']}")
        logger.info(f"  失败类别: {stats['failed_categories']}")
        logger.info(f"  总论文数: {stats['total_papers']}")
        logger.info(f"  新增论文: {stats['new_papers']}")
        logger.info(f"  更新论文: {stats['updated_papers']}")
        if stats['errors']:
            logger.warning(f"  错误数: {len(stats['errors'])}")
            for error in stats['errors'][:5]:  # 只显示前5个错误
                logger.warning(f"    - {error}")
        logger.info("=" * 60)
        
        stats['success'] = stats['failed_categories'] == 0
        return stats
        
    except Exception as e:
        logger.error(f"抓取过程发生严重错误: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
        return {'success': False, 'error': str(e)}
    
    finally:
        session.close()


def main():
    """主函数"""
    try:
        # 加载环境变量
        env_path = os.path.join(project_root, '.env')
        if os.path.exists(env_path):
            load_dotenv(env_path)
        
        # 执行抓取
        result = fetch_papers_for_date(TARGET_DATE)
        
        if result.get('success', False):
            logger.info("✅ 论文抓取任务完成")
            sys.exit(0)
        else:
            logger.error("❌ 论文抓取任务失败")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.warning("\n用户中断操作")
        sys.exit(130)
    except Exception as e:
        logger.error(f"程序异常退出: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

