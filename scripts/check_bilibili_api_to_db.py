#!/usr/bin/env python3
"""
检查B站API到数据库的更新流程是否通畅
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from bilibili_models import get_bilibili_session, BilibiliUp, BilibiliVideo
from bilibili_client import BilibiliClient
from datetime import datetime, timedelta
import logging

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def check_bilibili_update_flow():
    """检查B站API到数据库的更新流程"""
    logger.info("=" * 60)
    logger.info("检查B站API到数据库的更新流程")
    logger.info("=" * 60)
    
    session = get_bilibili_session()
    
    try:
        # 1. 检查数据库中的UP主数据
        ups = session.query(BilibiliUp).filter_by(is_active=True).limit(3).all()
        logger.info(f"\n1. 数据库中的UP主数量: {len(ups)}")
        
        if not ups:
            logger.warning("⚠️  数据库中没有活跃的UP主数据")
            return
        
        # 2. 检查最近更新时间
        logger.info("\n2. UP主数据更新情况:")
        for up in ups:
            last_fetch = up.last_fetch_at
            if last_fetch:
                time_diff = datetime.now() - last_fetch
                hours_ago = time_diff.total_seconds() / 3600
                logger.info(f"   - {up.name} (UID: {up.uid})")
                logger.info(f"     最后更新: {last_fetch.strftime('%Y-%m-%d %H:%M:%S')} ({hours_ago:.1f}小时前)")
                logger.info(f"     粉丝数: {up.fans_formatted or up.fans}")
                logger.info(f"     视频数: {up.videos_count}")
                logger.info(f"     总播放量: {up.views_formatted or up.views_count}")
                if up.fetch_error:
                    logger.warning(f"     ⚠️  错误信息: {up.fetch_error}")
            else:
                logger.warning(f"   - {up.name} (UID: {up.uid}): 从未更新")
        
        # 3. 测试API连接
        logger.info("\n3. 测试B站API连接:")
        try:
            client = BilibiliClient()
            test_uid = ups[0].uid
            logger.info(f"   测试UP主: {ups[0].name} (UID: {test_uid})")
            
            # 获取用户信息
            user_info = client.get_user_info(test_uid)
            if user_info:
                logger.info(f"   ✅ API连接正常")
                logger.info(f"   API返回的粉丝数: {user_info.get('fans', 'N/A')}")
                logger.info(f"   数据库中的粉丝数: {ups[0].fans}")
                
                # 比较数据
                api_fans = user_info.get('fans', 0)
                db_fans = ups[0].fans or 0
                if api_fans != db_fans:
                    logger.warning(f"   ⚠️  数据不一致！API: {api_fans}, 数据库: {db_fans}")
                    logger.info(f"   💡 建议运行 fetch_bilibili_data.py 更新数据")
                else:
                    logger.info(f"   ✅ 数据一致")
            else:
                logger.error("   ❌ API连接失败")
        except Exception as e:
            logger.error(f"   ❌ API测试失败: {e}")
        
        # 4. 检查视频数据
        logger.info("\n4. 视频数据情况:")
        total_videos = session.query(BilibiliVideo).count()
        recent_videos = session.query(BilibiliVideo).filter(
            BilibiliVideo.updated_at >= datetime.now() - timedelta(days=1)
        ).count()
        logger.info(f"   总视频数: {total_videos}")
        logger.info(f"   最近24小时更新的视频数: {recent_videos}")
        
        # 5. 检查定时任务配置
        logger.info("\n5. 定时任务配置:")
        from dotenv import load_dotenv
        load_dotenv()
        auto_fetch_enabled = os.getenv('AUTO_FETCH_ENABLED', 'false')
        bilibili_schedule = os.getenv('AUTO_FETCH_BILIBILI_SCHEDULE', '')
        logger.info(f"   自动抓取启用: {auto_fetch_enabled}")
        logger.info(f"   B站抓取计划: {bilibili_schedule if bilibili_schedule else '未配置'}")
        
        # 6. 总结
        logger.info("\n" + "=" * 60)
        logger.info("检查总结:")
        logger.info("=" * 60)
        
        if ups and ups[0].last_fetch_at:
            time_diff = datetime.now() - ups[0].last_fetch_at
            if time_diff < timedelta(hours=6):
                logger.info("✅ 数据更新正常（最近6小时内更新过）")
            elif time_diff < timedelta(hours=24):
                logger.warning("⚠️  数据较旧（超过6小时未更新）")
                logger.info("💡 建议检查定时任务是否正常运行")
            else:
                logger.error("❌ 数据过旧（超过24小时未更新）")
                logger.info("💡 建议手动运行 fetch_bilibili_data.py 更新数据")
        else:
            logger.error("❌ 无法确定数据更新状态")
        
        logger.info("\n💡 手动更新数据命令:")
        logger.info("   python3 fetch_bilibili_data.py")
        
    finally:
        session.close()

if __name__ == '__main__':
    check_bilibili_update_flow()

