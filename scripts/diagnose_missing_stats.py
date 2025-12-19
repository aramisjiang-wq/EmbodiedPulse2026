#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断部分企业统计数据缺失问题
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bilibili_models import get_bilibili_session, BilibiliUp, BilibiliVideo
from bilibili_client import BilibiliClient
from sqlalchemy import func

# 需要检查的企业列表
TARGET_UPS = {
    'Unitree宇树科技': 521974986,
    '云深处科技': 22477177,
    '众擎机器人': 3546728498202679,
    '逐际动力': 1172054289,
    '傅利叶Fourier': 519804427,
    '加速进化机器人': 3546665977907667,
}

def diagnose_missing_stats():
    """诊断统计数据缺失问题"""
    print("=" * 80)
    print("诊断部分企业统计数据缺失问题")
    print("=" * 80)
    
    session = get_bilibili_session()
    client = BilibiliClient()
    
    try:
        for name, uid in TARGET_UPS.items():
            print(f"\n【{name}】 (UID: {uid})")
            print("-" * 80)
            
            # 1. 检查数据库中的数据
            up = session.query(BilibiliUp).filter_by(uid=uid).first()
            if not up:
                print(f"  ❌ 数据库中不存在该UP主")
                continue
            
            print(f"  数据库字段值:")
            print(f"    videos_count: {up.videos_count}")
            print(f"    views_count: {up.views_count}")
            print(f"    views_formatted: {up.views_formatted or '(空)'}")
            print(f"    最后抓取时间: {up.last_fetch_at or '(未抓取)'}")
            print(f"    抓取错误: {up.fetch_error or '(无错误)'}")
            
            # 2. 从视频表实际统计
            video_count = session.query(func.count(BilibiliVideo.bvid)).filter_by(
                uid=uid,
                is_deleted=False
            ).scalar()
            
            total_views = session.query(func.sum(BilibiliVideo.play)).filter_by(
                uid=uid,
                is_deleted=False
            ).scalar() or 0
            
            print(f"  视频表实际统计:")
            print(f"    视频数量: {video_count}")
            print(f"    总播放量: {total_views}")
            
            # 3. 尝试使用 upstat 接口获取数据
            print(f"  尝试使用 upstat 接口获取数据...")
            try:
                upstat = client._get_upstat(uid)
                if upstat:
                    archive = upstat.get('archive', {})
                    if isinstance(archive, dict):
                        total_views_from_api = archive.get('view', 0)
                        print(f"    ✅ upstat 接口返回总播放量: {total_views_from_api:,}")
                    else:
                        print(f"    ⚠️  archive 不是字典类型: {type(archive)}")
                    likes = upstat.get('likes', 0)
                    print(f"    ✅ upstat 接口返回获赞数: {likes:,}")
                else:
                    print(f"    ❌ upstat 接口返回 None")
            except Exception as e:
                print(f"    ❌ upstat 接口调用失败: {e}")
            
            # 4. 分析问题
            print(f"  问题分析:")
            if up.videos_count == 0 or up.views_count == 0:
                print(f"    ⚠️  统计数据字段为0或空")
                if video_count > 0:
                    print(f"    💡 建议：可以从视频表更新 videos_count = {video_count}")
                if total_views > 0:
                    print(f"    💡 建议：可以从视频表更新 views_count = {total_views:,}")
            else:
                print(f"    ✅ 统计数据字段有值")
            
            if up.videos_count != video_count:
                print(f"    ⚠️  视频数量不一致：数据库={up.videos_count}, 实际={video_count}")
            if up.views_count != total_views:
                print(f"    ⚠️  总播放量不一致：数据库={up.views_count:,}, 实际={total_views:,}")
        
        print("\n" + "=" * 80)
        print("诊断完成")
        print("=" * 80)
        
    finally:
        session.close()

if __name__ == '__main__':
    diagnose_missing_stats()

