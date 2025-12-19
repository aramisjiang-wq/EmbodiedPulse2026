#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查视频更新状态
诊断为什么找不到需要更新的视频
"""

import sys
import os
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bilibili_models import get_bilibili_session, BilibiliVideo
from sqlalchemy import func

def check_video_update_status():
    """检查视频更新状态"""
    print("=" * 80)
    print("检查视频更新状态")
    print("=" * 80)
    
    session = get_bilibili_session()
    
    try:
        # 统计所有视频
        total_videos = session.query(func.count(BilibiliVideo.bvid)).filter_by(
            is_deleted=False
        ).scalar()
        
        print(f"\n总视频数: {total_videos}")
        
        # 检查更新时间分布
        now = datetime.now()
        cutoff_7days = now - timedelta(days=7)
        cutoff_1day = now - timedelta(days=1)
        
        videos_updated_7days = session.query(func.count(BilibiliVideo.bvid)).filter(
            BilibiliVideo.is_deleted == False,
            BilibiliVideo.updated_at >= cutoff_7days
        ).scalar()
        
        videos_updated_1day = session.query(func.count(BilibiliVideo.bvid)).filter(
            BilibiliVideo.is_deleted == False,
            BilibiliVideo.updated_at >= cutoff_1day
        ).scalar()
        
        videos_old = session.query(func.count(BilibiliVideo.bvid)).filter(
            BilibiliVideo.is_deleted == False,
            (BilibiliVideo.updated_at < cutoff_7days) | (BilibiliVideo.updated_at.is_(None))
        ).scalar()
        
        print(f"\n更新时间分布:")
        print(f"  最近1天更新: {videos_updated_1day} 个")
        print(f"  最近7天更新: {videos_updated_7days} 个")
        print(f"  7天前更新: {videos_old} 个")
        
        # 检查播放量为0的视频
        videos_zero_play = session.query(func.count(BilibiliVideo.bvid)).filter(
            BilibiliVideo.is_deleted == False,
            BilibiliVideo.play == 0
        ).scalar()
        
        print(f"\n播放量统计:")
        print(f"  播放量为0: {videos_zero_play} 个")
        
        # 检查最近更新的视频示例
        print(f"\n最近更新的视频示例（前10个）:")
        recent_videos = session.query(BilibiliVideo).filter_by(
            is_deleted=False
        ).order_by(BilibiliVideo.updated_at.desc()).limit(10).all()
        
        for v in recent_videos:
            days_ago = (now - v.updated_at).days if v.updated_at else None
            print(f"  {v.bvid[:12]}... 播放量: {v.play:,}, 更新时间: {v.updated_at} ({days_ago}天前)")
        
        # 检查需要更新的视频（即使 updated_at 在7天内，但播放量可能还是旧的）
        print(f"\n建议强制更新所有视频（使用 --force 参数）")
        print(f"  因为即使 updated_at 在7天内，播放量字段可能没有真正更新")
        
    finally:
        session.close()

if __name__ == '__main__':
    check_video_update_status()

