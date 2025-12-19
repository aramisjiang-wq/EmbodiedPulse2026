#!/bin/bash
# 检查服务器上的脚本并更新代码
# 使用方法：在服务器上运行此脚本

echo "=========================================="
echo "检查并更新服务器代码"
echo "=========================================="
echo ""

APP_DIR="/srv/EmbodiedPulse2026"
cd "$APP_DIR"

echo "1. 检查Git状态..."
git status

echo ""
echo "2. 检查关键脚本是否存在..."
SCRIPTS=(
    "scripts/fetch_single_video.py"
    "scripts/update_video_play_counts.py"
    "fetch_bilibili_data.py"
    "bilibili_models.py"
    "bilibili_client.py"
)

for script in "${SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        echo "✅ $script 存在"
    else
        echo "❌ $script 不存在"
    fi
done

echo ""
echo "3. 拉取最新代码..."
git fetch origin
git pull origin main

echo ""
echo "4. 再次检查脚本..."
for script in "${SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        echo "✅ $script 存在"
        # 显示文件大小和修改时间
        ls -lh "$script" | awk '{print "   大小: " $5 ", 修改时间: " $6 " " $7 " " $8}'
    else
        echo "❌ $script 仍然不存在"
    fi
done

echo ""
echo "=========================================="
echo "检查完成"
echo "=========================================="

