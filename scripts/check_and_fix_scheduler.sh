#!/bin/bash
# 检查并修复定时任务配置

set -e

APP_DIR="/srv/EmbodiedPulse2026"
ENV_FILE="${APP_DIR}/.env"

echo "=========================================="
echo "检查定时任务配置"
echo "=========================================="

# 检查 .env 文件是否存在
if [ ! -f "$ENV_FILE" ]; then
    echo "⚠️  .env 文件不存在，正在创建..."
    touch "$ENV_FILE"
fi

# 检查 AUTO_FETCH_ENABLED 配置
if grep -q "AUTO_FETCH_ENABLED" "$ENV_FILE"; then
    current_value=$(grep "AUTO_FETCH_ENABLED" "$ENV_FILE" | cut -d '=' -f2 | tr -d ' ')
    echo "当前 AUTO_FETCH_ENABLED 值: $current_value"
    
    if [ "$current_value" != "true" ]; then
        echo "⚠️  AUTO_FETCH_ENABLED 未设置为 true，正在修复..."
        # 替换或添加配置
        if grep -q "^AUTO_FETCH_ENABLED" "$ENV_FILE"; then
            sed -i 's/^AUTO_FETCH_ENABLED=.*/AUTO_FETCH_ENABLED=true/' "$ENV_FILE"
        else
            echo "AUTO_FETCH_ENABLED=true" >> "$ENV_FILE"
        fi
        echo "✅ 已设置为 AUTO_FETCH_ENABLED=true"
    else
        echo "✅ AUTO_FETCH_ENABLED 已正确设置为 true"
    fi
else
    echo "⚠️  未找到 AUTO_FETCH_ENABLED 配置，正在添加..."
    echo "AUTO_FETCH_ENABLED=true" >> "$ENV_FILE"
    echo "✅ 已添加 AUTO_FETCH_ENABLED=true"
fi

# 检查其他必要的定时任务配置
echo ""
echo "检查其他定时任务配置..."

# AUTO_FETCH_SCHEDULE
if ! grep -q "^AUTO_FETCH_SCHEDULE" "$ENV_FILE"; then
    echo "AUTO_FETCH_SCHEDULE=0 * * * *" >> "$ENV_FILE"
    echo "✅ 已添加 AUTO_FETCH_SCHEDULE=0 * * * *"
fi

# AUTO_FETCH_BILIBILI_SCHEDULE
if ! grep -q "^AUTO_FETCH_BILIBILI_SCHEDULE" "$ENV_FILE"; then
    echo "AUTO_FETCH_BILIBILI_SCHEDULE=0 */6 * * *" >> "$ENV_FILE"
    echo "✅ 已添加 AUTO_FETCH_BILIBILI_SCHEDULE=0 */6 * * *"
fi

# AUTO_FETCH_NEWS_SCHEDULE
if ! grep -q "^AUTO_FETCH_NEWS_SCHEDULE" "$ENV_FILE"; then
    echo "AUTO_FETCH_NEWS_SCHEDULE=0 * * * *" >> "$ENV_FILE"
    echo "✅ 已添加 AUTO_FETCH_NEWS_SCHEDULE=0 * * * *"
fi

# AUTO_FETCH_JOBS_SCHEDULE
if ! grep -q "^AUTO_FETCH_JOBS_SCHEDULE" "$ENV_FILE"; then
    echo "AUTO_FETCH_JOBS_SCHEDULE=0 * * * *" >> "$ENV_FILE"
    echo "✅ 已添加 AUTO_FETCH_JOBS_SCHEDULE=0 * * * *"
fi

echo ""
echo "=========================================="
echo "当前 .env 配置："
echo "=========================================="
grep -E "AUTO_FETCH|FLASK_ENV" "$ENV_FILE" || echo "（无相关配置）"

echo ""
echo "=========================================="
echo "检查服务状态"
echo "=========================================="

# 检查服务是否运行
if systemctl is-active --quiet embodiedpulse; then
    echo "✅ embodiedpulse 服务正在运行"
    
    echo ""
    echo "查看最近的日志（查找定时任务相关信息）："
    echo "----------------------------------------"
    journalctl -u embodiedpulse --no-pager -n 50 | grep -i "定时任务\|scheduler\|AUTO_FETCH" || echo "未找到定时任务相关日志"
    
    echo ""
    echo "=========================================="
    echo "建议操作："
    echo "=========================================="
    echo "1. 如果 AUTO_FETCH_ENABLED 刚刚被修改，需要重启服务："
    echo "   systemctl restart embodiedpulse"
    echo ""
    echo "2. 查看完整日志："
    echo "   journalctl -u embodiedpulse -f"
    echo ""
    echo "3. 等待几分钟后，检查是否有定时任务执行日志"
else
    echo "⚠️  embodiedpulse 服务未运行"
    echo "启动服务：systemctl start embodiedpulse"
fi

echo ""
echo "=========================================="
echo "检查完成"
echo "=========================================="

