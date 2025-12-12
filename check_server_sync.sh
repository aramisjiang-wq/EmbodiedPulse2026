#!/bin/bash
# 服务器端代码同步检查脚本
# 在服务器上运行此脚本检查代码同步状态

set -e

PROJECT_DIR="/opt/EmbodiedPulse"
REPO_URL="https://github.com/aramisjiang-wq/EmbodiedPulse2026.git"

echo "=========================================="
echo "服务器代码同步状态检查"
echo "=========================================="

# 1. 检查项目目录
echo ""
echo "1. 项目目录检查："
if [ -d "${PROJECT_DIR}" ]; then
    echo "   ✅ 项目目录存在: ${PROJECT_DIR}"
    cd ${PROJECT_DIR}
else
    echo "   ❌ 项目目录不存在: ${PROJECT_DIR}"
    echo "   需要先初始化项目"
    exit 1
fi

# 2. 检查Git配置
echo ""
echo "2. Git配置检查："
if [ -d ".git" ]; then
    echo "   ✅ Git仓库已初始化"
    echo "   远程仓库: $(git remote get-url origin 2>/dev/null || echo '未配置')"
else
    echo "   ❌ Git仓库未初始化"
    echo "   需要执行: git clone ${REPO_URL} ."
    exit 1
fi

# 3. 检查当前代码版本
echo ""
echo "3. 当前代码版本："
CURRENT_COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "未知")
CURRENT_COMMIT_SHORT=$(git rev-parse --short HEAD 2>/dev/null || echo "未知")
echo "   当前commit: ${CURRENT_COMMIT_SHORT}"
echo "   最后提交信息: $(git log -1 --pretty=format:'%s' 2>/dev/null || echo '未知')"
echo "   提交时间: $(git log -1 --pretty=format:'%cd' --date=format:'%Y-%m-%d %H:%M:%S' 2>/dev/null || echo '未知')"

# 4. 检查远程最新版本
echo ""
echo "4. 远程代码版本："
git fetch origin main > /dev/null 2>&1 || echo "   ⚠️  无法获取远程更新"
REMOTE_COMMIT=$(git rev-parse origin/main 2>/dev/null || echo "未知")
REMOTE_COMMIT_SHORT=$(git rev-parse --short origin/main 2>/dev/null || echo "未知")
echo "   远程commit: ${REMOTE_COMMIT_SHORT}"
echo "   远程最后提交: $(git log -1 --pretty=format:'%s' origin/main 2>/dev/null || echo '未知')"

# 5. 比较版本
echo ""
echo "5. 代码同步状态："
if [ "${CURRENT_COMMIT}" = "${REMOTE_COMMIT}" ] && [ "${CURRENT_COMMIT}" != "未知" ]; then
    echo "   ✅ 代码已是最新版本"
    SYNC_STATUS="已同步"
else
    echo "   ⚠️  代码不是最新版本"
    echo "   需要执行: git pull origin main"
    SYNC_STATUS="未同步"
fi

# 6. 检查Docker服务
echo ""
echo "6. Docker服务状态："
if command -v docker-compose &> /dev/null; then
    if [ -f "docker-compose.yml" ]; then
        echo "   ✅ docker-compose.yml存在"
        echo "   容器状态:"
        docker-compose ps 2>/dev/null || echo "   未运行"
    else
        echo "   ⚠️  docker-compose.yml不存在"
    fi
else
    echo "   ⚠️  docker-compose未安装"
fi

# 7. 检查服务访问
echo ""
echo "7. 服务访问检查："
SERVER_IP=$(hostname -I | awk '{print $1}' || echo "115.190.77.57")
if curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 http://localhost:5001 2>/dev/null | grep -q "200"; then
    echo "   ✅ 服务正常运行"
    echo "   访问地址: http://${SERVER_IP}:5001"
else
    echo "   ⚠️  服务无法访问（可能未启动）"
fi

# 8. 总结
echo ""
echo "=========================================="
echo "检查总结"
echo "=========================================="
echo "代码同步状态: ${SYNC_STATUS}"
if [ "${SYNC_STATUS}" = "未同步" ]; then
    echo ""
    echo "需要执行以下命令更新代码："
    echo "  cd ${PROJECT_DIR}"
    echo "  git pull origin main"
    echo "  docker-compose down"
    echo "  docker-compose up -d --build"
fi
echo "=========================================="

