#!/bin/bash
# 更新所有视频的播放量数据

echo "=== 更新所有视频播放量 ==="
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
cd "$PROJECT_DIR"

# 检查是否有专门的播放量更新脚本
if [ -f "scripts/update_video_play_counts.py" ]; then
    echo "✅ 使用专门的播放量更新脚本（直接调用B站API获取每个视频的播放量）"
    echo ""
    python3 scripts/update_video_play_counts.py --force
else
    echo "⚠️  未找到专门的播放量更新脚本，使用fetch_bilibili_data.py更新数据..."
    echo "   注意：这种方式可能无法获取到最新的播放量（受API限制）"
    echo ""
    # 更新所有UP主的数据
    python3 fetch_bilibili_data.py --fetch-all
fi

echo ""
echo "✅ 播放量更新完成"
echo ""
echo "验证更新结果："
bash scripts/check_bilibili_play_counts.sh

