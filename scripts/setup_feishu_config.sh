#!/bin/bash
# 交互式配置飞书登录

set -e

APP_DIR="/srv/EmbodiedPulse2026"

echo "============================================================"
echo "飞书登录配置向导"
echo "============================================================"
echo ""

cd "$APP_DIR"

# 检查.env文件
if [ ! -f ".env" ]; then
    echo "⚠️  .env文件不存在，正在创建..."
    if [ -f "env.example" ]; then
        cp env.example .env
        echo "✅ 已从env.example创建.env文件"
    else
        touch .env
        echo "✅ 已创建空的.env文件"
    fi
    echo ""
fi

# 读取现有配置
if grep -q "^FEISHU_APP_ID=" .env 2>/dev/null; then
    CURRENT_APP_ID=$(grep "^FEISHU_APP_ID=" .env | cut -d'=' -f2)
    echo "当前 FEISHU_APP_ID: ${CURRENT_APP_ID:0:10}..."
else
    CURRENT_APP_ID=""
fi

if grep -q "^FEISHU_APP_SECRET=" .env 2>/dev/null; then
    CURRENT_APP_SECRET=$(grep "^FEISHU_APP_SECRET=" .env | cut -d'=' -f2)
    echo "当前 FEISHU_APP_SECRET: ${CURRENT_APP_SECRET:0:10}..."
else
    CURRENT_APP_SECRET=""
fi

if grep -q "^FEISHU_REDIRECT_URI=" .env 2>/dev/null; then
    CURRENT_REDIRECT_URI=$(grep "^FEISHU_REDIRECT_URI=" .env | cut -d'=' -f2)
    echo "当前 FEISHU_REDIRECT_URI: $CURRENT_REDIRECT_URI"
else
    CURRENT_REDIRECT_URI=""
fi

echo ""
echo "============================================================"
echo "配置飞书登录"
echo "============================================================"
echo ""
echo "请提供以下信息（从飞书开放平台获取）:"
echo ""

# 获取App ID
if [ -z "$CURRENT_APP_ID" ]; then
    read -p "1. 飞书 App ID: " APP_ID
else
    read -p "1. 飞书 App ID [当前: ${CURRENT_APP_ID:0:10}...，直接回车保持]: " APP_ID
    if [ -z "$APP_ID" ]; then
        APP_ID="$CURRENT_APP_ID"
    fi
fi

# 获取App Secret
if [ -z "$CURRENT_APP_SECRET" ]; then
    read -p "2. 飞书 App Secret: " APP_SECRET
else
    read -p "2. 飞书 App Secret [当前: ${CURRENT_APP_SECRET:0:10}...，直接回车保持]: " APP_SECRET
    if [ -z "$APP_SECRET" ]; then
        APP_SECRET="$CURRENT_APP_SECRET"
    fi
fi

# 获取回调地址
if [ -z "$CURRENT_REDIRECT_URI" ]; then
    echo ""
    echo "3. 回调地址（选择域名）:"
    echo "   1) https://login.gradmotion.com/api/auth/feishu/callback"
    echo "   2) https://essay.gradmotion.com/api/auth/feishu/callback"
    read -p "   请选择 [1/2，默认1]: " REDIRECT_CHOICE
    REDIRECT_CHOICE=${REDIRECT_CHOICE:-1}
    
    if [ "$REDIRECT_CHOICE" = "2" ]; then
        REDIRECT_URI="https://essay.gradmotion.com/api/auth/feishu/callback"
    else
        REDIRECT_URI="https://login.gradmotion.com/api/auth/feishu/callback"
    fi
else
    read -p "3. 回调地址 [当前: $CURRENT_REDIRECT_URI，直接回车保持]: " REDIRECT_URI
    if [ -z "$REDIRECT_URI" ]; then
        REDIRECT_URI="$CURRENT_REDIRECT_URI"
    fi
fi

echo ""
echo "============================================================"
echo "确认配置"
echo "============================================================"
echo ""
echo "FEISHU_APP_ID: ${APP_ID:0:10}..."
echo "FEISHU_APP_SECRET: ${APP_SECRET:0:10}..."
echo "FEISHU_REDIRECT_URI: $REDIRECT_URI"
echo ""
read -p "确认保存配置? [y/N]: " CONFIRM

if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo "❌ 已取消配置"
    exit 0
fi

# 更新.env文件
echo ""
echo "正在更新.env文件..."

# 删除旧配置
sed -i '/^FEISHU_APP_ID=/d' .env
sed -i '/^FEISHU_APP_SECRET=/d' .env
sed -i '/^FEISHU_REDIRECT_URI=/d' .env

# 添加新配置
echo "" >> .env
echo "# ==================== 飞书OAuth配置 ====================" >> .env
echo "FEISHU_APP_ID=$APP_ID" >> .env
echo "FEISHU_APP_SECRET=$APP_SECRET" >> .env
echo "FEISHU_REDIRECT_URI=$REDIRECT_URI" >> .env

echo "✅ 配置已保存"
echo ""

# 验证配置
echo "============================================================"
echo "验证配置"
echo "============================================================"
echo ""

if grep -q "^FEISHU_APP_ID=$APP_ID" .env && \
   grep -q "^FEISHU_APP_SECRET=$APP_SECRET" .env && \
   grep -q "^FEISHU_REDIRECT_URI=$REDIRECT_URI" .env; then
    echo "✅ 配置验证成功"
else
    echo "❌ 配置验证失败，请检查.env文件"
    exit 1
fi

echo ""
echo "============================================================"
echo "下一步操作"
echo "============================================================"
echo ""
echo "1. 在飞书开放平台配置回调地址:"
echo "   $REDIRECT_URI"
echo ""
echo "2. 在飞书开放平台添加服务器IP到白名单:"
echo "   101.200.222.139"
echo ""
echo "3. 确保systemd服务加载.env文件:"
echo "   cat /etc/systemd/system/embodiedpulse.service | grep EnvironmentFile"
echo "   如果缺少，运行: bash scripts/fix_port_and_service.sh"
echo ""
echo "4. 重启服务:"
echo "   systemctl restart embodiedpulse"
echo ""
echo "5. 验证配置:"
echo "   bash scripts/check_and_fix_feishu_config.sh"
echo ""

