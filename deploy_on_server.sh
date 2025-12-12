#!/bin/bash
# 在服务器上直接运行的完整部署脚本
# 使用方法: 将此脚本上传到服务器后执行: bash deploy_on_server.sh

set -e

PROJECT_DIR="/opt/EmbodiedPulse"
REPO_URL="https://github.com/aramisjiang-wq/EmbodiedPulse2026.git"

echo "=========================================="
echo "Embodied Pulse Docker 部署脚本"
echo "=========================================="

# 1. 检查并安装Docker
if ! command -v docker &> /dev/null; then
    echo "[1/6] 安装Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl start docker
    systemctl enable docker
    rm get-docker.sh
    echo "✅ Docker安装完成"
else
    echo "[1/6] ✅ Docker已安装: $(docker --version)"
fi

# 2. 检查并安装Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "[2/6] 安装Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    echo "✅ Docker Compose安装完成"
else
    echo "[2/6] ✅ Docker Compose已安装: $(docker-compose --version)"
fi

# 3. 创建项目目录
echo "[3/6] 准备项目目录..."
mkdir -p ${PROJECT_DIR}
cd ${PROJECT_DIR}

# 4. 克隆或更新代码
echo "[4/6] 获取代码..."
if [ -d ".git" ]; then
    echo "更新代码..."
    git pull origin main || echo "⚠️ Git pull失败，继续使用现有代码"
else
    echo "克隆代码..."
    git clone ${REPO_URL} .
fi

# 5. 停止现有容器
echo "[5/6] 停止现有容器..."
docker-compose down || true

# 6. 构建并启动服务
echo "[6/6] 构建并启动服务..."
docker-compose up -d --build

# 7. 等待服务启动
echo "等待服务启动..."
sleep 20

# 8. 初始化数据库
echo "初始化数据库..."
docker-compose exec -T web python3 init_database.py || echo "⚠️ 数据库初始化可能已存在"

# 9. 检查服务状态
echo ""
echo "=========================================="
echo "服务状态:"
echo "=========================================="
docker-compose ps

# 10. 检查端口
echo ""
echo "=========================================="
echo "✅ 部署完成！"
echo "=========================================="
SERVER_IP=$(hostname -I | awk '{print $1}')
echo "服务地址: http://${SERVER_IP}:5001"
echo "或: http://115.190.77.57:5001"
echo ""
echo "常用命令:"
echo "  查看日志: cd ${PROJECT_DIR} && docker-compose logs -f"
echo "  查看web日志: cd ${PROJECT_DIR} && docker-compose logs -f web"
echo "  停止服务: cd ${PROJECT_DIR} && docker-compose down"
echo "  重启服务: cd ${PROJECT_DIR} && docker-compose restart"
echo "  查看状态: cd ${PROJECT_DIR} && docker-compose ps"
echo "=========================================="

# 11. 检查防火墙
echo ""
echo "如果无法访问，请检查防火墙:"
echo "  CentOS/RHEL: firewall-cmd --permanent --add-port=5001/tcp && firewall-cmd --reload"
echo "  Ubuntu/Debian: ufw allow 5001/tcp && ufw reload"
echo ""

