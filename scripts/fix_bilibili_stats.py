#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复Bilibili UP主统计数据
从视频表重新计算videos_count和views_count
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from bilibili_models import get_bilibili_session, BilibiliUp, BilibiliVideo
from bilibili_client import format_number
from sqlalchemy import func

def fix_up_stats():
    """修复UP主统计数据"""
    print("=" * 60)
    print("修复Bilibili UP主统计数据")
    print("=" * 60)
    
    # 加载环境变量
    env_path = os.path.join(project_root, '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
    
    session = get_bilibili_session()
    
    try:
        # 获取所有活跃的UP主
        ups = session.query(BilibiliUp).filter_by(is_active=True).all()
        print(f"\n找到 {len(ups)} 个活跃UP主\n")
        
        fixed_count = 0
        for up in ups:
            # 从视频表重新计算统计数据
            video_count = session.query(func.count(BilibiliVideo.bvid)).filter_by(
                uid=up.uid,
                is_deleted=False
            ).scalar()
            
            total_views = session.query(func.sum(BilibiliVideo.play)).filter_by(
                uid=up.uid,
                is_deleted=False
            ).scalar() or 0
            
            # 检查是否需要修复
            if up.videos_count != video_count or up.views_count != total_views:
                old_videos_count = up.videos_count
                old_views_count = up.views_count
                
                # 更新统计数据
                up.videos_count = video_count
                up.views_count = total_views
                up.views_formatted = format_number(total_views)
                
                print(f"✅ {up.name} (UID: {up.uid})")
                print(f"   视频数量: {old_videos_count} → {video_count}")
                print(f"   总播放量: {old_views_count} → {total_views} ({up.views_formatted})")
                
                fixed_count += 1
            else:
                print(f"✓  {up.name} (UID: {up.uid}) - 数据已正确，无需修复")
        
        # 提交更改
        if fixed_count > 0:
            session.commit()
            print(f"\n✅ 成功修复 {fixed_count} 个UP主的统计数据")
        else:
            print(f"\n✓ 所有数据都已正确，无需修复")
        
        print("\n" + "=" * 60)
        print("修复完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()


if __name__ == '__main__':
    fix_up_stats()

