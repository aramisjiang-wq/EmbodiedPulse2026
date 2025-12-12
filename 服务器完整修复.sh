#!/bin/bash
# 服务器完整修复脚本 - 包含所有依赖安装

set -e

echo "=========================================="
echo "服务器完整修复 - 安装依赖并部署"
echo "=========================================="

# 1. 安装Git
echo ""
echo "1. 安装Git..."
if ! command -v git &> /dev/null; then
    apt update
    apt install -y git
    echo "   ✅ Git已安装"
else
    echo "   ✅ Git已存在"
fi

# 2. 安装Docker
echo ""
echo "2. 安装Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl start docker
    systemctl enable docker
    rm get-docker.sh
    echo "   ✅ Docker已安装"
else
    echo "   ✅ Docker已存在"
fi

# 3. 安装Docker Compose
echo ""
echo "3. 安装Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    echo "   ✅ Docker Compose已安装"
else
    echo "   ✅ Docker Compose已存在"
fi

# 4. 克隆或更新项目
echo ""
echo "4. 准备项目目录..."
PROJECT_DIR="/opt/EmbodiedPulse"
if [ ! -d "${PROJECT_DIR}" ]; then
    echo "   项目目录不存在，正在克隆..."
    mkdir -p ${PROJECT_DIR}
    cd ${PROJECT_DIR}
    git clone https://github.com/aramisjiang-wq/EmbodiedPulse2026.git .
else
    echo "   项目目录存在，更新代码..."
    cd ${PROJECT_DIR}
    git fetch origin main
    git reset --hard origin/main
    git clean -fd
fi

# 5. 停止旧容器
echo ""
echo "5. 停止旧容器..."
docker-compose down 2>/dev/null || true
docker ps -a | grep -E "embodied|pulse" | awk '{print $1}' | xargs docker rm -f 2>/dev/null || true

# 6. 构建并启动
echo ""
echo "6. 构建并启动服务..."
docker-compose up -d --build

# 7. 等待启动
echo ""
echo "7. 等待服务启动（30秒）..."
sleep 30

# 8. 检查状态
echo ""
echo "8. 检查容器状态..."
docker-compose ps

# 9. 查看日志
echo ""
echo "9. 查看服务日志..."
docker-compose logs --tail=30 web

# 10. 测试服务
echo ""
echo "10. 测试服务..."
sleep 5
if curl -s -o /dev/null -w "%{http_code}" http://localhost:5001 | grep -q "200"; then
    echo "   ✅ 服务正常运行！"
    echo "   访问: http://115.190.77.57:5001"
else
    echo "   ⚠️  服务可能还有问题"
    echo "   查看详细日志: docker-compose logs web"
fi

echo ""
echo "=========================================="
echo "修复完成"
echo "=========================================="

