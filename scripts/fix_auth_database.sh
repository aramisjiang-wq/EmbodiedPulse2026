#!/bin/bash
# 修复认证数据库 - 创建缺失的auth_users表

set -e

echo "=========================================="
echo "修复认证数据库"
echo "=========================================="
echo ""

cd /srv/EmbodiedPulse2026 || {
    echo "❌ 错误: 项目目录不存在"
    exit 1
}

# 检查虚拟环境
if [ -d "venv" ]; then
    PYTHON=venv/bin/python3
elif [ -d ".venv" ]; then
    PYTHON=.venv/bin/python3
else
    PYTHON=python3
fi

echo "1️⃣  检查数据库连接..."
$PYTHON << 'EOF'
import os
import sys
sys.path.insert(0, '/srv/EmbodiedPulse2026')

from dotenv import load_dotenv
load_dotenv()

from database import db
from app import app

with app.app_context():
    # 检查数据库连接
    try:
        db.engine.connect()
        print("✅ 数据库连接成功")
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        sys.exit(1)
EOF

if [ $? -ne 0 ]; then
    echo "❌ 数据库连接失败，请检查配置"
    exit 1
fi

echo ""
echo "2️⃣  初始化认证数据库表..."
$PYTHON << 'EOF'
import os
import sys
sys.path.insert(0, '/srv/EmbodiedPulse2026')

from dotenv import load_dotenv
load_dotenv()

from app import app
from database import db
from auth_models import AuthUser, AdminUser, AccessLog, LoginHistory

with app.app_context():
    try:
        print("正在创建认证数据库表...")
        db.create_all()
        print("✅ 认证数据库表创建成功")
        print("   - auth_users (认证用户表)")
        print("   - admin_users (管理员表)")
        print("   - access_logs (访问日志表)")
        print("   - login_history (登录历史表)")
        
        # 检查表是否存在
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        if 'auth_users' in tables:
            print("✅ auth_users 表已存在")
        else:
            print("❌ auth_users 表创建失败")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ 创建表失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
EOF

if [ $? -ne 0 ]; then
    echo "❌ 初始化失败"
    exit 1
fi

echo ""
echo "3️⃣  验证表结构..."
$PYTHON << 'EOF'
import os
import sys
sys.path.insert(0, '/srv/EmbodiedPulse2026')

from dotenv import load_dotenv
load_dotenv()

from app import app
from database import db
from auth_models import AuthUser

with app.app_context():
    try:
        # 尝试查询表
        count = AuthUser.query.count()
        print(f"✅ auth_users 表验证成功，当前用户数: {count}")
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
EOF

if [ $? -ne 0 ]; then
    echo "❌ 验证失败"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ 认证数据库修复完成！"
echo "=========================================="
echo ""
echo "📋 下一步:"
echo "1. 重启服务: sudo systemctl restart embodiedpulse"
echo "2. 重新测试飞书登录"

