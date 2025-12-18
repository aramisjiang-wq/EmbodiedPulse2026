#!/usr/bin/env python3
"""
检查Bilibili视频表中"逐际动力"的视频数据
"""
import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from dotenv import load_dotenv
load_dotenv(os.path.join(project_root, '.env'))

from bilibili_models import get_bilibili_session, BilibiliUp, BilibiliVideo
from sqlalchemy import func

def main():
    print("=" * 60)
    print("检查Bilibili视频表中'逐际动力'的视频数据")
    print("=" * 60)
    
    session = get_bilibili_session()
    
    # 获取UP主
    up = session.query(BilibiliUp).filter_by(name='逐际动力', is_active=True).first()
    
    if not up:
        print("❌ 未找到UP主")
        session.close()
        return
    
    print(f"\nUP主信息:")
    print(f"  uid: {up.uid}")
    print(f"  name: {up.name}")
    
    # 查询所有视频（包括已删除的）
    all_videos = session.query(BilibiliVideo).filter_by(uid=up.uid).all()
    print(f"\n所有视频（包括已删除）: {len(all_videos)} 条")
    
    # 查询未删除的视频
    active_videos = session.query(BilibiliVideo).filter_by(
        uid=up.uid,
        is_deleted=False
    ).all()
    print(f"未删除的视频: {len(active_videos)} 条")
    
    # 计算统计数据
    video_count = session.query(func.count(BilibiliVideo.bvid)).filter_by(
        uid=up.uid,
        is_deleted=False
    ).scalar()
    
    total_views = session.query(func.sum(BilibiliVideo.play)).filter_by(
        uid=up.uid,
        is_deleted=False
    ).scalar() or 0
    
    print(f"\n计算结果:")
    print(f"  视频数量: {video_count}")
    print(f"  总播放量: {total_views}")
    
    # 显示前5个视频
    if active_videos:
        print(f"\n前5个视频:")
        for i, video in enumerate(active_videos[:5], 1):
            print(f"  {i}. {video.title[:50]}...")
            print(f"     播放量: {video.play}, is_deleted: {video.is_deleted}")
    
    # 检查是否有is_deleted=True的视频
    deleted_videos = session.query(BilibiliVideo).filter_by(
        uid=up.uid,
        is_deleted=True
    ).all()
    if deleted_videos:
        print(f"\n已删除的视频: {len(deleted_videos)} 条")
        print(f"  这些视频不会被计入统计")
    
    session.close()
    
    print("\n" + "=" * 60)
    print("检查完成")
    print("=" * 60)

if __name__ == '__main__':
    main()

