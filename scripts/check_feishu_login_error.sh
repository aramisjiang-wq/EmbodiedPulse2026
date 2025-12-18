#!/bin/bash
# 检查飞书登录错误

set -e

echo "=========================================="
echo "飞书登录错误检查"
echo "=========================================="
echo ""

cd /srv/EmbodiedPulse2026 || {
    echo "❌ 错误: 项目目录不存在"
    exit 1
}

# 1. 查看最近的飞书登录相关日志
echo "1️⃣  查看最近的飞书登录日志（最近100行）..."
echo "----------------------------------------"
sudo journalctl -u embodiedpulse -n 100 --no-pager | grep -i "feishu\|飞书\|callback\|登录\|error\|失败" | tail -30
echo "----------------------------------------"
echo ""

# 2. 查看最近的错误和异常
echo "2️⃣  查看最近的错误和异常..."
echo "----------------------------------------"
sudo journalctl -u embodiedpulse -n 200 --no-pager | grep -i "exception\|traceback\|error\|失败" | tail -20
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
echo "检查完成"
echo "=========================================="
echo ""
echo "📋 请查看上面的日志，找出具体的错误信息"
echo "   如果看到 'invalid_state' 或 'state参数验证失败'，"
echo "   说明state参数过期或已被消费，请重新点击登录按钮"

