#!/bin/bash
# 全面诊断脚本：论文、视频、登录验证

set -e

APP_DIR="/srv/EmbodiedPulse2026"

echo "============================================================"
echo "全面诊断：论文数据、视频数据、登录验证"
echo "============================================================"
echo ""

cd "$APP_DIR"

# 1. 检查论文数据
echo "============================================================"
echo "1. 论文数据诊断"
echo "============================================================"
echo ""

if [ -d "venv" ]; then
    venv/bin/python3 scripts/diagnose_data_issues.py 2>&1 | head -100
elif [ -d ".venv" ]; then
    .venv/bin/python3 scripts/diagnose_data_issues.py 2>&1 | head -100
else
    python3 scripts/diagnose_data_issues.py 2>&1 | head -100
fi

echo ""
echo "============================================================"
echo "2. 检查定时任务状态"
echo "============================================================"
echo ""

# 检查环境变量
echo "📅 环境变量配置:"
grep -E "AUTO_FETCH_ENABLED|AUTO_FETCH_SCHEDULE|AUTO_FETCH_BILIBILI_SCHEDULE" .env || echo "⚠️  未找到.env文件或相关配置"

echo ""
echo "📅 服务状态:"
systemctl is-active embodiedpulse && echo "✅ 服务运行中" || echo "❌ 服务未运行"

echo ""
echo "📅 最近50条日志（包含定时任务）:"
journalctl -u embodiedpulse -n 50 --no-pager | grep -E "定时|scheduled|fetch|抓取" || echo "⚠️  未找到相关日志"

echo ""
echo "============================================================"
echo "3. 检查视频数据完整性"
echo "============================================================"
echo ""

if [ -d "venv" ]; then
    venv/bin/python3 scripts/check_bilibili_data_integrity.py 2>&1 | head -150
elif [ -d ".venv" ]; then
    .venv/bin/python3 scripts/check_bilibili_data_integrity.py 2>&1 | head -150
else
    python3 scripts/check_bilibili_data_integrity.py 2>&1 | head -150
fi

echo ""
echo "============================================================"
echo "4. 检查登录验证配置"
echo "============================================================"
echo ""

echo "📋 检查 user_menu.js 是否在所有页面加载:"
grep -r "user_menu.js" templates/*.html | head -10 || echo "⚠️  未找到 user_menu.js 引用"

echo ""
echo "📋 检查 publicPages 白名单:"
grep -A 2 "publicPages" static/js/user_menu.js | head -5

echo ""
echo "============================================================"
echo "诊断完成"
echo "============================================================"

