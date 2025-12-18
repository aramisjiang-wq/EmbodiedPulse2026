#!/bin/bash
# 登录验证修复部署脚本
# 用于在服务器上更新代码和应用修复

set -e  # 遇到错误立即退出

echo "=========================================="
echo "开始部署登录验证修复"
echo "=========================================="

# 进入项目目录
cd /srv/EmbodiedPulse2026 || {
    echo "❌ 错误: 项目目录不存在"
    exit 1
}

echo "📥 拉取最新代码..."
git pull origin main || {
    echo "❌ 错误: Git pull 失败"
    exit 1
}

echo "✅ 代码更新完成"

echo "🔧 更新 Nginx 配置..."
bash scripts/nginx_config_fix.sh || {
    echo "❌ 错误: Nginx 配置更新失败"
    exit 1
}

echo "🔍 测试 Nginx 配置..."
sudo nginx -t || {
    echo "❌ 错误: Nginx 配置测试失败"
    exit 1
}

echo "🔄 重新加载 Nginx..."
sudo systemctl reload nginx || {
    echo "❌ 错误: Nginx 重新加载失败"
    exit 1
}

echo "✅ Nginx 配置已更新"

echo "🔄 重启 Flask 服务..."
sudo systemctl restart embodiedpulse || {
    echo "❌ 错误: Flask 服务重启失败"
    exit 1
}

# 等待服务启动
sleep 3

echo "🔍 检查服务状态..."
if systemctl is-active --quiet embodiedpulse; then
    echo "✅ Flask 服务运行正常"
else
    echo "⚠️  警告: Flask 服务可能未正常启动，请检查日志"
    echo "查看日志: sudo journalctl -u embodiedpulse -n 50"
fi

echo ""
echo "=========================================="
echo "✅ 部署完成！"
echo "=========================================="
echo ""
echo "📋 测试清单:"
echo "1. 访问 https://essay.gradmotion.com/ (未登录应跳转登录页)"
echo "2. 访问 https://essay.gradmotion.com/bilibili (未登录应跳转登录页)"
echo "3. 访问 https://blibli.gradmotion.com/ (未登录应跳转登录页)"
echo "4. 访问 https://login.gradmotion.com/login (应正常显示，不再404)"
echo "5. 测试飞书登录流程"
echo ""
echo "🔍 如果遇到问题，查看日志:"
echo "   sudo journalctl -u embodiedpulse -n 100 -f"
echo "   sudo tail -f /var/log/nginx/error.log"
echo ""

