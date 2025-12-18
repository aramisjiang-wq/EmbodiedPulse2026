#!/bin/bash
# 修复 /auth/callback 路由 - 更新 Nginx 配置

set -e

echo "=========================================="
echo "修复 /auth/callback 路由"
echo "=========================================="
echo ""

cd /srv/EmbodiedPulse2026 || {
    echo "❌ 错误: 项目目录不存在"
    exit 1
}

# 拉取最新代码
echo "1️⃣  拉取最新代码..."
git pull origin main
echo "✅ 代码已更新"
echo ""

# 运行 Nginx 配置修复脚本
echo "2️⃣  更新 Nginx 配置..."
bash scripts/nginx_config_fix.sh

# 如果使用 HTTPS，也需要更新 HTTPS 配置
if [ -f /etc/letsencrypt/live/login.gradmotion.com/fullchain.pem ]; then
    echo ""
    echo "3️⃣  检测到 HTTPS 证书，更新 HTTPS 配置..."
    bash scripts/add_https_to_nginx.sh
else
    echo ""
    echo "3️⃣  未检测到 HTTPS 证书，跳过 HTTPS 配置更新"
fi

echo ""
echo "=========================================="
echo "✅ Nginx 配置已更新"
echo "=========================================="
echo ""
echo "📋 测试配置:"
echo "1. 访问: https://login.gradmotion.com/auth/callback?token=test"
echo "   应该显示登录成功页面（即使token无效）"
echo ""
echo "2. 重新测试飞书登录流程"

