#!/bin/bash
# 诊断和修复登录验证及飞书登录问题

set -e

echo "=========================================="
echo "诊断登录验证和飞书登录问题"
echo "=========================================="
echo ""

cd /srv/EmbodiedPulse2026 || {
    echo "❌ 错误: 项目目录不存在"
    exit 1
}

# 1. 检查环境变量配置
echo "1️⃣  检查飞书环境变量配置..."
if [ -f .env ]; then
    echo "✅ .env 文件存在"
    
    # 安全地读取 .env 文件（只读取 KEY=VALUE 格式的行）
    MISSING_VARS=()
    
    # 读取 FEISHU_APP_ID
    FEISHU_APP_ID=$(grep -E "^FEISHU_APP_ID=" .env | cut -d '=' -f2- | tr -d '"' | tr -d "'" | xargs)
    if [ -z "$FEISHU_APP_ID" ]; then
        MISSING_VARS+=("FEISHU_APP_ID")
        echo "❌ FEISHU_APP_ID 未配置"
    else
        echo "✅ FEISHU_APP_ID: ${FEISHU_APP_ID:0:8}..."
    fi
    
    # 读取 FEISHU_APP_SECRET
    FEISHU_APP_SECRET=$(grep -E "^FEISHU_APP_SECRET=" .env | cut -d '=' -f2- | tr -d '"' | tr -d "'" | xargs)
    if [ -z "$FEISHU_APP_SECRET" ]; then
        MISSING_VARS+=("FEISHU_APP_SECRET")
        echo "❌ FEISHU_APP_SECRET 未配置"
    else
        echo "✅ FEISHU_APP_SECRET: 已配置"
    fi
    
    # 读取 FEISHU_REDIRECT_URI
    FEISHU_REDIRECT_URI=$(grep -E "^FEISHU_REDIRECT_URI=" .env | cut -d '=' -f2- | tr -d '"' | tr -d "'" | xargs)
    if [ -z "$FEISHU_REDIRECT_URI" ]; then
        echo "⚠️  FEISHU_REDIRECT_URI 未配置，将使用自动检测"
    else
        echo "✅ FEISHU_REDIRECT_URI: $FEISHU_REDIRECT_URI"
        # 检查是否是 HTTPS
        if [[ ! "$FEISHU_REDIRECT_URI" =~ ^https:// ]]; then
            echo "⚠️  警告: FEISHU_REDIRECT_URI 不是 HTTPS，建议使用 HTTPS"
        fi
    fi
    
    if [ ${#MISSING_VARS[@]} -gt 0 ]; then
        echo ""
        echo "❌ 发现缺失的配置项: ${MISSING_VARS[*]}"
        echo ""
        echo "请运行以下命令配置:"
        echo "  bash scripts/setup_feishu_config.sh"
        echo ""
        exit 1
    fi
else
    echo "❌ .env 文件不存在"
    echo "请运行: bash scripts/setup_feishu_config.sh"
    exit 1
fi
echo ""

# 2. 检查 systemd 服务配置
echo "2️⃣  检查 systemd 服务配置..."
if systemctl cat embodiedpulse | grep -q "EnvironmentFile"; then
    echo "✅ systemd 服务已配置 EnvironmentFile"
    systemctl cat embodiedpulse | grep "EnvironmentFile"
else
    echo "❌ systemd 服务未配置 EnvironmentFile"
    echo "正在修复..."
    
    SERVICE_FILE="/etc/systemd/system/embodiedpulse.service"
    if [ -f "$SERVICE_FILE" ]; then
        # 检查是否已有 EnvironmentFile
        if ! grep -q "EnvironmentFile" "$SERVICE_FILE"; then
            # 在 [Service] 部分添加 EnvironmentFile
            sed -i '/\[Service\]/a EnvironmentFile=/srv/EmbodiedPulse2026/.env' "$SERVICE_FILE"
            echo "✅ 已添加 EnvironmentFile 到服务文件"
            
            # 重新加载 systemd
            systemctl daemon-reload
            echo "✅ 已重新加载 systemd"
        fi
    fi
fi
echo ""

# 3. 检查服务是否加载了环境变量
echo "3️⃣  检查服务环境变量..."
if systemctl is-active --quiet embodiedpulse; then
    # 获取服务进程的环境变量
    PID=$(systemctl show -p MainPID --value embodiedpulse)
    if [ -n "$PID" ] && [ "$PID" != "0" ]; then
        echo "服务进程 PID: $PID"
        # 检查进程环境变量（需要 root 权限）
        if sudo cat /proc/$PID/environ 2>/dev/null | tr '\0' '\n' | grep -q "FEISHU_APP_ID"; then
            echo "✅ 服务已加载 FEISHU_APP_ID 环境变量"
        else
            echo "⚠️  服务可能未加载环境变量，建议重启服务"
        fi
    fi
else
    echo "⚠️  服务未运行"
fi
echo ""

# 4. 测试飞书 API 连接
echo "4️⃣  测试飞书 API 连接..."
if [ -n "$FEISHU_APP_ID" ] && [ -n "$FEISHU_APP_SECRET" ]; then
    echo "尝试获取 app_access_token..."
    RESPONSE=$(curl -s -X POST "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal" \
        -H "Content-Type: application/json" \
        -d "{\"app_id\":\"$FEISHU_APP_ID\",\"app_secret\":\"$FEISHU_APP_SECRET\"}")
    
    if echo "$RESPONSE" | grep -q '"code":0'; then
        echo "✅ 飞书 API 连接成功"
    else
        echo "❌ 飞书 API 连接失败"
        echo "响应: $RESPONSE"
    fi
else
    echo "⚠️  无法测试：环境变量未配置"
fi
echo ""

# 5. 检查前端文件
echo "5️⃣  检查前端文件..."
if [ -f "static/js/user_menu.js" ]; then
    echo "✅ user_menu.js 存在"
    if grep -q "checkAuthRequired" "static/js/user_menu.js"; then
        echo "✅ 包含 checkAuthRequired 函数"
    else
        echo "❌ 缺少 checkAuthRequired 函数"
    fi
else
    echo "❌ user_menu.js 不存在"
fi
echo ""

# 6. 提供修复建议
echo "=========================================="
echo "🔧 修复建议"
echo "=========================================="
echo ""

if [ ${#MISSING_VARS[@]} -eq 0 ]; then
    echo "1. 重启服务以加载最新配置和代码:"
    echo "   sudo systemctl restart embodiedpulse"
    echo ""
    echo "2. 检查服务日志:"
    echo "   sudo journalctl -u embodiedpulse -n 50 -f"
    echo ""
    echo "3. 测试登录流程:"
    echo "   - 访问 https://essay.gradmotion.com/"
    echo "   - 应该自动跳转到登录页"
    echo "   - 点击飞书扫码登录"
    echo ""
else
    echo "请先配置缺失的环境变量:"
    echo "  bash scripts/setup_feishu_config.sh"
    echo ""
fi

echo "=========================================="

