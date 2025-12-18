#!/bin/bash
# 重启服务并验证登录功能

set -e

echo "=========================================="
echo "重启服务并验证登录功能"
echo "=========================================="
echo ""

cd /srv/EmbodiedPulse2026 || {
    echo "❌ 错误: 项目目录不存在"
    exit 1
}

# 1. 拉取最新代码
echo "1️⃣  拉取最新代码..."
git pull origin main
echo "✅ 代码已更新"
echo ""

# 2. 重启服务
echo "2️⃣  重启 Flask 服务..."
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

# 3. 检查服务日志（最近错误）
echo "3️⃣  检查服务日志（最近10行）..."
sudo journalctl -u embodiedpulse -n 10 --no-pager | tail -10
echo ""

# 4. 测试本地连接
echo "4️⃣  测试本地 Flask 连接..."
if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5001/ | grep -q "200\|302\|301"; then
    echo "✅ Flask 本地连接正常"
else
    echo "❌ Flask 本地连接失败"
fi
echo ""

# 5. 测试 API 端点
echo "5️⃣  测试登录 API 端点..."
API_RESPONSE=$(curl -s -X POST http://127.0.0.1:5001/api/auth/feishu/login \
    -H "Content-Type: application/json" \
    -d '{"final_redirect": "/"}')

if echo "$API_RESPONSE" | grep -q '"success":true'; then
    echo "✅ 登录 API 端点正常"
    echo "响应: $(echo "$API_RESPONSE" | head -c 100)..."
else
    echo "❌ 登录 API 端点异常"
    echo "响应: $API_RESPONSE"
fi
echo ""

# 6. 检查前端文件版本
echo "6️⃣  检查前端文件..."
if [ -f "static/js/user_menu.js" ]; then
    if grep -q "立即执行登录检查" "static/js/user_menu.js"; then
        echo "✅ user_menu.js 已更新（包含立即执行逻辑）"
    else
        echo "⚠️  user_menu.js 可能未更新"
    fi
else
    echo "❌ user_menu.js 不存在"
fi
echo ""

# 7. 验证总结
echo "=========================================="
echo "✅ 服务重启完成"
echo "=========================================="
echo ""
echo "📋 下一步测试:"
echo ""
echo "1. 清除浏览器缓存和 localStorage:"
echo "   - 按 F12 打开开发者工具"
echo "   - Application -> Local Storage -> 清除所有数据"
echo "   - 或者使用无痕模式访问"
echo ""
echo "2. 测试强制登录验证:"
echo "   - 访问: https://essay.gradmotion.com/"
echo "   - 应该立即跳转到: https://essay.gradmotion.com/login"
echo ""
echo "3. 测试飞书登录:"
echo "   - 点击"飞书扫码登录"按钮"
echo "   - 应该跳转到飞书授权页面"
echo "   - 授权后应该成功返回并登录"
echo ""
echo "4. 如果还有问题，查看实时日志:"
echo "   sudo journalctl -u embodiedpulse -f"
echo ""
echo "5. 查看浏览器控制台（F12 -> Console）:"
echo "   - 检查是否有 JavaScript 错误"
echo "   - 检查网络请求是否成功"
echo ""

