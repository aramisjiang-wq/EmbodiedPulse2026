#!/bin/bash
# 远程服务器Docker部署脚本

set -e

SERVER_IP="115.190.77.57"
SERVER_USER="root"
SERVER_PASSWORD="ash@2025"
PROJECT_NAME="EmbodiedPulse"
REMOTE_DIR="/opt/${PROJECT_NAME}"

echo "=========================================="
echo "开始部署到服务器: ${SERVER_IP}"
echo "=========================================="

# 1. 检查本地是否有代码
if [ ! -f "docker-compose.yml" ]; then
    echo "错误: 请在项目根目录运行此脚本"
    exit 1
fi

# 2. 使用sshpass连接到服务器并执行部署命令
echo "正在连接到服务器..."

sshpass -p "${SERVER_PASSWORD}" ssh -o StrictHostKeyChecking=no ${SERVER_USER}@${SERVER_IP} << 'ENDSSH'
    set -e
    
    echo "=========================================="
    echo "在服务器上开始部署..."
    echo "=========================================="
    
    # 检查Docker是否安装
    if ! command -v docker &> /dev/null; then
        echo "安装Docker..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh
        systemctl start docker
        systemctl enable docker
        rm get-docker.sh
    fi
    
    # 检查Docker Compose是否安装
    if ! command -v docker-compose &> /dev/null; then
        echo "安装Docker Compose..."
        curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
    fi
    
    # 创建项目目录
    PROJECT_DIR="/opt/EmbodiedPulse"
    mkdir -p ${PROJECT_DIR}
    cd ${PROJECT_DIR}
    
    echo "=========================================="
    echo "✅ Docker环境检查完成"
    echo "=========================================="
ENDSSH

# 3. 使用rsync同步代码到服务器（需要安装rsync和sshpass）
echo "同步代码到服务器..."
sshpass -p "${SERVER_PASSWORD}" rsync -avz --exclude '.git' --exclude '__pycache__' --exclude '*.pyc' --exclude '*.db' --exclude 'venv' --exclude '.env' \
    ./ ${SERVER_USER}@${SERVER_IP}:${REMOTE_DIR}/

# 4. 在服务器上启动Docker服务
echo "在服务器上启动Docker服务..."
sshpass -p "${SERVER_PASSWORD}" ssh -o StrictHostKeyChecking=no ${SERVER_USER}@${SERVER_IP} << ENDSSH
    set -e
    cd ${REMOTE_DIR}
    
    echo "停止现有容器（如果存在）..."
    docker-compose down || true
    
    echo "构建并启动服务..."
    docker-compose up -d --build
    
    echo "等待服务启动..."
    sleep 10
    
    echo "检查服务状态..."
    docker-compose ps
    
    echo "=========================================="
    echo "✅ 部署完成！"
    echo "=========================================="
    echo "服务地址: http://${SERVER_IP}:5001"
    echo ""
    echo "查看日志: docker-compose logs -f"
    echo "停止服务: docker-compose down"
    echo "重启服务: docker-compose restart"
ENDSSH

echo "=========================================="
echo "✅ 远程部署完成！"
echo "=========================================="
echo "服务地址: http://${SERVER_IP}:5001"
echo ""

