#!/bin/bash
# 在服务器上更新视频播放量

set -e

# 服务器配置（请根据实际情况修改）
SERVER_HOST="${SERVER_HOST:-essay.gradmotion.com}"
SERVER_USER="${SERVER_USER:-root}"
APP_DIR="${APP_DIR:-/srv/EmbodiedPulse2026}"

echo "=========================================="
echo "在服务器上更新视频播放量"
echo "=========================================="
echo ""
echo "服务器: ${SERVER_USER}@${SERVER_HOST}"
echo "应用目录: ${APP_DIR}"
echo ""

# 通过SSH执行更新
ssh ${SERVER_USER}@${SERVER_HOST} << EOF
cd ${APP_DIR}

echo "=========================================="
echo "1. 激活虚拟环境"
echo "=========================================="
source venv/bin/activate 2>/dev/null || {
    echo "❌ 虚拟环境不存在或激活失败"
    exit 1
}

echo "✅ 虚拟环境已激活"

echo ""
echo "=========================================="
echo "2. 更新逐际动力的视频播放量"
echo "=========================================="

python3 scripts/update_video_play_counts.py --uids 1172054289 --force

echo ""
echo "=========================================="
echo "3. 检查更新结果"
echo "=========================================="

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
        print(f"✅ 目标视频更新后:")
        print(f"BV号: {video.bvid}")
        print(f"标题: {video.title}")
        print(f"播放量: {video.play:,} ({video.play_formatted})")
        print(f"更新时间: {video.updated_at}")
    else:
        print(f"❌ 未找到视频 {bvid}")
    
    session.close()
    
except Exception as e:
    print(f"❌ 检查失败: {e}")
    import traceback
    traceback.print_exc()

PYTHON_EOF

echo ""
echo "=========================================="
echo "更新完成"
echo "=========================================="

EOF

echo ""
echo "✅ 服务器更新完成"

