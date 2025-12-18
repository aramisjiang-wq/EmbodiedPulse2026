#!/bin/bash
# 诊断飞书登录问题

set -e

echo "=========================================="
echo "飞书登录问题诊断"
echo "=========================================="
echo ""

cd /srv/EmbodiedPulse2026 || {
    echo "❌ 错误: 项目目录不存在"
    exit 1
}

# 1. 检查环境变量
echo "1️⃣  检查飞书配置..."
FEISHU_APP_ID=$(grep "^FEISHU_APP_ID=" .env | cut -d'=' -f2)
FEISHU_APP_SECRET=$(grep "^FEISHU_APP_SECRET=" .env | cut -d'=' -f2)
FEISHU_REDIRECT_URI=$(grep "^FEISHU_REDIRECT_URI=" .env | cut -d'=' -f2)

if [ -z "$FEISHU_APP_ID" ] || [ -z "$FEISHU_APP_SECRET" ]; then
    echo "❌ 飞书配置缺失"
    echo "   FEISHU_APP_ID: ${FEISHU_APP_ID:-未配置}"
    echo "   FEISHU_APP_SECRET: ${FEISHU_APP_SECRET:-未配置}"
else
    echo "✅ 飞书配置存在"
    echo "   FEISHU_APP_ID: ${FEISHU_APP_ID:0:10}..."
    echo "   FEISHU_APP_SECRET: ${FEISHU_APP_SECRET:0:10}..."
    echo "   FEISHU_REDIRECT_URI: ${FEISHU_REDIRECT_URI:-未配置}"
fi
echo ""

# 2. 检查服务状态
echo "2️⃣  检查服务状态..."
if systemctl is-active --quiet embodiedpulse; then
    echo "✅ 服务运行正常"
else
    echo "❌ 服务未运行"
    echo "   启动服务: sudo systemctl start embodiedpulse"
fi
echo ""

# 3. 查看最近的错误日志
echo "3️⃣  查看最近的错误日志（最近50行）..."
echo "----------------------------------------"
sudo journalctl -u embodiedpulse -n 50 --no-pager | grep -i "error\|失败\|exception\|traceback" || echo "   未发现错误日志"
echo "----------------------------------------"
echo ""

# 4. 查看飞书相关日志
echo "4️⃣  查看飞书登录相关日志（最近30行）..."
echo "----------------------------------------"
sudo journalctl -u embodiedpulse -n 100 --no-pager | grep -i "feishu\|飞书\|callback\|登录" || echo "   未发现飞书相关日志"
echo "----------------------------------------"
echo ""

# 5. 测试飞书API连接
echo "5️⃣  测试飞书API连接..."
python3 << 'EOF'
import os
import sys
sys.path.insert(0, '/srv/EmbodiedPulse2026')

from dotenv import load_dotenv
load_dotenv()

try:
    from feishu_auth import FeishuAuth
    
    app_id = os.getenv('FEISHU_APP_ID')
    app_secret = os.getenv('FEISHU_APP_SECRET')
    
    if not app_id or not app_secret:
        print("❌ 飞书配置缺失")
        sys.exit(1)
    
    auth = FeishuAuth(app_id, app_secret)
    token = auth.get_app_access_token()
    print(f"✅ 飞书API连接成功")
    print(f"   app_access_token: {token[:20]}...")
except Exception as e:
    print(f"❌ 飞书API连接失败: {e}")
    import traceback
    traceback.print_exc()
EOF

echo ""
echo "=========================================="
echo "诊断完成"
echo "=========================================="
echo ""
echo "📋 下一步操作:"
echo ""
echo "1. 如果看到错误日志，请检查具体的错误信息"
echo "2. 如果飞书API连接失败，请检查配置是否正确"
echo "3. 查看完整日志: sudo journalctl -u embodiedpulse -f"
echo "4. 重新测试登录流程"

