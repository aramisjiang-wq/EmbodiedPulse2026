#!/bin/bash
# 检查服务器代码更新状态

SERVER_USER="${SERVER_USER:-root}"
SERVER_HOST="${SERVER_HOST:-essay.gradmotion.com}"
APP_DIR="${APP_DIR:-/srv/EmbodiedPulse2026}"

echo "=========================================="
echo "检查服务器代码更新状态"
echo "=========================================="
echo "服务器: ${SERVER_USER}@${SERVER_HOST}"
echo "项目目录: ${APP_DIR}"
echo ""

# 检查SSH连接
echo "1. 检查SSH连接..."
if ssh -o ConnectTimeout=5 "${SERVER_USER}@${SERVER_HOST}" "echo '连接成功'" > /dev/null 2>&1; then
    echo "✅ SSH连接正常"
else
    echo "❌ 无法连接到服务器"
    echo "请检查服务器地址和SSH配置"
    exit 1
fi

# 检查服务器上的最新提交
echo ""
echo "2. 检查服务器上的最新提交..."
ssh "${SERVER_USER}@${SERVER_HOST}" << EOF
cd ${APP_DIR}

echo "当前目录: \$(pwd)"
echo ""

# 检查是否是git仓库
if [ ! -d ".git" ]; then
    echo "❌ 不是Git仓库"
    exit 1
fi

# 获取最新提交
echo "服务器最新提交:"
git log --oneline -3

echo ""
echo "=========================================="
echo "3. 检查是否需要更新..."
echo "=========================================="

# 获取远程最新提交
git fetch origin main 2>/dev/null || echo "⚠️  Git fetch失败"

# 比较本地和远程
LOCAL_COMMIT=\$(git rev-parse HEAD)
REMOTE_COMMIT=\$(git rev-parse origin/main 2>/dev/null || echo "")

if [ -z "\$REMOTE_COMMIT" ]; then
    echo "⚠️  无法获取远程提交信息"
else
    echo "本地提交: \${LOCAL_COMMIT:0:8}"
    echo "远程提交: \${REMOTE_COMMIT:0:8}"
    
    if [ "\$LOCAL_COMMIT" = "\$REMOTE_COMMIT" ]; then
        echo "✅ 服务器代码已是最新版本"
    else
        echo "⚠️  服务器代码需要更新"
        echo ""
        echo "本地缺少的提交:"
        git log --oneline HEAD..origin/main 2>/dev/null || echo "无法获取"
    fi
fi

echo ""
echo "=========================================="
echo "4. 检查文件修改时间..."
echo "=========================================="

if [ -f "templates/bilibili.html" ]; then
    echo "templates/bilibili.html 修改时间:"
    ls -lh templates/bilibili.html | awk '{print \$6, \$7, \$8}'
    
    # 检查文件是否包含我们的修改
    if grep -q "年度播放量挂件高度 - 优化" templates/bilibili.html; then
        echo "✅ 文件包含最新优化代码"
    else
        echo "⚠️  文件可能未更新"
    fi
else
    echo "❌ 文件不存在"
fi

EOF

echo ""
echo "=========================================="
echo "检查完成"
echo "=========================================="

