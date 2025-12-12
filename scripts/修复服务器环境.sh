#!/bin/bash
# 修复服务器环境 - 安装依赖并修复docker-compose问题

set -e

echo "=========================================="
echo "修复服务器环境"
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

# 2. 检查并修复docker-compose
echo ""
echo "2. 检查docker-compose..."
if command -v docker-compose &> /dev/null; then
    # 测试docker-compose是否正常工作
    if docker-compose --version &> /dev/null; then
        echo "   ✅ docker-compose正常工作"
    else
        echo "   ⚠️  docker-compose有问题，重新安装..."
        rm -f /usr/local/bin/docker-compose
    fi
fi

# 3. 安装/重新安装docker-compose
if ! command -v docker-compose &> /dev/null || ! docker-compose --version &> /dev/null; then
    echo ""
    echo "3. 安装docker-compose..."
    # 删除旧版本
    rm -f /usr/local/bin/docker-compose
    rm -f /usr/bin/docker-compose
    
    # 安装新版本
    curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    
    # 验证安装
    if docker-compose --version &> /dev/null; then
        echo "   ✅ docker-compose安装成功"
        docker-compose --version
    else
        echo "   ❌ docker-compose安装失败"
        exit 1
    fi
fi

# 4. 检查Docker服务
echo ""
echo "4. 检查Docker服务..."
if ! systemctl is-active --quiet docker; then
    echo "   启动Docker服务..."
    systemctl start docker
    sleep 5
fi

# 5. 测试Docker
echo ""
echo "5. 测试Docker..."
if docker ps &> /dev/null; then
    echo "   ✅ Docker正常工作"
else
    echo "   ⚠️  Docker可能有问题"
    systemctl restart docker
    sleep 5
fi

# 6. 检查项目目录
echo ""
echo "6. 检查项目目录..."
PROJECT_DIR="/opt/EmbodiedPulse"
if [ ! -d "${PROJECT_DIR}" ]; then
    echo "   项目目录不存在，正在克隆..."
    mkdir -p ${PROJECT_DIR}
    cd ${PROJECT_DIR}
    git clone https://github.com/aramisjiang-wq/EmbodiedPulse2026.git .
else
    echo "   项目目录存在"
    cd ${PROJECT_DIR}
    
    # 更新代码
    echo "   更新代码..."
    git fetch origin main || {
        echo "   Git fetch失败，尝试重新克隆..."
        cd /opt
        rm -rf EmbodiedPulse
        git clone https://github.com/aramisjiang-wq/EmbodiedPulse2026.git EmbodiedPulse
        cd EmbodiedPulse
    }
    git reset --hard origin/main
    git clean -fd
fi

echo ""
echo "=========================================="
echo "✅ 环境修复完成"
echo "=========================================="
echo "现在可以执行修复服务脚本："
echo "  cd /opt/EmbodiedPulse"
echo "  bash scripts/紧急修复服务.sh"
echo "=========================================="

