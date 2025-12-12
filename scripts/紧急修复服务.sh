#!/bin/bash
# 紧急修复服务脚本 - 解决502错误和服务崩溃问题

set -e

echo "=========================================="
echo "紧急修复服务"
echo "=========================================="

PROJECT_DIR="/opt/EmbodiedPulse"
cd ${PROJECT_DIR} || {
    echo "项目目录不存在，正在创建..."
    mkdir -p ${PROJECT_DIR}
    cd ${PROJECT_DIR}
    git clone https://github.com/aramisjiang-wq/EmbodiedPulse2026.git .
}

# 1. 检查Docker服务
echo ""
echo "1. 检查Docker服务..."
if ! systemctl is-active --quiet docker; then
    echo "   启动Docker服务..."
    systemctl start docker
    sleep 5
fi

# 2. 停止所有相关容器
echo ""
echo "2. 停止所有相关容器..."
docker-compose down -v 2>/dev/null || true
docker ps -a | grep -E "embodied|pulse" | awk '{print $1}' | xargs docker rm -f 2>/dev/null || true

# 3. 清理资源
echo ""
echo "3. 清理Docker资源..."
docker system prune -f || true

# 4. 更新代码
echo ""
echo "4. 更新代码..."
git fetch origin main
git reset --hard origin/main
git clean -fd

# 5. 检查docker-compose.yml
echo ""
echo "5. 检查配置文件..."
if [ ! -f "docker-compose.yml" ]; then
    echo "   ❌ docker-compose.yml不存在"
    exit 1
fi

# 6. 重新构建（不使用缓存）
echo ""
echo "6. 重新构建镜像（不使用缓存）..."
docker-compose build --no-cache

# 7. 启动服务
echo ""
echo "7. 启动服务..."
docker-compose up -d

# 8. 等待服务启动
echo ""
echo "8. 等待服务启动（60秒）..."
sleep 60

# 9. 检查容器状态
echo ""
echo "9. 检查容器状态..."
docker-compose ps

# 10. 检查服务日志
echo ""
echo "10. 检查服务日志..."
echo "=== Web容器日志 ==="
docker-compose logs --tail=50 web || echo "无法获取日志"

echo ""
echo "=== Postgres容器日志 ==="
docker-compose logs --tail=20 postgres || echo "无法获取日志"

# 11. 检查服务健康
echo ""
echo "11. 检查服务健康..."
sleep 10

# 检查容器是否运行
WEB_CONTAINER=$(docker-compose ps -q web)
if [ -z "$WEB_CONTAINER" ]; then
    echo "   ❌ Web容器未运行"
    echo "   查看详细日志:"
    docker-compose logs web
    exit 1
fi

# 检查容器健康状态
if ! docker ps | grep -q "$WEB_CONTAINER.*Up"; then
    echo "   ⚠️  Web容器状态异常"
    docker-compose ps
    docker-compose logs --tail=100 web
    exit 1
fi

# 测试HTTP连接
echo ""
echo "12. 测试HTTP连接..."
for i in {1..5}; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 http://localhost:5001 || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        echo "   ✅ 服务正常运行！HTTP状态码: $HTTP_CODE"
        echo "   访问: http://115.190.77.57:5001"
        break
    else
        echo "   尝试 $i/5: HTTP状态码 $HTTP_CODE，等待10秒后重试..."
        sleep 10
    fi
done

if [ "$HTTP_CODE" != "200" ]; then
    echo ""
    echo "   ❌ 服务仍然无法访问"
    echo "   诊断信息:"
    echo "   - 容器状态:"
    docker-compose ps
    echo "   - 最新日志:"
    docker-compose logs --tail=100 web
    echo ""
    echo "   请检查："
    echo "   1. 端口5001是否被占用: netstat -tulpn | grep 5001"
    echo "   2. 防火墙设置: firewall-cmd --list-ports"
    echo "   3. 容器资源: docker stats --no-stream"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ 修复完成！服务正常运行"
echo "=========================================="
echo "服务地址: http://115.190.77.57:5001"
echo ""
echo "查看日志: docker-compose logs -f web"
echo "停止服务: docker-compose down"
echo "重启服务: docker-compose restart"
echo "=========================================="

