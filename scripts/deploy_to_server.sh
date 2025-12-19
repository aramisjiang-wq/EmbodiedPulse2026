#!/bin/bash
# 一键部署到服务器（需要配置SSH）

SERVER_USER="root"
SERVER_HOST="your-server-ip-or-domain"
SERVER_PATH="/srv/EmbodiedPulse2026"

echo "=========================================="
echo "部署到服务器"
echo "=========================================="
echo ""

# 检查是否有未提交的更改
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  有未提交的更改："
    git status --short
    echo ""
    read -p "是否先提交更改？(y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git add -A
        read -p "请输入提交信息: " commit_msg
        git commit -m "$commit_msg"
        git push
        echo "✅ 代码已提交并推送"
    fi
fi

echo ""
echo "连接到服务器: ${SERVER_USER}@${SERVER_HOST}"
echo ""

# 执行服务器端命令
ssh ${SERVER_USER}@${SERVER_HOST} << 'ENDSSH'
cd /srv/EmbodiedPulse2026
source venv/bin/activate

echo "1. 拉取最新代码..."
git pull

echo ""
echo "2. 检查Python语法..."
python3 -m py_compile auth_routes.py
if [ $? -eq 0 ]; then
    echo "✅ Python语法检查通过"
else
    echo "❌ Python语法检查失败"
    exit 1
fi

echo ""
echo "3. 重启服务..."
systemctl restart embodiedpulse

echo ""
echo "4. 等待服务启动..."
sleep 3

echo ""
echo "5. 检查服务状态..."
systemctl status embodiedpulse --no-pager -l | head -20

echo ""
echo "✅ 部署完成！"
ENDSSH

echo ""
echo "=========================================="
echo "部署完成"
echo "=========================================="

