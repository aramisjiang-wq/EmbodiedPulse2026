#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合修复B站数据问题
1. 修复缺失的UP主统计数据
2. 更新视频播放量
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bilibili_models import get_bilibili_session, BilibiliUp, BilibiliVideo
from bilibili_client import BilibiliClient, format_number
from sqlalchemy import func
from datetime import datetime

def comprehensive_fix():
    """综合修复B站数据"""
    print("=" * 80)
    print("综合修复B站数据")
    print("=" * 80)
    
    session = get_bilibili_session()
    client = BilibiliClient()
    
    try:
        # 获取所有活跃的UP主
        ups = session.query(BilibiliUp).filter_by(is_active=True).all()
        print(f"\n找到 {len(ups)} 个活跃UP主\n")
        
        fixed_stats_count = 0
        fixed_videos_count = 0
        
        for up in ups:
            print(f"【{up.name}】 (UID: {up.uid})")
            print("-" * 80)
            
            # 1. 修复UP主统计数据
            old_videos_count = up.videos_count
            old_views_count = up.views_count
            
            # 从视频表计算实际数据
            video_count = session.query(func.count(BilibiliVideo.bvid)).filter_by(
                uid=up.uid, is_deleted=False
            ).scalar()
            
            total_views_from_db = session.query(func.sum(BilibiliVideo.play)).filter_by(
                uid=up.uid, is_deleted=False
            ).scalar() or 0
            
            # 尝试使用 upstat 接口获取总播放量
            total_views_from_api = None
            try:
                upstat = client._get_upstat(up.uid)
                if upstat:
                    archive = upstat.get('archive', {})
                    if isinstance(archive, dict):
                        total_views_from_api = archive.get('view', 0)
            except Exception as e:
                pass
            
            # 选择最佳数据源
            final_views_count = total_views_from_api if total_views_from_api else total_views_from_db
            final_videos_count = video_count
            
            # 更新统计数据（如果数据缺失或不一致）
            needs_fix = False
            if up.videos_count == 0 and final_videos_count > 0:
                up.videos_count = final_videos_count
                needs_fix = True
                print(f"  ✅ 修复视频数量: 0 → {final_videos_count}")
            
            if up.views_count == 0 and final_views_count > 0:
                up.views_count = final_views_count
                up.views_formatted = format_number(final_views_count)
                needs_fix = True
                print(f"  ✅ 修复总播放量: 0 → {final_views_count:,} ({up.views_formatted})")
            
            if needs_fix:
                up.updated_at = datetime.now()
                fixed_stats_count += 1
            else:
                print(f"  ✓  统计数据已正确")
            
            # 2. 检查视频播放量是否需要更新
            # 获取最近7天未更新的视频
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=7)
            stale_videos = session.query(BilibiliVideo).filter(
                BilibiliVideo.uid == up.uid,
                BilibiliVideo.is_deleted == False,
                (BilibiliVideo.updated_at < cutoff_date) | (BilibiliVideo.updated_at.is_(None))
            ).limit(10).all()  # 每次只更新10个，避免触发风控
            
            if stale_videos:
                print(f"  ⚠️  发现 {len(stale_videos)} 个视频需要更新播放量（本次跳过，请使用 update_video_play_counts.py）")
                fixed_videos_count += len(stale_videos)
            
            print()
        
        # 提交更改
        if fixed_stats_count > 0:
            session.commit()
            print(f"✅ 成功修复 {fixed_stats_count} 个UP主的统计数据")
        else:
            print(f"✓  所有统计数据都已正确")
        
        if fixed_videos_count > 0:
            print(f"⚠️  发现 {fixed_videos_count} 个视频需要更新播放量")
            print(f"   请运行: python3 scripts/update_video_play_counts.py")
        
        print("\n" + "=" * 80)
        print("修复完成")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()

if __name__ == '__main__':
    comprehensive_fix()

