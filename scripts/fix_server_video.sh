#!/bin/bash
# 在服务器上修复视频数据的完整脚本
# 使用方法：在服务器上运行此脚本

echo "=========================================="
echo "修复服务器视频数据"
echo "=========================================="
echo ""

APP_DIR="/srv/EmbodiedPulse2026"
cd "$APP_DIR"

source venv/bin/activate

echo "1. 检查逐际动力的所有视频..."
python3 << 'PYTHON_EOF'
import os
from dotenv import load_dotenv

load_dotenv()

from bilibili_models import get_bilibili_session, BilibiliVideo, BilibiliUp

session = get_bilibili_session()

# 检查逐际动力
uid = 1172054289
up = session.query(BilibiliUp).filter_by(uid=uid).first()

if up:
    print(f"✅ 找到UP主: {up.name}")
    print(f"   视频数量: {up.videos_count}")
else:
    print(f"❌ 未找到UP主 {uid}")

# 检查所有视频
videos = session.query(BilibiliVideo).filter_by(
    uid=uid, is_deleted=False
).order_by(BilibiliVideo.pubdate_raw.desc()).limit(10).all()

print(f"\n逐际动力最新10个视频:")
for i, v in enumerate(videos, 1):
    print(f"{i}. {v.bvid} - {v.title[:50]}... - 播放量: {v.play:,}")

# 检查目标视频
bvid = 'BV1L8qEBKEFW'
video = session.query(BilibiliVideo).filter_by(bvid=bvid).first()

if video:
    print(f"\n✅ 找到目标视频 {bvid}")
    print(f"   播放量: {video.play:,}")
else:
    print(f"\n❌ 未找到目标视频 {bvid}")
    print("   需要抓取该视频")

session.close()
PYTHON_EOF

echo ""
echo "2. 抓取目标视频..."
python3 scripts/fetch_single_video.py BV1L8qEBKEFW --uid 1172054289

echo ""
echo "3. 更新逐际动力的所有视频播放量..."
python3 scripts/update_video_play_counts.py --uids 1172054289 --force

echo ""
echo "4. 验证结果..."
python3 << 'PYTHON_EOF'
import os
from dotenv import load_dotenv

load_dotenv()

from bilibili_models import get_bilibili_session, BilibiliVideo

session = get_bilibili_session()

bvid = 'BV1L8qEBKEFW'
video = session.query(BilibiliVideo).filter_by(bvid=bvid).first()

if video:
    print(f"\n✅ 目标视频:")
    print(f"BV号: {video.bvid}")
    print(f"标题: {video.title}")
    print(f"播放量: {video.play:,} ({video.play_formatted})")
    print(f"更新时间: {video.updated_at}")
else:
    print(f"\n❌ 仍然未找到视频 {bvid}")

session.close()
PYTHON_EOF

echo ""
echo "=========================================="
echo "修复完成"
echo "=========================================="
echo ""
echo "建议："
echo "  1. 重启服务: systemctl restart embodiedpulse"
echo "  2. 清除后端缓存（如果使用了缓存）"
echo "  3. 刷新前端页面"

