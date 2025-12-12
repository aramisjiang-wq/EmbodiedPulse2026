#!/bin/bash
# 检查部署状态脚本

echo "=========================================="
echo "部署状态检查"
echo "=========================================="

# 1. 检查Git状态
echo ""
echo "1. Git状态："
echo "   当前分支: $(git branch --show-current)"
echo "   待推送提交数: $(git log origin/main..HEAD --oneline 2>/dev/null | wc -l | tr -d ' ')"
if [ $(git log origin/main..HEAD --oneline 2>/dev/null | wc -l | tr -d ' ') -gt 0 ]; then
    echo "   ⚠️  有未推送的提交，需要执行: git push origin main"
else
    echo "   ✅ 所有提交已推送"
fi

# 2. 检查.gitignore
echo ""
echo "2. .gitignore配置："
if grep -q "docs/项目文档/" .gitignore 2>/dev/null; then
    echo "   ✅ 项目文档文件夹已正确忽略"
else
    echo "   ⚠️  项目文档文件夹未在.gitignore中"
fi

# 3. 检查GitHub Actions配置
echo ""
echo "3. GitHub Actions配置："
if [ -f ".github/workflows/auto-deploy.yml" ]; then
    echo "   ✅ 自动部署工作流文件存在"
    if grep -q "SERVER_HOST" .github/workflows/auto-deploy.yml; then
        echo "   ✅ 工作流配置正确（使用Secrets）"
    else
        echo "   ⚠️  工作流配置可能不完整"
    fi
else
    echo "   ⚠️  自动部署工作流文件不存在"
fi

# 4. 检查本地代码
echo ""
echo "4. 本地代码检查："
if [ -f "app.py" ] && [ -f "templates/index.html" ]; then
    echo "   ✅ 核心文件存在"
else
    echo "   ⚠️  核心文件缺失"
fi

echo ""
echo "=========================================="
echo "下一步操作："
echo "=========================================="
echo "1. 推送代码到GitHub:"
echo "   git push origin main"
echo ""
echo "2. 在GitHub设置Secrets（如果还没设置）："
echo "   - 进入仓库 Settings → Secrets and variables → Actions"
echo "   - 添加: SERVER_HOST, SERVER_USER, SERVER_PASSWORD"
echo ""
echo "3. 验证自动部署："
echo "   - 推送代码后，在GitHub Actions标签查看部署状态"
echo "   - 访问: http://115.190.77.57:5001"
echo "=========================================="

