#!/bin/bash
# 检查B站数据不一致问题

echo "=========================================="
echo "B站数据不一致问题检查"
echo "=========================================="
echo ""

cd /srv/EmbodiedPulse2026
source venv/bin/activate

echo "【1. 检查数据库中BV1L8qEBKEFW的所有记录】"
echo "----------------------------------------"
python3 << 'PYEOF'
from bilibili_models import get_bilibili_session, BilibiliVideo
session = get_bilibili_session()

# 检查BV1L8qEBKEFW有多少条记录
videos = session.query(BilibiliVideo).filter_by(bvid='BV1L8qEBKEFW').all()
print(f"BV1L8qEBKEFW的记录数: {len(videos)}")

if len(videos) > 1:
    print(f"\n⚠️  发现 {len(videos)} 条重复记录:")
    for i, v in enumerate(videos, 1):
        print(f"\n记录 {i}:")
        print(f"  - 播放量: {v.play:,}")
        print(f"  - 发布时间: {v.pubdate}")
        print(f"  - 更新时间: {v.updated_at}")
        print(f"  - is_deleted: {v.is_deleted}")
        print(f"  - UID: {v.uid}")
elif len(videos) == 1:
    v = videos[0]
    print(f"\n✅ 只有1条记录:")
    print(f"  - 播放量: {v.play:,}")
    print(f"  - 发布时间: {v.pubdate}")
    print(f"  - 更新时间: {v.updated_at}")
else:
    print("❌ 未找到记录")

session.close()
PYEOF

echo ""
echo "【2. 检查逐际动力的所有视频（按发布时间排序）】"
echo "----------------------------------------"
python3 << 'PYEOF'
from bilibili_models import get_bilibili_session, BilibiliVideo

LIMX_UID = 1172054289
session = get_bilibili_session()

# 获取所有视频，按发布时间倒序
videos = session.query(BilibiliVideo).filter_by(
    uid=LIMX_UID, is_deleted=False
).order_by(BilibiliVideo.pubdate.desc()).limit(10).all()

print(f"逐际动力的最新10个视频:")
for i, v in enumerate(videos, 1):
    print(f"{i}. {v.bvid} - {v.title[:40]}...")
    print(f"   播放量: {v.play:,}, 发布时间: {v.pubdate}, 更新时间: {v.updated_at}")

session.close()
PYEOF

echo ""
echo "【3. 检查API返回的视频列表】"
echo "----------------------------------------"
python3 << 'PYEOF'
from app import app

with app.test_client() as client:
    response = client.get('/api/bilibili/all?force=1')
    data = response.get_json()
    if data and data.get('success'):
        cards = data.get('data', [])
        limx_card = next((c for c in cards if c.get('user_info', {}).get('mid') == 1172054289), None)
        if limx_card:
            videos = limx_card.get('videos', [])
            print(f"API返回的前10个视频:")
            for i, v in enumerate(videos[:10], 1):
                print(f"{i}. {v.get('bvid')} - {v.get('title', '')[:40]}...")
                print(f"   播放量: {v.get('play_raw')}, 发布时间: {v.get('pubdate')}")
        else:
            print("❌ 未找到逐际动力数据")
    else:
        print(f"❌ API返回失败")
PYEOF

echo ""
echo "【4. 检查缓存中的数据】"
echo "----------------------------------------"
python3 << 'PYEOF'
import sys
sys.path.insert(0, '/srv/EmbodiedPulse2026')
import app
from datetime import datetime

with app.bilibili_cache_lock:
    cached_data = app.bilibili_cache.get('all_data')
    cache_expires_at = app.bilibili_cache.get('all_expires_at')
    
    if cached_data:
        print(f"✅ 缓存存在")
        if cache_expires_at:
            expires_time = datetime.fromtimestamp(cache_expires_at)
            now = datetime.now()
            remaining = (expires_time - now).total_seconds()
            print(f"   过期时间: {expires_time}")
            print(f"   剩余时间: {int(remaining)}秒")
        
        cards = cached_data.get('data', [])
        limx_card = next((c for c in cards if c.get('user_info', {}).get('mid') == 1172054289), None)
        if limx_card:
            videos = limx_card.get('videos', [])
            if videos:
                latest = videos[0]
                print(f"\n   缓存中的最新视频:")
                print(f"   BV号: {latest.get('bvid')}")
                print(f"   标题: {latest.get('title', '')[:50]}...")
                print(f"   播放量: {latest.get('play_raw')}")
                print(f"   发布时间: {latest.get('pubdate')}")
    else:
        print("❌ 缓存不存在")
PYEOF

echo ""
echo "【5. 检查是否有重复的BV号】"
echo "----------------------------------------"
python3 << 'PYEOF'
from bilibili_models import get_bilibili_session, BilibiliVideo
from sqlalchemy import func

session = get_bilibili_session()

# 查找重复的BV号
duplicates = session.query(
    BilibiliVideo.bvid,
    func.count(BilibiliVideo.bvid).label('count')
).group_by(BilibiliVideo.bvid).having(func.count(BilibiliVideo.bvid) > 1).all()

if duplicates:
    print(f"⚠️  发现 {len(duplicates)} 个重复的BV号:")
    for bvid, count in duplicates[:10]:  # 只显示前10个
        print(f"  {bvid}: {count} 条记录")
        if bvid == 'BV1L8qEBKEFW':
            # 显示详细信息
            videos = session.query(BilibiliVideo).filter_by(bvid=bvid).all()
            for v in videos:
                print(f"    - 播放量: {v.play:,}, 发布时间: {v.pubdate}, 更新时间: {v.updated_at}")
else:
    print("✅ 没有重复的BV号")

session.close()
PYEOF

echo ""
echo "=========================================="
echo "检查完成"
echo "=========================================="

