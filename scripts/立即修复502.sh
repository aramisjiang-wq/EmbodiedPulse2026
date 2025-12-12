#!/bin/bash
# 立即修复502错误 - 在服务器上直接运行

PROJECT_DIR="/opt/EmbodiedPulse"

echo "=========================================="
echo "立即修复502错误"
echo "=========================================="

# 确保在项目目录
if [ ! -d "${PROJECT_DIR}" ]; then
    echo "创建项目目录..."
    mkdir -p ${PROJECT_DIR}
    cd ${PROJECT_DIR}
    git clone https://github.com/aramisjiang-wq/EmbodiedPulse2026.git .
else
    cd ${PROJECT_DIR}
fi

echo ""
echo "1. 更新代码到最新版本..."
git fetch origin main
git reset --hard origin/main
git clean -fd

echo ""
echo "2. 停止所有相关容器..."
docker-compose down 2>/dev/null || true
docker ps -a | grep -E "embodied|pulse" | awk '{print $1}' | xargs docker rm -f 2>/dev/null || true

echo ""
echo "3. 重新构建并启动..."
docker-compose up -d --build

echo ""
echo "4. 等待服务启动（30秒）..."
sleep 30

echo ""
echo "5. 检查服务状态..."
docker-compose ps

echo ""
echo "6. 查看服务日志..."
docker-compose logs --tail=30 web

echo ""
echo "7. 测试服务..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:5001 | grep -q "200"; then
    echo "   ✅ 服务正常运行！"
    echo "   访问: http://115.190.77.57:5001"
else
    echo "   ⚠️  服务可能还有问题"
    echo "   查看详细日志: docker-compose logs web"
fi

echo ""
echo "=========================================="

