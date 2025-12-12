#!/bin/bash
# 快速部署脚本 - 在服务器上直接运行此脚本

set -e

PROJECT_DIR="/opt/EmbodiedPulse"
REPO_URL="https://github.com/aramisjiang-wq/EmbodiedPulse2026.git"

echo "=========================================="
echo "Embodied Pulse 快速部署"
echo "=========================================="

# 安装Docker
if ! command -v docker &> /dev/null; then
    echo "安装Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl start docker
    systemctl enable docker
    rm get-docker.sh
fi

# 安装Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "安装Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# 准备项目目录
mkdir -p ${PROJECT_DIR}
cd ${PROJECT_DIR}

# 克隆或更新代码
if [ -d ".git" ]; then
    echo "更新代码..."
    git pull origin main || true
else
    echo "克隆代码..."
    git clone ${REPO_URL} .
fi

# 停止旧容器
echo "停止旧容器..."
docker-compose down || true

# 启动服务
echo "构建并启动服务..."
docker-compose up -d --build

# 等待服务启动
echo "等待服务启动..."
sleep 15

# 初始化数据库
echo "初始化数据库..."
docker-compose exec -T web python3 init_database.py || true

# 显示状态
echo ""
echo "=========================================="
echo "✅ 部署完成！"
echo "=========================================="
docker-compose ps
echo ""
echo "服务地址: http://$(hostname -I | awk '{print $1}'):5001"
echo "或: http://115.190.77.57:5001"
echo ""

