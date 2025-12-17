#!/bin/bash
# 修复docker-compose权限并重新部署

set -e

echo "=========================================="
echo "修复权限并重新部署"
echo "=========================================="

# 1. 修复docker-compose权限
echo ""
echo "1. 修复docker-compose权限..."
chmod +x /usr/local/bin/docker-compose
ls -la /usr/local/bin/docker-compose

# 2. 验证docker-compose
echo ""
echo "2. 验证docker-compose..."
docker-compose --version

# 3. 进入项目目录
echo ""
echo "3. 进入项目目录..."
cd /opt/EmbodiedPulse

# 4. 停止所有容器
echo ""
echo "4. 停止所有容器..."
docker-compose down 2>/dev/null || true
docker ps -a | grep -E "embodied|pulse" | awk '{print $1}' | xargs docker rm -f 2>/dev/null || true

# 5. 重新构建并启动
echo ""
echo "5. 重新构建并启动..."
docker-compose up -d --build

# 6. 等待启动
echo ""
echo "6. 等待服务启动（30秒）..."
sleep 30

# 7. 检查状态
echo ""
echo "7. 检查容器状态..."
docker-compose ps

# 8. 查看日志
echo ""
echo "8. 查看服务日志..."
docker-compose logs --tail=50 web

# 9. 测试服务
echo ""
echo "9. 测试服务..."
sleep 5
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5001 || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ 服务正常运行！HTTP状态码: $HTTP_CODE"
    echo "   访问: http://115.190.77.57:5001"
else
    echo "   ⚠️  服务可能还有问题，HTTP状态码: $HTTP_CODE"
    echo "   查看详细日志: docker-compose logs web"
fi

echo ""
echo "=========================================="

