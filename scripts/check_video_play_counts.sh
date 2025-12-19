#!/bin/bash
# 检查视频播放量是否最新

cd /srv/EmbodiedPulse2026 || exit 1

echo "============================================================"
echo "检查视频播放量是否最新"
echo "============================================================"
echo ""

python3 << 'PYEOF'
import sys
sys.path.insert(0, '/srv/EmbodiedPulse2026')
from bilibili_models import get_bilibili_session, BilibiliVideo, BilibiliUp
from datetime import datetime, timedelta

session = get_bilibili_session()

print("【1. 检查逐际动力的最新视频】")
print("=" * 60)

limx_uid = 1172054289
limx_up = session.query(BilibiliUp).filter_by(uid=limx_uid).first()

if limx_up:
    print(f"UP主: {limx_up.name}")
    print(f"最后更新: {limx_up.last_fetch_at}")
    
    # 获取最新5个视频
    videos = session.query(BilibiliVideo).filter_by(
        uid=limx_uid,
        is_deleted=False
    ).order_by(BilibiliVideo.pubdate_raw.desc()).limit(5).all()
    
    print(f"\n最新5个视频:")
    for i, video in enumerate(videos, 1):
        age_hours = (datetime.now() - video.updated_at).total_seconds() / 3600 if video.updated_at else 999
        status = "✅" if age_hours < 24 else "⚠️" if age_hours < 168 else "❌"
        
        print(f"\n{status} {i}. {video.bvid}")
        print(f"   标题: {video.title[:60]}...")
        print(f"   发布时间: {video.pubdate.strftime('%Y-%m-%d %H:%M:%S') if video.pubdate else 'N/A'}")
        print(f"   播放量: {video.play:,} (格式化: {video.play_formatted})")
        print(f"   播放量更新时间: {video.updated_at.strftime('%Y-%m-%d %H:%M:%S') if video.updated_at else '从未更新'}")
        print(f"   播放量更新距离现在: {age_hours:.1f} 小时")
        
        # 如果视频发布时间很近但播放量很低，可能播放量未更新
        if video.pubdate:
            video_age_days = (datetime.now() - video.pubdate).total_seconds() / 86400
            if video_age_days < 7 and video.play < 1000:
                print(f"   ⚠️  视频发布{video_age_days:.1f}天，播放量可能未更新")

print("\n【2. 检查最近更新的视频】")
print("=" * 60)

# 检查最近24小时更新的视频
recent_updated = session.query(BilibiliVideo).filter(
    BilibiliVideo.updated_at >= datetime.now() - timedelta(days=1)
).order_by(BilibiliVideo.updated_at.desc()).limit(10).all()

print(f"最近24小时更新的视频数量: {len(recent_updated)}")
for video in recent_updated[:5]:
    print(f"  {video.bvid}: 播放量={video.play:,}, 更新时间={video.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")

print("\n【3. 检查播放量为0或很低的视频】")
print("=" * 60)

# 检查最近7天发布但播放量很低的视频
seven_days_ago = datetime.now() - timedelta(days=7)
low_play_videos = session.query(BilibiliVideo).filter(
    BilibiliVideo.pubdate >= seven_days_ago,
    BilibiliVideo.play < 1000,
    BilibiliVideo.is_deleted == False
).order_by(BilibiliVideo.pubdate.desc()).limit(10).all()

print(f"最近7天发布但播放量<1000的视频: {len(low_play_videos)}")
for video in low_play_videos[:5]:
    print(f"  {video.bvid}: {video.title[:50]}...")
    print(f"    播放量: {video.play}, 发布时间: {video.pubdate.strftime('%Y-%m-%d') if video.pubdate else 'N/A'}")

session.close()
PYEOF

echo ""
echo "============================================================"
echo "检查完成"
echo "============================================================"
echo ""
echo "如果发现播放量过时，可以执行以下命令更新:"
echo "  python3 scripts/update_video_play_counts.py --uids 1172054289 --force"

