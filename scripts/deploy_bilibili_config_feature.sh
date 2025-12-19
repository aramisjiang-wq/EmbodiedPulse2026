#!/bin/bash
# 部署B站配置信息展示功能到服务器

echo "=========================================="
echo "部署B站配置信息展示功能"
echo "=========================================="
echo ""

# 检查Git状态
echo "1. 检查Git状态..."
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  有未提交的更改，请先提交："
    git status --short
    echo ""
    read -p "是否继续部署？(y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "部署已取消"
        exit 1
    fi
else
    echo "✅ Git工作区干净"
fi

echo ""
echo "2. 需要更新的文件："
echo "   - auth_routes.py (新增配置API接口)"
echo "   - templates/admin_bilibili.html (新增配置展示区域)"
echo "   - static/js/admin_bilibili.js (新增配置加载函数)"
echo ""

read -p "确认部署到服务器？(y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "部署已取消"
    exit 1
fi

echo ""
echo "3. 部署步骤："
echo "   a) 推送到Git仓库"
echo "   b) 在服务器上拉取最新代码"
echo "   c) 重启服务"
echo ""

# 推送到Git（如果需要）
read -p "是否推送到Git？(y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "推送代码到Git..."
    git add auth_routes.py templates/admin_bilibili.html static/js/admin_bilibili.js
    git commit -m "feat: 添加B站管理端系统配置信息展示功能"
    git push
    echo "✅ 代码已推送到Git"
fi

echo ""
echo "4. 在服务器上执行以下命令："
echo "=========================================="
echo "cd /srv/EmbodiedPulse2026"
echo "source venv/bin/activate"
echo "git pull"
echo "systemctl restart embodiedpulse"
echo "systemctl status embodiedpulse --no-pager -l | head -20"
echo "=========================================="
echo ""
echo "或者使用SSH一键部署："
echo "ssh root@your-server 'cd /srv/EmbodiedPulse2026 && source venv/bin/activate && git pull && systemctl restart embodiedpulse'"
echo ""

