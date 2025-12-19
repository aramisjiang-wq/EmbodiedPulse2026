#!/bin/bash
# B站数据完整性检查脚本

echo "=== B站数据完整性检查 ==="
echo ""

python3 << EOF
import os
import sys
sys.path.insert(0, os.getcwd())

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

from bilibili_models import get_bilibili_session, BilibiliUp, BilibiliVideo
from datetime import datetime, timedelta
from sqlalchemy import func

session = get_bilibili_session()

try:
    # 1. 检查UP主数据
    print("1. UP主数据检查")
    ups = session.query(BilibiliUp).filter_by(is_active=True).all()
    print(f"   活跃UP主数量: {len(ups)}")
    
    for up in ups[:5]:  # 只显示前5个
        video_count = session.query(func.count(BilibiliVideo.bvid)).filter_by(
            uid=up.uid, is_deleted=False
        ).scalar()
        total_views = session.query(func.sum(BilibiliVideo.play)).filter_by(
            uid=up.uid, is_deleted=False
        ).scalar() or 0
        
        print(f"   - {up.name} (UID: {up.uid})")
        print(f"     视频数: {video_count} (数据库: {up.videos_count})")
        print(f"     总播放量: {total_views:,} (数据库: {up.views_count:,})")
        print(f"     最后更新: {up.last_fetch_at}")
    
    # 2. 检查视频数据
    print("\n2. 视频数据检查")
    total_videos = session.query(func.count(BilibiliVideo.bvid)).filter_by(
        is_deleted=False
    ).scalar()
    print(f"   总视频数: {total_videos}")
    
    # 检查最近更新的视频
    recent_videos = session.query(BilibiliVideo).filter_by(
        is_deleted=False
    ).order_by(BilibiliVideo.updated_at.desc()).limit(5).all()
    
    print("\n   最近更新的5个视频:")
    for video in recent_videos:
        print(f"   - {video.bvid}: {video.title[:40]}")
        print(f"     播放量: {video.play:,} | 更新时间: {video.updated_at}")
    
    # 3. 检查数据关联
    print("\n3. 数据关联检查")
    orphan_videos = session.query(BilibiliVideo).filter_by(
        is_deleted=False
    ).outerjoin(BilibiliUp, BilibiliVideo.uid == BilibiliUp.uid).filter(
        BilibiliUp.uid == None
    ).count()
    
    print(f"   孤立视频数（没有对应UP主）: {orphan_videos}")
    
    # 4. 检查数据新鲜度
    print("\n4. 数据新鲜度检查")
    now = datetime.now()
    one_day_ago = now - timedelta(days=1)
    
    recent_updates = session.query(func.count(BilibiliVideo.bvid)).filter(
        BilibiliVideo.updated_at >= one_day_ago,
        BilibiliVideo.is_deleted == False
    ).scalar()
    
    print(f"   24小时内更新的视频数: {recent_updates}")
    
    # 5. 检查特定视频的播放量
    print("\n5. 检查特定视频播放量（示例）")
    sample_videos = session.query(BilibiliVideo).filter_by(
        is_deleted=False
    ).order_by(BilibiliVideo.pubdate_raw.desc()).limit(3).all()
    
    for video in sample_videos:
        print(f"   - {video.bvid}: {video.title[:30]}")
        print(f"     播放量: {video.play:,} | 发布时间: {video.pubdate}")
        print(f"     更新时间: {video.updated_at}")
    
finally:
    session.close()
EOF

