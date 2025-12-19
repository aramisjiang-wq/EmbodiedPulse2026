#!/bin/bash
# 在服务器上检查视频播放量的脚本
# 使用方法：将此脚本上传到服务器，或通过SSH在服务器上直接运行

echo "=========================================="
echo "检查服务器视频播放量"
echo "=========================================="
echo ""

# 检查是否在服务器上（检查/srv目录是否存在）
if [ ! -d "/srv" ]; then
    echo "⚠️  警告：这似乎不是服务器环境"
    echo "   请通过SSH连接到服务器后运行此脚本"
    echo ""
    echo "   使用方法："
    echo "   ssh your-user@your-server"
    echo "   cd /srv/EmbodiedPulse2026"
    echo "   bash scripts/check_video_on_server.sh"
    echo ""
    exit 1
fi

APP_DIR="/srv/EmbodiedPulse2026"

if [ ! -d "$APP_DIR" ]; then
    echo "❌ 应用目录不存在: $APP_DIR"
    echo "   请确认应用目录路径"
    exit 1
fi

cd "$APP_DIR"

echo "应用目录: $APP_DIR"
echo ""

# 检查虚拟环境
if [ ! -f "venv/bin/activate" ]; then
    echo "❌ 虚拟环境不存在"
    exit 1
fi

echo "激活虚拟环境..."
source venv/bin/activate

echo ""
echo "=========================================="
echo "检查目标视频数据"
echo "=========================================="
echo ""

python3 << 'PYTHON_EOF'
import os
import sys
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

print("=" * 80)
print("服务器视频数据检查")
print("=" * 80)

try:
    from bilibili_models import get_bilibili_session, BilibiliVideo
    
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
        
        print("\n" + "=" * 80)
        if video.play == 5530:
            print("⚠️  播放量是5530，需要更新！")
            print("\n建议运行以下命令更新:")
            print("  python3 scripts/update_video_play_counts.py --uids 1172054289 --force")
        elif video.play == 162712:
            print("✅ 播放量已更新为162,712")
        else:
            print(f"当前播放量: {video.play:,}")
            print(f"如果前端显示5530，可能需要:")
            print("  1. 清除后端缓存")
            print("  2. 重启服务")
            print("  3. 检查前端是否使用了缓存")
    else:
        print(f"\n❌ 未找到视频 {bvid}")
        print("可能需要先抓取该视频:")
        print("  python3 scripts/fetch_single_video.py BV1L8qEBKEFW --uid 1172054289")
    
    # 检查逐际动力的最新视频
    print("\n" + "=" * 80)
    print("逐际动力最新5个视频:")
    print("=" * 80)
    
    uid = 1172054289
    latest_videos = session.query(BilibiliVideo).filter_by(
        uid=uid, is_deleted=False
    ).order_by(BilibiliVideo.pubdate_raw.desc()).limit(5).all()
    
    for i, v in enumerate(latest_videos, 1):
        print(f"\n{i}. {v.bvid}")
        print(f"   标题: {v.title[:60]}...")
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

