#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全地从Bilibili API获取更新视频数据
包含完整的错误处理、频率限制、重试机制和日志记录
"""

import os
import sys
import time
import logging
from datetime import datetime
from dotenv import load_dotenv

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

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
        123456789,  # 示例（需要替换为实际UID）
    ]
    logger.warning("无法从app.py导入BILIBILI_UP_LIST，使用默认列表")


def fetch_and_save_up_data_safe(uid, video_count=50, max_retries=3):
    """
    安全地抓取并保存单个UP主的数据（带重试和错误处理）
    
    Args:
        uid: UP主UID
        video_count: 抓取的视频数量
        max_retries: 最大重试次数
    
    Returns:
        dict: 抓取结果
    """
    session = get_bilibili_session()
    client = BilibiliClient()
    
    result = {
        'uid': uid,
        'success': False,
        'up_updated': False,
        'videos_created': 0,
        'videos_updated': 0,
        'errors': []
    }
    
    for attempt in range(max_retries):
        try:
            logger.info(f"开始抓取UP主 {uid} 的数据 (尝试 {attempt + 1}/{max_retries})...")
            
            # 从API获取数据（bilibili_client内部已有频率限制和重试机制）
            data = client.get_all_data(uid, video_count=video_count)
            
            if not data:
                error_msg = f"UP主 {uid} 数据获取失败"
                logger.warning(error_msg)
                result['errors'].append(error_msg)
                
                # 更新错误信息到数据库
                up = session.query(BilibiliUp).filter_by(uid=uid).first()
                if up:
                    up.fetch_error = error_msg
                    up.last_fetch_at = datetime.now()
                    try:
                        session.commit()
                    except Exception as e:
                        logger.error(f"更新错误信息失败: {e}")
                        session.rollback()
                
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5  # 递增等待时间：5s, 10s, 15s
                    logger.info(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                    continue
                else:
                    return result
            
            user_info = data.get('user_info', {})
            user_stat = data.get('user_stat', {})
            videos = data.get('videos', [])
            
            if not user_info:
                error_msg = f"UP主 {uid} 用户信息为空"
                logger.warning(error_msg)
                result['errors'].append(error_msg)
                if attempt < max_retries - 1:
                    time.sleep((attempt + 1) * 5)
                    continue
                else:
                    return result
            
            # 更新或创建UP主信息
            up = session.query(BilibiliUp).filter_by(uid=uid).first()
            if not up:
                up = BilibiliUp(uid=uid)
                session.add(up)
                logger.info(f"  创建新UP主记录: {uid}")
            
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
            
            # 提交UP主信息
            try:
                session.commit()
                result['up_updated'] = True
                logger.info(f"  ✅ UP主信息更新成功: {up.name} (粉丝: {up.fans_formatted})")
            except Exception as e:
                logger.error(f"  ❌ 更新UP主信息失败: {e}")
                session.rollback()
                result['errors'].append(f"UP主信息更新失败: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep((attempt + 1) * 5)
                    continue
                else:
                    return result
            
            # 处理视频数据
            if videos:
                logger.info(f"  处理 {len(videos)} 个视频...")
                
                for video_data in videos:
                    try:
                        bvid = video_data.get('bvid')
                        if not bvid:
                            continue
                        
                        # 查找或创建视频记录
                        video = session.query(BilibiliVideo).filter_by(bvid=bvid).first()
                        
                        if video:
                            # 更新现有视频
                            video.title = video_data.get('title', '')
                            video.description = video_data.get('description', '')
                            video.pic = video_data.get('pic', '')
                            video.pubdate = video_data.get('pubdate', 0)
                            video.pubdate_formatted = format_timestamp(video.pubdate)
                            video.length = video_data.get('length', '')
                            video.play = video_data.get('stat', {}).get('view', 0)
                            video.play_formatted = format_number(video.play)
                            video.danmaku = video_data.get('stat', {}).get('danmaku', 0)
                            video.danmaku_formatted = format_number(video.danmaku)
                            video.like = video_data.get('stat', {}).get('like', 0)
                            video.like_formatted = format_number(video.like)
                            video.coin = video_data.get('stat', {}).get('coin', 0)
                            video.coin_formatted = format_number(video.coin)
                            video.favorite = video_data.get('stat', {}).get('favorite', 0)
                            video.favorite_formatted = format_number(video.favorite)
                            video.share = video_data.get('stat', {}).get('share', 0)
                            video.share_formatted = format_number(video.share)
                            video.reply = video_data.get('stat', {}).get('reply', 0)
                            video.reply_formatted = format_number(video.reply)
                            video.url = f"https://www.bilibili.com/video/{bvid}"
                            video.last_updated = datetime.now()
                            
                            result['videos_updated'] += 1
                        else:
                            # 创建新视频
                            video = BilibiliVideo(
                                bvid=bvid,
                                uid=uid,
                                title=video_data.get('title', ''),
                                description=video_data.get('description', ''),
                                pic=video_data.get('pic', ''),
                                pubdate=video_data.get('pubdate', 0),
                                pubdate_formatted=format_timestamp(video_data.get('pubdate', 0)),
                                length=video_data.get('length', ''),
                                play=video_data.get('stat', {}).get('view', 0),
                                play_formatted=format_number(video_data.get('stat', {}).get('view', 0)),
                                danmaku=video_data.get('stat', {}).get('danmaku', 0),
                                danmaku_formatted=format_number(video_data.get('stat', {}).get('danmaku', 0)),
                                like=video_data.get('stat', {}).get('like', 0),
                                like_formatted=format_number(video_data.get('stat', {}).get('like', 0)),
                                coin=video_data.get('stat', {}).get('coin', 0),
                                coin_formatted=format_number(video_data.get('stat', {}).get('coin', 0)),
                                favorite=video_data.get('stat', {}).get('favorite', 0),
                                favorite_formatted=format_number(video_data.get('stat', {}).get('favorite', 0)),
                                share=video_data.get('stat', {}).get('share', 0),
                                share_formatted=format_number(video_data.get('stat', {}).get('share', 0)),
                                reply=video_data.get('stat', {}).get('reply', 0),
                                reply_formatted=format_number(video_data.get('stat', {}).get('reply', 0)),
                                url=f"https://www.bilibili.com/video/{bvid}",
                                last_updated=datetime.now()
                            )
                            session.add(video)
                            result['videos_created'] += 1
                        
                    except Exception as e:
                        logger.error(f"  处理视频失败 ({video_data.get('bvid', 'unknown')}): {e}")
                        result['errors'].append(f"视频 {video_data.get('bvid', 'unknown')}: {str(e)}")
                        continue
                
                # 提交视频数据
                try:
                    session.commit()
                    logger.info(f"  ✅ 视频数据更新成功: 新增 {result['videos_created']} 个，更新 {result['videos_updated']} 个")
                except Exception as e:
                    logger.error(f"  ❌ 提交视频数据失败: {e}")
                    session.rollback()
                    result['errors'].append(f"视频数据提交失败: {str(e)}")
            
            # 成功完成
            result['success'] = True
            return result
            
        except Exception as e:
            error_msg = f"抓取UP主 {uid} 失败: {e}"
            logger.error(error_msg)
            import traceback
            traceback.print_exc()
            result['errors'].append(error_msg)
            session.rollback()
            
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 10  # 递增等待时间：10s, 20s, 30s
                logger.info(f"等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
            else:
                return result
    
    return result


def fetch_all_bilibili_data(video_count=50, delay_between_ups=5):
    """
    安全地抓取所有UP主的数据
    
    Args:
        video_count: 每个UP主抓取的视频数量
        delay_between_ups: UP主之间的延迟（秒），避免触发频率限制
    
    Returns:
        dict: 总体抓取结果
    """
    logger.info("=" * 60)
    logger.info("开始从Bilibili API获取更新数据")
    logger.info(f"UP主数量: {len(BILIBILI_UP_LIST)}")
    logger.info(f"每个UP主视频数: {video_count}")
    logger.info(f"UP主间延迟: {delay_between_ups} 秒")
    logger.info("=" * 60)
    
    # 统计信息
    stats = {
        'total_ups': len(BILIBILI_UP_LIST),
        'success_ups': 0,
        'failed_ups': 0,
        'total_videos_created': 0,
        'total_videos_updated': 0,
        'errors': []
    }
    
    # 遍历所有UP主
    for idx, uid in enumerate(BILIBILI_UP_LIST, 1):
        logger.info(f"\n[{idx}/{stats['total_ups']}] 处理UP主: {uid}")
        
        result = fetch_and_save_up_data_safe(uid, video_count=video_count)
        
        if result['success']:
            stats['success_ups'] += 1
            stats['total_videos_created'] += result['videos_created']
            stats['total_videos_updated'] += result['videos_updated']
        else:
            stats['failed_ups'] += 1
        
        if result['errors']:
            stats['errors'].extend(result['errors'])
        
        # UP主之间的延迟（最后一个不需要延迟）
        if idx < stats['total_ups']:
            logger.info(f"等待 {delay_between_ups} 秒后处理下一个UP主...")
            time.sleep(delay_between_ups)
    
    # 最终统计
    logger.info("\n" + "=" * 60)
    logger.info("抓取完成统计:")
    logger.info(f"  总UP主数: {stats['total_ups']}")
    logger.info(f"  成功UP主: {stats['success_ups']}")
    logger.info(f"  失败UP主: {stats['failed_ups']}")
    logger.info(f"  新增视频: {stats['total_videos_created']}")
    logger.info(f"  更新视频: {stats['total_videos_updated']}")
    if stats['errors']:
        logger.warning(f"  错误数: {len(stats['errors'])}")
        for error in stats['errors'][:10]:  # 只显示前10个错误
            logger.warning(f"    - {error}")
    logger.info("=" * 60)
    
    return stats


def main():
    """主函数"""
    try:
        # 加载环境变量
        env_path = os.path.join(project_root, '.env')
        if os.path.exists(env_path):
            load_dotenv(env_path)
        
        # 初始化数据库
        init_bilibili_db()
        
        # 执行抓取
        stats = fetch_all_bilibili_data(video_count=50, delay_between_ups=5)
        
        if stats['failed_ups'] == 0:
            logger.info("✅ Bilibili数据更新任务完成")
            sys.exit(0)
        elif stats['success_ups'] > 0:
            logger.warning(f"⚠️ Bilibili数据更新部分完成（{stats['success_ups']}/{stats['total_ups']} 成功）")
            sys.exit(0)
        else:
            logger.error("❌ Bilibili数据更新任务失败")
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

