#!/bin/bash
# 检查API返回的数据和数据库中的数据是否一致

echo "=== API vs 数据库数据对比 ==="
echo ""

BASE_URL="${BASE_URL:-http://localhost:5001}"

# 1. 从API获取数据
echo "1. 从API获取数据"
echo "   请求: ${BASE_URL}/api/bilibili/all?force=1"
echo ""

api_response=$(curl -s "${BASE_URL}/api/bilibili/all?force=1")

# 2. 从数据库获取数据
echo "2. 从数据库获取数据"
echo ""

python3 << EOF
import os
import sys
import json
sys.path.insert(0, os.getcwd())

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

from bilibili_models import get_bilibili_session, BilibiliUp, BilibiliVideo
from bilibili_client import format_number, format_timestamp

# 解析API响应
api_data_str = '''${api_response}'''
api_data = json.loads(api_data_str)

# 从数据库获取数据
session = get_bilibili_session()

try:
    # 获取逐际动力的数据
    LIMX_UID = 1172054289
    
    # 从API数据中提取
    api_up_data = None
    if api_data.get('success') and api_data.get('data'):
        for up_data in api_data['data']:
            if up_data.get('user_info', {}).get('mid') == LIMX_UID:
                api_up_data = up_data
                break
    
    # 从数据库获取
    db_up = session.query(BilibiliUp).filter_by(uid=LIMX_UID).first()
    
    if api_up_data and db_up:
        print("逐际动力数据对比：")
        print("=" * 80)
        
        # UP主信息对比
        api_name = api_up_data.get('user_info', {}).get('name', '')
        db_name = db_up.name
        print(f"UP主名称: API={api_name}, DB={db_name}, {'✅' if api_name == db_name else '❌'}")
        
        # 视频数量对比
        api_videos = api_up_data.get('videos', [])
        api_video_count = len(api_videos)
        db_video_count = session.query(BilibiliVideo).filter_by(
            uid=LIMX_UID, is_deleted=False
        ).count()
        print(f"视频数量: API={api_video_count}, DB={db_video_count}, {'✅' if api_video_count == db_video_count else '❌'}")
        
        # 播放量对比（前3个视频）
        print("\n前3个视频播放量对比：")
        db_videos = session.query(BilibiliVideo).filter_by(
            uid=LIMX_UID, is_deleted=False
        ).order_by(BilibiliVideo.pubdate_raw.desc()).limit(3).all()
        
        for i, db_video in enumerate(db_videos):
            if i < len(api_videos):
                api_video = api_videos[i]
                api_play = api_video.get('play_raw', 0)
                db_play = db_video.play or 0
                
                match = "✅" if api_play == db_play else "❌"
                print(f"  {db_video.bvid}: API={api_play:,}, DB={db_play:,}, {match}")
                if api_play != db_play:
                    print(f"    差异: {abs(api_play - db_play):,}")
    else:
        print("❌ 无法获取数据")
        if not api_up_data:
            print("   API数据中未找到逐际动力")
        if not db_up:
            print("   数据库中未找到逐际动力")
    
finally:
    session.close()
EOF

