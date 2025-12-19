#!/bin/bash
# 在服务器上更新视频播放量的脚本
# 使用方法：将此脚本上传到服务器，或通过SSH在服务器上直接运行

echo "=========================================="
echo "在服务器上更新视频播放量"
echo "=========================================="
echo ""

# 检查是否在服务器上
if [ ! -d "/srv" ]; then
    echo "⚠️  警告：这似乎不是服务器环境"
    echo "   请通过SSH连接到服务器后运行此脚本"
    exit 1
fi

APP_DIR="/srv/EmbodiedPulse2026"

if [ ! -d "$APP_DIR" ]; then
    echo "❌ 应用目录不存在: $APP_DIR"
    exit 1
fi

cd "$APP_DIR"

if [ ! -f "venv/bin/activate" ]; then
    echo "❌ 虚拟环境不存在"
    exit 1
fi

echo "激活虚拟环境..."
source venv/bin/activate

echo ""
echo "=========================================="
echo "更新逐际动力的视频播放量"
echo "=========================================="
echo ""

# 更新所有逐际动力的视频
python3 scripts/update_video_play_counts.py --uids 1172054289 --force

echo ""
echo "=========================================="
echo "检查更新结果"
echo "=========================================="
echo ""

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
echo ""
echo "建议："
echo "  1. 清除后端缓存（如果使用了缓存）"
echo "  2. 重启服务: systemctl restart embodiedpulse"
echo "  3. 刷新前端页面查看最新数据"

