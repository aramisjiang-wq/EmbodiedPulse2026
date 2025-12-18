#!/bin/bash
# 快速重启服务并检查飞书登录错误

set -e

echo "=========================================="
echo "重启服务并检查飞书登录"
echo "=========================================="
echo ""

cd /srv/EmbodiedPulse2026 || {
    echo "❌ 错误: 项目目录不存在"
    exit 1
}

# 1. 重启服务
echo "1️⃣  重启服务..."
sudo systemctl restart embodiedpulse

# 等待服务启动
echo "等待服务启动..."
sleep 3

# 检查服务状态
if systemctl is-active --quiet embodiedpulse; then
    echo "✅ 服务运行正常"
else
    echo "❌ 服务启动失败"
    echo "查看错误日志:"
    sudo journalctl -u embodiedpulse -n 30 --no-pager
    exit 1
fi
echo ""

# 2. 检查飞书登录错误
echo "2️⃣  检查飞书登录相关日志..."
echo "----------------------------------------"
sudo journalctl -u embodiedpulse -n 100 --no-pager | grep -i "feishu\|飞书\|callback\|登录\|error\|失败" | tail -20 || echo "   未发现相关日志"
echo "----------------------------------------"
echo ""

# 3. 测试飞书API
echo "3️⃣  测试飞书API连接..."
python3 << 'EOF'
import os
import sys
sys.path.insert(0, '/srv/EmbodiedPulse2026')

from dotenv import load_dotenv
load_dotenv()

try:
    from feishu_auth import FeishuAuth
    
    print("正在测试飞书API...")
    auth = FeishuAuth()
    token = auth.get_app_access_token()
    print(f"✅ 成功获取app_access_token: {token[:30]}...")
except Exception as e:
    print(f"❌ 失败: {e}")
    import traceback
    traceback.print_exc()
EOF

echo ""
echo "=========================================="
echo "✅ 检查完成"
echo "=========================================="
echo ""
echo "📋 下一步:"
echo "1. 清除浏览器缓存（硬刷新：Ctrl+Shift+R）"
echo "2. 重新点击'飞书扫码登录'按钮"
echo "3. 如果还有问题，运行: bash scripts/check_feishu_login_error.sh"

