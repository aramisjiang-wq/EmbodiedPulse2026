#!/bin/bash
# 检查B站视频播放量是否最新（对比B站实际播放量）

echo "=== B站视频播放量检查 ==="
echo ""

# 检查特定视频的播放量
python3 << EOF
import os
import sys
sys.path.insert(0, os.getcwd())

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

from bilibili_models import get_bilibili_session, BilibiliVideo
from bilibili_client import BilibiliClient
import requests
from datetime import datetime

session = get_bilibili_session()

try:
    # 获取逐际动力的最新视频
    LIMX_UID = 1172054289
    videos = session.query(BilibiliVideo).filter_by(
        uid=LIMX_UID,
        is_deleted=False
    ).order_by(BilibiliVideo.pubdate_raw.desc()).limit(5).all()
    
    print(f"检查逐际动力的最新5个视频播放量：")
    print("=" * 80)
    
    for video in videos:
        print(f"\n视频: {video.bvid}")
        print(f"标题: {video.title[:50]}")
        print(f"数据库播放量: {video.play:,}")
        print(f"数据库更新时间: {video.updated_at}")
        
        # 从B站API获取实际播放量
        try:
            url = "https://api.bilibili.com/x/web-interface/view"
            params = {"bvid": video.bvid}
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.bilibili.com/',
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0:
                    stat = data.get('data', {}).get('stat', {})
                    actual_play = stat.get('view', 0)
                    print(f"B站实际播放量: {actual_play:,}")
                    
                    if actual_play != video.play:
                        diff = actual_play - video.play
                        print(f"⚠️  播放量不一致！差异: {diff:,}")
                    else:
                        print(f"✅ 播放量一致")
                else:
                    print(f"❌ API返回错误: {data.get('message')}")
            else:
                print(f"❌ HTTP错误: {response.status_code}")
        except Exception as e:
            print(f"❌ 获取B站数据失败: {e}")
        
        print("-" * 80)
        
finally:
    session.close()
EOF

