#!/bin/bash
# 更新所有视频的播放量数据

echo "=== 更新所有视频播放量 ==="
echo ""

cd /srv/EmbodiedPulse2026

# 检查是否有专门的播放量更新脚本
if [ -f "scripts/update_video_play_counts.py" ]; then
    echo "使用专门的播放量更新脚本..."
    python3 scripts/update_video_play_counts.py --force-update
else
    echo "使用fetch_bilibili_data.py更新数据..."
    # 更新所有UP主的数据
    python3 fetch_bilibili_data.py --fetch-all
fi

echo ""
echo "✅ 播放量更新完成"
echo ""
echo "验证更新结果："
bash scripts/check_bilibili_play_counts.sh

