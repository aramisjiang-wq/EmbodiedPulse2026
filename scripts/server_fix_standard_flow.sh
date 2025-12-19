#!/bin/bash
# 服务器端标准修复流程脚本
# 严格按照：GitHub → 服务器拉取 → 验证 → 重启 的流程

set -e  # 遇到错误立即退出

cd /srv/EmbodiedPulse2026 || {
    echo "❌ 无法进入项目目录"
    exit 1
}

echo "============================================================"
echo "B站数据问题标准修复流程"
echo "============================================================"
echo ""

# ==================== 步骤1: 从GitHub拉取最新代码 ====================
echo "【步骤1: 从GitHub拉取最新代码】"
echo "----------------------------------------"

# 检查git状态
echo "当前git状态:"
git status --short | head -10

# 备份当前修改（如果有）
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo ""
    echo "⚠️  检测到未提交的修改，创建备份..."
    BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    git diff > "$BACKUP_DIR/local_changes.patch" 2>/dev/null || true
    echo "备份已保存到: $BACKUP_DIR"
fi

# 拉取最新代码
echo ""
echo "从GitHub拉取最新代码..."
if git pull origin main; then
    echo "✅ 代码拉取成功"
    echo "最新commit:"
    git log --oneline -1
else
    echo "❌ 代码拉取失败"
    echo "请检查："
    echo "  1. GitHub连接是否正常"
    echo "  2. 是否有冲突需要解决"
    exit 1
fi

# ==================== 步骤2: 验证代码更新 ====================
echo ""
echo "【步骤2: 验证代码更新】"
echo "----------------------------------------"

# 检查关键文件是否存在
REQUIRED_FILES=(
    "bilibili_models.py"
    "auth_routes.py"
    "app.py"
    "scripts/full_bilibili_diagnosis.sh"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file 存在"
    else
        echo "❌ $file 不存在"
        exit 1
    fi
done

# ==================== 步骤3: 检查代码语法 ====================
echo ""
echo "【步骤3: 检查代码语法】"
echo "----------------------------------------"

# 检查Python语法
echo "检查Python文件语法..."
ERRORS=0

if python3 -m py_compile bilibili_models.py 2>&1; then
    echo "✅ bilibili_models.py 语法正确"
else
    echo "❌ bilibili_models.py 有语法错误"
    ERRORS=$((ERRORS + 1))
fi

if python3 -m py_compile auth_routes.py 2>&1; then
    echo "✅ auth_routes.py 语法正确"
else
    echo "❌ auth_routes.py 有语法错误"
    ERRORS=$((ERRORS + 1))
fi

if python3 -m py_compile app.py 2>&1; then
    echo "✅ app.py 语法正确"
else
    echo "❌ app.py 有语法错误"
    ERRORS=$((ERRORS + 1))
fi

if [ $ERRORS -gt 0 ]; then
    echo ""
    echo "❌ 发现 $ERRORS 个语法错误，请先修复"
    echo "可以使用修复脚本: bash scripts/fix_indentation_error.sh"
    exit 1
fi

# ==================== 步骤4: 测试模块导入 ====================
echo ""
echo "【步骤4: 测试模块导入】"
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
    sys.exit(1)

try:
    from auth_routes import admin_bp
    print("✅ auth_routes 导入成功")
except Exception as e:
    print(f"❌ auth_routes 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    from app import app
    print("✅ app 导入成功")
except Exception as e:
    print(f"❌ app 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("✅ 所有模块导入成功")
PYEOF

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ 模块导入失败，请检查错误信息"
    exit 1
fi

# ==================== 步骤5: 重启服务 ====================
echo ""
echo "【步骤5: 重启服务】"
echo "----------------------------------------"

# 停止服务
if systemctl is-active --quiet embodiedpulse; then
    echo "停止服务..."
    systemctl stop embodiedpulse
    sleep 2
fi

# 启动服务
echo "启动服务..."
systemctl start embodiedpulse
sleep 5

# 检查服务状态
if systemctl is-active --quiet embodiedpulse; then
    echo "✅ 服务启动成功"
    systemctl status embodiedpulse --no-pager -l | head -15
else
    echo "❌ 服务启动失败"
    echo "查看错误日志:"
    journalctl -u embodiedpulse -n 50 --no-pager | tail -30
    exit 1
fi

# ==================== 步骤6: 验证API ====================
echo ""
echo "【步骤6: 验证API】"
echo "----------------------------------------"

sleep 3
HTTP_CODE=$(curl -s -o /tmp/api_test.json -w "%{http_code}" http://localhost:5001/api/bilibili/all?force=1)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ API响应正常 (HTTP $HTTP_CODE)"
    python3 << 'PYEOF'
import json
try:
    with open('/tmp/api_test.json', 'r') as f:
        data = json.load(f)
    
    if data.get('success'):
        print(f"   UP主数量: {len(data.get('data', []))}")
        if data.get('data'):
            first = data['data'][0]
            print(f"   第一个UP主: {first.get('user_info', {}).get('name')}")
            print(f"   视频数量: {len(first.get('videos', []))}")
    else:
        print(f"   ⚠️  API返回失败: {data.get('error')}")
except Exception as e:
    print(f"   ⚠️  解析响应失败: {e}")
PYEOF
else
    echo "❌ API响应异常 (HTTP $HTTP_CODE)"
    if [ -f /tmp/api_test.json ]; then
        echo "响应内容:"
        head -20 /tmp/api_test.json
    fi
fi

# ==================== 步骤7: 总结 ====================
echo ""
echo "============================================================"
echo "修复流程完成"
echo "============================================================"
echo ""
echo "✅ 代码已从GitHub更新"
echo "✅ 代码语法验证通过"
echo "✅ 模块导入成功"
echo "✅ 服务已重启"
echo "✅ API测试完成"
echo ""
echo "下一步："
echo "1. 访问 https://essay.gradmotion.com/bilibili 检查前端页面"
echo "2. 访问 https://admin123.gradmotion.com/admin/bilibili 检查管理后台"
echo "3. 如果还有问题，执行: bash scripts/full_bilibili_diagnosis.sh"

