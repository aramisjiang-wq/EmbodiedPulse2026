#!/bin/bash
# 启动Flask服务器并启用定时任务

cd "$(dirname "$0")"

echo "=========================================="
echo "启动Embodied Pulse服务器（启用定时任务）"
echo "=========================================="
echo ""

# 设置环境变量
export AUTO_FETCH_ENABLED=true
export AUTO_FETCH_SCHEDULE="0 * * * *"  # 每小时整点执行
export AUTO_FETCH_MAX_RESULTS=100
export PORT=5001

echo "📋 配置信息："
echo "   - 自动抓取: 启用"
echo "   - 抓取时间: 每小时整点"
echo "   - 新闻更新: 每小时自动更新"
echo "   - 招聘更新: 每小时自动更新"
echo "   - 端口: $PORT"
echo ""

# 启动服务器
python3 app.py

