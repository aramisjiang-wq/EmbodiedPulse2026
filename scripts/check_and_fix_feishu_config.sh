#!/bin/bash
# 检查并修复飞书登录配置

set -e

APP_DIR="/srv/EmbodiedPulse2026"

echo "============================================================"
echo "检查并修复飞书登录配置"
echo "============================================================"
echo ""

cd "$APP_DIR"

# 检查.env文件是否存在
if [ ! -f ".env" ]; then
    echo "❌ .env文件不存在，正在创建..."
    if [ -f "env.example" ]; then
        cp env.example .env
        echo "✅ 已从env.example创建.env文件"
    else
        echo "❌ env.example也不存在，请手动创建.env文件"
        exit 1
    fi
fi

echo "📋 检查飞书配置..."
echo ""

# 检查必需的环境变量
MISSING_VARS=()

if ! grep -q "^FEISHU_APP_ID=" .env 2>/dev/null || grep -q "^FEISHU_APP_ID=$" .env 2>/dev/null; then
    MISSING_VARS+=("FEISHU_APP_ID")
    echo "❌ FEISHU_APP_ID 未配置"
else
    APP_ID=$(grep "^FEISHU_APP_ID=" .env | cut -d'=' -f2)
    echo "✅ FEISHU_APP_ID: ${APP_ID:0:10}..."
fi

if ! grep -q "^FEISHU_APP_SECRET=" .env 2>/dev/null || grep -q "^FEISHU_APP_SECRET=$" .env 2>/dev/null; then
    MISSING_VARS+=("FEISHU_APP_SECRET")
    echo "❌ FEISHU_APP_SECRET 未配置"
else
    APP_SECRET=$(grep "^FEISHU_APP_SECRET=" .env | cut -d'=' -f2)
    echo "✅ FEISHU_APP_SECRET: ${APP_SECRET:0:10}..."
fi

if ! grep -q "^FEISHU_REDIRECT_URI=" .env 2>/dev/null || grep -q "^FEISHU_REDIRECT_URI=$" .env 2>/dev/null; then
    MISSING_VARS+=("FEISHU_REDIRECT_URI")
    echo "❌ FEISHU_REDIRECT_URI 未配置"
else
    REDIRECT_URI=$(grep "^FEISHU_REDIRECT_URI=" .env | cut -d'=' -f2)
    echo "✅ FEISHU_REDIRECT_URI: $REDIRECT_URI"
fi

echo ""

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo "============================================================"
    echo "⚠️  发现缺失的配置项"
    echo "============================================================"
    echo ""
    echo "缺失的配置: ${MISSING_VARS[*]}"
    echo ""
    echo "📝 配置步骤:"
    echo ""
    echo "1. 在飞书开放平台获取以下信息:"
    echo "   - App ID"
    echo "   - App Secret"
    echo ""
    echo "2. 配置回调地址（在飞书开放平台）:"
    echo "   - 生产环境: https://login.gradmotion.com/api/auth/feishu/callback"
    echo "   - 或: https://essay.gradmotion.com/api/auth/feishu/callback"
    echo ""
    echo "3. 在服务器上编辑.env文件，添加以下配置:"
    echo ""
    for var in "${MISSING_VARS[@]}"; do
        case $var in
            FEISHU_APP_ID)
                echo "   FEISHU_APP_ID=你的App_ID"
                ;;
            FEISHU_APP_SECRET)
                echo "   FEISHU_APP_SECRET=你的App_Secret"
                ;;
            FEISHU_REDIRECT_URI)
                echo "   FEISHU_REDIRECT_URI=https://login.gradmotion.com/api/auth/feishu/callback"
                ;;
        esac
    done
    echo ""
    echo "4. 重启服务:"
    echo "   systemctl restart embodiedpulse"
    echo ""
    echo "============================================================"
    echo "💡 提示: 可以使用以下命令编辑.env文件:"
    echo "   nano .env"
    echo "   或"
    echo "   vi .env"
    echo "============================================================"
    exit 1
else
    echo "✅ 所有飞书配置项都已配置"
    echo ""
    
    # 验证配置是否正确加载
    echo "📋 验证配置加载..."
    if [ -d "venv" ]; then
        venv/bin/python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()
app_id = os.getenv('FEISHU_APP_ID')
app_secret = os.getenv('FEISHU_APP_SECRET')
if app_id and app_secret:
    print('✅ 配置可以正确加载')
else:
    print('❌ 配置加载失败')
    exit(1)
" || echo "❌ 配置验证失败"
    elif [ -d ".venv" ]; then
        .venv/bin/python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()
app_id = os.getenv('FEISHU_APP_ID')
app_secret = os.getenv('FEISHU_APP_SECRET')
if app_id and app_secret:
    print('✅ 配置可以正确加载')
else:
    print('❌ 配置加载失败')
    exit(1)
" || echo "❌ 配置验证失败"
    else
        python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()
app_id = os.getenv('FEISHU_APP_ID')
app_secret = os.getenv('FEISHU_APP_SECRET')
if app_id and app_secret:
    print('✅ 配置可以正确加载')
else:
    print('❌ 配置加载失败')
    exit(1)
" || echo "❌ 配置验证失败"
    fi
    
    echo ""
    echo "============================================================"
    echo "✅ 配置检查完成"
    echo "============================================================"
    echo ""
    echo "📝 如果服务正在运行，需要重启以加载新配置:"
    echo "   systemctl restart embodiedpulse"
    echo ""
fi

