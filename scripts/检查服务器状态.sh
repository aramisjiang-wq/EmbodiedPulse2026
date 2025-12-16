#!/bin/bash
# 检查服务器状态和代码完整性

echo "=========================================="
echo "服务器状态检查"
echo "=========================================="

PROJECT_DIR="/opt/EmbodiedPulse"

# 1. 检查项目目录
echo ""
echo "1. 检查项目目录..."
if [ -d "${PROJECT_DIR}" ]; then
    echo "   ✅ 项目目录存在: ${PROJECT_DIR}"
    cd ${PROJECT_DIR}
else
    echo "   ❌ 项目目录不存在: ${PROJECT_DIR}"
    exit 1
fi

# 2. 检查Git状态
echo ""
echo "2. 检查Git状态..."
if [ -d ".git" ]; then
    echo "   ✅ Git仓库已初始化"
    echo "   远程仓库: $(git remote get-url origin 2>/dev/null || echo '未配置')"
    echo "   当前分支: $(git branch --show-current 2>/dev/null || echo '未知')"
    
    # 检查代码是否最新
    echo ""
    echo "   检查代码版本..."
    git fetch origin main > /dev/null 2>&1
    CURRENT_COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "未知")
    REMOTE_COMMIT=$(git rev-parse origin/main 2>/dev/null || echo "未知")
    
    if [ "${CURRENT_COMMIT}" = "${REMOTE_COMMIT}" ] && [ "${CURRENT_COMMIT}" != "未知" ]; then
        echo "   ✅ 代码已是最新版本"
        echo "   Commit: $(git rev-parse --short HEAD)"
    else
        echo "   ⚠️  代码不是最新版本"
        echo "   当前: $(git rev-parse --short HEAD 2>/dev/null || echo '未知')"
        echo "   远程: $(git rev-parse --short origin/main 2>/dev/null || echo '未知')"
    fi
else
    echo "   ❌ Git仓库未初始化"
fi

# 3. 检查关键文件
echo ""
echo "3. 检查关键文件..."
FILES=("app.py" "docker-compose.yml" "Dockerfile" "requirements.txt" "templates/index.html" "static/js/app.js")
MISSING_FILES=()

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ $file (缺失)"
        MISSING_FILES+=("$file")
    fi
done

if [ ${#MISSING_FILES[@]} -gt 0 ]; then
    echo ""
    echo "   ⚠️  缺失文件: ${MISSING_FILES[*]}"
fi

# 4. 检查Docker服务
echo ""
echo "4. 检查Docker服务..."
if command -v docker &> /dev/null; then
    echo "   ✅ Docker已安装"
    echo "   版本: $(docker --version)"
    
    if systemctl is-active --quiet docker; then
        echo "   ✅ Docker服务运行中"
    else
        echo "   ⚠️  Docker服务未运行"
    fi
else
    echo "   ❌ Docker未安装"
fi

# 5. 检查docker-compose
echo ""
echo "5. 检查docker-compose..."
if command -v docker-compose &> /dev/null; then
    echo "   ✅ docker-compose已安装"
    docker-compose --version 2>/dev/null || echo "   ⚠️  docker-compose有问题"
else
    echo "   ❌ docker-compose未安装"
fi

# 6. 检查容器状态
echo ""
echo "6. 检查容器状态..."
if [ -f "docker-compose.yml" ]; then
    if docker-compose ps &> /dev/null; then
        echo "   容器状态:"
        docker-compose ps
    else
        echo "   ⚠️  无法获取容器状态（可能未运行）"
    fi
else
    echo "   ⚠️  docker-compose.yml不存在"
fi

# 7. 检查服务访问
echo ""
echo "7. 检查服务访问..."
SERVER_IP=$(hostname -I | awk '{print $1}' || echo "115.190.77.57")
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:5001 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ 服务正常运行"
    echo "   HTTP状态码: $HTTP_CODE"
    echo "   访问地址: http://${SERVER_IP}:5001"
else
    echo "   ⚠️  服务无法访问"
    echo "   HTTP状态码: $HTTP_CODE"
    echo "   可能原因: 服务未启动、端口被占用、防火墙阻止"
fi

# 8. 检查端口占用
echo ""
echo "8. 检查端口占用..."
if command -v netstat &> /dev/null; then
    PORT_5001=$(netstat -tulpn 2>/dev/null | grep ":5001" || echo "")
    if [ -n "$PORT_5001" ]; then
        echo "   5001端口占用情况:"
        echo "$PORT_5001"
    else
        echo "   ⚠️  5001端口未被占用（服务可能未启动）"
    fi
fi

# 9. 检查容器日志（如果有）
echo ""
echo "9. 检查容器日志（最后20行）..."
if docker-compose ps | grep -q "Up"; then
    echo "   Web容器日志:"
    docker-compose logs --tail=20 web 2>/dev/null || echo "   无法获取日志"
else
    echo "   ⚠️  容器未运行，无法查看日志"
fi

echo ""
echo "=========================================="
echo "检查完成"
echo "=========================================="










