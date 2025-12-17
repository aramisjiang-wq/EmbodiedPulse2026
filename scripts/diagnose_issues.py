#!/usr/bin/env python3
"""
诊断脚本：检查论文和B站数据问题
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, date, timedelta
from models import get_session, Paper
from bilibili_models import get_bilibili_session, BilibiliUp, BilibiliVideo
from sqlalchemy import func
import logging

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s %(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def check_papers_data():
    """检查论文数据"""
    logger.info("=" * 60)
    logger.info("检查论文数据...")
    logger.info("=" * 60)
    
    session = get_session()
    try:
        # 1. 总论文数
        total = session.query(Paper).count()
        logger.info(f"总论文数: {total}")
        
        if total == 0:
            logger.error("❌ 数据库中没有论文数据！")
            logger.info("解决方案: 运行 python3 fetch_new_data.py --papers")
            return False
        
        # 2. 最新论文日期
        latest = session.query(Paper).order_by(Paper.publish_date.desc()).first()
        if latest and latest.publish_date:
            days_ago = (date.today() - latest.publish_date).days
            logger.info(f"最新论文日期: {latest.publish_date} ({days_ago}天前)")
            
            if days_ago > 2:
                logger.warning(f"⚠️  最新论文是{days_ago}天前的，可能没有及时更新")
        else:
            logger.warning("⚠️  无法获取最新论文日期")
        
        # 3. 今天新增的论文
        today = date.today()
        today_start = datetime.combine(today, datetime.min.time())
        today_count = session.query(Paper).filter(
            Paper.created_at >= today_start
        ).count()
        logger.info(f"今天新增论文: {today_count}篇")
        
        # 4. 昨天新增的论文
        yesterday = today - timedelta(days=1)
        yesterday_start = datetime.combine(yesterday, datetime.min.time())
        yesterday_count = session.query(Paper).filter(
            Paper.created_at >= yesterday_start,
            Paper.created_at < today_start
        ).count()
        logger.info(f"昨天新增论文: {yesterday_count}篇")
        
        # 5. 检查12月16日的论文
        target_date = date(2024, 12, 16)
        target_papers = session.query(Paper).filter(
            Paper.publish_date == target_date
        ).count()
        logger.info(f"12月16日的论文: {target_papers}篇")
        
        if target_papers == 0:
            logger.warning("⚠️  12月16日没有论文数据")
            # 检查是否有接近日期的论文
            nearby_papers = session.query(Paper).filter(
                Paper.publish_date >= target_date - timedelta(days=3),
                Paper.publish_date <= target_date + timedelta(days=3)
            ).count()
            logger.info(f"12月13-19日的论文总数: {nearby_papers}篇")
        
        # 6. 检查API返回的数据格式
        papers = session.query(Paper).order_by(Paper.publish_date.desc()).limit(10).all()
        logger.info(f"示例论文（前10篇）:")
        for paper in papers:
            logger.info(f"  - {paper.id}: {paper.title[:50]}... (日期: {paper.publish_date})")
        
        return True
        
    except Exception as e:
        logger.error(f"检查论文数据失败: {e}", exc_info=True)
        return False
    finally:
        session.close()


def check_bilibili_data():
    """检查B站数据"""
    logger.info("=" * 60)
    logger.info("检查B站数据...")
    logger.info("=" * 60)
    
    session = get_bilibili_session()
    try:
        # 1. 检查UP主数量
        total_ups = session.query(BilibiliUp).filter_by(is_active=True).count()
        logger.info(f"活跃UP主数: {total_ups}")
        
        if total_ups == 0:
            logger.error("❌ 数据库中没有活跃的UP主数据！")
            logger.info("解决方案: 运行 python3 fetch_bilibili_data.py")
            return False
        
        # 2. 检查每个UP主的数据
        ups = session.query(BilibiliUp).filter_by(is_active=True).all()
        logger.info(f"UP主列表:")
        for up in ups:
            video_count = session.query(BilibiliVideo).filter_by(
                uid=up.uid,
                is_deleted=False
            ).count()
            
            last_update = up.last_fetch_at.strftime('%Y-%m-%d %H:%M:%S') if up.last_fetch_at else '从未更新'
            error_info = f" (错误: {up.fetch_error})" if up.fetch_error else ""
            
            logger.info(f"  - {up.name} (UID: {up.uid}): {video_count}个视频, 最后更新: {last_update}{error_info}")
        
        # 3. 检查总视频数
        total_videos = session.query(BilibiliVideo).filter_by(is_deleted=False).count()
        logger.info(f"总视频数: {total_videos}")
        
        if total_videos == 0:
            logger.warning("⚠️  数据库中没有视频数据")
            logger.info("解决方案: 运行 python3 fetch_bilibili_data.py")
        
        # 4. 检查API返回的数据格式
        logger.info("检查API数据格式...")
        all_data = []
        for up in ups[:3]:  # 只检查前3个UP主
            videos = session.query(BilibiliVideo).filter_by(
                uid=up.uid,
                is_deleted=False
            ).limit(5).all()
            
            logger.info(f"  UP主 {up.name}: {len(videos)}个视频示例")
        
        return True
        
    except Exception as e:
        logger.error(f"检查B站数据失败: {e}", exc_info=True)
        return False
    finally:
        session.close()


def check_api_endpoints():
    """检查API端点是否正常"""
    logger.info("=" * 60)
    logger.info("检查API端点...")
    logger.info("=" * 60)
    
    logger.info("建议手动测试以下API端点:")
    logger.info("  1. curl http://localhost:5001/api/papers")
    logger.info("  2. curl http://localhost:5001/api/bilibili/all")
    logger.info("  3. 检查浏览器控制台的网络请求")


def main():
    """主函数"""
    logger.info("开始诊断...")
    logger.info("")
    
    papers_ok = check_papers_data()
    logger.info("")
    
    bilibili_ok = check_bilibili_data()
    logger.info("")
    
    check_api_endpoints()
    logger.info("")
    
    logger.info("=" * 60)
    logger.info("诊断总结:")
    logger.info("=" * 60)
    
    if papers_ok:
        logger.info("✅ 论文数据: 正常")
    else:
        logger.error("❌ 论文数据: 有问题")
        logger.info("   解决方案: python3 fetch_new_data.py --papers")
    
    if bilibili_ok:
        logger.info("✅ B站数据: 正常")
    else:
        logger.error("❌ B站数据: 有问题")
        logger.info("   解决方案: python3 fetch_bilibili_data.py")
    
    logger.info("")
    logger.info("如果数据正常但前端仍无法显示，请检查:")
    logger.info("  1. 浏览器控制台的错误信息")
    logger.info("  2. 网络请求的响应状态")
    logger.info("  3. API返回的数据格式")


if __name__ == '__main__':
    main()

