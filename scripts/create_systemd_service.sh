#!/bin/bash
# 创建 systemd 服务配置文件

set -e

SERVICE_NAME="embodiedpulse"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
APP_DIR="/srv/EmbodiedPulse2026"
VENV_DIR="${APP_DIR}/venv"

echo "=========================================="
echo "创建 systemd 服务: ${SERVICE_NAME}"
echo "=========================================="

# 检查应用目录是否存在
if [ ! -d "$APP_DIR" ]; then
    echo "❌ 错误: 应用目录不存在: $APP_DIR"
    exit 1
fi

# 检查虚拟环境是否存在
if [ ! -d "$VENV_DIR" ]; then
    echo "⚠️  警告: 虚拟环境不存在，将创建..."
    cd "$APP_DIR"
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
fi

# 创建 systemd 服务文件
cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Embodied Pulse Flask Application (Gunicorn)
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=${APP_DIR}
Environment="PATH=${VENV_DIR}/bin"
Environment="FLASK_ENV=production"
EnvironmentFile=${APP_DIR}/.env
ExecStart=${VENV_DIR}/bin/gunicorn -c ${APP_DIR}/gunicorn_config.py app:app
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal
SyslogIdentifier=${SERVICE_NAME}

[Install]
WantedBy=multi-user.target
EOF

echo "✅ systemd 服务文件已创建: $SERVICE_FILE"

# 重新加载 systemd
systemctl daemon-reload

# 启用服务（开机自启）
systemctl enable ${SERVICE_NAME}

echo "✅ 服务已启用（开机自启）"
echo ""
echo "=========================================="
echo "下一步操作："
echo "=========================================="
echo "1. 启动服务: systemctl start ${SERVICE_NAME}"
echo "2. 查看状态: systemctl status ${SERVICE_NAME}"
echo "3. 查看日志: journalctl -u ${SERVICE_NAME} -f"
echo "4. 重启服务: systemctl restart ${SERVICE_NAME}"
echo "=========================================="

