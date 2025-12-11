#!/usr/bin/env python3
"""
抓取招聘信息
从GitHub仓库获取并保存到数据库
"""
import logging
import argparse
from github_jobs_client import fetch_all_jobs
from save_jobs_to_db import batch_save_jobs
from jobs_models import init_jobs_db

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s %(levelname)s] %(message)s',
    datefmt='%m/%d/%Y %H:%M:%S'
)
logger = logging.getLogger(__name__)


def fetch_and_save_jobs():
    """
    抓取并保存招聘信息
    """
    logger.info("=" * 60)
    logger.info("开始抓取招聘信息")
    logger.info("=" * 60)
    
    # 确保数据库已初始化
    try:
        init_jobs_db()
    except Exception as e:
        logger.warning(f"数据库初始化警告: {e}")
    
    # 获取招聘信息
    jobs = fetch_all_jobs()
    
    if not jobs:
        logger.warning("未获取到任何招聘信息")
        return
    
    logger.info(f"获取到 {len(jobs)} 条招聘信息，开始保存...")
    
    # 批量保存
    stats = batch_save_jobs(jobs)
    
    logger.info("=" * 60)
    logger.info("招聘信息抓取完成")
    logger.info("=" * 60)
    logger.info(f"总计: {stats['total']} 条")
    logger.info(f"新建: {stats['created']} 条")
    logger.info(f"更新: {stats['updated']} 条")
    logger.info(f"跳过: {stats['skipped']} 条")
    logger.info(f"错误: {stats['error']} 条")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="抓取招聘信息")
    parser.add_argument("--yes", action="store_true", help="自动确认，不询问")
    
    args = parser.parse_args()
    
    if not args.yes:
        print("将从GitHub获取招聘信息并保存到数据库")
        confirm = input("确认继续？(y/n): ")
        if confirm.lower() != 'y':
            print("已取消")
            exit(0)
    
    fetch_and_save_jobs()


