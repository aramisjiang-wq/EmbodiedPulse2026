#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查逐际动力的数据是否还在数据库中
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bilibili_models import get_bilibili_session, BilibiliUp, BilibiliVideo
from sqlalchemy import func

def check_limx_data():
    """检查逐际动力的数据"""
    print("=" * 80)
    print("检查逐际动力数据")
    print("=" * 80)
    
    session = get_bilibili_session()
    LIMX_UID = 1172054289
    
    try:
        # 1. 检查UP主记录
        print("\n【1. UP主记录】")
        print("-" * 80)
        up = session.query(BilibiliUp).filter_by(uid=LIMX_UID).first()
        if up:
            print(f"✅ UP主记录存在:")
            print(f"   UID: {up.uid}")
            print(f"   名称: {up.name}")
            print(f"   is_active: {up.is_active}")
            print(f"   videos_count: {up.videos_count}")
            print(f"   views_count: {up.views_count}")
            print(f"   last_fetch_at: {up.last_fetch_at}")
        else:
            print(f"❌ UP主记录不存在！")
            return
        
        # 2. 检查视频记录
        print("\n【2. 视频记录】")
        print("-" * 80)
        all_videos = session.query(BilibiliVideo).filter_by(uid=LIMX_UID).all()
        active_videos = session.query(BilibiliVideo).filter_by(
            uid=LIMX_UID, is_deleted=False
        ).all()
        
        print(f"所有视频（包括已删除）: {len(all_videos)} 条")
        print(f"未删除的视频: {len(active_videos)} 条")
        
        if active_videos:
            print(f"\n前10个视频:")
            for i, video in enumerate(active_videos[:10], 1):
                print(f"  {i}. {video.bvid} - {video.title[:40]}...")
                print(f"     播放量: {video.play:,}, is_deleted: {video.is_deleted}")
        
        # 3. 检查统计数据
        print("\n【3. 统计数据】")
        print("-" * 80)
        video_count = session.query(func.count(BilibiliVideo.bvid)).filter_by(
            uid=LIMX_UID, is_deleted=False
        ).scalar()
        total_views = session.query(func.sum(BilibiliVideo.play)).filter_by(
            uid=LIMX_UID, is_deleted=False
        ).scalar() or 0
        
        print(f"视频数量: {video_count}")
        print(f"总播放量: {total_views:,}")
        
        # 4. 检查is_active状态
        print("\n【4. 状态检查】")
        print("-" * 80)
        if not up.is_active:
            print(f"⚠️  UP主 is_active=False，这会导致数据不显示！")
            print(f"   建议：设置为 True")
        else:
            print(f"✅ UP主 is_active=True")
        
        deleted_count = len(all_videos) - len(active_videos)
        if deleted_count > 0:
            print(f"⚠️  有 {deleted_count} 个视频被标记为已删除")
        
    finally:
        session.close()

if __name__ == '__main__':
    check_limx_data()

