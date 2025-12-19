#!/bin/bash
# 检查数据库中play_formatted字段的值

cd /srv/EmbodiedPulse2026
source venv/bin/activate

echo "【检查BV1L8qEBKEFW的play_formatted字段】"
python3 << 'PYEOF'
from bilibili_models import get_bilibili_session, BilibiliVideo

session = get_bilibili_session()

video = session.query(BilibiliVideo).filter_by(bvid='BV1L8qEBKEFW').first()
if video:
    print(f"BV号: {video.bvid}")
    print(f"播放量(play): {video.play:,}")
    print(f"播放量格式化(play_formatted): {video.play_formatted}")
    print(f"更新时间: {video.updated_at}")
    
    # 检查是否需要更新play_formatted
    if video.play_formatted != f"{video.play / 10000:.1f}万" if video.play >= 10000 else str(video.play):
        print(f"\n⚠️  play_formatted可能需要更新")
        expected = f"{video.play / 10000:.1f}万" if video.play >= 10000 else str(video.play)
        print(f"   当前值: {video.play_formatted}")
        print(f"   期望值: {expected}")
else:
    print("❌ 未找到视频")

session.close()
PYEOF

echo ""
echo "【检查API返回的数据】"
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
            if videos:
                latest = videos[0]
                print(f"API返回的最新视频:")
                print(f"  BV号: {latest.get('bvid')}")
                print(f"  播放量(play): {latest.get('play')}")
                print(f"  播放量原始(play_raw): {latest.get('play_raw')}")
                print(f"  标题: {latest.get('title', '')[:50]}...")
        else:
            print("❌ 未找到逐际动力数据")
    else:
        print(f"❌ API返回失败")
PYEOF

