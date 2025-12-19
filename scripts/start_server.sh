#!/bin/bash
# 启动服务器脚本

cd /srv/EmbodiedPulse2026 || exit 1

echo "============================================================"
echo "启动Embodied Pulse服务"
echo "============================================================"
echo ""

# 1. 检查服务状态
echo "【1. 检查当前服务状态】"
echo "----------------------------------------"
if systemctl is-active --quiet embodiedpulse; then
    echo "⚠️  服务正在运行，先停止..."
    systemctl stop embodiedpulse
    sleep 2
else
    echo "✅ 服务未运行"
fi

# 2. 检查代码语法
echo ""
echo "【2. 检查代码语法】"
echo "----------------------------------------"
python3 -m py_compile bilibili_models.py 2>&1 && echo "✅ bilibili_models.py 语法正确" || echo "❌ bilibili_models.py 有语法错误"
python3 -m py_compile auth_routes.py 2>&1 && echo "✅ auth_routes.py 语法正确" || echo "❌ auth_routes.py 有语法错误"
python3 -m py_compile app.py 2>&1 && echo "✅ app.py 语法正确" || echo "❌ app.py 有语法错误"

# 3. 测试模块导入
echo ""
echo "【3. 测试模块导入】"
echo "----------------------------------------"
python3 << 'PYEOF'
import sys
sys.path.insert(0, '/srv/EmbodiedPulse2026')

try:
    from bilibili_models import get_bilibili_session, BilibiliUp, BilibiliVideo
    print("✅ bilibili_models 导入成功")
except Exception as e:
    print(f"❌ bilibili_models 导入失败: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

try:
    from app import app
    print("✅ app 导入成功")
except Exception as e:
    print(f"❌ app 导入失败: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("✅ 所有模块导入成功")
PYEOF

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ 模块导入失败，请先修复代码错误"
    exit 1
fi

# 4. 启动服务
echo ""
echo "【4. 启动服务】"
echo "----------------------------------------"
systemctl start embodiedpulse
sleep 5

# 5. 检查服务状态
echo ""
echo "【5. 检查服务状态】"
echo "----------------------------------------"
if systemctl is-active --quiet embodiedpulse; then
    echo "✅ 服务启动成功"
    systemctl status embodiedpulse --no-pager -l | head -25
else
    echo "❌ 服务启动失败"
    echo ""
    echo "查看错误日志:"
    journalctl -u embodiedpulse -n 50 --no-pager | tail -30
    exit 1
fi

# 6. 测试API
echo ""
echo "【6. 测试API端点】"
echo "----------------------------------------"
sleep 2
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/api/bilibili/all?force=1)
if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ API响应正常 (HTTP $HTTP_CODE)"
else
    echo "⚠️  API响应异常 (HTTP $HTTP_CODE)"
fi

echo ""
echo "============================================================"
echo "启动完成"
echo "============================================================"

