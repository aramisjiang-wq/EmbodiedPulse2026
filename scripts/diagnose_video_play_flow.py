#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整诊断视频播放量数据流
检查：数据库 → API → 前端显示
"""

import sys
import os
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bilibili_models import get_bilibili_session, BilibiliVideo, BilibiliUp
from sqlalchemy import func

def diagnose_video_play_flow():
    """诊断视频播放量数据流"""
    print("=" * 80)
    print("视频播放量数据流完整诊断")
    print("=" * 80)
    
    session = get_bilibili_session()
    
    try:
        # 1. 检查数据库中的视频数据
        print("\n【1. 数据库检查】")
        print("-" * 80)
        
        # 随机选择几个视频检查
        sample_videos = session.query(BilibiliVideo).filter_by(
            is_deleted=False
        ).order_by(BilibiliVideo.updated_at.desc()).limit(5).all()
        
        print(f"检查最近更新的5个视频：")
        for v in sample_videos:
            days_ago = (datetime.now() - v.updated_at).days if v.updated_at else None
            print(f"  BV号: {v.bvid[:12]}...")
            print(f"    标题: {v.title[:30] if v.title else 'N/A'}...")
            print(f"    播放量(原始): {v.play:,}")
            print(f"    播放量(格式化): {v.play_formatted}")
            print(f"    更新时间: {v.updated_at} ({days_ago}天前)")
            print()
        
        # 2. 检查需要更新的视频数量
        print("\n【2. 需要更新的视频统计】")
        print("-" * 80)
        
        now = datetime.now()
        cutoff_7days = now - timedelta(days=7)
        
        # 7天前未更新的
        old_videos = session.query(func.count(BilibiliVideo.bvid)).filter(
            BilibiliVideo.is_deleted == False,
            (BilibiliVideo.updated_at < cutoff_7days) | (BilibiliVideo.updated_at.is_(None))
        ).scalar()
        
        # 播放量为0的
        zero_play_videos = session.query(func.count(BilibiliVideo.bvid)).filter(
            BilibiliVideo.is_deleted == False,
            BilibiliVideo.play == 0
        ).scalar()
        
        # 7天内更新但播放量可能过时的（需要强制更新）
        recent_but_stale = session.query(func.count(BilibiliVideo.bvid)).filter(
            BilibiliVideo.is_deleted == False,
            BilibiliVideo.updated_at >= cutoff_7days,
            BilibiliVideo.play > 0
        ).scalar()
        
        print(f"7天前未更新的视频: {old_videos} 个")
        print(f"播放量为0的视频: {zero_play_videos} 个")
        print(f"7天内更新但可能需要强制更新的视频: {recent_but_stale} 个")
        print(f"\n💡 建议：如果前端显示还是旧的，使用 --force 强制更新所有视频")
        
        # 3. 模拟API返回的数据格式
        print("\n【3. API返回数据格式检查】")
        print("-" * 80)
        
        if sample_videos:
            v = sample_videos[0]
            api_format = {
                'bvid': v.bvid,
                'play': v.play_formatted or '0',
                'play_raw': v.play or 0,
            }
            print(f"示例视频 API 返回格式：")
            print(f"  {api_format}")
            print(f"\n前端会使用: play_raw ({api_format['play_raw']}) 或 play ({api_format['play']})")
        
        # 4. 检查UP主的总播放量计算
        print("\n【4. UP主总播放量检查】")
        print("-" * 80)
        
        sample_up = session.query(BilibiliUp).filter_by(is_active=True).first()
        if sample_up:
            # 从数据库字段
            db_views = sample_up.views_count or 0
            # 从视频表计算
            calculated_views = session.query(func.sum(BilibiliVideo.play)).filter_by(
                uid=sample_up.uid, is_deleted=False
            ).scalar() or 0
            
            print(f"UP主: {sample_up.name} (UID: {sample_up.uid})")
            print(f"  数据库字段 views_count: {db_views:,}")
            print(f"  从视频表计算的总播放量: {calculated_views:,}")
            if db_views != calculated_views:
                print(f"  ⚠️  数据不一致！数据库字段可能过时")
            else:
                print(f"  ✅ 数据一致")
        
        # 5. 建议操作
        print("\n【5. 建议操作】")
        print("-" * 80)
        print("1. 如果前端显示还是旧的播放量：")
        print("   - 运行: python3 scripts/update_video_play_counts.py --force")
        print("   - 然后访问: /api/bilibili/all?force=1 清除API缓存")
        print("   - 前端强制刷新: Ctrl+F5")
        print()
        print("2. 如果数据库数据已经是最新的，但前端还是旧的：")
        print("   - 检查API缓存（5分钟）")
        print("   - 检查浏览器缓存")
        print("   - 查看浏览器开发者工具的Network标签")
        
    finally:
        session.close()

if __name__ == '__main__':
    diagnose_video_play_flow()

