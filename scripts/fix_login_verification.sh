#!/bin/bash
# 修复登录验证问题：确保代码更新并清除缓存

set -e

APP_DIR="/srv/EmbodiedPulse2026"

echo "=========================================="
echo "修复登录验证问题"
echo "=========================================="
echo ""

cd "$APP_DIR"

# 1. 拉取最新代码
echo "1. 拉取最新代码..."
git pull origin main

# 2. 检查user_menu.js是否正确
echo ""
echo "2. 检查登录验证配置..."
if grep -q "'/bilibili'" static/js/user_menu.js; then
    echo "⚠️  发现 /bilibili 仍在白名单中，需要修复"
    echo "   正在修复..."
    sed -i "s|'/bilibili'||g" static/js/user_menu.js
    sed -i "s|, '/bilibili'||g" static/js/user_menu.js
    sed -i "s|'/bilibili', ||g" static/js/user_menu.js
    echo "✅ 已修复"
else
    echo "✅ /bilibili 不在白名单中（正确）"
fi

# 3. 验证修复
echo ""
echo "3. 验证修复..."
PUBLIC_PAGES=$(grep "const publicPages" static/js/user_menu.js)
echo "   当前白名单: $PUBLIC_PAGES"

if echo "$PUBLIC_PAGES" | grep -q "'/bilibili'"; then
    echo "❌ 修复失败，仍有 /bilibili 在白名单中"
    exit 1
else
    echo "✅ 验证通过"
fi

# 4. 重启服务
echo ""
echo "4. 重启服务..."
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
echo "=========================================="
echo "✅ 修复完成！"
echo "=========================================="
echo ""
echo "📝 下一步:"
echo "  1. 清除浏览器缓存（Ctrl+Shift+R 或 Cmd+Shift+R）"
echo "  2. 访问 https://essay.gradmotion.com/ 应该会跳转到登录页"
echo "  3. 访问 https://blibli.gradmotion.com/ 应该会跳转到登录页"
echo ""
echo "💡 如果仍然可以直接访问，可能是浏览器中已有token"
echo "   可以清除浏览器localStorage: localStorage.clear()"

