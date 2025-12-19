#!/bin/bash
# 验证播放量更新结果

echo "=== 验证播放量更新结果 ==="
echo ""

# 1. 检查关键视频的播放量
echo "1. 检查关键视频播放量（逐际动力的最新5个视频）"
echo "=" * 80
bash scripts/check_bilibili_play_counts.sh

echo ""
echo "2. 检查API返回的数据"
echo "=" * 80
bash scripts/check_api_vs_database.sh

echo ""
echo "3. 清除API缓存（如果需要）"
echo "   访问: http://localhost:5001/api/bilibili/all?force=1"
echo "   这会清除缓存并返回最新数据"

