#!/bin/bash
# 检查认证数据库状态

set -e

echo "=========================================="
echo "检查认证数据库状态"
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

echo "1️⃣  检查数据库类型和连接..."
$PYTHON << 'EOF'
import os
import sys
sys.path.insert(0, '/srv/EmbodiedPulse2026')

from dotenv import load_dotenv
env_path = '/srv/EmbodiedPulse2026/.env'
if os.path.exists(env_path):
    load_dotenv(env_path)

from app import app
from database import db

with app.app_context():
    # 检查数据库类型
    db_url = os.getenv('DATABASE_URL', 'sqlite:///./papers.db')
    print(f"数据库URL: {db_url[:50]}...")
    
    if 'postgresql' in db_url.lower() or 'postgres' in db_url.lower():
        print("✅ 数据库类型: PostgreSQL")
    elif 'sqlite' in db_url.lower():
        print("⚠️  数据库类型: SQLite")
    else:
        print("❓ 数据库类型: 未知")
    
    # 检查连接
    try:
        db.engine.connect()
        print("✅ 数据库连接成功")
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        sys.exit(1)
EOF

echo ""
echo "2️⃣  检查认证相关表..."
$PYTHON << 'EOF'
import os
import sys
sys.path.insert(0, '/srv/EmbodiedPulse2026')

from dotenv import load_dotenv
env_path = '/srv/EmbodiedPulse2026/.env'
if os.path.exists(env_path):
    load_dotenv(env_path)

from app import app
from database import db
from sqlalchemy import inspect

with app.app_context():
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    
    auth_tables = ['auth_users', 'admin_users', 'access_logs', 'login_history']
    
    print("认证相关表状态:")
    for table in auth_tables:
        if table in tables:
            print(f"  ✅ {table} - 存在")
        else:
            print(f"  ❌ {table} - 不存在")
    
    print(f"\n所有表数量: {len(tables)}")
    print(f"认证表数量: {sum(1 for t in auth_tables if t in tables)}/{len(auth_tables)}")
EOF

echo ""
echo "3️⃣  检查用户数据..."
$PYTHON << 'EOF'
import os
import sys
sys.path.insert(0, '/srv/EmbodiedPulse2026')

from dotenv import load_dotenv
env_path = '/srv/EmbodiedPulse2026/.env'
if os.path.exists(env_path):
    load_dotenv(env_path)

from app import app
from database import db
from auth_models import AuthUser, AdminUser, LoginHistory

with app.app_context():
    try:
        auth_user_count = AuthUser.query.count()
        admin_user_count = AdminUser.query.count()
        login_history_count = LoginHistory.query.count()
        
        print(f"认证用户数: {auth_user_count}")
        print(f"管理员数: {admin_user_count}")
        print(f"登录历史记录数: {login_history_count}")
        
        if auth_user_count > 0:
            print("\n最近的认证用户:")
            recent_users = AuthUser.query.order_by(AuthUser.created_at.desc()).limit(5).all()
            for user in recent_users:
                print(f"  - {user.name} ({user.feishu_id[:8]}...) - {user.created_at}")
        
        if login_history_count > 0:
            print("\n最近的登录记录:")
            recent_logs = LoginHistory.query.order_by(LoginHistory.login_time.desc()).limit(5).all()
            for log in recent_logs:
                print(f"  - {log.login_time} - {log.login_type} - {log.status}")
    except Exception as e:
        print(f"❌ 查询失败: {e}")
        import traceback
        traceback.print_exc()
EOF

echo ""
echo "=========================================="
echo "检查完成"
echo "=========================================="

