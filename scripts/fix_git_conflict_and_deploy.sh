#!/bin/bash
# 解决Git冲突并部署最新代码

set -e

echo "=========================================="
echo "解决Git冲突并部署最新代码"
echo "=========================================="
echo ""

cd /srv/EmbodiedPulse2026 || {
    echo "❌ 错误: 项目目录不存在"
    exit 1
}

# 1. 检查本地修改
echo "1️⃣  检查本地修改..."
if [ -n "$(git status --porcelain)" ]; then
    echo "发现本地修改，正在备份..."
    git stash save "本地修改备份 $(date +%Y%m%d_%H%M%S)"
    echo "✅ 本地修改已备份到stash"
else
    echo "✅ 没有本地修改"
fi
echo ""

# 2. 拉取最新代码
echo "2️⃣  拉取最新代码..."
git pull origin main
echo "✅ 代码已更新"
echo ""

# 3. 重启服务
echo "3️⃣  重启服务..."
sudo systemctl restart embodiedpulse

# 等待服务启动
echo "等待服务启动..."
sleep 3

# 检查服务状态
if systemctl is-active --quiet embodiedpulse; then
    echo "✅ Flask 服务运行正常"
else
    echo "❌ Flask 服务启动失败"
    echo "查看错误日志:"
    sudo journalctl -u embodiedpulse -n 30 --no-pager
    exit 1
fi
echo ""

echo "=========================================="
echo "✅ 部署完成！"
echo "=========================================="

