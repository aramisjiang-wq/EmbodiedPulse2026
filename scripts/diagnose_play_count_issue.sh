#!/bin/bash
# 完整诊断播放量显示问题

echo "=========================================="
echo "B站播放量显示问题完整诊断"
echo "=========================================="
echo ""

cd /srv/EmbodiedPulse2026
source venv/bin/activate

echo "【1. 检查数据库数据】"
echo "----------------------------------------"
python3 << 'PYEOF'
from bilibili_models import get_bilibili_session, BilibiliVideo

session = get_bilibili_session()
video = session.query(BilibiliVideo).filter_by(bvid='BV1L8qEBKEFW').first()
if video:
    print(f"✅ 数据库数据:")
    print(f"   播放量(play): {video.play:,}")
    print(f"   格式化(play_formatted): {video.play_formatted}")
    print(f"   更新时间: {video.updated_at}")
else:
    print("❌ 未找到视频")
session.close()
PYEOF

echo ""
echo "【2. 检查API代码是否已修复】"
echo "----------------------------------------"
echo "检查 app.py 第1321行:"
grep -n "format_number(video.play)" /srv/EmbodiedPulse2026/app.py | head -1
if [ $? -eq 0 ]; then
    echo "✅ app.py 已修复"
else
    echo "❌ app.py 未修复，仍使用 play_formatted"
    echo "当前代码:"
    sed -n '1318,1325p' /srv/EmbodiedPulse2026/app.py
fi

echo ""
echo "检查 bilibili_models.py 第153行:"
grep -n "format_number(self.play)" /srv/EmbodiedPulse2026/bilibili_models.py | head -1
if [ $? -eq 0 ]; then
    echo "✅ bilibili_models.py 已修复"
else
    echo "❌ bilibili_models.py 未修复，仍使用 play_formatted"
    echo "当前代码:"
    sed -n '150,160p' /srv/EmbodiedPulse2026/bilibili_models.py
fi

echo ""
echo "【3. 测试API返回数据（用户端）】"
echo "----------------------------------------"
python3 << 'PYEOF'
from app import app

with app.test_client() as client:
    response = client.get('/api/bilibili/all?force=1')
    data = response.get_json()
    if data and data.get('success'):
        cards = data.get('data', [])
        for card in cards:
            if card.get('user_info', {}).get('mid') == 1172054289:
                videos = card.get('videos', [])
                if videos:
                    latest = videos[0]
                    print(f"✅ API返回数据:")
                    print(f"   BV号: {latest.get('bvid')}")
                    print(f"   标题: {latest.get('title', '')[:50]}...")
                    print(f"   播放量(play): {latest.get('play')}")
                    print(f"   播放量原始(play_raw): {latest.get('play_raw')}")
                    break
    else:
        print(f"❌ API返回失败: {data}")
PYEOF

echo ""
echo "【4. 测试API返回数据（管理端）】"
echo "----------------------------------------"
python3 << 'PYEOF'
from bilibili_models import get_bilibili_session, BilibiliVideo

session = get_bilibili_session()
video = session.query(BilibiliVideo).filter_by(bvid='BV1L8qEBKEFW').first()
if video:
    video_dict = video.to_dict()
    print(f"✅ to_dict()返回数据:")
    print(f"   播放量(play): {video_dict.get('play')}")
    print(f"   播放量原始(play_raw): {video_dict.get('play_raw')}")
else:
    print("❌ 未找到视频")
session.close()
PYEOF

echo ""
echo "【5. 检查缓存状态】"
echo "----------------------------------------"
python3 << 'PYEOF'
import sys
sys.path.insert(0, '/srv/EmbodiedPulse2026')
import app
from datetime import datetime

with app.bilibili_cache_lock:
    cached_all = app.bilibili_cache.get('all_data')
    cache_expires_at = app.bilibili_cache.get('all_expires_at')
    
    if cached_all:
        print(f"⚠️  缓存存在")
        if cache_expires_at:
            expires_time = datetime.fromtimestamp(cache_expires_at)
            now = datetime.now()
            remaining = (expires_time - now).total_seconds()
            print(f"   过期时间: {expires_time}")
            print(f"   剩余时间: {int(remaining)}秒")
            
            # 检查缓存中的数据
            cards = cached_all.get('data', [])
            for card in cards:
                if card.get('user_info', {}).get('mid') == 1172054289:
                    videos = card.get('videos', [])
                    if videos:
                        latest = videos[0]
                        print(f"\n   缓存中的数据:")
                        print(f"   播放量(play): {latest.get('play')}")
                        print(f"   播放量原始(play_raw): {latest.get('play_raw')}")
                        break
    else:
        print("✅ 缓存不存在")
PYEOF

echo ""
echo "【6. 检查前端代码】"
echo "----------------------------------------"
echo "检查 templates/bilibili.html:"
if grep -q "playRaw = video.play_raw" /srv/EmbodiedPulse2026/templates/bilibili.html; then
    echo "✅ 前端代码已修复"
    echo "相关代码:"
    grep -A 5 "playRaw = video.play_raw" /srv/EmbodiedPulse2026/templates/bilibili.html | head -6
else
    echo "❌ 前端代码未修复"
fi

echo ""
echo "【7. 检查服务状态】"
echo "----------------------------------------"
systemctl status embodiedpulse --no-pager -l | head -15

echo ""
echo "=========================================="
echo "诊断完成"
echo "=========================================="

