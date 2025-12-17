#!/bin/bash
# 修复端口占用和 systemd 服务配置

set -e

SERVICE_FILE="/etc/systemd/system/embodiedpulse.service"
APP_DIR="/srv/EmbodiedPulse2026"

echo "=========================================="
echo "修复端口占用和 systemd 服务配置"
echo "=========================================="

# 1. 停止服务
echo "1. 停止 embodiedpulse 服务..."
systemctl stop embodiedpulse || true

# 2. 查找并杀死占用 5001 端口的进程
echo ""
echo "2. 查找占用 5001 端口的进程..."
PORT_PID=$(lsof -ti:5001 || true)

if [ -n "$PORT_PID" ]; then
    echo "发现进程占用 5001 端口: PID=$PORT_PID"
    echo "正在终止进程..."
    kill -9 $PORT_PID || true
    sleep 2
    echo "✅ 进程已终止"
else
    echo "✅ 5001 端口未被占用"
fi

# 再次确认端口是否释放
if lsof -ti:5001 > /dev/null 2>&1; then
    echo "⚠️  警告: 端口仍被占用，强制清理..."
    fuser -k 5001/tcp || true
    sleep 2
fi

# 3. 修复 systemd 服务配置，添加 EnvironmentFile
echo ""
echo "3. 修复 systemd 服务配置..."

# 备份原配置
cp "$SERVICE_FILE" "${SERVICE_FILE}.backup.$(date +%Y%m%d_%H%M%S)"

# 检查是否已有 EnvironmentFile
if grep -q "EnvironmentFile" "$SERVICE_FILE"; then
    echo "✅ EnvironmentFile 已存在"
else
    echo "添加 EnvironmentFile 配置..."
    # 在 [Service] 部分的 Environment 行之后添加 EnvironmentFile
    sed -i '/^Environment=/a EnvironmentFile='"$APP_DIR"'/.env' "$SERVICE_FILE"
    echo "✅ 已添加 EnvironmentFile"
fi

# 显示修改后的配置
echo ""
echo "修改后的服务配置（Environment 部分）："
grep -A 5 "\[Service\]" "$SERVICE_FILE" | grep -E "Environment|EnvironmentFile"

# 4. 重新加载 systemd
echo ""
echo "4. 重新加载 systemd..."
systemctl daemon-reload

# 5. 启动服务
echo ""
echo "5. 启动服务..."
systemctl start embodiedpulse

# 等待几秒
sleep 3

# 6. 检查服务状态
echo ""
echo "6. 检查服务状态..."
systemctl status embodiedpulse --no-pager -l | head -20

# 7. 检查端口
echo ""
echo "7. 检查端口 5001..."
if lsof -ti:5001 > /dev/null 2>&1; then
    echo "✅ 端口 5001 正在监听"
    lsof -i:5001
else
    echo "❌ 端口 5001 未监听"
fi

# 8. 查看日志（查找定时任务相关信息）
echo ""
echo "8. 查看最近的日志（查找定时任务信息）..."
journalctl -u embodiedpulse --no-pager -n 30 | grep -i "定时任务\|scheduler\|AUTO_FETCH\|Gunicorn服务器已就绪" || echo "未找到相关日志"

echo ""
echo "=========================================="
echo "修复完成"
echo "=========================================="
echo ""
echo "查看完整日志："
echo "  journalctl -u embodiedpulse -f"
echo ""

