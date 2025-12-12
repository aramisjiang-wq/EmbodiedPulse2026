#!/bin/bash
# 部署脚本 - 传统服务器部署

set -e  # 遇到错误立即退出

echo "=========================================="
echo "Robotics ArXiv Daily 部署脚本"
echo "=========================================="

# 检查是否在项目根目录
if [ ! -f "app.py" ]; then
    echo "错误: 请在项目根目录运行此脚本"
    exit 1
fi

# 1. 更新代码
echo "1. 更新代码..."
git pull origin main || echo "警告: Git pull失败，继续使用当前代码"

# 2. 激活虚拟环境
if [ -d "venv" ]; then
    echo "2. 激活虚拟环境..."
    source venv/bin/activate
else
    echo "2. 创建虚拟环境..."
    python3 -m venv venv
    source venv/bin/activate
fi

# 3. 安装/更新依赖
echo "3. 安装依赖..."
pip install --upgrade pip
pip install -r requirements.txt

# 4. 初始化数据库（如果不存在）
if [ ! -f "papers.db" ]; then
    echo "4. 初始化数据库..."
    python3 init_database.py
else
    echo "4. 数据库已存在，跳过初始化"
fi

# 5. 重启服务（如果使用systemd）
if systemctl is-active --quiet robotics-arxiv 2>/dev/null; then
    echo "5. 重启服务..."
    sudo systemctl restart robotics-arxiv
    echo "✅ 服务已重启"
elif [ -f "docker-compose.yml" ] && docker-compose ps | grep -q "robotics-arxiv-web"; then
    echo "5. 重启Docker容器..."
    docker-compose restart web
    echo "✅ 容器已重启"
else
    echo "5. 未检测到运行中的服务，请手动启动"
fi

echo "=========================================="
echo "✅ 部署完成！"
echo "=========================================="

