#!/bin/bash
# 简化版：检查服务器上的视频数据
# 使用方法: ./scripts/check_server_video_simple.sh [服务器地址] [用户名]

set -e

SERVER_USER="${2:-root}"
SERVER_HOST="${1:-essay.gradmotion.com}"
APP_DIR="/srv/EmbodiedPulse2026"

echo "=========================================="
echo "检查服务器视频数据"
echo "服务器: ${SERVER_USER}@${SERVER_HOST}"
echo "=========================================="
echo ""

# 通过SSH执行检查
ssh ${SERVER_USER}@${SERVER_HOST} << EOF
cd ${APP_DIR}

echo "1. 激活虚拟环境..."
source venv/bin/activate 2>/dev/null || {
    echo "❌ 虚拟环境不存在"
    exit 1
}

echo "2. 检查目标视频数据..."
python3 << 'PYTHON_EOF'
import os
from dotenv import load_dotenv

load_dotenv()

try:
    from bilibili_models import get_bilibili_session, BilibiliVideo
    
    session = get_bilibili_session()
    
    # 检查目标视频
    bvid = 'BV1L8qEBKEFW'
    video = session.query(BilibiliVideo).filter_by(bvid=bvid).first()
    
    if video:
        print(f"\n✅ 找到视频:")
        print(f"BV号: {video.bvid}")
        print(f"标题: {video.title}")
        print(f"播放量: {video.play:,}")
        print(f"播放量(格式化): {video.play_formatted}")
        print(f"更新时间: {video.updated_at}")
        
        if video.play == 5530:
            print(f"\n⚠️  播放量是5530，需要更新！")
        elif video.play == 162712:
            print(f"\n✅ 播放量已更新为162,712")
        else:
            print(f"\n当前播放量: {video.play:,}")
    else:
        print(f"\n❌ 未找到视频 {bvid}")
    
    session.close()
    
except Exception as e:
    print(f"❌ 检查失败: {e}")
    import traceback
    traceback.print_exc()

PYTHON_EOF

EOF

echo ""
echo "✅ 检查完成"

