#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查B站数据库中总播放量和总视频数字段的数据情况
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bilibili_models import get_bilibili_session, BilibiliUp, BilibiliVideo
from sqlalchemy import func

def check_stats_fields():
    """检查统计数据字段"""
    print("=" * 80)
    print("B站数据库统计数据字段检查")
    print("=" * 80)
    
    session = get_bilibili_session()
    
    try:
        # 获取所有活跃的UP主
        ups = session.query(BilibiliUp).filter_by(is_active=True).all()
        
        print(f"\n活跃UP主数量: {len(ups)}\n")
        
        # 统计字段为空的情况
        zero_videos_count = 0
        zero_views_count = 0
        both_zero = 0
        
        for up in ups:
            print(f"【{up.name}】 (UID: {up.uid})")
            print(f"  数据库字段值:")
            print(f"    videos_count: {up.videos_count} ({'有数据' if up.videos_count and up.videos_count > 0 else '无数据/为0'})")
            print(f"    views_count: {up.views_count} ({'有数据' if up.views_count and up.views_count > 0 else '无数据/为0'})")
            print(f"    views_formatted: {up.views_formatted or '(空)'}")
            
            # 从视频表实际统计
            video_count = session.query(func.count(BilibiliVideo.bvid)).filter_by(
                uid=up.uid,
                is_deleted=False
            ).scalar()
            
            total_views = session.query(func.sum(BilibiliVideo.play)).filter_by(
                uid=up.uid,
                is_deleted=False
            ).scalar() or 0
            
            print(f"  视频表实际统计:")
            print(f"    视频数量: {video_count}")
            print(f"    总播放量: {total_views}")
            
            # 对比分析
            if not up.videos_count or up.videos_count == 0:
                zero_videos_count += 1
                print(f"    ⚠️  videos_count 为0或空")
                if video_count > 0:
                    print(f"    💡 建议：可以从视频表更新 videos_count = {video_count}")
            
            if not up.views_count or up.views_count == 0:
                zero_views_count += 1
                print(f"    ⚠️  views_count 为0或空")
                if total_views > 0:
                    print(f"    💡 建议：可以从视频表更新 views_count = {total_views}")
            
            if (not up.videos_count or up.videos_count == 0) and (not up.views_count or up.views_count == 0):
                both_zero += 1
            
            print(f"  最后抓取时间: {up.last_fetch_at or '(未抓取)'}")
            print(f"  抓取错误: {up.fetch_error or '(无错误)'}")
            print()
        
        # 总结
        print("=" * 80)
        print("统计总结")
        print("=" * 80)
        print(f"总UP主数: {len(ups)}")
        print(f"videos_count 为0或空: {zero_videos_count} 个")
        print(f"views_count 为0或空: {zero_views_count} 个")
        print(f"两个字段都为0或空: {both_zero} 个")
        print()
        
        if zero_videos_count > 0 or zero_views_count > 0:
            print("⚠️  发现问题：部分UP主的统计数据字段为空或为0")
            print("\n可能的原因：")
            print("1. B站API无法获取统计数据（get_user_stat方法不可用）")
            print("2. 从视频列表计算时，只获取了部分视频（不完整）")
            print("3. API调用失败，fallback方法也无法获取完整数据")
            print("4. 数据抓取时API返回的user_stat为空或字段为0")
            print("\n建议：")
            print("1. 检查最近的数据抓取日志")
            print("2. 尝试重新抓取数据")
            print("3. 如果API无法获取，可以从视频表计算并更新")
        else:
            print("✅ 所有UP主的统计数据字段都有数据")
        
    finally:
        session.close()

if __name__ == '__main__':
    check_stats_fields()
