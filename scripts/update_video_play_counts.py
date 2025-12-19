#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
稳妥更新视频播放量数据
支持分批更新、错误重试、进度保存
"""

import sys
import os
import time
import json
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bilibili_models import get_bilibili_session, BilibiliVideo
from bilibili_client import BilibiliClient, format_number
from sqlalchemy import func

# 配置
BATCH_SIZE = 10  # 每批处理的视频数量
DELAY_BETWEEN_BATCHES = 3  # 批次之间的延迟（秒）
DELAY_BETWEEN_VIDEOS = 1  # 视频之间的延迟（秒）
MAX_RETRIES = 3  # 最大重试次数
PROGRESS_FILE = 'video_update_progress.json'  # 进度保存文件

def load_progress():
    """加载进度"""
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_progress(progress):
    """保存进度"""
    try:
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️  保存进度失败: {e}")

def get_video_info_from_api(client, bvid, retry=0):
    """从API获取视频信息"""
    try:
        # 使用 bilibili_client 的 _request_json 方法
        url = "https://api.bilibili.com/x/web-interface/view"
        params = {"bvid": bvid}
        
        data = client._request_json(url, params=params)
        if data and data.get('code') == 0:
            stat = data.get('data', {}).get('stat', {})
            return {
                'play': stat.get('view', 0),
                'video_review': stat.get('reply', 0),
                'favorites': stat.get('favorite', 0),
            }
        return None
    except Exception as e:
        if retry < MAX_RETRIES:
            print(f"    重试 {retry + 1}/{MAX_RETRIES}...")
            time.sleep(2 ** retry)  # 指数退避
            return get_video_info_from_api(client, bvid, retry + 1)
        else:
            print(f"    ❌ 获取失败: {e}")
            return None

def update_video_play_counts(specific_uids=None, force_update=False):
    """
    更新视频播放量数据
    
    Args:
        specific_uids: 指定要更新的UP主UID列表，None表示更新所有
        force_update: 是否强制更新所有视频（即使最近更新过）
    """
    print("=" * 80)
    print("稳妥更新视频播放量数据")
    print("=" * 80)
    
    session = get_bilibili_session()
    client = BilibiliClient()
    progress = load_progress()
    
    try:
        # 获取需要更新的视频列表
        query = session.query(BilibiliVideo).filter_by(is_deleted=False)
        
        if specific_uids:
            query = query.filter(BilibiliVideo.uid.in_(specific_uids))
        
        # 如果不需要强制更新，只更新最近7天未更新的视频
        # ✅ 改进：即使 updated_at 在7天内，如果播放量为0，也需要更新
        if not force_update:
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=7)
            query = query.filter(
                (BilibiliVideo.updated_at < cutoff_date) | 
                (BilibiliVideo.updated_at.is_(None)) |
                (BilibiliVideo.play == 0)  # ✅ 播放量为0的视频也需要更新
            )
        
        videos = query.order_by(BilibiliVideo.updated_at.asc()).all()
        total_videos = len(videos)
        
        print(f"\n找到 {total_videos} 个需要更新的视频")
        print(f"批次大小: {BATCH_SIZE}")
        print(f"批次延迟: {DELAY_BETWEEN_BATCHES} 秒")
        print(f"视频延迟: {DELAY_BETWEEN_VIDEOS} 秒")
        print(f"最大重试: {MAX_RETRIES} 次")
        print()
        
        if total_videos == 0:
            print("✅ 没有需要更新的视频")
            return
        
        # 从上次进度继续
        last_bvid = progress.get('last_bvid', None)
        start_index = 0
        if last_bvid:
            for i, v in enumerate(videos):
                if v.bvid == last_bvid:
                    start_index = i + 1
                    print(f"从上次进度继续，跳过前 {start_index} 个视频")
                    break
        
        updated_count = 0
        failed_count = 0
        skipped_count = 0
        
        # 分批处理
        for batch_start in range(start_index, total_videos, BATCH_SIZE):
            batch_end = min(batch_start + BATCH_SIZE, total_videos)
            batch_videos = videos[batch_start:batch_end]
            
            print(f"\n处理批次 {batch_start // BATCH_SIZE + 1} ({batch_start + 1}-{batch_end}/{total_videos})")
            
            for video in batch_videos:
                try:
                    # 获取视频信息
                    video_info = get_video_info_from_api(client, video.bvid)
                    
                    if video_info:
                        old_play = video.play
                        new_play = video_info.get('play', 0)
                        
                        # 更新数据
                        video.play = new_play
                        video.play_formatted = format_number(new_play)
                        video.video_review = video_info.get('video_review', 0)
                        video.video_review_formatted = format_number(video.video_review)
                        video.favorites = video_info.get('favorites', 0)
                        video.favorites_formatted = format_number(video.favorites)
                        video.updated_at = datetime.now()
                        
                        if old_play != new_play:
                            print(f"  ✅ {video.bvid[:12]}... 播放量: {old_play:,} → {new_play:,}")
                            updated_count += 1
                        else:
                            skipped_count += 1
                    else:
                        print(f"  ⚠️  {video.bvid[:12]}... 跳过（无法获取数据）")
                        failed_count += 1
                    
                    # 保存进度
                    progress['last_bvid'] = video.bvid
                    progress['last_update'] = datetime.now().isoformat()
                    save_progress(progress)
                    
                    # 视频之间延迟
                    if video != batch_videos[-1]:
                        time.sleep(DELAY_BETWEEN_VIDEOS)
                    
                except Exception as e:
                    print(f"  ❌ {video.bvid[:12]}... 更新失败: {e}")
                    failed_count += 1
            
            # 提交批次
            try:
                session.commit()
                print(f"  ✅ 批次已提交")
            except Exception as e:
                print(f"  ❌ 批次提交失败: {e}")
                session.rollback()
            
            # 批次之间延迟
            if batch_end < total_videos:
                print(f"  等待 {DELAY_BETWEEN_BATCHES} 秒...")
                time.sleep(DELAY_BETWEEN_BATCHES)
        
        # 清理进度文件
        if updated_count + skipped_count == total_videos:
            if os.path.exists(PROGRESS_FILE):
                os.remove(PROGRESS_FILE)
                print(f"\n✅ 进度文件已清理")
        
        print("\n" + "=" * 80)
        print("更新完成")
        print("=" * 80)
        print(f"总计: {total_videos} 个视频")
        print(f"更新: {updated_count} 个")
        print(f"跳过: {skipped_count} 个（数据未变化）")
        print(f"失败: {failed_count} 个")
        
    except Exception as e:
        print(f"\n❌ 更新过程出错: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='更新视频播放量数据')
    parser.add_argument('--uids', nargs='+', type=int, help='指定要更新的UP主UID列表')
    parser.add_argument('--force', action='store_true', help='强制更新所有视频')
    
    args = parser.parse_args()
    
    update_video_play_counts(
        specific_uids=args.uids,
        force_update=args.force
    )

