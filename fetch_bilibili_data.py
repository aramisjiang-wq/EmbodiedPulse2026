#!/usr/bin/env python3
"""
B站数据抓取脚本
定期从B站API抓取数据并存储到数据库
"""
import os
import sys
import time
import logging
from datetime import datetime
from bilibili_client import BilibiliClient, format_number, format_timestamp
from bilibili_models import (
    get_bilibili_session, BilibiliUp, BilibiliVideo,
    init_bilibili_db
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s %(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 从app.py导入UP主列表
try:
    from app import BILIBILI_UP_LIST
except ImportError:
    # 如果无法导入，使用默认列表
    BILIBILI_UP_LIST = [
        1172054289,  # 逐际动力
        3546728498202679,  # 众擎机器人
        22477177,  # 云深处科技
        519804427,  # 傅利叶Fourier
        # 添加更多UID...
    ]
    logger.warning("无法从app.py导入BILIBILI_UP_LIST，使用默认列表")


def fetch_and_save_up_data(uid, video_count=50):
    """
    抓取并保存单个UP主的数据
    
    Args:
        uid: UP主UID
        video_count: 抓取的视频数量
    
    Returns:
        bool: 是否成功
    """
    session = get_bilibili_session()
    client = BilibiliClient()
    
    try:
        logger.info(f"开始抓取UP主 {uid} 的数据...")
        
        # 从API获取数据
        data = client.get_all_data(uid, video_count=video_count)
        
        if not data:
            logger.warning(f"UP主 {uid} 数据获取失败")
            # 更新错误信息
            up = session.query(BilibiliUp).filter_by(uid=uid).first()
            if up:
                up.fetch_error = "数据获取失败"
                up.last_fetch_at = datetime.now()
                session.commit()
            return False
        
        user_info = data.get('user_info', {})
        user_stat = data.get('user_stat', {})
        videos = data.get('videos', [])
        
        # 更新或创建UP主信息
        up = session.query(BilibiliUp).filter_by(uid=uid).first()
        if not up:
            up = BilibiliUp(uid=uid)
            session.add(up)
        
        # 更新UP主基本信息
        up.name = user_info.get('name', f'UP主{uid}')
        up.face = user_info.get('face', '')
        up.sign = user_info.get('sign', '')
        up.level = user_info.get('level', 0)
        up.fans = user_info.get('fans', 0)
        up.fans_formatted = format_number(up.fans)
        up.friend = user_info.get('friend', 0)
        up.space_url = f"https://space.bilibili.com/{uid}"
        
        # 更新统计数据
        up.videos_count = user_stat.get('videos', 0)
        up.views_count = user_stat.get('views', 0)
        up.views_formatted = format_number(up.views_count)
        up.likes_count = user_stat.get('likes', 0)
        up.likes_formatted = format_number(up.likes_count)
        
        # 更新状态
        up.is_active = True
        up.last_fetch_at = datetime.now()
        up.fetch_error = None
        up.updated_at = datetime.now()
        
        session.commit()
        logger.info(f"UP主 {up.name} 信息已更新")
        
        # 处理视频数据
        saved_count = 0
        for video_data in videos:
            bvid = video_data.get('bvid', '')
            if not bvid:
                continue
            
            # 查找或创建视频记录
            video = session.query(BilibiliVideo).filter_by(bvid=bvid).first()
            if not video:
                video = BilibiliVideo(bvid=bvid, uid=uid)
                session.add(video)
            
            # 更新视频信息
            video.aid = video_data.get('aid', 0)
            video.title = video_data.get('title', '')
            video.pic = video_data.get('pic', '')
            video.description = video_data.get('description', '')
            video.length = video_data.get('length', '')
            
            # 统计数据
            play_raw = video_data.get('play', 0) or 0
            video.play = play_raw
            video.play_formatted = format_number(play_raw)
            video.video_review = video_data.get('video_review', 0) or 0
            video.video_review_formatted = format_number(video.video_review)
            video.favorites = video_data.get('favorites', 0) or 0
            video.favorites_formatted = format_number(video.favorites)
            
            # 时间
            pubdate_raw = video_data.get('pubdate', 0)
            if pubdate_raw:
                video.pubdate_raw = pubdate_raw
                video.pubdate = datetime.fromtimestamp(pubdate_raw)
            
            video.url = f"https://www.bilibili.com/video/{bvid}"
            video.is_deleted = False
            video.updated_at = datetime.now()
            
            saved_count += 1
        
        session.commit()
        logger.info(f"UP主 {up.name} 的视频数据已更新，共 {saved_count} 条")
        
        return True
        
    except Exception as e:
        logger.error(f"抓取UP主 {uid} 数据失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        # 更新错误信息
        try:
            up = session.query(BilibiliUp).filter_by(uid=uid).first()
            if up:
                up.fetch_error = str(e)
                up.last_fetch_at = datetime.now()
                session.commit()
        except:
            pass
        
        return False
    
    finally:
        session.close()


def fetch_all_bilibili_data(video_count=50, delay_between_requests=1.5):
    """
    抓取所有UP主的数据
    
    Args:
        video_count: 每个UP主抓取的视频数量
        delay_between_requests: 请求间隔（秒），避免触发风控
    """
    logger.info("=" * 60)
    logger.info("开始抓取所有B站数据")
    logger.info(f"UP主数量: {len(BILIBILI_UP_LIST)}")
    logger.info(f"每个UP主视频数量: {video_count}")
    logger.info("=" * 60)
    
    total = len(BILIBILI_UP_LIST)
    success_count = 0
    fail_count = 0
    
    for idx, uid in enumerate(BILIBILI_UP_LIST):
        try:
            # 添加请求间隔，避免触发B站风控
            if idx > 0:
                delay = delay_between_requests + (idx % 3) * 0.3
                logger.info(f"请求间隔 {delay:.1f}秒，避免风控 (进度: {idx+1}/{total})")
                time.sleep(delay)
            
            if fetch_and_save_up_data(uid, video_count=video_count):
                success_count += 1
            else:
                fail_count += 1
                
        except Exception as e:
            logger.error(f"处理UP主 {uid} 时出错: {e}")
            fail_count += 1
    
    logger.info("=" * 60)
    logger.info(f"抓取完成！成功: {success_count}, 失败: {fail_count}")
    logger.info("=" * 60)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='抓取B站数据并存储到数据库')
    parser.add_argument('--video-count', type=int, default=50, help='每个UP主抓取的视频数量')
    parser.add_argument('--delay', type=float, default=1.5, help='请求间隔（秒）')
    parser.add_argument('--init-db', action='store_true', help='初始化数据库表')
    parser.add_argument('--uid', type=int, help='只抓取指定UID的数据')
    
    args = parser.parse_args()
    
    # 初始化数据库
    if args.init_db:
        logger.info("初始化数据库...")
        init_bilibili_db()
        return
    
    # 如果指定了UID，只抓取该UP主
    if args.uid:
        fetch_and_save_up_data(args.uid, video_count=args.video_count)
    else:
        # 抓取所有UP主
        fetch_all_bilibili_data(
            video_count=args.video_count,
            delay_between_requests=args.delay
        )


if __name__ == '__main__':
    main()
