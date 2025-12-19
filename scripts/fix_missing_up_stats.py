#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复缺失的UP主统计数据
优先使用 upstat 接口，如果失败则从视频表计算
"""

import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bilibili_models import get_bilibili_session, BilibiliUp, BilibiliVideo
from bilibili_client import BilibiliClient, format_number
from sqlalchemy import func

# 需要修复的企业列表
TARGET_UPS = {
    'Unitree宇树科技': 521974986,
    '云深处科技': 22477177,
    '众擎机器人': 3546728498202679,
    '逐际动力': 1172054289,
    '傅利叶Fourier': 519804427,
    '加速进化机器人': 3546665977907667,
}

def fix_missing_up_stats():
    """修复缺失的UP主统计数据"""
    print("=" * 80)
    print("修复缺失的UP主统计数据")
    print("=" * 80)
    
    session = get_bilibili_session()
    client = BilibiliClient()
    
    try:
        fixed_count = 0
        
        for name, uid in TARGET_UPS.items():
            print(f"\n【{name}】 (UID: {uid})")
            print("-" * 80)
            
            # 获取UP主记录
            up = session.query(BilibiliUp).filter_by(uid=uid).first()
            if not up:
                print(f"  ❌ 数据库中不存在该UP主")
                continue
            
            old_videos_count = up.videos_count
            old_views_count = up.views_count
            
            # 方法1：尝试使用 upstat 接口获取总播放量
            total_views_from_api = None
            likes_from_api = None
            
            try:
                upstat = client._get_upstat(uid)
                if upstat:
                    archive = upstat.get('archive', {})
                    if isinstance(archive, dict):
                        total_views_from_api = archive.get('view', 0)
                        print(f"  ✅ upstat 接口返回总播放量: {total_views_from_api:,}")
                    likes_from_api = upstat.get('likes', 0)
                    if likes_from_api:
                        print(f"  ✅ upstat 接口返回获赞数: {likes_from_api:,}")
            except Exception as e:
                print(f"  ⚠️  upstat 接口调用失败: {e}")
            
            # 方法2：从视频表计算
            video_count = session.query(func.count(BilibiliVideo.bvid)).filter_by(
                uid=uid,
                is_deleted=False
            ).scalar()
            
            total_views_from_db = session.query(func.sum(BilibiliVideo.play)).filter_by(
                uid=uid,
                is_deleted=False
            ).scalar() or 0
            
            print(f"  视频表统计:")
            print(f"    视频数量: {video_count}")
            print(f"    总播放量: {total_views_from_db:,}")
            
            # 选择最佳数据源
            # 优先使用 API 返回的总播放量，如果失败则使用数据库计算的值
            final_views_count = total_views_from_api if total_views_from_api else total_views_from_db
            final_videos_count = video_count  # 视频数量只能从数据库获取
            
            # 更新数据
            if up.videos_count != final_videos_count or up.views_count != final_views_count:
                up.videos_count = final_videos_count
                up.views_count = final_views_count
                up.views_formatted = format_number(final_views_count)
                
                if likes_from_api:
                    up.likes_count = likes_from_api
                    up.likes_formatted = format_number(likes_from_api)
                
                up.updated_at = datetime.now()
                
                print(f"  ✅ 数据已更新:")
                print(f"    视频数量: {old_videos_count} → {final_videos_count}")
                print(f"    总播放量: {old_views_count:,} → {final_views_count:,} ({up.views_formatted})")
                if total_views_from_api:
                    print(f"    数据来源: upstat API")
                else:
                    print(f"    数据来源: 视频表计算")
                
                fixed_count += 1
            else:
                print(f"  ✓  数据已正确，无需更新")
            
            # 延迟避免频繁请求
            time.sleep(1)
        
        # 提交更改
        if fixed_count > 0:
            session.commit()
            print(f"\n✅ 成功修复 {fixed_count} 个UP主的统计数据")
        else:
            print(f"\n✓  所有数据都已正确，无需修复")
        
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
    from datetime import datetime
    fix_missing_up_stats()

