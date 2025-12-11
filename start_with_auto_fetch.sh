#!/bin/bash

# Robotics ArXiv Daily - 启动脚本（带自动定时抓取）
# 使用方法: ./start_with_auto_fetch.sh

cd "$(dirname "$0")"

# 启用自动定时抓取
export AUTO_FETCH_ENABLED=true

# 设置抓取时间（每小时执行一次）
# Cron 格式: 分钟 小时 日 月 星期
# 多个时间用分号分隔，如: "0 * * * *"
# 示例:
#   0 * * * *              - 每小时整点执行（默认）
#   0 2 * * *;0 14 * * *   - 每天2点和14点
#   0 8 * * *;0 20 * * *  - 每天8点和20点
export AUTO_FETCH_SCHEDULE="0 * * * *"

# 设置每次抓取数量（默认100篇）
export AUTO_FETCH_MAX_RESULTS=100

echo "===================================================="
echo "Robotics ArXiv Daily - 自动抓取模式"
echo "===================================================="
echo "✅ 自动抓取: 已启用"
echo "⏰ 抓取时间: 每小时整点执行（论文和新闻）"
echo "📊 抓取数量: 每类100篇"
echo "===================================================="
echo ""

# 启动服务器
python3 app.py

