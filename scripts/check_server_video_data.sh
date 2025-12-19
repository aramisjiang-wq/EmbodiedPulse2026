#!/bin/bash
# 检查服务器上的视频数据（特别是目标视频的播放量）

set -e

# 服务器配置（请根据实际情况修改）
SERVER_HOST="${SERVER_HOST:-essay.gradmotion.com}"
SERVER_USER="${SERVER_USER:-root}"
APP_DIR="${APP_DIR:-/srv/EmbodiedPulse2026}"

echo "=========================================="
echo "检查服务器视频数据"
echo "=========================================="
echo ""
echo "服务器: ${SERVER_USER}@${SERVER_HOST}"
echo "应用目录: ${APP_DIR}"
echo ""

# 通过SSH执行检查
ssh ${SERVER_USER}@${SERVER_HOST} << EOF
cd ${APP_DIR}

echo "=========================================="
echo "1. 检查数据库配置"
echo "=========================================="

if [ -f ".env" ]; then
    echo "📄 .env文件中的数据库配置:"
    grep -E "^DATABASE_URL=|^BILIBILI_DATABASE_URL=" .env | head -2 || echo "未找到数据库配置"
else
    echo "❌ .env文件不存在"
fi

echo ""
echo "=========================================="
echo "2. 检查数据库文件"
echo "=========================================="

if [ -f "bilibili.db" ]; then
    BILIBILI_SIZE=\$(du -h bilibili.db | cut -f1)
    echo "✅ bilibili.db 存在 (大小: \$BILIBILI_SIZE)"
else
    echo "❌ bilibili.db 不存在"
fi

echo ""
echo "=========================================="
echo "3. 检查目标视频数据"
echo "=========================================="

source venv/bin/activate 2>/dev/null || echo "⚠️  虚拟环境不存在或激活失败"

python3 << 'PYTHON_EOF'
import os
import sys
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

print("=" * 80)
print("服务器上的视频数据检查")
print("=" * 80)

try:
    from bilibili_models import get_bilibili_session, BilibiliVideo, BilibiliUp
    
    session = get_bilibili_session()
    
    # 检查目标视频
    bvid = 'BV1L8qEBKEFW'
    video = session.query(BilibiliVideo).filter_by(bvid=bvid).first()
    
    if video:
        print(f"\n✅ 找到目标视频:")
        print(f"BV号: {video.bvid}")
        print(f"标题: {video.title}")
        print(f"播放量: {video.play:,}")
        print(f"播放量(格式化): {video.play_formatted}")
        print(f"评论数: {video.video_review:,}")
        print(f"收藏数: {video.favorites:,}")
        print(f"更新时间: {video.updated_at}")
        print(f"发布时间: {video.pubdate}")
        
        # 检查是否是5530
        if video.play == 5530:
            print(f"\n⚠️  播放量确实是5530，需要更新！")
        elif video.play == 162712:
            print(f"\n✅ 播放量已更新为162,712")
        else:
            print(f"\n⚠️  播放量是 {video.play:,}，不是期望的值")
    else:
        print(f"\n❌ 未找到BV号为 {bvid} 的视频")
    
    # 检查逐际动力的最新视频
    print(f"\n" + "=" * 80)
    print("逐际动力最新5个视频:")
    print("=" * 80)
    
    uid = 1172054289
    latest_videos = session.query(BilibiliVideo).filter_by(
        uid=uid, is_deleted=False
    ).order_by(BilibiliVideo.pubdate_raw.desc()).limit(5).all()
    
    for i, v in enumerate(latest_videos, 1):
        print(f"\n{i}. {v.bvid}")
        print(f"   标题: {v.title[:50]}...")
        print(f"   播放量: {v.play:,} ({v.play_formatted})")
        print(f"   更新时间: {v.updated_at}")
    
    session.close()
    
except Exception as e:
    print(f"❌ 检查失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

PYTHON_EOF

echo ""
echo "=========================================="
echo "检查完成"
echo "=========================================="

EOF

echo ""
echo "✅ 远程检查完成"

