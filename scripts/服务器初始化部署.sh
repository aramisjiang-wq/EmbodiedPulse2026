#!/bin/bash
# 服务器初始化部署脚本 - 完整部署流程

set -e

echo "=========================================="
echo "服务器初始化部署"
echo "=========================================="

PROJECT_DIR="/opt/EmbodiedPulse"
REPO_URL="https://github.com/aramisjiang-wq/EmbodiedPulse2026.git"

# 1. 安装必要工具
echo ""
echo "1. 检查并安装必要工具..."

# 安装Git
if ! command -v git &> /dev/null; then
    echo "   安装Git..."
    apt update
    apt install -y git
fi

# 安装Docker
if ! command -v docker &> /dev/null; then
    echo "   安装Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl start docker
    systemctl enable docker
    rm get-docker.sh
fi

# 安装Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "   安装Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# 2. 准备项目目录
echo ""
echo "2. 准备项目目录..."

if [ -d "${PROJECT_DIR}" ]; then
    echo "   项目目录已存在，检查是否为Git仓库..."
    cd ${PROJECT_DIR}
    
    if [ ! -d ".git" ]; then
        echo "   不是Git仓库，备份并重新克隆..."
        cd /opt
        mv EmbodiedPulse EmbodiedPulse_backup_$(date +%Y%m%d_%H%M%S) 2>/dev/null || rm -rf EmbodiedPulse
        git clone ${REPO_URL} EmbodiedPulse
        cd EmbodiedPulse
    else
        echo "   是Git仓库，更新代码..."
        git fetch origin main
        git reset --hard origin/main
        git clean -fd
    fi
else
    echo "   项目目录不存在，克隆项目..."
    mkdir -p /opt
    cd /opt
    git clone ${REPO_URL} EmbodiedPulse
    cd EmbodiedPulse
fi

# 3. 验证关键文件
echo ""
echo "3. 验证关键文件..."
REQUIRED_FILES=("app.py" "docker-compose.yml" "Dockerfile" "requirements.txt" "templates/index.html")
MISSING=0

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "   ❌ 缺失: $file"
        MISSING=1
    else
        echo "   ✅ $file"
    fi
done

if [ $MISSING -eq 1 ]; then
    echo "   ⚠️  关键文件缺失，重新克隆..."
    cd /opt
    rm -rf EmbodiedPulse
    git clone ${REPO_URL} EmbodiedPulse
    cd EmbodiedPulse
fi

# 4. 停止旧容器
echo ""
echo "4. 停止旧容器..."
docker-compose down -v 2>/dev/null || true
docker ps -a | grep -E "embodied|pulse" | awk '{print $1}' | xargs docker rm -f 2>/dev/null || true

# 5. 清理资源
echo ""
echo "5. 清理Docker资源..."
docker system prune -f || true

# 6. 构建并启动
echo ""
echo "6. 构建并启动服务..."
docker-compose build --no-cache
docker-compose up -d

# 7. 等待服务启动
echo ""
echo "7. 等待服务启动（60秒）..."
sleep 60

# 8. 检查容器状态
echo ""
echo "8. 检查容器状态..."
docker-compose ps

# 9. 检查服务日志
echo ""
echo "9. 检查服务日志（最后30行）..."
docker-compose logs --tail=30 web

# 10. 测试服务
echo ""
echo "10. 测试服务..."
sleep 10

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 http://localhost:5001 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ 服务正常运行！"
    echo "   HTTP状态码: $HTTP_CODE"
    echo "   访问地址: http://115.190.77.57:5001"
else
    echo "   ⚠️  服务可能还有问题"
    echo "   HTTP状态码: $HTTP_CODE"
    echo ""
    echo "   查看详细日志:"
    docker-compose logs --tail=50 web
    echo ""
    echo "   检查容器状态:"
    docker-compose ps
fi

echo ""
echo "=========================================="
echo "部署完成"
echo "=========================================="

