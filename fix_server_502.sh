#!/bin/bash
# 修复服务器502错误的脚本
# 在服务器上运行此脚本

set -e

PROJECT_DIR="/opt/EmbodiedPulse"
REPO_URL="https://github.com/aramisjiang-wq/EmbodiedPulse2026.git"

echo "=========================================="
echo "修复服务器502错误"
echo "=========================================="

# 1. 检查项目目录
echo ""
echo "1. 检查项目目录..."
if [ ! -d "${PROJECT_DIR}" ]; then
    echo "   项目目录不存在，正在创建..."
    mkdir -p ${PROJECT_DIR}
    cd ${PROJECT_DIR}
    git clone ${REPO_URL} .
else
    echo "   ✅ 项目目录存在"
    cd ${PROJECT_DIR}
fi

# 2. 确保代码是最新的
echo ""
echo "2. 更新代码..."
if [ -d ".git" ]; then
    git fetch origin main
    git reset --hard origin/main
    git clean -fd
    echo "   ✅ 代码已更新"
else
    echo "   Git仓库不存在，正在克隆..."
    git clone ${REPO_URL} .
fi

# 3. 检查Docker
echo ""
echo "3. 检查Docker..."
if ! command -v docker &> /dev/null; then
    echo "   安装Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl start docker
    systemctl enable docker
    rm get-docker.sh
fi

if ! command -v docker-compose &> /dev/null; then
    echo "   安装Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# 4. 停止所有容器
echo ""
echo "4. 停止旧容器..."
docker-compose down || true
docker ps -a | grep embodied-pulse | awk '{print $1}' | xargs docker rm -f 2>/dev/null || true

# 5. 清理旧的镜像（可选）
echo ""
echo "5. 清理资源..."
docker system prune -f || true

# 6. 构建并启动
echo ""
echo "6. 构建并启动服务..."
docker-compose up -d --build

# 7. 等待服务启动
echo ""
echo "7. 等待服务启动..."
sleep 30

# 8. 检查容器状态
echo ""
echo "8. 检查容器状态..."
docker-compose ps

# 9. 检查日志
echo ""
echo "9. 检查服务日志（最后20行）..."
docker-compose logs --tail=20 web

# 10. 测试服务
echo ""
echo "10. 测试服务..."
sleep 5
if curl -s -o /dev/null -w "%{http_code}" http://localhost:5001 | grep -q "200"; then
    echo "   ✅ 服务正常运行"
else
    echo "   ⚠️  服务可能还有问题，查看日志："
    echo "   docker-compose logs web"
fi

echo ""
echo "=========================================="
echo "修复完成"
echo "=========================================="
echo "服务地址: http://115.190.77.57:5001"
echo ""
echo "如果还有问题，查看日志："
echo "  cd ${PROJECT_DIR}"
echo "  docker-compose logs -f web"
echo "=========================================="

