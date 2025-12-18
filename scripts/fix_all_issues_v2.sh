#!/bin/bash
# 修复三大问题（V2版本）

set -e

APP_DIR="/srv/EmbodiedPulse2026"

echo "============================================================"
echo "修复三大问题（V2版本）"
echo "============================================================"
echo ""

cd "$APP_DIR"

# 1. 诊断论文日期问题
echo "============================================================"
echo "1. 诊断论文日期问题"
echo "============================================================"
echo ""

if [ -d "venv" ]; then
    venv/bin/python3 scripts/diagnose_paper_date_issue.py 2>&1 | head -50
elif [ -d ".venv" ]; then
    .venv/bin/python3 scripts/diagnose_paper_date_issue.py 2>&1 | head -50
else
    python3 scripts/diagnose_paper_date_issue.py 2>&1 | head -50
fi

echo ""
echo "============================================================"
echo "2. 修复论文日期逻辑（使用submitted日期）"
echo "============================================================"
echo ""

# 修复daily_arxiv.py中的日期逻辑
if grep -q "publish_time.*result.published.date()" daily_arxiv.py; then
    echo "发现使用published.date()，正在修复为submitted.date()..."
    sed -i 's/publish_time\s*=\s*result\.published\.date()/publish_time = result.submitted.date() if hasattr(result, "submitted") else result.published.date()/g' daily_arxiv.py
    echo "✅ 已修复日期逻辑"
else
    echo "✅ 日期逻辑已正确（使用submitted日期）"
fi

echo ""
echo "============================================================"
echo "3. 从SQLite迁移Bilibili数据"
echo "============================================================"
echo ""

# 检查SQLite数据库是否存在
if [ -f "bilibili.db" ]; then
    echo "✅ 找到SQLite数据库: bilibili.db"
    
    if [ -d "venv" ]; then
        venv/bin/python3 scripts/migrate_bilibili_from_sqlite.py
    elif [ -d ".venv" ]; then
        .venv/bin/python3 scripts/migrate_bilibili_from_sqlite.py
    else
        python3 scripts/migrate_bilibili_from_sqlite.py
    fi
else
    echo "⚠️  SQLite数据库不存在: bilibili.db"
    echo "   跳过迁移，直接通过API更新数据"
fi

echo ""
echo "============================================================"
echo "4. 通过API更新Bilibili数据"
echo "============================================================"
echo ""

# 创建临时脚本更新数据
cat > /tmp/update_bilibili_data.py << 'EOF'
#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, '/srv/EmbodiedPulse2026')

from fetch_bilibili_data import fetch_all_bilibili_data

print("开始更新Bilibili数据...")
fetch_all_bilibili_data(video_count=100, delay_between_requests=3.0)
print("✅ 更新完成")
EOF

if [ -d "venv" ]; then
    venv/bin/python3 /tmp/update_bilibili_data.py
elif [ -d ".venv" ]; then
    .venv/bin/python3 /tmp/update_bilibili_data.py
else
    python3 /tmp/update_bilibili_data.py
fi

rm /tmp/update_bilibili_data.py

echo ""
echo "============================================================"
echo "5. 修复登录验证（添加版本号）"
echo "============================================================"
echo ""

VERSION=$(date +%s)
sed -i "s|user_menu.js|user_menu.js?v=${VERSION}|g" templates/index.html
sed -i "s|user_menu.js|user_menu.js?v=${VERSION}|g" templates/bilibili.html
echo "✅ 已为user_menu.js添加版本号: ${VERSION}"

echo ""
echo "============================================================"
echo "6. 重新抓取12月17日的论文（使用修复后的日期逻辑）"
echo "============================================================"
echo ""

if [ -d "venv" ]; then
    venv/bin/python3 scripts/fix_paper_fetch_dec17.py
elif [ -d ".venv" ]; then
    .venv/bin/python3 scripts/fix_paper_fetch_dec17.py
else
    python3 scripts/fix_paper_fetch_dec17.py
fi

echo ""
echo "============================================================"
echo "7. 重启服务"
echo "============================================================"
echo ""

systemctl restart embodiedpulse
sleep 3

if systemctl is-active --quiet embodiedpulse; then
    echo "✅ 服务重启成功"
else
    echo "❌ 服务启动失败"
    echo "查看日志: journalctl -u embodiedpulse -n 50"
    exit 1
fi

echo ""
echo "============================================================"
echo "✅ 修复完成！"
echo "============================================================"
echo ""
echo "📝 验证步骤:"
echo "  1. 清除浏览器缓存（Ctrl+Shift+R）"
echo "  2. 访问 https://essay.gradmotion.com/ 检查12月17日的论文"
echo "  3. 访问 https://essay.gradmotion.com/bilibili 检查视频数据"
echo "  4. 验证登录验证是否生效"
echo ""

