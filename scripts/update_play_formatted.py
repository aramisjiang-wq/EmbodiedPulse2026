#!/usr/bin/env python3
"""
更新数据库中所有视频的play_formatted字段
确保格式化字段与原始播放量一致
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bilibili_models import get_bilibili_session, BilibiliVideo
from bilibili_client import format_number

def update_play_formatted():
    """更新所有视频的play_formatted字段"""
    session = get_bilibili_session()
    
    try:
        # 获取所有视频
        videos = session.query(BilibiliVideo).filter_by(is_deleted=False).all()
        total = len(videos)
        updated = 0
        skipped = 0
        
        print(f"共找到 {total} 个视频")
        print("-" * 80)
        
        for video in videos:
            if not video.play:
                skipped += 1
                continue
            
            # 计算期望的格式化值
            expected_formatted = format_number(video.play)
            
            # 如果格式化值不一致，则更新
            if video.play_formatted != expected_formatted:
                old_formatted = video.play_formatted or 'None'
                video.play_formatted = expected_formatted
                updated += 1
                
                if updated <= 10:  # 只显示前10个更新
                    print(f"✅ {video.bvid[:12]}... 播放量: {video.play:,}")
                    print(f"   格式化: {old_formatted} → {expected_formatted}")
        
        session.commit()
        
        print("-" * 80)
        print(f"更新完成: {updated} 个视频已更新, {skipped} 个跳过（播放量为0）")
        
    except Exception as e:
        session.rollback()
        print(f"❌ 更新失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == '__main__':
    update_play_formatted()

