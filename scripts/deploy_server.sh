#!/usr/bin/env bash
set -e

APP_DIR="/srv/EmbodiedPulse2026"

echo "[deploy] 切换到应用目录: $APP_DIR"
cd "$APP_DIR"

echo "[deploy] 拉取最新代码..."
git fetch origin
git checkout main
git pull origin main

echo "[deploy] 激活虚拟环境并更新依赖..."
if [ -f "venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source venv/bin/activate
else
  echo "[deploy] 未找到 venv，自动创建..."
  python3 -m venv venv
  # shellcheck disable=SC1091
  source venv/bin/activate
fi

pip install --upgrade pip
pip install -r requirements.txt

echo "[deploy] 重启 systemd 服务 embodiedpulse..."
if command -v systemctl >/dev/null 2>&1; then
  systemctl restart embodiedpulse
  systemctl status embodiedpulse --no-pager -l || true
else
  echo "[deploy] 未检测到 systemctl，请手动重启 Gunicorn 或 Flask 服务。"
fi

echo "[deploy] 部署完成。"

#!/bin/bash
# 服务器端部署脚本（在服务器上直接运行）

set -e

PROJECT_DIR="/opt/EmbodiedPulse"
REPO_URL="https://github.com/aramisjiang-wq/EmbodiedPulse2026.git"

echo "=========================================="
echo "Embodied Pulse Docker 部署脚本"
echo "=========================================="

# 1. 检查并安装Docker
if ! command -v docker &> /dev/null; then
    echo "安装Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl start docker
    systemctl enable docker
    rm get-docker.sh
    echo "✅ Docker安装完成"
else
    echo "✅ Docker已安装"
fi

# 2. 检查并安装Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "安装Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    echo "✅ Docker Compose安装完成"
else
    echo "✅ Docker Compose已安装"
fi

# 3. 创建项目目录
mkdir -p ${PROJECT_DIR}
cd ${PROJECT_DIR}

# 4. 克隆或更新代码
if [ -d ".git" ]; then
    echo "更新代码..."
    git pull origin main || echo "警告: Git pull失败"
else
    echo "克隆代码..."
    git clone ${REPO_URL} .
fi

# 5. 停止现有容器
echo "停止现有容器..."
docker-compose down || true

# 6. 构建并启动服务
echo "构建并启动服务..."
docker-compose up -d --build

# 7. 等待服务启动
echo "等待服务启动..."
sleep 15

# 8. 初始化数据库（如果需要）
echo "初始化数据库..."
docker-compose exec -T web python3 init_database.py || echo "数据库可能已初始化"

# 9. 检查服务状态
echo "=========================================="
echo "服务状态:"
echo "=========================================="
docker-compose ps

echo ""
echo "=========================================="
echo "✅ 部署完成！"
echo "=========================================="
echo "服务地址: http://$(hostname -I | awk '{print $1}'):5001"
echo ""
echo "常用命令:"
echo "  查看日志: cd ${PROJECT_DIR} && docker-compose logs -f"
echo "  停止服务: cd ${PROJECT_DIR} && docker-compose down"
echo "  重启服务: cd ${PROJECT_DIR} && docker-compose restart"
echo "  查看状态: cd ${PROJECT_DIR} && docker-compose ps"
echo "=========================================="

