#!/bin/bash
# 调试API返回的视频列表排序问题

echo "=========================================="
echo "调试API返回的视频列表排序"
echo "=========================================="
echo ""

cd /srv/EmbodiedPulse2026
source venv/bin/activate

echo "【1. 检查数据库中pubdate和pubdate_raw的值】"
echo "----------------------------------------"
python3 << 'PYEOF'
from bilibili_models import get_bilibili_session, BilibiliVideo

LIMX_UID = 1172054289
session = get_bilibili_session()

# 检查最新10个视频的pubdate和pubdate_raw
videos = session.query(BilibiliVideo).filter_by(
    uid=LIMX_UID, is_deleted=False
).order_by(BilibiliVideo.pubdate.desc()).limit(10).all()

print("按pubdate排序（前10个）:")
for i, v in enumerate(videos, 1):
    print(f"{i}. {v.bvid} - 播放量: {v.play:,}")
    print(f"   pubdate: {v.pubdate}")
    print(f"   pubdate_raw: {v.pubdate_raw}")
    if v.pubdate_raw:
        from datetime import datetime
        pubdate_from_raw = datetime.fromtimestamp(v.pubdate_raw)
        print(f"   pubdate_raw转换: {pubdate_from_raw}")
        if v.pubdate and pubdate_from_raw:
            diff = abs((v.pubdate - pubdate_from_raw).total_seconds())
            if diff > 1:
                print(f"   ⚠️  时间不一致！差异: {diff}秒")

print("\n" + "="*60)
print("按pubdate_raw排序（前10个）:")
videos_raw = session.query(BilibiliVideo).filter_by(
    uid=LIMX_UID, is_deleted=False
).order_by(BilibiliVideo.pubdate_raw.desc()).limit(10).all()

for i, v in enumerate(videos_raw, 1):
    print(f"{i}. {v.bvid} - 播放量: {v.play:,}")
    print(f"   pubdate: {v.pubdate}")
    print(f"   pubdate_raw: {v.pubdate_raw}")

session.close()
PYEOF

echo ""
echo "【2. 检查API返回的视频列表】"
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
                print(f"{i}. {v.get('bvid')} - 播放量: {v.get('play_raw')}")
                print(f"   发布时间: {v.get('pubdate')}")
                print(f"   pubdate_raw: {v.get('pubdate_raw')}")
        else:
            print("❌ 未找到逐际动力数据")
    else:
        print(f"❌ API返回失败")
PYEOF

echo ""
echo "=========================================="
echo "检查完成"
echo "=========================================="

