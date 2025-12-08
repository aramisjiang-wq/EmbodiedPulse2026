#!/bin/bash

# Robotics ArXiv Daily - 启动脚本（带自动定时抓取）
# 使用方法: ./start_with_auto_fetch.sh

cd "$(dirname "$0")"

# 启用自动定时抓取
export AUTO_FETCH_ENABLED=true

# 设置抓取时间（每天凌晨2点）
# Cron 格式: 分钟 小时 日 月 星期
# 示例:
#   0 2 * * *    - 每天凌晨2点
#   0 */12 * * * - 每12小时
#   0 8,20 * * * - 每天8点和20点
export AUTO_FETCH_SCHEDULE="0 2 * * *"

# 设置每次抓取数量（建议5-10，避免API速率限制）
export AUTO_FETCH_MAX_RESULTS=10

echo "===================================================="
echo "Robotics ArXiv Daily - 自动抓取模式"
echo "===================================================="
echo "✅ 自动抓取: 已启用"
echo "⏰ 抓取时间: 每天凌晨2点"
echo "📊 抓取数量: 每类10篇"
echo "===================================================="
echo ""

# 启动服务器
python3 app.py

