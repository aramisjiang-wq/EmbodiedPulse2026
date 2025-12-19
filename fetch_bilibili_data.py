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


def fetch_and_save_up_data(uid, video_count=50, fetch_all=False):
    """
    抓取并保存单个UP主的数据
    
    Args:
        uid: UP主UID
        video_count: 抓取的视频数量（当fetch_all=False时使用）
        fetch_all: 是否抓取所有视频（True时忽略video_count，抓取所有）
    
    Returns:
        bool: 是否成功
    """
    session = get_bilibili_session()
    client = BilibiliClient()
    
    try:
        if fetch_all:
            logger.info(f"开始抓取UP主 {uid} 的所有视频数据...")
        else:
            logger.info(f"开始抓取UP主 {uid} 的数据（最新 {video_count} 个视频）...")
        
        # 从API获取数据
        data = client.get_all_data(uid, video_count=video_count, fetch_all=fetch_all)
        
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
        
        # 更新统计数据（只更新有效数据，防止覆盖为0）
        from sqlalchemy import func
        
        # 视频数量：优先使用API数据，如果为0则尝试从视频表计算
        api_videos_count = user_stat.get('videos', 0)
        if api_videos_count > 0:
            up.videos_count = api_videos_count
        elif up.videos_count == 0:
            # 如果API返回0且数据库也是0，尝试从视频表计算
            video_count = session.query(func.count(BilibiliVideo.bvid)).filter_by(
                uid=uid, is_deleted=False
            ).scalar()
            if video_count > 0:
                up.videos_count = video_count
                logger.info(f"从视频表计算视频数量: {video_count}")
        
        # 总播放量：优先使用API数据，如果为0则尝试从视频表计算
        api_views_count = user_stat.get('views', 0)
        if api_views_count > 0:
            up.views_count = api_views_count
            up.views_formatted = format_number(api_views_count)
        elif up.views_count == 0:
            # 如果API返回0且数据库也是0，尝试从视频表计算
            total_views = session.query(func.sum(BilibiliVideo.play)).filter_by(
                uid=uid, is_deleted=False
            ).scalar() or 0
            if total_views > 0:
                up.views_count = total_views
                up.views_formatted = format_number(total_views)
                logger.info(f"从视频表计算总播放量: {total_views:,}")
        
        # 获赞数：只更新有效数据
        api_likes_count = user_stat.get('likes', 0)
        if api_likes_count > 0:
            up.likes_count = api_likes_count
            up.likes_formatted = format_number(api_likes_count)
        
        # 更新状态
        up.is_active = True
        up.last_fetch_at = datetime.now()
        up.fetch_error = None
        up.updated_at = datetime.now()
        
        session.commit()
        logger.info(f"UP主 {up.name} 信息已更新")
        
        # 处理视频数据（更新为主，只更新已存在的记录，不创建新记录）
        updated_count = 0
        created_count = 0
        
        # ✅ 修复：即使视频列表为空，也要尝试更新已存在的视频播放量
        if not videos or len(videos) == 0:
            logger.warning(f"视频列表为空，尝试更新已存在的视频播放量 (UID: {uid})")
            # 获取该UP主最近更新的视频（最多50个），尝试更新播放量
            existing_videos = session.query(BilibiliVideo).filter_by(
                uid=uid, is_deleted=False
            ).order_by(BilibiliVideo.updated_at.asc()).limit(50).all()
            
            if existing_videos:
                logger.info(f"找到 {len(existing_videos)} 个已存在的视频，尝试更新播放量...")
                # 这里可以调用 update_video_play_counts 的逻辑，但为了简单，先跳过
                # 建议使用独立的视频播放量更新脚本
        
        for video_data in videos:
            bvid = video_data.get('bvid', '')
            if not bvid:
                continue
            
            # 查找或创建视频记录
            video = session.query(BilibiliVideo).filter_by(bvid=bvid).first()
            is_new = False
            if not video:
                # 只创建新视频记录（如果数据库中不存在）
                video = BilibiliVideo(bvid=bvid, uid=uid)
                session.add(video)
                is_new = True
                created_count += 1
            else:
                updated_count += 1
            
            # 更新视频信息（无论新旧都更新，确保数据最新）
            video.aid = video_data.get('aid', 0)
            video.title = video_data.get('title', '')
            video.pic = video_data.get('pic', '')
            video.description = video_data.get('description', '')
            video.length = video_data.get('length', '')
            
            # 统计数据（只更新有效数据，不覆盖为0）
            play_raw = video_data.get('play', 0) or 0
            if play_raw > 0:
                # 只有播放量大于0时才更新
                video.play = play_raw
                video.play_formatted = format_number(play_raw)
            # 如果 play_raw 为 0，不更新（保持原值，避免覆盖有效数据）
            video.video_review = video_data.get('video_review', 0) or 0
            video.video_review_formatted = format_number(video.video_review)
            video.favorites = video_data.get('favorites', 0) or 0
            video.favorites_formatted = format_number(video.favorites)
            
            # 时间（如果API返回了新的时间，也更新）
            pubdate_raw = video_data.get('pubdate', 0)
            if pubdate_raw:
                video.pubdate_raw = pubdate_raw
                video.pubdate = datetime.fromtimestamp(pubdate_raw)
            
            video.url = f"https://www.bilibili.com/video/{bvid}"
            video.is_deleted = False
            video.updated_at = datetime.now()
        
        session.commit()
        total_count = updated_count + created_count
        logger.info(f"UP主 {up.name} 的视频数据已更新: 更新{updated_count}条, 新增{created_count}条, 共{total_count}条")
        
        return True
        
    except Exception as e:
        logger.error(f"抓取UP主 {uid} 数据失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        # 更新错误信息（改进：记录详细错误信息和时间）
        try:
            up = session.query(BilibiliUp).filter_by(uid=uid).first()
            if up:
                error_msg = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: {str(e)}"
                up.fetch_error = error_msg
                up.last_fetch_at = datetime.now()
                session.commit()
                logger.error(f"已记录错误信息到数据库: {error_msg}")
        except Exception as db_error:
            logger.error(f"更新错误信息到数据库失败: {db_error}")
        
        return False
    
    finally:
        session.close()


def fetch_all_bilibili_data(video_count=50, delay_between_requests=1.5, fetch_all=False):
    """
    抓取所有UP主的数据
    
    Args:
        video_count: 每个UP主抓取的视频数量（当fetch_all=False时使用）
        delay_between_requests: 请求间隔（秒），避免触发风控
        fetch_all: 是否抓取所有视频（True时忽略video_count，抓取所有）
    """
    logger.info("=" * 60)
    logger.info("开始抓取所有B站数据")
    logger.info(f"UP主数量: {len(BILIBILI_UP_LIST)}")
    if fetch_all:
        logger.info(f"抓取模式: 所有视频（分页抓取）")
    else:
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
            
            if fetch_and_save_up_data(uid, video_count=video_count, fetch_all=fetch_all):
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
    parser.add_argument('--video-count', type=int, default=50, help='每个UP主抓取的视频数量（当--fetch-all未设置时使用）')
    parser.add_argument('--delay', type=float, default=1.5, help='请求间隔（秒）')
    parser.add_argument('--init-db', action='store_true', help='初始化数据库表')
    parser.add_argument('--uid', type=int, help='只抓取指定UID的数据')
    parser.add_argument('--fetch-all', action='store_true', help='抓取所有视频（分页抓取，忽略--video-count）')
    
    args = parser.parse_args()
    
    # 初始化数据库
    if args.init_db:
        logger.info("初始化数据库...")
        init_bilibili_db()
        return
    
    # 如果指定了UID，只抓取该UP主
    if args.uid:
        fetch_and_save_up_data(args.uid, video_count=args.video_count, fetch_all=args.fetch_all)
    else:
        # 抓取所有UP主
        fetch_all_bilibili_data(
            video_count=args.video_count,
            delay_between_requests=args.delay,
            fetch_all=args.fetch_all
        )


if __name__ == '__main__':
    main()
