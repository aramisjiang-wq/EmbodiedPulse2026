#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深度诊断B站数据问题
检查数据库 -> API -> 前端的完整数据流
"""

import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bilibili_models import get_bilibili_session, BilibiliUp, BilibiliVideo
from bilibili_client import BilibiliClient, format_number
from sqlalchemy import func
from datetime import datetime, timedelta

# 需要检查的企业列表
TARGET_UPS = {
    'Unitree宇树科技': 521974986,
    '云深处科技': 22477177,
    '众擎机器人': 3546728498202679,
    '逐际动力': 1172054289,
    '傅利叶Fourier': 519804427,
    '加速进化机器人': 3546665977907667,
}

def deep_diagnose():
    """深度诊断数据流"""
    print("=" * 80)
    print("深度诊断B站数据问题 - 完整数据流检查")
    print("=" * 80)
    
    session = get_bilibili_session()
    client = BilibiliClient()
    
    try:
        for name, uid in TARGET_UPS.items():
            print(f"\n【{name}】 (UID: {uid})")
            print("=" * 80)
            
            # ========== 1. 数据库层检查 ==========
            print("\n【1. 数据库层】")
            up = session.query(BilibiliUp).filter_by(uid=uid).first()
            if not up:
                print("  ❌ 数据库中不存在该UP主")
                continue
            
            print(f"  数据库原始值:")
            print(f"    videos_count: {up.videos_count} (type: {type(up.videos_count).__name__})")
            print(f"    views_count: {up.views_count} (type: {type(up.views_count).__name__})")
            print(f"    views_formatted: {repr(up.views_formatted)}")
            print(f"    last_fetch_at: {up.last_fetch_at}")
            
            # 检查是否为0或None
            if up.videos_count is None or up.videos_count == 0:
                print(f"    ⚠️  videos_count 为 None 或 0")
            if up.views_count is None or up.views_count == 0:
                print(f"    ⚠️  views_count 为 None 或 0")
            if not up.views_formatted:
                print(f"    ⚠️  views_formatted 为空")
            
            # ========== 2. 从视频表计算实际值 ==========
            print("\n【2. 视频表实际统计】")
            video_count = session.query(func.count(BilibiliVideo.bvid)).filter_by(
                uid=uid, is_deleted=False
            ).scalar()
            
            total_views = session.query(func.sum(BilibiliVideo.play)).filter_by(
                uid=uid, is_deleted=False
            ).scalar() or 0
            
            print(f"  视频数量: {video_count}")
            print(f"  总播放量: {total_views:,}")
            
            # 检查视频播放量更新时间
            recent_videos = session.query(BilibiliVideo).filter_by(
                uid=uid, is_deleted=False
            ).order_by(BilibiliVideo.updated_at.desc()).limit(5).all()
            
            if recent_videos:
                print(f"  最近更新的视频:")
                for v in recent_videos[:3]:
                    print(f"    {v.bvid[:12]}... 播放量: {v.play:,}, 更新时间: {v.updated_at}")
            else:
                print(f"  ⚠️  没有视频数据")
            
            # ========== 3. API层检查（模拟 /api/bilibili/all 的逻辑）==========
            print("\n【3. API层（模拟 /api/bilibili/all）】")
            
            # 模拟 app.py 第1321-1322行的逻辑
            videos_val = format_number(up.videos_count) if up.videos_count else '0'
            views_val = up.views_formatted or (format_number(up.views_count) if up.views_count else '0')
            likes_val = up.likes_formatted or (format_number(up.likes_count) if up.likes_count else '0')
            
            print(f"  API返回的 user_stat:")
            print(f"    videos: {repr(videos_val)}")
            print(f"    views: {repr(views_val)}")
            print(f"    likes: {repr(likes_val)}")
            
            # 检查问题
            if videos_val == '0':
                print(f"    ⚠️  videos 值为 '0'")
            if views_val == '0':
                print(f"    ⚠️  views 值为 '0'")
            
            # ========== 4. 检查 to_dict() 方法（管理端API）==========
            print("\n【4. 管理端API（to_dict()）】")
            up_dict = up.to_dict()
            print(f"  to_dict() 返回:")
            print(f"    videos_count: {up_dict.get('videos_count')}")
            print(f"    views_count: {up_dict.get('views_count')}")
            print(f"    views_formatted: {repr(up_dict.get('views_formatted'))}")
            print(f"    views: {repr(up_dict.get('views'))}")
            
            # ========== 5. 尝试使用 upstat 接口获取数据 ==========
            print("\n【5. upstat 接口检查】")
            try:
                upstat = client._get_upstat(uid)
                if upstat:
                    archive = upstat.get('archive', {})
                    if isinstance(archive, dict):
                        total_views_from_api = archive.get('view', 0)
                        print(f"  ✅ upstat 接口返回总播放量: {total_views_from_api:,}")
                    else:
                        print(f"  ⚠️  archive 不是字典: {type(archive)}")
                    likes = upstat.get('likes', 0)
                    print(f"  ✅ upstat 接口返回获赞数: {likes:,}")
                else:
                    print(f"  ❌ upstat 接口返回 None")
            except Exception as e:
                print(f"  ❌ upstat 接口调用失败: {e}")
            
            # ========== 6. 问题分析和建议 ==========
            print("\n【6. 问题分析】")
            issues = []
            
            if up.videos_count == 0 or up.videos_count is None:
                issues.append(f"videos_count 为 0 或 None（数据库中有 {video_count} 个视频）")
            
            if up.views_count == 0 or up.views_count is None:
                issues.append(f"views_count 为 0 或 None（视频表总播放量为 {total_views:,}）")
            
            if videos_val == '0':
                issues.append("API返回的 videos 值为 '0'")
            
            if views_val == '0':
                issues.append("API返回的 views 值为 '0'")
            
            # 检查视频播放量更新时间
            if recent_videos:
                oldest_update = min(v.updated_at for v in recent_videos if v.updated_at)
                if oldest_update:
                    days_ago = (datetime.now() - oldest_update).days
                    if days_ago > 1:
                        issues.append(f"视频播放量未更新（最近更新是 {days_ago} 天前）")
            
            if issues:
                print(f"  发现 {len(issues)} 个问题:")
                for i, issue in enumerate(issues, 1):
                    print(f"    {i}. {issue}")
            else:
                print(f"  ✅ 未发现问题")
            
            # ========== 7. 修复建议 ==========
            print("\n【7. 修复建议】")
            if up.videos_count == 0 and video_count > 0:
                print(f"  💡 修复 videos_count: 0 → {video_count}")
            if up.views_count == 0 and total_views > 0:
                print(f"  💡 修复 views_count: 0 → {total_views:,}")
            if up.views_count == 0:
                try:
                    upstat = client._get_upstat(uid)
                    if upstat:
                        archive = upstat.get('archive', {})
                        if isinstance(archive, dict):
                            api_views = archive.get('view', 0)
                            if api_views > 0:
                                print(f"  💡 使用 upstat 接口修复 views_count: 0 → {api_views:,}")
                except:
                    pass
        
        print("\n" + "=" * 80)
        print("诊断完成")
        print("=" * 80)
        
    finally:
        session.close()

if __name__ == '__main__':
    deep_diagnose()

