#!/bin/bash
# 修复502错误 - 诊断和修复脚本
# 在服务器上执行

cd /srv/EmbodiedPulse2026 || exit 1

echo "============================================================"
echo "502错误诊断和修复"
echo "============================================================"
echo ""

# 1. 检查服务状态
echo "【1. 检查服务状态】"
echo "----------------------------------------"
systemctl status embodiedpulse --no-pager -l | head -30

# 2. 查看最近的错误日志
echo ""
echo "【2. 查看最近的错误日志】"
echo "----------------------------------------"
journalctl -u embodiedpulse --since "5 minutes ago" --no-pager | tail -50

# 3. 检查应用日志
echo ""
echo "【3. 检查应用日志】"
echo "----------------------------------------"
if [ -f "app.log" ]; then
    tail -50 app.log | grep -i "error\|exception\|traceback" | tail -20
else
    echo "app.log 文件不存在"
fi

# 4. 检查Python语法错误
echo ""
echo "【4. 检查Python语法错误】"
echo "----------------------------------------"
python3 -m py_compile bilibili_models.py 2>&1 || echo "bilibili_models.py 有语法错误"
python3 -m py_compile auth_routes.py 2>&1 || echo "auth_routes.py 有语法错误"

# 5. 测试导入
echo ""
echo "【5. 测试模块导入】"
echo "----------------------------------------"
python3 << 'PYEOF'
import sys
sys.path.insert(0, '/srv/EmbodiedPulse2026')

try:
    print("测试导入 bilibili_models...")
    from bilibili_models import get_bilibili_session, BilibiliUp, BilibiliVideo
    print("✅ bilibili_models 导入成功")
except Exception as e:
    print(f"❌ bilibili_models 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("测试导入 auth_routes...")
    from auth_routes import admin_bp
    print("✅ auth_routes 导入成功")
except Exception as e:
    print(f"❌ auth_routes 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("测试导入 app...")
    from app import app
    print("✅ app 导入成功")
except Exception as e:
    print(f"❌ app 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✅ 所有模块导入成功")
PYEOF

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ 模块导入失败，请检查上面的错误信息"
    exit 1
fi

# 6. 检查代码修复
echo ""
echo "【6. 检查代码修复】"
echo "----------------------------------------"
if grep -q "try:" bilibili_models.py && grep -A 5 "try:" bilibili_models.py | grep -q "from bilibili_client import format_number"; then
    echo "✅ bilibili_models.py 已包含修复"
else
    echo "⚠️  bilibili_models.py 可能未包含修复"
    echo "检查第166-180行:"
    sed -n '166,180p' bilibili_models.py
fi

# 7. 尝试重启服务
echo ""
echo "【7. 尝试重启服务】"
echo "----------------------------------------"
systemctl restart embodiedpulse
sleep 5

# 8. 检查服务是否启动
echo ""
echo "【8. 检查服务状态】"
echo "----------------------------------------"
if systemctl is-active --quiet embodiedpulse; then
    echo "✅ 服务已启动"
    systemctl status embodiedpulse --no-pager -l | head -20
else
    echo "❌ 服务启动失败"
    echo "查看详细错误:"
    journalctl -u embodiedpulse -n 50 --no-pager
fi

# 9. 测试API端点
echo ""
echo "【9. 测试API端点】"
echo "----------------------------------------"
sleep 2
curl -s -o /dev/null -w "HTTP状态码: %{http_code}\n" http://localhost:5001/api/bilibili/all?force=1 || echo "API请求失败"

echo ""
echo "============================================================"
echo "诊断完成"
echo "============================================================"

