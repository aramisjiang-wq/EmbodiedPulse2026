#!/bin/bash
# 启动应用并启用自动化更新

cd "$(dirname "$0")"

echo "===================================================="
echo "启动 Embodied Pulse 应用"
echo "===================================================="

# 设置环境变量
export AUTO_FETCH_ENABLED=true
export AUTO_FETCH_SCHEDULE="0 * * * *"  # 每小时整点执行

echo "✅ 环境变量已设置:"
echo "   AUTO_FETCH_ENABLED=$AUTO_FETCH_ENABLED"
echo "   AUTO_FETCH_SCHEDULE=$AUTO_FETCH_SCHEDULE"
echo ""

# 检查依赖
echo "检查依赖..."
python3 -c "import apscheduler" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ APScheduler 已安装"
else
    echo "⚠️  APScheduler 未安装，自动化更新将不可用"
    echo "   安装命令: pip install apscheduler"
fi

echo ""
echo "===================================================="
echo "启动服务器..."
echo "===================================================="
echo ""

# 启动应用
python3 app.py

