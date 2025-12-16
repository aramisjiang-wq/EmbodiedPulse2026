#!/bin/bash
# 完整修复服务器 - 修复权限并部署服务

set -e

echo "=========================================="
echo "完整修复服务器"
echo "=========================================="

# 1. 修复docker-compose权限
echo ""
echo "1. 修复docker-compose权限..."
chmod +x /usr/local/bin/docker-compose
ls -la /usr/local/bin/docker-compose

# 验证docker-compose
if docker-compose --version &> /dev/null; then
    echo "   ✅ docker-compose正常工作"
    docker-compose --version
else
    echo "   ⚠️  docker-compose仍有问题，重新安装..."
    rm -f /usr/local/bin/docker-compose
    curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    docker-compose --version
fi

# 2. 检查Docker服务
echo ""
echo "2. 检查Docker服务..."
if ! systemctl is-active --quiet docker; then
    echo "   启动Docker服务..."
    systemctl start docker
    systemctl enable docker
    sleep 5
fi

# 3. 准备项目目录
echo ""
echo "3. 准备项目目录..."
PROJECT_DIR="/opt/EmbodiedPulse"
REPO_URL="https://github.com/aramisjiang-wq/EmbodiedPulse2026.git"

if [ ! -d "${PROJECT_DIR}" ] || [ ! -d "${PROJECT_DIR}/.git" ]; then
    echo "   项目目录不存在或不是Git仓库，重新克隆..."
    cd /opt
    rm -rf EmbodiedPulse
    git clone ${REPO_URL} EmbodiedPulse
    cd EmbodiedPulse
else
    echo "   项目目录存在，更新代码..."
    cd ${PROJECT_DIR}
    git fetch origin main
    git reset --hard origin/main
    git clean -fd
fi

# 4. 验证关键文件
echo ""
echo "4. 验证关键文件..."
REQUIRED_FILES=("app.py" "docker-compose.yml" "Dockerfile" "templates/index.html")
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ $file (缺失)"
        exit 1
    fi
done

# 5. 停止旧容器
echo ""
echo "5. 停止旧容器..."
docker-compose down -v 2>/dev/null || true
docker ps -a | grep -E "embodied|pulse" | awk '{print $1}' | xargs docker rm -f 2>/dev/null || true

# 6. 清理资源
echo ""
echo "6. 清理Docker资源..."
docker system prune -f || true

# 7. 构建并启动
echo ""
echo "7. 构建并启动服务..."
docker-compose build --no-cache
docker-compose up -d

# 8. 等待启动
echo ""
echo "8. 等待服务启动（60秒）..."
sleep 60

# 9. 检查容器状态
echo ""
echo "9. 检查容器状态..."
docker-compose ps

# 10. 检查服务日志
echo ""
echo "10. 检查服务日志（最后30行）..."
docker-compose logs --tail=30 web

# 11. 测试服务
echo ""
echo "11. 测试服务..."
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
fi

echo ""
echo "=========================================="
echo "修复完成"
echo "=========================================="










